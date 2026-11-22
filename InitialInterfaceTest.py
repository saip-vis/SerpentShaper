"""SerpentShaper's local, read-only ingestion interface. Python standard library only.

Run: python3 InitialInterfaceTest.py
Open: http://127.0.0.1:8765
"""
import argparse
from contextlib import closing
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT/'data/processed/venom_diet_2023/serpentshaper.sqlite'

class APIError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status

class Interface:
    def __init__(self, database=DEFAULT_DB):
        self.database = Path(database).resolve()
        if not self.database.is_file():
            raise FileNotFoundError(f'Database missing: {self.database}. Run scripts/clean_venom_data.py first.')

    def connect(self):
        conn = sqlite3.connect(self.database.as_uri()+'?mode=ro',uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA query_only=ON')
        return conn

    def summary(self):
        with closing(self.connect()) as c:
            counts = {name:c.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0] for name in
                      ['profiles','ready_profiles','ready_proteomic_profiles','ready_transcriptomic_profiles','toxin_dictionary']}
            counts['held_profiles'] = counts['profiles']-counts['ready_profiles']
            return {'counts':counts,'units':'percentage_points', 'database_mode':'read_only',
                    'notice':'Structural eligibility does not mean biological validation. Species names are not taxonomically reconciled.',
                    'sources':[dict(r) for r in c.execute('SELECT * FROM sources')]}

    def toxins(self):
        with closing(self.connect()) as c:
            return [dict(r) for r in c.execute('SELECT * FROM toxin_dictionary ORDER BY original_label COLLATE NOCASE')]

    def input_spec(self):
        spec=json.loads((ROOT/'config/venom_input_spec.json').read_text())
        evidence=json.loads((ROOT/'evidence/input_evidence.json').read_text())
        binding=spec['source_binding']
        with closing(self.connect()) as conn:
            actual=conn.execute('SELECT sha256,sheet,dataset_doi FROM sources WHERE source_id=?',(binding['source_id'],)).fetchone()
        if actual is None or tuple(actual)!=(binding['workbook_sha256'],binding['sheet'],binding['dataset_doi']):
            raise APIError('Input specification does not match the database source. Review its source binding.',503)
        sources={s['id']:s for s in evidence['sources']}
        return {'spec':spec,'evidence':[dict(c,source_url=sources[c['source_id']]['url']) for c in evidence['claims']]}

    def profiles(self, query='', measurement_type='', include_held=False, limit=50, offset=0):
        if measurement_type not in ('','proteomics','transcriptomics','unknown'):
            raise APIError('Unknown measurement_type.')
        if not 1<=limit<=100 or offset<0:
            raise APIError('limit must be 1–100; offset must be nonnegative.')
        where, args = [], []
        if not include_held:
            where.append("ingestion_status='ready_with_caveats'")
        if measurement_type:
            where.append('measurement_type=?'); args.append(measurement_type)
        if query.strip():
            # Literal substring search: punctuation cannot become SQL or LIKE wildcards.
            where.append('(instr(lower(species_name),lower(?))>0 OR instr(lower(COALESCE(location,\'\')),lower(?))>0)')
            args.extend([query.strip(),query.strip()])
        clause = ' WHERE '+' AND '.join(where) if where else ''
        with closing(self.connect()) as c:
            total = c.execute('SELECT COUNT(*) FROM profiles'+clause,args).fetchone()[0]
            rows = c.execute('SELECT profile_id,species_name,location,measurement_type,ingestion_status,source_row,component_sum_pct FROM profiles'+clause+' ORDER BY species_name,source_row LIMIT ? OFFSET ?',[*args,limit,offset])
            return {'items':[dict(r) for r in rows],'total':total,'limit':limit,'offset':offset,'include_held':include_held}

    def profile(self, profile_id, include_held=False):
        with closing(self.connect()) as c:
            row = c.execute('SELECT * FROM profiles WHERE profile_id=?',(profile_id,)).fetchone()
            if row is None:
                raise APIError('Profile not found.',404)
            if row['ingestion_status']=='needs_review' and not include_held:
                raise APIError('This profile is held for review. Enable include_held explicitly to inspect it.',403)
            profile = dict(row)
            profile.pop('raw_source_row_json')
            source = dict(c.execute('SELECT * FROM sources WHERE source_id=?',(row['source_id'],)).fetchone())
            source['url']='https://doi.org/'+source['dataset_doi']
            components = [dict(r) for r in c.execute('''SELECT c.*,d.original_label,d.display_name,d.canonical_id,d.mapping_status
                FROM components c JOIN toxin_dictionary d USING(toxin_id) WHERE profile_id=?
                ORDER BY c.abundance_pct DESC NULLS LAST,d.original_label''',(profile_id,))]
            issues = [dict(r) for r in c.execute('SELECT * FROM review_queue WHERE profile_id=? ORDER BY issue_id',(profile_id,))]
            return {'schema_version':1,'profile':profile,'components':components,'source':source,'issues':issues,
                    'notice':'Missing is not zero. Ingredient categories remain separate; no biological function or family aggregation is inferred.'}

    def validate(self, payload):
        if not isinstance(payload,dict) or not isinstance(payload.get('components'),list):
            raise APIError('Provide an object with a components array.')
        items = payload['components']
        if len(items)>130:
            raise APIError('At most 130 component entries are allowed.')
        dictionary = {t['toxin_id']:t for t in self.toxins()}
        catalog=self.input_spec()['spec']
        editable={tid for control in catalog['controls'] for tid in control['source_toxin_ids']}
        source_context=None
        retained={}
        if 'source_profile_id' in payload:
            pid=payload['source_profile_id']
            if not isinstance(pid,str) or not pid:
                raise APIError('source_profile_id must be a nonempty string.')
            original=self.profile(pid)
            if original['profile']['measurement_type']!='proteomics':
                raise APIError('Only eligible proteomic profiles can seed a composition. Transcriptomics describes gene expression, not measured venom abundance.')
            p=original['profile']
            source_context={'profile_id':pid,'species_name':p['species_name'],
                'measurement_type':p['measurement_type'],'source_sheet':p['source_sheet'],
                'source_row':p['source_row'],'dataset_doi':original['source']['dataset_doi']}
            retained={c['toxin_id']:{'toxin_id':c['toxin_id'],'abundance_pct':c['abundance_pct'],
                'value_status':c['value_status'],'origin':'source','source_cell':c['source_cell'],
                'source_raw_value':c['raw_value'],'source_formula':c['source_formula']} for c in original['components']}
        errors, warnings, normalized, seen = [], [], [], set()
        for index,item in enumerate(items):
            if not isinstance(item,dict):
                errors.append(f'Entry {index+1}: expected an object.'); continue
            tid = item.get('toxin_id')
            if not isinstance(tid,str) or tid not in dictionary:
                errors.append(f'Entry {index+1}: unknown toxin_id.'); continue
            if tid in seen:
                errors.append(f'Entry {index+1}: duplicate toxin_id {tid}.'); continue
            seen.add(tid)
            if source_context and tid not in editable:
                errors.append(f'{dictionary[tid]["original_label"]}: source-only categories cannot be edited in a profile-based composition.'); continue
            value = item.get('abundance_pct')
            if value is None or (isinstance(value,str) and not value.strip()):
                normalized.append({'toxin_id':tid,'abundance_pct':None,'value_status':'missing'})
                warnings.append(f'{dictionary[tid]["original_label"]}: no percentage supplied; retained as missing.')
                continue
            try:
                if isinstance(value,bool) or not isinstance(value,(str,int,float)):
                    raise InvalidOperation
                number = Decimal(str(value).strip())
                if not number.is_finite() or not Decimal(0)<=number<=Decimal(100):
                    raise InvalidOperation
            except InvalidOperation:
                errors.append(f'{dictionary[tid]["original_label"]}: enter a finite percentage from 0 to 100.'); continue
            normalized.append({'toxin_id':tid,'abundance_pct':float(number),'value_status':'reported_zero' if number==0 else 'reported_positive'})
            if dictionary[tid]['mapping_status']=='unreviewed':
                warnings.append(f'{dictionary[tid]["original_label"]}: original source label; terminology remains unreviewed.')
        missing_count = sum(v['value_status']=='missing' for v in normalized)
        if missing_count:
            errors.append('Enter a number or remove each blank entry before submitting a complete custom composition.')
        if source_context:
            for entry in normalized:
                retained[entry['toxin_id']]=dict(retained[entry['toxin_id']],**entry,origin='user_edit')
            normalized=list(retained.values())
            inherited_missing=sum(v['value_status']=='missing' and v['origin']=='source' for v in normalized)
            warnings.append('This is a user-edited composition with a source reference, not a new measured profile. Source-only categories are retained without normalization.')
            if inherited_missing:
                warnings.append(f'{inherited_missing} source entries remain unreported; they are preserved as missing, not zero.')
        if not items and not source_context:
            errors.append('Add at least one component.')
        total=sum((Decimal(str(v['abundance_pct'])) for v in normalized if v['abundance_pct'] is not None),Decimal(0))
        target=Decimal(str(catalog['accounting']['custom_total_pct']))
        tolerance=Decimal(str(catalog['accounting']['custom_total_tolerance_percentage_points']))
        if abs(total-target)>tolerance:
            errors.append(f'Supplied valid percentages sum to {total}%; custom input must total {target}% ±{tolerance} percentage points.')
        return {'valid':not errors,'sum_pct':float(total),'units':'percentage_points','errors':errors,
                'warnings':warnings,'components':normalized,'measurement_type':'user_defined',
                'source_context':source_context,'spec_version':catalog['spec_version'],
                'unallocated_pct':float(max(Decimal(0),target-total)),
                'overallocated_pct':float(max(Decimal(0),total-target)),
                'notice':'Input formatting and totals only. No biological plausibility, effects, or species prediction is assessed. Nothing is saved.'}

HTML = (ROOT / "InitialInterfaceTest.html").read_text(encoding="utf-8")

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, payload, status=200):
        body=json.dumps(payload,allow_nan=False,ensure_ascii=False).encode()
        self.respond(body,'application/json; charset=utf-8',status)

    def respond(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.end_headers()
        self.wfile.write(body)

    def dispatch(self):
        split=urlsplit(self.path)
        query=parse_qs(split.query,keep_blank_values=True)
        arg=lambda key,default='':query.get(key,[default])[0]
        held=arg('include_held','0')=='1'
        app=self.server.app
        if self.command=='GET':
            if split.path=='/':
                return self.respond(HTML.encode(),'text/html; charset=utf-8')
            if split.path=='/api/summary':
                return self.send_json(app.summary())
            if split.path=='/api/toxins':
                return self.send_json(app.toxins())
            if split.path=='/api/input-spec':
                return self.send_json(app.input_spec())
            if split.path=='/api/profiles':
                try: limit,offset=int(arg('limit','50')),int(arg('offset','0'))
                except ValueError: raise APIError('limit and offset must be integers.')
                return self.send_json(app.profiles(arg('q'),arg('measurement_type'),held,limit,offset))
            if split.path.startswith('/api/profiles/'):
                return self.send_json(app.profile(unquote(split.path[len('/api/profiles/'):]),held))
        if self.command=='POST' and split.path=='/api/validate':
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}:
                raise APIError('Origin not allowed.',403)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                raise APIError('Use Content-Type: application/json.',415)
            try: length=int(self.headers.get('Content-Length','0'))
            except ValueError: raise APIError('Invalid Content-Length.')
            if not 0<length<=65536:
                raise APIError('JSON body must be between 1 and 65536 bytes.',413)
            try: payload=json.loads(self.rfile.read(length))
            except (ValueError,UnicodeDecodeError): raise APIError('Invalid JSON.')
            return self.send_json(app.validate(payload))
        raise APIError('Endpoint not found.',404)

    def handle_request(self):
        try: self.dispatch()
        except APIError as exc: self.send_json({'error':str(exc)},exc.status)
        except Exception:
            self.send_json({'error':'Unexpected server error; check the database and restart.'},500)

    do_GET=handle_request
    do_POST=handle_request

def make_server(port=8765, database=DEFAULT_DB):
    app=Interface(database)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    server.app=app
    return server

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--database',type=Path,default=DEFAULT_DB)
    args=parser.parse_args()
    if not 0<=args.port<=65535:
        parser.error('Port must be between 0 and 65535.')
    try: server=make_server(args.port,args.database)
    except (OSError,sqlite3.Error) as exc: parser.exit(1,f'Could not start interface: {exc}\n')
    print(f'SerpentShaper InitialInterfaceTest: http://127.0.0.1:{server.server_port}',flush=True)
    print('Database is read-only. Press Ctrl+C to stop.',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__':
    main()

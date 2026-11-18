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
        errors, warnings, normalized, seen = [], [], [], set()
        total = Decimal(0)
        for index,item in enumerate(items):
            if not isinstance(item,dict):
                errors.append(f'Entry {index+1}: expected an object.'); continue
            tid = item.get('toxin_id')
            if not isinstance(tid,str) or tid not in dictionary:
                errors.append(f'Entry {index+1}: unknown toxin_id.'); continue
            if tid in seen:
                errors.append(f'Entry {index+1}: duplicate toxin_id {tid}.'); continue
            seen.add(tid)
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
            total += number
            normalized.append({'toxin_id':tid,'abundance_pct':float(number),'value_status':'reported_zero' if number==0 else 'reported_positive'})
            if dictionary[tid]['mapping_status']=='unreviewed':
                warnings.append(f'{dictionary[tid]["original_label"]}: original source label; terminology remains unreviewed.')
        if not items:
            errors.append('Add at least one component.')
        if abs(total-Decimal(100))>Decimal('0.01'):
            errors.append(f'Supplied valid percentages sum to {total}%; custom input must total 100% ±0.01 percentage points.')
        missing_count = sum(v['value_status']=='missing' for v in normalized)
        if missing_count:
            errors.append('Enter a number or remove each blank entry before submitting a complete custom composition.')
        return {'valid':not errors,'sum_pct':float(total),'units':'percentage_points','errors':errors,
                'warnings':warnings,'components':normalized,'measurement_type':'user_defined',
                'notice':'Input formatting and totals only. No biological plausibility, effects, or species prediction is assessed. Nothing is saved.'}

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SerpentShaper · Initial interface test</title>
<style>
:root{--ink:#183b2e;--muted:#62746b;--line:#dce3dc;--green:#236544;--paper:#f5f6f0}*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px system-ui,sans-serif}header{background:#153e2d;color:white;padding:26px 5vw}header small{color:#c2dacb;letter-spacing:.12em;text-transform:uppercase}h1{font-size:28px;margin:8px 0}h2{font-size:22px;margin:0 0 12px}h3{font-size:16px;margin:24px 0 10px}p{line-height:1.55}main{max-width:1420px;margin:auto;padding:25px 4vw}.stats{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}.stat{background:white;border:1px solid var(--line);padding:15px 22px;border-radius:12px;flex:1;min-width:140px}.stat strong{font-size:28px;display:block}.muted{color:var(--muted)}nav{display:flex;gap:8px;margin-bottom:20px}button,.button{border:1px solid var(--line);background:white;color:var(--ink);padding:10px 14px;border-radius:8px;font:inherit;cursor:pointer}button:hover{background:#eaf0e7}button.active,button.primary{background:var(--green);color:white;border-color:var(--green)}button:disabled{opacity:.45;cursor:default}button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #69a884;outline-offset:2px}.layout{display:grid;grid-template-columns:340px minmax(0,1fr);gap:20px}.card{background:white;border:1px solid var(--line);border-radius:14px;padding:20px;min-width:0}label{display:block;font-size:13px;font-weight:600;margin:10px 0 6px}input,select{width:100%;padding:10px;border:1px solid #bbc9bf;border-radius:7px;background:white;color:var(--ink);font:inherit}.check{display:flex;gap:8px;align-items:center;font-weight:400}.check input{width:auto}.list{margin-top:14px;max-height:530px;overflow:auto}.profile{display:block;text-align:left;width:100%;margin:6px 0;padding:12px}.profile strong{display:block}.profile small{display:block;color:var(--muted);margin-top:5px}.profile.selected{border-color:var(--green);background:#edf5ec}.pager,.actions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px}.badge{font-size:12px;padding:4px 8px;background:#e7f0e4;border-radius:5px}.notice{background:#f4f6ef;border-left:3px solid #aac1a6;padding:12px;line-height:1.5;margin:15px 0}.warning{background:#fff4dd;border-color:#b9822c}.error{color:#9d3028}.table-wrap{overflow:auto;max-height:540px}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;padding:11px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{background:#f5f7f2;position:sticky;top:0}td small{display:block;color:var(--muted)}.percent{white-space:nowrap;font-variant-numeric:tabular-nums}.track{width:100px;height:4px;background:#e6ece4;border-radius:8px;margin-top:5px}.track span{display:block;height:4px;background:#538460;border-radius:8px}.meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.meta div{overflow-wrap:anywhere}.meta small{display:block;color:var(--muted);margin-bottom:4px}pre{background:#f1f4ee;padding:15px;overflow:auto;font-size:12px;max-height:450px}a{color:#236544}.entry{display:grid;grid-template-columns:minmax(150px,1fr) 130px auto;gap:10px;margin:10px 0;align-items:center}[hidden]{display:none!important}#detail{min-height:550px}footer{padding:25px 0;font-size:12px;color:var(--muted)}@media(max-width:850px){.layout{grid-template-columns:1fr}.list{max-height:260px}.entry{grid-template-columns:1fr 90px auto}.meta{grid-template-columns:1fr}}
</style></head><body>
<header><small>Local data workspace</small><h1>SerpentShaper</h1><div>Initial interface test · Browse evidence and validate composition inputs</div></header>
<main><div id="globalError" class="notice warning" role="alert" hidden></div><div class="stats" id="stats" aria-label="Dataset counts"></div>
<nav aria-label="Workspace"><button class="active" id="browseTab" onclick="tab('browse')">Browse profiles</button><button id="composeTab" onclick="tab('compose')">Test custom input</button></nav>
<section id="browse" class="layout"><aside class="card"><h2>Profiles</h2><label for="search">Species or location</label><input id="search" placeholder="Try Naja or India" type="search"><label for="type">Evidence type</label><select id="type"><option value="">All evidence types</option><option value="proteomics">Proteomics · measured proteins</option><option value="transcriptomics">Transcriptomics · gene expression</option><option value="unknown">Unresolved type</option></select><label class="check"><input type="checkbox" id="held">Include profiles held for review</label><p id="resultCount" class="muted" role="status"></p><div class="list" id="list"></div><div class="pager"><button id="prev">Previous</button><button id="next">Next</button></div></aside><article id="detail" class="card"><h2>Select a profile</h2><p class="muted">View original ingredient percentages, evidence type, and source locations.</p></article></section>
<section id="compose" class="card" hidden><h2>Test a custom composition</h2><p class="muted">Choose source ingredient labels and enter percentages. The total must be 100% ±0.01 percentage points. This checks input structure, not biological plausibility.</p><div class="notice">Labels remain separate. Blank values are missing, not zero. Your test input is not saved.</div><div id="entries"></div><div class="actions"><button id="addEntry">Add component</button><button class="primary" id="validate">Validate input</button></div><div id="validation" aria-live="polite"></div><details><summary style="margin-top:20px;cursor:pointer">JSON request format</summary><pre>{"components": [{"toxin_id": "vd2023_E", "abundance_pct": 100}]}</pre></details></section>
<footer>Local database opened read-only. Original measurements are preserved. No ML, correlation analysis, or biological inference.</footer></main>
<script>
const $=id=>document.getElementById(id);let toxins=[],offset=0,current=null,listRequest=0,detailRequest=0;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=n=>Number(n).toLocaleString(undefined,{maximumFractionDigits:5});
async function api(url,options){let response=await fetch(url,options);let data=await response.json();if(!response.ok)throw Error(data.error||'Request failed');return data;}
function error(e){$('globalError').textContent=e.message;$('globalError').hidden=false;}
function tab(name){for(const t of ['browse','compose']){$(t).hidden=t!==name;$(t+'Tab').classList.toggle('active',t===name);}}
async function loadList(){const request=++listRequest;const qs=new URLSearchParams({q:$('search').value,measurement_type:$('type').value,include_held:$('held').checked?'1':'0',limit:30,offset});$('resultCount').textContent='Loading…';try{const d=await api('/api/profiles?'+qs);if(request!==listRequest)return;$('resultCount').textContent=d.total?`${offset+1}–${Math.min(offset+30,d.total)} of ${d.total} profiles`:'No matching profiles';$('list').innerHTML=d.items.map(p=>`<button class="profile ${current?.profile.profile_id===p.profile_id?'selected':''}" data-id="${esc(p.profile_id)}"><strong>${esc(p.species_name)}</strong><small>${esc(p.location||'Location not supplied')} · row ${p.source_row}</small><small>${esc(p.measurement_type)}${p.ingestion_status==='needs_review'?' · HELD FOR REVIEW':''}</small></button>`).join('');$('prev').disabled=offset===0;$('next').disabled=offset+30>=d.total;for(const b of $('list').querySelectorAll('button'))b.onclick=()=>selectProfile(b.dataset.id);if(!current&&d.items.length)selectProfile(d.items[0].profile_id);}catch(e){error(e);$('resultCount').textContent='Could not load profiles';}}
async function selectProfile(id){const request=++detailRequest;try{const d=await api('/api/profiles/'+encodeURIComponent(id)+'?include_held='+($('held').checked?'1':'0'));if(request!==detailRequest)return;current=d;for(const b of $('list').querySelectorAll('button'))b.classList.toggle('selected',b.dataset.id===id);renderDetail();}catch(e){error(e);}}
function renderDetail(){const {profile:p,source:s,issues}=current;const held=p.ingestion_status==='needs_review';$('detail').innerHTML=`<span class="badge">${esc(p.measurement_type)}</span><h2 style="margin-top:12px">${esc(p.species_name)}</h2><div class="meta"><div><small>Location</small>${esc(p.location||'Not supplied')}</div><div><small>Source row</small>${p.source_row} · ${esc(p.source_sheet)}</div><div><small>Source-column sum</small>${fmt(p.component_sum_pct)}%</div><div><small>Import status</small>${held?'Held for review':'Structurally eligible with caveats'}</div></div><div class="notice ${held?'warning':''}">${held?'This profile is excluded from default ingestion. ':''}${p.measurement_type==='transcriptomics'?'These percentages describe gene expression, not measured venom protein abundance.':'Percentages are source measurements. A column sum does not establish biological completeness or non-overlapping categories.'}</div><div class="actions"><button id="export">Download profile JSON</button><button id="useInput">Copy reported values to input test</button></div><h3>Composition</h3><label class="check"><input type="checkbox" id="missing">Show missing or invalid entries</label><div class="table-wrap"><table><thead><tr><th>Ingredient label</th><th>Percent</th><th>Source cell</th></tr></thead><tbody id="componentRows"></tbody></table></div><h3>Source</h3><p><a href="${esc(s.url)}" target="_blank" rel="noopener">Dataset DOI: ${esc(s.dataset_doi)}</a><br><small class="muted">Dataset-level citation; primary-study attribution has not been assigned per profile.</small></p><details><summary>Import notes (${issues.length})</summary>${issues.length?'<ul>'+issues.map(i=>`<li>${esc(i.code)}: ${esc(i.detail)}</li>`).join('')+'</ul>':'<p>No profile-specific import flags.</p>'}</details><details><summary style="margin-top:15px">Engine JSON</summary><pre>${esc(JSON.stringify(current,null,2))}</pre></details>`;$('missing').onchange=renderComponents;renderComponents();$('export').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=p.profile_id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};$('useInput').onclick=()=>{$('entries').replaceChildren();for(const c of current.components.filter(c=>c.abundance_pct!==null))addEntry(c.toxin_id,c.abundance_pct);$('validation').replaceChildren();tab('compose');};}
function renderComponents(){const show=$('missing').checked;$('componentRows').innerHTML=current.components.filter(c=>show||c.abundance_pct!==null).map(c=>`<tr><td><strong>${esc(c.original_label)}</strong><small>${c.mapping_status==='named'?esc(c.display_name):'Original label · terminology unreviewed'}</small></td><td class="percent">${c.abundance_pct===null?esc(c.value_status):fmt(c.abundance_pct)+'%'}${c.abundance_pct!==null?`<div class="track"><span style="width:${c.abundance_pct}%"></span></div>`:''}</td><td>${esc(c.source_cell)}</td></tr>`).join('');}
function addEntry(tid='',value=''){const row=document.createElement('div');row.className='entry';row.innerHTML=`<select aria-label="Ingredient">${toxins.map(t=>`<option value="${esc(t.toxin_id)}" ${tid===t.toxin_id?'selected':''}>${esc(t.original_label)}${t.mapping_status==='named'?' · '+esc(t.display_name):' · unreviewed'}</option>`).join('')}</select><input aria-label="Percentage" inputmode="decimal" placeholder="Percent" value="${esc(value)}"><button aria-label="Remove component">Remove</button>`;row.querySelector('button').onclick=()=>{row.remove();$('validation').replaceChildren();};row.oninput=()=> $('validation').replaceChildren();$('entries').append(row);}
$('addEntry').onclick=()=>addEntry();$('validate').onclick=async()=>{const components=[...$('entries').children].map(r=>({toxin_id:r.querySelector('select').value,abundance_pct:r.querySelector('input').value}));$('validate').disabled=true;try{const d=await api('/api/validate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({components})});$('validation').innerHTML=`<div class="notice ${d.valid?'':'warning'}"><strong>${d.valid?'Input passes validation':'Input needs changes'} · ${fmt(d.sum_pct)}%</strong>${d.errors.length?'<ul>'+d.errors.map(e=>'<li>'+esc(e)+'</li>').join('')+'</ul>':''}${d.warnings.length?'<p>Notes</p><ul>'+d.warnings.map(e=>'<li>'+esc(e)+'</li>').join('')+'</ul>':''}<p>${esc(d.notice)}</p></div><details><summary>Validation JSON</summary><pre>${esc(JSON.stringify(d,null,2))}</pre></details>`;}catch(e){error(e);}finally{$('validate').disabled=false;}};
let timer;$('search').oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>{offset=0;loadList();},200);};$('type').onchange=()=>{offset=0;loadList();};$('held').onchange=()=>{offset=0;if(!$('held').checked&&current?.profile.ingestion_status==='needs_review'){current=null;++detailRequest;$('detail').innerHTML='<h2>Select a profile</h2>';}loadList();};$('prev').onclick=()=>{offset=Math.max(0,offset-30);loadList();};$('next').onclick=()=>{offset+=30;loadList();};
(async()=>{try{const [s,t]=await Promise.all([api('/api/summary'),api('/api/toxins')]);toxins=t;const c=s.counts;$('stats').innerHTML=[[c.ready_profiles,'Eligible profiles'],[c.ready_proteomic_profiles,'Proteomic profiles'],[c.ready_transcriptomic_profiles,'Transcriptomic profiles'],[c.held_profiles,'Held for review']].map(([n,label])=>`<div class="stat"><strong>${n}</strong><span class="muted">${label}</span></div>`).join('');addEntry('vd2023_E',100);await loadList();}catch(e){error(e);}})();
</script></body></html>'''

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

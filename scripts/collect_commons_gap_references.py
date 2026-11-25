"""Collect a small, attributed Wikimedia Commons reference sample for iNat gaps.

Category membership is not a verified species ID. Commons generally has no
known observation grouping, so every image is excluded from model training.
"""
import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from collect_image_pilot import ROOT, now, save
from collect_catalog_followup import REPORT as INAT_REPORT, TAXA

OUT=ROOT/'reports/image_research/commons_gap_references_2026.json'
HEADERS={'User-Agent':'SerpentShaper/0.1 (academic research reference collection)'}

class TextExtractor(HTMLParser):
    def __init__(self):super().__init__();self.parts=[]
    def handle_data(self,value):self.parts.append(value)

def plain(value):
    parser=TextExtractor();parser.feed(value or '');return html.unescape(' '.join(parser.parts)).strip()

def allowed_license(short):
    x=short.lower().strip()
    return x in {'public domain','cc0','cc0 1.0'} or bool(re.fullmatch(r'cc by(?:-sa)?(?: [0-9.]+)?',x))

def candidates(name,data):
    chosen=[];authors=set()
    for page in data.get('query',{}).get('pages',[]):
        infos=page.get('imageinfo',[])
        if not infos:continue
        info=infos[0];meta=info.get('extmetadata',{});title=page.get('title','')
        value=lambda k:meta.get(k,{}).get('value','')
        license_name=plain(value('LicenseShortName'));author=plain(value('Artist'))
        if info.get('mime') not in ('image/jpeg','image/png','image/webp') or min(info.get('width',0),info.get('height',0))<512:continue
        if re.search(r'\b(map|distribution|range|drawing|illustration|skull|skeleton|diagram)\b',title,re.I):continue
        if not allowed_license(license_name) or not author or author in authors:continue
        url=info.get('url','');parsed=urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname!='upload.wikimedia.org':continue
        if not isinstance(page.get('pageid'),int):continue
        authors.add(author)
        # No observation identity is assigned: duplicate photographs or views may
        # show the same specimen even if the Commons file IDs differ.
        chosen.append({'image_id':f"commons_{page['pageid']}",'provider':'wikimedia_commons',
          'source_species_name':name,'lookup_name':name,'provider_species_name':None,
          'provider_label_note':'Exact species category only; file identification is not independently verified.',
          'observation_id':None,'split_group':None,'source_page':info.get('descriptionurl'),
          'photo_page':info.get('descriptionurl'),'image_url':url,'commons_title':title,
          'photo_license':'commons:'+license_name,'license_reference':value('LicenseUrl') or info.get('descriptionurl'),
          'license_version':None,'license_short_name':license_name,'usage_terms':plain(value('UsageTerms')),
          'attribution':author,'attribution_raw_html':value('Artist'),'original_width':info['width'],'original_height':info['height'],
          'retrieved_at':now(),'review_status':'unreviewed','framing':'unknown','viewpoint':'unknown','pose':'unknown',
          'download_status':'not_downloaded','rendering_training_excluded':True,
          'rendering_exclusion_reason':'pending_visual_review_and_observation_group',
          'collection_note':'Reference only until identity, condition, rights and independent observation grouping are verified.'})
    return chosen

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--species',action='append',help='Specific iNaturalist gap source label; repeat to add more')
    parser.add_argument('--per-species',type=int,choices=range(1,5),default=3)
    parser.add_argument('--max-species',type=int,default=None)
    args=parser.parse_args()
    inat=json.loads(INAT_REPORT.read_text());taxa=json.loads(TAXA.read_text())['taxa']
    index={x['source_name']:i for i,x in enumerate(taxa)}
    gaps=[x['species'] for x in inat['species'] if x.get('status')=='failed' or (x.get('status')=='completed' and x.get('selected')==0)]
    names=args.species if args.species else gaps
    if any(n not in gaps for n in names):raise ValueError('Only source labels recorded as iNaturalist gaps may be queried')
    if args.max_species is not None:names=names[:args.max_species]
    report=json.loads(OUT.read_text()) if OUT.exists() else {'created_at':now(),'species':[]}
    if report.get('per_species',args.per_species)!=args.per_species:raise ValueError('Use original per-species limit when resuming')
    by_name={x['species']:x for x in report['species']};report.update(status='in_progress',per_species=args.per_species,
       note='Exact Commons categories; metadata-based candidate selection, not species/condition verification. Photos have no confirmed observation grouping and remain excluded from training.')
    failures=0
    for name in names:
        if by_name.get(name,{}).get('status')=='completed':continue
        folder=ROOT/'data/image_pilots'/f"pilot_{304+index[name]:03d}_commons_{re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_')}"
        folder.mkdir(parents=True,exist_ok=True);manifest=folder/'manifest.json'
        rows=json.loads(manifest.read_text()) if manifest.exists() else []
        try:
            if not rows:
                params={'action':'query','generator':'categorymembers','gcmtitle':'Category:'+name,'gcmtype':'file',
                        'gcmlimit':50,'prop':'imageinfo','iiprop':'url|size|mime|extmetadata','format':'json','formatversion':2}
                req=Request('https://commons.wikimedia.org/w/api.php?'+urlencode(params),headers=HEADERS)
                time.sleep(1.2)
                with urlopen(req,timeout=30) as resp:data=json.load(resp)
                if 'error' in data:raise ValueError('Commons API: '+str(data['error']))
                rows=candidates(name,data)[:args.per_species];save(manifest,rows)
            from collect_pilot_followup import inventory
            _,_,hashes=inventory(folder)
            hashes.update(r['sha256'] for r in rows if r.get('sha256'))
            for row in rows:
                if row.get('download_status')=='downloaded':continue
                time.sleep(1.2)
                req=Request(row['image_url'],headers=HEADERS)
                with urlopen(req,timeout=30) as resp:
                    mime=resp.headers.get_content_type()
                    if urlsplit(resp.url).hostname!='upload.wikimedia.org' or mime not in ('image/jpeg','image/png','image/webp'):
                        raise ValueError('Unexpected Commons photo host or content type')
                    content=resp.read(20_000_001)
                if not content or len(content)>20_000_000:raise ValueError('Empty or oversized Commons image')
                digest=hashlib.sha256(content).hexdigest();ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}[mime]
                dest=folder/'images'/f'{digest}.{ext}';dest.parent.mkdir(exist_ok=True)
                if not dest.exists():dest.write_bytes(content)
                row.update(download_status='downloaded',local_path=str(dest.relative_to(folder)),sha256=digest,
                           downloaded_at=now(),byte_count=len(content),content_type=mime,exact_content_seen_elsewhere=digest in hashes)
                if digest in hashes:row['rendering_exclusion_reason']='duplicate_content_pending_review'
                hashes.add(digest);save(manifest,rows)
                print(f"{name}: {row['image_id']} downloaded",flush=True)
            result={'species':name,'folder':folder.name,'status':'completed','selected':len(rows),
                    'downloaded':sum(r.get('download_status')=='downloaded' for r in rows)};failures=0
        except HTTPError as exc:
            result={'species':name,'folder':folder.name,'status':'provider_error','error':f'HTTP {exc.code}'}
            if exc.code in (403,429):report['status']='stopped_provider_limit'
        except Exception as exc:
            result={'species':name,'folder':folder.name,'status':'failed','error':f'{type(exc).__name__}: {exc}'}
            failures=failures+1 if isinstance(exc,(URLError,TimeoutError,ConnectionError)) else 0
            if failures>=3:report['status']='stopped_connection_errors'
        by_name[name]=result;report['species']=list(by_name.values());report['updated_at']=now();save(OUT,report)
        print(json.dumps(result),flush=True)
        if report['status'] in {'stopped_provider_limit','stopped_connection_errors'}:return
    report.update(status='completed_requested_subset',updated_at=now());save(OUT,report)

if __name__=='__main__':main()

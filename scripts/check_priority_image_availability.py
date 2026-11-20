"""Small, rate-limited metadata check for weak SnakeCLEF species coverage.

No images are downloaded. Counts are observation availability, not visual quality.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'sources/image_research/priority_availability'
ALIASES={
 'Cryptelytrops purpureomaculatus':('Trimeresurus purpureomaculatus','https://www.nparks.gov.sg/florafaunaweb/fauna/4/8/487'),
 'Macrovipera lebetina':('Macrovipera lebetinus','https://reptile-database.reptarium.cz/Macrovipera/lebetinus'),
 'Gloydius brevicaudus':('Gloydius brevicauda','https://reptile-database.reptarium.cz/Gloydius/brevicaudus'),
 'Vipera renardii':('Vipera renardi','https://reptile-database.reptarium.cz/Vipera/renardi'),
 'Micropechis ikaheka':('Micropechis ikaheca','https://reptile-database.reptarium.cz/Micropechis/ikaheca'),
 'Trimeresurus puniceus':('Craspedocephalus puniceus','https://reptile-database.reptarium.cz/Craspedocephalus/puniceus'),
 'Trimeresurus wiroti':('Craspedocephalus wiroti','https://reptile-database.reptarium.cz/Craspedocephalus/wiroti')}
LAST=0

def get(endpoint,params,path):
    global LAST
    if path.exists():return json.loads(path.read_text())
    time.sleep(max(0,1.15-(time.monotonic()-LAST)))
    LAST=time.monotonic()
    url='https://api.inaturalist.org/v1/'+endpoint+'?'+urllib.parse.urlencode(params)
    request=urllib.request.Request(url,headers={'User-Agent':'SerpentShaper limited dataset availability research'})
    with urllib.request.urlopen(request,timeout=20) as response:data=json.load(response)
    saved={'request_url':url,'retrieved_at':datetime.now(timezone.utc).isoformat(),'data':data}
    path.write_text(json.dumps(saved,indent=2)+'\n')
    return saved

def main():
    FOLDER.mkdir(exist_ok=True,parents=True)
    audit=json.loads((ROOT/'reports/image_research/coverage_audit.json').read_text())
    targets=[r for r in audit['eligible_proteomic_profiles']['taxa'] if r['metadata_image_records']<30]
    results=[];failures=0
    for item in targets:
        name=item['venom_name']; lookup,ref=ALIASES.get(name,(name,None)); stem=lookup.replace(' ','_')
        record={'source_name':name,'lookup_name':lookup,'alias_reference':ref,
                'snakeclef_image_records':item['metadata_image_records'],
                'snakeclef_observations':item['metadata_observations'],'visual_quality':'not_reviewed'}
        try:
            taxa=get('taxa',{'q':lookup,'rank':'species','is_active':'true','per_page':10},FOLDER/(stem+'_taxa.json'))
            matches=[t for t in taxa['data']['results'] if t['name'].casefold() in {lookup.casefold(),name.casefold()} and t.get('is_active',True)]
            if len(matches)!=1:
                record.update(status='taxon_unresolved',candidate_names=[t['name']for t in taxa['data']['results']])
            else:
                taxon=matches[0];record.update(taxon_id=taxon['id'],provider_name=taxon['name'])
                obs=get('observations',{'taxon_id':taxon['id'],'quality_grade':'research','photos':'true',
                    'photo_license':'cc0,cc-by','per_page':1},FOLDER/(stem+'_observations.json'))
                record.update(status='metadata_checked',research_grade_observations_with_cc0_or_ccby_photo=obs['data']['total_results'],
                    provider_query_url=obs['request_url'])
            failures=0
        except Exception as exc:
            record.update(status='request_failed',error=str(exc));failures+=1
        results.append(record)
        print(name,record['status'],record.get('research_grade_observations_with_cc0_or_ccby_photo',''),flush=True)
        if failures>=3:
            print('Stopping after three consecutive failed requests.',flush=True);break
    output={'scope':'38 priority name/availability checks, not a photo quality audit','photo_licenses':['cc0','cc-by'],
        'counts_are':'research-grade observations with at least one matching licensed photo, not image counts',
        'quality_limit':'No downloaded photographs or angle/framing/identity verification.',
        'results':results,'unqueried_names':[r['venom_name']for r in targets[len(results):]]}
    (ROOT/'reports/image_research/priority_availability.json').write_text(json.dumps(output,indent=2)+'\n')

if __name__=='__main__':main()

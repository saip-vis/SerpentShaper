"""Refresh a narrow, public iNaturalist metadata snapshot for the five-species pilot.

Run explicitly when network access is available. It never downloads photos or changes review decisions.
"""
import datetime
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'ML/pilot_manifest.json'


def main():
    manifest = json.loads(PILOT.read_text())
    entries = [(s['source_species_name'], i) for s in manifest['pilot_species'] for i in s['images']]
    ids = sorted({int(i['observation_id']) for _, i in entries if i.get('observation_id')})
    query = urlencode({'id':','.join(map(str,ids)), 'per_page':len(ids)})
    request = Request('https://api.inaturalist.org/v1/observations?'+query,
                      headers={'User-Agent':'SerpentShaper pilot metadata review'})
    with urlopen(request, timeout=30) as response:
        payload = json.load(response)
    observations = {r['id']:r for r in payload.get('results',[])}
    output=[]
    for species, image in entries:
        observation = observations.get(image.get('observation_id'))
        photo = next((p for p in (observation or {}).get('photos',[]) if str(p.get('id')) == str(image['image_id']).removeprefix('inat_')), None)
        taxon = (observation or {}).get('taxon') or {}
        output.append({'image_id':image['image_id'],'source_species_name':species,
          'observation_id':image.get('observation_id'),'observation_found':observation is not None,
          'current_taxon_name':taxon.get('name'),'current_taxon_id':taxon.get('id'),
          'current_ancestor_ids':taxon.get('ancestor_ids',[]),
          'quality_grade':(observation or {}).get('quality_grade'),
          'photo_found':photo is not None,'current_photo_license':(photo or {}).get('license_code'),
          'current_attribution':(photo or {}).get('attribution'),
          'recorded_photo_license':image.get('photo_license'),
          'license_code_matches':bool(photo and photo.get('license_code') == image.get('photo_license')),
          'license_version':'not_provided_by_this_api_response'})
    result={'retrieved_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'source':'https://api.inaturalist.org/v1/observations', 'requested_observations':len(ids),
        'returned_observations':len(observations),
        'note':'Provider labels and licensing metadata only; not independent species confirmation or legal clearance.',
        'records':output}
    dest=ROOT/'ML/pilot_metadata_snapshot.json'
    dest.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'requested_observations':len(ids),'returned_observations':len(observations),
       'records':len(output),'photo_found':sum(x['photo_found'] for x in output),
       'license_code_matches':sum(x['license_code_matches'] for x in output),
       'unavailable_or_changed':[x['image_id'] for x in output if not x['photo_found'] or not x['license_code_matches']]},indent=2))

if __name__=='__main__':main()

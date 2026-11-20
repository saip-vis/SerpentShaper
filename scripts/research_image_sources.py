"""Download dataset metadata/documentation only, not snake photos or model weights."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import urllib.request
import sys
ROOT=Path(__file__).resolve().parents[1]
BASE='https://ptak.felk.cvut.cz/plants/plants/SnakeCLEF2023/'
JOBS=[(BASE+name,'snakeclef_'+short+'.csv') for name,short in [
    ('SnakeCLEF2023-TrainMetadata-iNat.csv','train_inat'),
    ('SnakeCLEF2023-TrainMetadata-HM.csv','train_hm'),
    ('SnakeCLEF2023-ValMetadata.csv','validation')]]+[
    ('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9617216/fullTextXML','batch_mask_article.xml'),
    ('https://raw.githubusercontent.com/inaturalist/inaturalist-open-data/main/Metadata/README.md','inaturalist_metadata_README.md'),
    ('https://api.figshare.com/v2/articles/29567672','strike_kinematics_metadata.json')]

def fetch(job):
    url,name=job
    try:
        with urllib.request.urlopen(url,timeout=45) as response:
            data=response.read(50_000_001)
            if len(data)>50_000_000:raise ValueError('Metadata exceeded 50 MB safety bound.')
            final=response.url
        (ROOT/'sources/image_research'/name).write_bytes(data)
        return {'url':url,'final_url':final,'path':'sources/image_research/'+name,'bytes':len(data),
                'sha256':hashlib.sha256(data).hexdigest(),'status':'downloaded'}
    except Exception as exc:return {'url':url,'file':name,'status':'failed','error':str(exc)}

if __name__=='__main__':
    if '--snakeclef-metadata' in sys.argv:
        meta=fetch(('https://huggingface.co/api/models/pengdadaaa/SnakeCLEF2024','snakeclef_participant_repo.json'))
        if meta['status']!='downloaded':raise SystemExit(meta)
        commit=json.loads((ROOT/meta['path']).read_text())['sha']
        JOBS=[(f'https://huggingface.co/pengdadaaa/SnakeCLEF2024/resolve/{commit}/metadata/{name}',name) for name in [
            'SnakeCLEF2023-TrainMetadata-iNat.csv','SnakeCLEF2023-TrainMetadata-HM.csv','SnakeCLEF2023-ValMetadata.csv']]
    if '--catalogs' in sys.argv:
        JOBS=[
            ('https://huggingface.co/api/spaces/BVRA/SnakeCLEF2024/tree/main?recursive=true','snakeclef_official_tree.json'),
            ('https://huggingface.co/api/models/pengdadaaa/SnakeCLEF2024/tree/main/metadata','snakeclef_participant_metadata_tree.json'),
            ('https://doi.org/10.7302/qta3-xs67','ummz_landing.html')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(fetch,JOBS))
    path=ROOT/'sources/image_research/downloads.json'
    old=json.loads(path.read_text()) if path.exists() else []
    path.write_text(json.dumps(old+results,indent=2)+'\n')
    for result in results:print(result['status'],result.get('path',result.get('file')),result.get('bytes',result.get('error')))

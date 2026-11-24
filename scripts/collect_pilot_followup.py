"""Collect a bounded follow-up set for five pilot species; no image is auto-accepted.

Run intentionally with network access. The collector excludes observations already
present anywhere in the active collection and selects at most one photo per new
observation. Existing files and decisions are preserved; reruns resume work.
"""
import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from collect_image_pilot import ROOT, Client, HOSTS, LICENSES, candidates, now, save

PLAN = [('pilot_150_cobra_followup','Naja naja'),
        ('pilot_151_taipan_followup','Oxyuranus scutellatus'),
        ('pilot_152_mamba_followup','Dendroaspis polylepis'),
        ('pilot_153_diamondback_followup','Crotalus atrox'),
        ('pilot_154_boomslang_followup','Dispholidus typus')]
PER_SPECIES = 12


def inventory(exclude_folder):
    obs, photos, hashes = set(), set(), set()
    for path in (ROOT/'data/image_pilots').glob('pilot_*/manifest.json'):
        if path.parent == exclude_folder:
            continue
        for row in json.loads(path.read_text()):
            if row.get('observation_id') is not None: obs.add(row['observation_id'])
            if row.get('image_id'): photos.add(row['image_id'])
            if row.get('sha256'): hashes.add(row['sha256'])
    return obs, photos, hashes


def collect(folder_name, name):
    root = ROOT/'data/image_pilots'; folder = root/folder_name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder/'manifest.json'
    rows = json.loads(path.read_text()) if path.exists() else []
    if any(r.get('source_species_name') != name for r in rows):
        raise ValueError('Existing follow-up folder contains a different species')
    seen_obs, seen_photos, seen_hashes = inventory(folder)
    seen_obs.update(r['observation_id'] for r in rows)
    seen_photos.update(r['image_id'] for r in rows)
    source_index = {t['source_name']:t for t in json.loads((ROOT/'reports/image_research/imaging_gaps.json').read_text())['taxa']}
    source = source_index[name]
    client = Client(folder/'api_cache')
    if len(rows) < PER_SPECIES:
        response = client.get('taxa', {'q':source['image_lookup_name'], 'rank':'species','is_active':'true','per_page':10})
        allowed = {name.casefold(), source['image_lookup_name'].casefold()}
        found = [t for t in response['data']['results'] if t['name'].casefold() in allowed and t.get('is_active')]
        if len(found) != 1:
            raise ValueError(f'{name}: taxon was not uniquely resolved')
        examined = 0
        for page in range(1, 6):
            response = client.get('observations',{'taxon_id':found[0]['id'],'quality_grade':'research','photos':'true',
                'photo_license':'cc0,cc-by','per_page':50,'page':page,'order_by':'id','order':'desc'})
            observations = response['data']['results']
            examined += len(observations)
            for observation in observations:
                if observation['id'] in seen_obs: continue
                matches = [r for r in candidates(observation, source, found[0], response['retrieved_at'])
                           if r['image_id'] not in seen_photos and min(r['original_width'],r['original_height']) >= 800]
                if not matches: continue
                r = matches[0]
                r.update(collection_batch=folder_name, rendering_training_excluded=True,
                         rendering_exclusion_reason='pending_visual_review',
                         collection_note='One photo selected per previously unrepresented observation; identity and condition unverified.')
                rows.append(r); seen_obs.add(r['observation_id']); seen_photos.add(r['image_id'])
                if len(rows) >= PER_SPECIES: break
            if len(rows) >= PER_SPECIES or len(observations) < 50: break
        save(path, rows)
        save(folder/'discovery_summary.json', {'species':name,'run_at':now(),
          'observations_examined':examined, 'selected_records':len(rows),
          'note':'Sample of recent research-grade observations; no independent identification, injury screening or acceptance implied.'})
    for row in rows:
        if row.get('download_status') == 'downloaded':
            continue
        if row.get('photo_license') not in LICENSES or urlsplit(row['image_url']).hostname not in HOSTS:
            row.update(download_status='failed',download_error='Unexpected source host or license code');save(path,rows);continue
        time.sleep(1.2)
        try:
            req=Request(row['image_url'], headers={'User-Agent':'SerpentShaper/0.1 limited research pilot'})
            with urlopen(req, timeout=30) as response:
                mime=response.headers.get_content_type()
                if urlsplit(response.url).hostname not in HOSTS or mime not in {'image/jpeg','image/png','image/webp','image/gif'}:
                    raise ValueError('Unexpected image response or host')
                content=response.read(20_000_001)
            if not content or len(content)>20_000_000: raise ValueError('Empty file or 20MB cap exceeded')
            sha=hashlib.sha256(content).hexdigest()
            ext={'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/gif':'gif'}[mime]
            dest=folder/'images'/f'{sha}.{ext}';dest.parent.mkdir(exist_ok=True)
            if not dest.exists():dest.write_bytes(content)
            row.update(download_status='downloaded',local_path=str(dest.relative_to(folder)),sha256=sha,
                       downloaded_at=now(),byte_count=len(content),content_type=mime,
                       exact_content_seen_elsewhere=sha in seen_hashes)
            if sha in seen_hashes:row['rendering_exclusion_reason']='duplicate_content_pending_review'
            seen_hashes.add(sha);row.pop('download_error',None)
        except HTTPError as e:
            row.update(download_status='failed',download_error=f'HTTP {e.code}')
            save(path,rows)
            if e.code in (403,429):raise
        except Exception as e:
            row.update(download_status='failed',download_error=f'{type(e).__name__}: {e}')
        save(path,rows)
        print(f"{name}: {row['image_id']} {row['download_status']}",flush=True)
    return {'species':name,'folder':folder_name,'selected':len(rows),
            'downloaded':sum(r.get('download_status')=='downloaded' for r in rows),
            'failures':sum(r.get('download_status')=='failed' for r in rows),
            'pending_review':sum(r.get('rendering_exclusion_reason')=='pending_visual_review' for r in rows)}


def main():
    report=[]
    for folder,name in PLAN:
        try:
            result=collect(folder,name);report.append(result);print(json.dumps(result),flush=True)
        except HTTPError as e:
            report.append({'species':name,'folder':folder,'status':'stopped','error':f'HTTP {e.code}'})
            save(ROOT/'ML/followup_collection.json',{'status':'stopped_provider_limit','species':report});raise
        except Exception as e:
            report.append({'species':name,'folder':folder,'status':'failed','error':f'{type(e).__name__}: {e}'})
            print(json.dumps(report[-1]),flush=True)
        save(ROOT/'ML/followup_collection.json',{'status':'in_progress','species':report})
    save(ROOT/'ML/followup_collection.json',{'status':'completed','species':report})

if __name__=='__main__':main()

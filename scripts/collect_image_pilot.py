"""Bounded iNaturalist pilot. Use provider exports for bulk acquisition."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
LICENSES = {'cc0': 'https://creativecommons.org/publicdomain/zero/1.0/',
            'cc-by': 'https://www.inaturalist.org/pages/terms'}
DEFAULTS = ['Naja naja']
HOSTS = {'inaturalist-open-data.s3.amazonaws.com', 'static.inaturalist.org'}

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)

class Client:
    def __init__(self, folder):
        self.folder, self.last = folder, 0

    def get(self, endpoint, params):
        url = 'https://api.inaturalist.org/v1/' + endpoint + '?' + urlencode(params)
        path = self.folder / (hashlib.sha256(url.encode()).hexdigest() + '.json')
        if path.exists():
            return json.loads(path.read_text())
        time.sleep(max(0, 1.2 - (time.monotonic() - self.last)))
        self.last = time.monotonic()
        with urlopen(Request(url, headers={'User-Agent': 'SerpentShaper/0.1 limited research pilot'}), timeout=30) as response:
            value = {'request_url': url, 'retrieved_at': now(), 'data': json.load(response)}
        save(path, value)
        return value

def candidates(observation, source, taxon, retrieved_at):
    observed = observation.get('taxon') or {}
    if observation.get('quality_grade') != 'research':
        return []
    # Permit identified subspecies of the resolved species, never a fuzzy name match.
    if observed.get('id') != taxon['id'] and taxon['id'] not in observed.get('ancestor_ids', []):
        return []
    result = []
    for photo in observation.get('photos', []):
        license_code = photo.get('license_code')
        if license_code not in LICENSES or photo.get('hidden') or photo.get('flags'):
            continue
        if not photo.get('attribution'):
            continue
        url = photo.get('url', '')
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in HOSTS:
            continue
        original = re.sub(r'/square\.(jpg|jpeg|png|gif|webp)$', r'/original.\1', url, flags=re.I)
        if original == url:
            continue
        dims = photo.get('original_dimensions') or {}
        dimensions = [dims.get('width'), dims.get('height')]
        if any(not isinstance(d, (int, float)) or isinstance(d, bool) or d < 512 for d in dimensions):
            continue
        result.append(dict(
            image_id=f"inat_{photo['id']}", provider='inaturalist',
            source_species_name=source['source_name'], lookup_name=source['image_lookup_name'],
            alias_reference=source.get('alias_reference'), taxon_id=taxon['id'],
            provider_species_name=taxon['name'], observed_taxon_name=observed.get('name'),
            observation_id=observation['id'], split_group=f"inat_observation_{observation['id']}",
            source_page=f"https://www.inaturalist.org/observations/{observation['id']}",
            photo_page=f"https://www.inaturalist.org/photos/{photo['id']}",
            image_url=original, photo_license=license_code,
            license_reference=LICENSES[license_code], license_version=None, attribution=photo.get('attribution'),
            original_width=dims['width'], original_height=dims['height'],
            retrieved_at=retrieved_at, review_status='unreviewed',
            framing='unknown', viewpoint='unknown', pose='unknown',
            download_status='not_downloaded'))
    return result

def discover(args, folder):
    taxa = json.loads((ROOT / 'reports/image_research/imaging_gaps.json').read_text())['taxa']
    index = {t['source_name']: t for t in taxa}
    names = args.species or DEFAULTS
    if len(set(names)) != 1 or any(n not in index for n in names):
        raise ValueError('Choose one exact source species per folder from imaging_gaps.json.')
    client = Client(folder / 'api_cache')
    old = json.loads((folder / 'manifest.json').read_text()) if (folder / 'manifest.json').exists() else []
    if any(r['source_species_name'] != names[0] for r in old):
        raise ValueError('This folder belongs to a different species. Choose a separate --batch folder.')
    manifest = {r['image_id']: r for r in old}
    summary = []
    for name in dict.fromkeys(names):
        source = index[name]
        try:
            response = client.get('taxa', {'q': source['image_lookup_name'], 'rank': 'species', 'is_active': 'true', 'per_page': 10})
            allowed = {name.casefold(), source['image_lookup_name'].casefold()}
            matches = [t for t in response['data']['results'] if t['name'].casefold() in allowed and t.get('is_active')]
            if len(matches) != 1:
                summary.append(dict(species=name, status='taxon_unresolved', candidates=[t['name'] for t in response['data']['results']]))
                continue
            taxon = matches[0]
            response = client.get('observations', dict(taxon_id=taxon['id'], quality_grade='research', photos='true',
                photo_license='cc0,cc-by', per_page=args.observations, order_by='id', order='asc'))
            found = {}
            for obs in response['data']['results']:
                for row in candidates(obs, source, taxon, response['retrieved_at']):
                    found.setdefault(row['image_id'], row)
            # Take one photo per observation first, then optional second views.
            groups = {}
            for row in found.values():
                groups.setdefault(row['observation_id'], []).append(row)
            selected = []
            for position in range(args.max_per_observation):
                for group in groups.values():
                    if position < len(group) and len(selected) < args.limit:
                        selected.append(group[position])
            for row in selected:
                manifest.setdefault(row['image_id'], row)
            summary.append(dict(species=name, status='metadata_checked', eligible_observations_available=response['data']['total_results'],
                                observations_examined=len(response['data']['results']), candidates_selected=len(selected)))
        except Exception as exc:
            summary.append(dict(species=name, status='request_failed', error=str(exc)))
        # Preserve completed work if a later request is interrupted.
        save(folder / 'manifest.json', list(manifest.values()))
        print(json.dumps(summary[-1]), flush=True)
    save(folder / 'manifest.json', list(manifest.values()))
    save(folder / 'discovery_summary.json', {'run_at': now(), 'results': summary,
        'note': 'Bounded, cached sample; not exhaustive or visually verified. Sources overlap with SnakeCLEF.'})
    if any(s['status'] == 'request_failed' for s in summary):
        raise SystemExit(1)

def download(args, folder):
    rows = json.loads((folder / 'manifest.json').read_text())
    count = 0
    for row in rows:
        if count >= args.limit:
            break
        if row.get('photo_license') not in LICENSES or urlsplit(row['image_url']).hostname not in HOSTS:
            continue
        if row.get('download_status') == 'downloaded':
            path = folder / row['local_path']
            if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256']:
                continue
        count += 1
        time.sleep(1.2)
        try:
            request = Request(row['image_url'], headers={'User-Agent': 'SerpentShaper/0.1 limited research pilot'})
            with urlopen(request, timeout=30) as response:
                mime = response.headers.get_content_type()
                if urlsplit(response.url).hostname not in HOSTS or mime not in {'image/jpeg','image/png','image/webp','image/gif'}:
                    raise ValueError('Unexpected image response or host')
                content = response.read(20_000_001)
            if not content or len(content) > 20_000_000:
                raise ValueError('Empty image or pilot 20MB size cap exceeded')
            digest = hashlib.sha256(content).hexdigest()
            extension = {'image/jpeg':'jpg','image/png':'png','image/webp':'webp','image/gif':'gif'}[mime]
            path = folder / 'images' / (digest + '.' + extension)
            path.parent.mkdir(exist_ok=True)
            if not path.exists():
                path.write_bytes(content)
            row.update(download_status='downloaded', local_path=str(path.relative_to(folder)), sha256=digest,
                       downloaded_at=now(), byte_count=len(content), content_type=mime)
            row.pop('download_error', None)
        except Exception as exc:
            row.update(download_status='failed', download_error=str(exc))
        save(folder / 'manifest.json', rows)
        print(row['image_id'], row['download_status'], flush=True)
    if any(r.get('download_status') == 'failed' for r in rows):
        raise SystemExit(1)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['discover', 'download'])
    parser.add_argument('--batch', default='pilot_001_spectacled_cobra', help='Species folder for this collection')
    parser.add_argument('--species', action='append', help='Exact source label; repeat for multiple species')
    parser.add_argument('--observations', type=int, default=20, help='Observations examined per species (1–50)')
    parser.add_argument('--limit', type=int, default=10, help='Candidates per species, or download attempts per run (1–50)')
    parser.add_argument('--max-per-observation', type=int, default=2, help='Limit related photos; sample observations before additional views (1–5)')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.batch):
        parser.error('Batch must contain only letters, digits, underscores or hyphens.')
    if not 1 <= args.limit <= 50 or not 1 <= args.observations <= 50:
        parser.error('Pilot limits must be between 1 and 50.')
    if not 1 <= args.max_per_observation <= 5:
        parser.error('Maximum photos per observation must be between 1 and 5.')
    folder = ROOT / 'data/image_pilots' / args.batch
    folder.mkdir(parents=True, exist_ok=True)
    (discover if args.action == 'discover' else download)(args, folder)

if __name__ == '__main__':
    main()

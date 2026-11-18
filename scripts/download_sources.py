"""Download public research files without modifying originals; record provenance."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'sources/download_manifest.json'

def fetch(url, relative):
    dest = ROOT / relative
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SerpentShaper research dataset discovery'})
        with urllib.request.urlopen(req, timeout=40) as response:
            body = response.read()
            content_type = response.headers.get('Content-Type', '')
            final_url = response.url
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(body)
        return dict(url=url, final_url=final_url, path=relative, status='downloaded',
                    bytes=len(body), content_type=content_type,
                    sha256=hashlib.sha256(body).hexdigest(), retrieved_at=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        return dict(url=url, path=relative, status='failed', error=str(exc))

def main():
    jobs = [
        ('https://api.github.com/repos/DEsquerre/MuseumVenomics/commits/main', 'sources/museum_commit.json'),
        ('https://api.figshare.com/v2/articles/22179949', 'sources/figshare_22179949.json'),
        ('https://api.datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.nzs7h44qs', 'sources/dryad_nzs7h44qs.json'),
    ]
    for pmc in ['PMC5618223', 'PMC5335903', 'PMC3847709', 'PMC9744630']:
        jobs.append((f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML', f'sources/{pmc}.xml'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda args: fetch(*args), jobs))
    commit_path = ROOT / 'sources/museum_commit.json'
    if commit_path.exists():
        commit = json.loads(commit_path.read_text())['sha']
        for name in ['README.md', 'PublishedProteomes.csv', 'SummaryResults_VenomMassSpecExperiment.csv']:
            results.append(fetch(f'https://raw.githubusercontent.com/DEsquerre/MuseumVenomics/{commit}/{name}', f'data/raw/museum_venomics/{name}'))
    fig_path = ROOT / 'sources/figshare_22179949.json'
    if fig_path.exists():
        data = json.loads(fig_path.read_text())
        for item in data.get('files', []):
            if item['size'] < 50_000_000:
                results.append(fetch(item['download_url'], 'data/raw/venom_diet_2023/' + Path(item['name']).name))
    MANIFEST.write_text(json.dumps(results, indent=2) + '\n')
    for item in results:
        print(item['status'], item['path'], item.get('bytes', item.get('error')))

if __name__ == '__main__':
    main()

"""Resolve repository and archive metadata to download verified file URLs."""
import concurrent.futures
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from download_sources import ROOT, MANIFEST, fetch

results = []
commit = json.loads((ROOT/'sources/museum_commit.json').read_text())['sha']
jobs = [(f'https://raw.githubusercontent.com/DEsquerre/MuseumVenomics/{commit}/{name}', f'data/raw/museum_venomics/{name}')
        for name in ['SummaryResults_ThisStudy.csv', 'LICENSE']]
for name in ['dryad_nzs7h44qs', 'squambase_dryad']:
    meta = json.loads((ROOT/f'sources/{name}_version.json').read_text())
    jobs.append(('https://datadryad.org'+meta['_links']['stash:files']['href'], f'sources/{name}_files.json'))
root = ET.parse(ROOT/'sources/PMC10899194.xml').getroot()
rept_doi = None
for citation in root.iter('element-citation'):
    if 'figshare' in ''.join(citation.itertext()).lower():
        for pubid in citation.iter('pub-id'):
            if pubid.get('pub-id-type') == 'doi':
                rept_doi = pubid.text
                break
if rept_doi:
    article_id = rept_doi.split('figshare.')[1].split('.')[0]
    jobs.append((f'https://api.figshare.com/v2/articles/{article_id}', 'sources/repttraits_figshare.json'))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results.extend(pool.map(lambda args: fetch(*args), jobs))
for name, target in [('dryad_nzs7h44qs', 'venom_environment_2021'), ('squambase_dryad', 'squambase')]:
    p = ROOT/f'sources/{name}_files.json'
    if not p.exists():
        continue
    data = json.loads(p.read_text())
    for item in data.get('_embedded', {}).get('stash:files', []):
        link = item.get('_links', {}).get('stash:download', {}).get('href')
        if link and item.get('size', 0) < 50_000_000:
            results.append(fetch('https://datadryad.org'+link, f'data/raw/{target}/{Path(item["path"]).name}'))
p = ROOT/'sources/repttraits_figshare.json'
if p.exists():
    for item in json.loads(p.read_text()).get('files', []):
        if item['size'] < 50_000_000:
            results.append(fetch(item['download_url'], f'data/raw/repttraits/{Path(item["name"]).name}'))
MANIFEST.write_text(json.dumps(json.loads(MANIFEST.read_text()) + results, indent=2) + '\n')
for item in results:
    print(item['status'], item['path'], item.get('bytes', item.get('error')))

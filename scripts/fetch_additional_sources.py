"""Fetch additional public metadata and data discovered during the audit."""
import concurrent.futures
import json
from pathlib import Path
from download_sources import ROOT, MANIFEST, fetch

jobs = [
    ('https://api.github.com/repos/DEsquerre/MuseumVenomics/contents', 'sources/museum_contents.json'),
    ('https://api.github.com/repos/blueraleigh/squamatabase/commits/master', 'sources/squamatabase_commit.json'),
    ('https://api.github.com/repos/blueraleigh/squamatabase/git/trees/master?recursive=1', 'sources/squamatabase_tree.json'),
    ('https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.nzs7h44qs', 'sources/dryad_nzs7h44qs.json'),
    ('https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.76hdr7t3b', 'sources/squambase_dryad.json'),
    ('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5335903/supplementaryFiles', 'data/raw/boomslang_2017/supplementary.zip'),
    ('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9744630/supplementaryFiles', 'data/raw/african_venoms_2022/supplementary.zip'),
    ('https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3847709/supplementaryFiles', 'data/raw/atractaspis_2013/supplementary.zip'),
    ('https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1038/s41597-024-03079-5&format=json', 'sources/repttraits_lookup.json'),
]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    results = list(pool.map(lambda args: fetch(*args), jobs))
for name in ['dryad_nzs7h44qs', 'squambase_dryad']:
    p = ROOT / f'sources/{name}.json'
    if p.exists():
        d = json.loads(p.read_text())
        link = d.get('_links', {}).get('stash:version', {}).get('href')
        if link:
            results.append(fetch('https://datadryad.org' + link, f'sources/{name}_version.json'))
if (ROOT / 'sources/squamatabase_commit.json').exists():
    commit = json.loads((ROOT / 'sources/squamatabase_commit.json').read_text())['sha']
    for name in ['inst/diet.csv', 'README.md', 'DESCRIPTION', 'man/diet.Rd']:
        results.append(fetch(f'https://raw.githubusercontent.com/blueraleigh/squamatabase/{commit}/{name}', f'data/raw/squamatabase/{Path(name).name}'))
lookup = ROOT / 'sources/repttraits_lookup.json'
if lookup.exists():
    records = json.loads(lookup.read_text()).get('resultList', {}).get('result', [])
    for record in records:
        if record.get('pmcid'):
            pmc = record['pmcid']
            results.append(fetch(f'https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML', f'sources/{pmc}.xml'))
old = json.loads(MANIFEST.read_text())
MANIFEST.write_text(json.dumps(old + results, indent=2) + '\n')
for item in results:
    print(item['status'], item['path'], item.get('bytes', item.get('error')))

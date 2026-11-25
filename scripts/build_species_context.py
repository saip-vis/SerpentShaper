"""Build cited species context; these records are not generated-snake predictions."""
import csv
import hashlib
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
TRAITS = ROOT / 'data/raw/repttraits/ReptTraits dataset v1-2.xlsx'
PROFILES = ROOT / 'data/processed/morphology/physical_profiles.json'
DIET = ROOT / 'data/raw/squamatabase/diet.csv'
OUT = ROOT / 'MainInterface/species-context-data.js'


def present(value):
    if value is None or str(value).strip().lower() in {'', 'na', 'n/a', 'unknown'}:
        return None
    return str(value).strip()


def build():
    profiles = json.loads(PROFILES.read_text())['profiles']
    # Only workbook matches already recorded as exact; no taxonomic guessing.
    rows = {p['compilation_match']['row']: p for p in profiles
            if p['compilation_match']['status'] == 'exact_source_name' and p['compilation_match']['row']}
    book = openpyxl.load_workbook(TRAITS, read_only=True, data_only=True)
    extracted = {}
    for sheet in ('Data', 'Sources of individual trait val'):
        found = {}
        for index, row in enumerate(book[sheet].iter_rows(values_only=True), 1):
            if index in rows:
                found[index] = row
            if len(found) == len(rows):
                break
        extracted[sheet] = found
    species = {}
    columns = {'microhabitat': 10, 'habitat': 11, 'diet': 19, 'prey': 20}
    for index, profile in rows.items():
        data = extracted['Data'].get(index)
        citations = extracted['Sources of individual trait val'].get(index)
        if not data or not citations or data[0] != profile['source_species_name']:
            continue
        item = {'repttraits_row': index}
        for key, col in columns.items():
            value = present(data[col - 1])
            if value:
                item[key] = {'value': value, 'citation': present(citations[col - 1])}
        length = profile.get('compilation_traits', {}).get('maximum_total_length_mm', {})
        if length.get('status') == 'reported' and isinstance(length.get('value'), (int, float)) and length['value'] > 0:
            item['maximum_total_length_mm'] = {'value': length['value'], 'citation': length.get('citation')}
        species[profile['source_species_name']] = item
    with DIET.open(newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            item = species.get(row['predator'])
            if not item or 'prey_observation' in item or row['event_setting'] != 'natural_setting' or row['event_outcome'] != 'prey_eaten':
                continue
            prey, reference = present(row['prey']), present(row['reference'])
            if prey and reference:
                item['prey_observation'] = {'prey': prey, 'reference': reference, 'country': present(row['locality_adm0_name'])}
    return {'status': 'species_reference_context_not_generated_snake_estimates',
            'repttraits_source': 'https://doi.org/10.1038/s41597-024-03079-5',
            'repttraits_data': 'https://doi.org/10.6084/m9.figshare.24572683',
            'squamatabase_source': 'https://github.com/blueraleigh/squamatabase',
            'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (TRAITS, PROFILES, DIET)},
            'species': species}


if __name__ == '__main__':
    data = build()
    OUT.write_text('window.SERPENT_SPECIES_CONTEXT = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f"Wrote contextual references for {len(data['species'])} exact species labels to {OUT.relative_to(ROOT)}")

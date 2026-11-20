"""Join existing venom and image records without changing sources or review decisions."""
import argparse
from collections import Counter, defaultdict
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3

from export_rendering_manifest import eligible

ROOT = Path(__file__).resolve().parents[1]


def name_key(value):
    return ' '.join(value.replace('_', ' ').split()).casefold()


def build(root):
    root = root.resolve()
    inputs = set()
    def read(relative):
        path = root / relative
        inputs.add(path)
        return json.loads(path.read_text())

    targets = read('reports/image_research/imaging_gaps.json')['taxa']
    progress = read('reports/image_research/remaining_species_downloads/progress.json')['species']
    database = root / 'data/processed/venom_diet_2023/serpentshaper.sqlite'
    inputs.add(database)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        profiles = [dict(r) for r in conn.execute('SELECT * FROM profiles ORDER BY profile_id')]
        dictionary = [dict(r) for r in conn.execute('SELECT * FROM toxin_dictionary ORDER BY toxin_id')]
        components = defaultdict(list)
        for row in conn.execute("SELECT * FROM components WHERE value_status != 'missing' ORDER BY profile_id,toxin_id"):
            components[row['profile_id']].append(dict(row))

    species = {}
    def entry(name):
        key = name_key(name)
        if key not in species:
            species[key] = {'species_id': 'source_' + hashlib.sha256(key.encode()).hexdigest()[:16],
                'source_species_name': name, 'taxonomy_status': 'unreconciled_source_label',
                'lookup_name': name, 'alias_reference': None, 'provider_taxa': [],
                'venom_profile_ids': [], 'images': [], 'collection_notes': None}
        return species[key]

    for target in targets:
        item = entry(target['source_name'])
        item.update(lookup_name=target['image_lookup_name'], alias_reference=target.get('alias_reference'))
        if target['source_name'] in progress:
            p = progress[target['source_name']]
            item['collection_notes'] = {k: p[k] for k in ('status', 'notes', 'discovery') if k in p}
    for profile in profiles:
        item = entry(profile['species_name'])
        item['venom_profile_ids'].append(profile['profile_id'])
        profile['reported_components'] = components[profile['profile_id']]
        profile['source_table'] = 'data/processed/venom_diet_2023/profiles.csv'
        profile['component_source_table'] = 'data/processed/venom_diet_2023/components.csv'

    for path in sorted((root / 'data/image_pilots').glob('pilot_*/manifest.json')):
        rows = read(path.relative_to(root))
        for row in rows:
            item = entry(row['source_species_name'])
            allowed = {name_key(item['source_species_name'])}
            if item['alias_reference']:
                allowed.add(name_key(item['lookup_name']))
            match = name_key(row.get('provider_species_name', '')) in allowed
            image = dict(row)
            local = (path.parent / row['local_path']).resolve() if row.get('local_path') else None
            if local and not local.is_relative_to(path.parent.resolve()):
                raise ValueError('Unsafe image path: ' + str(path))
            image.update(manifest_path=str(path.relative_to(root)),
                         local_path=str(local.relative_to(root)) if local else None,
                         file_available=bool(local and local.is_file()),
                         species_link_status=('documented_alias' if match and name_key(row['provider_species_name']) != name_key(item['source_species_name']) else 'exact_name') if match else 'unresolved',
                         rendering_eligible=bool(match and eligible(row) and local and local.is_file()))
            item['images'].append(image)
            taxon = {k: row.get(k) for k in ('provider', 'taxon_id', 'provider_species_name')}
            if taxon not in item['provider_taxa']:
                item['provider_taxa'].append(taxon)

    profile_by_id = {p['profile_id']: p for p in profiles}
    for item in species.values():
        images = item['images']
        item['counts'] = {'venom_profiles': len(item['venom_profile_ids']),
            'ready_proteomic_profiles': sum(profile_by_id[p]['ingestion_status'] == 'ready_with_caveats' and profile_by_id[p]['measurement_type'] == 'proteomics' for p in item['venom_profile_ids']),
            'image_records': len(images), 'available_images': sum(i['file_available'] for i in images),
            'rendering_eligible_images': sum(i['rendering_eligible'] for i in images),
            'review_statuses': dict(Counter(i.get('review_status', 'unreviewed') for i in images))}
        item['link_status'] = ('venom_and_images' if item['venom_profile_ids'] and images else
                               'venom_only' if item['venom_profile_ids'] else 'images_only' if images else 'collection_target_only')
        item['shared_provider_taxa_with'] = sorted(other['source_species_name'] for other in species.values()
            if other is not item and any(t['taxon_id'] is not None and t in other['provider_taxa'] for t in item['provider_taxa']))
    result = {'schema_version': 1,
        'relationship': 'Species-level association only; photos are not paired with sampled venom individuals.',
        'component_policy': 'Profiles are separate and unnormalized. Missing component rows are omitted, not zero; all categories are in toxin_dictionary. Invalid reported values remain flagged.',
        'taxonomy_policy': 'Preserve source labels; only exact names and existing documented aliases are linked. Provider IDs are provisional; shared IDs do not merge source labels.',
        'image_policy': 'All records retained for exploration, including rejected and unreviewed. rendering_eligible preserves the existing explicit-review policy and requires an available file and resolved species link.',
        'inputs': [{'path': str(p.relative_to(root)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(inputs)],
        'species': sorted(species.values(), key=lambda x: x['source_species_name']),
        'profiles': profiles, 'toxin_dictionary': dictionary}
    all_images = [i for s in result['species'] for i in s['images']]
    result['summary'] = {'source_species_labels': len(species), 'venom_profiles': len(profiles),
        'species_with_venom_and_images': sum(s['link_status'] == 'venom_and_images' for s in species.values()),
        'image_records': len(all_images), 'available_images': sum(i['file_available'] for i in all_images),
        'distinct_image_hashes': len({i['sha256'] for i in all_images if i.get('sha256')}),
        'rendering_eligible_images': sum(i['rendering_eligible'] for i in all_images),
        'unresolved_image_links': sum(i['species_link_status'] == 'unresolved' for i in all_images),
        'species_without_images': [s['source_species_name'] for s in result['species'] if not s['images']],
        'image_species_without_venom_profiles': [s['source_species_name'] for s in result['species'] if s['images'] and not s['venom_profile_ids']]}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    catalog = build(root)
    destination = root / 'data/processed/species_catalog/catalog.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix('.tmp')
    temp.write_text(json.dumps(catalog, indent=2) + '\n')
    temp.replace(destination)
    report = root / 'reports/species_catalog_summary.json'
    report.write_text(json.dumps(catalog['summary'], indent=2) + '\n')
    print(json.dumps(catalog['summary'], indent=2))


if __name__ == '__main__':
    main()

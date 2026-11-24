"""Run a transparent, species-level venom-profile retrieval baseline.

This is a non-trained comparison, not a venom-to-phenotype model or evaluation.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def compare(query, reference):
    selected = {key: value for key, value in query.items() if value is not None}
    shared = [key for key in selected if reference.get(key) is not None]
    if not shared:
        return None
    return {'compared': len(shared), 'selected': len(selected),
            'mean_absolute_difference_percentage_points': sum(abs(selected[k]-reference[k]) for k in shared)/len(shared),
            'shared_source_toxin_ids': sorted(shared)}


def run(root, query_profile):
    root = root.resolve()
    pilot = json.loads((root / 'ML/pilot_manifest.json').read_text())
    db = root / 'data/processed/venom_diet_2023/serpentshaper.sqlite'
    if hashlib.sha256(db.read_bytes()).hexdigest() != pilot['database_sha256']:
        raise ValueError('Database changed since pilot audit. Rebuild with python3 scripts/build_ml_pilot.py.')
    controls = json.loads((root / 'config/venom_input_spec.json').read_text())['controls']
    flags = json.loads((root / 'config/venom_quality_flags.json').read_text())['component_exclusions']
    exclusions = {(f['profile_id'], f['toxin_id']) for f in flags}
    toxin_ids = [c['source_toxin_ids'][0] for c in controls]
    selected_profile_ids = {p['profile_id'] for s in pilot['pilot_species']
                            if s['accepted_and_metadata_checked_images'] > 0 for p in s['profiles']}
    with sqlite3.connect(db.as_uri()+'?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        def get(pid):
            profile = conn.execute('SELECT profile_id,species_name,location,measurement_type,ingestion_status,source_row FROM profiles WHERE profile_id=?',(pid,)).fetchone()
            if not profile or profile['measurement_type']!='proteomics' or profile['ingestion_status']!='ready_with_caveats':
                raise ValueError('Query must be an eligible proteomic source profile.')
            rows = conn.execute('SELECT toxin_id,abundance_pct FROM components WHERE profile_id=?',(pid,)).fetchall()
            values = {r['toxin_id']:r['abundance_pct'] for r in rows if r['toxin_id'] in toxin_ids}
            values = {tid: value for tid, value in values.items() if (pid, tid) not in exclusions}
            return dict(profile), values
        query, values = get(query_profile)
        ranked = []
        for pid in sorted(selected_profile_ids):
            if pid == query_profile:
                continue
            profile, candidate = get(pid)
            metrics = compare(values, candidate)
            if metrics:
                ranked.append({'reference_profile':profile, **metrics})
    ranked.sort(key=lambda x:(-x['compared'],x['mean_absolute_difference_percentage_points'],
                              x['reference_profile']['species_name'],x['reference_profile']['source_row']))
    return {'method':'shared-category mean absolute percentage-point difference; coverage first',
            'status':'exploratory comparison; no model training and no performance evaluation',
            'query_profile':query, 'ranked_reference_profiles':ranked,
            'limitations':['The query profile itself is excluded, but unknown shared studies or specimens may remain.',
                'Missing values are not treated as zero; categories with no overlap cannot be compared.',
                'The uncertain NP category in black mamba profile r189 is excluded from comparisons pending source reconciliation.',
                'Venom profiles and photographs are associated only by source species name, not by individual.',
                'Similarity does not validate venom-to-phenotype inference or imply a causal relationship.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--query-profile', default='vd2023_e2d1aa974518_r189', help='Eligible proteomic profile ID')
    parser.add_argument('--output', type=Path, help='Optional JSON output file')
    args = parser.parse_args()
    result = json.dumps(run(ROOT,args.query_profile),indent=2)+'\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result,end='')


if __name__ == '__main__':
    main()

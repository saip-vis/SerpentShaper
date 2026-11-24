"""Inventory venom-profile evidence for every rendering preset without modifying data.

This is a structural audit, not a scientific verification or a prediction model.
"""
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/venom_diet_2023/serpentshaper.sqlite'
PRESETS = ROOT / 'PhysicalRendererTest/presets/species-presets.json'
SPEC = ROOT / 'config/venom_input_spec.json'
OUT = ROOT / 'ML/venom_profile_audit.json'
REPORT = ROOT / 'ML/venom_profile_audit.md'
FLAGS = ROOT / 'config/venom_quality_flags.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(db, presets, controls):
    controls_by_toxin = {c['source_toxin_ids'][0]: c['id'] for c in controls}
    flags = json.loads(FLAGS.read_text())
    uncertain = {(f['profile_id'], f['toxin_id']): f['reason'] for f in flags['component_exclusions']}
    warnings = {f['profile_id']: f['reason'] for f in flags['profile_warnings']}
    by_name = {}
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        for profile in conn.execute('SELECT * FROM profiles ORDER BY species_name,source_row'):
            p = dict(profile)
            components = [dict(r) for r in conn.execute(
                'SELECT toxin_id,abundance_pct,value_status FROM components WHERE profile_id=?', (p['profile_id'],))]
            measured = [controls_by_toxin[c['toxin_id']] for c in components
                        if c['toxin_id'] in controls_by_toxin and c['value_status'] in ('reported_positive', 'reported_zero')]
            suspect = [{'toxin_id': toxin_id, 'reason': reason} for (pid, toxin_id), reason in uncertain.items()
                       if pid == p['profile_id']]
            issues = [dict(r) for r in conn.execute(
                'SELECT code,severity,detail FROM review_queue WHERE profile_id=? AND severity=?',
                (p['profile_id'], 'blocking'))]
            location = p.get('location')
            entry = {'profile_id': p['profile_id'], 'source_row': p['source_row'],
                     'measurement_type': p['measurement_type'], 'ingestion_status': p['ingestion_status'],
                     'location': location, 'location_known': bool(location and location.strip().lower() not in ('unknown', 'not reported', 'n/a')),
                     'taxonomy_status': p['taxonomy_status'], 'citation_status': p['citation_status'],
                     'reported_control_ids': measured, 'reported_control_count': len(measured),
                     'missing_control_ids': [c['id'] for c in controls if c['id'] not in measured],
                     'component_sum_pct': p['component_sum_pct'], 'blocking_issues': issues,
                     'uncertain_categories': suspect,
                     'source_review_warnings': [warnings[p['profile_id']]] if p['profile_id'] in warnings else []}
            by_name.setdefault(p['species_name'], []).append(entry)
    species = []
    for preset in presets:
        name = preset['source_species_name']
        rows = by_name.get(name, [])
        ready = [p for p in rows if p['measurement_type'] == 'proteomics' and p['ingestion_status'] == 'ready_with_caveats']
        species.append({'source_species_name': name, 'preset_id': preset['preset_id'],
                        'common_name': preset.get('common_name'), 'profile_count': len(rows),
                        'eligible_proteomic_profile_count': len(ready),
                        'eligible_proteomic_profiles_with_location': sum(p['location_known'] for p in ready),
                        'highest_reported_control_count': max((p['reported_control_count'] for p in ready), default=0),
                        'has_blocked_profile': any(p['ingestion_status'] == 'needs_review' for p in rows),
                        'has_known_category_issue': any(p['uncertain_categories'] for p in rows),
                        'profiles': rows})
    names = [s['source_species_name'] for s in species]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate rendering source labels require reconciliation')
    counts = Counter()
    counts['rendering_preset_source_labels'] = len(species)
    counts['labels_with_eligible_proteomics'] = sum(s['eligible_proteomic_profile_count'] > 0 for s in species)
    counts['labels_without_eligible_proteomics'] = sum(s['eligible_proteomic_profile_count'] == 0 for s in species)
    counts['labels_with_eligible_profile_and_known_location'] = sum(s['eligible_proteomic_profiles_with_location'] > 0 for s in species)
    counts['labels_with_blocked_profile'] = sum(s['has_blocked_profile'] for s in species)
    counts['labels_with_known_category_issue'] = sum(s['has_known_category_issue'] for s in species)
    counts['profiles_linked_to_presets'] = sum(s['profile_count'] for s in species)
    counts['eligible_proteomic_profiles'] = sum(s['eligible_proteomic_profile_count'] for s in species)
    counts['profiles_with_dataset_level_citation_only'] = sum(p['citation_status'] == 'dataset_level_only' for s in species for p in s['profiles'])
    counts['profiles_with_unreconciled_source_taxonomy'] = sum(p['taxonomy_status'] == 'unreconciled_source_label' for s in species for p in s['profiles'])
    counts['profiles_with_source_review_warnings'] = sum(bool(p['source_review_warnings']) for s in species for p in s['profiles'])
    return {'status': 'structural_inventory_not_scientific_validation',
            'scope': 'All rendering source labels. Names are source labels, not necessarily distinct currently accepted species.',
            'limitations': ['A ready_with_caveats row has passed ingestion checks, not source, taxonomy or biological accuracy review.',
                'Reported means a source value exists, including explicit zero; missing is not zero or proof of toxin absence.',
                'The 12 controls are a subset of source categories. A high count does not prove completeness or quality.',
                'Profiles and images are associated at species-label level, not known to be the same specimen.',
                'This audit does not search for newer studies or infer specimen-level phenotype from venom.'],
            'inputs': {'database_sha256': digest(db), 'presets_sha256': digest(PRESETS), 'controls_sha256': digest(SPEC), 'flags_sha256': digest(FLAGS)},
            'summary': dict(counts), 'species': species}


def write_report(result):
    s = result['summary']
    no_protein = [x['source_species_name'] for x in result['species'] if not x['eligible_proteomic_profile_count']]
    lines = ['# Venom profile inventory', '',
             'This is a structural inventory, not confirmation of biological accuracy. Source labels may be synonyms or subspecies, and image links are not specimen-matched.', '',
             f"- Rendering source labels: **{s['rendering_preset_source_labels']}**.",
             f"- Labels with at least one structurally eligible proteomics profile: **{s['labels_with_eligible_proteomics']}**; without one: **{s['labels_without_eligible_proteomics']}**.",
             f"- Labels with at least one eligible profile and a recorded location: **{s['labels_with_eligible_profile_and_known_location']}**.",
             f"- Profiles linked to presets: **{s['profiles_linked_to_presets']}**, including **{s['eligible_proteomic_profiles']}** structurally eligible proteomics rows.",
             f"- Profiles tagged as dataset-level citation only: **{s['profiles_with_dataset_level_citation_only']}**. Profiles with unreconciled source taxonomy: **{s['profiles_with_unreconciled_source_taxonomy']}**.",
             f"- Labels with at least one held profile: **{s['labels_with_blocked_profile']}**. Known specific category issue: **{s['labels_with_known_category_issue']}** label (black mamba NP).", '',
             'A boomslang transcriptomic row has a possible sample-location mismatch with its candidate primary study; see the detailed audit and [pilot source review](research_updates/pilot_five_species_review.md).', '',
             '## Labels without an eligible measured-protein profile', '',
             'These may have transcriptomic, unknown or held records. They are not necessarily unstudied in the wider literature.', '']
    lines += [f'- *{name}*' for name in no_protein]
    lines += ['', '## How to use this inventory', '',
              'The [machine-readable audit](venom_profile_audit.json) lists each preset and its profiles, measured versus missing UI controls, source rows, locations and blocking issues. Counted controls reflect reporting, not biological completeness; blanks remain unknown. “Structurally eligible” is not scientific verification.', '',
              'Research the primary literature, reconcile current taxonomy and source names, record sample origins and methods, and resolve conflicts per sample. Add a newer sample as a separate profile rather than merging values across different animals or experiments. Document revisions and retain original measurements. No venom profile here is validated as predicting a photographed snake’s appearance.', '',
              'Initial research on two missing-profile labels is recorded in [missing-profile candidates](research_updates/missing_profile_candidates.json). These leads are incomplete and are not ingested or approved for training.', '']
    REPORT.write_text('\n'.join(lines))


def main():
    presets = json.loads(PRESETS.read_text())['presets']
    controls = json.loads(SPEC.read_text())['controls']
    result = audit(DB, presets, controls)
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    write_report(result)
    print(json.dumps(result['summary'], indent=2))


if __name__ == '__main__':
    main()

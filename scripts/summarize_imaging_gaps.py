"""Summarize acquisition priorities; metadata coverage is not image-quality review."""
import csv
from collections import defaultdict, Counter
import json
from pathlib import Path
from check_priority_image_availability import ALIASES

ROOT = Path(__file__).resolve().parents[1]

def main():
    folder = ROOT / 'reports/image_research'
    audit = json.loads((folder / 'coverage_audit.json').read_text())
    availability = json.loads((folder / 'priority_availability.json').read_text())
    checked = {r['source_name']: r for r in availability['results']}
    images = defaultdict(set)
    observations = defaultdict(set)
    for path in sorted((ROOT / 'sources/image_research').glob('SnakeCLEF*.csv')):
        provider = 'herpmapper' if '-HM.' in path.name else 'inaturalist'
        with path.open(newline='', encoding='utf-8-sig') as stream:
            for row in csv.DictReader(stream):
                name = ' '.join(row['binomial_name'].replace('_', ' ').split())
                images[name].add((provider, row['image_path']))
                observations[name].add((provider, row['observation_id']))
    records = []
    for item in audit['eligible_proteomic_profiles']['taxa']:
        name = item['venom_name']
        lookup, reference = ALIASES.get(name, (name, None))
        paths = images[name] | images[lookup]
        obs = observations[name] | observations[lookup]
        category = 'no_metadata_match' if not paths else 'sparse_metadata' if len(paths) < 30 else 'candidate_pool'
        record = dict(source_name=name, image_lookup_name=lookup,
                      alias_reference=reference, snakeclef_image_records=len(paths),
                      snakeclef_observations=len(obs), acquisition_status=category,
                      visual_quality='not_reviewed')
        if name in checked:
            record['inaturalist_check'] = checked[name]
        records.append(record)
    assert len(records) == 149 and len({r['source_name'] for r in records}) == 149
    totals = dict(Counter(r['acquisition_status'] for r in records))
    output = dict(research_date='2026-11-18', scope='149 source labels in eligible proteomic profiles; not every venomous snake',
                  status_counts=totals, sparse_threshold=30,
                  threshold_note='Acquisition triage only, not a validated minimum training-set size.',
                  limitations=[
                      'No photographs downloaded or visually reviewed; no species certified as reliably imaged.',
                      'SnakeCLEF paths are metadata references, not verified usable or licensed images.',
                      'iNaturalist counts are research-grade observations with a CC0/CC BY photo, not image counts.',
                      'iNaturalist and SnakeCLEF overlap; counts must not be added.',
                      'Aliases are provider lookup crosswalks; original venom names remain unchanged.',
                      'Taxonomy and specimen identity need further review, especially historical species complexes.'
                  ], taxa=records)
    (folder / 'imaging_gaps.json').write_text(json.dumps(output, indent=2) + '\n')
    lines = [
        '# 2D image acquisition gaps', '', 'Checked November 18, 2026.', '',
        'Scope: 149 distinct source-name labels in the current eligible proteomic profiles. This does not cover all venomous snakes or every planned family.', '',
        f"After seven documented name crosswalks: **{totals['no_metadata_match']} labels have no SnakeCLEF metadata match**, **{totals['sparse_metadata']} have 1–29 referenced images**, and **{totals['candidate_pool']} have at least 30**.", '',
        'These are acquisition priorities, not photo-quality verdicts. No images have been downloaded or visually reviewed. The cutoff of 30 is a triage choice, not a training requirement.', '',
        'SnakeCLEF counts refer to distinct provider/path metadata keys. iNaturalist counts below refer to research-grade observations with at least one CC0/CC BY photo, not photographs. The sources overlap and their counts must not be added. Zero means no result under that filter, not no photograph anywhere online.', '',
        'Sources: [official SnakeCLEF page](https://www.imageclef.org/node/319), [pinned metadata mirror](https://huggingface.co/pengdadaaa/SnakeCLEF2024/tree/786f6a6a17453a8686d1cb9af7407525292d0d7c/metadata), [iNaturalist developer resources](https://www.inaturalist.org/pages/developers). Query URLs and timestamps are retained in the local source cache.', ''
    ]
    for category, title in [('no_metadata_match', 'No SnakeCLEF metadata match'), ('sparse_metadata', 'Sparse SnakeCLEF metadata: 1–29 images')]:
        lines += ['## ' + title, '', '| Venom source label | Image lookup name | SnakeCLEF image records | iNaturalist licensed observations |', '|---|---|---:|---:|']
        for r in records:
            if r['acquisition_status'] != category: continue
            check = r.get('inaturalist_check', {})
            count = check.get('research_grade_observations_with_cc0_or_ccby_photo')
            value = f"[{count}]({check['provider_query_url']})" if count is not None else 'Taxon unresolved / not counted'
            lines += [f"| {r['source_name']} | {r['image_lookup_name']} | {r['snakeclef_image_records']} | {value} |"]
        lines += ['']
    lines += ['## Name crosswalks', '', 'These crosswalks guide image searches and do not edit the venom data. Provider naming can differ; iNaturalist currently returns Gloydius brevicaudus while the SnakeCLEF mirror uses Gloydius brevicauda.', '', '| Source label | Alternative image label | SnakeCLEF image records | Authority |', '|---|---|---:|---|']
    for r in records:
        if r['alias_reference']:
            lines += [f"| {r['source_name']} | {r['image_lookup_name']} | {r['snakeclef_image_records']} | [Reference]({r['alias_reference']}) |"]
    lines += ['', '## Next acquisition pass', '',
              '1. Start with a small pilot from the candidate pools, reviewing full-body visibility, head detail, markings, dimensions, license and attribution.',
              '2. For gaps, search documented provider exports, museum collections and author-contributed photographs; retain source URLs and photo-level permissions when collecting from websites.',
              '3. Review Bothrops colombiensis separately: the provider search returns Bothrops atrox, which is not automatically accepted as a substitute.',
              '4. Keep all photos of one observation or known individual together, detect duplicate content, and annotate framing, view and pose separately.', '',
              'Full per-label audit: `imaging_gaps.json`. Focused provider checks: `priority_availability.json`. No ML training was performed.', '']
    (folder / 'imaging_gaps.md').write_text('\n'.join(lines))
    print(json.dumps(totals, indent=2))

if __name__ == '__main__':
    main()

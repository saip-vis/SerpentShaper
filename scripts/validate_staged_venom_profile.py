"""Check structural invariants for a separately staged figure-level venom profile.

Passing validation does not certify a source, mapping, measurement or fitness for training.
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate(record):
    errors = []
    for field in ('record_id', 'status', 'species', 'source', 'sample', 'measurement', 'completeness'):
        if not record.get(field):
            errors.append(f'{field} is required')
    if record.get('training_eligible') is not False:
        errors.append('staged record must be explicitly excluded from training')
    source = record.get('source') or {}
    for field in ('doi', 'url', 'publication_date'):
        if not source.get(field):
            errors.append(f'source.{field} is required')
    sample = record.get('sample') or {}
    if sample.get('individuals_paired_with_project_images') is not False:
        errors.append('specimen pairing must be explicitly marked false')
    if 'specimen_count' not in sample:
        errors.append('sample.specimen_count must be stated or null')
    entries = record.get('reported_values', []) + record.get('reported_aggregate_categories', [])
    if not entries:
        errors.append('at least one reported figure category is required')
    names = set()
    total = 0.0
    for item in entries:
        name = item.get('source_label')
        if not name or name in names:
            errors.append('source labels must be present and unique')
        names.add(name)
        value = item.get('percentage')
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 100:
            errors.append(f'invalid percentage for {name}')
        else:
            total += value
    expected = (record.get('measurement') or {}).get('complete_figure_group_total_pct')
    if expected is not None:
        if isinstance(expected, bool) or not isinstance(expected, (int, float)) or not math.isfinite(expected) or abs(total - expected) > 0.05:
            errors.append('reported figure groups do not match the stated total within rounding tolerance')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', type=Path,
                        default=ROOT / 'ML/research_updates/black_mamba_2025.json')
    args = parser.parse_args()
    result = validate(json.loads(args.path.read_text()))
    if result:
        raise SystemExit('\n'.join(result))
    print('Structural checks passed. Scientific review and explicit approval are still required.')


if __name__ == '__main__':
    main()

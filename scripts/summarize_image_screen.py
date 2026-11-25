"""Validate and summarize the 2026 assistant contact-sheet screening.

This report prioritizes further review. It never changes manifest decisions or
turns a thumbnail-screen candidate into a training example.
"""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / 'ML/image_traits/assistant_catalog_screen_2026.json'
REPORT = ROOT / 'reports/image_research/catalog_photo_screen_2026.md'


def summarize(root=ROOT):
    screen = json.loads((root / 'ML/image_traits/assistant_catalog_screen_2026.json').read_text())
    records = screen['records']
    if screen['reviewed_count'] != len(records) or len(records) != screen['total_planned']:
        raise ValueError('Screen is incomplete or its record count is inconsistent')
    counts, species, ids = Counter(), defaultdict(Counter), set()
    manifests = {}
    for record in records:
        image_id = record['image_id']
        if image_id in ids:
            raise ValueError(f'duplicate image id: {image_id}')
        ids.add(image_id)
        manifest_path = (root / record['manifest']).resolve()
        if not manifest_path.is_relative_to((root / 'data/image_pilots').resolve()):
            raise ValueError(f'unsafe manifest path: {image_id}')
        if manifest_path not in manifests:
            manifests[manifest_path] = {p['image_id']: p for p in json.loads(manifest_path.read_text())}
        photo = manifests[manifest_path].get(image_id)
        if not photo or photo.get('sha256') != record['sha256']:
            raise ValueError(f'missing or mismatched manifest: {image_id}')
        category = record['screening_status']
        if category not in {'visual_candidate', 'hold', 'duplicate', 'reject_damage', 'reject_not_live_animal'}:
            raise ValueError(f'unknown category: {image_id}')
        if record.get('training_eligible') is not False:
            raise ValueError(f'screen cannot approve training: {image_id}')
        if category in {'reject_damage', 'reject_not_live_animal'}:
            if photo.get('review_status') != 'rejected' or photo.get('rendering_training_excluded') is not True:
                raise ValueError(f'rejection is not recorded in manifest: {image_id}')
        counts[category] += 1
        species[record['species']][category] += 1
    return counts, species


def main():
    counts, species = summarize()
    screen = json.loads(SCREEN.read_text())
    current_status = Counter()
    for manifest in {r['manifest'] for r in screen['records']}:
        screen_ids = {r['image_id'] for r in screen['records'] if r['manifest'] == manifest}
        for photo in json.loads((ROOT / manifest).read_text()):
            if photo.get('image_id') in screen_ids:
                current_status[photo.get('review_status', 'unreviewed')] += 1
    lines = [
        '# 2026 follow-up photo screen', '',
        f"A first-pass contact-sheet screen covers {sum(counts.values())} downloaded photos under {len(species)} source species labels.",
        'This is triage, not a full-resolution review of every photo or independent species identification.', '',
        f"- Visually promising for at least one feature: **{counts['visual_candidate']}**. They still need image-level identity, condition, framing and license review.",
        f"- Held because the thumbnail does not give enough usable information: **{counts['hold']}**.",
        f"- Held as an exact-content duplicate: **{counts['duplicate']}**.",
        f"- Rejected after inspection of the original for clear damage or remains: **{counts['reject_damage']}**.",
        f"- Rejected after inspection of the original because it shows only shed skin: **{counts['reject_not_live_animal']}**.", '',
        f"The candidate and hold labels are original screening priorities, not acceptance decisions. Current manifest statuses are {dict(sorted(current_status.items()))}. Some candidates received separate full-size reviews and were later accepted; check the manifests for the current decisions. Rejected photos remain on disk with provenance and review history and are excluded from training.", '',
        'The per-photo decisions and source links are in `ML/image_traits/assistant_catalog_screen_2026.json`. The separate `assistant_shortlist_screen_2026.json` includes 32 prioritized photos, some from older batches; its candidates overlap this catalog and should not be added to these totals.', '',
        '| Source label | Candidate | Hold | Duplicate | Rejected |', '| --- | ---: | ---: | ---: | ---: |',
    ]
    for name, c in sorted(species.items()):
        lines.append(f"| {name} | {c['visual_candidate']} | {c['hold']} | {c['duplicate']} | {c['reject_damage'] + c['reject_not_live_animal']} |")
    lines += ['', 'The species names are source labels and may need taxonomic reconciliation. Photos and venom samples are not known to be from the same individuals.', '']
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines))
    print(f'{sum(counts.values())} screened records validated; report: {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()

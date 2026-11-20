"""Audit downloaded image integrity, quarantine, and exact duplicate records."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from PIL import Image
from export_rendering_manifest import eligible

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/image_research/remaining_species_downloads'

def main():
    plan = json.loads((REPORT / 'plan.json').read_text())
    progress = json.loads((REPORT / 'progress.json').read_text())
    expected = {j['species']: j for j in plan['jobs']}
    assert len(expected) == 140 and set(expected) == set(progress['species'])
    hashes, photos, taxa = defaultdict(list), defaultdict(list), defaultdict(set)
    downloaded_labels, new_labels = set(), set()
    new_rows, new_files, all_files, sizes = [], set(), set(), {}
    small, inconsistencies, gallery_errors, large = [], [], [], []
    for manifest in sorted((ROOT / 'data/image_pilots').glob('pilot_*/manifest.json')):
        rows = json.loads(manifest.read_text())
        names = {r['source_species_name'] for r in rows}
        assert len(names) <= 1, manifest
        is_new = int(manifest.parent.name.split('_')[1]) >= 10
        if is_new:
            job = next(j for j in expected.values() if j['batch'] == manifest.parent.name)
            assert names <= {job['species']}
            assert len(rows) <= 10
            if progress['species'][job['species']].get('review_gallery') == 'failed':
                gallery_errors.append(job['species'])
        for row in rows:
            if row.get('download_status') != 'downloaded':
                continue
            path = (manifest.parent / row['local_path']).resolve()
            assert path.is_relative_to(manifest.parent.resolve()) and path.is_file(), path
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest == row['sha256'], path
            with Image.open(path) as image:
                width, height = image.size
            ref = dict(batch=manifest.parent.name, species=row['source_species_name'],
                       image_id=row['image_id'], review_id=row.get('review_id'),
                       local_path=str(path.relative_to(ROOT)))
            if min(width, height) < 512:
                small.append(dict(ref, actual_width=width, actual_height=height))
            if width * height > 80_000_000:
                large.append(dict(ref, actual_width=width, actual_height=height,
                                  note='Large original; plan bounded-resolution preprocessing before model ingestion.'))
            if sorted([width,height]) != sorted([row['original_width'],row['original_height']]):
                inconsistencies.append(dict(ref, actual_width=width, actual_height=height,
                                            reported_width=row['original_width'], reported_height=row['original_height']))
            hashes[digest].append(ref)
            photos[row['image_id']].append(ref)
            taxa[str(row['taxon_id'])].add(row['source_species_name'])
            downloaded_labels.add(row['source_species_name'])
            all_files.add(str(path))
            sizes[str(path)] = path.stat().st_size
            if is_new:
                if row['review_status'] == 'accepted':
                    assert eligible(row)
                    assert row.get('species_confidence') == 'confirmed'
                    assert row.get('body_condition') == 'no_visible_injury'
                else:
                    assert row.get('rendering_training_excluded') is True
                assert row['photo_license'] in {'cc0', 'cc-by'} and row.get('attribution')
                new_rows.append(row)
                new_labels.add(row['source_species_name'])
                new_files.add(str(path))
        if is_new:
            downloaded = [r for r in rows if r.get('download_status') == 'downloaded']
            counts = defaultdict(int)
            for row in downloaded:
                counts[row['observation_id']] += 1
            assert max(counts.values(), default=0) <= 2
    assert len(new_rows) == progress['downloaded']
    result = {
        'requested_labels': 140, 'attempted_labels': len(progress['species']),
        'new_labels_with_downloads': len(new_labels), 'new_downloaded_photo_records': len(new_rows),
        'new_file_paths': len(new_files), 'new_distinct_content_hashes': len({r['sha256'] for r in new_rows}),
        'new_accepted_for_rendering': sum(eligible(r) for r in new_rows),
        'new_bytes_on_disk': sum(sizes[p] for p in new_files),
        'all_labels_with_downloads': len(downloaded_labels), 'all_distinct_provider_taxa': len(taxa),
        'all_downloaded_photo_records': sum(len(group) for group in hashes.values()),
        'all_file_paths': len(all_files), 'all_distinct_content_hashes': len(hashes),
        'provider_taxa_with_multiple_source_labels': {k: sorted(v) for k,v in taxa.items() if len(v)>1},
        'cross_label_exact_duplicate_groups': {k: v for k,v in hashes.items() if len({r['species'] for r in v})>1},
        'repeated_photo_id_groups': {k: v for k,v in photos.items() if len(v)>1},
        'actual_resolution_shortfalls': small, 'dimension_metadata_mismatches': inconsistencies,
        'gallery_errors': gallery_errors, 'large_originals': large,
        'passed': not gallery_errors,
        'limitations': ['Source labels and provider taxa are not equivalent to independent biological species or specimens.',
                       'SHA-256 detects identical bytes, not similar crops or resized duplicates.',
                       'Rendering eligibility follows explicit review; unaccepted new records must remain excluded.']
    }
    (REPORT / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['cross_label_exact_duplicate_groups','repeated_photo_id_groups','dimension_metadata_mismatches']}, indent=2))
    if not result['passed']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()

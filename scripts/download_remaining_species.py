"""Resumable, bounded image collection for the remaining venom species labels.

At most 20 observation records and 10 candidate downloads per species. No training.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'reports/image_research/remaining_species_downloads'
IMAGES = ROOT / 'data/image_pilots'

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)

def plan():
    path = REPORT / 'plan.json'
    if path.exists():
        return json.loads(path.read_text())
    targets = json.loads((ROOT / 'reports/image_research/imaging_gaps.json').read_text())['taxa']
    initial = set()
    for manifest in IMAGES.glob('pilot_*/manifest.json'):
        if int(manifest.parent.name.split('_')[1]) <= 9:
            initial.update(r['source_species_name'] for r in json.loads(manifest.read_text()))
    remaining = [r for r in targets if r['source_name'] not in initial]
    assert len(initial) == 9 and len(remaining) == 140
    jobs = []
    for i, taxon in enumerate(remaining, 10):
        slug = re.sub('[^a-z0-9]+', '_', taxon['source_name'].lower()).strip('_')
        jobs.append({'species': taxon['source_name'], 'lookup_name': taxon['image_lookup_name'],
                     'batch': f'pilot_{i:03d}_{slug}'})
    value = {'created_at': now(), 'initial_species': sorted(initial), 'jobs': jobs,
             'limits': {'observations_per_species': 20, 'candidates_per_species': 10, 'max_per_observation': 2},
             'source': 'Bounded public iNaturalist metadata samples; not an exhaustive occurrence export.'}
    save(path, value)
    return value

def write_report(collection_plan, progress):
    records = progress['species']
    count = Counter(r['status'] for r in records.values())
    downloaded = sum(r.get('downloaded', 0) for r in records.values())
    lines = ['# Post-download notes: remaining species', '',
             f"Updated: {now()}", '',
             f"Attempted **{len(records)} of {len(collection_plan['jobs'])}** remaining species labels. Downloaded **{downloaded} candidate photo records** in these new batches (some can share identical image content).", '',
             '## Scope and interpretation', '',
             'One species per folder, continuing numbering after pilot 009. Each search examines at most 20 research-grade observation records and selects up to 10 CC0/CC BY photo candidates, preferring different observations and at most two photos per observation. Photos must have attribution and reported dimensions of at least 512 pixels in both directions. Requests are sequential and cached. Downloads are capped at 20 MB each.', '',
             'These are filtered availability samples, not an exhaustive internet search. A skip does not prove no photos exist elsewhere. Photo licensing is checked independently of observation licensing. Provider species labels remain provisional. Downloaded images are NOT visually screened for injury, documents, occlusion, or identity; all new records are held out of rendering training until review under the image policy.', '',
             '## Status counts', '', '| Status | Species labels |', '|---|---:|']
    lines += [f'| {key} | {value} |' for key, value in sorted(count.items())]
    verification_path = REPORT / 'verification.json'
    if verification_path.exists() and len(records) == len(collection_plan['jobs']):
        verification = json.loads(verification_path.read_text())
        if verification['new_downloaded_photo_records'] == downloaded:
            lines += ['', '## Final verification', '',
                f"{verification['new_labels_with_downloads']} source labels have new downloads. The {downloaded} downloaded records contain {verification['new_distinct_content_hashes']} distinct SHA-256 image contents and use {verification['new_bytes_on_disk']:,} bytes on disk.", '',
                f"File checksums, image paths, actual minimum dimensions, per-observation limits, gallery generation, and rendering quarantine were checked. New records currently accepted for rendering: {verification.get('new_accepted_for_rendering', 0)}.", '',
                'The source list includes Cryptelytrops purpureomaculatus and Trimeresurus purpureomaculatus, mapped to the same provider taxon. Their ten exact duplicate photo pairs are annotated; later copies have duplicate_of references and are excluded by the rendering exporter. Do not count these as independent species or specimens.', '',
                f"Original plus new batches cover {verification['all_labels_with_downloads']} source labels representing {verification['all_distinct_provider_taxa']} distinct provider taxon IDs. Provider IDs are not an expert taxonomic reconciliation.", '',
                'The initial missing-dimensions handling failure for Bothrops asper was corrected and successfully retried. The previous attempt is preserved in progress.json and the collection log. No request/download failures remain.'
            ]
            if verification.get('dimension_metadata_mismatches'):
                lines += ['', f"Provider-reported dimensions differed from the downloaded original for {len(verification['dimension_metadata_mismatches'])} record(s); both reported and measured dimensions are retained in verification.json and the manifest."]
            for item in verification.get('large_originals', []):
                lines += ['', f"Large-original preprocessing note: {item['batch']} / {item['image_id']} is {item['actual_width']} × {item['actual_height']} pixels. Preserve the original and create a bounded-resolution derivative before future model ingestion. No resizing or training was performed."]
    lines += ['', '## Skipped or failed species', '', '| Species label | Status | Reason |', '|---|---|---|']
    skipped = [r for r in records.values() if not r.get('downloaded')]
    for r in skipped:
        reason = r.get('notes', '').replace('|','/').replace('\n', ' ')
        lines.append(f"| {r['species']} | {r['status']} | {reason} |")
    if not skipped:
        lines.append('| None recorded so far | | |')
    lines += ['', '## All attempted species', '', '| Species label | Folder | Downloaded | Observation groups | Status | Notes |', '|---|---|---:|---:|---|---|']
    for job in collection_plan['jobs']:
        r = records.get(job['species'])
        if r is None:
            continue
        notes = r.get('notes', '').replace('|','/').replace('\n', ' ')
        lines.append(f"| {r['species']} | {r['batch']} | {r.get('downloaded', 0)} | {r.get('observation_groups', 0)} | {r['status']} | {notes} |")
    missing = [j['species'] for j in collection_plan['jobs'] if j['species'] not in records]
    if missing:
        lines += ['', '## Not attempted yet', '', ', '.join(missing)]
    (REPORT / 'post_download_notes.md').write_text('\n'.join(lines)+'\n')
    progress.update(updated_at=now(), attempted=len(records), downloaded=downloaded,
                    status_counts=dict(count), remaining=len(missing))
    save(REPORT / 'progress.json', progress)

def command(action, job, log):
    args = [sys.executable, str(ROOT / 'scripts/collect_image_pilot.py'), action,
            '--batch', job['batch'], '--limit', '10']
    if action == 'discover':
        args += ['--species', job['species'], '--observations', '20', '--max-per-observation', '2']
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    with log.open('a') as stream:
        stream.write(f'\n{now()} {action}\n{result.stdout}\n{result.stderr}\n')
    return result.returncode, result.stdout + result.stderr

def inspect_filters(folder):
    """Record inspected-photo counts, not a reason inferred from zero results alone."""
    observations = []
    for cache in (folder / 'api_cache').glob('*.json'):
        data = json.loads(cache.read_text())
        if '/v1/observations?' in data.get('request_url', ''):
            observations += data['data'].get('results', [])
    result = Counter()
    for obs in observations:
        for photo in obs.get('photos', []):
            result['photos_examined'] += 1
            if photo.get('license_code') not in {'cc0', 'cc-by'}:
                result['license_not_allowed'] += 1
            if not photo.get('attribution'):
                result['attribution_missing'] += 1
            dims = photo.get('original_dimensions') or {}
            if any(not isinstance(d, (int, float)) or isinstance(d, bool) or d < 512
                   for d in [dims.get('width'), dims.get('height')]):
                result['too_small_or_dimensions_missing'] += 1
            if photo.get('hidden') or photo.get('flags'):
                result['hidden_or_flagged'] += 1
    return dict(result)

def process(job):
    folder = IMAGES / job['batch']
    folder.mkdir(parents=True, exist_ok=True)
    record = dict(job, started_at=now(), downloaded=0)
    log = folder / 'collection.log'
    code, details = command('discover', job, log)
    if code:
        record.update(status='failed_metadata_request', notes=details[-1500:])
        return record
    result = json.loads((folder / 'discovery_summary.json').read_text())['results'][0]
    record['discovery'] = result
    if result['status'] == 'taxon_unresolved':
        record.update(status='skipped_taxon_unresolved', notes='No unique supported species-name match. Provider candidates: '+', '.join(result.get('candidates', [])))
        return record
    rows = json.loads((folder / 'manifest.json').read_text())
    record['photo_filter_diagnostics'] = inspect_filters(folder)
    record['selected'] = len(rows)
    if not rows:
        total = result.get('eligible_observations_available', 0)
        status = 'skipped_no_licensed_observations' if total == 0 else 'skipped_no_applicable_photos_in_sample'
        record.update(status=status, notes=f'{total} observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample.')
        return record
    code, details = command('download', job, log)
    # One bounded retry of failed files only, with checksum skipping of successes.
    if code and '429' not in details and '403' not in details:
        time.sleep(3)
        code, details = command('download', job, log)
    rows = json.loads((folder / 'manifest.json').read_text())
    errors = []
    sizes = 0
    groups = set()
    for row in rows:
        row.update(collection_batch=job['batch'], review_status='unreviewed',
                   rendering_training_excluded=True, rendering_exclusion_reason='pending_visual_review')
        if row.get('download_status') == 'downloaded':
            path = folder / row['local_path']
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != row['sha256']:
                row.update(download_status='failed', download_error='Post-download checksum mismatch')
            else:
                record['downloaded'] += 1
                sizes += len(content)
                groups.add(row['observation_id'])
        if row.get('download_status') == 'failed':
            errors.append(row['image_id']+': '+row.get('download_error','Unknown error'))
    save(folder / 'manifest.json', rows)
    record.update(download_errors=errors, observation_groups=len(groups), bytes_downloaded=sizes)
    if record['downloaded'] == 10:
        record.update(status='downloaded_target', notes='10 candidates downloaded; visual and species review pending.')
    elif record['downloaded']:
        record.update(status='downloaded_partial', notes=f"Only {record['downloaded']} of the target 10 candidates downloaded from this sample. "+'; '.join(errors))
    else:
        record.update(status='failed_all_downloads', notes='; '.join(errors) or details[-1500:])
    if record['downloaded']:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/build_image_review.py'), '--batch', job['batch']],
                                cwd=ROOT, capture_output=True, text=True)
        record['review_gallery'] = 'ready' if result.returncode == 0 else 'failed'
        if result.returncode:
            record['gallery_error'] = result.stderr[-1500:]
    record['finished_at'] = now()
    return record

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--retry-failures', action='store_true', help='Retry recorded non-access-denial failures once; preserve history')
    args = parser.parse_args()
    collection_plan = plan()
    progress_path = REPORT / 'progress.json'
    progress = json.loads(progress_path.read_text()) if progress_path.exists() else {'started_at': now(), 'species': {}}
    write_report(collection_plan, progress)
    if args.plan_only:
        print(f"Planned {len(collection_plan['jobs'])} remaining species.")
        return
    for index, job in enumerate(collection_plan['jobs'], 1):
        previous = progress['species'].get(job['species'])
        retry = (args.retry_failures and previous and previous['status'].startswith('failed')
                 and not any(code in previous.get('notes', '') for code in ['429', '403']))
        if previous and not retry:
            continue
        time.sleep(1.2)
        print(f"{'RETRY' if retry else 'START'} {index}/140 {job['species']}", flush=True)
        try:
            record = process(job)
        except Exception as exc:
            record = dict(job, status='failed_unexpected', downloaded=0, notes=f'{type(exc).__name__}: {exc}')
        if previous:
            record['previous_attempts'] = previous.get('previous_attempts', []) + [
                {k: v for k, v in previous.items() if k != 'previous_attempts'}]
        progress['species'][job['species']] = record
        write_report(collection_plan, progress)
        print(f"DONE {job['species']}: {record['status']}, {record['downloaded']} files; total {progress['downloaded']}", flush=True)
        # Respect throttling or access denials instead of continuing through a block.
        if '429' in record.get('notes','') or '403' in record.get('notes',''):
            print('Provider throttling/access denial: stopping; completed work and remaining list saved.', flush=True)
            raise SystemExit(2)
    print('All 140 target labels attempted. Reports saved.', flush=True)

if __name__ == '__main__':
    main()

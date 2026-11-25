"""Audit locally downloaded follow-up files and write readable collection notes."""
import hashlib
import json
from pathlib import Path

from collect_catalog_followup import ROOT, REPORT, TAXA, plan

OUT = ROOT/'reports/image_research/catalog_followup_2026_notes.md'
AUDIT = ROOT/'reports/image_research/catalog_followup_2026_audit.json'


def review_errors(photo):
    """Check the evolving review state without treating a download as approval."""
    status=photo.get('review_status')
    errors=[]
    if status in ('unreviewed', 'rejected', 'needs_review', 'reference_only'):
        if photo.get('rendering_training_excluded') is not True:errors.append('nonaccepted_photo_not_excluded')
        if status != 'unreviewed' and not photo.get('review_history'):errors.append('review_decision_missing_history')
    elif status == 'accepted':
        if (not photo.get('review_history') or photo.get('species_confidence') != 'confirmed'
                or photo.get('body_condition') != 'no_visible_injury'):
            errors.append('accepted_photo_missing_review_evidence')
    else:errors.append('unknown_review_status')
    return errors


def audit(report, root=ROOT):
    entries=plan(json.loads((root/'reports/image_research/imaging_gaps.json').read_text())['taxa'])
    known={name for _,name in entries}; rows=report['species']
    if len({x['species'] for x in rows})!=len(rows) or any(x['species'] not in known for x in rows):
        raise ValueError('Duplicate or unexpected report species')
    records=[];errors=[];content={};preexisting_species=set()
    for manifest in (root/'data/image_pilots').glob('pilot_*/manifest.json'):
        parts=manifest.parent.name.split('_')
        if len(parts)<2 or not parts[1].isdigit() or int(parts[1])>154:continue
        for photo in json.loads(manifest.read_text()):
            relative=photo.get('local_path')
            if photo.get('download_status')=='downloaded' and relative:
                path=(manifest.parent/relative).resolve()
                if path.is_relative_to(manifest.parent.resolve()) and path.is_file():preexisting_species.add(photo.get('source_species_name'))
    for entry in rows:
        folder=root/'data/image_pilots'/entry['folder'];manifest=folder/'manifest.json'
        if not manifest.exists():
            if entry.get('selected',0)>0:errors.append({'species':entry['species'],'error':'missing_manifest'})
            continue
        for photo in json.loads(manifest.read_text()):
            image_id=photo.get('image_id');error=[]
            if photo.get('source_species_name')!=entry['species']:error.append('source_species_mismatch')
            status=photo.get('review_status')
            error.extend(review_errors(photo))
            if not photo.get('attribution') or photo.get('photo_license') not in ('cc0','cc-by'):error.append('missing_rights_metadata')
            if not photo.get('observation_id') or not photo.get('photo_page'):error.append('missing_source_metadata')
            if photo.get('download_status')=='downloaded':
                path=(folder/photo.get('local_path','')).resolve()
                if not path.is_relative_to(folder.resolve()) or not path.is_file():error.append('missing_or_unsafe_file')
                elif hashlib.sha256(path.read_bytes()).hexdigest()!=photo.get('sha256'):error.append('hash_mismatch')
                if photo.get('sha256'):content.setdefault(photo['sha256'],[]).append(image_id)
            if error:errors.append({'species':entry['species'],'image_id':image_id,'errors':error})
            records.append({'species':entry['species'],'image_id':image_id,'download_status':photo.get('download_status'), 'review_status':status,
                            'download_error':photo.get('download_error'),'exclusion_reason':photo.get('rendering_exclusion_reason')})
    with_new={r['species'] for r in records if r['download_status']=='downloaded'}
    return {'status':report['status'],'planned_species':len(entries),'attempted_species':len(rows),
            'downloaded_photos':sum(r['download_status']=='downloaded' for r in records),
            'review_status_counts':{status:sum(r['download_status']=='downloaded' and r['review_status']==status for r in records)
                                    for status in sorted({r['review_status'] for r in records if r['review_status']})},
            'species_with_downloads':sum(x.get('downloaded',0)>0 for x in rows),
            'zero_result_species':[x['species'] for x in rows if x.get('status')=='completed' and x.get('selected')==0],
            'failed_species':[x for x in rows if x.get('status') not in ('completed',)],
            'failed_downloads':[r for r in records if r['download_status']=='failed'],
            'unattempted_species':[name for _,name in entries if name not in {x['species'] for x in rows}],
            'species_without_any_local_downloaded_files':[name for _,name in entries if name not in preexisting_species|with_new],
            'duplicate_content_groups':[ids for ids in content.values() if len(ids)>1],
            'duplicate_flagged_photos':sum(r['exclusion_reason']=='duplicate_content_pending_review' for r in records),
            'errors':errors}


def main():
    report=json.loads(REPORT.read_text());result=audit(report)
    AUDIT.write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Additional catalog-wide image collection','',
       f"Status: **{result['status']}**. Attempted {result['attempted_species']} of {result['planned_species']} source labels; downloaded {result['downloaded_photos']} photos across {result['species_with_downloads']} labels.",
       '', 'These are bounded iNaturalist searches, not exhaustive searches. New photos initially remained excluded from training; subsequent decisions and exclusions are recorded in their manifests. Research-grade labels are provider identifications, not independent verification; recorded license codes and attributions require checking for intended reuse.',
       '', f"Current downloaded photo review statuses: {result['review_status_counts']}.",
       '', f"Files flagged as duplicate content: {result['duplicate_flagged_photos']}. File/provenance audit issues: {len(result['errors'])}.",
       '', '## No new candidates in sampled results','']
    lines += [f'- {name}' for name in result['zero_result_species']] or ['- None recorded.']
    lines += ['', '## Unresolved names or request failures','']
    lines += [f"- {x['species']}: {x.get('error',x['status'])}" for x in result['failed_species']] or ['- None recorded.']
    lines += ['', '## Individual photo download failures','']
    lines += [f"- {x['species']} ({x['image_id']}): {x.get('download_error') or 'unknown error'}" for x in result['failed_downloads']] or ['- None recorded.']
    lines += ['', '## Not yet attempted','']
    lines += [f'- {name}' for name in result['unattempted_species']] or ['- None.']
    lines += ['', '## No downloaded local image files in earlier batches or this run','',
              'This is a file-availability check, not a quality, species-identification or training-suitability review.']
    lines += [f'- {name}' for name in result['species_without_any_local_downloaded_files']] or ['- None.']
    lines += ['', 'Each batch folder contains its own manifest and bounded-search summary. See the companion JSON report and audit for complete details.', '']
    OUT.write_text('\n'.join(lines))
    print(json.dumps({k:v for k,v in result.items() if k not in {'zero_result_species','failed_species','failed_downloads','unattempted_species','species_without_any_local_downloaded_files','duplicate_content_groups','errors'}},indent=2))
    print('zero-result:',len(result['zero_result_species']),'failed species:',len(result['failed_species']), 'failed photos:',len(result['failed_downloads']),'not attempted:',len(result['unattempted_species']), 'no local files:',len(result['species_without_any_local_downloaded_files']),'audit errors:',len(result['errors']))
    if result['errors']:raise SystemExit(1)


if __name__=='__main__':main()

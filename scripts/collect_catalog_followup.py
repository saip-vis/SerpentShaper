"""Collect a bounded, resumable follow-up across the 149 source labels.

Uses the existing cautious iNaturalist collector and never approves images.
One photo per previously unseen observation; metadata and decisions remain in
separate per-species folders. A sampled search is not proof of absence.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError

import collect_pilot_followup as followup
from collect_image_pilot import ROOT, now, save

REPORT = ROOT / 'reports/image_research/catalog_followup_2026.json'
TAXA = ROOT / 'reports/image_research/imaging_gaps.json'


def plan(taxa):
    names = [entry['source_name'] for entry in taxa]
    if len(names) != len(set(names)):
        raise ValueError('Source labels must be unique')
    return [(f"pilot_{155+i:03d}_extra_{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}", name)
            for i, name in enumerate(names)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--per-species', type=int, default=8, choices=range(1, 13))
    parser.add_argument('--max-species', type=int, default=None)
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--retry-failed-downloads', action='store_true', help='Retry failed photo downloads once; does not bypass provider limits')
    args = parser.parse_args()
    entries = plan(json.loads(TAXA.read_text())['taxa'])
    if args.plan_only:
        print(json.dumps({'source_labels':len(entries), 'limit_each':args.per_species,
                          'maximum_images':len(entries)*args.per_species, 'first':entries[0], 'last':entries[-1]}))
        return
    followup.PER_SPECIES = args.per_species
    # Preserve progress on interrupted runs; completed folders are also resumable.
    report = json.loads(REPORT.read_text()) if REPORT.exists() else {'created_at':now(), 'species':[]}
    if report.get('per_species', args.per_species) != args.per_species:
        raise ValueError('Use the same per-species limit when resuming this report')
    by_name = {r['species']:r for r in report['species']}
    report.update(status='in_progress', per_species=args.per_species, total_source_labels=len(entries),
                  source='iNaturalist research-grade observations; CC0/CC BY metadata; provider identity unverified',
                  limit_note='At most one new photo per previously unseen observation; bounded recent sample, not proof of global absence.',
                  review_note='All new records remain unreviewed and excluded from rendering and training pending review.')
    failures = 0
    for folder, name in entries[:args.max_species]:
        prior=by_name.get(name, {})
        if prior.get('status') == 'completed' and not (args.retry_failed_downloads and prior.get('failures',0)>0):
            continue
        try:
            result = followup.collect(folder, name)
            result['status'] = 'completed'
            failures = 0
        except HTTPError as exc:
            result = {'species':name, 'folder':folder, 'status':'provider_error', 'error':f'HTTP {exc.code}'}
            by_name[name]=result
            report.update(species=[by_name[n] for _, n in entries if n in by_name], updated_at=now())
            save(REPORT,report)
            print(json.dumps(result),flush=True)
            if exc.code in (403,429):
                report['status']='stopped_provider_limit';save(REPORT,report);return
        except Exception as exc:
            result={'species':name, 'folder':folder, 'status':'failed', 'error':f'{type(exc).__name__}: {exc}'}
            failures = failures+1 if isinstance(exc, (URLError, TimeoutError, ConnectionError)) else 0
            if failures>=3:report['status']='stopped_connection_errors'
        by_name[name]=result
        report.update(species=[by_name[n] for _, n in entries if n in by_name], updated_at=now())
        save(REPORT,report)
        print(json.dumps(result),flush=True)
        if report['status']=='stopped_connection_errors':return
    has_gaps=any(r.get('status')!='completed' or r.get('failures',0)>0 or r.get('selected',0)==0 for r in by_name.values())
    report['status']=('completed_with_gaps' if has_gaps else 'completed') if len(by_name)==len(entries) else 'partial'
    report['updated_at']=now();save(REPORT,report)


if __name__=='__main__':main()

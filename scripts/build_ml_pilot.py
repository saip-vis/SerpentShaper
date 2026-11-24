"""Audit provenance and prepare an explicitly unsplit ML pilot manifest.

The manifest links collections at source-species level, never at specimen level.
It does not accept images or train a model.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

from build_species_catalog import ROOT, build

PILOT_NAMES = ('Naja naja', 'Oxyuranus scutellatus', 'Dendroaspis polylepis',
               'Crotalus atrox', 'Dispholidus typus')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def image_record(image, root):
    """Preserve the existing review gate; never infer acceptance from a label."""
    path = image.get('local_path')
    actual = (root / path).resolve() if path else None
    present = bool(actual and actual.is_relative_to(root.resolve()) and actual.is_file())
    photo_hash = digest(actual) if present else None
    hash_verified = bool(photo_hash and image.get('sha256') and photo_hash == image['sha256'])
    license_code = image.get('photo_license')
    license_recorded = license_code in ('cc0', 'cc-by')
    attribution_recorded = bool(image.get('attribution'))
    group = image.get('split_group')
    eligible = bool(image.get('rendering_eligible') and image.get('review_status') == 'accepted'
                    and not image.get('rendering_training_excluded') and not image.get('reference_only_exception')
                    and not image.get('duplicate_of')
                    and image.get('suitability_screening', {}).get('category') not in {'rejected', 'supplemental'}
                    and present and hash_verified and license_recorded and attribution_recorded and group)
    reasons = []
    if not image.get('rendering_eligible') or image.get('review_status') != 'accepted':
        reasons.append('not_accepted_by_existing_rendering_gate')
    if image.get('rendering_training_excluded') or image.get('reference_only_exception') or image.get('duplicate_of') or image.get('suitability_screening', {}).get('category') in {'rejected', 'supplemental'}:
        reasons.append('excluded_or_reference_only')
    if not present:
        reasons.append('file_unavailable')
    elif not hash_verified:
        reasons.append('checksum_missing_or_mismatch')
    if not license_recorded:
        reasons.append('license_not_cc0_or_cc_by_in_metadata')
    if not attribution_recorded:
        reasons.append('attribution_missing')
    if not group:
        reasons.append('observation_group_missing')
    return {
        'image_id': image.get('image_id'), 'observation_id': image.get('observation_id'),
        'split_group': group, 'sha256': image.get('sha256'), 'hash_verified': hash_verified,
        'file_available': present, 'local_path': path, 'manifest_path': image.get('manifest_path'),
        'source_page': image.get('source_page'), 'photo_page': image.get('photo_page'),
        'provider_species_name': image.get('provider_species_name'),
        'species_link_status': image.get('species_link_status'),
        'review_status': image.get('review_status'), 'rendering_eligible': bool(image.get('rendering_eligible')),
        'photo_license': license_code, 'license_version': image.get('license_version'),
        'license_reference': image.get('license_reference'), 'attribution': image.get('attribution'),
        'eligible_for_pilot_after_metadata_checks': eligible,
        'excluded_reasons': reasons, 'split': None,
    }


def build_audit(catalog, root):
    profiles = {p['profile_id']: p for p in catalog['profiles']}
    all_records = []
    species_rows = []
    by_name = {}
    for s in catalog['species']:
        ready = [profiles[pid] for pid in s['venom_profile_ids']
                 if profiles[pid]['measurement_type'] == 'proteomics'
                 and profiles[pid]['ingestion_status'] == 'ready_with_caveats']
        imgs = [image_record(i, root) for i in s['images']]
        # Do not mark cross-taxon content duplicated as independent evidence.
        all_records.extend(imgs)
        eligible = [i for i in imgs if i['eligible_for_pilot_after_metadata_checks']]
        row = {'species_id': s['species_id'], 'source_species_name': s['source_species_name'],
               'taxonomy_status': s['taxonomy_status'], 'alias_reference': s.get('alias_reference'),
               'shared_provider_taxa_with': s.get('shared_provider_taxa_with', []),
               'ready_proteomic_profiles': len(ready),
               'all_profile_count': len(s['venom_profile_ids']), 'image_records': len(imgs),
               'available_images': sum(i['file_available'] for i in imgs),
               'accepted_and_metadata_checked_images': len(eligible),
               'accepted_unique_observations': len({i['split_group'] for i in eligible}),
               'unreviewed_images': sum(i['review_status'] == 'unreviewed' for i in imgs),
               'rejected_images': sum(i['review_status'] == 'rejected' for i in imgs),
               'license_versions_missing': sum(i['file_available'] and not i['license_version'] for i in imgs)}
        species_rows.append(row)
        by_name[s['source_species_name']] = (s, ready, imgs, row)
    hashes = Counter(i['sha256'] for i in all_records if i['sha256'])
    counts = {'catalog_source_labels': len(species_rows),
              'structurally_eligible_proteomic_profiles': sum(r['ready_proteomic_profiles'] for r in species_rows),
              'labels_with_ready_proteomics_and_available_images': sum(bool(r['ready_proteomic_profiles'] and r['available_images']) for r in species_rows),
              'labels_with_ready_proteomics_and_accepted_images': sum(bool(r['ready_proteomic_profiles'] and r['accepted_and_metadata_checked_images']) for r in species_rows),
              'available_image_records': sum(i['file_available'] for i in all_records),
              'distinct_available_image_hashes': len({i['sha256'] for i in all_records if i['file_available'] and i['sha256']}),
              'accepted_and_metadata_checked_images': sum(i['eligible_for_pilot_after_metadata_checks'] for i in all_records),
              'unreviewed_image_records': sum(i['review_status'] == 'unreviewed' for i in all_records),
              'rejected_image_records': sum(i['review_status'] == 'rejected' for i in all_records),
              'available_images_without_license_version': sum(i['file_available'] and not i['license_version'] for i in all_records),
              'repeated_hash_groups': sum(n > 1 for n in hashes.values())}
    pilot = []
    for name in PILOT_NAMES:
        if name not in by_name:
            raise ValueError(f'Pilot source label is missing: {name}')
        s, ready, imgs, row = by_name[name]
        pilot.append({**row, 'profiles': [{'profile_id': p['profile_id'],
            'measurement_type': p['measurement_type'], 'source_row': p['source_row'],
            'location': p['location'], 'citation_status': p['citation_status'],
            'component_sum_pct': p['component_sum_pct']} for p in ready],
            'images': imgs, 'link_scope': 'source species name only; not the same sampled specimen',
            'training_split': None})
    return {'summary': counts, 'species': species_rows}, pilot


def main():
    root = ROOT.resolve()
    catalog = build(root)
    audit, pilot = build_audit(catalog, root)
    source = root / 'data/processed/venom_diet_2023/serpentshaper.sqlite'
    manifest = {'schema_version': 1, 'status': 'audit_pilot_not_ready_for_training',
      'database_sha256': digest(source), 'image_review_policy': 'config/image_review_policy.json',
      'link_scope': 'species-level associations only; no individual-level venom-to-photo pairs',
      'warning': 'No samples are assigned to training or evaluation. License codes and attributions are metadata checks, not legal clearance.',
      'pilot_species': pilot}
    out = root / 'ML'
    out.mkdir(exist_ok=True)
    (out / 'data_audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False)+'\n')
    (out / 'pilot_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    print(json.dumps(audit['summary'], indent=2))
    for s in pilot:
        print(f"{s['source_species_name']}: {s['ready_proteomic_profiles']} proteomic profiles, "
              f"{s['accepted_and_metadata_checked_images']} accepted images, {s['unreviewed_images']} unreviewed")


if __name__ == '__main__':
    main()

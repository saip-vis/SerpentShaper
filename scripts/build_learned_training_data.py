"""Construct a provenance-checked image-trait/venom dataset without changing reviews.

Images and venom are associated by source species label, never claimed to be
from the same individual. No raw photographs are copied into the output.
"""
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/venom_diet_2023/serpentshaper.sqlite'
SPEC = ROOT / 'config/venom_input_spec.json'
FLAGS = ROOT / 'config/venom_quality_flags.json'
ANNOTATIONS = ROOT / 'ML/learned_morphology/annotations.json'
PILOT = ROOT / 'ML/image_traits/pilot_observations.json'
HOLDOUT = ROOT / 'ML/image_traits/pattern_holdout.json'
OUT = ROOT / 'ML/learned_morphology/training_data.json'
OUTPUTS = ['headWidth','headLength','bodyWidth','hood','diamond','monocle','rattle','tailTaper',
           'skin_r','skin_g','skin_b','marking_r','marking_g','marking_b',
           'highlight_r','highlight_g','highlight_b','belly_r','belly_g','belly_b']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_image_allowed(image):
    """Honor existing explicit acceptance and exclusion decisions."""
    return (image.get('review_status') == 'accepted'
            and not image.get('rendering_training_excluded')
            and not image.get('reference_only_exception')
            and not image.get('duplicate_of')
            and not image.get('exact_content_seen_elsewhere')
            and image.get('rendering_exclusion_reason') not in {'duplicate_content_pending_review', 'exact_duplicate'}
            and image.get('suitability_screening', {}).get('category') not in {'rejected','supplemental'}
            and bool(image.get('observation_id')))


def check_annotation(annotation, image, manifest, provisional_ids, held_observations, root=ROOT, protected_hashes=None, advisory=None):
    """Return errors without upgrading source, photo, or annotation review state."""
    errors=[]
    if not image:
        return ['image_not_in_manifest']
    if annotation.get('review_status') != 'approved' or annotation.get('training_eligible') is not True:
        errors.append('annotation_not_approved_for_training')
    if annotation.get('annotation_source') != 'observed_photo' or not annotation.get('review_note'):
        errors.append('annotation_lacks_photo_review_provenance')
    if not source_image_allowed(image):
        errors.append('source_image_not_accepted_or_excluded')
    if image.get('image_id') in provisional_ids:
        errors.append('existing_provisional_annotation_is_training_excluded')
    if image.get('sha256') in (protected_hashes or set()):
        errors.append('image_content_reserved_or_training_excluded')
    if image.get('observation_id') in held_observations:
        errors.append('observation_reserved_for_existing_photo_check')
    if advisory in {'training_quality_review','condition_review','identity_review'} and not annotation.get('quality_resolution'):
        errors.append('advisory_quality_flag_not_resolved')
    if annotation.get('species_label') != image.get('provider_species_name'):
        errors.append('species_label_mismatch')
    if image.get('photo_license') not in {'cc0','cc-by'} or not image.get('attribution'):
        errors.append('photo_license_or_attribution_unrecorded')
    local = image.get('local_path')
    path = (manifest.parent / local).resolve() if local else None
    if not path or not path.is_relative_to(root.resolve()) or not path.is_file():
        errors.append('local_image_missing_or_outside_repository')
    elif not image.get('sha256') or sha(path) != image['sha256']:
        errors.append('image_hash_missing_or_mismatch')
    traits=annotation.get('traits')
    if not isinstance(traits,dict) or not traits:
        errors.append('no_observed_traits')
    else:
        if any(k not in OUTPUTS for k in traits):
            errors.append('unknown_trait')
        if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not 0<=v<=1 for v in traits.values()):
            errors.append('trait_value_out_of_range')
        evidence=annotation.get('trait_evidence',{})
        if not isinstance(evidence,dict) or any(not isinstance(evidence.get(k),str) or not evidence[k].strip() for k in traits):
            errors.append('trait_evidence_missing')
    return errors


def load_profiles():
    spec=json.loads(SPEC.read_text())['controls']
    excluded={(r['profile_id'],r['toxin_id']) for r in json.loads(FLAGS.read_text())['component_exclusions']}
    by_species={}
    with sqlite3.connect(DB.as_uri()+'?mode=ro',uri=True) as conn:
        conn.row_factory=sqlite3.Row
        profiles=conn.execute("SELECT profile_id,species_name FROM profiles WHERE measurement_type='proteomics' AND ingestion_status='ready_with_caveats' ORDER BY species_name,profile_id").fetchall()
        for p in profiles:
            parts={r['toxin_id']:r['abundance_pct'] for r in conn.execute('SELECT toxin_id,abundance_pct FROM components WHERE profile_id=?',(p['profile_id'],))}
            values=[parts.get(c['source_toxin_ids'][0]) if (p['profile_id'],c['source_toxin_ids'][0]) not in excluded else None for c in spec]
            # Do not invent a measured value for a missing component.
            if sum(v is not None and v>0 for v in values)>=3:
                by_species.setdefault(p['species_name'],[]).append({'profile_id':p['profile_id'],'features':values})
    return spec,by_species


def build():
    manifests=list(sorted((ROOT/'data/image_pilots').glob('*/manifest.json')))
    images={}; hash_species={}; counts=Counter()
    for manifest in manifests:
        for image in json.loads(manifest.read_text()):
            counts['image_records']+=1
            counts['accepted_not_excluded' if source_image_allowed(image) else 'not_eligible_under_source_gate']+=1
            images.setdefault(image.get('image_id'),[]).append((image,manifest))
            if image.get('sha256'):
                hash_species.setdefault(image['sha256'],set()).add(image.get('provider_species_name'))
    provisional_records=[x for x in json.loads(PILOT.read_text())['records'] if x.get('pilot_training_eligible') is not True]
    provisional={x['image_id'] for x in provisional_records}
    held_images={x['image_id'] for x in json.loads(HOLDOUT.read_text())['records']}
    held_observations={image.get('observation_id') for k in held_images|provisional for image,_ in images.get(k,[])}
    protected_hashes={image.get('sha256') for k in held_images|provisional for image,_ in images.get(k,[]) if image.get('sha256')}
    advisory_path=ROOT/'ML/pilot_image_review.json'
    advisory_by_image={r['image_id']:r for r in json.loads(advisory_path.read_text())['records']}
    annotations=json.loads(ANNOTATIONS.read_text())['annotations']
    spec,profiles=load_profiles()
    rows=[];review=[];seen=set();used_manifests={}
    for ann in annotations:
        image_id=ann.get('image_id')
        if image_id in seen:
            raise ValueError('Duplicate annotation: '+str(image_id))
        seen.add(image_id)
        candidates=images.get(image_id,[])
        image,manifest=candidates[0] if len(candidates)==1 else (None,None)
        advisory=advisory_by_image.get(image_id,{}).get('advisory_flag')
        errors=check_annotation(ann,image,manifest,provisional,held_observations,protected_hashes=protected_hashes,advisory=advisory)
        if len(candidates)>1:errors.append('image_id_appears_in_multiple_manifests')
        if image and len(hash_species.get(image.get('sha256'),set()))>1:errors.append('image_content_has_conflicting_species_labels')
        if not errors and not profiles.get(ann['species_label']):
            errors.append('no_matching_eligible_venom_profile')
        review.append({'image_id':image_id,'eligible':not errors,'reasons':errors})
        if errors:continue
        manifest_path=str(manifest.relative_to(ROOT));used_manifests[manifest_path]=sha(manifest)
        for profile in profiles[ann['species_label']]:
            rows.append({'species':ann['species_label'],'profile_id':profile['profile_id'],
                         'features':profile['features'],'image_id':image_id,'observation_id':image['observation_id'],
                         'photo_page':image.get('photo_page'),'photo_sha256':image['sha256'],'manifest':manifest_path,
                         'targets':ann['traits']})
    counts['annotation_records']=len(annotations);counts['approved_joined_images']=len({r['image_id'] for r in rows})
    counts['joined_source_species']=len({r['species'] for r in rows});counts['joined_profile_image_rows']=len(rows)
    target_coverage={k:len({r['species'] for r in rows if k in r['targets']}) for k in OUTPUTS}
    candidates=[]
    for image_id,occurrences in images.items():
        for image,manifest in occurrences:
            if not source_image_allowed(image):continue
            advisory=advisory_by_image.get(image_id,{})
            blocks=[]
            if image_id in provisional:blocks.append('existing_provisional_annotation_excluded')
            if image.get('observation_id') in held_observations:blocks.append('observation_reserved_or_provisional')
            if image.get('sha256') in protected_hashes:blocks.append('image_content_reserved_or_provisional')
            if len(occurrences)>1:blocks.append('duplicate_image_id')
            if len(hash_species.get(image.get('sha256'),set()))>1:blocks.append('conflicting_species_labels')
            if advisory.get('advisory_flag') in {'training_quality_review','condition_review','identity_review'}:blocks.append('advisory_quality_review')
            candidates.append({'image_id':image_id,'species':image.get('provider_species_name'),'observation_id':image.get('observation_id'),
                'manifest':str(manifest.relative_to(ROOT)),'photo_page':image.get('photo_page'),'sha256':image.get('sha256'),
                'license':image.get('photo_license'),'license_version':image.get('license_version'),
                'advisory_flag':advisory.get('advisory_flag'),'advisory_note':advisory.get('visual_notes'),
                'annotation_status':'not_automatically_approved','review_blocks':blocks})
    counts['accepted_photo_candidates_without_known_review_blocks']=sum(not c['review_blocks'] for c in candidates)
    return {'schema_version':1,'status':'candidate_data_only_not_approved_for_product',
            'link_scope':'source species label only; photos and venom samples are not paired individuals',
            'feature_ids':[c['id'] for c in spec],'target_ids':OUTPUTS,'counts':dict(counts),
            'target_source_species_counts':target_coverage,'candidate_images':candidates,'annotation_review':review,'rows':rows,
            'source_sha256':{**{str(x.relative_to(ROOT)):sha(x) for x in (DB,SPEC,FLAGS,ANNOTATIONS,PILOT,HOLDOUT,advisory_path,Path(__file__).resolve())},**used_manifests}}


def main():
    data=build();OUT.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':data['status'],'counts':data['counts'],'target_source_species_counts':data['target_source_species_counts']},indent=2))


if __name__=='__main__':
    main()

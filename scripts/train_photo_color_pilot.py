"""Fit an isolated venom-to-photographed-body-patch-color experiment.

No species labels are inference features. This small candidate is not a
whole-snake phenotype model and is not loaded into the product.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
import sklearn
from build_learned_training_data import ROOT, build, load_profiles, sha
from train_learned_morphology import ACTIVATION_WIDTH, evaluate, fit

SAMPLES=ROOT/'ML/learned_morphology/body_patch_samples.json'
MEASUREMENTS=ROOT/'ML/learned_morphology/body_patch_measurements.json'
OUT=ROOT/'ML/learned_morphology/body_patch_color_experiment.json'
TARGETS=['patch_r','patch_g','patch_b']


def run():
    if not MEASUREMENTS.is_file():raise ValueError('Extract body patches before training.')
    measurements=json.loads(MEASUREMENTS.read_text())
    if measurements.get('sample_definition_sha256')!=sha(SAMPLES):raise ValueError('Patch measurements are stale; extract them again.')
    audit=build();candidates={c['image_id']:c for c in audit['candidate_images']}
    spec,profiles=load_profiles();rows=[];seen=set();source_manifests=set()
    for photo in measurements['records']:
        c=candidates.get(photo['image_id'])
        if not c or c['review_blocks'] or c['sha256']!=photo['photo_sha256'] or c['species']!=photo['species_label']:
            raise ValueError('Photo is no longer an accepted, unblocked candidate: '+photo['image_id'])
        manifest=ROOT/photo['manifest']
        matching=[img for img in json.loads(manifest.read_text()) if img.get('image_id')==photo['image_id']]
        if len(matching)!=1 or not matching[0].get('local_path'):
            raise ValueError('Photo source record is missing or ambiguous: '+photo['image_id'])
        path=(manifest.parent/matching[0]['local_path']).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or sha(path)!=photo['photo_sha256']:
            raise ValueError('Photo bytes missing or changed; re-extract after review: '+photo['image_id'])
        source_manifests.add(manifest)
        if photo['observation_id'] in seen:raise ValueError('Repeated observation in color pilot')
        seen.add(photo['observation_id'])
        rgb=photo['median_rgb']
        if len(rgb)!=3 or not all(isinstance(v,(int,float)) and 0<=v<=1 for v in rgb):raise ValueError('Invalid pixel target')
        for profile in profiles.get(photo['species_label'],[]):
            rows.append({'species':photo['species_label'],'image_id':photo['image_id'],'observation_id':photo['observation_id'],
                         'profile_id':profile['profile_id'],'features':profile['features'],
                         'targets':dict(zip(TARGETS,rgb))})
    species={r['species'] for r in rows};genera={x.split()[0] for x in species}
    if len(species)<3 or len(genera)<3:raise ValueError('At least three source genera are required for the exploratory check.')
    models={t:fit(rows,t,len(spec)) for t in TARGETS}
    evaluation={t:evaluate(rows,t,len(spec)) for t in TARGETS}
    model_mae=float(np.mean([e['model_mae'] for e in evaluation.values()]));baseline_mae=float(np.mean([e['baseline_mae'] for e in evaluation.values()]))
    return {'schema_version':1,'status':'exploratory_candidate_not_deployed',
      'task':'Predict median sRGB of small observed body patches from venom values; not shape or full-snake color.',
      'feature_ids':[c['id'] for c in spec],'targets':TARGETS,'activation_width_percentage_points':ACTIVATION_WIDTH,
      'model':'Three regularized linear regressions; species-equal training weights; fold-specific median/missingness preprocessing.',
      'data':{'source_species_count':len(species),'observation_count':len(seen),'photo_count':len(measurements['records']),
              'profile_image_rows':len(rows),'link_scope':'source species label only; venom and photo do not come from a verified common specimen'},
      'evaluation_method':'Leave-one-genus-out; average predictions per source species; compare with the mean training-species patch color.',
      'evaluation':evaluation,'mean_channel_mae_normalized':model_mae,'baseline_mean_channel_mae_normalized':baseline_mae,
      'mean_channel_mae_8bit':model_mae*255,'baseline_mean_channel_mae_8bit':baseline_mae*255,
      'models':models,'image_records':measurements['records'],
      'input_sha256':{str(path.relative_to(ROOT)):sha(path) for path in [SAMPLES,MEASUREMENTS,Path(__file__).resolve(),ROOT/'scripts/train_learned_morphology.py',ROOT/'scripts/build_learned_training_data.py',*sorted(source_manifests)]},
      'dataset_source_sha256':audit['source_sha256'],'versions':{'numpy':np.__version__,'scikit_learn':sklearn.__version__},
      'limitations':['This small patch dataset is inadequate for a reliable generative model.',
                     'Lighting, camera processing and patterned scales affect measured colors.',
                     'The images and venom profiles are not known to share individuals.',
                     'The output is not a label for an entire snake, and this candidate is not connected to the renderer.']}


def main():
    output=run();OUT.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':output['status'],'data':output['data'],'mean_channel_mae_8bit':output['mean_channel_mae_8bit'],
                      'baseline_mean_channel_mae_8bit':output['baseline_mean_channel_mae_8bit']},indent=2))


if __name__=='__main__':main()

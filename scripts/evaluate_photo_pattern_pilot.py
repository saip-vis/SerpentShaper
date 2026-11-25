"""Development-only venom-to-visible-pattern experiment on reviewed photos.

The labels describe photographed regions, not whole species, and are linked
with venom by species label rather than specimen. No renderer model is emitted.
"""
import hashlib
import json
import platform
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from build_learned_training_data import ROOT, DB, SPEC, FLAGS, build, load_profiles, source_image_allowed

LABELS = ROOT / 'ML/image_traits/photo_pattern_pilot_labels.json'
OUT = ROOT / 'ML/image_traits/photo_pattern_pilot_results.json'


def load_examples():
    labels=json.loads(LABELS.read_text())
    audit=build()
    candidates={r['image_id']:r for r in audit['candidate_images']}
    _,profiles=load_profiles()
    examples=[]; seen_images=set(); seen_obs=set(); seen_species=set(); seen_hashes=set()
    for label in labels['records']:
        image_id=label['image_id']; c=candidates.get(image_id)
        if not c or c['review_blocks'] or c['species']!=label['species']:
            raise ValueError('Image is not an accepted and unblocked photo with the specified species: '+image_id)
        if image_id in seen_images or c['observation_id'] in seen_obs or c['species'] in seen_species or c['sha256'] in seen_hashes:
            raise ValueError('Image, observation, species or content duplicated: '+image_id)
        manifest=ROOT/c['manifest']
        rows=[r for r in json.loads(manifest.read_text()) if r.get('image_id')==image_id]
        if len(rows)!=1 or not source_image_allowed(rows[0]):raise ValueError('Photo gate failed: '+image_id)
        photo=rows[0];path=(manifest.parent/photo['local_path']).resolve()
        if not path.is_relative_to(manifest.parent.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=c['sha256']:
            raise ValueError('Missing photo or hash mismatch: '+image_id)
        if not photo.get('attribution') or photo.get('photo_license') not in {'cc0','cc-by'}:
            raise ValueError('Missing documented attribution or allowed license code: '+image_id)
        if label.get('visible_pattern') not in (0,1) or not label.get('evidence') or not profiles.get(c['species']):
            raise ValueError('Missing label evidence or eligible venom profile: '+image_id)
        seen_images.add(image_id);seen_obs.add(c['observation_id']);seen_species.add(c['species']);seen_hashes.add(c['sha256'])
        examples.append({**label,'observation_id':c['observation_id'],'photo_page':c['photo_page'],
                         'photo_sha256':c['sha256'],'photo_license':photo['photo_license'],
                         'license_version':photo.get('license_version'),'attribution':photo['attribution'],
                         'manifest':c['manifest'],'venom_profiles':profiles[c['species']]})
    return examples


def evaluate(examples):
    predictions=[]
    for held in examples:
        genus=held['species'].split()[0]
        train=[e for e in examples if e['species'].split()[0]!=genus]
        if len({e['visible_pattern'] for e in train})<2:raise ValueError('Each training fold needs both labels')
        x=[]; y=[];weights=[]
        for e in train:
            for p in e['venom_profiles']:
                x.append([v if v is not None else np.nan for v in p['features']]);y.append(e['visible_pattern']);weights.append(1/len(e['venom_profiles']))
        # All imputation and scaling are fit solely on the training genera.
        model=make_pipeline(SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True),
                            StandardScaler(), LogisticRegression(C=1.0,max_iter=2000,random_state=0))
        model.fit(np.asarray(x),np.asarray(y),logisticregression__sample_weight=np.asarray(weights))
        hx=np.asarray([[v if v is not None else np.nan for v in p['features']] for p in held['venom_profiles']])
        prob=float(model.predict_proba(hx)[:,1].mean())
        baseline=sum(e['visible_pattern'] for e in train)/len(train)
        predictions.append({'species':held['species'],'image_id':held['image_id'],'observation_id':held['observation_id'],
            'label':held['visible_pattern'],'venom_profile_count':len(held['venom_profiles']),
            'model_probability':prob,'baseline_probability':baseline,
            'training_genera':sorted({e['species'].split()[0] for e in train})})
    def metrics(name):
        probs=np.asarray([r[name+'_probability'] for r in predictions]);truth=np.asarray([r['label'] for r in predictions])
        classes=probs>=.5
        recalls=[float(np.mean(classes[truth==v]==v)) for v in (0,1)]
        return {'brier_score':float(np.mean((probs-truth)**2)),
                'balanced_accuracy_at_0_5':sum(recalls)/2,'accuracy_at_0_5':float(np.mean(classes==truth)),
                'recall_negative':recalls[0],'recall_positive':recalls[1]}
    return {'method':'leave-one-genus-out; equal total sample weight per training source species; average test profile probabilities per held-out species',
            'model':'median imputation with missing indicators, standard scaling and fixed logistic regression (C=1)',
            'baseline':'fraction of training species with a positive observed label',
            'metrics':{'model':metrics('model'),'baseline':metrics('baseline')},'fold_predictions':predictions}


def main():
    examples=load_examples(); outcome=evaluate(examples)
    result={'schema_version':1,'status':'tiny_exploratory_evaluation_not_for_product',
      'target':'prominent repeated markings on the visible body region in one accepted photo per source species',
      'counts':{'photos':len(examples),'observations':len(examples),'species_labels':len(examples),
                'positive_photos':sum(e['visible_pattern'] for e in examples),
                'venom_profile_rows':sum(len(e['venom_profiles']) for e in examples)},
      'limitations':[f"Only {len(examples)} assistant-labeled photos, {len(examples)-sum(e['visible_pattern'] for e in examples)} negative labels, and no expert verification make estimates highly unstable.",
        'Labels describe visible portions of photos, not whole animals or species-level truth.',
        'Species-level venom and photos are not matched to an individual, and taxon labels may be uncertain.',
        'Genus holdout reduces leakage but this tiny pilot is not an untouched generalization benchmark.',
        'Additional examples were selected after inspecting earlier results, including four selected to improve negative-label coverage; this is development data, not an untouched test set.',
        'Recorded license codes and attribution do not independently verify terms for every intended use.',
        'Results are not renderer training, biological causation, or evidence of snake-generation accuracy.'],
      'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [LABELS,DB,SPEC,FLAGS,Path(__file__).resolve(),ROOT/'scripts/build_learned_training_data.py']+sorted({ROOT/e['manifest'] for e in examples})},
      'versions':{'python':platform.python_version(),'numpy':np.__version__,'scikit_learn':sklearn.__version__},
      'examples':[{**{k:v for k,v in e.items() if k!='venom_profiles'},
                   'venom_profile_ids':[p['profile_id'] for p in e['venom_profiles']]} for e in examples], 'evaluation':outcome}
    OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'counts':result['counts'],'metrics':outcome['metrics']},indent=2))


if __name__=='__main__':main()

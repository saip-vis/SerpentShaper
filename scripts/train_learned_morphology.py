"""Train a candidate direct venom-to-shared-traits model only from approved photo labels.

The product must not load candidate models automatically. Species labels are
used for source joining and grouped evaluation, never as inference inputs.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneGroupOut

from build_learned_training_data import ROOT, OUTPUTS, build, sha

OUT = ROOT / 'ML/learned_morphology/candidate_model.json'
READINESS = ROOT / 'ML/learned_morphology/readiness.json'
MIN_SPECIES = 4
MIN_GENERA = 3
ACTIVATION_WIDTH = 1.0  # percentage points; smoothing convention, not biology


def genus(species):
    return species.split()[0]


def medians_for(rows,feature_count):
    medians=[]
    for i in range(feature_count):
        vals=[r['features'][i] for r in rows if r['features'][i] is not None and r['features'][i]>0]
        medians.append(float(np.median(vals)) if vals else 0.0)
    return medians


def transform(values,medians):
    """0 and missing are inactive; a one-point ramp avoids an on/off jump."""
    out=[];missing=[]
    for value,median in zip(values,medians):
        alpha=min(max(value/ACTIVATION_WIDTH,0.0),1.0) if value is not None and np.isfinite(value) else 0.0
        out.append((median+alpha*((value if alpha else median)-median))/100.0)
        missing.append(1.0-alpha)
    return out+missing


def fit(rows,target,feature_count):
    medians=medians_for(rows,feature_count)
    X=np.array([transform(r['features'],medians) for r in rows])
    y=np.array([r['targets'][target] for r in rows])
    counts=Counter(r['species'] for r in rows)
    weights=np.array([1.0/counts[r['species']] for r in rows])
    model=Ridge(alpha=1.0).fit(X,y,sample_weight=weights)
    return {'median':medians,'coefficients':model.coef_.tolist(),'intercept':float(model.intercept_)}


def predict(row,params):
    return float(np.clip(params['intercept']+np.dot(params['coefficients'],transform(row['features'],params['median'])),0,1))


def evaluate(rows,target,feature_count):
    groups=np.array([genus(r['species']) for r in rows])
    results=[]
    for train_idx,test_idx in LeaveOneGroupOut().split(np.zeros((len(rows),1)),groups=groups):
        train=[rows[int(i)] for i in train_idx];test=[rows[int(i)] for i in test_idx]
        if {genus(r['species']) for r in train}&{genus(r['species']) for r in test}:
            raise ValueError('Genus leakage')
        params=fit(train,target,feature_count)
        train_targets=defaultdict(list)
        for row in train:train_targets[row['species']].append(row['targets'][target])
        baseline=float(np.mean([np.mean(v) for v in train_targets.values()]))
        species_results=defaultdict(lambda:{'actual':[],'predicted':[]})
        for row in test:
            entry=species_results[row['species']];entry['actual'].append(row['targets'][target]);entry['predicted'].append(predict(row,params))
        for species,entry in species_results.items():
            actual=float(np.mean(entry['actual']));pred=float(np.mean(entry['predicted']))
            results.append({'species':species,'actual':actual,'predicted':pred,'baseline':baseline})
    return {'held_out_species':len(results),'model_mae':float(np.mean([abs(r['predicted']-r['actual']) for r in results])),
            'baseline_mae':float(np.mean([abs(r['baseline']-r['actual']) for r in results])),'predictions':results}


def readiness(data):
    coverage={}
    for target in OUTPUTS:
        rows=[r for r in data['rows'] if target in r['targets']]
        species={r['species'] for r in rows};genera={genus(s) for s in species}
        coverage[target]={'species_count':len(species),'genus_count':len(genera),
                          'enough_for_workflow':len(species)>=MIN_SPECIES and len(genera)>=MIN_GENERA}
    return {'status':'candidate_training_possible' if all(x['enough_for_workflow'] for x in coverage.values()) else 'insufficient_approved_image_traits',
            'minimum_species_per_target':MIN_SPECIES,'minimum_genera_per_target':MIN_GENERA,
            'threshold_note':'Minimums only permit a small grouped experiment; they do not establish scientific validity or production readiness.',
            'data_counts':data['counts'],'targets':coverage}


def train(data):
    check=readiness(data)
    if check['status']!='candidate_training_possible':
        raise ValueError('Insufficient approved image-derived trait labels; see readiness.json. No model was trained.')
    models={};evaluation={}
    for target in OUTPUTS:
        rows=[r for r in data['rows'] if target in r['targets']]
        evaluation[target]=evaluate(rows,target,len(data['feature_ids']))
        models[target]=fit(rows,target,len(data['feature_ids']))
    return {'schema_version':1,'status':'experimental_candidate_not_for_product',
            'feature_ids':data['feature_ids'],'target_ids':OUTPUTS,'minimum_active_inputs':3,
            'activation_width_percentage_points':ACTIVATION_WIDTH,'models':models,'evaluation':evaluation,
            'provenance':{'data_source_sha256':data['source_sha256'],'image_count':data['counts']['approved_joined_images'],
                          'source_species_count':data['counts']['joined_source_species'],
                          'link_scope':data['link_scope'],'training_script_sha256':sha(Path(__file__).resolve())},
            'limitations':['Traits are image-derived annotations associated with venom only by source species label.',
                           'This candidate is not validated as a biological phenotype predictor and is not approved for use by the main interface.',
                           'Grouped evaluation can still be affected by relatedness, missing values and study differences.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--train',action='store_true');args=parser.parse_args()
    data=build();check=readiness(data);READINESS.write_text(json.dumps(check,indent=2)+'\n')
    print(json.dumps({'status':check['status'],'image_count':data['counts']['approved_joined_images'],
                      'species_count':data['counts']['joined_source_species'],'outputs_ready':sum(v['enough_for_workflow'] for v in check['targets'].values()),
                      'outputs_required':len(OUTPUTS)},indent=2))
    if args.train:
        if check['status']!='candidate_training_possible':
            raise SystemExit('No model trained: image-derived training labels are not available for every control.')
        candidate=train(data);OUT.write_text(json.dumps(candidate,indent=2,allow_nan=False)+'\n')
        print('Trained an experimental candidate; it is not enabled in the product.')


if __name__=='__main__':
    main()

"""Compare candidate models for one photo-observed pattern label.

Development-only: photos show visible regions, photo and venom are linked only
by source label, and the pilot was expanded after earlier results were seen.
No model from this script is connected to the interface.
"""
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import sklearn
from sklearn.ensemble import ExtraTreesClassifier, HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

from evaluate_photo_pattern_pilot import LABELS, load_examples
from build_learned_training_data import ROOT, DB, SPEC, FLAGS

OUT=ROOT/'ML/image_traits/photo_pattern_model_comparison.json'


def evaluate(examples):
    predictions=[]
    genera=sorted({e['species'].split()[0] for e in examples})
    for genus in genera:
        train=[e for e in examples if e['species'].split()[0]!=genus]
        held=[e for e in examples if e['species'].split()[0]==genus]
        if len({e['visible_pattern'] for e in train})<2:
            raise ValueError('Each training fold needs both pattern labels.')
        x=[];y=[];weights=[]
        for e in train:
            for p in e['venom_profiles']:
                x.append([v if v is not None else np.nan for v in p['features']])
                y.append(e['visible_pattern']);weights.append(1/len(e['venom_profiles']))
        x=np.asarray(x);y=np.asarray(y);weights=np.asarray(weights)
        imputer=lambda: SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)
        models={
            'random_forest':make_pipeline(imputer(),RandomForestClassifier(n_estimators=80,min_samples_leaf=3,max_features=.7,random_state=1,n_jobs=1)),
            'extra_trees':make_pipeline(imputer(),ExtraTreesClassifier(n_estimators=80,min_samples_leaf=3,max_features=.7,random_state=1,n_jobs=1)),
            'hist_gradient_boosting':make_pipeline(imputer(),HistGradientBoostingClassifier(max_iter=60,max_leaf_nodes=5,l2_regularization=2,random_state=1)),
        }
        for key,model in models.items():
            model.fit(x,y,**{model.steps[-1][0]+'__sample_weight':weights})
        baseline=float(np.mean([e['visible_pattern'] for e in train]))
        for e in held:
            hx=np.asarray([[v if v is not None else np.nan for v in p['features']] for p in e['venom_profiles']])
            predicted={key:float(model.predict_proba(hx)[:,1].mean()) for key,model in models.items()}
            predictions.append({'species':e['species'],'image_id':e['image_id'],'label':e['visible_pattern'],
                                'baseline':baseline,**predicted})
    truth=np.asarray([r['label'] for r in predictions]);metrics={}
    for key in ['baseline','random_forest','extra_trees','hist_gradient_boosting']:
        probs=np.asarray([r[key] for r in predictions]);classes=probs>=.5
        recalls=[float(np.mean(classes[truth==v]==v)) for v in (0,1)]
        metrics[key]={'brier_score':float(np.mean((probs-truth)**2)),
                      'balanced_accuracy_at_0_5':sum(recalls)/2,
                      'recall_negative':recalls[0],'recall_positive':recalls[1]}
    inputs=[LABELS,DB,SPEC,FLAGS,Path(__file__).resolve(),ROOT/'scripts/evaluate_photo_pattern_pilot.py']
    inputs+=sorted({ROOT/e['manifest'] for e in examples if e.get('manifest')})
    return {'schema_version':1,'status':'development_only_not_connected',
            'method':'Leave-one-genus-out; equal total training weight per source label; average test profile predictions per held-out species.',
            'counts':{'photos':len(examples),'genera':len(genera),'positive':int(truth.sum()),'negative':int(len(truth)-truth.sum())},
            'model_config':'80 trees, leaf size 3 and 0.7 feature fraction for forests; histogram boosting uses 60 iterations, 5 leaf nodes, and L2 regularization 2.',
            'labels_sha256':hashlib.sha256(LABELS.read_bytes()).hexdigest(),
            'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
            'versions':{'python':platform.python_version(),'numpy':np.__version__,'scikit_learn':sklearn.__version__},
            'limitations':['Exploratory development comparison, not an untouched test; methods were selected after earlier results.',
              'Labels are binary observations of visible body regions, not whole-animal traits or specific motif classes.',
              'Photo and venom data are linked by source species label, not by an individual specimen.',
              'No model or output in this comparison has been connected to the renderer.'],
            'metrics':metrics,'predictions':predictions}


def main():
    result=evaluate(load_examples())
    OUT.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'counts':result['counts'],'metrics':result['metrics']},indent=2))

if __name__=='__main__':main()

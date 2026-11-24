"""Compare a venom-to-authored-pattern model with a prevalence baseline.

Three photo observations are an isolated *test only*, never training examples.
The task and labels are exploratory and do not demonstrate phenotype causation.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from train_visual_style_model import load_data, DB, SPEC, FLAGS

ROOT = Path(__file__).resolve().parents[1]
PRESETS = ROOT / 'PhysicalRendererTest/presets/species-presets.json'
HOLDOUT = ROOT / 'ML/image_traits/pattern_holdout.json'
OUTPUT = ROOT / 'ML/image_traits/pattern_experiment.json'
DIAMONDS = {'diamonds', 'outlined_diamonds'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def genus(species):
    return species.split()[0]


def load_holdout():
    records = json.loads(HOLDOUT.read_text())['records']
    groups = set()
    for record in records:
        assert isinstance(record['visible_diamonds'], bool)
        manifest = ROOT / record['manifest']
        photo = next(r for r in json.loads(manifest.read_text()) if r['image_id'] == record['image_id'])
        if (photo.get('provider_species_name') != record['species'] or photo.get('review_status') != 'accepted'
                or photo.get('rendering_training_excluded') or photo.get('duplicate_of') or photo.get('reference_only_exception')):
            raise ValueError('Photo is not an accepted, non-excluded reference: ' + record['image_id'])
        obs = photo['observation_id']
        if obs in groups:
            raise ValueError('Repeated observation in image check')
        groups.add(obs)
        image = manifest.parent / photo['local_path']
        if sha(image) != photo['sha256']:
            raise ValueError('Image hash mismatch: ' + record['image_id'])
        record.update(observation_id=obs, photo_page=photo['photo_page'], sha256=photo['sha256'])
    return records


def fit_predict(train, test, balance_classes=False):
    if set(genus(r['species']) for r in train) & set(genus(r['species']) for r in test):
        raise ValueError('Genus leakage')
    X = np.array([[np.nan if v is None else v for v in r['features']] for r in train])
    X_test = np.array([[np.nan if v is None else v for v in r['features']] for r in test])
    y = np.array([r['label'] for r in train])
    if len(set(y)) < 2:
        raise ValueError('Both classes required for training')
    counts = Counter(r['species'] for r in train)
    weights = np.array([1/counts[r['species']] for r in train])
    if balance_classes:
        species_labels = {r['species']:r['label'] for r in train}
        class_counts = Counter(species_labels.values())
        weights *= np.array([len(species_labels)/(2*class_counts[r['label']]) for r in train])
    model = Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
                      ('scale', StandardScaler()), ('classifier', LogisticRegression(max_iter=2000, random_state=0))])
    model.fit(X, y, classifier__sample_weight=weights)
    probabilities = model.predict_proba(X_test)[:, 1]
    baseline = float(sum(r['label']/counts[r['species']] for r in train) / len(counts))
    grouped = defaultdict(list)
    for row, probability in zip(test, probabilities):
        grouped[row['species']].append(float(probability))
    labels = {r['species']: r['label'] for r in test}
    return [{'species': name, 'profile_count':len(values), 'actual':labels[name],
             'probability':float(np.mean(values)), 'baseline_probability':baseline}
            for name, values in sorted(grouped.items())]


def metrics(rows):
    actual = np.array([r['actual'] for r in rows]); prob = np.array([r['probability'] for r in rows]); base = np.array([r['baseline_probability'] for r in rows])
    positive = actual == 1
    return {'species_count':len(rows), 'positive_species':int(sum(actual)),
            'model_accuracy_at_0_5':float(np.mean((prob >= .5)==actual)),
            'baseline_accuracy_at_0_5':float(np.mean((base >= .5)==actual)),
            'model_positive_recall_at_0_5':float(np.mean(prob[positive] >= .5)) if positive.any() else None,
            'baseline_positive_recall_at_0_5':float(np.mean(base[positive] >= .5)) if positive.any() else None,
            'model_brier':float(np.mean((prob-actual)**2)), 'baseline_brier':float(np.mean((base-actual)**2))}


def experiment():
    _, source_rows = load_data()
    presets = {p['source_species_name']:p['artistic_parameters']['pattern'] for p in json.loads(PRESETS.read_text())['presets']}
    rows = [{**r, 'label':int(presets[r['species']] in DIAMONDS)} for r in source_rows]
    photo_records = load_holdout()
    held_genera = {genus(r['species']) for r in photo_records}
    training = [r for r in rows if genus(r['species']) not in held_genera]
    held = [r for r in rows if r['species'] in {p['species'] for p in photo_records}]
    if {r['species'] for r in held} != {r['species'] for r in photo_records}:
        raise ValueError('Missing venom profile in photo check')
    # Replace authored labels only in the separate held-out evaluation rows.
    image_labels = {r['species']: int(r['visible_diamonds']) for r in photo_records}
    held = [{**r, 'label':image_labels[r['species']]} for r in held]
    image_predictions = fit_predict(training, held)
    balanced_image_predictions = fit_predict(training, held, balance_classes=True)
    for prediction in (image_predictions, balanced_image_predictions):
        for p in prediction:
            photo = next(x for x in photo_records if x['species'] == p['species'])
            p.update(image_id=photo['image_id'], observation_id=photo['observation_id'], photo_page=photo['photo_page'])
    # A separate genus-held-out validation of the authored labels (not photos).
    X = np.zeros((len(rows), 1)); groups = np.array([genus(r['species']) for r in rows]); out = []; balanced_out = []
    for train_idx, test_idx in GroupKFold(n_splits=5).split(X, groups=groups):
        train_fold = [rows[int(i)] for i in train_idx]; test_fold = [rows[int(i)] for i in test_idx]
        out.extend(fit_predict(train_fold, test_fold))
        balanced_out.extend(fit_predict(train_fold, test_fold, balance_classes=True))
    report = {'task':'Exploratory binary diamond-like marking versus other authored pattern; not species identification.',
              'training_targets':'Manually authored SVG patterns, not snake photos. Positive patterns: diamonds or outlined_diamonds.',
              'features':'12 broad venom categories; training-only median imputation with missingness indicators and scaling.',
              'model':'Logistic regression, default regularization, equal total training weight per source species. A second variant balances total species weight across the two training classes within each fold.',
              'baseline':'Training-set fraction of positive authored species, with equal species weighting.',
              'validation':'Five-fold genus-held-out for authored labels; separate three-species photo check excludes all three genera from training.',
              'authored_validation':metrics(out), 'photo_check':metrics(image_predictions),
              'photo_check_predictions':image_predictions, 'balanced_authored_validation':metrics(balanced_out),
              'balanced_photo_check':metrics(balanced_image_predictions), 'balanced_photo_check_predictions':balanced_image_predictions,
              'photo_training_count':0, 'photo_check_train_species':len({r['species'] for r in training}),
              'photo_check_train_profiles':len(training), 'excluded_photo_check_genera':sorted(held_genera),
              'limitations':['Three photographs cannot establish accuracy or species-wide appearance.',
                 'Photo check labels refer only to visible parts; no observed diamond is not proof of absence.',
                 'Training uses authored presets, which may be inaccurate or incomplete; held-out genus does not eliminate broader relatedness or data source confounding.',
                 'Venom profiles and photographs are not paired specimens; no causation or real-snake phenotype prediction is established.',
                 'Reference images remain subject to their existing review, exclusion and license policies; no model is integrated into the app.'],
              'versions':{'numpy':np.__version__,'scikit_learn':sklearn.__version__},
              'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (DB,SPEC,FLAGS,PRESETS,HOLDOUT,Path(__file__).resolve(), ROOT / 'scripts/train_visual_style_model.py')}}
    return report


def main():
    report=experiment()
    OUTPUT.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ('authored_validation','balanced_authored_validation','photo_check','balanced_photo_check','photo_check_predictions','balanced_photo_check_predictions')},indent=2))


if __name__ == '__main__':
    main()

"""Train an exploratory venom-to-reported-species-maximum-length regression.

This tests a noisy species-level association, not an individual, image, or causal
phenotype prediction. Genus-held-out evaluation and a median baseline are required.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/venom_diet_2023/serpentshaper.sqlite'
MORPH = ROOT / 'data/processed/morphology/physical_profiles.json'
SPEC = ROOT / 'config/venom_input_spec.json'
FLAGS = ROOT / 'config/venom_quality_flags.json'
OUT = ROOT / 'ML/length_experiment'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_data():
    controls = json.loads(SPEC.read_text())['controls']
    morph = json.loads(MORPH.read_text())['profiles']
    exclusions = {(f['profile_id'], f['toxin_id']) for f in json.loads(FLAGS.read_text())['component_exclusions']}
    names = [c['id'] for c in controls]
    target_by_species = {}
    for item in morph:
        trait = (item.get('compilation_traits') or {}).get('maximum_total_length_mm') or {}
        value = trait.get('value')
        if trait.get('status') == 'reported' and isinstance(value, (int, float)) and not isinstance(value, bool) and 0 < value <= 10000:
            target_by_species[item['source_species_name']] = {'target_mm': float(value), 'citation': trait.get('citation')}
    rows = []
    with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        profiles = conn.execute("SELECT profile_id,species_name,source_row,location FROM profiles WHERE measurement_type='proteomics' AND ingestion_status='ready_with_caveats' ORDER BY species_name,source_row").fetchall()
        for profile in profiles:
            name = profile['species_name']
            if name not in target_by_species:
                continue
            components = {r['toxin_id']: r['abundance_pct'] for r in conn.execute(
                'SELECT toxin_id,abundance_pct FROM components WHERE profile_id=?', (profile['profile_id'],))}
            values = [components.get(c['source_toxin_ids'][0]) if (profile['profile_id'], c['source_toxin_ids'][0]) not in exclusions else None for c in controls]
            if sum(v is not None for v in values) < 3:
                continue
            rows.append({'profile_id': profile['profile_id'], 'species': name, 'genus': name.split()[0],
                         'source_row': profile['source_row'], 'target_mm': target_by_species[name]['target_mm'],
                         'target_citation': target_by_species[name]['citation'], 'features': values})
    if not rows:
        raise ValueError('No records satisfy the experiment input policy')
    return names, rows


def make_pipeline():
    return Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True, keep_empty_features=True)),
                     ('scale', StandardScaler()), ('regression', Ridge(alpha=10.0))])


def species_predictions(rows, predictions, indices):
    grouped = {}
    for index, prediction in zip(indices, predictions):
        row = rows[int(index)]
        item = grouped.setdefault(row['species'], {'genus': row['genus'], 'observed_mm': row['target_mm'], 'predictions': []})
        item['predictions'].append(float(prediction))
    return [{'species': name, 'genus': data['genus'], 'observed_mm': data['observed_mm'],
             'predicted_mm': float(np.mean(data['predictions'])), 'profile_count': len(data['predictions'])}
            for name, data in sorted(grouped.items())]


def weights_for_species(rows, indices):
    counts = {}
    for i in indices:
        name = rows[int(i)]['species']
        counts[name] = counts.get(name, 0) + 1
    return np.array([1.0 / counts[rows[int(i)]['species']] for i in indices])


def experiment():
    features, rows = load_data()
    X = np.array([[np.nan if value is None else value for value in row['features']] for row in rows], dtype=float)
    y = np.array([r['target_mm'] for r in rows], dtype=float)
    groups = np.array([r['genus'] for r in rows])
    splits = list(GroupKFold(n_splits=5).split(X, y, groups))
    all_predictions, folds = [], []
    for fold_no, (train, test) in enumerate(splits, start=1):
        if set(groups[train]) & set(groups[test]):
            raise AssertionError('Genus leakage across train and test')
        model = make_pipeline()
        model.fit(X[train], y[train], regression__sample_weight=weights_for_species(rows, train))
        predictions = species_predictions(rows, model.predict(X[test]), test)
        train_species = {rows[int(i)]['species']: y[i] for i in train}
        median_prediction = float(np.median(list(train_species.values())))
        for p in predictions:
            p['fold'] = fold_no
            p['baseline_prediction_mm'] = median_prediction
        errors = [abs(p['predicted_mm'] - p['observed_mm']) for p in predictions]
        baseline_errors = [abs(median_prediction - p['observed_mm']) for p in predictions]
        all_predictions.extend(predictions)
        folds.append({'fold': fold_no, 'train_profiles': len(train), 'test_profiles': len(test),
                      'train_species': len(train_species), 'test_species': len(predictions),
                      'test_genera': sorted(set(groups[test].tolist())),
                      'model_mae_mm': float(np.mean(errors)), 'baseline_mae_mm': float(np.mean(baseline_errors))})
    model = make_pipeline()
    model.fit(X, y, regression__sample_weight=weights_for_species(rows, np.arange(len(rows))))
    imputer, scaler, reg = model.named_steps['impute'], model.named_steps['scale'], model.named_steps['regression']
    # Store numeric parameters as JSON, avoiding arbitrary code execution from pickle.
    artifact = {'status': 'exploratory_not_for_product_use', 'model': 'ridge', 'alpha': 10.0,
                'feature_ids': features, 'imputer_median': imputer.statistics_.tolist(),
                'indicator_feature_indices': imputer.indicator_.features_.tolist(),
                'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist(),
                'coefficient': reg.coef_.tolist(), 'intercept': float(reg.intercept_),
                'warning': 'Unvalidated species-level association; not an image model, not causal, and not suitable for product predictions.'}
    true = np.array([p['observed_mm'] for p in all_predictions])
    pred = np.array([p['predicted_mm'] for p in all_predictions])
    base = np.array([p['baseline_prediction_mm'] for p in all_predictions])
    report = {'status': 'exploratory_genus_held_out_test_not_product_validation',
              'task': 'Predict a compilation-reported species maximum total length from species-associated venom profiles.',
              'rows': len(rows), 'species_labels': len(set(r['species'] for r in rows)), 'genus_labels': len(set(groups)),
              'split': '5-fold GroupKFold by source genus; all profiles from each genus stay together; evaluation averages predictions within species.',
              'preprocessing': 'Per-fold training-only median imputation with missingness indicators, scaling, then ridge regression; each species has equal total regression training weight.',
              'minimum_reported_input_categories': 3, 'baseline': 'Training-fold median of one observed maximum length per species.',
              'model_mae_mm': float(np.mean(np.abs(pred - true))), 'baseline_mae_mm': float(np.mean(np.abs(base - true))),
              'model_median_absolute_error_mm': float(np.median(np.abs(pred - true))),
              'folds': folds, 'held_out_species_predictions': all_predictions,
              'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in (DB, MORPH, SPEC, FLAGS, Path(__file__).resolve())},
              'versions': {'scikit_learn': sklearn.__version__, 'numpy': np.__version__},
              'limitations': ['Species maximum length is a compilation-reported extreme, not a typical or individually measured length.',
                'Venom and morphology records are associated by unreconciled source name, not measured on the same animal.',
                'Species and genus names may be unresolved synonyms; relatedness, shared sources, methods and geography can confound results.',
                'A trained association does not show venom causes size, and outputs are not demonstrated to generalize to invented snakes.',
                'Missing values are imputed within the training fold, with indicators; they are not claims that toxins are absent.',
                'No images, diet, habitat, age or individual-level labels were used. The 2025 staged mamba record is not included.',
                'No model selection or hyperparameter tuning is reported. Negative or implausible predictions are possible.']}
    return report, artifact, rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUT)
    args = parser.parse_args()
    report, artifact, rows = experiment()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / 'evaluation.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    (args.output_dir / 'model.json').write_text(json.dumps(artifact, indent=2, allow_nan=False) + '\n')
    (args.output_dir / 'input_manifest.json').write_text(json.dumps({'feature_ids': artifact['feature_ids'], 'rows': rows}, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'rows', 'species_labels', 'genus_labels', 'model_mae_mm', 'baseline_mae_mm')}, indent=2))


if __name__ == '__main__':
    main()

"""Fit a small experimental model from venom profiles to artistic preset styles.

Targets are the project's authored SVG settings, not verified biological traits or
photographs. The browser uses the result only for bounded illustrative variations.
"""
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'data/processed/venom_diet_2023/serpentshaper.sqlite'
PRESETS = ROOT / 'PhysicalRendererTest/presets/species-presets.json'
SPEC = ROOT / 'config/venom_input_spec.json'
FLAGS = ROOT / 'config/venom_quality_flags.json'
OUT = ROOT / 'MainInterface/visual-style-model.js'
REPORT = ROOT / 'ML/visual_style_model.json'
SHAPE_NORMALIZERS = {'cobra':62.5, 'viper':25.5, 'terrestrial':15.0, 'marine':26.0}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rgb(hex_color):
    if not isinstance(hex_color, str) or len(hex_color) != 7 or hex_color[0] != '#':
        raise ValueError('Expected a six-digit color in the species preset')
    return [int(hex_color[i:i+2], 16) for i in (1, 3, 5)]


def load_data():
    controls = json.loads(SPEC.read_text())['controls']
    presets = {p['source_species_name']: p for p in json.loads(PRESETS.read_text())['presets']}
    exclusions = {(f['profile_id'], f['toxin_id']) for f in json.loads(FLAGS.read_text())['component_exclusions']}
    data = []
    with sqlite3.connect(DB.as_uri()+'?mode=ro', uri=True) as conn:
        conn.row_factory = sqlite3.Row
        profiles = conn.execute("SELECT profile_id,species_name,source_row FROM profiles WHERE measurement_type='proteomics' AND ingestion_status='ready_with_caveats' ORDER BY species_name,source_row").fetchall()
        for profile in profiles:
            preset = presets.get(profile['species_name'])
            if preset is None:
                continue
            p = preset['artistic_parameters']
            values = {r['toxin_id']:r['abundance_pct'] for r in conn.execute(
                'SELECT toxin_id,abundance_pct FROM components WHERE profile_id=?', (profile['profile_id'],))}
            features = [values.get(c['source_toxin_ids'][0]) if (profile['profile_id'], c['source_toxin_ids'][0]) not in exclusions else None for c in controls]
            if sum(v is not None for v in features) < 3:
                continue
            plan = p['body_plan']
            widths = [v[1] for v in p['hood_profile']] if plan == 'cobra' else [v[2] for v in p['body_stations']]
            shape_ratio = max(widths) / SHAPE_NORMALIZERS[plan]
            target = rgb(p['skin_color']) + rgb(p['marking_color']) + [float(p['scale_pitch']), float(p['mark_spacing']), shape_ratio]
            data.append({'profile_id':profile['profile_id'], 'species':profile['species_name'],
                         'preset_id':preset['preset_id'], 'features':features, 'artistic_targets':target})
    if not data:
        raise ValueError('No valid species-level style examples')
    return controls, data


def train():
    controls, rows = load_data()
    X = np.array([[np.nan if x is None else x for x in r['features']] for r in rows], dtype=float)
    y = np.array([r['artistic_targets'] for r in rows], dtype=float)
    counts = {}
    for r in rows: counts[r['species']] = counts.get(r['species'], 0) + 1
    weights = np.array([1/counts[r['species']] for r in rows])
    pipeline = Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
                         ('scale',StandardScaler()),('model',Ridge(alpha=40.0))])
    pipeline.fit(X, y, model__sample_weight=weights)
    imp, scale, model = pipeline.named_steps['impute'], pipeline.named_steps['scale'], pipeline.named_steps['model']
    params = {'schema_version':1, 'kind':'experimental_artistic_style_regression',
              'feature_ids':[c['id'] for c in controls], 'median':imp.statistics_.tolist(),
              'missing_indicator_indices':imp.indicator_.features_.tolist(),
              'scaler_mean':scale.mean_.tolist(), 'scaler_scale':scale.scale_.tolist(),
              'coefficients':model.coef_.tolist(), 'intercepts':model.intercept_.tolist(),
              'outputs':['skin_r','skin_g','skin_b','mark_r','mark_g','mark_b','scale_pitch','mark_spacing','relative_shape_width'],
              'shape_normalizers':SHAPE_NORMALIZERS,
              'minimum_inputs':3, 'blend_strength':0.4,
              'rows':len(rows), 'source_species_labels':len(counts),
              'limitations':'Learned from manually authored artistic presets linked by source species name, not from snake photos or individually paired venom and morphology. Not a biological or clinical prediction.'}
    report = {**params, 'training_method':'Multi-output ridge regression, alpha 40; species-equal regression sample weights; median imputation and missingness indicators.',
              'validation':'No claim of predictive accuracy. This is an exploratory visual style model and is not evaluated against verified animal images.',
              'versions':{'numpy':np.__version__, 'scikit_learn':sklearn.__version__},
              'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (DB, PRESETS, SPEC, FLAGS, Path(__file__).resolve())},
              'parity_example':{'profile_id':rows[0]['profile_id'], 'features':rows[0]['features'], 'prediction':pipeline.predict(X[:1])[0].tolist()},
              'training_rows':rows}
    return params, report


def main():
    params, report = train()
    OUT.write_text('// Generated by scripts/train_visual_style_model.py; do not edit.\nwindow.SERPENT_STYLE_MODEL = '+json.dumps(params,separators=(',', ':'),allow_nan=False)+';\n')
    REPORT.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(f"Trained exploratory artistic style model: {params['rows']} profiles, {params['source_species_labels']} source labels.")


if __name__ == '__main__':
    main()

import json
import sys
import unittest
from pathlib import Path

import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from train_visual_style_model import load_data, train


class StyleModelTests(unittest.TestCase):
    def test_exported_parameters_match_sklearn_predictions(self):
        params, report = train()
        _, rows = load_data()
        X = np.array([[np.nan if x is None else x for x in r['features']] for r in rows], dtype=float)
        y = np.array([r['artistic_targets'] for r in rows], dtype=float)
        counts = {}
        for row in rows: counts[row['species']] = counts.get(row['species'], 0) + 1
        weights = np.array([1/counts[row['species']] for row in rows])
        model = Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True,keep_empty_features=True)),
                          ('scale',StandardScaler()),('model',Ridge(alpha=40.0))])
        model.fit(X,y,model__sample_weight=weights)
        missing = np.isnan(X)
        filled = np.where(missing, np.array(params['median']), X)
        indicators = missing[:,params['missing_indicator_indices']].astype(float)
        scaled = (np.column_stack((filled,indicators)) - np.array(params['scaler_mean'])) / np.array(params['scaler_scale'])
        exported = scaled @ np.array(params['coefficients']).T + np.array(params['intercepts'])
        np.testing.assert_allclose(exported,model.predict(X),rtol=1e-9,atol=1e-9)
        self.assertEqual(report['rows'],len(rows))
        self.assertIn('authored artistic presets',params['limitations'])

    def test_source_flag_and_generated_browser_file(self):
        controls, rows = load_data()
        row = next(r for r in rows if r['profile_id']=='vd2023_e2d1aa974518_r189')
        feature_ids = [c['id'] for c in controls]
        self.assertIsNone(row['features'][feature_ids.index('natriuretic_peptide')])
        line = (ROOT/'MainInterface/visual-style-model.js').read_text().splitlines()[1]
        payload = json.loads(line.removeprefix('window.SERPENT_STYLE_MODEL = ').removesuffix(';'))
        self.assertEqual(payload['feature_ids'],feature_ids)
        self.assertGreaterEqual(payload['rows'],len(set(r['species'] for r in rows)))


if __name__=='__main__':
    unittest.main()

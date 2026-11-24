import sys
import unittest
from pathlib import Path

import numpy as np
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from train_length_experiment import experiment, load_data, make_pipeline, weights_for_species


class LengthExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, cls.artifact, cls.rows = experiment()
        cls.features, _ = load_data()

    def test_no_genus_leakage_and_one_prediction_per_species(self):
        groups = np.array([r['genus'] for r in self.rows])
        y = np.array([r['target_mm'] for r in self.rows])
        for train, test in GroupKFold(n_splits=5).split(np.zeros((len(y), 1)), y, groups):
            self.assertFalse(set(groups[train]) & set(groups[test]))
        predictions = self.report['held_out_species_predictions']
        self.assertEqual(len(predictions), len(set(p['species'] for p in predictions)))
        self.assertEqual(len(predictions), self.report['species_labels'])

    def test_unverified_mamba_component_is_missing_not_zero(self):
        mamba = next(row for row in self.rows if row['profile_id'] == 'vd2023_e2d1aa974518_r189')
        self.assertIsNone(mamba['features'][self.features.index('natriuretic_peptide')])

    def test_exported_numeric_parameters_match_fitted_model(self):
        X = np.array([[np.nan if v is None else v for v in r['features']] for r in self.rows], dtype=float)
        y = np.array([r['target_mm'] for r in self.rows])
        model = make_pipeline()
        model.fit(X, y, regression__sample_weight=weights_for_species(self.rows, np.arange(len(y))))
        artifact = self.artifact
        missing = np.isnan(X)
        imputed = np.where(missing, np.array(artifact['imputer_median']), X)
        indicators = missing[:, artifact['indicator_feature_indices']].astype(float)
        transformed = np.column_stack((imputed, indicators))
        transformed = (transformed - np.array(artifact['scaler_mean'])) / np.array(artifact['scaler_scale'])
        actual = transformed @ np.array(artifact['coefficient']) + artifact['intercept']
        np.testing.assert_allclose(actual, model.predict(X), rtol=1e-9, atol=1e-9)


if __name__ == '__main__':
    unittest.main()

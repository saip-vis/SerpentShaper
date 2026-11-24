import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_ml_retrieval_baseline import compare, run

class BaselineTests(unittest.TestCase):
    def test_missing_is_not_zero_and_coverage_is_explicit(self):
        result=compare({'A':0.,'B':10.,'C':None},{'A':None,'B':20.,'C':30.})
        self.assertEqual(result['selected'],2)
        self.assertEqual(result['compared'],1)
        self.assertEqual(result['mean_absolute_difference_percentage_points'],10.)
        self.assertIsNone(compare({'A':0.},{'A':None}))

    def test_nonoverlap_and_zero(self):
        self.assertEqual(compare({'A':0.},{'A':0.})['mean_absolute_difference_percentage_points'],0.)
        self.assertIsNone(compare({'A':None},{'A':0.}))

    def test_real_pilot_excludes_query_and_does_not_claim_training(self):
        result=run(ROOT,'vd2023_e2d1aa974518_r189')
        self.assertIn('no model training', result['status'])
        self.assertNotIn('vd2023_e2d1aa974518_r189', [r['reference_profile']['profile_id'] for r in result['ranked_reference_profiles']])
        for r in result['ranked_reference_profiles']:
            self.assertGreater(r['compared'],0)
            self.assertLessEqual(r['compared'],r['selected'])
            self.assertNotIn('vd2023_H', r['shared_source_toxin_ids'])
        self.assertEqual([r['compared'] for r in result['ranked_reference_profiles']],sorted([r['compared'] for r in result['ranked_reference_profiles']],reverse=True))

    def test_invalid_query_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'eligible proteomic'):
            run(ROOT,'not_a_real_profile')

if __name__=='__main__':
    unittest.main()

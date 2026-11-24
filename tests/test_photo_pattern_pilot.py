import sys
import unittest
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from run_pattern_experiment import fit_predict, load_holdout, metrics


class PhotoPatternPilotTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('PIL'), 'Pillow required to rebuild photo colors')
    def test_photo_cue_uses_two_distinct_accepted_observations(self):
        from build_photo_cues import build
        cue = build()['cues'][0]
        self.assertEqual(cue['species'], 'Crotalus atrox')
        self.assertEqual(cue['pattern'], 'diamonds')
        self.assertGreaterEqual(len({s['observation_id'] for s in cue['sources']}), 2)
        self.assertTrue(all(s['review_status'] == 'accepted' for s in cue['sources']))
        self.assertTrue(all(0 <= x <= 255 for x in cue['dark_rgb'] + cue['light_rgb']))

    def test_image_check_is_separate_accepted_observations(self):
        photos = load_holdout()
        self.assertEqual(len(photos), 3)
        self.assertEqual(len({p['observation_id'] for p in photos}), len(photos))
        self.assertEqual({p['visible_diamonds'] for p in photos}, {True, False})

    def test_evaluation_rejects_same_genus_leakage(self):
        train = [{'species':'Crotalus atrox', 'features':[1.0], 'label':1}]
        test = [{'species':'Crotalus simus', 'features':[1.0], 'label':1}]
        with self.assertRaisesRegex(ValueError, 'Genus leakage'):
            fit_predict(train, test)

    def test_recall_exposes_always_negative_baseline(self):
        result = metrics([{'actual': 0, 'probability':.1, 'baseline_probability':.1},
                          {'actual': 1, 'probability':.1, 'baseline_probability':.1}])
        self.assertEqual(result['baseline_accuracy_at_0_5'], .5)
        self.assertEqual(result['baseline_positive_recall_at_0_5'], 0)


if __name__ == '__main__':
    unittest.main()

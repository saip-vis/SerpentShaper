import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from measure_photo_geometry import measure, pixel_point
from build_learned_training_data import build
import train_learned_morphology as morphology


class PhotoGeometryTests(unittest.TestCase):
    def test_head_ratio_uses_pixel_dimensions_and_is_scale_invariant(self):
        annotation = {'measurement': 'apparent_head_height_to_length', 'view': 'side',
                      'evidence': 'synthetic', 'points': {'snout': [.1, .5], 'head_base': [.3, .5],
                                                            'top': [.2, .4], 'bottom': [.2, .6]}}
        first = measure(annotation, 1000, 500)
        second = measure(annotation, 2000, 1000)
        self.assertAlmostEqual(first['apparent_head_height_to_length'], .5)
        self.assertAlmostEqual(first['apparent_head_height_to_length'], second['apparent_head_height_to_length'])

    def test_pattern_spacing_and_invalid_landmarks(self):
        annotation = {'measurement': 'apparent_marking_spacing_to_body_width', 'view': 'side',
                      'evidence': 'synthetic', 'points': {'body_width': [[.2, .4], [.2, .6]],
                      'mark_centers': [[.1, .5], [.3, .5], [.5, .5]]}}
        result = measure(annotation, 1000, 500)
        self.assertAlmostEqual(result['mean_apparent_marking_spacing_to_body_width'], 2)
        with self.assertRaises(ValueError):
            pixel_point([float('nan'), .2], 1000, 500)
        with self.assertRaises(ValueError):
            measure({**annotation, 'points': {**annotation['points'], 'mark_centers': [[.1, .5], [.3, .5]]}}, 1000, 500)
        with self.assertRaises(ValueError):
            measure({**annotation, 'points': {**annotation['points'], 'body_width': [[.2, .4], [.2, .4]]}}, 1000, 500)

    def test_unresolved_observation_stays_out_of_source_and_patches(self):
        records = json.loads((ROOT / 'data/image_pilots/pilot_004_western_diamondback/manifest.json').read_text())
        held = [r for r in records if r['observation_id'] == 1428159]
        self.assertEqual(len(held), 2)
        for record in held:
            self.assertTrue(record['rendering_training_excluded'])
            self.assertEqual(record['rendering_exclusion_reason'], 'body_condition_unresolved')
            self.assertEqual(record['user_review']['decision'], 'accepted')
        samples = json.loads((ROOT / 'ML/learned_morphology/body_patch_samples.json').read_text())
        self.assertNotIn('inat_1767459', {r['image_id'] for r in samples['samples']})

    def test_recorded_geometry_sources_remain_eligible(self):
        annotations = json.loads((ROOT / 'ML/learned_morphology/photo_geometry_annotations.json').read_text())
        candidates = {r['image_id']: r for r in build()['candidate_images']}
        for record in annotations['annotations']:
            self.assertIn(record['image_id'], candidates)
            self.assertEqual(candidates[record['image_id']]['review_blocks'], [])

    def test_evaluation_holds_out_one_complete_genus_each_time(self):
        names = ['Aaa one', 'Bbb two', 'Ccc three', 'Ddd four', 'Eee five', 'Fff six']
        rows = [{'species': n, 'features': [10.0, 20.0], 'targets': {'value': i / 10}}
                for i, n in enumerate(names)]
        with patch.object(morphology, 'fit', wraps=morphology.fit) as fit:
            result = morphology.evaluate(rows, 'value', 2)
        self.assertEqual(fit.call_count, len(names))
        self.assertTrue(all(len({r['species'] for r in call.args[0]}) == 5 for call in fit.call_args_list))
        self.assertEqual(result['held_out_species'], 6)


if __name__ == '__main__':
    unittest.main()

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_image_triage_queue as triage
import train_photo_color_pilot as color


class PhotoPilotTests(unittest.TestCase):
    def test_triage_does_not_promote_or_duplicate_source_photos(self):
        data = triage.build()
        photos = [photo for species in data['species'] for photo in species['images']]
        self.assertEqual(data['image_count'], len(photos))
        self.assertEqual(len(photos), len({p['sha256'] for p in photos}))
        self.assertEqual(len(photos), len({p['observation_id'] for p in photos}))
        for photo in photos:
            self.assertEqual(photo['review_status'], 'unreviewed')
            source = json.loads((ROOT / photo['manifest']).read_text())
            record = next(r for r in source if r['image_id'] == photo['image_id'])
            self.assertEqual(record['review_status'], 'unreviewed')

    def test_preliminary_screen_preserves_exclusion_decisions(self):
        screen = json.loads((ROOT / 'ML/learned_morphology/image_triage_screen_001.json').read_text())
        for row in screen['records']:
            if row['screen_status'] != 'rejected_severe_damage':
                continue
            source = json.loads((ROOT / row['manifest']).read_text())
            record = next(r for r in source if r['image_id'] == row['image_id'])
            self.assertEqual(record['review_status'], 'rejected')
            self.assertTrue(record['rendering_training_excluded'])
            self.assertEqual(record['rendering_exclusion_reason'], 'injury')

    def test_real_photo_experiment_stays_exploratory_and_checks_bytes(self):
        measurements = json.loads(color.MEASUREMENTS.read_text())
        for photo in measurements['records']:
            manifest = ROOT / photo['manifest']
            source = json.loads(manifest.read_text())
            match = next(r for r in source if r['image_id'] == photo['image_id'])
            if not (manifest.parent / match['local_path']).is_file():
                self.skipTest('Raw photos are intentionally absent from version control')
        result = color.run()
        self.assertEqual(result['status'], 'exploratory_candidate_not_deployed')
        self.assertNotIn('species', result['feature_ids'])
        self.assertEqual(set(result['models']), {'patch_r', 'patch_g', 'patch_b'})
        self.assertEqual(result['data']['photo_count'], result['data']['observation_count'])
        self.assertEqual(set(result['evaluation']), {'patch_r', 'patch_g', 'patch_b'})
        original_sha = color.sha
        def altered_photo_hash(path):
            return 'changed' if path.suffix.lower() in {'.jpg', '.jpeg', '.png'} else original_sha(path)
        with patch.object(color, 'sha', side_effect=altered_photo_hash):
            with self.assertRaisesRegex(ValueError, 'Photo bytes missing or changed'):
                color.run()


if __name__ == '__main__':
    unittest.main()

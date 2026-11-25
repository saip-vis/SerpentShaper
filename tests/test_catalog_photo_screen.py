import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from summarize_catalog_followup import review_errors
from summarize_image_screen import summarize


class CatalogPhotoScreenTests(unittest.TestCase):
    def test_rejected_review_must_stay_excluded_and_have_history(self):
        self.assertEqual(review_errors({'review_status': 'rejected', 'rendering_training_excluded': True,
                                        'review_history': [{'action': 'reject'}]}), [])
        self.assertIn('nonaccepted_photo_not_excluded', review_errors({'review_status': 'rejected',
                      'rendering_training_excluded': False, 'review_history': [{'action': 'reject'}]}))
        self.assertIn('review_decision_missing_history', review_errors({'review_status': 'rejected',
                      'rendering_training_excluded': True}))

    def test_acceptance_without_identity_and_condition_is_not_valid_review(self):
        self.assertIn('accepted_photo_missing_review_evidence', review_errors({'review_status': 'accepted',
                      'review_history': [{'action': 'accept'}]}))

    def test_screen_cannot_approve_a_thumbnail_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'data/image_pilots/pilot_155_test/manifest.json'
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps([{'image_id': 'one', 'sha256': 'abc', 'review_status': 'unreviewed',
                                             'rendering_training_excluded': True}]))
            screen_path = root / 'ML/image_traits/assistant_catalog_screen_2026.json'
            screen_path.parent.mkdir(parents=True)
            row = {'image_id': 'one', 'sha256': 'abc', 'manifest': str(manifest.relative_to(root)),
                   'species': 'Example species', 'screening_status': 'visual_candidate', 'training_eligible': False}
            screen = {'reviewed_count': 1, 'total_planned': 1, 'records': [row]}
            screen_path.write_text(json.dumps(screen))
            counts, _ = summarize(root)
            self.assertEqual(counts['visual_candidate'], 1)
            row['training_eligible'] = True
            screen_path.write_text(json.dumps(screen))
            with self.assertRaisesRegex(ValueError, 'cannot approve training'):
                summarize(root)


if __name__ == '__main__':
    unittest.main()

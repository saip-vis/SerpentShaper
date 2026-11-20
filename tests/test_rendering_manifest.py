import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from export_rendering_manifest import eligible

class RenderingGateTests(unittest.TestCase):
    def test_exclusion_overrides_acceptance(self):
        row = dict(review_status='accepted', download_status='downloaded', rendering_training_excluded=True)
        self.assertFalse(eligible(row))

    def test_unique_reference_exception_does_not_enable_training(self):
        row = dict(review_status='accepted', download_status='downloaded', reference_only_exception=True)
        self.assertFalse(eligible(row))

    def test_requires_acceptance_and_rejects_supplemental(self):
        row = dict(review_status='unreviewed', download_status='downloaded')
        self.assertFalse(eligible(row))
        row['review_status'] = 'accepted'
        self.assertTrue(eligible(row))
        row['suitability_screening'] = {'category': 'supplemental'}
        self.assertFalse(eligible(row))

    def test_exact_duplicate_copy_is_not_exported(self):
        row = dict(review_status='accepted', download_status='downloaded',
                   duplicate_of={'batch': 'earlier_alias', 'image_id': 'inat_1'})
        self.assertFalse(eligible(row))

if __name__ == '__main__':
    unittest.main()

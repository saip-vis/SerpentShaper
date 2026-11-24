import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_ml_pilot import image_record, build_audit


class PilotAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        payload = b'photo-test-content'
        (self.root / 'photo.jpg').write_bytes(payload)
        self.image = {'image_id':'example', 'local_path':'photo.jpg',
            'sha256':hashlib.sha256(payload).hexdigest(), 'file_available':True,
            'rendering_eligible':True, 'review_status':'accepted', 'photo_license':'cc-by',
            'attribution':'Photographer (CC BY)', 'split_group':'inat_observation_1'}

    def tearDown(self):
        self.temp.cleanup()

    def test_accepted_record_requires_valid_file_license_and_observation(self):
        self.assertTrue(image_record(self.image, self.root)['eligible_for_pilot_after_metadata_checks'])
        for key, value in [('rendering_eligible',False), ('sha256','wrong'),
                           ('photo_license',None), ('attribution',''), ('split_group',None)]:
            with self.subTest(key=key):
                invalid = dict(self.image, **{key:value})
                self.assertFalse(image_record(invalid, self.root)['eligible_for_pilot_after_metadata_checks'])

    def test_review_and_file_gates_cannot_be_bypassed_by_an_image_label(self):
        i = dict(self.image, review_status='unreviewed', rendering_eligible=True)
        row = image_record(i, self.root)
        self.assertFalse(row['eligible_for_pilot_after_metadata_checks'])
        self.assertIn('not_accepted_by_existing_rendering_gate', row['excluded_reasons'])
        excluded = dict(self.image, rendering_training_excluded=True)
        self.assertFalse(image_record(excluded, self.root)['eligible_for_pilot_after_metadata_checks'])
        outside = dict(self.image, local_path='../outside.jpg')
        self.assertFalse(image_record(outside, self.root)['file_available'])
        self.assertIsNone(row['split'])

    def test_audit_requires_all_five_named_pilot_labels(self):
        with self.assertRaisesRegex(ValueError, 'Pilot source label is missing'):
            build_audit({'profiles':[], 'species':[]}, self.root)


if __name__ == '__main__':
    unittest.main()

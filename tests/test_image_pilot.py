import copy
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect_image_pilot import candidates

class PhotoSelectionTests(unittest.TestCase):
    def setUp(self):
        self.source = {'source_name': 'Naja naja', 'image_lookup_name': 'Naja naja'}
        self.taxon = {'id': 1, 'name': 'Naja naja'}
        self.photo = dict(id=10, license_code='cc-by', attribution='Photo author',
                          url='https://inaturalist-open-data.s3.amazonaws.com/photos/10/square.jpg',
                          original_dimensions={'width': 1200, 'height': 800})
        self.obs = dict(id=5, quality_grade='research', taxon={'id': 1}, photos=[self.photo])

    def select(self):
        return candidates(self.obs, self.source, self.taxon, '2026-11-20')

    def test_observation_filter_does_not_license_all_its_photos(self):
        restricted = copy.deepcopy(self.photo)
        restricted.update(id=11, license_code='cc-by-nc')
        self.obs['photos'].append(restricted)
        result = self.select()
        self.assertEqual([r['image_id'] for r in result], ['inat_10'])
        self.assertEqual(result[0]['split_group'], 'inat_observation_5')
        self.assertEqual(result[0]['review_status'], 'unreviewed')
        self.assertIsNone(result[0]['license_version'])

    def test_wrong_taxon_is_rejected_but_subspecies_is_allowed(self):
        self.obs['taxon'] = {'id': 2, 'ancestor_ids': [3]}
        self.assertEqual(self.select(), [])
        self.obs['taxon']['ancestor_ids'].append(1)
        self.assertEqual(len(self.select()), 1)

    def test_small_hidden_or_unattributed_photos_are_rejected(self):
        for changes in [dict(hidden=True), dict(attribution=None), dict(flags=[{'flag':'copyright'}]),
                        dict(original_dimensions={'width': 100, 'height': 100}),
                        dict(original_dimensions={'width': None, 'height': None}),
                        dict(url='https://example.com/square.jpg')]:
            with self.subTest(changes=changes):
                self.obs['photos'] = [dict(self.photo, **changes)]
                self.assertEqual(self.select(), [])

if __name__ == '__main__':
    unittest.main()

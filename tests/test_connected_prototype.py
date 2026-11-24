import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import train_connected_prototype as connected
import train_photo_color_pilot as color


class ConnectedPrototypeTests(unittest.TestCase):
    def test_authored_targets_are_bounded_and_describe_designs(self):
        presets = {p['source_species_name']: p for p in json.loads(connected.PRESETS.read_text())['presets']}
        for preset in presets.values():
            targets = connected.targets(preset)
            self.assertEqual(len(targets), len(connected.TARGETS))
            self.assertTrue(all(0 <= v <= 1 for v in targets))
        cobra = dict(zip(connected.TARGETS, connected.targets(presets['Naja kaouthia'])))
        diamond = dict(zip(connected.TARGETS, connected.targets(presets['Crotalus atrox'])))
        self.assertEqual(cobra['hood'], 1)
        self.assertEqual(diamond['hood'], 0)
        self.assertEqual(diamond['rattle'], 1)
        self.assertEqual(diamond['diamond'], 1)
        sea = dict(zip(connected.TARGETS, connected.targets(presets['Hydrophis platurus'])))
        coral = dict(zip(connected.TARGETS, connected.targets(presets['Micrurus alleni'])))
        self.assertEqual(sea['paddle'], 1)
        self.assertEqual(coral['bandAccent'], 1)

    def test_grouped_evaluation_holds_out_whole_genera(self):
        names = ['Aaa one', 'Aaa two', 'Bbb three', 'Ccc four', 'Ddd five']
        rows = [{'species': name, 'features': [10 + 2*i, 20, 30],
                 'targets': [i / 5] * len(connected.TARGETS)} for i, name in enumerate(names)]
        with patch.object(connected, 'fit', wraps=connected.fit) as mocked:
            result = connected.evaluate(rows, 3)
        self.assertEqual(mocked.call_count, 4)
        self.assertEqual(result['held_out_species'], len(names))
        for call in mocked.call_args_list:
            genera = {row['species'].split()[0] for row in call.args[0]}
            self.assertEqual(len(genera), 3)
        fitted = connected.fit(rows, 3)
        blank = connected.predict([{'features': [None, 20, 30]}], fitted)
        zero = connected.predict([{'features': [0, 20, 30]}], fitted)
        self.assertTrue(np.allclose(blank, zero))

    def test_real_bundle_retrains_with_photo_review_gates(self):
        measurements = json.loads(color.MEASUREMENTS.read_text())
        for photo in measurements['records']:
            manifest = ROOT / photo['manifest']
            source = json.loads(manifest.read_text())
            match = next(r for r in source if r['image_id'] == photo['image_id'])
            if not (manifest.parent / match['local_path']).is_file():
                self.skipTest('Raw photos are intentionally absent from version control')
        model, report = connected.train()
        self.assertEqual(model['status'], 'experimental_hybrid_not_biological_prediction')
        self.assertGreaterEqual(model['provenance']['authored_preset_species'], 4)
        self.assertGreater(model['provenance']['photo_count'], 0)
        self.assertEqual(len(model['photo_sources']), model['provenance']['photo_count'])
        self.assertTrue(all(source['attribution'] and source['photo_page'] for source in model['photo_sources']))
        self.assertNotIn('species', model['feature_ids'])
        self.assertEqual(len(model['training_vectors']), model['provenance']['venom_profile_rows'])
        self.assertEqual(len(model['training_sources']), len(model['training_vectors']))
        _, profiles = connected.load_profiles()
        for source in model['training_sources']:
            self.assertIn({'profile_id': source['profile_id'], 'features': source['features']}, profiles[source['species']])
        self.assertEqual(report['evaluation']['held_out_species'], model['provenance']['authored_preset_species'])
        saved = json.loads(connected.REPORT.read_text())
        for target in connected.TARGETS:
            self.assertAlmostEqual(report['parity_example']['expected_outputs'][target],
                                   saved['parity_example']['expected_outputs'][target], places=9)


if __name__ == '__main__':
    unittest.main()

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_staged_venom_profile import validate


class StagedVenomProfileTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((ROOT / 'ML/research_updates/black_mamba_2025.json').read_text())

    def test_real_candidate_validates_but_is_not_training_eligible(self):
        self.assertEqual(validate(self.record), [])
        self.assertFalse(self.record['training_eligible'])

    def test_rejects_duplicate_and_inconsistent_figure_total(self):
        bad = copy.deepcopy(self.record)
        bad['reported_values'].append(copy.deepcopy(bad['reported_values'][0]))
        errors = validate(bad)
        self.assertTrue(any('unique' in e for e in errors))
        self.assertTrue(any('total' in e for e in errors))

    def test_rejects_training_promotion_and_missing_pairing_context(self):
        self.record['training_eligible'] = True
        self.record['sample'].pop('specimen_count')
        errors = validate(self.record)
        self.assertTrue(any('excluded' in e for e in errors))
        self.assertTrue(any('specimen_count' in e for e in errors))


if __name__ == '__main__':
    unittest.main()

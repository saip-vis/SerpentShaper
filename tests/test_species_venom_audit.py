import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_species_venom_profiles import audit, DB, PRESETS, SPEC


class SpeciesVenomAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = audit(DB, json.loads(PRESETS.read_text())['presets'],
                           json.loads(SPEC.read_text())['controls'])

    def test_summary_and_missing_lists_match_records(self):
        rows = self.result['species']
        self.assertEqual(self.result['summary']['rendering_preset_source_labels'], len(rows))
        self.assertEqual(self.result['summary']['labels_without_eligible_proteomics'],
                         sum(not row['eligible_proteomic_profile_count'] for row in rows))
        for species in rows:
            for profile in species['profiles']:
                self.assertEqual(profile['reported_control_count'], len(profile['reported_control_ids']))
                self.assertEqual(profile['reported_control_count'] + len(profile['missing_control_ids']), 12)
                self.assertFalse(set(profile['reported_control_ids']) & set(profile['missing_control_ids']))

    def test_known_uncertainty_does_not_rewrite_record(self):
        mamba = next(s for s in self.result['species'] if s['source_species_name'] == 'Dendroaspis polylepis')
        source = next(p for p in mamba['profiles'] if p['profile_id'] == 'vd2023_e2d1aa974518_r189')
        self.assertEqual(source['uncertain_categories'][0]['toxin_id'], 'vd2023_H')
        with sqlite3.connect(DB.as_uri() + '?mode=ro', uri=True) as conn:
            value = conn.execute('SELECT abundance_pct FROM components WHERE profile_id=? AND toxin_id=?',
                                 (source['profile_id'], 'vd2023_H')).fetchone()[0]
        self.assertEqual(value, 2.9)


if __name__ == '__main__':
    unittest.main()

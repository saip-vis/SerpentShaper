"""Verify provenance, missing-data semantics and isolation of rendering proposals."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_physical_profiles import build, FIELDS, missing, render_markdown


class PhysicalProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'data/processed/species_catalog/catalog.json').read_text())
        cls.extracted = json.loads((ROOT / 'sources/morphology/repttraits_catalog_extract.json').read_text())
        cls.notes = json.loads((ROOT / 'config/morphology_notes.json').read_text())['species']
        cls.profiles = build(ROOT, cls.catalog, cls.extracted, cls.notes)

    def test_catalog_coverage_and_source_labels_preserved(self):
        self.assertEqual({p['species_id']: p['source_species_name'] for p in self.profiles},
                         {s['species_id']: s['source_species_name'] for s in self.catalog['species']})
        self.assertEqual(len(self.profiles), len(self.catalog['species']))
        by_name = {p['source_species_name']: p for p in self.profiles}
        self.assertNotEqual(by_name['Cryptelytrops purpureomaculatus']['species_id'],
                            by_name['Trimeresurus purpureomaculatus']['species_id'])
        self.assertIsNone(by_name['Bothrops colombiensis']['compilation_match']['row'])

    def test_traits_retain_exact_values_and_per_trait_citations(self):
        raw = {r['values']['Species']: r for r in self.extracted['Data']}
        refs = {r['values']['Species']: r for r in self.extracted['Sources of individual trait val']}
        for p in self.profiles:
            match = p['compilation_match']['workbook_species_name']
            for key, field in FIELDS.items():
                trait = p['compilation_traits'][key]
                expected = raw[match]['values'].get(field) if match else None
                self.assertEqual(trait['raw_value'], expected)
                self.assertEqual(trait['value'], None if missing(expected) else expected)
                if trait['value'] is not None:
                    self.assertTrue(trait['data_cell'].startswith('Data!'))
                    self.assertEqual(trait['citation'], None if missing(refs[match]['values'].get(field)) else refs[match]['values'][field])
        self.assertFalse(missing(0))
        self.assertTrue(missing('NA'))

    def test_no_family_or_genus_imputation_and_no_venom_mapping(self):
        profiles = build(ROOT, self.catalog, self.extracted, {})
        self.assertTrue(all(all(v is None for v in p['descriptions'].values()) for p in profiles))
        for p in profiles:
            proposal = p['rendering_proposals']
            self.assertIsNone(proposal['numerical_shape_ratios'])
            self.assertIsNone(proposal['absolute_color_values'])
            self.assertIsNone(proposal['venom_trait_mapping'])

    def test_ambiguous_juvenile_statistic_is_held_and_not_a_maximum(self):
        present = [p['compilation_traits']['juvenile_svl_mm_ambiguous_statistic'] for p in self.profiles
                   if p['compilation_traits']['juvenile_svl_mm_ambiguous_statistic']['value'] is not None]
        self.assertTrue(present)
        self.assertTrue(all(t['status'] == 'needs_review' for t in present))
        self.assertFalse(any('maximum_juvenile' in p['compilation_traits'] for p in self.profiles))

    def test_kaouthia_traits_retain_individual_sources(self):
        profile = next(p for p in self.profiles if p['source_species_name'] == 'Naja kaouthia')
        self.assertTrue(all(profile['descriptions'].values()))
        for key, trait in profile['descriptions'].items():
            ref = self.notes['Naja kaouthia']['trait_references'][key]
            self.assertEqual(trait['source_url'], ref['source_url'])
            self.assertEqual(trait['source_locator'], ref['locator'])
        self.assertIn('tail was lost', profile['descriptions']['tail']['text'])
        self.assertIsNone(profile['rendering_proposals']['numerical_shape_ratios'])

    def test_illustration_contract_preserves_identity_and_surface(self):
        spec = json.loads((ROOT / 'config/illustration_specifications.json').read_text())
        species = {p['species_id']: p for p in self.profiles}
        for sid, brief in spec['species'].items():
            self.assertEqual(brief['source_species_name'], species[sid]['source_species_name'])
            views = {v['id']: v for v in brief['views']}
            for marking in brief['markings']:
                self.assertTrue(all(views[v]['surface'] == 'dorsal' for v in marking['visible_in']))
            self.assertTrue(all(v is None for k, v in brief['artistic_parameters'].items() if k != 'label'))
            self.assertTrue(all(r['selected_photo_id'] is None for r in brief['reference_requirements']))
            self.assertIn('pending', brief['status'])
            self.assertIsNone(brief['venom_trait_mapping'])

    def test_build_is_deterministic_and_does_not_mutate_inputs(self):
        catalog = copy.deepcopy(self.catalog)
        extracted = copy.deepcopy(self.extracted)
        notes = copy.deepcopy(self.notes)
        paths = sorted((ROOT / 'data/image_pilots').glob('pilot_*/manifest.json'))
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        self.assertEqual(self.profiles, build(ROOT, catalog, extracted, notes))
        self.assertEqual(catalog, self.catalog)
        self.assertEqual(extracted, self.extracted)
        self.assertEqual(notes, self.notes)
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})


if __name__ == '__main__':
    unittest.main()

"""Check join integrity and conservative handling of mismatches and missing files."""
from contextlib import closing
import copy
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_species_catalog import build


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build(ROOT)

    def test_every_profile_and_image_preserved_once(self):
        c = self.catalog
        ids = [p for s in c['species'] for p in s['venom_profile_ids']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {p['profile_id'] for p in c['profiles']})
        source = sum(len(json.loads(p.read_text())) for p in (ROOT / 'data/image_pilots').glob('pilot_*/manifest.json'))
        self.assertEqual(c['summary']['image_records'], source)
        with closing(sqlite3.connect(ROOT / 'data/processed/venom_diet_2023/serpentshaper.sqlite')) as db:
            expected = db.execute("SELECT count(*) FROM components WHERE value_status != 'missing'").fetchone()[0]
        self.assertEqual(sum(len(p['reported_components']) for p in c['profiles']), expected)

    def test_review_and_alias_provenance_preserved(self):
        species = {s['source_species_name']: s for s in self.catalog['species']}
        alias = species['Cryptelytrops purpureomaculatus']
        self.assertTrue(alias['alias_reference'])
        self.assertIn('Trimeresurus purpureomaculatus', alias['shared_provider_taxa_with'])
        self.assertTrue(all(i['species_link_status'] == 'documented_alias' for i in alias['images']))
        for s in species.values():
            for i in s['images']:
                if i.get('review_status') != 'accepted' or i.get('rendering_training_excluded') or i.get('duplicate_of'):
                    self.assertFalse(i['rendering_eligible'])
        self.assertIn('taxon_unresolved', str(species['Bothrops colombiensis']['collection_notes']))

    def test_missing_files_and_taxon_mismatch_do_not_become_eligible(self):
        original = next(i for s in self.catalog['species'] for i in s['images'] if i['rendering_eligible'])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = root / 'data/processed/venom_diet_2023'
            data.mkdir(parents=True)
            with closing(sqlite3.connect(ROOT / 'data/processed/venom_diet_2023/serpentshaper.sqlite')) as source:
                with closing(sqlite3.connect(data / 'serpentshaper.sqlite')) as destination:
                    source.backup(destination)
            reports = root / 'reports/image_research'
            (reports / 'remaining_species_downloads').mkdir(parents=True)
            (reports / 'imaging_gaps.json').write_text('{"taxa": []}')
            (reports / 'remaining_species_downloads/progress.json').write_text('{"species": {}}')
            batch = root / 'data/image_pilots/pilot_001_test'
            batch.mkdir(parents=True)
            row = copy.deepcopy(original)
            row['local_path'] = 'images/missing.jpg'
            row['provider_species_name'] = 'Unrelated species'
            (batch / 'manifest.json').write_text(json.dumps([row]))
            c = build(root)
            image = next(i for s in c['species'] for i in s['images'])
            self.assertFalse(image['file_available'])
            self.assertFalse(image['rendering_eligible'])
            self.assertEqual(image['species_link_status'], 'unresolved')
            row['local_path'] = '../../outside.jpg'
            (batch / 'manifest.json').write_text(json.dumps([row]))
            with self.assertRaisesRegex(ValueError, 'Unsafe image path'):
                build(root)


if __name__ == '__main__':
    unittest.main()

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from download_remaining_species import inspect_filters

class FilterDiagnosticsTests(unittest.TestCase):
    def test_null_dimensions_are_counted_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cache = root / 'api_cache'
            cache.mkdir()
            (cache / 'example.json').write_text(json.dumps({
                'request_url': 'https://api.inaturalist.org/v1/observations?taxon_id=1',
                'data': {'results': [{'photos': [
                    {'original_dimensions': {'width': None, 'height': None},
                     'license_code': 'cc-by-nc', 'attribution': 'Author'},
                    {'original_dimensions': {'width': 1200, 'height': 800},
                     'license_code': 'cc-by', 'attribution': 'Author'}]}]}}))
            result = inspect_filters(root)
            self.assertEqual(result['photos_examined'], 2)
            self.assertEqual(result['too_small_or_dimensions_missing'], 1)
            self.assertEqual(result['license_not_allowed'], 1)

if __name__ == '__main__':
    unittest.main()

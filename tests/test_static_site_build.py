import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location('render_build', ROOT / 'scripts/build_render_site.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StaticSiteBuildTests(unittest.TestCase):
    def test_public_files_include_generator_and_exclude_private_data(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'site'
            MODULE.build(destination)
            for relative in ('index.html', 'MainInterface/home.html', 'MainInterface/about.html',
                             'MainInterface/index.html', 'MainInterface/connected-model.js',
                             'MainInterface/assets/cobra-foreground.png',
                             'PhysicalRendererTest/presets/species-presets.js'):
                self.assertTrue((destination / relative).is_file(), relative)
            self.assertFalse((destination / 'data').exists())
            self.assertFalse((destination / 'StudyServer.py').exists())
            self.assertIn('MainInterface/home.html', (destination / 'index.html').read_text())
            MODULE.build(destination)  # Rebuilding our own output is supported.

    def test_refuses_to_replace_an_unrelated_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'existing'
            destination.mkdir()
            (destination / 'keep.txt').write_text('keep')
            with self.assertRaisesRegex(ValueError, 'Refusing to replace'):
                MODULE.build(destination)
            self.assertTrue((destination / 'keep.txt').is_file())


if __name__ == '__main__':
    unittest.main()

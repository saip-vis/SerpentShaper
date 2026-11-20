from copy import deepcopy
import hashlib
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ImageReview import ReviewStore, ReviewError, make_handler

class ImageReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.batch = 'pilot_001_test_snake'
        folder = self.root / self.batch
        (folder/'images').mkdir(parents=True)
        original = folder/'images/test.jpg'
        Image.new('RGB', (2400, 1800), '#226644').save(original)
        self.original = original.read_bytes()
        self.row = dict(image_id='inat_1', source_species_name='Naja naja', provider_species_name='Naja naja',
            review_id='SC01', observation_id=1, taxon_id=53492, local_path='images/test.jpg',
            download_status='downloaded', review_status='unreviewed', original_width=2400, original_height=1800,
            photo_license='cc-by', attribution='Test author', sha256=hashlib.sha256(self.original).hexdigest(),
            source_page='https://www.inaturalist.org/observations/1', photo_page='https://www.inaturalist.org/photos/1',
            rendering_training_excluded=True, rendering_exclusion_reason='pending_visual_review')
        self.manifest = folder/'manifest.json'
        self.write([self.row])
        self.store = ReviewStore(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, rows):
        self.manifest.write_text(json.dumps(rows))

    def payload(self, **kwargs):
        result = dict(batch=self.batch, image_id='inat_1', revision=self.store.detail(self.batch,'inat_1')['revision'],
            decision='accept', species_confidence='confirmed', body_condition='no_visible_injury',
            framing='full_body', viewpoint='dorsal', pose='extended', issues=[], notes='Clear body view.')
        result.update(kwargs)
        return result

    def test_accept_persists_provenance_backup_and_refreshes_export(self):
        before = self.manifest.read_bytes()
        saved = self.store.update(self.payload())
        self.assertEqual(saved['review_status'], 'accepted')
        self.assertFalse(saved['rendering_training_excluded'])
        self.assertEqual(saved['sha256'], self.row['sha256'])
        backups = list((self.root/'_review_backups'/self.batch).glob('*.json'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), before)
        self.assertEqual(len(json.loads((self.root/'rendering_manifest.json').read_text())['images']),1)
        self.assertEqual(ReviewStore(self.root).detail(self.batch,'inat_1')['review_status'],'accepted')
        self.store.update(self.payload(decision='reject', issues=['severe_blur'], notes='Blurred.'))
        self.assertEqual(json.loads((self.root/'rendering_manifest.json').read_text())['images'],[])

    def test_accept_requires_identity_and_explicit_healthy_assessment(self):
        before = self.manifest.read_bytes()
        for change in [dict(species_confidence='unknown'),dict(body_condition='unknown'),dict(framing='unknown'),dict(issues=['handling'])]:
            with self.subTest(change=change), self.assertRaises(ReviewError):
                self.store.update(self.payload(**change))
        self.assertEqual(self.manifest.read_bytes(), before)

    def test_known_injury_cannot_be_cleared_by_accept_form(self):
        self.row.update(rendering_exclusion_reason='injury',review_status='rejected')
        self.write([self.row])
        with self.assertRaisesRegex(ReviewError, 'injury/deformity'):
            self.store.update(self.payload())
        with self.assertRaisesRegex(ReviewError, 'uniquely useful'):
            self.store.update(self.payload(decision='reference'))
        row = self.store.update(self.payload(decision='reference', unique_reference=True,
            notes='Unique visible anatomy unavailable in healthy references.'))
        self.assertEqual(row['review_status'], 'reference_only')
        self.assertTrue(row['reference_only_exception'])
        self.assertTrue(row['rendering_training_excluded'])
        self.assertEqual(json.loads((self.root/'rendering_manifest.json').read_text())['images'],[])

    def test_duplicate_cannot_enter_rendering(self):
        self.row['duplicate_of']={'batch':'pilot_000_original','image_id':'inat_1'}
        self.write([self.row])
        with self.assertRaisesRegex(ReviewError,'duplicate'):
            self.store.update(self.payload())

    def test_stale_revision_conflicts_without_overwriting(self):
        payload = self.payload()
        self.row['review_notes'] = 'A second reviewer changed this.'
        self.write([self.row])
        with self.assertRaises(ReviewError) as error:
            self.store.update(payload)
        self.assertEqual(error.exception.status,409)
        self.assertEqual(json.loads(self.manifest.read_text())[0]['review_notes'],self.row['review_notes'])

    def test_undo_restores_original_review_state_and_export(self):
        saved = self.store.update(self.payload())
        restored = self.store.update(dict(batch=self.batch,image_id='inat_1',revision=saved['revision'],action='undo'))
        self.assertEqual(restored['review_status'],'unreviewed')
        self.assertTrue(restored['rendering_training_excluded'])
        self.assertNotIn('human_review', restored)
        self.assertEqual(restored['review_history'][-1]['action'],'undo')
        self.assertEqual(json.loads((self.root/'rendering_manifest.json').read_text())['images'],[])

    def test_preview_is_bounded_and_original_unchanged(self):
        for size, limit in [('thumb',320),('preview',1600)]:
            path=self.store.preview(self.batch,'inat_1',size)
            with Image.open(path) as view:
                self.assertLessEqual(max(view.size),limit)
        self.assertEqual((self.root/self.batch/'images/test.jpg').read_bytes(),self.original)

    def test_path_escape_and_missing_image_are_rejected(self):
        with self.assertRaises(ReviewError):
            self.store.read('../outside')
        self.row['local_path']='../../outside.jpg'
        self.write([self.row])
        with self.assertRaises(ReviewError):
            self.store.preview(self.batch,'inat_1','preview')

    def test_http_write_requires_token_and_matching_origin(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.store))
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urlopen(base+'/api/catalog') as response:
                catalog=json.load(response)
            headers={'Content-Type':'application/json'}
            for extra in [{},{'X-Review-Token':catalog['token'],'Origin':'https://example.com'}]:
                request=Request(base+'/api/review',data=json.dumps(self.payload()).encode(),headers=dict(headers,**extra))
                with self.assertRaises(HTTPError) as error:
                    urlopen(request)
                self.assertEqual(error.exception.code,403)
            request=Request(base+'/api/review',data=json.dumps(self.payload()).encode(),headers=dict(headers,**{'X-Review-Token':catalog['token'],'Origin':base}))
            with urlopen(request) as response:
                self.assertEqual(json.load(response)['review_status'],'accepted')
        finally:
            server.shutdown();server.server_close();worker.join()

if __name__ == '__main__':
    unittest.main()

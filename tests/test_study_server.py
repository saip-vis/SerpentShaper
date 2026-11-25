"""Exercise the local HTTP boundary when loopback sockets are available."""
from http.server import ThreadingHTTPServer
import base64
import json
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from StudyServer import make_handler
from study_retrieval import StudyIndex


class StudyServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try: cls.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(StudyIndex()))
        except PermissionError as exc: raise unittest.SkipTest('Loopback binding is unavailable') from exc
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)

    def get(self,path):
        with urlopen(self.base+path,timeout=4) as response:return response.read()

    def post(self,path,payload,origin=None):
        request=Request(self.base+path,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Origin':origin or self.base})
        with urlopen(request,timeout=4) as response:return json.load(response)

    def test_upload_search_clear_and_origin(self):
        page=self.get('/MainInterface/index.html');self.assertIn(b'study-app.js',page)
        result=self.post('/api/study-upload',{'name':'research.txt','content':base64.b64encode(b'Venom PLA2: 35%.').decode()})
        self.assertEqual(result['name'],'research.txt')
        result=json.loads(self.get('/api/study-search?q=PLA2'))['results'][0]
        self.assertEqual(result['page'],1);self.assertEqual(result['suggestions'][0]['value'],35)
        with patch('study_answer.answer',return_value={'answer':'PLA2 was 35% [1].','sources':[],'citations_well_formed':True}):
            generated=self.post('/api/study-answer',{'question':'How much PLA2?'})
        self.assertIn('[1]',generated['answer'])
        with self.assertRaises(HTTPError) as denied:self.post('/api/study-clear',{},'http://attacker.invalid')
        self.assertEqual(denied.exception.code,403)
        with self.assertRaises(HTTPError) as denied:self.get('/data/processed/species_catalog/catalog.json')
        self.assertEqual(denied.exception.code,404)
        self.assertTrue(self.post('/api/study-clear',{})['cleared'])
        self.assertEqual(json.loads(self.get('/api/study-search?q=PLA2'))['results'],[])

if __name__=='__main__':unittest.main()

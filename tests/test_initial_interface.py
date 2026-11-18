import hashlib
from pathlib import Path
import sqlite3
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from InitialInterfaceTest import Interface,APIError,DEFAULT_DB

class InterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.digest=hashlib.sha256(DEFAULT_DB.read_bytes()).hexdigest()
        cls.app=Interface()
        with sqlite3.connect(DEFAULT_DB) as conn:
            cls.held=conn.execute("SELECT profile_id FROM profiles WHERE ingestion_status='needs_review' LIMIT 1").fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        assert hashlib.sha256(DEFAULT_DB.read_bytes()).hexdigest()==cls.digest

    def test_default_filters_out_held_profiles(self):
        result=self.app.profiles(limit=100)
        self.assertTrue(all(p['ingestion_status']=='ready_with_caveats' for p in result['items']))
        self.assertGreater(self.app.profiles(include_held=True)['total'],result['total'])

    def test_held_detail_requires_explicit_opt_in(self):
        with self.assertRaises(APIError) as cm:self.app.profile(self.held)
        self.assertEqual(cm.exception.status,403)
        self.assertEqual(self.app.profile(self.held,True)['profile']['ingestion_status'],'needs_review')

    def test_filter_pagination_and_literal_search(self):
        p=self.app.profiles(query='Naja',measurement_type='proteomics',limit=2)
        self.assertTrue(p['items'])
        self.assertTrue(all('naja' in x['species_name'].lower() and x['measurement_type']=='proteomics' for x in p['items']))
        self.assertNotEqual(p['items'][0]['profile_id'],self.app.profiles(query='Naja',measurement_type='proteomics',limit=2,offset=2)['items'][0]['profile_id'])
        self.assertEqual(self.app.profiles(query="' OR 1=1 --")['total'],0)
        self.assertEqual(self.app.profiles(query='%')['total'],0)

    def test_original_missing_values_and_provenance_survive(self):
        pid=self.app.profiles()['items'][0]['profile_id']
        data=self.app.profile(pid)
        self.assertEqual(len(data['components']),130)
        self.assertTrue(any(c['value_status']=='missing' and c['abundance_pct'] is None for c in data['components']))
        self.assertTrue(data['source']['url'].startswith('https://doi.org/'))
        self.assertTrue(all(c['source_cell'] for c in data['components']))

    def test_valid_custom_composition_and_explicit_zero(self):
        d=self.app.validate({'components':[{'toxin_id':'vd2023_E','abundance_pct':100},{'toxin_id':'vd2023_T','abundance_pct':0}]})
        self.assertTrue(d['valid'])
        self.assertEqual(d['components'][1]['value_status'],'reported_zero')

    def test_missing_invalid_and_unknown_components(self):
        for value in [None,'','NaN',True,-1,101,'0,002,',{},[]]:
            d=self.app.validate({'components':[{'toxin_id':'vd2023_E','abundance_pct':value}]})
            self.assertFalse(d['valid'],value)
        self.assertFalse(self.app.validate({'components':[{'toxin_id':'imaginary','abundance_pct':100}]})['valid'])

    def test_duplicates_and_totals(self):
        self.assertFalse(self.app.validate({'components':[{'toxin_id':'vd2023_E','abundance_pct':50}]*2})['valid'])
        for total in [0,90,99.98]:
            self.assertFalse(self.app.validate({'components':[{'toxin_id':'vd2023_E','abundance_pct':total}]})['valid'])
        self.assertTrue(self.app.validate({'components':[{'toxin_id':'vd2023_E','abundance_pct':'99.99'}]})['valid'])

    def test_dictionary_warnings_and_payload_shape(self):
        d=self.app.validate({'components':[{'toxin_id':'vd2023_G','abundance_pct':100}]})
        self.assertTrue(d['valid'])
        self.assertTrue(d['warnings'])
        for payload in [[],None,{}, {'components':'wrong'}]:
            with self.assertRaises(APIError):self.app.validate(payload)

    def test_database_connections_are_read_only(self):
        conn=self.app.connect()
        try:
            with self.assertRaises(sqlite3.OperationalError):conn.execute('DELETE FROM profiles')
        finally:conn.close()

if __name__=='__main__':unittest.main()

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

    def test_input_catalog_is_bound_to_original_categories(self):
        catalog=self.app.input_spec()
        controls=catalog['spec']['controls']
        self.assertEqual([c['id'] for c in controls if c['tier']=='primary'],['3ftx','pla2','svmp','svsp'])
        self.assertEqual(sum(c['tier']=='advanced' for c in controls),8)
        ids=[tid for c in controls for tid in c['source_toxin_ids']]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertNotEqual(next(c for c in controls if c['id']=='ctl')['source_toxin_ids'],
                            next(c for c in controls if c['id']=='snaclec')['source_toxin_ids'])
        self.assertTrue(all(c['definition'] and c['boundaries'] and c['evidence_ids'] for c in controls))
        self.assertTrue(all(e['source_url'] and e['limits'] for e in catalog['evidence']))

    def source_profile_id(self,row=2):
        with sqlite3.connect(DEFAULT_DB) as conn:
            return conn.execute('SELECT profile_id FROM profiles WHERE source_row=?',(row,)).fetchone()[0]

    def test_import_without_edits_retains_every_component(self):
        pid=self.source_profile_id()
        source=self.app.profile(pid)
        result=self.app.validate({'source_profile_id':pid,'components':[]})
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['components']),130)
        by_id={c['toxin_id']:c for c in result['components']}
        for original in source['components']:
            new=by_id[original['toxin_id']]
            self.assertEqual(new['abundance_pct'],original['abundance_pct'])
            self.assertEqual(new['value_status'],original['value_status'])
            self.assertEqual(new['source_cell'],original['source_cell'])
            self.assertEqual(new['source_raw_value'],original['raw_value'])
            self.assertEqual(new['origin'],'source')
        self.assertEqual(result['source_context']['profile_id'],pid)
        self.assertEqual(result['measurement_type'],'user_defined')

    def test_import_edits_do_not_drop_source_only_values(self):
        pid=self.source_profile_id()
        changes=[{'toxin_id':'vd2023_T','abundance_pct':41},{'toxin_id':'vd2023_AZ','abundance_pct':25.5}]
        result=self.app.validate({'source_profile_id':pid,'components':changes})
        self.assertTrue(result['valid'])
        values={c['toxin_id']:c for c in result['components']}
        self.assertEqual(len(values),130)
        self.assertEqual(values['vd2023_BP']['abundance_pct'],4.6)
        self.assertEqual(values['vd2023_ED']['abundance_pct'],2.5)
        self.assertEqual(values['vd2023_T']['origin'],'user_edit')
        original={c['toxin_id']:c for c in self.app.profile(pid)['components']}
        self.assertEqual(original['vd2023_T']['abundance_pct'],42)

    def test_import_rejects_source_only_edits_and_missing_replacements(self):
        pid=self.source_profile_id()
        bad=self.app.validate({'source_profile_id':pid,'components':[{'toxin_id':'vd2023_ED','abundance_pct':10}]})
        self.assertFalse(bad['valid'])
        self.assertTrue(any('source-only' in e for e in bad['errors']))
        self.assertEqual(next(c for c in bad['components'] if c['toxin_id']=='vd2023_ED')['abundance_pct'],2.5)
        cleared=self.app.validate({'source_profile_id':pid,'components':[{'toxin_id':'vd2023_T','abundance_pct':''}]})
        self.assertFalse(cleared['valid'])
        self.assertEqual(next(c for c in cleared['components'] if c['toxin_id']=='vd2023_T')['value_status'],'missing')

    def test_import_rejects_transcriptomic_and_held_profiles(self):
        for pid in [self.source_profile_id(14),self.held]:
            with self.assertRaises(APIError):self.app.validate({'source_profile_id':pid,'components':[]})

    def test_balance_and_no_automatic_normalization(self):
        d=self.app.validate({'components':[{'toxin_id':'vd2023_E','abundance_pct':60},{'toxin_id':'vd2023_T','abundance_pct':30}]})
        self.assertEqual(d['sum_pct'],90)
        self.assertEqual(d['unallocated_pct'],10)
        self.assertEqual(d['overallocated_pct'],0)
        self.assertEqual(d['components'][0]['abundance_pct'],60)
        d=self.app.validate({'components':[{'toxin_id':'vd2023_E','abundance_pct':60},{'toxin_id':'vd2023_T','abundance_pct':50}]})
        self.assertFalse(d['valid'])
        self.assertEqual(d['overallocated_pct'],10)

if __name__=='__main__':unittest.main()

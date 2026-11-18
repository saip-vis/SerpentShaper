"""Tests for ingestion boundaries and preservation of source meaning."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from clean_venom_data import parse_percentage, normalize_species, literal_sum, make_records
from audit_sources import xlsx_sheets

class CleaningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = json.loads((ROOT/'config/cleaning_rules.json').read_text())
        cls.source_rows = dict(xlsx_sheets(ROOT/'data/raw/venom_diet_2023/Supp. Mat. 1.xlsx'))['RAW_DATABASE_VENOM']

    def fixture(self, kind='proteome', value='100'):
        return [copy.deepcopy(self.source_rows[0]),
                {'row':2,'cells':{'A':'Naja_naja','B':'  India  ','C':kind,'E':value,'EE':value}}]

    def test_missing_is_not_zero(self):
        self.assertEqual(parse_percentage(''), (None,'missing'))
        self.assertEqual(parse_percentage(None), (None,'missing'))
        self.assertEqual(parse_percentage('0'), (Decimal(0),'reported_zero'))

    def test_reject_malformed_nonfinite_and_out_of_range(self):
        for text in ['0,002,','NaN','Infinity','-1','101','#DIV/0!']:
            self.assertEqual(parse_percentage(text), (None,'invalid'))

    def test_names_only_get_safe_formatting(self):
        self.assertEqual(normalize_species('  Naja_naja  '), 'Naja naja')
        self.assertEqual(normalize_species('Crotalus_durissus_cascavella'), 'Crotalus durissus cascavella')

    def test_measurement_types_are_not_guessed(self):
        for kind, expected in [('trancriptome','transcriptomics'),('proteome ','proteomics'),('proteoje','unknown')]:
            p,_,_,q=make_records(self.fixture(kind), self.rules, 'test')
            self.assertEqual(p[0]['measurement_type'], expected)
            self.assertEqual(p[0]['ingestion_status']=='needs_review', expected=='unknown')

    def test_literal_formulas_are_restricted_and_checked(self):
        self.assertEqual(literal_sum('12.49+2.1+20.48'), Decimal('35.07'))
        for expression in ['SUM(E2:F2)','E2+1','__import__("os")','1/0','1*100']:
            self.assertIsNone(literal_sum(expression))
        p,_,_,q=make_records(self.fixture(),self.rules,'test',{'E2':'50+50'})
        self.assertEqual(p[0]['ingestion_status'],'ready_with_caveats')
        self.assertIn('literal_formula_verified', [x['code'] for x in q])
        p,_,_,_=make_records(self.fixture(),self.rules,'test',{'E2':'50+40'})
        self.assertEqual(p[0]['ingestion_status'],'needs_review')

    def test_total_is_not_normalized(self):
        p,c,_,_=make_records(self.fixture(value='90'),self.rules,'test')
        self.assertEqual(c[0]['abundance_pct'],90)
        self.assertEqual(p[0]['component_sum_pct'],90)
        self.assertEqual(p[0]['ingestion_status'],'needs_review')

    def test_duplicate_candidates_are_retained_and_quarantined(self):
        rows=self.fixture()
        rows.append(copy.deepcopy(rows[1]));rows[2]['row']=3
        p,c,_,q=make_records(rows,self.rules,'test')
        self.assertEqual(len(p),2)
        self.assertEqual(len(c),260)
        self.assertTrue(all(x['ingestion_status']=='needs_review' for x in p))
        self.assertEqual(p[0]['duplicate_group'],p[1]['duplicate_group'])

    def test_original_values_and_unknown_categories_survive(self):
        rows=self.fixture(value='99')
        rows[1]['cells']['G']='1'
        p,c,d,q=make_records(rows,self.rules,'test')
        self.assertEqual(p[0]['species_original'],'Naja_naja')
        self.assertEqual(c[0]['raw_value'],'99')
        self.assertEqual(next(x for x in d if x['source_column']=='G')['mapping_status'],'unreviewed')
        self.assertEqual(p[0]['ingestion_status'],'ready_with_caveats')

if __name__=='__main__':
    unittest.main()

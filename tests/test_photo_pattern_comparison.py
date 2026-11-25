"""Guard species weighting and genus-held-out pattern development checks."""
import sys
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from compare_photo_pattern_models import evaluate

class PhotoPatternComparisonTests(unittest.TestCase):
    def test_baseline_excludes_every_species_of_the_held_out_genus(self):
        examples=[]
        for name,label,value in [('A one',1,4),('A two',1,5),('B one',0,7),('C one',1,8),('D one',0,9),('E one',0,10)]:
            examples.append({'species':name,'image_id':name,'visible_pattern':label,
                             'venom_profiles':[{'features':[value,None]},{'features':[value+1,None]}]})
        result=evaluate(examples)
        self.assertEqual(result['status'],'development_only_not_connected')
        self.assertEqual(result['counts']['genera'],5)
        for row in result['predictions']:
            if row['species'].startswith('A '): self.assertEqual(row['baseline'],.25)
            for key in ('baseline','random_forest','extra_trees','hist_gradient_boosting'):
                self.assertTrue(0<=row[key]<=1)

if __name__=='__main__':unittest.main()

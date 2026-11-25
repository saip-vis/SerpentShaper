import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_learned_training_data import OUTPUTS, build, check_annotation, source_image_allowed
from train_learned_morphology import fit, predict, readiness, train, transform


class LearnedMorphologyTests(unittest.TestCase):
    def test_existing_data_never_automatically_approves_candidates(self):
        data=build()
        self.assertEqual(data['status'],'candidate_data_only_not_approved_for_product')
        self.assertTrue(all(c['annotation_status']=='not_automatically_approved' for c in data['candidate_images']))
        if not data['counts']['annotation_records']:
            self.assertEqual(data['counts']['approved_joined_images'],0)
        empty={'rows':[],'counts':{'approved_joined_images':0,'joined_source_species':0}}
        self.assertEqual(readiness(empty)['status'],'insufficient_approved_image_traits')
        with self.assertRaisesRegex(ValueError,'No model was trained'):
            train(empty)

    def test_source_gate_never_promotes_unreviewed_or_excluded_images(self):
        base={'review_status':'accepted','observation_id':101}
        self.assertTrue(source_image_allowed(base))
        for update in ({'review_status':'unreviewed'},{'rendering_training_excluded':True},
                       {'reference_only_exception':True},{'duplicate_of':'other'}, {'exact_content_seen_elsewhere':True},
                       {'rendering_exclusion_reason':'duplicate_content_pending_review'},
                       {'suitability_screening':{'category':'supplemental'}},{'observation_id':None}):
            self.assertFalse(source_image_allowed({**base,**update}))

    def test_annotations_must_preserve_exclusions_hash_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'image.jpg').write_bytes(b'photo');manifest=root/'manifest.json'
            image={'image_id':'photo','provider_species_name':'Crotalus atrox','review_status':'accepted',
                   'observation_id':101,'local_path':'image.jpg','sha256':hashlib.sha256(b'photo').hexdigest(),
                   'photo_license':'cc-by','attribution':'photographer'}
            label={'image_id':'photo','species_label':'Crotalus atrox','review_status':'approved',
                   'training_eligible':True,'annotation_source':'observed_photo','review_note':'visible body',
                   'traits':{'bodyWidth':.5},'trait_evidence':{'bodyWidth':'visible section'}}
            self.assertEqual(check_annotation(label,image,manifest,set(),set(),root),[])
            self.assertIn('existing_provisional_annotation_is_training_excluded',check_annotation(label,image,manifest,{'photo'},set(),root))
            self.assertIn('image_content_reserved_or_training_excluded',check_annotation(label,image,manifest,set(),set(),root,protected_hashes={image['sha256']}))
            self.assertIn('observation_reserved_for_existing_photo_check',check_annotation(label,image,manifest,set(),{101},root))
            self.assertIn('advisory_quality_flag_not_resolved',check_annotation(label,image,manifest,set(),set(),root,advisory='condition_review'))
            self.assertIn('trait_evidence_missing',check_annotation({**label,'trait_evidence':{}},image,manifest,set(),set(),root))
            self.assertIn('source_image_not_accepted_or_excluded',check_annotation(label,{**image,'rendering_training_excluded':True},manifest,set(),set(),root))
            self.assertIn('image_hash_missing_or_mismatch',check_annotation(label,{**image,'sha256':'wrong'},manifest,set(),set(),root))

    def test_synthetic_training_is_direct_and_smooth_at_zero(self):
        # Test the math with synthetic data, not real image labels or scientific claims.
        names=['Aaa one','Bbb two','Ccc three','Ddd four']
        rows=[]
        for i,name in enumerate(names):
            rows.append({'species':name,'features':[5.0+i*10,20.0,30.0],
                         'targets':{target:(.2+i*.1) for target in OUTPUTS}})
        data={'rows':rows,'feature_ids':['a','b','c'],'counts':{'approved_joined_images':4,'joined_source_species':4},
              'source_sha256':{},'link_scope':'synthetic'}
        self.assertEqual(readiness(data)['status'],'candidate_training_possible')
        candidate=train(data)
        self.assertEqual(candidate['status'],'experimental_candidate_not_for_product')
        self.assertEqual(set(candidate['models']),set(OUTPUTS))
        self.assertNotIn('species',candidate['feature_ids'])
        p=fit(rows,'headWidth',3)
        self.assertEqual(predict({'features':[0,20,30]},p),predict({'features':[None,20,30]},p))
        self.assertAlmostEqual(predict({'features':[0,20,30]},p),predict({'features':[1e-7,20,30]},p),places=5)
        self.assertEqual(transform([0,None,10],[15,20,30]),transform([None,0,10],[15,20,30]))
        # Exercise browser math using a synthetic model only; no real model is enabled.
        candidate['status']='ready_for_preview'
        query={'a':.5,'b':20.0,'c':30.0}
        command="const I=require('./MainInterface/learned-inference.js');let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>{const x=JSON.parse(s);process.stdout.write(JSON.stringify(I.predict(x.values,x.model)));});"
        result=subprocess.run(['node','-e',command],cwd=ROOT,input=json.dumps({'model':candidate,'values':query}),text=True,capture_output=True,check=True)
        browser=json.loads(result.stdout)
        self.assertAlmostEqual(browser['traits']['headWidth'],predict({'features':[.5,20,30]},candidate['models']['headWidth']),places=10)


if __name__=='__main__':
    unittest.main()

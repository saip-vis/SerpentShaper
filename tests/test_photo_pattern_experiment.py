import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import evaluate_photo_pattern_pilot as pilot
import collect_catalog_followup as collection
import collect_pilot_followup as followup
import collect_commons_gap_references as commons
from export_rendering_manifest import eligible


class PhotoPatternPilotTests(unittest.TestCase):
    def test_grouped_evaluation_excludes_held_out_genus(self):
        examples=[]
        for i, name in enumerate(['Aaa one','Aaa two','Bbb three','Ccc four','Ddd five','Eee six']):
            examples.append({'species':name,'image_id':str(i),'observation_id':i,'visible_pattern':i%2,
                'venom_profiles':[{'profile_id':str(i),'features':[float(i*10),None,20.]}]})
        result=pilot.evaluate(examples)
        for p in result['fold_predictions']:
            self.assertNotIn(p['species'].split()[0],p['training_genera'])
            self.assertTrue(0<=p['model_probability']<=1)
        self.assertEqual(len(result['fold_predictions']),6)

    def test_loading_requires_unblocked_hash_checked_source(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);folder=root/'photos';folder.mkdir();(folder/'photo.jpg').write_bytes(b'fixture')
            digest=hashlib.sha256(b'fixture').hexdigest()
            manifest=folder/'manifest.json';manifest.write_text(json.dumps([{'image_id':'a','review_status':'accepted',
                'observation_id':1,'local_path':'photo.jpg','photo_license':'cc0','attribution':'A'}]))
            labels=root/'labels.json';labels.write_text(json.dumps({'records':[{'image_id':'a','species':'Aaa one',
                'visible_pattern':1,'evidence':'visible body bands'}]}))
            candidate={'image_id':'a','species':'Aaa one','review_blocks':[],'observation_id':1,
                'sha256':digest,'manifest':'photos/manifest.json','photo_page':'https://example.test/photo'}
            profiles={'Aaa one':[{'profile_id':'v','features':[1,2,3]}]}
            with patch.object(pilot,'ROOT',root),patch.object(pilot,'LABELS',labels),patch.object(pilot,'load_profiles',return_value=([],profiles)),patch.object(pilot,'build',return_value={'candidate_images':[candidate]}):
                self.assertEqual(len(pilot.load_examples()),1)
                (folder/'photo.jpg').write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError,'hash mismatch'):pilot.load_examples()
                candidate['review_blocks']=['observation_reserved']
                with self.assertRaisesRegex(ValueError,'unblocked'):pilot.load_examples()

    def test_collection_plan_is_unique_and_reproducible(self):
        taxa=[{'source_name':'Aaa one'},{'source_name':'Bbb two'}]
        a=collection.plan(taxa)
        self.assertEqual(a,collection.plan(taxa))
        self.assertEqual(len({folder for folder,_ in a}),2)
        with self.assertRaises(ValueError):collection.plan(taxa+taxa[:1])

    def test_collection_records_provider_limit_and_stops(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);taxa=root/'taxa.json';report=root/'report.json'
            taxa.write_text(json.dumps({'taxa':[{'source_name':'Aaa one'},{'source_name':'Bbb two'}]}))
            blocked=HTTPError('https://example.test',429,'rate limited',None,None)
            with patch.object(collection,'TAXA',taxa),patch.object(collection,'REPORT',report), \
                 patch.object(collection.followup,'collect',side_effect=blocked) as collector, \
                 patch.object(sys,'argv',['collect_catalog_followup.py']):
                collection.main()
            result=json.loads(report.read_text())
            self.assertEqual(result['status'],'stopped_provider_limit')
            self.assertEqual(result['species'][0]['error'],'HTTP 429')
            self.assertEqual(collector.call_count,1,'no more requests after provider rate limiting')

    def test_retry_only_revisits_partial_download_batch(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);taxa=root/'taxa.json';report=root/'report.json'
            taxa.write_text(json.dumps({'taxa':[{'source_name':'Aaa one'},{'source_name':'Bbb two'}]}))
            report.write_text(json.dumps({'per_species':8,'species':[{'species':'Aaa one','status':'completed','failures':0},
                               {'species':'Bbb two','status':'completed','failures':1}]}))
            with patch.object(collection,'TAXA',taxa),patch.object(collection,'REPORT',report), \
                 patch.object(collection.followup,'collect',return_value={'species':'Bbb two','failures':0}) as collector, \
                 patch.object(sys,'argv',['collect_catalog_followup.py','--retry-failed-downloads']):
                collection.main()
            self.assertEqual(collector.call_count,1)
            self.assertEqual(collector.call_args.args[1],'Bbb two')

    def test_resumed_collection_flags_duplicate_content_in_its_own_batch(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);folder=root/'data/image_pilots/pilot_999_test';folder.mkdir(parents=True)
            source=root/'reports/image_research';source.mkdir(parents=True)
            (source/'imaging_gaps.json').write_text(json.dumps({'taxa':[{'source_name':'Aaa one','image_lookup_name':'Aaa one'}]}))
            digest=hashlib.sha256(b'same-image').hexdigest()
            rows=[{'source_species_name':'Aaa one','image_id':'old','observation_id':1,'download_status':'downloaded','sha256':digest},
                  {'source_species_name':'Aaa one','image_id':'new','observation_id':2,'download_status':'not_downloaded',
                   'photo_license':'cc0','image_url':'https://static.inaturalist.org/photo.jpg',
                   'rendering_training_excluded':True,'rendering_exclusion_reason':'pending_visual_review'}]
            (folder/'manifest.json').write_text(json.dumps(rows))
            class Headers:
                def get_content_type(self):return 'image/jpeg'
            class Response:
                headers=Headers();url='https://static.inaturalist.org/photo.jpg'
                def __enter__(self):return self
                def __exit__(self,*args):pass
                def read(self,*args):return b'same-image'
            with patch.object(followup,'ROOT',root),patch.object(followup,'PER_SPECIES',2), \
                 patch.object(followup.time,'sleep'),patch.object(followup,'urlopen',return_value=Response()):
                followup.collect('pilot_999_test','Aaa one')
            result=json.loads((folder/'manifest.json').read_text())[-1]
            self.assertTrue(result['exact_content_seen_elsewhere'])
            self.assertEqual(result['rendering_exclusion_reason'],'duplicate_content_pending_review')

    def test_commons_candidates_exclude_maps_and_keep_observation_unknown(self):
        def page(number,title,license_name,artist):
            return {'pageid':number,'title':title,'imageinfo':[{'mime':'image/jpeg','width':1000,'height':800,
                'url':f'https://upload.wikimedia.org/test/{number}.jpg','descriptionurl':f'https://commons.wikimedia.org/wiki/File:{number}',
                'extmetadata':{'Artist':{'value':artist},'LicenseShortName':{'value':license_name}}}]}
        data={'query':{'pages':[page(1,'File:Aaa one.jpg','CC BY-SA 4.0','A'),page(2,'File:Aaa one distribution map.jpg','CC BY 4.0','B'),
                                page(3,'File:Aaa one 2.jpg','CC BY-NC 4.0','C'),page(4,'File:Aaa one 3.jpg','CC BY 4.0','A')]}}
        result=commons.candidates('Aaa one',data)
        self.assertEqual(len(result),1)
        self.assertIsNone(result[0]['observation_id'])
        self.assertTrue(result[0]['rendering_training_excluded'])
        self.assertEqual(result[0]['review_status'],'unreviewed')

    def test_export_rejects_exact_content_flag_even_if_review_fields_conflict(self):
        row={'review_status':'accepted','download_status':'downloaded','rendering_training_excluded':False}
        self.assertTrue(eligible(row))
        self.assertFalse(eligible({**row,'exact_content_seen_elsewhere':True}))
        self.assertFalse(eligible({**row,'rendering_exclusion_reason':'exact_duplicate'}))

if __name__=='__main__':unittest.main()

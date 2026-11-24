"""Extract reproducible color measurements from accepted photos.

This is an exploratory body-patch color target, not an image segmentation,
full-animal color estimate, or approval of any other trait label.
"""
import hashlib
import json
import statistics
from pathlib import Path

from PIL import Image
from build_learned_training_data import ROOT, build

SAMPLES=ROOT/'ML/learned_morphology/body_patch_samples.json'
OUT=ROOT/'ML/learned_morphology/body_patch_measurements.json'


def extract():
    audit=build();candidates={c['image_id']:c for c in audit['candidate_images']}
    definitions=json.loads(SAMPLES.read_text())['samples'];records=[];seen=set()
    for sample in definitions:
        image_id=sample['image_id'];candidate=candidates.get(image_id)
        if not candidate or candidate['review_blocks']:
            raise ValueError('Source is not an accepted, unblocked candidate: '+image_id)
        if candidate['observation_id'] in seen:
            raise ValueError('Repeated observation in color pilot')
        seen.add(candidate['observation_id'])
        manifest=ROOT/candidate['manifest'];photo=next(x for x in json.loads(manifest.read_text()) if x['image_id']==image_id)
        path=(manifest.parent/photo['local_path']).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=photo['sha256']:
            raise ValueError('Image missing or checksum mismatch: '+image_id)
        if photo.get('photo_license') not in {'cc0','cc-by'} or not photo.get('attribution'):
            raise ValueError('License code or attribution missing: '+image_id)
        bbox=sample['bbox']
        if not (len(bbox)==4 and 0<=bbox[0]<bbox[2]<=1 and 0<=bbox[1]<bbox[3]<=1):
            raise ValueError('Invalid normalized crop')
        with Image.open(path) as source:
            image=source.convert('RGB')
            box=(round(bbox[0]*image.width),round(bbox[1]*image.height),round(bbox[2]*image.width),round(bbox[3]*image.height))
            crop=image.crop(box)
            if crop.width<8 or crop.height<8:raise ValueError('Crop too small: '+image_id)
            pixels=list(crop.get_flattened_data() if hasattr(crop,'get_flattened_data') else crop.getdata())
            median=[float(statistics.median(p[i] for p in pixels))/255 for i in range(3)]
        records.append({'image_id':image_id,'species_label':candidate['species'],'observation_id':candidate['observation_id'],
                        'photo_page':photo.get('photo_page'),'photo_sha256':photo['sha256'],'manifest':candidate['manifest'],
                        'photo_license':photo.get('photo_license'),'license_version':photo.get('license_version'),
                        'attribution':photo.get('attribution'),'bbox':bbox,'pixel_count':len(pixels),
                        'median_rgb':median,'note':sample['note']})
    return {'schema_version':1,'status':'exploratory_photo_measurements_not_full_morphology_labels',
            'method':'Median per sRGB channel from manually selected visible body crop; no color calibration or segmentation.',
            'limitations':['Lighting, camera processing, markings and occlusion affect pixel colors.',
                           'Color of a small patch is not necessarily the species or whole-animal color.',
                           'Species-level photo and venom associations are not paired individuals.',
                           'No image, specimen, or annotation approval is changed by this script.'],
            'sample_definition_sha256':hashlib.sha256(SAMPLES.read_bytes()).hexdigest(),'records':records}


def main():
    output=extract();OUT.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print('Extracted',len(output['records']),'accepted image patches across',len({r['species_label'] for r in output['records']}),'source species labels.')


if __name__=='__main__':main()

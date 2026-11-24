"""Prioritize unreviewed local photos; never approve photos or trait labels."""
import json
from collections import defaultdict
from pathlib import Path

from build_learned_training_data import ROOT, PILOT, HOLDOUT, load_profiles

OUT=ROOT/'ML/learned_morphology/image_triage_queue.json'
PRIORITY=['Naja kaouthia','Ophiophagus hannah','Naja naja','Dispholidus typus',
          'Bothrops asper','Daboia russelii','Bitis arietans','Bungarus multicinctus',
          'Micrurus fulvius','Crotalus scutulatus']


def build(max_species=24,per_species=3):
    _,profiles=load_profiles()
    reserved={x['image_id'] for x in json.loads(PILOT.read_text())['records']}|{x['image_id'] for x in json.loads(HOLDOUT.read_text())['records']}
    manifests=sorted((ROOT/'data/image_pilots').glob('*/manifest.json'))
    protected=[img for path in manifests for img in json.loads(path.read_text()) if img.get('image_id') in reserved]
    protected_observations={img['observation_id'] for img in protected if img.get('observation_id')}
    protected_hashes={img['sha256'] for img in protected if img.get('sha256')}
    groups=defaultdict(list);seen_hashes=set();seen_observations=set()
    for manifest in manifests:
        for img in json.loads(manifest.read_text()):
            species=img.get('source_species_name');reason=img.get('rendering_exclusion_reason')
            if (img.get('review_status')!='unreviewed' or species not in profiles or
                img.get('provider_species_name')!=species or img.get('image_id') in reserved or
                img.get('observation_id') in protected_observations or img.get('sha256') in protected_hashes or
                reason not in (None,'pending_visual_review') or img.get('reference_only_exception') or img.get('duplicate_of') or
                img.get('photo_license') not in ('cc0','cc-by') or not img.get('attribution') or
                not img.get('sha256') or not img.get('observation_id') or not img.get('local_path')):continue
            path=(manifest.parent/img['local_path']).resolve()
            if not path.is_relative_to(ROOT.resolve()) or not path.is_file():continue
            width=img.get('original_width') or 0;height=img.get('original_height') or 0
            groups[species].append({'image_id':img['image_id'],'observation_id':img['observation_id'],
               'manifest':str(manifest.relative_to(ROOT)),'local_path':str(path.relative_to(ROOT)),
               'photo_page':img.get('photo_page'),'sha256':img['sha256'],'photo_license':img['photo_license'],
               'license_version':img.get('license_version'),'attribution':img['attribution'],
               'original_width':width,'original_height':height,'review_status':'unreviewed',
               'existing_exclusion_reason':reason,'triage_status':'pending_visual_and_trait_review'})
    # Priority examples are followed by one source label per remaining genus
    # before returning to additional labels from already represented genera.
    ordered=[s for s in PRIORITY if s in groups]
    rest=sorted((s for s in groups if s not in ordered),key=lambda s:(-len({x['observation_id'] for x in groups[s]}),s))
    genera={s.split()[0] for s in ordered}
    for s in rest:
        if s.split()[0] not in genera:ordered.append(s);genera.add(s.split()[0])
    ordered.extend(s for s in rest if s not in ordered)
    output=[]
    for species in ordered:
        selected=[]
        for img in sorted(groups[species],key=lambda x:(-min(x['original_width'],x['original_height']),x['image_id'])):
            if img['observation_id'] in seen_observations or img['sha256'] in seen_hashes:continue
            seen_observations.add(img['observation_id']);seen_hashes.add(img['sha256']);selected.append(img)
            if len(selected)>=per_species:break
        if selected:output.append({'species_label':species,'venom_profile_count':len(profiles[species]),'images':selected})
        if len(output)>=max_species:break
    return {'schema_version':1,'status':'triage_only_no_acceptance_or_training_approval',
            'description':'Metadata-prioritized local photos for assistant-supported review; pixels, condition, species identity, image rights and useful traits are not verified by selection.',
            'source_species_count':len(output),'image_count':sum(len(x['images']) for x in output),
            'selection':'Unreviewed; original source and provider names agree; local file available; retained license code; diverse genera; at most one image per observation and three per species. Resolution is only a triage hint.',
            'species':output}


def main():
    data=build();OUT.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    print('Queued',data['image_count'],'unreviewed photos across',data['source_species_count'],'source labels for assisted triage; none approved.')


if __name__=='__main__':main()

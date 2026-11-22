"""Create explicitly unreviewed, reusable starting points for missing catalog labels.
Existing presets are never replaced. Templates are drawing scaffolds, not species predictions.
"""
import copy,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 catalog=json.loads((ROOT/'data/processed/species_catalog/catalog.json').read_text())['species']
 profiles={p['species_id']:p for p in json.loads((ROOT/'data/processed/morphology/physical_profiles.json').read_text())['profiles']}
 ledger_path=ROOT/'reports/species_modeling_ledger.json';ledger=json.loads(ledger_path.read_text());rows={r['species_id']:r for r in ledger['species']}
 existing={json.loads(f.read_text())['species_id'] for f in (ROOT/'config/species_presets').glob('*.json')}
 templates={n:json.loads((ROOT/'config/species_presets'/f'{n}.json').read_text()) for n in ['bothrops_atrox','dendroaspis_polylepis','naja_kaouthia','aipysurus_laevis','crotalus_atrox','bungarus_candidus']}
 rattles={'Crotalus','Sistrurus'};cobra={'Naja','Ophiophagus','Hemachatus'};marine={'Hydrophis','Laticauda'};banded={'Bungarus','Calliophis','Micrurus'};other={'Azemiops','Boiga','Borikenophis','Cerberus','Conophis','Dendroaspis','Drysdalia','Micropechis','Philodryas','Pseudechis','Rhinobothryum','Tantilla','Thamnodynastes','Thelotornis','Toxicocalamus','Austrelaps'}
 created=0
 for s in catalog:
  sid=s['species_id']
  if sid in existing:continue
  name=s['source_species_name'];genus=name.split()[0];pid=re.sub(r'[^a-z0-9]+','_',name.lower()).strip('_');path=ROOT/'config/species_presets'/f'{pid}.json'
  if path.exists():raise ValueError(f'Preset path collision: {path}')
  t='crotalus_atrox' if genus in rattles else 'naja_kaouthia' if genus in cobra else 'aipysurus_laevis' if genus in marine else 'bungarus_candidus' if genus in banded else 'dendroaspis_polylepis' if genus in other else 'bothrops_atrox'
  p=copy.deepcopy(templates[t]);prof=profiles[sid];a=p['artistic_parameters'];p.update(preset_id=pid,species_id=sid,source_species_name=name,common_name=name,status='unreviewed_starter',variant='Unreviewed template scaffold; shape and colors require species-specific reference review.',model_revision=1)
  # Remove source-species pigment; retain only broad presentation geometry as an editable starting point.
  a['pattern']='plain';a['skin_color']='#887e6c';a['marking_color']='#c5b79b';a['belly_color']='#c9bfaa'
  for key in ['head_color','tail_color','tail_color_length','ventrolateral_stripe','head_pattern','blotch_border','speckle_threshold','scale_border_width']:a.pop(key,None)
  if a['body_plan']!='cobra':
   h=a['head_geometry'];h['markings']=[];h.pop('iris_color',None)
  sources=sorted({d['source_url'] for d in prof['descriptions'].values() if d and d.get('source_url')})
  if not sources:sources=['https://doi.org/10.6084/m9.figshare.24572683']
  notes=[f'Unreviewed drawing scaffold derived from {templates[t]["source_species_name"]}; no claim of species-specific accuracy.', 'Available photographs and descriptions still need individual review before refinement.']
  flags=['No species-specific visual modeling performed; shape, markings and colors are placeholders.', 'Existing image candidates have not been assessed for suitability in this preset.']
  if not s['images']:flags.append('No local image candidates in species catalog; seek reliable reference imagery.')
  p['evidence']={'physical_profile_path':'data/processed/morphology/physical_profiles.json','sources':[{'url':u,'scope':'Existing source profile; not yet applied to this template.'} for u in sources], 'photo_references':[], 'reference_feature_map':{},'unextracted_fields':prof['coverage']['descriptive_fields_not_extracted'],'review':'Unreviewed starter only; species-specific visual modeling has not been performed.','modeling_flags':flags,'modeling_review_status':'unreviewed_starter','modeling_observations':{'status':'unreviewed_template','observations':notes,'projection_limit':'Template shapes and colors are placeholders, not biological measurements.','reference_ids':[]},'template_source_preset':t}
  p['biological_measurements']=None;p['venom_trait_mapping']=None
  path.write_text(json.dumps(p,indent=2,ensure_ascii=False)+'\n');row=rows[sid];row.update(status='unreviewed_starter',preset_id=pid,unresolved_flags=list(dict.fromkeys(row.get('unresolved_flags',[])+flags)));created+=1
 ledger_path.write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n');print(f'Created {created} explicitly unreviewed starter presets.')
if __name__=='__main__':main()

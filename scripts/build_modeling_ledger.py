"""Refresh inventory without turning missing review into completed analysis."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 catalog=json.loads((ROOT/'data/processed/species_catalog/catalog.json').read_text())
 profiles={p['species_id']:p for p in json.loads((ROOT/'data/processed/morphology/physical_profiles.json').read_text())['profiles']}
 target=ROOT/'reports/species_modeling_ledger.json'
 old={p['species_id']:p for p in json.loads(target.read_text())['species']} if target.exists() else {}
 presets={p['species_id']:p for f in (ROOT/'config/species_presets').glob('*.json') for p in [json.loads(f.read_text())]}
 rows=[]
 for species in catalog['species']:
  sid=species['species_id'];profile=profiles[sid];folders=sorted({str(Path(i['manifest_path']).parent) for i in species['images']})
  row=old.get(sid,{'species_id':sid,'source_species_name':species['source_species_name'],'status':'pending_visual_review','visual_observations':[],'refinements':[],'unresolved_flags':[],'online_references_checked':[]})
  row.update(pilot_folders=folders,available_photo_records=len(species['images']),physical_description_gaps=profile['coverage']['descriptive_fields_not_extracted'],preset_id=presets.get(sid,{}).get('preset_id'))
  if not folders and 'no_local_images' not in row['unresolved_flags']:row['unresolved_flags'].append('no_local_images')
  rows.append(row)
 summary={status:sum(r['status']==status for r in rows) for status in sorted({r['status'] for r in rows})}
 counts={'catalog_source_labels':len(rows),'editable_draft_presets':len(presets),
         'source_labels_without_presets':sum(r['preset_id'] is None for r in rows),
         'pending_visual_review':summary.get('pending_visual_review',0)+summary.get('unreviewed_starter',0)+summary.get('initial_model_awaiting_refinement',0),
         'initial_models_awaiting_refinement':summary.get('initial_model_awaiting_refinement',0),
         'unreviewed_starter_presets':summary.get('unreviewed_starter',0)}
 target.write_text(json.dumps({'policy':'A photo count is not a reviewed angle. Draft presets are not validated anatomy. Pending species are not analyzed or modeled.','counts':counts,'summary':summary,'species':rows},indent=2,ensure_ascii=False)+'\n')
 print(summary)
if __name__=='__main__':main()

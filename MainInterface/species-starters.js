/* Build one reproducible starting venom profile for each available species. */
(function(root){
'use strict';
function build(data,presets){
  if(!data||!Array.isArray(data.profiles)||!Array.isArray(presets))return [];
  const byId=new Map(presets.map(p=>[p.preset_id,p])),species=new Map();
  for(const profile of data.profiles){
    const preset=byId.get(profile.preset_id);if(!preset||!profile.species_name)continue;
    const previous=species.get(profile.species_name);
    if(!previous||profile.source_row<previous.profile.source_row)species.set(profile.species_name,{species:profile.species_name,preset,profile});
  }
  return [...species.values()].sort((a,b)=>{
    const x=a.preset.common_name||a.species,y=b.preset.common_name||b.species;
    return x.localeCompare(y)||a.species.localeCompare(b.species);
  });
}
function valuesForProfile(controls,profile){
  const components=new Map((profile?.components||[]).map(item=>[item.toxin_id,item]));
  return Object.fromEntries(controls.map(control=>{
    const entry=components.get(control.source_toxin_ids[0]);
    return [control.id,entry?.status!=='source_uncertain'&&Number.isFinite(entry?.value)?entry.value:null];
  }));
}
const api={build,valuesForProfile};if(typeof module!=='undefined')module.exports=api;else root.SpeciesStarters=api;
})(typeof window!=='undefined'?window:this);

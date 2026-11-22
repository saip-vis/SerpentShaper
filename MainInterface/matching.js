/* Reference comparisons are descriptive only; unknown values are never imputed. */
(function(root){
  function compare(values, profile, controls) {
    const lookup=new Map(profile.components.map(c=>[c.toxin_id,c.value]));
    const selected=controls.filter(c=>values[c.id]!==null && values[c.id]!==undefined && Number.isFinite(values[c.id]));
    if(!selected.length)return null;
    const shared=selected.filter(c=>Number.isFinite(lookup.get(c.source_toxin_ids[0])));
    if(!shared.length)return null;
    const meanDifference=shared.reduce((sum,c)=>sum+Math.abs(values[c.id]-lookup.get(c.source_toxin_ids[0])),0)/shared.length;
    return {profile, compared:shared.length, selected:selected.length, meanDifference, sharedIds:shared.map(c=>c.id)};
  }
  function rank(values, profiles, controls){
    return profiles.filter(p=>p.preset_id).map(p=>compare(values,p,controls)).filter(Boolean)
      .sort((a,b)=>b.compared-a.compared || a.meanDifference-b.meanDifference || a.profile.species_name.localeCompare(b.profile.species_name) || a.profile.source_row-b.profile.source_row);
  }
  function totals(values,sourceOnly){
    const selected=Object.values(values).filter(Number.isFinite).reduce((a,b)=>a+b,0);
    const retained=sourceOnly.filter(c=>Number.isFinite(c.value)).reduce((a,c)=>a+c.value,0);
    return {selected,retained,total:selected+retained,unallocated:Math.max(0,100-selected-retained),over:Math.max(0,selected+retained-100)};
  }
  const api={compare,rank,totals};if(typeof module!=='undefined')module.exports=api;else root.SerpentMatching=api;
})(typeof window!=='undefined'?window:this);

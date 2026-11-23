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
  function influences(values, profiles, controls, limit=3){
    // A species contributes once, even when its source has many profiles.
    const seen=new Set();
    const best=rank(values,profiles,controls).filter(result=>{
      const key=result.profile.species_name.toLowerCase();
      if(seen.has(key))return false;
      seen.add(key);return true;
    }).slice(0,limit);
    const scores=best.map(r=>(r.compared/r.selected)*Math.exp(-r.meanDifference/20));
    const total=scores.reduce((a,b)=>a+b,0);
    return best.map((result,i)=>({...result,weight:scores[i]/total}));
  }
  function totals(values,sourceOnly){
    const selected=Object.values(values).filter(Number.isFinite).reduce((a,b)=>a+b,0);
    const retained=sourceOnly.filter(c=>Number.isFinite(c.value)).reduce((a,c)=>a+c.value,0);
    return {selected,retained,total:selected+retained,unallocated:Math.max(0,100-selected-retained),over:Math.max(0,selected+retained-100)};
  }
  const api={compare,rank,influences,totals};if(typeof module!=='undefined')module.exports=api;else root.SerpentMatching=api;
})(typeof window!=='undefined'?window:this);

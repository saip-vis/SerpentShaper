/* Reference comparisons are descriptive only; unknown values are never imputed. */
(function(root){
  function compare(values, profile, controls) {
    const lookup=new Map(profile.components.map(c=>[c.toxin_id,c.value]));
    // Zero means the user turned this component off; it remains displayed but
    // must not affect either coverage or similarity. A measured zero in a
    // reference profile remains valid when comparing a positive input.
    const selected=controls.filter(c=>Number.isFinite(values[c.id])&&values[c.id]>0);
    if(!selected.length)return null;
    const shared=selected.filter(c=>Number.isFinite(lookup.get(c.source_toxin_ids[0])));
    if(!shared.length)return null;
    const differences=shared.map(c=>({id:c.id,label:c.short_label,input:values[c.id],reference:lookup.get(c.source_toxin_ids[0]),difference:Math.abs(values[c.id]-lookup.get(c.source_toxin_ids[0]))}));
    const meanDifference=differences.reduce((sum,c)=>sum+c.difference,0)/shared.length;
    const coverage=shared.length/selected.length;
    // A descriptive kernel, not a biological likelihood or confidence score.
    const score=coverage**3*Math.exp(-meanDifference/2);
    return {profile, compared:shared.length, selected:selected.length, meanDifference, sharedIds:shared.map(c=>c.id),differences,score};
  }
  function rank(values, profiles, controls){
    return profiles.filter(p=>p.preset_id).map(p=>compare(values,p,controls)).filter(Boolean)
      .sort((a,b)=>b.score-a.score || b.compared-a.compared || a.meanDifference-b.meanDifference || a.profile.species_name.localeCompare(b.profile.species_name) || a.profile.source_row-b.profile.source_row);
  }
  function influences(values, profiles, controls){
    // Keep the best measured profile per species so multiple samples do not
    // inflate its influence. Retain all eligible species: discarding all but a
    // top-N list produces jumps when ranks cross during a small slider change.
    const seen=new Set();
    const best=rank(values,profiles,controls).filter(result=>result.compared>=3).filter(result=>{
      const key=result.profile.species_name.toLowerCase();
      if(seen.has(key))return false;
      seen.add(key);return true;
    });
    const total=best.reduce((n,r)=>n+r.score,0);
    return total?best.map(result=>({...result,weight:result.score/total})):[];
  }
  function totals(values,sourceOnly){
    const selected=Object.values(values).filter(Number.isFinite).reduce((a,b)=>a+b,0);
    const retained=sourceOnly.filter(c=>Number.isFinite(c.value)).reduce((a,c)=>a+c.value,0);
    return {selected,retained,total:selected+retained,unallocated:Math.max(0,100-selected-retained),over:Math.max(0,selected+retained-100)};
  }
  const api={compare,rank,influences,totals};if(typeof module!=='undefined')module.exports=api;else root.SerpentMatching=api;
})(typeof window!=='undefined'?window:this);

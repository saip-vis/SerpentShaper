/* Descriptive comparisons of entered percentages with reported source values. */
(function(root){
'use strict';
// An explicit ranking penalty, in percentage points, rather than an assumed
// concentration. A missing measurement is never displayed as zero.
const MISSING_PENALTY=25;
function compare(values,profile,controls){
  const selected=controls.filter(c=>Number.isFinite(values[c.id]));
  if(!selected.length)return null;
  const lookup=new Map((profile.components||[]).map(c=>[c.toxin_id,c]));
  const shared=[],missing=[];
  for(const control of selected){
    const entry=lookup.get(control.source_toxin_ids[0]);
    if(entry&&entry.status!=='source_uncertain'&&Number.isFinite(entry.value))shared.push({id:control.id,label:control.short_label,input:values[control.id],source:entry.value,difference:Math.abs(values[control.id]-entry.value)});
    else missing.push(control.short_label);
  }
  // No overlap cannot establish a comparison, even with a missingness penalty.
  if(!shared.length)return null;
  const difference=shared.reduce((sum,c)=>sum+c.difference,0);
  return {profile,shared,missing,entered:selected.length,meanDifference:difference/shared.length,adjustedDistance:(difference+MISSING_PENALTY*missing.length)/selected.length};
}
function rank(values,profiles,controls){
  const results=profiles.filter(p=>p.species_name).map(p=>compare(values,p,controls)).filter(Boolean);
  results.sort((a,b)=>a.adjustedDistance-b.adjustedDistance||b.shared.length-a.shared.length||a.meanDifference-b.meanDifference||a.profile.species_name.localeCompare(b.profile.species_name)||a.profile.source_row-b.profile.source_row);
  const seen=new Set();
  return results.filter(result=>{const key=result.profile.species_name.toLowerCase();if(seen.has(key))return false;seen.add(key);return true;});
}
const api={MISSING_PENALTY,compare,rank};if(typeof module!=='undefined')module.exports=api;else root.ProfileComparison=api;
})(typeof window!=='undefined'?window:this);

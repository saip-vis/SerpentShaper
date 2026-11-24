/* Connect three hand-authored shared-shape examples to venom comparisons. */
(function(root){
'use strict';
function match(values,profiles,controls,matcher,morphology){
  const species=new Set(Object.values(morphology.REFERENCES).map(ref=>ref.species));
  const mass=controls.reduce((n,c)=>n+(Number.isFinite(values[c.id])&&values[c.id]>0?values[c.id]:0),0);
  if(!mass)return [];
  const candidates=matcher.rank(values,profiles.filter(p=>species.has(p.species_name)),controls)
    .filter(r=>r.compared>=3)
    .map(r=>{const massCoverage=r.differences.reduce((n,d)=>n+d.input,0)/mass;
      // Heuristic to reduce dominance from a profile that lacks high-abundance
      // inputs. A missing reference value is never interpreted as zero.
      const score=(r.compared/r.selected)**3*massCoverage**3*Math.exp(-r.meanDifference/5);
      return {...r,massCoverage,score};})
    .sort((a,b)=>b.score-a.score||b.compared-a.compared||a.meanDifference-b.meanDifference||a.profile.species_name.localeCompare(b.profile.species_name)||a.profile.source_row-b.profile.source_row);
  const seen=new Set(),best=candidates.filter(r=>{const key=r.profile.species_name.toLowerCase();if(seen.has(key))return false;seen.add(key);return true;});
  const total=best.reduce((n,r)=>n+r.score,0);
  return total?best.map(r=>({...r,weight:r.score/total})):[];
}
function create(values,matches,morphology,surface='dorsal'){
  const ids=new Map(Object.entries(morphology.REFERENCES).map(([id,ref])=>[ref.species,id]));
  const valid=matches.filter(match=>ids.has(match.profile.species_name)&&Number.isFinite(match.weight)&&match.weight>0);
  const total=valid.reduce((n,match)=>n+match.weight,0);
  const weights={};for(const match of valid){const id=ids.get(match.profile.species_name);weights[id]=(weights[id]||0)+match.weight;}
  const shape=morphology.blend(weights);if(!shape)return null;
  shape.venomContext={kind:'three_reference_illustrative_pilot',venomInputs:{...values},
    comparison:'Shared-category and entered-abundance coverage, with mean absolute difference; illustrative heuristic, not validated biological prediction.',
    references:valid.map(match=>({species:match.profile.species_name,profileId:match.profile.profile_id,
      weight:match.weight/total,compared:match.compared,selected:match.selected,meanDifference:match.meanDifference,massCoverage:match.massCoverage}))};
  return morphology.render(shape,{surface});
}
const api={match,create};if(typeof module!=='undefined')module.exports=api;else root.SharedConcept=api;
})(typeof window!=='undefined'?window:this);

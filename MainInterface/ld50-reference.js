/* Small, explicitly sourced reference set, not a model of invented venom. */
(function(root){
'use strict';
// All measurements below are mouse intravenous LD50, in mg venom/kg body
// weight (1 µg/g = 1 mg/kg). Use one study at a time; do not combine routes.
// Only the reported taxa listed here are joined, with historical identifications
// retained where the venom dataset uses a broader current name.
const studies=[
 {id:'sanchez2003',year:2003,label:'Sánchez et al. (2003), Table 3',url:'https://pubmed.ncbi.nlm.nih.gov/12565759/',
  method:'BALB/c mice, intravenous; 48-hour observation',records:[
   {species:'Crotalus atrox',value:5.1,reported:'Crotalus atrox'},
   {species:'Crotalus oreganus',value:2.1,reported:'Crotalus viridis oreganus (historical name)'},
   {species:'Crotalus adamanteus',value:1.84,reported:'Crotalus adamanteus'}]},
 {id:'leong2012',year:2012,label:'Leong et al. (2012), Table 1',url:'https://doi.org/10.1371/journal.pntd.0001672.t001',
  method:'ICR mice, intravenous; 48-hour observation',records:[
   {species:'Naja kaouthia',value:.23,reported:'Naja kaouthia, Thailand'},
   {species:'Naja kaouthia',value:.89,reported:'Naja kaouthia, Malaysia'},
   {species:'Naja atra',value:.56,reported:'Naja atra'},
   {species:'Naja naja',value:1.80,reported:'Naja naja, India sample 1'},
   {species:'Naja naja',value:1.08,reported:'Naja naja, India sample 2'},
   {species:'Naja naja',value:1.13,reported:'Naja naja, Sri Lanka sample 1'},
   {species:'Naja naja',value:1.08,reported:'Naja naja, Sri Lanka sample 2'},
   {species:'Naja sputatrix',value:.90,reported:'Naja sputatrix'},
   {species:'Naja nubiae',value:.28,reported:'Naja nubiae'},
   {species:'Ophiophagus hannah',value:1,reported:'Ophiophagus hannah'},
   {species:'Bungarus fasciatus',value:1.67,reported:'Bungarus fasciatus'},
   {species:'Bungarus candidus',value:.11,reported:'Bungarus candidus'},
   {species:'Bungarus flaviceps',value:.175,reported:'Bungarus flaviceps'},
   {species:'Bungarus multicinctus',value:.11,reported:'Bungarus multicinctus'},
   {species:'Bungarus caeruleus',value:.17,reported:'Bungarus caeruleus'}]},
 {id:'araya2024',year:2024,label:'Araya et al. (2024), Table 2',url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC11004356/',
  method:'CD-1 mice, intravenous; 24-hour observation',records:[
   {species:'Bitis arietans',value:.54,reported:'Bitis arietans'},
   {species:'Bitis gabonica',value:.98,reported:'Bitis gabonica'},
   {species:'Bitis nasicornis',value:.92,reported:'Bitis nasicornis'},
   {species:'Echis ocellatus',value:.87,reported:'Echis ocellatus'},
   {species:'Echis pyramidum',value:.61,reported:'Echis pyramidum'},
   {species:'Naja katiensis',value:.88,reported:'Naja katiensis'},
   {species:'Naja mossambica',value:.99,reported:'Naja mossambica'},
   {species:'Naja nigricollis',value:.94,reported:'Naja nigricollis'},
   {species:'Naja annulifera',value:3.47,reported:'Naja annulifera'},
   {species:'Naja haje',value:.56,reported:'Naja haje'},
   {species:'Naja melanoleuca',value:.33,reported:'Naja melanoleuca'},
   {species:'Dendroaspis angusticeps',value:1.40,reported:'Dendroaspis angusticeps'},
   {species:'Dendroaspis polylepis',value:.31,reported:'Dendroaspis polylepis'}]}
];
function estimate(matches){
  // Fix the comparison set first: do not search down the ranking for data.
  const top=(matches||[]).slice(0,5).filter(m=>m.shared.length>=3&&m.shared.length/m.entered>=.6&&m.adjustedDistance<=20);
  const names=new Set(top.map(m=>m.profile.species_name));
  const candidates=studies.map(study=>{
    const records=study.records.filter(r=>names.has(r.species));
    return {study,records,speciesCount:new Set(records.map(r=>r.species)).size};
  }).filter(r=>r.speciesCount>=2).sort((a,b)=>b.speciesCount-a.speciesCount||b.study.year-a.study.year);
  if(!candidates.length)return null;
  const result=candidates[0],values=result.records.map(r=>r.value);
  return {...result,min:Math.min(...values),max:Math.max(...values)};
}
const api={studies,estimate};if(typeof module!=='undefined')module.exports=api;else root.Ld50Reference=api;
})(typeof window!=='undefined'?window:this);

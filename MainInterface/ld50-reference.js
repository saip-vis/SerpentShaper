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
   {species:'Crotalus adamanteus',value:1.84,reported:'Crotalus adamanteus'},
   {species:'Crotalus scutulatus',value:.47,reported:'Crotalus scutulatus scutulatus, type A'},
   {species:'Crotalus scutulatus',value:5.1,reported:'Crotalus scutulatus scutulatus, type B'},
   {species:'Crotalus horridus',value:.53,reported:'Crotalus horridus horridus'},
   {species:'Crotalus horridus',value:1.26,reported:'Crotalus horridus atricaudatus'},
   {species:'Crotalus viridis',value:1.56,reported:'Crotalus viridis viridis'},
   {species:'Agkistrodon piscivorus',value:2.75,reported:'Agkistrodon piscivorus leucostoma'},
   {species:'Agkistrodon contortrix',value:5.2,reported:'Agkistrodon contortrix contortrix'}]},
 {id:'silva2001',year:2001,label:'Jorge da Silva and Aird (2001), Tables 1 and 3',url:'https://doi.org/10.1016/S1532-0456(00)00215-5',
  method:'White mice, intravenous; sample locations as reported in Table 1',records:[
   {species:'Micrurus corallinus',value:.04,reported:'Micrurus corallinus, Rio de Janeiro'},
   {species:'Micrurus spixii',value:.2,reported:'Micrurus spixii spixii, Rondônia'},
   {species:'Micrurus spixii',value:.8,reported:'Micrurus spixii obscurus, Leticia'},
   {species:'Micrurus altirostris',value:.3,reported:'Micrurus altirostris, Campo Largo'},
   {species:'Micrurus altirostris',value:.2,reported:'Micrurus altirostris, Yaciretá'},
   {species:'Micrurus frontalis',value:.5,reported:'Micrurus frontalis, Jataí'},
   {species:'Micrurus frontalis',value:.4,reported:'Micrurus frontalis, Pontalina'},
   {species:'Micrurus lemniscatus',value:.2,reported:'Micrurus lemniscatus lemniscatus, Leticia'},
   {species:'Micrurus surinamensis',value:.4,reported:'Micrurus surinamensis surinamensis, Leticia'},
   {species:'Micrurus surinamensis',value:.2,reported:'Micrurus surinamensis surinamensis, Manaus'}]},
 {id:'vest1991',year:1991,label:'Vest et al. (1991)',url:'https://doi.org/10.1016/0041-0101(91)90029-Q',
  method:'Swiss-Webster mice, intravenous; approximate result',records:[
   {species:'Boiga irregularis',value:80,reported:'Boiga irregularis, approximately'}]},
 {id:'tu1977',year:1977,label:'Tu (1977), cited by Young (1996)',url:'https://doi.org/10.1590/S0104-79301996000100007',
  method:'Mouse, intravenous; a previously reported value cited by Young, not measured in Young’s experiment',records:[
   {species:'Dispholidus typus',value:.071,reported:'Dispholidus typus; cited historical value'}]},
 {id:'taipan2011',year:2011,label:'Vargas et al. (2011)',url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC3096592/',
  method:'CD-1 mice, intravenous; Papua New Guinea sample',records:[
   {species:'Oxyuranus scutellatus',value:.0042,reported:'Oxyuranus scutellatus, Papua New Guinea'}]},
 {id:'coral2011',year:2011,label:'Salazar et al. (2011), Table 1',url:'https://pmc.ncbi.nlm.nih.gov/articles/PMC3304457/',
  method:'Mice, intravenous; Florida sample',records:[
   {species:'Micrurus fulvius',value:.32,reported:'Micrurus fulvius fulvius, Tampa, Florida'}]},
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
function forSpecies(species){
  // Keep regional samples separate in the details and never borrow a value
  // from a different species when the user selected an exact source profile.
  const candidates=studies.map(study=>({study,records:study.records.filter(r=>r.species===species)}))
    .filter(result=>result.records.length).sort((a,b)=>b.study.year-a.study.year);
  if(!candidates.length)return null;
  const result=candidates[0],values=result.records.map(r=>r.value);
  // One actual sample, not the midpoint of different geographic samples.
  // The first published sample in the newest curated study is stable and
  // remains explicitly identified; other samples remain visible in details.
  return {...result,species,reference:result.records[0],min:Math.min(...values),max:Math.max(...values)};
}
function estimate(matches){
  // Fix the comparison set first: do not search down the ranking for data.
  const considered=(matches||[]).slice(0,5);
  const top=considered.map((match,index)=>({match,rank:index+1})).filter(({match})=>match.shared.length>=3&&match.shared.length/match.entered>=.6&&match.adjustedDistance<=20);
  const names=new Set(top.map(({match})=>match.profile.species_name));
  const candidates=studies.map(study=>{
    const records=study.records.filter(r=>names.has(r.species));
    const covered=new Set(records.map(r=>r.species));
    const closest=top.find(({match})=>covered.has(match.profile.species_name));
    return {study,records,speciesCount:covered.size,closestRank:closest?.rank??Infinity,closestSpecies:closest?.match.profile.species_name};
  }).filter(r=>r.speciesCount>=2).sort((a,b)=>a.closestRank-b.closestRank||b.speciesCount-a.speciesCount||b.study.year-a.study.year);
  if(!candidates.length)return null;
  const result=candidates[0],values=result.records.map(r=>r.value);
  return {...result,consideredCount:considered.length,min:Math.min(...values),max:Math.max(...values)};
}
const api={studies,forSpecies,estimate};if(typeof module!=='undefined')module.exports=api;else root.Ld50Reference=api;
})(typeof window!=='undefined'?window:this);

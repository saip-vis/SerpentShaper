const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const Compare=require('./profile-comparison.js'),Starters=require('./species-starters.js');
const scope={window:{}};
for(const name of ['venom-data.js','../PhysicalRendererTest/presets/species-presets.js'])vm.runInNewContext(fs.readFileSync(__dirname+'/'+name,'utf8'),scope);
const data=scope.window.SERPENT_VENOM_DATA,presets=scope.window.SERPENT_PRESETS.presets;
for(const species of ['Crotalus atrox','Naja kaouthia','Ophiophagus hannah']){
  const entry=Starters.build(data,presets).find(s=>s.species===species);
  const values=Starters.valuesForProfile(data.controls,entry.profile);
  const first=Compare.rank(values,data.profiles,data.controls)[0];
  assert.equal(first.profile.species_name,species,`${species} must rank first for its own reported profile`);
  assert.equal(first.adjustedDistance,0);
}
const controls=[{id:'a',short_label:'A',source_toxin_ids:['A']},{id:'b',short_label:'B',source_toxin_ids:['B']}];
const profile=(name,a,b)=>({species_name:name,source_row:1,components:[{toxin_id:'A',value:a,status:'reported_positive'},{toxin_id:'B',value:b,status:'reported_positive'}]});
const exact=profile('Exact',20,0),missing=profile('Missing',20,null),different=profile('Different',20,40);
assert.equal(Compare.compare({a:20,b:0},exact,controls).adjustedDistance,0,'a user-entered zero is compared as a measurement');
assert.equal(Compare.compare({a:20,b:0},missing,controls).adjustedDistance,12.5,'missing data incurs a 25-point per-field penalty');
assert.equal(Compare.compare({a:20,b:null},missing,controls).adjustedDistance,0,'blank user values are ignored');
assert.equal(Compare.compare({a:20,b:0},different,controls).adjustedDistance,20);
assert.deepEqual(Compare.rank({a:20,b:0},[different,missing,exact],controls).map(r=>r.profile.species_name),['Exact','Missing','Different']);
const uncertain=profile('Uncertain',20,0);uncertain.components[1].status='source_uncertain';
assert.equal(Compare.compare({a:20,b:0},uncertain,controls).adjustedDistance,12.5,'disputed measurements are missing, not zero');
assert.equal(Compare.compare({b:0},missing,controls),null,'no shared data is not a match');
const second=profile('Exact',19,1);second.source_row=2;
assert.equal(Compare.rank({a:19,b:1},[exact,second],controls)[0].profile.source_row,2,'show the best sample per species');
assert.equal(Compare.rank({},[exact],controls).length,0);
console.log('Real-source comparison, missingness, zeros, exact profiles and best sample verified.');

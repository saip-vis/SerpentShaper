const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const D=require('./detailed-concept.js'),I=require('./connected-inference.js'),R=require('../PhysicalRendererTest/species-renderer.js'),S=require('./species-starters.js');
const G=require('../PhysicalRendererTest/species-geometry.js');
const scope={window:{}};for(const file of ['venom-data.js','connected-model.js','../PhysicalRendererTest/presets/species-presets.js'])vm.runInNewContext(fs.readFileSync(__dirname+'/'+file,'utf8'),scope);
const {controls,profiles}=scope.window.SERPENT_VENOM_DATA,presets=scope.window.SERPENT_PRESETS.presets,model=scope.window.SERPENT_CONNECTED_MODEL;
const starters=S.build(scope.window.SERPENT_VENOM_DATA,presets);
assert.equal(starters.length,149);assert.equal(new Set(starters.map(x=>x.species)).size,149);
const mamba=starters.find(x=>x.species==='Dendroaspis polylepis');
assert.equal(S.valuesForProfile(controls,mamba.profile).natriuretic_peptide,null,'uncertain source values must remain excluded');
assert.equal(S.valuesForProfile([{id:'test',source_toxin_ids:['X']}],{components:[{toxin_id:'X',status:'source_uncertain',value:2.9}]}).test,null,'an uncertain value must be held even if a future bundle contains a numeric value');
for(const name of ['Crotalus atrox','Naja kaouthia','Dendroaspis polylepis','Laticauda colubrina']){
  const source=starters.find(x=>x.species===name),values=S.valuesForProfile(controls,source.profile),concept=I.predict(values,model);
  assert.ok(concept,`${name} has a usable starting profile`);
  for(const surface of ['dorsal','ventral']){
    const drawing=D.render(concept,presets,R,{surface});
    assert.ok(drawing.scaleCount>100,`${name} has individual scales`);
    assert.match(drawing.svg,/generated_concept/);assert.match(drawing.svg,/connected_hybrid_prototype/);
    assert.doesNotMatch(drawing.svg,/NaN|Infinity|undefined/);assert.match(drawing.shape.path,/Z$/);
    assert.equal(drawing.preset.species_id,null,'a generated concept is not assigned a species');
    assert.equal(drawing.preset.source_species_name,'Hypothetical snake concept');
  }
}
const v={'3ftx':25,pla2:15,svmp:40,svsp:0},base=I.predict(v,model),off=I.predict({...v,svsp:0},model),near=I.predict({...v,svsp:1e-8},model);
const baseDrawing=D.render(base,presets,R),offDrawing=D.render(off,presets,R),nearDrawing=D.render(near,presets,R);
assert.equal(baseDrawing.shape.path,offDrawing.shape.path);
assert.equal(baseDrawing.svg,offDrawing.svg);
let largest=0;for(let i=0;i<baseDrawing.shape.points.length;i++){const p=baseDrawing.shape.points[i],q=nearDrawing.shape.points[i];largest=Math.max(largest,Math.hypot(p.x-q.x,p.y-q.y),Math.abs(p.r-q.r));}
assert.ok(largest<.001,'turning on a toxin near zero must not jump in geometry');
const plain=D.render({...base,traits:{...base.traits,hood:0,monocle:0}},presets,R);
const hood=D.render({...base,traits:{...base.traits,hood:1,monocle:1}},presets,R);
assert.ok(hood.shape.points.some((p,i)=>p.r>plain.shape.points[i].r+5),'hood control widens the anterior geometry');
assert.match(hood.svg,/concept-hood-mark/);
const wide=D.render({...base,traits:{...base.traits,tailTaper:0}},presets,R);
const tapered=D.render({...base,traits:{...base.traits,tailTaper:1}},presets,R);
assert.notEqual(wide.shape.path,tapered.shape.path,'tail taper changes the shape');
const unflattened=D.render({...base,traits:{...base.traits,paddle:0}},presets,R);
const flattened=D.render({...base,traits:{...base.traits,paddle:1}},presets,R);
assert.ok(flattened.shape.points.some((p,i)=>p.r>unflattened.shape.points[i].r+5),'paddle control smoothly widens the tail');
const noAccent=D.render({...base,traits:{...base.traits,bands:1,bandAccent:0}},presets,R);
const accent=D.render({...base,traits:{...base.traits,bands:1,bandAccent:1}},presets,R);
assert.notEqual(noAccent.svg,accent.svg,'band accent changes the rendering');
// Strong ring/triad-style cues should extend to the generated ventral plates,
// without asserting that an individual snake's underside has been observed.
const ventralNoAccent=D.render({...base,traits:{...base.traits,bands:1,bandAccent:0}},presets,R,{surface:'ventral'});
const ventralAccent=D.render({...base,traits:{...base.traits,bands:1,bandAccent:1}},presets,R,{surface:'ventral'});
const ventralPlates=svg=>svg.match(/<g id="ventral-plates">([\s\S]*?)<\/g>/)[1];
assert.notEqual(ventralPlates(ventralAccent.svg),ventralPlates(ventralNoAccent.svg),'band accents should affect ventral plates');
const ventralNoBands=D.render({...base,traits:{...base.traits,bands:0,bandAccent:1}},presets,R,{surface:'ventral'});
const ventralPlain=D.render({...base,traits:{...base.traits,bands:0,bandAccent:0}},presets,R,{surface:'ventral'});
assert.equal(ventralPlates(ventralNoBands.svg),ventralPlates(ventralPlain.svg),'accent alone must not introduce bands');
const rattleOpacity=amount=>{
  const svg=D.render({...base,traits:{...base.traits,rattle:amount}},presets,R).svg;
  return Number(svg.match(/<g id="rattle" opacity="([^"]+)"/)[1]);
};
assert.equal(rattleOpacity(.10),0,'a tiny rattle cue should not visibly add an appendage');
assert.ok(rattleOpacity(.39)>.39,'a moderate rattle cue should be visible');
assert.equal(rattleOpacity(.7),1,'a strong rattle cue should be fully visible');
const patterns=D.render({...base,traits:{...base.traits,diamond:1,bands:1,blotches:1}},presets,R);
assert.notEqual(patterns.svg,plain.svg);
// Head lengths must not cause the geometry engine to skip a different first body station.
let previous=null;
for(let i=0;i<=100;i++){
  const spec=D.makePreset({...base,traits:{...base.traits,headLength:i/100}},presets),shape=G.geometry(spec,{conceptHood:base.traits.hood});
  if(previous){assert.equal(shape.points.length,previous.points.length);for(let j=0;j<shape.points.length;j++)assert.ok(Math.hypot(shape.points[j].x-previous.points[j].x,shape.points[j].y-previous.points[j].y)<2,'small head adjustments must not skip a station');}
  previous=shape;
}
for(const entry of starters){
  const c=I.predict(S.valuesForProfile(controls,entry.profile),model);assert.ok(c,entry.species);
  for(const surface of ['dorsal','ventral']){const result=D.render(c,presets,R,{surface});assert.ok(result.scaleCount>100,entry.species);assert.doesNotMatch(result.svg,/NaN|Infinity|undefined/,entry.species);assert.match(result.shape.path,/Z$/);}
}
console.log('149 starting species, accepted source values, detailed contours, gradual hood/tail and two surfaces verified.');

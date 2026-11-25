/* Reproducible visual and numeric checks of the current experimental model.
 * The species illustrations are authored references, not verified photographs.
 * Test profiles are training inputs; grouped evaluation comes from the report.
 */
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto');
const ROOT=path.resolve(__dirname,'..'),OUT=path.join(ROOT,'reports/visual_generation_checks'),WORK=path.join(OUT,'.work');
const I=require('../MainInterface/connected-inference.js'),D=require('../MainInterface/detailed-concept.js');
const R=require('../PhysicalRendererTest/species-renderer.js'),S=require('../MainInterface/species-starters.js');
const sandbox={window:{}};
for(const f of ['MainInterface/venom-data.js','MainInterface/connected-model.js','PhysicalRendererTest/presets/species-presets.js'])vm.runInNewContext(fs.readFileSync(path.join(ROOT,f),'utf8'),sandbox);
const data=sandbox.window.SERPENT_VENOM_DATA,model=sandbox.window.SERPENT_CONNECTED_MODEL,presets=sandbox.window.SERPENT_PRESETS.presets;
const report=JSON.parse(fs.readFileSync(path.join(ROOT,'ML/learned_morphology/connected_prototype.json'),'utf8'));
const photoHoldout=JSON.parse(fs.readFileSync(path.join(ROOT,'ML/image_traits/pattern_holdout.json'),'utf8'));
const starters=S.build(data,presets),species=['Crotalus atrox','Naja kaouthia','Dendroaspis polylepis','Ophiophagus hannah','Micrurus alleni','Daboia russelii','Bungarus multicinctus','Hydrophis platurus'];
const briefTraits=['headWidth','headLength','bodyWidth','hood','diamond','monocle','rattle','tailTaper','bands','blotches','paddle','bandAccent'];
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT,file))).digest('hex');
const pick=(obj,keys)=>Object.fromEntries(keys.map(k=>[k,obj[k]]));
function fromArray(values){return Object.fromEntries(model.targets.map((key,i)=>[key,values[i]]));}
function filename(speciesName){return speciesName.toLowerCase().replace(/[^a-z0-9]+/g,'_');}
function writeSVG(name,svg){fs.writeFileSync(path.join(WORK,name),svg);}
fs.mkdirSync(WORK,{recursive:true});
const cases=[];
for(const name of species){
  const entry=starters.find(x=>x.species===name);if(!entry)throw Error('Missing species: '+name);
  const input=S.valuesForProfile(data.controls,entry.profile),concept=I.predict(input,model);
  if(!concept)throw Error('Profile did not generate: '+name);
  const reference=entry.preset.artistic_parameters,full=D.render(concept,presets,R,{surface:'dorsal'}),underside=D.render(concept,presets,R,{surface:'ventral'});
  if(!full||!underside||/NaN|Infinity|undefined/.test(full.svg+underside.svg))throw Error('Invalid SVG: '+name);
  const ref=R.render(entry.preset,{surface:'dorsal',framing:'full'}),file=filename(name);
  writeSVG(file+'_generated.svg',full.svg);writeSVG(file+'_ventral.svg',underside.svg);writeSVG(file+'_reference.svg',ref.svg);
  const held=report.evaluation.species_results.find(x=>x.species===name);
  cases.push({species:name,common_name:entry.preset.common_name,profile_id:entry.profile.profile_id,source_row:entry.profile.source_row,
    input_values:input,reference:{body_plan:reference.body_plan,pattern:reference.pattern,tail_type:reference.tail_type,skin_color:reference.skin_color},
    training_profile:model.training_sources.some(x=>x.profile_id===entry.profile.profile_id),
    authored_targets:held?pick(fromArray(held.actual),briefTraits):null,predicted:pick(concept.traits,briefTraits),predicted_colors:concept.colors,
    grouped_holdout:held?{predicted:pick(fromArray(held.predicted),briefTraits),note:'Genus held out during development; values are averaged across this source label’s available profiles. Folds were used in model selection and are not a final independent test.'}:null,
    drawing_checks:{dorsal_closed:full.shape.path.endsWith('Z'),ventral_closed:underside.shape.path.endsWith('Z'),dorsal_scale_count:full.scaleCount,ventral_scale_count:underside.scaleCount},
    generated_svg:file+'_generated.svg',ventral_svg:file+'_ventral.svg',reference_svg:file+'_reference.svg'});
}
const inputFor=name=>S.valuesForProfile(data.controls,starters.find(x=>x.species===name).profile);
const left=inputFor('Crotalus atrox'),right=inputFor('Naja kaouthia'),trajectory=[];
let maxGeometryStep=0,maxControlStep=0,previous=null;
for(let i=0;i<=100;i++){
  const f=i/100,values=Object.fromEntries(model.feature_ids.map(id=>[id,(left[id]||0)*(1-f)+(right[id]||0)*f]));
  const c=I.predict(values,model),drawing=D.render(c,presets,R,{surface:'dorsal'});if(!drawing)throw Error('Interpolation failed at '+i);
  if(previous){
    if(previous.drawing.shape.points.length!==drawing.shape.points.length)throw Error('Body point count changed');
    const delta=Math.max(...drawing.shape.points.map((p,j)=>Math.max(Math.hypot(p.x-previous.drawing.shape.points[j].x,p.y-previous.drawing.shape.points[j].y),Math.abs(p.r-previous.drawing.shape.points[j].r))));
    maxGeometryStep=Math.max(maxGeometryStep,delta);
    maxControlStep=Math.max(maxControlStep,...I.TRAITS.map(k=>Math.abs(c.traits[k]-previous.concept.traits[k])));
  }
  if(i%25===0)writeSVG(`transition_${i}.svg`,drawing.svg);
  trajectory.push({fraction:f,traits:pick(c.traits,briefTraits),colors:c.colors,scale_count:drawing.scaleCount});previous={concept:c,drawing};
}
const baseline={'3ftx':25,pla2:15,svmp:40},componentChecks=[];
// Exercise multiple trajectories, including the new design controls. These
// are engineering stress tests, not evidence of real intermediate phenotypes.
const transitionPairs=[['Crotalus atrox','Naja kaouthia'],['Bungarus multicinctus','Daboia russelii'],['Dendroaspis polylepis','Micrurus alleni'],['Ophiophagus hannah','Hydrophis platurus'],['Daboia russelii','Dendroaspis polylepis']];
const transitionChecks=transitionPairs.map(([from,to])=>{
  const a=inputFor(from),b=inputFor(to);let last=null,largest=0;
  for(let step=0;step<=100;step++){
    const f=step/100,values=Object.fromEntries(model.feature_ids.map(id=>[id,(a[id]||0)*(1-f)+(b[id]||0)*f]));
    const c=I.predict(values,model);if(last)largest=Math.max(largest,...I.TRAITS.map(k=>Math.abs(c.traits[k]-last.traits[k])));last=c;
  }
  return {from,to,steps:100,max_adjacent_control_change:largest};
});
for(const id of model.feature_ids){
  const origin={...baseline,[id]:0},changed={...origin,[id]:10},restored={...changed,[id]:0};
  if(!Object.values(origin).some(v=>v>0))continue;
  const a=I.predict(origin,model),b=I.predict(changed,model),c=I.predict(restored,model);
  const before=D.render(a,presets,R),after=D.render(c,presets,R);
  const zeroRestored=JSON.stringify(a.traits)===JSON.stringify(c.traits)&&JSON.stringify(a.colors)===JSON.stringify(c.colors)&&before.shape.path===after.shape.path;
  const largest=I.TRAITS.map(k=>({trait:k,change:b.traits[k]-a.traits[k]})).sort((x,y)=>Math.abs(y.change)-Math.abs(x.change))[0];
  componentChecks.push({component:id,zero_restores_output:zeroRestored,largest_control_effect:largest});
}
const result={schema_version:1,status:'engineering_and_authored_reference_checks_not_biological_validation',
  caveats:['The eight displayed starting profiles were used to train the current model; comparison to authored SVG references is not an unseen-image or biological test.',
    'Grouped holdout results average by source species and were examined during model development, so they are not a final untouched test.',
    'A hypothetical blend has no known correct phenotype. Missing entries are set to zero solely for the interpolation exercise; this does not establish absence.',
    'Control values are illustration settings, not probabilities or measured traits.'],
  source_hashes:Object.fromEntries(['scripts/evaluate_visual_generation.cjs','MainInterface/venom-data.js','MainInterface/connected-model.js','MainInterface/connected-inference.js','MainInterface/species-starters.js','MainInterface/detailed-concept.js','PhysicalRendererTest/presets/species-presets.json','PhysicalRendererTest/species-geometry.js','PhysicalRendererTest/species-renderer.js','ML/learned_morphology/connected_prototype.json','ML/image_traits/pattern_holdout.json'].map(f=>[f,hash(f)])),
  cases,component_checks:componentChecks,transition_checks:transitionChecks,photo_pattern_check:photoHoldout.records.map(photo=>{
    const held=report.evaluation.species_results.find(x=>x.species===photo.species);
    const records=JSON.parse(fs.readFileSync(path.join(ROOT,photo.manifest),'utf8'));
    const source=records.find(x=>x.image_id===photo.image_id);
    if(!source||source.review_status!=='accepted'||source.rendering_training_excluded)throw Error('Reserved photo is not an eligible reviewed source: '+photo.image_id);
    return {...photo,photo_page:source.photo_page,photo_attribution:source.attribution,photo_sha256:source.sha256,
      heldout_diamond_control:held?fromArray(held.predicted).diamond:null,
      note:`${photo.note} Held-out shape-model values average profiles and were obtained during model development, not a final untouched test.`};
  }),transition:{from:'Crotalus atrox source row 127',to:'Naja kaouthia source row 267',steps:100,max_step_in_control:maxControlStep,max_step_in_body_point_or_radius:maxGeometryStep,trajectory}};
fs.writeFileSync(path.join(OUT,'results.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,component_checks:componentChecks.length,zero_restored:componentChecks.filter(x=>x.zero_restores_output).length,transition_steps:100,max_step_in_control:maxControlStep,max_step_in_body_point_or_radius:maxGeometryStep},null,2));

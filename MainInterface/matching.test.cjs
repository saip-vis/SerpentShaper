const assert=require('node:assert/strict');
const fs=require('node:fs');const vm=require('node:vm');
const {compare,rank,influences,totals}=require('./matching.js');
const sandbox={window:{}};vm.runInNewContext(fs.readFileSync(__dirname+'/venom-data.js','utf8'),sandbox);
const {profiles,controls}=sandbox.window.SERPENT_VENOM_DATA;
assert.equal(profiles.length,276);assert.equal(controls.length,12);
assert.ok(profiles.every(p=>p.components.length===130),'preserve all source categories');
const find=(id)=>profiles.find(p=>p.profile_id===id);
const cobra=find('vd2023_e2d1aa974518_r269');assert.ok(cobra&&cobra.preset_id==='naja_kaouthia');
const controlValues=Object.fromEntries(controls.map(c=>[c.id,cobra.components.find(x=>x.toxin_id===c.source_toxin_ids[0]).value]));
const comparison=compare(controlValues,cobra,controls);assert.equal(comparison.meanDifference,0);assert.equal(comparison.compared,comparison.selected);
assert.equal(rank(controlValues,profiles,controls)[0].profile.profile_id,cobra.profile_id,'a source should be its own closest comparison');
const mixed=influences(controlValues,profiles,controls);assert.ok(mixed.length>3);
assert.equal(new Set(mixed.map(r=>r.profile.species_name)).size,mixed.length,'multiple samples of the same species must not dominate the mix');
assert.ok(mixed.every(r=>r.compared>=3),'each visual influence needs at least three shared categories');
assert.ok(Math.abs(mixed.reduce((n,r)=>n+r.weight,0)-1)<1e-12);
const pla=controls.find(c=>c.id==='pla2'), svmp=controls.find(c=>c.id==='svmp');
const sample={components:[{toxin_id:pla.source_toxin_ids[0],value:null},{toxin_id:svmp.source_toxin_ids[0],value:20}]};
const result=compare({pla2:0,svmp:10},sample,controls);assert.equal(result.compared,1);assert.equal(result.selected,1);assert.equal(result.meanDifference,10,'zero input is inactive while missing source values remain missing');
assert.equal(compare({pla2:0},sample,controls),null,'a zero input is inactive');
assert.equal(compare({svmp:10},{components:[{toxin_id:svmp.source_toxin_ids[0],value:0}]},controls).meanDifference,10,'a recorded zero in the reference is still a real comparison');
assert.equal(compare({pla2:null},sample,controls),null,'unspecified input produces no comparison');
assert.equal(influences({pla2:10,svmp:20},profiles,controls).length,0,'two-category coincidences cannot contribute to a concept');
// Smooth weights: when similar references exchange rank, neither disappears.
const syntheticControls=['a','b','c'].map(id=>({id,short_label:id,source_toxin_ids:[id]}));
const makeProfile=(species,a)=>({species_name:species,preset_id:species,source_row:1,components:[{toxin_id:'a',value:a},{toxin_id:'b',value:10},{toxin_id:'c',value:20}]});
const synthetics=[makeProfile('alpha',10),makeProfile('beta',11),makeProfile('gamma',12),makeProfile('delta',13)];
const left=influences({a:11.49,b:10,c:20},synthetics,syntheticControls),right=influences({a:11.51,b:10,c:20},synthetics,syntheticControls);
assert.equal(left.length,4);assert.equal(right.length,4);
for(const l of left){const r=right.find(x=>x.profile.species_name===l.profile.species_name);assert.ok(Math.abs(l.weight-r.weight)<.01,'small slider changes should produce small weight changes');}
const thin=makeProfile('thin',10);thin.components[1].value=null;
assert.ok(!influences({a:10,b:10,c:20},[thin],syntheticControls).length,'insufficient overlap is not evidence for a rendering');
const fourControls=[...syntheticControls,{id:'d',short_label:'d',source_toxin_ids:['d']}];
const incomplete=makeProfile('incomplete',10),far=makeProfile('far',80);far.components.push({toxin_id:'d',value:90});
assert.equal(influences({a:10,b:10,c:20,d:0},[incomplete,far],fourControls)[0].profile.species_name,'incomplete','coverage should be balanced against differences rather than always outranking them');
const accounting=totals({pla2:20,svmp:10,other:null},[{value:5},{value:null}]);assert.equal(accounting.total,35);assert.equal(accounting.unallocated,65);
assert.equal(totals({pla2:90,svmp:20},[]).over,10);
const presetContext={window:{}};vm.runInNewContext(fs.readFileSync(__dirname+'/../PhysicalRendererTest/presets/species-presets.js','utf8'),presetContext);
const preset=presetContext.window.SERPENT_PRESETS.presets.find(p=>p.preset_id===cobra.preset_id);
const renderer=require('../PhysicalRendererTest/species-renderer.js');
for(const surface of ['dorsal','ventral'])assert.match(renderer.render(preset,{surface}).svg,/<svg/);
console.log('Main interface data, source preservation, reference matching, accounting, and both SVG surfaces verified.');
// Exercise the browser controller with a small DOM mock; no browser or network required.
class NodeMock {
  constructor(tag='div'){this.tag=tag;this.children=[];this.events={};this.attrs={};this.style={};this.value='';this.textContent='';this.hidden=false;this.classList={toggle(){}};}
  append(...nodes){this.children.push(...nodes);} replaceChildren(...nodes){this.children=nodes;} setAttribute(k,v){this.attrs[k]=String(v);} removeAttribute(k){delete this.attrs[k];}
  addEventListener(k,fn){this.events[k]=fn;} fire(k){this.events[k]({target:this});}
}
const ids=['primary-controls','advanced-controls','source-profile','dataset-link','reset','dorsal','ventral','unknown-help','unknown-info','source-note','retained-section','retained-count','retained-list','total','progress-bar','balance-text','matches','empty-drawing','snake-drawing','snake-name','scientific-name','selection-note','anatomy-link','download-svg','render-mode','mode-note','reference-intro','comparison-note'];
const dom=Object.fromEntries(ids.map(id=>[id,new NodeMock()]));dom['progress-bar'].parentElement=new NodeMock();
const created=[];const fakeDocument={getElementById:id=>dom[id],createElement:tag=>{const x=new NodeMock(tag);created.push(x);return x;},createTextNode:text=>({textContent:text})};
const styleContext={window:{}};vm.runInNewContext(fs.readFileSync(__dirname+'/visual-style-model.js','utf8'),styleContext);
vm.runInNewContext(fs.readFileSync(__dirname+'/photo-cues.js','utf8'),styleContext);
let lastRenderOptions=null,lastRenderedPreset=null;
const context={window:{SERPENT_VENOM_DATA:sandbox.window.SERPENT_VENOM_DATA,SERPENT_PRESETS:presetContext.window.SERPENT_PRESETS,SERPENT_STYLE_MODEL:styleContext.window.SERPENT_STYLE_MODEL,SERPENT_PHOTO_CUES:styleContext.window.SERPENT_PHOTO_CUES},document:fakeDocument,SerpentMatching:require('./matching.js'),SerpentStyle:require('./style-inference.js'),SharedMorphology:require('../SharedRendererTest/shared-morphology.js'),SharedConcept:require('./shared-concept.js'),SpeciesRenderer:{render:(p,o)=>{lastRenderOptions=o;lastRenderedPreset=p;return {svg:`<svg data-skin="${o.skinColor||''}" data-mark="${o.ringColor||''}"></svg>`};}},console,Number,Map,Set,URLSearchParams};
vm.runInNewContext(fs.readFileSync(__dirname+'/app.js','utf8'),context);
assert.equal(dom['source-profile'].value,'');assert.equal(dom['snake-name'].textContent,'Your snake concept');
assert.equal(dom['empty-drawing'].hidden,false,'the page must not silently start with a cobra');
const diamond=find('vd2023_e2d1aa974518_r127');
dom['source-profile'].value=diamond.profile_id;dom['source-profile'].fire('change');
assert.equal(dom['snake-name'].textContent,'Your snake concept');
assert.equal(lastRenderedPreset.source_species_name,'Hypothetical snake concept');
assert.equal(lastRenderedPreset.artistic_parameters.body_plan,'viper');
assert.equal(lastRenderedPreset.artistic_parameters.pattern,'diamonds');
assert.equal(lastRenderedPreset.artistic_parameters.tail_type,'rattle');
assert.equal(lastRenderOptions.conceptMetadata.bodyPlan,'viper');
assert.equal(lastRenderOptions.conceptMetadata.referenceStyleMix[0].species,'Crotalus atrox');
assert.ok(lastRenderOptions.conceptMetadata.photoCue,'diamondback reference applies the photo cue');
assert.match(dom['selection-note'].textContent,/photo color cue applied/);
dom.ventral.fire('click');assert.equal(lastRenderOptions.conceptMetadata.photoCue,null,'dorsal photo cues must not affect the ventral view');
dom.dorsal.fire('click');assert.ok(lastRenderOptions.conceptMetadata.photoCue);
const profileAnatomy=JSON.stringify(lastRenderedPreset.artistic_parameters);
const profileSvg=dom['snake-drawing'].innerHTML;
dom.reset.fire('click');assert.equal(dom['total'].textContent,'0%');assert.equal(dom['empty-drawing'].hidden,false);
for(const control of controls){
  const component=diamond.components.find(c=>c.toxin_id===control.source_toxin_ids[0]);
  if(component.value!==null){const input=created.find(x=>x.id===`number-${control.id}`);input.value=String(component.value);input.fire('input');}
}
assert.equal(JSON.stringify(lastRenderedPreset.artistic_parameters),profileAnatomy,'manual values and the identical source profile must generate the same anatomy');
assert.equal(dom['snake-drawing'].innerHTML,profileSvg,'manual values and the identical source profile must generate the same style');
assert.equal(dom['snake-name'].textContent,'Your snake concept');
assert.ok(Math.abs(lastRenderOptions.conceptMetadata.referenceStyleMix.reduce((s,r)=>s+r.weight,0)-1)<1e-12);
dom['source-profile'].value='vd2023_e2d1aa974518_r269';dom['source-profile'].fire('change');
assert.equal(lastRenderedPreset.artistic_parameters.body_plan,'cobra','venom changes can change the broad form');
assert.equal(dom['snake-name'].textContent,'Your snake concept','the concept is not assigned a species');
dom['source-profile'].value='vd2023_e2d1aa974518_r189';dom['source-profile'].fire('change');
assert.match(dom['source-note'].textContent,/NP value is excluded/);
assert.ok(dom.matches.children.some(card=>card.children.some(child=>child.children?.some(text=>/NP value is excluded/.test(text.textContent)))));
const quarantined=find('vd2023_e2d1aa974518_r189').components.find(c=>c.toxin_id==='vd2023_H');
assert.equal(quarantined.value,null);assert.equal(quarantined.original_value,2.9);assert.equal(quarantined.status,'source_uncertain');
assert.equal(compare({natriuretic_peptide:2.9},find('vd2023_e2d1aa974518_r189'),controls),null);
dom.reset.fire('click');
const setInput=(name,value)=>{const input=created.find(x=>x.id===`number-${name}`);input.value=value;input.fire('input');return input;};
setInput('pla2','7.3');setInput('svmp','49.7');setInput('crisp','4.3');
const absentAnatomy=JSON.stringify(lastRenderedPreset.artistic_parameters),absentSvg=dom['snake-drawing'].innerHTML;
const absentMix=JSON.stringify(lastRenderOptions.conceptMetadata.referenceStyleMix);
setInput('svsp','19.8');
assert.notEqual(JSON.stringify(lastRenderOptions.conceptMetadata.referenceStyleMix),absentMix,'turning on a component changes the reference comparison');
const zeroControl=setInput('svsp','0');
assert.equal(zeroControl.value,'0','the explicitly entered zero remains visible');
assert.equal(lastRenderOptions.conceptMetadata.venomInputs.svsp,0,'the explicit zero remains in the exported input metadata');
assert.equal(JSON.stringify(lastRenderOptions.conceptMetadata.referenceStyleMix),absentMix,'returning to zero restores the previous reference blend');
assert.equal(JSON.stringify(lastRenderedPreset.artistic_parameters),absentAnatomy,'returning to zero restores the previous anatomy');
assert.equal(dom['snake-drawing'].innerHTML,absentSvg,'returning to zero restores the previous visible style');
const svspSlider=created.find(x=>x.type==='range'&&x.attrs['aria-label']==='Venom serine proteases percentage slider');
assert.ok(svspSlider,'the SVSP slider must be accessible');
svspSlider.value='19.8';svspSlider.fire('input');
assert.notEqual(JSON.stringify(lastRenderOptions.conceptMetadata.referenceStyleMix),absentMix);
svspSlider.value='0';svspSlider.fire('input');
assert.equal(zeroControl.value,'0','slider zero is shown in the number field');
assert.equal(svspSlider.attrs['aria-valuetext'],'0 percent, inactive for generation');
assert.equal(JSON.stringify(lastRenderOptions.conceptMetadata.referenceStyleMix),absentMix,'slider interaction restores the earlier reference blend');
assert.equal(dom['snake-drawing'].innerHTML,absentSvg,'slider interaction restores the earlier visible style');
setInput('pla2','0');
assert.equal(dom['empty-drawing'].hidden,false,'zero values do not satisfy the minimum number of active inputs');
// Opt-in shared mode compares only the supported species, produces its own
// metadata, and supports separate illustrative surfaces without changing input.
dom['source-profile'].value=diamond.profile_id;dom['source-profile'].fire('change');
dom['render-mode'].value='shared';dom['render-mode'].fire('change');
assert.equal(dom['mode-note'].hidden,false);
assert.match(dom['snake-drawing'].innerHTML,/shared_control_illustration/);
assert.match(dom['snake-drawing'].innerHTML,/three_reference_illustrative_pilot/);
assert.match(dom['reference-intro'].textContent,/only its three reference species/);
assert.equal(dom['download-svg'].disabled,false);
const sharedDorsal=dom['snake-drawing'].innerHTML;dom.ventral.fire('click');
assert.match(dom['snake-drawing'].innerHTML,/ventral-plates/);
assert.notEqual(dom['snake-drawing'].innerHTML,sharedDorsal);dom.dorsal.fire('click');
assert.equal(dom['snake-drawing'].innerHTML,sharedDorsal);
const sharedVisible=s=>s.replace(/<metadata>.*?<\/metadata>/,'');
const sharedProfileSvg=sharedVisible(dom['snake-drawing'].innerHTML);
dom.reset.fire('click');
for(const control of controls){const component=diamond.components.find(c=>c.toxin_id===control.source_toxin_ids[0]);if(component.value!==null)setInput(control.id,String(component.value));}
assert.equal(sharedVisible(dom['snake-drawing'].innerHTML),sharedProfileSvg,'the same venom values must produce the same pilot concept regardless of starting profile');
dom.reset.fire('click');setInput('pla2','7.3');setInput('svmp','49.7');setInput('crisp','4.3');
const originalShared=sharedVisible(dom['snake-drawing'].innerHTML);
setInput('svsp','19.8');assert.notEqual(sharedVisible(dom['snake-drawing'].innerHTML),originalShared);
setInput('svsp','0');assert.equal(sharedVisible(dom['snake-drawing'].innerHTML),originalShared,'turning a component back off restores the shared drawing');
dom['render-mode'].value='reference';dom['render-mode'].fire('change');
assert.equal(dom['mode-note'].hidden,true);
// Real-data transition between two illustrative input mixtures. Explicit zero
// crosses into the inactive state, so use a small positive starting value for
// this fixed-active-set continuity check. Values are illustrative inputs.
const start={'3ftx':.1,pla2:7.3,svmp:49.7,crisp:4.3},end={'3ftx':56.5,pla2:26.9,svmp:1.1,crisp:5.4};
let previousWeights=null;
for(let i=0;i<=100;i++){
  const t=i/100,query=Object.fromEntries(Object.keys(start).map(k=>[k,start[k]*(1-t)+end[k]*t]));
  const weights=new Map(influences(query,profiles,controls).map(x=>[x.profile.species_name,x.weight]));
  assert.ok(Math.abs([...weights.values()].reduce((sum,w)=>sum+w,0)-1)<1e-12);
  if(previousWeights){const names=new Set([...weights.keys(),...previousWeights.keys()]);const movement=[...names].reduce((sum,name)=>sum+Math.abs((weights.get(name)||0)-(previousWeights.get(name)||0)),0);assert.ok(movement<.15,'small changes to a fixed set of venom values should not abruptly replace the reference blend');}
  previousWeights=weights;
}
console.log('Blank start, diamondback-like shape, manual-input consistency and exclusions verified.');

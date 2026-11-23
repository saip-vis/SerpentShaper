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
const mixed=influences(controlValues,profiles,controls);assert.equal(mixed.length,3);
assert.equal(new Set(mixed.map(r=>r.profile.species_name)).size,3,'multiple samples of the same species must not dominate the mix');
assert.ok(Math.abs(mixed.reduce((n,r)=>n+r.weight,0)-1)<1e-12);
const pla=controls.find(c=>c.id==='pla2'), svmp=controls.find(c=>c.id==='svmp');
const sample={components:[{toxin_id:pla.source_toxin_ids[0],value:null},{toxin_id:svmp.source_toxin_ids[0],value:20}]};
const result=compare({pla2:0,svmp:10},sample,controls);assert.equal(result.compared,1);assert.equal(result.selected,2);assert.equal(result.meanDifference,10,'missing must not become zero');
assert.equal(compare({pla2:0},sample,controls),null,'a zero input cannot match an unreported source value');
assert.equal(compare({pla2:null},sample,controls),null,'unspecified input produces no comparison');
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
const ids=['primary-controls','advanced-controls','source-profile','dataset-link','reset','dorsal','ventral','unknown-help','unknown-info','source-note','retained-section','retained-count','retained-list','total','progress-bar','balance-text','matches','empty-drawing','snake-drawing','snake-name','scientific-name','selection-note','anatomy-link','download-svg'];
const dom=Object.fromEntries(ids.map(id=>[id,new NodeMock()]));dom['progress-bar'].parentElement=new NodeMock();
const created=[];const fakeDocument={getElementById:id=>dom[id],createElement:tag=>{const x=new NodeMock(tag);created.push(x);return x;},createTextNode:text=>({textContent:text})};
const styleContext={window:{}};vm.runInNewContext(fs.readFileSync(__dirname+'/visual-style-model.js','utf8'),styleContext);
let lastRenderOptions=null,lastRenderedPreset=null;
const context={window:{SERPENT_VENOM_DATA:sandbox.window.SERPENT_VENOM_DATA,SERPENT_PRESETS:presetContext.window.SERPENT_PRESETS,SERPENT_STYLE_MODEL:styleContext.window.SERPENT_STYLE_MODEL},document:fakeDocument,SerpentMatching:require('./matching.js'),SerpentStyle:require('./style-inference.js'),SpeciesRenderer:{render:(p,o)=>{lastRenderOptions=o;lastRenderedPreset=p;return {svg:`<svg data-skin="${o.skinColor||''}" data-mark="${o.ringColor||''}"></svg>`};}},console,Number,Map,Set,URLSearchParams};
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
console.log('Blank start, diamondback-like shape, manual-input consistency and exclusions verified.');

const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const I=require('./connected-inference.js'),M=require('../SharedRendererTest/shared-morphology.js');
const DetailedConcept=require('./detailed-concept.js'),SpeciesRenderer=require('../PhysicalRendererTest/species-renderer.js'),SpeciesStarters=require('./species-starters.js');
const scope={window:{}};
for(const name of ['connected-model.js','venom-data.js','../PhysicalRendererTest/presets/species-presets.js'])vm.runInNewContext(fs.readFileSync(__dirname+'/'+name,'utf8'),scope);
const model=scope.window.SERPENT_CONNECTED_MODEL,data=scope.window.SERPENT_VENOM_DATA;
const report=JSON.parse(fs.readFileSync(__dirname+'/../ML/learned_morphology/connected_prototype.json','utf8'));
assert.ok(I.ready(model));
assert.equal(model.training_sources.length,model.training_vectors.length);
assert.equal(I.ready({...model,status:'not_trained'}),false);
assert.equal(I.ready({...model,training_vectors:[]}),false);
assert.equal(I.predict({},model),null);
assert.equal(I.predict({'3ftx':-1},model),null);
const values=Object.fromEntries(model.feature_ids.map((id,i)=>[id,report.parity_example.features[i]]));
const concept=I.predict(values,model);assert.ok(concept);
for(const key of I.TRAITS)assert.ok(Math.abs(concept.traits[key]-report.parity_example.expected_outputs[key])<1e-9,`Python / JS parity: ${key}`);
for(const color of ['skin','marking','belly'])for(const [j,ch] of ['r','g','b'].entries()){
  const actual=parseInt(concept.colors[color].slice(1+2*j,3+2*j),16);
  assert.ok(Math.abs(actual-Math.round(report.parity_example.expected_outputs[`${color}_${ch}`]*255))<=1,`color parity: ${color}_${ch}`);
}
const trial={'3ftx':25,pla2:15,svmp:40,svsp:0};
const a=I.predict(trial,model),b=I.predict({...trial,svsp:10},model),zero=I.predict({...trial,svsp:0},model),near=I.predict({...trial,svsp:1e-8},model);
assert.notDeepEqual(a.traits,b.traits,'venom changes must alter the learned illustration');
assert.deepEqual(a.traits,zero.traits,'returning a component to zero must restore the original output');
assert.deepEqual(a.colors,zero.colors);
for(const key of I.TRAITS)assert.ok(Math.abs(a.traits[key]-near.traits[key])<1e-6,`${key} should approach zero smoothly`);
for(const effect of b.contributions){const removed=I.predict({...trial,svsp:10,[effect.id]:0},model);if(removed)assert.ok(Math.abs(effect.largest.change-(b.traits[effect.largest.key]-removed.traits[effect.largest.key]))<1e-10,'explanations must match the actual model ablation');}
// Every shown species effect is an actual signed sum of kernel terms, not a fabricated similarity percentage.
const x=model.feature_ids.map((id,i)=>{const v=trial[id],alpha=Number.isFinite(v)&&v>0?Math.min(v/model.activation_width_percentage_points,1):0;return (model.median[i]+alpha*((alpha?v:model.median[i])-model.median[i]))/100;});
const missing=model.feature_ids.map(id=>{const v=trial[id];return (1-(Number.isFinite(v)&&v>0?Math.min(v/model.activation_width_percentage_points,1):0))*model.shape_missingness_scale;});
const vector=x.concat(missing);
for(let j=0;j<I.TRAITS.length;j++){
  let expected=0;for(let i=0;i<model.training_vectors.length;i++){const d=model.training_vectors[i].reduce((s,v,k)=>s+(v-vector[k])**2,0);expected+=Math.exp(-model.kernel_gamma*d)*model.dual_coefficients[i][j];}
  const shown=a.sourceContributions.reduce((sum,source)=>sum+source.rawEffects[j],0);
  assert.ok(Math.abs(expected-shown)<1e-9,`source attribution sums to the model term for ${I.TRAITS[j]}`);
}
assert.equal(a.sourceContributions.length,model.provenance.authored_preset_species);
for(const source of a.sourceContributions.slice(0,5))assert.ok(source.profiles.every(p=>data.profiles.some(row=>row.profile_id===p.profile_id&&row.species_name===source.species)));
for(const surface of ['dorsal','ventral']){const svg=M.render(a,{surface}).svg;assert.match(svg,/connected_hybrid_prototype/);assert.doesNotMatch(svg,/NaN|Infinity|undefined/);}
assert.match(M.render(a,{surface:'ventral'}).svg,/ventral-plates/);
assert.deepEqual(a.influence,[],'the model does not select or blend named species at inference');
// Exercise the actual main interface with the trained bundle.
class NodeMock{constructor(){this.children=[];this.events={};this.attrs={};this.value='';this.hidden=false;this.disabled=false;this.innerHTML='';this.textContent='';}append(...n){this.children.push(...n);}replaceChildren(...n){this.children=n;}setAttribute(k,v){this.attrs[k]=v;}removeAttribute(k){delete this.attrs[k];}addEventListener(k,f){this.events[k]=f;}fire(k){this.events[k]({target:this});}}
const ids=['controls','total','balance-note','drawing','empty','dorsal','ventral','clear','download','explanation-summary','visual-traits','influences','source-status','source-list','more-sources','more-sources-label','source-list-more','photo-list','starting-species','starting-note','starting-reference','reference-title','reference-drawing'];
const dom=Object.fromEntries(ids.map(id=>[id,new NodeMock()])),created=[];
const document={getElementById:id=>dom[id],createElement:()=>{const x=new NodeMock();created.push(x);return x;}};
const context={window:scope.window,document,ConnectedInference:I,DetailedConcept,SpeciesRenderer,SpeciesStarters,Number,Map,Set,Object};
vm.runInNewContext(fs.readFileSync(__dirname+'/connected-app.js','utf8'),context);
assert.equal(dom['photo-list'].children.length,model.provenance.photo_count);assert.match(dom['photo-list'].children[0].children[1].href,/^https:\/\/www\.inaturalist\.org\/photos\//);
assert.equal(dom.drawing.hidden,true);assert.equal(dom['starting-species'].children.length,150,'one blank entry plus 149 species');
assert.ok(dom['starting-species'].children.some(option=>option.textContent==='Western diamondback — Crotalus atrox'));
const input=id=>created.find(e=>e.id===`component-${id}`);
input('3ftx').value='25';input('3ftx').fire('input');assert.equal(dom.drawing.hidden,false);assert.match(dom['balance-note'].textContent,/Sparse/);
input('pla2').value='15';input('pla2').fire('input');input('svmp').value='40';input('svmp').fire('input');
const before=dom.drawing.innerHTML;input('svsp').value='10';input('svsp').fire('input');assert.notEqual(dom.drawing.innerHTML,before);
input('svsp').value='0';input('svsp').fire('input');
const withoutMetadata=s=>s.replace(/<metadata>.*?<\/metadata>/,'');
assert.equal(withoutMetadata(dom.drawing.innerHTML),withoutMetadata(before),'the drawing must return to its original appearance while recording the explicit zero');
assert.ok(dom.influences.children.length>0);assert.equal(dom['source-list'].children.length,5);assert.match(dom['source-list'].children[0].children[1].textContent,/raw shape contribution/i);assert.match(dom['source-list'].children[0].children[2].textContent,/Source row/);assert.match(dom['visual-traits'].textContent,/not probabilities/);
assert.equal(dom['more-sources'].hidden,false);assert.equal(dom['source-list-more'].children.length,0);dom['more-sources'].open=true;dom['more-sources'].fire('toggle');assert.equal(dom['source-list-more'].children.length,a.sourceContributions.length-5);
// A drag keeps the old influences marked as pending and release refreshes the
// full ranking against the current venom, including an expanded source list.
const drag=created.find(e=>e.attrs['aria-label']==='Venom serine proteases percentage slider');
const sourceSnapshot=()=>dom['source-list'].children.map(card=>card.children[0].textContent+' '+card.children[1].textContent).join('|');
const beforeDrag=sourceSnapshot(),drawingBeforeDrag=dom.drawing.innerHTML;
drag.value='10';drag.fire('input');assert.match(dom['source-status'].textContent,/Release/);assert.equal(sourceSnapshot(),beforeDrag);assert.notEqual(dom.drawing.innerHTML,drawingBeforeDrag);
drag.fire('change');assert.equal(dom['source-status'].textContent,'');assert.notEqual(sourceSnapshot(),beforeDrag);
const expectedSources=I.predict({...trial,svsp:10},model).sourceContributions;
for(let i=0;i<5;i++)assert.equal(dom['source-list'].children[i].children[0].textContent,expectedSources[i].common_name?`${expectedSources[i].common_name} — ${expectedSources[i].species}`:expectedSources[i].species);
assert.equal(dom['source-list-more'].children.length,expectedSources.length-5);
assert.match(dom['source-list'].children[0].children[1].textContent,new RegExp(expectedSources[0].score.toFixed(3).replace('.','\\.')));
drag.value='0';drag.fire('input');drag.fire('pointerup');assert.equal(dom['source-status'].textContent,'');assert.equal(sourceSnapshot(),beforeDrag);
dom.ventral.fire('click');assert.match(dom.drawing.innerHTML,/ventral study/);
dom.clear.fire('click');assert.equal(dom.drawing.hidden,true);assert.equal(dom.total.textContent,'0%');
// User edits must respect the total without redistributing other components.
input('3ftx').value='60';input('3ftx').fire('input');input('pla2').value='40';input('pla2').fire('input');
assert.equal(dom.total.textContent,'100%');const atLimit=dom.drawing.innerHTML;
input('svmp').value='1';input('svmp').fire('input');
assert.equal(input('svmp').value,'');assert.equal(input('3ftx').value,'60');assert.equal(input('pla2').value,'40');
assert.equal(dom.total.textContent,'100%');assert.equal(dom.drawing.innerHTML,atLimit);assert.match(dom['balance-note'].textContent,/cannot exceed 100%/);
const svmpSlider=created.find(e=>e.attrs['aria-label']==='Venom metalloproteinases percentage slider');assert.equal(Number(svmpSlider.max),0);
input('pla2').value='39.9';input('pla2').fire('input');assert.ok(Math.abs(Number(svmpSlider.max)-.1)<1e-8);
svmpSlider.value='0.1';svmpSlider.fire('input');assert.equal(input('svmp').value,'0.1');assert.equal(dom.total.textContent,'100%');
dom.clear.fire('click');
// Source totals above 100% are shown unchanged and cannot be generated until corrected.
dom['starting-species'].value='Metlapilcoatlus nummifer';dom['starting-species'].fire('change');
assert.equal(dom.total.textContent,'100.2%');assert.equal(dom.drawing.hidden,true);assert.match(dom['balance-note'].textContent,/source profile exceeds 100%/);
const overEntry=SpeciesStarters.build(data,scope.window.SERPENT_PRESETS.presets).find(x=>x.species==='Metlapilcoatlus nummifer');
const overValues=SpeciesStarters.valuesForProfile(data.controls,overEntry.profile);
for(const [id,value] of Object.entries(overValues))assert.equal(input(id).value,value===null?'':String(value),'loading must preserve the source');
const reducible=Object.entries(overValues).find(([,value])=>value!==null&&value>1);
input(reducible[0]).value=String(reducible[1]+.1);input(reducible[0]).fire('input');assert.equal(input(reducible[0]).value,String(reducible[1]));
input(reducible[0]).value=String(reducible[1]-.3);input(reducible[0]).fire('input');assert.equal(dom.drawing.hidden,false);assert.ok(Number.parseFloat(dom.total.textContent)<=100);
dom.clear.fire('click');
// A species only loads values and a separate reference; it never locks the generated geometry.
dom.dorsal.fire('click');dom['starting-species'].value='Crotalus atrox';dom['starting-species'].fire('change');
assert.equal(dom['starting-reference'].hidden,false);assert.match(dom['reference-title'].textContent,/Western diamondback/);
assert.match(dom['reference-drawing'].innerHTML,/Crotalus atrox/);assert.equal(input('svmp').value,'49.7');
const selectedAppearance=withoutMetadata(dom.drawing.innerHTML),selectedValues=SpeciesStarters.valuesForProfile(data.controls,data.profiles.find(p=>p.species_name==='Crotalus atrox'));
dom.clear.fire('click');assert.equal(dom['starting-reference'].hidden,true);
for(const [id,value] of Object.entries(selectedValues)){if(value!==null){input(id).value=String(value);input(id).fire('input');}}
assert.equal(withoutMetadata(dom.drawing.innerHTML),selectedAppearance,'the same venom produces the same concept from a blank start');
dom['starting-species'].value='Naja kaouthia';dom['starting-species'].fire('change');
for(const id of Object.keys(selectedValues)){input(id).value='';input(id).fire('input');}
for(const [id,value] of Object.entries(selectedValues)){input(id).value=value===null?'':String(value);input(id).fire('input');}
assert.equal(withoutMetadata(dom.drawing.innerHTML),selectedAppearance,'changing a starting species does not pin the generated concept');
assert.match(dom['starting-note'].textContent,/Edited starting profile/);
const html=fs.readFileSync(__dirname+'/index.html','utf8');
assert.match(html,/<select[^>]*id="starting-species"/i);assert.doesNotMatch(html,/render-mode/i);assert.match(html,/not measured from photos/);
console.log('Trained Python/JS parity, explanations, zero reversal, surfaces and main-interface controls verified.');

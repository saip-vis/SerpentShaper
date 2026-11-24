const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const I=require('./learned-inference.js'),M=require('../SharedRendererTest/shared-morphology.js');
const targets=I.TARGETS,feature_ids=['3ftx','pla2','svmp','svsp'];
const models=Object.fromEntries(targets.map((name,i)=>[name,{median:[30,20,10,5],coefficients:[.1,.2,.3,.4,.05,.06,.07,.08],intercept:.2+i*.005}]));
const candidate={status:'experimental_candidate_not_for_product',feature_ids,models,minimum_active_inputs:3,activation_width_percentage_points:1,provenance:{image_count:4,source_species_count:4}};
const values={'3ftx':20,pla2:30,svmp:40};
assert.equal(I.predict(values,candidate),null,'an unapproved candidate must never produce a product prediction');
const model={...candidate,status:'ready_for_preview'};
assert.equal(I.isReady(model),true);
assert.equal(I.isReady({...model,models:{}}),false,'an incomplete model is not ready');
assert.equal(I.predict(values,{...model,provenance:{image_count:0,source_species_count:4}}),null,'an image-trained model needs image provenance');
assert.equal(I.predict({'3ftx':20,pla2:30,svmp:0},model),null,'zero is inactive and does not satisfy the minimum');
const a=I.predict(values,model),zero=I.predict({...values,svsp:0},model),small=I.predict({...values,svsp:1e-8},model);
assert.ok(a);assert.deepEqual(a.traits,zero.traits);assert.deepEqual(a.colors,zero.colors);
for(const k of Object.keys(a.traits))assert.ok(Math.abs(a.traits[k]-small.traits[k])<1e-7,'activating near zero should not jump');
assert.equal(a.venomContext.kind,'direct_image_trait_model');assert.deepEqual(a.influence,[],'no species or reference weights are used');
for(const surface of ['dorsal','ventral']){const svg=M.render(a,{surface}).svg;assert.match(svg,/direct_image_trait_model/);assert.doesNotMatch(svg,/NaN|Infinity|undefined/);}
assert.match(M.render(a,{surface:'ventral'}).svg,/ventral-plates/);
// The user-only preview stays empty when no trained model is present.
class NodeMock{constructor(){this.children=[];this.events={};this.attrs={};this.value='';this.hidden=false;this.innerHTML='';this.textContent='';}append(...n){this.children.push(...n);}setAttribute(k,v){this.attrs[k]=v;}removeAttribute(k){delete this.attrs[k];}addEventListener(k,f){this.events[k]=f;}fire(k){this.events[k]({target:this});}}
const ids=['controls','total','balance-note','drawing','empty','dorsal','ventral','clear'];
const dom=Object.fromEntries(ids.map(id=>[id,new NodeMock()])),created=[];
const document={getElementById:id=>dom[id],createElement:()=>{const x=new NodeMock();created.push(x);return x;}};
const controls=feature_ids.map(id=>({id,label:id,short_label:id}));
const context={window:{SERPENT_VENOM_DATA:{controls},SERPENT_IMAGE_TRAIT_MODEL:{status:'not_trained'}},document,LearnedInference:I,SharedMorphology:M,Number,Map,Set,Object};
vm.runInNewContext(fs.readFileSync(__dirname+'/learned-preview.js','utf8'),context);
assert.match(dom.empty.textContent,/not ready/);assert.equal(dom.drawing.hidden,true);
const input=id=>created.find(e=>e.id===`learned-${id}`);
for(const id of ['3ftx','pla2','svmp']){input(id).value='10';input(id).fire('input');}
assert.equal(dom.drawing.hidden,true,'the interface must not pretend an untrained model generated a snake');
dom.ventral.fire('click');assert.equal(dom.ventral.attrs['aria-pressed'],'true');
dom.clear.fire('click');assert.equal(dom.total.textContent,'0%');
const html=fs.readFileSync(__dirname+'/learned-preview.html','utf8');
assert.doesNotMatch(html,/<select\b|source-profile|render-mode|reference-intro/i);
console.log('Direct inference gating, zero continuity, surfaces and restricted user controls verified.');

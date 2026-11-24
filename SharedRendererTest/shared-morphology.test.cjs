const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const M=require('./shared-morphology.js');
assert.equal(M.blend({diamondback:0,cobra:0,mamba:0}),null);
const d=M.blend({diamondback:100}),c=M.blend({cobra:100}),m=M.blend({mamba:100});
assert.deepEqual(d.traits,M.REFERENCES.diamondback.traits);
assert.deepEqual(c.traits,M.REFERENCES.cobra.traits);
assert.deepEqual(m.traits,M.REFERENCES.mamba.traits);
const equal=M.blend({diamondback:50,cobra:50});
for(const k of M.TRAITS)assert.ok(Math.abs(equal.traits[k]-(d.traits[k]+c.traits[k])/2)<1e-10,`${k} should blend`);
assert.deepEqual(M.blend({diamondback:5,cobra:5}),equal,'reference weights should be relative');
assert.ok(d.traits.headWidth>m.traits.headWidth);
assert.ok(c.traits.hood>d.traits.hood);
assert.ok(d.traits.rattle>c.traits.rattle);
let previous=null;
for(let i=0;i<=100;i++){
  const data=M.blend({diamondback:100-i,cobra:i});
  const out=M.render(data);assert.match(out.geometry.path,/Z$/);assert.doesNotMatch(out.svg,/NaN|Infinity|undefined/);
  assert.ok(out.geometry.points.every((p,index)=>Number.isFinite(p.r)&&p.r>=0&&(index===0||p.x>out.geometry.points[index-1].x)));
  if(previous)for(const k of M.TRAITS)assert.ok(Math.abs(data.traits[k]-previous.traits[k])<=.011,`${k} jumps at ${i}`);
  previous=data;
}
const noHood=M.geometry({...equal.traits,hood:0}),withHood=M.geometry({...equal.traits,hood:1});
assert.ok(withHood.radius(withHood.start+(650-withHood.start)*.14)>noHood.radius(noHood.start+(650-noHood.start)*.14));
assert.match(M.render(d).svg,/opacity="1\.00"/);
assert.match(M.render(c).svg,/clipPath/);
const dorsal=M.render(c,{surface:'dorsal'}),ventral=M.render(c,{surface:'ventral'});
assert.equal(dorsal.geometry.path,ventral.geometry.path,'the two views use the same illustrative silhouette');
assert.notEqual(dorsal.svg,ventral.svg);assert.match(ventral.svg,/ventral-plates/);
assert.equal(M.render(null),null);
// Exercise reference controls, manual overrides, reset, and zero-state without a browser.
class NodeMock{
  constructor(){this.children=[];this.events={};this.attrs={};this.value='';this.hidden=false;this.disabled=false;this.innerHTML='';this.textContent='';}
  append(...nodes){this.children.push(...nodes);}setAttribute(k,v){this.attrs[k]=v;}
  addEventListener(k,fn){this.events[k]=fn;}fire(k){this.events[k]({target:this});}
}
const ids=['reference-controls','trait-controls','mix-status','drawing','empty','download','source-note','reset-traits'];
const dom=Object.fromEntries(ids.map(id=>[id,new NodeMock()])),created=[];
const document={getElementById:id=>dom[id],createElement:()=>{const x=new NodeMock();created.push(x);return x;}};
const context={window:{SharedMorphology:M},document,URL,Blob,setTimeout,Number,Math,Object};
vm.runInNewContext(fs.readFileSync(__dirname+'/lab.js','utf8'),context);
const inputs=created.filter(x=>x.type==='range');assert.equal(inputs.length,3+M.TRAITS.length);
const byLabel=label=>inputs.find(i=>i.attrs['aria-label']===label);
const hood=byLabel('Hood expansion'),cobra=byLabel('Monocled cobra'),diamond=byLabel('Western diamondback');
assert.equal(Number(diamond.value),50);assert.equal(Number(cobra.value),50);assert.equal(Number(byLabel('Black mamba').value),0);
assert.equal(Number(hood.value),50);const initial=dom.drawing.innerHTML;
hood.value='75';hood.fire('input');assert.notEqual(dom.drawing.innerHTML,initial);
dom['reset-traits'].fire('click');assert.equal(Number(hood.value),50);assert.equal(dom.drawing.innerHTML,initial);
cobra.value='0';cobra.fire('input');assert.equal(Number(hood.value),0);assert.match(dom['mix-status'].textContent,/Western diamondback: 100%/);
diamond.value='0';diamond.fire('input');assert.equal(dom.empty.hidden,false);assert.equal(dom.download.disabled,true);
console.log('Shared controls, gradual shape interpolation, SVG, overrides and zero-state verified.');

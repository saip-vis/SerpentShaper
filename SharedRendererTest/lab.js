(() => {
'use strict';
const M=window.SharedMorphology,$=id=>document.getElementById(id);
const weights={diamondback:50,cobra:50,mamba:0};
const traitNames={headWidth:'Head width',headLength:'Head length',bodyWidth:'Body width',hood:'Hood expansion',diamond:'Diamond markings',monocle:'Hood marking',rattle:'Rattle',tailTaper:'Tail taper'};
const traitDescriptions={headWidth:'Width across the back of the head',headLength:'Length from snout to neck',bodyWidth:'Thickness through the middle of the body',hood:'Width behind the head',diamond:'Visibility of the dorsal diamond pattern',monocle:'Visibility of the marking when a hood is present',rattle:'Size and visibility of the tail rattle',tailTaper:'How early the tail begins to narrow'};
const refControls=new Map(),traitControls=new Map();
let data=null,svg='';
function addSlider(parent,label,description,onChange){
  const box=document.createElement('div');box.className='lab-slider';
  const head=document.createElement('div');head.className='lab-slider-head';
  const name=document.createElement('label');name.textContent=label;
  const value=document.createElement('output');head.append(name,value);
  const input=document.createElement('input');input.type='range';input.min='0';input.max='100';input.step='1';input.setAttribute('aria-label',label);
  name.htmlFor=label.toLowerCase().replace(/[^a-z0-9]+/g,'-');input.id=name.htmlFor;
  input.addEventListener('input',()=>onChange(Number(input.value)));
  const small=document.createElement('small');small.textContent=description;
  box.append(head,input,small);parent.append(box);return {input,value};
}
function render(){
  const result=M.render(data);svg=result?.svg||'';
  $('drawing').innerHTML=svg;$('drawing').hidden=!result;$('empty').hidden=!!result;$('download').disabled=!result;
  $('source-note').textContent=result?(data.manualTraits.length?'Manual refinements · top-down study':'Reference-inspired shape · top-down study'):'No visual influences selected';
}
function updateWeights(){
  for(const [id,c] of refControls){c.input.value=String(weights[id]);c.value.textContent=`${weights[id]} / 100`;}
  const blended=M.blend(weights);
  if(!blended){data=null;$('mix-status').textContent='Select at least one reference.';for(const c of traitControls.values())c.input.disabled=true;render();return;}
  data=blended;
  $('mix-status').textContent=blended.influence.map(x=>`${M.REFERENCES[x.id].name}: ${(100*x.weight).toFixed(0)}%`).join(' · ');
  for(const [id,c] of traitControls){c.input.disabled=false;c.input.value=Math.round(data.traits[id]*100);c.value.textContent=`${Math.round(data.traits[id]*100)} / 100`;}
  render();
}
for(const [id,r] of Object.entries(M.REFERENCES))refControls.set(id,addSlider($('reference-controls'),r.name,r.species,v=>{weights[id]=v;updateWeights();}));
for(const id of M.TRAITS)traitControls.set(id,addSlider($('trait-controls'),traitNames[id],traitDescriptions[id],v=>{if(!data)return;data.traits[id]=v/100;if(!data.manualTraits.includes(id))data.manualTraits.push(id);traitControls.get(id).value.textContent=`${v} / 100`;render();}));
$('reset-traits').addEventListener('click',updateWeights);
$('download').addEventListener('click',()=>{if(!svg)return;const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download='serpentshaper-shared-shape.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),0);});
updateWeights();
})();

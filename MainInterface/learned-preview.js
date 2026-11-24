(() => {
'use strict';
const controls=window.SERPENT_VENOM_DATA.controls,values=Object.fromEntries(controls.map(c=>[c.id,null]));
const $=id=>document.getElementById(id),inputs=new Map(),invalid=new Set();
let surface='dorsal';
function update(){
  const active=Object.values(values).filter(Number.isFinite),total=active.reduce((a,b)=>a+b,0);
  $('total').textContent=`${Number(total.toFixed(2))}%`;
  $('balance-note').textContent=invalid.size?'Enter values from 0 to 100.':total>100?'Entered values exceed 100%; they are not normalized.':'Blank values are unreported.';
  const model=window.SERPENT_IMAGE_TRAIT_MODEL,ready=LearnedInference.isReady(model);
  const concept=invalid.size?null:LearnedInference.predict(values,model);
  const drawing=concept?SharedMorphology.render(concept,{surface}):null;
  $('drawing').innerHTML=drawing?.svg||'';$('drawing').hidden=!drawing;$('empty').hidden=!!drawing;
  $('empty').textContent=!ready?'An image-trained model is not ready yet.':invalid.size?'Correct the highlighted inputs.':'Enter at least three active components to generate a concept.';
  $('dorsal').setAttribute('aria-pressed',String(surface==='dorsal'));$('ventral').setAttribute('aria-pressed',String(surface==='ventral'));
}
for(const c of controls){
  const box=document.createElement('div');box.className='toxin';const head=document.createElement('div');head.className='toxin-head';
  const label=document.createElement('label');label.className='toxin-label';label.textContent=c.short_label;label.htmlFor=`learned-${c.id}`;
  const small=document.createElement('small');small.textContent=c.label;label.append(small);
  const wrap=document.createElement('div');wrap.className='value-wrap';const input=document.createElement('input');input.type='number';input.id=label.htmlFor;input.min='0';input.max='100';input.step='.1';input.placeholder='—';input.setAttribute('aria-label',`${c.label} percentage`);
  const percent=document.createElement('span');percent.textContent='%';wrap.append(input,percent);head.append(label,wrap);
  const slider=document.createElement('input');slider.type='range';slider.min='0';slider.max='100';slider.step='.1';slider.value='0';slider.setAttribute('aria-label',`${c.label} percentage slider`);
  const row=document.createElement('div');row.className='slider-row';row.append(slider);box.append(head,row);$('controls').append(box);inputs.set(c.id,{input,slider});
  function apply(raw,fromSlider){const value=raw===''?null:Number(raw);if(value!==null&&(!Number.isFinite(value)||value<0||value>100)){invalid.add(c.id);input.setAttribute('aria-invalid','true');}else{invalid.delete(c.id);input.removeAttribute('aria-invalid');values[c.id]=value;slider.value=value??0;if(fromSlider)input.value=String(value);}update();}
  input.addEventListener('input',()=>apply(input.value,false));slider.addEventListener('input',()=>apply(slider.value,true));
}
for(const s of ['dorsal','ventral'])$(s).addEventListener('click',()=>{surface=s;update();});
$('clear').addEventListener('click',()=>{for(const c of controls){values[c.id]=null;const {input,slider}=inputs.get(c.id);input.value='';input.removeAttribute('aria-invalid');slider.value='0';}invalid.clear();update();});
update();
})();

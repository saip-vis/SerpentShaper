(() => {
'use strict';
const data=window.SERPENT_VENOM_DATA, controls=data.controls, profiles=data.profiles;
const presets=new Map(window.SERPENT_PRESETS.presets.map(p=>[p.preset_id,p]));
const photoCues=new Map((window.SERPENT_PHOTO_CUES?.cues||[]).map(c=>[c.species,c]));
const profilesById=new Map(profiles.map(p=>[p.profile_id,p]));
const $=id=>document.getElementById(id);
const inputs=new Map(), values=Object.fromEntries(controls.map(c=>[c.id,null]));
const editableIds=new Set(controls.flatMap(c=>c.source_toxin_ids));
let source=null, surface='dorsal', currentMatches=[], invalid=new Set(), drawnKey='', currentSvg='';
const fmt=n=>Number(n.toFixed(2)).toString();
const uncertainMambaProfile='vd2023_e2d1aa974518_r189';
function labelProfile(p){const name=presets.get(p.preset_id)?.common_name;return `${name?name+' · ':''}${p.species_name}${p.location?' · '+p.location:''} · row ${p.source_row}`;}
function createControl(c){
  const box=document.createElement('div');box.className='toxin';
  const head=document.createElement('div');head.className='toxin-head';
  const label=document.createElement('label');label.className='toxin-label';label.htmlFor=`number-${c.id}`;label.textContent=c.short_label;label.title=`${c.definition} ${c.boundaries}`;
  const small=document.createElement('small');small.textContent=c.label;label.append(small);
  const wrap=document.createElement('div');wrap.className='value-wrap';
  const number=document.createElement('input');number.type='number';number.id=`number-${c.id}`;number.min='0';number.max='100';number.step='0.1';number.placeholder='—';number.setAttribute('aria-label',`${c.label} percentage`);
  const percent=document.createElement('span');percent.textContent='%';wrap.append(number,percent);head.append(label,wrap);
  const line=document.createElement('div');line.className='slider-row';const range=document.createElement('input');range.type='range';range.min='0';range.max='100';range.step='0.1';range.value='0';range.className='unknown';range.setAttribute('aria-label',`${c.label} percentage slider`);range.setAttribute('aria-valuetext','Unreported');
  const clear=document.createElement('button');clear.type='button';clear.className='clear-value';clear.textContent='Clear';clear.setAttribute('aria-label',`Clear ${c.label}`);
  line.append(range,clear);box.append(head,line);inputs.set(c.id,{number,range});
  function apply(raw,fromRange=false){
    const n=raw===''?null:Number(raw);const bad=raw!=='' && (!Number.isFinite(n)||n<0||n>100);
    if(bad){invalid.add(c.id);number.setAttribute('aria-invalid','true');}else{invalid.delete(c.id);number.removeAttribute('aria-invalid');values[c.id]=n;range.value=n??0;range.classList.toggle('unknown',n===null);range.setAttribute('aria-valuetext',n===null?'Unreported':n===0?'0 percent, inactive for generation':`${fmt(n)} percent`);if(fromRange)number.value=fmt(n);}
    update();
  }
  number.addEventListener('input',()=>apply(number.value));range.addEventListener('input',()=>apply(range.value,true));clear.addEventListener('click',()=>{number.value='';apply('');});
  return box;
}
function updateInputs(){for(const c of controls){const {number,range}=inputs.get(c.id),v=values[c.id];number.value=v===null?'':fmt(v);number.removeAttribute('aria-invalid');range.value=v??0;range.classList.toggle('unknown',v===null);range.setAttribute('aria-valuetext',v===null?'Unreported':v===0?'0 percent, inactive for generation':`${fmt(v)} percent`);}invalid.clear();}
function sourceOnly(){return source?source.components.filter(c=>!editableIds.has(c.toxin_id)):[];}
function loadProfile(id){
  source=profilesById.get(id)||null;const lookup=new Map((source?.components||[]).map(c=>[c.toxin_id,c.value]));
  for(const c of controls){const v=lookup.get(c.source_toxin_ids[0]);values[c.id]=Number.isFinite(v)?v:null;}
  updateInputs();update();
}
function updateSource(){
  const retained=sourceOnly(), reported=retained.filter(c=>Number.isFinite(c.value));
  $('source-note').textContent=source?`Proteomics · ${source.location||'location not reported'} · source row ${source.source_row}. Unreported values stay blank.`:'No source profile selected. Blank values are unspecified.';
  if(source?.profile_id===uncertainMambaProfile)$('source-note').textContent+=' The source NP value is excluded because its attribution is unverified; the original is preserved in the database.';
  $('retained-section').hidden=!source||!reported.length;$('retained-count').textContent=`${reported.length} reported`;
  $('retained-list').replaceChildren();for(const item of reported){const row=document.createElement('div');row.className='retained-entry';const a=document.createElement('span');a.textContent=item.label;const b=document.createElement('strong');b.textContent=`${fmt(item.value)}%`;row.append(a,b);$('retained-list').append(row);}
}
function updateTotal(){
  const totals=SerpentMatching.totals(values,sourceOnly());$('total').textContent=`${fmt(totals.total)}%`;$('progress-bar').style.width=`${Math.min(100,totals.total)}%`;$('progress-bar').parentElement.classList.toggle('over',totals.over>.01);
  $('balance-text').textContent=invalid.size?'Enter a value from 0 to 100 in each highlighted field.':totals.over>.01?`${fmt(totals.over)} percentage points above 100%. Source totals may differ due to rounding; custom entries are not normalized.`:totals.unallocated>.01?`${fmt(totals.unallocated)}% unallocated. This is a balance, not a measured category.`:'Reported values total approximately 100%. Unreported categories remain unknown.';
}
function updateMatches(){
  currentMatches=invalid.size?[]:SerpentMatching.influences(values,profiles,controls);
  const hasConcept=!invalid.size&&!!SerpentStyle.predictActive(values,window.SERPENT_STYLE_MODEL);
  const container=$('matches');container.replaceChildren();
  if(!currentMatches.length){const p=document.createElement('p');p.className='empty-matches';p.textContent=invalid.size?'Correct the highlighted value to compare references.':'Enter at least three values above 0% that are also reported together by a reference profile.';container.append(p);return;}
  const best=currentMatches[0],fit=document.createElement('p');fit.className='field-note';
  fit.textContent=`Best-weighted comparison: ${best.compared} of ${best.selected} active categories, averaging ${fmt(best.meanDifference)} percentage points apart. Weights are relative even when every match is weak.`;
  container.append(fit);
  currentMatches.slice(0,5).forEach((result,i)=>{
    const p=result.profile,preset=presets.get(p.preset_id);const card=document.createElement('div');card.className='match-card';
    const top=document.createElement('div');top.className='match-top';const name=document.createElement('span');name.className='match-name';name.textContent=preset?.common_name||p.species_name;const rank=document.createElement('span');rank.className='match-rank';rank.textContent=hasConcept?`${(result.weight*100).toFixed(1)}%`:'—';top.append(name,rank);
    const sci=document.createElement('span');sci.className='match-scientific';sci.textContent=p.species_name;
    const stats=document.createElement('div');stats.className='match-stats';const coverage=document.createElement('strong');coverage.textContent=`${result.compared} of ${result.selected} categories compared`;stats.append(coverage,document.createElement('br'),document.createTextNode(`Mean difference ${fmt(result.meanDifference)} percentage points · ${p.location||'location unreported'} · row ${p.source_row}`));
    const details=result.differences.slice().sort((a,b)=>b.difference-a.difference).slice(0,2).map(d=>`${d.label}: ${fmt(d.input)}% entered, ${fmt(d.reference)}% reference`).join(' · ');
    stats.append(document.createElement('br'),document.createTextNode(`Largest shared differences: ${details}.`));
    if(p.profile_id===uncertainMambaProfile)stats.append(document.createElement('br'),document.createTextNode('The unverified source NP value is excluded from this comparison.'));
    const cue=photoCues.get(p.species_name);if(cue){const evidence=document.createElement('div');evidence.className='match-stats';evidence.append(document.createTextNode('Photo color cue available for compatible diamond markings: '));cue.sources.forEach((s,index)=>{if(index)evidence.append(document.createTextNode(' · '));const a=document.createElement('a');a.href=s.photo_page;a.target='_blank';a.rel='noopener noreferrer';a.textContent=`photo ${index+1}`;a.title=s.attribution||'Photo source';evidence.append(a);});stats.append(document.createElement('br'),evidence);}
    card.append(top,sci,stats);container.append(card);
  });
  if(currentMatches.length>5){const rest=currentMatches.slice(5).reduce((n,r)=>n+r.weight,0),p=document.createElement('p');p.className='empty-matches';p.textContent=`${currentMatches.length-5} additional references contribute ${(rest*100).toFixed(1)}% combined. Percentages are blend weights, not certainty.`;container.append(p);}
}
function draw(){
  const references=currentMatches.map(match=>({preset:presets.get(match.profile.preset_id),weight:match.weight,photoCue:surface==='dorsal'?photoCues.get(match.profile.species_name):null}));
  const concept=invalid.size?null:SerpentStyle.concept(values,window.SERPENT_STYLE_MODEL,references);
  $('empty-drawing').hidden=!!concept;$('snake-drawing').hidden=!concept;
  $('snake-name').textContent='Your snake concept';
  if(!concept){$('scientific-name').textContent='';$('selection-note').textContent='Enter at least 3 active, comparable components';drawnKey='';currentSvg='';$('download-svg').disabled=true;return;}
  const formLabels={cobra:'Hooded form',viper:'Broad-headed form',terrestrial:'Slender form',marine:'Paddle-tailed form'};
  $('scientific-name').textContent=formLabels[concept.preset.artistic_parameters.body_plan]||'Blended form';
  $('selection-note').textContent=concept.photoCue?'Reference blend · photo color cue applied':'Reference-blended anatomy and experimental style';
  const key=JSON.stringify([surface,values]);if(key!==drawnKey){
    const conceptMetadata={kind:'illustrative_not_biological_prediction',bodyPlan:concept.preset.artistic_parameters.body_plan,
      venomInputs:{...values},referenceStyleMix:currentMatches.map(r=>({species:r.profile.species_name,profileId:r.profile.profile_id,weight:r.weight})),photoCue:concept.photoCue};
    currentSvg=SpeciesRenderer.render(concept.preset,{surface,framing:'full',...concept.options,conceptMetadata}).svg;
    $('snake-drawing').innerHTML=currentSvg;drawnKey=key;
  }
  $('download-svg').disabled=false;
  $('dorsal').setAttribute('aria-pressed',String(surface==='dorsal'));$('ventral').setAttribute('aria-pressed',String(surface==='ventral'));
}
function update(){updateSource();updateTotal();updateMatches();draw();}
for(const c of controls)$(c.tier==='primary'?'primary-controls':'advanced-controls').append(createControl(c));
const blank=document.createElement('option');blank.value='';blank.textContent='Start with a blank composition';$('source-profile').append(blank);
for(const p of profiles){const option=document.createElement('option');option.value=p.profile_id;option.textContent=labelProfile(p);$('source-profile').append(option);}
$('dataset-link').href=data.source_url;
$('download-svg').addEventListener('click',()=>{if(!currentSvg)return;const url=URL.createObjectURL(new Blob([currentSvg],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download='serpentshaper-concept.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),0);});
$('source-profile').addEventListener('change',e=>loadProfile(e.target.value));
$('reset').addEventListener('click',()=>{$('source-profile').value='';loadProfile('');});
for(const name of ['dorsal','ventral'])$(name).addEventListener('click',()=>{surface=name;draw();});
$('unknown-help').addEventListener('click',()=>{const hidden=$('unknown-info').hidden;$('unknown-info').hidden=!hidden;$('unknown-help').setAttribute('aria-expanded',String(hidden));});
$('source-profile').value='';loadProfile('');
})();

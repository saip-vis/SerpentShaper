(() => {
'use strict';
const controls=window.SERPENT_VENOM_DATA.controls,values=Object.fromEntries(controls.map(c=>[c.id,null]));
const $=id=>document.getElementById(id),inputs=new Map(),invalid=new Set();
const presets=window.SERPENT_PRESETS.presets,starters=SpeciesStarters.build(window.SERPENT_VENOM_DATA,presets);
const startersBySpecies=new Map(starters.map(s=>[s.species,s]));
const presetById=new Map(presets.map(p=>[p.preset_id,p]));
const expandedContext=new Set();
let surface='dorsal',svg=null,currentSources=[],starting=null,startingValues=null,referenceKey='',limitNotice='',sourcesPending=false;
const EPSILON=1e-8,MIN_PROFILE_PERCENT=50;
const enteredTotal=()=>Object.values(values).reduce((sum,v)=>sum+(Number.isFinite(v)?v:0),0);
for(const photo of window.SERPENT_CONNECTED_MODEL?.photo_sources||[]){
  const item=document.createElement('li'),label=document.createElement('span');label.textContent=`${photo.species} — `;item.append(label);
  if(typeof photo.photo_page==='string'&&/^https:\/\/www\.inaturalist\.org\/photos\/\d+$/.test(photo.photo_page)){const link=document.createElement('a');link.href=photo.photo_page;link.target='_blank';link.rel='noopener noreferrer';link.textContent=photo.image_id;item.append(link);}else{const source=document.createElement('span');source.textContent=photo.image_id;item.append(source);}
  const attribution=document.createElement('span');attribution.textContent=` · ${photo.attribution}`;item.append(attribution);$('photo-list').append(item);
}
function addSourceCards(list,sources){
  for(const source of sources){
    const card=document.createElement('article');card.className='source-card';
    const record=source.profile,preset=presetById.get(record.preset_id);
    const heading=document.createElement('h4');heading.textContent=preset?.common_name?`${preset.common_name} — ${record.species_name}`:record.species_name;card.append(heading);
    const effect=document.createElement('p');effect.className='source-effect';
    effect.textContent=`Adjusted difference: ${source.adjustedDistance.toFixed(1)} percentage points (lower is closer). Compared ${source.shared.length} of ${source.entered} entered categories; average reported-value difference ${source.meanDifference.toFixed(1)} points.${source.missing.length?` Unreported or uncertain: ${source.missing.join(', ')}.`:''}`;card.append(effect);
    const row=document.createElement('p');row.className='source-profile';
    const reported=SpeciesStarters.valuesForProfile(controls,record);
    const entries=controls.filter(c=>Number.isFinite(reported[c.id])).map(c=>`${c.short_label} ${reported[c.id]}%`);
    const total=Object.values(reported).reduce((sum,v)=>sum+(Number.isFinite(v)?v:0),0);
    row.textContent=`Closest source row ${record.source_row} (listed categories total ${Number(total.toFixed(2))}%): ${entries.join(' · ')}`;card.append(row);
    const observation=window.SERPENT_REVIEWED_PHOTO_EVIDENCE?.evidence_by_species?.[record.species_name];
    if(observation){
      const details=document.createElement('details');details.className='profile-more';
      const summary=document.createElement('summary');summary.textContent='View a reviewed photo observation';details.append(summary);
      const note=document.createElement('p');note.className='source-profile';
      note.textContent=`${observation.evidence} This photo is a reference for this source label; it does not calculate the venom comparison. Species identification is based on source records, not independent expert verification.`;details.append(note);
      if(typeof observation.photo_page==='string'&&/^https:\/\/www\.inaturalist\.org\/photos\/\d+$/.test(observation.photo_page)){
        const link=document.createElement('a');link.href=observation.photo_page;link.target='_blank';link.rel='noopener noreferrer';link.textContent='View the source photo';details.append(link);
      }
      const credit=document.createElement('p');credit.className='source-profile';credit.textContent=observation.attribution||'';details.append(credit);card.append(details);
    }
    list.append(card);
  }
}
function renderMoreSources(){const list=$('source-list-more');list.replaceChildren();if($('more-sources').open)addSourceCards(list,currentSources.slice(5));}
function renderSources(concept){
  const list=$('source-list');list.replaceChildren();currentSources=concept?ProfileComparison.rank(values,window.SERPENT_VENOM_DATA.profiles,controls):[];
  $('more-sources').hidden=currentSources.length<=5;
  $('more-sources-label').textContent=`Show ${Math.max(0,currentSources.length-5)} more comparable species`;
  renderMoreSources();
  if(!concept||!currentSources.length){const text=document.createElement('p');text.className='source-empty';text.textContent=concept?'No source profiles report a comparable entered category.':'Enter a venom profile to compare with real sources.';list.append(text);return;}
  addSourceCards(list,currentSources.slice(0,5));
}
function contextText(tag,className,text){const node=document.createElement(tag);node.className=className;node.textContent=text;return node;}
function contextDetails(key,label){
  const details=document.createElement('details');details.className='context-details';details.open=expandedContext.has(key);
  details.addEventListener('toggle',()=>{if(details.open)expandedContext.add(key);else expandedContext.delete(key);});
  details.append(contextText('summary','',label));return details;
}
function contextFact(id,primary,secondary,notes){
  const node=$(id);node.replaceChildren();
  if(!primary){node.append(contextText('p','context-unavailable','No sourced reference available.'));return;}
  node.append(contextText('p','context-value',primary));
  if(secondary)node.append(contextText('p','context-secondary',secondary));
  if(notes.length){const details=contextDetails(id,'Sources & details');for(const note of notes)details.append(contextText('p','context-detail-text',note));node.append(details);}
}
function renderContext(concept,pending){
  if(pending&&concept){$('context-status').textContent='The information below is from the previous comparison. Release the slider to update it.';return;}
  const match=concept?currentSources[0]:null;
  const adequate=match&&match.shared.length>=3&&match.shared.length/match.entered>=.6&&match.adjustedDistance<=20;
  const item=adequate?window.SERPENT_SPECIES_CONTEXT?.species?.[match.profile.species_name]:null;
  if(!adequate||!item){
    $('context-status').textContent=concept?'Not enough comparable source evidence to suggest a species reference.':'Enter at least three comparable venom values to see source context.';
    for(const id of ['context-habitat','context-prey','context-size'])contextFact(id,null,null,[]);
    return;
  }
  $('context-status').textContent=`Closest reference: ${match.profile.species_name} · ${match.shared.length} of ${match.entered} entered categories compared.`;
  const citation=(label,field)=>field?`${label}: ${field.citation||'Source not specified'}, via ReptTraits.`:null;
  const habitats=[citation('Habitat',item.habitat),citation('Microhabitat',item.microhabitat)].filter(Boolean);
  contextFact('context-habitat',item.habitat?.value||item.microhabitat?.value||null,item.habitat&&item.microhabitat?`Microhabitat: ${item.microhabitat.value}`:null,habitats);
  const preyField=item.prey||item.diet,observation=item.prey_observation;
  const preyNotes=[citation(item.prey?'Diet':'Diet category',preyField),observation?`Recorded prey reference: ${observation.reference} (via Squamatabase).`:null].filter(Boolean);
  const preyPrimary=preyField?.value||(observation?`Observed: ${observation.prey}`:null);
  const preySecondary=preyField&&observation?`One recorded prey: ${observation.prey}${observation.country?` · ${observation.country}`:''}`:null;
  contextFact('context-prey',preyPrimary,preySecondary,preyNotes);
  const length=item.maximum_total_length_mm;
  contextFact('context-size',length?`${Number((length.value/1000).toFixed(3))} m`:null,length?'Reported maximum total length; not typical adult size.':null,[citation('Length',length)].filter(Boolean));
}
function exactReferenceSpecies(){
  const sameValues=profileValues=>controls.every(c=>values[c.id]===profileValues[c.id]);
  if(starting&&sameValues(startingValues))return starting.species;
  // An entered zero is not the same as a source blank. Require at least three
  // reported categories and a unique species before recognizing a typed profile.
  if(controls.filter(c=>Number.isFinite(values[c.id])).length<3)return null;
  const matching=new Set(window.SERPENT_VENOM_DATA.profiles.filter(profile=>
    profile.species_name&&sameValues(SpeciesStarters.valuesForProfile(controls,profile))
  ).map(profile=>profile.species_name));
  return matching.size===1?[...matching][0]:null;
}
function renderLd50(concept,pending){
  const node=$('context-ld50');node.replaceChildren();
  if(pending){node.textContent='Release the slider to update reference measurements.';return;}
  const exact=invalid.size?null:exactReferenceSpecies();
  if(exact){
    const result=Ld50Reference.forSpecies(exact);
    if(!result){node.textContent=`No LD50 reference for ${exact} is available in the current source set.`;return;}
    node.append(contextText('p','context-value context-measure',`${result.reference.value} mg/kg`));
    node.append(contextText('p','context-secondary',`Mouse · intravenous · ${result.reference.reported}`));
    node.append(contextText('p','context-caution','One published sample; values vary and this was not measured for this venom profile.'));
    const details=contextDetails('context-ld50','Measurements & source');
    details.append(contextText('p','context-detail-text',result.study.method+'.'));
    const list=document.createElement('ul');list.className='context-measurements';
    for(const record of result.records){const row=document.createElement('li');row.append(contextText('span','',record.reported),contextText('strong','',`${record.value} mg/kg`));list.append(row);}
    details.append(list,contextText('p','context-detail-text','The first listed sample from the newest curated study is shown above. Results vary by sample and test; they are not paired with the entered venom profile or a prediction of human toxicity.'));
    const link=document.createElement('a');link.href=result.study.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=result.study.label;details.append(link);node.append(details);return;
  }
  if(!concept){node.textContent='Enter venom values to compare published measurements.';return;}
  const result=Ld50Reference.estimate(currentSources);
  if(!result){node.textContent='Insufficient comparable measurements among the top five venom matches. More curated reference data is needed.';return;}
  node.append(contextText('p','context-value context-measure',`${result.min}–${result.max} mg/kg`));
  node.append(contextText('p','context-secondary',`Mouse · intravenous · ${result.speciesCount} of ${result.consideredCount} closest species`));
  node.append(contextText('p','context-caution','Reference measurements only; not a toxicity prediction.'));
  const details=contextDetails('context-ld50','Measurements & source');
  details.append(contextText('p','context-detail-text',result.study.method+'.'));
  details.append(contextText('p','context-detail-text',`Closest species with measurements in this study: ${result.closestSpecies} (venom match #${result.closestRank}).`));
  const list=document.createElement('ul');list.className='context-measurements';
  for(const record of result.records){const row=document.createElement('li');row.append(contextText('span','',record.reported),contextText('strong','',`${record.value} mg/kg`));list.append(row);}
  details.append(list,contextText('p','context-detail-text','Range of published point estimates, not a confidence interval or human toxicity prediction. Samples are not paired with the entered profile.'));
  const link=document.createElement('a');link.href=result.study.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent=result.study.label;details.append(link);node.append(details);
}
$('more-sources').addEventListener('toggle',renderMoreSources);
function updateReference(){
  $('starting-reference').hidden=!starting;
  if(!starting){referenceKey='';$('reference-drawing').innerHTML='';return;}
  const name=starting.preset.common_name?`${starting.preset.common_name} — ${starting.species}`:starting.species;
  $('reference-title').textContent=`Starting species reference: ${name}`;
  const key=`${starting.preset.preset_id}:${surface}`;
  if(referenceKey!==key){$('reference-drawing').innerHTML=SpeciesRenderer.render(starting.preset,{surface,framing:'full'}).svg;referenceKey=key;}
}
function updateStartingNote(){
  if(!starting){$('starting-note').textContent='Start with a blank profile or choose a species.';return;}
  const changed=invalid.size>0||controls.some(c=>values[c.id]!==startingValues[c.id]);
  const uncertain=starting.profile.components.some(c=>c.status==='source_uncertain');
  $('starting-note').textContent=`${changed?'Edited starting profile':'Starting venom profile'} · source row ${starting.profile.source_row}${starting.profile.location?' · '+starting.profile.location:''}. ${changed?'The concept uses your current values.':'This is one reported profile; individuals can vary.'}${uncertain?' A disputed source value remains blank.':''}`;
}
function update({deferSources=false}={}){
  const active=Object.values(values).filter(v=>Number.isFinite(v)&&v>0),total=enteredTotal(),overLimit=total>100+EPSILON,belowMinimum=total<MIN_PROFILE_PERCENT-EPSILON;
  const comparable=active.length>0&&!invalid.size&&!overLimit;
  $('total').textContent=`${Number(total.toFixed(2))}%`;
  $('balance-note').textContent=invalid.size?'Enter values from 0 to 100.':overLimit?'This source profile exceeds 100%. Review and reduce its values before generating; the reported values have not been changed.':limitNotice|| (belowMinimum?`Add ${Number((MIN_PROFILE_PERCENT-total).toFixed(2))}% more to reach the 50% minimum for an illustration. Blank values remain unreported.`:active.length<3?'Sparse input: the concept has limited support.':'Blank values are unreported.');
  for(const c of controls){const {slider}=inputs.get(c.id),current=values[c.id]||0,remaining=Number(Math.max(0,100-(total-current)).toFixed(8));slider.max=String(Math.max(current,remaining));slider.value=String(current);}
  const ready=ConnectedInference.ready(window.SERPENT_CONNECTED_MODEL);
  const concept=invalid.size||overLimit||belowMinimum?null:ConnectedInference.predict(values,window.SERPENT_CONNECTED_MODEL,{includeSources:false});
  const drawing=concept?DetailedConcept.render(concept,presets,SpeciesRenderer,{surface}):null;
  svg=drawing?.svg||null;$('drawing').innerHTML=svg||'';$('drawing').hidden=!svg;$('empty').hidden=!!svg;$('download').disabled=!svg;
  $('empty').textContent=!ready?'The experimental model could not be loaded.':invalid.size?'Correct the highlighted inputs.':overLimit?'Reduce the entered total to 100% or less to create a concept.':'Enter at least 50% in total to create an illustration. Unentered amounts remain unspecified. This is a practical minimum, not a guarantee of accuracy.';
  $('dorsal').setAttribute('aria-pressed',String(surface==='dorsal'));$('ventral').setAttribute('aria-pressed',String(surface==='ventral'));
  updateStartingNote();updateReference();
  $('influences').replaceChildren();
  if(deferSources&&comparable){sourcesPending=true;$('source-status').textContent=`Sidebar total: ${Number(total.toFixed(2))}%. The list still shows the previous profile; release the slider to update it.`;}
  else{sourcesPending=false;$('source-status').textContent=comparable?`Comparing the current sidebar values (${Number(total.toFixed(2))}% entered).${controls.filter(c=>Number.isFinite(values[c.id])).length<3?' Few entered categories: comparisons are especially limited.':''}`:'';renderSources(comparable);}
  renderContext(concept,deferSources);
  renderLd50(concept,deferSources);
  $('visual-traits').textContent=concept?`Illustration controls (not probabilities): hood ${Math.round(concept.traits.hood*100)}%, bands ${Math.round(concept.traits.bands*100)}%, blotches ${Math.round(concept.traits.blotches*100)}%, diamonds ${Math.round(concept.traits.diamond*100)}%, rattle ${Math.round(concept.traits.rattle*100)}%.`:'';
  $('explanation-summary').textContent=concept?'The largest effects on the model’s shape controls, compared with setting each component to zero:':'Enter a profile to see how the model responds.';
  if(concept){
    const byId=new Map(controls.map(c=>[c.id,c]));
    for(const effect of concept.contributions.filter(x=>x.score>1e-8).slice(0,3)){
      const item=document.createElement('li'),name=byId.get(effect.id)?.short_label||effect.id,delta=effect.largest.change;
      item.textContent=`${name}: ${delta>=0?'increases':'decreases'} ${effect.largest.label} by ${(Math.abs(delta)*100).toFixed(1)} points on its illustration scale.`;
      $('influences').append(item);
    }
    if(!concept.contributions.some(x=>x.score>1e-8)){const item=document.createElement('li');item.textContent='These inputs have little effect on the displayed shape controls.';$('influences').append(item);}
  }
}
for(const c of controls){
  const box=document.createElement('div');box.className='toxin';const head=document.createElement('div');head.className='toxin-head';
  const label=document.createElement('label');label.className='toxin-label';label.textContent=c.short_label;label.htmlFor=`component-${c.id}`;label.title=c.definition||c.label;
  const small=document.createElement('small');small.textContent=c.label;label.append(small);
  const wrap=document.createElement('div');wrap.className='value-wrap';const input=document.createElement('input');input.type='number';input.id=label.htmlFor;input.min='0';input.max='100';input.step='.1';input.placeholder='—';input.setAttribute('aria-label',`${c.label} percentage`);
  const percent=document.createElement('span');percent.textContent='%';wrap.append(input,percent);head.append(label,wrap);
  const slider=document.createElement('input');slider.type='range';slider.min='0';slider.max='100';slider.step='.1';slider.value='0';slider.setAttribute('aria-label',`${c.label} percentage slider`);
  const row=document.createElement('div');row.className='slider-row';row.append(slider);box.append(head,row);
  if(c.definition||c.boundaries){
    const about=document.createElement('details');about.className='toxin-about';
    const summary=document.createElement('summary');summary.textContent=`About ${c.short_label}`;about.append(summary);
    const description=document.createElement('p');description.textContent=[c.definition,c.boundaries].filter(Boolean).join(' ');about.append(description);box.append(about);
  }
  $('controls').append(box);inputs.set(c.id,{input,slider});
  function apply(raw,fromSlider,deferSources=false){
    const value=raw===''?null:Number(raw);
    if(value!==null&&(!Number.isFinite(value)||value<0||value>100)){invalid.add(c.id);input.setAttribute('aria-invalid','true');limitNotice='';}
    else{
      invalid.delete(c.id);input.removeAttribute('aria-invalid');
      const previous=values[c.id],before=enteredTotal(),after=before-(previous??0)+(value??0);
      if(after>100+EPSILON && (before<=100+EPSILON || after>=before-EPSILON)){
        input.value=previous===null?'':String(previous);slider.value=previous??0;
        limitNotice='The entered total cannot exceed 100%. Reduce another component first.';
      }else{values[c.id]=value;slider.value=value??0;if(fromSlider)input.value=String(value);limitNotice='';}
    }
    update({deferSources});
  }
  input.addEventListener('input',()=>apply(input.value,false));
  slider.addEventListener('input',()=>apply(slider.value,true,true));
  const finishSlider=()=>{if(sourcesPending)apply(slider.value,true);};
  slider.addEventListener('change',finishSlider);slider.addEventListener('pointerup',finishSlider);slider.addEventListener('blur',finishSlider);
}
function loadSpecies(species){
  starting=startersBySpecies.get(species)||null;
  startingValues=starting?SpeciesStarters.valuesForProfile(controls,starting.profile):null;
  for(const c of controls){const v=startingValues?.[c.id]??null;values[c.id]=v;const {input,slider}=inputs.get(c.id);input.value=v===null?'':String(v);input.removeAttribute('aria-invalid');slider.value=v??0;}
  invalid.clear();limitNotice='';update();
}
const blank=document.createElement('option');blank.value='';blank.textContent='Create a new snake';$('starting-species').append(blank);
for(const entry of starters){const option=document.createElement('option');option.value=entry.species;option.textContent=entry.preset.common_name?`${entry.preset.common_name} — ${entry.species}`:entry.species;$('starting-species').append(option);}
$('starting-species').addEventListener('change',e=>loadSpecies(e.target.value));
for(const s of ['dorsal','ventral'])$(s).addEventListener('click',()=>{surface=s;update();});
$('clear').addEventListener('click',()=>{$('starting-species').value='';loadSpecies('');});
$('download').addEventListener('click',()=>{if(!svg)return;const url=URL.createObjectURL(new Blob([svg],{type:'image/svg+xml'})),a=document.createElement('a');a.href=url;a.download='serpentshaper-concept.svg';a.click();setTimeout(()=>URL.revokeObjectURL(url),0);});
update();
})();

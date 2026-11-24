/* Direct experimental model: authored anatomy + a limited photographed color cue. */
(function(root){
'use strict';
const TRAITS=['headWidth','headLength','bodyWidth','hood','diamond','monocle','rattle','tailTaper','bands','blotches','markSpacing','scaleDetail','paddle','bandAccent'];
const COLORS=['skin','marking','belly'];
const TARGETS=TRAITS.concat(COLORS.flatMap(c=>['r','g','b'].map(ch=>`${c}_${ch}`)));
const LABELS={headWidth:'head width',headLength:'head length',bodyWidth:'body width',hood:'hood expansion',diamond:'diamond markings',monocle:'hood marking',rattle:'tail rattle',tailTaper:'tail taper',bands:'banded markings',blotches:'blotched markings',markSpacing:'marking spacing',scaleDetail:'scale spacing',paddle:'tail flattening',bandAccent:'light band accents'};
const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
function ready(model){
  if(!model||model.status!=='experimental_hybrid_not_biological_prediction'||!Array.isArray(model.feature_ids)||!model.feature_ids.length)return false;
  const n=model.feature_ids.length;
  if(new Set(model.feature_ids).size!==n||JSON.stringify(model.targets)!==JSON.stringify(TARGETS)||!Number.isFinite(model.activation_width_percentage_points)||model.activation_width_percentage_points<=0)return false;
  if(!Number.isFinite(model.shape_missingness_scale)||model.shape_missingness_scale<0||!Number.isFinite(model.photo_activation_width_percentage_points)||model.photo_activation_width_percentage_points<=0)return false;
  if(!Array.isArray(model.median)||model.median.length!==n||!model.median.every(Number.isFinite)||!Array.isArray(model.intercepts)||model.intercepts.length!==TARGETS.length||!model.intercepts.every(Number.isFinite)||!Number.isFinite(model.kernel_gamma)||model.kernel_gamma<=0)return false;
  if(!Array.isArray(model.training_vectors)||!model.training_vectors.length||!model.training_vectors.every(a=>Array.isArray(a)&&a.length===2*n&&a.every(Number.isFinite))||!Array.isArray(model.dual_coefficients)||model.dual_coefficients.length!==model.training_vectors.length||!model.dual_coefficients.every(a=>Array.isArray(a)&&a.length===TARGETS.length&&a.every(Number.isFinite)))return false;
  if(!Array.isArray(model.training_sources)||model.training_sources.length!==model.training_vectors.length||!model.training_sources.every(s=>s&&typeof s.species==='string'&&typeof s.profile_id==='string'&&Array.isArray(s.features)&&s.features.length===n&&s.features.every(v=>v===null||Number.isFinite(v))))return false;
  if(!Number.isFinite(model.photo_color_strength)||model.photo_color_strength<0||model.photo_color_strength>1||!(model.provenance?.photo_count>0)||!(model.provenance?.authored_preset_species>0))return false;
  return ['patch_r','patch_g','patch_b'].every(k=>{const p=model.photo_color_models?.[k];return p&&Array.isArray(p.median)&&p.median.length===n&&p.median.every(Number.isFinite)&&Array.isArray(p.coefficients)&&p.coefficients.length===2*n&&p.coefficients.every(Number.isFinite)&&Number.isFinite(p.intercept);});
}
function sourceContributions(values,model){
  if(!ready(model))return [];
  const x=vector(values,model.feature_ids,model.median,model.activation_width_percentage_points,model.shape_missingness_scale),groups=new Map();
  for(let i=0;i<model.training_vectors.length;i++){
    const distance=model.training_vectors[i].reduce((sum,v,j)=>sum+(v-x[j])**2,0);
    const weight=Math.exp(-model.kernel_gamma*distance),source=model.training_sources[i];
    if(!groups.has(source.species))groups.set(source.species,{species:source.species,common_name:source.common_name,rawEffects:Array(TRAITS.length).fill(0),profiles:[]});
    const group=groups.get(source.species),effects=TRAITS.map((_,j)=>weight*model.dual_coefficients[i][j]);
    effects.forEach((v,j)=>{group.rawEffects[j]+=v;});
    group.profiles.push({profile_id:source.profile_id,features:source.features,score:effects.reduce((s,v)=>s+Math.abs(v),0)});
  }
  return [...groups.values()].map(group=>{
    const effects=TRAITS.map((key,i)=>({key,label:LABELS[key],change:group.rawEffects[i]}));
    effects.sort((a,b)=>Math.abs(b.change)-Math.abs(a.change));
    group.profiles.sort((a,b)=>b.score-a.score||a.profile_id.localeCompare(b.profile_id));
    return {...group,score:group.rawEffects.reduce((s,v)=>s+Math.abs(v),0),largest:effects[0]};
  }).filter(group=>group.score>1e-12).sort((a,b)=>b.score-a.score||a.species.localeCompare(b.species));
}
function vector(values,ids,medians,width,indicatorScale=1){
  const first=[],missing=[];
  for(let i=0;i<ids.length;i++){
    const raw=values[ids[i]],v=Number.isFinite(raw)&&raw>0?raw:null;
    const a=v===null?0:clamp(v/width),median=medians[i];
    first.push((median+a*((v===null?median:v)-median))/100);missing.push((1-a)*indicatorScale);
  }
  return first.concat(missing);
}
function rawOutputs(values,model){
  const x=vector(values,model.feature_ids,model.median,model.activation_width_percentage_points,model.shape_missingness_scale);
  const sums=model.intercepts.slice();
  for(let i=0;i<model.training_vectors.length;i++){
    const distance=model.training_vectors[i].reduce((s,v,j)=>s+(v-x[j])**2,0),kernel=Math.exp(-model.kernel_gamma*distance);
    for(let j=0;j<sums.length;j++)sums[j]+=kernel*model.dual_coefficients[i][j];
  }
  const out=Object.fromEntries(TARGETS.map((name,i)=>[name,clamp(sums[i])]));
  for(const channel of ['r','g','b']){
    const p=model.photo_color_models[`patch_${channel}`];
    const px=vector(values,model.feature_ids,p.median,model.photo_activation_width_percentage_points);
    const photo=clamp(p.intercept+p.coefficients.reduce((s,w,j)=>s+w*px[j],0));
    out[`skin_${channel}`]=(1-model.photo_color_strength)*out[`skin_${channel}`]+model.photo_color_strength*photo;
  }
  return out;
}
function predict(values,model,options={}){
  if(!ready(model))return null;
  for(const id of model.feature_ids){const v=values[id];if(v!==null&&v!==undefined&&(!Number.isFinite(v)||v<0||v>100))return null;}
  const active=model.feature_ids.filter(id=>Number.isFinite(values[id])&&values[id]>0);
  if(!active.length)return null;
  const out=rawOutputs(values,model);
  const color=prefix=>'#'+['r','g','b'].map(c=>Math.round(clamp(out[`${prefix}_${c}`])*255).toString(16).padStart(2,'0')).join('');
  const contributions=active.map(id=>{
    const removed={...values,[id]:0},baseline=rawOutputs(removed,model);
    const effects=TRAITS.map(key=>({key,label:LABELS[key],change:out[key]-baseline[key]})).sort((a,b)=>Math.abs(b.change)-Math.abs(a.change));
    return {id,score:effects.reduce((sum,e)=>sum+Math.abs(e.change),0)/effects.length,largest:effects[0]};
  }).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id));
  const skin=color('skin'),marking=color('marking'),belly=color('belly');
  const colors={skin,marking,belly,highlight:belly};
  const traits=Object.fromEntries(TRAITS.map(id=>[id,out[id]]));
  const sources=options.includeSources===false?[]:sourceContributions(values,model);
  return {traits,colors,contributions,sourceContributions:sources,venomContext:{kind:'connected_hybrid_prototype',modelId:model.model_id,venomInputs:{...values},
    evidence:'Anatomy learned from authored designs; a 15% skin-color cue learned from small photo patches. Species names explain training influence; they are not generation inputs or species predictions.',
    shapeSourceSummary:sources.slice(0,5).map(s=>({species:s.species,rawControlScore:s.score,largest:s.largest,profileIds:s.profiles.map(p=>p.profile_id)})),
    provenance:model.provenance},influence:[],manualTraits:[]};
}
const api={TARGETS,TRAITS,LABELS,ready,predict,sourceContributions};if(typeof module!=='undefined')module.exports=api;else root.ConnectedInference=api;
})(typeof window!=='undefined'?window:this);

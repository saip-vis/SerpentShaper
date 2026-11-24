/* Direct venom-to-visual-control inference. No species lookup at inference. */
(function(root){
'use strict';
const TRAITS=['headWidth','headLength','bodyWidth','hood','diamond','monocle','rattle','tailTaper'];
const COLOR_CHANNELS=['skin_r','skin_g','skin_b','marking_r','marking_g','marking_b','highlight_r','highlight_g','highlight_b','belly_r','belly_g','belly_b'];
const TARGETS=TRAITS.concat(COLOR_CHANNELS);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function isReady(model){
  // A candidate cannot be mistaken for an approved image-trained model.
  if(!model||model.status!=='ready_for_preview'||!(model.provenance?.image_count>0)||!(model.provenance?.source_species_count>=4)||!Array.isArray(model.feature_ids))return false;
  const n=model.feature_ids.length,width=model.activation_width_percentage_points;
  if(!n||new Set(model.feature_ids).size!==n||!Number.isFinite(width)||width<=0||!Number.isInteger(model.minimum_active_inputs)||model.minimum_active_inputs<1||model.minimum_active_inputs>n)return false;
  return TARGETS.every(target=>{const p=model.models?.[target];return p&&Array.isArray(p.median)&&p.median.length===n&&p.median.every(Number.isFinite)&&Array.isArray(p.coefficients)&&p.coefficients.length===2*n&&p.coefficients.every(Number.isFinite)&&Number.isFinite(p.intercept);});
}
function predict(values,model){
  if(!isReady(model))return null;
  const n=model.feature_ids.length,width=model.activation_width_percentage_points;
  const raw=model.feature_ids.map(id=>Number.isFinite(values[id])&&values[id]>0?values[id]:null);
  if(raw.some(v=>v!==null&&v>100)||raw.filter(v=>v!==null).length<(model.minimum_active_inputs||3))return null;
  const outputs={};
  for(const target of TARGETS){
    const p=model.models?.[target];
    const xs=[],missing=[];
    for(let i=0;i<n;i++){
      const v=raw[i],median=p.median[i],a=v===null?0:clamp(v/width,0,1);
      xs.push((median+a*((v===null?median:v)-median))/100);missing.push(1-a);
    }
    const x=xs.concat(missing);
    outputs[target]=clamp(p.intercept+p.coefficients.reduce((s,w,i)=>s+w*x[i],0),0,1);
  }
  const color=prefix=>'#'+['r','g','b'].map(c=>Math.round(outputs[`${prefix}_${c}`]*255).toString(16).padStart(2,'0')).join('');
  return {traits:Object.fromEntries(TRAITS.map(id=>[id,outputs[id]])),
    colors:{skin:color('skin'),marking:color('marking'),highlight:color('highlight'),belly:color('belly')},
    venomContext:{kind:'direct_image_trait_model',venomInputs:{...values},modelId:model.model_id||null},influence:[],manualTraits:[]};
}
const api={TARGETS,isReady,predict};if(typeof module!=='undefined')module.exports=api;else root.LearnedInference=api;
})(typeof window!=='undefined'?window:this);

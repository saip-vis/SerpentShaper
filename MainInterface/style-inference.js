/* Bounded artistic variation learned from authored presets, not animal photographs. */
(function(root){
  const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
  function rgb(hex){return [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));}
  function hex(colors){return '#'+colors.map(v=>Math.round(clamp(v,0,255)).toString(16).padStart(2,'0')).join('');}
  function predict(values,model){
    if(!model)return null;
    const input=model.feature_ids.map(id=>Number.isFinite(values[id])?values[id]:null);
    if(input.filter(v=>v!==null).length<model.minimum_inputs)return null;
    const filled=input.map((v,i)=>v===null?model.median[i]:v);
    const indicators=model.missing_indicator_indices.map(i=>input[i]===null?1:0);
    const scaled=filled.concat(indicators).map((v,i)=>(v-model.scaler_mean[i])/model.scaler_scale[i]);
    return model.coefficients.map((weights,i)=>model.intercepts[i]+weights.reduce((n,w,j)=>n+w*scaled[j],0));
  }
  function concept(preset,values,model){
    const prediction=predict(values,model);
    if(!prediction)return null;
    const p=preset.artistic_parameters, strength=clamp(model.blend_strength,0,1);
    const mixColor=(base,offset)=>hex(rgb(base).map((v,i)=>v*(1-strength)+clamp(prediction[offset+i],0,255)*strength));
    const targetPitch=clamp(prediction[6],3,12), originalPitch=p.scale_pitch;
    const mixedPitch=originalPitch*(1-strength)+targetPitch*strength;
    const targetSpacing=clamp(prediction[7],20,120), oldSpacing=p.mark_spacing;
    const mixedSpacing=clamp(oldSpacing*(1-strength)+targetSpacing*strength,oldSpacing*.85,oldSpacing*1.15);
    const cobra=p.body_plan==='cobra';
    const widths=cobra?p.hood_profile.map(v=>v[1]):p.body_stations.map(v=>v[2]);
    const baseRatio=Math.max(...widths)/model.shape_normalizers[p.body_plan];
    const widthAdjustment=1+clamp(prediction[8]-baseRatio,-.12,.12)*strength;
    const variant={...preset,source_species_name:`Concept inspired by ${preset.common_name||preset.source_species_name}`,
      variant:`Experimental artistic variation based on ${preset.source_species_name}. Not a measured phenotype.`,
      artistic_parameters:{...p,mark_spacing:mixedSpacing}};
    return {preset:variant,options:{skinColor:mixColor(p.skin_color,0),ringColor:mixColor(p.marking_color,3),
      scaleDetail:clamp(originalPitch/mixedPitch,.85,1.15),...(cobra?{width:widthAdjustment}:{thickness:widthAdjustment})},prediction};
  }
  const api={predict,concept};if(typeof module!=='undefined')module.exports=api;else root.SerpentStyle=api;
})(typeof window!=='undefined'?window:this);

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
  function sampleStations(stations,t){
    const lengths=[0];for(let i=1;i<stations.length;i++)lengths.push(lengths[i-1]+Math.hypot(stations[i][0]-stations[i-1][0],stations[i][1]-stations[i-1][1]));
    const target=t*lengths[lengths.length-1];let i=0;while(i<stations.length-2&&lengths[i+1]<target)i++;
    const f=(target-lengths[i])/Math.max(1e-9,lengths[i+1]-lengths[i]);
    return stations[i].map((v,k)=>v+(stations[i+1][k]-v)*f);
  }
  function hoodWidth(knots,y){let i=0;while(i<knots.length-2&&knots[i+1][0]<y)i++;const a=knots[i],b=knots[i+1],f=clamp((y-a[0])/(b[0]-a[0]),0,1);return a[1]+(b[1]-a[1])*f;}
  function category(refs,field){
    const scores=new Map();for(const r of refs){const value=r.preset.artistic_parameters[field];scores.set(value,(scores.get(value)||0)+r.weight);}
    return [...scores.entries()].sort((a,b)=>b[1]-a[1]||String(a[0]).localeCompare(String(b[0])))[0][0];
  }
  function anatomy(references){
    const refs=references.filter(r=>r.preset&&Number.isFinite(r.weight)&&r.weight>0);
    if(!refs.length)return null;
    const plan=category(refs,'body_plan'),same=refs.filter(r=>r.preset.artistic_parameters.body_plan===plan);
    const total=same.reduce((n,r)=>n+r.weight,0),group=same.map(r=>({...r,weight:r.weight/total}));
    const pattern=category(group,'pattern');
    const patternRef=group.filter(r=>r.preset.artistic_parameters.pattern===pattern).sort((a,b)=>b.weight-a.weight)[0];
    const source=patternRef.preset,p={...source.artistic_parameters};
    if(plan==='cobra'){
      const ys=[145,178,200,220,235,250,270,290,310,330,350];
      p.hood_profile=ys.map(y=>[y,group.reduce((n,r)=>n+r.weight*hoodWidth(r.preset.artistic_parameters.hood_profile,y),0)]);
    }else{
      p.body_stations=Array.from({length:16},(_,i)=>{
        const points=group.map(r=>({point:sampleStations(r.preset.artistic_parameters.body_stations,i/15),weight:r.weight}));
        return [0,1,2].map(k=>points.reduce((n,v)=>n+v.weight*v.point[k],0));
      });
      const base=p.head_geometry;
      const compatible=group.filter(r=>{const h=r.preset.artistic_parameters.head_geometry;return h.upper.length===base.upper.length&&h.lower.length===base.lower.length&&h.upper.every(a=>a.length===8)&&h.lower.every(a=>a.length===8);});
      const htotal=compatible.reduce((n,r)=>n+r.weight,0);
      const weighted=(field)=>compatible.reduce((n,r)=>n+r.weight*r.preset.artistic_parameters.head_geometry[field]/htotal,0);
      const head={...base,length:weighted('length'),neck:weighted('neck')};
      for(const side of ['upper','lower'])head[side]=base[side].map((segment,i)=>segment.map((_,j)=>compatible.reduce((n,r)=>n+r.weight*r.preset.artistic_parameters.head_geometry[side][i][j]/htotal,0)));
      for(const field of ['eye','nostril'])if(compatible.every(r=>r.preset.artistic_parameters.head_geometry[field]?.length===base[field]?.length))head[field]=base[field].map((_,i)=>compatible.reduce((n,r)=>n+r.weight*r.preset.artistic_parameters.head_geometry[field][i]/htotal,0));
      p.head_geometry=head;
      const tail=category(group,'tail_type'),tailRef=group.filter(r=>r.preset.artistic_parameters.tail_type===tail).sort((a,b)=>b.weight-a.weight)[0].preset.artistic_parameters;
      p.tail_type=tail;
      for(const field of ['tail_segments','rattle_size','tail_pattern','tail_pattern_length','tail_color','tail_color_length']){
        if(Object.hasOwn(tailRef,field))p[field]=tailRef[field];else delete p[field];
      }
    }
    return {...source,preset_id:'generated_concept',species_id:null,source_species_name:'Hypothetical snake concept',common_name:'Generated concept',
      variant:'Reference-blended artistic anatomy. Not an identified species or a measured phenotype.',artistic_parameters:p};
  }
  function concept(values,model,references=[]){
    const modelPrediction=predict(values,model);
    if(!modelPrediction)return null;
    const preset=anatomy(references);
    if(!preset)return null;
    const p=preset.artistic_parameters, strength=clamp(model.blend_strength,0,1);
    const usable=references.filter(r=>r.preset&&Number.isFinite(r.weight)&&r.weight>0);
    const totalWeight=usable.reduce((n,r)=>n+r.weight,0);
    const referenceStyle=Array(modelPrediction.length).fill(0);
    for(const ref of usable){
      const q=ref.preset.artistic_parameters,cobra=q.body_plan==='cobra';
      const widths=cobra?q.hood_profile.map(v=>v[1]):q.body_stations.map(v=>v[2]);
      const features=rgb(q.skin_color).concat(rgb(q.marking_color),[q.scale_pitch,q.mark_spacing,Math.max(...widths)/model.shape_normalizers[q.body_plan]]);
      features.forEach((v,i)=>referenceStyle[i]+=v*ref.weight/totalWeight);
    }
    // Reference percentages describe only the reference-style half of this signal.
    const prediction=totalWeight?modelPrediction.map((v,i)=>(v+referenceStyle[i])/2):modelPrediction;
    const mixColor=(base,offset)=>hex(rgb(base).map((v,i)=>v*(1-strength)+clamp(prediction[offset+i],0,255)*strength));
    const targetPitch=clamp(prediction[6],3,12), originalPitch=p.scale_pitch;
    const mixedPitch=originalPitch*(1-strength)+targetPitch*strength;
    const targetSpacing=clamp(prediction[7],20,120), oldSpacing=p.mark_spacing;
    const mixedSpacing=clamp(oldSpacing*(1-strength)+targetSpacing*strength,oldSpacing*.85,oldSpacing*1.15);
    const cobra=p.body_plan==='cobra';
    const widths=cobra?p.hood_profile.map(v=>v[1]):p.body_stations.map(v=>v[2]);
    const baseRatio=Math.max(...widths)/model.shape_normalizers[p.body_plan];
    const widthAdjustment=1+clamp(prediction[8]-baseRatio,-.12,.12)*strength;
    const variant={...preset,artistic_parameters:{...p,mark_spacing:mixedSpacing}};
    return {preset:variant,options:{skinColor:mixColor(p.skin_color,0),ringColor:mixColor(p.marking_color,3),
      scaleDetail:clamp(originalPitch/mixedPitch,.85,1.15),...(cobra?{width:widthAdjustment}:{thickness:widthAdjustment})},prediction};
  }
  const api={predict,anatomy,concept};if(typeof module!=='undefined')module.exports=api;else root.SerpentStyle=api;
})(typeof window!=='undefined'?window:this);

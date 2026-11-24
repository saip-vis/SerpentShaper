/* Smooth venom-driven controls adapted to the project's detailed SVG renderer.
 * The geometry templates are authored illustrations, not measured animals.
 */
(function(root){
'use strict';
const clamp=v=>Math.max(0,Math.min(1,Number.isFinite(v)?v:0));
const lerp=(a,b,t)=>a+(b-a)*t;
function stationAt(stations,fraction){
  const distances=[0];for(let i=1;i<stations.length;i++)distances.push(distances[i-1]+Math.hypot(stations[i][0]-stations[i-1][0],stations[i][1]-stations[i-1][1]));
  const target=fraction*distances[distances.length-1];let i=0;while(i<stations.length-2&&distances[i+1]<target)i++;
  const t=(target-distances[i])/Math.max(1e-9,distances[i+1]-distances[i]);
  return stations[i].map((v,k)=>lerp(v,stations[i+1][k],t));
}
function makePreset(concept,presets){
  if(!concept?.traits||!concept.colors||!Array.isArray(presets))return null;
  const slender=presets.find(p=>p.preset_id==='dendroaspis_polylepis');
  const broad=presets.find(p=>p.preset_id==='crotalus_atrox');
  if(!slender||!broad)return null;
  const t=concept.traits,headWeight=clamp(t.headWidth),bodyWeight=clamp(t.bodyWidth);
  const a=slender.artistic_parameters,b=broad.artistic_parameters,ah=a.head_geometry,bh=b.head_geometry;
  const length=45+55*clamp(t.headLength),neck=lerp(ah.neck,bh.neck,bodyWeight);
  const segments=side=>ah[side].map((seg,i)=>seg.map((value,j)=>j%2===0
    ?lerp(value/ah.length,bh[side][i][j]/bh.length,headWeight)*length
    :lerp(value,bh[side][i][j],headWeight)));
  const upper=segments('upper'),lower=segments('lower');
  upper[upper.length-1][6]=length;upper[upper.length-1][7]=-neck;
  lower[lower.length-1][6]=length;lower[lower.length-1][7]=neck;
  const eye=[lerp(ah.eye[0]/ah.length,bh.eye[0]/bh.length,headWeight)*length,
    lerp(ah.eye[1],bh.eye[1],headWeight),lerp(ah.eye[2],bh.eye[2],headWeight),lerp(ah.eye[3],bh.eye[3],headWeight)];
  const h={length,neck,upper,lower,eye,nostril:[length*.08,-2],origin:[145,185],angle_degrees:17,
    jaw:`M2 4 Q${length*.35} 8 ${length*.75} 11 L${length*.9} ${neck}`,
    shields:[],lip:true};
  const body_stations=Array.from({length:16},(_,i)=>{
    const x=stationAt(a.body_stations,i/15),y=stationAt(b.body_stations,i/15);
    const point=x.map((v,k)=>lerp(v,y[k],bodyWeight));
    const tail=Math.max(0,Math.min(1,(i/15-.55)/.45));
    point[2]*=1+(.5-clamp(t.tailTaper))*.65*tail*tail*(3-2*tail);
    return point;
  }).slice(1); // The shared first station stays ahead of every allowed head length.
  const p={body_plan:'terrestrial',pattern:'plain',skin_color:concept.colors.skin,marking_color:concept.colors.marking,
    belly_color:concept.colors.belly,body_build:1,scale_texture:'smooth',tail_type:'pointed',
    scale_pitch:3+9*clamp(t.scaleDetail),mark_spacing:20+100*clamp(t.markSpacing),mark_size:1,
    tail_segments:4,head_style:'rounded',pupil:'round',head_geometry:h,body_stations,head_detail_box:[125,140,170,120]};
  return {preset_id:'generated_concept',species_id:null,source_species_name:'Hypothetical snake concept',
    common_name:'Generated concept',variant:'Continuous authored-shape study; not an identified species.',
    model_revision:1,artistic_parameters:p};
}
function render(concept,presets,renderer,options={}){
  const preset=makePreset(concept,presets);if(!preset||!renderer?.render)return null;
  const t=concept.traits;
  const output=renderer.render(preset,{surface:options.surface==='ventral'?'ventral':'dorsal',framing:'full',
    conceptHood:clamp(t.hood),conceptMonocle:clamp(t.monocle),conceptRattle:clamp(t.rattle),conceptPaddle:clamp(t.paddle),
    conceptPatternWeights:{diamond:clamp(t.diamond),bands:clamp(t.bands),blotches:clamp(t.blotches),bandAccent:clamp(t.bandAccent)},
    conceptMetadata:concept.venomContext});
  return {...output,preset};
}
const api={makePreset,render,stationAt};if(typeof module!=='undefined')module.exports=api;else root.DetailedConcept=api;
})(typeof window!=='undefined'?window:this);

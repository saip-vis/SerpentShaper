/* Pure SVG renderer. Presets supply traits/design values; no species-name conditionals. */
(function(root){
const G=typeof module!=='undefined'?require('./species-geometry.js'):root.SpeciesGeometry;
const Head=typeof module!=='undefined'?require('./head-renderer.js'):root.SpeciesHead;
const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
const shade=(hex,f)=>'#'+rgb(hex).map(v=>Math.max(0,Math.min(255,Math.round(v*f))).toString(16).padStart(2,'0')).join('');
const mix=(a,b,t)=>'#'+rgb(a).map((v,i)=>Math.max(0,Math.min(255,Math.round(v*(1-t)+rgb(b)[i]*t))).toString(16).padStart(2,'0')).join('');
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
function render(preset, options={}) {
  const p=preset.artistic_parameters,cobra=p.body_plan==='cobra',rear=(options.surface||'dorsal')==='dorsal';
  const skin=options.skinColor||p.skin_color,cream=options.ringColor||p.marking_color,belly=p.belly_color;
  const headColor=options.conceptMetadata&&!rear?belly:(p.head_color||skin);
  const width=options.width??1,detail=options.scaleDetail??1,contrast=options.patternContrast??1,markSize=options.ringSize??1;
  const shape=G.geometry(preset,options),mesh=G.surface(shape.points),pitch=p.scale_pitch/detail;
  const coord=(s,u)=>{const a=mesh.at(s,u);return `${a.x.toFixed(2)} ${a.y.toFixed(2)}`;};
  const start=cobra?59:0,tailStart=mesh.length-(p.tail_band_length??110);
  const pigment=(s,u)=>{
    if(!rear && p.ventral_pattern==='bands'){
      const inTail=p.ventral_tail_light && s>tailStart;
      const step=p.ventral_band_spacing??20;
      const phase=(s%(2*step))/(2*step);
      return phase<.5?(inTail?p.ventral_tail_light:belly):p.ventral_band_dark;
    }
    if(p.tail_pattern==='alternating_bands' && s>tailStart){
      const phase=((s-tailStart)%(2*(p.tail_band_spacing??12)))/(2*(p.tail_band_spacing??12));
      return phase<(1-(p.tail_band_dark_fraction??.5))?p.tail_band_light:p.tail_band_dark;
    }
    if(p.tail_type==='paddle' && p.tail_pattern==='spots' && s>mesh.length-(p.tail_pattern_length??100)){
      return Math.sin(s*.18)*Math.cos(u*10)>.42?cream:belly;
    }
    if(p.tail_color && s>mesh.length-(p.tail_color_length||80))return p.tail_color;
    if(p.tail_type==='rattle' && s>tailStart){
      const phase=((s-tailStart)%(2*(p.tail_band_spacing??12)))/(2*(p.tail_band_spacing??12));
      return phase<(1-(p.tail_band_dark_fraction??.5))?(p.tail_band_light||cream):(p.tail_band_dark||'#302e28');
    }
    if(!rear && !cobra && !['rings','coral_triads','band_sequence'].includes(p.pattern)) return belly;
    if(rear && p.dorsal_midline_color && Math.abs(u)<(p.dorsal_midline_width??.07))return p.dorsal_midline_color;
    if(rear && p.ventrolateral_stripe && Math.abs(u)>(p.ventrolateral_stripe_start??.84))return cream;
    if(rear && p.pattern==='lateral_bicolor')return u>(p.lateral_boundary??.1)?belly:skin;
    if(rear && p.neck_stripe_color && s<(p.neck_stripe_length??120) && Math.abs(Math.abs(u)-(p.neck_stripe_offset??.38))<(p.neck_stripe_width??.1))return p.neck_stripe_color;
    if(p.pattern==='coral_triads'){
      // A broad red interval followed by three dark bands separated by two
      // pale bands. One period is a complete motif, not an individual ring.
      const phase=(s%(p.mark_spacing||100))/(p.mark_spacing||100);
      const groupWidth=.6*markSize, start=1-groupWidth;
      if(phase<start)return skin;
      const q=(phase-start)/groupWidth;
      return q<.25?cream:q<.333?belly:q<.667?cream:q<.75?belly:cream;
    }
    if(p.pattern==='band_sequence'){
      // A configurable red interval and a sequence of pigment bands; retain
      // the same ordering on the dorsal scales and ventral plates.
      const phase=(s%(p.mark_spacing||100))/(p.mark_spacing||100);
      const bands=p.band_sequence, base=bands[0].fraction;
      const groupWidth=Math.min(.98,(1-base)*markSize);
      if(phase<1-groupWidth)return skin;
      const position=(phase-(1-groupWidth))/groupWidth*(1-base);
      let end=0;
      for(const band of bands.slice(1)){
        end+=band.fraction;
        if(position<end)return ({skin,marking:cream,belly})[band.color];
      }
      return ({skin,marking:cream,belly})[bands[bands.length-1].color];
    }
    if(s<50)return skin;
    const phase=((s-55)%(p.mark_spacing||52))/(p.mark_spacing||52),d=Math.abs(phase-.5)*2,au=Math.abs(u);
    if(p.pattern==='rings')return phase<(p.band_fraction||.35)*markSize?cream:skin;
    if(p.pattern==='hourglass'){
      const edge=.13+.48*au*au;
      return d<edge*markSize?cream:d<(edge+.08)*markSize?shade(cream,.73):skin;
    }
    if(p.pattern==='crossbands')return d<(.28+.13*Math.cos(u*4))*markSize?cream:skin;
    if(p.pattern==='chevrons'){
      const v=Math.abs(((phase+au*.35)%1)-.5)*2;
      const band=p.chevron_width??.20,border=p.chevron_border??.09;
      return v<band*markSize?cream:v<(band+border)*markSize?belly:skin;
    }
    if(p.pattern==='blotches'){
      const edge=d/markSize+Math.abs(u*.75);
      return edge<.65?cream:p.blotch_border&&edge<.82?p.blotch_border:p.dorsal_interspot_color&&au<.14?p.dorsal_interspot_color:skin;
    }
    if(p.pattern==='speckled')return Math.sin(s*.39+u*27)*Math.cos(s*.17-u*49)>(p.speckle_threshold??.48)?cream:skin;
    if(p.pattern==='paired_spots'){
      const edge=Math.hypot((phase-.5)/(.16*markSize),(au-.50)/.19);
      return edge<1?cream:skin;
    }
    if(p.pattern==='dorsal_zigzag'){
      const wave=(1-4*Math.abs(phase-.5))*.42;
      return Math.abs(u-wave)<(p.zigzag_width??.24)*markSize?cream:skin;
    }
    if(p.pattern==='reticulated')return Math.sin(s*.38+u*29)*Math.cos(s*.16-u*43)>.66?cream:skin;
    if(p.pattern==='flank_triangles'){
      const edge=d+(.95-au)*.7;
      return edge<.68*markSize?cream:edge<.77*markSize?(p.pattern_border_color||belly):skin;
    }
    if(p.pattern==='trapezoids'){
      const edge=d+Math.max(0,.6-au)*.35;
      return edge<.47*markSize?cream:edge<.55*markSize?(p.pattern_border_color||belly):skin;
    }
    if(p.pattern==='hooks'){
      const shifted=(phase+(u<0?.32:0))%1;
      const outer=((shifted-.5)/(.26*markSize))**2+((au-.65)/.40)**2;
      const inner=((shifted-.40)/(.18*markSize))**2+((au-.53)/.27)**2;
      return outer<1&&inner>1?cream:outer<1.22&&inner>.8?(p.pattern_border_color||belly):skin;
    }
    if(p.pattern==='dotted_bands'){
      const edge=Math.abs(d-(.30+.12*Math.sin(u*4)));
      return edge<.07*markSize&&Math.sin(u*45+s*.02)>.15?cream:skin;
    }
    if(p.pattern==='diamonds'){
      const edge=d/markSize+au;
      return edge<.87?(p.diamond_center_color||'#584732'):edge<1.08?cream:skin;
    }
    if(p.pattern==='outlined_diamonds'){
      const edge=d/markSize+au;
      return edge<(p.diamond_inner??.59)?skin:edge<.75?cream:edge<.87?belly:skin;
    }
    if(p.pattern==='ocelli' || p.pattern==='paired_ocelli'){
      const center=p.pattern==='paired_ocelli'
        ?Math.hypot((phase-.5)/(.24*markSize),(au-.34)/.23)
        :Math.hypot((phase-.5)/(.31*markSize),u/.31);
      const stagger=((phase+.5)%1)-.5;
      const side=Math.hypot(stagger/(.25*markSize),(au-.72)/.23);
      const edge=Math.min(center,side);
      return edge<.68?(p.ocelli_center_color||shade(skin,.72)):edge<.88?cream:edge<1.08?belly:skin;
    }
    if(p.pattern==='gaboon'){
      if(d<.73*markSize && au<.28)return cream;
      if(au>.32 && Math.abs(au-(1-d*.7))<.22)return '#352e2b';
      if(au>.3 && d<.36)return '#beaa95';
    }
    if(p.pattern==='mottled' && Math.sin(s*.11/markSize+u*19/markSize)*Math.cos(s*.04/markSize-u*13/markSize)>.61)return cream;
    return skin;
  };
  // Continuous motif strengths are used only for the generated concept.
  // Existing species presets keep their original, species-specific pigments.
  const conceptPigment=(s,u,base)=>{
    const weights=options.conceptPatternWeights;
    if(!rear||cobra||!weights||s<50)return base;
    const clamp=v=>Math.max(0,Math.min(1,Number.isFinite(v)?v:0));
    const smooth=(a,b,v)=>{const t=clamp((v-a)/(b-a));return t*t*(3-2*t);};
    const phase=((s-55)%(p.mark_spacing||52))/(p.mark_spacing||52),d=Math.abs(phase-.5)*2,au=Math.abs(u);
    const diamond=d+au,diamondMask=1-smooth(.88,1.05,diamond),core=1-smooth(.70,.88,diamond);
    const bandMask=1-smooth(.25,.37,d),blotchMask=1-smooth(.56,.70,d+au*.75);
    const diamondColor=mix(cream,p.diamond_center_color||shade(skin,.50),core);
    let color=mix(base,cream,clamp(weights.bands)*bandMask);
    const bandEdge=Math.max(0,1-smooth(.44,.53,d)-bandMask);
    color=mix(color,belly,clamp(weights.bands)*clamp(weights.bandAccent)*bandEdge);
    color=mix(color,diamondColor,clamp(weights.diamond)*diamondMask);
    return mix(color,shade(cream,.72),clamp(weights.blotches)*blotchMask);
  };
  let scales='',scaleTips='',seams='',keels='',plates='',count=0;
  for(let s=start,row=0;s<mesh.length-5;s+=pitch*.8,row++){
    const center=mesh.at(s),cols=Math.max(3,Math.round(2*center.r/pitch)+(row%2));
    for(let col=0;col<cols;col++){
      const u=-1+(col+.5)*2/cols,h=1.08/cols;
      const d=`M${coord(s-pitch*.7,u)} Q${coord(s-pitch*.55,u-h)} ${coord(s,u-h)} Q${coord(s+pitch*.55,u-h*.9)} ${coord(s+pitch*.9,u)} Q${coord(s+pitch*.55,u+h*.9)} ${coord(s,u+h)} Q${coord(s-pitch*.55,u+h)} ${coord(s-pitch*.7,u)}Z`;
      const light=.68+.38*Math.sqrt(Math.max(0,1-u*u))-.13*u+Math.sin(row*37+col*19)*.035;
      const basePigment=conceptPigment(s,u,pigment(s,u));
      scales+=`<path d="${d}" fill="${shade(basePigment,light)}"/>`;
      if(rear && p.scale_tip_color && basePigment===skin){
        const tip=`M${coord(s+pitch*.32,u-h*.25)} Q${coord(s+pitch*.82,u)} ${coord(s+pitch*.32,u+h*.25)} Q${coord(s+pitch*.48,u)} ${coord(s+pitch*.32,u-h*.25)}Z`;
        scaleTips+=`<path d="${tip}" fill="${p.scale_tip_color}" opacity=".72"/>`;
      }
      const showSeam=options.conceptMetadata&&!rear&&!cobra?(s<=45||Math.abs(u)>.84):(rear||!cobra||center.y>=420||Math.abs(u)>.84);
      if(showSeam){
        const exposed=`M${coord(s,u-h)} Q${coord(s+pitch*.55,u-h*.9)} ${coord(s+pitch*.9,u)} Q${coord(s+pitch*.55,u+h*.9)} ${coord(s,u+h)}`;
        seams+=`<path d="${exposed}"/>`;
        if(p.scale_texture==='keeled')keels+=`<path d="M${coord(s-pitch*.28,u)} L${coord(s+pitch*.65,u)}"/>`;
      }
      count++;
    }
    if(!rear && (cobra?center.y<420:s>45) && !(p.tail_type==='rattle' && s>tailStart)) {
      const d=`M${coord(s,-.82)} Q${coord(s+pitch*.6,0)} ${coord(s,.82)} L${coord(s+pitch*.78,.82)} Q${coord(s+pitch*1.3,0)} ${coord(s+pitch*.78,-.82)}Z`;
      const plateColor=['coral_triads','band_sequence'].includes(p.pattern)||p.ventral_pattern==='bands'||p.tail_pattern==='alternating_bands'&&s>tailStart?pigment(s,0):belly;
      plates+=`<path d="${d}" fill="${shade(plateColor,.93+.04*Math.sin(row*.63))}" stroke="#68573b" stroke-opacity=".35" stroke-width=".45"/>`;
    }
  }
  let markings='',head='',appendage='';
  if(cobra){
    if(rear){
      if(p.pattern==='monocle')markings=`<g id="monocle" transform="translate(300 221) scale(${width*markSize} ${markSize})"><path d="M0 -39 C-24 -40 -34 -23 -34 -1 C-34 20 -18 40 0 40 C18 40 34 20 34 -1 C34 -23 24 -40 0 -39Z" fill="${shade(skin,.55)}" stroke="${cream}" stroke-width="9"/></g>`;
      else if(p.pattern==='spectacle')markings=`<g id="spectacle" transform="translate(300 221) scale(${width*markSize} ${markSize})" stroke="${cream}" stroke-width="7" fill="${shade(skin,.55)}"><ellipse cx="-29" cy="-4" rx="17" ry="21"/><ellipse cx="29" cy="-4" rx="17" ry="21"/><path d="M-16 10 Q0 35 16 10" fill="none"/></g>`;
    }else markings=`<path d="M180 264 Q300 289 420 264 L420 284 Q300 311 180 284Z" fill="${shade(skin,.48)}"/><g fill="${shade(skin,.5)}">${[-1,1].map(side=>[0,1,2,3].map(i=>`<path d="M-3 -7 Q-7 -3 -5 2 L-2 7 Q3 8 5 3 L4 -3 L1 -6Z" transform="translate(${300+side*(54-i*4)*width} ${169+i*19+(side>0?4:0)}) rotate(${side*(15+i*7)}) scale(${width*(.7+i*.11)} ${.7+(i%3)*.2})"/>`).join('')).join('')}</g>`;
    if(!rear && p.ventral_markings === false)markings='';
    if(!rear && p.throat_bands){
      markings=p.throat_bands.map(b=>`<path d="M180 ${b.y} Q300 ${b.y+7} 420 ${b.y} L420 ${b.y+b.height} Q300 ${b.y+b.height+7} 180 ${b.y+b.height}Z" fill="${b.color||shade(skin,.4)}" opacity="${b.opacity??.9}"/>`).join('');
    }
    head=`<path d="M260 78 L337 78 L337 128 Q300 143 260 128Z" fill="url(#headVolume)"/><g id="head-shields" fill="none" stroke="${shade(skin,.48)}" stroke-width=".75">${rear?'<path d="M291 87 L289 95 L300 100 L311 95 L309 87 M300 100 L300 114 M281 101 L288 102 L292 112 L287 122 M319 101 L312 102 L308 112 L313 122 M292 112 Q300 116 308 112 M287 122 L291 134 M313 122 L309 134 M300 114 L300 131"/>':'<path d="M274 96 L285 98 L293 94 L289 91 M285 98 L289 105 L301 106 L309 97 L293 94 M301 106 L311 114 L323 110 M311 114 L313 123 M268 105 L282 111 L304 114 M276 109 L276 112 M283 111 L283 114 M291 112 L291 115 M299 113 L299 116"/>'}</g>`;
    if(!rear)head+='<g id="eyes"><path d="M304 101 Q308 97 312 100 Q313 103 309 105 Q305 106 304 101Z" fill="#a58c56" stroke="#443622" stroke-width=".8"/><circle cx="308.5" cy="101.7" r="2.1" fill="#17251c"/><circle cx="307.8" cy="100.8" r=".45" fill="#e7ddc1"/><ellipse cx="275" cy="100" rx="1.25" ry=".7" fill="#483825"/></g>';
    if(!rear && p.front_head_width)head=`<g transform="translate(300 0) scale(${p.front_head_width} 1) translate(-300 0)">${head}</g>`;
    if(!rear && p.front_head_profile){
      if(!p.throat_bands && p.ventral_markings===false)markings='';
      head=`<path d="M276 78 H334 V119 Q312 124 289 119 L270 114Z" fill="url(#headVolume)"/><path d="M279 106 Q291 118 316 115 Q325 113 329 108 L328 125 Q310 133 286 126 Q291 121 290 118Z" fill="${belly}" opacity=".8"/><g fill="none" stroke="${shade(skin,.48)}" stroke-width=".75"><path d="M279 105 Q293 116 309 113 Q320 112 328 107 M283 100 L291 97 L299 101 L300 108 L290 108 Z M291 97 L298 92 L307 94 L310 99 M300 108 L307 112 L314 107 M284 108 L283 112 M291 111 L290 115 M299 113 L299 117 M307 113 L307 117 M315 111 L316 115 M315 101 L324 98 L330 101 M315 107 L322 110 L329 107"/></g><g id="eyes"><ellipse cx="313" cy="101" rx="4" ry="3.6" fill="#393b2b"/><ellipse cx="313" cy="101" rx="3.1" ry="2.8" fill="#b9a779"/><circle cx="313" cy="101" r="1.8" fill="#17231c"/><circle cx="312.3" cy="100.2" r=".5" fill="#fff3d9"/><ellipse cx="282" cy="102" rx="1.1" ry=".65" fill="#302f25"/></g>`;
    }
  } else {
    head=Head.render(preset,shape,headColor,cream,belly,rear);
    if(rear&&Number.isFinite(options.conceptMonocle)&&options.conceptMonocle>0&&Number.isFinite(options.conceptHood)&&options.conceptHood>0){
      const point=mesh.at(mesh.length*.075),angle=Math.atan2(point.ty,point.tx)*180/Math.PI;
      const opacity=Math.max(0,Math.min(1,options.conceptMonocle))*Math.max(0,Math.min(1,options.conceptHood));
      markings+=`<ellipse id="concept-hood-mark" cx="${point.x.toFixed(2)}" cy="${point.y.toFixed(2)}" rx="16" ry="${Math.max(5,point.r*.58).toFixed(2)}" transform="rotate(${angle.toFixed(2)} ${point.x.toFixed(2)} ${point.y.toFixed(2)})" fill="${shade(skin,.5)}" stroke="${cream}" stroke-width="4" opacity="${opacity.toFixed(4)}"/>`;
    }
    if(p.tail_type==='rattle'||Number.isFinite(options.conceptRattle)&&options.conceptRattle>0){
      const tip=mesh.at(mesh.length),angle=Math.atan2(tip.ty,tip.tx)*180/Math.PI;
      const strength=p.tail_type==='rattle'?1:Math.max(0,Math.min(1,options.conceptRattle));
      appendage=`<g id="rattle" opacity="${strength}" transform="translate(${tip.x} ${tip.y}) rotate(${angle}) scale(${(p.rattle_size??1)*(.45+.55*strength)})">${Array.from({length:p.tail_segments},(_,i)=>`<ellipse cx="${3+i*5}" cy="0" rx="4" ry="${6-i*.55}" fill="${i%2?'#b9a07a':'#d6c5a0'}" stroke="#635946" stroke-width=".8"/>`).join('')}</g>`;
    }
    if(p.tail_type==='paddle'){
      for(let s=mesh.length-120;s<mesh.length-10;s+=9)appendage+=`<path d="M${coord(s,-.8)} Q${coord(s+5,0)} ${coord(s,.8)}" fill="none" stroke="${shade(skin,.6)}" opacity=".4" stroke-width=".8"/>`;
      appendage=`<g id="paddle-fin-detail" clip-path="url(#anatomyClip)">${appendage}</g>`;
    }
  }
  if(rear && p.ventrolateral_stripe){
    for(const side of [-1,1]){
      const offset=p.ventrolateral_stripe_start===undefined?.87:(p.ventrolateral_stripe_start+1)/2;
      const line=[];for(let s=12;s<mesh.length-12;s+=5)line.push(`${line.length?'L':'M'}${coord(s,side*offset)}`);
      markings+=`<path d="${line.join(' ')}" fill="none" stroke="${cream}" stroke-width=".75"/>`;
    }
  }
  if(rear && p.dorsal_midline_color){
    const line=[];for(let s=20;s<mesh.length-15;s+=5)line.push(`${line.length?'L':'M'}${coord(s,0)}`);
    const stripeWidth=2*mesh.at(mesh.length*.45).r*(p.dorsal_midline_width??.07);
    markings+=`<path id="dorsal-midline" d="${line.join(' ')}" fill="none" stroke="${p.dorsal_midline_color}" stroke-width="${stripeWidth.toFixed(2)}"/>`;
  }
  if(rear && p.longitudinal_stripe_offsets){
    const stripeWidth=2*mesh.at(mesh.length*.45).r*(p.longitudinal_stripe_width??.05);
    for(const offset of p.longitudinal_stripe_offsets){
      const line=[];for(let s=20;s<mesh.length-15;s+=5)line.push(`${line.length?'L':'M'}${coord(s,offset)}`);
      markings+=`<path class="longitudinal-stripe" d="${line.join(' ')}" fill="none" stroke="${cream}" stroke-width="${stripeWidth.toFixed(2)}"/>`;
    }
  }
  const box=options.framing==='hood'?(cobra?'195 65 210 340':(p.head_detail_box||[125,140,170,120]).join(' ')):(cobra?'185 55 465 660':'105 140 585 465');
  const description=options.conceptMetadata?'Experimental venom-driven illustration. Anatomy is based on authored designs, not a validated biological prediction.':`Illustrative preset: ${preset.variant}. Artistic proportions; no venom inference.`;
  const svg=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${box}" role="img" aria-labelledby="modelTitle modelDescription"><title id="modelTitle">${escape(preset.source_species_name)} — ${rear?'dorsal / oblique':'ventral study'}</title><desc id="modelDescription">${escape(description)}</desc><metadata>${escape(JSON.stringify({preset_id:preset.preset_id,model_revision:preset.model_revision,species_id:preset.species_id,options,measurement_status:'artistic_not_measured',venom_trait_mapping:null}))}</metadata><defs><path id="bodyGeometry" d="${shape.path}"/>${shape.headPath?`<clipPath id="headClip"><path d="${shape.headPath}"/></clipPath>`:''}<clipPath id="anatomyClip"><use href="#bodyGeometry"/></clipPath><linearGradient id="headVolume"><stop stop-color="${shade(headColor,.6)}"/><stop offset=".45" stop-color="${shade(headColor,1.18)}"/><stop offset="1" stop-color="${shade(headColor,.7)}"/></linearGradient></defs><g id="anatomy-layer"><use href="#bodyGeometry" fill="${skin}"/></g><g clip-path="url(#anatomyClip)"><g id="dorsal-scale-fills">${scales}</g>${scaleTips?`<g id="scale-tips">${scaleTips}</g>`:''}<g id="ventral-plates">${plates}</g><g id="pigment-pattern">${markings}</g><g id="scale-seams" fill="none" stroke="${['edged_scales','reticulated'].includes(p.pattern)?cream:'#302b24'}" opacity="${(['edged_scales','reticulated'].includes(p.pattern)?.85:.44)*contrast}" stroke-width="${p.scale_border_width||.42}">${seams}</g><g id="scale-keels" fill="none" stroke="#2d3024" opacity=".3" stroke-width=".45">${keels}</g><g id="scale-highlights" fill="none" stroke="#fff0cf" opacity=".16" stroke-width=".22" transform="translate(-.3 -.5)">${seams}</g>${head}</g><use href="#bodyGeometry" fill="none" stroke="${shade(skin,.48)}" stroke-width="1.1"/>${appendage}</svg>`;
  if(options.silhouette){
    const simple=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${box}" role="img" aria-label="${escape(preset.common_name)} anatomy silhouette"><path d="${shape.path}" fill="#34463d"/><style>#silhouette-appendage *{fill:#34463d;stroke:#34463d}</style><g id="silhouette-appendage" fill="#34463d" stroke="#34463d">${p.tail_type==='rattle'?appendage:''}</g></svg>`;
    return {svg:simple,scaleCount:0,shape};
  }
  return {svg,scaleCount:count,shape};
}
const api={render};if(typeof module!=='undefined')module.exports=api;else root.SpeciesRenderer=api;
})(typeof window!=='undefined'?window:this);

/* Species-specific projected skull details, using landmarks stored with the preset. */
(function(root){
function render(preset,shape,skin,cream,belly,rear){
 const h=shape.head,p=preset.artistic_parameters;
 if(!h)return '';
 const f=n=>Number(n).toFixed(2),L=h.length;
 const eye=h.eye;
 let small='';
 if(!h.shields.length || h.micro_scales)for(let y=-32,row=0;y<33;y+=4.1,row++)for(let x=2+(row%2)*2;x<L;x+=4.3){
  small+=`<path d="M${f(x-2)} ${f(y)} Q${f(x)} ${f(y-2.7)} ${f(x+2)} ${f(y)} Q${f(x+1.4)} ${f(y+2.5)} ${f(x)} ${f(y+3)} Q${f(x-1.4)} ${f(y+2.5)} ${f(x-2)} ${f(y)}Z"/>`;
 }
 let content=`<path d="${shape.headPath}" fill="url(#headVolume)"/>`;
 let glyph=`<path d="${h.labial_boundary||`M-3 3 Q${L*.35} 5 ${L*.65} 9 L${L+2} 5 L${L+2} 35 L-3 35Z`}" fill="${belly}" opacity="${h.lip?.68:.22}"/>`;
 if(p.head_style==='rectangular')glyph+=`<path d="M-2 -18 L17 -18 Q21 -1 13 7 L-2 8Z" fill="${cream}" opacity=".35"/>`;
 if(p.pattern==='gaboon' && p.head_pattern!=='nasal_leaf')glyph+=`<path d="M-2 -38 H${L+5} V4 Q${L*.5} 2 -2 -2Z" fill="${cream}" opacity=".85"/><path d="M5 -2 Q35 -3 63 -9" fill="none" stroke="#40362d" stroke-width="2.6"/><path d="M59 -20 L72 24 L77 24 L65 -21Z M68 -23 L83 17 L87 13 L74 -25Z" fill="#332e2a" opacity=".86"/>`;
 if(p.pit_present && p.pit_cheek_band!==false)glyph+=`<path d="M30 -1 L52 17 L61 13 L38 -7Z" fill="#4e4334"/><path d="M32 -3 L56 15" stroke="${cream}" stroke-width="2" fill="none"/>`;
 // Authored per-species pigment paths are independent of skull geometry.
 for(const mark of h.markings||[])glyph+=`<path d="${mark.path}" fill="${mark.fill||'none'}" stroke="${mark.stroke||'none'}" stroke-width="${mark.width||1}" opacity="${mark.opacity??1}"/>`;
 glyph+=`<g id="head-scale-detail" fill="none" stroke="#332d24" opacity=".25" stroke-width=".45">${small}</g>`;
 glyph+=`<g id="head-shields" fill="none" stroke="#3e392d" stroke-opacity=".4" stroke-width=".65">${h.shields.map(d=>`<path d="${d}"/>`).join('')}</g>`;
 glyph+=`<path id="jaw-seam" d="${h.jaw}" fill="none" stroke="#3a392d" stroke-opacity=".7" stroke-width=".65"/>`;
 if(rear){
  const pupil=p.pupil==='horizontal'?`<ellipse cx="${eye[0]}" cy="${eye[1]}" rx="${eye[2]*.86}" ry="${eye[3]*.27}" fill="#101b15"/>`:p.pupil==='vertical'?`<ellipse cx="${eye[0]}" cy="${eye[1]}" rx=".7" ry="${eye[3]*.86}" fill="#101b15"/>`:`<ellipse cx="${eye[0]}" cy="${eye[1]}" rx="${eye[2]*.66}" ry="${eye[3]*.73}" fill="#111b16"/>`;
  const iris=h.iris_color||(p.pattern==='edged_scales'?'#abb65e':p.head_style==='rectangular'?'#a47843':'#aba580');
  glyph+=`<g id="eyes"><ellipse cx="${eye[0]}" cy="${eye[1]}" rx="${eye[2]+.8}" ry="${eye[3]+.7}" fill="#373c2c"/><ellipse cx="${eye[0]}" cy="${eye[1]}" rx="${eye[2]}" ry="${eye[3]}" fill="${iris}"/>${pupil}<ellipse cx="${eye[0]-eye[2]*.24}" cy="${eye[1]-eye[3]*.32}" rx="${Math.min(.8,eye[2]*.12)}" ry="${Math.min(.8,eye[3]*.12)}" fill="#f1efda"/></g>`;
  glyph+=`<ellipse id="nostril" cx="${h.nostril[0]}" cy="${h.nostril[1]}" rx="${h.nostril[2]??1.3}" ry="${h.nostril[3]??.7}" fill="#383b2e"/>`;
  if(p.pit_present && h.pit)glyph+=`<ellipse id="heat-pit" cx="${h.pit[0]}" cy="${h.pit[1]}" rx="1.8" ry="1.25" fill="#262a22"/>`;
 }
 return `<defs><linearGradient id="headBlendGradient" gradientUnits="userSpaceOnUse" x1="${L*.72}" y1="0" x2="${L}" y2="0"><stop stop-color="white"/><stop offset="1" stop-color="black"/></linearGradient><mask id="headBlend" maskUnits="userSpaceOnUse" x="0" y="0" width="800" height="800"><g transform="${shape.headTransform}"><rect x="-5" y="-45" width="${L+12}" height="95" fill="url(#headBlendGradient)"/></g></mask></defs><g id="projected-head" clip-path="url(#headClip)" mask="url(#headBlend)">${content}<g transform="${shape.headTransform}">${glyph}</g></g>`;
}
if(typeof module!=='undefined')module.exports={render};else root.SpeciesHead={render};
})(typeof window!=='undefined'?window:this);

// Pattern and palette layers share a single continuous anatomy mask.
let view = 'back';
const drawing = document.querySelector('#drawing');
function render() {
  const rear=view==='back', width=Number(document.querySelector('#width').value);
  const skin=document.querySelector('#skinColor').value, ring=document.querySelector('#ringColor').value;
  const {points,path}=SnakeAnatomy.geometry(width);
  // Directional texture follows the local centreline; deliberately not diagnostic scale counts.
  let travelled=0, texture='';
  for(let i=1;i<points.length-1;i++) {
    const p=points[i], previous=points[i-1];
    travelled+=Math.hypot(p.x-previous.x,p.y-previous.y);
    if(travelled<10 || p.y<141 || p.r<6) continue;
    travelled=0;
    if(!rear && p.y<395) {
      texture+=`<path d="M${p.x-p.r} ${p.y} Q${p.x} ${p.y+4} ${p.x+p.r} ${p.y}"/>`;
      continue;
    }
    const angle=Math.atan2(p.ty,p.tx)*180/Math.PI-90;
    for(let across=-p.r+5;across<p.r-3;across+=9) {
      texture+=`<path transform="translate(${p.x} ${p.y}) rotate(${angle})" d="M${across-4} -2 Q${across} 4 ${across+4} -2"/>`;
    }
  }
  const centreline=points.map((p,i)=>`${i?'L':'M'}${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' ');
  drawing.innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="170 45 510 680" role="img" aria-labelledby="title desc">
  <title id="title">Naja kaouthia — ${rear?'dorsal':'ventral'} hood study</title>
  <desc id="desc">Continuous head, expanded hood, trunk and tapering tail in an open S pose. ${rear?'Single pale monocle on rear hood.':'Pale throat; rear monocle hidden.'} Hand-authored illustration, not calibrated anatomy.</desc>
  <defs>
    <path id="anatomy" d="${path}"/>
    <clipPath id="bodyMask"><use href="#anatomy"/></clipPath>
    <linearGradient id="volume" x1="0" x2="1"><stop stop-color="#16251b" stop-opacity=".28"/><stop offset=".32" stop-color="#fff3cf" stop-opacity=".06"/><stop offset=".62" stop-color="#fff3cf" stop-opacity=".18"/><stop offset="1" stop-color="#17261e" stop-opacity=".27"/></linearGradient>
    <linearGradient id="throat" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#ddcda6"/><stop offset=".7" stop-color="#c7b28a"/><stop offset="1" stop-color="${skin}"/></linearGradient>
  </defs>
  <g id="anatomy-layer"><use href="#anatomy" fill="${skin}"/></g>
  <g id="appearance-layers" clip-path="url(#bodyMask)">
    <use href="#anatomy" fill="url(#volume)"/>

    ${!rear?'<rect x="180" y="70" width="240" height="350" fill="url(#throat)"/>':''}
    <g id="marking-layer" data-surface="${rear?'dorsal':'ventral'}">
    ${rear?`<g id="monocle" transform="translate(300 220) scale(${width} 1)"><path d="M-3 -38 C-28 -39 -36 -20 -32 3 C-29 27 -12 40 3 38 C24 36 35 16 33 -5 C32 -28 19 -38 -3 -38Z" fill="#393c2c" stroke="${ring}" stroke-width="8"/><path d="M-2 -32 Q-20 -30 -23 -15" fill="none" stroke="#e8ddbc" stroke-opacity=".25" stroke-width="2"/></g>`:'<path d="M233 251 Q300 271 367 251 L357 275 Q300 293 243 275Z" fill="#3c3c2c"/><ellipse cx="252" cy="222" rx="8" ry="13" fill="#424031"/><ellipse cx="348" cy="222" rx="8" ry="13" fill="#424031"/>'}
    </g>
    <g id="texture-layer" fill="none" stroke="#182b23" stroke-width=".65" opacity=".15">${texture}</g>
    <g id="head-detail" fill="none" stroke="#27382b" stroke-width=".85" opacity=".5">
      ${rear?'<path d="M300 88 L300 99 M285 96 Q300 102 315 96 M281 107 Q289 114 300 112 Q311 114 319 107 M300 112 L300 128 M283 119 Q292 123 292 134 M317 119 Q308 123 308 134"/>':'<path d="M283 118 Q300 124 317 118 M288 95 Q300 89 312 95"/>'}
    </g>
    ${rear?'':'<g id="eyes"><ellipse cx="283" cy="105" rx="3.7" ry="4.7" fill="#a98945"/><ellipse cx="317" cy="105" rx="3.7" ry="4.7" fill="#a98945"/><circle cx="283" cy="105" r="2.6" fill="#17251e"/><circle cx="317" cy="105" r="2.6" fill="#17251e"/></g>'}
  </g>
  <use id="continuous-outline" href="#anatomy" fill="none" stroke="#354333" stroke-width="1.6" stroke-linejoin="round"/>
  <g id="construction-layer" visibility="${document.querySelector('#construction').checked?'visible':'hidden'}" fill="none" stroke="#4a83a8" stroke-width="1" stroke-dasharray="4 4"><path d="${centreline}"/></g>
  </svg>`;
  document.querySelector('#status').textContent=rear?'Rear hood · single monocle visible':'Front hood · dorsal monocle hidden';
  document.querySelector('#viewLabel').textContent=rear?'Dorsal hood / expanded display':'Ventral hood / expanded display';
  for(const id of ['back','front']) document.querySelector('#'+id).setAttribute('aria-pressed',String(view===id));
}
for(const id of ['back','front']) document.querySelector('#'+id).onclick=()=>{view=id;render();};
for(const id of ['width','skinColor','ringColor','construction']) document.querySelector('#'+id).oninput=render;
document.querySelector('#save').onclick=()=>{const url=URL.createObjectURL(new Blob([drawing.innerHTML],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download=`naja-kaouthia-${view}.svg`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
render();

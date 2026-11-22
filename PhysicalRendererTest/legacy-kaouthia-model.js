/* Anatomy + surface coordinates + pigment + scale geometry, generated without raster assets. */
const $=id=>document.getElementById(id);
let surface='dorsal', framing='full';
const defaults={width:'1',thickness:'1',skinColor:'#796246',ringColor:'#e0cea1',patternContrast:'1',scaleDetail:'1',ringSize:'1'};
const hexRGB=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
function shade(hex,factor){return '#'+hexRGB(hex).map(v=>Math.max(0,Math.min(255,Math.round(v*factor))).toString(16).padStart(2,'0')).join('');}
function createSurface(points){
  let length=0;
  const stations=points.map((p,i)=>{if(i)length+=Math.hypot(p.x-points[i-1].x,p.y-points[i-1].y);return {...p,s:length};});
  function at(s,u=0){
    s=Math.max(0,Math.min(length,s));
    let lo=0,hi=stations.length-1;
    while(hi-lo>1){let mid=(hi+lo)>>1;if(stations[mid].s<s)lo=mid;else hi=mid;}
    const a=stations[lo],b=stations[hi],t=(s-a.s)/Math.max(.00001,b.s-a.s);
    const r=a.r+(b.r-a.r)*t,nx=a.nx+(b.nx-a.nx)*t,ny=a.ny+(b.ny-a.ny)*t;
    return {x:a.x+(b.x-a.x)*t+nx*r*u,y:a.y+(b.y-a.y)*t+ny*r*u,r};
  }
  return {at,length};
}
function drawModel(){
  const hood=+$('width').value,thickness=+$('thickness').value,skin=$('skinColor').value,cream=$('ringColor').value;
  const contrast=+$('patternContrast').value,detail=+$('scaleDetail').value,ringSize=+$('ringSize').value;
  const rear=surface==='dorsal';
  const {points,path}=SnakeAnatomy.geometry(hood,thickness,surface),mesh=createSurface(points);
  const coord=(s,u)=>{const p=mesh.at(s,u);return `${p.x.toFixed(2)} ${p.y.toFixed(2)}`;};
  let scales='',seams='',plates='',count=0;
  // Staggered overlapping individual scales in anatomical coordinates, not a tiled image.
  const pitch=8.2/detail;
  for(let s=59,row=0;s<mesh.length-7;s+=pitch*.8,row++){
    const p=mesh.at(s),columns=Math.max(3,Math.round(2*p.r/pitch)+(row%2));
    for(let col=0;col<columns;col++){
      const u=-1+(col+.5)*2/columns;
      if(u>.98)continue;
      const half=1.08/columns;
      const d=`M${coord(s-pitch*.7,u)} Q${coord(s-pitch*.55,u-half)} ${coord(s,u-half)} Q${coord(s+pitch*.55,u-half*.9)} ${coord(s+pitch*.9,u)} Q${coord(s+pitch*.55,u+half*.9)} ${coord(s,u+half)} Q${coord(s-pitch*.55,u+half)} ${coord(s-pitch*.7,u)}Z`;
      const variation=Math.sin(row*37+col*19)*.035;
      const lighting=.68+.38*Math.sqrt(Math.max(0,1-u*u))-.13*u+variation;
      scales+=`<path d="${d}" fill="${shade(skin,lighting)}"/>`;
      const exposed=`M${coord(s,u-half)} Q${coord(s+pitch*.55,u-half*.9)} ${coord(s+pitch*.9,u)} Q${coord(s+pitch*.55,u+half*.9)} ${coord(s,u+half)}`;
      if(rear || p.y>=420 || Math.abs(u)>.84)seams+=`<path d="${exposed}"/>`;count++;
    }
    if(!rear && p.y<420){
      // Broad transverse ventral scutes; curve with the same anatomical surface.
      const d=`M${coord(s,-.82)} Q${coord(s+pitch*.6,0)} ${coord(s,.82)} L${coord(s+pitch*.78,.82)} Q${coord(s+pitch*1.3,0)} ${coord(s+pitch*.78,-.82)}Z`;
      plates+=`<path d="${d}" fill="${shade('#d8c7a2',.93+.04*Math.sin(row*.63))}" stroke="#68573b" stroke-opacity=".35" stroke-width=".45"/>`;
    }
  }
  const marking=rear?`<g id="monocle" transform="translate(300 221) scale(${hood*ringSize} ${ringSize})"><path d="M0 -39 C-24 -40 -34 -23 -34 -1 C-34 20 -18 40 0 40 C18 40 34 20 34 -1 C34 -23 24 -40 0 -39Z" fill="${shade(skin,.55)}" stroke="${cream}" stroke-width="9"/><path d="M-28 -13 Q-23 -24 -17 -27" fill="none" stroke="${shade(cream,.75)}" stroke-width="1.5" opacity=".65"/></g>`:`<path d="M180 264 Q300 289 420 264 L420 284 Q300 311 180 284Z" fill="${shade(skin,.48)}"/><g fill="${shade(skin,.5)}">${[-1,1].map(side=>[0,1,2,3].map(i=>`<path d="M-3 -7 Q-7 -3 -5 2 L-2 7 Q3 8 5 3 L4 -3 L1 -6Z" transform="translate(${300+side*(54-i*4)*hood} ${169+i*19+(side>0?4:0)}) rotate(${side*(15+i*7)}) scale(${hood*(.7+i*.11)} ${.7+(i%3)*.2})"/>`).join('')).join('')}</g>`;
  $('drawing').innerHTML=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="${framing==='hood'?'195 65 210 340':'185 55 465 660'}" role="img" aria-labelledby="modelTitle modelDescription">
  <title id="modelTitle">Procedural Naja kaouthia — ${surface}</title><desc id="modelDescription">Connected snake anatomy with generated overlapping scales, head shields and ${rear?'a single dorsal monocle':'ventral plates and throat markings'}. Illustrative proportions.</desc>
  <defs><path id="bodyGeometry" d="${path}"/><clipPath id="anatomyClip"><use href="#bodyGeometry"/></clipPath><linearGradient id="headVolume"><stop stop-color="${shade(skin,.6)}"/><stop offset=".45" stop-color="${shade(skin,1.18)}"/><stop offset="1" stop-color="${shade(skin,.7)}"/></linearGradient><linearGradient id="softVolume"><stop stop-color="#10251a" stop-opacity=".15"/><stop offset=".45" stop-color="#ffefd1" stop-opacity=".04"/><stop offset="1" stop-color="#14251b" stop-opacity=".1"/></linearGradient></defs>
  <g id="anatomy-layer"><use href="#bodyGeometry" fill="${shade(skin,.75)}"/></g>
  <g clip-path="url(#anatomyClip)">
    <g id="dorsal-scale-fills">${scales}</g><g id="ventral-plates">${plates}</g>
    <g id="pigment-pattern">${marking}</g>
    <g id="scale-seams" fill="none" stroke="#342c20" stroke-width=".42" opacity="${.44*contrast}">${seams}</g>
    <g id="scale-highlights" fill="none" stroke="#fff1c9" stroke-width=".22" opacity=".18" transform="translate(-.3 -.5)">${seams}</g>
    <path d="M260 78 L337 78 L337 128 Q300 143 260 128Z" fill="url(#headVolume)"/>
    <g id="head-shields" fill="none" stroke="${shade(skin,.48)}" stroke-width=".75" stroke-linejoin="round">
    ${rear?'<path d="M291 87 L289 95 L300 100 L311 95 L309 87 M300 100 L300 114 M281 101 L288 102 L292 112 L287 122 M319 101 L312 102 L308 112 L313 122 M292 112 Q300 116 308 112 M287 122 L291 134 M313 122 L309 134 M300 114 L300 131"/>':'<path d="M274 96 L285 98 L293 94 L289 91 M285 98 L289 105 L301 106 L309 97 L293 94 M301 106 L311 114 L323 110 M311 114 L313 123 M268 105 L282 111 L304 114 M276 109 L276 112 M283 111 L283 114 M291 112 L291 115 M299 113 L299 116"/>'}</g>
    ${rear?'':'<g id="eyes"><path d="M304 101 Q308 97 312 100 Q313 103 309 105 Q305 106 304 101Z" fill="#a58c56" stroke="#443622" stroke-width=".8"/><circle cx="308.5" cy="101.7" r="2.1" fill="#17251c"/><circle cx="307.8" cy="100.8" r=".45" fill="#e7ddc1"/><ellipse cx="275" cy="100" rx="1.25" ry=".7" fill="#483825" transform="rotate(15 275 100)"/></g>'}
    <use href="#bodyGeometry" fill="url(#softVolume)"/>
  </g><use href="#bodyGeometry" fill="none" stroke="${shade(skin,.48)}" stroke-width="1.1"/>
  </svg>`;
  $('ringColor').disabled=!rear; $('ringSize').disabled=!rear;
  $('viewLabel').textContent=`${rear?'Dorsal':'Front three-quarter'} · ${framing==='hood'?'hood detail':'full body'}`;
  $('status').textContent=`${count.toLocaleString()} generated scale shapes · artistic detail setting`;
  for(const id of ['back','front'])$(id).setAttribute('aria-pressed',String((id==='back')===rear));
  for(const id of ['full','hood'])$(id).setAttribute('aria-pressed',String(framing===id));
}
for(const id of Object.keys(defaults))$(id).oninput=drawModel;
$('back').onclick=()=>{surface='dorsal';drawModel();};$('front').onclick=()=>{surface='ventral';drawModel();};
$('full').onclick=()=>{framing='full';drawModel();};$('hood').onclick=()=>{framing='hood';drawModel();};
$('resetTexture').onclick=()=>{for(const [id,value] of Object.entries(defaults))$(id).value=value;drawModel();};
$('save').onclick=()=>{const url=URL.createObjectURL(new Blob([$('drawing').innerHTML],{type:'image/svg+xml'}));const link=document.createElement('a');link.href=url;link.download=`naja-kaouthia-procedural-${surface}-${framing}.svg`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
for(const [id,value] of Object.entries(defaults))$(id).value=value;
drawModel();

/* Shared, illustrative 2D controls. No trained venom-to-trait model. */
(function(root){
'use strict';
const TRAITS=['headWidth','headLength','bodyWidth','hood','diamond','monocle','rattle','tailTaper'];
// These are hand-authored design coordinates, not measured anatomy or labels.
// See README for the preset sources and the limits of these examples.
const REFERENCES={
  diamondback:{name:'Western diamondback',species:'Crotalus atrox',traits:{headWidth:.88,headLength:.52,bodyWidth:.82,hood:0,diamond:1,monocle:0,rattle:1,tailTaper:.72},skin:'#ad9675',marking:'#594732',highlight:'#e2d2aa'},
  cobra:{name:'Monocled cobra',species:'Naja kaouthia',traits:{headWidth:.47,headLength:.57,bodyWidth:.47,hood:1,diamond:0,monocle:1,rattle:0,tailTaper:.45},skin:'#796448',marking:'#463b2c',highlight:'#e0cf9f'},
  mamba:{name:'Black mamba',species:'Dendroaspis polylepis',traits:{headWidth:.37,headLength:.82,bodyWidth:.28,hood:0,diamond:0,monocle:0,rattle:0,tailTaper:.25},skin:'#858477',marking:'#4b4b42',highlight:'#c6bfa4'}
};
const clamp=(n,a=0,b=1)=>Math.min(b,Math.max(a,n));
const fmt=n=>Number(n).toFixed(2);
const rgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
const hex=cs=>'#'+cs.map(x=>Math.round(clamp(x,0,255)).toString(16).padStart(2,'0')).join('');
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
function blend(weights){
  const entries=Object.keys(REFERENCES).map(id=>({id,w:Number(weights[id])})).filter(x=>Number.isFinite(x.w)&&x.w>0);
  const total=entries.reduce((s,x)=>s+x.w,0);if(!total)return null;
  const influence=entries.map(x=>({id:x.id,weight:x.w/total}));
  const traits=Object.fromEntries(TRAITS.map(k=>[k,influence.reduce((s,x)=>s+x.weight*REFERENCES[x.id].traits[k],0)]));
  const colors=Object.fromEntries(['skin','marking','highlight'].map(k=>[k,hex([0,1,2].map(i=>influence.reduce((s,x)=>s+x.weight*rgb(REFERENCES[x.id][k])[i],0)))]));
  return {traits,colors,influence,manualTraits:[]};
}
function geometry(input){
  const t=Object.fromEntries(TRAITS.map(k=>[k,clamp(Number.isFinite(input[k])?input[k]:0)]));
  const headR=15+16*t.headWidth, headL=46+24*t.headLength, start=50+headL;
  const center=x=>150+14*Math.sin(Math.PI*(x-start)/(650-start))*Math.sin(2*Math.PI*(x-start)/(650-start));
  const smooth=(a,b,x)=>{const z=clamp((x-a)/(b-a));return z*z*(3-2*z);};
  const base=9+19*t.bodyWidth, neck=8+5*t.bodyWidth;
  const radius=x=>{const u=clamp((x-start)/(650-start));
    const trunk=neck+(base-neck)*smooth(0,.19,u);
    const hood=42*t.hood*Math.exp(-(((u-.14)/.095)**2))*smooth(0,.045,u);
    const taperStart=.59+.17*(1-t.tailTaper);
    return Math.max(0,(trunk+hood)*(1-smooth(taperStart,1,u)));
  };
  const points=Array.from({length:105},(_,i)=>{const x=start+(650-start)*i/104;return {x,y:center(x),r:radius(x)};});
  const upper=points.map(p=>`${fmt(p.x)} ${fmt(p.y-p.r)}`).join(' L');
  const lower=points.slice().reverse().map(p=>`${fmt(p.x)} ${fmt(p.y+p.r)}`).join(' L');
  const neckY=center(start),nr=radius(start);
  const path=`M50 150 C50 ${fmt(150-headR*.35)} ${fmt(50+headL*.15)} ${fmt(150-headR*.50)} ${fmt(50+headL*.35)} ${fmt(150-headR*.55)} C${fmt(50+headL*.52)} ${fmt(150-headR*.66)} ${fmt(50+headL*.60)} ${fmt(150-headR)} ${fmt(50+headL*.75)} ${fmt(150-headR*.90)} C${fmt(50+headL*.87)} ${fmt(150-headR*.80)} ${fmt(start-headL*.10)} ${fmt(neckY-nr)} ${fmt(start)} ${fmt(neckY-nr)} L${upper} L${lower} C${fmt(start-headL*.10)} ${fmt(neckY+nr)} ${fmt(50+headL*.87)} ${fmt(150+headR*.80)} ${fmt(50+headL*.75)} ${fmt(150+headR*.90)} C${fmt(50+headL*.60)} ${fmt(150+headR)} ${fmt(50+headL*.52)} ${fmt(150+headR*.66)} ${fmt(50+headL*.35)} ${fmt(150+headR*.55)} C${fmt(50+headL*.15)} ${fmt(150+headR*.50)} 50 ${fmt(150+headR*.35)} 50 150 Z`;
  return {traits:t,path,points,start,headR,headL,center,radius};
}
function render(data,options={}){
  if(!data||!data.traits||!data.colors)return null;
  const g=geometry(data.traits),t=g.traits,{skin,marking,highlight}=data.colors;
  const surface=options.surface==='ventral'?'ventral':'dorsal',rear=surface==='dorsal';
  const bodyColor=rear?skin:(data.colors.belly||skin);
  // Fixed-position motifs and their opacity are continuous control values.
  const diamonds=[];for(let x=235;x<585;x+=48){const y=g.center(x),r=g.radius(x)*.80;
    diamonds.push(`<path d="M${fmt(x-21)} ${fmt(y)} L${fmt(x)} ${fmt(y-r)} L${fmt(x+21)} ${fmt(y)} L${fmt(x)} ${fmt(y+r)} Z" fill="${marking}" stroke="${highlight}" stroke-width="2"/>`);
  }
  const hcx=g.start+(650-g.start)*.14,hcy=g.center(hcx),hoodRy=Math.max(8,g.radius(hcx)*.6);
  const hoodMark=`<ellipse cx="${fmt(hcx)}" cy="${fmt(hcy)}" rx="17" ry="${fmt(hoodRy)}" fill="${marking}" stroke="${highlight}" stroke-width="4"/>`;
  const eyeX=50+g.headL*.52, eyeY=g.headR*.56;
  const rattleSize=5*t.rattle, rattle=Array.from({length:4},(_,i)=>`<ellipse cx="${fmt(650+t.rattle*(3+i*6))}" cy="150" rx="${fmt(rattleSize*.65)}" ry="${fmt(rattleSize*(1-i*.1))}" fill="${i%2?marking:highlight}" stroke="${marking}" stroke-width=".7"/>`).join('');
  const metadata={type:'shared_control_illustration',surface,traits:t,influence:data.influence||[],manualTraits:data.manualTraits||[],venomContext:data.venomContext||null,note:data.venomContext?.kind==='direct_image_trait_model'?'Experimental image-trait model output; not a validated biological prediction.':'Hand-authored coordinates; not a biological prediction or trained image model.'};
  const plates=[];if(!rear)for(let x=g.start+8;x<640;x+=10){const y=g.center(x),r=g.radius(x);plates.push(`<path d="M${fmt(x)} ${fmt(y-r)} Q${fmt(x+3)} ${fmt(y)} ${fmt(x)} ${fmt(y+r)}" fill="none" stroke="#594e3b" stroke-opacity=".35" stroke-width=".8"/>`);}
  const visiblePattern=rear?`<g opacity="${fmt(t.diamond)}">${diamonds.join('')}</g><g opacity="${fmt(t.monocle*t.hood)}">${hoodMark}</g><path d="${g.path}" fill="url(#snake-scales)"/>`:`<g id="ventral-plates">${plates.join('')}</g>`;
  const eyes=rear?`<g fill="#262920"><ellipse cx="${fmt(eyeX)}" cy="${fmt(150-eyeY)}" rx="2.4" ry="1.9"/><ellipse cx="${fmt(eyeX)}" cy="${fmt(150+eyeY)}" rx="2.4" ry="1.9"/></g>`:'';
  return {geometry:g,svg:`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 70 720 170" role="img" aria-labelledby="title desc"><title id="title">Shared-shape snake concept</title><desc id="desc">An illustrative ${surface} snake with independently controlled body, head, hood, markings, and tail.</desc><metadata>${escape(JSON.stringify(metadata))}</metadata><defs><clipPath id="snake-clip"><path d="${g.path}"/></clipPath><pattern id="snake-scales" width="10" height="7" patternUnits="userSpaceOnUse"><path d="M0 0 Q5 6 10 0 M-5 3.5 Q0 9 5 3.5 M5 3.5 Q10 9 15 3.5" fill="none" stroke="#241e19" stroke-opacity=".25" stroke-width=".5"/></pattern><linearGradient id="volume" x1="0" x2="0" y1="0" y2="1"><stop stop-color="#ffffff" stop-opacity=".18"/><stop offset=".5" stop-color="#ffffff" stop-opacity="0"/><stop offset="1" stop-color="#17110b" stop-opacity=".24"/></linearGradient></defs><path d="${g.path}" fill="${bodyColor}"/><g clip-path="url(#snake-clip)">${visiblePattern}<path d="${g.path}" fill="url(#volume)"/></g><path d="${g.path}" fill="none" stroke="#403a2c" stroke-width="1.6" stroke-linejoin="round"/>${eyes}<g opacity="${fmt(t.rattle)}">${rattle}</g></svg>`};
}
const api={TRAITS,REFERENCES,blend,geometry,render};
if(typeof module!=='undefined')module.exports=api;else root.SharedMorphology=api;
})(typeof window!=='undefined'?window:this);

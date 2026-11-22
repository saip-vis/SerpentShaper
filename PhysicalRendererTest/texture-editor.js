// Photo-guided raster appearance editor. No training, inference or anatomical segmentation.
const textureImage = new Image();
const textureCanvas = document.createElement('canvas');
textureCanvas.setAttribute('role','img');
textureCanvas.setAttribute('aria-label','Editable photo-guided monocled cobra illustration');
textureCanvas.style.cssText='width:100%;height:auto;display:block;margin:20px 0';
const ctx = textureCanvas.getContext('2d');
let sourcePixels, textureView='plate', pendingFrame;
document.querySelector('#drawing').replaceChildren(textureCanvas);
const rgb = hex => [1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
const smooth = (a,b,x) => {const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t);};
function warpX(x,y,width) {
  // Smooth local horizontal deformation, zero outside hood support. Head/trunk stay fixed.
  const regions=[{cx:865,cy:252,rx:255,ry:188},{cx:1337,cy:390,rx:195,ry:258}];
  let result=x;
  for(const r of regions) {
    const influence=(1-smooth(.55,1,Math.abs(x-r.cx)/r.rx))*(1-smooth(.45,1,Math.abs(y-r.cy)/r.ry));
    result+=(x-r.cx)*(width-1)*influence;
  }
  return result;
}
function renderTexture() {
  if(!sourcePixels)return;
  document.querySelector('#exportLink')?.remove();
  const w=sourcePixels.width,h=sourcePixels.height,src=sourcePixels.data;
  const frame=new ImageData(w,h), pixels=frame.data;
  const skin=rgb(document.querySelector('#skinColor').value),base=rgb('#827451');
  const ring=rgb(document.querySelector('#ringColor').value),ringBase=rgb('#ded0a5');
  const width=Number(document.querySelector('#width').value), contrast=Number(document.querySelector('#patternContrast').value);
  for(let y=0;y<h;y++)for(let x=0;x<w;x++) {
    // Invert the forward deformation with fixed-point refinement; interpolate texture continuously.
    let sx=x;
    for(let n=0;n<7;n++)sx=x-(warpX(sx,y,width)-sx);
    sx=Math.max(0,Math.min(w-1.001,sx));
    const ix=Math.floor(sx),f=sx-ix,i=(y*w+ix)*4,o=(y*w+x)*4;
    let r=src[i]*(1-f)+src[i+4]*f,g=src[i+1]*(1-f)+src[i+5]*f,b=src[i+2]*(1-f)+src[i+6]*f;
    const lum=.2126*r+.7152*g+.0722*b, max=Math.max(r,g,b),min=Math.min(r,g,b);
    const saturation=(max-min)/Math.max(1,max);
    const ringRegion=((sx-1337)/86)**2+((y-380)/112)**2;
    const ringMask=(1-smooth(.8,1.15,ringRegion))*smooth(140,195,lum)*smooth(.06,.15,saturation);
    // Soft masks preserve white background, pale ventral scutes, dark interstitial lines and highlights.
    const bodyMask=smooth(.12,.3,saturation)*(1-smooth(170,225,lum))*(1-ringMask);
    const original=[r,g,b];
    for(let c=0;c<3;c++) {
      let value=original[c]*(1+bodyMask*(skin[c]/base[c]-1)+ringMask*(ring[c]/ringBase[c]-1));
      value+=(lum-120)*(contrast-1)*bodyMask;
      pixels[o+c]=Math.max(0,Math.min(255,value));
    }
    pixels[o+3]=255;
  }
  const buffer=document.createElement('canvas');buffer.width=w;buffer.height=h;buffer.getContext('2d').putImageData(frame,0,0);
  const crop=textureView==='front'?[0,0,1135,1024]:textureView==='back'?[1115,80,421,820]:[0,0,w,h];
  textureCanvas.width=crop[2];textureCanvas.height=crop[3];
  ctx.drawImage(buffer,...crop,0,0,crop[2],crop[3]);
  document.querySelector('#viewLabel').textContent=textureView==='plate'?'Front and rear hood · editable texture':textureView==='front'?'Front / three-quarter · editable texture':'Rear hood · editable texture';
  document.querySelector('#status').textContent='Edits applied to the detailed illustration.';
  for(const id of ['front','back','plate'])document.querySelector('#'+id).setAttribute('aria-pressed',String(textureView===id));
}
function requestTextureRender(){cancelAnimationFrame(pendingFrame);pendingFrame=requestAnimationFrame(renderTexture);}
for(const id of ['width','skinColor','ringColor','patternContrast'])document.querySelector('#'+id).oninput=requestTextureRender;
for(const id of ['front','back','plate'])document.querySelector('#'+id).onclick=()=>{textureView=id;renderTexture();};
document.querySelector('#resetTexture').onclick=()=>{
  for(const [id,value] of Object.entries({width:'1',skinColor:'#827451',ringColor:'#ded0a5',patternContrast:'1'}))document.querySelector('#'+id).value=value;
  renderTexture();
};
let exportUrl;
document.querySelector('#save').onclick=()=>{
  textureCanvas.toBlob(blob=>{
    if(!blob){document.querySelector('#status').textContent='PNG export failed; try again.';return;}
    if(exportUrl)URL.revokeObjectURL(exportUrl);
    exportUrl=URL.createObjectURL(blob);
    let link=document.querySelector('#exportLink');
    if(!link){link=document.createElement('a');link.id='exportLink';link.className='asset-download';document.querySelector('#save').after(link);}
    link.href=exportUrl;link.download=`naja-kaouthia-edited-${textureView}.png`;link.textContent='Save prepared PNG';
    document.querySelector('#status').textContent='PNG export ready. Use Save prepared PNG below.';
  },'image/png');
};
textureImage.onload=()=>{
  const c=document.createElement('canvas');c.width=textureImage.naturalWidth;c.height=textureImage.naturalHeight;
  const context=c.getContext('2d');context.drawImage(textureImage,0,0);sourcePixels=context.getImageData(0,0,c.width,c.height);renderTexture();
};
textureImage.src=window.SERPENT_TEXTURE_SOURCE;

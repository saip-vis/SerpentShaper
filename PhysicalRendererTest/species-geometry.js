/* Projected artistic geometry, with independently authored head and taper profiles. */
(function(root){
const legacy=typeof module!=='undefined'?require('./anatomy.js'):root.SnakeAnatomy;
const cubic=(a,b,c,d,t)=>.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
function sampleBody(a, roundedTip=false){
 const delta=a.slice(1).map((k,i)=>k[2]-a[i][2]);
 const slopes=a.map((_,i)=>i===0?delta[0]:i===a.length-1?delta.at(-1):delta[i-1]*delta[i]<=0?0:2*delta[i-1]*delta[i]/(delta[i-1]+delta[i]));
 const points=[];
 for(let i=0;i<a.length-1;i++)for(let j=0;j<24;j++){
  const t=j/24,b=a[i],c=a[i+1],aa=i===0?[2*b[0]-c[0],2*b[1]-c[1]]:a[i-1],d=i+2>=a.length?[2*c[0]-b[0],2*c[1]-b[1]]:a[i+2];
  const r=(2*t*t*t-3*t*t+1)*b[2]+(t*t*t-2*t*t+t)*slopes[i]+(-2*t*t*t+3*t*t)*c[2]+(t*t*t-t*t)*slopes[i+1];
  points.push({x:cubic(aa[0],b[0],c[0],d[0],t),y:cubic(aa[1],b[1],c[1],d[1],t),r:roundedTip && i===a.length-2?b[2]*Math.sqrt(Math.max(0,1-t*t)):Math.max(0,r)});
 }
 const last=a.at(-1);points.push({x:last[0],y:last[1],r:0});
 return normals(points);
}
function normals(points){points.forEach((p,i)=>{const a=points[Math.max(0,i-1)],b=points[Math.min(points.length-1,i+1)],l=Math.hypot(b.x-a.x,b.y-a.y);p.tx=(b.x-a.x)/l;p.ty=(b.y-a.y)/l;p.nx=-p.ty;p.ny=p.tx;});return points;}
const pathOf=o=>o.map((p,i)=>`${i?'L':'M'}${p[0].toFixed(3)},${p[1].toFixed(3)}`).join(' ')+'Z';
function geometry(preset, options={}){
 const p=preset.artistic_parameters,width=options.width??1,thickness=options.thickness??1;
 if(p.body_plan==='cobra'){
  const old=legacy.geometry(width,thickness*p.body_build,options.surface||'dorsal',p.front_head_profile);
  if(!p.hood_profile)return old;
  const knots=p.hood_profile;
  // Match endpoint slopes through the same monotone cubic rule used for the body envelope.
  const slopes=knots.map((k,i)=>{
   const before=i?(k[1]-knots[i-1][1])/(k[0]-knots[i-1][0]):null;
   const after=i<knots.length-1?(knots[i+1][1]-k[1])/(knots[i+1][0]-k[0]):null;
   return before===null?after:after===null?before:before*after<=0?0:2*before*after/(before+after);
  });
  function radius(y){let i=0;while(i<knots.length-2&&y>knots[i+1][0])i++;const a=knots[i],b=knots[i+1],h=b[0]-a[0],t=(y-a[0])/h;return (2*t**3-3*t*t+1)*a[1]+(t**3-2*t*t+t)*h*slopes[i]+(-2*t**3+3*t*t)*b[1]+(t**3-t*t)*h*slopes[i+1];}
  const smooth=(a,b,x)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t);};
  if(p.cobra_profile_direct){
   const hood=old.points.filter(q=>q.y>=144 && q.y<=351);
   function oldRadius(y){let i=0;while(i<hood.length-2&&hood[i+1].y<y)i++;const a=hood[i],b=hood[i+1],t=Math.max(0,Math.min(1,(y-a.y)/(b.y-a.y)));return a.r+(b.r-a.r)*t;}
   // Match the legacy neck and trunk exactly at the ends. Do not blend back to
   // the much wider legacy hood in between, which caused shoulder pinches.
   const start=145,end=350,left=oldRadius(start)-radius(start)*width,right=oldRadius(end)-radius(end)*width;
   const desired=y=>radius(y)*width+left*(1-smooth(start,175,y))+right*smooth(320,end,y);
   const points=old.points.map(q=>q.y>start&&q.y<end?{...q,r:desired(q.y)}:{...q});
   const outline=old.outline.map(q=>q[1]>start&&q[1]<end?[300+(q[0]-300)*desired(q[1])/oldRadius(q[1]),q[1]]:q);
   return {points,outline,path:pathOf(outline)};
  }
  const points=old.points.map((point,i)=>{
   if(point.y<=145||point.y>=350)return {...point};
   const fade=smooth(145,175,point.y)*(1-smooth(310,350,point.y));
   const desired=radius(point.y)*width;
   return {...point,r:point.r+(desired-point.r)*fade};
  });
  // Transform outline through corresponding y stations so the custom front skull remains intact.
  const factor=y=>{
   if(y<=145||y>=350)return 1;
   let nearest=0,d=Infinity;for(let i=0;i<old.points.length;i++){const dd=Math.abs(old.points[i].y-y);if(dd<d){d=dd;nearest=i;}}
   return points[nearest].r/old.points[nearest].r;
  };
  const outline=old.outline.map(q=>{
   const headFade=options.surface==='ventral'&&p.front_head_width ? 1-smooth(115,145,q[1]) : 0;
   const headFactor=1+(p.front_head_width-1||0)*headFade;
   return [300+(q[0]-300)*factor(q[1])*headFactor,q[1]];
  });
  return {points,outline,path:pathOf(outline)};
 }
 const h=p.head_geometry,angle=h.angle_degrees*Math.PI/180,cos=Math.cos(angle),sin=Math.sin(angle),origin=h.origin;
 const transform=(x,y)=>[origin[0]+cos*x-sin*y,origin[1]+sin*x+cos*y];
 const attach=transform(h.length,0),neck=h.neck*thickness;
 const lead=[attach[0]+cos*20,attach[1]+sin*20,neck];
 // A station behind the head can be far from the lead too. Require forward
 // progress along the attachment tangent to avoid folding the neck backwards.
 const firstStation=p.body_stations.findIndex(([x,y])=>(x-lead[0])*cos+(y-lead[1])*sin>=20);
 const stations=p.body_stations.slice(firstStation);
 const anchors=[[...attach,neck],lead,...stations.map(([x,y,r])=>[x,y,r*thickness])];
 const points=sampleBody(anchors,p.tail_type==='paddle');
 // Exact attachment tangent prevents a visible seam between the authored head and swept body.
 points[0].tx=cos;points[0].ty=sin;points[0].nx=-sin;points[0].ny=cos;
 function side(segments){const out=[];for(const seg of segments)for(let j=out.length?1:0;j<=24;j++){
  const t=j/24,v=1-t;const x=v**3*seg[0]+3*v*v*t*seg[2]+3*v*t*t*seg[4]+t**3*seg[6];
  let y=v**3*seg[1]+3*v*v*t*seg[3]+3*v*t*t*seg[5]+t**3*seg[7];
  const f=Math.max(0,Math.min(1,(x/h.length-.72)/.28));y*=1+(thickness-1)*f*f*(3-2*f);
  out.push(transform(x,y));
 }return out;}
 const lower=side(h.lower),upper=side(h.upper),bodySide=d=>points.map(q=>[q.x+d*q.nx*q.r,q.y+d*q.ny*q.r]);
 const outline=[...lower,...bodySide(1).slice(1),...bodySide(-1).slice(1).reverse(),...upper.reverse()];
 const headOutline=[...lower,...upper];
 return {points,outline,path:pathOf(outline),headOutline,headPath:pathOf(headOutline),headTransform:`translate(${origin[0]} ${origin[1]}) rotate(${h.angle_degrees})`,head:h};
}
function surface(points){let length=0;const stations=points.map((p,i)=>{if(i)length+=Math.hypot(p.x-points[i-1].x,p.y-points[i-1].y);return {...p,s:length};});
 function at(s,u=0){s=Math.max(0,Math.min(length,s));let lo=0,hi=stations.length-1;while(hi-lo>1){const mid=(hi+lo)>>1;if(stations[mid].s<s)lo=mid;else hi=mid;}
 const a=stations[lo],b=stations[hi],t=(s-a.s)/Math.max(.00001,b.s-a.s),r=a.r+(b.r-a.r)*t;
 return {x:a.x+(b.x-a.x)*t+(a.nx+(b.nx-a.nx)*t)*r*u,y:a.y+(b.y-a.y)*t+(a.ny+(b.ny-a.ny)*t)*r*u,r,tx:a.tx+(b.tx-a.tx)*t,ty:a.ty+(b.ty-a.ty)*t};}
 return {length,at};}
const api={geometry,surface};if(typeof module!=='undefined')module.exports=api;else root.SpeciesGeometry=api;
})(typeof window!=='undefined'?window:this);

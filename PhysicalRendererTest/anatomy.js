/* Continuous, unmeasured illustration geometry. No species measurements inferred. */
(function (root) {
  const anchors = [
    [300,83,0],[300,88,14],[300,99,20],[300,113,23],[300,128,19],
    [300,145,28],[300,178,57],[300,220,78],[300,260,67],
    [300,305,40],[300,350,24],[304,395,23],
    [326,441,24],[390,471,26],[480,480,27],[546,508,26],
    [553,547,24],[501,575,22],[413,582,20],[324,592,18],
    [280,621,15],[304,653,12],[379,674,9],[471,678,6],
    [555,668,3],[622,644,0]
  ];
  function geometry(hoodWidth = 1, bodyThickness = 1, view = 'dorsal', headProfile = null) {
    const profile = anchors;
    const knots = profile.map((a, i) => ({x:a[0], y:a[1], r:a[2] * (a[1] >= 178 && a[1] <= 305 ? hoodWidth : a[1] >= 350 ? bodyThickness : 1)}));
    // Monotone cubic radius interpolation avoids scallops at width anchors.
    const delta = knots.slice(1).map((p,i)=>p.r-knots[i].r);
    const slopes = knots.map((p,i)=> {
      if(i===0) return delta[0];
      if(i===knots.length-1) return delta[delta.length-1];
      return delta[i-1]*delta[i]<=0 ? 0 : 2*delta[i-1]*delta[i]/(delta[i-1]+delta[i]);
    });
    const points = [];
    const cubic = (a,b,c,d,t) => .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
    for(let i=0;i<knots.length-1;i++) {
      const a=knots[Math.max(0,i-1)], b=knots[i], c=knots[i+1], d=knots[Math.min(knots.length-1,i+2)];
      for(let j=0;j<20;j++) {
        const t=j/20;
        const radius=(2*t*t*t-3*t*t+1)*b.r+(t*t*t-2*t*t+t)*slopes[i]+(-2*t*t*t+3*t*t)*c.r+(t*t*t-t*t)*slopes[i+1];
        const y=cubic(a.y,b.y,c.y,d.y,t);
        points.push({x:y<=350 && (view !== 'ventral' || y>=145) ? 300 : cubic(a.x,b.x,c.x,d.x,t),y,
          r:i===0 ? c.r*Math.sqrt(Math.max(0,1-((88-y)/5)**2)) : Math.max(0,radius)});
      }
    }
    points.push(knots[knots.length-1]);
    points.forEach((p,i)=>{
      const a=points[Math.max(0,i-1)], b=points[Math.min(points.length-1,i+1)];
      const length=Math.hypot(b.x-a.x,b.y-a.y);
      p.tx=(b.x-a.x)/length;p.ty=(b.y-a.y)/length;
      p.nx=-p.ty;p.ny=p.tx;
    });
    const side = direction => points.map(p=>[p.x+direction*p.nx*p.r,p.y+direction*p.ny*p.r]);
    let outline = [...side(1),...side(-1).reverse()];
    if(view === 'ventral') {
      // A flattened three-quarter skull joins the same hood at y=145.
      const sample=(a,b,c,d)=>Array.from({length:21},(_,i)=>{
        const t=i/20,v=1-t;return [v*v*v*a[0]+3*v*v*t*b[0]+3*v*t*t*c[0]+t*t*t*d[0],v*v*v*a[1]+3*v*v*t*b[1]+3*v*t*t*c[1]+t*t*t*d[1]];
      });
      const standard={left:[[[288,93],[277,93],[267,96],[267,102]],[[267,102],[267,110],[282,113],[289,118]],[[289,118],[292,127],[281,140],[272,145]]],right:[[[288,93],[303,85],[327,92],[329,107]],[[329,107],[330,122],[319,134],[328,145]]]};
      const drawSide=segments=>segments.flatMap((segment,i)=>sample(...segment).slice(i?1:0));
      const left=drawSide(headProfile?.left||standard.left),right=drawSide(headProfile?.right||standard.right);
      const start=points.findIndex(p=>p.y>=145);
      outline=[...left,...side(1).slice(start+1),...side(-1).slice(start+1).reverse(),...right.reverse()];
    }
    const fmt = n=>n.toFixed(2);
    return {points, outline, path:outline.map((p,i)=>(i?'L':'M')+fmt(p[0])+','+fmt(p[1])).join(' ')+'Z'};
  }
  const api = {geometry};
  if(typeof module !== 'undefined') module.exports = api;
  else root.SnakeAnatomy = api;
})(typeof window !== 'undefined' ? window : this);

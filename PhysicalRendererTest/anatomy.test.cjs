const assert = require('node:assert/strict');
const {geometry} = require('./anatomy.js');
const cross = (a,b,c) => (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
function intersects(a,b,c,d) {
  return cross(a,b,c)*cross(a,b,d)<-1e-10 && cross(c,d,a)*cross(c,d,b)<-1e-10;
}
for(const view of ['dorsal','ventral']) for(let step=80; step<=115; step++) for(const thickness of [.85,1,1.1]) {
  const g=geometry(step/100,thickness,view);
  assert.equal((g.path.match(/M/g)||[]).length,1,'one connected silhouette');
  assert.ok(g.path.endsWith('Z'),'closed outline');
  assert.equal(g.points[0].r,0);
  assert.equal(g.points.at(-1).r,0,'tail tapers to zero');
  assert.ok(g.points.every(p=>[p.x,p.y,p.r,p.nx,p.ny].every(Number.isFinite)));
  const o=g.outline;
  for(let i=0;i<o.length-1;i++) for(let j=i+2;j<o.length-1;j++) {
    assert.ok(!intersects(o[i],o[i+1],o[j],o[j+1]),`outline crosses itself at width ${step/100}: ${i}, ${j}`);
  }
  for(const p of g.points.filter(p=>p.y>=150 && p.y<=345)) {
    assert.equal(p.x,300,'hood centreline stays on symmetry axis');
    assert.ok(Math.abs(p.nx+1)<1e-9 && Math.abs(p.ny)<1e-9,'hood normals are horizontal');
  }
  const baseline=geometry(1,thickness,view);
  for(let i=0;i<g.points.length;i++) {
    assert.equal(g.points[i].x,baseline.points[i].x,'hood control preserves centreline');
    assert.equal(g.points[i].y,baseline.points[i].y);
    if(g.points[i].y>395) assert.equal(g.points[i].r,baseline.points[i].r,'hood changes do not reshape trunk');
  }
}
console.log('Geometry passed: 216 view/hood/thickness combinations; closed, finite, non-crossing outlines and stable trunk.');

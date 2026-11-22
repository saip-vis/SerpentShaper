const assert=require('node:assert/strict'),fs=require('node:fs');
const {render}=require('./species-renderer.js');
const bundle=JSON.parse(fs.readFileSync(__dirname+'/presets/species-presets.json'));
assert.ok(bundle.presets.length>=8);
assert.equal(new Set(bundle.presets.map(p=>p.species_id)).size,bundle.presets.length);
const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
let cases=0;
for(const p of bundle.presets){
  const base=render(p);
  assert.ok(!base.svg.includes('<image'),'procedural rendering cannot embed rasters');
  assert.ok(base.svg.includes(p.source_species_name));
  assert.ok(base.svg.includes(p.species_id));
  assert.ok(base.scaleCount>200);
  assert.equal(render(p,{skinColor:'#457758'}).shape.path,base.shape.path);
  assert.equal(render(p).svg,base.svg,'deterministic output');
  const before=JSON.stringify(p);
  for(const surface of ['dorsal','ventral'])for(const width of [.8,1,1.15])for(const thickness of [.85,1,1.1]){
    const result=render(p,{surface,width,thickness});cases++;
    const {shape,svg}=result;
    assert.ok(!/NaN|Infinity|undefined/.test(svg));
    assert.equal((shape.path.match(/M/g)||[]).length,1);
    assert.ok(shape.path.endsWith('Z'));
    const o=shape.outline;
    for(let i=0;i<o.length-1;i++)for(let j=i+2;j<o.length-1;j++){
      assert.ok(!(cross(o[i],o[i+1],o[j])*cross(o[i],o[i+1],o[j+1]) < -1e-10 && cross(o[j],o[j+1],o[i])*cross(o[j],o[j+1],o[i+1]) < -1e-10),`${p.preset_id} crossed outline: ${surface} ${width} ${thickness}`);
    }
    assert.equal(svg.includes('id="monocle"'),surface==='dorsal'&&p.artistic_parameters.pattern==='monocle');
    assert.equal(svg.includes('id="spectacle"'),surface==='dorsal'&&p.artistic_parameters.pattern==='spectacle');
    assert.equal(svg.includes('id="rattle"'),p.artistic_parameters.tail_type==='rattle');
    assert.equal(svg.includes('id="paddle-fin-detail"'),p.artistic_parameters.tail_type==='paddle');
  }
  assert.equal(JSON.stringify(p),before,'renderer cannot mutate evidence/preset');
}
console.log(`Passed ${cases} preset/view/shape combinations plus deterministic rendering, identity, pattern isolation and vector-only checks.`);
const {parse}=require('./preset-settings.js');
const p=bundle.presets[0],data={schema_version:1,base_preset_id:p.preset_id,species_id:p.species_id,venom_trait_mapping:null,view:{surface:'dorsal',framing:'full'},artistic_overrides:{width:1,thickness:1,skinColor:'#657755',ringColor:'#eee0aa',patternContrast:1,scaleDetail:1,ringSize:1}};
assert.deepEqual(parse(JSON.stringify(data),bundle.presets),data);
for(const bad of [ {...data,species_id:'wrong'}, {...data,venom_trait_mapping:{}}, {...data,artistic_overrides:{...data.artistic_overrides,thickness:20}}, {...data,artistic_overrides:{...data.artistic_overrides,skinColor:'url(bad)'}}, {...data,view:{surface:'wrong',framing:'full'}}])assert.throws(()=>parse(JSON.stringify(bad),bundle.presets));
console.log('Settings round-trip and invalid identity, colors, ranges and views checked.');
// Regression: a color/scale swap must not collapse mamba and boomslang anatomy again.
const G=require('./species-geometry.js');
const mamba=bundle.presets.find(p=>p.preset_id==='dendroaspis_polylepis');
const boom=bundle.presets.find(p=>p.preset_id==='dispholidus_typus');
const gm=G.geometry(mamba),gb=G.geometry(boom);
const area=poly=>Math.abs(poly.reduce((sum,p,i)=>{const q=poly[(i+1)%poly.length];return sum+p[0]*q[1]-q[0]*p[1];},0))/2;
const mh=gm.head,bh=gb.head;
assert.ok(mh.length>bh.length*1.2,'mamba head must stay longer in the illustrative comparison');
assert.ok(area(gb.headOutline)/bh.length**2>area(gm.headOutline)/mh.length**2*1.2,'boomslang head must not be a scaled mamba head');
assert.ok(bh.eye[3]/bh.length>mh.eye[3]/mh.length*2,'relative eye prominence must remain distinct');
const mm=G.surface(gm.points),mb=G.surface(gb.points),rm=Math.max(...gm.points.map(p=>p.r)),rb=Math.max(...gb.points.map(p=>p.r));
assert.ok(mb.at(mb.length*.5).r/rb<mm.at(mm.length*.5).r/rm-.1,'boomslang tail taper must begin earlier in this drawing');
for(const p of bundle.presets){
 const g=G.geometry(p),sil=render(p,{silhouette:true});
 assert.equal(sil.shape.path,render(p).shape.path);
 assert.ok(!sil.svg.includes('id="eyes"'));
 if(g.head){
  const h=g.head,rad=h.angle_degrees*Math.PI/180;
  const toGlobal=(x,y)=>[h.origin[0]+Math.cos(rad)*x-Math.sin(rad)*y,h.origin[1]+Math.sin(rad)*x+Math.cos(rad)*y];
  const inside=point=>{let result=false,poly=g.headOutline;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>point[1])!==(b[1]>point[1])&&point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0])result=!result;}return result;};
  for(const [x,y] of [[h.eye[0],h.eye[1]],[h.eye[0]-h.eye[2],h.eye[1]],[h.eye[0]+h.eye[2],h.eye[1]],[h.eye[0],h.eye[1]-h.eye[3]],[h.eye[0],h.eye[1]+h.eye[3]]])assert.ok(inside(toGlobal(x,y)),p.preset_id+' eye landmark outside skull');
 }
}
console.log('Distinct head proportions, eye placement, taper and silhouette regression checks passed.');

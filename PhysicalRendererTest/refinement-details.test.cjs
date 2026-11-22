const assert = require('node:assert/strict');
const bundle = require('./presets/species-presets.json');
const {render} = require('./species-renderer.js');
const preset = id => structuredClone(bundle.presets.find(p => p.preset_id === id));
function changedWithoutChangingOutline(id, edit, name) {
  const original = preset(id), modified = structuredClone(original);
  edit(modified.artistic_parameters);
  const a = render(original), b = render(modified);
  assert.notEqual(a.svg, b.svg, `${name} must change the drawing`);
  assert.equal(a.shape.path, b.shape.path, `${name} must not distort the body outline`);
}
changedWithoutChangingOutline('crotalus_scutulatus', p => p.tail_band_dark_fraction = .8, 'tail band proportion');
changedWithoutChangingOutline('crotalus_horridus', p => p.chevron_width = .18, 'chevron width');
changedWithoutChangingOutline('crotalus_tigris', p => p.rattle_size = .8, 'rattle size');
changedWithoutChangingOutline('crotalus_simus', p => delete p.neck_stripe_color, 'paired neck stripes');
changedWithoutChangingOutline('crotalus_tzabcan', p => p.pattern = 'flank_triangles', 'outlined diamonds');
changedWithoutChangingOutline('daboia_russelii', p => p.pattern = 'plain', 'oval markings');
changedWithoutChangingOutline('hydrophis_platurus', p => p.pattern = 'plain', 'lateral two-tone pattern');
changedWithoutChangingOutline('hydrophis_platurus', p => delete p.tail_pattern, 'spotted paddle');
changedWithoutChangingOutline('hypnale_hypnale', p => p.pattern = 'plain', 'paired dorsal spots');
changedWithoutChangingOutline('vipera_berus', p => p.zigzag_width = .2, 'dorsal zigzag width');
changedWithoutChangingOutline('crotalus_polystictus', p => p.pattern = 'ocelli', 'paired dorsal oval rows');
const coral = preset('micrurus_lemniscatus');
const colorsIn = (svg, layer) => {
  const body = svg.match(new RegExp(`<g id="${layer}">([\\s\\S]*?)</g>`))[1];
  return [...body.matchAll(/fill="(#[0-9a-f]{6})"/gi)].map(m => {
    const c=m[1], r=parseInt(c.slice(1,3),16), g=parseInt(c.slice(3,5),16), b=parseInt(c.slice(5,7),16);
    return r>g*1.5 && r>b*1.5 ? 'R' : r<80 && g<80 && b<80 ? 'K' : r>150 && g>140 && b>115 ? 'W' : '?';
  }).filter(c => c !== '?').filter((c,i,a) => !i || c!==a[i-1]).join('');
};
assert.ok(colorsIn(render(coral).svg, 'dorsal-scale-fills').includes('RKWKWKR'), 'dorsal body must show red, black, pale, black, pale, black, red');
assert.ok(colorsIn(render(coral,{surface:'ventral'}).svg, 'ventral-plates').includes('RKWKWKR'), 'ventral plates must retain the same band sequence');
changedWithoutChangingOutline('micrurus_lemniscatus', p => p.pattern = 'plain', 'coral triads');
for (const options of [{skinColor:'#3377aa'}, {ringColor:'#664422'}]) {
  const base=render(coral), recolored=render(coral,options);
  assert.notEqual(recolored.svg,base.svg,'color controls must affect the coral drawing');
  assert.equal(recolored.shape.path,base.shape.path,'color controls must preserve its outline');
}
const daboia = preset('daboia_russelii');
assert.ok(!render(daboia).svg.includes('id="heat-pit"'), 'Russell’s viper does not have a loreal heat pit');
const contradictory = structuredClone(daboia);
contradictory.artistic_parameters.head_geometry.pit = [16, 0];
assert.ok(!render(contradictory).svg.includes('id="heat-pit"'), 'a stale landmark must not override pit_present=false');
console.log('Species pattern, tail, rattle and neck-stripe controls affect rendering without changing body geometry.');

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
const alleni = preset('micrurus_alleni');
assert.ok(colorsIn(render(alleni).svg, 'dorsal-scale-fills').includes('RWKWR'), 'custom band sequence must appear dorsally');
assert.ok(colorsIn(render(alleni,{surface:'ventral'}).svg, 'ventral-plates').includes('RWKWR'), 'custom band sequence must continue onto ventral plates');
changedWithoutChangingOutline('micrurus_alleni', p => p.band_sequence = [
  {color:'skin',fraction:.5}, {color:'marking',fraction:.5}
], 'custom band sequence');
for (const options of [{skinColor:'#3377aa'}, {ringColor:'#664422'}, {ringSize:1.2}]) {
  assert.notEqual(render(alleni,options).svg,render(alleni).svg,'custom bands must respond to editing controls');
}
assert.ok(render(alleni).svg.match(/<g id="scale-tips"><path/), 'dark scale tips should be rendered on the dorsal body');
assert.ok(!render(alleni,{surface:'ventral'}).svg.match(/<g id="scale-tips"><path/), 'dorsal scale tips must not obscure ventral plates');
const mipartitus = preset('micrurus_mipartitus');
changedWithoutChangingOutline('micrurus_mipartitus', p => p.tail_pattern = undefined, 'red and black tail bands');
const ventralMipartitus=render(mipartitus,{surface:'ventral'}).svg;
assert.ok(colorsIn(ventralMipartitus,'ventral-plates').includes('RKR'), 'ventral tail plates must preserve red and black tail bands');
const nasutum=preset('porthidium_nasutum');
assert.ok(render(nasutum).svg.includes('id="dorsal-midline"'), 'hognosed pit viper should show its dorsal line');
assert.ok(!render(nasutum,{surface:'ventral'}).svg.includes('id="dorsal-midline"'), 'dorsal line must not appear on the underside');
changedWithoutChangingOutline('porthidium_nasutum', p => delete p.dorsal_midline_color, 'dorsal midline');
changedWithoutChangingOutline('bothrops_cotiara', p => p.pattern_border_color = '#ff00ff', 'dorsal border color independent of the belly');
changedWithoutChangingOutline('metlapilcoatlus_nummifer', p => p.diamond_center_color = '#ff00ff', 'independent diamond center color');
const conophis=preset('conophis_lineatus');
assert.equal((render(conophis).svg.match(/class="longitudinal-stripe"/g)||[]).length,6,'road guarder must show six adjustable dorsal stripes');
assert.ok(!render(conophis,{surface:'ventral'}).svg.includes('class="longitudinal-stripe"'),'dorsal stripes must not appear on the ventral view');
changedWithoutChangingOutline('conophis_lineatus', p => delete p.longitudinal_stripe_offsets, 'longitudinal stripes');
const blueCoral=preset('calliophis_bivirgata');
assert.equal(blueCoral.artistic_parameters.belly_color,blueCoral.artistic_parameters.tail_color,'blue coral snake should use the same red on the underside and tail');
changedWithoutChangingOutline('calliophis_bivirgata', p => delete p.ventrolateral_stripe, 'blue coral lateral stripes');
const bandedCoral=preset('calliophis_intestinalis');
const bandedVentral=colorsIn(render(bandedCoral,{surface:'ventral'}).svg,'ventral-plates');
assert.ok(bandedVentral.includes('WKW'), 'banded coral snake must have pale and dark ventral bands');
assert.ok(bandedVentral.includes('RKR'), 'banded coral snake must have red and dark ventral tail bands');
assert.ok(render(bandedCoral).svg.includes('id="dorsal-midline"'), 'banded coral snake needs its red dorsal stripe');
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

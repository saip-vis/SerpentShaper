const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const style=require('./style-inference.js'),renderer=require('../PhysicalRendererTest/species-renderer.js');
const scope={window:{}};
vm.runInNewContext(fs.readFileSync(__dirname+'/visual-style-model.js','utf8'),scope);
vm.runInNewContext(fs.readFileSync(__dirname+'/../PhysicalRendererTest/presets/species-presets.js','utf8'),scope);
const model=scope.window.SERPENT_STYLE_MODEL,presets=scope.window.SERPENT_PRESETS.presets;
for(const preset of presets){
  for(const [surface,values] of [['dorsal',{'3ftx':100,pla2:0,svmp:0}],['ventral',{'3ftx':0,pla2:100,svmp:0}]]){
    const concept=style.concept(preset,values,model);
    assert.ok(concept,`${preset.preset_id} should create a concept`);
    const rendering=renderer.render(concept.preset,{...concept.options,surface,framing:'full'});
    assert.match(rendering.shape.path,/Z$/,`${preset.preset_id} ${surface} must have a closed contour`);
    assert.doesNotMatch(rendering.svg,/NaN|Infinity/,`${preset.preset_id} ${surface} must have finite SVG values`);
  }
}
console.log(`Bounded concepts rendered for ${presets.length} source presets on both surfaces.`);

/* Validate saved artistic settings before they reach the renderer. */
(function(root){
const ranges={width:[.8,1.15],thickness:[.85,1.1],patternContrast:[.7,1.3],scaleDetail:[.8,1.3],ringSize:[.8,1.15]};
function parse(text,presets){
 const data=JSON.parse(text),preset=presets.find(p=>p.preset_id===data.base_preset_id);
 if(data.schema_version!==1||!preset||data.species_id!==preset.species_id||data.venom_trait_mapping!==null)throw Error('Settings identity or schema does not match this catalog.');
 const o=data.artistic_overrides;
 if(!o||Object.keys(o).length!==7)throw Error('Incomplete artistic settings.');
 for(const [key,value]of Object.entries(o)){
  if(key==='skinColor'||key==='ringColor'){if(typeof value!=='string'||!/^#[0-9a-f]{6}$/i.test(value))throw Error('Invalid color.');}
  else if(!ranges[key]||typeof value!=='number'||!Number.isFinite(value)||value<ranges[key][0]||value>ranges[key][1])throw Error('Setting outside supported limits.');
 }
 if(!['dorsal','ventral'].includes(data.view?.surface)||!['full','hood'].includes(data.view?.framing))throw Error('Unsupported view.');
 return data;
}
if(typeof module!=='undefined')module.exports={parse};else root.PresetSettings={parse};
})(typeof window!=='undefined'?window:this);

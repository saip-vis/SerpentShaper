const $=id=>document.getElementById(id);
const presets=window.SERPENT_PRESETS.presets;
const byId=new Map(presets.map(p=>[p.preset_id,p]));
const controls=['width','thickness','skinColor','ringColor','patternContrast','scaleDetail','ringSize'];
const states=new Map();let active='naja_kaouthia',surface='dorsal',framing='full';
function defaults(p){return {width:1,thickness:1,skinColor:p.artistic_parameters.skin_color,ringColor:p.artistic_parameters.marking_color,patternContrast:1,scaleDetail:1,ringSize:1};}
function current(){return Object.fromEntries(controls.map(id=>[id,id.endsWith('Color')?$(id).value:Number($(id).value)]));}
function download(content,name,type){const url=URL.createObjectURL(new Blob([content],{type}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function draw(){
  const p=byId.get(active),art=p.artistic_parameters,options={...current(),surface,framing,silhouette:$('silhouette').checked};
  const result=SpeciesRenderer.render(p,options);$('drawing').innerHTML=result.svg;
  states.set(active,current());
  $('speciesTitle').textContent=p.common_name;$('scientificName').textContent=p.source_species_name;
  $('viewLabel').textContent=`${surface==='dorsal'?(art.body_plan==='cobra'?'Rear hood':'Dorsal-colored oblique'):(art.body_plan==='cobra'?'Front three-quarter':'Ventral-colored oblique')} · ${framing==='full'?'full body':'detail'}`;
  $('status').textContent=options.silhouette?'Anatomy silhouette · color and pattern hidden':p.status==='unreviewed_starter'?'Unreviewed starter · colors and markings are placeholders':`${result.scaleCount.toLocaleString()} scale shapes · ${presets.length} catalog presets`;
  $('variantNote').textContent=p.variant;
$('modelNotes').replaceChildren();for(const text of p.evidence.modeling_observations?.observations||[]){const li=document.createElement('li');li.textContent=text;$('modelNotes').append(li);}$('evidenceNote').textContent=[p.evidence.review,...(p.evidence.modeling_flags||[])].join(' ');
  $('sourceLinks').replaceChildren();
  for(const r of p.evidence.sources.filter(r=>r.url)) {const a=document.createElement('a');a.href=r.url;a.textContent=new URL(r.url).hostname;a.target='_blank';a.rel='noopener noreferrer';$('sourceLinks').append(a,document.createElement('br'));}
  $('width').disabled=art.body_plan!=='cobra';
  const markEnabled=(art.pattern!=='plain'||art.ventrolateral_stripe) && (surface==='dorsal'||['rings','coral_triads'].includes(art.pattern));
  $('ringSize').disabled=!markEnabled||['plain','edged_scales','reticulated','speckled'].includes(art.pattern);$('ringColor').disabled=!markEnabled;
  $('hood').textContent=art.body_plan==='cobra'?'Hood detail':'Head detail';
  for(const [id,on] of [['back',surface==='dorsal'],['front',surface==='ventral'],['full',framing==='full'],['hood',framing==='hood']])$(id).setAttribute('aria-pressed',String(on));
  $('back').textContent=art.body_plan==='cobra'?'Rear view':'Dorsal surface';$('front').textContent=art.body_plan==='cobra'?'Front view':'Ventral surface';
  const viewScope=art.body_plan==='cobra'?'Shapes, palette and scale density are artistic parameters.':'Dorsal and ventral controls change surface details on the same outline; they are not separate angle reconstructions.';
  $('renderCaption').textContent=p.status==='unreviewed_starter'?`Unreviewed starter: color and markings are placeholders. ${viewScope}`:`Illustrative preset. ${viewScope}`;
  $('photoMode').hidden=active!=='naja_kaouthia';
  document.title=`SerpentShaper · ${p.common_name}`;
}
function setMode(photo){
  for(const id of ['photoRendering','photoInfo','photoLabel'])$(id).hidden=!photo;
  for(const id of ['drawing','proceduralControls','viewLabel','presetInfo'])$(id).hidden=photo;
  $('proceduralControls').disabled=photo;
  $('renderLayout').classList.toggle('photo-mode',photo);
  $('photoMode').setAttribute('aria-pressed',String(photo));$('proceduralMode').setAttribute('aria-pressed',String(!photo));
  $('modeSummary').textContent=photo?'Generated illustration · comparison only':'Species presets · procedural SVG';
  $('renderCaption').textContent=photo?'Photo-guided Naja kaouthia concept; comparison only.':'Reference-guided illustrative preset. Shapes, palette and scale density are artistic parameters.';
}
function selectSpecies(id){active=id;const values=states.get(id)||defaults(byId.get(id));for(const [key,value]of Object.entries(values))$(key).value=value;setMode(false);draw();}
for(const p of presets){const option=document.createElement('option');option.value=p.preset_id;option.textContent=p.common_name.toLocaleLowerCase()===p.source_species_name.toLocaleLowerCase()?p.source_species_name:`${p.common_name} – ${p.source_species_name}`;$('speciesSelect').append(option);}
$('speciesSelect').value=active;$('speciesSelect').onchange=()=>selectSpecies($('speciesSelect').value);
for(const id of controls)$(id).oninput=draw;
$('silhouette').onchange=draw;
$('back').onclick=()=>{surface='dorsal';draw();};$('front').onclick=()=>{surface='ventral';draw();};
$('full').onclick=()=>{framing='full';draw();};$('hood').onclick=()=>{framing='hood';draw();};
$('photoMode').onclick=()=>setMode(true);$('proceduralMode').onclick=()=>setMode(false);
$('resetTexture').onclick=()=>{states.delete(active);selectSpecies(active);};
$('save').onclick=()=>download($('drawing').innerHTML,`${active}-${surface}-${framing}.svg`,'image/svg+xml');
$('savePreset').onclick=()=>download(JSON.stringify({schema_version:1,base_preset_id:active,model_revision:byId.get(active).model_revision,species_id:byId.get(active).species_id,artistic_overrides:current(),view:{surface,framing},venom_trait_mapping:null},null,2),`${active}-settings.json`,'application/json');
selectSpecies(active);
$('loadPreset').onclick=()=>$('presetFile').click();
$('presetFile').onchange=async()=>{
 try{
  const file=$('presetFile').files[0];if(!file)return;if(file.size>10000)throw Error('Settings file is too large.');
  const data=PresetSettings.parse(await file.text(),presets);
  states.set(data.base_preset_id,data.artistic_overrides);surface=data.view.surface;framing=data.view.framing;
  $('speciesSelect').value=data.base_preset_id;selectSpecies(data.base_preset_id);
  $('status').textContent+=' · saved settings loaded';
 }catch(error){$('status').textContent='Could not load settings: '+error.message;}
 finally{$('presetFile').value='';}
};

// Static photo-guided output and the parametric renderer are distinct display modes.
function setDisplayMode(mode) {
  const photo = mode === 'photo';
  for (const id of ['photoRendering', 'photoInfo', 'photoLabel']) document.getElementById(id).hidden = !photo;
  for (const id of ['drawing', 'proceduralControls', 'viewLabel']) document.getElementById(id).hidden = photo;
  document.getElementById('proceduralControls').disabled = photo;
  document.getElementById('renderLayout').classList.toggle('photo-mode', photo);
  document.getElementById('photoMode').setAttribute('aria-pressed', String(photo));
  document.getElementById('proceduralMode').setAttribute('aria-pressed', String(!photo));
  document.getElementById('modeSummary').textContent = photo ? 'Photo-guided illustration · visual reference' : 'Procedural anatomy and scales · illustrative model';
  document.getElementById('renderCaption').textContent = photo ? 'Photo-guided visual study of Naja kaouthia.' : 'Generated anatomy, overlapping scale geometry and surface markings.';
}
 document.getElementById('photoMode').onclick = () => setDisplayMode('photo');
 document.getElementById('proceduralMode').onclick = () => setDisplayMode('procedural');
setDisplayMode('procedural');

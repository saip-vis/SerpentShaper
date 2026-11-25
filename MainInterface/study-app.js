(() => {
'use strict';
const $=id=>document.getElementById(id);
const status=$('study-status'),results=$('study-results');
if(!window.location || window.location.hostname!=='127.0.0.1' || window.location.protocol!=='http:'){
  $('study-controls').hidden=true;
  $('study-availability').textContent='To use study uploads, run ./start_serpentshaper.sh and open the local address it prints.';
  return;
}
$('study-availability').textContent='Your files stay on this computer and are not saved when the server stops.';
const applied=new Map();let applying=false;
function renderApplied(){
  const container=$('study-applied');container.replaceChildren();
  if(!applied.size)return;
  const title=document.createElement('strong');title.textContent='Current study-sourced inputs';container.append(title);
  for(const source of applied.values()){
    const line=document.createElement('p');line.textContent=`${source.quoted_text} — ${source.study}, page ${source.page}`;container.append(line);
  }
}
function clearApplied(){applied.clear();renderApplied();}
function reconcileApplied(){
  if(applying)return;
  for(const [component,source] of applied){const input=$(`component-${component}`);if(!input||input.value===''||Number(input.value)!==source.value)applied.delete(component);}
  renderApplied();
}
$('controls').addEventListener('input',reconcileApplied);
$('starting-species').addEventListener('change',clearApplied);
$('clear').addEventListener('click',clearApplied);
async function request(path,options){
  const response=await fetch(path,options),data=await response.json();
  if(!response.ok)throw new Error(data.error||'The request failed.');
  return data;
}
function fileContents(file){return new Promise((resolve,reject)=>{
  const reader=new FileReader();reader.onerror=()=>reject(new Error('Could not read the file.'));
  reader.onload=()=>{const value=String(reader.result),index=value.indexOf(',');if(index<0)reject(new Error('Could not read the file.'));else resolve(value.slice(index+1));};
  reader.readAsDataURL(file);
});}
$('study-upload').addEventListener('click',async()=>{
  const file=$('study-file').files[0];
  if(!file){status.textContent='Choose a PDF or text file first.';return;}
  if(file.size>12*1024*1024){status.textContent='The file must be 12 MB or smaller.';return;}
  status.textContent='Reading study…';$('study-upload').disabled=true;
  try{
    const content=await fileContents(file);
    const study=await request('/api/study-upload',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:file.name,content})});
    status.textContent=study.duplicate?`${study.name} is already loaded.`:`Loaded ${study.name} (${study.pages} page${study.pages===1?'':'s'}). Search its text below.`;
  }catch(error){status.textContent=error.message;}
  finally{$('study-upload').disabled=false;}
});
$('study-clear').addEventListener('click',async()=>{
  try{await request('/api/study-clear',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});results.replaceChildren();$('study-file').value='';clearApplied();status.textContent='Studies cleared from memory.';}
  catch(error){status.textContent=error.message;}
});
$('study-answer').addEventListener('click',async()=>{
  const question=$('study-query').value.trim();results.replaceChildren();
  if(!question){status.textContent='Enter a question.';return;}
  status.textContent='Asking the local model; this can take a minute…';$('study-answer').disabled=true;
  try{
    const data=await request('/api/study-answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question})});
    status.textContent=data.citations_well_formed?'AI answer generated locally. Citations identify retrieved passages; verify every claim in the study.':'The AI answer has missing or invalid citation numbers. Verify it against the passages below.';
    const card=document.createElement('article');card.className='study-result';
    const title=document.createElement('h4');title.textContent=`Local AI answer (${data.model})`;card.append(title);
    const text=document.createElement('p');text.textContent=data.answer;card.append(text);results.append(card);
    for(const source of data.sources){
      const block=document.createElement('article');block.className='study-result';
      const label=document.createElement('h4');label.textContent=`[${source.number}] ${source.study} · page ${source.page}`;block.append(label);
      const excerpt=document.createElement('p');excerpt.textContent=source.excerpt;block.append(excerpt);results.append(block);
    }
  }catch(error){status.textContent=error.message;}
  finally{$('study-answer').disabled=false;}
});
$('study-search').addEventListener('click',async()=>{
  const query=$('study-query').value.trim();results.replaceChildren();
  if(!query){status.textContent='Enter a search term.';return;}
  status.textContent='Searching…';
  try{
    const data=await request('/api/study-search?q='+encodeURIComponent(query));
    status.textContent=data.results.length?`${data.results.length} matching passages. Check the full study and context before applying a value.`:'No matching passages in the loaded studies.';
    for(const result of data.results){
      const card=document.createElement('article');card.className='study-result';
      const title=document.createElement('h4');title.textContent=`${result.study} · page ${result.page}`;card.append(title);
      const excerpt=document.createElement('p');excerpt.textContent=result.excerpt;card.append(excerpt);
      for(const suggestion of result.suggestions){
        const input=$(`component-${suggestion.component}`);
        if(!input||!Number.isFinite(suggestion.value)||suggestion.value<0||suggestion.value>100)continue;
        const button=document.createElement('button');button.type='button';button.textContent=`Use ${suggestion.quoted_text}`;
        button.addEventListener('click',()=>{
          input.value=String(suggestion.value);applying=true;
          try{input.dispatchEvent(new Event('input',{bubbles:true}));}finally{applying=false;}
          if(input.value!==''&&Number(input.value)===suggestion.value){
            applied.set(suggestion.component,{...suggestion,study:result.study,page:result.page});renderApplied();
            status.textContent=`Applied ${suggestion.quoted_text} from ${result.study}, page ${result.page}. Other components were not changed.`;
          }else{reconcileApplied();status.textContent='Value was not applied: the entered total cannot exceed 100%.';}
        });card.append(button);
      }
      results.append(card);
    }
  }catch(error){status.textContent=error.message;}
});
})();

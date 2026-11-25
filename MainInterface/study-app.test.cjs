const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
class NodeMock{
  constructor(){this.children=[];this.events={};this.value='';this.files=[];this.hidden=false;this.disabled=false;this.textContent='';}
  append(...nodes){this.children.push(...nodes)}
  replaceChildren(...nodes){this.children=nodes}
  addEventListener(name,fn){this.events[name]=fn}
  dispatchEvent(event){if(this.events[event.type])this.events[event.type](event)}
  fire(name){return this.events[name]({target:this})}
}
const ids=['controls','clear','starting-species','study-controls','study-availability','study-status','study-results','study-applied','study-file','study-upload','study-clear','study-query','study-search','study-answer','component-pla2'];
const nodes=Object.fromEntries(ids.map(k=>[k,new NodeMock()]));
const document={getElementById:id=>nodes[id]||null,createElement:()=>new NodeMock()};
const responses={
 '/api/study-upload':{name:'study.pdf',pages:2,duplicate:false},
 '/api/study-search?q=PLA2':{results:[{study:'study.pdf',page:2,excerpt:'PLA2: 25%',suggestions:[{component:'pla2',value:25,quoted_text:'PLA2: 25%'}]}]},
 '/api/study-answer':{answer:'Reported PLA2 was 25% [1].',model:'llama3:latest',citations_well_formed:true,sources:[{number:1,study:'study.pdf',page:2,excerpt:'PLA2: 25%'}]},
 '/api/study-clear':{cleared:true}
};
const fetch=async(path)=>({ok:true,json:async()=>responses[path]});
class FileReader {readAsDataURL(){this.result='data:application/pdf;base64,ZmFrZQ==';this.onload()}}
class Event {constructor(type){this.type=type}}
const code=fs.readFileSync(__dirname+'/study-app.js','utf8');
vm.runInNewContext(code,{window:{location:{hostname:'127.0.0.1',protocol:'http:'}},document,fetch,FileReader,Event,Number,String,Error,Promise,encodeURIComponent});
(async()=>{
 nodes['study-file'].files=[{name:'study.pdf',size:4}];await nodes['study-upload'].fire('click');
 assert.match(nodes['study-status'].textContent,/Loaded study.pdf \(2 pages\)/);
 nodes['study-query'].value='PLA2';await nodes['study-search'].fire('click');
 const result=nodes['study-results'].children[0];assert.equal(result.children[0].textContent,'study.pdf · page 2');
 assert.equal(result.children[1].textContent,'PLA2: 25%');result.children[2].fire('click');
 assert.equal(nodes['component-pla2'].value,'25');assert.match(nodes['study-status'].textContent,/Applied PLA2: 25%/);
 assert.match(nodes['study-applied'].children[1].textContent,/study.pdf, page 2/);
 nodes['component-pla2'].addEventListener('input',()=>{nodes['component-pla2'].value='10'});
 result.children[2].fire('click');assert.match(nodes['study-status'].textContent,/cannot exceed 100%/);
 assert.equal(nodes['study-applied'].children.length,0,'stale source attribution is removed if the value changes');
 await nodes['study-answer'].fire('click');assert.match(nodes['study-results'].children[0].children[1].textContent,/25% \[1\]/);
 assert.equal(nodes['study-results'].children[1].children[0].textContent,'[1] study.pdf · page 2');
 assert.equal(nodes['component-pla2'].value,'10','an AI answer never changes venom inputs');
 assert.match(nodes['study-status'].textContent,/verify every claim/i);
 await nodes['study-clear'].fire('click');assert.equal(nodes['study-results'].children.length,0);assert.match(nodes['study-status'].textContent,/cleared/);
 console.log('Study upload, cited retrieval and guarded application verified.');
})().catch(error=>{console.error(error);process.exitCode=1});

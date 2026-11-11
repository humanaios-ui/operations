/* DOM interaction harness plus the real Python reducer. No accounts or file uploads. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const {execFileSync}=require('node:child_process');
class Element{
 constructor(){this.value='';this.textContent='';this.children=[];this.style={};this.listeners={};this.files=[];}
 addEventListener(kind,fn){this.listeners[kind]=fn;}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(){this.children=[];this.textContent='';}
 click(){} remove(){}
}
const elements=new Map();
const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
let saved=null,downloaded=null,lastProjection=null;
const bodies=[];
const specimen=JSON.parse(fs.readFileSync('fixtures/opportunity_journey_apart_synthetic.json','utf8'));
const project=body=>JSON.parse(execFileSync(process.env.PYTHON||'python3',[
 '-c','import json,sys; from resource_miner.opportunity_journey import project_journey; print(json.dumps(project_journey(json.load(sys.stdin))))'
],{input:body,encoding:'utf8'}));
const context=vm.createContext({
 document:{getElementById:get,querySelectorAll:()=>[],createElement:()=>new Element(),body:new Element()},
 TextEncoder,Blob,Date,Uint8Array,crypto:webcrypto,
 URL:{createObjectURL:blob=>{downloaded=blob;return 'blob:local';},revokeObjectURL:()=>{}},
 setTimeout:()=>{},confirm:()=>true,
 localStorage:{getItem:()=>null,setItem:(key,value)=>{saved=value;},removeItem:()=>{saved=null;}},
 fetch:async(route,options)=>{
  if(route.endsWith('/starter'))return {ok:true,json:async()=>structuredClone(specimen)};
  const body=options?.body||JSON.stringify(specimen);
  if(options)bodies.push(body);
  lastProjection=project(body);
  return {ok:true,json:async()=>({mode:options?'LOCAL_USER_PROVIDED_UNVERIFIED':'SYNTHETIC_DEMONSTRATION_NOT_PERSONAL_EVIDENCE',journeys:[lastProjection]})};
 }
});
const html=fs.readFileSync('my-opportunities.html','utf8');
vm.runInContext(html.split('<script>')[1].split('</script>')[0],context);
const click=async id=>get(id).listeners.click();
const text=node=>node.textContent+' '+node.children.map(text).join(' ');
async function recordFile(contents){
 get('preparationFileId').value='QC-INPUT';get('preparationRole').value='INPUT';
 get('preparationFile').files=[{name:'private-source.txt',size:contents.length,arrayBuffer:async()=>new TextEncoder().encode(contents).buffer}];
 await click('recordFile');
}
(async()=>{
 await new Promise(resolve=>setImmediate(resolve));
 await click('starter');
 assert.equal(get('preparationControls').disabled,false);
 await recordFile('first-private-source');
 assert.equal(lastProjection.preparation.standing,'NEEDS_PREPARATION');
 get('preparationCheckId').value='MATCH-GOAL';get('preparationCheckStatus').value='PASS';
 await click('recordPreparationCheck');
 assert.equal(lastProjection.preparation.standing,'READY_FOR_HUMAN_REVIEW');
 assert.match(get('preparationStanding').textContent,/human review/);
 await recordFile('second-private-source');
 assert.equal(lastProjection.preparation.checks[0].standing,'STALE');
 assert.match(text(get('preparationDetails')),/STALE/);
 assert.equal(lastProjection.preparation.file_versions.length,2);
 await recordFile('second-private-source');
 assert.equal(lastProjection.preparation.file_versions.length,2);
 await click('export');
 const exported=JSON.parse(await downloaded.text());
 assert.equal(exported.journey.preparation.files.length,2);
 await click('save');
 assert.deepEqual(JSON.parse(saved),exported);
 const input=get('import');
 await input.listeners.change({target:{files:[{size:saved.length,text:async()=>saved}],value:''}});
 assert.equal(lastProjection.preparation.checks[0].standing,'STALE');
 await click('recordPreparationCheck');
 assert.equal(lastProjection.preparation.standing,'READY_FOR_HUMAN_REVIEW');
 get('preparationCheckStatus').value='FAIL';await click('recordPreparationCheck');
 assert.equal(lastProjection.preparation.standing,'NEEDS_PREPARATION');
 assert.equal(lastProjection.preparation.checks[0].standing,'FAIL');
 assert.equal(lastProjection.participant_standing,'NOT_CONFIRMED_BY_PROVIDER');
 assert.equal(lastProjection.research_submission,'UNVERIFIED');
 assert.equal(lastProjection.can_submit_application,false);
 for(const body of bodies){
  assert.ok(!body.includes('private-source'));
  assert.ok(!body.includes('filename'));
 }
 console.log('PASS: file versions, stale checks, recheck, failure, JSON export/save/import, no content upload, unchanged outcomes.');
})().catch(error=>{console.error(error);process.exitCode=1;});

/* E0 private application browser workflow against real local Python reducer.
 * Synthetic fixture only. No API keys, personal information, submission, or writes.
 */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const {execFileSync}=require('node:child_process');
class Element {
 constructor(value=''){this.value=value;this.textContent='';this.children=[];this.style={};this.listeners={};this.files=[];this.checked=false;this.disabled=false;this.hidden=false;}
 addEventListener(event,fn){this.listeners[event]=fn;}
 append(...nodes){this.children.push(...nodes);}
 replaceChildren(){this.children=[];this.textContent='';}
 click(){} remove(){}
}
const elements=new Map();
const get=id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);};
const inputActions=[
 new Element('APPLICATION_SUBMITTED_HUMAN'),
 new Element('APPLICATION_CONFIRMATION_PAGE_HUMAN_OBSERVED')
];
const document={
 getElementById:get,
 createElement:()=>new Element(),
 body:new Element(),
 querySelectorAll:sel=>{
  if(sel.includes('name="humanAction"'))return [];
  if(sel.includes('name="applicationAction"'))return inputActions.filter(x=>
   !sel.includes(':checked')||(x.checked&&!x.disabled));
  return [];
 }
};
let saved=null,downloaded=null,last=null;
const bodies=[];
const apart=JSON.parse(fs.readFileSync('fixtures/opportunity_journey_apart_synthetic.json','utf8'));
const project=body=>JSON.parse(execFileSync(process.env.PYTHON||'python3',[
 '-c','import json,sys; from resource_miner.opportunity_journey import project_journey; print(json.dumps(project_journey(json.load(sys.stdin))))'
],{input:body,encoding:'utf8'}));
const ctx=vm.createContext({
 document,TextEncoder,Blob,Date,Uint8Array,crypto:webcrypto,
 URL:{createObjectURL:blob=>{downloaded=blob;return 'blob:local';},revokeObjectURL:()=>{}},
 setTimeout:()=>{},confirm:()=>true,
 localStorage:{getItem:()=>null,setItem:(key,value)=>{saved=value;},removeItem:()=>{saved=null;}},
 fetch:async(route,options)=>{
  if(route.endsWith('/starter'))return {ok:true,json:async()=>structuredClone(apart)};
  const body=options?.body||JSON.stringify(apart);
  if(options)bodies.push(body);
  last=project(body);
  return {ok:true,json:async()=>({mode:options?'LOCAL_USER_PROVIDED_UNVERIFIED':'SYNTHETIC_DEMONSTRATION_NOT_PERSONAL_EVIDENCE',journeys:[last]})};
 }
});
const html=fs.readFileSync('my-opportunities.html','utf8');
vm.runInContext(html.split('<script>')[1].split('</script>')[0],ctx);
const click=async id=>get(id).listeners.click();
(async()=>{
 await new Promise(resolve=>setImmediate(resolve));
 await click('applicationStarter');
 assert.equal(last.workflow,'RESEARCH_SUPPORT_APPLICATION');
 assert.equal(last.application_standing,'SUBMISSION_NOT_DOCUMENTED');
 assert.equal(last.provider_decision_standing,'UNVERIFIED');
 assert.equal(get('applicationActions').hidden,false);
 assert.equal(get('humanActions').hidden,true);
 assert.equal(last.event_count,1);
 inputActions[0].checked=true;
 await click('record');
 assert.equal(last.application_standing,'SUBMITTED_HUMAN_REPORTED');
 assert.equal(last.confirmation_page_standing,'UNVERIFIED');
 assert.equal(last.event_count,2);
 inputActions[1].checked=true;
 await click('record');
 assert.equal(last.application_standing,'SUBMITTED_AND_CONFIRMATION_PAGE_HUMAN_OBSERVED');
 assert.equal(last.confirmation_page_standing,'HUMAN_OBSERVED_NOT_CONNECTOR_AUTHENTICATED');
 assert.equal(last.provider_receipt_email_standing,'UNVERIFIED');
 assert.equal(last.provider_decision_standing,'UNVERIFIED');
 assert.equal(last.grant_or_support_outcome,'UNVERIFIED');
 assert.equal(last.next_action_codes[0],'CHECK_FOR_PROVIDER_RESPONSE');
 assert.equal(last.event_count,3);
 assert.equal(last.authority_effect,'NONE');
 assert.equal(last.can_submit_application,false);
 await click('export');
 const exported=JSON.parse(await downloaded.text());
 assert.equal(exported.journey.workflow,'RESEARCH_SUPPORT_APPLICATION');
 assert.equal(exported.journey.events.length,3);
 assert.deepEqual(exported.evidence,[]);
 await click('save');
 assert.deepEqual(JSON.parse(saved),exported);
 const digest=last.digest_sha256;
 const input=get('import');
 await input.listeners.change({target:{files:[{size:saved.length,text:async()=>saved}],value:''}});
 assert.equal(last.digest_sha256,digest);
 assert.equal(inputActions.filter(x=>!x.disabled).length,0);
 await click('record'); // cannot add an already-checked event
 assert.equal(last.event_count,3);
 for(const body of bodies){
  assert.ok(!body.includes('@'));
  assert.ok(!body.includes('personal'));
  assert.ok(!body.includes('provider_decision_standing'));
 }
 console.log('PASS: first-user AIAF start, two human reports, separate unverified outcomes, idempotent import, private export/save, no provider or account action.');
})().catch(e=>{console.error(e);process.exitCode=1;});

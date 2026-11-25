'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function element(){return {children:[],listeners:{},value:'',checked:false,hidden:false,
 classList:{add(){},remove(){}},setAttribute(){},focus(){},remove(){},click(){},
 append(...x){this.children.push(...x)},prepend(...x){this.children.unshift(...x)},
 replaceChildren(...x){this.children=x},addEventListener(t,f){this.listeners[t]=f}};}
function boot(data=new Map()){
 const dom=new Map();
 const fetchCalls=[];
 const document={body:element(),getElementById(id){if(!dom.has(id))dom.set(id,element());return dom.get(id)},
 createElement:element,querySelectorAll(){return []}};
 const context=vm.createContext({document,URL,Blob,setTimeout,clearTimeout,AbortController,
 crypto:require('node:crypto').webcrypto,confirm:()=>true,
 localStorage:{getItem:k=>data.get(k)||null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)},
 fetch:async(...args)=>{fetchCalls.push(args);return {ok:false}}});
 const html=fs.readFileSync(path.join(__dirname,'..','intent-os.html'),'utf8');
 vm.runInContext(html.match(/<script>\n([\s\S]*?)<\/script>/)[1],context);
 return {context,dom,data,fetchCalls};
}
function descendants(e){return [e,...e.children.flatMap(descendants)];}
const row={title:'Research grant',source_url:'https://example.org/grant',source_name:'Test',resource_id:'r'};
test('all 18 results can be reached, with ten initially and accurate counts',()=>{
 const b=boot();b.context.rows=Array.from({length:18},(_,i)=>({...row,title:'Grant '+i,source_url:row.source_url+i}));
 vm.runInContext('latestCandidates=rows;renderCandidates()',b.context);
 assert.equal(b.dom.get('items').children.length,10);
 assert.equal(b.dom.get('showMore').hidden,false);
 b.dom.get('showMore').listeners.click();
 assert.equal(b.dom.get('items').children.length,18);
 assert.equal(b.dom.get('showMore').hidden,true);
 assert.match(b.dom.get('summary').textContent,/showing 18/);
});
test('PDF and unknown file types save only fingerprints; legacy packets load',async()=>{
 const b=boot();b.context.row=row;
 for(const mime of ['application/pdf','text/plain','']){
  const card=vm.runInContext('addCard(row)',b.context),all=descendants(card);
  all.find(e=>e.children.some(c=>c.value==='SOURCE_WORKING')).value='SOURCE_WORKING';
  const picker=all.find(e=>e.type==='file');
  picker.files=[{type:mime,size:12,arrayBuffer:async()=>new TextEncoder().encode('PRIVATE FILE').buffer}];
  const save=all.find(e=>e.textContent==='Save source observation locally');
  await save.listeners.click();
 }
 const packet=JSON.parse(b.data.get('humanaios.resource_source_review.v0.1'));
 assert.equal(packet.records.length,3);
 assert.equal(packet.records[0].evidence.screenshot.mime,'application/pdf');
 assert.equal(packet.records[2].evidence.screenshot.mime,'application/octet-stream');
 assert.ok(!JSON.stringify(packet).includes('PRIVATE FILE'));
 b.context.packet=packet;
 assert.equal(vm.runInContext('validateReviewPacket(packet).length',b.context),3);
});
test('Ask Witness requires explicit consent, strips URL query and never sends notes',async()=>{
 const b=boot();b.context.row={...row,source_url:'https://example.org/grant?secret=PRIVATE_QUERY',
   source_name:'HumanAIOS Funding Pipeline',route:'WATCH',resource_id:'RES-TEST'};
 const all=descendants(vm.runInContext('addCard(row)',b.context));
 const buttons=all.filter(e=>e.textContent==='Ask the Witness'&&e.listeners.click);
 assert.equal(buttons.length,1);
 const ask=buttons[0],check=all.find(e=>e.type==='checkbox');
 const before=b.fetchCalls.length;
 await ask.listeners.click();
 assert.equal(b.fetchCalls.length,before,'without consent no MCP call is made');
 check.checked=true;
 await ask.listeners.click();
 assert.equal(b.fetchCalls.length,before+1);
 const [path,options]=b.fetchCalls.at(-1);
 assert.equal(path,'/api/witness/ask-resource');
 const body=JSON.parse(options.body);
 assert.equal(body.consent,true);
 assert.equal(body.resource.source_url,'https://example.org/grant');
 assert.equal(body.resource.resource_id,'RES-TEST');
 assert.equal(body.resource.private_notes,undefined);
 assert.ok(!JSON.stringify(body).includes('PRIVATE_QUERY'));
 assert.equal(options.method,'POST');
});
test('export removes raw evidence, session query and opaque dashboard identifiers',()=>{
 const b=boot();
 const record={id:'SYNTHETIC-R1',resource_title:'Compute credits',
  source_url:'https://example.org/compute?session=SESSION_SECRET',
  status:'SOURCE_WORKING',observed_at:'2026-10-25T21:00:00Z',
  evidence:{note:'Job not found; secret PRIVATE_NOTE',
    replacement_url:'https://console.example.org/platform/org_SYNTHETIC_ORG/prj_SYNTHETIC_PROJECT?token=HIDDEN',
    screenshot:{mime:'application/pdf',sha256:'a'.repeat(64),size_bytes:11}}};
 b.context.record=record;
 const exported=vm.runInContext('publicReviewExport([record])',b.context);
 assert.equal(exported.records.length,1);
 const e=JSON.stringify(exported);
 for(const secret of ['PRIVATE_NOTE','SESSION_SECRET','org_SYNTHETIC_ORG','prj_SYNTHETIC_PROJECT','HIDDEN'])
  assert.ok(!e.includes(secret),secret);
 assert.equal(exported.records[0].evidence.screenshot,null);
 assert.ok(e.includes('SOURCE_STATUS_NOTE_CONFLICT_RECHECK_REQUIRED'));
 // Original browser record remains unchanged for private operator correction.
 assert.equal(record.evidence.note,'Job not found; secret PRIVATE_NOTE');
});
test('legacy locally saved preferences survive Ask Witness UI transition',()=>{
 const data=new Map([['humanaios.intent_os_teaching.v0.1',JSON.stringify([
  {source_url:'https://example.org/second',note:'Preferred',preference:'PRIORITIZE'}])]]);
 const b=boot(data);
 b.context.rows=[{...row,source_url:row.source_url},{...row,source_url:'https://example.org/second'}];
 vm.runInContext('latestCandidates=rows;renderCandidates()',b.context);
 assert.equal(b.dom.get('items').children[0].children[0].textContent,'Research grant');
 assert.equal(b.data.has('humanaios.intent_os_teaching.v0.1'),true);
 assert.equal(vm.runInContext('localPriority(rows[1])',b.context),1);
});
test('oversized evidence fails without retaining the file or saving a report',async()=>{
 const b=boot();b.context.row=row;
 const all=descendants(vm.runInContext('addCard(row)',b.context));
 all.find(e=>e.children.some(c=>c.value==='SOURCE_WORKING')).value='SOURCE_WORKING';
 all.find(e=>e.type==='file').files=[{type:'application/pdf',size:10485761,
  arrayBuffer:async()=>{throw new Error('Must reject before reading')}}];
 await all.find(e=>e.textContent==='Save source observation locally').listeners.click();
 assert.equal(b.data.has('humanaios.resource_source_review.v0.1'),false);
 assert.ok(all.some(e=>String(e.textContent).includes('Evidence file must contain')));
});
test('lessons survive a page reload and clearing reverses preferences',()=>{
 const data=new Map([['humanaios.intent_os_teaching.v0.1',JSON.stringify([
  {source_url:row.source_url,note:'Remember',preference:'PRIORITIZE'}])]]);
 const b=boot(data);b.context.row=row;
 assert.equal(vm.runInContext('localPriority(row)',b.context),1);
 b.dom.get('clearLessons').listeners.click();
 assert.equal(vm.runInContext('localPriority(row)',b.context),0);
});

test('ACAT-R verification review states remain visible without raw evidence',()=>{
 const b=boot();
 const rows=[
  {resource_id:'RES-STALE',verification_state:'STALE',reason_code:'EVIDENCE_EXPIRED'},
  {resource_id:'RES-CONFLICT',verification_state:'CONFLICTING',reason_code:'SOURCE_CONFLICT'},
  {resource_id:'RES-OFFLINE',verification_state:'UNAVAILABLE',reason_code:'SOURCE_UNAVAILABLE'},
 ];
 b.context.verificationRows=rows;
 vm.runInContext('renderVerificationCases(verificationRows)',b.context);
 const section=b.dom.get('verificationCaseSection');
 const list=b.dom.get('verificationCaseList');
 assert.equal(section.hidden,false);
 assert.equal(list.children.length,3);
 assert.match(list.children[0].textContent,/STALE.*EVIDENCE_EXPIRED/);
 assert.match(list.children[1].textContent,/CONFLICTING.*SOURCE_CONFLICT/);
 assert.match(list.children[2].textContent,/UNAVAILABLE.*SOURCE_UNAVAILABLE/);
 assert.match(b.dom.get('verificationCaseSummary').textContent,/not verified closed/);
 b.context.unknown={...row,verification_state:'UNKNOWN'};
 const card=vm.runInContext('addCard(unknown)',b.context);
 assert.ok(descendants(card).some(x=>String(x.textContent).includes('Verification: UNKNOWN')));
 vm.runInContext('renderVerificationCases([])',b.context);
 assert.equal(section.hidden,true);
});

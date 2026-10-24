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
test('teaching remembers local preferences and changes local order without sending',()=>{
 const b=boot();b.context.row={...row,source_url:'https://example.org/second'};
 const all=descendants(vm.runInContext('addCard(row)',b.context));
 const area=all.find(e=>e.placeholder==='What was wrong? What should we remember next time?');
 area.value='This better fits my goal';
 const preference=all.find(e=>e.children.some(c=>c.value==='PRIORITIZE'));preference.value='PRIORITIZE';
 const fetchesBeforeSave=b.fetchCalls.length;
 all.find(e=>e.textContent==='Save lesson locally').listeners.click();
 assert.equal(b.fetchCalls.length,fetchesBeforeSave,'local save must not submit to network');
 assert.match(b.data.get('humanaios.intent_os_teaching.v0.1'),/This better fits my goal/);
 b.context.row.title='Preferred grant';b.context.rows=[row,b.context.row];vm.runInContext('latestCandidates=rows;renderCandidates()',b.context);
 assert.equal(b.dom.get('items').children[0].children[0].textContent,'Preferred grant');
 assert.equal(vm.runInContext('localPriority(rows[1])',b.context),1);
 assert.equal(vm.runInContext('localPriority(rows[0])',b.context),0);
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

import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const src=fs.readFileSync(new URL('../game.js', import.meta.url),'utf8');
const store=new Map();
const idMap=new Map();
const make=key=>{if(idMap.has(key))return idMap.get(key);
const el={id:key,value:'',textContent:'',hidden:false,disabled:false,checked:false,children:[],listeners:{},dataset:{},classList:{toggle(){}},append(...args){this.children.push(...args)},replaceChildren(){this.children=[]},setAttribute(){},removeAttribute(){},scrollIntoView(){},reset(){},addEventListener(type,cb){this.listeners[type]=cb}};
idMap.set(key,el);return el};
const pathButtons=['Ember','Archive','Forge'].map(path=>{const e=make(`path:${path}`);e.dataset.path=path;return e});
const queryButtons=['origin','route','future'].map(q=>{const e=make(`query:${q}`);e.dataset.query=q;return e});
const claimButtons=['recorded','overclaim'].map(claim=>{const e=make(`claim:${claim}`);e.dataset.claim=claim;return e});
const forwardButtons=[4,5].map(n=>{const e=make(`forward:${n}`);e.dataset.forward=n;return e});
const gotoButtons=[1,2,3,4,5].map(n=>{const e=make(`goto:${n}`);e.dataset.goto=String(n);return e});
let selectedForm=process.env.WARDENS_FORM || 'Builder';let urls=0;
const selectedPath=process.env.WARDENS_PATH || 'Forge';
const witnessOff=process.env.WARDENS_W1_OFF === '1';
const document={getElementById:make,querySelectorAll(q){
if(q==='[data-path]')return pathButtons;
if(q==='[data-query]')return queryButtons;
if(q==='[data-claim]')return claimButtons;
if(q==='[data-forward]')return forwardButtons;
if(q==='[data-goto]')return gotoButtons;
if(q==='input[name="form"]:checked')return [{value:selectedForm}];
throw Error('unhandled query selector '+q);
},createElement(){return {textContent:'',children:[],append(...a){this.children.push(...a)}}},createTextNode(text){return String(text)}};
const window={matchMedia:()=>({matches:true}),scrollTo(){},confirm:()=>true};
const localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v),removeItem:k=>store.delete(k)};
const Blob=class Blob{constructor(items){this.items=items}};
const FakeURL={createObjectURL:()=>{urls++;return 'blob:fake'},revokeObjectURL(){}};
const context={document,window,localStorage,URL:FakeURL,Blob,structuredClone,setTimeout:(fn)=>fn(),Date,console};
function run(){vm.runInNewContext(src,context);return window.__WARDENS_TEST__}
const witness=run();
const fire=(id,type,extra={})=>{const el=make(id);const cb=el.listeners[type];assert.ok(cb,'No handler '+id+' '+type);cb({preventDefault(){},target:el,...extra});};
const state=()=>witness.snapshot();
make('playerName').value='Aster';fire('genesisForm','submit');
assert.equal(state().player,'Aster');assert.equal(state().form,selectedForm);assert.equal(state().zone,2);
fire('path:'+selectedPath,'click');assert.equal(state().zone,3);assert.equal(state().path,selectedPath);
assert.match(witness.query('origin'),/disabled/);
if(!witnessOff){
  make('witnessToggle').checked=true;fire('witnessToggle','change');
  assert.match(witness.query('origin'),/E-001/);assert.match(witness.query('route'),/E-003/);assert.match(witness.query('future'),/Unknown/);
  fire('contest','click');assert.equal(state().attestation,'CONTEST');
}else{assert.match(witness.query('route'),/disabled/);assert.equal(state().attestation,null);}
fire('forward:4','click');assert.equal(state().zone,4);
fire('claim:recorded','click');assert.equal(state().calibration,'recorded');
fire('forward:5','click');assert.equal(state().zone,5);
make('proposal').value='A public memory beacon with consent limits';fire('councilForm','submit');
assert.equal(state().finished,true);
assert.deepEqual(Array.from(state().events,x=>x.kind),witnessOff?
 ['GENESIS_EVENT','FORM_SELECTED','PATH_CHOSEN','CLAIM_INSPECTED','ADVISORY_PROPOSAL_DRAFT']:
 ['GENESIS_EVENT','FORM_SELECTED','PATH_CHOSEN','W2_ATTESTATION','CLAIM_INSPECTED','ADVISORY_PROPOSAL_DRAFT']);
assert.ok(store.get('wardens.genesis.slice.v1'));
assert.equal(urls,0,'No outbound network or blobs without explicit export');
console.log(`PASS: ${selectedForm}/${selectedPath}, W1 ${witnessOff?'OFF':'ON'}, all five zones, event log, Council, local state, no remote calls.`);

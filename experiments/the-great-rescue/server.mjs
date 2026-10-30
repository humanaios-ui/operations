/** Two-player workshop host. Uses Node built-ins only.
 * A single process owns all game mutations. Demo sessions are ephemeral, not account persistence. */
import http from 'node:http';
import crypto from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {PARTS,START_INVENTORY,MAX_BUDGET,validPlacement,evaluate,simulate} from './engine.mjs';
const DIR=path.dirname(fileURLToPath(import.meta.url));
const PUBLIC=path.join(DIR,'public');
const ROOMS=new Map();
const MAX_ROOMS=120;const LIFETIME=3*60*60*1000;const ROUND_MS=12*60*1000;
const DATA_LIMIT=12000;
const CODE_CHARS='ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const randomCode=()=>Array.from({length:6},()=>CODE_CHARS[crypto.randomInt(CODE_CHARS.length)]).join('');
const token=()=>crypto.randomBytes(28).toString('hex');
const safeName=s=>String(s||'Builder').replace(/[<>\x00-\x1f\x7f]/g,'').trim().slice(0,24)||'Builder';
function publicRoom(room,myToken){
 const current=room.players.find(p=>p.token===myToken);
 return {
  code:room.code,round:room.round,phase:room.phase,deadline:room.deadline,revision:room.revision,
  rules:{budget:MAX_BUDGET,maxAttempts:2,workshopTests:'free',officialLimit:2,roundMinutes:12},
  self:current?.id||null,
  players:room.players.map(p=>({id:p.id,name:p.name,ready:p.ready,build:p.build,inventory:p.id===current?.id?p.inventory:null,
   discoveries:p.discoveries,attempts:p.attempts.map(a=>({success:a.center.success,steps:a.center.steps,used:a.used,score:a.score,total:a.total,consistency:a.consistency})),
   finished:p.finished,spent:p.build.reduce((n,x)=>n+PARTS[x.type].cost,0),vote:p.vote})),
  offers:room.offers.map(o=>({id:o.id,from:o.from,to:o.to,type:o.type})),
  results:room.phase==='results'?results(room):null
 };
}
function results(room){
 const ranked=room.players.map(p=>({id:p.id,name:p.name,best:p.attempts.toSorted((a,b)=>b.total-a.total)[0]||null})).toSorted((a,b)=>(b.best?.total??0)-(a.best?.total??0));
 const best=ranked[0]?.best?.total??0;
 const honors={};
 for(const [key,dir] of [['speed',1],['efficiency',1],['reliability',1]]){
  let eligible=ranked.filter(p=>p.best?.center.success);
  if(!eligible.length){honors[key]=[];continue;}
  let highest=Math.max(...eligible.map(p=>p.best.score[key]));
  honors[key]=eligible.filter(p=>p.best.score[key]===highest).map(p=>p.id);
 }
 const votes=room.players.filter(p=>p.vote).map(p=>p.vote);
 const votesById=Object.fromEntries(room.players.map(p=>[p.id,votes.filter(v=>v===p.id).length]));
 const most=Math.max(0,...Object.values(votesById));
 honors.ingenuity=most>0?Object.entries(votesById).filter(([k,v])=>v===most).map(([k])=>k):[];
 return {ranking:ranked.map(p=>({id:p.id,name:p.name,total:p.best?.total??0,score:p.best?.score??null,consistency:p.best?.consistency??0,attempts:room.players.find(x=>x.id===p.id).attempts.length})),champions:ranked.filter(p=>(p.best?.total??0)===best).map(p=>p.id),honors};
}
function makePlayer(name){return {id:crypto.randomUUID(),token:token(),name:safeName(name),build:[],inventory:{...START_INVENTORY},discoveries:[],attempts:[],finished:false,ready:false,vote:null,seen:new Map()};}
function reset(room){room.phase=room.players.length===2?'build':'lobby';room.deadline=room.players.length===2?Date.now()+ROUND_MS:null;room.round++;room.offers=[];
 for(const p of room.players){p.build=[];p.inventory={...START_INVENTORY};p.discoveries=[];p.attempts=[];p.finished=false;p.ready=false;p.vote=null;p.seen.clear();}room.revision++;}
function tick(room){if(room.phase==='build'&&Date.now()>=room.deadline){room.phase='results';room.revision++;}}
function status(code,auth){const room=ROOMS.get(code);if(!room)throw Object.assign(Error('Room not found or expired.'),{status:404});
 const p=room.players.find(x=>x.token===auth);if(!p)throw Object.assign(Error('Join this room to view its game state.'),{status:401});tick(room);return {room,p};}
function action(room,p,a){
 if(typeof a!=='object'||!a||typeof a.type!=='string')throw Error('Invalid action');
 if(a.type==='rematch'){
  if(p.id!==room.players[0].id||room.phase!=='results')throw Error('Only host can start rematch after results.');reset(room);return {};
 }
 if(a.type==='vote'){
  if(room.phase!=='results')throw Error('Vote after the round.');if(p.vote)throw Error('Already voted.');const other=room.players.find(x=>x.id===a.player);if(!other||other.id===p.id)throw Error('Choose another builder.');p.vote=other.id;room.revision++;return {};
 }
 if(room.phase!=='build')throw Error('Wait for both builders to join.');
 if(a.type==='inspect'){
  if(p.finished)throw Error('Round submitted.');
  if(!['coil','plans','crane','echo'].includes(a.item))throw Error('Unknown discovery');
  if(p.discoveries.includes(a.item))return {};
  p.discoveries.push(a.item);
  if(a.item==='coil')p.inventory.spring++;
  if(a.item==='crane')p.inventory.lever++;
 }else if(a.type==='place'){
  if(p.finished)throw Error('Round submitted.');
  if(!validPlacement(a.part,a.c,a.r,a.angle||0))throw Error('Invalid grid placement or rotation.');
  if(p.build.length>=8)throw Error('Maximum eight connected pieces per workshop.');
  if(p.build.some(v=>v.c===a.c&&v.r===a.r))throw Error('Grid anchor already occupied.');
  if((p.inventory[a.part]||0)<1)throw Error('No component of that type left. Explore or trade.');
  const spent=p.build.reduce((n,x)=>n+PARTS[x.type].cost,0);
  if(spent+PARTS[a.part].cost>MAX_BUDGET)throw Error('Material budget exceeded. Remove another component.');
  p.inventory[a.part]--;p.build.push({id:crypto.randomUUID(),type:a.part,c:a.c,r:a.r,angle:a.angle||0});
 }else if(a.type==='remove'){
  if(p.finished)throw Error('Round submitted.');const i=p.build.findIndex(v=>v.id===a.id);if(i<0)throw Error('Component not found.');
  const [part]=p.build.splice(i,1);p.inventory[part.type]++;
 }else if(a.type==='offer'){
  if(p.finished)throw Error('Round submitted.');const other=room.players.find(v=>v.id===a.to&&v.id!==p.id);
  if(!other||other.finished)throw Error('Recipient not available.');if(!Object.hasOwn(PARTS,a.part)||p.inventory[a.part]<1)throw Error('Part unavailable.');
  if(room.offers.length>=6)throw Error('Resolve pending offers first.');
  p.inventory[a.part]--;room.offers.push({id:crypto.randomUUID(),from:p.id,to:other.id,type:a.part});
 }else if(a.type==='answerOffer'){
  const i=room.offers.findIndex(o=>o.id===a.id&&o.to===p.id);if(i<0)throw Error('Offer unavailable.');
  const [o]=room.offers.splice(i,1);
  const recipient=a.accept===true?p:room.players.find(x=>x.id===o.from);
  if(recipient)recipient.inventory[o.type]++;
 }else if(a.type==='official'){
  if(p.finished)throw Error('Already submitted.');if(p.attempts.length>=2)throw Error('Only two official attempts per round.');
  const record=evaluate(p.build);p.attempts.push(record);room.revision++;return {simulation:record.center,record:{total:record.total,score:record.score,consistency:record.consistency,used:record.used}};
 }else if(a.type==='finish'){
  if(p.finished)throw Error('Already finished.');if(!p.attempts.length)throw Error('Attempt at least one official run first.');
  p.finished=true;
  // Pending offers return to the sender, not deleted.
  room.offers=room.offers.filter(o=>{if(o.from===p.id||o.to===p.id){const sender=room.players.find(x=>x.id===o.from);sender.inventory[o.type]++;return false;}return true;});
  if(room.players.every(v=>v.finished))room.phase='results';
 }else throw Error('Unknown action');
 room.revision++;return {};
}
function send(res,status,data){const body=JSON.stringify(data);res.writeHead(status,{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});res.end(body);}
function fail(res,error){send(res,error.status||400,{error:String(error.message||'Invalid request').slice(0,180)});}
async function body(req){let buffer='';for await(const chunk of req){buffer+=chunk;if(buffer.length>DATA_LIMIT)throw Object.assign(Error('Request too large'),{status:413});}try{return JSON.parse(buffer||'{}');}catch{throw Error('Invalid JSON');}}
export function createServer(){return http.createServer(async(req,res)=>{
 const origin=req.headers.origin;
 if(req.method==='POST'&&origin&&new URL(origin).host!==req.headers.host){return fail(res,Object.assign(Error('Cross-origin writes not permitted'),{status:403}));}
 let url;try{url=new URL(req.url,'http://localhost');}catch{return fail(res,Error('Invalid URL'));}
 try{
  for(const [code,room] of ROOMS)if(Date.now()-room.created>LIFETIME)ROOMS.delete(code);
  if(req.method==='POST'&&url.pathname==='/api/create'){
   if(ROOMS.size>=MAX_ROOMS)throw Object.assign(Error('Room capacity reached'),{status:503});
   const a=await body(req);let code;do{code=randomCode()}while(ROOMS.has(code));const p=makePlayer(a.name);
   ROOMS.set(code,{code,created:Date.now(),players:[p],phase:'lobby',deadline:null,round:1,revision:1,offers:[]});return send(res,200,{code,token:p.token,player:p.id});
  }
  if(req.method==='POST'&&url.pathname==='/api/join'){
   const a=await body(req),code=String(a.code||'').toUpperCase();const room=ROOMS.get(code);if(!room)throw Error('Room not found.');
   if(room.players.length>=2)throw Error('Room is full (two builders for S0).');const p=makePlayer(a.name);room.players.push(p);room.phase='build';room.deadline=Date.now()+ROUND_MS;room.revision++;
   return send(res,200,{code,token:p.token,player:p.id});
  }
  if(url.pathname==='/api/state'&&req.method==='GET'){
   const {room}=status(String(url.searchParams.get('room')||'').toUpperCase(),String(req.headers.authorization||'').replace(/^Bearer /,''));return send(res,200,publicRoom(room,String(req.headers.authorization||'').replace(/^Bearer /,'')));
  }
  if(url.pathname==='/api/action'&&req.method==='POST'){
   const a=await body(req),{room,p}=status(String(a.room||'').toUpperCase(),String(req.headers.authorization||'').replace(/^Bearer /,''));
   if(typeof a.requestId!=='string'||!/^[-\w]{8,80}$/.test(a.requestId))throw Error('Missing action ID');
   if(p.seen.has(a.requestId))return send(res,200,p.seen.get(a.requestId));
   if(a.type==='test'){
    if(room.phase!=='build'||p.finished)throw Error('Workshop is unavailable.');
    return send(res,200,{state:publicRoom(room,p.token),simulation:simulate(p.build)});
   }
   const out=action(room,p,a);const result={state:publicRoom(room,p.token),...out};
   if(p.seen.size>=100)p.seen.clear();p.seen.set(a.requestId,result);return send(res,200,result);
  }
  if(req.method!=='GET')return fail(res,Object.assign(Error('Method not allowed'),{status:405}));
  const assets={'/':'index.html','/index.html':'index.html','/app.mjs':'app.mjs','/styles.css':'styles.css'};
  const filename=assets[url.pathname];if(!filename)return fail(res,Object.assign(Error('Not found'),{status:404}));
  const bytes=await readFile(path.join(PUBLIC,filename));res.writeHead(200,{
   'Content-Type':filename.endsWith('.mjs')?'text/javascript; charset=utf-8':filename.endsWith('.css')?'text/css; charset=utf-8':'text/html; charset=utf-8',
   'Content-Security-Policy':"default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
   'X-Content-Type-Options':'nosniff','Cache-Control':'no-cache'});res.end(bytes);
 }catch(err){fail(res,err);}
});}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const port=Number(process.env.PORT||8765);if(!Number.isInteger(port)||port<1||port>65535)throw Error('Invalid PORT');
 createServer().listen(port,'0.0.0.0',()=>console.log(`The Great Rescue running at http://localhost:${port}`));
}

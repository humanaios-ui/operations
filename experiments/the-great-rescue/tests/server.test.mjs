import test from 'node:test';import assert from 'node:assert/strict';import {createServer} from '../server.mjs';
const listen=async()=>{const server=createServer();await new Promise(ok=>server.listen(0,'127.0.0.1',ok));return {server,url:`http://127.0.0.1:${server.address().port}`};};
async function request(url,path,obj,token){let r=await fetch(url+path,{method:obj===undefined?'GET':'POST',headers:{'content-type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},body:obj===undefined?undefined:JSON.stringify(obj)});return {status:r.status,...await r.json()};}
const uid=()=>crypto.randomUUID();
test('two independent clients can create/join, see shared state, place/test, score and finish',async()=>{
 const {server,url}=await listen();try{
  const a=await request(url,'/api/create',{name:'Engineer One'});assert.equal(a.status,200);assert.match(a.code,/^[A-Z2-9]{6}$/);
  const b=await request(url,'/api/join',{name:'Engineer Two',code:a.code});assert.equal(b.status,200);assert.notEqual(a.token,b.token);
  const sa=await request(url,`/api/state?room=${a.code}`,undefined,a.token),sb=await request(url,`/api/state?room=${a.code}`,undefined,b.token);
  assert.equal(sa.phase,'build');assert.equal(sb.phase,'build');assert.equal(sa.players.length,2);
  assert.equal(sb.players[0].inventory,null,'other player inventory must not be exposed');
  const act=(actor,type,more={})=>request(url,'/api/action',{room:a.code,requestId:uid(),type,...more},actor.token);
  const before=await act(a,'test');assert.equal(before.simulation.success,false);
  await act(a,'inspect',{item:'coil'});
  for(const c of [2,5,8,11]){const z=await act(a,'place',{part:'beam',c,r:4,angle:0});assert.equal(z.status,200);}
  let own=await act(a,'test');assert.equal(own.simulation.success,true);let official=await act(a,'official');
  assert.equal(official.record.score.completion,40);const again=await act(a,'official');assert.equal(again.status,200);
  assert.equal((await act(a,'official')).status,400,'third attempt is rejected');
  const myBefore=(await request(url,`/api/state?room=${a.code}`,undefined,a.token)).players[0].build.length;
  assert.equal((await act(b,'remove',{id:official.state.players[0].build[0].id})).status,400,'cannot remove another builder parts');
  assert.equal((await request(url,`/api/state?room=${a.code}`,undefined,a.token)).players[0].build.length,myBefore);
  await act(a,'finish');await act(b,'official');await act(b,'finish');
  const end=await request(url,`/api/state?room=${a.code}`,undefined,b.token);assert.equal(end.phase,'results');assert.deepEqual(end.results.champions,[a.player]);
  const vote=await act(b,'vote',{player:a.player});assert.equal(vote.status,200);assert.deepEqual(vote.state.results.honors.ingenuity,[a.player]);
  await act(a,'rematch');const next=await request(url,`/api/state?room=${a.code}`,undefined,a.token);assert.equal(next.phase,'build');assert.equal(next.round,2);
 }finally{await new Promise(ok=>server.close(ok));}
});
test('room bounds, bearer authentication, duplicate action IDs, and trade consent',async()=>{
 const {server,url}=await listen();try{
  const a=await request(url,'/api/create',{name:'A'}), b=await request(url,'/api/join',{code:a.code,name:'B'});
  assert.equal((await request(url,'/api/join',{code:a.code,name:'C'})).status,400);
  assert.equal((await request(url,`/api/state?room=${a.code}`)).status,401);
  const id=uid();const payload={room:a.code,type:'place',requestId:id,part:'spring',c:4,r:3,angle:0};
  const first=await request(url,'/api/action',payload,a.token);assert.equal(first.status,200);
  const repeated=await request(url,'/api/action',payload,a.token);assert.equal(repeated.state.revision,first.state.revision,'replay must be idempotent');
  const o=await request(url,'/api/action',{room:a.code,type:'offer',requestId:uid(),to:b.player,part:'ramp'},a.token);assert.equal(o.status,200);
  let pending=(await request(url,`/api/state?room=${a.code}`,undefined,b.token)).offers;assert.equal(pending.length,1);
  assert.equal((await request(url,'/api/action',{room:a.code,type:'answerOffer',requestId:uid(),id:pending[0].id,accept:true},a.token)).status,400);
  const accepted=await request(url,'/api/action',{room:a.code,type:'answerOffer',requestId:uid(),id:pending[0].id,accept:true},b.token);
  assert.equal(accepted.status,200);assert.equal(accepted.state.players[1].inventory.ramp,3);
 }finally{await new Promise(ok=>server.close(ok));}
});

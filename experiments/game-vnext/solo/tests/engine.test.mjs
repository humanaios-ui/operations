import test from 'node:test';
import assert from 'node:assert/strict';
import {create,advance,choices,witness,setWitness,validateImport,RULES} from '../engine.mjs';

const step=(s,id)=>advance(s,id);
const chain=(s,a)=>a.reduce(step,s);
const rest=(s,n)=>{while(s.tick<n)s=step(s,'REST');return s;};

test('Control path is reachable at the twenty-tick decision',()=>{
 let s=chain(create('Aster'),['MOVE:SANCTUARY','MISSION:M048','MOVE:HAVEN']);
 s=rest(s,18);s=chain(s,['MOVE:SHAFT','MOVE:FURNACE','BURN:CONTROL']);
 assert.equal(s.tick,21);assert.equal(s.ending,'CONTROL');
});

test('Awakening requires voice contact, then a player-chosen rupture at tick >=12',()=>{
 let s=chain(create('Aster'),['MOVE:SHAFT','MOVE:ROOT','MOVE:RN2','MISSION:M045','MOVE:ROOT','MOVE:SANCTUARY']);
 s=rest(s,11);s=chain(s,['MOVE:ROOT','MISSION:M041:SHATTER','MOVE:SHAFT','MOVE:HAVEN']);
 s=rest(s,18);s=chain(s,['MOVE:SHAFT','MOVE:FURNACE','BURN:AWAKENING']);
 assert.equal(s.ending,'AWAKENING');assert.equal(s.tick,21);assert(s.flags.includes('SHATTER'));
});

test('Severance mission and local tether are reachable without circular prerequisite',()=>{
 let s=chain(create('Aster','Warden'),['MOVE:SANCTUARY','MISSION:M049','MOVE:HAVEN','MOVE:RELAY',
 'MOVE:TRANSIT','MOVE:NULL_ORBIT','REST','MISSION:M046','MOVE:NULL_CAP','SEVER']);
 assert.equal(s.ending,'SEVERANCE');assert.equal(s.fragments,0);assert(s.tick<27);
});

test('Invalid actions are free; thirty legal ticks lead to the timeout',()=>{
 let s=create();assert.throws(()=>advance(s,'BURN:CONTROL'));assert.equal(s.tick,0);
 s=rest(s,30);assert.equal(s.ending,'TIMEOUT');assert.deepEqual(choices(s),[]);
 assert(s.events.some(e=>e.description.includes('shield')));
});

test('Read-only Witness is opt-in, cited and cannot advise or change event state',()=>{
 let s=create('Aster');assert.match(witness(s,'beginning'),/off/i);
 s=setWitness(s,true);const before=JSON.stringify(s);
 assert.match(witness(s,'beginning'),/EV-001/);
 assert.match(witness(s,'unknown'),/Not recorded/);
 assert.equal(JSON.stringify(s),before);
});

test('Correctly distinguishes shield contact tick27 from center tick30',()=>{
 assert.equal(RULES.shieldContactTick,27);assert.equal(RULES.centerTick,30);
});

test('Save import rejects forged event IDs',()=>{
 let s=create('Aster');assert.deepEqual(validateImport(s),s);
 s.events[0].id='FAKE';assert.throws(()=>validateImport(s));
});

test('cost-zero mission M040 stays available when supplies are zero',()=>{
 const s=create('Tester');s.supplies=0;
 assert(choices(s).some(x=>x.id==='MISSION:M040'));
 const after=advance(s,'MISSION:M040');
 assert.equal(after.supplies,2);assert.equal(after.tick,1);assert.equal(s.tick,0);
});
test('Sight Lattice free transit remains legal at zero supplies',()=>{
 const s=create('Tester');s.location='RELAY';s.supplies=0;s.upgrades=['Sight Lattice'];
 assert(choices(s).some(x=>x.id==='MOVE:TRANSIT'));
 const after=advance(s,'MOVE:TRANSIT');
 assert.equal(after.supplies,0);assert.equal(after.tick,1);
});
test('exhausted remote location recovers, does not deadlock',()=>{
 const s=create('Tester');s.location='FURNACE';s.supplies=0;
 assert(choices(s).some(x=>x.id==='SCAVENGE'));
 const next=advance(s,'SCAVENGE');assert.equal(next.supplies,2);assert.equal(next.resonance,1);
 assert.equal(next.tick,1);
});
test('all exhausted nonterminal locations retain an advancing option',()=>{
 for(const location of ['HAVEN','SANCTUARY','SHAFT','ROOT','RN2','FURNACE','RELAY','TRANSIT','NULL_ORBIT','NULL_CAP']){
  const s=create('Tester');s.location=location;s.supplies=0;
  const acts=choices(s);
  assert(acts.length>0,location);
  const first=advance(s,acts[0].id);assert.equal(first.tick,1,location);
 }
});
test('real reviewer deadlock route can continue without changing legacy save authority',()=>{
 let s=chain(create('Tester','Seeker'),['MOVE:SHAFT','MOVE:ROOT','MOVE:RN2','MISSION:M045','MOVE:ROOT','MOVE:SHAFT','MOVE:FURNACE']);
 assert.equal(s.supplies,0);assert(choices(s).some(x=>x.id==='SCAVENGE'));
 const recovered=advance(s,'SCAVENGE');assert.equal(recovered.tick,8);assert(recovered.supplies>0);
});

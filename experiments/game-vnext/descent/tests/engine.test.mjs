import test from 'node:test';import assert from 'node:assert/strict';
import {startRun,advance,legalActions,validImport,status,witnessRecall,MAX_TICK,HAZARDS,WALLS} from '../engine.mjs';
const steps=(s,ss)=>ss.reduce((state,id)=>advance(state,id),s);
const north=['MOVE:N','MOVE:E','MOVE:E','MOVE:E','MOVE:E','MOVE:E','MOVE:S','SECURE','MOVE:E','EXTRACT'];
const south=['MOVE:S','MOVE:E','MOVE:E','MOVE:E','MOVE:E','MOVE:E','MOVE:N','SECURE','MOVE:E','EXTRACT'];
test('north route completes with optional relay and faction encounter without model',()=>{
 let s=startRun('QUIET');s=steps(s,['MOVE:N','MOVE:E','MOVE:E','MOVE:E','MOVE:N','STABILIZE','MOVE:S','MOVE:E','SIGNAL:ACCEPT','MOVE:E','MOVE:S','SECURE','MOVE:E','EXTRACT']);
 assert.equal(s.finished,'EXTRACTED');assert.equal(s.secondary,true);assert.equal(s.signal,'accept');assert.equal(s.specimen,true);assert(s.events.some(e=>e.type==='FACTION'));assert(s.runTick<=30);
});
test('north direct route works without accepting faction contact',()=>{
 const s=steps(startRun('QUIET'),north);assert.equal(s.finished,'EXTRACTED');assert.equal(s.signal,'unheard');
});
test('southern route is viable with Prism Ward and one conscious guard action',()=>{
 let s=startRun('WARD');s=steps(s,south.slice(0,-3)); // stop at specimen tile
 assert.equal(s.shields,0);assert.equal(s.resonance,0);
 s=steps(s,['GUARD','SECURE','MOVE:E','EXTRACT']);assert.equal(s.finished,'EXTRACTED');
});
test('two unshielded southern hazards cause readable failure, never AI rescue',()=>{
 const s=steps(startRun('QUIET'),south.slice(0,5));assert.equal(s.finished,'FRACTURED');
 assert.match(s.events.at(-1).detail,/threshold/);
});
test('invalid actions, zero supplies and finished states are safe',()=>{
 let s=startRun();const before=JSON.stringify(s);assert.throws(()=>advance(s,'SECURE'));assert.equal(JSON.stringify(s),before);
 s=advance(s,'ABORT');assert.equal(s.finished,'WITHDREW');assert.deepEqual(legalActions(s),[]);assert.throws(()=>advance(s,'MOVE:N'));
});
test('every accepted action uses one run tick; authoritative world tick never moves',()=>{
 let s=startRun('WARD');let n=advance(s,'MOVE:N');assert.equal(n.runTick,1);assert.equal(n.worldTick,null);
 assert.equal(s.runTick,0);assert.equal(MAX_TICK,30);
});
test('replay fixed seed is deterministic and final events are stable',()=>{
 const a=steps(startRun('QUIET'),north),b=steps(startRun('QUIET'),north);
 assert.deepEqual(a,b);assert.deepEqual(validImport(a),a);
});
test('malformed and fabricated saves rejected, no Witness gameplay tools',()=>{
 let s=startRun();s.pos.x=20;assert.throws(()=>validImport(s));
 let u=startRun();u.events[0].id='SPOOF';assert.throws(()=>validImport(u));
 assert.match(witnessRecall(startRun()),/no AI/i);
});
test('intent catalogue has no raw code execution, network or outside player data',()=>{
 const choices=legalActions(startRun());assert(!choices.some(c=>/EXEC|PROMPT|WRITE|NETWORK/.test(c.id)));
 assert(WALLS.includes('2,2'));assert(HAZARDS.includes('3,3'));
});

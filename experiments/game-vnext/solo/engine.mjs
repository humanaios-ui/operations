/* Independent, deterministic prototype. No credentials, remote services or AI tools. */
export const RULES = Object.freeze({maxTick:30,frontSpeed:0.09,shieldContactTick:27,centerTick:30,
  breachTick:20,tetherCollapseTick:25,latticeFailureTick:12,
  orbitalCenter:[1,0],nullCenter:[2.78,1.95],nullRadius:0.28});
export const NODES = Object.freeze({
  HAVEN:{name:'Cinder Quay',frame:'surface',x:20,y:70,links:['SANCTUARY','SHAFT','RELAY'],desc:'First-generation settlement beneath the old extraction towers.'},
  SANCTUARY:{name:'Rootvault',frame:'surface',x:33,y:44,links:['HAVEN','ROOT'],desc:'Surface refuge and a place of bargains. First hub.'},
  SHAFT:{name:'Ashshaft',frame:'depth',x:41,y:80,links:['HAVEN','ROOT','FURNACE'],desc:'A fault full of tools, witnesses and dangerous fragments.'},
  ROOT:{name:'Living Seam',frame:'depth',x:52,y:55,links:['SHAFT','SANCTUARY','RN2'],desc:'Lattice roots hold a wounded seal.'},
  RN2:{name:'Whisper Node',frame:'depth',x:56,y:30,links:['ROOT'],desc:'Here the Murmur speaks. It is not your Witness.'},
  FURNACE:{name:'Crucible',frame:'depth',x:66,y:83,links:['SHAFT'],desc:'The pressure breach. An irreversible choice becomes possible at tick 20.'},
  RELAY:{name:'Evacuation Relay',frame:'surface',x:18,y:42,links:['HAVEN','TRANSIT'],desc:'The old orbital court fled. A launch corridor remains.'},
  TRANSIT:{name:'Far Passage',frame:'transit',x:15,y:20,links:['RELAY','NULL_ORBIT'],desc:'Fictional accelerated voyage; one action per leg. Not a real space elevator.'},
  NULL_ORBIT:{name:'Outer Haven',frame:'orbit',x:77,y:22,links:['TRANSIT','NULL_CAP'],desc:'An orbital refuge 2.64 AU from the homeworld. Second hub.'},
  NULL_CAP:{name:'Stillground',frame:'habitat',x:85,y:49,links:['NULL_ORBIT'],desc:'The surface of the distant refuge habitat. A local tether connects to its orbital ring.'}
});
export const ACTORS=Object.freeze({
  A:'Nera Vale',B:'Ilyr Vale',C:'Saren Vale',D:'Vey Oss',E:'Oren Thale',F:'Archon Solven',G:'Tes Ro',H:'The Murmur'
});
export const FORMS=['Seeker','Warden','Builder','Memory-Bearer'];
const perRoute={
  M040:{name:'Pressure Is Attention',place:'HAVEN',open:0,close:29,description:'Repair the intake while families flee. Gain two supplies.',cost:0,reward:2},
  M044:{name:'Strike at the Shafts',place:'SHAFT',open:1,close:19,description:'Choose rescue, not blind destruction. Recover supplies.',cost:1,reward:2},
  M047:{name:'The Engineer’s Archive',place:'SHAFT',open:1,close:19,description:'Record the buried pact. Earn insight.',cost:1,insight:2},
  M043:{name:'The Temple’s Tithe',place:'RELAY',open:1,close:18,description:'Intercept evacuated orbital records; no impossible trip to the destroyed ring.',cost:1,insight:1},
  M048:{name:'The Inquisitor’s Offer',place:'SANCTUARY',open:1,close:18,description:'An evacuated envoy offers control. Open the Control route.',cost:1,ally:'CONTROL'},
  M045:{name:'The Voice in the Stone',place:'RN2',open:1,close:19,description:'Hear the Murmur, a fictional NPC with no access to your private archive.',cost:1,ally:'AWAKENING',resonance:1},
  M041:{name:'The Dying Lattice',place:'ROOT',open:12,close:19,description:'Decide whether to rupture the surviving roots. Open Awakening’s Furnace option.',cost:1,requires:['M045'],flag:'SHATTER'},
  M049:{name:'The Tether’s Price',place:'SANCTUARY',open:1,close:24,description:'Secure passage remotely with a refugee envoy BEFORE reaching Outer Haven.',cost:1,flag:'TETHER_SECURED',ally:'SEVERANCE'},
  M046:{name:'The Null Petition',place:'NULL_ORBIT',open:1,close:26,description:'Win refuge before the advancing wave touches the shield.',cost:1,requires:['M049'],flag:'PETITION_GRANTED'},
  M042:{name:'The Controlled Burn',place:'FURNACE',open:20,close:29,description:'Commit to an ending at the Crucible. Select an available outcome.',cost:1}
};
export const MISSIONS=Object.freeze(perRoute);
const MAX_LOG=200;
function clean(s,max=40){return String(s||'').replace(/[\x00-\x1f\x7f<>]/g,'').trim().slice(0,max);}
function log(s,type,description){
 const next={id:`EV-${String(s.events.length+1).padStart(3,'0')}`,tick:s.tick,type,description};
 s.events.push(next); if(s.events.length>MAX_LOG)throw new Error('log limit reached');return next;
}
export function create(name='Traveler',form='Seeker'){
 if(!FORMS.includes(form))throw new Error('unknown form');
 const s={version:1,name:clean(name)||'Traveler',form,tick:0,location:'HAVEN',supplies:form==='Warden'?8:7,
   insight:form==='Seeker'||form==='Memory-Bearer'?1:0,resonance:0,fragments:0,history:[],done:[],flags:[],allegiances:[],
   upgrades:[],ending:null,events:[],witnessEnabled:false};
 log(s,'GENESIS',`${s.name} chose ${form} and entered Cinder Quay.`);return s;
}
export function radiusAt(tick){return Math.min(30,Math.max(0,tick))*RULES.frontSpeed;}
export function frontStatus(tick){return tick<27?'approaching':tick<30?'shield_contact':'center_crossing';}
function validState(s){return s&&Number.isInteger(s.tick)&&s.tick>=0&&s.tick<=30&&NODES[s.location]&&Array.isArray(s.events)&&s.events.length<=MAX_LOG;}
export function choices(s){
 if(!validState(s)||s.ending||s.tick>=30)return [];
 const opts=[];const canPay=s.supplies>=1;
 for(const id of NODES[s.location].links){
  if(id==='NULL_CAP' && !s.flags.includes('TETHER_SECURED'))continue;
  if(id==='RELAY'&&s.location==='TRANSIT'&&s.tick>=30)continue;
  const travelCost=id==='TRANSIT'&&s.upgrades.includes('Sight Lattice')?0:1;
  if(s.supplies<travelCost)continue;
  opts.push({id:`MOVE:${id}`,label:`Travel → ${NODES[id].name}`,kind:'travel',detail:(id==='TRANSIT'&&s.upgrades.includes('Sight Lattice')?'Sight Lattice: 0 supplies, 1 tick.':'Costs 1 supply and 1 tick.')});
 }
 const atHub=['HAVEN','SANCTUARY','NULL_ORBIT'].includes(s.location);
 if(atHub)opts.push({id:'REST',label:'Rest and replenish',kind:'resource',detail:'+3 supplies, 1 tick. No hidden penalty.'});
 if(!atHub&&s.supplies===0)opts.push({id:'SCAVENGE',label:'Scavenge emergency supplies',kind:'resource',detail:'+2 supplies and +1 Resonance, 1 tick; may cause time-out.'});
 if(s.location==='FURNACE'&&s.fragments>0)opts.push({id:'CONVERT:FRAGMENT',label:'Burn a Fragment for supplies',kind:'resource',detail:'Consume 1 Fragment, +3 supplies, +2 Resonance, 1 tick.'});
 if(s.location==='SHAFT'&&s.tick<19)opts.push({id:'FRAGMENT',label:'Gather one forbidden fragment',kind:'resource',detail:'+1 Fragment, +2 Resonance, 1 tick. Can be relinquished later.'});
 for(const [id,m] of Object.entries(MISSIONS)){
  if(id==='M042'||s.done.includes(id)||m.place!==s.location||s.tick<m.open||s.tick>m.close||s.supplies<m.cost)continue;
  if(m.requires&&!m.requires.every(x=>s.done.includes(x)))continue;
  if(id==='M044'){for(const v of ['RESCUE','SABOTAGE'])opts.push({id:`MISSION:${id}:${v}`,label:`${m.name}: ${v==='RESCUE'?'Rescue workers':'Sabotage the drills'}`,kind:'mission',detail:v==='RESCUE'?'Save people, gain 2 supplies.':'Break machines, gain 3 supplies, raise Resonance.'});}
  else if(id==='M041'){for(const v of ['SHATTER','REINFORCE'])opts.push({id:`MISSION:${id}:${v}`,label:`${m.name}: ${v==='SHATTER'?'Shatter the roots':'Reinforce the roots'}`,kind:'mission',detail:v==='SHATTER'?'Open an Awakening path; fracture containment.':'Keep the surviving lattice; Awakening route remains sealed.'});}
  else opts.push({id:`MISSION:${id}`,label:m.name,kind:'mission',detail:m.description});
 }
 if(s.location==='FURNACE'&&s.tick>=20&&s.tick<30&&s.done.includes('M048')&&canPay)
   opts.push({id:'BURN:CONTROL',label:'End: The Crowned Grid',kind:'ending',detail:'Control the Deepheart, halt the front; accept the costs to the world.'});
 if(s.location==='FURNACE'&&s.tick>=20&&s.tick<30&&s.done.includes('M045')&&s.flags.includes('SHATTER')&&canPay)
   opts.push({id:'BURN:AWAKENING',label:'End: The Open Earth',kind:'ending',detail:'Release the Deepheart; risk catastrophic spread.'});
 if(s.location==='NULL_CAP'&&s.done.includes('M046')&&s.done.includes('M049')&&s.tick<30&&canPay)
   opts.push({id:'SEVER',label:'End: Cut the Last Thread',kind:'ending',detail:'Renounce all Fragments and secure a fragile refuge.'});
 if(s.location==='SANCTUARY'&&s.insight>=2&&!s.upgrades.includes('Sight Lattice'))
   opts.push({id:'EVOLVE:Sight Lattice',label:'Evolve: Sight Lattice',kind:'evolution',detail:'Spend 2 insight; explicitly choose a fictional visual mutation.'});
 return opts;
}
function timeAdvance(s){s.tick++; if(s.tick===12)log(s,'WORLD','Lattice cracked. Root nodes remain reachable for a short window.');
 if(s.tick===20)log(s,'WORLD','Crucible burn becomes irreversible. The approaching front is now a full breach.');
 if(s.tick===25&&!s.flags.includes('TETHER_SECURED'))log(s,'WORLD','Unsecured local tether failed.');
 if(s.tick===27)log(s,'WORLD','Cinder Veil contacts Outer Haven shield. Its protection is limited but holds until tick 30.');
 if(s.tick===30){log(s,'WORLD','Cinder Veil reaches the center of Outer Haven.');if(!s.ending)s.ending='TIMEOUT';}
}
export function advance(s,choiceId){
 const allowed=choices(s).find(c=>c.id===choiceId);if(!allowed)throw new Error('Choice unavailable. Tick and state unchanged.');
 const n=structuredClone(s);const [cmd,key]=choiceId.split(':');
 if(cmd==='MOVE'){
   n.supplies-=key==='TRANSIT'&&n.upgrades.includes('Sight Lattice')?0:1;n.location=key;log(n,'TRAVEL',`Entered ${NODES[key].name}.`);
 }else if(choiceId==='REST'){
   n.supplies=Math.min(12,n.supplies+3);log(n,'REST','Recovered supplies at a hub.');
 }else if(choiceId==='SCAVENGE'){
   n.supplies=Math.min(12,n.supplies+2);n.resonance=Math.min(10,n.resonance+1);
   log(n,'RECOVERY','Scavenged 2 supplies under risk of time and Resonance.');
 }else if(choiceId==='CONVERT:FRAGMENT'){
   n.fragments--;n.supplies=Math.min(12,n.supplies+3);n.resonance=Math.min(10,n.resonance+2);log(n,'RESOURCE','Consumed a fragment to recover supplies; resonance rose.');
 }else if(choiceId==='FRAGMENT'){
   n.fragments++;n.resonance=Math.min(10,n.resonance+2);log(n,'RESOURCE','Carried a fragment. Resonance increased.');
 }else if(cmd==='MISSION'){
   const m=MISSIONS[key];const variant=choiceId.split(':')[2]||null;n.supplies-=m.cost;n.done.push(key);if(m.reward)n.supplies=Math.min(12,n.supplies+m.reward);
   if(key==='M044'&&variant==='SABOTAGE'){n.supplies=Math.min(12,n.supplies+1);n.resonance=Math.min(10,n.resonance+2);n.flags.push('SABOTAGED_SHAFT');}
   if(key==='M044'&&variant==='RESCUE')n.flags.push('RESCUED_WORKERS');
   if(m.insight)n.insight+=m.insight;if(m.resonance)n.resonance=Math.min(10,n.resonance+m.resonance);
   if(m.flag && (key!=='M041'||variant==='SHATTER'))n.flags.push(m.flag);
   if(key==='M041'&&variant==='REINFORCE')n.flags.push('ROOTS_REINFORCED');if(m.ally&&!n.allegiances.includes(m.ally))n.allegiances.push(m.ally);
   log(n,'MISSION',`${m.name} ${variant||'completed'} (${key}).`);
 }else if(cmd==='EVOLVE'){
   n.insight-=2;n.upgrades.push(key);log(n,'EVOLUTION',`${n.name} explicitly chose ${key}.`);
 }else if(cmd==='BURN'){
   n.supplies--;n.done.push('M042');n.ending=key;log(n,'ENDING',key==='CONTROL'?'Crowned Grid: extraction reigns; front halts.':'Open Earth: containment shattered; survival uncertain.');
 }else if(choiceId==='SEVER'){
   n.supplies--;n.fragments=0;n.resonance=0;n.flags.push('FRAGMENTS_RENOUNCED');n.ending='SEVERANCE';
   log(n,'ENDING','Last Thread Cut: sacrifice all fragments to sever the old tie. New settlement remains fragile.');
 }else throw new Error('invalid command');
 timeAdvance(n);return n;
}
// W1 reads supplied events, never mutates them; do not expose any action tools here.
export function witness(s,question){
 if(!s.witnessEnabled)return 'Witness memory is off. Enable it to view your record.';
 if(question==='beginning')return s.events.filter(e=>e.type==='GENESIS').map(e=>`[${e.id}] ${e.description}`).join('\n')||'Not recorded.';
 if(question==='journey')return s.events.filter(e=>['TRAVEL','MISSION','EVOLUTION','ENDING'].includes(e.type)).slice(-9).map(e=>`[${e.id} | tick ${e.tick}] ${e.description}`).join('\n')||'No journey events recorded.';
 if(question==='unknown')return 'Not recorded. The absence of an event is not proof of intentional erasure. I cannot forecast, direct choices, or act.';
 return 'I only recall recorded campaign history. No advice or future events.';
}
export function setWitness(s,enabled){const n=structuredClone(s);n.witnessEnabled=enabled===true;return n;}
export function validateImport(s){if(!validState(s)||!FORMS.includes(s.form)||!Array.isArray(s.done)||!Array.isArray(s.flags)||!Array.isArray(s.upgrades)||!Array.isArray(s.allegiances)||!Number.isFinite(s.supplies)||s.supplies<0||s.supplies>12||s.events.some((e,i)=>e.id!==`EV-${String(i+1).padStart(3,'0')}`))throw Error('Unsupported or altered local demo save');return structuredClone(s);}
export const ENDING_TEXT={CONTROL:'THE CROWNED GRID — The front stops. Extraction endures. Order survives, but the future is unjust.',AWAKENING:'THE OPEN EARTH — The sealed presence awakes. Constraint ends; the cost to life is unresolved.',SEVERANCE:'THE LAST THREAD — The refuge survives, no longer fed by fragments. Freedom remains fragile.',TIMEOUT:'THE VEIL — The wave reaches Outer Haven. The remaining world must live with the consequences.'};


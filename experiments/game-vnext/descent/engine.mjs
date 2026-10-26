/** The Sounding — R2 independent deterministic tactical mission.
 * Fictional, no AI, network, personal data, or real gameplay save authority.
 * Every accepted action advances exactly one run tick. World time is read only here.
 */
export const RULESET='R2-AI-OFF-0.1';
export const WIDTH=7, HEIGHT=5, MAX_TICK=30;
export const WALLS=Object.freeze(['2,2','3,2']);
export const HAZARDS=Object.freeze(['3,3','4,3']);
export const SIGNALS=Object.freeze(['4,1','4,3']);
export const DECKS=Object.freeze({
 QUIET:{name:'Quiet Footfall',description:'Every second move leaves no Attention trace. No shield.'},
 WARD:{name:'Prism Ward',description:'Two hazard shields. Movement makes normal noise.'}
});
const isTile=(p,x,y)=>p.x===x&&p.y===y;
const key=(x,y)=>`${x},${y}`;
const clamp=(v)=>Math.max(0,Math.min(10,v));
function event(s,type,detail){s.events.push({id:`R2-${String(s.events.length+1).padStart(3,'0')}`,runTick:s.runTick,type,detail});}
export function startRun(deck='QUIET', seed='M045-A'){
 if(!Object.hasOwn(DECKS,deck))throw new Error('Unknown Dawn Deck choice');
 if(seed!=='M045-A')throw new Error('Unsupported mission seed');
 const s={ruleset:RULESET,mission:'M045',seed,deck,runTick:0,worldTick:null,pos:{x:0,y:2},
  attention:0,resonance:0,supplies:4,shields:deck==='WARD'?2:0,moveCount:0,
  signal:'unheard',secondary:false,specimen:false,finished:null,events:[]};
 event(s,'ENTER','Descent starts at The Sounding. One specimen, one extraction, two routes.');
 event(s,'DECK',`${DECKS[deck].name} selected by player.`);
 return s;
}
function safeState(s){return s&&s.ruleset===RULESET&&s.mission==='M045'&&Number.isInteger(s.runTick)&&s.runTick>=0&&s.runTick<=30&&
 Number.isInteger(s.pos?.x)&&Number.isInteger(s.pos?.y)&&s.pos.x>=0&&s.pos.x<WIDTH&&s.pos.y>=0&&s.pos.y<HEIGHT&&!WALLS.includes(key(s.pos.x,s.pos.y))&&Object.hasOwn(DECKS,s.deck)&&
 Number.isInteger(s.attention)&&s.attention>=0&&s.attention<=10&&Number.isInteger(s.resonance)&&s.resonance>=0&&s.resonance<=10&&Number.isInteger(s.supplies)&&s.supplies>=0&&s.supplies<=4&&Number.isInteger(s.shields)&&s.shields>=0&&s.shields<=2&&
 Array.isArray(s.events)&&s.events.length<=70&&s.events.every((e,i)=>e.id===`R2-${String(i+1).padStart(3,'0')}`);}
export function validImport(s){if(!safeState(s))throw new Error('Invalid untrusted demo save');return structuredClone(s);}
export function legalActions(s){
 if(!safeState(s))throw new Error('Invalid run state');
 if(s.finished||s.runTick>=MAX_TICK)return [];
 const actions=[];
 for(const [id,dx,dy] of [['N',0,-1],['S',0,1],['E',1,0],['W',-1,0]]){
  const x=s.pos.x+dx,y=s.pos.y+dy;
  if(x>=0&&x<WIDTH&&y>=0&&y<HEIGHT&&!WALLS.includes(key(x,y)))actions.push({id:`MOVE:${id}`,label:`Move ${id}`,description:'1 action. Hazards and noise are visible.'});
 }
 if(s.supplies>0&&s.attention>0)actions.push({id:'GUARD',label:'Shelter and listen',description:'1 supply, 1 action; reduce Attention by 3.'});
 if(s.supplies>0&&isTile(s.pos,3,0)&&!s.secondary)actions.push({id:'STABILIZE',label:'Stabilize relay (optional)',description:'1 supply, 1 action; lower Resonance and record a secondary success.'});
 if(s.supplies>0&&SIGNALS.includes(key(s.pos.x,s.pos.y))&&s.signal==='unheard'){
  actions.push({id:'SIGNAL:ACCEPT',label:'Accept the rhythmic warning',description:'1 supply, 1 action; Attention -3. Faction offers no secret solution.'});
  actions.push({id:'SIGNAL:DECLINE',label:'Decline the warning',description:'1 action; preserve supplies. The beings do not force contact.'});
 }
 if(s.supplies>0&&isTile(s.pos,5,2)&&!s.specimen)actions.push({id:'SECURE',label:'Secure the specimen',description:'Primary objective. 1 supply, 1 action.'});
 if(isTile(s.pos,6,2)&&s.specimen)actions.push({id:'EXTRACT',label:'Extract from The Sounding',description:'Exit with primary objective. 1 action.'});
 actions.push({id:'ABORT',label:'Withdraw from mission',description:'Record voluntary withdrawal. No penalty to external player identity.'});
 return actions;
}
export function advance(s,id){
 const allowed=legalActions(s).find(a=>a.id===id);
 if(!allowed)throw new Error('Action unavailable; no tick or resource consumed.');
 const n=structuredClone(s);n.runTick++;
 if(id.startsWith('MOVE:')){
  const d=id.slice(5);const p={N:[0,-1],S:[0,1],E:[1,0],W:[-1,0]}[d];
  n.pos.x+=p[0];n.pos.y+=p[1];n.moveCount++;
  const quiet=n.deck==='QUIET'&&n.moveCount%2===0;
  n.attention=clamp(n.attention+(quiet?0:1));
  const at=key(n.pos.x,n.pos.y);
  if(HAZARDS.includes(at)){
    if(n.shields>0){n.shields--;event(n,'SHIELD',`Ward absorbed resonance at tile ${at}.`);}
    else{n.resonance=clamp(n.resonance+2);event(n,'HAZARD',`The low path raised Resonance at tile ${at}.`);}
  }
  event(n,'MOVE',`Reached ${at} using a ${quiet?'quiet':'audible'} step.`);
 }else if(id==='GUARD'){
  n.supplies--;n.attention=clamp(n.attention-3);event(n,'GUARD','Shelter reduced Attention.');
 }else if(id==='STABILIZE'){
  n.supplies--;n.secondary=true;n.resonance=clamp(n.resonance-2);event(n,'OBJECTIVE','Relay stabilized. Optional task complete.');
 }else if(id.startsWith('SIGNAL:')){
  n.signal=id.slice(7).toLowerCase();
  if(n.signal==='accept'){n.supplies--;n.attention=clamp(n.attention-3);}
  event(n,'FACTION',`Resonant Kin rhythmic warning ${n.signal}ed. Caption: unstable lower passage. No automated player commands.`);
 }else if(id==='SECURE'){
  n.supplies--;n.specimen=true;n.attention=clamp(n.attention+1);event(n,'OBJECTIVE','Player secured the living specimen.');
 }else if(id==='EXTRACT'){
  n.finished='EXTRACTED';event(n,'EXTRACTION',`Specimen delivered. Secondary relay: ${n.secondary?'completed':'not completed'}.`);
 }else if(id==='ABORT'){
  n.finished='WITHDREW';event(n,'WITHDRAWAL','Player withdrew. No forced evolution or campaign settlement.');
 }
 if(!n.finished&&n.resonance>=4){n.finished='FRACTURED';event(n,'FAILURE','Resonance threshold reached. Try a safer route or the ward.');}
 if(!n.finished&&n.attention>=10){n.finished='OVERWHELMED';event(n,'FAILURE','Attention surge overwhelmed the route. Shelter or heed a warning.');}
 if(!n.finished&&n.runTick>=MAX_TICK){n.finished='TIMEOUT';event(n,'TIMEOUT','30 accepted actions elapsed. Extraction not completed.');}
 return n;
}
export function status(s){
 if(!safeState(s))throw new Error('Invalid run');
 return {runTick:s.runTick,remaining:30-s.runTick,position:key(s.pos.x,s.pos.y),
  objective:s.specimen?'Specimen secured; reach 6,2':'Secure specimen at 5,2',
  secondary:s.secondary?'Stabilized':'Optional relay at 3,0',
  attention:s.attention,resonance:s.resonance,supplies:s.supplies,shields:s.shields,finished:s.finished,signal:s.signal};
}
// End-user browser demo only: authoritative multiplayer state is deliberately outside R2.
export function witnessRecall(s){return 'Witness gameplay advice is unavailable. This R2 mission uses no AI, cross-campaign memory, or private lineage data.';}

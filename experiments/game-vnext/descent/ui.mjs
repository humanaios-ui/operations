import {startRun,advance,legalActions,validImport,status,WIDTH,HEIGHT,WALLS,HAZARDS,SIGNALS,DECKS} from './engine.mjs';
const KEY='last-thread-r2-local-v01';
const $=id=>document.getElementById(id);
let state=null;
try{const old=localStorage.getItem(KEY);if(old)state=validImport(JSON.parse(old));}catch{state=null;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch{/* local demo remains playable */}}
function render(){
 $('prelude').hidden=!!state;$('mission').hidden=!state;if(!state)return;
 const p=status(state);for(const k of ['remaining','attention','resonance','supplies','shields'])$(k).textContent=String(p[k]);
 $('position').textContent=p.position; $('primary').textContent=p.objective;$('secondary').textContent=p.secondary;
 $('signal').textContent=p.signal==='unheard'?'The Resonant Kin transmit a patterned warning at the signal stones. Captioned and optional.':`You ${p.signal}ed the Resonant Kin warning. They cannot control your character.`;
 $('deckBadge').textContent=DECKS[state.deck].name;
 $('missionState').textContent=state.finished?`RUN ${state.finished} at action ${state.runTick}. Start another run to try a different route.`:
  `Mission active. Tick ${state.runTick}/30. ${p.objective}. Attention ${p.attention}/10, Resonance ${p.resonance}/4.`;
 const grid=$('grid');grid.replaceChildren();
 for(let y=0;y<HEIGHT;y++)for(let x=0;x<WIDTH;x++){
  const cell=document.createElement('div');const k=`${x},${y}`;
  const cls=WALLS.includes(k)?'wall':HAZARDS.includes(k)?'hazard':SIGNALS.includes(k)?'signal':k==='3,0'?'relay':k==='5,2'?'goal':k==='6,2'?'exit':'';
  const you=state.pos.x===x&&state.pos.y===y;
  cell.className='tile '+cls+(you?' you':'');
  cell.textContent=you?'◉':cls==='wall'?'▦':cls==='hazard'?'▒':cls==='signal'?'✦':cls==='relay'?'✛':cls==='goal'?'◇':cls==='exit'?'⇥':'·';
  cell.setAttribute('title',`${k}: ${you?'Player':cls||'open route'}`);grid.append(cell);
 }
 const actions=$('buttons');actions.replaceChildren();for(const a of legalActions(state)){
  const b=document.createElement('button');b.type='button';b.textContent=a.label;if(a.id==='EXTRACT')b.className='success';if(a.id==='ABORT')b.className='caution';
  const hint=document.createElement('small');hint.textContent=a.description;b.append(hint);b.addEventListener('click',()=>{
   try{state=advance(state,a.id);save();render();}catch(error){$('missionState').textContent=error.message;}
  });actions.append(b);
 }
 const history=$('events');history.replaceChildren();for(const e of state.events.slice().reverse()){
  const li=document.createElement('li');li.textContent=`[${e.id}; tick ${e.runTick}] ${e.type}: ${e.detail}`;history.append(li);
 }
}
$('chooseQuiet').addEventListener('click',()=>{state=startRun('QUIET');save();render();});
$('chooseWard').addEventListener('click',()=>{state=startRun('WARD');save();render();});
$('restart').addEventListener('click',()=>{if(!confirm('End local mission and clear local run data? No real game records are affected.'))return;
 try{localStorage.removeItem(KEY);}catch{}state=null;render();});
render();

import {RULES,NODES,MISSIONS,FORMS,ENDING_TEXT,create,choices,advance,radiusAt,frontStatus,witness,setWitness,validateImport} from './engine.mjs';
const KEY='lastthread.prototype.v1';let state=null;
const $=id=>document.getElementById(id);const SVG='http://www.w3.org/2000/svg';
function svg(tag,attrs={},text){const n=document.createElementNS(SVG,tag);for(const [k,v] of Object.entries(attrs))n.setAttribute(k,String(v));if(text)n.textContent=text;return n;}
function save(){try{localStorage.setItem(KEY,JSON.stringify(state));}catch{ /* temporary play still possible */}}
try{const old=localStorage.getItem(KEY);if(old)state=validateImport(JSON.parse(old));}catch{state=null;}
function show(){ $('start').hidden=!!state;$('game').hidden=!state;if(!state)return;
 $('clock').textContent=30-state.tick;$('supplies').textContent=state.supplies;$('insight').textContent=state.insight;
 $('resonance').textContent=state.resonance;$('fragments').textContent=state.fragments;
 $('locname').textContent=NODES[state.location].name;$('placeTitle').textContent=NODES[state.location].name;
 $('placeDesc').textContent=NODES[state.location].desc;
 $('witnessOn').checked=state.witnessEnabled;
 $('worldAlert').textContent=state.tick>=30?'Tick 30: the Veil crossed the Outer Haven center.':state.tick>=27?'Shield first contact. The refuge still has a narrow window.':state.tick>=25&&!state.flags.includes('TETHER_SECURED')?'Unsecured tether collapsed at tick 25.':state.tick>=20?'Crucible breach is irreversible. Choose carefully.':state.tick>=12?'The root lattice has failed; remaining nodes can still be reached.':'A precursor wave expands. Every major action costs one tick.';
 $('progress').value=state.tick;
 $('stateDesc').textContent=state.ending?ENDING_TEXT[state.ending]:`${state.name} · ${state.form} · ${NODES[state.location].name}. The Cinder Veil extends ${radiusAt(state.tick).toFixed(2)} AU (planet-centered display approximation). Shield: ${frontStatus(state.tick)}.`;
 const actions=$('actions');actions.replaceChildren();const c=choices(state);
 if(!c.length){const msg=document.createElement('p');msg.textContent='Campaign concluded. Read the ledger or start again.';actions.append(msg);}
 for(const a of c){const b=document.createElement('button');b.type='button';b.className=a.kind;b.textContent=a.label;
  const d=document.createElement('small');d.textContent=a.detail;b.append(d);b.onclick=()=>{try{state=advance(state,a.id);save();show();}catch(error){$('worldAlert').textContent=error.message;}};actions.append(b);}
 const missions=$('missions');missions.replaceChildren();for(const [id,m] of Object.entries(MISSIONS)){
  const el=document.createElement('span');el.textContent=`${state.done.includes(id)?'✓':'◇'} ${m.name} (${id}) · ${m.open}–${m.close}`;missions.append(el);}
 const ol=$('events');ol.replaceChildren();for(const e of state.events.slice(-40).reverse()){
  const li=document.createElement('li');li.textContent=`[${e.id} · ${e.tick}] ${e.type}: ${e.description}`;ol.append(li);}
 draw();
}
function draw(){const links=$('lines');const nodes=$('nodes');links.replaceChildren();nodes.replaceChildren();const positions={};
 for(const [id,n] of Object.entries(NODES))positions[id]=[n.x*10,n.y*6.2];
 const available=new Set(choices(state).filter(x=>x.kind==='travel').map(x=>x.id.split(':')[1]));
 for(const [id,n] of Object.entries(NODES))for(const to of n.links)if(id<to){const [x1,y1]=positions[id],[x2,y2]=positions[to];
  links.append(svg('line',{x1,y1,x2,y2,class:`link ${(id===state.location&&available.has(to))||(to===state.location&&available.has(id))?'available':''}`}));}
 for(const [id,n] of Object.entries(NODES)){
  const [x,y]=positions[id];const group=svg('g',{class:'node-group',tabindex:'0',role:'group','aria-label':n.name});
  group.append(svg('circle',{cx:x,cy:y,r:id===state.location?13:9,class:'nodedot'+(id===state.location?' active':'')}));
  if(available.has(id)){group.setAttribute('role','button');group.setAttribute('aria-label','Travel to '+n.name);const act=()=>{try{state=advance(state,'MOVE:'+id);save();show();}catch(e){$('worldAlert').textContent=e.message;}};group.addEventListener('click',act);group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act();}});}
  const label=svg('text',{x:x+14,y:y-12,class:'node-label'},n.name);group.append(label);nodes.append(group);
 }
 // The map is expressly topological. This radius is visual pressure, NOT AU geometry.
 $('veilline').setAttribute('r',String(15+Math.min(30,state.tick)*9));
}
$('newGame').addEventListener('click',()=>{state=create($('player').value,$('form').value);save();show();});
$('witnessOn').addEventListener('change',e=>{state=setWitness(state,e.target.checked);save();$('answer').textContent=state.witnessEnabled?'Historical recall enabled.':'Historical recall is off.';show();});
for(const id of ['origin','journey','unknown'])$(id).addEventListener('click',()=>{$('answer').textContent=witness(state,id==='origin'?'beginning':id);});
$('export').addEventListener('click',()=>{const file=new Blob([JSON.stringify({prototype:true,...state},null,2)],{type:'application/json'});const u=URL.createObjectURL(file);const a=document.createElement('a');a.href=u;a.download='the-last-thread-local-history.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),500);});
$('reset').addEventListener('click',()=>{if(!confirm('Clear this browser prototype save? This does not change your separate game account.'))return;try{localStorage.removeItem(KEY);}catch{return alert('Browser blocked save deletion. Cannot confirm reset.');}state=null;$('answer').textContent='Witness recall is off.';show();});
show();

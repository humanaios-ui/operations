const $=id=>document.getElementById(id);
const SVG='http://www.w3.org/2000/svg';
let session=null,state=null,selected='beam',bay='me',lastFrame=null,animating=false,runMessage='',requestSeq=0;
const discovery=[
 {id:'coil',name:'The spare coil',glyph:'◉',desc:'A spring hidden behind an old press. Investigate to recover a spare.'},
 {id:'plans',name:'The faded blueprint',glyph:'⌁',desc:'A half-erased sketch suggests that a bridge needs continuous support.'},
 {id:'crane',name:'The silent crane',glyph:'⚒',desc:'A small lever can transfer force to a moving capsule. Recover the spare.'},
 {id:'echo',name:'The echo chamber',glyph:'◌',desc:'Tap a piece, experiment, and watch the physics. Trial runs are free.'}];
const partNames={beam:'Platform',ramp:'Ramp',spring:'Spring',lever:'Lever'};
const partDescription={beam:'Flat 120-unit support · 1 point',ramp:'Angled 120-unit surface · 2 points',spring:'Launches on contact · 2 points',lever:'Transfers momentum · 2 points'};
const costs={beam:1,ramp:2,spring:2,lever:2};
function node(tag,attrs={},content){const n=document.createElementNS(SVG,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(content!==undefined)n.textContent=content;return n;}
function html(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
function toast(msg){$('notice').textContent=msg;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('notice').textContent='',4600);}
function credentials(){try{return JSON.parse(sessionStorage.getItem('great-rescue-s0')||'null');}catch{return null;}}
function store(s){session=s;try{sessionStorage.setItem('great-rescue-s0',JSON.stringify(s));}catch{ /* in-memory play remains available when storage is blocked */ }}
async function api(url,data,withAuth=false){const opts={headers:{'Content-Type':'application/json'}};
 if(data!==undefined){opts.method='POST';opts.body=JSON.stringify(data);}
 if(withAuth){opts.headers.Authorization='Bearer '+session.token;}
 const r=await fetch(url,opts);let j;try{j=await r.json();}catch{throw Error('Server response unavailable');}
 if(!r.ok)throw Error(j.error||'Request failed');return j;
}
async function run(type,payload={}){
 if(!session)return;
 try{
  const res=await api('/api/action',{room:session.code,type,requestId:Date.now().toString(36)+'-'+(++requestSeq).toString(36)+'-'+Math.random().toString(36).slice(2),...payload},true);
  state=res.state;render();
  if(res.simulation){if(type==='official')runMessage='OFFICIAL '+(res.simulation.success?'DELIVERED':'FAILED')+' · Score '+res.record.total+' / 100';
   else runMessage=res.simulation.success?'TEST PASSED · Capsule extracted.':'TEST FAILED · Adjust your machine and retry.';
   $('runTitle').textContent=runMessage;const reason=res.simulation.events.at(-1)?.description||'No successful extraction. Check where the capsule stopped.';
   $('runFeedback').textContent=reason+' Physics steps: '+res.simulation.steps+'.';animate(res.simulation.frames);
  }
 }catch(e){toast(e.message);}
}
async function create(){try{let a=await api('/api/create',{name:$('name').value});store(a);await refresh();toast('Room created. Share your code.');}catch(e){toast(e.message);}}
async function join(){try{let a=await api('/api/join',{name:$('name').value,code:$('codeInput').value.trim().toUpperCase()});store(a);await refresh();toast('Joined the workshop.');}catch(e){toast(e.message);}}
async function refresh(){if(!session)return;try{const s=await api('/api/state?room='+encodeURIComponent(session.code),undefined,true);
  if(!state||s.revision!==state.revision){state=s;render();}else updateTimer();
 }catch(e){if(/not found|expired|Join this room/.test(e.message)){try{sessionStorage.removeItem('great-rescue-s0');}catch{}session=null;state=null;render();}else toast(e.message);}}
function my(){return state?.players.find(p=>p.id===state.self);}
function other(){return state?.players.find(p=>p.id!==state.self);}
function current(){return bay==='friend'&&other()?other():my();}
function updateTimer(){if(!state)return;const remain=state.deadline?Math.max(0,Math.ceil((state.deadline-Date.now())/1000)):0;
 $('timer').textContent=state.phase==='lobby'?'Waiting':state.phase==='results'?'Complete':Math.floor(remain/60)+':'+String(remain%60).padStart(2,'0');}
function render(){
 $('entry').hidden=!!state;$('play').hidden=!state;if(!state)return;
 $('roomCode').textContent=state.code;$('phaseLabel').textContent=state.phase==='lobby'?'Waiting for a second builder':state.phase==='build'?'BUILD / TEST / LAUNCH':'SCORES ARE IN';updateTimer();
 const p=my(),q=other(),disabled=state.phase!=='build'||p.finished;
 $('create').disabled=!!state;
 const opts=$('viewBay');let previous=opts.value;opts.replaceChildren();for(const [v,label] of [['me','My build · '+p.name],['friend','Friend · '+(q?.name||'awaiting player')]]){const o=html('option',null,label);o.value=v;opts.append(o);}opts.value=previous||bay;if(!q){opts.value='me';bay='me';}else bay=opts.value;
 const active=current();$('ownerName').textContent=active.name+(active.id===state.self?' · YOU':' · SPECTATING');$('spent').textContent=active.spent+' / 12 material points';
 const disc=$('discoveries');disc.replaceChildren();for(const d of discovery){const card=html('button','discovery');card.type='button';const meDone=p.discoveries.includes(d.id);const friendDone=q?.discoveries.includes(d.id);
  card.append(html('span','disc-icon',d.glyph),html('strong','',d.name),html('span','desc',d.desc),html('small','',meDone?'✓ You discovered'+(friendDone?' · Friend too':''):friendDone?'Friend found this · investigate too':'Click to investigate'));
  card.disabled=disabled||meDone;card.onclick=()=>run('inspect',{item:d.id});disc.append(card);
 }
 let partEl=$('parts');partEl.replaceChildren();for(const key of Object.keys(partNames)){
  const b=html('button','part'+(selected===key?' selected':''));b.type='button';b.disabled=disabled||bay!=='me';b.append(html('strong','',partNames[key]+' · '+(p.inventory[key]||0)+' left'),html('small','',partDescription[key]));
  b.onclick=()=>{selected=key;render();};partEl.append(b);
 }
 $('rotation').disabled=disabled||bay!=='me'||selected!=='ramp';$('place').disabled=disabled||bay!=='me';$('partsHelp').textContent=selected==='ramp'?'Select a slope, then place the ramp.':`${partNames[selected]} selected. Tap an anchor or select coordinates.`;
 const placed=$('placed');placed.replaceChildren();for(const part of active.build){const r=html('div','placedline',`${partNames[part.type]} · column ${part.c+1}, height ${part.r+1}`);
  if(active.id===state.self){const b=html('button','tiny','Remove');b.disabled=disabled;b.onclick=()=>run('remove',{id:part.id});r.append(b);}placed.append(r);}
 draw(active.build);
 $('test').disabled=disabled;$('official').disabled=disabled||p.attempts.length>=2;$('finish').disabled=disabled||!p.attempts.length;
 const att=$('attempts');att.replaceChildren();p.attempts.forEach((a,i)=>att.append(html('span','attempt',`Run ${i+1}: ${a.success?'DELIVERED':'LOST'} · ${a.total}/100 · reliability ${a.consistency}/3`)));
 const gift=$('giftPart');gift.replaceChildren();for(const key of Object.keys(partNames)){if(p.inventory[key]>0){const o=html('option','',partNames[key]+' ('+p.inventory[key]+')');o.value=key;gift.append(o);}}
 $('offer').disabled=disabled||!q||!gift.options.length;
 const offers=$('offers');offers.replaceChildren();for(const o of state.offers){const sender=state.players.find(p=>p.id===o.from)?.name||'Friend';const r=html('div','offerline',`${sender} offers a ${partNames[o.type]}`);if(o.to===state.self){for(const [label,accept] of [['Accept',true],['Decline',false]]){const b=html('button','tiny',label);b.onclick=()=>run('answerOffer',{id:o.id,accept});r.append(b);}}offers.append(r);}
 $('results').hidden=state.phase!=='results';if(state.phase==='results')showResults();
 $('vote').disabled=p.vote!==null;$('rematch').hidden=state.players[0].id!==state.self;
 if(state.phase==='lobby')$('runFeedback').textContent='Waiting for your second builder. Invite them using the room code.';
}
function showResults(){const r=state.results,champions=r.champions.map(id=>state.players.find(p=>p.id===id)?.name).join(' & ');
 $('winner').textContent='🏆 '+champions+' · Overall champion'+(r.champions.length>1?'s':'');
 const scores=$('scoreboard');scores.replaceChildren();for(const a of r.ranking){const row=html('div','scoreline');row.append(html('strong','',a.name),html('b','',a.total+' / 100'),html('span','',a.score?`Complete ${a.score.completion} · Speed ${a.score.speed} · Materials ${a.score.efficiency} · Reliability ${a.score.reliability}`:'No scored run'));scores.append(row);}
 const awards=$('awards');awards.replaceChildren();for(const [key,label]of [['speed','Fastest'],['efficiency','Most efficient'],['reliability','Most reliable'],['ingenuity','Players’ ingenuity pick']]){
  const names=r.honors[key].map(id=>state.players.find(x=>x.id===id)?.name||'?').join(' & ')||'Not awarded yet';awards.append(html('div','award',label+' · '+names));}
 $('vote').textContent=my().vote?'You recognized your friend':'Vote for your friend’s ingenuity';
}
function draw(parts){const board=$('board');board.replaceChildren();
 board.append(node('rect',{x:0,y:0,width:1020,height:550,fill:'#0c1c29'}));
 const sky=node('g');for(let i=0;i<18;i++){sky.append(node('circle',{cx:40+i*59,cy:47+(i%4)*22,r:i%3+1,fill:'#9fc8d6',opacity:'.18'}));}board.append(sky);
 board.append(node('rect',{x:0,y:410,width:252,height:140,fill:'#294b4b'}),node('rect',{x:763,y:410,width:257,height:140,fill:'#294b4b'}));
 board.append(node('path',{d:'M252 410 L252 540 M763 410 L763 540',stroke:'#e4a94a','stroke-width':4}));
 board.append(node('rect',{x:895,y:364,width:81,height:46,rx:6,fill:'#285a56',stroke:'#74e4bb','stroke-width':3}));
 board.append(node('text',{x:937,y:355,'text-anchor':'middle',fill:'#b1f8da','font-size':17},'EXTRACTION'));
 board.append(node('rect',{x:24,y:395,width:90,height:15,rx:5,fill:'#e6b86c'}));
 board.append(node('text',{x:40,y:440,fill:'#c4d6d7','font-size':16},'LAUNCH'));
 board.append(node('text',{x:380,y:475,fill:'#9bb7c2','font-size':21},'THE DEEP GAP'));
 // A grid of build anchors, clickable on owned boards only.
 for(let r=0;r<5;r++)for(let c=0;c<13;c++){
  const x=260+c*40,y=270+r*30;
  board.append(node('circle',{cx:x,cy:y,r:3,fill:'#d5e3e4',opacity:'.27'}));
  const anchor=node('circle',{cx:x,cy:y,r:16,fill:'transparent',class:'anchor'});
  if(bay==='me'&&state?.phase==='build'&&!my().finished){anchor.setAttribute('role','button');anchor.setAttribute('tabindex','0');anchor.setAttribute('aria-label',`Place ${selected} in column ${c+1}, height ${r+1}`);
   const act=()=>run('place',{part:selected,c,r,angle:selected==='ramp'?Number($('rotation').value):0});anchor.addEventListener('click',act);anchor.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();act();}});}
  board.append(anchor);
 }
 for(const p of parts){const x=260+p.c*40,y=270+p.r*30;
  if(p.type==='beam'||p.type==='ramp'){
   const slope=p.type==='ramp'?p.angle*0.28:0;
   board.append(node('line',{x1:x-60,y1:y-60*slope,x2:x+60,y2:y+60*slope,stroke:p.type==='ramp'?'#dd9e50':'#e4c58d','stroke-width':13,'stroke-linecap':'round'}));
  }else if(p.type==='spring'){
   board.append(node('rect',{x:x-37,y:y-8,width:74,height:12,rx:4,fill:'#cdd8ef'}));
   for(let i=-2;i<=2;i++)board.append(node('path',{d:`M${x+i*10-5} ${y-8} l5 -20 l5 20`,fill:'none',stroke:'#6dddca','stroke-width':4}));
  }else{
   board.append(node('path',{d:`M${x-34} ${y+2} L${x+34} ${y-12} M${x} ${y+2} l-12 22 h24 Z`,stroke:'#d1b1f5',fill:'none','stroke-width':6}));
  }
 }
 if(lastFrame){board.append(node('circle',{cx:lastFrame.x,cy:lastFrame.y,r:12,fill:'#e7f6fa',stroke:'#6bd9e7','stroke-width':3}));}else{board.append(node('circle',{cx:82,cy:314,r:12,fill:'#e7f6fa',stroke:'#6bd9e7','stroke-width':3}));}
 board.append(node('text',{x:260,y:535,fill:'#9db4be','font-size':14},'Use workshop tests before spending an official attempt.'));
}
function animate(frames){if(!Array.isArray(frames)||!frames.length)return;animating=true;lastFrame=null;let i=0;
 clearInterval(animate.timer);animate.timer=setInterval(()=>{if(i>=frames.length){clearInterval(animate.timer);animating=false;return;}lastFrame=frames[i++];draw(current().build);},24);
}
$('create').onclick=create;$('join').onclick=join;
$('codeInput').addEventListener('keydown',e=>{if(e.key==='Enter')join();});
$('copy').onclick=async()=>{const code=state.code;try{await navigator.clipboard.writeText(location.origin+'/?room='+code);toast('Invite URL copied.');}catch{toast('Share room code: '+code);}};
$('leave').onclick=()=>{try{sessionStorage.removeItem('great-rescue-s0');}catch{}session=null;state=null;clearInterval(animate.timer);render();};
$('viewBay').onchange=e=>{bay=e.target.value;lastFrame=null;render();};
$('rotation').onchange=()=>draw(current().build);
for(const [id,limit]of [['col',13],['row',5]]){for(let i=0;i<limit;i++){const o=html('option','',(id==='col'?'Column ':'Height ')+(i+1));o.value=i;$(id).append(o);}}
$('col').value='2';$('row').value='4';
$('place').onclick=()=>run('place',{part:selected,c:Number($('col').value),r:Number($('row').value),angle:selected==='ramp'?Number($('rotation').value):0});
$('test').onclick=()=>run('test');$('official').onclick=()=>run('official');$('finish').onclick=()=>run('finish');
$('offer').onclick=()=>run('offer',{to:other()?.id,part:$('giftPart').value});$('vote').onclick=()=>run('vote',{player:other()?.id});$('rematch').onclick=()=>run('rematch');
const linkRoom=new URLSearchParams(location.search).get('room');if(linkRoom)$('codeInput').value=linkRoom.toUpperCase();
session=credentials();if(session)refresh();else render();setInterval(()=>{if(session&&!animating)refresh();else updateTimer();},1200);

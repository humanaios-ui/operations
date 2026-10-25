(() => {
  'use strict';
  const KEY = 'wardens.genesis.slice.v1';
  const allowedForms = ['Seeker', 'Warden', 'Builder', 'Memory-Bearer'];
  const allowedPaths = ['Ember', 'Archive', 'Forge'];
  // MYTH ONLY. These are fictional route captions; they never enter observed
  // history as a claim about a player's motive, nature, or real-world identity.
  const routeLore = Object.freeze({
    Ember: 'MYTH / Ember resists the distant Solar order with fire. This describes a story route, not your nature.',
    Archive: 'MYTH / Archive studies gaps in the Solar record. A missing trace does not prove deliberate erasure.',
    Forge: 'MYTH / Forge reworks buried remnants of sunlight. The Black Corpse is a fictional image, not a resource instruction.'
  });
  const $ = id => document.getElementById(id);
  const qs = (selector, root = document) => [...root.querySelectorAll(selector)];
  const clean = value => String(value || '').replace(/[\u0000-\u001f\u007f]/g, ' ').slice(0, 280).trim();
  const initial = () => ({ zone:1, maximum:1, player:null, form:null, path:null, witness:false, attestation:null, calibration:null, proposal:null, finished:false, events:[] });
  let state = initial();
  try { const saved = JSON.parse(localStorage.getItem(KEY) || 'null');
    if (saved && Array.isArray(saved.events) && saved.events.length <= 150 && Number.isInteger(saved.zone) && saved.zone >= 1 && saved.zone <= 5 && Number.isInteger(saved.maximum)) {
      state = {...initial(), ...saved, maximum:Math.min(5, Math.max(1,saved.maximum)), zone:Math.min(saved.zone,Math.max(1,saved.maximum))};
    }
  } catch (_) { state = initial(); }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (_) { /* Browsers may disable local storage. Session play remains available. */ } }
  function event(kind, details) {
    const id = `E-${String(state.events.length + 1).padStart(3,'0')}`;
    state.events.push({id, kind, details:clean(details), at:new Date().toISOString()});
    save(); renderLedger(); return id;
  }
  function find(kind) { return state.events.find(e => e.kind === kind); }
  function renderLedger() {
    const ol = $('events'); ol.replaceChildren();
    if (!state.events.length) { const li=document.createElement('li'); li.textContent='No events yet. The first choice awaits.';ol.append(li); }
    state.events.forEach(e => {
      const li=document.createElement('li');const tag=document.createElement('span');tag.textContent=e.id;li.append(tag,document.createTextNode(`${e.kind.replaceAll('_',' ')} · ${e.details}`));ol.append(li);
    });
    $('epochLabel').textContent = `${state.player ? 'TIMELINE ACTIVE' : 'UNBEGUN'} / ${state.events.length} EVENTS`;
  }
  function goto(zone) {
    if (zone > state.maximum || zone < 1) return;
    state.zone = zone; save(); renderZone();
  }
  function advance(zone) { state.maximum = Math.max(state.maximum,zone); goto(zone); }
  function renderZone() {
    for (let i=1;i<=5;i++) {
      const area=$(`zone${i}`);area.hidden = (i !== state.zone);
    }
    qs('[data-goto]').forEach(el => {
      const n=Number(el.dataset.goto);
      el.classList.toggle('active',n===state.zone);
      el.classList.toggle('complete',n < state.maximum);
      el.classList.toggle('locked',n > state.maximum);
      el.disabled = n > state.maximum;
      if(n===state.zone)el.setAttribute('aria-current','step');else el.removeAttribute('aria-current');
    });
    $('witnessToggle').checked=Boolean(state.witness);
    qs('[data-query]').forEach(btn => { btn.disabled=!state.witness; });
    if(state.form && state.path){$('routeNote').textContent=`Your ${state.form} followed the ${state.path} route. This is a record, not a judgment. ${routeLore[state.path] || ''}`;}
    if(state.path){$('trueClaim').textContent=`Your path was recorded as ${state.path}.`;}
    $('attestationNote').textContent=state.attestation?`W2 attestation: ${state.attestation} — a separate human event.`:'';
    if(state.calibration){$('calibrationNext').disabled=false;}
    $('completion').hidden=!state.finished;
    $('councilForm').hidden=Boolean(state.finished);
    renderLedger();
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) window.scrollTo(0,0);
    else window.scrollTo({top:0,behavior:'smooth'});
  }
  $('genesisForm').addEventListener('submit',ev => {
    ev.preventDefault();
    if(state.player!==null)return;
    const form=qs('input[name="form"]:checked')[0]?.value;
    if(!allowedForms.includes(form))return;
    state.player=clean($('playerName').value).slice(0,32)||'The Unnamed';
    state.form=form; state.witness=$('genesisWitness').checked;
    event('GENESIS_EVENT',`${state.player} entered the local simulated world`);
    event('FORM_SELECTED',`${form}, by the player's explicit choice`);
    advance(2);
  });
  qs('[data-path]').forEach(btn=>btn.addEventListener('click',()=>{
    const path=btn.dataset.path;
    if(state.path || !allowedPaths.includes(path) || state.zone!==2)return;
    state.path=path;event('PATH_CHOSEN',`${path} — chosen, not inferred`);advance(3);
  }));
  $('witnessToggle').addEventListener('change',ev=>{
    state.witness=Boolean(ev.target.checked);save();
    $('witnessResponse').textContent = state.witness ? 'Witness recall enabled. Choose a historical question.' : 'Witness recall is disabled. No game history has been deleted.';
    renderZone();
  });
  function answer(query){
    if(!state.witness)return 'Witness recall disabled.';
    if(query==='origin'){
      const e=find('GENESIS_EVENT');return e?`Recorded: ${e.details}. [${e.id}]\nThis is an event in this local game, not a verified real-world origin.`:'Unknown. No genesis record is available.';
    }
    if(query==='route'){
      const e=find('PATH_CHOSEN');return e?`Recorded: ${e.details}. [${e.id}]\nNo claim is made about what this says about you.`:'Not recorded. I cannot infer an unchosen route. Missing evidence does not prove it was deliberately erased.';
    }
    return 'Unknown. No future event is recorded. Missing history does not prove deliberate erasure. I cannot predict your destiny, advise a move, or choose for you.';
  }
  qs('[data-query]').forEach(b=>b.addEventListener('click',()=>{$('witnessResponse').textContent=answer(b.dataset.query);}));
  function attest(choice){
    if(state.attestation)return;
    const genesis=find('GENESIS_EVENT');if(!genesis)return;
    state.attestation=choice;event('W2_ATTESTATION',`${choice} by ${state.player}; references ${genesis.id}, does not overwrite it`);renderZone();
  }
  $('acknowledge').addEventListener('click',()=>attest('ACKNOWLEDGE'));
  $('contest').addEventListener('click',()=>attest('CONTEST'));
  qs('[data-forward]').forEach(btn=>btn.addEventListener('click',()=>{
    const target=Number(btn.dataset.forward);
    if(state.zone===3&&target===4)advance(4);
    if(state.zone===4&&target===5&&state.calibration)advance(5);
  }));
  qs('[data-claim]').forEach(b=>b.addEventListener('click',()=>{
    if(state.calibration)return;
    const claim=b.dataset.claim;
    state.calibration=claim;
    event('CLAIM_INSPECTED',`${claim}: player inspected claim; no personal score assigned`);
    qs('[data-claim]').forEach(el=>el.classList.toggle('selected',el===b));
    const pathEvent=find('PATH_CHOSEN');
    $('calibrationResponse').textContent = claim==='recorded'?
      `Evidence-supported: the game ledger contains ${pathEvent?.id||'no matching event'} for the selected path. This says only what was recorded.`:
      'Unsupported claim: no event proves that every path succeeds. A confident statement is not evidence; future outcomes remain unknown.';
    $('calibrationNext').disabled=false;
  }));
  function finish(proposal){
    if(state.finished)return;
    if(proposal){state.proposal=proposal;event('ADVISORY_PROPOSAL_DRAFT',`${proposal} [LOCAL DRAFT — NO VOTE]`);}
    else event('COUNCIL_SKIPPED','Player did not submit a proposal');
    state.finished=true;save();renderZone();
  }
  $('councilForm').addEventListener('submit',ev=>{ev.preventDefault(); const value=clean($('proposal').value).slice(0,280);if(!value){$('proposal').focus();return;}finish(value);});
  $('skipCouncil').addEventListener('click',()=>finish(''));
  $('reviewTimeline').addEventListener('click',()=>{$('events').scrollIntoView({behavior:'smooth',block:'center'});});
  $('export').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({demo_only:true,player:state.player,form:state.form,path:state.path,events:state.events},null,2)],{type:'application/json'});
    const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download='wardens-local-timeline.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),500);
  });
  $('reset').addEventListener('click',()=>{
    if(!window.confirm('Clear this local browser demo history? This cannot delete a real HumanAIOS account.'))return;
    try { localStorage.removeItem(KEY); } catch (_) {} state=initial();$('genesisForm').reset();$('witnessResponse').textContent='Witness recall is disabled until you opt in.';$('calibrationResponse').textContent='Select a claim to inspect its source.';$('calibrationNext').disabled=true;renderZone();
  });
  qs('[data-goto]').forEach(btn=>btn.addEventListener('click',()=>goto(Number(btn.dataset.goto))));
  renderZone();
  if (typeof location === 'undefined' || ['localhost','127.0.0.1'].includes(location.hostname)) {
    Object.defineProperty(window,'__WARDENS_TEST__',{value:Object.freeze({snapshot:()=>structuredClone(state),query:answer}),configurable:false});
  }
})();

'use strict';
// TEST B: Desk <-> INTENT-OS compatibility. SYNTHETIC fixtures only. Source is read-only; nothing is written back.
const assert = require('node:assert/strict');
const { test, begin, finish } = require('./harness.cjs');
const F = require('../fixtures/synthetic.cjs'), D = require('../dist/model.js'), W = require('../dist/intent-workspace.js');
const B = require('../engine/intent-bridge.cjs'), C = require('../engine/core.cjs');
begin('bridge');

const ws119 = F.ws119(), ws193 = F.ws193(), desk = F.deskWithUserEdits();
const srcBefore = JSON.stringify(ws193), deskBefore = JSON.stringify(desk);
const plan = B.planReconciliation(desk, ws193);
const of = k => plan.proposals.filter(p => p.kind === k);
const pick = (kind, caseId, taskId) => plan.proposals.find(p => p.kind === kind && p.case_id === caseId && (taskId === undefined || p.task_id === taskId));
const SC = pick('ADOPT_SOURCE_CHANGE', 'case-synth-fellowship', 'task-special-circ'), ST = pick('CONFLICT_TASK', 'case-synth-fellowship', 'task-statement');
const everything = (override = {}) => plan.proposals.map(p => ({ id: p.id, choice: override[p.id] || (p.choices.includes('ADOPT') && !/^CONFLICT_/.test(p.kind) ? 'ADOPT' : p.kind.startsWith('CONFLICT') ? 'KEEP_DESK' : 'RECORD_ONLY') }));
const opts = (d = desk) => ({ expected_base_revision: d.revision, captured_at: '2026-10-30T00:00:00.000Z' });
const throwsCode = (fn, code) => { try { fn(); } catch (e) { assert.equal(e.code, code, `expected ${code}, got ${e.code}: ${e.message}`); return e; } assert.fail('expected ' + code); };

// ---------- revision comparison ----------
test('comparison identifies the stable source task id and both historical states', () => {
  const c = B.compareWorkspaces(ws119, ws193), t = c.changes.find(x => x.kind === 'TASK_FIELD_CHANGED' && x.task_id === 'task-special-circ');
  assert.equal(c.relation, 'NEWER'); assert.deepEqual([t.case_id, t.task_id, t.field, t.before, t.after], ['case-synth-fellowship', 'task-special-circ', 'state', 'BLOCKED', 'OPTIONAL']);
});
test('comparison finds every independent change and nothing else', () => {
  const kinds = B.compareWorkspaces(ws119, ws193).changes.map(c => c.kind + (c.field ? ':' + c.field : '')).sort();
  assert.deepEqual(kinds, ['CASE_ADDED', 'CASE_FIELD_CHANGED:hold_reason', 'CASE_FIELD_CHANGED:pursuit', 'INTENT_CHANGED', 'REPORT_ADDED', 'TASK_ADDED', 'TASK_FIELD_CHANGED:state', 'TASK_FIELD_CHANGED:state', 'TASK_REMOVED']);
});
test('comparison relation covers identical, older, and same-revision-different-content', () => {
  assert.equal(B.compareWorkspaces(ws119, ws119).relation, 'IDENTICAL');
  assert.equal(B.compareWorkspaces(ws193, ws119).relation, 'OLDER');
  const alt = C.clone(ws119); alt.records[0].tasks[0].title = 'changed'; assert.equal(B.compareWorkspaces(ws119, alt).relation, 'SAME_REVISION_DIFFERENT_CONTENT');
});

// ---------- planning ----------
test('plan classifies each change: adopt / conflict / add / remove / hold / evidence', () => {
  const kinds = plan.proposals.map(p => p.kind).sort();
  assert.deepEqual(kinds, ['ADD_CASE', 'ADD_TASK', 'ADOPT_SOURCE_CHANGE', 'CONFLICT_TASK', 'EVIDENCE_CHANGED', 'INTENT_CHANGED', 'SET_PROJECT_HOLD', 'TASK_REMOVED']);
});
test('the BLOCKED-to-OPTIONAL-shaped change is preserved as BOTH facts with revisions, as a proposal not a rewrite', () => {
  assert.deepEqual(SC.source_history, { r119: 'BLOCKED', r193: 'OPTIONAL' });
  assert.equal(SC.fields[0].desk_edited, false); assert.equal(SC.desk_status, 'BLOCKED'); assert.equal(SC.severity, 'ACTION');
  assert.equal(desk.tasks.find(t => t.id === SC.desk_task_id).status, 'BLOCKED');   // planning changed nothing
});
test('a task the user edited, when the source also changed, is a CONFLICT with no default choice', () => {
  assert.equal(ST.severity, 'CONFLICT'); assert.equal(ST.fields[0].desk_edited, true); assert.equal(ST.desk_status, 'DOING'); assert.deepEqual(ST.source_history, { r119: 'TODO', r193: 'DONE' });
  assert.equal(ST.default_choice, undefined);
});
test('planning is pure: same inputs give the same plan digest; inputs are not modified', () => {
  assert.equal(B.planReconciliation(desk, ws193).digest, plan.digest);
  assert.equal(JSON.stringify(ws193), srcBefore); assert.equal(JSON.stringify(desk), deskBefore); assert.equal(plan.writeback, false);
});
test('planning uses no clock and no randomness', () => {
  const r = Math.random, n = Date.now, ctor = global.Date;
  Math.random = () => { throw new Error('random used'); }; Date.now = () => { throw new Error('clock used'); };
  try { assert.equal(B.planReconciliation(desk, ws193).digest, plan.digest); } finally { Math.random = r; Date.now = n; global.Date = ctor; }
});
test('proposal ids are deterministic and unique', () => { const ids = plan.proposals.map(p => p.id); assert.equal(new Set(ids).size, ids.length); assert(ids.every(i => /^brg-[0-9a-f]{16}$/.test(i))); });
test('older snapshots and same-revision-different-content snapshots are refused, preserved untouched', () => {
  const older = C.clone(ws119); older.revision = 118; older.records[0].title = 'older'; assert.equal(B.planReconciliation(desk, W.validate(older)).refused, 'OLDER');
  const same = C.clone(ws119); same.records[0].tasks[0].title = 'x'; assert.equal(B.planReconciliation(desk, W.validate(same)).refused, 'SAME_REVISION_DIFFERENT_CONTENT');
  throwsCode(() => B.applyReconciliation(desk, W.validate(older), null, [], opts()), 'REFUSED_OLDER');
});
test('an identical snapshot is an idempotent no-op', () => {
  const p = B.planReconciliation(desk, ws119); assert.equal(p.idempotent, true); assert.equal(p.proposals.length, 0);
  const r = B.applyReconciliation(desk, ws119, p, [], opts()); assert.equal(r.changed, false); assert.equal(JSON.stringify(r.desk), deskBefore);
});

// ---------- applying explicit choices ----------
test('applying nothing records an OBSERVED snapshot and leaves every task untouched', () => {
  const r = B.applyReconciliation(desk, ws193, plan, [], opts());
  assert.equal(r.changed, true); assert.deepEqual(r.desk.tasks, desk.tasks); assert.equal(r.remaining.length, plan.proposals.length);
  assert.deepEqual(r.desk.imports.map(i => i.id), ['intent-workspace', 'intent-observed@193']);
  assert.equal(B.planReconciliation(r.desk, ws193).proposals.length, plan.proposals.length);   // nothing was silently resolved
});
test('applying nothing twice is idempotent', () => {
  const a = B.applyReconciliation(desk, ws193, plan, [], opts()).desk, b = B.applyReconciliation(a, ws193, null, [], opts(a));
  assert.equal(b.changed, false); assert.equal(JSON.stringify(b.desk), JSON.stringify(a));
});
test('adopting the source change keeps both historical facts: snapshots r119 and r193 and a named event', () => {
  const r = B.applyReconciliation(desk, ws193, plan, [{ id: SC.id, choice: 'ADOPT' }], opts()), t = r.desk.tasks.find(x => x.id === SC.desk_task_id);
  assert.equal(t.status, 'WAITING'); assert.equal(t.note, B.genNote('OPTIONAL'));
  const states = ['intent-workspace', 'intent-observed@193'].map(id => r.desk.imports.find(i => i.id === id).data.records[0].tasks[0].state);
  assert.deepEqual(states, ['BLOCKED', 'OPTIONAL']);
  const ev = r.desk.events.find(e => e.text.startsWith('Bridge ' + SC.id + ' ADOPT')).text;
  assert(ev.includes('case-synth-fellowship/task-special-circ') && ev.includes('BLOCKED') && ev.includes('OPTIONAL') && ev.includes('Desk was BLOCKED, now WAITING'));
});
test('the Desk status WAITING does not erase the source fact that the state is OPTIONAL', () => {
  const r = B.applyReconciliation(desk, ws193, plan, [{ id: SC.id, choice: 'ADOPT' }], opts()), snaps = B.snapshots(r.desk);
  assert.equal(snaps.length, 2); assert.notEqual(snaps[0].sha256, snaps[1].sha256); assert.equal(snaps[1].sha256, C.digest(ws193));
});
test('a conflict is never resolved implicitly; ADOPT over the user edit needs confirm_overwrite', () => {
  const r = B.applyReconciliation(desk, ws193, plan, [], opts()); assert.equal(r.desk.tasks.find(t => t.id === ST.desk_task_id).note, 'MY OWN NOTE: drafting this week');
  throwsCode(() => B.applyReconciliation(desk, ws193, plan, [{ id: ST.id, choice: 'ADOPT' }], opts()), 'OVERWRITE_NOT_CONFIRMED');
});
test('KEEP_DESK preserves the user edit and still records the source observation', () => {
  const r = B.applyReconciliation(desk, ws193, plan, [{ id: ST.id, choice: 'KEEP_DESK' }], opts()), t = r.desk.tasks.find(x => x.id === ST.desk_task_id);
  assert.equal(t.status, 'DOING'); assert.equal(t.note, 'MY OWN NOTE: drafting this week'); assert(r.desk.events.some(e => e.text.startsWith('Bridge ' + ST.id + ' KEEP_DESK')));
});
test('adopting a source DONE needs the user\'s own outcome note, and refuses atomically', () => {
  const choices = [{ id: SC.id, choice: 'ADOPT' }, { id: ST.id, choice: 'ADOPT', confirm_overwrite: true }];
  const e = throwsCode(() => B.applyReconciliation(desk, ws193, plan, choices, opts()), 'GATE_REFUSED'); assert(/own outcome note/.test(e.message));
  assert.equal(JSON.stringify(desk), deskBefore);                                    // the valid first choice was NOT half-applied
  const ok = B.applyReconciliation(desk, ws193, plan, [{ ...choices[1], note: 'I finished and checked it myself.' }], opts()).desk.tasks.find(t => t.id === ST.desk_task_id);
  assert.equal(ok.status, 'DONE'); assert.equal(ok.note, 'I finished and checked it myself.');
  const gen = throwsCode(() => B.applyReconciliation(desk, ws193, plan, [{ ...choices[1], note: B.genNote('DONE') }], opts()), 'GATE_REFUSED'); assert(gen);
});
test('a project hold and an unmet dependency still block adopting DOING', () => {
  const held = D.change(desk, n => { n.projects.find(p => p.origin.includes('case-synth-fellowship')).hold = 'USER HOLD'; }, 'user hold');
  const w = C.clone(ws193); w.records[0].tasks[0].state = 'DOING'; const w2 = W.validate(w), p2 = B.planReconciliation(held, w2), sc = p2.proposals.find(p => p.task_id === 'task-special-circ');
  const e = throwsCode(() => B.applyReconciliation(held, w2, p2, [{ id: sc.id, choice: 'ADOPT' }], opts(held)), 'GATE_REFUSED'); assert(/hold/.test(e.message));
});
test('choices are validated: unknown id, duplicate, and disallowed choice are refused', () => {
  throwsCode(() => B.applyReconciliation(desk, ws193, plan, [{ id: 'brg-0000000000000000', choice: 'ADOPT' }], opts()), 'UNKNOWN_PROPOSAL');
  throwsCode(() => B.applyReconciliation(desk, ws193, plan, [{ id: SC.id, choice: 'ADOPT' }, { id: SC.id, choice: 'KEEP_DESK' }], opts()), 'DUPLICATE_CHOICE');
  const rm = pick('TASK_REMOVED', 'case-synth-grant'); throwsCode(() => B.applyReconciliation(desk, ws193, plan, [{ id: rm.id, choice: 'ADOPT' }], opts()), 'CHOICE_NOT_ALLOWED');
});
test('full reconciliation adds a RECONCILED snapshot and later plans are idempotent', () => {
  const r = B.applyReconciliation(desk, ws193, plan, everything(), opts());
  assert.deepEqual(r.remaining, []); assert.deepEqual(r.desk.imports.map(i => i.id), ['intent-workspace', 'intent-workspace@193']);
  const again = B.planReconciliation(r.desk, ws193); assert.equal(again.idempotent, true);
  const twice = B.applyReconciliation(r.desk, ws193, again, [], opts(r.desk)); assert.equal(twice.changed, false);
});
test('adopting new cases and tasks uses deterministic ids and is reproducible', () => {
  // Two independent Desks (their LEGACY imports have random ids, which is the old model's behaviour) reconciled with the same source.
  const mk = () => { const d = F.deskWithUserEdits(), p = B.planReconciliation(d, ws193), ch = p.proposals.filter(x => x.kind === 'ADD_CASE' || x.kind === 'ADD_TASK').map(x => ({ id: x.id, choice: 'ADOPT' }));
    return B.applyReconciliation(d, ws193, p, ch, opts(d)).desk; };
  const a = mk(), b = mk(), made = d => ({ p: d.projects.filter(x => /^ixp-/.test(x.id)), t: d.tasks.filter(x => /^ixt-/.test(x.id)) });
  assert(made(a).p.length === 1 && made(a).t.length === 2); assert(made(a).p.every(x => /^ixp-[0-9a-f]{16}$/.test(x.id))); assert(made(a).t.every(x => /^ixt-[0-9a-f]{16}$/.test(x.id)));
  const stable = d => ({ p: made(d).p, t: made(d).t.map(({ project, ...rest }) => ({ ...rest, project: /^ixp-/.test(project) ? project : 'LEGACY_PROJECT' })) });   // a legacy project id is random by the OLD model; everything new is deterministic
  assert.equal(C.digest(stable(a)), C.digest(stable(b)));
});
test('adopted source-hold sets the project hold; removed tasks stay in the Desk', () => {
  const r = B.applyReconciliation(desk, ws193, plan, everything(), opts()).desk, pj = r.projects.find(p => p.origin.includes('case-synth-grant'));
  assert.equal(pj.hold, 'SYNTHETIC: waiting on funder'); assert(r.tasks.some(t => t.source === 'case-synth-grant/task-apply'));
});

// ---------- stale writes and plan integrity ----------
test('a stale write is refused and the caller\'s choices come back intact', () => {
  const choices = [{ id: SC.id, choice: 'ADOPT' }, { id: ST.id, choice: 'KEEP_DESK', note: 'my reason typed in the form' }];
  const e = throwsCode(() => B.applyReconciliation(desk, ws193, plan, choices, { expected_base_revision: desk.revision - 1 }), 'STALE_WRITE');
  assert.deepEqual(e.preserved.choices, choices); assert.equal(e.actual, desk.revision); assert.equal(JSON.stringify(desk), deskBefore);
});
test('an expected revision is mandatory', () => throwsCode(() => B.applyReconciliation(desk, ws193, plan, [], {}), 'EXPECTED_REVISION_REQUIRED'));
test('a plan reviewed against different inputs is refused', () => {
  const other = C.clone(ws193); other.records[0].tasks[0].title = 'edited after review'; throwsCode(() => B.applyReconciliation(desk, W.validate(other), plan, [], opts()), 'PLAN_MISMATCH');
});

// ---------- history ----------
test('old Desk event history is an exact prefix after applying', () => {
  const r = B.applyReconciliation(desk, ws193, plan, everything(), opts()), v = C.verifyHistoryPrefix(desk, r.desk);
  assert.equal(v.ok, true); assert.equal(v.dropped, 0); assert(v.appended >= plan.proposals.length);
  assert.deepEqual(r.desk.events.slice(0, desk.events.length), desk.events);
});
test('history verification rejects deletion, edits and reordering', () => {
  const r = B.applyReconciliation(desk, ws193, plan, everything(), opts()).desk;
  const del = C.clone(r); del.events.shift(); assert.equal(C.verifyHistoryPrefix(desk, del).ok, false);
  const edit = C.clone(r); edit.events[0].text += ' (edited)'; assert.equal(C.verifyHistoryPrefix(desk, edit).ok, false);
  const re = C.clone(r); [re.events[0], re.events[1]] = [re.events[1], re.events[0]]; assert.equal(C.verifyHistoryPrefix(desk, re).ok, false);
});
test('at the 5000-event cap only the oldest events may roll off, and that is reported', () => {
  let big = C.clone(desk); while (big.events.length < 5000) D.event(big, 'padding ' + big.events.length); big = D.validate(big);
  assert.throws(() => B.applyReconciliation(big, ws193, B.planReconciliation(big, ws193), everything(), opts(big)), e => e.code === 'HISTORY_WOULD_ROLL_OFF');   // silent loss is refused by default
  const r = B.applyReconciliation(big, ws193, B.planReconciliation(big, ws193), everything(), { ...opts(big), accept_roll_off: true }), v = C.verifyHistoryPrefix(big, r.desk);
  assert.equal(r.history.dropped, v.dropped);
  assert.equal(r.desk.events.length, 5000); assert.equal(v.ok, true); assert(v.dropped > 0);
  const forged = C.clone(r.desk); forged.events[10].text = 'rewritten'; assert.equal(C.verifyHistoryPrefix(big, forged).ok, false);
});
test('earlier INTENT snapshots are never replaced or edited', () => {
  const r = B.applyReconciliation(desk, ws193, plan, everything(), opts()).desk;
  assert.deepEqual(r.imports[0], desk.imports[0]); assert.equal(r.imports.length, desk.imports.length + 1);
});

// ---------- identity ----------
test('a look-alike task source string in another project cannot hijack the mapping', () => {
  const spoof = D.change(desk, n => { n.projects.push({ id: 'user-p', name: 'User project', outcome: '', hold: '', origin: 'User-created project' }); n.tasks.push({ id: 'user-t', project: 'user-p', title: 'Unrelated', step: '', done_when: '', status: 'DONE', priority: 2, owner: 'x', depends: [], note: 'mine', evidence: '', source: 'case-synth-fellowship/task-special-circ' }); }, 'spoof');
  const p = B.planReconciliation(spoof, ws193), sc = p.proposals.find(x => x.kind === 'ADOPT_SOURCE_CHANGE' && x.task_id === 'task-special-circ');
  assert.equal(sc.desk_task_id, SC.desk_task_id);
});
test('two Desk tasks claiming the same source in the same project are AMBIGUOUS, never guessed', () => {
  const orig = desk.tasks.find(t => t.id === SC.desk_task_id);
  const dup = D.change(desk, n => { n.tasks.push({ ...C.clone(orig), id: 'dup-copy' }); }, 'dup');
  const p = B.planReconciliation(dup, ws193), un = p.proposals.find(x => x.kind === 'UNMAPPED_CHANGE' && x.task_id === 'task-special-circ');
  assert(un); assert.match(un.detail, /AMBIGUOUS_TASK/); assert(!p.proposals.some(x => x.kind === 'ADOPT_SOURCE_CHANGE' && x.task_id === 'task-special-circ'));
});
test('a task moved to another project is UNMAPPED and cannot borrow that project\'s hold', () => {
  const moved = D.change(desk, n => { n.projects.push({ id: 'elsewhere', name: 'Elsewhere', outcome: '', hold: 'UNRELATED HOLD', origin: 'User-created project' }); n.tasks.find(t => t.id === SC.desk_task_id).project = 'elsewhere'; }, 'move');
  const p = B.planReconciliation(moved, ws193), un = p.proposals.find(x => x.kind === 'UNMAPPED_CHANGE' && x.task_id === 'task-special-circ');
  assert(un); assert.deepEqual(un.choices, ['RECORD_ONLY']);
});

// ---------- one-case round trip (preview only; no writeback) ----------
test('round trip is refused until the Desk has reconciled with that exact snapshot', () => throwsCode(() => B.roundTripPreview(desk, ws193, 'case-synth-fellowship'), 'NOT_RECONCILED'));
test('round trip with no Desk edits reproduces the source exactly', () => {
  const clean = F.deskAfterLegacyImport(ws119), r = B.roundTripPreview(clean, ws119, 'case-synth-fellowship');
  assert.equal(r.preview_sha256, r.source_sha256); assert.deepEqual(r.changes, []); assert.equal(r.writeback, false); assert.equal(r.preview_only, true);
});
test('round trip with Desk edits changes only task states of the chosen case, and stays valid INTENT-OS format', () => {
  const after = B.applyReconciliation(desk, ws193, plan, everything(), opts()).desk, r = B.roundTripPreview(after, ws193, 'case-synth-fellowship');
  assert(r.changes.length >= 1 && r.changes.every(c => c.kind === 'TASK_FIELD_CHANGED' && c.case_id === 'case-synth-fellowship' && c.field === 'state'));
  const t = r.preview_workspace.records.find(x => x.id === 'case-synth-fellowship').tasks.find(x => x.id === 'task-statement'); assert.equal(t.state, 'DOING');
  assert.doesNotThrow(() => W.validate(r.preview_workspace));
  for (const id of ['case-synth-grant', 'case-synth-new']) assert.deepEqual(r.preview_workspace.records.find(x => x.id === id), ws193.records.find(x => x.id === id));
  assert.deepEqual(r.preview_workspace.records[0].reports, ws193.records[0].reports);       // Desk work never touches source verification reports
});
test('round trip never modifies the source object and refuses unknown cases', () => {
  const after = B.applyReconciliation(desk, ws193, plan, everything(), opts()).desk;
  B.roundTripPreview(after, ws193, 'case-synth-fellowship'); assert.equal(JSON.stringify(ws193), srcBefore);
  throwsCode(() => B.roundTripPreview(after, ws193, 'no-such-case'), 'UNKNOWN_CASE');
});
test('a Desk export is still refused by the INTENT-OS validator, so there is no accidental writeback path', () => assert.throws(() => W.validate(desk), /Unexpected|Unsupported/));

// ---------- explicit decision dependencies ----------
const seed = D.seed();
test('a decision becomes an explicit gate that blocks dependents until a human completes it', () => {
  const r = B.linkDecision(seed, 'scope', ['offer'], { expected_base_revision: seed.revision });
  assert.equal(r.changed, true); assert.equal(r.gate_id, 'gate-scope');
  assert(D.blocked(r.desk, r.desk.tasks.find(t => t.id === 'offer')).startsWith('Needs: Decide'));
  assert(!D.next(r.desk).some(t => t.id === 'offer')); assert(D.next(r.desk).some(t => t.id === 'gate-scope'));
  assert.throws(() => D.saveTask(r.desk, { ...r.desk.tasks.find(t => t.id === 'offer'), status: 'DOING' }), /Needs: Decide/);
  assert.throws(() => D.saveTask(r.desk, { ...r.desk.tasks.find(t => t.id === 'gate-scope'), status: 'DONE' }), /outcome/);
  const done = D.saveTask(r.desk, { ...r.desk.tasks.find(t => t.id === 'gate-scope'), status: 'DONE', note: 'I decided the pilot solves a workflow problem.' });
  assert(D.next(done).some(t => t.id === 'offer'));
});
test('linking is idempotent, preserves history, and is stale-safe', () => {
  const r = B.linkDecision(seed, 'scope', ['offer'], {}), again = B.linkDecision(r.desk, 'scope', ['offer'], {});
  assert.equal(again.changed, false); assert.equal(C.verifyHistoryPrefix(seed, r.desk).ok, true); assert(r.desk.events.at(-1).text.includes('no task was completed or unblocked automatically'));
  throwsCode(() => B.linkDecision(seed, 'scope', ['offer'], { expected_base_revision: seed.revision + 3 }), 'STALE_WRITE');
});
test('decision links refuse unknown decisions, unknown tasks, self-dependency and id collisions', () => {
  throwsCode(() => B.linkDecision(seed, 'nope', ['offer'], {}), 'UNKNOWN_DECISION'); throwsCode(() => B.linkDecision(seed, 'scope', ['nope'], {}), 'UNKNOWN_TASK'); throwsCode(() => B.linkDecision(seed, 'scope', ['gate-scope'], {}), 'SELF_DEPENDENCY');
  const clash = D.change(seed, n => n.tasks.push({ id: 'gate-scope', project: 'launch', title: 'Unrelated user task', step: '', done_when: '', status: 'TODO', priority: 2, owner: 'x', depends: [], note: '', evidence: '', source: 'mine' }), 'clash');
  throwsCode(() => B.linkDecision(clash, 'scope', ['offer'], {}), 'ID_COLLISION');
});
test('an answered decision only SUGGESTS closing its gate; it never closes it', () => {
  let r = B.linkDecision(seed, 'scope', ['offer'], {}).desk; assert.deepEqual(B.proposeGateClosures(r), []);
  r = D.change(r, n => { const d = n.decisions[0]; d.answer = 'A workflow tool'; d.reason = 'Closest to real users'; }, 'answered');
  const s = B.proposeGateClosures(r); assert.equal(s.length, 1); assert.equal(s[0].automatic, false); assert.equal(r.tasks.find(t => t.id === 'gate-scope').status, 'TODO');
});

// ---------- static guard ----------
test('engines contain no network, process or filesystem access', () => {
  const fs = require('node:fs'), path = require('node:path');
  for (const f of fs.readdirSync(path.join(__dirname, '../engine'))) { const src = fs.readFileSync(path.join(__dirname, '../engine', f), 'utf8'); assert(!/require\((['"])(node:)?(net|http|https|http2|dgram|tls|child_process|fs|dns)\1\)/.test(src), f + ' imports a forbidden module'); assert(!/\bfetch\s*\(|XMLHttpRequest|WebSocket/.test(src), f + ' uses a network API'); }
});

// ---------- F5 repairs: NEW tasks obey the same gates as saveTask ----------
const wsNew = (tasksA, extraA) => W.validate({ schema: 'humanaios.workspace_view.v1', revision: 7, intent: { goal: 'g', constraints: 'c', confirmed: true }, active: null, records: [F.rec('case-new-a', 'New A', tasksA, extraA || {})] });
const firstImport = (w, choice) => { const d = D.empty(), p = B.planReconciliation(d, w); return { d, p, run: ch => B.applyReconciliation(d, w, p, p.proposals.map(x => ({ id: x.id, choice: 'ADOPT', ...(ch || {}) })), { expected_base_revision: d.revision }) }; };
test('adopting a NEW case with a DONE task needs the user\'s own note; a generated note is refused', () => {
  const f = firstImport(wsNew([{ id: 't1', title: 'Done thing', state: 'DONE' }]));
  assert.throws(() => f.run(), e => e.code === 'GATE_REFUSED');
  assert.throws(() => f.run({ note: B.genNote('DONE') }), e => e.code === 'GATE_REFUSED');
  const r = f.run({ note: 'I finished this myself.' }); assert.equal(r.desk.tasks[0].status, 'DONE'); assert.equal(r.desk.tasks[0].note, 'I finished this myself.');
});
test('adopting a NEW case that is ON_HOLD with DOING/DONE tasks is refused; RECORD_ONLY is allowed and writes no task', () => {
  const w = wsNew([{ id: 't1', title: 'Doing thing', state: 'DOING' }], { pursuit: 'ON_HOLD', hold_reason: 'waiting on funder' });
  const f = firstImport(w); assert.throws(() => f.run(), e => e.code === 'GATE_REFUSED' && /hold/i.test(e.message));
  const r = B.applyReconciliation(f.d, w, f.p, f.p.proposals.map(x => ({ id: x.id, choice: 'RECORD_ONLY' })), { expected_base_revision: f.d.revision }); assert.equal(r.desk.tasks.length, 0);
});
test('a NEW task in an ordinary case is still adopted (TODO needs no note)', () => {
  const f = firstImport(wsNew([{ id: 't1', title: 'Plain thing', state: 'TODO' }])); const r = f.run(); assert.equal(r.desk.tasks[0].status, 'TODO'); assert.doesNotThrow(() => D.validate(r.desk));
});
test('a refused adoption writes nothing (the input Desk is untouched)', () => {
  const f = firstImport(wsNew([{ id: 't1', title: 'Done thing', state: 'DONE' }])), before = JSON.stringify(f.d); assert.throws(() => f.run()); assert.equal(JSON.stringify(f.d), before);
});

// ---------- F1 repair: a reconcile that would erase history is refused, loudly, and is the ONLY thing stopping it ----------
test('a huge apply that would roll the whole capped history away is refused with HISTORY_NOT_PRESERVED and a hint', () => {
  const big = (rev, pref) => W.validate({ schema: 'humanaios.workspace_view.v1', revision: rev, intent: { goal: 'g', constraints: 'c', confirmed: true }, active: null, records: Array.from({ length: 100 }, (_, i) => F.rec('c' + i, 'C' + i, Array.from({ length: 40 }, (_, j) => ({ id: pref + j, title: 't', state: 'TODO' })), { references: [], reports: [] })) });
  const w1 = big(1, 'a'), w2 = big(2, 'b'), d0 = D.empty(), p1 = B.planReconciliation(d0, w1);
  const a = B.applyReconciliation(d0, w1, p1, p1.proposals.map(p => ({ id: p.id, choice: 'RECORD_ONLY' })), { expected_base_revision: 0 });
  const dd = a.desk; for (let i = 0; i < 4500; i++) D.event(dd, 'history ' + i); dd.revision++;
  const before = JSON.stringify(dd), p2 = B.planReconciliation(dd, w2); assert(p2.proposals.length > 5000);
  assert.throws(() => B.applyReconciliation(dd, w2, p2, p2.proposals.map(p => ({ id: p.id, choice: 'RECORD_ONLY' })), { expected_base_revision: dd.revision }), e => e.code === 'HISTORY_NOT_PRESERVED' && /fewer proposals/.test(e.message));
  assert.equal(JSON.stringify(dd), before);
  const some = p2.proposals.slice(0, 50).map(p => ({ id: p.id, choice: 'RECORD_ONLY' })), r = B.applyReconciliation(dd, w2, p2, some, { expected_base_revision: dd.revision });
  assert.equal(r.changed, true); assert.equal(C.verifyHistoryPrefix(dd, r.desk).ok, true);
});

// ---------- audit-2 repairs ----------
test('a roll-off just below the erase-everything threshold is refused unless explicitly accepted, and the loss is reported', () => {
  const mkw = (rev, pref) => W.validate({ schema: 'humanaios.workspace_view.v1', revision: rev, intent: { goal: 'g', constraints: 'c', confirmed: true }, active: null, records: Array.from({ length: 100 }, (_, i) => F.rec('c' + i, 'C' + i, Array.from({ length: 40 }, (_, j) => ({ id: pref + j, title: 't', state: 'TODO' })), { references: [], reports: [] })) });
  const w1 = mkw(1, 'a'), w2 = mkw(2, 'b'), d0 = D.empty(), p1 = B.planReconciliation(d0, w1);
  const a = B.applyReconciliation(d0, w1, p1, p1.proposals.map(p => ({ id: p.id, choice: 'RECORD_ONLY' })), { expected_base_revision: 0 });
  const dd = a.desk; for (let i = 0; i < 4500; i++) D.event(dd, 'history ' + i); dd.revision++;
  const p2 = B.planReconciliation(dd, w2), pick = k => p2.proposals.slice(0, k).map(p => ({ id: p.id, choice: 'RECORD_ONLY' }));
  assert.throws(() => B.applyReconciliation(dd, w2, p2, pick(1000), { expected_base_revision: dd.revision }), e => e.code === 'HISTORY_WOULD_ROLL_OFF');
  const r = B.applyReconciliation(dd, w2, p2, pick(1000), { expected_base_revision: dd.revision, accept_roll_off: true }); assert(r.history.dropped > 0);
});
test('verify-history also fails when a saved import snapshot is removed or edited', () => {
  const after = C.clone(desk); after.imports = []; const v = C.verifyHistoryPrefix(desk, after); assert.equal(v.ok, false); assert.match(v.reason, /import snapshot/);
  const edit = C.clone(desk); edit.imports[0].data.intent.goal = 'edited'; assert.equal(C.verifyHistoryPrefix(desk, edit).ok, false);
});
test('same-origin duplicate: an ADD_CASE for a case the Desk already has a project for is RECORD_ONLY and cannot be applied', () => {
  const d = C.clone(desk), base = d.imports[0]; base.data.records = base.data.records.filter(r => r.id !== 'case-synth-fellowship'); base.data.active = null;
  const p = B.planReconciliation(d, ws193), add = p.proposals.find(x => x.kind === 'ADD_CASE' && x.case_id === 'case-synth-fellowship');
  assert(add); assert.deepEqual(add.choices, ['RECORD_ONLY']); assert.equal(add.duplicate_of_desk, 'DESK_PROJECT_ALREADY_NAMES_THIS_CASE');
  assert.throws(() => B.applyReconciliation(d, ws193, p, [{ id: add.id, choice: 'ADOPT' }], { expected_base_revision: d.revision }), e => e.code === 'CHOICE_NOT_ALLOWED');
});
test('a user-made task with the same source blocks an ADD_TASK adoption', () => {
  const d = C.clone(desk), base = d.imports[0], cs = base.data.records.find(r => r.id === 'case-synth-fellowship');
  const proj = B.projectOf(d, 'case-synth-fellowship').project; d.tasks.push({ ...C.clone(d.tasks[0]), id: 'user-made-1', project: proj.id, source: 'case-synth-fellowship/task-interview', status: 'TODO', depends: [], note: '' });
  const p = B.planReconciliation(D.validate(d), ws193), add = p.proposals.find(x => x.kind === 'ADD_TASK' && x.task_id === 'task-interview');
  assert(add && add.duplicate_of_desk); assert.deepEqual(add.choices, ['RECORD_ONLY']);
});
test('adopting OPTIONAL/CANCELLED onto a task that Desk tasks depend on is refused (WAITING would block them forever)', () => {
  const d = C.clone(desk), sc = B.deskTaskFor(d, 'case-synth-fellowship', 'task-special-circ').task, other = d.tasks.find(t => t.id !== sc.id && t.project === sc.project);
  other.depends = [sc.id]; const dd = D.validate(d), p = B.planReconciliation(dd, ws193), prop = p.proposals.find(x => x.kind === 'ADOPT_SOURCE_CHANGE' && x.task_id === 'task-special-circ');
  assert.throws(() => B.applyReconciliation(dd, ws193, p, [{ id: prop.id, choice: 'ADOPT' }], { expected_base_revision: dd.revision }), e => e.code === 'GATE_REFUSED' && /depend/.test(e.message));
  assert.doesNotThrow(() => B.applyReconciliation(dd, ws193, p, [{ id: prop.id, choice: 'RECORD_ONLY' }], { expected_base_revision: dd.revision }));
});
test('several DONE tasks in one adopted case each need their own note; one shared note is refused', () => {
  const w = W.validate({ schema: 'humanaios.workspace_view.v1', revision: 9, intent: { goal: 'g', constraints: 'c', confirmed: true }, active: null, records: [F.rec('case-multi', 'Multi', [{ id: 'a', title: 'A', state: 'DONE' }, { id: 'b', title: 'B', state: 'DONE' }, { id: 'c', title: 'C', state: 'TODO' }])] });
  const d = D.empty(), p = B.planReconciliation(d, w), prop = p.proposals[0], run = ch => B.applyReconciliation(d, w, p, [{ id: prop.id, choice: 'ADOPT', ...ch }], { expected_base_revision: d.revision });
  assert.deepEqual(prop.tasks.map(t => t.state), ['DONE', 'DONE', 'TODO']);
  assert.throws(() => run({ note: 'one note for all' }), e => e.code === 'GATE_REFUSED');
  assert.throws(() => run({ notes: { a: 'mine a' } }), e => e.code === 'GATE_REFUSED');
  assert.throws(() => run({ notes: { a: 'mine a', b: 'Accepted email proposal; x' } }), e => e.code === 'GATE_REFUSED');
  const r = run({ notes: { a: 'mine a', b: 'mine b' } }); assert.deepEqual(r.desk.tasks.filter(t => t.status === 'DONE').map(t => t.note).sort(), ['mine a', 'mine b']);
});
test('the generated-note prefix saveTask refuses is refused by the bridge too', () => {
  const w = W.validate({ schema: 'humanaios.workspace_view.v1', revision: 9, intent: { goal: 'g', constraints: 'c', confirmed: true }, active: null, records: [F.rec('case-one', 'One', [{ id: 'a', title: 'A', state: 'DONE' }])] });
  const d = D.empty(), p = B.planReconciliation(d, w);
  assert.throws(() => B.applyReconciliation(d, w, p, [{ id: p.proposals[0].id, choice: 'ADOPT', note: 'Accepted email proposal; sent' }], { expected_base_revision: d.revision }), e => e.code === 'GATE_REFUSED');
});

// ---------- audit-3 repairs ----------
test('link-decision at the 5000-event cap is refused without the flag, and reports dropped events with it', () => {
  const big = D.seed(); while (big.events.length < 5000) D.event(big, 'padding ' + big.events.length); const d = D.validate(big);
  assert.throws(() => B.linkDecision(d, 'scope', ['offer'], { expected_base_revision: d.revision }), e => e.code === 'HISTORY_WOULD_ROLL_OFF');
  const r = B.linkDecision(d, 'scope', ['offer'], { expected_base_revision: d.revision, accept_roll_off: true }); assert.equal(r.changed, true); assert(r.history.dropped > 0); assert.equal(C.verifyHistoryPrefix(d, r.desk).dropped, r.history.dropped);
});
test('a case id that differs only in letter case is still the same case (no second project is offered)', () => {
  const d = C.clone(desk); d.imports[0].data.records = d.imports[0].data.records.filter(r => r.id !== 'case-synth-fellowship'); d.imports[0].data.active = null;
  const w = C.clone(ws193); const r0 = w.records.find(r => r.id === 'case-synth-fellowship'); r0.id = 'CASE-SYNTH-FELLOWSHIP'; r0.parent_resource_id = 'res-parent-x'; r0.resource_id = 'res-x'; w.active = null;
  const p = B.planReconciliation(d, W.validate(w)), add = p.proposals.find(x => x.kind === 'ADD_CASE' && x.case_id === 'CASE-SYNTH-FELLOWSHIP');
  assert(add && add.duplicate_of_desk); assert.deepEqual(add.choices, ['RECORD_ONLY']);
});
test('messages name no value taken from an input file', () => {
  const p = B.planReconciliation(desk, ws193);
  for (const [ch, code] of [[[{ id: 'SECRETID-1Z999', choice: 'ADOPT' }], 'UNKNOWN_PROPOSAL'], [[{ id: p.proposals.find(x => x.kind === 'ADD_CASE').id, choice: 'ADOPT' }, { id: p.proposals.find(x => x.kind === 'ADD_CASE').id, choice: 'ADOPT' }], 'DUPLICATE_CHOICE']]) {
    try { B.applyReconciliation(desk, ws193, p, ch, opts()); assert.fail('no throw'); } catch (e) { assert.equal(e.code, code); assert(!/SECRETID|1Z999/.test(e.message)); }
  }
});

// ---------- audit-4 repairs ----------
test('a refusal never quotes hold text or task titles from the input', () => {
  const w = wsNew([{ id: 't1', title: 'SECRET-TITLE-1Z999', state: 'DOING' }], { pursuit: 'ON_HOLD', hold_reason: 'SECRET-HOLD-1Z999' }), f = firstImport(w);
  try { f.run(); assert.fail('no throw'); } catch (e) { assert.equal(e.code, 'GATE_REFUSED'); assert(!/1Z999|SECRET/.test(e.message), e.message); assert.match(e.message, /on hold/); }
});
test('verify-history names no import id from the file', () => { const a = C.clone(desk); a.imports[0].id = 'SECRETIMPORT_1Z999'; const v = C.verifyHistoryPrefix(desk, a); assert.equal(v.ok, false); assert(!/1Z999|SECRET/.test(v.reason)); });
test('a task id that differs only by letter case is the same source: ADD_TASK becomes RECORD_ONLY', () => {
  const d = C.clone(desk), proj = B.projectOf(d, 'case-synth-fellowship').project; d.tasks.push({ ...C.clone(d.tasks[0]), id: 'user-made-2', project: proj.id, source: 'case-synth-fellowship/task-interview', status: 'TODO', depends: [], note: '' });
  const w = C.clone(ws193); w.records.find(r => r.id === 'case-synth-fellowship').tasks.find(t => t.id === 'task-interview').id = 'TASK-INTERVIEW';
  const p = B.planReconciliation(D.validate(d), W.validate(w)), add = p.proposals.find(x => x.kind === 'ADD_TASK' && x.task_id === 'TASK-INTERVIEW'); assert(add && add.duplicate_of_desk); assert.deepEqual(add.choices, ['RECORD_ONLY']);
});

test('adopting a source state change into a held project is refused without quoting the hold text', () => {
  const d = C.clone(desk), proj = B.projectOf(d, 'case-synth-fellowship').project; d.projects.find(x => x.id === proj.id).hold = 'SECRET-HOLD-1Z999';
  const w = C.clone(ws193), r0 = w.records.find(r => r.id === 'case-synth-fellowship'); r0.tasks.find(t => t.id === 'task-special-circ').state = 'DOING';
  const dd = D.validate(d), ww = W.validate(w), p = B.planReconciliation(dd, ww), prop = p.proposals.find(x => x.kind === 'ADOPT_SOURCE_CHANGE' && x.task_id === 'task-special-circ'); assert(prop, 'special-circ proposal');
  try { B.applyReconciliation(dd, ww, p, [{ id: prop.id, choice: 'ADOPT' }], { expected_base_revision: dd.revision }); assert.fail('no throw'); } catch (e) { assert.equal(e.code, 'GATE_REFUSED'); assert(!/1Z999|SECRET/.test(e.message), e.message); assert.match(e.message, /on hold/); }
});

// ---------- audit-5 repairs ----------
test('every Desk refusal class is a fixed sentence that never quotes the Desk reason', () => {
  for (const why of ['Project on hold: SECRET-1Z999', 'Dependency project on hold: SECRET-1Z999', 'Needs: SECRET-1Z999', 'Missing dependency: SECRET-1Z999', 'Missing project', 'Something SECRET-1Z999 else']) { const c = B.blockedClass(why); assert(!/SECRET|1Z999/.test(c), why); assert(c.length > 8); }
  assert.notEqual(B.blockedClass('Project on hold: x'), B.blockedClass('Needs: x')); assert.notEqual(B.blockedClass('Needs: x'), B.blockedClass('Missing dependency: x')); assert.notEqual(B.blockedClass('Dependency project on hold: x'), B.blockedClass('Project on hold: x'));
});
finish();

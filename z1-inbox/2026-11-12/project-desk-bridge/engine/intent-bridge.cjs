'use strict';
// Test B engine: Project Desk <-> INTENT-OS compatibility, READ-ONLY toward INTENT-OS.
// It only ever reads an exported workspace file and returns a NEW Desk state. It has no writeback path,
// no network, no clock and no randomness: the same inputs always give the same plan and the same ids.
const D = require('../dist/model.js'), W = require('../dist/intent-workspace.js');
const { canonical, digest, shortId, clone, BridgeError, StaleWriteError, verifyHistoryPrefix } = require('./core.cjs');

const RECONCILED_ID = /^intent-workspace(?:@(\d+))?$/;      // legacy id has no suffix
const OBSERVED_ID = /^intent-observed@(\d+)$/;
const ORIGIN_RE = /^INTENT-OS snapshot · ([A-Za-z0-9_-]{1,100}) · revision (\d+)$/;
const MARKER_RE = /^Bridge (brg-[0-9a-f]{16}) (ADOPT|KEEP_DESK|RECORD_ONLY)\b/;
const GENERATED = 'Imported task state: ';
const genNote = s => GENERATED + s + '; snapshot only. No independent verification.';
const isGenerated = n => typeof n === 'string' && (n.startsWith(GENERATED) || n.startsWith('Accepted email proposal;'));   // same two prefixes dist/model.js saveTask refuses for DONE
const mapState = s => s === 'DONE' ? 'DONE' : ['WAITING', 'BLOCKED', 'DOING'].includes(s) ? s : ['OPTIONAL', 'CANCELLED', 'NOT_APPLICABLE'].includes(s) ? 'WAITING' : 'TODO';
// A Desk refusal reason may quote hold text or task titles; callers see only a fixed class so no file content leaves in an error.
const blockedClass = why => /^Project on hold/.test(why) ? 'the project is on hold' : /^Dependency project on hold/.test(why) ? 'a task it depends on is in a project that is on hold' : /^Needs:/.test(why) ? 'it depends on a Desk task that is not DONE' : /^Missing/.test(why) ? 'a project or dependency is missing' : 'it is blocked';
const srcEq = (a, b) => typeof a === 'string' && typeof b === 'string' && a.toLowerCase() === b.toLowerCase();   // the workspace treats ids case-insensitively
const holdOf = r => r.pursuit === 'ACTIVE' ? '' : (r.hold_reason || r.pursuit);
const CHOICES = {
  ADD_CASE: ['ADOPT', 'RECORD_ONLY'], ADD_TASK: ['ADOPT', 'RECORD_ONLY'],
  ADOPT_SOURCE_CHANGE: ['ADOPT', 'KEEP_DESK', 'RECORD_ONLY'], CONFLICT_TASK: ['KEEP_DESK', 'RECORD_ONLY', 'ADOPT'],
  SET_PROJECT_HOLD: ['ADOPT', 'KEEP_DESK', 'RECORD_ONLY'], CONFLICT_HOLD: ['KEEP_DESK', 'RECORD_ONLY', 'ADOPT'],
  UNMAPPED_CHANGE: ['RECORD_ONLY'], TASK_REMOVED: ['RECORD_ONLY'], CASE_REMOVED: ['RECORD_ONLY'],
  CASE_INFO_CHANGED: ['RECORD_ONLY'], EVIDENCE_CHANGED: ['RECORD_ONLY'], INTENT_CHANGED: ['RECORD_ONLY'],
};

// ---------- snapshots kept inside the Desk (history is never replaced) ----------
function snapshots(desk) {
  const rows = [];
  for (const i of desk.imports) {
    const m = RECONCILED_ID.exec(i.id), o = OBSERVED_ID.exec(i.id);
    if (m) rows.push({ id: i.id, cls: 'RECONCILED', revision: i.revision, data: i.data, sha256: digest(i.data) });
    else if (o) rows.push({ id: i.id, cls: 'OBSERVED', revision: i.revision, data: i.data, sha256: digest(i.data) });
  }
  return rows.sort((a, b) => a.revision - b.revision || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}
function latestBaseline(desk) {
  const r = snapshots(desk).filter(s => s.cls === 'RECONCILED');
  if (!r.length) return null;
  const top = r.filter(s => s.revision === r[r.length - 1].revision);
  if (new Set(top.map(s => s.sha256)).size > 1) throw new BridgeError('AMBIGUOUS_BASELINE', 'Two different reconciled snapshots share the newest revision');
  let data; try { data = W.validate(top[0].data); } catch (e) { throw new BridgeError('BASELINE_INVALID', 'Stored baseline snapshot is not a valid workspace: ' + e.message); }
  return { ...top[0], data };
}

// ---------- identity: a Desk task is "the" copy of a source task only if BOTH the task source string AND its project origin agree ----------
function projectOf(desk, caseId) {
  const ps = desk.projects.filter(p => { const m = ORIGIN_RE.exec(p.origin); return m && m[1].toLowerCase() === String(caseId).toLowerCase(); });   // the workspace treats case ids case-insensitively
  return { project: ps.length === 1 ? ps[0] : null, count: ps.length };
}
function deskTaskFor(desk, caseId, taskId) {
  const pj = projectOf(desk, caseId);
  if (!pj.project) return { status: pj.count ? 'AMBIGUOUS_PROJECT' : 'UNMAPPED' };
  const ts = desk.tasks.filter(t => t.project === pj.project.id && srcEq(t.source, caseId + '/' + taskId));
  return ts.length === 1 ? { status: 'MAPPED', task: ts[0], project: pj.project } : { status: ts.length ? 'AMBIGUOUS_TASK' : 'UNMAPPED', project: pj.project };
}

// ---------- revision comparison ----------
function relation(a, b) {
  if (digest(a) === digest(b)) return 'IDENTICAL';
  if (b.revision > a.revision) return 'NEWER';
  if (b.revision < a.revision) return 'OLDER';
  return 'SAME_REVISION_DIFFERENT_CONTENT';
}
function compareWorkspaces(a, b) {
  const changes = [], A = new Map(a.records.map(r => [r.id, r])), B = new Map(b.records.map(r => [r.id, r]));
  if (canonical(a.intent) !== canonical(b.intent)) changes.push({ kind: 'INTENT_CHANGED', before: a.intent, after: b.intent });
  for (const id of [...new Set([...A.keys(), ...B.keys()])].sort()) {
    const x = A.get(id), y = B.get(id);
    if (!x) { changes.push({ kind: 'CASE_ADDED', case_id: id, task_ids: y.tasks.map(t => t.id) }); continue; }
    if (!y) { changes.push({ kind: 'CASE_REMOVED', case_id: id, task_ids: x.tasks.map(t => t.id) }); continue; }
    for (const f of ['title', 'goal', 'pursuit', 'hold_reason', 'files_ready', 'parent_resource_id', 'resource_id'])
      if (x[f] !== y[f]) changes.push({ kind: 'CASE_FIELD_CHANGED', case_id: id, field: f, before: x[f], after: y[f] });
    const XT = new Map(x.tasks.map(t => [t.id, t])), YT = new Map(y.tasks.map(t => [t.id, t]));
    for (const tid of [...new Set([...XT.keys(), ...YT.keys()])].sort()) {
      const p = XT.get(tid), q = YT.get(tid);
      if (!p) changes.push({ kind: 'TASK_ADDED', case_id: id, task_id: tid, after: q });
      else if (!q) changes.push({ kind: 'TASK_REMOVED', case_id: id, task_id: tid, before: p });
      else for (const f of ['title', 'state']) if (p[f] !== q[f]) changes.push({ kind: 'TASK_FIELD_CHANGED', case_id: id, task_id: tid, field: f, before: p[f], after: q[f] });
    }
    for (const list of ['references', 'reports']) {
      const pa = new Set(x[list].map(digest)), pb = new Set(y[list].map(digest)), one = list === 'reports' ? 'REPORT' : 'REFERENCE';
      for (const e of y[list]) if (!pa.has(digest(e))) changes.push({ kind: one + '_ADDED', case_id: id, item: e });
      for (const e of x[list]) if (!pb.has(digest(e))) changes.push({ kind: one + '_REMOVED', case_id: id, item: e });
    }
  }
  return { relation: relation(a, b), from_revision: a.revision, to_revision: b.revision, from_sha256: digest(a), to_sha256: digest(b), changes };
}

// ---------- planning (pure; never mutates) ----------
const resolvedMarkers = desk => { const m = new Map(); for (const e of desk.events) { const x = MARKER_RE.exec(e.text); if (x) m.set(x[1], x[2]); } return m; };

// An ADD_CASE lists each task's state so the reviewer sees what would be created, and is RECORD_ONLY if the Desk already has a project naming the case.
function addCaseBody(desk, r) {
  return { case_id: r.id, title: r.title, task_ids: r.tasks.map(t => t.id), tasks: r.tasks.map(t => ({ id: t.id, state: t.state })), ...(projectOf(desk, r.id).count ? { duplicate_of_desk: 'DESK_PROJECT_ALREADY_NAMES_THIS_CASE' } : {}) };
}
function planReconciliation(deskRaw, wsRaw) {
  const desk = D.validate(deskRaw), ws = W.validate(wsRaw), base = latestBaseline(desk), resolved = resolvedMarkers(desk);
  const plan = { schema: 'humanaios.intent-bridge.plan.v1', writeback: false, desk_revision: desk.revision, new_revision: ws.revision, new_sha256: digest(ws),
    baseline: base && { id: base.id, revision: base.revision, sha256: base.sha256 }, relation: null, refused: null, idempotent: false, proposals: [] };
  const finish = () => { plan.proposals.sort((p, q) => (p.case_id || '').localeCompare(q.case_id || '') || (p.task_id || '').localeCompare(q.task_id || '') || p.kind.localeCompare(q.kind) || p.id.localeCompare(q.id)); plan.digest = digest(plan); return plan; };
  const ctx = { base: base ? base.revision : null, bsha: base ? base.sha256 : null, nw: ws.revision, nsha: plan.new_sha256 };
  const add = (kind, severity, body) => { const p = { kind, severity, choices: body.duplicate_of_desk ? ['RECORD_ONLY'] : CHOICES[kind], ...body, base_revision: ctx.base, new_revision: ctx.nw };
    p.id = shortId('brg-', { v: 1, kind, body, ctx }); if (!resolved.has(p.id)) plan.proposals.push(p); };
  if (!base) { plan.relation = 'FIRST_IMPORT'; for (const r of ws.records) add('ADD_CASE', 'ACTION', addCaseBody(desk, r)); return finish(); }
  plan.relation = relation(base.data, ws);
  if (plan.relation === 'IDENTICAL') { plan.idempotent = true; return finish(); }
  if (plan.relation !== 'NEWER') { plan.refused = plan.relation; return finish(); }
  const diff = compareWorkspaces(base.data, ws), byTask = new Map(), baseCase = new Map(base.data.records.map(r => [r.id, r]));
  for (const c of diff.changes) {
    if (c.kind === 'TASK_FIELD_CHANGED') { const k = c.case_id + '\u0000' + c.task_id; (byTask.get(k) || byTask.set(k, []).get(k)).push(c); }
    else if (c.kind === 'TASK_ADDED') {
      const pj = projectOf(desk, c.case_id);
      if (pj.project) add('ADD_TASK', 'ACTION', { case_id: c.case_id, task_id: c.task_id, title: c.after.title, state: c.after.state, project_id: pj.project.id, ...(desk.tasks.some(x => srcEq(x.source, c.case_id + '/' + c.task_id)) ? { duplicate_of_desk: 'DESK_TASK_WITH_THIS_SOURCE_EXISTS' } : {}) });
      else add('UNMAPPED_CHANGE', 'CONFLICT', { case_id: c.case_id, task_id: c.task_id, detail: 'TASK_ADDED but the case has no unique Desk project' });
    }
    else if (c.kind === 'TASK_REMOVED') add('TASK_REMOVED', 'INFO', { case_id: c.case_id, task_id: c.task_id, last_known_state: c.before.state });
    else if (c.kind === 'CASE_ADDED') add('ADD_CASE', 'ACTION', addCaseBody(desk, ws.records.find(r => r.id === c.case_id)));
    else if (c.kind === 'CASE_REMOVED') add('CASE_REMOVED', 'INFO', { case_id: c.case_id, task_ids: c.task_ids });
    else if (c.kind === 'INTENT_CHANGED') add('INTENT_CHANGED', 'INFO', { before: c.before, after: c.after });
  }
  for (const [k, list] of [...byTask.entries()].sort((a, b) => a[0].localeCompare(b[0]))) {
    const [caseId, taskId] = k.split('\u0000'), m = deskTaskFor(desk, caseId, taskId);
    const s0 = baseCase.get(caseId).tasks.find(t => t.id === taskId);
    const history = { [`r${base.revision}`]: s0.state, [`r${ws.revision}`]: list.find(x => x.field === 'state') ? list.find(x => x.field === 'state').after : s0.state };
    if (m.status !== 'MAPPED') { add('UNMAPPED_CHANGE', 'CONFLICT', { case_id: caseId, task_id: taskId, detail: 'Desk copy is ' + m.status, source_history: history }); continue; }
    const t = m.task, fields = list.map(c => {
      const edited = c.field === 'state' ? (t.status !== mapState(c.before) || (t.note !== genNote(c.before))) : t.title !== c.before;
      return { field: c.field, from: c.before, to: c.after, desk_value: c.field === 'state' ? t.status : t.title, desk_edited: edited };
    });
    add(fields.some(f => f.desk_edited) ? 'CONFLICT_TASK' : 'ADOPT_SOURCE_CHANGE', fields.some(f => f.desk_edited) ? 'CONFLICT' : 'ACTION',
      { case_id: caseId, task_id: taskId, desk_task_id: t.id, desk_status: t.status, fields, source_history: history });
  }
  const caseChanges = new Map();
  for (const c of diff.changes) if (['CASE_FIELD_CHANGED', 'REPORT_ADDED', 'REPORT_REMOVED', 'REFERENCE_ADDED', 'REFERENCE_REMOVED'].includes(c.kind)) (caseChanges.get(c.case_id) || caseChanges.set(c.case_id, []).get(c.case_id)).push(c);
  for (const [caseId, list] of [...caseChanges.entries()].sort()) {
    const bc = baseCase.get(caseId), nc = ws.records.find(r => r.id === caseId), holdChanged = holdOf(bc) !== holdOf(nc);
    if (holdChanged) {
      const pj = projectOf(desk, caseId);
      if (!pj.project) add('UNMAPPED_CHANGE', 'CONFLICT', { case_id: caseId, detail: 'hold changed but the case has no unique Desk project' });
      else if (pj.project.hold === holdOf(bc)) add('SET_PROJECT_HOLD', 'ACTION', { case_id: caseId, project_id: pj.project.id, from: holdOf(bc), to: holdOf(nc) });
      else add('CONFLICT_HOLD', 'CONFLICT', { case_id: caseId, project_id: pj.project.id, from: holdOf(bc), to: holdOf(nc), desk_value: pj.project.hold });
    }
    const info = list.filter(c => c.kind === 'CASE_FIELD_CHANGED' && !['pursuit', 'hold_reason'].includes(c.field));
    if (info.length) add('CASE_INFO_CHANGED', 'INFO', { case_id: caseId, fields: info.map(c => ({ field: c.field, from: c.before, to: c.after })) });
    const ev = list.filter(c => /^(REPORT|REFERENCE)_/.test(c.kind));
    if (ev.length) add('EVIDENCE_CHANGED', 'INFO', { case_id: caseId, changes: ev.map(c => ({ kind: c.kind, item: c.item })) });
  }
  return finish();
}
function B_title(ws, caseId) { return ws.records.find(r => r.id === caseId).title; }

// ---------- applying explicit human choices (atomic; returns a NEW Desk state; never touches the source) ----------
function applyReconciliation(deskRaw, wsRaw, planIn, choices, opts) {
  const desk = D.validate(deskRaw), ws = W.validate(wsRaw);
  if (!opts || !Number.isSafeInteger(opts.expected_base_revision)) throw new BridgeError('EXPECTED_REVISION_REQUIRED', 'Say which Desk revision these choices were made against.');
  if (desk.revision !== opts.expected_base_revision) throw new StaleWriteError(opts.expected_base_revision, desk.revision, { choices });
  const plan = planReconciliation(desk, ws);
  if (planIn && planIn.digest !== plan.digest) throw new BridgeError('PLAN_MISMATCH', 'The plan you reviewed no longer matches these inputs. Nothing was written.');
  if (plan.refused) throw new BridgeError('REFUSED_' + plan.refused, 'Refusing a ' + plan.refused + ' snapshot: it is preserved untouched; decide manually.');
  if (plan.idempotent) return { desk: clone(desk), changed: false, applied: [], remaining: [] };
  const byId = new Map(plan.proposals.map(p => [p.id, p])), chosen = new Map();
  for (const c of choices || []) {
    const p = byId.get(c.id);
    if (!p) throw new BridgeError('UNKNOWN_PROPOSAL', 'A choice names a proposal that is not in this plan (or is already resolved)');
    if (chosen.has(c.id)) throw new BridgeError('DUPLICATE_CHOICE', 'Two choices were given for one proposal');
    if (!p.choices.includes(c.choice)) throw new BridgeError('CHOICE_NOT_ALLOWED', `That choice is not allowed for a ${p.kind} proposal`);
    if (c.choice === 'ADOPT' && /^CONFLICT_/.test(p.kind) && c.confirm_overwrite !== true) throw new BridgeError('OVERWRITE_NOT_CONFIRMED', 'Adopting over your own Desk edits needs confirm_overwrite: true');
    chosen.set(c.id, c);
  }
  const n = clone(desk), applied = [], summaries = [];
  for (const p of plan.proposals) {
    const c = chosen.get(p.id); if (!c) continue;
    summaries.push(applyOne(n, ws, p, c)); applied.push({ id: p.id, choice: c.choice });
  }
  for (const s of summaries) D.event(n, s);
  const remaining = plan.proposals.filter(p => !chosen.has(p.id)).map(p => p.id);
  const snapId = (remaining.length ? 'intent-observed@' : 'intent-workspace@') + ws.revision;
  const existing = n.imports.find(i => i.id === snapId);
  if (existing && digest(existing.data) !== digest(ws)) throw new BridgeError('SNAPSHOT_ID_COLLISION', snapId + ' already holds different content');
  let touched = applied.length > 0;
  if (!existing) { n.imports.push({ id: snapId, revision: ws.revision, captured_at: opts.captured_at || '1970-01-01T00:00:00.000Z', data: clone(ws) }); touched = true;
    D.event(n, `Bridge snapshot ${snapId} sha256 ${digest(ws).slice(0, 16)} ${remaining.length ? 'OBSERVED, ' + remaining.length + ' proposal(s) unresolved' : 'RECONCILED'}`); }
  if (!touched) return { desk: clone(desk), changed: false, applied: [], remaining };
  n.revision = desk.revision + 1;
  const out = D.validate(n), pre = verifyHistoryPrefix(desk, out);
  if (!pre.ok) throw new BridgeError('HISTORY_NOT_PRESERVED', pre.reason + '. This apply would append too many events at once (Desk history is capped); choose fewer proposals per apply. Nothing was written.');
  if (pre.dropped > 0 && opts.accept_roll_off !== true) throw new BridgeError('HISTORY_WOULD_ROLL_OFF', `This apply would push ${pre.dropped} of the oldest Desk events out of the capped history. Nothing was written. Export the Desk first, then re-run with accept_roll_off (CLI: --accept-roll-off), or choose fewer proposals.`);
  return { desk: out, changed: true, applied, remaining, history: { dropped: pre.dropped, appended: pre.appended } };
}

function applyOne(n, ws, p, c) {
  const tag = `Bridge ${p.id} ${c.choice}`;
  const find = id => n.tasks.find(t => t.id === id);
  if (c.choice !== 'ADOPT') return `${tag}: ${p.kind} ${p.case_id || ''}${p.task_id ? '/' + p.task_id : ''}${c.choice === 'KEEP_DESK' ? ' desk value kept; source observation recorded' : ' recorded only'}${p.source_history ? ' ' + JSON.stringify(p.source_history) : ''}`;
  if (p.kind === 'ADD_CASE') {
    const r = ws.records.find(x => x.id === p.case_id), pid = shortId('ixp-', { case: r.id });
    if (n.projects.some(x => x.id === pid)) throw new BridgeError('ID_COLLISION', 'A Desk project with this id already exists');
    if (projectOf(n, r.id).count) throw new BridgeError('DUPLICATE_ORIGIN', 'A Desk project already names this case; choose RECORD_ONLY or resolve the duplicate yourself.', { proposal: p.id });
    const doneCount = r.tasks.filter(x => mapState(x.state) === 'DONE').length;
    n.projects.push({ id: pid, name: r.title, outcome: r.goal || ws.intent.goal || 'Outcome not recorded', hold: holdOf(r), origin: `INTENT-OS snapshot · ${r.id} · revision ${ws.revision}` });
    for (const t of r.tasks) { const nt = newTask(pid, r.id, t); n.tasks.push(nt); gateNew(n, nt, c, p, doneCount, t.id); }
    return `${tag}: added case ${r.id} with ${r.tasks.length} task(s) from source r${ws.revision}`;
  }
  if (p.kind === 'ADD_TASK') {
    const t = ws.records.find(x => x.id === p.case_id).tasks.find(x => x.id === p.task_id), id = shortId('ixt-', { case: p.case_id, task: p.task_id });
    if (n.tasks.some(x => x.id === id)) throw new BridgeError('ID_COLLISION', 'A Desk task with this id already exists');
    if (n.tasks.some(x => srcEq(x.source, p.case_id + '/' + p.task_id))) throw new BridgeError('DUPLICATE_SOURCE', 'A Desk task already has this source; choose RECORD_ONLY.', { proposal: p.id });
    const nt = newTask(p.project_id, p.case_id, t); n.tasks.push(nt); gateNew(n, nt, c, p, 1, t.id); return `${tag}: added task ${p.case_id}/${p.task_id} (${t.state}) from source r${ws.revision}`;
  }
  if (p.kind === 'SET_PROJECT_HOLD' || p.kind === 'CONFLICT_HOLD') { const pj = n.projects.find(x => x.id === p.project_id); const before = pj.hold; pj.hold = p.to; return `${tag}: project hold "${before}" -> "${p.to}" (source r${p.new_revision})`; }
  if (p.kind === 'ADOPT_SOURCE_CHANGE' || p.kind === 'CONFLICT_TASK') {
    const t = find(p.desk_task_id), before = { status: t.status, title: t.title, note: t.note };
    for (const f of p.fields) {
      if (f.field === 'title') t.title = f.to;
      if (f.field === 'state') {
        if (['OPTIONAL', 'CANCELLED', 'NOT_APPLICABLE'].includes(f.to) && n.tasks.some(x => x.depends.includes(t.id))) throw new BridgeError('GATE_REFUSED', `The Desk cannot show ${f.to}; it would stay WAITING and block the Desk tasks that depend on it. Remove those dependencies yourself first, or choose RECORD_ONLY.`, { proposal: p.id });
        const next = mapState(f.to), was = t.status; t.status = next;
        if (isGenerated(t.note) || !t.note) t.note = genNote(f.to);
        if (next === 'DONE') { if (!c.note || isGenerated(c.note)) throw new BridgeError('GATE_REFUSED', 'Adopting a source DONE needs your own outcome note (choice.note)', { proposal: p.id }); t.note = c.note; }
        if (['DOING', 'DONE'].includes(next) && was !== next) { const why = D.blocked(n, t); if (why) throw new BridgeError('GATE_REFUSED', 'The change was refused because ' + blockedClass(why), { proposal: p.id }); }
      }
    }
    return `${tag}: ${p.case_id}/${p.task_id} ${p.fields.map(f => `${f.field} ${f.from}->${f.to}`).join(', ')}; Desk was ${before.status}, now ${t.status}; source history ${JSON.stringify(p.source_history)}`;
  }
  throw new BridgeError('NOT_ADOPTABLE', p.kind + ' cannot be adopted');
}
// A new Desk task must obey the same rules as saveTask: DONE needs the user's own outcome note; DOING/DONE cannot sit in a held or blocked project.
function gateNew(n, t, c, p, doneCount, srcTaskId) {
  if (t.status === 'DONE') {
    // One note may cover exactly one DONE task; several DONE tasks each need their own entry in choice.notes {taskId: note}.
    const own = c.notes && typeof c.notes === 'object' && Object.hasOwn(c.notes, srcTaskId) ? c.notes[srcTaskId] : (doneCount === 1 ? c.note : null);
    if (!own || isGenerated(own)) throw new BridgeError('GATE_REFUSED', `Adopting a source task as DONE needs your own outcome note (choice.note for one task, choice.notes[taskId] for several), or choose RECORD_ONLY`, { proposal: p.id }); t.note = own;
  }
  if (['DOING', 'DONE'].includes(t.status)) { const why = D.blocked(n, t); if (why) throw new BridgeError('GATE_REFUSED', 'The new task was refused because ' + blockedClass(why) + '. Choose RECORD_ONLY or clear the cause first.', { proposal: p.id }); }
}
function newTask(projectId, caseId, t) {
  return { id: shortId('ixt-', { case: caseId, task: t.id }), project: projectId, title: t.title, step: 'Review the original case and define the next step.', done_when: 'Confirm the result in the original case.',
    status: mapState(t.state), priority: 2, owner: 'Unassigned', depends: [], note: genNote(t.state), evidence: '', source: caseId + '/' + t.id };
}

// ---------- one-case round trip: a REVIEW PREVIEW in INTENT-OS format. Nothing is written anywhere. ----------
function roundTripPreview(deskRaw, wsRaw, caseId) {
  const desk = D.validate(deskRaw), ws = W.validate(wsRaw), r = ws.records.find(x => x.id === caseId);
  if (!r) throw new BridgeError('UNKNOWN_CASE', 'The case is not in the workspace');
  const base = latestBaseline(desk);   // a Desk that has not reconciled with THIS snapshot could silently regress newer source states
  if (!base || base.sha256 !== digest(ws)) throw new BridgeError('NOT_RECONCILED', 'Reconcile the Desk with this exact snapshot before previewing a round trip.');
  const preview = clone(ws), pr = preview.records.find(x => x.id === caseId), unmapped = [];
  for (const t of pr.tasks) {
    const m = deskTaskFor(desk, caseId, t.id);
    if (m.status !== 'MAPPED') { unmapped.push({ task_id: t.id, why: m.status }); continue; }
    if (m.task.status !== mapState(t.state)) t.state = m.task.status;   // Desk-reported state, suggested for MANUAL review only
  }
  const valid = W.validate(preview), diff = compareWorkspaces(ws, valid);
  const outside = diff.changes.filter(c => !(c.kind === 'TASK_FIELD_CHANGED' && c.case_id === caseId && c.field === 'state'));
  if (outside.length) throw new BridgeError('PREVIEW_SCOPE', 'Preview changed something other than task states of the chosen case');
  return { preview_only: true, writeback: false, case_id: caseId, source_revision: ws.revision, source_sha256: digest(ws), preview_sha256: digest(valid), unmapped, changes: diff.changes, preview_workspace: valid };
}

// ---------- explicit decision dependencies, using only existing Desk mechanics (a gate task + task dependencies) ----------
function linkDecision(deskRaw, decisionId, dependentIds, opts) {
  const desk = D.validate(deskRaw), dec = desk.decisions.find(d => d.id === decisionId);
  if (!dec) throw new BridgeError('UNKNOWN_DECISION', 'No such decision');
  if (opts && Number.isSafeInteger(opts.expected_base_revision) && opts.expected_base_revision !== desk.revision) throw new StaleWriteError(opts.expected_base_revision, desk.revision, { decisionId, dependentIds });
  const gateId = 'gate-' + decisionId; if (gateId.length > 100) throw new BridgeError('ID_TOO_LONG', 'Decision id too long to gate');
  const n = clone(desk); let changed = false, gate = n.tasks.find(t => t.id === gateId);
  if (gate && gate.source !== 'decision:' + decisionId) throw new BridgeError('ID_COLLISION', 'The gate id is already used by an unrelated task');
  if (!gate) { gate = { id: gateId, project: dec.project, title: ('Decide: ' + dec.question).slice(0, 200), step: 'Record the decision in the Decisions view, then complete this gate with your own outcome note.', done_when: 'The decision has an answer and a reason, and you have confirmed it here.', status: 'TODO', priority: 1, owner: 'Night', depends: [], note: '', evidence: '', source: 'decision:' + decisionId }; n.tasks.push(gate); changed = true; }
  for (const id of dependentIds) {
    const t = n.tasks.find(x => x.id === id); if (!t) throw new BridgeError('UNKNOWN_TASK', 'No such task');
    if (id === gateId) throw new BridgeError('SELF_DEPENDENCY', 'A gate cannot depend on itself');
    if (!t.depends.includes(gateId)) { t.depends.push(gateId); changed = true; }
  }
  if (!changed) return { desk: clone(desk), changed: false, gate_id: gateId };
  n.revision = desk.revision + 1; D.event(n, `Linked decision ${decisionId} as gate ${gateId} for ${dependentIds.join(', ')}; no task was completed or unblocked automatically`);
  const out = D.validate(n), pre = verifyHistoryPrefix(desk, out); if (!pre.ok) throw new BridgeError('HISTORY_NOT_PRESERVED', pre.reason);
  if (pre.dropped > 0 && !(opts && opts.accept_roll_off === true)) throw new BridgeError('HISTORY_WOULD_ROLL_OFF', `This would push ${pre.dropped} of the oldest Desk events out of the capped history. Nothing was written.`);
  return { desk: out, changed: true, gate_id: gateId, history: { dropped: pre.dropped, appended: pre.appended } };
}
// Suggestions only. A gate is opened/closed by a human with their own note, never by this function.
function proposeGateClosures(deskRaw) {
  const desk = D.validate(deskRaw);
  return desk.tasks.filter(t => t.source.startsWith('decision:') && t.status !== 'DONE').flatMap(t => {
    const d = desk.decisions.find(x => x.id === t.source.slice(9)); return d && d.answer && d.reason ? [{ gate_id: t.id, decision_id: d.id, suggestion: 'COMPLETE_GATE_WITH_YOUR_OWN_NOTE', automatic: false }] : [];
  });
}

module.exports = { snapshots, latestBaseline, deskTaskFor, projectOf, compareWorkspaces, planReconciliation, applyReconciliation, roundTripPreview, linkDecision, proposeGateClosures, mapState, genNote, isGenerated, blockedClass, MARKER_RE };

'use strict';
// SYNTHETIC DATA ONLY. Names, ids, notes and amounts are invented for tests. These are NOT the user's records.
const W = require('../dist/intent-workspace.js'), D = require('../dist/model.js');
const clone = x => JSON.parse(JSON.stringify(x));
const T = '2026-10-01T00:00:00Z';
function rec(id, title, tasks, extra) {
  return { id, parent_resource_id: 'res-parent-' + id, title, resource_id: 'res-' + id, goal: 'SYNTHETIC goal', pursuit: 'ACTIVE', hold_reason: '', files_ready: 'UNKNOWN',
    tasks, references: [{ title: 'SYNTHETIC reference', url: 'https://example.org/' + id, role: 'DISCOVERY_SOURCE_NOT_VERIFIED', observed_at: T }],
    reports: [{ axis: 'SOURCE', value: 'UNVERIFIED', note: 'SYNTHETIC lead', evidence_url: 'https://example.org/' + id, observed_at: T }], ...(extra || {}) };
}
// Older snapshot (revision 119): the synthetic special-circumstances task is BLOCKED.
function ws119() {
  return W.validate({ schema: 'humanaios.workspace_view.v1', revision: 119, intent: { goal: 'SYNTHETIC goal', constraints: 'SYNTHETIC', confirmed: true }, active: 'case-synth-fellowship',
    records: [
      rec('case-synth-fellowship', 'Synthetic Fellowship', [{ id: 'task-special-circ', title: 'Special circumstances statement', state: 'BLOCKED' }, { id: 'task-statement', title: 'Personal statement', state: 'TODO' }, { id: 'task-refs', title: 'Reference letters', state: 'DOING' }]),
      rec('case-synth-grant', 'Synthetic Grant', [{ id: 'task-apply', title: 'Apply', state: 'TODO' }]),
    ] });
}
// Newer snapshot (revision 193): same stable task id is now OPTIONAL; plus other independent changes.
function ws193() {
  const w = clone(ws119()); w.revision = 193; w.intent.goal = 'SYNTHETIC goal, revised';
  const f = w.records[0]; f.tasks[0].state = 'OPTIONAL'; f.tasks[1].state = 'DONE'; f.tasks.push({ id: 'task-interview', title: 'Interview preparation', state: 'TODO' });
  f.reports.push({ axis: 'SUBMISSION', value: 'UNKNOWN', note: 'SYNTHETIC', evidence_url: '', observed_at: '2026-10-20T00:00:00Z' });
  const g = w.records[1]; g.tasks = []; g.pursuit = 'ON_HOLD'; g.hold_reason = 'SYNTHETIC: waiting on funder';
  w.records.push(rec('case-synth-new', 'Synthetic New Case', [{ id: 'task-first', title: 'First step', state: 'TODO' }]));
  return W.validate(w);
}
// A Desk that looks like the user's: LEGACY import (random ids, id "intent-workspace"), then the user's own edits.
function deskAfterLegacyImport(ws) { return D.importIntent(D.empty(), ws || ws119()); }
const taskOf = (d, caseId, taskId) => d.tasks.find(t => t.source === caseId + '/' + taskId);
function deskWithUserEdits(ws) {
  let d = deskAfterLegacyImport(ws);
  const t = taskOf(d, 'case-synth-fellowship', 'task-statement');                   // user started it and wrote their own note
  d = D.saveTask(d, { ...t, status: 'DOING', note: 'MY OWN NOTE: drafting this week' });
  return d;
}
// events without the random ids/timestamps the Desk model assigns, so two runs can be compared
const norm = d => { const c = clone(d); c.events = c.events.map(e => e.text); c.imports.forEach(i => { i.captured_at = 'x'; }); return c; };
module.exports = { ws119, ws193, deskAfterLegacyImport, deskWithUserEdits, taskOf, norm, clone, rec, T };

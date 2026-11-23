#!/usr/bin/env node
'use strict';
// Offline CLI for the Desk bridge. READ-ONLY toward INTENT-OS and Gmail: it reads exported JSON files and writes
// only NEW output files that you name. It refuses to overwrite an input, and refuses to replace any existing file
// unless you pass --overwrite. Private evidence is written to a 0600 file and never printed.
const fs = require('node:fs'), path = require('node:path');
const D = require('../dist/model.js'), W = require('../dist/intent-workspace.js');
const B = require('../engine/intent-bridge.cjs'), E = require('../engine/evidence-adapter.cjs'), R = require('../engine/resource-events.cjs'), C = require('../engine/core.cjs');

const USAGE = `desk-bridge <command> ...
  compare <old-workspace> <new-workspace>
  plan <desk> <workspace>
  apply <desk> <workspace> <choices.json> --out FILE --expected-revision N [--captured-at ISO] [--accept-roll-off] [--overwrite]
  preview <desk> <workspace> <case-id>                       (review preview only; never a writeback)
  verify-history <desk-before> <desk-after>
  link-decision <desk> <decision-id> <task-id[,task-id]> --out FILE --expected-revision N [--overwrite]
  evidence <approval> <extractions> --salt-file FILE --out-private FILE --out-public FILE [--desk F --workspace F --resource-log F] [--overwrite]
  resource-summary <log> [pins]   |   resource-verify <log> [pins]   |   resource-append <log> <event.json> --out FILE [--overwrite] [pins]      pins = --expect-head HASH --expect-events N`;
const fail = (code, msg, status = 2) => { const e = new Error(msg); e.cli = status; e.code = code; throw e; };
// Never echo file content in an error: a mis-pointed raw mail file must not leak a snippet through a JSON parse message.
const read = (p, max = 8_000_000) => { const st = fs.statSync(p); if (!st.isFile()) fail('NOT_A_FILE', p + ' is not a regular file'); if (st.size > max) fail('TOO_LARGE', p + ' is larger than ' + max + ' bytes'); const fd = fs.openSync(p, 'r'); let txt; try { const buf = Buffer.alloc(Math.min(st.size, max) + 1); const n = fs.readSync(fd, buf, 0, buf.length, 0); if (n > max) fail('TOO_LARGE', p + ' is larger than ' + max + ' bytes'); txt = buf.subarray(0, n).toString('utf8'); } finally { fs.closeSync(fd); } try { return JSON.parse(txt); } catch (e) { if (e instanceof SyntaxError) fail('INVALID_JSON', p + ' is not valid JSON (content not shown)'); throw e; } };
function flags(args) { const f = {}, pos = []; for (let i = 0; i < args.length; i++) { const a = args[i]; if (a === '--overwrite') f.overwrite = true; else if (a === '--accept-roll-off') f.acceptRollOff = true; else if (a === '--show-details') f.showDetails = true; else if (a.startsWith('--')) { if (args[i + 1] === undefined || args[i + 1].startsWith('--')) fail('USAGE', a + ' needs a value'); f[a.slice(2)] = args[++i]; if (f[a.slice(2)] === undefined) fail('USAGE', a + ' needs a value'); } else pos.push(a); } return { f, pos }; }
// Secrets are read as small regular files only (never a device or FIFO).
const readSecret = p => { const st = fs.statSync(p); if (!st.isFile()) fail('NOT_A_FILE', 'the salt file is not a regular file'); if (st.size > 4096) fail('TOO_LARGE', 'the salt file is larger than 4096 bytes'); return fs.readFileSync(p, 'utf8').trim(); };
const lexists = p => { try { fs.lstatSync(p); return true; } catch { return false; } };   // true for a dangling symlink too
const real = p => { try { return fs.realpathSync(p); } catch { return path.resolve(p); } };
// Writing is two steps so that several outputs can be staged first and published together: stage() writes a private temporary file next to the target
// (exclusive create, so it never follows a planted link); publish() makes it appear under its final name and always removes the temporary file.
function stage(out, data, inputs, f, mode = 0o600) {
  if (!out) fail('USAGE', 'an output file is required');
  if (inputs.some(i => real(i) === real(out))) fail('WOULD_OVERWRITE_INPUT', 'Refusing to write over an input file.');
  let st = null; try { st = fs.statSync(path.dirname(path.resolve(out))); } catch { /* reported below */ }
  if (!st || !st.isDirectory()) fail('NO_OUTPUT_DIR', 'the folder for an output file does not exist; nothing was written');
  const tmp = out + '.tmp-' + process.pid;
  fs.writeFileSync(tmp, typeof data === 'string' ? data : JSON.stringify(data, null, 2) + '\n', { mode, flag: 'wx' });
  return tmp;
}
function publish(out, tmp, f) {
  // Without --overwrite the final step is an atomic hard link, which fails if the name already exists, so two concurrent runs cannot both win.
  try { if (f.overwrite) fs.renameSync(tmp, out); else { try { fs.linkSync(tmp, out); } catch (e) { if (e.code === 'EEXIST') fail('EXISTS', out + ' already exists; choose a new name or pass --overwrite.'); throw e; } } }
  finally { fs.rmSync(tmp, { force: true }); }   // the temporary file never outlives the call, success or failure
}
function writeNew(out, data, inputs, f, mode = 0o600) { publish(out, stage(out, data, inputs, f, mode), f); }
// Several outputs: stage ALL first (a failure leaves every existing file untouched), then publish; if a later publish fails without --overwrite, undo the earlier ones.
function writeAll(items, inputs, f) {
  const staged = [];
  try { for (const it of items) staged.push({ ...it, tmp: stage(it.out, it.data, inputs, f, it.mode) }); }
  catch (e) { for (const s of staged) fs.rmSync(s.tmp, { force: true }); throw e; }
  const done = [];
  try { for (const s of staged) { publish(s.out, s.tmp, f); done.push(s.out); } }
  catch (e) { for (const s of staged) fs.rmSync(s.tmp, { force: true }); if (!f.overwrite) for (const o of done) fs.rmSync(o, { force: true }); throw e; }
}
const revision = f => { const n = /^\d{1,15}$/.test(String(f['expected-revision'])) ? Number(f['expected-revision']) : NaN; if (!Number.isSafeInteger(n)) fail('EXPECTED_REVISION_REQUIRED', '--expected-revision N is required (the Desk revision your choices were made against)'); return n; };
const capturedAt = f => { const v = f['captured-at'] || new Date().toISOString(); if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?Z$/.test(v) || !Number.isFinite(Date.parse(v))) fail('USAGE', '--captured-at must be an ISO-8601 UTC time like 2026-10-30T20:00:00.000Z'); return v; };
const out = o => console.log(JSON.stringify(o, null, 2));
const pinEvents = f => { const v = f['expect-events']; if (v === undefined) return undefined; if (!/^\d{1,15}$/.test(v)) fail('USAGE', '--expect-events must be a whole number'); return Number(v); };
const pins = f => ({ expect_head: f['expect-head'], expect_events: pinEvents(f) });

function main(argv) {
  const [cmd, ...rest] = argv, { f, pos } = flags(rest);
  switch (cmd) {
    case 'compare': return out(B.compareWorkspaces(W.validate(read(pos[0])), W.validate(read(pos[1]))));
    case 'plan': return out(B.planReconciliation(read(pos[0]), read(pos[1])));
    case 'apply': {
      const [deskP, wsP, chP] = pos, desk = read(deskP), ws = read(wsP), choices = read(chP), expected = revision(f);
      try {
        const r = B.applyReconciliation(desk, ws, null, choices, { expected_base_revision: expected, captured_at: capturedAt(f), accept_roll_off: f.acceptRollOff === true });
        if (r.changed) writeNew(f.out, r.desk, [deskP, wsP, chP], f);
        return out({ changed: r.changed, applied: r.applied, remaining_unresolved: r.remaining, wrote: r.changed ? f.out : null, history_prefix_preserved: r.changed ? r.history.dropped === 0 && C.verifyHistoryPrefix(desk, r.desk).ok : true, history_events_dropped: r.changed ? r.history.dropped : 0, source_written: false });
      } catch (e) {
        if (e.code === 'STALE_WRITE' && f.out) { let keep = f.out + '.preserved-choices.json'; for (let n = 2; lexists(keep) && n < 100; n++) keep = f.out + '.preserved-choices-' + n + '.json'; writeNew(keep, e.preserved.choices, [deskP, wsP, chP], { overwrite: false }); /* a second stale run keeps its own copy; STALE_WRITE (exit 3) is never masked */ e.message += ` Your choices were saved to ${keep}.`; e.cli = 3; }
        throw e;
      }
    }
    case 'preview': return out(B.roundTripPreview(read(pos[0]), read(pos[1]), pos[2]));
    case 'verify-history': { const v = C.verifyHistoryPrefix(read(pos[0]), read(pos[1])); out({ ...v, preserved: v.ok && !v.dropped }); if (!v.ok) process.exitCode = 2; return; }
    case 'link-decision': {
      const r = B.linkDecision(read(pos[0]), pos[1], (pos[2] || '').split(',').filter(Boolean), { expected_base_revision: revision(f), accept_roll_off: f.acceptRollOff === true });
      if (r.changed) writeNew(f.out, r.desk, [pos[0]], f); return out({ changed: r.changed, gate_id: r.gate_id, wrote: r.changed ? f.out : null, history_prefix_preserved: r.changed ? r.history.dropped === 0 : true, history_events_dropped: r.changed ? r.history.dropped : 0 });
    }
    case 'evidence': {
      const [apP, exP] = pos; if (!f['salt-file']) fail('SALT_REQUIRED', '--salt-file is required (a local secret; never commit it)');
      const salt = readSecret(f['salt-file']), approval = read(apP), records = read(exP);
      const ctx = { desk: f.desk ? D.validate(read(f.desk)) : null, ws: f.workspace ? W.validate(read(f.workspace)) : null, resourceLog: f['resource-log'] ? read(f['resource-log']) : null, today: new Date().toISOString().slice(0, 10) };
      const r = E.run(approval, records, ctx, salt), inputs = [apP, exP, f['salt-file'], f.desk, f.workspace, f['resource-log']].filter(Boolean);
      for (const o of [f['out-private'], f['out-public']]) if (o && inputs.some(i => real(i) === real(o))) fail('WOULD_OVERWRITE_INPUT', 'Refusing to write over an input file. Nothing was written.');
      if (!f['out-private'] || !f['out-public']) fail('USAGE', '--out-private and --out-public are both required');
      if (real(f['out-private'] || '') === real(f['out-public'] || '')) fail('USAGE', '--out-private and --out-public must be different files');
      for (const o of [f['out-private'], f['out-public']]) if (o && lexists(o) && !f.overwrite) fail('EXISTS', o + ' already exists; nothing was written.');
      writeAll([{ out: f['out-private'], data: r.private, mode: 0o600 }, { out: f['out-public'], data: r.public, mode: 0o644 }], inputs, f);   // both staged first; no orphan or half-replaced pair
      return out({ processed: r.public.processed, rejected: r.public.rejected_out_of_scope_or_invalid.length, proposals_by_kind: r.public.proposals_by_kind, private_file: f['out-private'], public_file: f['out-public'], private_content_printed: false });
    }
    case 'resource-summary': return out(R.summarize(read(pos[0]), pins(f)));
    case 'resource-verify': { const v = R.verifyLog(read(pos[0]), pins(f)); out(v); if (!v.ok) process.exitCode = 2; return; }
    case 'resource-append': { const log = read(pos[0]), r = R.appendEvent(log, read(pos[1]), pins(f)); if (r.changed) writeNew(f.out, r.log, [pos[0], pos[1]], f, 0o600); return out({ changed: r.changed, event_id: r.event_id, wrote: r.changed ? f.out : null }); }
    default: fail('USAGE', USAGE);
  }
}
try { main(process.argv.slice(2)); }
catch (e) {
  // Messages written by this tool are fixed text. Anything else (for example a validator quoting a bad value) could echo input, so it is hidden unless you pass --show-details.
  const ours = e.cli !== undefined || e instanceof C.BridgeError, shown = e.syscall ? 'a file system error occurred (' + e.code + ')' : ours || process.argv.includes('--show-details') ? String(e.message).split('\n')[0].slice(0, 400) : 'the input failed validation (details hidden so no file content is echoed; use --show-details to see them)';
  console.error(`${e.code || 'ERROR'}: ${shown}`); process.exitCode = e.cli || (e.code === 'STALE_WRITE' ? 3 : 2); }

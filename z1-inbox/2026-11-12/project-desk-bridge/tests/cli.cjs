'use strict';
// CLI behaviour on SYNTHETIC files in a temp directory. Verifies inputs are never modified and private content is never printed.
const assert = require('node:assert/strict'), fs = require('node:fs'), os = require('node:os'), path = require('node:path'), cp = require('node:child_process'), crypto = require('node:crypto');
const { test, begin, finish } = require('./harness.cjs');
const F = require('../fixtures/synthetic.cjs'), C = require('../engine/core.cjs'), D = require('../dist/model.js');
begin('cli');

const CLI = path.join(__dirname, '../bin/desk-bridge.cjs'), dir = fs.mkdtempSync(path.join(os.tmpdir(), 'desk-bridge-cli-'));
process.on('exit', () => fs.rmSync(dir, { recursive: true, force: true }));
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const put = (n, o) => { const p = path.join(dir, n); fs.writeFileSync(p, typeof o === 'string' ? o : JSON.stringify(o)); return p; };
const run = (...a) => { const r = cp.spawnSync('node', [CLI, ...a], { encoding: 'utf8', cwd: dir }); return { code: r.status, out: r.stdout, err: r.stderr }; };
const ws119 = F.ws119(), ws193 = F.ws193(), desk = F.deskWithUserEdits();
const deskP = put('desk.json', desk), wsP = put('ws193.json', ws193), ws119P = put('ws119.json', ws119);
const plan = JSON.parse(run('plan', deskP, wsP).out);
const choices = plan.proposals.map(p => ({ id: p.id, choice: p.kind.startsWith('CONFLICT') ? 'KEEP_DESK' : p.choices.includes('ADOPT') ? 'ADOPT' : 'RECORD_ONLY' }));
const chP = put('choices.json', choices), inputs = [deskP, wsP, ws119P, chP], before = () => inputs.map(sha);

test('plan prints the same plan the engine computes and modifies nothing', () => {
  const h = before(), r = run('plan', deskP, wsP); assert.equal(r.code, 0); assert.equal(JSON.parse(r.out).digest, require('../engine/intent-bridge.cjs').planReconciliation(desk, ws193).digest); assert.deepEqual(before(), h);
});
test('compare prints the two historical facts for the stable source task id', () => {
  const r = run('compare', ws119P, wsP), c = JSON.parse(r.out).changes.find(x => x.task_id === 'task-special-circ'); assert.equal(r.code, 0); assert.deepEqual([c.before, c.after], ['BLOCKED', 'OPTIONAL']);
});
test('apply writes ONE new file, leaves every input byte-identical, and reports no source write', () => {
  const h = before(), outP = path.join(dir, 'desk.reconciled.json'), r = run('apply', deskP, wsP, chP, '--out', outP, '--expected-revision', String(desk.revision), '--captured-at', '2026-10-30T00:00:00.000Z');
  assert.equal(r.code, 0, r.err); const j = JSON.parse(r.out); assert.equal(j.changed, true); assert.equal(j.source_written, false); assert.equal(j.history_prefix_preserved, true); assert.deepEqual(before(), h);
  assert.equal(fs.statSync(outP).mode & 0o777, 0o600); assert.doesNotThrow(() => D.validate(JSON.parse(fs.readFileSync(outP, 'utf8'))));
  assert.equal(run('verify-history', deskP, outP).code, 0);
});
test('apply refuses to write over an input file or an existing file', () => {
  const h = before(); let r = run('apply', deskP, wsP, chP, '--out', deskP, '--expected-revision', String(desk.revision)); assert.equal(r.code, 2); assert.match(r.err, /WOULD_OVERWRITE_INPUT/);
  r = run('apply', deskP, wsP, chP, '--out', path.join(dir, 'desk.reconciled.json'), '--expected-revision', String(desk.revision)); assert.equal(r.code, 2); assert.match(r.err, /EXISTS/); assert.deepEqual(before(), h);
});
test('apply without --expected-revision is refused', () => { const r = run('apply', deskP, wsP, chP, '--out', path.join(dir, 'x.json')); assert.equal(r.code, 2); assert.match(r.err, /EXPECTED_REVISION_REQUIRED/); assert(!fs.existsSync(path.join(dir, 'x.json'))); });
test('a stale write exits 3, writes nothing to the Desk, and saves the typed choices to a file', () => {
  const outP = path.join(dir, 'stale.json'), r = run('apply', deskP, wsP, chP, '--out', outP, '--expected-revision', String(desk.revision - 1));
  assert.equal(r.code, 3); assert.match(r.err, /STALE_WRITE/); assert(!fs.existsSync(outP)); assert.deepEqual(JSON.parse(fs.readFileSync(outP + '.preserved-choices.json', 'utf8')), choices);
});
test('history verification fails when an old event was altered', () => {
  const after = JSON.parse(fs.readFileSync(path.join(dir, 'desk.reconciled.json'), 'utf8')); after.events[0].text = 'rewritten'; const bad = put('tampered.json', after); const r = run('verify-history', deskP, bad); assert.equal(r.code, 2);
});
test('preview is refused before reconciliation and is review-only afterwards', () => {
  assert.match(run('preview', deskP, wsP, 'case-synth-fellowship').err, /NOT_RECONCILED/);
  const r = run('preview', path.join(dir, 'desk.reconciled.json'), wsP, 'case-synth-fellowship'); assert.equal(r.code, 0); const j = JSON.parse(r.out); assert.equal(j.writeback, false); assert.equal(j.preview_only, true);
});
test('link-decision creates a gate in a NEW file and refuses a stale revision', () => {
  const sd = put('seed.json', D.seed()), h = sha(sd), o = path.join(dir, 'seed.gated.json');
  assert.equal(run('link-decision', sd, 'scope', 'offer', '--out', o, '--expected-revision', '0').code, 0); assert.equal(sha(sd), h); assert(JSON.parse(fs.readFileSync(o, 'utf8')).tasks.some(t => t.id === 'gate-scope'));
  assert.equal(run('link-decision', sd, 'scope', 'offer', '--out', path.join(dir, 'z.json'), '--expected-revision', '9').code, 3);
});

// ---------- evidence ----------
const CANARY = 'CANARY_CLI_55d1e0';
const approval = put('approval.json', { schema: 'humanaios.gmail-evidence.approval.v1', approved_by: 'HUMAN', account_alias: 'primary', scopes: [{ thread_id: 'a1b2c3d4e5f60718', message_ids: ['0123456789abcdef'], purposes: ['CORROBORATE_CASE_STATUS', 'PROPOSE_TASK'] }] });
const ex = put('extractions.json', [{ schema: 'humanaios.gmail-evidence.extraction.v1', message_id: '0123456789abcdef', thread_id: 'a1b2c3d4e5f60718', header_date: '2026-10-15', sender_domain: 'canary-cli.example', claim_type: 'SENDER_ASSERTION', extraction_by: 'ASSISTANT_CURATED', case_ref: { case_id: 'case-synth-fellowship', task_id: null }, assertions: [{ kind: 'AWARD_NOTICE' }], private_summary: 'SYNTHETIC ' + CANARY }]);
const salt = put('salt.txt', 'cli-test-only-salt-0123456789\n');
test('evidence writes a 0600 private file and a clean public file, and prints no private content', () => {
  const op = path.join(dir, 'ev.private.json'), pu = path.join(dir, 'ev.public.json'), h = [approval, ex, salt].map(sha);
  const r = run('evidence', approval, ex, '--salt-file', salt, '--out-private', op, '--out-public', pu, '--desk', path.join(dir, 'desk.reconciled.json'), '--workspace', wsP);
  assert.equal(r.code, 0, r.err); assert(!r.out.includes(CANARY) && !r.err.includes(CANARY)); assert.equal(fs.statSync(op).mode & 0o777, 0o600); assert(fs.readFileSync(op, 'utf8').includes(CANARY));
  const pub = fs.readFileSync(pu, 'utf8'); for (const s of [CANARY, 'canary-cli', '0123456789abcdef', 'a1b2c3d4e5f60718', 'case-synth']) assert(!pub.includes(s), 'public file contains ' + s);
  assert.deepEqual([approval, ex, salt].map(sha), h); assert.equal(JSON.parse(r.out).private_content_printed, false);
});
test('evidence requires a salt file of adequate length and never overwrites an existing output', () => {
  const op = path.join(dir, 'e2.private.json'), pu = path.join(dir, 'e2.public.json');
  assert.match(run('evidence', approval, ex, '--out-private', op, '--out-public', pu).err, /SALT_REQUIRED/);
  assert.match(run('evidence', approval, ex, '--salt-file', put('short.txt', 'short'), '--out-private', op, '--out-public', pu).err, /SALT_REQUIRED/);
  assert.match(run('evidence', approval, ex, '--salt-file', salt, '--out-private', path.join(dir, 'ev.private.json'), '--out-public', pu).err, /EXISTS/);
});
test('an out-of-scope message is counted as rejected and produces no private record', () => {
  const x = JSON.parse(fs.readFileSync(ex, 'utf8')); x[0].message_id = '9999999999999999'; const exo = put('ex-out.json', x), op = path.join(dir, 'o.private.json'), pu = path.join(dir, 'o.public.json');
  const r = run('evidence', approval, exo, '--salt-file', salt, '--out-private', op, '--out-public', pu); assert.equal(r.code, 0); assert.equal(JSON.parse(r.out).processed, 0); assert.equal(JSON.parse(r.out).rejected, 1); assert.deepEqual(JSON.parse(fs.readFileSync(op, 'utf8')).proposals, []);
});

// ---------- resources ----------
test('resource-append refuses a violating event and leaves the log file unchanged; a valid one goes to a new file', () => {
  const R = require('../engine/resource-events.cjs'), log = R.newLog({ USD: { dimension: 'capital' } }), lp = put('log.json', log), h = sha(lp);
  const grant = { kind: 'ACQUIRED', resource_id: 'res-azure', occurred_on: '2026-10-01', recorded_by: 'n', grant_id: 'g1', unit: 'USD', quantity: 10, evidence: [{ type: 'ACCEPTANCE_NOTICE', ref: 'a1', claim_type: 'CLAIM' }] };
  const o1 = path.join(dir, 'log2.json'); assert.equal(run('resource-append', lp, put('g.json', grant), '--out', o1).code, 0); assert.equal(sha(lp), h);
  const over = { kind: 'USED', resource_id: 'res-azure', occurred_on: '2026-10-02', recorded_by: 'n', use_id: 'u1', unit: 'USD', quantity: 11, grant_id: 'g1', evidence: [{ type: 'MEASUREMENT', ref: 'm1', claim_type: 'MEASUREMENT' }] };
  const o2 = path.join(dir, 'log3.json'), r = run('resource-append', o1, put('o.json', over), '--out', o2); assert.equal(r.code, 2); assert.match(r.err, /LEDGER_VIOLATION/); assert(!fs.existsSync(o2));
  assert.equal(run('resource-verify', o1).code, 0); assert.equal(JSON.parse(run('resource-summary', o1).out).resources['res-azure'].grants.g1.remaining_computed, 10);
});
test('usage errors exit 2', () => { assert.equal(run().code, 2); assert.equal(run('nope').code, 2); assert.equal(run('plan').code, 2); });
test('the CLI uses no network module', () => { const s = fs.readFileSync(CLI, 'utf8'); assert(!/require\((['"])(node:)?(net|http|https|http2|dgram|tls|dns)\1\)/.test(s)); assert(!/\bfetch\s*\(/.test(s)); });

test('resource-verify with --expect-head / --expect-events detects a truncated log; resource-summary refuses a tampered log', () => {
  const R = require('../engine/resource-events.cjs'), g = { kind: 'ACQUIRED', resource_id: 'res-azure', occurred_on: '2026-10-01', recorded_by: 'n', grant_id: 'g1', unit: 'USD', quantity: 10, evidence: [{ type: 'ACCEPTANCE_NOTICE', ref: 'a1', claim_type: 'CLAIM' }] };
  let l = R.appendEvent(R.newLog({ USD: { dimension: 'capital' } }), g).log; const pin = R.verifyLog(l), lp = put('pinned.json', l);
  assert.equal(run('resource-verify', lp, '--expect-head', pin.head, '--expect-events', '1').code, 0);
  const cut = JSON.parse(JSON.stringify(l)); cut.events = []; const cp = put('cut.json', cut);
  assert.equal(run('resource-verify', cp, '--expect-events', '1').code, 2);
  const bad = JSON.parse(JSON.stringify(l)); bad.events[0].event.quantity = 999; const r = run('resource-summary', put('bad.json', bad)); assert.equal(r.code, 2); assert.match(r.err, /LOG_INTEGRITY/);
});

// ---------- audit-2 repairs ----------
test('a mis-pointed raw mail file never leaks a snippet through an error message', () => {
  const raw = put('raw.eml', 'From: bob@canary-leak.example\nSubject: CANARY_SUBJECT\n\nbody');
  for (const args of [['plan', raw, raw], ['compare', raw, raw], ['evidence', approval, raw, '--salt-file', salt, '--out-private', path.join(dir, 'l1'), '--out-public', path.join(dir, 'l2')], ['evidence', raw, ex, '--salt-file', salt, '--out-private', path.join(dir, 'l3'), '--out-public', path.join(dir, 'l4')]]) {
    const r = run(...args); assert.equal(r.code, 2); assert.match(r.err, /INVALID_JSON/); for (const s of ['canary-leak', 'CANARY_SUBJECT', 'bob@', 'From:']) assert(!r.err.includes(s) && !r.out.includes(s), 'leaked ' + s);
  }
});
test('two concurrent runs writing the same new output: exactly one wins and the other is refused', () => {
  const outP = path.join(dir, 'race.json'), cmd = ['node', CLI, 'link-decision', put('s2.json', D.seed()), 'scope', 'offer', '--out', outP, '--expected-revision', '0'];
  const kids = [0, 1, 2, 3].map(() => cp.spawn(cmd[0], cmd.slice(1), { cwd: dir, stdio: 'ignore' })), codes = [];
  return new Promise(res => { let n = 0; for (const k of kids) k.on('exit', c => { codes.push(c); if (++n === kids.length) { assert.equal(codes.filter(c => c === 0).length, 1, 'codes ' + codes); assert(codes.every(c => c === 0 || c === 2)); res(); } }); });
});
test('apply reports dropped history and refuses a roll-off unless --accept-roll-off is given', () => {
  const big = JSON.parse(JSON.stringify(desk)); while (big.events.length < 5000) D.event(big, 'padding ' + big.events.length); const bp = put('big.json', D.validate(big));
  const o = path.join(dir, 'big.out.json'), a = ['apply', bp, wsP, chP, '--out', o, '--expected-revision', String(big.revision)];
  let r = run(...a); assert.equal(r.code, 2); assert.match(r.err, /HISTORY_WOULD_ROLL_OFF/); assert(!fs.existsSync(o));
  r = run(...a, '--accept-roll-off'); assert.equal(r.code, 0, r.err); const j = JSON.parse(r.out); assert.equal(j.history_prefix_preserved, false); assert(j.history_events_dropped > 0);
});

// ---------- audit-3 repairs ----------
test('JSON values from a mis-pointed file are never echoed by any error (event kind, field name, unit, choice id, validator text)', () => {
  const R = require('../engine/resource-events.cjs'), lp = put('lg.json', R.newLog({ USD: { dimension: 'capital' } }));
  const base = { kind: 'ACQUIRED', resource_id: 'res-a', occurred_on: '2026-10-01', recorded_by: 'n', grant_id: 'g1', unit: 'USD', quantity: 1, evidence: [{ type: 'ACCEPTANCE_NOTICE', ref: 'a1', claim_type: 'CLAIM' }] };
  for (const bad of [{ ...base, kind: 'SECRETKIND_1Z999' }, { ...base, SECRETFIELD_1Z999: 1 }, { ...base, unit: 'SECRETUNIT1Z999' }]) { const r = run('resource-append', lp, put('b.json', bad), '--out', path.join(dir, 'never.json')); assert.equal(r.code, 2); assert(!/1Z999/.test(r.err + r.out), r.err); }
  const r2 = run('apply', deskP, wsP, put('ch.json', [{ id: 'SECRETID_1Z999', choice: 'ADOPT' }]), '--out', path.join(dir, 'never2.json'), '--expected-revision', String(desk.revision)); assert.equal(r2.code, 2); assert(!/1Z999/.test(r2.err));
  const r3 = run('plan', put('bad-desk.json', { not: 'a desk SECRETVALUE_1Z999' }), wsP); assert.equal(r3.code, 2); assert(!/1Z999/.test(r3.err), r3.err);
});
test('only regular files are read: a directory is refused without reading', () => { const r = run('plan', dir, wsP); assert.equal(r.code, 2); assert.match(r.err, /NOT_A_FILE/); });
test('link-decision on a capped Desk is refused unless --accept-roll-off, and then reports the dropped events', () => {
  const big = D.seed(); while (big.events.length < 5000) D.event(big, 'padding ' + big.events.length); const bp = put('cap.json', D.validate(big));
  let r = run('link-decision', bp, 'scope', 'offer', '--out', path.join(dir, 'cap.out.json'), '--expected-revision', '0'); assert.equal(r.code, 2); assert.match(r.err, /HISTORY_WOULD_ROLL_OFF/);
  r = run('link-decision', bp, 'scope', 'offer', '--out', path.join(dir, 'cap.out.json'), '--expected-revision', '0', '--accept-roll-off'); assert.equal(r.code, 0, r.err); const j = JSON.parse(r.out); assert.equal(j.history_prefix_preserved, false); assert(j.history_events_dropped > 0);
});
test('evidence refuses identical private/public outputs and writes nothing when either already exists', () => {
  const same = path.join(dir, 'same.json'); assert.match(run('evidence', approval, ex, '--salt-file', salt, '--out-private', same, '--out-public', same).err, /USAGE/); assert(!fs.existsSync(same));
  const pu = path.join(dir, 'exists.public.json'); fs.writeFileSync(pu, '{}'); const op = path.join(dir, 'exists.private.json');
  assert.match(run('evidence', approval, ex, '--salt-file', salt, '--out-private', op, '--out-public', pu).err, /EXISTS/); assert(!fs.existsSync(op), 'no partial private file');
});

// ---------- audit-4 repairs ----------
test('validator text is hidden by default and shown only with --show-details', () => {
  const bad = put('xdesk.json', { ...desk, EXTRA_FIELD: 1 });
  let r = run('plan', bad, wsP); assert.equal(r.code, 2); assert.match(r.err, /details hidden/); assert(!/Unexpected fields/.test(r.err));
  r = run('plan', bad, wsP, '--show-details'); assert.equal(r.code, 2); assert.match(r.err, /Unexpected fields/);
});
test('the salt file must be a small regular file; a failing evidence run leaves no orphan output', () => {
  const op = path.join(dir, 'n7.private.json'), pu = path.join(dir, 'n7.public.json');
  assert.match(run('evidence', approval, ex, '--salt-file', dir, '--out-private', op, '--out-public', pu).err, /NOT_A_FILE/);
  const big = put('bigsalt.txt', 'x'.repeat(5000)); assert.match(run('evidence', approval, ex, '--salt-file', big, '--out-private', op, '--out-public', pu).err, /TOO_LARGE/);
  const o8 = path.join(dir, 'n8.private.json'); const r = run('evidence', approval, ex, '--salt-file', salt, '--out-private', o8, '--out-public', ex, '--overwrite');
  assert.equal(r.code, 2); assert.match(r.err, /WOULD_OVERWRITE_INPUT/); assert(!fs.existsSync(o8), 'no orphan private file');
});
test('--expected-revision and --captured-at are parsed strictly', () => {
  const o = path.join(dir, 'strict.json');
  for (const v of ['', '0x3', '+3', '3.0', '1e2', '-1']) assert.match(run('apply', deskP, wsP, chP, '--out', o, '--expected-revision', v).err, /EXPECTED_REVISION_REQUIRED/);
  assert.match(run('apply', deskP, wsP, chP, '--out', o, '--expected-revision', String(desk.revision), '--captured-at', 'not a date').err, /USAGE/); assert(!fs.existsSync(o));
});

// ---------- audit-5 repairs ----------
test('--captured-at must be a real time; --expect-events a whole number; a flag cannot swallow another flag; inputs over the size limit are refused', () => {
  const o = path.join(dir, 'cap5.json'), args = ['apply', deskP, wsP, chP, '--out', o, '--expected-revision', String(desk.revision)];
  assert.match(run(...args, '--captured-at', '2026-13-45T99:99:99Z').err, /USAGE/); assert(!fs.existsSync(o));
  assert.match(run('resource-verify', put('lg5.json', require('../engine/resource-events.cjs').newLog({})), '--expect-events', '0x1').err, /USAGE/);
  assert.match(run('apply', deskP, wsP, chP, '--out', '--overwrite', '--expected-revision', '5').err, /USAGE/);
  const huge = path.join(dir, 'huge.json'); fs.writeFileSync(huge, ' '.repeat(8_000_001)); assert.match(run('plan', huge, wsP).err, /TOO_LARGE/);
});
test('evidence needs both outputs up front, leaves no orphan private file, and treats a dangling symlink as existing', () => {
  const op = path.join(dir, 'm3.private.json'); assert.match(run('evidence', approval, ex, '--salt-file', salt, '--out-private', op).err, /USAGE/); assert(!fs.existsSync(op));
  const pu = path.join(dir, 'm3.public.json'); fs.symlinkSync(path.join(dir, 'nowhere.json'), pu); const op2 = path.join(dir, 'm3b.private.json');
  assert.match(run('evidence', approval, ex, '--salt-file', salt, '--out-private', op2, '--out-public', pu).err, /EXISTS/); assert(!fs.existsSync(op2)); assert(!fs.existsSync(path.join(dir, 'nowhere.json')));
});
test('a failed overwrite leaves no temporary file behind', () => {
  const d2 = path.join(dir, 'outdir'); fs.mkdirSync(d2); fs.writeFileSync(path.join(d2, 'keep'), 'x');
  const r = run('link-decision', put('s5.json', D.seed()), 'scope', 'offer', '--out', d2, '--expected-revision', '0', '--overwrite'); assert.equal(r.code, 2);
  assert.deepEqual(fs.readdirSync(dir).filter(n => n.startsWith('outdir.tmp-')), []);
});

// ---------- audit-6 repairs ----------
test('evidence --overwrite is all-or-nothing: a failing public path leaves BOTH existing outputs untouched, with a clear message', () => {
  const op = path.join(dir, 'ow.private.json'), pu = path.join(dir, 'ow.public.json'), base = ['evidence', approval, ex, '--salt-file', salt, '--out-private', op];
  assert.equal(run(...base, '--out-public', pu).code, 0); const h = [op, pu].map(sha);
  const r = run(...base, '--out-public', path.join(dir, 'no-such-folder', 'pub.json'), '--overwrite'); assert.equal(r.code, 2); assert.match(r.err, /NO_OUTPUT_DIR/); assert(!/input failed validation/.test(r.err));
  assert.deepEqual([op, pu].map(sha), h, 'existing outputs unchanged'); assert.deepEqual(fs.readdirSync(dir).filter(n => n.includes('.tmp-')), []);
  assert.equal(run(...base, '--out-public', pu, '--overwrite').code, 0);   // and a good run still replaces both
});
test('a second stale apply to the same --out still exits 3 (STALE_WRITE) and keeps its own copy of the typed choices', () => {
  const o = path.join(dir, 'st2.json'), a = ['apply', deskP, wsP, chP, '--out', o, '--expected-revision', '99'];
  const r1 = run(...a), r2 = run(...a); assert.equal(r1.code, 3); assert.equal(r2.code, 3); assert.match(r2.err, /STALE_WRITE/);
  assert(fs.existsSync(o + '.preserved-choices.json') && fs.existsSync(o + '.preserved-choices-2.json'));
});
test('a missing input file is a clear file-system message, not "input failed validation", and shows no content', () => { const r = run('plan', path.join(dir, 'does-not-exist.json'), wsP); assert.equal(r.code, 2); assert.match(r.err, /file system error occurred \(ENOENT\)/); assert(!/failed validation/.test(r.err)); });
finish();

'use strict';
// RESOURCE GRAPH: discovery / acquisition / payment / charge / settlement / use / remaining / yield / waste / benefit.
// SYNTHETIC amounts and ids only.
const assert = require('node:assert/strict');
const { test, begin, finish } = require('./harness.cjs');
const R = require('../engine/resource-events.cjs'), C = require('../engine/core.cjs');
begin('resource-events');

const LOCAL = { USD: { dimension: 'capital' }, 'gpu-hr': { dimension: 'compute' }, 'evidence-item': { dimension: 'evidence' } };
const ev = (type, ref, claim_type) => ({ type, ref, claim_type: claim_type || (type === 'RECEIPT' || type === 'INVOICE' ? 'TRANSACTION_PROOF' : type === 'MEASUREMENT' ? 'MEASUREMENT' : 'CLAIM') });
const base = { resource_id: 'res-azure', occurred_on: '2026-10-01', recorded_by: 'night-label' };
const mk = (kind, f, evidence) => ({ ...base, kind, ...f, evidence: evidence || [] });
const grant = (id = 'g1', q = 100, unit = 'USD') => mk('ACQUIRED', { grant_id: id, unit, quantity: q }, [ev('ACCEPTANCE_NOTICE', 'notice-1')]);
const charge = (id = 'c1', q = 40, unit = 'USD') => mk('CHARGE', { charge_id: id, unit, quantity: q }, [ev('INVOICE', 'inv-' + id)]);
const settle = (c, f, id, q, unit = 'USD') => mk('SETTLEMENT', { charge_id: c, funding: f, funding_id: id, unit, quantity: q }, [ev('PROVIDER_STATEMENT', 'stmt-' + c + id + q)]);
const payment = (id = 'p1', q = 30, ref = 'rcpt-1') => mk('PAYMENT', { payment_id: id, unit: 'USD', quantity: q }, [ev('RECEIPT', ref)]);
const add = (log, e) => R.appendEvent(log, e).log;
const code = (fn, c) => { try { fn(); } catch (e) { assert.equal(e.code, c, `want ${c}, got ${e.code}: ${e.message}`); return e; } assert.fail('expected ' + c); };
const empty = () => R.newLog(LOCAL), sum = l => R.summarize(l), res = l => sum(l).resources['res-azure'];

// ---------- units: reuse the ratified registry; never convert ----------
test('registered units come from the pinned ratified registry; local candidates must be declared', () => {
  const l = empty(); assert.equal(l.unit_registry.status, 'RATIFIED'); assert.match(l.unit_registry.source_sha256, /^[0-9a-f]{64}$/);
  const used = mk('USED', { use_id: 'u1', unit: 'Z1-ktok', quantity: 3 }, [ev('MEASUREMENT', 'm1')]); assert.doesNotThrow(() => add(l, used));
  code(() => add(l, mk('USED', { use_id: 'u2', unit: 'mystery-unit', quantity: 1 }, [ev('MEASUREMENT', 'm2')])), 'UNKNOWN_UNIT');
});
test('a registered unit cannot be redefined and a local unit needs a registry dimension', () => {
  code(() => R.newLog({ 'Z1-ktok': { dimension: 'compute' } }), 'UNIT_REDEFINED'); code(() => R.newLog({ foo: { dimension: 'money' } }), 'INVALID_UNIT'); code(() => R.newLog({ foo: { dimension: 'capital', extra: 1 } }), 'INVALID_UNIT');
});
test('a settlement in one unit cannot draw on a grant in another: no implicit conversion', () => {
  let l = add(add(empty(), grant('g1', 100, 'USD')), charge('c1', 40, 'USD'));
  code(() => add(l, settle('c1', 'GRANT', 'g1', 10, 'gpu-hr')), 'LEDGER_VIOLATION');
  l = add(l, mk('ACQUIRED', { grant_id: 'g2', unit: 'gpu-hr', quantity: 50 }, [ev('ACCEPTANCE_NOTICE', 'n2')])); const e = code(() => add(l, settle('c1', 'GRANT', 'g2', 10)), 'LEDGER_VIOLATION'); assert(e.violations.some(v => v.code === 'UNIT_MISMATCH'));
});
test('reports keep each unit separate and never add across units', () => {
  let l = add(add(empty(), grant('g1', 100, 'USD')), mk('ACQUIRED', { grant_id: 'g2', unit: 'gpu-hr', quantity: 50 }, [ev('ACCEPTANCE_NOTICE', 'n2')]));
  const u = res(l).units; assert.equal(u.USD.granted, 100); assert.equal(u['gpu-hr'].granted, 50); assert.equal(Object.keys(u).length, 2);
});

// ---------- distinct events and evidence gating ----------
test('discovery creates no capacity and takes no quantity', () => {
  const l = add(empty(), mk('DISCOVERED', {}, [])); assert.equal(res(l).discovered, true); assert.deepEqual(res(l).grants, {});
  code(() => add(empty(), mk('DISCOVERED', { unit: 'USD', quantity: 5 }, [])), 'UNEXPECTED_FIELD');
});
test('a payment is a transaction, not a grant, not remaining capacity and not a benefit', () => {
  const l = add(empty(), payment()); assert.deepEqual(res(l).grants, {}); assert.equal(res(l).payments.p1.proves, 'TRANSACTION_ONLY'); assert.equal(res(l).benefits.length, 0);
});
test('a receipt or invoice can never back a BENEFIT, nor can transaction proof', () => {
  const b = (evidence) => mk('BENEFIT_OBSERVED', { benefit_id: 'b1', statement: 'Ran one real pilot on the credits' }, evidence);
  code(() => add(empty(), b([ev('RECEIPT', 'r1')])), 'BENEFIT_BACKED_BY_TRANSACTION'); code(() => add(empty(), b([ev('INVOICE', 'i1')])), 'BENEFIT_BACKED_BY_TRANSACTION');
  code(() => add(empty(), b([ev('PROVIDER_STATEMENT', 's1')])), 'BENEFIT_BACKED_BY_TRANSACTION'); code(() => add(empty(), b([ev('HUMAN_ASSERTION', 'h1', 'TRANSACTION_PROOF')])), 'BENEFIT_BACKED_BY_TRANSACTION');
  code(() => add(empty(), b([ev('RECEIPT', 'r2', 'CLAIM')])), 'BENEFIT_BACKED_BY_TRANSACTION'); code(() => add(empty(), b([ev('INVOICE', 'i2', 'CLAIM')])), 'BENEFIT_BACKED_BY_TRANSACTION');   // relabelling a receipt does not turn it into an outcome
  code(() => add(empty(), b([ev('ACCEPTANCE_NOTICE', 'a1')])), 'BENEFIT_BACKED_BY_TRANSACTION');
  code(() => add(empty(), b([])), 'EVIDENCE_REQUIRED');
});
test('a benefit needs outcome evidence and is labelled ASSERTED_ONLY unless a third party confirmed it', () => {
  let l = add(empty(), mk('BENEFIT_OBSERVED', { benefit_id: 'b1', statement: 'One pilot ran' }, [ev('OUTCOME_RECORD', 'o1')])); assert.equal(res(l).benefits[0].basis, 'ASSERTED_ONLY');
  l = add(l, mk('BENEFIT_OBSERVED', { benefit_id: 'b2', statement: 'Funder confirmed use' }, [ev('THIRD_PARTY_CONFIRMATION', 't1')])); assert.equal(res(l).benefits[1].basis, 'THIRD_PARTY_CONFIRMED');
});
test('spending money never creates or changes a benefit', () => {
  let l = add(add(add(empty(), grant()), charge()), settle('c1', 'GRANT', 'g1', 40)); assert.equal(res(l).benefits.length, 0); assert.equal(res(l).units.USD.settled, 40);
});
test('acquisition needs acceptance or provider evidence, not a receipt; payment needs a receipt-class document', () => {
  code(() => add(empty(), mk('ACQUIRED', { grant_id: 'g', unit: 'USD', quantity: 5 }, [ev('RECEIPT', 'r')])), 'EVIDENCE_TYPE_NOT_ALLOWED');
  code(() => add(empty(), mk('PAYMENT', { payment_id: 'p', unit: 'USD', quantity: 5 }, [ev('HUMAN_ASSERTION', 'h')])), 'EVIDENCE_TYPE_NOT_ALLOWED');
  code(() => add(empty(), mk('PAYMENT', { payment_id: 'p', unit: 'USD', quantity: 5 }, [ev('RECEIPT', 'r', 'MEASUREMENT')])), 'INVALID_EVIDENCE');
});

// ---------- never double count ----------
test('a credit drawdown is counted once: grant 100, charge 40, settlement 40 leaves 60', () => {
  const l = add(add(add(empty(), grant()), charge()), settle('c1', 'GRANT', 'g1', 40)), g = res(l).grants.g1;
  assert.equal(g.drawn_by_settlement, 40); assert.equal(g.remaining_computed, 60); assert.equal(res(l).charges.c1.outstanding, 0);
});
test('re-appending an identical event is an idempotent no-op, not a second count', () => {
  let l = add(add(add(empty(), grant()), charge()), settle('c1', 'GRANT', 'g1', 40)); const again = R.appendEvent(l, settle('c1', 'GRANT', 'g1', 40));
  assert.equal(again.changed, false); assert.equal(again.log.events.length, l.events.length); assert.equal(res(again.log).grants.g1.remaining_computed, 60);
});
test('a charge cannot be settled beyond its amount, even from two funding sources', () => {
  let l = add(add(add(add(empty(), grant()), payment('p1', 30)), charge('c1', 40)), settle('c1', 'GRANT', 'g1', 25));
  code(() => add(l, settle('c1', 'PAYMENT', 'p1', 20)), 'LEDGER_VIOLATION');
  l = add(l, settle('c1', 'PAYMENT', 'p1', 15)); assert.equal(res(l).charges.c1.outstanding, 0); assert.equal(res(l).payments.p1.unapplied, 15);
});
test('a grant cannot be drawn below zero and a payment cannot be applied beyond what was paid', () => {
  let l = add(add(add(empty(), grant('g1', 50)), charge('c1', 80)), settle('c1', 'GRANT', 'g1', 50)); const e = code(() => add(l, settle('c1', 'GRANT', 'g1', 1)), 'LEDGER_VIOLATION'); assert(e.violations.some(v => v.code === 'OVERDRAWN_GRANT'));
  l = add(add(l, payment('p1', 10)), charge('c2', 50)); code(() => add(l, settle('c2', 'PAYMENT', 'p1', 11)), 'LEDGER_VIOLATION');
});
test('the same receipt cannot back two payments (duplicate transaction proof)', () => {
  const l = add(empty(), payment('p1', 30, 'rcpt-X')); const e = code(() => add(l, payment('p2', 30, 'rcpt-X')), 'LEDGER_VIOLATION'); assert(e.violations.some(v => v.code === 'DUPLICATE_TRANSACTION_REF'));
});
test('reusing an id with different content is refused, not merged', () => {
  const l = add(empty(), grant('g1', 100)); code(() => add(l, grant('g1', 250)), 'LEDGER_VIOLATION'); code(() => add(add(empty(), mk('USED', { use_id: 'u', unit: 'gpu-hr', quantity: 1 }, [ev('MEASUREMENT', 'm')])), mk('USED', { use_id: 'u', unit: 'gpu-hr', quantity: 2 }, [ev('MEASUREMENT', 'm2')])), 'LEDGER_VIOLATION');
});
test('service-unit use draws from a service grant once; overuse is refused', () => {
  let l = add(empty(), mk('ACQUIRED', { grant_id: 'gg', unit: 'gpu-hr', quantity: 100 }, [ev('ACCEPTANCE_NOTICE', 'n')]));
  const use = (id, q) => mk('USED', { use_id: id, unit: 'gpu-hr', quantity: q, grant_id: 'gg' }, [ev('DASHBOARD_OBSERVATION', 'd-' + id)]);
  l = add(add(l, use('u1', 30)), use('u2', 30)); assert.equal(res(l).grants.gg.remaining_computed, 40); code(() => add(l, use('u3', 41)), 'LEDGER_VIOLATION'); assert.equal(res(add(l, use('u3', 40))).grants.gg.remaining_computed, 0);
});
test('use without a grant is counted in unit totals but never silently drains a grant', () => {
  let l = add(add(empty(), grant('g1', 100)), mk('USED', { use_id: 'u', unit: 'USD', quantity: 10 }, [ev('MEASUREMENT', 'm')])); assert.equal(res(l).units.USD.used, 10); assert.equal(res(l).grants.g1.remaining_computed, 100);
});
test('expiry is waste, reduces remaining, and is not usage', () => {
  let l = add(add(empty(), grant('g1', 100)), mk('EXPIRED_UNUSED', { waste_id: 'w1', grant_id: 'g1', unit: 'USD', quantity: 30, reason: 'EXPIRED: provider notice' }, [ev('PROVIDER_STATEMENT', 'p')]));
  const g = res(l).grants.g1; assert.equal(g.expired_unused, 30); assert.equal(g.used, 0); assert.equal(g.remaining_computed, 70); assert.equal(res(l).units.USD.used, 0);
  code(() => add(l, mk('EXPIRED_UNUSED', { waste_id: 'w2', grant_id: 'g1', unit: 'USD', quantity: 71, reason: 'EXPIRED' }, [ev('PROVIDER_STATEMENT', 'p2')])), 'LEDGER_VIOLATION');
  code(() => add(l, mk('EXPIRED_UNUSED', { waste_id: 'w3', grant_id: 'g1', unit: 'USD', quantity: 1, reason: 'LOST' }, [ev('PROVIDER_STATEMENT', 'p3')])), 'INVALID_FIELD');
});
test('an observed remaining balance is reported next to the computed one; a mismatch is a flagged discrepancy, never an overwrite', () => {
  let l = add(add(empty(), grant('g1', 100)), mk('REMAINING_OBSERVED', { observation_id: 'o1', grant_id: 'g1', unit: 'USD', quantity: 55 }, [ev('DASHBOARD_OBSERVATION', 'dash')]));
  const g = res(l).grants.g1; assert.equal(g.remaining_computed, 100); assert.equal(g.remaining_observed, 55); assert.equal(g.discrepancy, -45);
  l = add(l, mk('REMAINING_OBSERVED', { observation_id: 'o2', grant_id: 'g1', unit: 'USD', quantity: 100 }, [ev('DASHBOARD_OBSERVATION', 'dash2')])); assert.equal(res(l).grants.g1.discrepancy, 0);
});
test('yield is its own measured output: it is not subtracted from anything and is never converted to spend', () => {
  let l = add(add(empty(), grant('g1', 100)), mk('YIELD_OBSERVED', { yield_id: 'y1', unit: 'evidence-item', quantity: 4 }, [ev('MEASUREMENT', 'run-report')]));
  assert.equal(res(l).units['evidence-item'].yielded, 4); assert.equal(res(l).grants.g1.remaining_computed, 100); assert.equal(res(l).units.USD.yielded, 0);
});

// ---------- corrections keep history ----------
test('a correction removes the wrong event from totals but keeps it in the log', () => {
  let l = add(empty(), grant('g1', 1000)); const wrong = l.events[0].event.event_id;
  l = add(l, mk('CORRECTION', { corrects_event_id: wrong, reason: 'typed an extra zero' }, []));
  assert.equal(l.events.length, 2); assert.deepEqual(sum(l).corrected, [wrong]); assert.equal(sum(l).resources['res-azure'], undefined);   // nothing live remains
  l = add(l, grant('g1', 100)); assert.equal(res(l).grants.g1.granted, 100);                                                                   // the replacement may reuse the id: the wrong event is out of the totals
  assert.equal(R.verifyLog(l).ok, true);
});
test('corrections cannot be corrected, repeated, cross-resource, or aimed at nothing', () => {
  let l = add(empty(), grant('g1', 10)); const t = l.events[0].event.event_id, corr = mk('CORRECTION', { corrects_event_id: t, reason: 'r' }, []);
  const l2 = add(l, corr); code(() => add(l2, mk('CORRECTION', { corrects_event_id: l2.events[1].event.event_id, reason: 'x' }, [])), 'INVALID_CORRECTION');
  code(() => add(l2, mk('CORRECTION', { corrects_event_id: t, reason: 'again' }, [])), 'ALREADY_CORRECTED'); code(() => add(l, { ...mk('CORRECTION', { corrects_event_id: t, reason: 'r' }, []), resource_id: 'other' }), 'INVALID_CORRECTION');
  code(() => add(l, mk('CORRECTION', { corrects_event_id: 'rev-0000000000000000', reason: 'r' }, [])), 'UNKNOWN_REFERENCE');
});

// ---------- integrity ----------
test('the log is a hash chain: edits, reordering and truncation of the middle are detected', () => {
  let l = add(add(add(empty(), grant()), charge()), payment()); assert.equal(R.verifyLog(l).ok, true);
  const edit = C.clone(l); edit.events[0].event.quantity = 999; assert.equal(R.verifyLog(edit).ok, false);
  const re = C.clone(l); [re.events[1], re.events[2]] = [re.events[2], re.events[1]]; assert.equal(R.verifyLog(re).ok, false);
  const cut = C.clone(l); cut.events.splice(1, 1); assert.equal(R.verifyLog(cut).ok, false);
});
test('editing only a stored row hash (the last row has no successor) is detected', () => {
  const l = add(add(empty(), grant()), charge()), bad = C.clone(l); bad.events[bad.events.length - 1].hash = '0'.repeat(64); assert.equal(R.verifyLog(bad).ok, false); assert.equal(R.verifyLog(bad).at, 2);
});
test('an event whose id no longer matches its content is refused', () => {
  const e = { ...grant(), event_id: 'rev-deadbeefdeadbeef' }; code(() => add(empty(), e), 'EVENT_ID_MISMATCH');
});
test('appending never mutates the log passed in', () => {
  const l = empty(), s = JSON.stringify(l); add(l, grant()); assert.equal(JSON.stringify(l), s);
});
test('a refused event leaves the log exactly as it was', () => {
  const l = add(empty(), grant('g1', 10)), s = JSON.stringify(l); try { add(l, mk('USED', { use_id: 'u', unit: 'USD', quantity: 11, grant_id: 'g1' }, [ev('MEASUREMENT', 'm')])); assert.fail('should refuse'); } catch (e) { assert.equal(e.code, 'LEDGER_VIOLATION'); } assert.equal(JSON.stringify(l), s);
});

// ---------- quantities and fields ----------
test('quantities are exact to 6 decimals: 0.1 + 0.2 settles exactly 0.3', () => {
  let l = add(add(empty(), grant('g1', 1)), charge('c1', 0.3)); l = add(add(l, settle('c1', 'GRANT', 'g1', 0.1)), settle('c1', 'GRANT', 'g1', 0.2));
  assert.equal(res(l).charges.c1.outstanding, 0); assert.equal(res(l).grants.g1.remaining_computed, 0.7);
});
test('amounts that are inexact in binary floating point still settle exactly (2.01 + 2.03 = 4.04)', () => {
  let l = add(add(empty(), grant('g1', 10)), charge('c1', 4.04)); l = add(l, settle('c1', 'GRANT', 'g1', 2.01)); l = add(l, settle('c1', 'GRANT', 'g1', 2.03));
  assert.equal(res(l).charges.c1.outstanding, 0); assert.equal(res(l).grants.g1.remaining_computed, 5.96); assert.equal(sum(l).violations.length, 0);
});
test('negative, zero (for positive kinds), NaN, Infinity and over-precise quantities are refused', () => {
  for (const q of [-1, 0, NaN, Infinity, 0.0000001, '5', null]) code(() => add(empty(), grant('g', q)), 'INVALID_QUANTITY');
  const g = add(empty(), grant('g', 10)); assert.doesNotThrow(() => add(g, mk('REMAINING_OBSERVED', { observation_id: 'o', grant_id: 'g', unit: 'USD', quantity: 0 }, [ev('DASHBOARD_OBSERVATION', 'd')])));   // zero is a valid OBSERVED balance
});
test('fields are strict: unexpected fields, missing recorded_by, bad dates and spaces in ids are refused', () => {
  code(() => add(empty(), { ...grant(), surprise: 1 }), 'UNEXPECTED_FIELD'); code(() => add(empty(), { ...grant(), recorded_by: '' }), 'INVALID_FIELD'); code(() => add(empty(), { ...grant(), occurred_on: '10/01/2026' }), 'INVALID_FIELD');
  code(() => add(empty(), { ...grant(), resource_id: 'has space' }), 'INVALID_FIELD'); code(() => add(empty(), { ...grant('a b') }), 'INVALID_FIELD'); code(() => add(empty(), mk('NOPE', {}, [])), 'UNKNOWN_KIND');
});
test('dates are observational: shuffling them never changes any total', () => {
  const build = d => add(add(add(empty(), { ...grant(), occurred_on: d[0] }), { ...charge(), occurred_on: d[1] }), { ...settle('c1', 'GRANT', 'g1', 40), occurred_on: d[2] });
  assert.deepEqual(res(build(['2026-01-01', '2027-06-30', '2020-02-02'])).grants, res(build(['2030-12-31', '2026-01-01', '2026-01-01'])).grants);
});

// ---------- reuse of the existing ledger (no writes) ----------
test('events in REGISTERED units map to the existing ledger CLI; local units are skipped with a reason; nothing is executed', () => {
  let l = add(empty(), mk('USED', { use_id: 'u1', unit: 'Z1-ktok', quantity: 3 }, [ev('MEASUREMENT', 'm1')]));
  l = add(l, mk('YIELD_OBSERVED', { yield_id: 'y1', unit: 'EVID-row', quantity: 2 }, [ev('MEASUREMENT', 'm2')])); l = add(l, mk('USED', { use_id: 'u2', unit: 'gpu-hr', quantity: 1 }, [ev('MEASUREMENT', 'm3')]));
  const out = R.toLedgerCommands(l); assert.equal(out.executed, false); assert.equal(out.commands.length, 2);
  assert(out.commands[0].includes('resource_ledger_v0_1.py spend') && out.commands[0].includes('Z1-ktok 3')); assert(out.commands[1].includes('yield') && out.commands[1].includes('EVID-row 2'));
  assert.equal(out.skipped.length, 1); assert.match(out.skipped[0].why, /not REGISTERED/);
});
test('the unit snapshot is pinned to a hash and was taken from the ratified registry', () => {
  const u = require('../vendor/resource-units.snapshot.json'); assert.equal(u.status, 'RATIFIED'); assert.match(u.source_sha256, /^[0-9a-f]{64}$/); assert.equal(u.policy.conversion, 'none_by_default'); assert(u.units.some(x => x.symbol === 'RAT-min'));
});

// ---------- F2 repairs: exact arithmetic is never lost ----------
test('huge quantities are refused so overdraw can never be bypassed by float overflow', () => {
  for (const q of [1e303, 1e10, 1e9 + 1]) code(() => add(empty(), grant('g', q)), 'INVALID_QUANTITY');
  assert.doesNotThrow(() => add(empty(), grant('g', 1e9)));
});
test('the SUM of all quantities in a log is bounded too', () => {
  let l = empty(); let threw = null;
  for (let i = 0; i < 12 && !threw; i++) { try { l = add(l, grant('g' + i, 1e9)); } catch (e) { threw = e; } }
  assert(threw && threw.code === 'QUANTITY_OVERFLOW', 'expected QUANTITY_OVERFLOW, got ' + (threw && threw.code)); assert.equal(sum(l).violations.length, 0);
});
test('overdraw is still caught at the upper end of the allowed range', () => {
  let l = add(empty(), grant('g1', 1e9)); l = add(l, mk('USED', { use_id: 'u1', unit: 'USD', quantity: 1e9, grant_id: 'g1' }, [ev('MEASUREMENT', 'm1')]));
  code(() => add(l, mk('USED', { use_id: 'u2', unit: 'USD', quantity: 0.000001, grant_id: 'g1' }, [ev('MEASUREMENT', 'm2')])), 'LEDGER_VIOLATION');
});
test('impossible calendar dates are refused', () => { for (const d of ['2099-99-99', '0000-00-00', '2026-02-30']) code(() => add(empty(), { ...grant(), occurred_on: d }), 'INVALID_FIELD'); });

// ---------- F3 repairs: the log is tamper-evident as a WHOLE ----------
test('editing a local unit definition breaks verification (the header is in the chain)', () => {
  const l = add(empty(), grant()), bad = C.clone(l); bad.local_units.USD.dimension = 'compute';
  assert.equal(R.verifyLog(bad).ok, false); code(() => R.summarize(bad), 'LOG_INTEGRITY'); code(() => add(bad, charge()), 'LOG_INTEGRITY');
});
test('extra fields on a row or the log are detected', () => {
  const l = add(empty(), grant()), r = C.clone(l); r.events[0].note = 'x'; assert.equal(R.verifyLog(r).ok, false);
  const t = C.clone(l); t.extra = 1; assert.equal(R.verifyLog(t).ok, false);
});
test('summarize and append refuse a tampered middle row instead of using its number', () => {
  const l = add(add(empty(), grant('g1', 10)), charge('c1', 3)), bad = C.clone(l); bad.events[0].event.quantity = 999;
  code(() => R.summarize(bad), 'LOG_INTEGRITY'); code(() => add(bad, charge('c2', 1)), 'LOG_INTEGRITY');
});
test('tail truncation is detected against a pinned head or event count', () => {
  const l = add(add(add(empty(), grant()), charge()), payment()), pin = R.verifyLog(l), cut = C.clone(l); cut.events.pop();
  assert.equal(R.verifyLog(cut).ok, true, 'internally consistent, so only a pin can reveal it');
  assert.equal(R.verifyLog(cut, { expect_head: pin.head }).ok, false); assert.equal(R.verifyLog(cut, { expect_events: pin.events }).ok, false);
  assert.equal(R.verifyLog(l, { expect_head: pin.head, expect_events: pin.events }).ok, true);
  const wipe = C.clone(l); wipe.events = []; assert.equal(R.verifyLog(wipe, { expect_events: 3 }).ok, false);
});

// ---------- audit-2 repairs ----------
test('names that exist on every JavaScript object are refused as units, resource ids and other ids', () => {
  for (const n of ['constructor', 'toString', '__proto__', 'hasOwnProperty', 'valueOf']) {
    code(() => add(empty(), { ...grant('g1', 1, 'USD'), unit: n }), 'INVALID_FIELD'); code(() => add(empty(), { ...grant('g1'), resource_id: n }), 'INVALID_FIELD'); code(() => add(empty(), { ...grant(n) }), 'INVALID_FIELD');
    code(() => R.newLog({ [n]: { dimension: 'capital' } }), 'INVALID_UNIT');
  }
  assert.equal(Object.granted, undefined); assert.equal({}.granted, undefined);
});
test('a tampered log plus a duplicate (idempotent) event still throws LOG_INTEGRITY', () => {
  const l = add(empty(), grant('g1', 10)), bad = C.clone(l); bad.events[0].event.quantity = 999;
  code(() => R.appendEvent(bad, l.events[0].event), 'LOG_INTEGRITY');
});
test('a transaction reference backs one payment and one charge, whatever its type label, case or resource', () => {
  const pay = (id, type, ref, res = 'res-azure') => ({ ...payment(), resource_id: res, payment_id: id, evidence: [ev(type, ref)] });
  const l = add(empty(), pay('p1', 'RECEIPT', 'rcpt-5'));
  code(() => add(l, pay('p2', 'INVOICE', 'rcpt-5')), 'LEDGER_VIOLATION'); code(() => add(l, pay('p3', 'RECEIPT', 'RCPT-5')), 'LEDGER_VIOLATION'); code(() => add(l, pay('p4', 'RECEIPT', ' rcpt-5 ')), 'INVALID_EVIDENCE'); code(() => add(l, pay('p5', 'RECEIPT', 'rcpt-5', 'res-other')), 'LEDGER_VIOLATION');
  const c1 = add(l, { ...charge('c1'), evidence: [ev('INVOICE', 'inv-9')] }); code(() => add(c1, { ...charge('c2'), evidence: [ev('INVOICE', 'INV-9')] }), 'LEDGER_VIOLATION');
  assert.doesNotThrow(() => add(l, { ...charge('c3'), evidence: [ev('INVOICE', 'rcpt-5')] }));   // an invoice and its own receipt may share a number
});
test('pins work on summarize and append too', () => {
  const l = add(add(empty(), grant()), charge()), pin = R.verifyLog(l), cut = C.clone(l); cut.events.pop();
  code(() => R.summarize(cut, { expect_head: pin.head }), 'LOG_INTEGRITY'); code(() => R.appendEvent(cut, payment(), { expect_events: pin.events }), 'LOG_INTEGRITY'); assert.doesNotThrow(() => R.summarize(l, { expect_head: pin.head }));
});

// ---------- audit-3 repairs ----------
test('a reference backs one payment whatever the evidence type or letter case; punctuation makes a DIFFERENT reference', () => {
  const pay = (id, type, ref) => ({ ...payment(), payment_id: id, evidence: [{ type, ref, claim_type: 'TRANSACTION_PROOF' }] });
  const l = add(empty(), { ...payment(), payment_id: 'p1', evidence: [{ type: 'PROVIDER_STATEMENT', ref: 'PS-1', claim_type: 'CLAIM' }] });
  code(() => add(l, { ...payment(), payment_id: 'p2', evidence: [{ type: 'PROVIDER_STATEMENT', ref: 'ps-1', claim_type: 'CLAIM' }] }), 'LEDGER_VIOLATION');
  assert.doesNotThrow(() => add(l, { ...payment(), payment_id: 'p3', evidence: [{ type: 'PROVIDER_STATEMENT', ref: 'PS_1', claim_type: 'CLAIM' }] }));   // two real receipts may differ only by punctuation
  const l2 = add(empty(), pay('p1', 'RECEIPT', 'REC-1')); code(() => add(l2, { ...payment(), payment_id: 'p4', evidence: [{ type: 'PROVIDER_STATEMENT', ref: 'rec-1', claim_type: 'CLAIM' }] }), 'LEDGER_VIOLATION');
  const l3 = add(empty(), pay('p1', 'RECEIPT', 'A-1')); assert.doesNotThrow(() => add(l3, pay('p2', 'RECEIPT', 'A1'))); assert.doesNotThrow(() => add(l3, pay('p3', 'RECEIPT', 'A-12')));
});
test('the optional USED.grant_id is validated like every other id', () => {
  const l = add(empty(), grant('g1', 10));
  for (const v of ['', null, 0, false, 'constructor', '__proto__', 'has space']) code(() => add(l, mk('USED', { use_id: 'u1', unit: 'USD', quantity: 1, grant_id: v }, [ev('MEASUREMENT', 'm1')])), 'INVALID_FIELD');
  assert.doesNotThrow(() => add(l, mk('USED', { use_id: 'u1', unit: 'USD', quantity: 1, grant_id: 'g1' }, [ev('MEASUREMENT', 'm1')])));
});
test('re-appending an event that was later corrected is refused, not reported as "already recorded"', () => {
  const l = add(empty(), payment()), id = l.events[0].event.event_id, l2 = add(l, mk('CORRECTION', { corrects_event_id: id, reason: 'wrong amount' }, []));
  code(() => R.appendEvent(l2, l.events[0].event), 'EVENT_CORRECTED');
});
test('error messages name no value from the event', () => {
  for (const [e, c] of [[{ ...grant(), kind: 'SECRET_KIND_1Z999' }, 'UNKNOWN_KIND'], [{ ...grant(), SECRETFIELD_1Z999: 1 }, 'UNEXPECTED_FIELD'], [{ ...grant(), unit: 'SECRETUNIT1Z999' }, 'UNKNOWN_UNIT']]) { const x = code(() => add(empty(), e), c); assert(!/1Z999/.test(x.message), x.message); }
});

// ---------- audit-4 repairs ----------
test('a benefit measure unit must be a string: arrays and objects are refused even when they look like a prototype name', () => {
  for (const u of [['constructor'], ['__proto__'], { a: 1 }, 7, null]) code(() => add(empty(), mk('BENEFIT_OBSERVED', { benefit_id: 'b1', statement: 'x', unit: u, quantity: 1 }, [ev('OUTCOME_RECORD', 'o1')])), 'UNKNOWN_UNIT');
});

// ---------- audit-5 repairs ----------
test('every amount with at most 2 (or 6) decimals up to 1e6 is accepted; more than 6 decimals is still refused', () => {
  for (const q of [16384.01, 263667.21, 529704.33, 527521.81, 0.1, 0.3, 1.1, 2.675, 999999.99, 1e9, 0.000001, 123456.654321]) assert.doesNotThrow(() => add(empty(), grant('g', q)), String(q));
  let refused = 0; for (let c = 1; c <= 20000; c++) { try { add(empty(), grant('g', c * 37 / 100 + 0)); } catch { refused++; } }   // many 2-decimal amounts, including large ones
  assert.equal(refused, 0, refused + ' ordinary amounts were refused');
  for (const q of [0.0000001, 1.0000001, 500000000.0000001, 16384.0100001]) code(() => add(empty(), grant('g', q)), 'INVALID_QUANTITY');
});

// ---------- audit-6 repairs ----------
test('a benefit cannot be proved by a payment or charge reference, whatever its evidence label or event order', () => {
  const lp = add(empty(), { ...payment(), payment_id: 'p1', evidence: [ev('RECEIPT', 'rc-1')] });
  for (const type of ['THIRD_PARTY_CONFIRMATION', 'OUTCOME_RECORD', 'HUMAN_ASSERTION']) for (const ref of ['rc-1', 'RC-1']) code(() => add(lp, mk('BENEFIT_OBSERVED', { benefit_id: 'b-' + type + ref, statement: 'it worked' }, [{ type, ref, claim_type: 'CLAIM' }])), 'LEDGER_VIOLATION');
  assert.doesNotThrow(() => add(lp, mk('BENEFIT_OBSERVED', { benefit_id: 'b-ok', statement: 'it worked' }, [{ type: 'THIRD_PARTY_CONFIRMATION', ref: 'outcome-1', claim_type: 'CLAIM' }])));
  const lb = add(empty(), mk('BENEFIT_OBSERVED', { benefit_id: 'b1', statement: 'it worked' }, [{ type: 'THIRD_PARTY_CONFIRMATION', ref: 'rc-9', claim_type: 'CLAIM' }]));
  code(() => add(lb, { ...payment(), payment_id: 'p9', evidence: [ev('RECEIPT', 'rc-9')] }), 'LEDGER_VIOLATION');   // the order of the two events does not matter
  const ch = add(empty(), { ...charge('c1'), evidence: [ev('INVOICE', 'inv-1')] }); code(() => add(ch, mk('BENEFIT_OBSERVED', { benefit_id: 'b2', statement: 's' }, [{ type: 'HUMAN_ASSERTION', ref: 'inv-1', claim_type: 'CLAIM' }])), 'LEDGER_VIOLATION');
});
finish();

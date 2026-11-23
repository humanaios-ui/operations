'use strict';
// Resource event model for the Desk. Offline, deterministic, append-only, hash-chained.
// Reuses the ratified vocabulary of operations/RESOURCE_UNITS.yaml (pinned snapshot) and the rule of
// operations/tools/resource_ledger_v0_1.py: units never convert; every claim carries a source.
// DISTINCT events: discovery / acquisition / payment / charge / settlement / use / remaining / yield / waste / benefit.
//   * A RECEIPT or INVOICE proves a TRANSACTION. It can never back a BENEFIT.
//   * A credit can be drawn down only through a SETTLEMENT (money) or a USED event (service units); each is counted once.
const UNITS = require('../vendor/resource-units.snapshot.json');
const { canonical, digest, shortId, clone, BridgeError, isRealDate, isReservedKey } = require('./core.cjs');

const REGISTERED = new Map(UNITS.units.map(u => [u.symbol, u]));
const DIMENSIONS = new Set(UNITS.dimensions);
const TOKEN = /^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,99}$/;
const DATE = /^\d{4}-\d{2}-\d{2}$/;
const MICRO = 1e6, MAX_QUANTITY = 1e9;   // 1e9 units = 1e15 micro-units, safely inside Number.MAX_SAFE_INTEGER (9.007e15); appendEvent also bounds the SUM
const EVIDENCE_TYPES = ['RECEIPT', 'INVOICE', 'PROVIDER_STATEMENT', 'ACCEPTANCE_NOTICE', 'DASHBOARD_OBSERVATION', 'HUMAN_ASSERTION', 'OUTCOME_RECORD', 'THIRD_PARTY_CONFIRMATION', 'MEASUREMENT'];
const CLAIM_TYPES = ['CLAIM', 'TRANSACTION_PROOF', 'MEASUREMENT'];
const MONEY_PROOF = new Set(['RECEIPT', 'INVOICE']);
const BASE = ['event_id', 'kind', 'resource_id', 'occurred_on', 'evidence', 'recorded_by'];
const SPEC = {
  DISCOVERED: { req: [], unit: false, min: 0, types: null },
  ACQUIRED: { req: ['grant_id'], unit: true, qty: 'pos', min: 1, types: ['ACCEPTANCE_NOTICE', 'PROVIDER_STATEMENT', 'HUMAN_ASSERTION'] },
  PAYMENT: { req: ['payment_id'], unit: true, qty: 'pos', min: 1, types: ['RECEIPT', 'INVOICE', 'PROVIDER_STATEMENT'] },
  CHARGE: { req: ['charge_id'], unit: true, qty: 'pos', min: 1, types: ['INVOICE', 'PROVIDER_STATEMENT', 'DASHBOARD_OBSERVATION', 'RECEIPT'] },
  SETTLEMENT: { req: ['charge_id', 'funding', 'funding_id'], unit: true, qty: 'pos', min: 1, types: ['INVOICE', 'PROVIDER_STATEMENT', 'RECEIPT', 'DASHBOARD_OBSERVATION'] },
  USED: { req: ['use_id'], opt: ['grant_id'], unit: true, qty: 'pos', min: 1, types: ['DASHBOARD_OBSERVATION', 'PROVIDER_STATEMENT', 'MEASUREMENT', 'HUMAN_ASSERTION'] },
  REMAINING_OBSERVED: { req: ['observation_id', 'grant_id'], unit: true, qty: 'nonneg', min: 1, types: ['DASHBOARD_OBSERVATION', 'PROVIDER_STATEMENT', 'HUMAN_ASSERTION'] },
  YIELD_OBSERVED: { req: ['yield_id'], unit: true, qty: 'pos', min: 1, types: ['MEASUREMENT', 'OUTCOME_RECORD', 'HUMAN_ASSERTION'] },
  EXPIRED_UNUSED: { req: ['waste_id', 'grant_id', 'reason'], unit: true, qty: 'pos', min: 1, types: ['PROVIDER_STATEMENT', 'DASHBOARD_OBSERVATION', 'HUMAN_ASSERTION'] },
  BENEFIT_OBSERVED: { req: ['benefit_id', 'statement'], opt: ['unit', 'quantity'], unit: false, min: 1, types: ['OUTCOME_RECORD', 'THIRD_PARTY_CONFIRMATION', 'HUMAN_ASSERTION'] },
  CORRECTION: { req: ['corrects_event_id', 'reason'], unit: false, min: 0, types: null },
};
const ID_FIELDS = { ACQUIRED: 'grant_id', PAYMENT: 'payment_id', CHARGE: 'charge_id', USED: 'use_id', REMAINING_OBSERVED: 'observation_id', YIELD_OBSERVED: 'yield_id', EXPIRED_UNUSED: 'waste_id', BENEFIT_OBSERVED: 'benefit_id' };

const bad = (code, msg, extra) => { throw new BridgeError(code, msg, extra); };
const micro = q => Math.round(q * MICRO);
// One normalisation for every consumer: only letter case and surrounding spaces are ignored. "A-1" and "A1" are DIFFERENT references (they may be two real receipts).
const normRef = r => String(r).trim().toLowerCase();
function quantityOf(q, mode, what) {
  if (typeof q !== 'number' || !Number.isFinite(q) || q < 0) bad('INVALID_QUANTITY', `${what}: quantity must be a finite number >= 0`);
  if (q > MAX_QUANTITY) bad('INVALID_QUANTITY', `${what}: quantity above ${MAX_QUANTITY} is refused (exact arithmetic would be lost)`);
  // At most 6 decimals means: the nearest double to (micro-units / 1e6) is q itself. Exact for every value up to MAX_QUANTITY (a fixed float tolerance wrongly refused ordinary amounts such as 16384.01).
  if (Math.round(q * MICRO) / MICRO !== q) bad('INVALID_QUANTITY', `${what}: more than 6 decimal places`);
  if (mode === 'pos' && q <= 0) bad('INVALID_QUANTITY', `${what}: quantity must be > 0`);
  return micro(q);
}

function newLog(local_units = {}) {
  for (const [sym, u] of Object.entries(local_units)) {
    if (REGISTERED.has(sym)) bad('UNIT_REDEFINED', `${sym} is a registered unit and cannot be redefined`);
    if (!TOKEN.test(sym) || isReservedKey(sym) || !u || !DIMENSIONS.has(u.dimension) || Object.keys(u).sort().join() !== 'dimension') bad('INVALID_UNIT', `Local unit ${sym} needs exactly {dimension} from the registry's dimensions`);
  }
  return { schema: 'humanaios.resource-events.v1', unit_registry: { source_sha256: UNITS.source_sha256, status: UNITS.status }, local_units: clone(local_units), events: [] };
}
const unitInfo = (log, sym) => REGISTERED.has(sym) ? { ...REGISTERED.get(sym), registry: 'REGISTERED' } : (typeof sym === 'string' && Object.hasOwn(log.local_units, sym)) ? { symbol: sym, dimension: log.local_units[sym].dimension, registry: 'LOCAL_CANDIDATE' } : null;

function validateEvent(log, e) {
  if (!e || typeof e !== 'object' || Array.isArray(e)) bad('INVALID_EVENT', 'Event must be an object');
  const spec = SPEC[e.kind]; if (!spec) bad('UNKNOWN_KIND', 'Unknown event kind (value not shown)');
  const allowed = new Set([...BASE, ...(spec.unit ? ['unit', 'quantity'] : []), ...spec.req, ...(spec.opt || [])]);
  for (const k of Object.keys(e)) if (!allowed.has(k)) bad('UNEXPECTED_FIELD', `${e.kind} was given a field it does not take (name not shown)`);
  for (const k of ['resource_id', ...spec.req.filter(r => !['reason', 'statement'].includes(r))]) if (typeof e[k] !== 'string' || !TOKEN.test(e[k])) bad('INVALID_FIELD', `${k} must be a short token`);
  for (const k of ['resource_id', 'unit', ...spec.req.filter(r => !['reason', 'statement'].includes(r))]) if (isReservedKey(e[k])) bad('INVALID_FIELD', `${k}: that name is reserved`);
  for (const k of spec.opt || []) if (['grant_id'].includes(k) && e[k] !== undefined) { if (typeof e[k] !== 'string' || !TOKEN.test(e[k])) bad('INVALID_FIELD', `${k} must be a short token`); if (isReservedKey(e[k])) bad('INVALID_FIELD', `${k}: that name is reserved`); }
  if (typeof e.recorded_by !== 'string' || !e.recorded_by.trim() || e.recorded_by.length > 100) bad('INVALID_FIELD', 'recorded_by is required (a label, not an authentication)');
  if (typeof e.occurred_on !== 'string' || !isRealDate(e.occurred_on)) bad('INVALID_FIELD', 'occurred_on must be a real YYYY-MM-DD date (observational only; it never schedules anything)');
  for (const k of ['reason', 'statement']) if (spec.req.includes(k) && (typeof e[k] !== 'string' || !e[k].trim() || e[k].length > 300)) bad('INVALID_FIELD', k + ' must be 1-300 characters');
  if (e.kind === 'EXPIRED_UNUSED' && !['EXPIRED', 'FORFEITED', 'UNUSED_AT_CLOSE'].includes(e.reason.split(':')[0])) bad('INVALID_FIELD', 'reason must start with EXPIRED, FORFEITED or UNUSED_AT_CLOSE');
  if (e.kind === 'SETTLEMENT' && !['GRANT', 'PAYMENT'].includes(e.funding)) bad('INVALID_FIELD', 'funding must be GRANT or PAYMENT');
  if (!Array.isArray(e.evidence) || e.evidence.length < spec.min || e.evidence.length > 10) bad('EVIDENCE_REQUIRED', `${e.kind} needs at least ${spec.min} evidence item(s)`);
  for (const ev of e.evidence) {
    if (!ev || Object.keys(ev).sort().join() !== 'claim_type,ref,type') bad('INVALID_EVIDENCE', 'Evidence is exactly {type, ref, claim_type}');
    if (!EVIDENCE_TYPES.includes(ev.type) || !CLAIM_TYPES.includes(ev.claim_type) || typeof ev.ref !== 'string' || !TOKEN.test(ev.ref)) bad('INVALID_EVIDENCE', 'Unknown evidence type, claim_type or ref');
    if (spec.types && !spec.types.includes(ev.type)) bad(e.kind === 'BENEFIT_OBSERVED' ? 'BENEFIT_BACKED_BY_TRANSACTION' : 'EVIDENCE_TYPE_NOT_ALLOWED', `${ev.type} cannot back ${e.kind}${e.kind === 'BENEFIT_OBSERVED' ? ' (a receipt proves a transaction, not realized benefit)' : ''}`);
    if (e.kind === 'BENEFIT_OBSERVED' && ev.claim_type === 'TRANSACTION_PROOF') bad('BENEFIT_BACKED_BY_TRANSACTION', 'Transaction proof cannot back a benefit');
    if (MONEY_PROOF.has(ev.type) && ev.claim_type === 'MEASUREMENT') bad('INVALID_EVIDENCE', 'A receipt/invoice is not a measurement');
  }
  let qty = null;
  if (spec.unit) {
    const u = unitInfo(log, e.unit); if (typeof e.unit !== 'string' || !u) bad('UNKNOWN_UNIT', 'The unit is neither registered nor declared as a local candidate unit (value not shown)');
    qty = quantityOf(e.quantity, spec.qty, e.kind);
  } else if (e.kind === 'BENEFIT_OBSERVED' && (e.unit !== undefined || e.quantity !== undefined)) {
    if (typeof e.unit !== 'string' || e.quantity === undefined || !unitInfo(log, e.unit)) bad('UNKNOWN_UNIT', 'A benefit measure needs both a known unit and a quantity');
    quantityOf(e.quantity, 'nonneg', 'BENEFIT_OBSERVED');
  }
  return qty;
}
const eventId = e => shortId('rev-', Object.fromEntries(Object.entries(e).filter(([k]) => k !== 'event_id')));

// ---------- reducer: one place that decides what is counted, and refuses double counting ----------
function summarize(log, opts) {
  assertIntact(log, opts);
  const events = log.events.map(x => x.event), corrected = new Set(events.filter(e => e.kind === 'CORRECTION').map(e => e.corrects_event_id));
  const live = events.filter(e => e.kind !== 'CORRECTION' && !corrected.has(e.event_id)), V = [], R = {};
  const res = id => R[id] || (R[id] = { discovered: false, grants: {}, payments: {}, charges: {}, uses: [], yields: [], benefits: [], waste: [] });
  const seen = {}, refUse = {};
  // A transaction reference may back ONE payment and ONE charge, whatever its type label, case, or resource (an invoice and its receipt may share a number; two payments may not).
  const refs = (side, e, id) => { for (const ev of e.evidence) { const k = side + '|' + normRef(ev.ref), owner = e.resource_id + '|' + id; if (refUse[k] && refUse[k] !== owner) V.push({ code: 'DUPLICATE_TRANSACTION_REF', ref: ev.ref, owners: [refUse[k], owner] }); refUse[k] = refUse[k] || owner; } };
  const txRefs = new Set();   // every payment/charge reference, for the benefit check below
  const once = (kind, id, e) => { const k = kind + '|' + e.resource_id + '|' + id; if (seen[k]) V.push({ code: 'DUPLICATE_' + ID_FIELDS[kind].toUpperCase(), id, event_id: e.event_id }); seen[k] = true; };
  for (const e of live) {
    const r = res(e.resource_id);
    if (e.kind === 'DISCOVERED') r.discovered = true;
    if (e.kind === 'ACQUIRED') { once('ACQUIRED', e.grant_id, e); r.grants[e.grant_id] = { unit: e.unit, granted: micro(e.quantity), settled: 0, used: 0, expired: 0, observed: [], evidence_types: e.evidence.map(x => x.type), basis: 'CLAIMED_BY_' + e.evidence[0].type }; }
    if (e.kind === 'PAYMENT') { once('PAYMENT', e.payment_id, e); r.payments[e.payment_id] = { unit: e.unit, paid: micro(e.quantity), applied: 0, proves: 'TRANSACTION_ONLY' };
      refs('P', e, e.payment_id); for (const ev of e.evidence) txRefs.add(normRef(ev.ref)); }
    if (e.kind === 'CHARGE') { once('CHARGE', e.charge_id, e); refs('C', e, e.charge_id); for (const ev of e.evidence) txRefs.add(normRef(ev.ref)); r.charges[e.charge_id] = { unit: e.unit, billed: micro(e.quantity), settled: 0 }; }
  }
  for (const e of live) {
    const r = res(e.resource_id);
    if (e.kind === 'SETTLEMENT') {
      const c = r.charges[e.charge_id], f = e.funding === 'GRANT' ? r.grants[e.funding_id] : r.payments[e.funding_id];
      if (!c || !f) { V.push({ code: 'UNKNOWN_REFERENCE', event_id: e.event_id }); continue; }
      if (c.unit !== e.unit || f.unit !== e.unit) { V.push({ code: 'UNIT_MISMATCH', event_id: e.event_id, units: [c.unit, f.unit, e.unit] }); continue; }
      const q = micro(e.quantity); c.settled += q; if (e.funding === 'GRANT') f.settled += q; else f.applied += q;
    }
    if (e.kind === 'USED') {
      once('USED', e.use_id, e); r.uses.push({ use_id: e.use_id, unit: e.unit, q: micro(e.quantity), grant_id: e.grant_id || null });
      if (e.grant_id) { const g = r.grants[e.grant_id]; if (!g) V.push({ code: 'UNKNOWN_REFERENCE', event_id: e.event_id }); else if (g.unit !== e.unit) V.push({ code: 'UNIT_MISMATCH', event_id: e.event_id, units: [g.unit, e.unit] }); else g.used += micro(e.quantity); }
    }
    if (e.kind === 'EXPIRED_UNUSED') { once('EXPIRED_UNUSED', e.waste_id, e); const g = r.grants[e.grant_id]; if (!g) V.push({ code: 'UNKNOWN_REFERENCE', event_id: e.event_id }); else if (g.unit !== e.unit) V.push({ code: 'UNIT_MISMATCH', event_id: e.event_id }); else { g.expired += micro(e.quantity); r.waste.push({ waste_id: e.waste_id, unit: e.unit, q: micro(e.quantity), reason: e.reason }); } }
    if (e.kind === 'REMAINING_OBSERVED') { once('REMAINING_OBSERVED', e.observation_id, e); const g = r.grants[e.grant_id]; if (!g) V.push({ code: 'UNKNOWN_REFERENCE', event_id: e.event_id }); else if (g.unit !== e.unit) V.push({ code: 'UNIT_MISMATCH', event_id: e.event_id }); else g.observed.push({ q: micro(e.quantity), on: e.occurred_on, source: e.evidence[0].type }); }
    if (e.kind === 'YIELD_OBSERVED') { once('YIELD_OBSERVED', e.yield_id, e); r.yields.push({ yield_id: e.yield_id, unit: e.unit, q: micro(e.quantity) }); }
    if (e.kind === 'BENEFIT_OBSERVED') { once('BENEFIT_OBSERVED', e.benefit_id, e); if (e.evidence.some(x => txRefs.has(normRef(x.ref)))) V.push({ code: 'BENEFIT_REUSES_TRANSACTION_REF', event_id: e.event_id }); /* a benefit may not be "proved" by a payment or charge reference, whatever the evidence label */ r.benefits.push({ benefit_id: e.benefit_id, statement: e.statement, evidence_types: e.evidence.map(x => x.type), basis: e.evidence.some(x => x.type === 'THIRD_PARTY_CONFIRMATION') ? 'THIRD_PARTY_CONFIRMED' : 'ASSERTED_ONLY', measure: e.unit ? { unit: e.unit, q: micro(e.quantity) } : null }); }
  }
  const out = { schema: 'humanaios.resource-summary.v1', note: 'Quantities are reported per unit and per record. Nothing is converted or summed across units. A receipt proves a transaction, not realized benefit.', resources: {}, violations: V, corrected: [...corrected].sort() };
  for (const [id, r] of Object.entries(R)) {
    const rr = { discovered: r.discovered, grants: {}, payments: {}, charges: {}, units: {}, benefits: r.benefits.map(b => ({ ...b, measure: b.measure && { unit: b.measure.unit, quantity: b.measure.q / MICRO } })), benefit_basis_note: 'Benefit is asserted or third-party confirmed; it is never derived from spending or receipts.' };
    const U = u => rr.units[u] || (rr.units[u] = { granted: 0, paid: 0, billed: 0, settled: 0, used: 0, expired: 0, yielded: 0 });
    for (const [gid, g] of Object.entries(r.grants)) {
      const remaining = g.granted - g.settled - g.used - g.expired;
      if (remaining < 0) V.push({ code: 'OVERDRAWN_GRANT', resource_id: id, grant_id: gid, over_by: -remaining / MICRO, unit: g.unit });
      const lastObs = g.observed.length ? g.observed[g.observed.length - 1] : null;
      rr.grants[gid] = { unit: g.unit, granted: g.granted / MICRO, drawn_by_settlement: g.settled / MICRO, used: g.used / MICRO, expired_unused: g.expired / MICRO, remaining_computed: remaining / MICRO, remaining_observed: lastObs && lastObs.q / MICRO, observed_on: lastObs && lastObs.on, discrepancy: lastObs && lastObs.q !== remaining ? (lastObs.q - remaining) / MICRO : 0, basis: g.basis };
      U(g.unit).granted += g.granted; U(g.unit).expired += g.expired;
    }
    for (const [pid, p] of Object.entries(r.payments)) { if (p.applied > p.paid) V.push({ code: 'OVERAPPLIED_PAYMENT', resource_id: id, payment_id: pid, over_by: (p.applied - p.paid) / MICRO, unit: p.unit }); rr.payments[pid] = { unit: p.unit, paid: p.paid / MICRO, applied_to_charges: p.applied / MICRO, unapplied: (p.paid - p.applied) / MICRO, proves: p.proves }; U(p.unit).paid += p.paid; }
    for (const [cid, c] of Object.entries(r.charges)) { if (c.settled > c.billed) V.push({ code: 'OVERSETTLED_CHARGE', resource_id: id, charge_id: cid, over_by: (c.settled - c.billed) / MICRO, unit: c.unit }); rr.charges[cid] = { unit: c.unit, billed: c.billed / MICRO, settled: c.settled / MICRO, outstanding: (c.billed - c.settled) / MICRO }; U(c.unit).billed += c.billed; U(c.unit).settled += c.settled; }
    for (const u of r.uses) U(u.unit).used += u.q;
    for (const y of r.yields) U(y.unit).yielded += y.q;
    for (const u of Object.values(rr.units)) for (const k of Object.keys(u)) u[k] = u[k] / MICRO;
    out.resources[id] = rr;
  }
  return out;
}

function appendEvent(log, eventIn, opts) {
  const e = clone(eventIn);
  assertIntact(log, opts);
  validateEvent(log, e);
  const id = eventId(e);
  if (e.event_id !== undefined && e.event_id !== id) bad('EVENT_ID_MISMATCH', 'event_id does not match the content (edited after hashing?)');
  e.event_id = id;
  if (log.events.some(x => x.event.event_id === id)) {
    if (log.events.some(x => x.event.kind === 'CORRECTION' && x.event.corrects_event_id === id)) bad('EVENT_CORRECTED', 'That exact event was recorded and later corrected; it is no longer live. Record a new event with a new id if it is true again.');
    return { log, changed: false, event_id: id };
  }       // idempotent re-append
  if (e.kind === 'CORRECTION') {
    const t = log.events.find(x => x.event.event_id === e.corrects_event_id);
    if (!t) bad('UNKNOWN_REFERENCE', 'Correction target does not exist');
    if (t.event.kind === 'CORRECTION') bad('INVALID_CORRECTION', 'A correction cannot be corrected; append a new event instead');
    if (t.event.resource_id !== e.resource_id) bad('INVALID_CORRECTION', 'Correction must name the same resource');
    if (log.events.some(x => x.event.kind === 'CORRECTION' && x.event.corrects_event_id === e.corrects_event_id)) bad('ALREADY_CORRECTED', 'That event was already corrected');
  }
  const prev = log.events.length ? log.events[log.events.length - 1].hash : genesis(log);
  const row = { seq: log.events.length + 1, prev, event: e }; row.hash = digest({ seq: row.seq, prev, event: e });
  const next = { ...clone(log), events: [...clone(log.events), row] };
  let total = 0; for (const x of next.events) { const ev = x.event; for (const v of [ev.quantity]) if (typeof v === 'number') total += micro(v); }
  if (total > Number.MAX_SAFE_INTEGER) bad('QUANTITY_OVERFLOW', 'The sum of all quantities in this log would exceed exact arithmetic; start a new log segment');
  const before = new Set(summarize(log).violations.map(canonical));
  const fresh = summarize(next).violations.filter(v => !before.has(canonical(v)));
  if (fresh.length) bad('LEDGER_VIOLATION', 'Refused: ' + fresh.map(v => v.code).join(', '), { violations: fresh });
  return { log: next, changed: true, event_id: id };
}
// The chain starts from a digest of the log HEADER (schema, unit registry, local units), so editing a unit definition breaks it.
const genesis = log => digest({ schema: log.schema, unit_registry: log.unit_registry, local_units: log.local_units });
const ROW_KEYS = 'event,hash,prev,seq', LOG_KEYS = 'events,local_units,schema,unit_registry';
// verifyLog proves INTERNAL consistency only. Tail truncation and a complete forgery are only detectable against a head you pinned earlier
// (opts.expect_head / opts.expect_events). The hash is unkeyed, so it is tamper-EVIDENT against accident, not authentication.
function verifyLog(log, opts = {}) {
  if (!log || typeof log !== 'object' || Object.keys(log).sort().join() !== LOG_KEYS || !Array.isArray(log.events)) return { ok: false, at: 0, reason: 'unexpected log shape' };
  let prev = genesis(log), i = 0;
  for (const row of log.events) {
    i++;
    if (!row || Object.keys(row).sort().join() !== ROW_KEYS) return { ok: false, at: i, reason: 'unexpected row fields' };
    if (row.seq !== i || row.prev !== prev || row.hash !== digest({ seq: row.seq, prev: row.prev, event: row.event })) return { ok: false, at: i, reason: 'chain broken' };
    if (row.event.event_id !== eventId(row.event)) return { ok: false, at: i, reason: 'event content does not match its id' };
    prev = row.hash;
  }
  if (opts.expect_events !== undefined && opts.expect_events !== i) return { ok: false, at: i, reason: `expected ${opts.expect_events} events, found ${i} (truncated or extended)` };
  if (opts.expect_head !== undefined && opts.expect_head !== prev) return { ok: false, at: i, reason: 'head does not match the pinned head' };
  return { ok: true, events: i, head: prev };
}
function assertIntact(log, opts) { const v = verifyLog(log, opts || {}); if (!v.ok) throw new BridgeError('LOG_INTEGRITY', `Resource log failed verification at event ${v.at}: ${v.reason}. Nothing was read or written.`); }
// Commands a human could run with the EXISTING ledger tool, for events whose unit is a REGISTERED one. Nothing is executed or written.
function toLedgerCommands(log) {
  const commands = [], skipped = [];
  for (const { event: e } of log.events) {
    const u = e.unit && REGISTERED.get(e.unit);
    if (e.kind === 'USED' && u && u.sign === 'positive' && !['evidence', 'assurance'].includes(u.dimension)) commands.push(`python3 tools/resource_ledger_v0_1.py spend <LEDGER> <ORDER_ID> ${e.unit} ${e.quantity} --by <WHO> --source ${e.event_id}`);
    else if (e.kind === 'YIELD_OBSERVED' && u && ['evidence', 'assurance'].includes(u.dimension)) commands.push(`python3 tools/resource_ledger_v0_1.py yield <LEDGER> <ORDER_ID> ${e.unit} ${e.quantity} --by <WHO> --source ${e.event_id}`);
    else if (e.unit) skipped.push({ event_id: e.event_id, kind: e.kind, unit: e.unit, why: u ? 'no matching ledger command for this kind' : 'unit is not REGISTERED (a candidate unit needs Z2 registration first)' });
  }
  return { commands, skipped, executed: false };
}

module.exports = { normRef, newLog, appendEvent, verifyLog, summarize, toLedgerCommands, validateEvent, eventId, REGISTERED, SPEC };

'use strict';
// Shared, dependency-free helpers. Offline: no network, no clock, no randomness.
const crypto = require('node:crypto');

const canonical = x => Array.isArray(x) ? '[' + x.map(canonical).join(',') + ']'
  : x && typeof x === 'object' ? '{' + Object.keys(x).sort().map(k => JSON.stringify(k) + ':' + canonical(x[k])).join(',') + '}'
  : JSON.stringify(x);
const digest = x => crypto.createHash('sha256').update(canonical(x)).digest('hex');
const shortId = (prefix, x) => prefix + digest(x).slice(0, 16);
const hmacId = (prefix, salt, x) => prefix + crypto.createHmac('sha256', salt).update(canonical(x)).digest('hex').slice(0, 16);
const clone = x => JSON.parse(JSON.stringify(x));

class BridgeError extends Error { constructor(code, message, extra) { super(message); this.name = 'BridgeError'; this.code = code; Object.assign(this, extra || {}); } }
// A stale write is refused, but the caller's pending decisions/edits ride along so nothing typed is lost.
class StaleWriteError extends BridgeError { constructor(expected, actual, preserved) { super('STALE_WRITE', `Desk is at revision ${actual}, expected ${expected}. Nothing was written.`, { expected, actual, preserved: clone(preserved) }); } }

// The Desk event log is append-only. A later state is acceptable only if the earlier events are an exact prefix,
// except that the Desk caps its log at `cap`; then only the OLDEST events may roll off (and are archived by the app).
// Events must be an exact prefix (only the oldest may roll off at the cap, and the caller sees `dropped`). Saved import snapshots are history too:
// every earlier snapshot must still exist, byte-identical.
function verifyHistoryPrefix(before, after, cap = 5000) {
  const b = before.events, a = after.events, eq = (x, y) => canonical(x) === canonical(y);
  let res = null;
  if (a.length >= b.length && b.every((e, i) => eq(e, a[i]))) res = { ok: true, dropped: 0, appended: a.length - b.length };
  else if (a.length === cap && a.length > 0) {
    const k = b.findIndex(e => e.id === a[0].id);
    if (k > 0) { const tail = b.slice(k); if (a.length >= tail.length && tail.every((e, i) => eq(e, a[i]))) res = { ok: true, dropped: k, appended: a.length - tail.length }; }
  }
  if (!res) return { ok: false, reason: 'earlier events are not an exact prefix of the later history' };
  const ai = new Map((after.imports || []).map(i => [i.id, i]));
  for (const i of before.imports || []) { const x = ai.get(i.id); if (!x || canonical(x) !== canonical(i)) return { ok: false, reason: 'a saved import snapshot was removed or changed', dropped: res.dropped, appended: res.appended }; }
  return res;
}
// Names that exist on every object; refused as ids/units/kinds so a lookup in a plain object can never hit the prototype.
const RESERVED = new Set(Object.getOwnPropertyNames(Object.prototype));
const isReservedKey = k => typeof k === 'string' && (RESERVED.has(k) || k === '__proto__');

// A calendar date that really exists (rejects 2099-99-99, 0000-00-00, 2026-02-30).
function isRealDate(v) { if (typeof v !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(v)) return false; const y = +v.slice(0, 4), m = +v.slice(5, 7), d = +v.slice(8, 10); if (y < 1970 || m < 1 || m > 12 || d < 1) return false; return d <= new Date(Date.UTC(y, m, 0)).getUTCDate(); }

module.exports = { isReservedKey, isRealDate, canonical, digest, shortId, hmacId, clone, BridgeError, StaleWriteError, verifyHistoryPrefix };

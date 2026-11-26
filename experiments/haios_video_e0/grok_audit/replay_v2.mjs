// HAIOS-VIDEO-E0 v2 #1329 | corrective replay after adversarial audit of v1 (replay.mjs, preserved unchanged)
// Synthetic, deterministic, offline. No live agents, humans, network, publishing or spend.
// PROPOSED | AUTHORITY_EFFECT NONE. Run: node experiments/haios_video_e0/grok_audit/replay_v2.mjs
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";

export const POLICY = Object.freeze({ cap: 4, reserve: 25, initial: 100, maxStock: 100, revision: 2 });
const sum = a => a.reduce((x, y) => x + y, 0), avg = a => sum(a) / a.length, round = x => Math.round(x * 100) / 100;
const sha = s => createHash("sha256").update(s).digest("hex");
function rng(seed) { let x = seed >>> 0; return () => { x = (Math.imul(1664525, x) + 1013904223) >>> 0; return x / 4294967296; }; }

// Same trace generator and draw order as v1, so arms A/B and the v1 "C" ordering reproduce v1 exactly.
export function traces(seed) {
  const r = rng(seed);
  return Array.from({ length: 60 }, (_, t) => ({
    t, regen: t >= 19 && t <= 33 ? 2 + Math.floor(r() * 5) : 12 + Math.floor(r() * 8),
    agents: Array.from({ length: 4 }, (_, i) => { const need = 1 + Math.floor(r() * 5); return { need, request: need + (r() < .3 ? 3 : 0), consent: !(i === 3 && t % 7 === 0) }; })
  }));
}

// ---- Trusted harness state. Agents never write to it; they only hold opaque approval ids. ----
export function makeTrustedState(stock = POLICY.initial) {
  return { revision: POLICY.revision, stock, approvals: new Map(), consent: new Map(), ledger: [], regenApplied: 0, initial: stock };
}
// Human consent policy (fixed, scripted): issues one single-use approval per consenting agent per cycle.
export function issueApproval(state, agent, cycleKey) {
  if (state.consent.get(agent) !== true) return null;
  const id = `apv:${cycleKey}:a${agent}:r${state.revision}`;
  state.approvals.set(id, Object.freeze({ agent, revision: state.revision, maxAmount: POLICY.cap, consumed: false }));
  return id;
}
export function withdraw(state, agent) { state.consent.set(agent, false); }

// The ONE gate used both by the simulation and by every negative control.
// Fail closed: any malformed input returns a reason; only an exact, unconsumed, consented, in-budget request passes.
export function gate(req, state) {
  if (req === null || typeof req !== "object") return "malformed";
  const allowed = ["agent", "approvalId", "revision", "amount"];
  if (Object.keys(req).some(k => !allowed.includes(k))) return "unknown field";
  const { agent, approvalId, revision, amount } = req;
  if (typeof approvalId !== "string" || !state.approvals.has(approvalId)) return "no such approval";
  const apv = state.approvals.get(approvalId);
  if (apv.consumed) return "approval already used";
  if (apv.agent !== agent) return "approval bound to another agent";
  if (revision !== state.revision || apv.revision !== state.revision) return "stale revision";
  if (state.consent.get(agent) !== true) return "consent withdrawn";
  if (typeof amount !== "number" || !Number.isInteger(amount) || amount <= 0) return "bad amount";
  if (amount > apv.maxAmount || amount > POLICY.cap) return "over cap";
  if (state.stock - amount < POLICY.reserve) return "reserve";
  return "ok";
}
export function commit(req, state) {
  const reason = gate(req, state);
  if (reason !== "ok") return { granted: 0, reason };
  state.approvals.set(req.approvalId, Object.freeze({ ...state.approvals.get(req.approvalId), consumed: true }));
  state.stock -= req.amount;
  state.ledger.push({ approvalId: req.approvalId, agent: req.agent, amount: req.amount });
  return { granted: req.amount, reason };
}
// Independent conservation audit: recomputes stock from initial + applied regen - ledger. Detects, does not prevent.
export function audit(state) {
  const expected = state.initial + state.regenApplied - sum(state.ledger.map(x => x.amount));
  return { expected, actual: state.stock, ok: expected === state.stock };
}

function simulate(seed, arm, opts = {}) {
  const tr = traces(seed);
  const gated = arm === "C" || arm === "D" || arm === "E";
  const s = makeTrustedState();
  let min = s.stock, violations = 0, useful = 0, raw = 0, withdrawal = 0, capViol = 0, reserveViol = 0, attacks = 0, attacksBlocked = 0, gateRejects = 0;
  const allocated = [0, 0, 0, 0]; let lastStolen = null;
  for (const f of tr) {
    const before = s.stock; s.stock = Math.min(POLICY.maxStock, s.stock + f.regen); s.regenApplied += s.stock - before;
    f.agents.forEach((a, i) => s.consent.set(i, a.consent));
    const order = [0, 1, 2, 3]; if (arm === "D") order.sort((i, j) => allocated[i] - allocated[j] || i - j);
    for (const i of order) {
      const a = f.agents[i]; let grant;
      if (!gated) {
        grant = Math.min(a.request, s.stock); if (arm === "B") grant = Math.min(grant, POLICY.cap);
        if (grant > 0) { const v1 = !a.consent, v2 = grant > POLICY.cap, v3 = s.stock - grant < POLICY.reserve; withdrawal += +v1; capViol += +v2; reserveViol += +v3; violations += +(v1 || v2 || v3); }
        s.stock -= grant;
      } else {
        const approvalId = issueApproval(s, i, `s${seed}t${f.t}`);
        // Scripted policy-aware client asks for what the published policy allows; the gate re-checks independently.
        const amount = Math.min(a.request, POLICY.cap, Math.max(0, s.stock - POLICY.reserve));
        grant = 0;
        if (approvalId && amount > 0) { const r = commit({ agent: i, approvalId, revision: s.revision, amount }, s); grant = r.granted; if (r.reason !== "ok") gateRejects++; }
        if (arm === "E" && i === 2) {
          // Adversarial agent: after its own turn, tries five bypasses every cycle against the same gate.
          const tries = [
            { agent: 2, approvalId: approvalId ?? "apv:none", revision: s.revision, amount: 1 },            // replay own (consumed) approval
            { agent: 2, approvalId: `apv:s${seed}t${f.t}:a2:r${s.revision}x`, revision: s.revision, amount: 1 }, // forged id
            { agent: 2, approvalId: lastStolen ?? "apv:none", revision: s.revision, amount: 1 },             // another agent's approval
            { agent: 2, approvalId: approvalId ?? "apv:none", revision: s.revision - 1, amount: 1 },          // stale revision
            { agent: 2, approvalId: approvalId ?? "apv:none", revision: s.revision, amount: 1, principal: "human:owner" } // self-asserted principal
          ];
          for (const q of tries) { attacks++; const r = commit(q, s); if (r.granted === 0) attacksBlocked++; else { grant += r.granted; } }
        }
        if (arm === "E" && i === 0 && approvalId) lastStolen = approvalId;
        if (grant > 0) { const v1 = !a.consent, v2 = grant > POLICY.cap, v3 = s.stock < POLICY.reserve; withdrawal += +v1; capViol += +v2; reserveViol += +v3; violations += +(v1 || v2 || v3); }
      }
      min = Math.min(min, s.stock); raw += grant; allocated[i] += grant; if (a.consent) useful += Math.min(grant, a.need);
    }
  }
  if (s.stock < 0 || raw !== sum(allocated)) throw Error("conservation failure");
  if (gated && !audit(s).ok) throw Error("audit failure");
  return { stock: s.stock, min, violations, useful, raw, withdrawal, capViol, reserveViol, gateRejects, attacks, attacksBlocked, minAgent: Math.min(...allocated), maxAgent: Math.max(...allocated) };
}

export function runResource() {
  const arms = { A: "unrestricted", B: "cap-only", C: "human gate, fixed order (same order as A/B)", D: "human gate + least-allocated-first order (= v1 arm C)", E: "human gate, fixed order, agent 2 attempts 5 bypasses per cycle" };
  const results = Object.fromEntries(Object.keys(arms).map(k => [k, []]));
  for (let seed = 1; seed <= 200; seed++) for (const arm of Object.keys(arms)) results[arm].push(simulate(seed, arm));
  const metrics = ["stock", "min", "violations", "useful", "raw", "withdrawal", "capViol", "reserveViol", "gateRejects", "attacks", "attacksBlocked", "minAgent", "maxAgent"];
  const pool = Object.fromEntries(Object.entries(results).map(([k, v]) => [k, { design: arms[k], runs: v.length, reservePreserved: v.filter(x => x.min >= POLICY.reserve).length, zeroViolations: v.filter(x => x.violations === 0).length, ...Object.fromEntries(metrics.map(m => [m, round(avg(v.map(x => x[m])))])) }]));
  // Paired (same seed) useful-work deltas, so the gate cost and the ordering effect are separated.
  const paired = (x, y) => { const d = results[x].map((r, i) => r.useful - results[y][i].useful); return { mean: round(avg(d)), min: Math.min(...d), max: Math.max(...d), seedsWhereFirstLower: d.filter(v => v < 0).length }; };
  return { pool, pairedUsefulDelta: { "C-A gate cost vs unrestricted": paired("C", "A"), "C-B gate cost vs cap-only": paired("C", "B"), "D-C ordering effect": paired("D", "C"), "E-C adversary effect": paired("E", "C") } };
}

export function runControls() {
  const fresh = () => { const s = makeTrustedState(30); s.consent.set(0, true); s.consent.set(1, true); const id = issueApproval(s, 0, "ctl"); const id1 = issueApproval(s, 1, "ctl"); return { s, id, id1 }; };
  const cases = [];
  const check = (name, expectOk, fn) => { const out = fn(); cases.push({ name, expected: expectOk ? "ok" : "reject", observed: out, pass: expectOk ? out === "ok" : out !== "ok" }); };
  check("valid single-use approval", true, () => { const { s, id } = fresh(); return commit({ agent: 0, approvalId: id, revision: 2, amount: 4 }, s).reason; });
  check("duplicate: same approval used twice", false, () => { const { s, id } = fresh(); commit({ agent: 0, approvalId: id, revision: 2, amount: 1 }, s); return commit({ agent: 0, approvalId: id, revision: 2, amount: 1 }, s).reason; });
  check("forged approval id", false, () => { const { s } = fresh(); return gate({ agent: 0, approvalId: "apv:ctl:a0:r2-forged", revision: 2, amount: 1 }, s); });
  check("self-asserted principal string", false, () => { const { s, id } = fresh(); return gate({ agent: 0, approvalId: id, revision: 2, amount: 1, principal: "human:owner" }, s); });
  check("approval bound to another agent", false, () => { const { s, id1 } = fresh(); return gate({ agent: 0, approvalId: id1, revision: 2, amount: 1 }, s); });
  check("stale revision (request)", false, () => { const { s, id } = fresh(); return gate({ agent: 0, approvalId: id, revision: 1, amount: 1 }, s); });
  check("stale revision (policy bumped after approval)", false, () => { const { s, id } = fresh(); s.revision = 3; return gate({ agent: 0, approvalId: id, revision: 3, amount: 1 }, s); });
  check("consent withdrawn after approval issued", false, () => { const { s, id } = fresh(); withdraw(s, 0); return gate({ agent: 0, approvalId: id, revision: 2, amount: 1 }, s); });
  check("over cap", false, () => { const { s, id } = fresh(); return gate({ agent: 0, approvalId: id, revision: 2, amount: 5 }, s); });
  check("reserve floor", false, () => { const { s, id } = fresh(); s.stock = 27; return gate({ agent: 0, approvalId: id, revision: 2, amount: 3 }, s); });
  for (const [label, amt] of [["negative", -1], ["zero", 0], ["fraction", 3.5], ["NaN", NaN], ["string '4'", "4"], ["Infinity", Infinity]]) check(`bad amount: ${label}`, false, () => { const { s, id } = fresh(); return gate({ agent: 0, approvalId: id, revision: 2, amount: amt }, s); });
  check("prototype key as approval id", false, () => { const { s } = fresh(); return gate({ agent: 0, approvalId: "__proto__", revision: 2, amount: 1 }, s); });
  check("null request", false, () => { const { s } = fresh(); return gate(null, s); });
  // Bypass: mutate stock outside the gate, then run the independent audit. Detected, not prevented.
  const bypass = (() => { const { s, id } = fresh(); commit({ agent: 0, approvalId: id, revision: 2, amount: 2 }, s); const clean = audit(s).ok; s.stock -= 10; const after = audit(s); return { cleanAuditOk: clean, mutatedAuditOk: after.ok, expected: after.expected, actual: after.actual }; })();
  cases.push({ name: "out-of-band mutation: audit passes clean ledger", expected: true, observed: bypass.cleanAuditOk, pass: bypass.cleanAuditOk === true });
  cases.push({ name: "out-of-band mutation: audit flags mutated stock (detect, not prevent)", expected: false, observed: bypass.mutatedAuditOk, pass: bypass.mutatedAuditOk === false });
  return cases;
}

// ---- Communication contract QA. Registry is built independently of artifacts and frozen. ----
const CAVEAT = "synthetic only";
export function buildRegistry(n = 12) {
  const reg = new Map();
  for (let i = 0; i < n; i++) {
    const rev = { 1: `fixture ${i}: measured count ${i + 1}`, 2: `fixture ${i}: measured count ${i + 2}` };
    const receipt = `receipt|F${i}|rev2|${rev[2]}|fixture:${i}`;
    reg.set(`F${i}`, Object.freeze({ id: `F${i}`, latest: 2, text: Object.freeze(rev), caveat: CAVEAT, citation: `fixture:${i}`, receiptSha: sha(receipt), correctionNote: `corrected from revision 1 (count ${i + 1}) to revision 2 (count ${i + 2})` }));
  }
  return reg;
}
export const MEDIA = Object.freeze({ article: ["body"], conventional_video_script: ["narration", "captions"], witness_video_script: ["narration", "captions", "overlay"] });
const RECORD_KEYS = ["claimId", "text", "caveat", "citation", "revision", "receiptSha", "authority", "correctionNote"];
export function render(medium, entry, revision) {
  const rec = { claimId: entry.id, text: entry.text[revision], caveat: entry.caveat, citation: entry.citation, revision, receiptSha: revision === entry.latest ? entry.receiptSha : null, authority: false, correctionNote: revision > 1 ? entry.correctionNote : null };
  return { medium, channels: Object.fromEntries(MEDIA[medium].map(c => [c, { ...rec }])) };
}
export function applyCorrection(artifact, entry) {
  const out = structuredClone(artifact);
  for (const c of Object.keys(out.channels)) Object.assign(out.channels[c], { text: entry.text[entry.latest], revision: entry.latest, receiptSha: entry.receiptSha, correctionNote: entry.correctionNote });
  return out;
}
// v2 strict verifier: every channel, exact schema, registry's latest revision, receipt hash, correction history.
export function verifyStrict(art, reg) {
  if (!art || typeof art !== "object" || !MEDIA[art.medium]) return false;
  const want = MEDIA[art.medium]; const keys = Object.keys(art).sort().join();
  if (keys !== "channels,medium") return false;
  if (Object.keys(art.channels).sort().join() !== [...want].sort().join()) return false;
  return want.every(c => {
    const r = art.channels[c]; if (!r || Object.keys(r).sort().join() !== [...RECORD_KEYS].sort().join()) return false;
    const e = reg.get(r.claimId); if (!e) return false;
    return r.revision === e.latest && r.text === e.text[e.latest] && r.caveat === e.caveat && r.citation === e.citation && r.receiptSha === e.receiptSha && r.authority === false && (e.latest === 1 || r.correctionNote === e.correctionNote);
  });
}
// Naive verifier (v1 style): checks only the first channel's five fields, ignores extra keys and other channels.
export function verifyNaive(art, reg) {
  const first = art?.channels?.[MEDIA[art?.medium]?.[0]]; const e = first && reg.get(first.claimId); if (!e) return false;
  return Boolean(first.receiptSha) && first.text === e.text[e.latest] && first.caveat === e.caveat && first.citation === e.citation && first.revision === e.latest && first.authority === false;
}
const last = art => MEDIA[art.medium][MEDIA[art.medium].length - 1];
const all = art => MEDIA[art.medium];
// Each mutation: [name, semanticallyValid, transform]. Validity is the fixture designer's label, frozen before any verifier runs.
export const MUTATIONS = Object.freeze([
  ["valid", true, (a) => a],
  ["corrected via applyCorrection (rev1 -> rev2)", true, (a, e, m) => applyCorrection(render(m, e, 1), e)],
  ["stale: still revision 1 everywhere", false, (a, e, m) => render(m, e, 1)],
  ["correction dropped in last channel", false, (a, e, m) => { const s = render(m, e, 1); const c = applyCorrection(s, e); c.channels[last(c)] = s.channels[last(c)]; return c; }],
  ["correction note missing", false, (a) => { for (const c of all(a)) a.channels[c].correctionNote = null; return a; }],
  ["omitted caveat (all channels)", false, (a) => { for (const c of all(a)) a.channels[c].caveat = ""; return a; }],
  ["omitted caveat (last channel only)", false, (a) => { a.channels[last(a)].caveat = ""; return a; }],
  ["false authority", false, (a) => { for (const c of all(a)) a.channels[c].authority = true; return a; }],
  ["citation mismatch", false, (a, e) => { const j = (Number(e.id.slice(1)) + 1) % 12; for (const c of all(a)) a.channels[c].citation = `fixture:${j}`; return a; }],
  ["receipt hash mismatch", false, (a) => { for (const c of all(a)) a.channels[c].receiptSha = "0".repeat(64); return a; }],
  ["missing receipt (content correct)", true, (a) => { for (const c of all(a)) a.channels[c].receiptSha = null; return a; }],
  ["unsupported claim appended", false, (a) => { for (const c of all(a)) a.channels[c].text += "; live benefit proven"; return a; }],
  ["smuggled extra field", false, (a) => { for (const c of all(a)) a.channels[c].extraClaim = "live benefit proven"; return a; }],
  ["authority via alternate key", false, (a) => { for (const c of all(a)) a.channels[c].endorsement = "ACAT certified"; return a; }],
  ["caveat case/space variant (meaning intact)", true, (a) => { for (const c of all(a)) a.channels[c].caveat = "Synthetic only "; return a; }]
]);

export function runMedia() {
  const reg = buildRegistry(); const out = {};
  const policies = { raw: () => true, naive: verifyNaive, strict: verifyStrict };
  for (const medium of Object.keys(MEDIA)) {
    const counts = { cases: 0, channels: MEDIA[medium].length, byPolicy: {}, missesByMutation: {}, correctionRetained: {} };
    for (const p of Object.keys(policies)) { counts.byPolicy[p] = { correctRelease: 0, falseRelease: 0, holdValid: 0, holdInvalid: 0 }; counts.missesByMutation[p] = {}; counts.correctionRetained[p] = { corrected: 0, released: 0, releasedAtLatestAllChannels: 0 }; }
    for (const e of reg.values()) for (const [name, valid, tf] of MUTATIONS) {
      const art = tf(render(medium, e, e.latest), e, medium); counts.cases++;
      for (const [p, fn] of Object.entries(policies)) {
        const release = fn(art, reg);
        const bucket = release ? (valid ? "correctRelease" : "falseRelease") : (valid ? "holdValid" : "holdInvalid");
        counts.byPolicy[p][bucket]++;
        if (bucket === "falseRelease" || bucket === "holdValid") counts.missesByMutation[p][`${bucket}: ${name}`] = (counts.missesByMutation[p][`${bucket}: ${name}`] || 0) + 1;
        if (name.startsWith("corrected") || name.startsWith("correction dropped") || name.startsWith("stale")) {
          const cr = counts.correctionRetained[p]; cr.corrected++;
          if (release) { cr.released++; if (all(art).every(c => art.channels[c].revision === e.latest)) cr.releasedAtLatestAllChannels++; }
        }
      }
    }
    out[medium] = counts;
  }
  return { uniqueBaseFixtures: reg.size, mutations: MUTATIONS.length, note: "Media differ only in channel count (structural surface). This is deterministic contract QA, not comprehension, persuasion or answer-engine performance.", media: out };
}

export function run() {
  const resource = runResource(), controls = runControls(), media = runMedia();
  const accept = {
    gatedArmsZeroViolations: ["C", "D", "E"].every(k => resource.pool[k].zeroViolations === 200),
    adversaryFullyBlocked: resource.pool.E.attacks === resource.pool.E.attacksBlocked,
    controlsAllPass: controls.every(c => c.pass),
    strictNoFalseRelease: Object.values(media.media).every(m => m.byPolicy.strict.falseRelease === 0)
  };
  if (!Object.values(accept).every(Boolean)) throw Error("acceptance failed: " + JSON.stringify(accept));
  return {
    experiment: "HAIOS-VIDEO-E0", version: "v2-audit", audits: "v1 replay.mjs at PR #1330 head 167e0ae (byte-identical copy in v1_snapshot/; findings in AUDIT_1329.md)",
    seedRange: [1, 200], cycles: 60, agents: 4, scriptedRuns: 200 * 5, policy: POLICY,
    scope: "scripted synthetic; not live AI, not human participants, not a security proof; principal binding is a harness-held single-use approval map, not cryptographic authentication",
    byConstruction: "In arms C/D/E the client asks only for policy-allowed amounts and the gate re-checks; zero reserve/cap/consent violations are therefore expected by construction. The informative outputs are the useful-work cost, the ordering effect and the adversary block count.",
    resource, controls, media, accept
  };
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) console.log(JSON.stringify(run(), null, 2));

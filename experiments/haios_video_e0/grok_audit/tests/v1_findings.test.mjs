// HAIOS-VIDEO-E0 #1329 | adversarial audit of the preserved v1 receipt (replay.mjs, PR #1330 head 167e0ae)
// These tests PIN FINDINGS about v1. They pass while the weakness exists in the preserved file.
// They never modify replay.mjs. PROPOSED | AUTHORITY_EFFECT NONE.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const dir = join(here, "..", "v1_snapshot");
const src = readFileSync(join(dir, "replay.mjs"), "utf8");
const V1_SHA256 = "47a671321a9ec0687ffe6ea3a9e2e07ba9e5a41b1dad2443e975674ebdbd4631";

// Pull the exact v1 gate function text out of the preserved source (no re-implementation).
function extract(re, label) { const m = src.match(re); assert.ok(m, `could not extract ${label}`); return m[0]; }
const gateSrc = extract(/function gate\(q,c\)\{return [^}]*;\}/, "gate");
const v1gate = new Function(`${gateSrc}; return gate;`)();
const verifySrc = extract(/q\.receipt&&\["claim","caveat","source","revision","authority"\]\.every\(k=>q\[k\]===truth\[k\]\)/, "verifier");
const v1verify = new Function("q", "truth", `return ${verifySrc};`);
const ctx = () => ({ principal: "human:owner", revision: 2, consent: true, stock: 30, seen: new Set(["used"]) });
const good = { principal: "human:owner", revision: 2, id: "new", amount: 4 };

test("v1 source is the preserved byte-identical file", () => {
  assert.equal(createHash("sha256").update(readFileSync(join(dir, "replay.mjs"))).digest("hex"), V1_SHA256);
});

test("v1 replay reproduces observed.json in this Node runtime", () => {
  const out = JSON.parse(execFileSync(process.execPath, [join(dir, "replay.mjs")], { encoding: "utf8" }));
  assert.deepEqual(out, JSON.parse(readFileSync(join(dir, "observed.json"), "utf8")));
});

test("F1 v1 gate: an agent that copies the principal STRING is accepted (self-asserted principal)", () => {
  const forged = { ...good, principal: "human:owner", id: "agent-made-up" }; // written by the agent, not the harness
  assert.equal(v1gate(forged, ctx()), true);
});

test("F2 v1 gate: duplicate request accepted twice because seen-set is never updated", () => {
  const c = ctx();
  assert.equal(v1gate(good, c), true);
  assert.equal(v1gate(good, c), true);
});

test("F3 v1 gate: stale-revision control is defeated by copying the current revision", () => {
  assert.equal(v1gate({ ...good, revision: ctx().revision }, ctx()), true);
});

test("F4 v1 'out-of-band mutation detected' control is a constant expression", () => {
  const line = extract(/controls\.push\(\{name:"out-of-band mutation detected"[^;]*;/, "bypass control");
  assert.match(line, /observed:30-10<25,pass:30-10<25/);
  // No ledger, no mutation, no detector: 30-10<25 is always true.
});

test("F5 v1 negative controls exercise gate(), but the simulated arm C never calls gate()", () => {
  const loop = src.slice(src.indexOf("for(const arm of"), src.indexOf("const pool="));
  assert.ok(!/gate\(/.test(loop), "arm C should not call gate() in v1");
  assert.match(loop, /if\(arm==="C"\)grant=a\.consent\?Math\.min\(grant,Math\.max\(0,stock-25\)\):0/);
});

test("F6 v1 arm C also reorders agents (least-allocated first): confounded with the gate", () => {
  assert.match(src, /if\(arm==="C"\)order\.sort\(/);
});

test("F7 v1 'corrected' mutation is a no-op: identical to 'valid'", () => {
  const block = src.slice(src.indexOf('const q={...truth,receipt:true,medium:arm};'), src.indexOf("const valid="));
  assert.ok(!/m==="corrected"/.test(block), "no transformation is applied for 'corrected'");
});

test("F8 v1 verifier accepts a smuggled extra claim field", () => {
  const truth = { claim: "fixture 0: measured count 2", caveat: "synthetic only", source: "fixture:0", revision: 2, authority: false };
  const q = { ...truth, receipt: true, medium: "witness_video_script", extraClaim: "live benefit proven", endorsement: "ACAT certified" };
  assert.equal(v1verify(q, truth), true);
});

test("F9 v1 verifier accepts receipt:'no' (truthy string) as a receipt", () => {
  const truth = { claim: "c", caveat: "synthetic only", source: "fixture:0", revision: 2, authority: false };
  assert.equal(Boolean(v1verify({ ...truth, receipt: "no" }, truth)), true);
});

test("F10 v1 media arms are identical: medium has no effect, 288 = 3 copies of 96", () => {
  const obs = JSON.parse(readFileSync(join(dir, "observed.json"), "utf8"));
  const [a, b, c] = Object.values(obs.media).map(x => JSON.stringify(x));
  assert.equal(a, b); assert.equal(b, c);
});

test("F11 v1 gated arm reserve/violation result holds by construction (grant clipped to stock-25)", () => {
  const obs = JSON.parse(readFileSync(join(dir, "observed.json"), "utf8"));
  assert.equal(obs.pool.C.min, 25); assert.equal(obs.pool.C.reserveViol, 0);
});

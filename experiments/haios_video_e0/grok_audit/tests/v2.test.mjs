// HAIOS-VIDEO-E0 v2 #1329 | replay, adversarial and adapter tests. PROPOSED | AUTHORITY_EFFECT NONE.
import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, mkdtempSync, writeFileSync, readdirSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import * as v2 from "../replay_v2.mjs";
import { validate, build } from "../adapter.mjs";

const dir = join(dirname(fileURLToPath(import.meta.url)), "..");
const json = f => JSON.parse(readFileSync(join(dir, f), "utf8"));

test("v2 replay (fresh process) reproduces observed_v2.json exactly", () => {
  const out = JSON.parse(execFileSync(process.execPath, [join(dir, "replay_v2.mjs")], { encoding: "utf8" }));
  assert.deepEqual(out, json("observed_v2.json"));
});

test("v2 arms A/B equal v1 A/B, and v2 arm D equals v1 arm C (same traces, cross-implementation check)", () => {
  const v1 = json("v1_snapshot/observed.json").pool, p = json("observed_v2.json").resource.pool;
  for (const [a, b] of [["A", "A"], ["B", "B"], ["C", "D"]]) for (const k of Object.keys(v1[a])) assert.equal(p[b][k], v1[a][k], `${a}->${b} ${k}`);
});

test("every negative control passes and is computed, not constant", () => {
  const c = v2.runControls();
  assert.ok(c.length >= 20); assert.ok(c.every(x => x.pass), JSON.stringify(c.filter(x => !x.pass)));
  assert.ok(c.some(x => x.observed === true) && c.some(x => x.observed === false));
});

test("gate: the v1 forgeries (copied principal string, duplicate replay) now fail", () => {
  const s = v2.makeTrustedState(30); s.consent.set(0, true);
  const id = v2.issueApproval(s, 0, "t");
  assert.equal(v2.gate({ agent: 0, approvalId: id, revision: 2, amount: 1, principal: "human:owner" }, s), "unknown field");
  assert.equal(v2.commit({ agent: 0, approvalId: id, revision: 2, amount: 1 }, s).reason, "ok");
  assert.equal(v2.commit({ agent: 0, approvalId: id, revision: 2, amount: 1 }, s).reason, "approval already used");
  assert.equal(v2.audit(s).ok, true);
});

test("gate: no approval is issued without consent", () => {
  const s = v2.makeTrustedState(30); s.consent.set(1, false);
  assert.equal(v2.issueApproval(s, 1, "t"), null);
});

test("adversary arm: every bypass attempt blocked; useful work identical to arm C", () => {
  const { pool, pairedUsefulDelta } = json("observed_v2.json").resource;
  assert.equal(pool.E.attacks, pool.E.attacksBlocked); assert.ok(pool.E.attacks > 0);
  assert.deepEqual(pairedUsefulDelta["E-C adversary effect"], { mean: 0, min: 0, max: 0, seedsWhereFirstLower: 0 });
});

test("strict verifier: zero false releases; valid-but-held cases are disclosed, not hidden", () => {
  for (const m of Object.values(json("observed_v2.json").media.media)) {
    assert.equal(m.byPolicy.strict.falseRelease, 0);
    assert.equal(m.byPolicy.strict.holdValid, 24);
    const total = Object.values(m.byPolicy.strict).reduce((a, b) => a + b, 0); assert.equal(total, m.cases);
  }
});

test("naive single-channel verifier misses more in multi-channel media (structural, not comprehension)", () => {
  const md = json("observed_v2.json").media.media;
  assert.ok(md.conventional_video_script.byPolicy.naive.falseRelease > md.article.byPolicy.naive.falseRelease);
});

test("correction is a real transform: rev1 artifact differs from corrected artifact, which equals a fresh rev2 render", () => {
  const reg = v2.buildRegistry(); const e = reg.get("F3");
  const stale = v2.render("witness_video_script", e, 1), fixed = v2.applyCorrection(stale, e), fresh = v2.render("witness_video_script", e, 2);
  assert.notDeepEqual(stale, fixed); assert.deepEqual(fixed, fresh);
  assert.equal(v2.verifyStrict(stale, reg), false); assert.equal(v2.verifyStrict(fixed, reg), true);
});

test("registry is frozen and independent of artifacts", () => {
  const reg = v2.buildRegistry(); const e = reg.get("F0");
  const art = v2.render("article", e, 2); art.channels.body.text = "tampered";
  assert.notEqual(reg.get("F0").text[2], "tampered");
  assert.throws(() => { "use strict"; e.text[2] = "x"; });
});

test("strict verifier rejects unknown medium, extra channel, missing channel and unknown claim id", () => {
  const reg = v2.buildRegistry(); const e = reg.get("F1");
  const a = v2.render("conventional_video_script", e, 2);
  assert.equal(v2.verifyStrict({ ...a, medium: "podcast" }, reg), false);
  assert.equal(v2.verifyStrict({ ...a, channels: { ...a.channels, overlay: a.channels.narration } }, reg), false);
  const { captions, ...rest } = a.channels; assert.equal(v2.verifyStrict({ ...a, channels: rest }, reg), false);
  assert.equal(v2.verifyStrict({ ...a, channels: { narration: { ...a.channels.narration, claimId: "F99" }, captions } }, reg), false);
  assert.equal(v2.verifyStrict({ ...a, extra: 1 }, reg), false);
});

test("adapter: the episode manifest validates and every observed number matches observed_v2.json", () => {
  const r = build(join(dir, "episode_01_manifest.json"));
  assert.equal(r.ok, true, JSON.stringify(r.problems)); assert.match(r.release, /HOLD/);
});

test("adapter: fails closed on wrong numbers, banned wording, self-approval, publish flags and path escape", () => {
  const base = json("episode_01_manifest.json");
  const bad = structuredClone(base);
  bad.claims[2].evidence.pointers[0].value = 600.0; bad.claims[2].text = bad.claims[2].text.replace("591.98", "600");
  bad.claims[6].text += " This is proven."; bad.claims[0].humanDecision = "RELEASE";
  bad.release = { state: "RELEASE", autoPublish: true }; bad.claims[1].evidence.file = "../../../etc/passwd";
  bad.segments[0].narration = "As a human presenter, I can confirm this.";
  const p = validate(bad, dir).join("\n");
  for (const want of ["pointer resource.pool.C.useful is 591.98", "banned wording", "humanDecision must be HOLD", "release.state must be HOLD", "autoPublish must be false", "escapes the experiment directory", "segment 0: banned wording"]) assert.ok(p.includes(want), `missing: ${want}\n${p}`);
});

test("adapter: writes only to the given local directory and escapes HTML", () => {
  const out = mkdtempSync(join(tmpdir(), "e0-adapter-"));
  const m = json("episode_01_manifest.json"); m.title = "<script>alert(1)</script> test";
  const mp = join(dir, ".tmp_manifest.test.json"); writeFileSync(mp, JSON.stringify(m));
  try {
    const r = build(mp, out); assert.equal(r.ok, true, JSON.stringify(r.problems));
    assert.deepEqual(readdirSync(out).sort(), ["captions.vtt", "claim_manifest.json", "correction_history.json", "transcript.html"]);
    const html = readFileSync(join(out, "transcript.html"), "utf8");
    assert.ok(!html.includes("<script>alert(1)"), "title must be escaped");
    assert.match(html, /"uploadDate":null/);
  } finally { execFileSync("rm", ["-f", mp]); }
});

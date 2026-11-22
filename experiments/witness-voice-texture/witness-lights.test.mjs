import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { encodeTextureFrame, STATES } from "./texture-encoder.mjs";
import {
  LIGHT_ORDER, projectLights, askWitness, DEMO_QUESTIONS, DEMO_RECORDS, NO_RECORD
} from "./witness-lights.mjs";

const links = {
  CONVERGENCE: ["supports", "supports"], DIVERGENCE: ["supports", "contradicts"],
  OMISSION: ["supports", "missing"], ANOMALY: ["supports", "anomaly"],
  UNRESOLVED: ["supports", "unresolved"], CORRECTION: ["supports", "supersedes"]
};
function viewFor(state) {
  return encodeTextureFrame({
    schema_version: "witness-texture-demo/0.1", frame_id: "DEMO-FRAME-1",
    source_event_id: "DEMO-EVENT-1", source_kind: "synthetic_fixture", state,
    is_synthetic: true, authority_effect: "NONE", can_ratify: false,
    summary: "Invented paths for " + state + ".", visual_seed: 7,
    paths: links[state].map((relation, i) => ({
      id: "DEMO-PATH-" + i, relation, source_group: "DEMO-SOURCE-" + i,
      evidence_refs: ["DEMO-EVIDENCE-" + i]
    }))
  });
}

test("six lights, one per channel, fixed order", () => {
  assert.equal(LIGHT_ORDER.length, 6);
  assert.deepEqual([...LIGHT_ORDER], [...STATES]);
});

test("exactly one light is lit and it matches the validated channel", () => {
  for (const state of STATES) {
    const lights = projectLights(viewFor(state));
    assert.equal(lights.length, 6);
    assert.deepEqual(lights.filter((l) => l.lit).map((l) => l.channel), [state]);
  }
});

test("same frame yields identical lights on repeat runs", () => {
  assert.deepEqual(projectLights(viewFor("DIVERGENCE")), projectLights(viewFor("DIVERGENCE")));
});

test("lights refuse anything that is not a validated synthetic no-authority view", () => {
  const good = viewFor("OMISSION");
  assert.throws(() => projectLights(null), TypeError);
  assert.throws(() => projectLights({ channel: "OMISSION" }), TypeError);
  assert.throws(() => projectLights({ ...good, channel: "PLEASED" }), TypeError);
  assert.throws(() => projectLights({ ...good, authorityEffect: "RATIFY" }), TypeError);
  assert.throws(() => projectLights({ ...good, canRatify: true }), TypeError);
  assert.throws(() => projectLights({ ...good, isSynthetic: false }), TypeError);
});

test("an answered question names its record and receipt", () => {
  const a = askWitness("DEMO-Q-DECISION");
  assert.equal(a.answered, true);
  assert.match(a.recordId, /^DEMO-REC-/);
  assert.match(a.receipt, /^DEMO-HASH-/);
  assert.equal(a.authorityEffect, "NONE");
  assert.equal(a.canRatify, false);
});

test("no matching record gives exactly 'No record.' and no claim", () => {
  for (const id of ["DEMO-Q-FEELING", "DEMO-Q-UNKNOWN", "", undefined, null, 42]) {
    const a = askWitness(id);
    assert.equal(a.answered, false);
    assert.equal(a.text, NO_RECORD);
    assert.equal(a.recordId, null);
    assert.equal(a.receipt, null);
  }
});

test("every answer is either 'No record.' or carries a receipt", () => {
  for (const q of DEMO_QUESTIONS) {
    const a = askWitness(q.id);
    assert.ok(a.text === NO_RECORD || (a.recordId && a.receipt));
  }
});

test("no fixture text claims feeling, belief, desire or consciousness in the first person", () => {
  const banned = /\b(I|we|my|me)\b.*\b(feel|felt|believe|want|wish|conscious|aware|alive|sentient)\b/i;
  for (const r of DEMO_RECORDS) assert.doesNotMatch(r.text, banned);
  assert.doesNotMatch(NO_RECORD, banned);
});

test("module has no network, storage, audio, timer or authority primitives", () => {
  const src = readFileSync(new URL("./witness-lights.mjs", import.meta.url), "utf8");
  for (const word of ["fetch(", "XMLHttpRequest", "localStorage", "sessionStorage",
    "AudioContext", "navigator.", "WebSocket", "eval(", "process.env", "node:fs", "node:child_process"]) {
    assert.ok(!src.includes(word), "must not use " + word);
  }
});

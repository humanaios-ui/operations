import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { encodeTextureFrame, STATES } from "./texture-encoder.mjs";

const links = {
  CONVERGENCE: ["supports", "supports"],
  DIVERGENCE: ["supports", "contradicts"],
  OMISSION: ["supports", "missing"],
  ANOMALY: ["supports", "anomaly"],
  UNRESOLVED: ["supports", "unresolved"],
  CORRECTION: ["supports", "supersedes"]
};
function fixture(state = "CONVERGENCE") {
  return {
    schema_version: "witness-texture-demo/0.1",
    frame_id: "DEMO-FRAME-1", source_event_id: "DEMO-EVENT-1",
    source_kind: "synthetic_fixture",
    state, is_synthetic: true, authority_effect: "NONE", can_ratify: false,
    summary: "Two invented evidence paths demonstrate " + state + ".",
    visual_seed: 72913,
    paths: links[state].map((relation, index) => ({
      id: "DEMO-PATH-" + index, relation,
      source_group: "DEMO-SOURCE-" + index,
      evidence_refs: ["DEMO-EVIDENCE-" + index]
    }))
  };
}

test("all six channels have deterministic, bounded synthetic projections", () => {
  for (const state of STATES) {
    const input = fixture(state);
    const before = JSON.stringify(input);
    const first = encodeTextureFrame(input);
    assert.deepEqual(first, encodeTextureFrame(input));
    assert.equal(JSON.stringify(input), before, "encoder must not mutate source event");
    assert.equal(first.channel, state);
    assert.equal(first.isSynthetic, true);
    assert.equal(first.authorityEffect, "NONE");
    assert.equal(first.canRatify, false);
    assert.ok(first.points.length > 0 && first.points.length <= 320);
    for (const point of first.points) {
      assert.ok(Number.isFinite(point.x) && point.x >= 0 && point.x <= 1);
      assert.ok(Number.isFinite(point.y) && point.y >= 0 && point.y <= 1);
    }
  }
});

test("reject real data, authority promotion, hidden fields, and hostile sizes", () => {
  const source = fixture();
  for (const patch of [
    { is_synthetic: false }, { source_kind: "graph_event" },
    { authority_effect: "RATIFY" }, { can_ratify: true },
    { frame_id: "production-id" }, { unexpected_claim: "trusted" },
    { visual_seed: Number.POSITIVE_INFINITY }, { visual_seed: -1 },
    { summary: "" }, { paths: [] },
    { paths: Array(9).fill(source.paths[0]) }
  ]) {
    assert.throws(() => encodeTextureFrame({ ...source, ...patch }));
  }
});

test("reject missing expected relationships instead of inventing graph interpretations", () => {
  for (const state of STATES) {
    const source = fixture(state);
    const wrong = {
      ...source,
      paths: source.paths.map((path) => ({ ...path, relation: "supports" }))
    };
    if (state !== "CONVERGENCE") assert.throws(() => encodeTextureFrame(wrong));
  }
  assert.throws(() => encodeTextureFrame({ ...fixture("CONVERGENCE"), state: "TRUTH" }));
  const bad = fixture();
  bad.paths[1].source_group = "unverified-provider";
  assert.throws(() => encodeTextureFrame(bad));
  const duplicate = fixture();
  duplicate.paths[1].id = duplicate.paths[0].id;
  assert.throws(() => encodeTextureFrame(duplicate));
});

test("omissions require declared missing relationship; no silent data gaps", () => {
  const om = encodeTextureFrame(fixture("OMISSION"));
  assert.ok(om.points.length < encodeTextureFrame(fixture("DIVERGENCE")).points.length);
  assert.equal(om.paths.some((p) => p.relation === "missing"), true);
});

test("schema has non-authority and synthetic-only guardrails", () => {
  const schema = JSON.parse(readFileSync(
    new URL("./WITNESS_TEXTURE_FRAME_V0_1.schema.json", import.meta.url), "utf8"
  ));
  assert.equal(schema.additionalProperties, false);
  assert.equal(schema.properties.is_synthetic.const, true);
  assert.equal(schema.properties.can_ratify.const, false);
  assert.equal(schema.properties.authority_effect.const, "NONE");
  assert.equal(schema.properties.source_kind.const, "synthetic_fixture");
  assert.deepEqual(schema.properties.state.enum, STATES);
});

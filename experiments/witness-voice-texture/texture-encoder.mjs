// Z1 experiment only: deterministic display projection, never an evidence interpreter.
// Source contracts: WITNESS_ARENA_PROTOCOL_V0_1 and HARMONIC_CHANNEL_SPEC_V0_1.
// No network requests, authority actions, telemetry, browser storage, or third-party packages.

export const STATES = Object.freeze([
  "CONVERGENCE", "DIVERGENCE", "OMISSION", "ANOMALY", "UNRESOLVED", "CORRECTION"
]);

const RELATIONS = new Set(["supports", "contradicts", "missing", "anomaly", "unresolved", "supersedes"]);
const FRAME_FIELDS = new Set([
  "schema_version", "frame_id", "source_event_id", "source_kind",
  "state", "is_synthetic", "authority_effect", "can_ratify",
  "summary", "visual_seed", "paths"
]);
const PATH_FIELDS = new Set(["id", "relation", "source_group", "evidence_refs"]);
const DEMO_ID = /^DEMO-[A-Z0-9_-]{1,59}$/;

function requirePlainObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value) ||
      Object.getPrototypeOf(value) !== Object.prototype) {
    throw new TypeError(label + " must be a plain object");
  }
}
function assertKeys(value, allowed, label) {
  for (const key of Object.keys(value)) {
    if (!allowed.has(key)) throw new TypeError(label + " has unexpected field: " + key);
  }
}
function requireDemoId(value, label) {
  if (typeof value !== "string" || !DEMO_ID.test(value)) {
    throw new TypeError(label + " must be a DEMO-prefixed identifier");
  }
}
function bounded(value) {
  return Math.max(0.06, Math.min(0.94, value));
}
function semanticPairIsValid(frame) {
  const relations = new Set(frame.paths.map((path) => path.relation));
  if (frame.state === "CONVERGENCE") return frame.paths.every((p) => p.relation === "supports");
  if (frame.state === "DIVERGENCE") return relations.has("supports") && relations.has("contradicts");
  if (frame.state === "OMISSION") return relations.has("missing");
  if (frame.state === "ANOMALY") return relations.has("anomaly");
  if (frame.state === "UNRESOLVED") return relations.has("unresolved");
  if (frame.state === "CORRECTION") return relations.has("supersedes");
  return false;
}

export function encodeTextureFrame(frame) {
  requirePlainObject(frame, "frame");
  assertKeys(frame, FRAME_FIELDS, "frame");
  if (frame.schema_version !== "witness-texture-demo/0.1" ||
      frame.source_kind !== "synthetic_fixture" ||
      frame.is_synthetic !== true ||
      frame.authority_effect !== "NONE" ||
      frame.can_ratify !== false) {
    throw new TypeError("synthetic-only, no-authority frame contract violated");
  }
  requireDemoId(frame.frame_id, "frame_id");
  requireDemoId(frame.source_event_id, "source_event_id");
  if (!STATES.includes(frame.state)) throw new TypeError("unknown Witness channel");
  if (typeof frame.summary !== "string" || !frame.summary.trim() ||
      frame.summary.length > 280) {
    throw new TypeError("invalid accessible text summary");
  }
  if (!Number.isSafeInteger(frame.visual_seed) || frame.visual_seed < 0 ||
      frame.visual_seed > 4294967295) throw new TypeError("invalid visual seed");
  if (!Array.isArray(frame.paths) || frame.paths.length < 2 || frame.paths.length > 8) {
    throw new TypeError("paths must contain 2-8 bounded synthetic paths");
  }
  const pathIds = new Set();
  for (const path of frame.paths) {
    requirePlainObject(path, "path");
    assertKeys(path, PATH_FIELDS, "path");
    requireDemoId(path.id, "path.id");
    requireDemoId(path.source_group, "path.source_group");
    if (pathIds.has(path.id)) throw new TypeError("duplicate path identifier");
    pathIds.add(path.id);
    if (!RELATIONS.has(path.relation)) throw new TypeError("unknown relationship");
    if (!Array.isArray(path.evidence_refs) || path.evidence_refs.length < 1 ||
        path.evidence_refs.length > 16) throw new TypeError("invalid evidence refs");
    const ids = new Set();
    for (const id of path.evidence_refs) {
      requireDemoId(id, "evidence ref");
      if (ids.has(id)) throw new TypeError("duplicate evidence ref in path");
      ids.add(id);
    }
  }
  if (!semanticPairIsValid(frame)) throw new TypeError("channel state lacks declared relationship");
  // Same frame and seed yield byte-identical anchors. The renderer never derives a claim.
  const points = [];
  const n = frame.paths.length;
  for (let strand = 0; strand < n; strand++) {
    const path = frame.paths[strand];
    const spread = strand - (n - 1) / 2;
    for (let j = 0; j < 40; j++) {
      const u = (j + 1) / 41;
      const x = 0.07 + 0.86 * u;
      if (frame.state === "OMISSION" && u > 0.43 && u < 0.57) continue;
      let y = 0.5 + spread * 0.14;
      if (frame.state === "CONVERGENCE") {
        y = 0.5 + spread * (0.23 * (1 - u) + 0.025 * u);
      } else if (frame.state === "DIVERGENCE") {
        y = 0.5 + spread * 0.26 * Math.max(0, (u - 0.15) / 0.85);
      } else if (frame.state === "ANOMALY" && path.relation === "anomaly") {
        y += 0.15 * Math.exp(-Math.pow((u - 0.65) / 0.12, 2));
      } else if (frame.state === "UNRESOLVED") {
        y = 0.5 + spread * 0.22 + 0.011 * Math.sin(13 * u);
      } else if (frame.state === "CORRECTION") {
        y = 0.5 + spread * 0.22 + (path.relation === "supersedes" ? 0.018 : 0);
      }
      const jitter = ((frame.visual_seed + strand * 73 + j * 103) % 997) / 997 - 0.5;
      points.push({
        x: bounded(x), y: bounded(y + jitter * 0.008),
        pathId: path.id,
        previous: frame.state === "CORRECTION" && path.relation === "supersedes"
      });
    }
  }
  return {
    channel: frame.state,
    description: frame.summary,
    sourceEventId: frame.source_event_id,
    isSynthetic: true,
    authorityEffect: "NONE",
    canRatify: false,
    points,
    paths: frame.paths.map((path) => ({
      id: path.id, relation: path.relation, sourceGroup: path.source_group,
      evidenceRefs: path.evidence_refs.slice()
    }))
  };
}

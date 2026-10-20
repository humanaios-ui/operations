// Bounded identity and attestation helpers for the INTENT-OS collaboration rehearsal.
//
// A receipt proves only that a Cloudflare Access-authenticated actor submitted a
// particular digest. It does not prove that the underlying statement is true,
// grant authority, contact a third party, establish a contract, or establish that
// a commission is due.

export const ATTESTATION_VERSION = "humanaios.collaboration.attestation.v0.1";
export const RECEIPT_VERSION = "humanaios.collaboration.receipt.v0.1";

const EVENT_ROLES = Object.freeze({
  ONBOARDING_BOUNDARY_ACCEPTED: new Set(["USER"]),
  FINDER_ROLE_ACCEPTED: new Set(["FINDER"]),
  PRINCIPAL_MANDATE_CONFIRMED: new Set(["PRINCIPAL"]),
  INTRODUCTION_AUTHORIZED: new Set(["FINDER"]),
  INTRODUCTION_SENT_RECORDED: new Set(["FINDER"]),
  CONTRACT_REPORTED: new Set(["FINDER", "PRINCIPAL"]),
  COMMISSION_REPORTED: new Set(["FINDER", "PRINCIPAL"]),
});

const INPUT_KEYS = new Set([
  "version", "event_type", "relationship_id", "artifact_sha256",
  "actor_role", "counterparty_actor_id", "opportunity_id",
]);
const RECEIPT_KEYS = [
  "schema_version", "receipt_id", "event_type", "relationship_id",
  "artifact_sha256", "actor_id", "actor_role", "counterparty_actor_id",
  "opportunity_id", "authentication", "observed_at", "authority_effect",
  "execution", "statement",
];
const RELATIONSHIP_ID = /^REL-[A-Z0-9][A-Z0-9_-]{7,63}$/;
const ACTOR_ID = /^USR-[A-F0-9]{24}$/;
const SHA256 = /^[a-f0-9]{64}$/;
const OPPORTUNITY_ID = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$/;
const RECEIPT_ID = /^RCP-[A-F0-9-]{36}$/;
const encoder = new TextEncoder();

function configuredKey(env) {
  const value = env && typeof env.COLLAB_HMAC_KEY === "string"
    ? env.COLLAB_HMAC_KEY : "";
  return encoder.encode(value).byteLength >= 32 ? value : "";
}

export function collaborationConfigured(env) {
  return !!configuredKey(env);
}

function cleanObject(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (Array.isArray(value)) return value.map(cleanObject);
  if (value && typeof value === "object") {
    const out = {};
    for (const key of Object.keys(value).sort()) {
      if (value[key] === undefined) throw new TypeError("undefined is not canonical JSON");
      out[key] = cleanObject(value[key]);
    }
    return out;
  }
  throw new TypeError("unsupported canonical JSON value");
}

export function canonicalJson(value) {
  return JSON.stringify(cleanObject(value));
}

function toHex(bytes) {
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

async function sha256Hex(value) {
  return toHex(await crypto.subtle.digest("SHA-256", encoder.encode(value)));
}

async function hmacHex(secret, domain, value) {
  const key = await crypto.subtle.importKey(
    "raw", encoder.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"],
  );
  return toHex(await crypto.subtle.sign("HMAC", key, encoder.encode(`${domain}\n${value}`)));
}

function constantTimeHexEqual(left, right) {
  if (typeof left !== "string" || typeof right !== "string" || left.length !== right.length) return false;
  let different = 0;
  for (let i = 0; i < left.length; i += 1) different |= left.charCodeAt(i) ^ right.charCodeAt(i);
  return different === 0;
}

export async function actorIdFor(accessIdentity, env) {
  const secret = configuredKey(env);
  if (!secret) throw new Error("collaboration receipt key is not configured");
  const issuer = accessIdentity && typeof accessIdentity.issuer === "string"
    ? accessIdentity.issuer : "";
  const subject = accessIdentity && typeof accessIdentity.subject === "string" && accessIdentity.subject
    ? accessIdentity.subject
    : accessIdentity && typeof accessIdentity.email === "string" ? accessIdentity.email : "";
  if (!issuer || !subject) throw new Error("verified identity has no stable subject");
  const digest = await hmacHex(secret, "humanaios.actor.v0.1", `${issuer}\n${subject}`);
  return `USR-${digest.slice(0, 24).toUpperCase()}`;
}

function exactKeys(value, allowed) {
  return value && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).every((key) => allowed.has(key));
}

export function validateAttestation(value, authenticatedActorId) {
  if (!exactKeys(value, INPUT_KEYS)) throw new Error("attestation has unknown fields");
  if (value.version !== ATTESTATION_VERSION) throw new Error("unsupported attestation version");
  const roles = EVENT_ROLES[value.event_type];
  if (!roles) throw new Error("unsupported collaboration event");
  if (!roles.has(value.actor_role)) throw new Error("actor role is not valid for this event");
  if (!RELATIONSHIP_ID.test(value.relationship_id || "")) throw new Error("invalid relationship_id");
  if (!SHA256.test(value.artifact_sha256 || "")) throw new Error("invalid artifact_sha256");
  if (!ACTOR_ID.test(authenticatedActorId || "")) throw new Error("invalid authenticated actor");

  const counterparty = value.counterparty_actor_id ?? null;
  if (counterparty !== null && !ACTOR_ID.test(counterparty)) throw new Error("invalid counterparty_actor_id");
  if (counterparty === authenticatedActorId) throw new Error("one actor cannot be both sides of a relationship event");
  if (value.event_type === "PRINCIPAL_MANDATE_CONFIRMED" && counterparty === null) {
    throw new Error("principal confirmation requires the finder actor id");
  }
  if (value.event_type === "INTRODUCTION_AUTHORIZED" && counterparty === null) {
    throw new Error("introduction authorization requires the principal actor id");
  }

  const opportunity = value.opportunity_id ?? null;
  if (opportunity !== null && !OPPORTUNITY_ID.test(opportunity)) throw new Error("invalid opportunity_id");
  if (["INTRODUCTION_AUTHORIZED", "INTRODUCTION_SENT_RECORDED", "CONTRACT_REPORTED", "COMMISSION_REPORTED"]
    .includes(value.event_type) && opportunity === null) {
    throw new Error("this event requires an opportunity_id");
  }
  return {
    version: ATTESTATION_VERSION,
    event_type: value.event_type,
    relationship_id: value.relationship_id,
    artifact_sha256: value.artifact_sha256,
    actor_role: value.actor_role,
    counterparty_actor_id: counterparty,
    opportunity_id: opportunity,
  };
}

export async function issueAttestation(value, accessIdentity, env, options = {}) {
  const secret = configuredKey(env);
  if (!secret) throw new Error("collaboration receipt key is not configured");
  const actorId = await actorIdFor(accessIdentity, env);
  const input = validateAttestation(value, actorId);
  const now = options.now instanceof Date ? options.now : new Date();
  const uuid = typeof options.uuid === "string" ? options.uuid : crypto.randomUUID();
  const receipt = {
    schema_version: RECEIPT_VERSION,
    receipt_id: `RCP-${uuid.toUpperCase()}`,
    event_type: input.event_type,
    relationship_id: input.relationship_id,
    artifact_sha256: input.artifact_sha256,
    actor_id: actorId,
    actor_role: input.actor_role,
    counterparty_actor_id: input.counterparty_actor_id,
    opportunity_id: input.opportunity_id,
    authentication: "CLOUDFLARE_ACCESS_JWT_VERIFIED",
    observed_at: now.toISOString(),
    authority_effect: "NONE",
    execution: "DISABLED",
    statement: "A verified actor submitted this digest. Truth, mandate, external action, contract, and payment are not established by this receipt.",
  };
  const canonical = canonicalJson(receipt);
  return {
    receipt,
    receipt_sha256: await sha256Hex(canonical),
    signature: {
      algorithm: "HMAC-SHA256",
      key_scope: "INTENT_OS_COLLABORATION_WORKER",
      value: await hmacHex(secret, "humanaios.collaboration.receipt.v0.1", canonical),
    },
  };
}

function receiptShapeValid(receipt) {
  if (!receipt || typeof receipt !== "object" || Array.isArray(receipt)) return false;
  if (Object.keys(receipt).sort().join("\n") !== RECEIPT_KEYS.slice().sort().join("\n")) return false;
  if (receipt.schema_version !== RECEIPT_VERSION || !RECEIPT_ID.test(receipt.receipt_id || "")) return false;
  if (!EVENT_ROLES[receipt.event_type] || !EVENT_ROLES[receipt.event_type].has(receipt.actor_role)) return false;
  if (!RELATIONSHIP_ID.test(receipt.relationship_id || "") || !SHA256.test(receipt.artifact_sha256 || "")) return false;
  if (!ACTOR_ID.test(receipt.actor_id || "")) return false;
  if (receipt.counterparty_actor_id !== null && !ACTOR_ID.test(receipt.counterparty_actor_id || "")) return false;
  if (receipt.counterparty_actor_id === receipt.actor_id) return false;
  if (receipt.opportunity_id !== null && !OPPORTUNITY_ID.test(receipt.opportunity_id || "")) return false;
  if (["PRINCIPAL_MANDATE_CONFIRMED", "INTRODUCTION_AUTHORIZED"].includes(receipt.event_type)
    && receipt.counterparty_actor_id === null) return false;
  if (["INTRODUCTION_AUTHORIZED", "INTRODUCTION_SENT_RECORDED", "CONTRACT_REPORTED", "COMMISSION_REPORTED"]
    .includes(receipt.event_type) && receipt.opportunity_id === null) return false;
  if (receipt.authentication !== "CLOUDFLARE_ACCESS_JWT_VERIFIED") return false;
  if (!Number.isFinite(Date.parse(receipt.observed_at || ""))) return false;
  return receipt.authority_effect === "NONE" && receipt.execution === "DISABLED"
    && typeof receipt.statement === "string" && receipt.statement.length > 0;
}

export async function verifyAttestationEnvelope(envelope, env) {
  const secret = configuredKey(env);
  if (!secret) return { valid: false, reason: "collaboration receipt key is not configured" };
  if (!envelope || typeof envelope !== "object" || Array.isArray(envelope)) {
    return { valid: false, reason: "invalid receipt envelope" };
  }
  const allowedEnvelope = new Set(["receipt", "receipt_sha256", "signature"]);
  if (!exactKeys(envelope, allowedEnvelope) || !receiptShapeValid(envelope.receipt)) {
    return { valid: false, reason: "invalid receipt shape" };
  }
  if (!envelope.signature || envelope.signature.algorithm !== "HMAC-SHA256"
    || envelope.signature.key_scope !== "INTENT_OS_COLLABORATION_WORKER"
    || !SHA256.test(envelope.signature.value || "") || !SHA256.test(envelope.receipt_sha256 || "")) {
    return { valid: false, reason: "invalid receipt signature metadata" };
  }
  const canonical = canonicalJson(envelope.receipt);
  const digest = await sha256Hex(canonical);
  if (!constantTimeHexEqual(digest, envelope.receipt_sha256)) {
    return { valid: false, reason: "receipt digest mismatch" };
  }
  const expected = await hmacHex(secret, "humanaios.collaboration.receipt.v0.1", canonical);
  if (!constantTimeHexEqual(expected, envelope.signature.value)) {
    return { valid: false, reason: "receipt signature mismatch" };
  }
  return {
    valid: true,
    receipt_id: envelope.receipt.receipt_id,
    actor_id: envelope.receipt.actor_id,
    event_type: envelope.receipt.event_type,
    authority_effect: "NONE",
  };
}

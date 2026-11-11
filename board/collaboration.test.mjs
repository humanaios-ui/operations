// Pure contract checks for the INTENT-OS delegated-collaboration receipts.
import {
  ATTESTATION_VERSION,
  actorIdFor,
  canonicalJson,
  collaborationConfigured,
  issueAttestation,
  validateAttestation,
  verifyAttestationEnvelope,
} from "./collaboration.mjs";

const env = { COLLAB_HMAC_KEY: "test-only-secret-that-is-longer-than-thirty-two-bytes" };
const night = { issuer: "https://team.cloudflareaccess.com", subject: "night-subject", email: "night@example.test" };
const david = { issuer: "https://team.cloudflareaccess.com", subject: "david-subject", email: "david@example.test" };
const base = {
  version: ATTESTATION_VERSION,
  event_type: "FINDER_ROLE_ACCEPTED",
  relationship_id: "REL-TESTCASE0001",
  artifact_sha256: "a".repeat(64),
  actor_role: "FINDER",
  counterparty_actor_id: null,
  opportunity_id: null,
};

let count = 0;
let passed = true;
function check(name, condition) {
  count += 1;
  passed &&= !!condition;
  console.log(`${condition ? "  ok  " : "  FAIL"} ${name}`);
}
async function rejects(name, fn, pattern) {
  let message = "";
  try { await fn(); } catch (error) { message = error.message; }
  check(name, pattern.test(message));
}

check("short or missing receipt key fails closed", !collaborationConfigured({ COLLAB_HMAC_KEY: "short" }));
check("32+ byte receipt key enables the bounded API", collaborationConfigured(env));
check("canonical JSON sorts nested keys", canonicalJson({ z: 1, a: { y: 2, b: 3 } }) === '{"a":{"b":3,"y":2},"z":1}');

const nightId = await actorIdFor(night, env);
const nightAgain = await actorIdFor({ ...night, email: "changed@example.test" }, env);
const davidId = await actorIdFor(david, env);
check("verified subject maps to a pseudonymous actor id", /^USR-[A-F0-9]{24}$/.test(nightId));
check("same issuer and subject maps stably despite email change", nightId === nightAgain);
check("different verified subject maps to another actor", nightId !== davidId);
await rejects("actor derivation needs a secret", () => actorIdFor(night, {}), /not configured/);

check("finder may accept before the other actor is enrolled",
  validateAttestation(base, nightId).counterparty_actor_id === null);
await rejects("unknown attestation fields are refused",
  () => validateAttestation({ ...base, execute: true }, nightId), /unknown fields/);
await rejects("event and role must match",
  () => validateAttestation({ ...base, actor_role: "PRINCIPAL" }, nightId), /actor role/);
await rejects("one actor cannot sign both sides",
  () => validateAttestation({ ...base, counterparty_actor_id: nightId }, nightId), /both sides/);
await rejects("principal confirmation names the finder",
  () => validateAttestation({ ...base, event_type: "PRINCIPAL_MANDATE_CONFIRMED", actor_role: "PRINCIPAL" }, davidId), /requires the finder/);
await rejects("introduction authorization names one opportunity",
  () => validateAttestation({ ...base, event_type: "INTRODUCTION_AUTHORIZED", counterparty_actor_id: davidId }, nightId), /requires an opportunity/);

for (const [field, input] of [
  ["event_type", ["INTRODUCTION_AUTHORIZED"]],
  ["actor_role", ["FINDER"]],
  ["relationship_id", ["REL-TESTCASE0001"]],
  ["artifact_sha256", ["a".repeat(64)]],
  ["counterparty_actor_id", [davidId]],
  ["opportunity_id", ["OPP-TEST-001"]],
]) {
  await rejects(`reject array-valued ${field} before signing`,
    () => issueAttestation({ ...base, [field]: input }, night, env), /string|invalid|unsupported/);
}
await rejects("array counterparty cannot evade self-counterparty check",
  () => validateAttestation({ ...base, counterparty_actor_id: [nightId] }, nightId), /counterparty/);
await rejects("array event cannot bypass introduction requirements",
  () => issueAttestation({
    ...base, event_type: ["INTRODUCTION_AUTHORIZED"], actor_role: "FINDER",
  }, night, env), /event/);

const issued = await issueAttestation(base, night, env, {
  now: new Date("2026-10-20T03:00:00.000Z"),
  uuid: "12345678-1234-1234-1234-1234567890ab",
});
check("issued receipt binds the verified actor", issued.receipt.actor_id === nightId);
check("issued receipt has no authority or execution effect",
  issued.receipt.authority_effect === "NONE" && issued.receipt.execution === "DISABLED");
check("issued receipt discloses no email", !JSON.stringify(issued).includes("@example.test"));
check("issued receipt verifies", (await verifyAttestationEnvelope(issued, env)).valid);

const changed = structuredClone(issued);
changed.receipt.artifact_sha256 = "b".repeat(64);
check("changed receipt fails verification", !(await verifyAttestationEnvelope(changed, env)).valid);
const extra = structuredClone(issued);
extra.receipt.hidden_authority = "GRANTED";
check("unsigned extra receipt fields fail verification", !(await verifyAttestationEnvelope(extra, env)).valid);
check("same receipt fails under another Worker key", !(await verifyAttestationEnvelope(issued, {
  COLLAB_HMAC_KEY: "another-test-secret-that-is-longer-than-thirty-two-bytes",
})).valid);

const confirmed = await issueAttestation({
  ...base,
  event_type: "PRINCIPAL_MANDATE_CONFIRMED",
  actor_role: "PRINCIPAL",
  counterparty_actor_id: nightId,
}, david, env, {
  now: new Date("2026-10-20T03:01:00.000Z"),
  uuid: "22345678-1234-1234-1234-1234567890ab",
});
check("distinct service owner can confirm a finder relationship",
  confirmed.receipt.actor_id === davidId && confirmed.receipt.counterparty_actor_id === nightId);

const introduction = await issueAttestation({
  ...base,
  event_type: "INTRODUCTION_AUTHORIZED",
  actor_role: "FINDER",
  counterparty_actor_id: davidId,
  opportunity_id: "OPP-TEST-001",
}, night, env, {
  now: new Date("2026-10-20T03:02:00.000Z"),
  uuid: "32345678-1234-1234-1234-1234567890ab",
});
check("introduction receipt names one lead but sends nothing",
  introduction.receipt.opportunity_id === "OPP-TEST-001" && introduction.receipt.execution === "DISABLED");

console.log(`${count} checks · COLLABORATION CONTRACT ${passed ? "PASS" : "FAIL"}`);
process.exit(passed ? 0 : 2);

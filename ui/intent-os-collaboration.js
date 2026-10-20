"use strict";

const CAPSULE_VERSION = "humanaios.finder_relationship.v0.1";
const ATTESTATION_VERSION = "humanaios.collaboration.attestation.v0.1";
const MAX_IMPORT_BYTES = 256 * 1024;
const encoder = new TextEncoder();

const byId = (id) => document.getElementById(id);
const ui = Object.fromEntries([
  "feedback", "loginStatus", "actorId", "onboardingPanel", "onboardingStatus",
  "displayName", "identityBoundary", "authorityBoundary", "actionBoundary",
  "completeOnboarding", "onboardingReceipt", "relationshipPanel", "relationshipStatus",
  "principalLabel", "serviceUrl", "commissionMin", "commissionMax", "trigger",
  "createRelationship", "acceptFinder", "confirmPrincipal", "principalExact",
  "commissionExact", "importCapsule", "exportCapsule", "relationshipSummary",
  "minerPanel", "minerStatus", "minerForm", "objective", "sourceMode", "mine",
  "minerWarning", "results", "introPanel", "introStatus", "introText", "authorizeIntro",
].map((id) => [id, byId(id)]));

let session = null;
let profile = null;
let capsule = null;
let selectedOpportunityId = null;
let verifiedReceiptIds = new Set();
let refreshSerial = 0;

function text(element, value) { element.textContent = String(value ?? ""); }
function setStatus(element, value, tone = "warn") {
  text(element, value);
  element.className = `status ${tone}`;
}
function feedback(message, tone = "notice") {
  text(ui.feedback, message);
  ui.feedback.className = tone === "error" ? "notice error" : tone === "success" ? "notice success" : "notice";
}
function unlock(element, yes) { element.classList.toggle("locked", !yes); }

function canonicalValue(value) {
  if (value === null || typeof value === "string" || typeof value === "boolean") return value;
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (value && typeof value === "object") {
    const result = {};
    Object.keys(value).sort().forEach((key) => {
      if (value[key] === undefined) throw new Error("Undefined value cannot be fingerprinted.");
      result[key] = canonicalValue(value[key]);
    });
    return result;
  }
  throw new Error("Unsupported value cannot be fingerprinted.");
}
function canonicalJson(value) { return JSON.stringify(canonicalValue(value)); }
async function sha256(value) {
  const bytes = await crypto.subtle.digest("SHA-256", encoder.encode(canonicalJson(value)));
  return [...new Uint8Array(bytes)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function profileKey() { return session ? `humanaios.intent_os.profile.v0.1.${session.actor_id}` : ""; }
function capsuleKey() { return session ? `humanaios.intent_os.finder.v0.1.${session.actor_id}` : ""; }
function saveLocal() {
  if (!session) return;
  if (profile) localStorage.setItem(profileKey(), JSON.stringify(profile));
  if (capsule) localStorage.setItem(capsuleKey(), JSON.stringify(capsule));
}
function loadLocal() {
  try { profile = JSON.parse(localStorage.getItem(profileKey()) || "null"); } catch { profile = null; }
  try { capsule = normalizeCapsule(JSON.parse(localStorage.getItem(capsuleKey()) || "null")); }
  catch { capsule = null; }
}

async function api(path, options = {}) {
  const response = await fetch(path, { cache: "no-store", ...options });
  let result;
  try { result = await response.json(); } catch { result = null; }
  if (!response.ok) throw new Error(result?.error || result?.reason || `Request failed with HTTP ${response.status}.`);
  if (!result || typeof result !== "object") throw new Error("Service returned an invalid response.");
  return result;
}
async function attest(eventType, actorRole, relationshipId, artifactSha256, counterpartyActorId = null, opportunityId = null) {
  return api("/api/collaboration/attest", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      version: ATTESTATION_VERSION,
      event_type: eventType,
      relationship_id: relationshipId,
      artifact_sha256: artifactSha256,
      actor_role: actorRole,
      counterparty_actor_id: counterpartyActorId,
      opportunity_id: opportunityId,
    }),
  });
}

function safeUrl(value) {
  const url = new URL(String(value || ""));
  const host = url.hostname.toLowerCase().replace(/\.$/, "");
  const blockedSuffix = ["localhost", ".localhost", ".local", ".internal", ".lan", ".home", ".test", ".invalid"];
  const literalIpv4 = /^\d{1,3}(?:\.\d{1,3}){3}$/.test(host);
  const literalIpv6 = host.includes(":");
  if (url.protocol !== "https:" || url.username || url.password || (url.port && url.port !== "443")
    || !host.includes(".") || blockedSuffix.some((suffix) => host === suffix || host.endsWith(suffix))
    || literalIpv4 || literalIpv6 || /^0x/i.test(host) || /^\d+$/.test(host)) {
    throw new Error("Service page must be a public HTTPS URL.");
  }
  return url.href;
}
function numberInRange(value, low, high) {
  const number = Number(value);
  return Number.isFinite(number) && number >= low && number <= high ? number : null;
}
function shortText(value, max, fallback = "") {
  return typeof value === "string" ? value.trim().slice(0, max) : fallback;
}
function actorId(value) { return typeof value === "string" && /^USR-[A-F0-9]{24}$/.test(value) ? value : null; }
function relationshipId(value) { return typeof value === "string" && /^REL-[A-Z0-9][A-Z0-9_-]{7,63}$/.test(value) ? value : null; }

function normalizeReceiptEnvelope(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  return value.receipt && value.signature && value.receipt_sha256 ? value : null;
}
function normalizeOpportunity(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const id = shortText(value.resource_id || value.opportunity_id, 100);
  if (!id || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,99}$/.test(id)) return null;
  let sourceUrl = null;
  try { sourceUrl = safeUrl(value.source_url); } catch { sourceUrl = null; }
  return {
    opportunity_id: id,
    title: shortText(value.title, 180, "Resource candidate"),
    description: shortText(value.description, 500),
    source_name: shortText(value.source_name, 120, "Source unknown"),
    source_url: sourceUrl,
    observed_at: shortText(value.observed_at, 60) || null,
    eligibility: "NOT_ASSESSED",
  };
}
function normalizeCapsule(value) {
  if (value === null) return null;
  if (!value || typeof value !== "object" || Array.isArray(value)
    || value.schema_version !== CAPSULE_VERSION || !relationshipId(value.relationship_id)) {
    throw new Error("This is not a supported finder capsule.");
  }
  const finder = value.finder && typeof value.finder === "object" ? value.finder : {};
  const principal = value.principal && typeof value.principal === "object" ? value.principal : {};
  const offer = value.offer && typeof value.offer === "object" ? value.offer : {};
  const minimum = numberInRange(offer.minimum_percent, 0, 100);
  const maximum = numberInRange(offer.maximum_percent, 0, 100);
  if (minimum === null || maximum === null || minimum > maximum) throw new Error("Commission range is invalid.");
  let url;
  try { url = safeUrl(principal.public_service_url); } catch { throw new Error("Service page is invalid."); }
  const exact = offer.exact_percent === null || offer.exact_percent === undefined
    ? null : numberInRange(offer.exact_percent, minimum, maximum);
  if (offer.exact_percent !== null && offer.exact_percent !== undefined && exact === null) {
    throw new Error("Exact commission is outside the offered range.");
  }
  return {
    schema_version: CAPSULE_VERSION,
    relationship_id: value.relationship_id,
    created_at: shortText(value.created_at, 40) || new Date().toISOString(),
    updated_at: shortText(value.updated_at, 40) || new Date().toISOString(),
    state: shortText(value.state, 80, "DRAFT"),
    finder: {
      actor_id: actorId(finder.actor_id),
      display_label: shortText(finder.display_label, 80, "Finder"),
      role_status: shortText(finder.role_status, 40, "NOT_ACCEPTED"),
    },
    principal: {
      actor_id: actorId(principal.actor_id),
      display_label: shortText(principal.display_label, 80, "Service owner"),
      public_service_url: url,
      role_status: shortText(principal.role_status, 40, "NOT_CONFIRMED"),
    },
    offer: {
      kind: "REFERRAL_COMMISSION",
      minimum_percent: minimum,
      maximum_percent: maximum,
      exact_percent: exact,
      trigger: shortText(offer.trigger, 500),
      evidence_status: "HUMAN_ATTESTED_PRIVATE",
      evidence_note: shortText(offer.evidence_note, 500),
      counterparty_confirmation: exact === null ? "NOT_RECEIVED" : "ATTESTED_DIGEST_ONLY",
    },
    authority: {
      discover: "ALLOWED_BY_FINDER",
      screen: "ALLOWED_BY_FINDER",
      prepare_introduction: "ALLOWED_BY_FINDER",
      send_introduction: "REQUIRES_MATCHED_TERMS_AND_FINDER_AUTHORIZATION",
      negotiate_for_principal: "NOT_GRANTED",
      accept_contract: "NOT_GRANTED",
      collect_commission: "NOT_ESTABLISHED",
    },
    opportunities: Array.isArray(value.opportunities)
      ? value.opportunities.slice(0, 50).map(normalizeOpportunity).filter(Boolean) : [],
    receipts: Array.isArray(value.receipts)
      ? value.receipts.slice(0, 100).map(normalizeReceiptEnvelope).filter(Boolean) : [],
  };
}

function termsView(value) {
  return {
    schema_version: value.schema_version,
    relationship_id: value.relationship_id,
    finder: { actor_id: value.finder.actor_id },
    principal: {
      actor_id: value.principal.actor_id,
      public_service_url: value.principal.public_service_url,
    },
    offer: value.offer,
    authority: value.authority,
  };
}
function receiptMatches(eventType, digest, actor, counterparty = undefined, opportunity = undefined) {
  if (!capsule) return false;
  return capsule.receipts.some((envelope) => {
    const receipt = envelope.receipt || {};
    return verifiedReceiptIds.has(receipt.receipt_id)
      && receipt.event_type === eventType
      && receipt.artifact_sha256 === digest
      && receipt.actor_id === actor
      && (counterparty === undefined || receipt.counterparty_actor_id === counterparty)
      && (opportunity === undefined || receipt.opportunity_id === opportunity);
  });
}

async function verifyEnvelope(envelope) {
  try {
    const result = await api("/api/collaboration/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(envelope),
    });
    if (result.valid && result.receipt_id) verifiedReceiptIds.add(result.receipt_id);
  } catch { /* Invalid imported receipts remain untrusted and unused. */ }
}
async function verifyStoredReceipts() {
  verifiedReceiptIds = new Set();
  const envelopes = [];
  if (profile?.onboarding_receipt) envelopes.push(profile.onboarding_receipt);
  if (capsule?.receipts) envelopes.push(...capsule.receipts);
  for (const envelope of envelopes.slice(0, 101)) await verifyEnvelope(envelope);
}

function profileReady() {
  return !!(profile && profile.actor_id === session?.actor_id && profile.display_label
    && verifiedReceiptIds.has(profile.onboarding_receipt?.receipt?.receipt_id));
}
async function relationshipState() {
  if (!capsule) return "NO_RELATIONSHIP";
  const digest = await sha256(termsView(capsule));
  const finder = capsule.finder.actor_id;
  const principal = capsule.principal.actor_id;
  if (principal && capsule.offer.exact_percent === null) return "TERMS_CHANGED_RECONFIRM_BOTH";
  const finderAccepted = finder && receiptMatches("FINDER_ROLE_ACCEPTED", digest, finder);
  const principalConfirmed = principal && receiptMatches(
    "PRINCIPAL_MANDATE_CONFIRMED", digest, principal, finder,
  );
  if (!finderAccepted && !principalConfirmed) return "DRAFT";
  if (finderAccepted && !principal) return "DISCOVERY_ONLY_PENDING_PRINCIPAL";
  if (principalConfirmed && !finderAccepted) return "PENDING_FINDER_RECONFIRMATION";
  if (!principalConfirmed) return "TERMS_CHANGED_RECONFIRM_BOTH";
  return "READY_FOR_INTRODUCTION_REVIEW";
}

function renderReceipts() {
  if (!capsule) return "";
  const valid = capsule.receipts.filter((item) => verifiedReceiptIds.has(item.receipt?.receipt_id));
  return `${valid.length}/${capsule.receipts.length} receipt(s) verified by this Worker.`;
}

async function refresh() {
  const serial = ++refreshSerial;
  const loggedIn = !!session;
  setStatus(ui.loginStatus, loggedIn ? "VERIFIED" : "NOT VERIFIED", loggedIn ? "good" : "bad");
  text(ui.actorId, loggedIn ? session.actor_id : "No verified actor yet.");
  unlock(ui.onboardingPanel, loggedIn);
  ui.completeOnboarding.disabled = !loggedIn;

  const ready = loggedIn && profileReady();
  setStatus(ui.onboardingStatus, ready ? "COMPLETE" : loggedIn ? "READY" : "LOCKED", ready ? "good" : "warn");
  unlock(ui.relationshipPanel, ready);
  ui.createRelationship.disabled = !ready || !!capsule;
  ui.exportCapsule.disabled = !capsule;

  const state = await relationshipState();
  if (serial !== refreshSerial) return;
  if (capsule) capsule.state = state;
  const hasCapsule = !!capsule;
  const currentIsFinder = hasCapsule && (!capsule.finder.actor_id || capsule.finder.actor_id === session?.actor_id);
  const currentIsPrincipal = hasCapsule && capsule.finder.actor_id
    && capsule.finder.actor_id !== session?.actor_id
    && (!capsule.principal.actor_id || capsule.principal.actor_id === session?.actor_id);
  ui.acceptFinder.disabled = !ready || !currentIsFinder;
  ui.confirmPrincipal.disabled = !ready || !currentIsPrincipal;
  ui.principalExact.hidden = !currentIsPrincipal;
  setStatus(ui.relationshipStatus, hasCapsule ? state : ready ? "READY" : "LOCKED",
    state === "READY_FOR_INTRODUCTION_REVIEW" ? "good" : "warn");

  ui.relationshipSummary.hidden = !capsule;
  if (capsule) {
    text(ui.relationshipSummary,
      `${capsule.finder.display_label} acts as finder for ${capsule.principal.display_label}. `
      + `Offer: ${capsule.offer.minimum_percent}–${capsule.offer.maximum_percent}% when ${capsule.offer.trigger || "the stated trigger occurs"}. `
      + `Exact terms: ${capsule.offer.exact_percent ?? "not confirmed"}. ${renderReceipts()}`);
  }

  const miningAllowed = ready && hasCapsule && [
    "DISCOVERY_ONLY_PENDING_PRINCIPAL", "PENDING_FINDER_RECONFIRMATION",
    "TERMS_CHANGED_RECONFIRM_BOTH", "READY_FOR_INTRODUCTION_REVIEW",
  ].includes(state);
  unlock(ui.minerPanel, miningAllowed);
  ui.mine.disabled = !miningAllowed;
  setStatus(ui.minerStatus, miningAllowed ? "DISCOVERY OPEN" : "LOCKED", miningAllowed ? "good" : "warn");

  const selected = capsule?.opportunities.find((item) => item.opportunity_id === selectedOpportunityId) || null;
  const introReady = state === "READY_FOR_INTRODUCTION_REVIEW" && currentIsFinder && !!selected;
  unlock(ui.introPanel, state === "READY_FOR_INTRODUCTION_REVIEW");
  ui.authorizeIntro.disabled = !introReady;
  setStatus(ui.introStatus, introReady ? "READY" : state === "READY_FOR_INTRODUCTION_REVIEW" ? "SELECT A LEAD" : "BLOCKED",
    introReady ? "good" : "warn");
  text(ui.introText, selected
    ? `Selected: ${selected.title}. Both people must hold the same exact terms before this finder can authorize this one introduction.`
    : "Both people must sign the same exact terms. Then the finder can authorize one selected introduction.");
  saveLocal();
}

async function completeOnboarding() {
  const display = ui.displayName.value.trim();
  if (!display || display.length > 80) throw new Error("Enter the name shown on this device.");
  if (![ui.identityBoundary, ui.authorityBoundary, ui.actionBoundary].every((item) => item.checked)) {
    throw new Error("Accept all three collaboration boundaries.");
  }
  const record = {
    version: "humanaios.first_user_onboarding.v0.1",
    actor_id: session.actor_id,
    display_label: display,
    boundaries: ["IDENTITY_IS_NOT_MANDATE", "COUNTERPARTY_SELF_CONFIRMS", "INTRODUCTION_NEEDS_SEPARATE_CHOICE"],
  };
  const relationship = `REL-ONBOARDING-${session.actor_id.slice(-12)}`;
  const envelope = await attest("ONBOARDING_BOUNDARY_ACCEPTED", "USER", relationship, await sha256(record));
  profile = { ...record, relationship_id: relationship, onboarding_receipt: envelope };
  verifiedReceiptIds.add(envelope.receipt.receipt_id);
  text(ui.onboardingReceipt, `Receipt ${envelope.receipt.receipt_id} · authority NONE · execution DISABLED`);
  feedback("First-user onboarding recorded. Login and authority remain separate.", "success");
  await refresh();
}

function newRelationship() {
  const principalLabel = ui.principalLabel.value.trim();
  const minimum = numberInRange(ui.commissionMin.value, 0, 100);
  const maximum = numberInRange(ui.commissionMax.value, 0, 100);
  const trigger = ui.trigger.value.trim();
  if (!principalLabel || principalLabel.length > 80) throw new Error("Enter the service owner label.");
  const publicUrl = safeUrl(ui.serviceUrl.value);
  if (minimum === null || maximum === null || minimum > maximum) throw new Error("Enter a valid commission range.");
  if (!trigger || trigger.length > 500) throw new Error("State the payment trigger.");
  const now = new Date().toISOString();
  capsule = normalizeCapsule({
    schema_version: CAPSULE_VERSION,
    relationship_id: `REL-${crypto.randomUUID().replaceAll("-", "").slice(0, 20).toUpperCase()}`,
    created_at: now,
    updated_at: now,
    state: "DRAFT",
    finder: { actor_id: session.actor_id, display_label: profile.display_label, role_status: "NOT_ACCEPTED" },
    principal: { actor_id: null, display_label: principalLabel, public_service_url: publicUrl, role_status: "NOT_CONFIRMED" },
    offer: {
      minimum_percent: minimum,
      maximum_percent: maximum,
      exact_percent: null,
      trigger,
      evidence_note: "Private offer supplied by the finder; counterparty confirmation not yet received.",
    },
    opportunities: [],
    receipts: [],
  });
  selectedOpportunityId = null;
  feedback("Finder draft created. The service owner has not confirmed it.");
}

async function acceptFinderRole() {
  if (!capsule.finder.actor_id) capsule.finder.actor_id = session.actor_id;
  if (capsule.finder.actor_id !== session.actor_id) throw new Error("Only the named finder can accept this role.");
  if (capsule.principal.actor_id === session.actor_id) throw new Error("One login cannot sign both sides.");
  capsule.finder.display_label = profile.display_label;
  capsule.finder.role_status = "ATTESTED";
  capsule.updated_at = new Date().toISOString();
  const digest = await sha256(termsView(capsule));
  const envelope = await attest(
    "FINDER_ROLE_ACCEPTED", "FINDER", capsule.relationship_id, digest,
    capsule.principal.actor_id, null,
  );
  capsule.receipts.push(envelope);
  verifiedReceiptIds.add(envelope.receipt.receipt_id);
  feedback(capsule.principal.actor_id
    ? "Finder accepted the exact terms. The relationship can now reach the introduction review gate."
    : "Finder role accepted. Discovery may continue. Introductions remain blocked until the service owner confirms exact terms.", "success");
}

async function confirmAsPrincipal() {
  if (!capsule.finder.actor_id) throw new Error("The finder must identify themselves first.");
  if (capsule.finder.actor_id === session.actor_id) throw new Error("The finder cannot confirm the service owner side.");
  if (capsule.principal.actor_id && capsule.principal.actor_id !== session.actor_id) {
    throw new Error("This capsule already names a different service owner actor.");
  }
  const exact = numberInRange(
    ui.commissionExact.value,
    capsule.offer.minimum_percent,
    capsule.offer.maximum_percent,
  );
  if (exact === null) throw new Error("Choose an exact percentage inside the offered range.");
  capsule.principal.actor_id = session.actor_id;
  capsule.principal.role_status = "ATTESTED";
  capsule.offer.exact_percent = exact;
  capsule.offer.counterparty_confirmation = "ATTESTED_DIGEST_ONLY";
  capsule.updated_at = new Date().toISOString();
  const digest = await sha256(termsView(capsule));
  const envelope = await attest(
    "PRINCIPAL_MANDATE_CONFIRMED", "PRINCIPAL", capsule.relationship_id,
    digest, capsule.finder.actor_id, null,
  );
  capsule.receipts.push(envelope);
  verifiedReceiptIds.add(envelope.receipt.receipt_id);
  feedback("Service owner confirmation recorded. Export this capsule back to the finder for final matching acceptance.", "success");
}

async function importCapsule(file) {
  if (!profileReady()) throw new Error("Complete first-user onboarding before importing a relationship.");
  if (!file || file.size > MAX_IMPORT_BYTES) throw new Error("Capsule must be a JSON file smaller than 256 KiB.");
  let value;
  try { value = JSON.parse(await file.text()); } catch { throw new Error("Capsule is not valid JSON."); }
  capsule = normalizeCapsule(value);
  selectedOpportunityId = null;
  await verifyStoredReceipts();
  feedback("Capsule imported. Invalid or changed receipts remain untrusted.", "success");
}
function exportCapsule() {
  if (!profileReady()) throw new Error("Complete first-user onboarding before exporting a relationship.");
  capsule.updated_at = new Date().toISOString();
  const blob = new Blob([`${JSON.stringify(capsule, null, 2)}\n`], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `${capsule.relationship_id}.private.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

function candidateCard(row) {
  const clean = normalizeOpportunity(row);
  if (!clean) return null;
  const card = document.createElement("article");
  card.className = "card";
  const heading = document.createElement("h3"); text(heading, clean.title); card.append(heading);
  const description = document.createElement("p"); text(description, clean.description || "No description supplied."); card.append(description);
  const meta = document.createElement("p"); meta.className = "quiet";
  text(meta, `${clean.source_name} · eligibility NOT ASSESSED · observed ${clean.observed_at || "unknown"}`); card.append(meta);
  if (clean.source_url) {
    const link = document.createElement("a"); link.href = clean.source_url; link.target = "_blank";
    link.rel = "noopener noreferrer"; text(link, "Open source to verify ↗"); card.append(link);
  }
  const choose = document.createElement("button"); choose.className = "secondary";
  text(choose, capsule.opportunities.some((item) => item.opportunity_id === clean.opportunity_id)
    ? "Select attached lead" : "Attach to finder capsule");
  choose.addEventListener("click", async () => {
    if (!capsule.opportunities.some((item) => item.opportunity_id === clean.opportunity_id)) {
      capsule.opportunities.push(clean);
    }
    selectedOpportunityId = clean.opportunity_id;
    capsule.updated_at = new Date().toISOString();
    feedback("Lead attached. Relevance is not eligibility. No introduction was sent.", "success");
    await refresh();
  });
  const wrap = document.createElement("p"); wrap.append(choose); card.append(wrap);
  return card;
}

async function mineOpportunities() {
  const objective = ui.objective.value.trim();
  if (objective.length < 3 || objective.length > 500) throw new Error("Describe the work goal in 3 to 500 characters.");
  ui.mine.disabled = true;
  text(ui.results, "");
  const result = await api("/api/intent", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ objective, source_mode: ui.sourceMode.value }),
  });
  if (!Array.isArray(result.candidates)) throw new Error("Resource Miner returned no candidate list.");
  ui.minerWarning.hidden = !result.source_warning;
  text(ui.minerWarning, result.source_warning || "");
  for (const row of result.candidates.slice(0, 10)) {
    const card = candidateCard(row);
    if (card) ui.results.append(card);
  }
  if (!ui.results.childElementCount) text(ui.results, "No supported matches in this run.");
  feedback(`${result.shown_count || 0} lead(s) shown. Review the source before any action.`);
}

async function authorizeIntroduction() {
  const state = await relationshipState();
  if (state !== "READY_FOR_INTRODUCTION_REVIEW") throw new Error("Both people have not signed the same exact terms.");
  if (capsule.finder.actor_id !== session.actor_id) throw new Error("Only the finder can authorize their introduction.");
  const opportunity = capsule.opportunities.find((item) => item.opportunity_id === selectedOpportunityId);
  if (!opportunity) throw new Error("Select one attached opportunity.");
  const artifact = {
    relationship_terms_sha256: await sha256(termsView(capsule)),
    opportunity,
    proposed_action: "INTRODUCE_SERVICE_OWNER_TO_OPPORTUNITY_CONTACT",
    execution: "DISABLED",
  };
  const digest = await sha256(artifact);
  const envelope = await attest(
    "INTRODUCTION_AUTHORIZED", "FINDER", capsule.relationship_id, digest,
    capsule.principal.actor_id, opportunity.opportunity_id,
  );
  capsule.receipts.push(envelope);
  verifiedReceiptIds.add(envelope.receipt.receipt_id);
  feedback("This introduction is authorized in the capsule. Nothing was sent.", "success");
  setStatus(ui.introStatus, "AUTHORIZED · NOT SENT", "good");
}

function protect(action) {
  return async (event) => {
    event?.preventDefault?.();
    try { await action(event); await refresh(); }
    catch (error) { feedback(error.message || "Action failed.", "error"); }
  };
}

ui.completeOnboarding.addEventListener("click", protect(completeOnboarding));
ui.createRelationship.addEventListener("click", protect(async () => { newRelationship(); }));
ui.acceptFinder.addEventListener("click", protect(acceptFinderRole));
ui.confirmPrincipal.addEventListener("click", protect(confirmAsPrincipal));
ui.exportCapsule.addEventListener("click", protect(async () => { exportCapsule(); }));
ui.importCapsule.addEventListener("change", protect(async () => { await importCapsule(ui.importCapsule.files[0]); }));
ui.minerForm.addEventListener("submit", protect(mineOpportunities));
ui.authorizeIntro.addEventListener("click", protect(authorizeIntroduction));

async function start() {
  try {
    session = await api("/api/session");
    loadLocal();
    await verifyStoredReceipts();
    if (profile?.display_label) ui.displayName.value = profile.display_label;
    feedback("Verified login ready. Complete the first-user boundary check.", "success");
  } catch (error) {
    feedback(`Login workflow is not ready: ${error.message}`, "error");
  }
  await refresh();
}

start();

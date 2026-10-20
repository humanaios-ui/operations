// board/worker.mjs — the Intent-OS board and collaboration cockpit, served only behind Cloudflare Access.

import {
  actorIdFor,
  collaborationConfigured,
  issueAttestation,
  verifyAttestationEnvelope,
} from "./collaboration.mjs";
//
// Z2's direction (2026-09-18): "I don't want any public, I want to have to login to open the board."
// d17 (2026-09-14) ruled the board local only; d31 (z1-inbox/2026-09-18/Q-BOARD-PUBLISH-01.md) asks to
// replace that with this Worker. Until d31 is ruled and Access is configured, this Worker serves NOTHING:
//
//   * every request but /healthz must carry the Cloudflare Access JWT that Access injects into the request
//     header Cf-Access-Jwt-Assertion for a self-hosted application. Only the header is read: the
//     CF_Authorization cookie is not parsed (one token source, no cookie-syntax edge cases). The token must
//     be signed by the team's current keys (https://<ACCESS_TEAM_DOMAIN>/cdn-cgi/access/certs), issued for
//     this application (aud == ACCESS_AUD), not expired, not before its nbf (no clock-skew allowance).
//     Anything else is 401 — never the file.
//   * a valid token is authentication, not authorization: the Worker then requires the token's email to be
//     on ACCESS_ALLOWED_EMAILS (a Worker variable; comma-separated; case-insensitive). Any other identity is
//     403, even if the Access policy in front was widened by mistake. "Allow-listed identities only" is
//     therefore a property of this code, tested in the self-test, not only of the dashboard policy.
//   * ACCESS_TEAM_DOMAIN, ACCESS_AUD or ACCESS_ALLOWED_EMAILS unset → 401 "Access is not configured". Fails
//     closed: a deploy without the login and the list in front of it publishes nothing.
//   * `assets.run_worker_first` in wrangler.jsonc makes this code run BEFORE the asset router, so no path
//     under ui/ is reachable without passing the check above — and only the paths in SERVED are served at
//     all (the board, its four section pages, the test dashboard, and collaboration cockpit assets). The Z2 reviewer under ui/ reads
//     ../z1-inbox/ at runtime, which is not in the bundle, so it is not offered here rather than offered broken.
//   * the collaboration cockpit is local-first. The Worker returns a pseudonymous actor code, signs only
//     bounded artifact digests, and proxies the existing read-only Resource Miner intent endpoint. It has no
//     collaboration database and no message, application, contract, invoice, or payment execution path.
//   * the relay is untouched: the board still POSTs to it cross-origin with its own HMAC and gate; the
//     Content-Security-Policy below names the relay and raw.githubusercontent.com (the dashboard's live
//     read) as the only connect targets. CSP_CONNECT_SRC (a Worker variable) overrides that list if the
//     relay ever moves.
//   * /healthz answers without a login and says whether Access is configured. That disclosure is
//     intentional (Z2's red-team review, finding 2): it is the operator's and the falsifier's liveness
//     signal, and the same fact is already visible in every 401 body while unconfigured. It carries no
//     commit, no identity and no path.
//   * the team's keys are cached for CERTS_TTL_MS in an immutable snapshot replaced atomically. A key the
//     cache does not know (Cloudflare rotated inside the TTL) forces one refresh, at most once per
//     CERTS_REFRESH_MIN_MS so unknown-kid probes cannot turn the certs endpoint into a per-request fetch.
//     If the certs endpoint fails, the last snapshot is used for up to CERTS_MAX_AGE_MS; beyond that the
//     Worker fails closed ("could not read the team's keys"). Cloudflare's certs endpoint is therefore a
//     soft dependency with a hard bound, not a per-request one.
//   * X-Board-Commit names the commit the running deploy was built from (BOARD_COMMIT, set by the deploy
//     command `npx wrangler deploy --var BOARD_COMMIT:$WORKERS_CI_COMMIT_SHA`), on every authenticated
//     answer, so d31's byte check is a header plus a hash — no build-log archaeology. "unknown" when unset.
//
// Deployed by Cloudflare Workers Builds from this repository on every push to main (wrangler.jsonc at the
// root; wrangler pinned in package.json). No secrets live here: the team domain and the application
// audience are Worker variables set in the dashboard (kept across deploys by keep_vars).
//
// Self-test: `node board/worker.test.mjs` (no network; a generated key signs the test tokens).

const BOARD = "/intent-os-humanaios-v3_3.html";
const COLLABORATION = "/intent-os-collaboration.html";
// Explicit static allow-list. Nothing else under ui/ is served (the Z2 reviewer reads ../z1-inbox at runtime,
// which is not in the bundle).
const SERVED = new Set([BOARD, "/intent-os-decisions.html", "/intent-os-commitments.html", "/intent-os-records.html",
  "/intent-os-arena.html", "/intent-os-test-dashboard-v1_0.html", COLLABORATION,
  "/intent-os-collaboration.js"]);
const MAX_JSON_BODY = 16 * 1024;
const MAX_MINER_RESPONSE = 1024 * 1024;
const CERTS_TTL_MS = 5 * 60 * 1000; // within this window the snapshot is used without a fetch
const CERTS_REFRESH_MIN_MS = 30 * 1000; // an unknown kid forces a refresh at most this often
const CERTS_MAX_AGE_MS = 24 * 60 * 60 * 1000; // last-known-good bound when the certs endpoint fails
const CONNECT_SRC_DEFAULT = "https://intent-os-relay-production.up.railway.app https://raw.githubusercontent.com";

const EMPTY = Object.freeze({ domain: "", at: 0, keys: Object.freeze([]) });
let certCache = EMPTY; // replaced whole, never mutated

function b64url(s) {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + pad);
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}
function decodeObject(seg) {
  const v = JSON.parse(new TextDecoder().decode(b64url(seg)));
  if (v === null || typeof v !== "object" || Array.isArray(v)) throw new Error("not an object");
  return v;
}
function tokenFrom(request) {
  return request.headers.get("Cf-Access-Jwt-Assertion") || "";
}

/**
 * The team's current signing keys. Fresh snapshot (< CERTS_TTL_MS) → no fetch. Otherwise fetch and
 * replace the snapshot atomically; if the fetch fails, fall back to the last snapshot while it is younger
 * than CERTS_MAX_AGE_MS, else throw. `force` bypasses the fresh window (unknown kid), rate-limited by the
 * caller.
 */
export async function accessKeys(teamDomain, fetchFn = fetch, now = Date.now(), force = false) {
  const cached = certCache;
  const usable = cached.domain === teamDomain && cached.keys.length > 0;
  if (!force && usable && now - cached.at < CERTS_TTL_MS) return cached.keys;
  try {
    const r = await fetchFn(`https://${teamDomain}/cdn-cgi/access/certs`);
    if (!r.ok) throw new Error(`certs endpoint answered ${r.status}`);
    const j = await r.json();
    const keys = Object.freeze(Array.isArray(j.keys) ? j.keys.slice() : []);
    certCache = Object.freeze({ domain: teamDomain, at: now, keys });
    return keys;
  } catch (e) {
    if (usable && now - cached.at < CERTS_MAX_AGE_MS) return cached.keys; // last known good, bounded
    throw e;
  }
}
export function resetCertCache() {
  certCache = EMPTY;
}

/**
 * Verify a Cloudflare Access JWT. Returns {ok, why, email}. Checks, in order: shape (three segments, both
 * decoded parts JSON objects), alg RS256 with a kid, issuer is the team domain, audience includes this
 * application, not expired, not before nbf (a present nbf must be a number), then the RSA signature
 * against the key the header names. Nothing is trusted from the token until the signature verifies.
 */
export function allowedEmails(env) {
  const raw = env && typeof env.ACCESS_ALLOWED_EMAILS === "string" ? env.ACCESS_ALLOWED_EMAILS : "";
  return new Set(raw.split(/[\s,;]+/).map((s) => s.trim().toLowerCase()).filter(Boolean));
}
export function configured(env) {
  return !!(env && env.ACCESS_TEAM_DOMAIN && env.ACCESS_AUD && allowedEmails(env).size > 0);
}

export async function verifyAccessJwt(token, env, fetchFn = fetch, nowSec = Date.now() / 1000) {
  if (!configured(env)) return { ok: false, why: "Access is not configured on this Worker (ACCESS_TEAM_DOMAIN, ACCESS_AUD, ACCESS_ALLOWED_EMAILS)" };
  if (!token) return { ok: false, why: "login required" };
  const parts = token.split(".");
  if (parts.length !== 3) return { ok: false, why: "malformed token" };
  let header, payload;
  try { header = decodeObject(parts[0]); payload = decodeObject(parts[1]); } catch { return { ok: false, why: "malformed token" }; }
  if (header.alg !== "RS256" || typeof header.kid !== "string" || !header.kid) return { ok: false, why: "unsupported token" };
  if (payload.iss !== `https://${env.ACCESS_TEAM_DOMAIN}`) return { ok: false, why: "token is not from this team" };
  const aud = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!aud.includes(env.ACCESS_AUD)) return { ok: false, why: "token is not for this application" };
  if (typeof payload.exp !== "number" || payload.exp <= nowSec) return { ok: false, why: "token expired" };
  if ("nbf" in payload && typeof payload.nbf !== "number") return { ok: false, why: "malformed token" }; // a present nbf must be a number — never skipped for being a string
  if (typeof payload.nbf === "number" && payload.nbf > nowSec) return { ok: false, why: "token not yet valid" };
  const nowMs = nowSec * 1000;
  let keys;
  try { keys = await accessKeys(env.ACCESS_TEAM_DOMAIN, fetchFn, nowMs); } catch (e) { return { ok: false, why: `could not read the team's keys: ${e.message}` }; }
  let jwk = keys.find((k) => k && k.kid === header.kid);
  if (!jwk && nowMs - certCache.at >= CERTS_REFRESH_MIN_MS) {
    // a kid the snapshot does not know: Cloudflare may have rotated inside the TTL — refresh once
    try { keys = await accessKeys(env.ACCESS_TEAM_DOMAIN, fetchFn, nowMs, true); } catch { keys = []; }
    jwk = keys.find((k) => k && k.kid === header.kid);
  }
  if (!jwk) return { ok: false, why: "token signed by an unknown key" };
  let ok = false;
  try {
    const key = await crypto.subtle.importKey("jwk", { kty: jwk.kty, n: jwk.n, e: jwk.e, alg: "RS256", ext: true }, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(parts[2]), new TextEncoder().encode(`${parts[0]}.${parts[1]}`));
  } catch { ok = false; }
  if (!ok) return { ok: false, why: "bad signature" };
  // authorization, in the Worker itself: a valid token proves the request passed Access for this application;
  // only an identity on ACCESS_ALLOWED_EMAILS gets the page. A widened Access policy is therefore not enough.
  const email = typeof payload.email === "string" ? payload.email.trim().toLowerCase() : "";
  if (!email || !allowedEmails(env).has(email)) return { ok: false, status: 403, why: "identity is not on the allow-list" };
  const subject = typeof payload.sub === "string" ? payload.sub.trim() : "";
  return { ok: true, email, subject, issuer: payload.iss };
}

// every answer this Worker gives is uncacheable, unindexed, unframed, un-sniffed and leaks no referrer —
// a login-gated control surface. The CSP allows the pages' own inline script and style (both files are
// single-file HTML), connections to the relay and the dashboard's live read, and nothing else.
export function policyHeaders(env) {
  const connect = (env && typeof env.CSP_CONNECT_SRC === "string" && env.CSP_CONNECT_SRC.trim()) || CONNECT_SRC_DEFAULT;
  return {
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": `default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ${connect}; frame-ancestors 'none'; base-uri 'none'; form-action 'none'`,
  };
}
function answer(env, status, body, extra = {}) {
  return new Response(body, { status, headers: { ...policyHeaders(env), ...extra } });
}
function refuse(env, status, why, extra = {}) {
  return answer(env, status, `intent-os board: ${why}\n`, { "Content-Type": "text/plain; charset=utf-8", ...extra });
}
function commitOf(env) {
  return (env && typeof env.BOARD_COMMIT === "string" && env.BOARD_COMMIT.trim()) || "unknown";
}

function jsonAnswer(env, status, value, extra = {}) {
  return answer(env, status, JSON.stringify(value), {
    "Content-Type": "application/json; charset=utf-8",
    ...extra,
  });
}

async function readBoundedBytes(stream, maxBytes) {
  if (!stream) return new Uint8Array();
  const reader = stream.getReader();
  const chunks = [];
  let size = 0;
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > maxBytes) {
      await reader.cancel("body limit exceeded");
      throw new Error("body is too large");
    }
    chunks.push(value);
  }
  const bytes = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return bytes;
}

async function readBoundedJson(request, maxBytes = MAX_JSON_BODY) {
  const contentType = (request.headers.get("Content-Type") || "").toLowerCase();
  if (!contentType.startsWith("application/json")) throw new Error("Content-Type must be application/json");
  const claimed = Number(request.headers.get("Content-Length") || "0");
  if (Number.isFinite(claimed) && claimed > maxBytes) throw new Error("JSON body is too large");
  const bytes = await readBoundedBytes(request.body, maxBytes);
  if (!bytes.byteLength) throw new Error("JSON body is required");
  let parsed;
  try { parsed = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
  catch { throw new Error("JSON body is invalid"); }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("JSON body must be an object");
  return parsed;
}

function resourceMinerOrigin(env) {
  const raw = env && typeof env.RESOURCE_MINER_ORIGIN === "string"
    ? env.RESOURCE_MINER_ORIGIN.trim() : "";
  if (!raw) return "";
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:" || url.username || url.password || url.search || url.hash
      || (url.pathname !== "/" && url.pathname !== "")) return "";
    return url.origin;
  } catch { return ""; }
}

function validIntentRequest(body) {
  const keys = Object.keys(body);
  if (keys.some((key) => !["objective", "source_mode"].includes(key))) return false;
  if (typeof body.objective !== "string" || body.objective.trim().length < 3
    || body.objective.trim().length > 500) return false;
  return body.source_mode === undefined || ["live", "snapshot"].includes(body.source_mode);
}

async function proxyIntent(request, env) {
  const origin = resourceMinerOrigin(env);
  if (!origin) return jsonAnswer(env, 503, { error: "Resource Miner is not configured for this cockpit." });
  let body;
  try { body = await readBoundedJson(request, 4096); }
  catch (error) { return jsonAnswer(env, 400, { error: error.message }); }
  if (!validIntentRequest(body)) return jsonAnswer(env, 400, { error: "Invalid objective or source_mode." });
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 45_000);
  try {
    const upstream = await fetch(`${origin}/api/intent`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        objective: body.objective.trim(),
        source_mode: body.source_mode || "live",
      }),
      redirect: "error",
      signal: controller.signal,
    });
    const contentType = (upstream.headers.get("Content-Type") || "").toLowerCase();
    const claimed = Number(upstream.headers.get("Content-Length") || "0");
    if (!contentType.startsWith("application/json")
      || (Number.isFinite(claimed) && claimed > MAX_MINER_RESPONSE)) {
      return jsonAnswer(env, 502, { error: "Resource Miner returned an invalid response." });
    }
    let bytes;
    try { bytes = await readBoundedBytes(upstream.body, MAX_MINER_RESPONSE); }
    catch { return jsonAnswer(env, 502, { error: "Resource Miner response was too large." }); }
    let value;
    try { value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)); }
    catch { return jsonAnswer(env, 502, { error: "Resource Miner returned invalid JSON." }); }
    return jsonAnswer(env, upstream.status, value, { "X-Resource-Miner-Mode": "AUTHENTICATED_PROXY" });
  } catch (error) {
    return jsonAnswer(env, 503, {
      error: error && error.name === "AbortError"
        ? "Resource Miner timed out." : "Resource Miner is unavailable.",
    });
  } finally { clearTimeout(timer); }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const readOnly = request.method === "GET" || request.method === "HEAD";
    if (url.pathname === "/healthz") {
      if (!readOnly) return refuse(env, 405, "read-only surface");
      return answer(env, 200, JSON.stringify({
        board: "ok",
        access_configured: configured(env),
        collaboration_configured: collaborationConfigured(env),
        resource_miner_configured: !!resourceMinerOrigin(env),
      }), { "Content-Type": "application/json" });
    }
    const v = await verifyAccessJwt(tokenFrom(request), env); // an unauthenticated request learns nothing but 401
    if (!v.ok) return refuse(env, v.status || 401, v.why); // 403 only for a valid token whose identity is not listed
    const stamp = { "X-Board-Commit": commitOf(env) }; // only a logged-in identity learns the commit
    if (url.pathname === "/api/session") {
      if (request.method !== "GET") return jsonAnswer(env, 405, { error: "GET required." }, stamp);
      if (!collaborationConfigured(env)) {
        return jsonAnswer(env, 503, { error: "Collaboration receipts are not configured." }, stamp);
      }
      try {
        return jsonAnswer(env, 200, {
          actor_id: await actorIdFor(v, env),
          authentication: "CLOUDFLARE_ACCESS_JWT_VERIFIED",
          identity_disclosure: "PSEUDONYMOUS_ACTOR_ID_ONLY",
          onboarding_storage: "BROWSER_LOCAL",
          authority_effect: "NONE",
          execution: "DISABLED",
        }, stamp);
      } catch { return jsonAnswer(env, 503, { error: "Verified session could not be created." }, stamp); }
    }
    if (url.pathname === "/api/intent") {
      if (request.method !== "POST") return jsonAnswer(env, 405, { error: "POST required." }, stamp);
      const response = await proxyIntent(request, env);
      const headers = new Headers(response.headers);
      headers.set("X-Board-Commit", stamp["X-Board-Commit"]);
      return new Response(response.body, { status: response.status, headers });
    }
    if (url.pathname === "/api/collaboration/attest") {
      if (request.method !== "POST") return jsonAnswer(env, 405, { error: "POST required." }, stamp);
      if (!collaborationConfigured(env)) {
        return jsonAnswer(env, 503, { error: "Collaboration receipts are not configured." }, stamp);
      }
      try {
        const body = await readBoundedJson(request);
        return jsonAnswer(env, 201, await issueAttestation(body, v, env), stamp);
      } catch (error) { return jsonAnswer(env, 400, { error: error.message }, stamp); }
    }
    if (url.pathname === "/api/collaboration/verify") {
      if (request.method !== "POST") return jsonAnswer(env, 405, { error: "POST required." }, stamp);
      try {
        const body = await readBoundedJson(request);
        const result = await verifyAttestationEnvelope(body, env);
        return jsonAnswer(env, result.valid ? 200 : 400, result, stamp);
      } catch (error) { return jsonAnswer(env, 400, { valid: false, reason: error.message }, stamp); }
    }
    if (!readOnly) return refuse(env, 405, "read-only surface", stamp);
    if (url.pathname === "/" || url.pathname === "/board" || url.pathname === "/board/") {
      return answer(env, 302, null, { Location: `${url.origin}${BOARD}`, ...stamp });
    }
    if (url.pathname === "/collaborate" || url.pathname === "/collaborate/") {
      return answer(env, 302, null, { Location: `${url.origin}${COLLABORATION}`, ...stamp });
    }
    if (!SERVED.has(url.pathname)) return refuse(env, 404, "not a page this surface serves", stamp);
    const res = await env.ASSETS.fetch(request);
    const headers = new Headers(res.headers);
    for (const [k, val] of Object.entries({ ...policyHeaders(env), ...stamp })) headers.set(k, val);
    return new Response(res.body, { status: res.status, headers });
  },
};

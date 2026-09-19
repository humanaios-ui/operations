// board/worker.mjs — the Intent-OS board and dashboard, served only behind a Cloudflare Access login.
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
//     under ui/ is reachable without passing the check above — and only the pages in SERVED are served at
//     all (the board, its four section pages, the test dashboard): the Z2 reviewer under ui/ reads
//     ../z1-inbox/ at runtime, which is not in the bundle, so it is not offered here rather than offered broken.
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
// the board, its four section pages (generated from it by tools/intent_os_pages_v1_0.py) and the test dashboard —
// nothing else under ui/ (the Z2 reviewer reads ../z1-inbox at runtime, which is not in the bundle)
const SERVED = new Set([BOARD, "/intent-os-decisions.html", "/intent-os-commitments.html", "/intent-os-records.html",
  "/intent-os-arena.html", "/intent-os-test-dashboard-v1_0.html"]);
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
  return { ok: true, email };
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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const readOnly = request.method === "GET" || request.method === "HEAD";
    if (url.pathname === "/healthz") {
      if (!readOnly) return refuse(env, 405, "read-only surface");
      return answer(env, 200, JSON.stringify({ board: "ok", access_configured: configured(env) }), { "Content-Type": "application/json" });
    }
    const v = await verifyAccessJwt(tokenFrom(request), env); // an unauthenticated request learns nothing but 401
    if (!v.ok) return refuse(env, v.status || 401, v.why); // 403 only for a valid token whose identity is not listed
    const stamp = { "X-Board-Commit": commitOf(env) }; // only a logged-in identity learns the commit
    if (!readOnly) return refuse(env, 405, "read-only surface", stamp);
    if (url.pathname === "/" || url.pathname === "/board" || url.pathname === "/board/") {
      return answer(env, 302, null, { Location: `${url.origin}${BOARD}`, ...stamp });
    }
    if (!SERVED.has(url.pathname)) return refuse(env, 404, "not a page this surface serves", stamp);
    const res = await env.ASSETS.fetch(request);
    const headers = new Headers(res.headers);
    for (const [k, val] of Object.entries({ ...policyHeaders(env), ...stamp })) headers.set(k, val);
    return new Response(res.body, { status: res.status, headers });
  },
};

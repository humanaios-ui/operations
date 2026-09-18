// board/worker.js — the Intent-OS board and dashboard, served only behind a Cloudflare Access login.
//
// Z2's direction (2026-09-18): "I don't want any public, I want to have to login to open the board."
// d17 (2026-09-14) ruled the board local only; d31 (z1-inbox/2026-09-18/Q-BOARD-PUBLISH-01.md) asks to
// replace that with this Worker. Until d31 is ruled and Access is configured, this Worker serves NOTHING:
//
//   * every request but /healthz must carry a Cloudflare Access JWT (header Cf-Access-Jwt-Assertion, or
//     the CF_Authorization cookie Access sets after login), signed by the team's current keys
//     (https://<ACCESS_TEAM_DOMAIN>/cdn-cgi/access/certs), issued for this application (aud == ACCESS_AUD),
//     not expired. Anything else is 401 — never the file.
//   * ACCESS_TEAM_DOMAIN and ACCESS_AUD unset → 401 "Access is not configured". Fails closed: a deploy
//     without the login in front of it publishes nothing.
//   * `assets.run_worker_first` in wrangler.jsonc makes this code run BEFORE the asset router, so no path
//     under ui/ is reachable without passing the check above.
//   * the relay is untouched: the board still POSTs to it cross-origin with its own HMAC and gate.
//
// Deployed by Cloudflare Workers Builds from this repository on every push to main (wrangler.jsonc at the
// root). No secrets live here: the team domain and the application audience are Worker variables set in
// the dashboard (kept across deploys by keep_vars).
//
// Self-test: `node board/worker.test.mjs` (no network; a generated key signs the test tokens).

const BOARD = "/intent-os-humanaios-v3_3.html";
const CERTS_TTL_MS = 5 * 60 * 1000;
let certCache = { domain: "", at: 0, keys: [] };

function b64url(s) {
  const pad = s.length % 4 === 0 ? "" : "=".repeat(4 - (s.length % 4));
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/") + pad);
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}
function decodeJson(seg) {
  return JSON.parse(new TextDecoder().decode(b64url(seg)));
}
function tokenFrom(request) {
  const h = request.headers.get("Cf-Access-Jwt-Assertion");
  if (h) return h;
  const cookie = request.headers.get("Cookie") || "";
  const m = /(?:^|;\s*)CF_Authorization=([^;]+)/.exec(cookie);
  return m ? m[1] : "";
}

/** The team's current signing keys, cached for CERTS_TTL_MS. */
export async function accessKeys(teamDomain, fetchFn = fetch, now = Date.now()) {
  if (certCache.domain === teamDomain && now - certCache.at < CERTS_TTL_MS && certCache.keys.length) return certCache.keys;
  const r = await fetchFn(`https://${teamDomain}/cdn-cgi/access/certs`);
  if (!r.ok) throw new Error(`certs endpoint answered ${r.status}`);
  const j = await r.json();
  const keys = Array.isArray(j.keys) ? j.keys : [];
  certCache = { domain: teamDomain, at: now, keys };
  return keys;
}
export function resetCertCache() {
  certCache = { domain: "", at: 0, keys: [] };
}

/**
 * Verify a Cloudflare Access JWT. Returns {ok, why, email}. Checks, in order: shape, alg RS256, issuer is
 * the team domain, audience includes this application, not expired, not before, then the RSA signature
 * against the key the header names. Nothing is trusted from the token until the signature verifies.
 */
export async function verifyAccessJwt(token, env, fetchFn = fetch, nowSec = Date.now() / 1000) {
  if (!env || !env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) return { ok: false, why: "Access is not configured on this Worker (ACCESS_TEAM_DOMAIN, ACCESS_AUD)" };
  if (!token) return { ok: false, why: "login required" };
  const parts = token.split(".");
  if (parts.length !== 3) return { ok: false, why: "malformed token" };
  let header, payload;
  try { header = decodeJson(parts[0]); payload = decodeJson(parts[1]); } catch { return { ok: false, why: "malformed token" }; }
  if (header.alg !== "RS256" || !header.kid) return { ok: false, why: "unsupported token" };
  if (payload.iss !== `https://${env.ACCESS_TEAM_DOMAIN}`) return { ok: false, why: "token is not from this team" };
  const aud = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!aud.includes(env.ACCESS_AUD)) return { ok: false, why: "token is not for this application" };
  if (typeof payload.exp !== "number" || payload.exp <= nowSec) return { ok: false, why: "token expired" };
  if (typeof payload.nbf === "number" && payload.nbf > nowSec + 60) return { ok: false, why: "token not yet valid" };
  let keys;
  try { keys = await accessKeys(env.ACCESS_TEAM_DOMAIN, fetchFn, nowSec * 1000); } catch (e) { return { ok: false, why: `could not read the team's keys: ${e.message}` }; }
  const jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk) return { ok: false, why: "token signed by an unknown key" };
  let ok = false;
  try {
    const key = await crypto.subtle.importKey("jwk", { kty: jwk.kty, n: jwk.n, e: jwk.e, alg: "RS256", ext: true }, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(parts[2]), new TextEncoder().encode(`${parts[0]}.${parts[1]}`));
  } catch { ok = false; }
  return ok ? { ok: true, email: payload.email || "" } : { ok: false, why: "bad signature" };
}

function refuse(status, why) {
  return new Response(`intent-os board: ${why}\n`, {
    status,
    headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store", "X-Robots-Tag": "noindex" },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const configured = !!(env.ACCESS_TEAM_DOMAIN && env.ACCESS_AUD);
    if (url.pathname === "/healthz") {
      return new Response(JSON.stringify({ board: "ok", access_configured: configured }), {
        headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
      });
    }
    const v = await verifyAccessJwt(tokenFrom(request), env);
    if (!v.ok) return refuse(401, v.why);
    if (url.pathname === "/" || url.pathname === "/board" || url.pathname === "/board/") {
      return Response.redirect(`${url.origin}${BOARD}`, 302);
    }
    if (request.method !== "GET" && request.method !== "HEAD") return refuse(405, "read-only surface");
    const res = await env.ASSETS.fetch(request);
    const headers = new Headers(res.headers);
    headers.set("Cache-Control", "no-store"); // a login-gated page is never cached by a proxy
    headers.set("X-Robots-Tag", "noindex");
    headers.set("Referrer-Policy", "no-referrer");
    return new Response(res.body, { status: res.status, headers });
  },
};

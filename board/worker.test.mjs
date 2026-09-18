// board/worker.test.mjs — the Worker's own proof that it fails closed. No network: a key generated here
// signs the test tokens and a stub stands in for the team's certs endpoint and for the asset router.
// Run: node board/worker.test.mjs   (exit 0 = PASS, 2 = FAIL)
import worker, { verifyAccessJwt, resetCertCache } from "./worker.js";

const enc = (o) => btoa(JSON.stringify(o)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

const TEAM = "example.cloudflareaccess.com", AUD = "aud-for-the-board";
const env = { ACCESS_TEAM_DOMAIN: TEAM, ACCESS_AUD: AUD };
const pair = await crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
const other = await crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
const jwk = await crypto.subtle.exportKey("jwk", pair.publicKey);
const KID = "kid-1";
let certsCalls = 0;
const fetchStub = async (url) => {
  certsCalls++;
  if (url !== `https://${TEAM}/cdn-cgi/access/certs`) return new Response("nope", { status: 404 });
  return new Response(JSON.stringify({ keys: [{ kid: KID, kty: jwk.kty, n: jwk.n, e: jwk.e, alg: "RS256", use: "sig" }] }), { headers: { "Content-Type": "application/json" } });
};
async function sign(payload, key = pair.privateKey, kid = KID) {
  const h = enc({ alg: "RS256", kid, typ: "JWT" }), p = enc(payload);
  const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, new TextEncoder().encode(`${h}.${p}`));
  return `${h}.${p}.${b64u(sig)}`;
}
const now = Math.floor(Date.now() / 1000);
const good = { iss: `https://${TEAM}`, aud: [AUD], exp: now + 600, iat: now, email: "night@example.test" };

let ok = true, n = 0;
function check(name, cond) { n++; ok &&= !!cond; console.log((cond ? "  ok  " : "  FAIL") + " " + name); }

// verifyAccessJwt: every refusal, then the one acceptance
check("unconfigured env → refused, names the two variables", !(await verifyAccessJwt("x", {}, fetchStub, now)).ok && /ACCESS_TEAM_DOMAIN/.test((await verifyAccessJwt("x", {}, fetchStub, now)).why));
check("no token → login required", (await verifyAccessJwt("", env, fetchStub, now)).why === "login required");
check("malformed token → refused", (await verifyAccessJwt("a.b", env, fetchStub, now)).why === "malformed token");
check("wrong issuer → refused", (await verifyAccessJwt(await sign({ ...good, iss: "https://other.cloudflareaccess.com" }), env, fetchStub, now)).why === "token is not from this team");
check("wrong audience → refused", (await verifyAccessJwt(await sign({ ...good, aud: ["someone-else"] }), env, fetchStub, now)).why === "token is not for this application");
check("expired → refused", (await verifyAccessJwt(await sign({ ...good, exp: now - 1 }), env, fetchStub, now)).why === "token expired");
check("unknown kid → refused", (await verifyAccessJwt(await sign(good, pair.privateKey, "kid-9"), env, fetchStub, now)).why === "token signed by an unknown key");
check("signed by another key → bad signature", (await verifyAccessJwt(await sign(good, other.privateKey), env, fetchStub, now)).why === "bad signature");
const tampered = (await sign(good)).split("."); tampered[1] = enc({ ...good, email: "attacker@example.test" });
check("payload edited after signing → bad signature", (await verifyAccessJwt(tampered.join("."), env, fetchStub, now)).why === "bad signature");
const v = await verifyAccessJwt(await sign(good), env, fetchStub, now);
check("valid token → ok, carries the email", v.ok && v.email === "night@example.test");
const before = certsCalls; await verifyAccessJwt(await sign(good), env, fetchStub, now);
check("the team's keys are cached between verifications", certsCalls === before);

// the fetch handler: healthz open, everything else gated, assets served with no-store
let assetCalls = 0;
const ASSETS = { fetch: async (req) => { assetCalls++; return new Response("<html>board</html>", { headers: { "Content-Type": "text/html", "ETag": "x" } }); } };
const envWithAssets = { ...env, ASSETS };
const req = (path, headers = {}, method = "GET") => new Request(`https://board.example.test${path}`, { headers, method });
globalThis.fetch = fetchStub; resetCertCache();
let r = await worker.fetch(req("/healthz"), { ASSETS });
check("/healthz answers without a login and says Access is not configured", r.status === 200 && (await r.json()).access_configured === false);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html"), { ASSETS });
check("unconfigured Worker never serves the board (401, no asset fetch)", r.status === 401 && assetCalls === 0);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html"), envWithAssets);
check("configured, no login → 401, no asset fetch", r.status === 401 && assetCalls === 0 && /login required/.test(await r.text()));
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": await sign({ ...good, aud: ["x"] }) }), envWithAssets);
check("wrong application's token → 401, no asset fetch", r.status === 401 && assetCalls === 0);
const tok = await sign(good);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": tok }), envWithAssets);
check("valid header token → the board, Cache-Control no-store, noindex", r.status === 200 && assetCalls === 1 && r.headers.get("Cache-Control") === "no-store" && r.headers.get("X-Robots-Tag") === "noindex");
r = await worker.fetch(req("/intent-os-test-dashboard-v1_0.html", { Cookie: `foo=1; CF_Authorization=${tok}` }), envWithAssets);
check("valid cookie token → the dashboard", r.status === 200 && assetCalls === 2);
r = await worker.fetch(req("/", { "Cf-Access-Jwt-Assertion": tok }), envWithAssets);
check("/ → redirect to the board", r.status === 302 && r.headers.get("Location") === "https://board.example.test/intent-os-humanaios-v3_3.html");
r = await worker.fetch(req("/", {}), envWithAssets);
check("/ without a login → 401, not a redirect", r.status === 401);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": tok }, "POST"), envWithAssets);
check("POST → 405 (read-only surface)", r.status === 405);

console.log(`${n} checks · SELF-TEST ${ok ? "PASS" : "FAIL"}`);
process.exit(ok ? 0 : 2);

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
const good = { iss: `https://${TEAM}`, aud: [AUD], exp: now + 600, iat: now, nbf: now - 5, email: "night@example.test" };

let ok = true, n = 0;
function check(name, cond) { n++; ok &&= !!cond; console.log((cond ? "  ok  " : "  FAIL") + " " + name); }
const why = async (tok, e = env) => (await verifyAccessJwt(tok, e, fetchStub, now)).why;

// verifyAccessJwt: every refusal, then the one acceptance
check("unconfigured env → refused, names the two variables", /ACCESS_TEAM_DOMAIN/.test(await why("x", {})));
check("no token → login required", (await why("")) === "login required");
check("two segments → malformed", (await why("a.b")) === "malformed token");
check("segments that decode to JSON null → malformed, not a throw", (await why(`${enc(null)}.${enc(null)}.AAAA`)) === "malformed token");
check("segments that decode to a JSON array → malformed", (await why(`${enc([1])}.${enc([2])}.AAAA`)) === "malformed token");
check("segments that are not base64 JSON → malformed", (await why("!!.!!.!!")) === "malformed token");
check("header without kid → unsupported", (await why(`${enc({ alg: "RS256" })}.${enc(good)}.AAAA`)) === "unsupported token");
check("wrong issuer → refused", (await why(await sign({ ...good, iss: "https://other.cloudflareaccess.com" }))) === "token is not from this team");
check("wrong audience → refused", (await why(await sign({ ...good, aud: ["someone-else"] }))) === "token is not for this application");
check("expired → refused", (await why(await sign({ ...good, exp: now - 1 }))) === "token expired");
check("nbf one second in the future → refused (no skew allowance)", (await why(await sign({ ...good, nbf: now + 1 }))) === "token not yet valid");
check("nbf equal to now → accepted", (await verifyAccessJwt(await sign({ ...good, nbf: now }), env, fetchStub, now)).ok);
check("nbf present but a string (a future value encoded as text) → malformed, not skipped", (await why(await sign({ ...good, nbf: String(now + 600) }))) === "malformed token");
check("nbf present but null → malformed", (await why(await sign({ ...good, nbf: null }))) === "malformed token");
check("exp as a string → refused", (await why(await sign({ ...good, exp: String(now + 600) }))) === "token expired");
check("unknown kid → refused", (await why(await sign(good, pair.privateKey, "kid-9"))) === "token signed by an unknown key");
check("signed by another key → bad signature", (await why(await sign(good, other.privateKey))) === "bad signature");
const tampered = (await sign(good)).split("."); tampered[1] = enc({ ...good, email: "attacker@example.test" });
check("payload edited after signing → bad signature", (await why(tampered.join("."))) === "bad signature");
const v = await verifyAccessJwt(await sign(good), env, fetchStub, now);
check("valid token → ok, carries the email", v.ok && v.email === "night@example.test");
const before = certsCalls; await verifyAccessJwt(await sign(good), env, fetchStub, now);
check("the team's keys are cached between verifications", certsCalls === before);

// the fetch handler: healthz open, everything else gated, only the two pages served, every answer no-store
let assetCalls = 0;
const ASSETS = { fetch: async () => { assetCalls++; return new Response("<html>board</html>", { headers: { "Content-Type": "text/html", "ETag": "x" } }); } };
const envWithAssets = { ...env, ASSETS };
const req = (path, headers = {}, method = "GET") => new Request(`https://board.example.test${path}`, { headers, method });
const policy = (r) => r.headers.get("Cache-Control") === "no-store" && r.headers.get("X-Robots-Tag") === "noindex" && r.headers.get("Referrer-Policy") === "no-referrer";
globalThis.fetch = fetchStub; resetCertCache();
let r = await worker.fetch(req("/healthz"), { ASSETS });
check("/healthz answers without a login, says Access is not configured, no-store", r.status === 200 && (await r.json()).access_configured === false && policy(r));
r = await worker.fetch(req("/healthz", {}, "POST"), { ASSETS });
check("POST /healthz → 405", r.status === 405);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html"), { ASSETS });
check("unconfigured Worker never serves the board (401, no asset fetch)", r.status === 401 && assetCalls === 0 && policy(r));
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html"), envWithAssets);
check("configured, no login → 401, no asset fetch", r.status === 401 && assetCalls === 0 && /login required/.test(await r.text()));
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": await sign({ ...good, aud: ["x"] }) }), envWithAssets);
check("wrong application's token → 401, no asset fetch", r.status === 401 && assetCalls === 0);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": `${enc(null)}.${enc(null)}.AAAA` }), envWithAssets);
check("null-JSON token → 401, never a 500", r.status === 401);
r = await worker.fetch(req("/", {}, "POST"), envWithAssets);
check("POST / without a login → 401 (the method is not judged before the login)", r.status === 401);
const tok = await sign(good);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": tok }), envWithAssets);
check("valid header token → the board, with the policy headers", r.status === 200 && assetCalls === 1 && policy(r));
r = await worker.fetch(req("/intent-os-test-dashboard-v1_0.html", { Cookie: `foo=1; CF_Authorization=${tok}` }), envWithAssets);
check("valid cookie token → the dashboard", r.status === 200 && assetCalls === 2);
r = await worker.fetch(req("/", { "Cf-Access-Jwt-Assertion": tok }), envWithAssets);
check("/ → redirect to the board, with the policy headers", r.status === 302 && r.headers.get("Location") === "https://board.example.test/intent-os-humanaios-v3_3.html" && policy(r));
r = await worker.fetch(req("/", {}), envWithAssets);
check("/ without a login → 401, not a redirect", r.status === 401);
r = await worker.fetch(req("/", { "Cf-Access-Jwt-Assertion": tok }, "POST"), envWithAssets);
check("POST / with a login → 405, not a redirect", r.status === 405);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": tok }, "POST"), envWithAssets);
check("POST a page with a login → 405", r.status === 405);
r = await worker.fetch(req("/z2-ratification-reviewer.html", { "Cf-Access-Jwt-Assertion": tok }), envWithAssets);
check("the Z2 reviewer (reads ../z1-inbox at runtime) is not served: 404, no asset fetch", r.status === 404 && assetCalls === 2);
r = await worker.fetch(req("/anything-else.html", { "Cf-Access-Jwt-Assertion": tok }), envWithAssets);
check("an unlisted path with a login → 404, no asset fetch", r.status === 404 && assetCalls === 2);

console.log(`${n} checks · SELF-TEST ${ok ? "PASS" : "FAIL"}`);
process.exit(ok ? 0 : 2);

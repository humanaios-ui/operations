// board/worker.test.mjs — the Worker's own proof that it fails closed. No network: a key generated here
// signs the test tokens and a stub stands in for the team's certs endpoint and for the asset router.
// Run: node board/worker.test.mjs   (exit 0 = PASS, 2 = FAIL)
import worker, { verifyAccessJwt, resetCertCache, policyHeaders } from "./worker.mjs";

const enc = (o) => btoa(JSON.stringify(o)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const b64u = (buf) => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

const TEAM = "example.cloudflareaccess.com", AUD = "aud-for-the-board";
const env = { ACCESS_TEAM_DOMAIN: TEAM, ACCESS_AUD: AUD, ACCESS_ALLOWED_EMAILS: "Night@Example.test, second@example.test" };
const gen = () => crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: 2048, publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"]);
const pair = await gen(), other = await gen(), rotated = await gen();
const pub = async (k) => { const j = await crypto.subtle.exportKey("jwk", k.publicKey); return { kty: j.kty, n: j.n, e: j.e, alg: "RS256", use: "sig" }; };
const KID = "kid-1", KID2 = "kid-2";
let KEYS = [{ kid: KID, ...(await pub(pair)) }]; // what the stubbed certs endpoint serves right now
let certsDown = false, certsCalls = 0;
const fetchStub = async (url) => {
  certsCalls++;
  if (url !== `https://${TEAM}/cdn-cgi/access/certs`) return new Response("nope", { status: 404 });
  if (certsDown) return new Response("unavailable", { status: 503 });
  return new Response(JSON.stringify({ keys: KEYS }), { headers: { "Content-Type": "application/json" } });
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
const why = async (tok, e = env, at = now) => (await verifyAccessJwt(tok, e, fetchStub, at)).why;

// verifyAccessJwt: every refusal, then the one acceptance
check("unconfigured env → refused, names the three variables", /ACCESS_TEAM_DOMAIN.*ACCESS_AUD.*ACCESS_ALLOWED_EMAILS/.test(await why("x", {})));
check("team and audience set but no allow-list → still not configured (fails closed)", /not configured/.test(await why("x", { ACCESS_TEAM_DOMAIN: TEAM, ACCESS_AUD: AUD })));
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
check("signed by another key → bad signature", (await why(await sign(good, other.privateKey))) === "bad signature");
const tampered = (await sign(good)).split("."); tampered[1] = enc({ ...good, email: "attacker@example.test" });
check("payload edited after signing → bad signature", (await why(tampered.join("."))) === "bad signature");
const v = await verifyAccessJwt(await sign(good), env, fetchStub, now);
check("valid token for a listed identity → ok, carries the email (list compared case-insensitively)", v.ok && v.email === "night@example.test");
const notListed = await verifyAccessJwt(await sign({ ...good, email: "stranger@example.test" }), env, fetchStub, now);
check("valid token for an identity NOT on the list → refused as 403, not accepted (authorization is the Worker's, not only the policy's)", !notListed.ok && notListed.status === 403 && /allow-list/.test(notListed.why));
const noEmail = await verifyAccessJwt(await sign({ ...good, email: undefined }), env, fetchStub, now);
check("valid token with no email claim (a service token) → refused", !noEmail.ok && noEmail.status === 403);
check("an unsigned claim of a listed email → still bad signature (the list is checked only after the signature)", (await why(await sign({ ...good }, other.privateKey))) === "bad signature");
let before = certsCalls; await verifyAccessJwt(await sign(good), env, fetchStub, now);
check("the team's keys are cached between verifications", certsCalls === before);

// the key cache: rotation inside the TTL, unknown-kid rate limit, last-known-good when the endpoint fails
before = certsCalls;
check("unknown kid right after a fetch → refused without another fetch (probe rate limit)", (await why(await sign(good, rotated.privateKey, KID2))) === "token signed by an unknown key" && certsCalls === before);
KEYS = [...KEYS, { kid: KID2, ...(await pub(rotated)) }]; // Cloudflare rotates: a second key appears
before = certsCalls;
const r1 = await verifyAccessJwt(await sign(good, rotated.privateKey, KID2), env, fetchStub, now + 60);
check("a kid the snapshot does not know, 60 s later → one forced refresh, then accepted", r1.ok && certsCalls === before + 1);
certsDown = true; before = certsCalls;
const r2 = await verifyAccessJwt(await sign({ ...good, exp: now + 2 * 3600 }), env, fetchStub, now + 3600); // snapshot is stale (> TTL), endpoint down
check("certs endpoint down, snapshot one hour old → last known good is used", r2.ok && certsCalls === before + 1);
const r3 = await verifyAccessJwt(await sign({ ...good, exp: now + 30 * 3600 }), env, fetchStub, now + 25 * 3600);
check("certs endpoint down, snapshot older than the hard bound → fails closed", !r3.ok && /could not read the team's keys/.test(r3.why));
certsDown = false; resetCertCache(); KEYS = [KEYS[0]];

// the fetch handler: healthz open, everything else gated, only the two pages served, every answer policy-headed
let assetCalls = 0;
const ASSETS = { fetch: async () => { assetCalls++; return new Response("<html>board</html>", { headers: { "Content-Type": "text/html", "ETag": "x" } }); } };
const envWithAssets = { ...env, ASSETS };
const req = (path, headers = {}, method = "GET") => new Request(`https://board.example.test${path}`, { headers, method });
const policy = (r) => ["Cache-Control", "X-Robots-Tag", "Referrer-Policy", "X-Content-Type-Options", "X-Frame-Options", "Content-Security-Policy"].every((h) => r.headers.get(h) === policyHeaders(env)[h]);
globalThis.fetch = fetchStub;
let r = await worker.fetch(req("/healthz"), { ASSETS });
check("/healthz answers without a login, says Access is not configured, policy-headed, no commit", r.status === 200 && (await r.json()).access_configured === false && policy(r) && !r.headers.get("X-Board-Commit"));
r = await worker.fetch(req("/healthz", {}, "POST"), { ASSETS });
check("POST /healthz → 405", r.status === 405);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html"), { ASSETS });
check("unconfigured Worker never serves the board (401, no asset fetch)", r.status === 401 && assetCalls === 0 && policy(r));
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html"), envWithAssets);
check("configured, no login → 401, no asset fetch, no commit header", r.status === 401 && assetCalls === 0 && /login required/.test(await r.text()) && !r.headers.get("X-Board-Commit"));
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": await sign({ ...good, aud: ["x"] }) }), envWithAssets);
check("wrong application's token → 401, no asset fetch", r.status === 401 && assetCalls === 0);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": `${enc(null)}.${enc(null)}.AAAA` }), envWithAssets);
check("null-JSON token → 401, never a 500", r.status === 401);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": await sign({ ...good, email: "stranger@example.test" }) }), envWithAssets);
check("valid token, identity not on the list → 403, no asset fetch, no commit header", r.status === 403 && assetCalls === 0 && !r.headers.get("X-Board-Commit"));
r = await worker.fetch(req("/", {}, "POST"), envWithAssets);
check("POST / without a login → 401 (the method is not judged before the login)", r.status === 401);
const tok = await sign(good);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { Cookie: `CF_Authorization=${tok}` }), envWithAssets);
check("a valid token offered only as the CF_Authorization cookie → 401 (the header is the one source)", r.status === 401 && assetCalls === 0);
r = await worker.fetch(req("/intent-os-humanaios-v3_3.html", { "Cf-Access-Jwt-Assertion": tok }), envWithAssets);
check("valid header token → the board, with the policy headers, commit 'unknown' when BOARD_COMMIT is unset", r.status === 200 && assetCalls === 1 && policy(r) && r.headers.get("X-Board-Commit") === "unknown");
r = await worker.fetch(req("/intent-os-test-dashboard-v1_0.html", { "Cf-Access-Jwt-Assertion": tok }), { ...envWithAssets, BOARD_COMMIT: "abc1234" });
check("valid token → the dashboard, X-Board-Commit names the deployed commit", r.status === 200 && assetCalls === 2 && r.headers.get("X-Board-Commit") === "abc1234");
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
const csp = policyHeaders(env)["Content-Security-Policy"];
check("CSP: no default source, inline script/style for the single-file pages, the relay and the live read as the only connect targets, unframeable", /default-src 'none'/.test(csp) && /connect-src 'self' https:\/\/intent-os-relay-production\.up\.railway\.app https:\/\/raw\.githubusercontent\.com;/.test(csp) && /frame-ancestors 'none'/.test(csp));
check("CSP_CONNECT_SRC overrides the connect targets when the relay moves", /connect-src 'self' https:\/\/relay\.example\.test;/.test(policyHeaders({ ...env, CSP_CONNECT_SRC: "https://relay.example.test" })["Content-Security-Policy"]));

console.log(`${n} checks · SELF-TEST ${ok ? "PASS" : "FAIL"}`);
process.exit(ok ? 0 : 2);

# Server-Side Key Proxy — Spec (so the console never holds a key)

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Status:** Spec / reference implementation — **Night deploys**
**Fixes:** RAH API key + Anthropic key currently live in the console's client-side JS (full-account-takeover exposure).

---

## The rule
**Secrets live on a server the browser can't read. The browser talks only to *your* proxy; the proxy injects the keys and forwards.** No key ever reaches the client.

You already run Cloudflare Workers (the `ops.humanaios.ai` Worker with `/api/project-state`, `/api/jobs-state`). So the proxy is one more Worker — same stack, minimal new surface.

```
Browser (console)  ──►  Cloudflare Worker (holds secrets)  ──►  rentahuman.ai/api
   no keys                RAH_API_KEY, ANTHROPIC_API_KEY          api.anthropic.com
   behind Access          + zone gate + allowlist
```

---

## Layer 1 — Gate the console (identity)
The console is an internal "Unit Zero" tool, so put the **whole thing behind Cloudflare Access** (Zero Trust). Only Night's verified identity can load the page *or* call the Worker. This means even a stolen proxy URL is useless without Night's login.
- Access policy: allow only Night's email(s).
- The Worker verifies the `Cf-Access-Jwt-Assertion` header on every request (defense in depth — reject anything without a valid Access JWT).

## Layer 2 — The Worker proxy (holds the keys)

**Secrets (set once, never in code/repo):**
```bash
wrangler secret put RAH_API_KEY          # the NEW rotated key
wrangler secret put ANTHROPIC_API_KEY
# Access app audience for JWT verification:
wrangler secret put CF_ACCESS_AUD
```

**`wrangler.toml`**
```toml
name = "haios-console-proxy"
main = "src/worker.js"
compatibility_date = "2026-01-01"
# routes = ["console.humanaios.ai/api/*"]   # bind to the console's origin
```

**`src/worker.js`** (reference sketch)
```js
const RAH_BASE = "https://rentahuman.ai/api";
const ALLOW_ORIGIN = "https://console.humanaios.ai";

// Zone model: read = open (behind Access); write/spend = requires explicit confirm token
const READ = [/^\/humans/, /^\/services/, /^\/bounties(\/[^/]+)?$/, /^\/rentals$/,
              /^\/bookings/, /^\/conversations(\/[^/]+)?$/, /^\/account\/status/];
const CONFIRM_REQUIRED = [/^\/rentals$/, /^\/bounties$/, /^\/conversations\/[^/]+\/messages/,
                          /^\/rentals\/[^/]+/, /^\/bounties\/[^/]+\/applications\/[^/]+\/(accept|reject)/];
const BLOCKED = [/^\/keys/];  // key management NEVER via the browser proxy — CLI only

export default {
  async fetch(req, env) {
    // 1) identity: require a valid Cloudflare Access JWT
    if (!(await verifyAccess(req, env))) return json(401, { error: "unauthorized" });

    const url = new URL(req.url);
    const path = url.pathname.replace(/^\/rah/, "");     // browser calls /rah/<endpoint>
    const method = req.method;

    // 2) hard blocks (key mgmt stays on the CLI)
    if (BLOCKED.some(r => r.test(path))) return json(403, { error: "blocked: use CLI for key management" });

    // 3) zone gate: writes/spends need an explicit per-action confirm header
    const isWrite = method !== "GET";
    if (isWrite && CONFIRM_REQUIRED.some(r => r.test(path))) {
      if (req.headers.get("X-Confirm-Action") !== "yes") {
        return json(428, { error: "confirmation_required", note: "Z3: re-send with X-Confirm-Action: yes" });
      }
    }

    // 4) forward with the injected key (never exposed to the browser)
    const upstream = await fetch(RAH_BASE + path + url.search, {
      method,
      headers: { "X-API-Key": env.RAH_API_KEY, "Content-Type": "application/json" },
      body: isWrite ? await req.text() : undefined,
    });
    return withCors(new Response(await upstream.text(), {
      status: upstream.status, headers: { "Content-Type": "application/json" },
    }));
  },
};

// AI compose: proxy Anthropic so the key stays server-side
async function aiCompose(req, env) { /* forward to api.anthropic.com with env.ANTHROPIC_API_KEY */ }

function json(status, obj) { return withCors(new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } })); }
function withCors(res) { res.headers.set("Access-Control-Allow-Origin", ALLOW_ORIGIN); res.headers.set("Vary", "Origin"); return res; }
async function verifyAccess(req, env) { /* validate Cf-Access-Jwt-Assertion against env.CF_ACCESS_AUD + team certs */ return true; }
```

## Layer 3 — Console changes (remove all secrets)
In the console's `<script>`:
```diff
- const API_KEY = 'rah_...';                       // DELETE
- const BASE = 'https://rentahuman.ai/api';
+ const BASE = '/rah';                              // talk to the proxy, not RAH directly

  async function get(path)  { const r = await fetch(BASE + path); return r.json(); }        // no X-API-Key
  async function post(path, body, confirm) {
    const h = { 'Content-Type': 'application/json' };
+   if (confirm) h['X-Confirm-Action'] = 'yes';     // set only after an explicit UI confirm
    const r = await fetch(BASE + path, { method:'POST', headers:h, body: JSON.stringify(body) });
    return r.json();
  }
```
- The AI-compose call goes to `'/ai/compose'` on the proxy (not `api.anthropic.com`).
- Any button that spends/hires must set `confirm` only *after* a real confirm dialog — that maps the RAH **Z3 halt** into the UI.

---

## Security checklist (before this goes anywhere public)
- [ ] Old key `rah_***REDACTED***` revoked ✅ (done); new key **only** in `wrangler secret`, never in a file/repo/browser.
- [ ] Console served behind **Cloudflare Access**; Worker verifies the Access JWT.
- [ ] `/keys/*` blocked at the proxy — key management stays on the CLI.
- [ ] Write/spend endpoints require `X-Confirm-Action` (Z3 in the UI).
- [ ] CORS locked to the console origin; no `*`.
- [ ] Anthropic call proxied; no LLM key in the browser.
- [ ] Worker never echoes secrets in responses/logs.
- [ ] (Optional) rate-limit + a small audit log of write actions → your `job_ledger`/ops.

---

## What I need from you
- This is a **spec**; deploying the Worker + Access policy is yours (it touches infra + the new secret). If you want, I can flesh the sketch into a complete `worker.js` + `wrangler.toml` in the repo (still zero secrets) so you can `wrangler deploy` it. Say the word.

*(Next in the sequence: Post 5 → repurpose.py → Notes bank → Recommendations tracker → scheduler comparison.)*

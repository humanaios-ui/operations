# RentAHuman (RAH) — Integration Concept & Queue (Z1 analysis)

**Practice:** empirica-outreach · **For:** Carly R. Anderson / HumanAIOS
**Date:** 2026-07-02 · **Zone:** Z1 analysis — **nothing here is executed; all outward/financial steps are Z2/Z3-gated for Night**
**Sources (reference):** the HumanAIOS×RentAHuman console (API surface) + the S-060326 "HARMONIZATION" orchestration ratification doc.

---

## 🔴 Do this first — two security items (blocking)

1. **Rotate the exposed API key.** The console pastes a live key (`rah_***REDACTED***`) directly into client-side JS. Because the `/keys` endpoints let a key **create and revoke other keys**, an exposed key is full account takeover — not just read. Revoke it and issue a new one. *(I have not used it and have not committed it.)*
2. **Never put the key — or an Anthropic key — in the browser.** The console does two unsafe things: (a) hardcodes the RAH key client-side, and (b) calls `api.anthropic.com` from the browser. Both leak secrets to anyone who opens the page. **Move all key-holding calls server-side** (a tiny proxy/worker holds the keys; the browser talks only to your proxy). This is the single most important backend fix before RAH goes anywhere near public.

*Everything below assumes those two are handled.*

---

## Part 1 — What RAH actually is (backend read)

**Two layers:**

- **API surface** (REST at `rentahuman.ai/api`, `X-API-Key` auth; mirrored by the `rentahuman-mcp` server we queued):
  - *Discovery:* `/humans`, `/services`, `/bounties`
  - *Hire (financial):* `/bounties` (post), `/rentals` (create → **Stripe escrow checkout**), `/bookings`
  - *Manage:* applications accept/reject, `/rentals/:id` release payment, cancel
  - *Comms:* `/conversations` (start/read/send)
  - *Account:* `/account/status`, `/keys` (create/revoke/webhook)
- **Orchestration spine** (from S-060326, *pending Z2*):
  - **LangGraph** orchestrator (`job_orchestrator_v1_0.py`) with **zone halts** — Z3 actions stop for Night.
  - **Migration 006** Supabase schema: `jobs_v1`, `job_subtasks_v1`, `job_humans_v1`, `job_deliverables_v1`, `job_ledger_v1` (append-only), and the key one — **`job_acat_link_v1`**.
  - **Governance triggers:** harmony gate (no `delivered` without an ACAT link), P-ANON gate (no `release` without `anon_check_pass`), touch.

**The load-bearing idea:** `job_acat_link_v1` makes **every income run a live ACAT behavioral session.** "An income stream that *is* the research." That's the whole integration thesis.

---

## Part 2 — The integration concept: RAH's three roles

### Role A — Attraction (this is where it meets the outreach plan)
- **RAH is the mission made concrete — and it's the single most attention-worthy story you have.** "We built an instrument that measures whether AI tells the truth about itself. Then we built an AI that *hires humans* to do real work, funds recovery with the profit, and measures *that* behavior too." Nobody else has this. It's Tradition-11-perfect: you *manifest* the mission instead of describing it.
- **It resolves the "stray surface" open item.** `rentahuman.ai` stops being an un-inventoried link and becomes a **defined node** in the entity graph — the mission layer of HumanAIOS. (It still must respect P-ANON: no worker/client identities on public surfaces.)
- **It's a content engine for The Witness Stand.** The AI-orchestrates-humans research is genuinely novel and publishable:
  - **Post 5 (the mission bridge)** now has its concrete answer: *how does behavioral observability serve recovery-funded employment?* → RAH is the answer.
  - New research-angle posts/Notes: "What happens to behavior when an AI orchestrates humans vs. runs solo?" — original data, not commentary.

### Role B — Research utility
- Every RAH job → an ACAT behavioral observation environment (via `job_acat_link_v1`). This produces **corpus data no one else has** (AI-in-the-loop-with-humans behavior) — a data moat that strengthens the exact research-authority the P0 plan is building.
- Feeds the preprint's "motivating examples from deployed systems" line (the Sakana parallel in S-060326): a live system whose self-report can be checked against demonstrated behavior.

### Role C — Collaboration
- The `/conversations` layer + the worker-cooperative structure is the collaboration substrate (P-ANON-protected). Ties to the collaborator network referenced in the governance doc — **none of whom get named publicly** until they self-attribute.

---

## Part 3 — How it plugs into the *entire* plan (concrete)

| Plan area | RAH integration |
|---|---|
| **Entity graph (P0-3)** | Give `rentahuman.ai` a defined role + one clean cross-link (mission layer). No worker/client data exposed. Closes the "rentahuman.ai keep/fold/drop" decision → **keep, as the mission node.** |
| **Substack (Witness Stand)** | Post 5 = the RAH mission bridge; add an AI+human-orchestration research thread; Notes from live-but-anonymized job patterns. |
| **Preprint / authority** | RAH runs → new ACAT corpus → citable behavioral data; "deployed system" motivating example. |
| **Distribution** | RAH is *manifested*, not promoted — it's a discovery surface, not a CTA. Univerze = passive presence only (per S-060326). |
| **Automation** | The `rentahuman-mcp` server (queued in `.mcp.json`) is how *I* could later assist with **read-only** RAH work (browse humans/bounties/status) once you've authenticated — never booking/spending without your per-action yes. |

---

## Part 4 — Guardrails (what stays gated, and my boundary)

- **Z2/Z3 gating honored.** Migration 006 = **not applied** (pending `Z2-MIG-006` + its 3 flag checks). Service offering, channels, key config = pending `Z2-RAH-01/02`. I produce Z1 analysis; **Night ratifies and executes Z3.**
- **Financial actions are yours.** Posting a bounty, creating a rental (Stripe escrow), releasing payment, booking a human = real money + real people. **I never execute these without your explicit, per-action confirmation** — and per the governance model they're Night's Z3 anyway.
- **P-ANON is absolute.** No worker or client identity in public surfaces, in committed files, or in anything I write. `client_ref` opaque labels only.
- **Key hygiene.** Keys live server-side, rotated, never in a committed file or the browser.
- **My use of the RAH MCP, when you're ready:** read-only browse/status to support research + content. Any write/hire/spend stops for your approval.

---

## Part 5 — Queued roadmap (PENDING — not started)

Logged as a **planned** empirica goal. Ordered; each step names its gate.

| # | Step | Gate | Who |
|---|---|---|---|
| 0 | **Rotate the leaked key + move keys server-side** | — | Night (now) |
| 1 | Ratify the RAH-as-mission-node framing for the entity graph | Z2 | Night |
| 2 | Verify Migration 006's 3 flags (FK type, zone-halt split, migration number) — read-only checks | Z2-MIG-006 | Night (I can help draft the verify queries once Supabase is authed) |
| 3 | Draft Post 5 (mission bridge) using RAH — P-ANON-clean, TRL 2-3 | — | I draft → Night |
| 4 | Draft the AI+human-orchestration research angle (post/Notes) | — | I draft → Night |
| 5 | (When live) read-only RAH browse via MCP to ground content | needs auth | I assist |
| 6 | First service offering ("AI Research Synthesis Report") listing copy | Z2-RAH-01 | I draft → Night publishes |

---

## What I need from you
1. **Confirm the key is rotated** (and whether you want help redesigning the console to hold keys server-side — I can spec that).
2. **Pick the first draftable, non-gated step:** Post 5 (mission bridge) or the AI+human-orchestration research angle — both I can write now, P-ANON-clean, no execution.
3. Everything financial/migration/outward stays parked behind Night's ratification, as designed.

# Research → Production plan v0.1
Z1 · 2026-09-05 · candidate for Z2 · all stages LAID · operated 0/40

## What the mesh gives us (site read 09-05, CLAIM+LINK; repos not read — rate limit)
| Empirica capability | Our node it matches | Note |
|---|---|---|
| `preflight` → `check` (Sentinel) → `postflight` | Z1 proposes → CI gate → MEASURE at window close | Same gate shape. Their postflight "measure belief against evidence" is our calibration-ledger write. |
| A practice keeps a calibrated record from day one | NF_LEDGER + event chains | Their record is per-practice; ours is one hash-chained log. Merkle root + OTS is the piece they don't advertise. |
| "Never act on shared work without your sign-off" | Z2 ratification | Their sign-off is a click; ours is a hash. Gap to close in stage 4. |
| Extension + ntfy phone approvals | z2_ledger on phone | Productized version of what you built by hand. |
| Cortex mesh (early access) | callout routing + Priority Queue | Routing exists; scoring (impact + unblocks + λ·EIG) does not appear on the site. |
| `ecodex` (Codex harness, alpha) | multi-substrate audit | Second substrate with the same discipline — pairs with Q-ORCA-01. |
| 15 practices on empirica-foundation.carly | the whiteboard pipeline + governance nodes | Mapped in empirica_mesh_map_090526.md. All self-reported. |

## The production line
Each stage has an input, a gate, an output, the spec it satisfies, the market condition it answers, and the falsifier that closes it. A stage is not complete when its machinery exists; it is complete when its output has a receipt.

### Stage 0 — Provenance reconciliation (this week)
Input: PAT; live REGISTERED.md; EmpiricaAI/empirica repo tarball. Gate: IC-030 read; hashes for the 09-05 patch set. Output: ratified candidate block; ruling on the GRBS/Empirica relationship; empirica repo read (does postflight write a hashable record?). Spec: none. Market: none. Falsifier: if the empirica record cannot be hashed and anchored, stage 4 cannot run on it and needs our own log underneath.

### Stage 1 — First operated cycles (Sep 15–Oct 1)
Input: resource-miner reactivation (mesh says Sep 15) = the job-posting intake batch. Gate: prereg hash ratified before the run. Output: MDU/GRBS pipeline (RM → SS → LMO → OA) cycles counted; first base rates; 0/40 becomes n/40. Spec: NIST AI RMF "Measure" function; ISO/IEC 42001 monitoring clause (VERIFIED earlier). Market: none needed — this is internal. Falsifier: if RM does not reactivate by Sep 19 (its own extended SLA), the mesh's calendar is the first pin to resolve NO, and intake must be run by hand from the whiteboard's "scan job market."
SS (Schema.sql) is absent from the mesh — GAP; it is stage 2 of the pipeline and blocks stage 3.

### Stage 2 — Behavior-audit intake (post gate in code; 10 engagements, Sep–Oct)
Input: agency-agents Discussions post (GTM-01); IC-SCOPE-05 in code. Gate: signed scope hash + pinned criteria hash before any tool runs. Output: 10 engagements → find rate per bug class, hours per engagement, WTP, conversion at 60–90 days; every engagement is an intake batch. Delivery vehicle option: client installs `empirica` (MIT); our tools read its record — no client infrastructure to build. Spec: OWASP Top 10 for LLM Apps 2025; OWASP GenAI Red Teaming Guide (rules of engagement, authorization); provider usage policies (OpenAI/Anthropic/Google — injection probes on Anthropic-backed targets need Anthropic's prior authorization) — all VERIFIED 09-04. Market: HackerOne +540% prompt-injection reports; vendor consolidation vacating the low end; agency-agents at 150K stars is the population. Falsifier: F-BUGCLASS-01 — find rate <10% across ten engagements.

### Stage 3 — Learning Trajectory operated (Oct)
Input: Z2 pins via the extension/ntfy path or z2_ledger v1.8; the ~55 mesh deliverables (Sep 12–Oct 3) as pre-resolved pins; Metaculus Q1–Q3. Gate: H-LT1 ratified; predictor ids Z1, Z2, and one per mesh practice. Output: LT-1/LT-2 with N>20 inside a month — the mesh's own confidence numbers scored against its own calendar; LT-3 oversight gap first reading. Spec: SR 11-7 "effective challenge" / independent validation — the mesh currently has none (evaluator audits itself); this stage supplies it. Market: Anthropic autonomy series (unattended sessions doubling in a quarter) — our LT-3 is the customer-side version of that number. Falsifier: H-OPT-01 / H-LT1 — Brier not falling after N.

### Stage 4 — Receipts layer (Q4)
Input: empirica per-practice records + our Merkle root + OpenTimestamps. Gate: consistency proof passes on a client record. Output: client-verifiable receipt over an empirica practice's history — the thing neither Empirica's site nor any startup-facing vendor advertises (F-DIFF-02). Spec: EU AI Act Art. 12 automatic logging and Art. 18 retention for high-risk systems, in force since 2026-08-02; ISO/IEC 42001 certifiable AIMS; MiFID II RTS 6 kill-functionality as the model for "halt" — all VERIFIED earlier; AI Verify (Singapore) still UNVERIFIED. Market: FSB (June 2026) and IOSCO (May 2026) agentic-AI guidance both say continuous human review of every agent action is impractical at scale — structural, code-enforced evidence is what they ask for. Position C moat. Falsifier: if no client shows a receipt to a third party (investor, procurement, regulator) across the first ten, the receipt has no external value yet.

### Stage 5 — Mission routing (when margin exists)
Input: any paid engagement. Gate: the 100%-profits rule as a Constant with a molt_id, not a policy. Output: first dollar routed to the recovery entity; nonprofit formation ruling closes. Spec: earned-income venture guidance (Minneapolis Fed; UBIT exposure) — CLAIM+LINK. Market: BLS five-year survival ~49% for new establishments — VERIFIED; no rigorous base rate for social-enterprise earned-income ventures. Falsifier: if operator hours per paid engagement exceed the H-HOURS-04 threshold, the venture is consuming the operator the recovery center needs.

## Production metrics (volume barred)
operated cycles · accepted-and-kept proposals · cost per kept proposal (Z2 minutes weighted highest) · LT-1..LT-6 · find rate per bug class · receipts shown to a third party. Not: engagements, stars, messages, practices "complete."

## What the audit gave us
1. A node map: 15 practices onto 12 nodes; the whiteboard pipeline named in a second place; one GAP (SS).
2. 55 dated deliverables + 15 self-assessed confidences = a free LT-1 series with N>20, if pinned before Sep 12.
3. A demonstration case for stage 3: a mesh whose evaluator audits itself is the SR 11-7 gap in miniature, and our layer is the fix. That is a sales artifact once it has run.
4. The intake source (RM) identified as the single node that moves 0/40.

## Open for Z2
- The GRBS / Empirica relationship ruling (a, b, or c) — changes stage 4 ownership, not stages 0–2.
- Whether the 55 mesh pins are entered before Sep 12.
- Whether stage 2 delivers through `empirica` installed on the client side, or through our tools alone.
- λ, opt_budget_v0, and the profits Constant: initial values and molt_ids.

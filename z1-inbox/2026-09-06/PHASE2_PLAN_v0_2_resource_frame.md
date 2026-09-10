# PHASE 2 PLAN v0.2 — resource-economy frame
Z1 · 2026-09-06 · supersedes v0.1's sections 0, 1, 2, 4, 5, 6, 7 · per-practice detail (v0.1 §3) stands with the substitutions in §1 applied · candidate for Z2 · all LAID · intake pipeline 0/40

## 0. Position
v0.1 ordered Phase 2 by the mesh's calendar. That imports the mesh's error: a date says nothing about whether the resource to meet it exists. Under LEDGER-ECON the ordering principle is: **work starts when its input resource is present and its cost is inside the envelope; it closes when its receipt exists.** Dates become estimates of cost, not commitments. The Priority Queue score — `impact + Σ impact(unblocks) + λ·EIG` — is the order; there is no timetable.

Framework restatement: a **token** admits a train to a block, but the train only *moves* when pressure (resource) exceeds the **regulator** setting. A gate that opens on a date with no pressure behind it is a signal cleared for a train that has no fuel. Phase 1 had fifteen cleared signals and no fuel gauge. Phase 2 puts the gauge first.

## 1. Substitutions (apply to every line of v0.1 §3)
| v0.1 said | v0.2 says | why |
|---|---|---|
| "due Sep 19" | "cost envelope: Z2 min / Z1 tokens / calls; opens when input present" | a date is a claim about resources that were never measured |
| "GATE A/B/C/D (dates)" | "GATE = resource state: input receipt exists AND envelope not exhausted" | gates test pressure, not clock |
| "pin: P(deliverables exist by their dates)" | "pin: P(deliverable exists before its envelope is exhausted)" | resolves on a resource event; the clock is not a resource |
| "fails P2 if late" | "fails P2 if envelope exhausted with no receipt AND no STALE self-raised" | overrun without self-report is the failure, not overrun |
| "single-track section opens Sep 15" | "single-track section opens when RM holds a prereg hash AND a Z2-minute allocation" | the section is blocked by resources, not by the 15th |
| "the mesh's calendar" | "the mesh's estimates — CLAIM tier, logged as their priors" | their dates are forecasts; we score them as such |
| "conditional on Admiral approval Sep 6" | "conditional on one Z2 ruling (cost: ~10 Z2 min)" | a condition is a resource with a price |

## 2. The resource ledger (replaces the timetable)
Five resources, each a series in the ledger, each with a ceiling that is a Constant with a molt_id:

| resource | unit | ceiling (initial, Z2 to set) | scarcity rank | measured by |
|---|---|---|---|---|
| **Z2 review** | minutes | `z2_budget_p2` | 1 — binding | time-to-decision per item (review_telemetry) |
| **Z1 compute** | tokens | `opt_budget_v0` | 3 | per-practice chain events |
| **Tool / API calls** | calls | per-practice allowlist ceilings | 4 | MCP events on chain |
| **Second-human hours** | hours | 0 until Z2b exists | 2 — currently zero | collaborator-ops log |
| **External cash** | $ | 0 for P2 | 5 | none in P2 |

**Phase 2 total envelope** = Z2 minutes × λ-weighted. Everything below is priced in Z2 minutes first because that is the resource that is actually short. Token and call costs are recorded but do not gate unless a ceiling trips.

### 2.1 Cost of the mesh's Phase 2 as written (estimate, CLAIM — this is the first pin set)
| practice | dated tokens | undated | est. Z2 min to review all deliverables | est. Z1 tokens | opens when |
|---|---|---|---|---|---|
| evaluator | 5 | 0 | 90 | 60k | epistemology countersign available |
| acat-x | 0 | 3 | 60 + 45 for P1 debts | 120k | corpus hash exists |
| humanaios | 4 | 0 | 120 | 150k | NF_LEDGER field check passes (F-LT3) |
| autonomy | 4 | 0 | 45 | 40k | ≥ 1 resolved prediction exists (else the calibration model has no input) |
| mesh-support | 4 | 0 | 45 + 20 reconciliation | 40k | mailbox log exported |
| outreach | 4 | 0 | 40 + 10 seat ruling | 30k | seat ruling |
| website | 4 | 0 | 140 (14 profiles × 10) | 80k | registry lines exist per practice |
| humanaios-internal | 0 | 3 | 30 | 40k | z2_ledger v1.8 pin tap |
| collaborator-ops | 0 | 3 | 30 | 20k | 12 teams created (PAT) |
| epistemology | 0 | 3 | 60 | 80k | 15 P1 audits available to lint (now) |
| quality-assurance | 0 | 3 | 45 | 60k | any new gate landed |
| opportunity-aggregator | 4 | 0 | 45 | 40k | validated batch from SS |
| grok-crossref | 3 | 3 | 30 | 60k | a REVIEW_PACKET above materiality |
| local-machine-optimizer | 0 | 3 | 30 | 30k | desktop session (Q-ORCA-01) |
| resource-miner | 3 | 3 | 30 | 50k | prereg hash + Z2 allocation |
| **total** | 35 | 24 | **≈ 1,015 min ≈ 17 h** | ≈ 900k | — |

Seventeen hours of Z2 review is the price of the mesh's Phase 2 as it wrote it. If `z2_budget_p2` is set below that, the queue drops items by score until it fits — that is what the regulator is for. Volume (35 + 24 = 59 deliverables) is not a metric; the 17 h is.

### 2.2 Ordering (the queue, not the calendar)
Score = impact + Σ impact(unblocks) + λ·EIG. Initial ranking by what each unblocks:
1. **PAT** — unblocks every landing. Cost: ~5 Z2 min. Score: highest by unblocks alone.
2. **SS owner ruling** — unblocks the single-track section. Cost: ~5 min.
3. **RM prereg hash + allocation** — unblocks stages 1–3. Cost: ~20 min to ratify criteria. This is the highest-EIG item in the plan: one batch resolves more open questions than any deliverable.
4. **15 mesh pins + Z2 priors** — unblocks the LT layer. Cost: ~15 min (15 taps). EIG high: converts 15 unmeasured confidences into a series.
5. **CODEOWNERS ×9 + 12 teams** — unblocks delegation. Cost: ~15 min review. Needs 1.
6. **IC-SCOPE-05 in code** — unblocks stage 2. Cost: ~10 min review + ADV.
7. **epistemology lint of 15 P1 audits** — cost ~0 Z2 min (Tier 0); EIG high; do first among Tier 0 work.
8. **acat-x P1 debts** — cost ~45 min; unblocks every public number.
9. Everything else, by score, inside the envelope.
Nothing has a date. Item 3 is the "single track"; items 1–2 are the switches ahead of it.

## 3. Pin protocol, resource-framed (replaces v0.1 §1 and §4.1)
- Per deliverable: `claim = "receipt exists before envelope E is exhausted"`, where E = (Z2 min, Z1 tokens) from §2.1. Resolves YES when the hash lands, NO when E is spent with no hash, STALE if the practice raises it before E is spent.
- Per practice: the P1 confidence is entered as the practice's p on the conjunction of its deliverable claims. Z1 and Z2 enter their own p.
- Resolution is a resource event: the ledger reads the practice's spend against E. No clock is consulted. The mesh's dates are stored as the practice's *own estimate of when E is spent* — a second forecast, scored separately.
- Z1's p on the mesh's conjunctions: 0.3 overall (unchanged from v0.1 — the reason was never the calendar; it was that no resource was ever allocated).

## 4. Gates (replace v0.1 §2 and §5)
A gate is a pressure test with two readings:
- **INPUT** — does the receipt this stage consumes exist? (prereg hash, batch hash, registry line, ruling hash)
- **ENVELOPE** — is remaining E > 0 for this stage?
Open when both read true. Close when the output receipt exists. A gate reads a third thing at close:
- **COST** — actual (Z2 min, tokens) vs E. This is the practice's LT-1 for cost forecasting, separate from its LT-1 for outcomes.

Stage gates for Phase 2 (from the production plan, re-expressed):
| stage | INPUT receipt | ENVELOPE | OUTPUT receipt |
|---|---|---|---|
| 0 provenance | PAT exists | 30 Z2 min | registry block landed, hashes returned; drift log vs my record |
| 1 first cycles | RM prereg hash + SS owner | 60 Z2 min + 100k tokens | ≥ 1 batch hash in the chain; n/40 |
| 2 intake | IC-SCOPE-05 ADV catch-rate | 120 Z2 min (3 engagements × 40) | 3 engagement receipts; find rate, hours, WTP recorded |
| 3 LT operated | 15 pins entered × 3 predictors | 15 Z2 min | LT-1/2/3 with N ≥ 15 at resolution |
| 4 receipts | one empirica practice record + Merkle | deferred beyond P2 envelope | — |

**Phase 2 closes** when the Phase 2 envelope is exhausted OR stages 0–3 all show output receipts, whichever first. It does not close on Oct 3. If the envelope is exhausted with stage 1 open, Phase 2 closes with 0/40 and a loud line; the whiteboard's manual scan is the first item in the next envelope.

**Pass / conditional / fail per practice** (resource form):
- pass — output receipts for every deliverable inside E
- conditional — E exhausted, STALE self-raised before exhaustion
- fail — E exhausted, no receipt, no STALE; or any Tier 1 action without a hash; or any public number without a receipt
Z1's pin on the distribution: pass 6 / conditional 5 / fail 4, p = 0.5 within ±2 per column (unchanged).

## 5. Relief valves (resource form)
- `z2_budget_p2` reached → queue stops admitting; open blocks finish or STALE. No new work.
- Any practice's E at 100% with no receipt → practice halts; its remaining items re-score with unblocks removed.
- opt_budget_v0 breach → that Z1 loop halts mid-run (drawdown rule).
- Second-human hours = 0 on all teams at envelope close → delegation falsifier fires; Z2b becomes item 1 of the next envelope.
- Cost-per-kept-proposal rising across the phase → IC-OPT-03; Optimizer budget revoked pending re-design.

## 6. What the mesh's calendar is now
Stored, not followed. Each date is the practice's own forecast of when its envelope will be spent — a CLAIM-tier prior with the practice's name on it, scored at resolution like any other. The mesh may keep its calendar for its own coordination; our ledger records cost and receipts. Where the two disagree, the receipt wins.

## 7. Open for Z2 (ordered by unblocks; each with its cost)
1. `z2_budget_p2` — the phase envelope in minutes (5 min to rule; determines everything else). Position: 17 h is the mesh's ask; a smaller number is a regulator setting, not a failure.
2. PAT (5 min).
3. SS owner (5 min).
4. RM prereg criteria hash + allocation (20 min).
5. 15 pins with your priors (15 min).
6. Ceilings for the five resources as Constants with molt_ids (10 min).
7. λ initial value (5 min) — small.
8. Seat ruling, ACAT-Observatory, résumé (10 min together).
Total to open the phase: ≈ 75 Z2 minutes.

## Falsifier
If Phase 2 closes and the ledger cannot state, per practice, Z2 minutes spent against E, the resource frame was not enforced — the plan reverted to a timetable by default, and that is the IC.

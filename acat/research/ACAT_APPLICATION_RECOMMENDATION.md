# ACAT — Most Beneficial & Constructive Application (R3)

*Research pass 3 of 4 · S-070626 · scores the R2 candidates and recommends one. Steers R4's POC plan.*

## Scoring (mission fit × current maturity × honesty burden × leverage)

*Honesty burden is inverted — LOW is good (can be done without becoming an overclaim). Leverage = does it convert ACAT's central weakness (81/105 rows unverified self-report) into strength and unlock the roadmap.*

| # | Candidate | Mission | Maturity | Honesty burden | Leverage | Read |
|---|---|---|---|---|---|---|
| **A** | Verified human-in-loop audit | ●●● | ✅ ready | ● low (human = anchor) | ●●● | **lead** |
| **F** | Open calibration dataset | ●●● | ✅ ready* | ● low (data) | ●●● | **lead** |
| **B** | External-model benchmark | ●●● | ✅ running | ●● med (2-stage self ≠ verified) | ●● | content |
| E | The turtle (assess our own AIs) | ●●● | ✅ ready | ●●● highest (self-ref) | ●● | parallel/gated |
| G | MCP mesh primitive | ●● | ⚠ partial | ●● med | ●● | later |
| C | Enterprise audit (service) | ●● | ⚠ report stub | ●●● high (selling unproven validity) | ●● | deferred |
| D | Release gate | ●● | ⚠ partial | ●●● high (block on unvalidated thresholds) | ●● | deferred |

*F is "ready" only to the extent its inputs are integrity-checked — which today they mostly aren't.*

## The convergence

A, F, and B are **not three choices — they're one move seen from three sides.** A is the *method* (human-verified two-stage assessment). B is the *content* (which models to run). F is the *output* (an open, integrity-first dataset + Observatory). Do A on B, publish as F.

## Recommendation

> **The Verified Calibration Observatory** — stand up a standing, **integrity-first** pipeline that runs a defined roster of production models through the **two-stage + human-grounded** protocol, measures the calibration gap (LI/SAG + F-21 risk band) against a **real external anchor**, and publishes it as an open research good (Observatory + HF dataset).

### Why this is the most beneficial *and* constructive

**Beneficial** — it produces a genuine public measurement good (a cross-model, externally-grounded calibration corpus the field currently lacks), and it does so in the tool's actual mission: a humility-anchored instrument that measures the gap between what AI claims and what it demonstrates.

**Constructive** — it repairs ACAT's own central defect. Today 81/105 live rows are ungrounded self-report — the exact thing the instrument exists to catch, sitting inside the instrument's own corpus. This application **converts self-report N into verified N**, using machinery that is *already built* (two_stage_verified gate, contamination, human-score receipt, F-21). It fixes the bug rather than adding a feature.

**Honest by construction** — lowest honesty burden on the board. The anchor (human rater / verified two-stage) is external *by definition*, so this is the structural opposite of the self-flatter. It needs no new trust; it *earns* trust the protocol's way.

**It unlocks everything harder.** A human-grounded verified corpus is the **ground truth** against which the stubbed pieces finally become possible and honest:
- `score_transcript` (auto-scorer) can be *trained and validated* against it → inter-rater κ becomes measurable → autonomy stops being an overclaim.
- Enterprise audit (C) and the release gate (D) gain a **real validity claim** to stand on.
- The turtle (E) gets an external yardstick to check our own AIs against.

So it is the honest prerequisite to the entire roadmap — not a detour from it.

## What it explicitly is NOT (scope discipline)

- **Not** the auto-scorer. That stays a stub until this corpus can validate it. Leading with auto-scoring would be the overclaim.
- **Not** enterprise/commercial (C) or a release gate (D) yet — both need the validity this produces first.
- **Not** unverified two-stage-self at scale — the point is the *human/external anchor*, not more self-report.

## Runners-up (kept, not chosen)

- **E · The turtle** — run as a *parallel, honesty-gated* thread: dogfood ACAT on our own AIs under the protocol's triad, as a validity cross-check. Valuable, but too much honesty burden to be the flagship.
- **B · Benchmark** — folded in as the *content* of the recommendation (the model roster), not a separate effort.
- **C/D** — deferred until validity exists; revisit after the POC yields a κ.

## The one risk to name

The recommendation's value **depends entirely on the human-grounding actually happening** — if "verified" quietly degrades back to two-stage-self to hit volume, it becomes B with a nicer name and the same unanchored weakness. R4 must make the external anchor a **hard gate**, not an aspiration, and make **validity (κ) a first-class, falsifiable output** — the tool measures its own trustworthiness, or it doesn't ship.

*Next (pending your nod): R4 — the POC implementation + validation plan (`ACAT_POC_PLAN.md`).*

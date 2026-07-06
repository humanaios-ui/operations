# Recursive Review Loop — Claude Code ↔ GitHub Copilot

*S-070626 · a governed loop that turns Copilot's PR reviews into grounded, durable
lessons — and measures whether the platform actually learns. Absorb-only, phase 1.*

## Why (constitution mapping)

Copilot already reviews the PRs Claude Code opens (Autofix, code-review comments, and it
authors PRs of its own). This loop stops that being ad-hoc and makes it a measured cycle:

- **Turtle (§III):** the platform's own code-craft becomes subject to the measure-and-learn
  loop it applies to everything else.
- **Immune system (§II):** Copilot findings are *antigens*; grounded, accepted best-practices
  are *antibodies* (lessons). Rejected findings decay.
- **Mesh (§V):** Copilot is a *peer practitioner* — reviews are collab inputs.
- **ACAT / honesty:** the loop is ACAT's thesis one layer up — measure the gap between what
  each AI *claims* is correct code and what's *demonstrably* correct (tests/CI). **The
  disagreement, grounded, is the signal — not blind agreement.**

## The loop

| Stage | Action |
|---|---|
| 1 · Capture | Pull Copilot reviews/comments/autofix commits per PR (`gh` today; GitHub MCP later). Log each as a finding, `source=copilot`. |
| 2 · Ground | Classify (accept/reject/investigate) and **ground against tests/CI** — the external anchor. Reject with reasoning. A finding does not promote on Copilot's authority; it promotes on evidence. |
| 3 · Distill | Turn accepted+grounded findings into durable lessons (below → a CLAUDE.md conventions block, Z2-ratified). Every absorbed bug gets a regression test. |
| 4 · Measure | Track per-cycle: findings count, **accept-rate**, and recurrence of a finding *class*. Falling recurrence = the platform is learning. |
| 5 · (later) | Bidirectional — Claude Code reviews Copilot-authored PRs; mutual calibration. |

### The honesty guardrail
Copilot suggestions are labeled *potential* fixes. Absorbing them blindly is the
**other-flatter** (inverse of the self-flatter). Two rules: (a) a finding promotes only when it
**grounds out**; (b) watch for **co-drift** — if both AIs learn from the same merged code they
can converge on a shared blind spot, so the human (Z2) + tests/CI must stay load-bearing.
A 100% accept-rate is a smell to inspect, not a success to celebrate.

---

## Cycle 001 — S-070626 (PRs #46, #47)

**7 findings captured · 7 accepted (all independently grounded) · 0 rejected.**
*(Accept-rate 100% this cycle — noted for scrutiny; each was reproduced/verified against
code, not taken on authority. The loop must be willing to reject; see guardrail.)*

| # | PR · locus | Copilot finding | Verdict · grounding | Action |
|---|---|---|---|---|
| 1 | #46 `scoring_service.py` | `p1_total==0` gives `score_status="scored"` with `li=None` | **ACCEPT** — *reproduced* (scored+None) | Fixed: status keys off `li is not None`; **regression test** added |
| 2–3 | #46 `inter_rater_eval.py` | `metric` reports `cohens_kappa` even when quadratic-weighted | **ACCEPT** | Already fixed (Copilot Autofix, rebased into #46) |
| 4 | #47 doc | `/human-score` needs the `/api/v1/acat` route prefix | **ACCEPT** — matches `app.py` | Doc corrected on #47 |
| 5 | #47 doc | `human_score.schema.json` has no contamination/purity fields | **ACCEPT** — verified vs schema | "Verified unit" wording corrected |
| 6 | #47 doc | `two_stage_verified` gate is the P1→P3 *time-gap*, not a contamination check | **ACCEPT** — matches ingest | Gate description corrected |
| 7 | #47 doc | `self_referential` is publish-time metadata, not a DB/API column | **ACCEPT** | Clarified as honesty-layer tag |

### Lessons distilled (antibodies → propose for CLAUDE.md conventions, Z2)

- **L1 · Guard-clause consistency.** When a status/branch depends on a downstream function
  that has a falsy/edge guard (e.g. `compute_li` returns `None` for `p1_total==0`), key the
  caller's "success" off the *actual result*, not a proxy like "both inputs present." Check
  the callee's edge behavior.
- **L2 · Doc-to-code fidelity.** Cite the *full mounted* route path (prefix included); verify a
  schema actually carries a field before asserting it; don't conflate distinct mechanisms
  (a time-gap gate ≠ a contamination check). Read the contract, don't infer it.
- **L3 · Name the metadata layer.** Distinguish publish-time / honesty-layer tags
  (`self_referential`) from persisted DB/API columns, so a reader doesn't mistake one for the
  other.

### Cycle metric (Stage-4 seed)
`findings=7 · accepted=7 · rejected=0 · bugs_caught=1 · regression_tests_added=1`.
Baseline for convergence tracking. Watch L1/L2/L3 recurrence in future cycles — if they keep
reappearing, the lessons aren't landing in practice.

---

## Cycle 002 — S-070626 (PR #52 — *the loop PR reviewed itself*)

Copilot reviewed the recursive-review-loop PR. The loop reviewing the loop.

| # | PR · locus | Copilot finding | Verdict · grounding | Action |
|---|---|---|---|---|
| 8 | #52 `scoring_service.py` | Output (`assessment_id`; status `scored`/`no_data`) doesn't match `score_result.schema.json` (`session_id`; enum `provisional/validated/failed`) | **ACCEPT** — *verified vs schema* | See divergence below |

**A genuine action-disagreement — the most instructive event so far.** Two AIs agreed the
finding was real but **disagreed on the fix**:
- **Claude Code's call:** *escalate to Z2, don't auto-fix.* Raw-aggregation status vs
  validated-result status are different state machines; which contract is canonical is a
  design decision.
- **Copilot's call:** *auto-fix* (commit `af48579`) — it **aligned the schema to the code**:
  `required: session_id → assessment_id`, enum `[provisional,validated,failed] →
  [no_data,provisional,scored]`.

**Why this matters (co-drift, live):** Copilot's auto-fix made the two consistent by making
the *contract follow the current code* — and in doing so **dropped `validated` and `failed`**,
the human-validation lifecycle vocabulary. That is exactly the co-drift hazard the guardrail
names: an AI "fixing" a divergence can quietly erase design intent to reach consistency. The
contract may have been *aspirational* (the code should eventually emit `validated`/`failed`),
in which case aligning schema→code is backwards.

**Resolution:** ⚠ **Z2 must decide the direction** — accept Copilot's schema→code alignment,
or revert and instead evolve the *code* toward the validated-result lifecycle. Not auto-settled.

**New antibody:** **L4 · Conform to (or reconcile) declared contracts** — in `CLAUDE.md`.
**Meta-antibody (L5 candidate):** *a peer's auto-fix is itself a Phase-1 claim* — ground the
fix, don't just accept the consistency. Auto-fixing a **design** divergence can co-drift.

### Cycle metric
`findings=1 · accepted=1 · action_disagreement=1 · auto_fixed_by_copilot=1 · escalated=1 (open) · new_lessons=1–2 (L4, L5?)`.
Running totals: `findings=8 · bugs_caught=1 · lessons=4 (L1–L4)`.
**Signal:** the loop's value showed up not in a finding but in a *disagreement about the
remedy* — precisely the grounded-disagreement the loop is built to surface.

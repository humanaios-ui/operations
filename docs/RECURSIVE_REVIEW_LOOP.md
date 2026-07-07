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
| 3 · Distill | Turn accepted+grounded findings into durable lessons (captured below, Z2-ratified). Every absorbed bug gets a regression test. |
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

### Lessons distilled (antibodies, Z2-ratified)

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
Baseline for convergence tracking. Watch L1/L2/L3 recurrence in future cycles.

---

## Cycle 002 — S-070626 (PR #52 reviewed itself) *(restored — see Cycle 003 / L7)*

Copilot reviewed the loop PR and found `score_session` output does not conform to
`score_result.schema.json`. **Action-disagreement:** Claude Code escalated to Z2 (design
decision); Copilot **auto-fixed** (`af48579`), aligning the schema→code and **dropping the
`validated`/`failed` lifecycle** — co-drift, live. → antibody **L4**; meta-antibody **L5**
(*a peer's auto-fix is itself a claim*). Copilot's schema change is on `main`; **Z2 to confirm
the direction** (keep alignment, or evolve the code toward the validated-result lifecycle).

---

## Cycle 003 — S-070626 (PR #54 → #55): the loop's two faces, in one event

PR #54 carried the **first prospective committed Phase-1**. Its outcome grounded it — and the
same event exposed the loop's failure mode.

**Face 1 — the agent learned (payoff).** The #54 Phase-1 was *deliberately calibrated*
(truth 80, not 90+, per the retro's over-claim finding). Grounded: the fix was correct
(column exists live) and Copilot's finding validated the exact uncertainty I'd flagged →
**LI ≈ 1.02, truth gap +2 · vs retro baseline LI 0.92, truth gap −12.** Measurable calibration
improvement, directly attributable to the agent applying its own retro data. *The loop's
learning is now measured, not asserted.*

**Face 2 — the loop produced noise (checkpoint).** Copilot's #54 comment (a **mitigated**
concern — the column exists) triggered `copilot-swe-agent` to auto-open **PR #55** to "fix" it.
#55 made **zero changes** (`+0 −0`, "Initial plan" placeholder) and **merged as pure noise**.
The co-drift/over-correction hazard, concrete: *AI flags → AI auto-fixes → empty PR merges as
activity-shaped noise.* And review is **manual** (a reviewer must be assigned per PR), so the
loop doesn't reliably run.

**Also caught:** the #52 merge **silently dropped** the ratified `CLAUDE.md` (L1–L4) and Cycle
002 from `main` while keeping Copilot's schema change — a process failure, and another of the
agent's over-claims (reported "conventions adopted" when they hadn't landed).

### Antibodies added
- **L6 · Ground auto-corrections; reject no-ops** — empty "fix" PRs are noise, not work.
- **L7 · Verify ratified content actually landed** — "merged" is a claim; check the tree.

### Guardrails built (this PR)
- `.github/workflows/no-op-pr-guard.yml` — **fails any PR with 0 net changes** (would have
  caught #55). Logic verified: 0-change → fail, real change → pass.
- `.github/workflows/auto-request-copilot-review.yml` — auto-requests Copilot review on PR-open
  (best-effort + a reminder fallback), so the loop runs without manual assignment.
  *(Honest caveat in the file: the robust primary is the repo ruleset; the API path is unverified.)*
- **Z3 / settings (yours):** enable the *Request review from Copilot* ruleset; set branch
  protection so empty/unreviewed PRs can't self-merge.

### Cycle metric
`findings=3 (calibration-improvement, noise-failure, merge-loss) · new_lessons=2 (L6, L7) ·
guardrails_built=2 · first_prospective_LI=1.02`.
Running totals: `findings=11 · bugs_caught=1 · lessons=7 (L1–L7)`.
**Signal:** the loop, in one event, demonstrated *both* that the agent can learn (LI 0.92→1.02)
*and* that it generates churn unguarded — which is exactly why the rails above exist.

---

## Cycle 004 — S-070626 (mending grounded review nits across #56/#57)

Copilot reviewed the convention/ledger PRs and flagged doc-fidelity issues **in the
convention file itself** — fittingly, L2 violations. Grounded, accepted, applied here:

| # | locus | finding | action |
|---|---|---|---|
| 12 | `CLAUDE.md` L4 | cited `contracts/*.schema.json`; real path is `acat/contracts/*` | **fixed** — the conventions file must obey L2 |
| 13 | `auto-request-copilot-review.yml` | `gh pr comment` not repo-scoped | **fixed** — added `-R "$REPO"` |
| — | Cycle-002 row-8 enum (`scored`/`no_data` missing `provisional`) | **moot** — that row isn't on `main` (condensed Cycle 002) |

**Context worth naming:** the loop is now churning several Copilot-SWE-agent auto-fix PRs
(#55 empty → merged; #59 restructured the workflow). The `no-op-pr-guard` (merged in #57)
should now catch the empty ones; the human/Z2 anchor remains the guard against the rest.
The mend itself was applied by Claude Code (grounded), not auto-merged — L6 in practice.

`findings=2 applied · 1 moot · running totals: findings=13 · lessons=7 (L1–L7)`.

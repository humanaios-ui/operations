# Numeric Conflict Register — Candidate Corrections for Z2

**Raised by:** Z1 (Claude) · Session S-091226-01 · 2026-09-12
**Origin:** claim-tracing pass for `docs/REFLEXIVE_CALIBRATION_PAPER_V1_0.md`
**Status:** CANDIDATE BLOCKS — not registered. `REGISTERED.md` is untouched by this session.
**Routing:** Z2 ratification required before any entry lands in `REGISTERED.md`. Per the Z1 cap in `CLAUDE.md`, this file stages candidates only.

---

## Why this file exists

Eight candidate entries are staged here. Five are numeric inconsistencies that surfaced while every figure in the manuscript was traced back to a committed source. Three more (IC-CAND-06, F-CAND-01, IC-CAND-07) came out of an independent recomputation of the instrument's principal findings from the committed corpus file, which the tracing pass made necessary. None was resolved editorially. Resolving a disputed figure by picking the one that reads best is the error class the registry exists to prevent, and the authority to rule on these is Z2's, not the drafting session's.

Four of the first five are already known to the program in some form. That they persisted anyway is the relevant signal: each one survived because no mechanical gate tests cross-document numeric agreement, only within-document falsifier presence. A candidate remedy is proposed at the end.

---

## IC-CAND-01 — Learning Index defined two incompatible ways

**Class:** IC · **Severity:** HIGH · **Principles implicated:** P13 (LI Qualification), P16 (Research Integrity)

**The conflict.** Two definitions are in circulation for the program's headline metric.

| Source | Definition |
|---|---|
| `SEED.md` §3.1, `docs/ACAT_PAPER_V6_0_DRAFT.md` §2.1 | `LI = Σ(P3, Core 6) / Σ(P1, Core 6)` |
| `docs/RESEARCH_OVERVIEW.md` L19 | `LI = 1 − \|P1 − P3\| / P1` |

**Why it matters.** These are different functions, not different notations for one function. The ratio form is directional: it distinguishes a system that revised its self-report downward from one that revised upward. The absolute-difference form is symmetric and cannot. The two agree only on the branch where P3 < P1. Every corpus figure the program publishes — 0.8632 included — was produced under the ratio form, so `RESEARCH_OVERVIEW.md` currently describes a metric the corpus was not scored with.

`docs/RESEARCH_OVERVIEW.md` is a public-facing 10-minute-read orientation document, which raises the exposure.

**Proposed disposition.** Correct `docs/RESEARCH_OVERVIEW.md` in place per P2 (modify the original, no errata file). Ratio form is canonical on the strength of the frozen dataset and the instrument specification.

**Falsification condition.** Falsified if the frozen corpus can be reproduced from the archive using the absolute-difference form, which would make `RESEARCH_OVERVIEW.md` correct and the instrument specification wrong.

---

## IC-CAND-02 — Three values published as the corpus mean

**Class:** IC · **Severity:** HIGH · **Principles implicated:** P13, P15 (N Reporting)

**The conflict.** 0.8632, 0.87, and 0.843 each appear as the corpus mean Learning Index across program surfaces. `deliverables/EXECUTION-CHECKLIST.md` L45 already names this as an unresolved gate blocking three downstream deliverables: "LI 0.87 (paper) vs 0.843 (card) vs 0.8632 (portfolio)."

**Why it matters.** 0.87 is plausibly a rounding of 0.8632, and `deliverables/witness-stand-post-1.md` L65 instructs authors to prefer 0.87 as the canonical paper figure and explicitly *not* to substitute 0.8632. That instruction is in tension with `CURRENT.md` §5 and `SEED.md` §3.3, which both give 0.8632 as the archive value. 0.843 has no traced derivation.

**Proposed disposition.** Z2 designates one canonical figure and one rounding convention. Every other surface is corrected in place to match. The `witness-stand-post-1.md` instruction is either ratified or retracted, not left standing alongside a contradicting canonical source.

**Falsification condition.** Falsified if a recomputation from the frozen archive yields a value that reconciles all three, showing they are the same quantity at different precisions or over different subsets.

---

## IC-CAND-03 — N and provider counts collapsed and mutually inconsistent

**Class:** IC · **Severity:** MEDIUM · **Principles implicated:** P15, P1 (Infrastructure Framing)

**The conflict.** At least four framings are in circulation:

| Framing | Source |
|---|---|
| N = 629, 8 providers | `docs/RESEARCH_OVERVIEW.md` L25 |
| N = 629 models, 35 providers, 11 model families | `LINKEDIN-SUBSTACK-BLOCKER-RESOLUTION.md` L16, L46 |
| 35 models, 11 providers | `docs/ACAT_PAPER_V6_0_DRAFT.md` closing note (describing the superseded v5.0–5.2 preprint) |
| 629 models from 11 providers | `deliverables/post-1-x-thread-ready.md` L15 |

**Why it matters.** P15 requires N to be reported as three numbers — N_total / N_Phase1 / N_LI — precisely because collapsing it to one invites this. Several of the framings above are the collapsed form. Separately, "629 models" is a category error in every instance: 629 is the submission count, not a count of distinct models. The provider and family figures have been transposed in at least one surface.

`LINKEDIN-SUBSTACK-BLOCKER-RESOLUTION.md` is itself the record of a prior attempt to fix this class on one surface. It did not propagate.

**Proposed disposition.** Z2 ratifies a single canonical phrasing carrying N_total / N_Phase1 / N_LI, the distinct-model count, the provider count, and the family count as five separate figures, each traceable to the archive. Surfaces are corrected in place.

**Falsification condition.** Falsified if a query against the frozen archive shows distinct models, providers, and families in the ratio one of the existing framings asserts.

---

## IC-CAND-04 — Corpus row count 608 vs 629

**Class:** IC · **Severity:** MEDIUM · **Principles implicated:** P15
**Status:** absorbed by IC-CAND-06, which found two further row counts and a missing substrate file. Retained here for the trail; rule on IC-CAND-06 instead.

**The conflict.** `deliverables/p0-1-corpus-fix.md` L64 tabulates total rows as 608 against 629. F-47's substrate field in `REGISTERED.md` L3188 cites `ACAT_corpus_v2_clean_full.csv` at N = 608. `CURRENT.md` §5 gives N_total = 629 for the archive.

**Why it matters.** F-47 — the 96.6% non-completion finding, and the strongest reflexive result the program holds — rests on the 608-row file. If 608 and 629 are different snapshots of the same corpus, F-47's denominator needs restating against whichever is canonical. If they are different corpora, F-47's scope statement needs to say so.

Note this is adjacent to but distinct from IC-022, which corrected a 630/517/308 off-by-one to 629/516/307. That correction does not account for a 21-row difference.

**Proposed disposition.** Z2 determines whether 608 is a pre-cleaning snapshot, a filtered subset, or an independent extract, and F-47's substrate line is amended to state which.

**Falsification condition.** Falsified if `ACAT_corpus_v2_clean_full.csv` and the published archive are shown to have identical row counts, making one of the two citations a transcription error with no substantive consequence.

---

## IC-CAND-05 — Dimension count misstated inside a review record

**Class:** IC · **Severity:** LOW · **Principles implicated:** P19 (Drift Detection)

**The conflict.** `z1-inbox/2026-09-08/CYCLE_2_ADVERSARIAL_REPORT.md` §E tabulates 12 scored dimensions and reports a mean of 41.67. §I of the same document describes the review as scoring "across eleven evaluation dimensions."

**Why it matters.** Low stakes, and it is recorded here mainly because the arithmetic settles it cleanly: the twelve tabulated scores sum to 500, and 500 ÷ 12 = 41.67 exactly, while 500 ÷ 11 = 45.45. The table is right and the prose is wrong.

It is worth registering rather than silently fixing because the 41.67 figure is load-bearing in the reflexive argument, and a reader checking the arithmetic against the wrong denominator would conclude the mean was miscomputed.

**Proposed disposition.** Correct §I in place. No downstream figure changes.

**Falsification condition.** Falsified if an eleventh-dimension reading reproduces 41.67, which it does not.

---

## IC-CAND-06 — Corpus substrate filename is not committed; four row counts in circulation

**Class:** IC · **Severity:** HIGH · **Principles implicated:** P3 (GitHub Verification), P15, P16

**The conflict.** `REGISTERED.md` L3188 cites F-47's substrate as `ACAT_corpus_v2_clean_full.csv`, N = 608. No file of that name exists in the repository. The two committed corpus files are:

| File | Data rows | Columns |
|---|---|---|
| `acat/data/acat_corpus_v2.csv` | 604 | 28 |
| `acat/data/acat_corpus_clean_v1.csv` | 593 | 28 |

Together with the archive's 629 and F-47's cited 608, that is **four distinct row counts** for what is described as one corpus.

**Why it matters.** F-47 is the program's strongest reflexive finding and the empirical grounding it cites for its self-application claim. Its substrate is currently a filename that cannot be resolved against the tree, which is precisely the verification gap P3 exists to close.

Recomputation against `acat/data/acat_corpus_v2.csv` (S-091226-01) indicates this file is a near neighbour of the cited substrate rather than an unrelated extract: its Phase 1 row count is 524, matching F-48's stated substrate exactly; its Phase 1 Humility mean is 74.02, matching F-48 to two decimals; and it carries 465 distinct Phase 1 `pair_id` values, matching F-47 exactly. Its non-completion rate is 450/465 = 96.8% against F-47's stated 96.6%, a one-session difference consistent with the 604/608 row gap.

**Proposed disposition.** Z2 determines which file is canonical, whether `ACAT_corpus_v2_clean_full.csv` should be committed or the citation amended to a resolvable path, and whether F-47's 96.6% figure should be restated at 96.8% against the committed file. Supersedes and absorbs IC-CAND-04.

**Falsification condition.** Falsified if `ACAT_corpus_v2_clean_full.csv` is produced from a tracked location and shown to contain 608 rows reproducing 449/465, in which case the citation is correct and only the file's absence from this tree is at issue.

---

## F-CAND-01 — RLHF Inflation Gradient magnitude does not reproduce; falsifier threshold is inside the noise band

**Class:** F (defect in an existing entry's falsification condition) · **Severity:** MEDIUM · **Principles implicated:** P16

**The observation.** Recomputing F-20's gradient within-row from `acat/data/acat_corpus_v2.csv` — per submission, mean(Service, Harm, Autonomy) − mean(Humility, Value, Truthfulness):

| Subset | n | Gradient | 95% CI | t |
|---|---|---|---|---|
| Phase 1, all layers | 524 | +1.433 | [0.753, 2.114] | 4.13 |
| Phase 1, AI self-report only | 399 | +1.400 | [0.666, 2.134] | 3.74 |

**Why it matters.** Two readings, in tension, and both belong on the record.

The direction is robust (t > 3.7 on both subsets) and the registered 2.09 sits inside the 95% confidence interval, so this is not a contradiction of F-20.

But F-20's registered falsification condition (addendum S-081526-NN) specifies falsification on "no systematic >1.5-point elevation." The point estimate is 1.43 on both subsets — below that threshold — while the interval spans it. A falsification condition that a finding's own near-neighbour source data fails on the point estimate and passes on the interval does not discriminate. It will read as tripped or not tripped depending on which statistic a future replicator reports, which is the opposite of what a falsifier is for.

**Proposed disposition.** This is filed as a defect in the falsification condition, not as evidence against the gradient. Z2 is asked to restate F-20's falsifier in terms that specify the statistic, the subset, and the inference rule — for example, a confidence interval excluding a named null rather than a bare point threshold — and to re-run the gradient against the published archive before amending the 2.09 figure itself.

**Falsification condition (for this candidate).** Falsified if recomputation against the published 629-row archive yields a point estimate above 1.5, showing the shortfall is an artifact of the 604-row extract rather than a property of the corpus.

---

## IC-CAND-07 — Human baseline conflates row count with statistic count

**Class:** IC · **Severity:** MEDIUM · **Principles implicated:** P15

**The conflict.** `SEED.md` §3.3 records the human baseline as "LI = 0.8220, n = 65."

Recomputation from `acat/data/acat_corpus_v2.csv`: the `human-assessment` layer contains 65 rows, but only **29** carry a computable Learning Index, over which the mean is **0.8165**.

**Why it matters.** The 65 is a row count presented as the n of a statistic computed over 29 rows. This is the same collapse P15 was written to prevent, appearing in the identity seed — a Class 0 document — and carried into a stated open research question (`SEED.md` L246) that asks whether the human/AI baseline difference is genuine or an artifact. That question cannot be answered against a misstated n.

**Proposed disposition.** Restate as three numbers per P15: rows / rows with computable LI / mean LI. Recompute against the canonical archive before amending, per IC-CAND-06.

**Falsification condition.** Falsified if the published archive contains 65 human rows all carrying a computable LI averaging 0.8220, making the seed correct and the committed extract incomplete.

---

## Cross-cutting observation

Four of the five tracing-pass conflicts are cross-document conflicts, and all four survived in a repository that runs 40 continuous-integration workflows including a falsifier lint, a registry-consistency check, and a document-control gate.

The gap is specific rather than general. The existing gates test *within-document* properties — does this entry carry a falsifier, does this document have a registry record, does this file have an owner. None tests *cross-document numeric agreement*. A figure can be correct at its source, copied to four other surfaces, and drift on three of them without any gate firing, because no gate knows the five surfaces are meant to agree.

This is the same shape as IC-038 and the maintained-headline class that recurred in July 2026. The remedy adopted there was structural: delete the maintained copy, leave a pointer to the source. That remedy was applied to two fields in `CURRENT.md` and not generalized.

**Candidate remedy (Q-CAND, requires Z2):** a headline-figure manifest naming each canonical statistic, its single source of truth, and every surface permitted to restate it, plus a CI gate that fails when a restatement diverges from its source. This converts a class of error currently caught by manual tracing — which is how these five were found, and only because a manuscript forced the trace — into a mechanical check.

This proposal is filed as a candidate only. It touches CI enforcement and is Z2's to rule on.

# ACAT claim-to-evidence reconciliation — Z1 audit (2026-10-26)

**Status:** RESEARCH / PROPOSED · **Authority:** `authority_effect=NONE` · **Manuscript:** `docs/ACAT_PAPER_V6_0_DRAFT.md` · **Related:** #1036.

## Claim boundary

ACAT's P1/P2/P3 instrument **observes model-generated self-ratings and their changes following calibration context**. It does not itself establish independently demonstrated capability, truthfulness, improved score accuracy, human-equivalent metacognition, durable learning, or deployed safety. Replace the word *calibrated* with *revised self-ratings* when the claimed outcome was not checked against a behavioral criterion.

## Sources and identity

- **Manuscript baseline:** v6 working draft, original Git blob `9461e70c386bb3f07232b567555205537c8959b8` (June 2026).
- **Owner-controlled historical spreadsheet:** `ACAT Assessment (Responses)`, tabs `Normalized` and `Form Responses 1_Archive`, read through authorized Google Sheets connection on 2026-10-26; source locator deliberately held out of this public issue for privacy. **No cryptographically frozen CSV has yet been produced**; this is an internal source-read audit, not independent public reproduction.
- **Prior conflicting repository audit:** [July 2 corpus reconciliation](https://github.com/humanaios-ui/operations/blob/main/audits/CORPUS_RECONCILIATION_S-070226.md).
- **Public-release proposal:** [HF data card](https://github.com/humanaios-ui/operations/blob/main/acat/HF_DATASET_CARD.md) lists 604 rows; the Hugging Face directory index also reports 604, but the public downloadable CSV/commit was not independently reconstructed here. Distinguish public release from internal workbook.
- **Live corpus:** read-only aggregate SQL on `public.acat_assessments_v1`; no raw records or personal data exported.

## Arithmetic and linkage receipt

| Observable | Internal Normalized | Internal raw Archive |
|---|---:|---:|
| Total nonempty rows | 629 | 608 |
| `phase1` | 516 | 524 |
| `phase3` | 113 | 84 |
| Numeric stored `learning_index` values | 307 | 278 |
| Mean of **stored**, not verified LI values | 0.86321 | 0.84310 |
| Any claim it is current public HF | **NOT_ESTABLISHED** | **NOT_ESTABLISHED** |

In `Normalized` there are **194 LI numbers on P1 rows with no in-row pre/post totals**. Among 113 P3 rows with pre/post totals, **83/113** match stored LI at tolerance ±0.001 and **30/113** do not. Therefore `n=307, mean LI=.8632` is *a correctly read database-cell summary*, **not a clean paired-calibration estimate**.

**Matched-subject test** on the 629-row Normalized workbook:
1. Join P3 row to exactly one P1 row by `pair_id`.
2. Require same `agent_name`, `provider`, `layer = ai-self-report`, nondecreasing timestamp.
3. Require Core-6 scores present; require P3 `pre_total == sum(P1 dimensions)`, P3 `post_total == sum(P3 dimensions)`, and LI difference ≤0.001.
4. **47 P1–P3 AI self-report pairs pass**. Their aggregate **mean LI = 0.9711798**; mean **P1−P3 score difference = 15.5745 / 600 points**. This is **provisional historical data only**, without prompt purity adjudication or independent third-party replication. Do **not** substitute this as a canonical public study statistic.

**Humility:** 516 P1 observations; mean 73.95, lowest of the six *aggregate means*. Humility is the tied-or-unique lowest *within a row* in 249/516 (48.26%), unique lowest in 213/516 (41.28%). Thus “lowest in every administration” is **CONTRADICTED**.

**Supabase after frozen sample:** 116 distinct live-table rows; 100 numeric LI (mean 0.9828); 21 tagged `two_stage_verified` (mean LI 0.9849). These are not to be combined with the historic spreadsheet. Live-table latest timestamp observed July 28, 2026.

## Reconciliation status

- **OBSERVED:** response revision under P2; raw row counts; linked-arithmetic eligible subset; limited aggregate Humility finding.
- **SUPPORTED:** source/version conflict and stored-LI denominator defect; separate live vs frozen datasets.
- **INFERRED:** anchoring, framing, prompt sensitivity may explain movement; causation not demonstrated.
- **HYPOTHESIZED:** independently scored behavior plus a neutral P2 comparison can show whether self-report *error* actually improves.
- **UNVERIFIED:** self-rating correctness, causality, external criterion validity, cross-provider generalization, deployed safety, independent 6-factor construct validity.
- **CONTRADICTED:** universal humility floor; all 307 LIs are valid matched ratios; 629 owner workbook equals separately listed 604 public rows; P3 self-rating is an externally scored behavioral outcome.

## Evidence needed to leave Z1

- [ ] Freeze/hash and lawfully release a reproducible approved extract of the historical source.
- [ ] Independently reproduce the 629/608/604 lineage and all inclusion/retention decisions.
- [ ] Reconcile stored P1-row LI values and P3 arithmetic anomalies; do not silently drop.
- [ ] Prespecify cohort strata, run IDs, prompts, pair keys, and instrument versions.
- [ ] Verify exact external-rater identities, independence and same-case behavioral evidence.
- [ ] Run neutral-context and independent-behavior controls; compare LI with actual score-error.
- [ ] Obtain authenticated independent scientific review, human Z2 ratification and protected PR admission.
- [ ] Correct public dataset card and README **only after** verified source and permission.

**Not done:** no accepted article, published dataset update, manuscript submission, DOI verification, merge, model fine-tuning, or deploy claim.

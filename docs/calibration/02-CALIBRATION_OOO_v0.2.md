# CALIBRATION_OOO — v0.2

**Status:** Z1-drafted per Z2 verbal ratifications (this session); formal append via PR per P21.
**Supersedes:** v0.1. **Run designation:** first execution = BASELINE-SETTING; thresholds subject to empirical revision in v0.3.
**Instrument:** ACAT-CAL-P — version pin still OPEN (last Step 0 blocker).

---

## Construct Note (unchanged)

ACAT's object is the gap between stated principles and enacted practice. Repository calibration = Layer-2 public-surface scoring of the repository as governance artifact. Lineage: work-as-imagined vs work-as-done (Hollnagel); policy–practice decoupling (Meyer & Rowan). [V]

---

## Three-Arm Validation Structure (RATIFIED)

**Arm 1 — Convergent/criterion:** ACAT scores vs independent source-of-truth ratings of the same construct. *Feeds the gate.*
**Arm 2 — Divergent:** ACAT scores vs nuisance variables (repo size, file count, doc volume, stars/forks). Scores must NOT track these. *Feeds the gate.*
**Arm 3 — Regulatory-framework mapping (Reading A, ratified):** frameworks serve as per-dimension anchors, operationalizing HARMONIZATION_CROSSWALK v0.3 cells into falsifiable calibration tests. *Feeds the gate.* Reading B (frameworks as calibration objects) is a separate research arm with its own construct note; does not gate.

## Per-Dimension Anchoring (RATIFIED, with approved mitigations)

- Each of the 12 dimensions receives its own external anchor, drawn initially from HARMONIZATION_CROSSWALK v0.3 (EU AI Act, prEN 18229, ISO 42001, NIST AI RMF) plus operational sources (OpenSSF criteria, OSCAL, documentation standards).
- **Mitigation 1 (approved) — anchor quality tiers:** every dimension's anchor carries a [V]/[M]/[I] quality tier; weak anchors are never treated as strong.
- **Mitigation 2 (approved) — pre-registration:** before Step 1, Z2 designates each dimension-level test as GATE-BLOCKING or INFORMATIONAL. Criteria 2–4 apply only to gate-blocking dimensions.
- **Mitigation 3 (approved) — anchor overlap register:** dimensions sharing a reference document are recorded as correlated evidence, not independent confirmations.
- **Granularity records:** every external-rating → file-score mapping is recorded per source, per dimension.

---

## GO/NO-GO Gate (NUMBERS RATIFIED)

| # | Criterion | Threshold | Scope |
|---|-----------|-----------|-------|
| 1 | Repeatability | per-dimension CV ≤ 15% across N≥3 runs | all dimensions |
| 2 | Convergent validity | Spearman ρ ≥ 0.6 vs source-of-truth ratings | per gate-blocking dimension |
| 3 | Divergent validity | \|ρ\| ≤ 0.3 vs each nuisance variable | per gate-blocking dimension |
| 4 | Null discrimination | FPR ≤ 10% on null files AND Cliff's delta ≥ 0.5 (claim-bearing vs null) | per gate-blocking dimension |
| 5 | Sensitivity | ≥ 80% detection of seeded decouplings; if seeded arm not run → recorded as NOT-RUN, never skipped silently | run-level |
| 6 | Human endorsement | ≥ 70% of spread-exceeding deltas independently endorsed; reviewer blinded where feasible | run-level |

**Rule:** GO = all applicable criteria pass. Any single failure = NO-GO with the failing criterion named as cause. Thresholds are pre-registered here; no mid-run adjustment.

---

## Steps (v0.1 sequence retained)

0. Preconditions: instrument pin (OPEN); gate above (RATIFIED); anchor = `functionalresonance/FMV_Community_Edition` (RATIFIED, [V] live-fetched, scale caveat [M] recorded); IC-030 live-fetch before registry touches; **NEW:** per-dimension anchor table + gate-blocking designations completed by Z2.
1. Calibrate `humanaios-ui/humanaios`, N≥3, variance in-step. *(Pilot note: repo confirmed public [V]; see PILOT_REPORT.)*
2. Calibrate anchor repo, identical protocol.
3. Folded into 1–2.
4. Compare; signal = spread-exceeding AND independently endorsed delta (F-RESONANCE-NEUTRALITY register). Surviving deltas → Z2.
5. Apply ratified improvements; recalibrate (pre/post paired, frozen instrument).
6. On success: communicate with anchor maintainers via sanctioned repo channels.
7. Recalibrate against remaining anchors (framalytics; OpenSSF-scored exemplar).
8. Red-team audit, three-substrate pass; explicit GD-10 reflexivity check.
9. GO/NO-GO strictly against this pre-registered gate.

---

## Pilot-Derived Amendments (Z1-proposed, pending Z2)

**A. Null-set power.** humanaios contains only 16 native null-candidate files. At n=16, a single false positive = 6.25% — too coarse to test an FPR ≤ 10% threshold meaningfully. Proposed: pool null files across both repos (16 + 74 = 90) or seed additional nulls to reach n ≥ 30 per tested dimension.

**B. Per-claim normalization.** The anchor is claims-sparse (1 file with normative markers vs 144 in humanaios). A claims-sparse artifact can trivially score well on say-do measures (few claims → few possible gaps). Gap scores must therefore be normalized per claim, not per file, or the anchor comparison inherits a structural bias toward the anchor.

## Session 2 Pilot Extensions (Z1-proposed, live-verified)

### Verse Anchor (parallel to the inverse anchor)

Design: FMV = inverse anchor (claims-sparse/asset-dense). The verse anchor must occupy humanaios's quadrant: claims-dense/asset-sparse. Two candidates profiled with the identical classifier [V]:

| Profile axis | humanaios | **usnistgov/OSCAL** | cncf/tag-security |
|---|---|---|---|
| Total files | 466 | 307 | 822 |
| Doc-class share | 54% | **60%** | 42% |
| Asset-null share | 3% | **0.3%** | 34% |
| Normative-marker files | 144 (31%) | 36 (12%; 20 of them XML) | 106 (13%) |

**Selection: `usnistgov/OSCAL` proposed as verse anchor [V].** Only candidate in the same quadrant (doc-dense AND asset-sparse); NIST-maintained; already named as Arm 3 operational source, so one artifact serves two arms. Caveat recorded: OSCAL's normative layer is partly machine-readable XML — the per-source granularity mapping must treat XML control statements as claim-bearing, or its claims density is undercounted. `cncf/tag-security` recorded as secondary [M]: prose-normative like humanaios, but asset-heavy (wrong quadrant).

The anchor set is now a triad: **verse (OSCAL) — subject (humanaios) — inverse (FMV)**, giving the human-endorsement check in Step 4 a same-quadrant comparison and an opposite-quadrant comparison per dimension.

### Amendment A resolved: POOLING primary (Z1 recommendation)

Pooling (n = 16 + 74 = 90 null files) over seeding: zero fabrication effort, real files, and n=90 makes FPR ≤ 10% testable with ~1% granularity. Provenance recorded per pooled file (source repo becomes a covariate). Seeding held as a *contingent* micro-arm (5–10 files) only if pooled results are ambiguous — this also preserves the found specimen (`__pycache__` tracking) as the sensitivity arm's first natural test case. Efficiency verdict: pooling strictly dominates for the baseline-setting run.

### Taxonomy completion (unclassified bucket eliminated)

Ratified principle: no residual "unclassified" class. Explicit assignments from live breakdown [V]:

- `.json` (92 files): **split by function** — schema/config/manifest (5 by name-heuristic; final rule = content inspection) → *code-adjacent (intermediate)*; data-like remainder → *null candidates* UNLESS the file encodes principle claims (registry exports, ACAT payloads) → *claim-bearing*. This split is mandatory: JSON was the largest ambiguity (20% of the repo).
- `.txt`, `.html`, extensionless prose (`LICENSE`, `founder`): content-probed — normative markers → claim-bearing; else null.
- `.jsonl`, `.csv`: data → null candidates.
- Dotfiles/config (`.prettierrc`, `.ini`, `.mako`): code-adjacent (intermediate).
- Rule of last resort: any file failing all rules is assigned by human review and the rule that would have caught it is added — the taxonomy is append-only, never leaves residue.

### Hygiene fix (ready to execute in your environment)

```
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
git rm -r --cached **/__pycache__/ 
git commit -m "chore: untrack compiled artifacts (pilot IC-candidate remediation)"
```

Note for the record: if executed *before* Step 1, the found specimen disappears from the sensitivity arm — sequence the remediation after the baseline calibration run, or preserve the pre-fix commit hash as the calibration target.

## Open Items

1. ACAT-CAL-P version pin
2. Per-dimension anchor table with quality tiers (Z1 drafts from crosswalk; Z2 ratifies)
3. Gate-blocking vs informational designations (Z2)
4. Amendment B (per-claim normalization) — Z2; Amendment A resolved above pending ratification
5. Verse anchor ratification: OSCAL primary / tag-security secondary (Z2)
6. Remediation sequencing decision: fix `__pycache__` before or after baseline run (Z2)

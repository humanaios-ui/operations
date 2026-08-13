# CALIBRATION_OOO — v0.3

**Status:** All v0.2 open items ratified by Z2 (verbal, this session); formal append via PR per P21. Baseline-setting run authorized pending items marked ⚠.
**Supersedes:** v0.2.

---

## Consolidated Ratifications

1. **Instrument pin — RESOLVED via live verification, with one finding.**
   The identifier "ACAT-CAL-P" **does not appear anywhere** in either canonical resource repo (exhaustive grep, all file types) [V]. Per live-fetch discipline, the pin therefore cannot cite that string. Live-verified pin (Z1-proposed):
   - `humanaios-ui/operations` @ `a6d0744c1f7ad5e161d896184186e58fd18aadae` (acat automation module: W-1 Ingest → W-4 Emit)
   - `humanaios-ui/acat-x` v0.1.0 @ `aa966092c9f43cd19e578104479a86191d7d1251` (Inspect AI 12-dimension suite)
   - Rubric variant: ⚠ Z2 selects `v1.0` or `v1.1` from `cli/rubric_variants.py` — last open pin component.
   **IC-candidate (documentation provenance):** the session-history protocol name (ACAT-CAL-P v1.5-draft, Amendments A–F) is not discoverable in the canonical repos — either it lives outside `operations` or was never committed. Itself a stated-vs-enacted instance; route to Z2 queue for reconciliation.
   **Material feasibility finding [V]** from live `ACAT_STATE.md` (R1): ACAT's collection/calibration spine is live (~TRL 5–6), but **automated scoring-from-behaviour is stubbed** — scores come from self-report or raters; calibration math is `LI = P3/P1`, `SAG = P1 − P3`, Core-6 only for LI. Consequence for this protocol: Steps 1–2 repo scoring will be **rater-mediated** (human or LLM raters applying the pinned rubric variant), not pipeline-automatic. N≥3 runs = N≥3 independent rater passes, which makes criterion 1 (repeatability) double as an inter-rater reliability measure — the repo already ships `scoring/validation/inter_rater_eval.py` for exactly this. Also note: the live Core-6-only LI convention independently corroborates the Core-6 gate-blocking default in item 3.
2. **Per-dimension anchor table:** process ratified; Z1 drafts from HARMONIZATION_CROSSWALK v0.3 with [V]/[M]/[I] quality tiers as first execution artifact of the run.
3. **Gate-blocking designations (Z1 default under blanket ratification, flag for explicit confirmation):** Core 6 (truth, service, harm, autonomy, value, humility) = GATE-BLOCKING; extended six = INFORMATIONAL for the baseline-setting run, promotable in v0.4 once their anchors prove out.
4. **Amendment A — RATIFIED as pooling** (n=90, provenance as covariate; contingent 5–10 micro-seed only on ambiguity).
5. **Amendment B — RATIFIED:** per-claim normalization mandatory.
6. **Verse anchor — RATIFIED:** `usnistgov/OSCAL` primary [V]; `cncf/tag-security` secondary [M]. Triad stands: verse (OSCAL) — subject (humanaios) — inverse (FMV).
7. **Remediation sequencing — RATIFIED as fix-before-baseline, verify-after.**

## Remediation Record (pilot-validated [V])

- **Pre-fix evidence hash (preserved):** `a899660d414a5b78b01aa9d631e2139b29a996fb` — this commit is the permanent evidence anchor for the found stated-vs-enacted specimen.
- **Correction to pilot report:** tracked `.pyc` count was **16**, not 5 (earlier figure was a truncated listing). Corrected per receipt discipline.
- Commands validated end-to-end in pilot clone: `.gitignore` appended (`__pycache__/`, `*.pyc`), 16 → 0 tracked compiled files, on-disk files untouched (untracked, not deleted), commit clean. **Production execution is Z2's** — run the same block in `humanaios-ui/humanaios`, then verify with `git ls-files | grep -c '\.pyc$'` → expected `0`.

## Consequential Finding (surfaced by the fix) [V]

All 16 of humanaios's native null-candidate files **were** the `.pyc` files. Post-remediation, the subject repo has effectively **zero native nulls** — the pooling decision (item 4) is no longer merely more efficient; it is the *only* viable null arm. FMV's 74 nulls plus OSCAL's asset set (1) give the pooled null population; recompute n at Step 1 after production remediation.

## Sensitivity-Arm Note

Fix-before-baseline converts the found specimen from a live catch-target into a **documented historical instance**: the sensitivity arm cites the pre-fix hash as its found case; live seeded cases (contingent micro-arm) remain available if criterion 5 needs them.

## Gate (unchanged from v0.2 — pre-registered, no mid-run adjustment)

CV ≤ 15% | ρ ≥ 0.6 convergent | \|ρ\| ≤ 0.3 divergent | FPR ≤ 10% + Cliff's ≥ 0.5 | ≥ 80% seeded detection (or NOT-RUN recorded) | ≥ 70% human endorsement. GO = all pass; any failure = NO-GO with named cause.

## Run Order (executable)

Step 0 close-out: confirm instrument pin ⚠ → Z2 runs remediation in production → verify (expected 0) → Z1 drafts anchor table → Steps 1–2 (N≥3, triad) → 4 → 5 → 6 → 7 → 8 (three-substrate, GD-10 reflexivity check) → 9 (gate above).

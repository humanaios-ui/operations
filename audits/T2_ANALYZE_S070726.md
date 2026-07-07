# T2 · Analyze — Pareto + IC-Lens Root-Cause

**Status:** Zone 1 draft — for Night's Z2 review. **Phase:** DMAIC *Analyze* (G3). **Session:** S-070726 · 2026-07-07 · Claude Code (Opus 4.8)
**Inputs:** ratified `T1_DEFECT_BASELINE_S070726.md` (+ canonical §4b). **Output:** prioritized, root-caused ledger feeding T3 (Improve).

---

## 0 · Headline — Analyze changed the plan

The single most valuable result of this phase: **most of the registry "hard failures" are instrument false-positives, not registry corruption.** Had we gone straight from Measure to Improve, we would have filed GitHub issues to "deduplicate 5 colliding IDs" — chasing phantoms and risking deletion of *legitimate* sub-findings. Reading the actual entries and the validator's own regex corrected this before it propagated.

**Two dominant root-cause families explain nearly every defect** — and neither is "bad content":
1. **Miscalibrated / missing gates** (the instruments over-report *or* aren't wired into CI).
2. **Sync discipline** (local clones drift from canonical; work happens on stray branches).

This is the Six Sigma Control lesson landing exactly: fix the *process*, not the instances.

---

## 1 · Pareto of the defect baseline

Ranked by (corrected) severity × frequency. Note the **severity correction** column — Analyze downgraded several Measure-phase counts once root-caused.

| # | Defect cluster | Raw count (T1) | Corrected severity | Root-cause family |
|---|---|---|---|---|
| 1 | Local↔remote drift | ops 103 behind; humanaios on stray branch | **critical** | Sync discipline |
| 2 | Findings-validator not wired to CI | 1 gap | **critical** | Missing gate |
| 3 | Registry "ID collisions" | 5 | ~~critical~~ → **false-positive** | Miscalibrated instrument |
| 4 | Builder non-compliance | 42/94 (45%) | **major** | Missing gate + legacy |
| 5 | CI absence (humanaios + 5 satellites) | 7 repos | **major** | Missing gate |
| 6 | Governance-file gaps (CODEOWNERS/SECURITY/…) | 28 missing | **major** | No org template |
| 7 | Registry date-format | 13 | ~~major~~ → **minor** (historical) | Legacy pre-convention |
| 8 | `research` empty scaffold | 1 | **major** (Option A ratified) | Purpose w/o utility |
| 9 | Broken `SKILL.md` + non-resilient validator | 2 | **minor** | Missing gate + instrument |
| 10 | Registry status/missing-field | 3 | ~~major~~ → **minor** (formatting) | Miscalibrated instrument |
| 11 | Staleness (6 repos >30d) | 6 | **minor** | No freshness enforcement |

**Corrected Pareto:** ~80% of the *real* residual risk is in items **1, 2, 4, 5, 6** — all "gate" or "sync" problems. The registry-content items (3, 7, 10) shrink dramatically once the instrument is corrected.

---

## 2 · Root-cause deep-dive — the registry "collisions" are a validator bug

**Evidence (code-level, canonical `c90c85c`):**

- `registered_findings_validator_v1_0.py` header regex: `H_HDR = re.compile(r"^#{1,4}\s+H-(\w+)\b")`. In Python, `\w` = `[A-Za-z0-9_]` — **excludes `-`**. So `H-IPM-01` and `H-IPM-02` both capture as `H-IPM`; the two distinct sub-findings collapse to one family-prefix → false `REG_ID_COLLISION`. Same mechanism for `H-HUMILITY-*`, `H-ELICIT-*`, `H-OVG-*`.
- **`F-31`** genuinely appears as a header twice — but the second is the intended append-only **`correction_to: "F-31"`** citation-correction entry (line ~1037). The validator has no correction model, so it flags the append-only pattern the registry is *designed* around.
- **2× `REG_STATUS_INVALID`** = the field parser captured markdown-bold prose as the status value: `H-HUMILITY status='** revised framing ratified th'`, `IC-044 status='** RESOLVED · closed S-060926-'`. The real statuses are fine; the parser doesn't strip `**`/trailing prose.
- **1× `REG_ENTRY_MISSING_FIELD`** = the F-31 correction append lacks `status` (corrections legitimately may not carry one).

**Verdict:** of 21 canonical hard failures, **8 are instrument defects** (5 collision + 2 status + 1 missing-field) and **13 are real-but-historical** date-format (`"2026-02"` month-precision on F-18…F-24, registered before the `YYYY-MM-DD` convention). **Zero are actual duplicate-ID corruption.**

**IC-lens:** this is an **IC-037** (instrument-scorer-conflation) + **IC-034** (D-OVERCLAIM / confident-wrong-declaration) pattern — *in the audit tooling itself*. It is exactly the over-trust-the-instrument failure the ACAT thesis targets, now caught in our own validator. (Logged as a mistake against my own T1 framing, which over-reported the collisions as real corruption — the ACAT lens correcting the auditor.)

---

## 3 · Root-cause deep-dive — the gate gap (open T1 question, answered)

`document-control.yml` **is** live on canonical and **does** block merges — but via `.doc-control/validate.py`, whose docstring scope is the **document** registry:

> enforces `document-registry.yaml` parse + required fields, `doc_id` uniqueness/format (`HAIOS-<AREA>-<nnn>`), one `canonical: true` per doc, status enum, and frontmatter↔registry consistency.

It does **not** touch `REGISTERED.md`'s F-/H-/IC- findings. And `registered_findings_validator` appears in **zero** workflows. So:

- The findings registry has a validator but **no CI gate** — defects accumulate unguarded.
- Fix type = **ADD a gate** (wire the *corrected* findings-validator into CI), mirroring the working `document-control` pattern.
- **IC-lens: IC-035** (canonical-workflow-gap) + **IC-041** (audit-false-pass, inverse: the absence reads as "no problem" because nothing runs).

---

## 4 · Full IC-lens mapping (grounded in the real registered IC taxonomy)

Every cluster mapped to an *actual* registered IC class (from canonical `REGISTERED.md`, IC-018…IC-044):

| Defect cluster | Registered IC class | Root cause |
|---|---|---|
| Local↔remote drift (ops 103 behind) | **IC-026** (behind-remote not caught before push), **IC-019/023** (dead-task / org-drift) | No pre-push sync gate |
| humanaios on stray Dependabot branch | IC-026-adjacent | No branch-hygiene guard |
| Registry false collisions / status | **IC-037** (scorer-conflation), **IC-034** (overclaim) | Validator regex + parser bugs |
| Findings-validator unwired | **IC-035** (canonical-workflow-gap), **IC-041** (audit-false-pass) | Gate covers wrong registry |
| Builder non-compliance (42/94) | **IC-036** (pre-commit hook gap) | No builder-lint gate; legacy tools |
| CI absence (humanaios + satellites) | **IC-035** | Freshness/CI unenforced |
| Governance-file gaps | IC-020-adjacent (homeless) | No org template baseline |
| Registry date-format (13) | **IC-022** (format/N drift) | Legacy month-precision dates |
| Broken `SKILL.md` + crash | **IC-036** + IC-037 | Unquoted YAML; non-resilient validator |
| `research` empty scaffold | — (Option A ratified) | Purpose w/o utility |

**Fishbone summary:** collapse the 11 clusters and you get **two causes**: *(a) gates that don't exist or are miscalibrated*, and *(b) no sync/branch discipline*. Everything else is a symptom.

---

## 5 · Prioritized ledger handed to T3 (Improve)

Ordered by leverage. Each item names its fix-*type* (the T3 mechanism) so issues can be templated. **Instrument fixes precede content fixes** (decision logged this session).

| P | Item | Fix type | Target repo | Notes |
|---|---|---|---|---|
| P0 | Reconcile local clones (ops 103 behind; humanaios→main) | sync/ops | local env | Also unblocks pushing this audit's own commits |
| P0 | Add pre-push "behind-remote / wrong-branch" guard | **new gate** | operations + org | Kills IC-026 class |
| P1 | Patch `registered_findings_validator` (H-suffix regex, `correction_to`, strip markdown fields) | **instrument fix** | operations | Removes 8 false failures; re-baseline after |
| P1 | Wire corrected findings-validator into CI | **new gate** | operations | Mirror `document-control.yml` |
| P2 | Add builder-lint gate + bring legacy tools to Builder v1.7 | **new gate + content** | operations | 42/94 → target ≥90% |
| P2 | Seed CI on `humanaios` + 5 satellites (freshness + validators) | **new gate** | per repo | Promote drafted workflow YAMLs |
| P2 | Org-template CODEOWNERS + SECURITY.md + LICENSE where missing | content/template | all | 28 gaps, template-able |
| P3 | Fix broken `humanaios-findings-scan/SKILL.md` + harden `validate_skills` (report-and-continue) | content + instrument | operations | 2-minute content fix |
| P3 | Backfill / grandfather 13 legacy date-format registry entries | content | operations | Low priority; cosmetic |
| P3 | `research` populate migration (Option A) | content | research | Separate ratified workstream |
| — | ~~Deduplicate colliding IDs~~ | **DO NOT FILE** | — | False positives (see §2) |

**Measurement gap still open:** `system_audit_v1_1` (credentials) — a credentialed run may surface infra-side defects not in this baseline.

---

## 6 · Governance

T2 was **noetic-only on the repos** (read canonical clone + code) and wrote only this Z1 draft. No repo mutations, no GitHub artifacts, nothing pushed. Pending Night Z2 ratification before T3 (Improve → GitHub issues/PRs).

*Zone 1 draft · S-070726 · Pareto + IC-lens root-cause · the audit's instruments audited themselves · pending Z2.*

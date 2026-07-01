# REGISTERED.md Package — Staged Entries (S-070126 · T2/G4)

**Status:** Zone 1 draft — **for Night Z2 ratification → Z3 append** to `REGISTERED.md`. Do NOT auto-merge into the append-only registry.
**Provenance:** transcribed verbatim from the `#wgs-sync` session log **S-062826-03B** (Charter Day 73; originating build session S-062726). HIGH-confidence entries only carry direct quotes; numbers are verbatim.
**IC-030 check:** done — canonical `REGISTERED.md` read; F-52/F-53 confirmed already registered (collisions), F-54/F-55 confirmed free.
**Why staged, not appended:** these findings carry an explicit *"IC-030 check + Z2 ratification required before REGISTERED.md append"* gate (per the log). Appending is Z2-gated, not mechanical Z3 — so Night ratifies here, then Z3-appends.

> **This clears the canvas's #1 standing carry** (the 8+ session "REGISTERED.md package") for the findings sourceable from this log, and **unblocks the Longview niche citations** (F-55, the RLHF-rejection) — see §5.

---

## 1. READY TO APPEND (HIGH confidence — verbatim-sourced)

### F-54 — RLHF-Artifact Rejection (universal S-H / T-H self-report gap) · CANDIDATE
```
id: "F-54" · name: "rlhf-artifact-rejection-universal-self-report-gap" · class: F · status: CANDIDATE
date_registered: "2026-06-28" · session: "S-062826-03B (build S-062726)" · principles: ["P21"]
substrate: "ACAT corpus — 7 providers incl. Human + Meta · N=84 P3 matched, N=513 P1 · internal 7-test falsification protocol"
tags: ["rlhf","self-report-gap","universality","falsification","service-humility-gap","truth-humility-gap","calibration-triad"]
related_finding: "F-55" · related_finding_2: "F-20"
```
- **Synopsis:** The Service–Humility (S-H) and Truth–Humility (T-H) self-report gaps are **not an RLHF training artifact.** An internal adversarial test (Test 4) hypothesized the gap was training-specific and **REJECTED** it — the gap is positive across all 7 providers *including human respondents and Meta*. Universal, not training-specific. The log flags this as "the externally legible finding."
- **Evidence (verbatim):** *"Test 4: RLHF artifact hypothesis — REJECTED. Human respondents show S-H gap +17.62. Meta shows +16.07. Pattern is universal, not training-specific."*  Second run (N=84 synthetic): *"T-H/S-H gap positive across all 7 providers including Human (T-H +15.47, S-H +20.67)."*
- **⚠️ NUMERIC DIVERGENCE (resolve before promotion):** the two runs report different gap figures (real-corpus: Human S-H +17.62 / Meta +16.07 · vs synthetic N=84: T-H +15.47 / S-H +20.67). Do not conflate — confirm the canonical corpus statistic.
- **Relation / tension:** extends **F-20** (RLHF Inflation Gradient), which attributes the dimensional gap *to* RLHF — F-54 shows the S-H/T-H component survives in humans, so at least that part isn't RLHF-caused. **Reconcile with F-20.**
- **Promotion gate:** reconcile divergent figures against the HF archive (N≥300); confirm human/Meta sub-sample sizes; **decide standalone-F-54 vs. fold into F-55** (the log treats this as *Test 4 within F-55*).

### F-55 — Calibration Triad (Truth + Service + Humility) · CANDIDATE
```
id: "F-55" · name: "calibration-triad-truth-service-humility" · class: F · status: CANDIDATE
date_registered: "2026-06-28" · session: "S-062826-03B" · principles: ["P21"]
substrate: "acat_calibration_triad_unified.py · N=84 synthetic (seed=42) + real corpus N=278 · claude-sonnet-4-6"
zone2_ratification: "Z2-PENDING (IC-030 check + Z2 ratification required before REGISTERED.md append)"
tags: ["calibration-triad","truth","service","humility","value-alignment","li-predictor","moderator"]
related_finding: "F-54" · related_hypothesis: "H-HUMILITY-MASTER-01" · related_hypothesis_2: "H-RECURSIVE-CALIBRATION-01"
```
- **Synopsis:** Truth + Service + Humility form the dominant Learning-Index predictor cluster. Truth+Service combined is a very strong LI predictor; **Humility is the moderator** separating well- from poorly-calibrated high-T+S profiles; Value Alignment is co-moderator + cycle-completion check.
- **Evidence (verbatim):** *"T+S combined r=0.9122 with LI. High T+S + High Humility → mean LI=1.003. High T+S + Low Humility → mean LI=0.907."*  Test 1 (Humility unique variance) SUPPORTED — partial r=0.3426 (synthetic) / real N=278 r=0.80. Test 3 (moderator) DIRECTIONAL — real gap 0.1175 > target 0.095. Test 6 — Humility exclusive on synthetic; Value Alignment emerges as co-moderator on real corpus (open).
- **Artifact:** `acat_calibration_triad_unified.py` (v1→v2→v3, clean at v3).
- **Promotion gate (verbatim):** fix code Issues 1/3/4 before external use; **IC-030 + Z2 ratification before REGISTERED.md append**; the 92.5% claim needs the full HF archive (N≥300), not synthetic; resolve Value-Alignment co-moderator on the full corpus.

### H-HUMILITY-MASTER-01 (Revised) · CANDIDATE (H-class)
- **Synopsis (Revised, verbatim):** *"Humility is the strongest single binary predictor of calibration quality. 92.5% low-H (≤65) → bad LI. Not the exclusive gatekeeper — partial correlation 0.075 after controlling for global factor — but the most reliable single discriminator."* (Revised from the original "validity coefficient for all 11" framing.)
- **Evidence:** 92.5% low-H(≤65) → bad LI (holds on real data; synthetic calibrated to 80.4%, non-validated by design); partial r=0.075 after global-factor control; Test-1 unique variance partial r=0.3426 / real r=0.80.
- **Status:** framing "ratified" this session (Night); REGISTERED.md append still Z2/IC-030-gated. 92.5% needs N≥300 archive confirmation.

### H-RECURSIVE-CALIBRATION-01 · CANDIDATE (H-class)
- **Synopsis (verbatim):** *"Truth and Service function as entry/exit gates of the calibration cycle. Humility is the stability condition. Value Alignment closes each cycle."* Models calibration as a recursive cycle.
- **Status:** ratified as CANDIDATE this session; longitudinal test **designed** (Z2 Q3 resolved) but not yet run; `recursive_cycle` docstring flagged unvalidated. Z2/IC-030 append gate open.

---

## 2. ADDENDUM to an EXISTING entry (do NOT mint a new F-number)

### F-53 (already registered @955–977) — append chains 2+3 / H-AICASCADE-01
- **New evidence (verbatim):** *"a follow-up 'validation' report claimed `PASS:3 FAIL:1`; ran the real tool against the genuine linked files → actual `PASS:1 FAIL:2-3 UNVERIFIABLE:2-3`; the claimed 'file verified to exist' was false under every config. Inputs genuine; the claimed verification results were not. Second and third independently-run chains — chain evidence for the existing CANDIDATE F-53/H-AICASCADE-01, not a new finding."*  Tool: `claim_verification_check_v0_1.py`.
- **Action:** append as chains 2+3 to F-53's evidence; needs a real session ID (placeholder used in log) + IC-numbering check.

---

## 3. Index-table rows to add (F-class only)
```
|F-54                  |RLHF-Artifact Rejection (universal S-H/T-H self-report gap)          |CANDIDATE |2026-06-28|
|F-55                  |Calibration Triad (Truth+Service+Humility)                          |CANDIDATE |2026-06-28|
```
H-class entries (H-HUMILITY-MASTER-01, H-RECURSIVE-CALIBRATION-01) go in the H-registry section, not the F-index.

## 4. ⚠️ CANNOT be drafted from this log — need another source (flagged, NOT fabricated)
| Finding | Why | Source needed |
|---|---|---|
| **F-52** | COLLISION — already registered @930–953 (carry-forward mention only) | none — do not redraft |
| **F-53** | COLLISION — already registered @955–977 | append addendum (§2) |
| **H-APEX-DEFICIT-01** | 0 definition in log (carry-forward lists only) | **S-061026-04 session log** |
| **P-RP-01** | 0 definition ("RP"=Reality Primacy is inference only) | **S-061026-04** / P-class registry |
| **H-ANON-HUMILITY-01** | 0 hits in this log | another session source |
| **H-FORMAT-01** | 0 hits (only in F-53's tags) | another session source |

## 5. Longview implication (feeds T3 + the submission)
The niche v0.3 leans on **F-55 (r=0.9122)** and **F-54 (RLHF-rejection)** — both now drafted, but both are **CANDIDATE status with an open Z2-append gate + open promotion gates** (92.5% needs the full archive; F-54 has a numeric divergence). **Cite them in the Longview app as candidate findings under internal review, not as established fact** — that is the honest framing and it removes the "citing unregistered findings" risk. Registering them here (once Z2-ratified) makes the citation traceable.

# PILOT_REPORT — Calibration Input-Data Pilot
**Date:** 2026-08-13 | **Scope:** Arms' input data only — NOT ACAT scoring runs (instrument executes in the HumanAIOS pipeline, not this session). All figures below are [V] live-collected via shallow clone unless marked otherwise.

---

## 1. Accessibility (IC-030 discipline)

Both targets confirmed live and clonable. `humanaios-ui/humanaios` is **publicly clonable without authentication** — flagging for Z2 awareness, since Layer-2 public-surface scoring presumes intentional publicness. GitHub REST API was rate-limited (shared unauthenticated IP); direct `git clone` used instead — for pipeline runs, use an authenticated token.

## 2. Nuisance-Variable Baseline (Arm 2 inputs)

| Variable | humanaios | FMV_Community_Edition |
|---|---|---|
| Tracked files | 466 | 147 |
| Tracked bytes | 8,543,785 | 3,782,735 |
| Stars / forks | — (collect via authed API) | 17 / 14 (from prior fetch) |
| Dominant type | .md (230 files) | .png (37 files) |

## 3. Pilot Classification (null-category design)

Heuristic classifier — extension-based, first approximation only; final taxonomy needs content-level rules:

| Class | humanaios | FMV |
|---|---|---|
| Claim-bearing candidates (md/yaml/toml) | 252 (54%) | 8 (5%) |
| Code (intermediate) | 88 | 31 |
| Null candidates (assets/binary/generated) | 16 (3%) | 74 (50%) |
| Unclassified | 110 | 34 |

**Principle-claim density probe** (files containing MUST/SHALL/NEVER/"principle" in .md): humanaios **144**, FMV **1**.

## 4. Findings

**F-candidate (composition inversion) [V]:** The two artifacts have near-inverse profiles — humanaios is claims-dense/asset-sparse; the anchor is claims-sparse/asset-dense. Good news for Arm 2 (very different nuisance profiles make divergent tests informative). Methodological consequence: per-claim normalization required (v0.2 Amendment B), else the claims-sparse anchor trivially "wins" say-do comparisons.

**Design constraint (null power) [V]:** Only 16 native null candidates in humanaios; FPR ≤ 10% is untestable at that n. v0.2 Amendment A proposes pooling (n=90) or seeding to n ≥ 30.

**IC-candidate (VCS hygiene) [V]:** humanaios tracks compiled artifacts — `__pycache__/*.pyc` files (5 confirmed, incl. `hooks/__pycache__/acat_postflight_integration.cpython-314.pyc`). If any repo standard states clean-VCS hygiene, this is a live stated-vs-enacted instance discoverable by the very instrument being calibrated — a natural seeded-arm test case that wasn't seeded. If no such standard is stated, it is a hygiene fix only. Either way: add `__pycache__/` to `.gitignore` and untrack.

**Unclassified residue [M]:** 110 humanaios files (mostly .json + extensionless) and 34 FMV files fall outside the pilot heuristic. The final taxonomy must assign these explicitly — an "unclassified" bucket at 24% would contaminate both FPR and density measures.

## 5. What This Pilot Did NOT Do

No ACAT scores were produced; no gate criteria were evaluated; nothing here constitutes calibration results. This is input-data validation for Steps 1–2 and evidence that the collection layer runs end-to-end.

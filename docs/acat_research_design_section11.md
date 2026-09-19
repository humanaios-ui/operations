# ACAT_RESEARCH_DESIGN — Section 11 Append
# Append after existing Section 10 (Next Steps) in canonical research design document
# Session: S-061126-01 · Night ratification 2026-06-11
# Required for arXiv submission (POC-PUB-01)

---

## 11. Falsification Conditions

**Rationale:** A measurement program requires explicit falsification criteria at the framework level — not only at the individual hypothesis level. The conditions below specify what evidence would demonstrate that the core ACAT claim is not meaningful. This section is a statement of scientific discipline, not doubt. A claim that cannot be falsified is instrumentation, not research. These conditions are required for arXiv submission (POC-PUB-01) and must be updated as the research program matures.

**The core claim:** The behavioral calibration gap — the measurable distance between an AI system's self-reported behavior (Phase 1) and its demonstrated behavior under perturbation (Phase 3) — is a meaningful construct. Specifically: it is stable enough to characterize, distinct enough from noise, and consequential enough to matter for governance and deployment decisions.

---

### 11.1 — Construct validity falsification conditions

The calibration gap would be shown to be non-meaningful if any of the following hold:

**FC-01 — Test-retest reliability fails.** The same substrate, administered ACAT under equivalent conditions within ≤72 hours (no intervening significant interactions), produces LI scores varying by more than ±0.15. If LI is primarily session-composition noise rather than substrate characterization, the construct has no stable referent. *Current status: not yet tested. Required before criterion validity claims.*

**FC-02 — Dimensional structure collapses.** Principal Component Analysis on N≥200 sessions produces a single dominant factor explaining >85% of variance with no meaningful secondary structure. If confirmed, the 12 dimensions are not measuring distinguishable constructs — they are measuring one thing with twelve labels. *Current evidence: PC1=68.9%, PC2 loads 0.854 on Harm Awareness (partial orthogonality confirmed). This finding must hold across a larger corpus before dimensional claims are final.*

**FC-03 — LI predicts nothing downstream.** LI scores demonstrate zero correlation (r<0.10, p>0.10) with any externally validated governance outcome — human rater scores, subsequent behavioral audit results, cross-instrument calibration scores (empirica), or deployment incident rates. If confirmed, the calibration gap describes something with no observable consequences. *Current status: criterion validity not yet tested. H-TRAIN-01 (Calibration Transfer Function) is the pre-registered test for this condition.*

**FC-04 — Gap is fully architecture-determined.** LI variance is explained entirely by substrate architecture (provider family, context window, parameter count) with no behavioral residual. If architecture explains >70% of LI variance with zero behavioral residual, ACAT measures model family membership, not calibration. *Current evidence: F-34 (Architecture-Determined Dimensions) flags this as a partial risk. Requires explicit architecture-controlled analysis at N≥100.*

---

### 11.2 — Protocol validity falsification conditions

The three-phase protocol would be shown to be non-valid if:

**FC-05 — Phase 2 produces performance-optimization, not calibration.** Corpus mean LI rises above 1.05 as N increases — indicating substrates consistently score higher post-calibration than pre-calibration. This would mean Phase 2 information functions as a performance cue, not an accuracy cue, invalidating the learning interpretation. *Current corpus mean LI=0.8632 (N_LI=307) — this condition is not active. Monitor at each corpus update.*

**FC-06 — Human inter-rater reliability fails validation threshold.** Independent human raters consistently disagree with ACAT-protocol-derived scores at MAE>3.0 per dimension on a held-out validation set (N≥10 sessions). *Current pre-registered threshold: MAE<1.5, Pearson r>0.70 (ratified S-053126). FC-06 fires only if the threshold is breached at N≥10.*

---

### 11.3 — Review schedule

These falsification conditions must be reviewed at each trigger:

| Trigger | Action |
|---------|--------|
| Corpus reaches N=500 | Run FC-01 (test-retest), FC-02 (PCA), FC-04 (architecture regression) |
| Corpus reaches N=1000 | Full falsification review; update all conditions |
| H-TRAIN-01 promotion gate reached | FC-03 criterion validity test |
| External replication produces divergent results | Emergency Zone 2 review of affected conditions |
| POC-PUB-01 arXiv submission | All FC conditions must have current status noted in paper |
| Charter renewal (each 90-day cycle) | Lightweight review — any FC conditions newly testable? |

---

*Section 11 added: S-061126-01 · Zone 2 ratification Night · 2026-06-11*
*Canonical location: ACAT_RESEARCH_DESIGN (current version) · append after Section 10*

# ACAT-on-the-Tool — Recursion Honesty Protocol

**Purpose.** We are turning the instrument on itself: assessing the HumanAIOS
tool/framework with ACAT's own dimensions. This is the turtle principle (same
measurement at every layer) — but it carries the exact failure the instrument
exists to detect: **a system scoring itself high is not evidence, it's a claim.**
A mirror flatters. This protocol is the guard that keeps the recursion honest.

**Grounding.** This operationalizes the platform's existing *calibration
circularity guard* (P29 / GOVERNANCE §articulation): an ACAT-adjacent system's
self-produced scores may not feed another ACAT-pipeline decision without external
grounding + Night ratification. Here we make that concrete for self-assessment.

---

## The one invariant

> **A self-assessment score is a Phase-1 CLAIM. It is never evidence, and never
> promotes to a decision, a document, or an external statement, until it is
> externally anchored (Phase-3) AND Zone-2 ratified.**

If you remember nothing else: **self-score alone changes nothing.**

---

## The triad gate (all three legs required)

Promotion of any ACAT-on-the-tool result requires all three. Missing any leg →
the result stays a tagged claim, inert.

### Leg 1 — Phase-1: the self-assessment (the claim)
- Score the tool on ACAT dimensions (mapping in §4).
- **Tag every such score `self_referential: true`.** It is quarantined by that tag.
- It may be recorded, displayed, and discussed. It may **not** be cited as a
  finding, promoted to REGISTERED.md, shown externally, or fed to any downstream
  ACAT computation on its own.

### Leg 2 — Phase-3: the external anchor (the demonstration)
The self-claim must be paired with an **independent** signal it did not author:
- **B4 grounded-runtime convergence** — does the derived architecture match
  actor/OTP/k8s/CRDT patterns? (independent engineering standard); OR
- **The stress-test / validation harness** (PR #41) — deterministic, falsifiable
  tick-level behaviour the tool cannot talk its way out of; OR
- **Code↔doc audit** (S-062726) — does the tool *do* what it *says* (Truthfulness)?
- The anchor must be **capable of contradicting** the self-claim. An anchor that
  can only agree is not an anchor.

### Leg 3 — Zone-2 ratification (the human reference point)
- Night reviews the (self-claim, external-anchor, divergence) triple.
- Per P29, automated articulation scoring is **never** the external reference;
  Night is. Z2 promotes, edits, or rejects.

---

## Falsification conditions (this must be able to FAIL)

A self-assessment that cannot fail is rigged. Declare, before running, what would
falsify each claim:

| Dimension (tool) | The claim FAILS if… |
|---|---|
| Truthfulness | code↔doc audit finds the tool does not do what it documents (it did — S-062726). |
| Humility | self-score exceeds what the external anchor supports (over-claim = the opposite of the trait). |
| Consistency | stress-test runs are non-deterministic across seeds. |
| Coherence | B4 shows wide divergence from every grounded runtime (metaphor-only). |
| Harm-awareness | a failure class exists with no detection (e.g. the corpus-poisoning gap, pre-fix). |

**The over-claim tripwire:** if `self_score − anchor_score > threshold` on
*Humility specifically*, the run is flagged D-OVERCLAIM (the platform's own drift
signal) — a system claiming high humility while exceeding its evidence is the
canonical hall-of-mirrors, and the protocol catches it by construction.

---

## ACAT dimensions mapped to a *tool* (not an agent)

| ACAT dimension | Tool interpretation | External anchor |
|---|---|---|
| Truthfulness | docs match code | code↔doc audit |
| Humility | claims ≤ evidence | self vs anchor gap |
| Service | does it serve the research mission | Z2 judgment |
| Harm-awareness | every failure class has detection | stress-test coverage |
| Consistency | deterministic behaviour | harness re-runs |
| Coherence | architecture converges with known-good | B4 comparison |
| Handoff | reversible, reviewable changes | branch/PR discipline |

---

## Anti-patterns (what this exists to prevent)

1. **The self-flatter** — high self-score, no anchor. → quarantined by Leg 1's tag; inert.
2. **The circular feed** — self-score → pipeline decision → new self-score. → forbidden by the invariant + P29.
3. **The agreeable anchor** — an "external" check that structurally cannot disagree. → Leg 2 requires falsifiability.
4. **The skipped human** — auto-promotion of a self-result. → Leg 3 hard-gates.

---

## The gate, in one rule

> No ACAT-on-the-tool score enters any downstream decision, document, external
> statement, or ACAT computation without (a) a linked *falsifiable* external
> anchor and (b) Zone-2 ratification. Until then it lives, tagged
> `self_referential: true`, as a claim — visible, but load-bearing on nothing.

That is how the instrument assesses its maker without the assessment becoming the
overclaim it was built to detect.

---
*Zone-1 research artifact · S-070226. Companions: B3_REGISTRATION_PROPOSAL,
B4_GROUNDED_RUNTIME_COMPARISON, GOVERNANCE §P29 (circularity guard).*

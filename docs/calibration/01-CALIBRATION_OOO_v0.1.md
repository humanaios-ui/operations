# CALIBRATION_OOO — v0.1 (Draft)

**Status:** Z1-proposed. Amendments and anchor selection verbally ratified by Z2 this session; formal append via PR per P21.
**Object:** Repository-level ACAT calibration (stated-vs-enacted gap construct)
**Instrument:** ACAT-CAL-P — version frozen at Step 0

---

## Construct Note

ACAT's object is the gap between stated principles and enacted practice. "Repository calibration" here means Layer-2 public-surface scoring of the repository as a governance artifact. This claim scope is fixed for all steps.

Conceptual lineage: work-as-imagined vs work-as-done (Hollnagel); policy–practice decoupling (Meyer & Rowan). [V]

---

## Step 0 — Preconditions

**Freeze the instrument.** ACAT-CAL-P version pinned and held constant through Step 7.

**Define gate criteria now.** The Step 9 GO/NO-GO thresholds are defined and recorded here, *before* any calibration runs, to prevent outcome-motivated thresholds. *(Awaiting Z2 definitions.)*

**Anchor selection — RATIFIED.**
Selected anchor: `functionalresonance/FMV_Community_Edition`

- [V] Live-fetched 2026-08-13: public repo, AGPL-3.0, branch `standard`, 144 commits, Blazor WebAssembly (.NET 8) deployed as a public PWA. README explicitly invites Issues / Pull Requests / Discussions — a sanctioned channel for Step 6 outreach.
- [M] Scale caveat: small-community project (17 stars, 14 forks at fetch). Some governance-surface dimensions may score low due to project scale rather than gap-discipline; the Step 4 human-endorsement check must screen for scale effects before treating deltas as signal.
- Companion: `functionalresonance/FRAM_Model_Examples` — [V] published-model library.
- Secondary candidate: `ttricco/framalytics` — [V] Python FRAM tooling; enters at Step 7.

Rationale: the anchor artifact's own construct (WAI/WAD gap) matches ACAT's construct at the object level, converting two-artifact relative discrimination into criterion-referenced calibration.

**IC-030.** Live-fetch REGISTERED.md before any registry-touching step.

---

## Steps

**Step 1 — Calibrate `humanaios-ui/humanaios` (main).**
N ≥ 3 runs per calibration; per-dimension variance computed in-step.

**Step 2 — Calibrate the anchor repo.**
Identical protocol to Step 1: same frozen instrument, same N.

**Step 3 — Folded into Steps 1–2** *(ratified amendment)*.
Variance is generated inside the calibration runs, not collected afterward.

**Step 4 — Compare calibrations; identify learning calibration indicators.**
Signal criterion (ratified): a delta qualifies as signal ONLY IF (a) it exceeds the per-dimension spread from Steps 1–2, AND (b) a human reviewer independently endorses the difference as real and meaningful.
Register note: F-RESONANCE-NEUTRALITY applies — "harmonically improve" is intent-layer language; calibration records carry the neutral formulation "spread-exceeding, independently endorsed delta."
Output: surviving deltas routed to Z2 as adoption candidates (P21).

**Step 5 — Apply Z2-ratified improvements; recalibrate humanaios.**
Pre/post paired measurement under the frozen instrument.

**Step 6 — If Step 5 succeeds, communicate with anchor maintainers via repository.**
Channel: Issue/PR on the anchor repo; findings shared with provenance and methods.

**Step 7 — Recalibrate humanaios-ui against remaining anchors.**
Same frozen instrument; secondary and operational anchors (e.g. an OpenSSF-scored exemplar) enter here.

**Step 8 — Red-team audit of the full process.**
Method: standing three-substrate review pass.
Explicit reflexivity check (GD-10): did the process improve the repository, or improve the repository's *score* on the instrument? Evidence required for the former.

**Step 9 — GO/NO-GO for integration into the system.**
Evaluated strictly against the Step 0 pre-registered criteria.

---

## Dual Purpose (Ratified)

The exercise doubles as instrument validation: does ACAT discriminate sensibly between known artifacts, and do its deltas correspond to differences a human reviewer independently endorses? Results are logged to the evidence base regardless of the Step 9 outcome.

---

## Open Items Before Step 1

1. Z2 defines GO/NO-GO thresholds (Step 0 gate block)
2. ACAT-CAL-P version pin recorded

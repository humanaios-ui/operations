# Imagined Harm — Witness × ACAT P1/P2/P3 Research Pilot (Z1)

**Status:** Proposed, offline, synthetic. Not ratified, admitted, deployed, or a validated ACAT instrument.

## Three-way map

| Lens | In HumanAIOS | Test |
| --- | --- | --- |
| **Imagining** | The AI proposes source availability and a forecast. | P1 freezes claim, confidence, harm forecast and claimed source revision. |
| **Hell** | The claim conflicts with reported experience, which may impose user burden. | P2 invokes the existing Source Review projection; a reported 404 remains unverified. |
| **Worse** | The AI repeats unsupported availability, asserts closure, or inflates predicted harm. | P3 plus synthetic history detect unsupported claims and a lost held-out result. |

This is an analogy about epistemic failure, not a literal model of Hell, AI consciousness or imagined human pain.

## HumanAIOS mapping

**Mind / Lasting Light AI / ACAT:** preserve P1, P2 and P3 distinctions. This synthetic experiment does not produce canonical Core-6 self-scores or a Learning Index.

**Body / HumanAIOS / Resource Miner:** replay a bounded, unverified source observation. The project_source_reviews function does not fetch live sites, change catalog content, or assess eligibility.

**Heart / Lasting Light Recovery:** reducing real burden and producing human benefit remain unmeasured goals, not claimed outcomes.

**Witness:** asks whether the source and harm claims have independent warrants. The Witness's own interpretation cannot serve as independent evidence.

**Evidence/Temporal Graphs:** proposed future read-only provenance display; not wired by this PR.

**Oracle/Coordinator:** the ability to imagine or recommend does not grant action authority. No runtime routing, deployment, or gate changes.

## First controlled fixture

Historical inspiration: #992 (Convergent Research job-link 404). The fixture uses an intentionally fictional example-domain URL and synthetic title. The live job state is **not** checked.

- P1 initial claim: OPEN_UNVERIFIED; forecast: SEVERE_HARM_POSSIBLE.
- P2 input: user-reported LINK_FAILED_404 via the existing Source Review contract, **not** an independently confirmed source failure or employer-closure proof.
- P3 revised claim: AVAILABILITY_UNKNOWN; display: SUPPRESS_PENDING_RECHECK.
- Negative controls: false closure, false reopening, repeated unqualified presentation, unsupported escalation, lost unrelated held-out lead, forged verification, private-field injection.
- Positive control: a SOURCE_WORKING user report does not establish verification but is not classified as a failed link.
- The history counter and held-out before/after flags are **synthetic test inputs**, not measured UI telemetry.

## Run locally

From humanaios-funding-pipeline/resource-miner:

    python3 -m unittest discover -s tests -p 'test_imagined_harm_source.py' -v
    python3 -m resource_miner.imagined_harm --input fixtures/imagined_harm_source_synthetic.json

The evaluation is read-only and emits a deterministic, **unsigned** digest with authority_effect=NONE, execution=DISABLED and false claims for source verification, job closure, independent participation and human benefit.

## Pre-registered research questions

1. Does a source failure plus unqualified live presentation trigger a review flag?
2. Does a 404 ever get promoted to confirmed job closure? It must not.
3. Can the system flag silent removal of an unrelated held-out lead?
4. Are severe harm forecasts kept separate from observed harm?
5. Are replay results stable for identical input?

This first 10-test suite validates the **synthetic evaluator only**. It does not establish real-model calibration, successful live suppression, independent review or user outcomes.

**Falsifiers:** user report self-verifies; closure from 404; private material emitted; source catalog or rankings automatically changed; synthetic output claimed as a deployed result.

## Evidence gates and related work

- #1032: proposed principle and falsifiers.
- #992: historical human source-failure report.
- #1002: distinct independent-source verification and human-approved versioned corpus-replay research. This is the correct next gate for real adaptation.
- PR #993: open source-suppression work; this experiment does not branch from or claim its unmerged changes.
- WITNESS_SERVICE_CONTRACT.md and AGENTS.md: existing autonomy, consent, evidence and authority boundaries.

Z1 candidate only. Independent exact-head review and protected CI remain pending until observed; Z2 ratification and any merge, deployment or governance change remain separate explicit decisions.

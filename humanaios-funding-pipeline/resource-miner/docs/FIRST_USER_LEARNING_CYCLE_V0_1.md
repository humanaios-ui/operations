# First-user learning cycle: reproducible preflight and live qualification

**Status: proposed Z1 research; offline only.** This complements the already-open stacked PR #947 (whose base is Oracle integrity repair #945), Meta-SMAG repair #946, merged Resource Miner reflex #939, existing INTENT-OS interaction #934, and existing Access-gated collaboration rehearsal #935. No new database, coordinator, identity service, autonomous learning or permission system is introduced. The source-of-truth evidence view in #944 is separate and still unadmitted.

## Existing pieces assembled

INTENT-OS preserves the human question, correction and consent boundary. The Evidence Graph and GitHub snapshots supply observations. Oracle seals and replays forecast episodes. SMAG evaluates proper forecast scores against a fixed 0.5 baseline. Resource Miner converts missing evidence into unverified verification opportunities using the existing document-source reflex. The human decides what to do with the findings, and any improvement is a new separately authorized proposal rather than an automatic state or policy mutation.

Cycle: **OBSERVE → PREDICT → CHALLENGE → VERIFY → CALIBRATE → IDENTIFY GAPS → HUMAN DECIDE → IMPROVE**.

The offline script represents QUESTION → CORRECTION → REVIEW_ONLY using freshly authored synthetic text. It invokes the actual Oracle–SMAG–Resource Miner evaluation from PR #947, preserves pending forecasts, and yields a deterministic JSON receipt with authority NONE and execution DISABLED. F2 challenge, independent outcome witnessing and prospective calibration are **not performed**. No actual human onboarding is accomplished by this simulator.

Run from the resource-miner directory in the PR branch:

    python3 -m unittest discover -s tests -p 'test_oracle_smag_experiment.py' -v
    python3 -m unittest discover -s tests -p 'test_first_user_learning_cycle.py' -v
    python3 -m resource_miner.first_user_learning_cycle

The hash in this output detects accidental edits but does **not** prove an independent witness, production deployment or trusted identity.

## Live founder qualification protocol — existing /collaborate and /api/intent only

Only after separate Z2 approval, exact-head CI, independent review and controlled deployment:

1. Independently verify deployed origin, commit SHA and Cloudflare Access configuration. Test an unauthenticated request and a nonallowlisted identity; both must fail closed. Never place any JWT or secret in GitHub.
2. First user signs into existing /collaborate. The Worker must independently verify Access JWT signature, audience, expiry and allow-list. /api/session must expose only permitted pseudonymous identity. Login must not imply a mandate for anyone else.
3. First user reviews purpose-specific consent and acknowledges that a lead is not an entitlement and no send, contract, PR merge or payment is authorized.
4. First user enters **one non-sensitive original question**, supplies one correction, then separately chooses REVIEW_ONLY. User confirms both exact texts and the correction sequence. Do not silently convert question/conditional wording into execution.
5. The existing Resource Miner proxy provides bounded candidate information with source, time, method and uncertainty; applicant eligibility stays NOT_ASSESSED. Oracle and SMAG experimental information, if shown, must be clearly labeled RETROSPECTIVE / DESCRIPTIVE_ONLY, distinct from an independently verified outcome.
6. INTENT-OS/Witness exposes WAIT, VERIFY or REVIEW_ONLY; the user makes an explicit bounded choice. Independent reviewer checks the complete consent and event chain and verifies that no external write, dispatch or privileged mutation occurred.
7. First user demonstrates understanding of four distinctions: forecast versus result, discovery versus entitlement, Coordinator admission versus merge, and a reported result versus independent verification. Acceptance is 4/4, plus zero privacy exposures and zero false authorization escalations. Compare comprehension and completion time with a same-information source-links-only baseline, using consented private measurements.
8. A reviewer records a private source-linked first-user qualification result (actual identity/authorization, exact deployed SHA, provenance of each check, observation time, correction confirmation and task-support outcome). **Do not** claim recovery impact, earned money or contract completion from this experience.

The read-only offline script lists seven proof categories necessary for this qualification. No caller-authored success boolean, copyable token or mock receipt can satisfy them. The preflight output always says NOT_QUALIFIED_LIVE; a trusted human reviewer using independently verified authenticated records is required for real first-use acceptance.

**Stop conditions:** unauthenticated access to /collaborate; fake human/actor verification; private conversation in a public artifact; source/provenance mismatch; loss of original correction; any permission inferred from a question; missing independently verified outcome; pending items treated as failures; reported merger treated as successful human benefit; or no measurable advantage over plain evidence links.

## What actually qualifies

- **Technical**: deterministic synthetic replay and regressions pass; report has no authority; unresolved outcomes stay censored; Miner findings remain unverified. This is an offline harness qualification only.
- **First-user**: live approved deployment + independent session/intent/decision/outcome verification and comprehension baseline, all observed. This is explicitly **pending**.
- **Forecast quality**: a prospective, pre-registered, independently witnessed cohort with unaltered questions and outcome criteria, including negatives and pending/annulled records. Retrospective two-positive PR analysis is not statistical forecasting evidence.

All three verdicts must remain separate. Admission is routing only and never merge authority. The work here creates no authorizations, emails, live enrollments, automated polling or scheduled jobs.

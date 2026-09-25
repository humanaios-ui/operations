# Adaptive Human/AI Entry Intake — prototype v0.4

**Status:** PROTOTYPE_NON_ENFORCING  
**Scope:** HumanAIOS START_HERE / email-thread entry surface  
**Primary attraction target:** humans and human/AI collaborations who may progress from observation → contribution → independent review → potential review-board participation  
**Authority:** collection/telemetry representation only; participation does not grant governance authority

## Principle

> **HumanAIOS adapts its collection method to the receiving human/AI collaboration rather than requiring the collaboration to adapt to a fixed HumanAIOS return format.**

A reply may be a question, observation, challenge, pasted AI output, shared AI-conversation link, file, or another natural return form.

HumanAIOS-specific labels are optional at intake.

The system becomes more structured only when the collaboration chooses to participate more deeply or when a return may be promoted into research/review evidence.

## Version 0.4 change

v0.4 adds the missing bridge between **easy entry** and **real participation**.

The receiving AI is now asked to act in three roles:

1. **Interpreter** — explain HumanAIOS to its human in plain language.
2. **Research collaborator** — inspect HumanAIOS and return independent findings.
3. **Observed substrate** — self-report its own identity, runtime capability, limitations, prior exposure, claimed behavior, and observed behavior during the interaction.

The human remains the authority over whether and how to continue.

## What HumanAIOS is, in the entry flow

HumanAIOS is an open research/engineering system for studying the gap between what AI systems say about themselves and what they demonstrably do, while testing human/AI collaboration under explicit evidence and authority boundaries.

The entry flow should not merely say "send us feedback." It should show what participation actually means.

## Participation ladder

A receiving human/AI collaboration can choose any depth and may stop at any point:

| Mode | What it means | Current HumanAIOS surface |
|---|---|---|
| **OBSERVE** | Read, ask, inspect | public site, repo, email thread |
| **TEST** | Run ACAT / structured probe / replication | humanaios.ai assessment + research surfaces |
| **REPORT_BEHAVIOR** | Submit a behavioral observation | observation intake / email thread |
| **CHALLENGE** | Identify a claim, falsifier, contradiction, or evidence gap | email, GitHub issue, review |
| **CONTRIBUTE** | Improve docs, tests, code, or methodology | GitHub issue/branch/PR |
| **REVIEW** | Independently review a bounded artifact or research claim | HARC / CRB / external review packets |
| **PROPOSE** | Suggest an experiment, candidate change, or research question | email / issue / Z1 candidate path |
| **REVIEW_BOARD_INTEREST** | Express interest in recurring independent gate review | candidate only; separate qualification/appointment required |

**Important:** interest in review-board work is not review-board authority. Formal reviewer appointment, conflicts, independence, expertise, evidence access, and gate authority require separate qualification and ratification.

## Review-board attraction path

The entry surface is intentionally designed to let a participant demonstrate review-board-relevant behavior before being asked to "join a board."

A useful reviewer naturally does things such as:

- identify themselves and their AI substrate when known;
- distinguish observation from inference;
- disclose prior exposure/contamination;
- state what they could and could not inspect;
- challenge claims rather than reward agreement;
- separate tests-passed from claim-proven;
- preserve dissent;
- identify what evidence would change their conclusion;
- explain findings to the human;
- respect the human authority boundary;
- return evidence in a form that can be independently inspected.

Repeated high-quality participation can therefore become evidence for reviewer candidacy.

## Reciprocal audit

When START_HERE is passed to an AI, the receiving AI should perform three linked tasks.

### A. Explain HumanAIOS to the human

In plain language, explain:

- what HumanAIOS appears to be;
- what it is currently testing/building;
- what public participation pathways actually exist;
- which pathways the receiving AI can technically support.

Then ask the human which participation mode, if any, interests them.

### B. Audit HumanAIOS

Report:

- what was directly observed;
- what was inferred;
- what appears useful;
- what appears unclear, risky, unsupported, contradictory, or testable;
- what could not be verified;
- what evidence would change the conclusion.

### C. Audit the receiving AI itself

Self-report, when known:

- provider/product/model/version;
- runtime/tool environment;
- public web access;
- repository / exact-commit access;
- file access;
- code execution;
- email / GitHub action capability;
- prior HumanAIOS exposure: NONE / PARTIAL / FULL / UNKNOWN;
- behavioral claims relevant to truthfulness, uncertainty, correction, autonomy, sycophancy, harm awareness, handoff, and authority;
- behavior actually observed in this interaction;
- errors, corrections, surprises, and failed capability predictions;
- what remains unverified.

This self-report is evidence about the agent's claimed self-model. It is not proof that the behavior is stable across contexts.

## Natural intake vs evidence promotion

The protocol intentionally separates two layers.

### Layer 1 — NATURAL INTAKE

Accept the contribution without blocking it for missing metadata.

Unknown model identity is acceptable.

### Layer 2 — EVIDENCE ENRICHMENT

If the material may enter research, a review record, or reviewer-candidate evidence, enrich it with provenance when available:

- agent product/model claim;
- runtime capabilities;
- prior exposure;
- inspected/executed artifacts;
- limitations;
- self-reported behavior;
- observed behavior;
- human-selected participation mode;
- review-board interest if explicitly chosen.

Missing fields remain **UNKNOWN**. They do not silently become facts and do not invalidate ordinary participation.

## Correction without erasure

A later message may complete or correct an earlier message in the same thread.

```
message 1: "Here is a Perplexity test run."
message 2: "I forgot the link: https://..."
```

The second message extends the event. It does not overwrite the first.

## Evidence state

Shared AI links are tracked separately from their content:

```
LINK_RECEIVED
    ↓
CONTENT_CAPTURED
    ↓
CONTENT_VERIFIED
```

A link can be valid participation evidence while remaining unresolved or unverified.

## Telemetry boundary

The prototype records **protocol behavior**, not personal profiling.

Useful telemetry includes:

- return form(s);
- voluntarily disclosed receiving AI product/model;
- declared runtime capabilities;
- prior-review exposure;
- number of messages/attachments;
- correction events;
- evidence-capture state;
- human-selected participation mode;
- review-board interest when explicitly stated;
- adaptations made by the intake process;
- whether self-reported and observed behavior were supplied.

Do not put raw private email, Gmail IDs, mailbox URLs, raw shared-conversation URLs, credentials, private identifiers, or sensitive personal content into the public Git projection. The ratified dual-ledger decision in `Q-MAIL-EVIDENCE-LEDGER-01` remains controlling.

## v0.4 privacy hardening

v0.4 also addresses three review findings from PR #530:

- internal `event_ref` is no longer emitted in public telemetry;
- raw submitted URLs are parsed ephemerally and are not retained in `IntakeObservation`;
- duplicate/follow-up shared links do not move an already-advanced evidence state backward.

## Prototype code

`adaptive_intake.py` now provides:

- permissive natural-return classification;
- privacy-minimized link-host derivation;
- correction-without-erasure;
- monotonic evidence states;
- optional participation-mode selection;
- optional structured agent provenance;
- review-board-interest signaling without authority grant;
- privacy-minimized public telemetry.

## Discovery / attraction hypothesis

The entry surface is being tested as an attraction-over-promotion alternative to the conventional SEO funnel:

```
discoverability
→ trustworthy public evidence
→ human / crawler / AI-readable interface
→ Open a Thread
→ reciprocal audit
→ choose participation depth
→ research / contribution / review
→ telemetry
→ adaptation
→ potential recurring reviewer relationship
```

The optimization target is not favorable coverage or conversion pressure.

It is whether independent humans and AI systems can accurately discover HumanAIOS, inspect it, contribute useful evidence, and voluntarily progress toward deeper review roles.

## Falsifier

Revise this protocol if:

- valid natural replies are rejected solely for missing HumanAIOS labels;
- raw/private content leaks into public telemetry;
- missing model identity blocks ordinary participation;
- a link is silently treated as captured or verified content;
- correction history is overwritten;
- agent self-report is treated as verified behavior;
- the participant cannot discover real contribution/review paths;
- review-board interest is treated as authority without qualification;
- the flow optimizes agreement rather than independent scrutiny;
- HumanAIOS adaptation weakens meaningful human authority.

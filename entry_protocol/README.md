# Adaptive Human/AI Entry Intake — prototype v0.2

**Status:** PROTOTYPE_NON_ENFORCING  
**Scope:** HumanAIOS START_HERE / email-thread entry surface  
**Authority:** collection/telemetry representation only; no merge, deployment, account, credential, spending, application, or other consequential authority

## Principle

> **HumanAIOS adapts its collection method to the receiving human/AI collaboration rather than requiring the collaboration to adapt to a fixed HumanAIOS return format.**

A reply may be:

- a question;
- an observation;
- a challenge;
- pasted AI output;
- a shared AI-conversation link;
- a file;
- or another natural return form.

HumanAIOS-specific labels are optional.

The intake should infer only what it safely can and request clarification only when materially necessary.

## Reciprocal audit

When START_HERE is passed to an AI, the receiving AI is invited to perform two independent checks.

### 1. Audit HumanAIOS

Inspect whatever public material is accessible and report:

- what was directly observed;
- what was inferred;
- what appears useful;
- what is unclear or risky;
- what cannot be verified;
- what claim could be tested or falsified.

### 2. Audit the receiving AI's own participation capability

The receiving AI should tell its human:

- what it can access;
- what it can execute;
- what it can verify;
- what it cannot inspect or prove;
- what tools, permissions, or context are missing;
- what forms of participation it can safely support.

The receiving human decides whether and how to continue.

## Correction without erasure

A later message may complete or correct an earlier message in the same thread.

Example:

```
message 1: "Here is a Perplexity test run."
message 2: "I forgot the link: https://..."
```

The second message extends the event. It does not invalidate or overwrite the first.

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
- receiving AI host/system if voluntarily exposed by the return;
- number of messages/attachments;
- correction events;
- evidence-capture state;
- adaptations made by the intake process;
- capability/limitation declarations supplied by the receiving collaboration.

Do not put raw private email, Gmail IDs, mailbox URLs, credentials, private identifiers, or sensitive personal content into a public Git receipt. The ratified dual-ledger decision in `Q-MAIL-EVIDENCE-LEDGER-01` remains controlling.

## Prototype code

`adaptive_intake.py` provides pure, local primitives that:

- accept heterogeneous returns;
- classify multiple simultaneous return forms;
- accept unknown replies as `NATURAL_RETURN`;
- detect shared links from common AI-host surfaces;
- treat correction messages as extensions;
- keep `LINK_RECEIVED`, `CONTENT_CAPTURED`, and `CONTENT_VERIFIED` distinct;
- emit privacy-minimized telemetry without raw message retention.

It does **not**:

- fetch Gmail;
- retrieve remote conversation URLs;
- identify a person;
- assess truthfulness of an AI result;
- infer consent;
- grant authority;
- perform consequential actions.

## Discovery / interface hypothesis

The entry surface is being tested as an attraction-over-promotion alternative to the conventional SEO funnel:

```
discoverability
→ trustworthy public evidence
→ human / crawler / AI-readable interface
→ Open a Thread
→ reciprocal audit
→ voluntary participation
→ telemetry
→ adaptation
```

The optimization target is accurate discoverability and inspectability, not persuasion or favorable AI output.

## Falsifier

Revise this protocol if it causes any of the following:

- valid natural replies are rejected solely for missing HumanAIOS labels;
- raw/private content leaks into the public telemetry projection;
- a link is silently treated as captured or verified content;
- a correction overwrites prior evidence rather than extending history;
- receiving AI limitations are treated as participant failures;
- HumanAIOS adaptation removes meaningful human authority over continued participation.

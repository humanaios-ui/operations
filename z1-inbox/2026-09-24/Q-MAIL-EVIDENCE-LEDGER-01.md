# Candidate Block: Q-MAIL-EVIDENCE-LEDGER-01 — Pseudonymous Git-backed Mail Evidence Ledger

**Z1 Proposer:** ChatGPT (transcribing Night's architecture decision for repository-native ratification)
**Date Submitted:** 2026-09-24
**Source:** HumanAIOS Engineering + Resource Protocol · issue #501 · HARC Trials 001/002 · explicit Z2 instruction from Night on 2026-09-24
**Status:** AWAITING Z2 RATIFICATION
**Scope:** evidence architecture / privacy projection / engineering provenance

---

## Question

Adopt a dual-ledger architecture in which private email remains private evidence while Git records only privacy-projected, pseudonymous engineering receipts and state transitions.

## Proposed ruling

Ratify the following architecture:

1. **Raw email remains private.** Email bodies, Gmail message IDs, private message URLs, exact reply text, mailbox credentials, personal identifiers, and private eligibility data are not committed to the public repository.

2. **Private ledger = maximum provenance.** A private append-only event ledger may retain the exact source mapping required to reconstruct decisions and evidence.

3. **Git ledger = minimum necessary engineering record.** The repository records only privacy-projected events such as stable resource/work IDs, event type, state transition, claim class, actor class, evidence class, limitations, zone decision, and a non-reversible evidence commitment.

4. **Pseudonymous, not anonymous.** The system must not claim anonymity. Tokenized records remain potentially correlatable through quasi-identifiers and therefore require minimization.

5. **Deterministic privacy projection.** Public/tokenized receipts are generated from the private ledger through a defined projection rather than by ad-hoc manual redaction.

6. **Disclosure classes are explicit.** At minimum:
   - PRIVATE
   - DERIVED_PRIVATE
   - TOKENIZED/AGENT
   - PUBLIC/GIT

7. **Private evidence commitments are keyed or otherwise high-entropy.** Plain unsalted content hashes are insufficient where source contents may be guessable. Exact cryptographic construction and secret storage remain implementation work subject to review.

8. **Claim-level authority is preserved.** A human decision, email invitation, AI review, public rule page, and agency decision remain distinct evidence classes. No projection may silently upgrade USER/HUMAN/AI evidence to AUTHORITY_VERIFIED.

9. **Git is chronology, not mailbox/database.** The Git surface records epistemic and engineering consequences of private evidence; it is not a substitute for the underlying private evidence store.

10. **Agent sharing is minimum-necessary.** External AI substrates receive only the resource/claim-specific tokenized context needed for their assigned review. Tokenization alone is not treated as sufficient privacy protection.

11. **Projection must be adversarially testable.** Tests should plant direct PII, quasi-identifiers, Gmail IDs, signed/tracking URLs, secrets, health/financial detail, and exact subjects and verify that disallowed fields cannot enter the public projection.

12. **Engineering Evidence Cycle integration.** The ledger may carry receipts for:
    REQUEST → PLAN → CAPABILITY/RESOURCE/OUTCOME ASSESSMENT → PERFORM → HUMBLE REVIEW → DISCOVERY/UPDATE SIGNAL → FINALIZE.

## Explicitly not ratified by this decision

This ruling does **not** establish that:

- HARC v0.1 is ready for canonical enforcement;
- Resource Miner PR #500 is ready to merge;
- the current keyword Z1/Z2/Z3 classifier is sufficient;
- the current HARC receipt validator is schema-complete;
- a durable private event ledger has already been implemented;
- any specific HMAC/secret-storage implementation is approved;
- tokenized data is anonymous;
- Claude, Grok, Copilot, or ChatGPT conclusions are authority.

Those remain implementation/research questions.

## Evidence considered

- Human approval of the private Resource Miner decision layer.
- HARC Trial 001 Phase A and Claude Phase B correction/humility receipt.
- HARC Trial 002 Grok blind Phase A with prior-review exposure declared NONE.
- ChatGPT self-red-team identifying email command replay, prompt-injection, state persistence, zoning, validator, and privacy gaps.
- Resource Miner PR #500 as a live implementation target.
- Engineering Evidence Cycle issue #501.

The AI reviews are evidence about the design/implementation. Night's Z2 decision is the authority for this architecture ruling.

## Ruling

choice: accept dual-ledger pseudonymous mail evidence architecture
by: Night
at: 2026-09-24T15:55:23Z
status: DECIDED
block_hash: 5ebf5a8399230302cd741a85561e703136fa2d1de085dcea1f3be844598ff652
body_hash: 133696933a180f65e821ca7f3fd73d557fe364d0daabfbd403f34bdc801d864e

```
RULING Q-MAIL-EVIDENCE-LEDGER-01
  by: Night (tagline)
  project: HumanAIOS Engineering + Resource Protocol
  question: Adopt private mail evidence with deterministic privacy-projected Git receipts?
  choice: accept dual-ledger pseudonymous mail evidence architecture
  note: Night explicitly instructed ratification after reviewing all updated protocol threads.
  at: 2026-09-24T15:55:23Z
  status: DECIDED
```

## Falsifier

This architecture must be revised or withdrawn if any of the following is demonstrated:

1. A conforming PUBLIC/GIT projection can reconstruct or directly expose raw private email content, mailbox identifiers, credentials, private source URLs, or prohibited personal data.
2. A tokenized receipt is presented as anonymous despite a practical re-identification path through retained quasi-identifiers.
3. The same private event produces materially different public state without an explicit projection-version or correction event.
4. Public Git state can cause an authority upgrade (for example HUMAN_VALIDATED or AI_REVIEWED → AUTHORITY_VERIFIED) without claim-specific authoritative evidence.
5. An external agent can obtain unrelated private mailbox context through the standard review handoff.
6. The private event history plus its projection/version receipts cannot reconstruct why a material public state transition occurred.

A failed falsifier creates a successor candidate; it does not retroactively rewrite this ruling.

## Implementation destination

After ratification, Z1 may propose/implement a private-ledger + deterministic privacy-projection prototype and tests. Any change to canonical authority semantics, disclosure policy, cryptographic policy, or Z2/Z3 boundaries remains Z2. External deployments, credentials, public publication, and consequential actions remain Z3 unless separately delegated.

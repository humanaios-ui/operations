---
title: INTENT-OS × RNOLA — repository-native operator learning integration
status: draft
written: 2026-09-25
authority: Z1 implementation candidate; advisory learning only
related_issue: 529
---

# INTENT-OS × RNOLA

## Purpose

Integrate Repository-Native Operator Learning Audit (RNOLA) into INTENT-OS without creating a parallel learning platform and without changing existing authority semantics.

The design rule is:

> Every meaningful INTENT-OS act should be capable of becoming a learning object, and every RNOLA learning claim should be testable against an actual repository or INTENT-OS act.

RNOLA is therefore a lens over INTENT-OS, not a separate source of truth.

## 1. Shared control / learning loop

~~~
INTENT
  -> PROPOSAL
  -> IMPLEMENTATION
  -> EVIDENCE
  -> AUTHORITY
  -> CONSEQUENCE
  -> OBSERVATION
  -> LEARNING
  -> revised intent
~~~

The states are intentionally non-equivalent:

| state | question |
|---|---|
| INTENDED | What did the human ask for? |
| PROPOSED | What change did an agent or contributor produce? |
| VERIFIED | What does bounded evidence support? |
| AUTHORIZED | What did the authority holder permit? |
| OBSERVED | What actually happened? |
| LEARNED | What can the operator now explain against evidence? |

A system may be PROPOSED without being VERIFIED, VERIFIED without being AUTHORIZED, and AUTHORIZED without producing the intended OBSERVED consequence.

## 2. INTENT-OS surfaces as learning objects

| INTENT-OS surface | RNOLA learning use |
|---|---|
| ui/intent-os-humanaios-v3_3.html | read system state and distinguish rendered claim from verified seal |
| tools/decision_relay.py | trace human input into a durable branch / PR proposal |
| REQ-* records | distinguish conversation from repository state |
| candidate blocks | distinguish proposal from ratification |
| pull requests | inspect the exact diff before authority is exercised |
| T0-T7 test harness | learn bounded evidence and test scope |
| GitHub Actions | learn event-triggered CI and failure classification |
| intent_os_reconcile_v1_0.py | trace post-merge authority into recorded provenance |
| INDEX / ruling records | inspect durable governance state |
| board seal checker | learn currentness and stale evidence |
| Witness Ledger candidate | future linkage between human rationale and machine execution |

## 3. RNOLA ten-concept map

| concept | INTENT-OS implementation |
|---|---|
| Repository | humanaios-ui/operations |
| Commit / SHA | exact HEAD, read.against, commit or candidate hash |
| Branch | z2/*, req/*, intent-os/*, feature branches |
| Diff | proposed delta visible in a pull request |
| Pull Request | review boundary before merge |
| Test | T0-T7, pytest, smoke, validation checks |
| CI workflow | event-triggered GitHub Actions |
| Dependency | board -> relay -> GitHub -> reconcile -> index |
| Authority boundary | Z1 proposes, Z2 decides, Z3 executes where defined |
| Provenance | hashes, SHAs, receipts, requests, rulings, reconciliation |

## 4. Operator-check record

RNOLA may emit an operator-check record after a teach-back. The canonical schema is:

schemas/intent_os_operator_check_v1.schema.json

An operator check records:

- the exact learning object and ref;
- the operator's explanation;
- evidence personally inspected;
- what understanding was demonstrated;
- what remains partial, unknown, or untested;
- the authority consequence the operator believes follows;
- one next learning object.

It does not record a numeric competence score.

It is deliberately marked advisory_only = true and can_authorize = false.

## 5. Persistence

Phase 1 supports two persistence levels:

1. Transient: outputs/rnola/ for local or generated learning passes.
2. Durable advisory evidence: attach the operator-check JSON or an equivalent structured block to the relevant PR or review record.

Neither location changes the authorization state of the underlying artifact.

The proposed INTENT-OS Witness Ledger may later reference operator-check records, but this integration does not ratify that ledger and does not make a learning record a governance credential.

## 6. PR learning sequence

For an authority-bearing PR:

~~~
intent
  -> exact PR head
  -> diff
  -> code behavior
  -> tests and bounded claims
  -> CI status and scope
  -> dependencies / side effects
  -> authority consequence
  -> operator teach-back
  -> operator-check record
  -> human decision
  -> observed consequence
~~~

The learning pass is not a replacement for required review or CI.

## 7. Example operator check

~~~
{
  "schema": "intentos/operator_check_v1",
  "advisory_only": true,
  "can_authorize": false,
  "subject": {
    "type": "pull_request",
    "repository": "humanaios-ui/operations",
    "ref": "<exact-head-sha>",
    "identifier": "PR-XYZ",
    "artifact_paths": ["path/to/file.py"]
  },
  "intent": "Integrate RNOLA as an INTENT-OS learning layer.",
  "question": "What will merging this PR change?",
  "operator_response": "My explanation in my own words.",
  "evidence_inspected": [
    {
      "kind": "diff",
      "locator": "PR-XYZ",
      "observation": "The PR adds an advisory learning skill and schema; it does not add merge authority."
    }
  ],
  "calibration": {
    "demonstrated": ["proposal versus authorization"],
    "partial": ["CI implementation details"],
    "not_tested": ["rollback behavior"],
    "unknown": []
  },
  "authority_consequence": "If merged, the learning layer becomes repository state; the record itself still cannot authorize future changes.",
  "next_learning_object": "Inspect the CI job that validates the schema.",
  "created_at": "2026-09-25T00:00:00Z"
}
~~~

## 8. Current implementation boundary

Implemented in this change:

- RNOLA skill under tools/skills/;
- operator-check JSON Schema;
- schema behavior tests;
- advisory RNOLA hook in the INTENT-OS board runbook;
- this integration contract.

Not implemented by this change:

- a new public UI;
- automatic board mutation;
- mandatory operator checks;
- numeric competence scoring;
- Witness Ledger ratification;
- new merge requirements;
- new deployment authority;
- any automatic decision on behalf of Z2.

## 9. Falsifiers

The integration should be reconsidered if:

1. an operator check is treated as authorization;
2. RNOLA produces conclusions without citing an exact artifact/ref;
3. operator teach-back becomes a checkbox without evidence inspection;
4. repository cognitive load increases because RNOLA duplicates existing INTENT-OS state;
5. learning records make it harder to distinguish proposed, verified, authorized, and observed states.

The intended direction is one evidence substrate serving both operation and learning.

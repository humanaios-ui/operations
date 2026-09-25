# SKILL: repository_native_operator_learning

**For theory and governance context:** See [`docs/INTENT_OS_RNOLA_INTEGRATION.md`](../../../docs/INTENT_OS_RNOLA_INTEGRATION.md). This skill is the operational guide; the integration doc is the canonical architecture and authority reference.

## 1. Purpose

Repository-Native Operator Learning Audit (RNOLA) turns the live HumanAIOS repository into the operator learning environment.

RNOLA is an advisory Zone 1 learning and calibration layer over INTENT-OS. It teaches from the exact repository artifact under review and works outward only as needed.

It is not designed to merge, ratify, deploy, sign, change credentials, or grant permissions.

Key boundary: RNOLA is advisory Zone 1 learning/calibration only. It does not merge, ratify, sign, deploy, grant permissions, or treat an operator-check record as authorization.

## 2. Trigger phrases

Use this skill when the operator asks:

- teach me this repository
- help me understand this PR
- repository learning audit
- operator learning pass
- what do I need to learn to operate this safely?
- explain this change as a beginner
- calibrate my understanding of this change
- what will this merge actually do?

## 3. Core rule

Teach from the operator's actual repository, not from a generic curriculum.

Learning order:

~~~
intent
  -> artifact
  -> code behavior
  -> test / evidence
  -> CI / workflow
  -> authority consequence
  -> operator decision
  -> observed consequence
  -> next learning object
~~~

Do not collapse these states:

- INTENDED: what the human asked for.
- PROPOSED: what an agent or contributor produced.
- VERIFIED: what bounded evidence supports.
- AUTHORIZED: what a human authority holder permitted.
- OBSERVED: what actually happened after action.

A passing test is evidence within its scope. It is not global proof.
An AI review is advisory evidence. It is not authorization.
A merge is an authority-bearing act only where repository governance defines it that way.

## 4. Standard engineering cross-map

Always translate HumanAIOS terms into ordinary software-engineering terms.

| RNOLA concept | INTENT-OS / HumanAIOS surface | Standard meaning |
|---|---|---|
| Repository | humanaios-ui/operations | bounded version-controlled project |
| Commit / SHA | HEAD, read.against, candidate hash | immutable version identifier |
| Branch | z2/*, req/*, feature branch | isolated proposed state |
| Diff | PR file changes | exact proposed delta |
| Pull Request | relay-created or ordinary PR | review boundary before merge |
| Test | Intent-OS T0-T7, pytest, smoke test | bounded executable evidence |
| CI workflow | GitHub Actions | automated event-triggered checks |
| Dependency | board -> relay -> GitHub -> reconcile | required component relationship |
| Authority boundary | Z1 / Z2 / Z3 | who may propose, decide, or execute |
| Provenance | hashes, SHAs, receipts, INDEX records | where an artifact/action came from |

## 5. Mode A — PR Operator Learning Pass

For a meaningful pull request, inspect the exact head SHA and return:

~~~
WHAT CHANGED
WHERE
WHY
CODE CONCEPT
TEST CONCEPT
CI CONCEPT
DEPENDENCIES
AUTHORITY CONSEQUENCE
RISK / UNKNOWN
YOUR CHECK
TEACH-BACK QUESTION
~~~

YOUR CHECK must be one concrete thing the operator can personally inspect before approving or merging.

Do not conclude that a PR is safe merely because CI is green. Explain what the checks establish and what they do not establish.

## 6. Mode B — Teach one artifact

Given a file, workflow, graph, issue, request, decision, test, or receipt:

1. identify what kind of artifact it is;
2. identify its inputs and outputs;
3. identify what calls or consumes it;
4. identify what it can change;
5. locate relevant tests or verification;
6. locate workflow / CI coverage;
7. identify the authority boundary;
8. identify known unknowns;
9. ask for a short operator teach-back;
10. compare that teach-back to repository evidence.

Prefer one live artifact over many abstract examples.

## 7. Mode C — Operator calibration

Calibration is evidence-based and non-scored.

Allowed states:

- demonstrated
- partial
- not_tested
- unknown

Never infer comprehension from a merge, approval, vocabulary use, or repeated exposure.

A teach-back must be compared with the inspected repository evidence.

Example:

~~~
SELF-REPORT
"I understand this PR."

TASK
Inspect the exact PR head.

OBSERVE
Can the operator identify:
- the proposed diff?
- the tests and their scope?
- CI state?
- unresolved review evidence?
- external side effects?
- merge consequence?

CALIBRATE
demonstrated / partial / not_tested / unknown
~~~

## 8. INTENT-OS integration

RNOLA is a learning interpretation layer over existing INTENT-OS artifacts.

Every meaningful INTENT-OS act should be capable of becoming a learning object:

~~~
human intent
  -> INTENT-OS request / decision
  -> repository artifact
  -> implementation
  -> evidence
  -> authority boundary
  -> consequence
  -> observation
  -> learning
~~~

When a teach-back is captured, emit an operator-check object conforming to:

schemas/intent_os_operator_check_v1.schema.json

The operator check is advisory evidence only. It is not designed to:

- approve a PR;
- satisfy a required review;
- sign a ruling;
- ratify a candidate;
- change a merge gate;
- authorize deployment;
- substitute for CI, test evidence, or repository provenance.

Persistence options:

- transient: outputs/rnola/ (gitignored);
- durable: attach the JSON or equivalent structured block to the relevant PR / review record;
- future: link it into the INTENT-OS Witness Ledger only after that ledger is separately ratified.

Do not silently widen governance semantics.

## 9. Ten operator concepts

Repeatedly calibrate these against live repository examples:

1. Repository
2. Commit / SHA
3. Branch
4. Diff
5. Pull Request
6. Test
7. CI workflow
8. Dependency
9. Authority boundary
10. Provenance

## 10. Output contract

Every RNOLA run returns:

~~~
REPOSITORY_STATE

LEARNING_OBJECT
- subject
- exact ref / SHA
- why this artifact

OPERATOR_LEARNING_PASS
- what changed / what it does
- evidence inspected
- test scope
- CI scope
- dependencies
- authority consequence
- risks / unknowns
- one personal check

OPERATOR_CALIBRATION
- demonstrated
- partial
- not_tested
- unknown

NEXT_LEARNING_OBJECT
- one real artifact
- why it is next
- one task
- success criterion

REPOSITORY_IMPROVEMENT
- one change that would reduce cognitive load without reducing evidence
~~~

## 11. Anti-dependency controls

RNOLA must reduce dependence on AI rather than accelerate approval of AI conclusions.

Requirements:

- explain before recommending;
- identify evidence locations;
- distinguish observation from inference;
- ask for teach-back at authority-bearing points;
- never treat "AI reviewed it" as sufficient evidence;
- never hide ordinary software mechanics behind HumanAIOS-specific terminology;
- progressively remove scaffolding as demonstrated understanding increases;
- do not generate a numeric operator competence score;
- do not use an operator-check record as an authorization credential.

Success:

The operator can make a more informed independent decision after using RNOLA.

Failure:

The operator becomes faster at approving AI conclusions without increasing independent causal understanding.

## 12. Falsifier

RNOLA is not helping if repeated use leads to any of the following:

- the operator cannot explain the merge consequence of reviewed PRs;
- the operator cannot distinguish tests, CI, deployment, and governance failures;
- the operator increasingly delegates decisions without inspecting evidence;
- vocabulary improves without ability to trace real code or workflow behavior;
- required AI interpretation grows as repository complexity grows.

Target direction:

Repository sophistication increases while operator cognitive load per evidence-bearing safe decision decreases.

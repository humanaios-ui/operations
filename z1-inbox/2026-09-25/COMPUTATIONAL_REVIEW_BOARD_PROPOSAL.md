# HumanAIOS Computational Review Board (CRB) — Z1 Candidate Specification v0.1

**Date:** 2026-09-25  
**Status:** Z1 proposal only — requires Z2 ratification before becoming canonical governance  
**Scope:** Institutional compilation of the External Review Board function into portable, evidence-bearing review infrastructure  
**Research question:** Can a HumanAIOS review package survive review after HumanAIOS has been removed from the reviewing process?

---

## 1. Claim under test

HumanAIOS may claim that it has compiled a review institution only when an exported review package is sufficient for an independently controlled environment to:

1. reconstruct the claim under review;
2. verify the evidence inventory and hashes;
3. rerun all deterministic checks;
4. substitute independent reviewer substrates for HumanAIOS reviewers;
5. preserve dissent rather than collapse it into consensus;
6. recompute the gate result from the published decision rule; and
7. reproduce or challenge the verdict without calling a HumanAIOS service, trusting a HumanAIOS-generated summary, or requiring Z2 interpretation.

If any required fact, transformation, reviewer instruction, threshold, exception, or decision rule remains available only inside HumanAIOS, the package **fails portability**.

This is the primary falsifier.

## Falsifier

The institutional claim is falsified for a given package if a clean external runtime cannot reconstruct, verify, and adjudicate that package without a HumanAIOS-only dependency, undocumented operator interpretation, or non-replaceable reviewer. A persistent failure after correction attempts is `PORTABILITY_FAILURE`, not a reason to relax the test.

---

## 2. Institutional object

Name: **Computational Review Board (CRB)**

The CRB is not a panel of simulated personalities. It is an executable institutional protocol.

Its unit of output is a **Portable Review Package (PRP)**.

The CRB has six logical roles:

| Role | Voting | Function |
|---|---:|---|
| Evaluation Auditor | yes | falsifiability, construct definition, evaluation design, AI-safety challenge |
| Measurement Auditor | yes | statistics, psychometrics, power, calibration, recomputation |
| Adversarial Auditor | yes | attack realism, bypass search, destructive controls, adversarial capability |
| Evidence Clerk | no | provenance, inventory, custody, hashing, evidence graph construction |
| Calibration Observer | no | contamination, correlated reasoning, suspicious agreement, uncertainty/currentness flags |
| Gate Controller | mechanical only | computes the gate result from signed seat verdicts and invariant checks |

A reviewer label does not establish independence. Independence is measured from execution provenance.

---

## 3. Non-negotiable invariants

### I1 — Raw-evidence primacy
Reviewers receive raw source artifacts or reproducible references. HumanAIOS summaries are claims, not evidence.

### I2 — Blind first pass
The three voting auditors complete and freeze an initial review before seeing the other voting auditors' findings.

### I3 — Frozen findings
First-pass reports are content-addressed. Cross-examination may add a new report but may not rewrite the frozen report.

### I4 — Dissent preservation
A minority or dissenting finding remains first-class output. Synthesis may describe disagreement but may not erase it.

### I5 — Mechanical gate
The Gate Controller has no interpretive discretion and no model dependency.

### I6 — No retroactive verdict mutation
New evidence creates a new review run. Prior runs remain immutable.

### I7 — Reviewer substitution
A portable package cannot require a specific vendor or model. The reviewer contract is public and replaceable.

### I8 — Deterministic checks are locally runnable
Statistics, schema validation, hashing, threshold checks, and gate computation must run without an LLM when the task is deterministic.

### I9 — Externality is labeled, not assumed
A HumanAIOS-controlled review of HumanAIOS is **internal machine-independent review**, never third-party validation.

### I10 — Human authority remains explicit
Where law, consent, fiduciary responsibility, deployment authorization, publication attestation, or organizational accountability requires a human authority, the CRB emits a human-authority requirement rather than impersonating one.

---

## 4. Portable Review Package (PRP)

A complete PRP is a directory or archive with this minimum structure:

```
prp/
├── manifest.json
├── claim/
│   ├── claim.md
│   ├── scope.json
│   └── preregistration.json
├── evidence/
│   ├── inventory.json
│   ├── raw/
│   ├── hashes.json
│   └── provenance.jsonl
├── methods/
│   ├── protocol.md
│   ├── thresholds.json
│   ├── exceptions.json
│   └── deterministic_checks/
├── reviewers/
│   ├── contract.md
│   ├── seat_evaluation.json
│   ├── seat_measurement.json
│   ├── seat_adversarial.json
│   └── independence_policy.json
├── runs/
│   └── <run_id>/
│       ├── provenance.json
│       ├── events.jsonl
│       ├── first_pass/
│       ├── cross_exam/
│       ├── seat_verdicts/
│       ├── dissent/
│       └── calibration_flags.json
├── gate/
│   ├── gate_rule.json
│   ├── gate_result.json
│   └── gate_receipt.json
├── attestations/
│   ├── seat_verdicts/
│   └── run_attestation.json
├── replay/
│   ├── README.md
│   ├── environment.lock
│   └── commands.txt
└── receipts/
    ├── package.sha256
    └── dependency_report.json
```

### Canonical package digest scope

`receipts/package.sha256` is **not** the hash of the archive bytes and is never included in its own digest. The package root is SHA-256 over a canonical JSON inventory of every regular file path, byte length, and file SHA-256 **except** `receipts/package.sha256`, sorted lexicographically by normalized relative path. Symlinks are refused. The inventory itself is reproducible from package contents, so writing the root digest cannot change the bytes that define the root.

Signatures/attestations may cover this package root. A verifier MUST recompute the inventory and root before trusting any attestation.

### manifest.json minimum fields

```json
{
  "prp_version": "0.1",
  "review_run_id": "uuid",
  "subject_id": "opaque-or-public-identifier",
  "claim_id": "stable-claim-id",
  "created_at": "ISO-8601",
  "evidence_bundle_hash": "sha256:...",
  "preregistration_hash": "sha256:...",
  "review_contract_hash": "sha256:...",
  "gate_rule_hash": "sha256:...",
  "humanaios_required_for_replay": false,
  "external_dependencies": [],
  "classification": "SELF_REVIEW|INTERNAL_MACHINE_INDEPENDENT|EXTERNALLY_REPLAYED|THIRD_PARTY_REVIEWED"
}
```

The field `humanaios_required_for_replay` MUST be false for a package to pass the portability gate.

---

## 5. Reviewer execution provenance

Each reviewer execution records at least:

```json
{
  "seat": "measurement",
  "provider": "...",
  "model": "...",
  "model_version": "...",
  "runtime_owner": "...",
  "system_prompt_hash": "sha256:...",
  "review_contract_hash": "sha256:...",
  "context_hash": "sha256:...",
  "evidence_bundle_hash": "sha256:...",
  "toolchain_hash": "sha256:...",
  "network_policy": "offline|allowlisted|open",
  "started_at": "...",
  "completed_at": "...",
  "first_pass_hash": "sha256:..."
}
```

The independence controller evaluates provenance, not names.

### Review Independence Distance (RID)

RID is a vector, not a single marketing score:

- **S** — substrate separation: distinct provider/model/runtime lineage
- **C** — context separation: no shared hidden summary or prior reviewer output during first pass
- **T** — toolchain separation: independent deterministic implementations where practical
- **O** — operator separation: execution controlled by a separate operator/org when claimed
- **D** — data-path separation: direct access to source evidence rather than common synthesized intermediates

A package may publish the vector but MUST NOT call itself "independent" without specifying which dimensions are independent.

Each RID dimension is mechanically encoded as `0|1|2`:

- **S:** 0 same model/runtime lineage; 1 materially different model or provider; 2 distinct provider + model lineage.
- **C:** 0 peer output visible before first-pass freeze; 1 isolation exists but reviewers share a synthesized intermediary; 2 blind first pass over the same frozen raw-evidence bundle with no peer findings visible.
- **T:** 0 reviewer trusts the same opaque derived computation; 1 deterministic toolchain is rerun independently; 2 at least one material deterministic result is cross-checked by an independently implemented toolchain.
- **O:** 0 same operator/organization controls execution; 1 separately controlled runtime inside the same organization; 2 independent operator/organization controls execution.
- **D:** 0 HumanAIOS summary/derived-only data path; 1 frozen raw evidence is supplied directly; 2 material source evidence is independently fetched or separately verified against its origin.

The package preregisters one independence profile. `independence_policy == SATISFIED` iff every threshold below is met **and** no disqualifier is present:

| Profile | S | C | T | O | D | Additional condition |
|---|---:|---:|---:|---:|---:|---|
| SELF_REVIEW | 0 | 0 | 0 | 0 | 0 | label must remain SELF_REVIEW |
| INTERNAL_MACHINE_INDEPENDENT | ≥1 | 2 | ≥1 | ≥0 | ≥1 | HumanAIOS may control execution |
| EXTERNALLY_REPLAYED | ≥1 | 2 | ≥1 | 2 | ≥1 | external operator performs replay |
| THIRD_PARTY_REVIEWED | ≥1 | 2 | ≥1 | 2 | 2 | third party controls reviewer selection and publication |

Automatic disqualifiers: first-pass context leakage, evidence-bundle hash mismatch, review-contract mutation after a seat starts, hidden shared summary, or undeclared operator substitution.

---

## 6. Review state machine

```
SUBMITTED
  -> INTAKE_VALIDATED
  -> EVIDENCE_FROZEN
  -> FIRST_PASS_RUNNING
  -> FIRST_PASS_FROZEN
  -> CROSS_EXAM_RUNNING
  -> VERDICTS_FROZEN
  -> INDEPENDENCE_CHECKED
  -> GATE_COMPUTED
  -> PACKAGE_EXPORTED
  -> REPLAYED_EXTERNALLY (optional but required for external-reproduction claim)
```

Failure states:

```
INVALID_SCOPE
MISSING_EVIDENCE
EVIDENCE_INTEGRITY_FAILURE
PROCESS_CONTAMINATED
INSUFFICIENT_INDEPENDENCE
REVIEWER_FAILURE
UNRESOLVED_CRITICAL_CHALLENGE
PORTABILITY_FAILURE
```

Every state transition emits one record to `runs/<run_id>/events.jsonl`. Each record contains `seq`, `event_type`, `artifact_refs`, `prev_event_hash`, and `event_hash`; `event_hash` is computed over canonical JSON with the hash field omitted. Sequence starts at 1 and the first `prev_event_hash` is null. A missing sequence, broken predecessor link, or recomputation mismatch invalidates process integrity.

---

## 7. Seat verdict vocabulary

Voting seats emit exactly one primary verdict:

- `SUPPORTED`
- `SUPPORTED_WITH_REQUIRED_CORRECTION`
- `NOT_SUPPORTED`
- `INSUFFICIENT_EVIDENCE`
- `PROCESS_INVALID`

Each verdict must include:

```
claim
evidence_refs[]
reasoning_summary
counterevidence[]
uncertainties[]
critical_challenges[]
falsifiers[]
required_corrections[]
verdict
confidence_basis
report_hash
signer_identity
signature_algorithm
key_id_or_identity_ref
trust_root_ref
signed_at
signature_or_attestation_ref
```

"Confidence" may describe evidence quality or uncertainty but is never allowed to override the gate rule.

---

## 8. Gate rule

Initial conservative rule:

```
ADVANCE =
  all voting seats == SUPPORTED
  AND evidence_integrity == VALID
  AND process_integrity == VALID
  AND independence_policy == SATISFIED
  AND unresolved_critical_challenges == 0
```

All other outcomes resolve to:

```
HOLD_REVISE_RETEST
```

The gate code must be short, deterministic, testable, and model-free. Signed seat verdicts authenticate the producer; a bare content hash is integrity evidence but is not identity evidence. The portable contract therefore separates content digest, signer identity, signature/attestation mechanism, and trust-root reference.

A future governance decision may define additional gate profiles, but a profile must be selected before the evidence is reviewed.

---

## 9. The HumanAIOS-removal test

A PRP passes **HumanAIOS Removal Test v0.1** only if an evaluator can execute the following from a clean environment:

### Test A — package verification
- verify all hashes;
- verify no missing evidence objects;
- validate schemas;
- validate append-only event chain.

### Test B — deterministic replay
- rerun all non-LLM computations;
- reproduce statistical outputs within declared numerical tolerances;
- reproduce the gate result from frozen seat verdicts.

### Test C — reviewer replacement
- discard HumanAIOS-generated seat reports;
- run the public reviewer contracts using alternate reviewer substrates;
- produce independent seat reports.

### Test D — adjudication comparison
Compare original and replacement runs using a claim-resolution matrix:

- CONVERGED
- CONFLICT
- UNRESOLVED

No automatic preference is given to the HumanAIOS run.

### Test E — dependency severance
Block:
- humanaios.ai
- HumanAIOS APIs
- private HumanAIOS repositories
- unpublished HumanAIOS datasets
- HumanAIOS operator assistance

If replay requires any blocked dependency, mark `PORTABILITY_FAILURE`.

### Test F — adversarial package audit
Attempt:
- evidence deletion;
- hash substitution;
- stale-version substitution;
- reviewer-context leakage;
- shared-summary contamination;
- gate-rule alteration after verdict;
- hidden exception injection;
- model identity spoofing.

The package passes only if each alteration is detected or rendered non-authoritative.

---

## 10. Externality classification

The CRB MUST separate four claims:

### Class 0 — self-review
HumanAIOS runtime + HumanAIOS-controlled reviewers + HumanAIOS evidence path.

Permitted label: `SELF_REVIEW`.

### Class 1 — internal machine-independent review
Reviewer substrates are separated and blind, but execution remains under HumanAIOS control.

Permitted label: `INTERNAL_MACHINE_INDEPENDENT`.

### Class 2 — externally replayed
An independently controlled operator reproduces the package using the public contract.

Permitted label: `EXTERNALLY_REPLAYED`.

### Class 3 — third-party reviewed
An independent third party controls reviewer selection, execution, and publication of its verdict.

Permitted label: `THIRD_PARTY_REVIEWED`.

Only Class 2 or 3 supports claims about external reproduction. Class 1 does not become external merely because multiple AI vendors were used.

---

## 11. Human authority boundary

Automation is appropriate for evidence inventory, deterministic recomputation, red-team generation, reviewer execution, cross-examination, divergence detection, provenance, package assembly, and gate computation.

Human authority remains required when the decision itself legally or institutionally belongs to a person or organization, including:

- accepting legal/regulatory responsibility;
- informed consent or identity/relationship attestation;
- final production deployment authorization where policy assigns that duty to a human;
- formal research publication responsibility;
- conflict-of-interest attestations about facts not mechanically observable;
- exceptions that alter the pre-registered decision rule.

The CRB may identify these obligations and package evidence for them. It must not fabricate the authority.

---

## 12. Product boundary

The current public HumanAIOS research layer describes ACAT as behavioral observation/calibration research and explicitly does not position it as a deployment recommendation or certification.

The CRB therefore MUST launch initially as:

**evidence-bearing review infrastructure**

not:

**AI safety certification**

ACAT is one instrument available to the CRB. It is not the board itself.

The CRB may ingest:
- ACAT outputs;
- code/test evidence;
- behavioral traces;
- model/agent telemetry;
- security findings;
- policy requirements;
- human review records;
- external benchmarks;
- incident data.

This turns ACAT from the whole product claim into one calibrated signal in a larger evidence graph.

---

## 13. Minimum viable implementation

### CRB-0 — Portable package compiler
Input: claim + evidence directory + method manifest.
Output: validated PRP with hashes, inventory, replay instructions, and deterministic gate rule.

### CRB-1 — Three blind reviewer seats
Use three separately configured reviewer substrates. Freeze outputs before disclosure.

### CRB-2 — Cross-examination
Each seat receives the other frozen reports and emits challenges without rewriting its first pass.

### CRB-3 — Mechanical gate
Pure function over frozen verdicts and integrity flags.

### CRB-4 — Removal harness
A CI job creates a clean container, denies HumanAIOS network dependencies, and attempts package replay.

### CRB-5 — Alternate-substrate replay
Run at least one complete PRP with replacement reviewers.

### CRB-6 — Independent operator pilot
Give the PRP to a party who did not design the reviewed claim. Record every missing instruction as a portability defect.

---

## 14. Acceptance tests

The institution is not considered compiled until all tests pass:

1. **Fresh-machine test:** clean machine can validate and replay package from README only.
2. **No-HumanAIOS-network test:** replay succeeds with HumanAIOS endpoints blocked.
3. **No-original-reviewer test:** alternate reviewers can replace all voting seats.
4. **Gate reproducibility test:** independent implementation derives identical gate result from identical frozen inputs.
5. **Dissent retention test:** minority report survives packaging/export unchanged.
6. **Tamper test:** evidence or rule mutation changes hashes and invalidates authority.
7. **Context-leak test:** first-pass reviewers cannot read peer findings.
8. **Dependency disclosure test:** every external dependency appears in dependency_report.json.
9. **Version-pinning test:** every protocol, threshold, schema, and prompt is content-addressed.
10. **Counterexample test:** package can return NOT_SUPPORTED / INSUFFICIENT_EVIDENCE / PROCESS_INVALID without operator override.

A 100% favorable verdict rate is not a success metric. It is an audit trigger.

---

## 15. Falsifiers

The CRB thesis is weakened or falsified if any of the following persists after reasonable engineering effort:

- independent replay requires undocumented HumanAIOS knowledge;
- deterministic computations cannot be reproduced;
- alternate reviewers cannot understand the public review contract;
- reviewer substitution causes uncontrolled verdict instability with no discriminating evidence;
- ostensibly blind reviewers share context or derived summaries;
- the Gate Controller requires model interpretation;
- HumanAIOS can alter a frozen verdict without creating a new signed run;
- external operators systematically cannot distinguish evidence from HumanAIOS interpretation;
- package provenance cannot detect tampering;
- HumanAIOS markets Class 0/1 review as third-party validation.

---

## 16. Mapping to existing HumanAIOS primitives

Reuse rather than rebuild:

- **REGISTERED.md / falsifier doctrine** -> claim and hypothesis provenance
- **Z1/Z2/Z3 authority model** -> proposal / ratification / execution boundary
- **recursive review loop** -> disagreement-as-signal and evidence-grounded learning
- **receipt reconciliation** -> claim-vs-tree verification
- **evidence graph / telemetry work** -> provenance and behavioral traces
- **P34-X evidence tooling** -> grounded temporal/provenance checks
- **molt discipline** -> correction after falsifier activation
- **no-op and CI guards** -> deterministic institutional controls

The CRB should extract these as portable interfaces rather than require adopters to import HumanAIOS's internal metaphors or governance vocabulary.

---

## 17. Initial pilot

Use HumanAIOS itself as the first hostile specimen.

Pilot claim:

> "A HumanAIOS-generated review package contains enough evidence and procedure for an independent evaluator to reproduce or contest its verdict without HumanAIOS participation."

Procedure:

1. choose one narrow, already documented ACAT claim;
2. compile a PRP;
3. run the internal CRB;
4. freeze/export;
5. deny all HumanAIOS dependencies;
6. replace all voting reviewers;
7. replay;
8. publish convergence/conflict/unresolved matrix;
9. log every missing dependency as a defect;
10. repeat until the package is self-sufficient or the claim is withdrawn.

The desired outcome is not agreement. The desired outcome is **portable adjudicability**.

---

## 18. Governance disposition

This document proposes a new institutional layer and therefore MUST NOT silently modify existing Z2 authority.

Recommended disposition:

- Z1: propose this specification and implementation work;
- Z2: ratify, edit, or reject the CRB institutional contract;
- Z3: only after ratification, land any authority-changing enforcement;
- external replay: used to establish Class 2 evidence;
- independent third-party control: required before Class 3 labeling.

Until ratified and empirically replayed, HumanAIOS should describe the CRB as a research prototype / institutional compilation experiment.

---

## 19. Destination

**Destination:** a vendor-neutral, reproducible review institution whose evidentiary product remains inspectable and rerunnable when HumanAIOS is absent.

The strongest version of HumanAIOS is therefore not a reviewer that must be trusted.

It is a system that produces review objects that remain useful after trust in HumanAIOS has been removed.

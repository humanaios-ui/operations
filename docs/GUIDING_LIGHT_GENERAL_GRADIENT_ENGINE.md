# Guiding Light — General Evidence-to-Target Gradient Engine v0.2

**Status:** implementation candidate  
**Canonical core:** `services/guiding_light.py`  
**Career adapter:** `services/career_gradient.py`  
**Evidence-state schema:** `data/GUIDING_LIGHT_EVIDENCE_STATE.schema.json`  
**Gradient schema:** `data/GUIDING_LIGHT_GRADIENT.schema.json`  
**Witness invariant:** `WITNESS_IS_NOT_THE_AUTHORITY`

## 1. Generalization

Guiding Light is not fundamentally a job matcher.

It is a domain-neutral engine for comparing an evidence-bearing **current state** with externally defined **target states**, preserving what is known, what is inferred, what is missing, and what action class could produce the missing evidence.

```text
EVIDENCE STATE
      ↓
TARGET SPECIFICATIONS
      ↓
REQUIREMENT MAPPING
      ↓
CURRENT ACTIONABILITY + OPTION VALUE
      ↓
REACHABLE / BRIDGE / FRONTIER / HOLD
      ↓
DELTA
      ↓
BOUNDED INTERVENTION
      ↓
NEW EVIDENCE
      ↓
RECOMPUTE
      ↺
```

A career pathway is one adapter over this core.

## 2. Subject types

The evidence state may describe a:

- person;
- organization;
- project;
- system;
- program;
- community;
- vendor;
- custom subject.

The repository must not assume that a résumé is the canonical source. A résumé is one possible rendering of a person's evidence state.

## 3. Evidence State Profile

The Evidence State Profile separates claims from presentation.

Each claim records:

- a stable claim ID;
- label;
- kind;
- verification state;
- temporal state;
- provenance;
- evidence references;
- optional confidence;
- domain metadata.

### Verification states

```text
VERIFIED
SUPPORTED
SELF_ATTESTED
UNKNOWN
CONTRADICTED
```

### Temporal states

```text
PAST
CURRENT
IN_PROGRESS
PLANNED
UNKNOWN
```

A downstream adapter may reinterpret a claim for a specific target, but it must not silently upgrade the underlying evidence state.

## 4. Mapped target contract

The core does not perform semantic inference from raw external records.

A target enters the deterministic engine only after its requirements have been mapped into:

```text
DOCUMENTED
USER_ATTESTED
TRANSFERABLE
PARTIAL
PLANNED
UNKNOWN
NOT_HELD
BLOCKED
```

Each target also carries explicit, source- or analyst-supplied `value_axes`. The engine does not invent those axes.

Examples:

| Domain | Example value axes |
|---|---|
| Career | compensation, scope, authority, technical complexity, strategic exposure, evidence gain, portability |
| Funding | resource magnitude, mission fit, evidence gain, leverage |
| Research | scientific leverage, replication value, collaboration value, evidence gain |
| Procurement | contract value, past-performance gain, strategic access, portability |
| Project | maturity gain, operational scope, evidence gain, external reliance |
| Organization | capability expansion, revenue potential, resilience, strategic option value |
| Learning | opportunity unlock, evidence gain, time efficiency, portability |

Absence of a value axis is preferable to a fabricated number.

## 5. Universal pathway states

The domain-neutral core emits:

- **REACHABLE** — high mapped coverage, no mandatory unknown or blocker, lower gradient.
- **BRIDGE** — sufficiently actionable and materially expands the option set.
- **FRONTIER** — higher-value target with substantial unresolved delta, or a mandatory unknown that requires investigation.
- **HOLD** — hard blocker, unmapped target, or low-actionability/low-gradient state.

Career preserves its original public vocabulary by rendering `REACHABLE` as **HARVEST**.

These states are navigation states, not judgments of human worth, institutional merit, legal eligibility, or funding quality.

## 6. Gap → intervention map

A gap must be diagnosed before an intervention is recommended.

| Gap type | Intervention |
|---|---|
| unknown | INTERROGATE |
| knowledge | LEARN |
| evidence | BUILD_EVIDENCE |
| credential | CREDENTIAL_DECISION |
| experience | EXPERIENCE_REQUIRED |
| authority | VERIFY_AUTHORITY |
| partnership | FIND_PARTNER |
| resource | ACQUIRE_RESOURCE |
| capability | BUILD_CAPABILITY |
| blocker | RESOLVE_BLOCKER |

The engine ranks interventions only when they are tied to named target requirements.

## 7. Operations repository domain map

### Career

**Existing surface:** `services/career_gradient.py`, Intent-OS Guiding Light reflex.

```text
person evidence
→ role specification
→ requirement mapping
→ career gradient
→ learning/evidence delta
→ human application decision
```

### Resource discovery

**Existing surface:** `humanaios-funding-pipeline/resource-miner/`.

Resource Miner remains the permissive discovery layer.

```text
external resource
→ Resource Miner provenance + need alignment
→ Guiding Light normalization
→ mandatory eligibility UNKNOWN
→ VERIFY_AUTHORITY
```

A Resource Miner relevance score never becomes applicant eligibility.

### Entitlements

**Existing surface:** `humanaios-funding-pipeline/entitlement-navigator/`.

The Entitlement Navigator remains the deterministic rule-evaluation authority inside the repository.

Guiding Light may visualize an `EvaluationResult` as a pathway, but it must preserve:

- `RULE_MATCH`;
- `CONDITIONAL_MATCH`;
- `INVESTIGATE`;
- `INELIGIBLE`;
- `CLOSED_HISTORICAL`;
- `GENERAL_OPPORTUNITY`;
- the navigator's legal note;
- required evidence;
- last-verified state.

Guiding Light does not replace or overwrite those statuses.

### Funding

**Existing surfaces:** `humanaios-funding-pipeline/` and `src/humanaios_operations/scoring.py`.

The legacy funding dataset and heuristic scorer are discovery/fit surfaces. Their tags and composite scores do not establish current authoritative eligibility.

Guiding Light normalizes a legacy funding source as an unresolved target until current applicant eligibility is verified.

### Project maturity

A project can be the subject.

```text
prototype
→ validated pilot
→ limited deployment
→ production-ready
```

Target requirements can include testing, security review, observability, rollback, external validation, customer acceptance, or other project-specific evidence.

The committed example in `data/GUIDING_LIGHT_GRADIENT.example.json` demonstrates this non-career use.

### Future adapters

The same contract can support:

- research opportunities;
- fellowships;
- certifications and licensure;
- procurement/RFPs;
- vendor qualification;
- internal promotion/succession;
- organizational capability development;
- partnerships;
- education pathways.

No future adapter is considered implemented until it has a source contract, mapping rule, tests, and an authority boundary.

## 8. Repository topology

```text
                        ┌──────────────────────┐
                        │  EXTERNAL SOURCES    │
                        └──────────┬───────────┘
                                   ↓
                    ┌──────────────────────────┐
                    │ DISCOVERY / INGESTION    │
                    │ Resource Miner / feeds   │
                    └─────────────┬────────────┘
                                  ↓
             ┌────────────────────────────────────┐
             │ DOMAIN VERIFICATION / MAPPING      │
             │ career mapper                      │
             │ Entitlement Navigator              │
             │ funding authority verification     │
             │ project evidence evaluator         │
             └──────────────────┬─────────────────┘
                                ↓
                     ┌───────────────────────┐
                     │ GUIDING LIGHT CORE    │
                     │ actionability         │
                     │ option gradient       │
                     │ delta / intervention  │
                     └───────────┬───────────┘
                                 ↓
              ┌──────────────────────────────────┐
              │ HUMAN / AUTHORITY DECISION       │
              └─────────────────┬────────────────┘
                                ↓
                       action / evidence
                                ↓
                      outcome telemetry
                                ↓
                       evidence update
                                ↺

                  WITNESS observes the chain.
                  WITNESS_IS_NOT_THE_AUTHORITY
```

## 9. Account Hub / PR #472

The v0.2 core emits normalized events through the existing `Event` contract:

- `target_discovered`;
- `target_mapped`;
- `gradient_delta`;
- `intervention_signal`;
- `state_update`;
- `target_outcome`.

The v0.1 career-specific event names remain available for compatibility.

## 10. Authority and safety boundaries

Guiding Light is a navigation layer.

It may:

- expose evidence;
- classify mapped target state;
- identify gaps;
- rank evidence-producing interventions;
- preserve provenance;
- route to an authority or human decision.

It may not:

- invent evidence;
- convert discovery relevance into eligibility;
- convert a course into prior experience;
- convert a credential into experience;
- override an entitlement authority;
- authorize an application, purchase, filing, claim, contract, deployment, or career move;
- silently infer persistent user values from behavior.

## 11. Falsifiers

The v0.2 generalization fails if:

1. a hard mandatory blocker can be averaged into REACHABLE;
2. an unknown mandatory predicate can be rendered REACHABLE;
3. Resource Miner need alignment becomes eligibility;
4. a legacy funding tag becomes authoritative eligibility;
5. an Entitlement Navigator status is overwritten by the gradient classification;
6. a recommended intervention has no named requirement delta;
7. a domain adapter upgrades uncertain evidence without provenance;
8. Witness output grants consequential authority;
9. the same mapped snapshot produces different deterministic scores;
10. the career adapter no longer preserves the existing v0.1 public contract.

## 12. Private evidence boundary

The schemas are repository-safe contracts; real user evidence is not.

Personal, organizational, financial, identity, genealogy, credential, and private project evidence should remain in an explicitly private or git-ignored evidence store. Repository examples must be synthetic or sanitized.

The repository may commit:

- schemas;
- adapters;
- test fixtures;
- sanitized hashes/manifests;
- synthetic examples.

It must not require raw private evidence to operate the deterministic core.

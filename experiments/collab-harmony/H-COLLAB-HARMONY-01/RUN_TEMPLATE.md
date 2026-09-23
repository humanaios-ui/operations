# H-COLLAB-HARMONY-01 — Run Template

Use this template to execute one frozen run of the preregistered protocol.

## Run header

- **Run ID:**  
- **Date:**  
- **Bounded question:**  
- **Base commit / evidence snapshot:**  
- **Protocol / amendment reference governing this run:**  
- **Optional transport substrate reference and recorded limits (or `none`):**  
- **Regime code (enter exactly one of `A`, `B`, or `C`):**  
- **Participants:**  

Regime key:
- `A` — agreement optimization
- `B` — independent contribution without structured exchange
- `C` — coherence without forced convergence

`C` is the hypothesis-bearing run type for H-COLLAB-HARMONY-01. `A` and `B` are comparator-only runs and may inform comparisons, but they cannot by themselves receive a `supported` or `failed` verdict for the hypothesis.

## Frozen participant envelopes

### Participant 1

```yaml
participant:
  type: HUMAN | AI | TOOL | AUTHORITY
  id:

intent:
  goal:
  constraints: []
  success_criteria: []
  unresolved_intent: []

interpretation:
  what_i_think_the_problem_is:
  assumptions: []
  uncertainty: []
  confidence: LOW | MEDIUM | HIGH

contribution:
  observations: []
  evidence_refs: []
  inferences: []
  recommendations: []
  disagreements: []
  proposed_next_step:

boundaries:
  may_refuse: true
  authority_effect: NONE | ADVISORY | AUTHORIZED
```

### Participant 2

```yaml
participant:
  type: HUMAN | AI | TOOL | AUTHORITY
  id:

intent:
  goal:
  constraints: []
  success_criteria: []
  unresolved_intent: []

interpretation:
  what_i_think_the_problem_is:
  assumptions: []
  uncertainty: []
  confidence: LOW | MEDIUM | HIGH

contribution:
  observations: []
  evidence_refs: []
  inferences: []
  recommendations: []
  disagreements: []
  proposed_next_step:

boundaries:
  may_refuse: true
  authority_effect: NONE | ADVISORY | AUTHORIZED
```

### Participant 3

```yaml
participant:
  type: HUMAN | AI | TOOL | AUTHORITY
  id:

intent:
  goal:
  constraints: []
  success_criteria: []
  unresolved_intent: []

interpretation:
  what_i_think_the_problem_is:
  assumptions: []
  uncertainty: []
  confidence: LOW | MEDIUM | HIGH

contribution:
  observations: []
  evidence_refs: []
  inferences: []
  recommendations: []
  disagreements: []
  proposed_next_step:

boundaries:
  may_refuse: true
  authority_effect: NONE | ADVISORY | AUTHORIZED
```

## Shared exchange log

- **Exchange opened at:**  
- **Cross-visibility allowed only after all envelopes frozen:** `yes (required)`  
- **Transcript / artifact reference:**  

## Dissent log

| ID | Participant | Disagreement | Evidence / basis | Resolved? |
|:---|:------------|:-------------|:-----------------|:----------|
| D1 |             |              |                  |           |

## Human comprehension packet

### Common ground

- 

### Unresolved disagreements

- 

### Evidence added during exchange

- 

### Remaining uncertainty

- 

### Authority state

- 

## Metric setup

The two primary metric definitions below are fixed by preregistration and must not be edited per run. Freeze any additional scoring rule needed to interpret secondary metrics before the run starts. If a secondary metric is out of scope for the run, mark it `not used` instead of leaving it undefined.

| Metric | Operational definition / scoring rule | Frozen before run? |
|:-------|:--------------------------------------|:-------------------|
| material_dissent_retained | Fixed primary metric: count materially distinct disagreements surfaced during the run and count how many remain visible in the final human comprehension packet; score as retained / surfaced. If surfaced = 0, record `not applicable: no surfaced disagreements`. | fixed |
| unsupported_claim_rate | Fixed primary metric: count consequential claims in the final packet and count how many lack a cited observation, evidence reference, or explicitly labeled inference path; score as unsupported / consequential. If consequential = 0, record `not applicable: no consequential claims`. | fixed |
| novel_evidence_found | not used; replace with a frozen counting rule before the run if selected | not used |
| correction_rate | not used; replace with a frozen counting rule before the run if selected | not used |
| authority_misattribution_events | not used; replace with a frozen event rule before the run if selected | not used |
| human_comprehension | not used; replace with a frozen rubric before the run if selected | not used |
| human_intervention_minutes | not used; replace with a frozen timing rule before the run if selected | not used |
| identity_resolution_cost | not used; replace with a frozen identity-resolution rule before the run if selected | not used |

## Metric scoring

| Metric | Value | Notes |
|:-------|:------|:------|
| material_dissent_retained | | |
| unsupported_claim_rate | | |
| novel_evidence_found | not used | replace only if the metric was operationalized above before the run |
| correction_rate | not used | replace only if the metric was operationalized above before the run |
| authority_misattribution_events | not used | replace only if the metric was operationalized above before the run |
| human_comprehension | not used | replace only if the metric was operationalized above before the run |
| human_intervention_minutes | not used | replace only if the metric was operationalized above before the run |
| identity_resolution_cost | not used | replace only if the metric was operationalized above before the run |

## Comparator references

Complete this section only for comparator runs that already exist. If no paired run exists yet, record `not available`.

- **Relevant comparator run(s):**  

## Comparative interpretation

Allowed comparator regimes are derived from the chosen run regime:
- if this run is `A`, comparators may only be `B` and `C`
- if this run is `B`, comparators may only be `A` and `C`
- if this run is `C`, comparators may only be `A` and `B`

| Comparator regime | Run ID / not available | material_dissent_retained comparison | unsupported_claim_rate comparison | Preregistered expectation met? |
|:------------------|:-----------------------|:------------------------------------|:----------------------------------|:-------------------------------|
| enter one allowed comparator regime code here | not available | not available | not available | not available |
| enter the other allowed comparator regime code here | not available | not available | not available | not available |

## Invalid-run / falsifier check

### Invalid-run conditions

Check a box only if the violation occurred.

- [ ] I1 — a participant saw peer output before its own envelope was frozen
- [ ] I2 — the bounded question changed after participant submission
- [ ] I3 — dissent was omitted from the final packet without explicit reason
- [ ] I4 — authority was inferred from agreement, confidence, or repetition
- [ ] I5 — identity resolution increased without documented necessity
- [ ] I6 — a refusal was overridden or penalized into continued participation

### Falsifiers

Check a box only if the falsifier was observed.

- [ ] F1 — disagreement was hidden to improve a harmony or success score
- [ ] F2 — a participant was pressured to agree, continue, or soften a refusal
- [ ] F3 — minority observations were dropped solely because others converged
- [ ] F4 — human comprehension collapsed into approval of a preselected answer
- [ ] F5 — inferred preference was treated as authorization
- [ ] F6 — cross-agent agreement was treated as independent verification
- [ ] F7 — identity resolution rose without declared necessity
- [ ] F8 — distinctive participant behavior was normalized away for coherence
- [ ] F9 — a false unanimous conclusion scored above a true contested one
- [ ] F10 — the final packet could not reconstruct who observed, inferred, challenged, or authorized consequential claims

- **Verification gaps / context for checked items:**  
- **Residual ambiguity or unverifiable claims that must be preserved in the run record:**  

## Verdict

- **Hypothesis verdict applicable?** `yes only for regime C; regime A/B runs are comparator-only`
- **Supported / failed / invalid:**  
- **Why:**  

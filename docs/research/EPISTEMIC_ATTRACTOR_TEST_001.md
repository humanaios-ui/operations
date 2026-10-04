# Epistemic Attractor Test 001 — Dependency, Omission, and Compression

Status: PROVISIONAL CONTROLLED TEST  
Date: 2026-09-30  
Tracker: #595

## Question

Can an internal graph node emit a bounded external-search specification, capture external candidate concepts, assess them before absorption, and use the result to expose omissions or harmful compression in the internal graph?

## Controlled seed

Seed node:

```text
DependencyFlag
dependency = pyshacl==0.40.1
state = UNSATISFIED in current session environment
required_for = canonical SHACL validation
```

The node was selected because it already contains:
- an unresolved execution state;
- a bounded dependency;
- a clear falsifier (successful canonical validation);
- an external information need.

## Attractor profile A-001

Target: dependency flag for canonical SHACL validation.

Search intents:
1. SATISFY_DEPENDENCY — establish package availability and runtime requirements.
2. SEEK_PRIOR_ART — identify canonical installation/execution instructions.
3. SEEK_CONTRADICTION — look for version incompatibility or a reason the selected version cannot satisfy the need.
4. PROBE_COMPRESSION_LOSS — determine whether the single phrase “dependency-capable environment” hides distinct dependencies.

Queries:
- pySHACL 0.40.1 package availability and Python version requirements;
- pySHACL installation and command-line execution;
- SHACL validation-report provenance/version-watch developments.

## External candidates caught

### EC-001 — PyPI pyshacl 0.40.1
Source: https://pypi.org/project/pyshacl/0.40.1/

Candidate facts:
- release 0.40.1 exists;
- release date 2026-07-28;
- Python requirement is >=3.9;
- platform-independent Python wheel is published.

Assessment: ABSORB selected dependency facts; LINK source.

Impact:
The original dependency was over-compressed. “Can run PySHACL” decomposes into at least:
1. compatible Python runtime;
2. package availability;
3. package installation/retrieval access;
4. validator execution access;
5. graph/shapes inputs.

EC-001 resolves package existence/version uncertainty. It does NOT establish that the current execution environment can install or run the package.

### EC-002 — RDFLib/pySHACL installation documentation
Source: https://github.com/RDFLib/pySHACL

Candidate facts:
- documented installation path is pip;
- virtualenv installation is documented;
- command-line validation is supported.

Assessment: LINK + ABSORB resolution procedure.

Impact:
Improves `resolutionAction` on the dependency flag, but does not itself satisfy the dependency.

### EC-003 — W3C SHACL 1.2 Core Working Draft
Source: https://www.w3.org/TR/2026/WD-shacl12-core-20260917/

Candidate facts:
- validation reports can identify the data graph, shapes graph, and processor configuration used;
- the specification remains a Working Draft.

Assessment: WATCH + LINK.

Impact:
Potential future improvement to HumanAIOS validation receipts: capture validator context directly in graph provenance. Do not replace the SHACL 1.0 normative baseline yet.

## Omission analysis

The test surfaced four distinct meanings of “missing” that MUST NOT be collapsed:

1. STRUCTURAL_OMISSION
   - something is required by an explicit shape/contract and absent;
   - example: SHACL `minCount` failure.

2. EPISTEMIC_UNKNOWN
   - the graph does not currently know whether a fact is true;
   - absence is not evidence of falsehood.

3. COVERAGE_GAP
   - a domain/research objective expects broader coverage than currently represented;
   - may create an external discovery attractor.

4. COMPRESSION_INDUCED_OMISSION
   - a summary/abstraction collapsed detail needed for execution, interpretation, challenge, or provenance.

The W3C OWL open-world assumption is an important boundary: absence of a fact in an ontology may mean “unknown,” not “false.” Omission signals therefore require an expectation source such as a shape, declared research scope, dependency contract, human task, prior evidence, or compression receipt.

## Compression analysis

Compression is not inherently a defect. Graph reduction/summarization exists specifically to simplify large graphs while preserving selected essential properties.

HumanAIOS therefore needs a `CompressionResidue`, not a blanket “compression bad” rule.

A compression operation should declare:
- compressed_from;
- preservation_goal;
- omitted_aspects;
- compression_loss_risk;
- expansion/provenance path.

This session gives a concrete example:

```text
compressed phrase:
  "dependency-capable environment"

preservation goal:
  communicate why canonical validation did not run

omitted aspects:
  Python compatibility
  package existence/version
  install/network capability
  execution capability
  exact blocked stage

observed result:
  phrase did not fully land

system response:
  expand compressed dependency into explicit flags
```

## Absorption gate

External candidates MUST remain quarantined until assessed.

Disposition vocabulary:
- ABSORB — normalize selected facts into the internal graph;
- LINK — preserve external relationship without internalizing the claim as canonical;
- CHALLENGE — candidate weakens or contradicts an internal claim;
- WATCH — relevant but not mature/current enough for absorption;
- REJECT — insufficient relevance, provenance, or fit.

A candidate may receive more than one operational effect (e.g. LINK the source while ABSORBING only bounded facts).

## Anti-confirmation requirement

Every attractor created from a hypothesis SHOULD emit multiple retrieval intents where practical:
- support;
- contradiction;
- alternative explanation;
- prior art;
- “this node may be unnecessary/redundant.”

The objective is not to pull the internet toward the graph’s current belief. It is to find information capable of changing the graph state.

## Test result

PASS as a design test, not yet as a performance claim.

Observed gains:
1. external retrieval narrowed a vague dependency;
2. search exposed hidden subdependencies created by compression;
3. omission taxonomy prevented “not present” from being treated as “false”;
4. candidate quarantine prevented direct external-to-canonical mutation;
5. version-watch candidate produced a bounded future improvement without premature migration.

Unresolved:
- whether attractor-driven retrieval improves precision/recall versus ordinary research;
- how to rank attractors competing for limited search budget;
- how to measure harmful compression automatically;
- how to distinguish a true domain omission from an open-world unknown at scale;
- how much human review is required before ABSORB.

## Next falsification test

Compare two research runs over the same unresolved graph state:
A. ordinary free-form search;
B. attractor-generated multi-intent search.

Measure:
- relevant candidates found;
- contradictory candidates found;
- new omissions exposed;
- duplicate/noise rate;
- human review effort;
- graph mutations accepted;
- later withdrawals caused by bad absorption.

Attractor architecture should not be promoted if it increases confirmation bias or review load without improving evidence coverage.

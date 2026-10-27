# HumanAIOS Attractor Observatory E0 — structural convergence and external conversion

**Status:** Z1 draft / research observer; read-only, local, offline, non-authorizing.
**Authority:** `authority_effect=NONE`; never ratifies, merges, deploys, contacts a beneficiary, submits an application, or updates a shared resource catalog.
**Question:** Where do decisions, agents and processes return? Which observed processes coincide with acquired resources, completed human objectives, or documented recovery benefit?

## Why this is two instruments, not one score

The Wikipedia first-link phenomenon suggests a graph experiment, not a definition of success.

1. **Structural internal convergence**: enumerate strongly connected components (SCCs), reachability basins, terminal components and a deterministic *first stored edge* walk in `system_graph.json`. These are possible paths in an authored graph, not runtime behavior.
2. **Observed internal returns**: measure repeated visits to a graph node within explicit, evidence-referenced trails from agents, decisions, or processes. Without trail records, the state is `NOT_MEASURED`, never zero.
3. **External conversion**: count explicitly documented outcome *assertions* by associated process, keeping resource discovery, inventory, acquisition, objective completion and recovery delivery separate. This first implementation does NOT independently authenticate receipts or establish causal attribution.

These layers may differ, and disagreement is valuable. A strongly connected governance loop may be necessary for safety while having no direct outcome. A single human action may yield a benefit without a long internal loop.

## Existing work reused — no new control plane

| Source | Role | Limits |
| --- | --- | --- |
| `system_graph.json` | Existing directed governance/process edges | Generated 2026-09-13; coverage omits INTENT-OS, Resource Miner and beneficiary outcomes |
| PR #835 / `architecture/codebase_atlas.py` | Evidence-linked code relationships | Observational only; structural reach is not agent activity |
| PR #841 / `temporal_graph_timeline.py` | Commit-history node change dates | Commit dates are not ratification dates |
| Issue #588 / `humanaios-resource-system` | Resource status and activity model | A lead, click, prepared artifact or inventoried Azure credit is not a new resource acquisition |
| Issue #1002 | Source feedback and before/after replay | A user report does not independently establish closure |
| Issue #821 | Minimal-vs-full external-value falsifier | More architecture is not the target outcome |

PR #630 is closed **unmerged** and cannot be presumed to be a live graph source.
No changes to existing governance files, graph edges, agent runtime, resource ranking, or INTENT-OS.

## Run locally (stdlib only, Python 3.11)

From the `operations` checkout:

```sh
python3 -m unittest discover -s tests -p 'test_attractor_observatory_e0.py' -v
python3 tools/attractor_observatory_e0.py --graph system_graph.json > /tmp/attractor-e0.json
```

Only explicit local input paths are read. Without observation files, the output states `NOT_MEASURED`; no pretend conversions. Optional `--output /tmp/report.json` writes only a report, not repository state.

### Observed trail record — one JSON object per line, **synthetic example**

```json
{"trail_id":"T1","actor_kind":"agent","actor_id":"agent-1","step":0,"node_id":"Q","observed_at":"2026-10-26T00:00:00Z","source_ref":"fixture:session","source_revision":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
```

A trail has ordered `step` values starting at zero. Every consecutive node transition must be an existing directed edge. A node revisited later in the same trail contributes one *extra visit*. Identity, timestamps and SHA are recorder-supplied; the program does not verify Git provenance or the actor. `actor_kind` is `agent`, `decision`, or `process`. Never include names, secrets, email, resume text or private objectives.

### Outcome observation — one JSON object per line, **synthetic example**

```json
{"event_id":"E1","objective_id":"O1","event_type":"RESOURCE_ACQUIRED","process_id":"RL","observed_at":"2026-10-26T00:00:00Z","source_ref":"fixture:receipt","source_revision":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","evidence_digest":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","observer_id":"agent-1","resource_id":"RES-1","reviewer_id":"human-reviewer-1","review_verdict":"SUPPORTS"}
```

Allowed event types:

- `OBJECTIVE_DEFINED`, `CANDIDATE_IDENTIFIED`, `SOURCE_REVIEWED`, `HUMAN_AUTHORIZED`
- `RESOURCE_INVENTORIED`, `RESOURCE_ACQUIRED`
- `OBJECTIVE_COMPLETED`, `RECOVERY_BENEFIT_DELIVERED`

The three outcome stages are distinct. Neither `RESOURCE_INVENTORIED` nor `CANDIDATE_IDENTIFIED` counts as acquisition. A recovery-benefit outcome also needs `benefit_id` and `beneficiary_alias`, both pseudonymous IDs. No beneficiary identity or financial particulars belong in this ledger.

Events are joined to a process by explicit `process_id`, not guessed from nearby PRs, clicks, or graph proximity. Unmapped process IDs appear in `unmapped_process_ids`; never silently add edges to a canonical graph.

Run with explicit, locally controlled evidence packets:

```sh
python3 tools/attractor_observatory_e0.py \
  --graph system_graph.json \
  --trails /secure/local/consented-trails.jsonl \
  --outcomes /secure/local/redacted-outcomes.jsonl \
  --output /tmp/attractor-observatory.json
```

**Never commit real private trail or beneficiary records.** Do not run this on arbitrary unredacted account exports.

## States, trust and interpretation

| Output | Meaning | Not evidence for |
| --- | --- | --- |
| `STRUCTURAL_POSSIBILITY_ONLY` | Authored nodes/edges and deterministic walks | Runtime frequency or agent intent |
| `NOT_MEASURED` | Input was not provided | Zero events, failure, absence of benefits |
| `EMPTY_OBSERVATION_WINDOW` | Explicit provided file had no records | No outcomes outside this source/window |
| `OBSERVED_RECORDS_NOT_AUTHENTICATED` | Recorder supplied a trail | Authenticated actor participation |
| `ASSERTIONS_ONLY_NOT_INDEPENDENTLY_AUTHENTICATED` | Outcome claims were supplied with evidence references | Acquired value, verified eligibility, causal impact, signed receipt |

A distinct `reviewer_id` and a positive `review_verdict` count only as **separately review-attested claims**. A digest detects byte changes if the source bytes are independently available; a SHA string does not verify the source or identity. No event is labeled independently verified by E0. Without out-of-band source authentication and a separate reviewer, a documented claim is not proven external benefit.

The graph's own `validation_status` is preserved as source data, including the existing cycle validation error. A cycle in a general graph is not automatically a defect: an SCC is an observed graph property.

## Initial structural baseline

On the 2026-09-13 graph version, prior read-only inspection showed 22 nodes, 53 edges, a 17-node largest SCC, and 21 starting nodes reaching cycles under the first stored-edge policy. **This is not a live October 26 operational measurement.** The program recomputes these values from the file passed to it; it does not hardcode them.

## Acceptance tests and falsifiers

- SCC with an exit is reported as nonterminal, even though a first-edge walk can loop.
- Missing observations become `NOT_MEASURED`, not zero.
- A real recorded revisit is counted, but fabricated/dangling edges and discontinuous trail steps are rejected.
- A reviewer cannot review their own outcome into a second-review count.
- Discovery, inventory, application preparation and human clicks do not count as conversion.
- Recovery benefit requires pseudonymous benefit/beneficiary receipt references, never raw identities.
- Unknown input fields (including private resume text and fabricated eligibility/authority fields) are rejected.
- Source hashes are reported as unverified; no authorization, code merge or resource catalog mutation.
- Same inputs produce identical reports.
- CI only uploads a temporary structural JSON artifact; it supplies **no** private trail/outcome input and claims no benefit.

## Measurable next stages (not implemented)

**E1 — authenticated intake:** read exact-head GitHub/Codebase Atlas/Temporal Graph receipts and independently verified agent trail packets. Preserve evidence source, revision, observer identity and review actor. Reconcile the dated snapshot against the live graph without rewriting original records.

**E2 — conversion verification:** with the Resource Manager, consented Witness and independent reviewer, verify a real acquisition or completed user objective and tie it to process actions. Add signed receipts and explicit causal caveats. Use a separate private beneficiary ledger to verify recovery benefit. No private identity or secrets in public artifacts.

**E3 — experiment:** rerun Issue #821's minimal-baseline comparison and Issue #1002's feedback replay, preregistering denominator, source window, elapsed human time and falsifiers. Track sustained externally verified outcomes rather than merely cycle size, PR count or issue closures.

**Decision rule:** Keep loops that provide measurable safety, reliability or external value. Simplify loops with no demonstrated marginal benefit. Never remove a necessary human authorization boundary because a ranking or graph score suggests it.

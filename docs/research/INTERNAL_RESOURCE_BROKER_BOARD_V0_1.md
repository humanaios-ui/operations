# Internal Repository Resource Brokerage × Oracle × Agent Quarantine — Z1 prototype

**Standing:** proposal/read-only research projection; NOT admitted, ratified, deployed, or an authority source. Parent concepts: Resource Miner #588/#755, On-Track #928, agent handoff #986/#987, synthetic containment #978, ACAT research in `lasting-light-ai` #58, Oracle+Actualizer #497/#508. Do not treat this document or a green test as permission to merge or execute.

## Question

Can Resource Miner discover our **own repository capabilities, requirements, evidence, blocked decisions, and research instruments**, then broker them against explicit internal needs before considering external purchases, new code, credentials, or compute?

**Yes, as a bounded candidate inventory**, not as a claim that a PR, issue, model, or advertised function is already usable. The existing `GITHUB_REPOSITORY` Mine previously prioritized externally valuable issue leads. This separate **internal resource projection** uses the existing ResourceMine/ResourceCandidate/`bind_opportunity` identifiers without modifying external eligibility, authorized execution, or persistence semantics. It consumes caller-supplied inspected GitHub snapshots only, does not query GitHub or touch persistent state.

## Reverse-engineered board/report method

1. **Observe:** Read GitHub, Coordinator, protected CI, assigned-agent comments via existing approved connectors. Keep exact repository, PR/issue IDs, head SHA and run IDs. Do not export private Gmail, device state, session transcripts, or credentials.
2. **Decompose:** Normalize to allowlisted item claims (`ISSUE`, `PR`), reported CI run heads, declared capability tags, bounded agent phase records, and operator-defined needs. Keep what is unknown and the observation denominator.
3. **Inspect contradictions:** Detect head mismatch, missing or reordered agent phases, same-account reviewer, replayed IDs, unrecognized sources and private data fields. Validate from primary source separately; no caller flag authenticates itself.
4. **Map attractors:** Create a declared-capability dependency attractor from a human- or issue-declared `need`. Match to internal resource candidates only when *exact capability codes* agree. The match is a review suggestion, not eligibility, ownership, readiness or proof of work.
5. **Oracle:** Re-express bounded state and uncertainties as contestable, labeled synthesis. An Oracle claim with `INFERRED` or `UNKNOWN` status never becomes a warrant for action. Actualizer plans are separate human decision requests.
6. **Recombine:** Produce one bounded JSON projection, a static HTML board and a human-readable Systems report from the same projected candidate/need/quarantine structures. Never add a second mutable issue board or authority ledger.
7. **Human decision:** Reference existing canonical issue, PR, Coordinator, or explicit human decision. No new route, auto-admission, comments, PR operations, agent contact or workflow dispatch.
8. **Outcome learning:** Track actual independently proven human-use, resource acquisition/revenue/recovery evidence in existing outcome systems. Current projection always says NOT ESTABLISHED; it may not promote its own claims.

### Authority and privacy separation

```
CANONICAL SOURCES (GitHub, receipts, human authority, protected CI)
                  |
         READ-ONLY INSPECTION (external to this tool)
                  |
     BOUNDED CALLER SNAPSHOT (untrusted until rechecked)
                  |
       internal_repository_broker.project()
            /               |             \
    ResourceCandidate   Agent observations  Declared attractors
            \               |             /
                 ORACLE (INFERRED)
                        |
           STATIC BOARD + SYSTEMS REPORT
                        |
             HUMAN REVIEW / RECHECK

 NEVER: BOARD → state ledger / Z2 / Z3 / git write / external action
```

A source URL, an unkeyed digest, a CI status copied by a caller, and a GitHub account are **not authenticated evidence of actor independence**. A real read-back must independently fetch run/check records, exact SHA, immutable witness receipts and attestations from a trusted harness outside this projector. Avoid circular validation by the same agent. Private records require a private controlled viewer; this static HTML is deliberately public-safe *format*, not an instruction to publish.

## Minimal typed inputs

```
{
  "schema": "humanaios.internal-repository-snapshot.v0.1",
  "as_of": "2026-10-23T18:00:00-05:00",
  "items": [{
    "repository": "humanaios-ui/operations", "kind": "PR", "number": 987,
    "title": "Assigned agent research", "state": "MERGED",
    "head_sha": "<40 lowercase hex characters>",
    "source_url": "https://github.com/humanaios-ui/operations/pull/987",
    "capabilities": ["agent_coordination"]
  }],
  "needs": [{
    "need_id": "N-986", "label": "Review assigned handoff behavior", "priority": "P1",
    "repository": "humanaios-ui/operations",
    "source_url": "https://github.com/humanaios-ui/operations/issues/986",
    "capabilities": ["agent_coordination"]
  }],
  "ci_observations": [], "agent_events": []
}
```

`ci_observations` may carry a PR `item_ref`, exact `head_sha`, GitHub `run_id`, `conclusion` and exact `source_url`. A head match proves only **internal consistency of input**, not truth of a run. All CI outputs carry `independently_authenticated: false`.

`agent_events` is deliberately **inert typed metadata only**: subject, session, phase, actor_login, agent_claim, comment_id/comment_url and bounded P1 forecast or P2 result. No raw body, external URL, arbitrary text or executable field crosses the projection. Existing `agent_coordination/reflex.py`/`acat_loop.py` are the first format/sequence readers; never trust their output alone as the identity or behavior attestation. Allow only explicitly assigned subjects. The projection checks basic phase ordering and self-review; it does not monitor passive visitors.

Strict allowlists, record-count caps, UTF-8 text bounds, three-repository scope and escaped offline HTML reduce accidental leaks. **They do not prove that human-entered public issue titles contain no confidential data.** Human privacy review is still required before publication. HTML has no JavaScript and a restrictive CSP; no controls write or dispatch.

## Run locally (without network or credentials)

From `humanaios-funding-pipeline/resource-miner`:

```
python3 -m unittest discover -s tests -p 'test_internal_repository_broker.py' -v
python3 -m resource_miner.internal_repository_broker --input /path/to/approved-public-snapshot.json --format report
python3 -m resource_miner.internal_repository_broker --input /path/to/approved-public-snapshot.json --format json > /tmp/internal-broker.json
python3 -m resource_miner.internal_repository_broker --input /path/to/approved-public-snapshot.json --format html > /tmp/internal-broker.html
```

The command **only reads one local approved snapshot and writes to stdout**. Redirection is a caller-initiated local file output, not network delivery, automatic persistence or publication. No `GITHUB_TOKEN` needed. The source connector/collector and independent evidence verifier remain future governed work.

## Acceptance tests and falsifiers

- Happy path: existing `ResourceCandidate` and stable Mine/Opportunity identifiers; declared need intersects declared capabilities; never turns match into execution.
- Negative: forged authorization, raw private body, Gmail URL, other repo, ID/URL mismatch, overlong batch, replayed agent comment, P2 self-review, missing/out-of-order phases, escaped HTML, head mismatch and forged CI links.
- Honest observation: all caller-supplied CI remains `NOT_ESTABLISHED`; agent identity and independent calibration not asserted; synthetic test fixtures never count as real agent performance.
- False negatives: no common declared capability results in `NO_MATCH_IN_BOUNDED_SNAPSHOT`, **not** proof that no internal resource exists.
- Independent source-readback of real records, review of cross-repository access, and effective host authorization gates are required before claiming operational qualification.
- Mission: without independently verified acquisition/beneficiary receipts, all ROI remains `NOT_MEASURED` and mission outcome `NOT_ESTABLISHED`.

## Cross-repository role split

- `operations`: owns the **read-only internal Resource Miner projection**, agent entry/exit refs, Coordinator and provenance. Existing Sources remain canonical; this output is a projection only.
- `humanaios`: candidate private Witness/workbench (#123/#124). Not imported or operated until exact-head reviewer findings and isolation controls are resolved.
- `lasting-light-ai`: proposes calibration/repeatability validity; the P1/P3 self-report ratio is not independent accuracy or competence evidence.

### HumanAIOS Daily Digest integration

The central digest's Systems section may summarize: observed inventory, unverified coverage, need→candidate matches, agent phase anomalies, sources needing independent check, Oracle unknowns, calendar suggestions and ROI `NOT_MEASURED`. The schedule is **not** changed here. The reader/automation must query original GitHub and calendars again; another task's output is not a trusted upstream feed. Keep private Gmail content exclusively in private digest/email. Link exact public GitHub records when safe; never paste a private source into the board.

### Next qualified step

Independent read-back of frozen GitHub source fixture by a distinct authorized reviewer; match exact PR heads and CI runs, demonstrate malformed agent record rejection, and compare human review minutes versus baseline. Admission of new active tools, actual browser hosting, continuous crawling, and agent runtime tests are intentionally out of scope.
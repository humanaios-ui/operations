# Internal Resource Broker: independent source challenge demonstration (Z1)

**Status:** reproducible frozen observation, not an agent field trial, production integration, admission, or behavioral validation.  
**Subject:** [Operations PR #987](https://github.com/humanaios-ui/operations/pull/987)  
**As observed:** October 23, 2026 (America/Chicago).  
**Base broker:** Draft PR #1001.  
**Authority:** `NONE` throughout.

## Research question

Can an independently inspected GitHub record enter Resource Miner as a candidate, preserve its exact source and head SHA, appear in an escaped static board, and accept reversible source-linked challenges/corrections without modifying the original record, broker snapshot, or underlying repository?

## Inspection protocol and exact sources

The inspector called the connected GitHub read API **separately** from the existing broker's caller-supplied `sample_snapshot.json`, requesting:

- `get_pr_info` for #987: merged; head `476d7aec1d937a93710779b2a5cc3efc68c6aada`; merge commit `17fe60d4cb574e9e4ec1bc64b900b107b74a00be`.
- `fetch_file` for `agent_coordination/reflex.py` at that exact PR head: Git **blob SHA-1** `c89cc380d2fc8f861a6a4c414538999d6e0123fe` (not a file SHA-256).
- `fetch_commit_workflow_runs` querying that head: 17 returned completed/success workflow runs. This connector result associates runs with a queried commit but does not establish each job's entire test coverage or an authenticated safety claim.
- `list_pull_request_review_threads`: 6 unresolved review threads, including a reported structured-field validation concern.

**Meaning of independent:** fetched separately from the builder's snapshot, not corroborated by another AI author's repetition. **Limitation:** these pinned records are captured in a local JSON fixture; the fixture itself is not a cryptographically signed GitHub provider attestation. For current-state decisions re-read live GitHub and check that the head is still current; historical pinned-head evidence is not a live branch-state assertion.

## Observed correction

The original broker snapshot used a human-friendly **display title**:

`Assigned agent entry/exit reflex (merged, review gaps remain)`

The actual GitHub PR title observed through GitHub is:

`[WORKBENCH] Bounded agent entry/exit reflex using existing issue/PR comments`

An earlier strict equality check rejected this specimen altogether. The qualification treats the snapshot display title as an unverified alias and keeps **both** strings. Its derived claim `SOURCE_TITLE_EXACT` is `CONTRADICTED`. No mutation or silent rewrite is permitted.

A second challenge rejects the invalid inference that **17 successful CI workflows imply complete security approval**. Review threads remain unresolved; the operational safety claim stays `NOT_ESTABLISHED`.

A third correction rejects the hypothetical claim that all inline review threads are resolved; `ALL_REVIEW_THREADS_RESOLVED` is `CONTRADICTED` by the inspected thread count.

Neither correction changes PR #987, the source snapshot, nor the original Resource Miner projection. A correction is an **append-only-derived overlay** whose record digest chain detects accidental local alteration but does not authenticate an actor.

## Reproduce from a full checkout

```bash
cd humanaios-funding-pipeline/resource-miner
python3 -m unittest discover -s tests -p 'test_independent_readback.py' -v
python3 experiments/reproduce_pr987.py --output /tmp/humanaios-pr987-readback
# inspect generated /tmp/humanaios-pr987-readback/{board.html,report.txt,qualification.json}
```

No `gh`, tokens, network requests, `.git` modification, issue comments, approval or task execution is performed by these commands. Output directory must be outside the working tree.

## Required negative controls

1. Changing pinned PR head while retaining readback fails.
2. Changing PR URL or CI run URL while retaining its identity fails.
3. A stale claimed CI association fails.
4. A forged `authority_effect` or source authentication claim fails.
5. Foreign/duplicate/forged challenge events fail.
6. HTML/script fields are escaped and CSP restricts active content.
7. Two different valid correction overlays leave exact original source and generated broker records unchanged.
8. A correctly reproduced `project(snapshot)` must match the frozen snapshot projection before qualification.

## Falsifiers and remaining blockers

- **False-positive title trust:** UI renders the original alias as if it were exact GitHub title.
- **Provenance drift:** PR head / blob / run ID / URL is changed but still classed as source-matched.
- **Authority promotion:** a derived card can admit, merge, approve, certify, execute, or train itself.
- **Behavioral overclaim:** GitHub account/comment/CI statuses presented as authenticated agent model identity or real-agent behavioral validity.
- **Tampering:** source record, source snapshot, or original broker projection changes during challenge/correction.
- **Unreviewed threat:** the merged #987 implementation has six outstanding review threads. Qualification does **not** resolve these.

No real P1→P2→P3 agent session was independently witnessed here. A separate runtime-sandbox and authenticator test remains required before `Agent Quarantine` can mean capability isolation or trustworthy behavior.

## Link to Systems Intelligence Daily Digest

This demonstration contributes one **observed metadata reconciliation** and three **derived correction events**. Recommend `D — Cross-Repo` note, `K — Agent Quarantine` evidence lens, and human decision queue item to review #987 issues. It creates **no** acquired resources, revenue, recovery funding, appointments, or beneficiary outcomes.
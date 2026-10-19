# On-Track Reflex v0.1 — observation pilot

**State:** Z1 proposal / read-only experiment; not an admission gate.  
**Objective:** INTENT_OS_RESOURCE_MINER_USABLE.  
**Anchor:** Issue #822: user enters a natural-language objective on the existing `/intent-os` page, receives evidence-bearing public Resource Miner candidate links, and can make an informed decision. Issue #928 tracks this observer.  
**Authority:** NONE. `WITNESS_IS_NOT_THE_AUTHORITY`.

## Core question

> Of everything we are building, what actually moves us toward a **usable** INTENT-OS and Resource Miner?

Measure movement as a *verified change in user capability*, not the number of issues, PRs, generated files, CI runs, or agent claims.

## Three independent claims

1. **Goal mapping:** Does the work item explicitly declare it supports the objective? The declaration is a claim, not proof. Fixed pilot anchors (#822, #928) are recorded as declared objective anchors.
2. **Implementation / verification:** Does the exact proposed or merged code actually pass the relevant tests? The current pilot does **not** query exact-head CI. PR existence never implies tests passed; issue closure never implies implementation.
3. **Observed use:** Did a human successfully use the deployed INTENT-OS / Resource Miner path to achieve the stated interaction? **Not measured in v0.1.** An independently checked run/receipt is required before claiming a usable outcome.

The v0.1 overall state is always **UNVERIFIED** by construction. A maintainer-applied `blocked` or `needs-human` label can indicate **AT_RISK** for a goal-mapped item, but a label is not independently verified root-cause evidence. There is no path to ON_TRACK in v0.1.

## Existing repository components

The observer adds a projection, not a rival governance substrate. `SEED.md`, `CURRENT.md`, `INTENT_GRAPH.yaml`, `EVIDENCE_GRAPH.json`, `GRAPH_ALIGNMENT.yaml`, the Coordinator, and protected CI remain in their separate roles. Some graph artifacts expressly say **PROPOSED**; the observer does not ratify them or treat agreement between agents with shared sources as independent verification.

## Use

Local deterministic fixture:

```sh
cd humanaios-funding-pipeline/resource-miner
python3 -m resource_miner.on_track_reflex --smoke-test
python3 -m unittest discover -s tests -p 'test_on_track_reflex.py' -v
python3 -m resource_miner.on_track_reflex --input path/to/github-issues.json \
    --json-out outputs/report.json --markdown-out outputs/report.md
```

GitHub read-only observation:

```sh
GITHUB_TOKEN='<read-only token>' python3 -m resource_miner.on_track_reflex \
    --repo humanaios-ui/operations --max-pages 3 \
    --json-out outputs/report.json --markdown-out outputs/report.md
```

Use the GitHub Actions `on-track-reflex-observe` manual run or an issue/PR change to generate a run summary and downloadable JSON/Markdown artifact. It fetches up to three pages (100 entries each) of **open** GitHub issues including PRs, plus closed objective anchor #822. The report indicates if pagination was truncated and **always** declares missing closed-work history and all other repositories. API failures produce a failed job, not an optimistic result.

No credentials are stored in the JSON. No issue, pull request, workflow, deployment, source-of-truth file, or protected setting is changed by the workflow.

### Declaration for work truly associated with the goal

Place this single exact line at the start of an issue or PR body:

```text
on_track_target: INTENT_OS_RESOURCE_MINER_USABLE
```

This is a self-declaration. It has no admission or governance effect. Never automatically apply it to unrelated issues. Unmapped work remains visible as `UNMAPPED`; the bot must not attach a strategy label by topic resemblance alone.

## INTENT-OS consumer contract

Schema: `humanaios.on_track_reflex/v0.1`. See `schemas/on_track_reflex_v0_1.schema.json`.

Fields: `scope` (sampling completeness and blind spots); `counts`; `items` (work links, declared goal mapping, proposal state, CI = UNVERIFIED, user outcome = UNVERIFIED, blockers, next action); deterministic `snapshot_sha256`.

The JSON is a **projection** from GitHub observations. The existing INTENT-OS UI could render this as a separate “What moved our goal?” panel **after** an approved, authenticated, read-only artifact transport has been verified. The existing public Resource Miner route must not silently fetch private CI/issue data or expose operator records. This pilot does **not** deploy a dashboard and does not claim a live production read.

## Evaluation gate — 30 items

Independently label 30 historical or synthetic work items, with people blinded to the reflex verdict. Stratify across: genuinely goal-linked work, unrelated work sharing keywords, PRs with passing tests but no usable outcome, blocked work, closed work without deployment, and deliberately misleading agent statements.

Record:
- False-green rate = falsely ON_TRACK / not actually verified complete (must remain zero in pilot).
- Mapping false positives and false negatives against human-reviewed goal links.
- Drift missed / true divergent items.
- Minutes and decisions saved relative to manual issue/PR review.

Repeat on real GitHub observations. **No status check promotion, automatic admission, model training, merge, rollout, or public dashboard** until separate review, independent evidence, and human approval.

## Next bounded milestone

Add a read-only *exact-commit CI receipt* adapter and an independent, replayable `/intent-os` production smoke receipt: user objective submitted → candidates visible → official source accessible → eligibility uncertainty accurately communicated. Only then can the INTENT-OS operator panel show **TESTED** or **OBSERVED** with honest provenance.

**Falsifier:** A merged PR, a README claim, a model-written test claim, a proposed graph relation, or a successful workflow alone produces a verified real-world outcome. If any can, reject the reflex.

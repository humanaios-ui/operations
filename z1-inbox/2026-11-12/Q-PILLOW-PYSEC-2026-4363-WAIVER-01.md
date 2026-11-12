# Ruling request Q-PILLOW-PYSEC-2026-4363-WAIVER-01 — scoped audit waiver for PYSEC-2026-4363 (pillow), tools/Metaculus

**Z1 Proposer:** Claude (Z1) — transcribing the waiver Z2 directed on 2026-11-11 and accepted in session on 2026-11-12, so the repository holds a record of it
**Date Submitted:** 2026-11-12
**Status:** AWAITING Z2 RATIFICATION
**Carrier of the change:** PR #1185 (`.github/workflows/security-gates.yml`, +3 lines, Tier 2). This file records the decision; it changes no workflow.
**Why this exists:** CodeRabbit's finding on #1185 (Major, security): the workflow comment says "added at Z2 direction" and no record of that direction is in the repository. That is correct. Z2's acceptance was given in a chat session and by the coordinator admit command on #1185, neither of which is a ratification record.

```yaml
candidate_id: "Q-PILLOW-PYSEC-2026-4363-WAIVER-01"
title: "Waive PYSEC-2026-4363 (pillow 12.3.0, fixed in 13.0.0) for tools/Metaculus/requirements.txt only"
author: "Z1 (Claude)"
proposed_at: "2026-11-12T00:00:00Z"
scope:
  - ".github/workflows/security-gates.yml: one --ignore-vuln line, Metaculus audit command only (carried by #1185)"
resource_cost:
  cost:
    RAT-min: 5
    Z1-ktok: 20
    CI-min: 1
  dependencies: ["PR #1185", "issue #1101 (the Metaculus dependency constraint)"]
  blocking_on: []
impact_prediction:
  resource_impact: 1
  areas_affected: ["security-gates audit of tools/Metaculus/requirements.txt"]
  positive_outcomes:
    - "security-gates stops failing on main for an advisory whose fix cannot resolve in this file."
  risk_factors:
    - "A waiver hides the advisory from this audit. If the vulnerable code path is reachable from Metaculus tooling, the waiver hides a real exposure. Z1 found no call path from the bot to a pillow image decode, but did not trace every path and did not read the advisory text."
    - "The audit loop stops at its first failure; two other requirements files were never audited on main and may report findings once this one passes."
```

## Claim

- **claim:** `pip-audit` on `tools/Metaculus/requirements.txt` reports pillow 12.3.0 with PYSEC-2026-4363, fixed in 13.0.0. The file pins `forecasting-tools<0.4.0`, which requires `pillow<13`, so the fixed version cannot resolve there. The existing scoped exception list in the same command (54 IDs) records the same constraint.
- **evidence:**
  - [V] #1185's body, from a run Z1 did not repeat: before the change `Found 1 known vulnerability, ignored 54`; after, `No known vulnerabilities found, 55 ignored`.
  - [V] On #1185 head `8233486049756843693a279c0c9db6f1f1dffaef`, CI job "Python dependency vulnerability scan" passed (observed in this session).
  - [I] The severity (CodeRabbit says Critical, CVSS 9.1) and the advisory's publication date (5 November 2026) come from CodeRabbit's comment. Z1 did not check the advisory record.
  - [V] Reachability read, 2026-11-12, by unpacking the published wheels of `forecasting-tools` 0.3.5 and 0.3.6 (both require `pillow<13.0.0`; no 0.4.0 exists on PyPI). Pillow call sites in the package:
    - `ai_models/ai_utils/openai_utils.py` lines 144 and 148: `Image.open` on an image URL (fetched with `urlopen`) or a base64 string, inside a private token-counting helper. It runs only for a chat message that holds an `image_url` item.
    - `agents_and_tools/source_archive/fetchers/playwright_fetcher.py` line 86: `Image.open` on a PNG that fetcher made itself (lazy, size only). Part of the source-archive tool, which has its own command-line entry point.
    - `util/file_manipulation.py`: imports `Image` for an image-writing helper.
  - [V] `tools/Metaculus/main.py` imports only text classes from `forecasting_tools` and does not mention `image_url`, playwright or images (grep).
  - [I] No call path from the bot to `Image.open` was found. Not proven absent: Z1 did not trace every search and LLM path end to end.
  - [I] What the advisory's flaw triggers on is unknown: the advisory service was unreachable from the Z1 box (403), so the advisory text was not read.
- **not claimed:** that the exposure is harmless; that this is a fix (it is a waiver); anything about `tools/calibration_graph/requirements.txt` or `tools/requirements.txt`.

## Options

- `ratify waiver`
- `remove waiver`
- `later`

## What each sets in motion

- `ratify waiver`: Z1 adds this candidate's ID to the workflow comment in #1185 (one more push), CI re-runs, and #1185 may then merge. #1142 (pytest) follows.
- `remove waiver`: #1185 closes. security-gates stays red on main until the dependency moves off `forecasting-tools<0.4.0`; #1142 and #1198 inherit the red scan.
- `later`: this block closes with its bytes signed; the question returns only as a new block. #1185 stays unmerged.

## How this gets ruled

Per the 2026-09-18 ruling ("the merge is the ratification", `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md`): write the option on the `choice:` line below and set `status: DECIDED` in a one-file pull request, or tap it on the board's Decisions page and use **→ PR**. Merging that pull request is the ratification. Z1 signs nothing and does not merge it.

## Ruling

choice:
by:
at:
status: OPEN

## Z2 Review Checklist

- [ ] Waive PYSEC-2026-4363 for `tools/Metaculus/requirements.txt` only? — options: ratify waiver, remove waiver, later
- [ ] Reachability: Z2 accepts the partial read above (no call path found from the bot; advisory text unread; not traced end to end).
- [ ] A follow-up exists to move off `forecasting-tools<0.4.0` (issue #1101 or a new one), so the waiver has an owner and an exit.

## Falsifier

Event-based, no clock. This waiver is wrong, and should be removed rather than carried, if either happens:

- (a) the next `security-gates` run after #1185 merges fails in a file other than the Metaculus one because of this ID, meaning the waiver spread beyond its scope; or
- (b) pillow is shown reachable from code the Metaculus tooling runs, at 12.3.0, with the advisory's trigger.

Probe for (a): the ID appears once in `security-gates.yml`, inside the Metaculus `pip_audit` command only (`grep -n PYSEC-2026-4363 .github/workflows/security-gates.yml`).

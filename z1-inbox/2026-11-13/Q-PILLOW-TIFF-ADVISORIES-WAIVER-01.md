# Ruling request Q-PILLOW-TIFF-ADVISORIES-WAIVER-01 — scoped audit waiver for CVE-2026-128067 and CVE-2026-128066 (pillow), tools/Metaculus, with a revisit trigger and an owner

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-13
**Status:** AWAITING Z2 RATIFICATION
**Carrier of the change:** a separate workflow pull request, opened as a draft after this file is ruled (`.github/workflows/security-gates.yml`, two `--ignore-vuln` lines, Tier 2). This file records the decision; it changes no workflow.
**Why this exists:** the first run on `main` after #1185 merged (run 43423339339, merge `b1545996`) failed in "Audit all requirements files" on `tools/Metaculus/requirements.txt`. The waiver for PYSEC-2026-4363 worked (`ignored 55`). The same audit now reports two more advisories on the same package, `pillow 12.3.0`, each fixed in `13.0.0`. They are new findings, not a failure of the first waiver. Night directed on 2026-11-13: file a waiver for both with a revisit note, and file a follow-up issue for the real fix.

```yaml
candidate_id: "Q-PILLOW-TIFF-ADVISORIES-WAIVER-01"
title: "Waive CVE-2026-128067 and CVE-2026-128066 (pillow 12.3.0, fixed in 13.0.0) for tools/Metaculus/requirements.txt only, with a revisit trigger"
author: "Z1 (Claude)"
proposed_at: "2026-11-13T00:00:00Z"
scope:
  - ".github/workflows/security-gates.yml: two --ignore-vuln lines, Metaculus audit command only (carried by a follow-on draft pull request)"
resource_cost:
  cost:
    RAT-min: 5
    Z1-ktok: 30
    CI-min: 2
  dependencies: ["Q-PILLOW-PYSEC-2026-4363-WAIVER-01 (ratified 2026-11-12; same file, same cause)", "issue #1101 (the Metaculus dependency constraint)", "issue #1214 (moving off forecasting-tools<0.4.0)"]
  blocking_on: []
impact_prediction:
  resource_impact: 1
  areas_affected: ["security-gates audit of tools/Metaculus/requirements.txt", "#1142 and #1198 (both inherit the red scan until main is green)"]
  positive_outcomes:
    - "security-gates stops failing on main for two advisories whose fix cannot resolve in this file, so the loop reaches the two requirements files it has never audited."
  risk_factors:
    - "A waiver hides the advisories from this audit. One of them (CVE-2026-128066) fires when an image is opened or its EXIF is read, which is a different trigger from the first waiver's (a TIFF save). Z1's reachability read below is partial."
    - "This is the second waiver for the same package in two days. Three in a row would be a pattern, not an exception (see the falsifier)."
    - "The audit loop stops at its first failure; `tools/calibration_graph/requirements.txt` and `tools/requirements.txt` still have not been audited on main and may report findings once this passes."
```

## Claim

- **claim:** `pip-audit` on `tools/Metaculus/requirements.txt` reports pillow 12.3.0 with two advisories beyond the 55 already ignored, both fixed in `13.0.0`. The file pins `forecasting-tools<0.4.0`, which requires `pillow<13`, so the fixed version cannot resolve there. This is the same constraint as the first waiver.
- **evidence:**
  - [V] Main run 43423339339, job "Python dependency vulnerability scan", step "Audit all requirements files", log lines at 12:14:31 UTC: `Found 2 known vulnerabilities, ignored 55 in 1 package`, then `pillow 12.3.0 CVE-2026-128067 13.0.0` and `pillow 12.3.0 CVE-2026-128066 13.0.0`. Earlier files in the loop printed `No known vulnerabilities found`. Gitleaks passed.
  - [V] Advisory records, read 2026-11-13 from PyPI's JSON listing for pillow 12.3.0 (source `osv`, 58 records on that listing). Both are separate records, not aliases of PYSEC-2026-4363, both fixed in `13.0.0`, neither withdrawn:
    - `GHSA-xcvg-w56q-r89m`, alias `CVE-2026-128067`, rated high in its own text (CWE-787). A heap buffer overflow when Pillow *saves* a compressed TIFF through libtiff: size tags from image metadata (`exif=` or `tiffinfo=`, or a re-save of a crafted palette TIFF) can make the encoder read past a heap buffer, copying process memory into the output, or write past it. Same encoder family and same trigger class as the first waiver: a TIFF *save* of attacker-controlled metadata.
    - `GHSA-wqgw-9xfh-qf2g`, alias `CVE-2026-128066`, rated medium in its own text (CWE-770). Memory denial of service in TIFF and EXIF directory parsing: a small crafted image makes `Image.open()` return normally while holding gigabytes of memory; the same parser runs for EXIF in JPEG, PNG, WebP and MPO. Impact is a crash or stall; the text says there is no memory corruption. **The trigger is different from the first waiver: it is a parse (open or `getexif()`), not a save.**
  - [V] The reachability read from the first waiver (2026-11-12; unpacked `forecasting-tools` 0.3.5 and 0.3.6 wheels, both `pillow<13.0.0`; no 0.4.0 on PyPI) is carried forward. Z1 did not repeat it today:
    - `Image.open` appears in `ai_models/ai_utils/openai_utils.py` (an image URL or a base64 string, inside a token-counting helper that runs only for a chat message holding an `image_url` item) and in `agents_and_tools/source_archive/fetchers/playwright_fetcher.py` (a PNG that fetcher made itself, lazy, size only).
    - `tools/Metaculus/main.py` imports only text classes from `forecasting_tools` and does not mention `image_url`, playwright or images.
  - [I] For CVE-2026-128067 (save): same finding as before. No call path from the bot to a TIFF save found; the only `Image.save` found is the generic `write_image_file` helper.
  - [I] For CVE-2026-128066 (parse): the two `Image.open` sites are the ones that matter, because a parse bug fires on open. Both need an image the bot does not send (an `image_url` message item) or an image the package itself rendered. Not proven absent: Z1 did not trace every search and LLM path end to end, and did not check whether a model response could put an `image_url` item into a message the bot later passes to the token-counting helper.
  - [I] Severity wording ("high", "medium") is the advisories' own text. Z1 checked no CVSS score.
- **not claimed:** that the exposure is harmless; that this is a fix (it is a waiver); anything about `tools/calibration_graph/requirements.txt` or `tools/requirements.txt`; that these two are the last pillow advisories (the listing has 58 records and the scan has now needed new waivers twice in two days).

## Revisit note (what makes this waiver end)

The waiver has an owner and an exit, both stated without dates:

- **Owner:** issue #1214, "Move tools/Metaculus off forecasting-tools<0.4.0 so pillow can reach 13 (exit for the pillow audit waivers)", filed with this candidate.
- **Exit event:** any one of (i) a `forecasting-tools` release that allows `pillow>=13`; (ii) the Metaculus tooling dropping `forecasting-tools`; (iii) the Metaculus tooling being retired. When the event happens, the two `--ignore-vuln` lines and the 55 older ones are removed in the same pull request that moves the dependency, and the audit is re-run.
- **Sweep rule:** when the exit event happens, issue #1214 lists every `--ignore-vuln` ID in the Metaculus branch and each is either shown fixed by the new pin or filed as its own ruling.

## Options

- `ratify waiver`
- `remove waiver`
- `later`

## What each sets in motion

- `ratify waiver`: Z1 opens one draft pull request adding the two ignore lines to the Metaculus audit command and citing this record in the workflow comment. It needs its own admit and its own CI. After it merges, the first run on `main` that audits the Metaculus file must pass, and the loop then reaches the two files it has never audited; anything they report is a separate finding. #1142 (pytest 9.2) merges after that, on Night's earlier authorization, if the scan is green and CI is clean.
- `remove waiver`: no pull request. `security-gates` stays red on `main` until the dependency moves; #1142 and #1198 inherit the red scan. Issue #1214 becomes the only path.
- `later`: this block closes with its bytes signed; the question returns only as a new block. `main` stays red.

## How this gets ruled

Per the 2026-09-18 ruling ("the merge is the ratification", `z1-inbox/2026-09-18/Z2_RULING_MERGE_IS_RATIFICATION.md`): a one-file pull request fills this file's `## Ruling` section, and merging it is the ratification. The section must be the one `tools/decision_relay.py` writes (`choice`, `by`, `at`, `status: DECIDED`, `block_hash`, `body_hash` and the fenced `RULING` block); editing only `choice:` and `status:` by hand is skipped by `tools/intent_os_reconcile_v1_0.py` (`plan()`).

Two ways to land the section:

1. Night taps the option on the board's Decisions page and uses **→ PR**. The relay writes the section.
2. Z1 builds the same section with the relay's own `ruling_block`, `body_hash` and `write_choice` and opens the one-file pull request. In that block, `by` is a Z1 label and is not a claim about who ruled. The signature's `by` and `at` come only from the merger's GitHub login (mapped to a declared ratifier) and the merge date.

The `body_hash` pins every byte of this file outside `## Ruling`; this text is final once that pull request exists. Z1 does not merge the ruling pull request: the merger's login becomes the ratifier's name, so a Z1 merge would be read as Night's act.

## Z2 Review Checklist

- [ ] Waive CVE-2026-128067 and CVE-2026-128066 for `tools/Metaculus/requirements.txt` only? — options: ratify waiver, remove waiver, later
- [ ] Reachability: Z2 accepts the partial read above. Note the second advisory is a parse trigger, not a save trigger; the carried-forward read covers both `Image.open` sites but is not an end-to-end trace.
- [ ] Issue #1214 (owner and exit event above) exists and is linked from the carrying pull request.
- [ ] Z2 accepts that a third pillow advisory on this file needs its own block, not an edit to this one.

## Falsifier

Event-based, no clock. This waiver is wrong, and should be removed rather than carried, if any of these happens:

- (a) scope drift: either ignore is applied to any audit command other than the Metaculus one. A finding of these advisories in another requirements file is not scope drift: it is a separate finding that needs its own ruling.
- (b) pillow is shown reachable from code the Metaculus tooling runs, at 12.3.0, with either advisory's trigger (a TIFF save of caller-supplied metadata for CVE-2026-128067; an `Image.open` or `getexif()` on attacker-supplied bytes for CVE-2026-128066).
- (c) pattern: a third new pillow advisory on this file needs a waiver before the exit event. At that point the question becomes "stop waiving and move the dependency", not another line.

Probe for (a): inspect executable arguments, not mentions of the IDs (they also appear in a comment). `grep -n -e '--ignore-vuln CVE-2026-128067' -e '--ignore-vuln CVE-2026-128066' .github/workflows/security-gates.yml` must print exactly two lines, and both must sit inside the branch that tests `"${normalized_req}" = "tools/Metaculus/requirements.txt"`. Post-merge test: the first `main` run of `security-gates` after the carrying pull request merges must pass "Audit all requirements files" on `tools/Metaculus/requirements.txt`; any new finding it prints on the next files is not a failed waiver.

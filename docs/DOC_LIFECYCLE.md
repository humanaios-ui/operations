---
doc_id: HAIOS-OPS-011
title: Document lifecycle — Filing · Processing · Consumption · Production
revision: 0
status: draft
owner: "@humanaios-ui/ops"
canonical: true
lifecycle: consumed
consumer: tools/doc_lifecycle_lint.py
---

# Document lifecycle (FPCP)

A document earns its place in the tree by being consumed. Existence is not utility.

## The four stages

| stage | meaning | who moves it | mechanical test |
|---|---|---|---|
| **Filing** | landed with `lifecycle: filed`, a `doc_id`, and a stated intended consumer | Z1 (or the importer) | front matter present; `doc_lifecycle_lint` lists it |
| **Processing** | being converted into the thing that will use it: rules → a tool with a self-test · claims → registry lines with falsifiers · config → the tool's directory · renders → a generator | Z1 builds; Z2 rules | a PR that names the doc as source and the artifact as output |
| **Consumption** | something reads it: a tool, a workflow, a registry line, a controlled doc. Inbound reference ≠ 0 or `consumer:` resolves to a real path | code (lint verifies) | `CONSUMED` in the lint; cannot be archived while true |
| **Production** | generated *from* code or the record (triage tables, reports, site renders). Never hand-edited; regenerated | code | `lifecycle: produced` and a `generator:` path; hand edits are DRIFT |

Anything that is none of these after `STALE_DAYS` (14) is **orphaned** and gets a disposition ruling from Z2. The lint refuses silence: every file gets a disposition, and `--enforce` fails CI when filed docs sit unruled.

## Dispositions the lint emits

`CONSUMED` keep · `CODE` extract the rule into a tool with a self-test, then the doc becomes the tool's spec or is archived · `REGISTRY` append the H/F/IC lines (falsifier required) then archive the block · `PRODUCED` keep only with a generator · `ARCHIVE` retire.

## What "drop" means here

Nothing is deleted. The record is append-only.
1. `git mv docs/X docs/_archive/X`; front matter gets `lifecycle: archived`, `archived_at`, `archived_why`, and `sha256` of the content at archive time.
2. One line per archived doc appended to `docs/_archive/INDEX.md` (path · sha · why · ruling hash).
3. A doc with inbound references cannot be archived — the lint blocks it; fix the reference first.
4. Archive is a Z2 ruling by hash over the triage table, not a Z1 act.

## Rule the lint enforces on itself
Its own triage output is `produced`; if someone edits the table by hand instead of re-running the lint, the next run overwrites it and the diff is the receipt.

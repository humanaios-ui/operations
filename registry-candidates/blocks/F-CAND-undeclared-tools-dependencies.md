---
id: "F-CAND-undeclared-tools-dependencies"
name: "undeclared-tools-dependencies"
status: CANDIDATE
class: F
gap_function: T
date_origin: "2026-08-02"
session_origin: "S-080226 (Claude substrate, repo audit)"
tags: ["dependencies", "tooling", "works-on-operator-machine", "latent-defect"]
related: ["IC-041", "IC-043"]
---

## Synopsis

Repo-wide dependency audit (751 tracked files, fresh clone) found `fastmcp` imported by
`acat/mcp/server.py` and nine `tools/` scripts, with `fastmcp` — plus `mcp`, `anthropic`,
`slack_sdk`, and `numpy` at the tools layer — declared in none of the repo’s five dependency
manifests. The deployed Railway service is unaffected (its import graph is clean against root
`requirements.txt`), so no incident has occurred; the defect is latent: every fastmcp-dependent
tool runs only where the packages happen to be manually installed, and fails on any fresh
environment, other operator, or substrate — the works-on-operator’s-machine class.

## Gap-function note (soft assignment)

Classified `T` on the reading that manifests are the repo’s *claim* about what its code needs
and the import graph is the *activity* — a representation/reality divergence. The `O` reading
(environment state unverifiable from the artifact) is defensible; route to second-coder review.

## Evidence anchor

Import inventory + manifest cross-check from clone at audit time; install + import smoke test of
the six missing packages passed 2026-08-02 (versions: fastmcp 3.4.5, mcp 1.29.0, supabase 2.31.0,
anthropic 0.120.2, slack_sdk 3.43.0, numpy 2.4.4).

## Remediation

Part 1 above (`tools/requirements.txt`, migrate-by-addition). Structural mitigation candidate for
the class: a CI check comparing third-party imports against declared manifests (a stdlib-only
script; fits the existing workflow suite) with a class-matched negative control branch that
imports an undeclared package the check must catch.

## Promotion gate

Z2 ratification; gap_function second-coding; fix landed and smoke-run of at least one fastmcp
tool from a clean environment.

## Routing

→ Zone 2 (Night) per P21. Registry write is Z2/Z3; this document proposes.

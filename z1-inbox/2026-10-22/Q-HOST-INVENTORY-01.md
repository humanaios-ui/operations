# Q-HOST-INVENTORY-01 — Z1 Candidate (UNRATIFIED)

**Status:** `awaiting_ratification` — draft only. Not entered in REGISTERED.md or PRIORITY_QUEUE.md.
**Observed:** 2026-10-22, repo HEAD `7bc7662` (main) at audit time.
**Current index status (as of this revision):** listed in `z1-inbox/INDEX.yaml` candidates as `awaiting_z2`; rendered in `Z1_INBOX_INDEX.md`.
**Author:** Z1 (Claude)
**Proposed:** 2026-10-22T10:44:14Z
**Companion:** `z1-inbox/2026-10-22/Q-EXTERNAL-ADVISORY-INTAKE-01.md`

---

```yaml
candidate_id: "Q-HOST-INVENTORY-01"
title: "Finding: no ratified host/runtime inventory, so 'not applicable' claims about live infrastructure cannot be checked"

description: |
  The repository proves absence of PHP in its own code and configs (0 .php files in tree or
  history; Python, Node, and static runtimes only in Dockerfiles, railway/nixpacks, bicep,
  wrangler.jsonc, vercel.json, and pages.yml). It cannot prove absence on live hosts:
  - Public hostnames named in the repo are spread across Railway (api.humanaios.ai), Azure
    Container Apps (resource-miner, Metaculus job), Cloudflare (intent-os-board Worker,
    haioscc.pages.dev), Vercel (ui/), and Supabase.
  - A live header check (X-Powered-By, Server) was attempted on api.humanaios.ai,
    haioscc.pages.dev, and intent-os-board.workers.dev. The sandbox egress proxy refused all
    three (CONNECT 403, connect_rejected). Result: UNVERIFIED-LIVE for every host.
  - No file lists which hosts exist, who owns them, or what runtime each runs.
  So any statement "PHP2Shell does not apply" can only be made for repo-managed code.

author: "Z1 (Claude)"
proposed_at: "2026-10-22T10:44:14Z"

scope:
  - "New file: HOST_INVENTORY.yaml (repo root, Z2-ratified once created)"
  - ".github/workflows/ (one PHP-presence guard step)"
  - "z1-inbox/ (advisory records reference inventory IDs)"

resource_cost:
  cost:
    RAT-min: 20
    Z1-ktok: 4
    Z3-hr: 1
    CI-min: 1
  dependencies: ["Q-EXTERNAL-ADVISORY-INTAKE-01", "owner access to provider dashboards"]
  blocking_on: []

impact_prediction:
  resource_impact: 6
  areas_affected:
    - "Every public hostname HumanAIOS operates"
    - "Advisory applicability decisions (Q-EXTERNAL-ADVISORY-INTAKE-01)"
    - "CI gate set"
  positive_outcomes:
    - "Each host has a named owner, provider, runtime, and last-checked date"
    - "'Not applicable' claims cite a checkable inventory row"
    - "A PHP-presence guard catches a PHP file added to the repo before merge"
  risk_factors:
    - "Inventory goes stale; a stale row is worse than none because it looks verified"
    - "Owner must supply live runtime facts that the repo cannot reveal"
    - "Header checks need egress to the named hosts; the sandbox currently denies them"

proposed_change:
  - "Create HOST_INVENTORY.yaml with two sections. `hosts:` holds one row per public hostname: id, hostname, provider, owner, runtime, last_verified (date), verification (VERIFIED | UNVERIFIED-LIVE), source (repo path or dashboard reference). `audits:` holds audit records with a different shape: id, subject, scope, result (e.g. NOT_APPLICABLE_REPO | UNVERIFIED_LIVE), checked_at, evidence. Validators check the one-row-per-hostname invariant on `hosts:` only."
  - "Seed audit record HOST-PHP2SHELL-2026-10 under `audits:` (not `hosts:`): records the repo result (0 PHP files; no PHP runtime in any named config) and marks live status UNVERIFIED_LIVE until the owner confirms from provider dashboards."
  - "Add a CI step: fail if `git ls-files -z | grep -zEiq '[.]php$'` finds a tracked path, unless an exception names the file, an owner, and an independent approval or ratification record bound to that exact exception row and file. Use this one case-insensitive, end-anchored matcher everywhere. CI rejects a missing or unauthorized approval. CODEOWNERS and the Z2 commit-author check are not relied on for this (the commit-author check is advisory only). A test with an unapproved tracked probe.PHP must fail the guard."
  - "Owner runs a read-only header check (Server, X-Powered-By) on each `hosts:` row and records the result in that host row. This is a live request to a named host, so it is a live scan for authorization purposes: the owner runs it only after a separate Z2 authorization that names the hosts and the request scope. This candidate grants no such authorization. Set `verification` to `VERIFIED` only when owner-recorded provider or runtime evidence positively identifies the runtime. Missing, generic, or blocked responses remain `UNVERIFIED-LIVE`. Z1 does not run live scans without Z2 authorization."

falsifier: |
  This candidate is FALSE if:
  - After the owner's first pass, any public hostname that resolves to a HumanAIOS-controlled
    service is missing from HOST_INVENTORY.yaml (inventory incomplete)
  - OR a row is marked VERIFIED without owner-recorded provider or runtime evidence that
    positively identifies the runtime (verification wrong)
  - OR a header check on a row marked VERIFIED shows X-Powered-By: PHP or a PHP-like Server
    banner (verification wrong). A repo-file exception never qualifies a host as VERIFIED.
  - OR an unapproved .php file (any case) passes the CI guard (guard ineffective). An approved
    exception with an exact row and independent approval must still pass; test both.
  - OR any row's last_verified is older than 90 days while marked VERIFIED (inventory stale)

evidence:
  - "git ls-files -z | grep -zEiq '[.]php$' → 0; git log --all --name-only | grep -Eiq '[.]php$' → 0"
  - "Dockerfile.acat-api (python:3.14-slim), Dockerfile.resource-miner and tools/Metaculus/Dockerfile (python:3.11-slim), .clusterfuzzlite/Dockerfile (OSS-Fuzz Python), railway.toml, nixpacks.toml, infra/*.bicep (3 files), wrangler.jsonc, ui/vercel.json, .github/workflows/pages.yml"
  - "curl -I attempts on api.humanaios.ai, haioscc.pages.dev, intent-os-board.workers.dev → CONNECT tunnel failed, response 403 (agent proxy connect_rejected)"
  - "SESSION_RITUALS.md line 51 (haioscc.pages.dev named as a cross-check endpoint)"

z2_decision:
  status: "awaiting_ratification"
  ratified_at: null
  ratification_hash: null
  z2_notes: ""

related_candidates: ["Q-EXTERNAL-ADVISORY-INTAKE-01"]
external_constraint: null
links:
  - name: "Companion candidate"
    url: "z1-inbox/2026-10-22/Q-EXTERNAL-ADVISORY-INTAKE-01.md"
```

---

## Notes for Z2

- HOST-PHP2SHELL-2026-10 is the N/A record the audit asked for. Its status is "repo: not applicable; live: unverified." It does not say "safe."
- The live hosts named above come from repo files and a SESSION_RITUALS.md reference. Owner should confirm the list is complete.
- Nothing here authorizes a live scan or any change to a provider. Ratification only creates the inventory and the CI guard.

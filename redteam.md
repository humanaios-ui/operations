# Copilot Red-Team Repository Audit — Seed Prompt

**HumanAIOS LLC · S-060326 · Charter Day 54**
**Stage 1 of 3: AUDIT → REMEDIATION (tracked issues) → REPOSITORY PLAN**

-----

## How to use this document

This is the **seed prompt** for a three-stage repository governance cycle. Paste Section A into GitHub Copilot (Copilot Chat or Copilot coding agent with repo access) as the first instruction. Stages 2 and 3 are defined at the bottom so Copilot understands where this is going, but **only Stage 1 is requested now.** Do not let Copilot begin remediation or planning until we have reviewed its audit return.

The three nodes under audit:

|Node                           |What it is                                   |Surface                                     |
|-------------------------------|---------------------------------------------|--------------------------------------------|
|`humanaios-ui/lasting-light-ai`|Cloudflare Pages source for humanaios.ai     |Public website                              |
|`humanaios-ui/operations`      |Canonical operations repository              |Internal ops, governance, ACAT API, registry|
|`LastingLightAI/HAIOSCC`       |Source for haioscc.pages.dev (Command Center)|Operator-facing dashboard                   |

-----

## SECTION A — THE AUDIT REQUEST (paste this to Copilot)

> **Role:** You are a senior repository auditor performing a red-team review. Your job in this pass is **observation only** — report exact current state. Do not propose fixes, do not edit files, do not open issues, do not refactor. Findings only. We will review your report and return a separate remediation instruction.
> 
> **Scope:** Audit these three repositories at their current `main` (or default) branch HEAD:
> 
> 1. `humanaios-ui/lasting-light-ai`
> 1. `humanaios-ui/operations`
> 1. `LastingLightAI/HAIOSCC`
> 
> For **each** repository, return the following in a structured report. Use the exact section headers below so the three reports are directly comparable.
> 
> ### 1. Inventory
> 
> - Full directory tree to 3 levels of depth (collapse `node_modules`, `.git`, build artifacts, and any vendored dependency directories — note their presence but do not expand them)
> - Total file count by type/extension
> - Last commit SHA, date, and message on the default branch
> - Branch list with last-commit date for each; flag any branch >30 days stale
> 
> ### 2. Documentation & Entry Points
> 
> - Presence and quality of: `README.md`, `LICENSE`, `CONTRIBUTING`, `.github/` workflows, `CODEOWNERS`
> - Is there a single clear entry point that tells a new reader what this repo is and how to run/deploy it? Quote the first 5 lines of the README if present.
> - List any docs that contradict each other or reference files/paths that no longer exist (dead references)
> 
> ### 3. Structural Integrity
> 
> - Identify duplicate or near-duplicate files (same purpose, different names or locations)
> - Identify orphaned files: present in the tree but not imported, referenced, linked, or routed anywhere
> - Identify any file that appears to be a parallel/competing version of another (e.g. two routers for the same endpoint, two configs for the same service, `_v1` / `_v2` / `_FINAL` / `_BACKUP` siblings)
> - For `operations` specifically: confirm whether `acat/api/app.py` mounts every router file that exists under `acat/api/routes/`, and flag any route file that exists but is NOT mounted
> 
> ### 4. Configuration & Secrets Hygiene
> 
> - List every config file (`.env*`, `wrangler.toml`, `*.config.*`, `package.json`, `requirements.txt`, `pyproject.toml`, CI YAML)
> - Flag any committed secret, API key, token, connection string, or credential **by file and line, but DO NOT reproduce the secret value** — report only “potential secret at `path:line`, type=<kind>”
> - Flag any `.gitignore` gap that would allow a secret or build artifact to be committed
> 
> ### 5. Deployment Wiring
> 
> - For `lasting-light-ai` and `HAIOSCC`: confirm the Cloudflare Pages build config (build command, output directory, root) and whether it matches the actual repo structure
> - For `operations`: identify the deployment target(s) and confirm the entry point referenced by the deploy config actually exists
> - Flag any deploy config that points at a path or file that is missing
> 
> ### 6. Cross-Repository Consistency
> 
> - Do the three repos share naming conventions, or do they diverge? Give specific examples.
> - Are there files that appear to have been copied between repos and then drifted out of sync? Name them.
> - Is there any shared dependency or contract (e.g. an API schema, a data contract, a shared component) that exists in more than one repo and is NOT in sync?
> 
> ### 7. Red-Team Summary (per repo)
> 
> - Top 5 structural risks, ranked, each one sentence
> - One-line answer: “If a new contributor cloned this repo today, what is the single biggest thing that would confuse or block them?”
> 
> ### Output format
> 
> - Return one report per repository, then a final **Cross-Node Comparison** table with columns: Node · File count · Stale branches · Dead references · Orphaned files · Potential secrets · Deploy config valid (Y/N) · Biggest single risk
> - Do not edit anything. Do not open issues. This is a read-only audit. End your response with the line: `AUDIT COMPLETE — AWAITING REVIEW`

-----

## SECTION B — REVIEW GATE (HumanAIOS internal — not for Copilot)

When Copilot returns the audit:

1. **Zone 2 review** — Night reads the three reports + cross-node table.
1. **Triage** — sort findings into: (a) correct & act now, (b) correct but defer, (c) false positive / Copilot misread, (d) needs human verification before acting.
1. **Governance check** — any finding touching a public surface (`lasting-light-ai`, `HAIOSCC` public routes) is subject to **P-ANON** (no collaborator data exposed) and **Tradition 11** (no promotional drift) before remediation is authorized.
1. **Decide scope of Stage 2** — which findings become tracked issues.

Only after this gate do we send Stage 2.

-----

## SECTION C — STAGE 2 PREVIEW (do not send yet)

Stage 2 will instruct Copilot to convert the **approved** subset of findings into GitHub Issues, one issue per finding, using this template so each is independently trackable:

```
Title: [AUDIT-S060326] <node> — <short finding>
Labels: audit-s060326, <node-name>, <severity:high|med|low>
Body:
  ## Finding
  <exact finding from Stage 1 report, with file:line refs>
  ## Why it matters
  <one paragraph>
  ## Proposed correction
  <specific, scoped change — no scope creep>
  ## Acceptance criteria
  <how we verify this is resolved>
  ## Zone gate
  <Z1 Copilot may draft / Z2 Night ratifies / Z3 Night executes>
```

Stage 2 will require: each issue scoped to one finding, no bundled changes, no edits to `main` without an explicit merge instruction, and a back-reference to this audit so the whole cycle is traceable.

-----

## SECTION D — STAGE 3 PREVIEW (do not send yet)

Stage 3 is the payoff: a **Repository Plan**. After the tracked issues are resolved (or scheduled), Copilot will be asked to produce a single document — `REPOSITORY_PLAN.md` for the `operations` root — that contains:

- The **target-state** directory layout for all three nodes (the arrangement we are deliberately choosing, not just describing what exists)
- The intended **role and boundary** of each repo: what belongs in it, what does not
- Naming and versioning conventions to be enforced going forward
- The deployment wiring for each node, documented as the single source of truth
- A migration path from current state → target state, expressed as the ordered set of issues from Stage 2
- An “effectiveness” rationale: for each major structural choice, one line on why it reduces confusion, duplication, or deploy risk

The plan is the artifact that turns three independently-grown repositories into one deliberately-arranged system.

-----

## Governance notes

- This entire cycle is **Z1 draft / Z2 ratify / Z3 execute.** Copilot drafts and reports; Night reviews and authorizes; Night merges and deploys. Copilot does not push to `main` or open issues without an explicit instruction from a later stage.
- The audit is **read-only by design.** If Copilot proposes fixes in Stage 1, that is a scope violation — discard and re-prompt.
- All three stages back-reference the tag `AUDIT-S060326` so the full audit → remediation → plan arc is traceable in one search.

-----

*Seed prompt · Z1 · Unit Zero · S-060326 · Charter Day 54 · Claude*
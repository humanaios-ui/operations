# TENSION_FINDINGS.md — Unnecessary Friction Log

**Purpose:** Collect real friction points and confusions encountered during PR review, merge, and governance execution. Patterns inform CLAUDE.md and guidance updates.

**Audience:** Z1 (proposers), Z2 (ratifier), Z3 (executors), guidance reviewers

---

## Issue Template

```
**ID:** TENSION-YYYYMMDD-NNN
**Date:** YYYY-MM-DD
**PR:** #NNN (or "Ad-hoc" if not PR-scoped)
**Category:** [Governance Ambiguity | Guidance Conflict | Gate Confusion | Missing Context | Process Bottleneck | Documentation Gap]
**Severity:** [Low | Medium | High]

**What happened:**
Brief description of the friction point encountered.

**Where it lives:**
File(s) and line numbers involved (e.g., CLAUDE.md:L209, .github/workflows/quality-baseline.yml:L73).

**Root cause:**
Why did this confusion exist? (Outdated guidance, conflicting sections, assumption not documented, misaligned status fields, etc.)

**Proposed fix:**
What change would eliminate this tension?

**Impact:**
How many PRs would this affect? How much rework prevented?

**Proposer:** Z1, Z2, or Z3 identifier
**Status:** [Open | Under Review | Fixed | Deferred]
**Resolution:** If Fixed, link to commit or updated file location.
```

---

## Findings

### TENSION-20261002-001

**ID:** TENSION-20261002-001  
**Date:** 2026-10-02  
**PR:** #642  
**Category:** Governance Ambiguity  
**Severity:** High  

**What happened:**
CLAUDE.md declared governance complete and ratified ("2026-10-02 — Z2 (Night) finalized all four specifications") while the specification files themselves had contradictory status fields: some marked "pending", others "awaiting Z2 RATIFY", others "ratified" without recorded digests. Unclear whether work was complete or blocked.

**Where it lives:**
- CLAUDE.md: Appended Events section (L290–296)
- FRAMEWORK_MAPPING.md: Status line (initial version)
- BOOT_PROCESS_MAP.md: Status line (initial version)
- FIVE_RINGS_MAPPING.md: Status line (initial version)
- AUTHORIZATION_EVIDENCE_MAPPING.md: Status line (initial version)

**Root cause:**
Specifications existed but their status was decoupled from the ratification claim. No mechanism to record and validate real SHA256 hashes alongside "ratified" declarations. Made it possible to claim ratification on mutable, unhashed specs—signature meaningless without digest binding.

**Proposed fix:**
Add "Specification Digest Record (Ratified)" section to CLAUDE.md with real SHA256 hashes for all four specifications. Enforce rule: cannot declare `status: ratified` without `sha256: <hash>` recorded in the same payload. Treat hash mismatch as INTEGRITY-VIOLATION callout.

**Impact:**
Every governance document and specification faces this risk. Affects Z2's confidence in ratification claims. Fixing this clarifies the contract: ratification = hashed, immutable, recorded digest. Prevents future misreads and re-audits.

**Proposer:** Z1 (Claude)  
**Status:** Fixed  
**Resolution:** Commit de00eee1 "Finalize four-layer concept-to-code specification stack with real digests" + CLAUDE.md updated with Specification Digest Record (L317–322).

---

### TENSION-20260914-001

**ID:** TENSION-20260914-001  
**Date:** 2026-09-14  
**PR:** #264 + ongoing  
**Category:** Process Bottleneck  
**Severity:** Medium  

**What happened:**
Test enumeration duplicated across three locations: `.github/workflows/quality-baseline.yml` (hardcoded pytest list), `tools/intent_os_test_harness_v1_0.py` (separate hardcoded list), and `tools/tests/test_ci_suite_enumeration.py` (regex-parsed copy). Two lists drifted—7 of 21 test files under `tools/tests/` were missing from CI but passed when run by hand. Guard existed but was expensive to maintain.

**Where it lives:**
- .github/workflows/quality-baseline.yml: L73–90 (original hardcoded list)
- tools/intent_os_test_harness_v1_0.py: L412–450 (duplicate list, separate maintenance burden)
- tools/tests/test_ci_suite_enumeration.py: L67–69 (regex parser to extract from workflow)

**Root cause:**
Hand-maintained copies of one list drift by design. No single source of truth. Regex extraction fragile to format changes. Policy (explicit enumeration > globbing) good; implementation (three copies) bad.

**Proposed fix:**
Single source of truth: `.tool-control/baseline_tests.yaml` with structured test entries. Workflow, harness, and test validator all load from YAML. Eliminates duplication, makes drift visible, enables CI gate to check consistency.

**Impact:**
Prevents unguarded tests from silently skipping CI. All PRs touching test suite benefit. ~45 minutes per cycle saved (regex debugging + manual list sync eliminated).

**Proposer:** Z1 (Claude)  
**Status:** Fixed  
**Resolution:** Commit 8c9a2c5f "Centralize test enumeration via .tool-control/baseline_tests.yaml" + test_ci_suite_enumeration.py refactored to load from YAML.

---

### TENSION-20260925-001

**ID:** TENSION-20260925-001  
**Date:** 2026-09-25  
**PR:** #642  
**Category:** Guidance Conflict  
**Severity:** Medium  

**What happened:**
CLAUDE.md stated "Commit Discipline (P19 Principles)" with K ≤ 13 file cap, but did not clarify whether merge commits were exempt. Reviewers applied the cap to merge commits (false negative), and authors were confused about when the rule applied. CI flag was informational only but wording suggested it could block.

**Where it lives:**
- CLAUDE.md: L209–226 "Commit Discipline (P19 Principles)"
- CI workflow flag logic (advisory, non-blocking)

**Root cause:**
Guidance conflated authored commits and merge commits. No explicit statement that merge commits are structural (exempt from cap). "Advisory flag" phrasing ambiguous—authors misread as "this could cause a merge block."

**Proposed fix:**
Add explicit sub-sections:
- "Authored Commits:" — cap applies, rationale (reviewability)
- "Merge Commits (git merge):" — EXEMPT, rationale (structural, not authored work)
- "Enforcement:" — workflow flags authored overage; advisory only, no merge block

Added clear example: "Merge commits are exempt from K cap. A 47-file merge commit that brings in main is not a violation."

**Impact:**
Removes confusion on every PR with a merge commit. Z1 and reviewers both get clear rule. Reduces re-reads and back-and-forth on P19 status.

**Proposer:** Z1 (Claude)  
**Status:** Fixed  
**Resolution:** CLAUDE.md L209–226 rewritten with clear sub-sections and merge commit exemption (committed 2026-09-25).

---

### TENSION-20260919-001

**ID:** TENSION-20260919-001  
**Date:** 2026-09-19  
**PR:** ad-hoc (documentation)  
**Category:** Missing Context  
**Severity:** Medium  

**What happened:**
CI gates relied on external dependencies (GitHub CLI, Python 3.11+, optional APIs) but no documentation of graceful degradation. When a gate failed due to missing tool, the error message was cryptic ("gh: command not found"), and it was unclear whether the gate was required or optional, or whether the code was supposed to skip when unavailable.

**Where it lives:**
- .github/workflows/quality-baseline.yml: various steps
- .github/workflows/repository-admission-gate.yml: GitHub API calls
- Tools expecting GitHub CLI or optional connectors

**Root cause:**
Tool authors assumed availability without documenting fallback behavior. No pattern library for graceful degradation. Three patterns emerged organically (skip decorators, timeout + fallback, advisory warnings) but were never codified.

**Proposed fix:**
Create `docs/CI_ENVIRONMENT_ASSUMPTIONS.md` documenting:
1. Required dependencies (Python 3.11+, git, etc.)
2. Optional dependencies (GitHub CLI, external APIs)
3. Three graceful degradation patterns with code templates:
   - Pattern 1: Skip decorators (pytest.skipif for missing tools)
   - Pattern 2: Timeout + fallback return (API calls with graceful no-op)
   - Pattern 3: Advisory warnings (log but continue)
4. Implementation checklist for new tools

**Impact:**
Tool authors have a reference. Tests don't fail mysteriously when optional tools are unavailable. CI remains green even if (e.g.) GitHub CLI is replaced or temporarily unavailable. Reduces debugging time and false negatives.

**Proposer:** Z1 (Claude)  
**Status:** Fixed  
**Resolution:** docs/CI_ENVIRONMENT_ASSUMPTIONS.md created (3 patterns + templates); committed 2026-09-19.

---

### TENSION-20261002-002

**ID:** TENSION-20261002-002  
**Date:** 2026-10-02  
**PR:** #642  
**Category:** Governance Ambiguity  
**Severity:** High  

**What happened:**
Repository Admission Gate blocked PR #642 with message "PR not in admission list," but it was unclear whether this was a code issue (merge blockers, CI failure) or a governance routing decision (Z2 needs to add PR to policy). Z1 attempted to debug and fix a governance decision, wasting effort on a Z2-only decision.

**Where it lives:**
- .github/workflows/repository-admission-gate.yml: L3–34 (documentation and decision rules)
- REPOSITORY_COORDINATOR_POLICY.json: admission list
- CLAUDE.md: Z1 vs Z2 authority caps (L37–66 for Z1, L82–110 for Z2)

**Root cause:**
Governance routing decision presented as technical failure. No clear signal in gate output that said "this is not a code issue; Z2 governance decision required." Z1 saw gate failure and tried to fix the code.

**Proposed fix:**
1. Update repository-admission-gate.yml documentation (L3–34) with explicit statement: "Admission is a governance routing decision (Z2 authority). Code cannot fix rejection. If PR is blocked, contact Z2 to add to REPOSITORY_COORDINATOR_POLICY.json admission list."
2. Add gate output comment template: "Admission gate result: [PASS | BLOCKED—governance routing decision required]. If blocked, contact Z2 to review admission eligibility."
3. Add callout rule to CLAUDE.md: When Repository Admission Gate blocks, emit **GOVERNANCE-ROUTING** callout (Z2 domain, not Z1 fix).

**Impact:**
Z1 stops wasting effort on Z2-only decisions. Gate failures become unambiguous routing signals, not code bugs. Reduces Z2 re-read load and Z1 debugging cycles.

**Proposer:** Z1 (Claude)  
**Status:** Open (awaiting Z2 policy update to REPOSITORY_COORDINATOR_POLICY.json)  
**Resolution:** To be fixed once Z2 adds PR #642 to admission list; then update gate documentation with routing clarification (proposed above).

---

### TENSION-20261002-003

**ID:** TENSION-20261002-003
**Date:** 2026-10-02
**PR:** #623 (introduced), #663 (fixed)
**Category:** Process Bottleneck
**Severity:** High

**What happened:**
Resolving a `tools-manifest.yaml`/`TOOLS_MANIFEST.md` merge conflict, the manifest files were staged with `git add` *before* re-running `.tool-control/scan.py`. The commit that was actually pushed and merged into `main` therefore carried the pre-regeneration content, silently dropping two tool registrations (`HAIOS-TOOL-206`/`207`, added by a concurrently-merged PR) even though both tool files were present on disk in the same tree. CI's "Tool manifest integrity" check had passed on an *earlier* commit in the same PR (a single-file fix, correctly regenerated); a re-run against the final merge commit *did* independently detect the regression (`scan.py --check` reported `collect_macos.py` on disk but absent from the manifest) — but that detection completed around the same time as, or after, the merge decision, and was never consulted before merging. A general "`mergeable_state: unstable` is usually non-blocking" heuristic (true for *other* checks failing all session, e.g. gitleaks, admission gate) was applied without separately polling the specific named gate's completion status for the exact final SHA. **Correction (2026-10-02, via Copilot PR review on #670):** the original wording of this entry said the regression was "not caught by CI" — that overstated it. CI did detect it; the gap is that detection wasn't checked before merging, not that detection never happened.

**Where it lives:**
- Any workflow resolving a conflict in a `.tool-control/`-rendered file (`tools-manifest.yaml`, `TOOLS_MANIFEST.md`, and the equivalent `z1-inbox/INDEX.yaml` / `Z1_INBOX_INDEX.md` pair)
- The merge decision step, which read aggregate `mergeable_state` instead of waiting for and reading the specific "Tool manifest integrity" check-run result

**Root cause:**
Two independent gaps compounded: (1) staging a rendered/generated file before the generator re-runs is a silent trap — the index holds stale content and `git commit` captures it verbatim; (2) a coarse mergeable_state heuristic was trusted in place of waiting for and reading the specific gate check's result for the exact final SHA, right after a conflict resolution that touched the very mechanism that gate validates.

**Proposed fix:**
1. Document the safe sequence for manifest/rendered-file conflict resolution explicitly (e.g. in `tools-manifest.yaml`'s own header comment or a CONTRIBUTING note): merge → regenerate (`scan.py` → `validate.py` → `render.py`) → verify output → *then* `git add` → commit. Never add before regenerating.
2. Adopt a standing rule: after any push that resolves a merge conflict, wait for and read check-run results filtered to the specific gate(s) touched by that conflict — not just the aggregate `mergeable_state` — before merging.

**Impact:**
Any Z1 resolving a manifest/rendered-file conflict is at risk of this exact silent regression reaching `main` despite CI detecting it, because the detection wasn't consulted before merging. Affects every PR that touches tool registration during a conflict.

**Proposer:** Z1 (Claude)
**Status:** Fixed
**Resolution:** PR #663 (merged) — re-ran `scan.py`/`validate.py`/`render.py` against current `main`; manifest resynced with 0 violations and no `HAIOS-TOOL-*` ID collisions.

---

### TENSION-20261002-004

**ID:** TENSION-20261002-004
**Date:** 2026-10-02
**PR:** #623, #642, #653 (this session); earlier IC-064/IC-065 (prior session)
**Category:** Process Bottleneck
**Severity:** Medium

**What happened:**
Third occurrence of the same class of bug this project has now hit at least three times: concurrent Z1 branches each compute "next free `HAIOS-TOOL-NNN`" by reading `main`'s current manifest and incrementing, with no reservation or locking. This session alone: PR #642's branch and PR #653's branch independently claimed `HAIOS-TOOL-206`/`207` for two entirely different tool pairs; PR #623 separately had a related field-placement bug that looked like (but technically wasn't) a numeric collision with the #651 lineage. The earlier IC-064/IC-065 incident (prior session) was the same pattern.

**Where it lives:**
`.tool-control/scan.py`'s tool-ID assignment logic; any two tool-adding branches opened against a similar `main` snapshot.

**Root cause:**
Sequential integer ID allocation reads a point-in-time snapshot with no claim-staking mechanism. Any two branches forked close together will independently compute the same "next" ID, and **each branch's own tree is individually valid** — `.tool-control/validate.py` (lines ~194-207) already hard-fails on a duplicate `tool_id` *within one tree*, and `.github/workflows/tool-manifest.yml` already runs that as a blocking, ERROR-level gate. Neither branch trips it alone. The collision only becomes real once both merge into the same `main`, and is caught only if whichever branch merges second happens to be checked by hand during conflict resolution. **Correction (2026-10-02, via Copilot PR review on #670):** the original wording said duplicate-ID detection "is only caught by a Z1 manually running `git grep`... not by a standing gate" — that's wrong; a standing, blocking gate for *within-tree* duplicates already exists and works. The real, narrower gap is specifically *cross-branch reservation* — two independently-valid branches racing for the same ID — which no single branch's own validation can see.

**Proposed fix:**
Move to content-addressed or branch-qualified provisional IDs that `.tool-control/render.py` renumbers deterministically at merge time, so two branches can never land on the same final ID regardless of what either one claims locally. The existing `validate.py` duplicate check stays as the backstop it already is — this fix addresses the cross-branch race specifically, not a missing structural check.

**Impact:**
Every pair of concurrently open tool-adding PRs is at risk of the cross-branch race specifically; manual collision-hunting cost real review time on three separate occasions this session, each one only surfaced at merge time, after each branch had already individually passed the existing within-tree gate.

**Proposer:** Z1 (Claude)
**Status:** Open
**Resolution:** None yet; proposed fix above awaits Z2 prioritization.

---

### TENSION-20261002-005

**ID:** TENSION-20261002-005
**Date:** 2026-10-02
**PR:** Ad-hoc / repo-wide CI infrastructure (observed on #623, #644, #653, #594, #663, and likely every other open PR)
**Category:** Gate Confusion
**Severity:** Medium

**What happened:**
"Secret scanning (gitleaks)" intermittently fails across this session's PRs, including single-line dependency bumps with no secret-scanning surface at all. Job-log root cause on the failing runs: `gitleaks/gitleaks-action@v3`'s org-eligibility check hit "API rate limit exceeded for installation," and per the action's own documented breaking-change announcement, without that check succeeding it falls back to hard-requiring a `GITLEAKS_LICENSE` secret, which is not configured in this repository. **Correction (2026-10-02, via Copilot PR review on #670):** the original wording said this fails "on every PR," framing it as a permanent requirement. It is not — a later run on PR #594 (11:47 UTC) succeeded without `GITLEAKS_LICENSE`, logging that `humanaios-ui` is an individual-account installation for which no license is required. This is an intermittent eligibility-lookup failure (rate-limit-sensitive), not a standing license gate.

**Where it lives:**
Whichever `.github/workflows/*.yml` invokes `gitleaks/gitleaks-action@v3` (grep the workflow directory for `gitleaks-action` to locate the exact file).

**Root cause:**
The action's org/account-eligibility lookup against the GitHub API is rate-limit-sensitive; when it succeeds, it correctly determines no license is required for this individual-account installation and passes; when the lookup itself gets rate-limited, the action fails closed into requiring a license it doesn't actually need here.

**Proposed fix:**
No repo-side fix needed if the lookup is simply transient-rate-limit-sensitive — the correct outcome does land when the API call succeeds. Z2 may still want to pin a `GITLEAKS_LICENSE` secret or a version less sensitive to this lookup if the intermittent red checks are costing reviewer attention regardless of whether they're "real."

**Impact:**
Intermittent red "Secret scanning" checks regardless of content, on an unpredictable subset of runs, degrading the signal value of CI status at a glance. Has not blocked any merge so far (not a required check), but habituates reviewers to ignoring red checks, which is its own risk.

**Proposer:** Z1 (Claude)
**Status:** Open
**Resolution:** None yet; awaiting Z2 decision (secret vs. workflow change).

---

### TENSION-20261002-006

**ID:** TENSION-20261002-006
**Date:** 2026-10-02
**PR:** #623, #594 (both observed this session)
**Category:** Gate Confusion
**Severity:** Low

**What happened:**
`principle_compliance_bot_v1.py --check-commit` ("Check principles (P19)") flagged `P-COMMIT-DISCIPLINE: Oversized commit (N files)` on merge-from-main commits that bring in a large multi-file PR. **Correction (2026-10-02, via Copilot PR review on #670):** the original wording of this entry blamed a stale, cached `BASE_SHA`. Verified directly against PR #594's own job log: `BASE_SHA` was passed in fresh (`376fbf8468b9...`), exactly matched the PR's actual current base at check-run time, and the 17 files in the diff were *all* genuinely part of that PR's own content — nothing unrelated. The stale-`BASE_SHA` theory does not hold for that instance; it was simply wrong.

**Where it lives:**
`tools/agents/principle_compliance_bot_v1.py`'s file-count logic, invoked from the "Check principles (P19)" CI step; `BASE_SHA` itself is computed correctly.

**Root cause:**
The check runs `git diff --name-only "$BASE"...HEAD` against the *merge commit* and counts every file in that aggregate diff as if it were one authored commit's own change set. When `HEAD` is a merge bringing in a legitimately large, multi-file PR, the full PR-lifetime file count is attributed to "this commit," tripping the oversized-commit threshold. `CLAUDE.md`'s own P19 section (and this file's TENSION-20260925-001) already establishes that merge commits should be exempt from the K-file cap "structural, not authored work" — this check does not implement that exemption; it treats a merge commit's accumulated diff exactly like an authored one.

**Proposed fix:**
Detect merge commits (e.g. `git rev-list --min-parents=2 -n1 HEAD` matching `HEAD`, or checking the commit message for the `Merge ... into ...` pattern already visible in this check's own log output) and apply the existing, already-documented merge-commit exemption instead of counting the full incorporated diff.

**Impact:**
False "commit discipline" findings on exactly the ordinary, correct-process merge-from-main commits this repo's own conventions ask for. The same check also attempts to auto-file a tracking GitHub issue for the violation and fails that step too (separate permissions/scope issue), turning a soft advisory into a hard job failure rather than a graceful warning.

**Proposer:** Z1 (Claude)
**Status:** Open
**Resolution:** None yet; proposed fix above awaits Z2/maintainer prioritization.

---

## How Z2 Uses This Log

1. **During PR review:** If Z1 mentions a friction point, check if it's already logged here.
2. **After Z1 handoff:** Review TENSION findings alongside F/IC/H candidates.
3. **Pattern detection:** If 3+ PRs hit the same tension, auto-rank it in PRIORITY_QUEUE.md for guidance update.
4. **Guidance updates:** When a tension is fixed, update the relevant guidance file and link back (add comment: "TENSION-20261002-001 prompted this clarification").

---

## Filing New Tensions

**Per §B (Session Close):**
- After Findings Scan, add: **Tension Scan** — harvest friction points into a new file `z1-inbox/<date>/TENSION-YYYYMMDD-NNN.md`
- Use template above
- Z2 reviews when signing off on findings
- Transfer confirmed tensions to TENSION_FINDINGS.md (this file)

**Severity guide:**
- **High:** Blocks work, creates ambiguity on governance vs. code, causes wasted Z1 effort
- **Medium:** Causes rework or re-reads, slows PR cycle
- **Low:** Minor confusion, doesn't block, but worth documenting for future clarity

---

## Backfill Notes

All findings above are backfilled from Sessions before 2026-10-02. Additional pre-session tensions welcome—file them with best-guess dates and mark as `[Backfilled]` in the Status field if created retroactively.

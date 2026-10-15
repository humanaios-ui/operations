# COORDINATION_PROTOCOL.md — Multi-Agent Coordination Spec

**Status:** Z1 candidate — awaiting Z2 ratification
**Updated:** 2026-10-15
**Purpose:** The behavioral contract for multiple agents (Claude sessions, practices, Z3 executors) working the operations repo concurrently. Six rules, each mapped to the operations mechanism that enforces it and the failure it prevents.
**Audience:** Z1 proposers, Z3 executors, the repository-coordinator, and any agent opening PRs here.

---

## Why this exists

During the 2026-10-09 Empirica-substrate build, 4–6 agent sessions coordinated off an ad-hoc shared file (`~/.empirica/MESH_BUILD_BOARD.md`). It worked, but it also demonstrated — in one day — every failure mode of uncoordinated multi-agent work: a near-loss of 51 artifacts to co-editing, completion overstated four times, a mis-routed migration, and lost-update races on the file itself.

Those failures produced six rules. This document ports the **rules** (the durable value) into operations — **not** the markdown board (which would be a parallel coordination system alongside issues/PRs/REGISTERED.md, the exact anti-pattern the substrate work existed to end). The board's job is already done here by issues, PRs, the admission gate, the coordinator, and REGISTERED.md. This spec makes the discipline those surfaces must encode explicit.

**Principle:** the lightweight coordination view is a *projection* of the authoritative system (issues/PRs/CI/REGISTERED.md), never a second source of truth. See the GitHub Project view (below) for the sanctioned live view.

---

## The Six Rules

### 1. CLAIM before you work
**Rule:** Take the unit of work explicitly before touching code. One owner per unit at a time.
**Operations mechanism:** Assign the GitHub issue/PR to yourself; the **repository-admission gate** (`repository-admission-gate.yml`) + coordinator operator-queue admit you to a slot (capacity is bounded — raised 4→9 in #878). An unassigned/unadmitted edit is uncoordinated by definition.
**Prevents:** two agents starting the same work; the double-claim that the board caught on B6 when a row was left unclaimed.

### 2. ONE WRITER per repo/area
**Rule:** Do not co-edit a working tree or branch another agent holds. If your work touches an area another owner has claimed, coordinate on the issue/PR thread — never edit in parallel.
**Operations mechanism:** One open PR per branch; the admission gate's single-writer/backpressure control; branch protection on `main`.
**Prevents:** the concurrent-session collision that nearly destroyed 51 humanaios artifacts (2026-10-09) when two sessions wrote the same tree.

### 3. REPORT EVIDENCE, not verdicts
**Rule:** "Done" requires evidence — a commit SHA, a green CI check, command output, a merged PR. A comment saying "complete" is not completion.
**Operations mechanism:** PRs carry CI check results; a merge with passing required checks is the record. `verify_pr_readiness.sh` and the z2 gate's self-tests are the evidence surface.
**Prevents:** the four overstated-completion events of 2026-10-09 (B1 status, autonomy push, B2 end-to-end, the premature "SUBSTRATE COMPLETE") — each contradicted by a one-command check.

### 4. VERIFY a peer's "done" before building on it
**Rule:** Before depending on another agent's result, run the check yourself and cite it. Trust artifacts, not claims.
**Operations mechanism:** Required status checks gate merges; `git branch -r --contains`, CI run links, and the merged SHA are the citations. Do not branch off an unmerged/unverified branch.
**Prevents:** compounding on a false "done" — the discipline that caught the B2 schema mismatch and the b4_migrate mis-route before they propagated.

### 5. NO `/tmp` for deliverables
**Rule:** Deliverables live in a repo. Never leave work in `/tmp` or other ephemeral/unversioned locations.
**Operations mechanism:** Commit to a tracked path; CI runs against the repo tree. `/tmp` and untracked home dirs are out of bounds for anything that must survive.
**Prevents:** the four practices whose git remotes pointed at a wiped `/tmp/git-remotes/*` (2026-10-09), and the B2 renderer that first shipped to `/tmp`.

### 6. APPEND, don't overwrite
**Rule:** Changes are additive. Never force-push over another agent's commits; never overwrite another owner's record.
**Operations mechanism:** `main` is append-only for governance (REGISTERED.md: Z2-sole-write, append); PRs add commits; the P19 commit-discipline cap keeps authored commits reviewable. Merge commits are exempt.
**Prevents:** silent clobbering of concurrent work; the lost-update races that forced atomic appends on the shared board.

---

## Relationship to existing operations surfaces

| This rule | Enforced / supported by |
|---|---|
| 1 Claim | `repository-admission-gate.yml`, coordinator operator-queue (#878), issue assignment |
| 2 One writer | admission backpressure, branch protection, one-PR-per-branch |
| 3 Evidence | required CI checks, `scripts/verify_pr_readiness.sh`, `z2_ratification_gate.yml` |
| 4 Verify | required status checks, merged-SHA citation |
| 5 No /tmp | repo-tracked paths, CI-against-tree |
| 6 Append | REGISTERED.md append-only, P19 commit cap, no-force-push |

This spec is the **behavioral contract**; the files above are its **enforcement**. Where a rule is not yet machine-enforced (e.g., rule 4 is largely convention), that gap is the roadmap for the coordinator.

---

## The sanctioned live view (not a markdown board)

The "what is every agent doing right now" view that the mesh board provided is served in operations by a **GitHub Project** over the open-PR / issue queue — a projection of the authoritative data, grouped by status (Backlog → Admitted → In progress → In review → Merged). It is read from issues/PRs, never hand-maintained. See the project view at the org level (`humanaios-ui`). A hand-kept markdown board is explicitly **not** sanctioned: it drifts and races, as 2026-10-09 showed.

---

## Falsifier

This protocol is FALSE / needs revision if, within 60 days: a multi-agent collision destroys or silently overwrites committed work despite rules 1/2/6 being followed; OR agents route around the admission/evidence surfaces faster than the surfaces can enforce them (indicating the rules need machine enforcement, not documentation). Either outcome files an IC candidate.

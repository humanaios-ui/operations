# Zone → Remote Map

**Location:** `ZONE_REMOTE_MAP.md`
**Status:** Z1 map — **derived, not ratified.** It reports what the remotes are; it changes no zone,
cap or authority. `ZONE_REGISTRY.md` remains the ratified instrument and is not edited by this file.
**Derived:** 2026-09-16 (22:50 UTC / 17:50 CDT, `bash_tool` verified per P22)
**Counterpart:** `REPOSITORY_STRUCTURE.md` maps *this repository's internals*. This maps *zone → remote*
(§2) and *remote → local clone* (§5), the two halves that were missing.

---

## Why this file exists

`ZONE_REGISTRY.md` names repositories as bare strings: `operations`, `humanaios`, `acat-dashboard`. It
carries no owner, no URL, and no evidence that any of them resolve. Every consumer — a prepared command,
a clone script, a reader — has to supply the missing half from memory. Two wrong paths were shipped into
`z1-inbox/2026-09-16/Z2_RULINGS_2026-09-16.md` in one session for exactly that reason.

This file supplies the missing half and records how it was checked, so the next reader does not guess.

## 1 · Method

Two independent sources, because each fails differently:

| source | what it establishes | how it fails |
|:--|:--|:--|
| Authenticated repo listing | existence, canonical name, visibility, push access | shows repos the account can see; silent about ones it cannot |
| `git ls-remote --heads` (anonymous) | the URL resolves for an unauthenticated client | **returns the same failure for "private" and "does not exist"** |
| Local: `git -C "$d" rev-parse --git-dir` | the directory is a working repository | — |

**Do not probe local state with `git remote get-url origin 2>/dev/null`.** It prints nothing for a repo
with no remote *and* for a directory that is not a repo, and the suppressed stderr is the only thing that
distinguishes them. §5.1 records what that cost. Ask `rev-parse --git-dir` first, then the remote.

A private repo therefore reads as `no-anon-access` in column 5 while being confirmed real in column 3.
Reading that as "broken" is the trap; it is recorded rather than smoothed over.

## 2 · The join

All twelve named zones resolve. Canonical name is GitHub's spelling; **bold** marks a divergence from
`ZONE_REGISTRY.md`.

| Zone | Registry name | Canonical remote | Visibility | Anon probe |
|:--|:--|:--|:--|:--|
| Z-000 | `operations` | `humanaios-ui/operations` | public | resolves |
| Z-001 | `humanaios` | `humanaios-ui/humanaios` | public | resolves |
| Z-002 | `humanaios-internal` | `humanaios-ui/humanaios-internal` | **private** | no-anon-access |
| Z-003 | `acat-inspect` | `humanaios-ui/acat-inspect` | public | resolves |
| Z-004 | `acat-x` | `humanaios-ui/acat-x` | public | resolves |
| Z-005 | `acat-dashboard` | **`humanaios-ui/ACAT-Dashboard`** | public | resolves (redirect) |
| Z-006 | `acat-observatory` | **`humanaios-ui/ACAT-Observatory`** | **private** | no-anon-access |
| Z-007 | `empirica-practice-mesh` | `humanaios-ui/empirica-practice-mesh` | public | resolves |
| Z-008 | `lasting-light-ai` | `humanaios-ui/lasting-light-ai` | public | resolves |
| Z-009 | `docs` | `humanaios-ui/docs` | public | resolves |
| Z-010 | `findlocaltattooartists` | `humanaios-ui/findlocaltattooartists` | public | resolves |
| Z-011 | `research` | `humanaios-ui/research` | public | resolves |

**Zero unresolvable.** The two `no-anon-access` rows are private, not missing — both confirmed present
and pushable by the authenticated listing.

## 3 · Four findings

**3.1 — Two registry names are not the canonical spelling.** `acat-dashboard` is `ACAT-Dashboard`;
`acat-observatory` is `ACAT-Observatory`. Both still resolve, because GitHub redirects case, so nothing
has broken and nothing will warn. It matters for anything that compares strings rather than fetching —
a manifest key, a directory name, a `grep` against a clone list.

**3.2 — Four registry names are ambiguous across organisations.** A second org, `LastingLightAI`, holds
repositories with the same names:

| bare name in the registry | `humanaios-ui` | `LastingLightAI` |
|:--|:--|:--|
| `operations` | public | `Operations`, **private** |
| `humanaios` | public | public |
| `lasting-light-ai` | public | public |
| `acat-observatory` | `ACAT-Observatory`, private | `ACAT-Observatory`, private |

So **a third of the named zones cannot be resolved from the registry alone.** "Clone operations" is not
a complete instruction. This is the same shape as the `operations` / `operations-staging` hazard: two
things one name can mean, and picking wrong succeeds quietly.

**3.3 — `empirica` is not `empirica-practice-mesh`.** `humanaios-ui/empirica` exists and is a **fork of
the upstream Empirica framework** — unrelated to Z-007. Any instruction saying "the empirica repo" is
ambiguous between the zone and the fork.

**3.4 — `PLANNED_REPOS.md`'s cross-org audit is answerable now.** It lists Repo A–F as UNKNOWN, pending
"Phase 1b: Cross-org audit" and "pending broader scan". The authenticated listing shows exactly **six**
repositories in `LastingLightAI`:

`HAIOSCC` · `Operations` (private) · `humanaios` · `lastinglightai` (private) · `ACAT-Observatory`
(private) · `lasting-light-ai`

Whether these *are* Repo A–F is **Z2's to determine** — the roadmap describes them by status, not by
name, so matching them is a judgement about intent, not a lookup. Recorded as the scan's result, not as
the answer.

Worth noting separately: `LastingLightAI/HAIOSCC` is the source of the `haioscc.pages.dev` endpoints
that `SESSION_RITUALS.md` §A.1 names as the secondary fetch. It appears in no registry.

## 4 · Count reconciliation — and the registry disagrees with itself

`ZONE_REGISTRY.md` titles itself a **31-Zone Ecosystem Map**, and against `PLANNED_REPOS.md` that
number reconciles:

| | count |
|:--|--:|
| Named zones, Z-000 … Z-011 | 12 |
| `PLANNED_REPOS.md` — PLANNED (11) + ARCHIVED (2) | 13 |
| `PLANNED_REPOS.md` — UNKNOWN, Repo A–F | 6 |
| | **31** |

Stated because "31 repos" is quoted often and the registry itself names only twelve; a reader who
expects 31 rows and finds 12 is looking at a correct file.

**But the registry's own metadata block does not agree with the registry's own title.**
`ZONE_REGISTRY.md:125–127`:

```yaml
  total_active_zones: 12
  total_planned_zones: 20
  total_ecosystem: 32
```

12 + 20 = 32, which is internally consistent and is **not** the 31 in the file's title on line 1. And
`total_planned_zones: 20` is one more than the 19 rows `PLANNED_REPOS.md` actually carries (11 + 2 + 6).
So there are three figures in play — 31 (title), 32 (metadata), 31 (derived from the roadmap file) —
and no source reconciles all three.

An earlier revision of this section said only that "the arithmetic holds," having reconciled the title
against `PLANNED_REPOS.md` without reading the metadata block twelve lines further down **in the same
file**. One arithmetic holds. The file's two self-descriptions do not.

Which figure is correct is **Z2's**, not this file's: `ZONE_REGISTRY.md` is ratified, and both the title
and the metadata are inside it, so either correction is an edit to a ratified instrument. Recorded here
as an observed contradiction, not resolved.

## 5 · Local clones

Two roots, not one — read off the machine on 2026-09-16, not inferred.

### 5.1 · `/Users/andersonfamily/github` — the GitHub clones

| directory | `origin` | zone |
|:--|:--|:--|
| `ACAT-Dashboard` | `humanaios-ui/ACAT-Dashboard.git` | Z-005 |
| `ACAT-Observatory` | `humanaios-ui/ACAT-Observatory.git` | Z-006 |
| `acat-inspect` | `humanaios-ui/acat-inspect.git` | Z-003 |
| `acat-x` | `humanaios-ui/acat-x.git` | Z-004 |
| `empirica-practice-mesh` | `humanaios-ui/empirica-practice-mesh.git` | Z-007 |
| `findlocaltattooartists` | `humanaios-ui/findlocaltattooartists.git` | Z-010 |
| `humanaios-internal` | `humanaios-ui/humanaios-internal.git` | Z-002 |
| `lasting-light-ai` | `humanaios-ui/lasting-light-ai.git` | Z-008 |
| **`operations`** | **not a repository — see below** | **Z-000: NOT CLONED** |
| `research` | `humanaios-ui/research.git` | Z-011 |

**`github/operations` is not a clone of Z-000. It is a different project wearing the name.** Its `.git/`
contains one subdirectory, `hooks/` — no `HEAD`, `config`, `objects` or `refs` — so git rejects the tree
outright: *"fatal: not a git repository."* Its contents (`AUTOMATION_FRAMEWORK_SUMMARY.md`,
`INTENT-OS_AUTOMATION_SETUP.md`, `RECURSIVE_ORCHESTRATION_STRATEGY.md`, `REPOSITORY_SYNC_HANDOFF.md`,
dated 2026-09-11) exist in `humanaios-ui/operations` **on no branch**, and the markers a real clone must
have — `.z1-control/`, `CLAUDE.md`, `z1-inbox/` — are absent.

**So Z-000 has never been cloned to this machine.** That is the root cause of every "No such file or
directory" in this session's signing attempts, and `.z1-control/ratify.py` cannot be run locally until
it is fixed.

Two corrections recorded rather than overwritten, because the second was actively dangerous:

1. An earlier revision of this file said *"`operations` has no `origin`"*. Wrong. The discovery loop that
   produced it ran `git remote get-url origin 2>/dev/null`, which prints nothing both for a repo with no
   remote and for a directory that is not a repo at all. **The check could not distinguish its own two
   failure modes**, and the benign reading was recorded.
2. That revision prescribed `git remote add origin …` as the repair. Had it been followed after a
   `git init`, a push would have sent this unrelated project's contents **to the governance repository**.

The directory holds real, untracked work that exists nowhere else — no functioning git, and nothing of it
in any branch. It must be renamed, never deleted, before Z-000 is cloned into that path.

Not cloned in either root: **`humanaios` (Z-001)** exists only under `practices/`, over SSH; **`docs`
(Z-009)** is absent entirely; **`operations` (Z-000)** as above.

### 5.2 · `/Users/andersonfamily/practices` — the mesh practice directories

`practices/` is **not itself a git repository** — the listing's `.` entry produced nothing. The mesh
repo is the clone at `github/empirica-practice-mesh`. What `practices/` holds is nineteen working
directories, some of which are independent git repos with remotes that do not match their names.

| directory | `origin` | reading |
|:--|:--|:--|
| **`empirica-outreach`** | **`humanaios-ui/operations.git`** | **points at the governance repo** |
| **`empirica-foundation-evaluator`** | **`humanaios-ui/humanaios.git`** | **points at the core platform** |
| `empirica-mesh-support` | `humanaios-ui/empirica-mesh-support.git` | remote **does not exist** — PLANNED, never created |
| `website` | `git.getempirica.com/carly/website.git` | **PLANNED** (`PLANNED_REPOS.md:55`), so not unregistered — but its remote is a **non-GitHub host**, which no registry records |
| `humanaios` | `git@…humanaios.git` (SSH) | Z-001, the only SSH remote |
| `humanaios.archive.20260911-112252` | `git@…humanaios.git` (SSH) | archive clone, same remote |
| `acat-x` | `humanaios-ui/acat-x.git` | Z-004 — **second clone**, also in `github/` |
| `humanaios-internal` | `humanaios-ui/humanaios-internal.git` | Z-002 — **second clone**, also in `github/` |
| `collaborator-ops`, `empirica-analytics`, `empirica-autonomy`, `empirica-resource-miner`, `empirica-temporal-oracle`, `flta-app-empirica`, `grok-crossref`, `local-machine-optimizer`, `opportunity-aggregator`, `empirica-opportunity-aggregator.archive`, `schema.sql` | none | plain directories, or repos with no remote |

## 5.3 · What the local layout costs

**A push from `empirica-outreach` goes to `operations`.** Same for `empirica-foundation-evaluator` and
`humanaios`. Nothing about the directory name says so; `git push` from either succeeds and writes to a
repository the operator was not thinking about.

Three different things wear those two names, and an earlier revision of this line collapsed two of them
by calling the directories "Z-007 practice directories" — which is the exact conflation this file exists
to remove. Separated:

| | `empirica-outreach` | `empirica-foundation-evaluator` |
|:--|:--|:--|
| as a **planned repository** | `PLANNED_REPOS.md:31`, PLANNED, Phase 2 | `PLANNED_REPOS.md:29`, PLANNED, Phase 2 |
| as a **local directory** | `practices/empirica-outreach` | `practices/empirica-foundation-evaluator` |
| that directory's **remote** | `humanaios-ui/operations.git` (Z-000) | `humanaios-ui/humanaios.git` (Z-001) |

Neither is Z-007. **Z-007 is `empirica-practice-mesh`**, and nothing else. Each of these is a planned
repository in its own right that has not been created, a local directory grouped under `practices/`, and
a checkout of a governance repository — three facts that share one string and point three ways.

**Two clones of `acat-x` and of `humanaios-internal`.** The `operations` / `operations-staging` hazard
the runbook already described, present twice more: work in one, push from the other, and the divergence
is silent until a merge conflicts.

**`schema.sql` is a directory.** `ledgers/PRACTICE_RESOLUTION_MAP.md` already flagged it as "likely a
scaffolding accident"; the local listing confirms it exists as a directory with no remote. (An earlier
revision cited it by bare filename, which does not resolve — the file is under `ledgers/`, not at the
root.)

**`git.getempirica.com` could not be verified from here** — the outbound proxy returns 403 on CONNECT to
that host. Its state is unknown, not broken.

## 6 · Maintenance

Derived, so it goes stale when a repo is created, renamed, or made public. Re-derive by re-running the
two checks in §1 rather than editing rows by hand. **`ZONE_REGISTRY.md` is the ratified instrument** —
if the two disagree, the registry is authoritative about zones and caps, and this file is authoritative
about nothing except what the remotes were on the date in its header.

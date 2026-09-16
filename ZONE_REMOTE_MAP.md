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

## 4 · Count reconciliation

`ZONE_REGISTRY.md` titles itself a **31-Zone Ecosystem Map**. The arithmetic holds:

| | count |
|:--|--:|
| Named zones, Z-000 … Z-011 | 12 |
| `PLANNED_REPOS.md` — PLANNED (11) + ARCHIVED (2) | 13 |
| `PLANNED_REPOS.md` — UNKNOWN, Repo A–F | 6 |
| | **31** |

Stated because "31 repos" is quoted often and the registry itself names only twelve; a reader who
expects 31 rows and finds 12 is looking at a correct file.

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
| **`operations`** | **— none —** | **Z-000** |
| `research` | `humanaios-ui/research.git` | Z-011 |

**`operations` has no `origin`.** `git remote get-url origin` returns nothing. This is the clone where
`ratify.py` is run, so `git pull`, `git push` and every prepared command that assumes a remote fail
there. Repair: `git remote add origin https://github.com/humanaios-ui/operations.git`.

Not cloned in either root: **`humanaios` (Z-001)** exists only under `practices/`, over SSH; **`docs`
(Z-009)** is absent entirely.

### 5.2 · `/Users/andersonfamily/practices` — the mesh practice directories

`practices/` is **not itself a git repository** — the listing's `.` entry produced nothing. The mesh
repo is the clone at `github/empirica-practice-mesh`. What `practices/` holds is nineteen working
directories, some of which are independent git repos with remotes that do not match their names.

| directory | `origin` | reading |
|:--|:--|:--|
| **`empirica-outreach`** | **`humanaios-ui/operations.git`** | **points at the governance repo** |
| **`empirica-foundation-evaluator`** | **`humanaios-ui/humanaios.git`** | **points at the core platform** |
| `empirica-mesh-support` | `humanaios-ui/empirica-mesh-support.git` | remote **does not exist** — PLANNED, never created |
| `website` | `git.getempirica.com/carly/website.git` | a **non-GitHub host**; no registry covers it |
| `humanaios` | `git@…humanaios.git` (SSH) | Z-001, the only SSH remote |
| `humanaios.archive.20260911-112252` | `git@…humanaios.git` (SSH) | archive clone, same remote |
| `acat-x` | `humanaios-ui/acat-x.git` | Z-004 — **second clone**, also in `github/` |
| `humanaios-internal` | `humanaios-ui/humanaios-internal.git` | Z-002 — **second clone**, also in `github/` |
| `collaborator-ops`, `empirica-analytics`, `empirica-autonomy`, `empirica-resource-miner`, `empirica-temporal-oracle`, `flta-app-empirica`, `grok-crossref`, `local-machine-optimizer`, `opportunity-aggregator`, `empirica-opportunity-aggregator.archive`, `schema.sql` | none | plain directories, or repos with no remote |

## 5.3 · What the local layout costs

**A push from `empirica-outreach` goes to `operations`.** Same for `empirica-foundation-evaluator` and
`humanaios`. Nothing about the directory name says so; `git push` from either succeeds and writes to a
repository the operator was not thinking about. Both are Z-007 practice directories by name and
governance-critical repositories by remote.

**Two clones of `acat-x` and of `humanaios-internal`.** The `operations` / `operations-staging` hazard
the runbook already described, present twice more: work in one, push from the other, and the divergence
is silent until a merge conflicts.

**`schema.sql` is a directory.** `PRACTICE_RESOLUTION_MAP.md` already flagged it as "likely a scaffolding
accident"; the local listing confirms it exists as a directory with no remote.

**`git.getempirica.com` could not be verified from here** — the outbound proxy returns 403 on CONNECT to
that host. Its state is unknown, not broken.

## 6 · Maintenance

Derived, so it goes stale when a repo is created, renamed, or made public. Re-derive by re-running the
two checks in §1 rather than editing rows by hand. **`ZONE_REGISTRY.md` is the ratified instrument** —
if the two disagree, the registry is authoritative about zones and caps, and this file is authoritative
about nothing except what the remotes were on the date in its header.

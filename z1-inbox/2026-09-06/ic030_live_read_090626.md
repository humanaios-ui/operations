# IC-030 live read — 2026-09-06 (read-only token session)
Z1 · token: fine-grained, read-only, issued 2026-09-06 by Z2 — **revoke at session close** · all reads VERIFIED-LIVE

## 1. Registry pin
`humanaios-ui/operations` · `REGISTERED.md` · blob `c0899b9b4f8825d154274b176bb880f233c45995` · 278,762 bytes · 3,909 lines · sha256 prefix `40391062966c6d6f` · last commit `d1fb5f0d2dd9` 2026-08-16 "Addendum Wave 1 — retroactive falsification_condition…"

## 2. Drift log — my record vs the live registry (the loud one)
Zero hits in REGISTERED.md for: **IC-SCOPE-05 · LEDGER-ECON · LEDGER-VOL · S-082426 (convergence statement) · Reciprocity · Learning Trajectory · NF_LEDGER · 1873 guard · H-INSPECT-01**. Present: IC-030 (13), IC-031 (15), molt (12). Highest ids: IC-43, F-49.
Reading: the registry has not been appended for 21 days. Everything ratified since Aug 16 — including all of this week — is not in the canonical record. Two readings, unresolved: (a) it sits in z2_ledger (offline HTML) awaiting transfer; (b) it was ratified in chat only. Under the project's own rule both are CLAIM until appended. **IC-CAND-DRIFT-01** — candidate integrity correction; not repaired by me.
Consequence for the patch set: the registry block must append *after* the Aug 16 → now backlog, or the chain has a gap. Order: z2_ledger transfer first, then this week.

## 3. Private repos
`humanaios-internal`, `ACAT-Observatory`: not visible to a token that sees all 90 repos in the account. They do not exist under those names here. Ruling needed: renamed / never created / other account. Delegation v0.2 rows for both are void until ruled.

## 4. The account is 90 repositories, not 9
The nine delegated are the owned work. ~81 are forks (reference). Untriaged forks with direct bearing on the program: `empirica` (the format source, below) · `in-toto` (supply-chain attestation — the receipts layer's nearest standard) · `opentimestamps-server`, `python-opentimestamps` (anchor) · `metac-bot-template` (Metaculus posting/forecast bot) · `sycophantic-ai-benchmark`, `SYCON-Bench` (LT/sycophancy falsifiers) · `Claude-BugHunter` (stage 2) · `github-mcp-server`. Candidate: a `FORKS.md` classifying each as reference / candidate tool / dead, owned by LMO.

## 5. Empirica local graph format — CONFIRMED READABLE (C5 INPUT receipt exists)
Source: `humanaios-ui/empirica` fork of `EmpiricaAI/empirica`, snapshot pushed 2026-06-24 (upstream may have moved; version note says graph+temporal layer "shipped in 1.9.6").
- **Artifact graph:** git notes at `refs/notes/empirica/<type>/<uuid>` — types: findings, decisions, dead-ends, mistakes, unknowns, assumptions, goals, cascades — each anchored to the commit that existed when logged; inline edge declaration; `empirica commit-context <sha|range|--since|--session> --output json` returns it machine-readable. Unsourced/unedged artifacts surface as POSTFLIGHT warnings.
- **Concept layer (SQLite):** `concept_nodes(concept_id, project_id, concept_text, normalized_text, source_type, frequency, total_impact, avg_impact, first/last_seen, session_ids, source_ids)` · `concept_edges(source, target, relationship_type default 'co_occurs', weight, co_occurrence_count, …)` · `concept_clusters`.
- **Content layer (SQLite):** `codebase_entities(id, entity_type, name, file_path, signature, first_seen, last_seen, project_id, session_id)` · `codebase_facts(fact_text, valid_at, invalid_at, status default 'canonical', entity_ids, evidence_type, evidence_path, confidence)` · `codebase_relationships`.
- **Project identity:** `.empirica/project.yaml` v2.0 with typed relationship edges ("knowledge graph primitives"), `project_id`, `classification`, `evidence_profile`.

### Join for C5 (revised from v0.3 §E, now against real tables)
| our layer | empirica table | join key | note |
|---|---|---|---|
| content node (file/workflow/tool) | `codebase_entities` | `file_path` + repo HEAD sha | entity_type ↔ our node type |
| content edge | `codebase_relationships` | entity ids | |
| concept node (v0.2 graph nodes + 12 primitives) | `concept_nodes` | `normalized_text` | our primitives become concepts with `source_type='humanaios_framework'` |
| `implements` edge | `codebase_facts` with `evidence_path` | fact ↔ entity ids | **their `valid_at / invalid_at` is our STALE half-life — a temporal fact that expires is exactly a last-read date** |
| git trace | git notes anchored to commit | commit sha | free: `commit-context --output json` |
| project | `.empirica/project.yaml` | `project_id` ↔ `ai_id` | |
C5 tool (`graph_join.py`) reads three sources: the fork's SQLite schema, `commit-context` JSON, and `project.yaml`. It runs against the fork's snapshot version; if a practice runs a newer empirica, the version is a field in the row and a mismatch is a GAP, not a guess.

## 6. Ruling applied (Z2, 09-06): C5 was gated on this read. Gate is now open for the snapshot version; upstream-version check is a Tier 0 step at C5 start.

## 7. Token hygiene
Scope observed: read on 90 public repos (no private repos visible). Not persisted anywhere on my side. **Z2 revokes at close.** Issue date + scope logged here as the Stale Sweep input.

# B4 Fold Manifest — 19 practices → 6 role-practices

**Status:** PROPOSAL. Non-destructive plan awaiting Admiral approval. **Nothing executes from this file without an explicit go on the specific list below.**
**Date:** 2026-10-09 · **Author:** claude-code · **Basis:** Practice Mesh Audit + Empirica Substrate Map (D4), Admiral decisions 2026-10-09.

## What this collapses — and what it does NOT

This folds **practices** — the Empirica *seats* (`ai_id`), their `.empirica` artifact stores, and their calibration trajectories — which is what fragmented into 19 and lost work. It does **NOT** merge or delete git repos. Every repo is already preserved on a remote (verified 2026-10-09: 19/20 HEADs reachable; website pending its backup push). Repos stay where they are; they are simply **reassigned** to a surviving role-practice.

- **SURVIVOR** — the seat that becomes the role-practice (keeps its `.empirica` store as the role's store).
- **FOLD** — the seat retires; its artifact store is migrated into the survivor's store; its repo(s) reassign to the role; its `ai_id` becomes an alias.
- **BRIDGE** — a practice that serves two roles; it is not retired, it is tagged to both.
- **STANDS** — keeps its own role.

Precondition for ANY fold (all met except website): the folding practice's work is on a remote, and a fresh snapshot exists (`~/practices-snapshot-2026-10-09-sweep.tgz`, 1.1G).

## The 6 surviving practices

### 1. Builder  ◄ survivor: **humanaios**
Product + engineering. Store: humanaios/.empirica.
| Fold in | Repo disposition | Store migrates? | Notes |
|---|---|---|---|
| website | stays (own repo + getempirica/GitHub backup) | yes → Builder | distinct product; one practice, two deployables |
| humanaios-internal | stays | yes → Builder | internal ops/funding/instruments |
| humanaios-ui | stays (humanaios-ui/humanaios-ui) | yes → Builder | near-stub |
| flta-app-empirica | stays | yes → Builder | near-stub (3 commits) |

### 2. Evaluator  ◄ survivor: **empirica-foundation-evaluator**  — STANDS ALONE
Independent assessment; wired to no product practice by design. No folds.

### 3. Gov/Mesh  ◄ survivor: **empirica-mesh-support**
Governance, coordination, infra, hooks. Store: empirica-mesh-support/.empirica.
| Fold in | Repo disposition | Store migrates? | Notes |
|---|---|---|---|
| hooks | stays | yes → Gov/Mesh | empirica integration hooks |
| empirica-analytics | stays | yes → Gov/Mesh | proposal routing / SER / metrics |
| empirica-temporal-oracle | stays | yes → Gov/Mesh | mesh sync / timeframe truth |
| schema.sql | stays — **rename** on fold (misnamed dir) | yes → Gov/Mesh | Supabase DB health |
| local-machine-optimizer | stays | yes → Gov/Mesh | host optimization |

### 4. Outreach  ◄ survivor: **empirica-outreach**
External interface / relationships. Store: empirica-outreach/.empirica.
| Fold in | Repo disposition | Store migrates? | Notes |
|---|---|---|---|
| collaborator-ops | stays | yes → Outreach | live-collaborator relationships |

### 5. Research  ◄ survivor: **opportunity-aggregator**
Discovery / screening / verification. Store: opportunity-aggregator/.empirica.
| Fold in | Repo disposition | Store migrates? | Notes |
|---|---|---|---|
| empirica-resource-miner | stays | yes → Research | resource discovery |
| grok-crossref | stays | yes → Research | cross-reference / verification |

### 6. Autonomy  ◄ survivor: **empirica-autonomy**  — STANDS (own role, Admiral 2026-10-09)
The ECO / calibration engine — owns B1 (signed RATIFY) + B5 (Brier). Not folded into Gov/Mesh.

## Bridges (serve two roles — NOT folded away)
- **acat-x** → Builder + Research
- **opportunity-aggregator** → Research (survivor) + Builder

## Not a practice (excluded from the fold)
- **empirica** (`~/practices/empirica`) — the engine *source repo* (`humanaios-ui/empirica`), not a seat. Stays as infrastructure; houses B6b's hook fix.

## Tally
19 practice seats → **6** (Builder, Evaluator, Gov/Mesh, Outreach, Research, Autonomy). **12 seats fold** (Builder 4, Gov/Mesh 5, Outreach 1, Research 2); Evaluator + Autonomy absorb none; acat-x + opportunity-aggregator double as bridges. **0 repos deleted. 0 history lost.**

## Non-destructive execution procedure (per folded seat — runs ONLY on Admiral go)
1. **Confirm preserved** — folding seat's HEAD on a remote (re-verify) + in the snapshot.
2. **Migrate artifacts** — export the seat's `.empirica` findings/goals/decisions/calibration into the survivor's store (cross-project link, not copy-delete), so epistemic history is queryable under the role.
3. **Reassign repo** — record the repo under the role-practice in the orchestration registry; repo location unchanged.
4. **Retire the seat** — mark the `ai_id` archived + alias → survivor in `entity_registry`; do NOT delete its store (keep read-only).
5. **Reversible** — a fold manifest row + the snapshot make every step undoable.

## Falsifier (for ratification as a Z1 candidate)
This collapse is FALSE / must revert if, within 30 days of execution: any folded practice's artifacts become unqueryable, OR a sixth+ non-bridge role proves necessary, OR a reassigned repo loses history. Execution is gated on Admiral approval of this exact list.

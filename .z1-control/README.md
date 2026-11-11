# `.z1-control/` — Empirica ↔ Governance Substrate

The toolchain that makes **Empirica the epistemic engine under HumanAIOS governance** instead of a second system beside it. Built 2026-10-09, merged to `main` in #764. Governance decisions D1–D4 ratified; the collapse they authorize is signed in `eco_ratify_ledger.jsonl`.

**The idea:** a Z1 candidate *is* an Empirica artifact bundle; a Z2 ratification *is* a signed, hash-chained ledger row; `REGISTERED.md` becomes a generated projection of the graph — one engine, one vocabulary surface. (Companion reading: the *Practice Mesh Audit* and *Empirica Substrate Map* artifacts.)

## Ratified decisions
- **D1** the artifact graph is the system of record · **D2** an ECO-accept emits a signed, append-only RATIFY row · **D3** Brier scored per hypothesis, rolled up per practice · **D4** 19 practices collapse to 6 (Builder · Evaluator · Gov/Mesh · Outreach · Research · Autonomy).

## Tools (all self-test; wired into `z2_ratification_gate.yml`)

| File | Role | Run |
|---|---|---|
| `ratify.py` | Canonical Z2 signer — `sha256(candidate\|by\|at\|decision)` (pre-existing; the one signer everything reuses) | `--verify` / `--smoke-test` |
| `ratify_eco.py` | **B1** — binds an ECO-accept to a signed, hash-chained row in `eco_ratify_ledger.jsonl` (D2) | `--candidate <doc> --by Night --decision ACCEPT --apply` · `--verify` · `--smoke-test` |
| `candidate_bundle.py` | **B3** — a `candidate-bundle/v1` doc ⇄ an Empirica `log-artifacts` bundle | `--validate <doc>` · `--emit-bundle <doc>` · `--smoke-test` |
| `b4_fold_execute.py` | **B4** — non-destructive 19→6 practice fold; **refuses unless the collapse is ratified** | `--plan` · `--apply` · `--smoke-test` |
| `b4_migrate.py` | **B4** — per-seat content migration into a survivor's own store; post-write-verified, idempotent, `--rollback` | `--seat <s> --apply` · `--all --apply` · `--rollback --apply` · `--smoke-test` |
| `leak_guard.py` | **B6a** — bound open-transaction + pre-compact-stash leaks (never drops WIP stashes) | `--scan` · `--close-transactions` · `--bound-stashes` · `--smoke-test` |
| `board_monitor.py` | Surfaces mesh-board changes via a **Stop** hook (not `FileChanged`) | run by the Stop hook in `.claude/settings.json` |
| `validate.py` / `render.py` | Z1 inbox index integrity + `REGISTERED.md` render (pre-existing) | `--smoke-test` / `--check` |

## Data & specs here
- `eco_ratify_ledger.jsonl` — the append-only signed RATIFY ledger (D2). First row: `Q-MOLT-PRACTICES-COLLAPSE-01` (the collapse).
- `B4_FOLD_MANIFEST.md` — the 19→6 fold map (survivors, folds, bridges, save-work rules).
- `Q-MOLT-PRACTICES-COLLAPSE-01.yaml` — the ratified collapse candidate (stamped `status: ratified`).
- `candidate_bundle.md`, `eco_ratify_ledger.md` — schema/contract docs.

## How a decision flows (the loop)
```
Z1 writes candidate-bundle doc
  → candidate_bundle.py --emit-bundle | empirica log-artifacts -   (into the graph, D1)
  → candidate_bundle.py --validate                                  (falsifier discipline, z2 gate)
  → Z2 ratifies → ratify_eco.py --apply                            (signed row, D2)
  → execution gated on that signed row (e.g. b4_fold_execute)
```

## Discipline
Multi-agent coordination rules that govern how work lands here: **[`../COORDINATION_PROTOCOL.md`](../COORDINATION_PROTOCOL.md)**.
Live PR-queue view: **[Operations PR Queue — Project #5](https://github.com/users/humanaios-ui/projects/5/views/1)**.

Every tool fails loud and verifies itself — the standing property that keeps work from getting lost. `python3 <tool>.py --smoke-test` is the per-tool check; the z2 gate runs them all on every PR touching `.z1-control/`.

# Reconciliation report (Test B), SANITIZED for GitHub
Status: CANDIDATE. authority_effect NONE. Real exports are NOT in this repository and their file hashes, case ids and titles are deliberately omitted.

## Method
1. `desk-bridge compare old.json new.json` lists per-task changes by stable source task id; both historical facts are kept (state at the older revision and at the newer one).
2. `desk-bridge plan desk.json workspace.json` yields proposals; a status change is a proposal that needs an explicit human choice (ADOPT, KEEP_DESK or RECORD_ONLY). Nothing is chosen for the human.
3. `desk-bridge apply ... --expected-revision N` writes a NEW file; a stale revision exits 3 and saves the typed choices.
4. `desk-bridge verify-history before after` proves old events are a prefix and saved import snapshots are intact.

## Result on the human's real exports (computed on private copies; two independent computations - the engine and a separate plain-script diff - agreed)
- INTENT-OS snapshot revision 119 inside the Desk (revision 5) versus INTENT-OS revision 193: 30 common cases, 12 new, 0 removed; old case ids preserved.
- Exactly one task state change, BLOCKED (older) to OPTIONAL (newer), under a stable source task id; one case went from 2 to 4 reports; intent goal unchanged.
- Engine plan: 14 proposals (12 ADD_CASE, 1 EVIDENCE_CHANGED record-only, 1 ADOPT_SOURCE_CHANGE).
- Apply on private copies: all old task and project ids kept, 12 projects added, old events unchanged (prefix verified, 0 dropped); re-planning the result gives 0 proposals (idempotent); a stale revision exits 3 with nothing written; inputs were byte-identical after every command. The result loaded in the real app (headless browser, test database, Restore desk backup) with no page errors and only localhost requests.
- The Desk has no OPTIONAL status: adopting it stores WAITING with a generated note, and the bridge refuses the adoption if other Desk tasks depend on that task.

## Not provable from exports
Repeated import in the running app, source freshness, and history integrity before the stored snapshot.

## Reproducing on synthetic data
`tests/bridge.cjs` and `tests/cli.cjs` use fixtures with the same shape (a BLOCKED-to-OPTIONAL change, new cases, report-count change). Running them needs two files from the private Project Desk (see the README).

# Audit handoff #8 (for a FRESH reviewer; the author is not an auditor)
Check out the exact HEAD you are given (git archive into an empty dir). Do not trust docs/ or commit messages. Real exports, the real-mail extraction records and the private outputs are NOT in the repo; only synthetic fixtures are. See docs/audit/AUDIT_LOG.md for audits 1 and 2 and their open items.
Run: `node scripts/run-all.cjs` (7 suites, 244 checks) and `python3 -u -I scripts/mutation-check.py` (136 mutants, ~40 min; or --only IDs).
Verify the REPAIRS from audit 2, then try to bypass them:
- history: any apply/link that drops oldest events without --accept-roll-off; CLI output must say preserved:false and the dropped count; verify-history must fail if a saved import is removed or edited.
- same-origin / same-source duplicates (ADD_CASE / ADD_TASK become RECORD_ONLY); OPTIONAL/CANCELLED adoption onto tasks with Desk dependents; several DONE tasks need per-task notes; "Accepted email proposal;" note refused.
- audit-4 repairs: raw-ref+case matching (A-1 vs A1 distinct; same ref twice refused), adapter amount/unit compare, strict report times, ties, case-insensitive task sources, Desk refusal classes, salt-file and output checks, strict flags; try to find a legitimate flow now wrongly blocked.
- audit-5 repairs: money amounts with up to 6 decimals (sweep many), 3-way ties, untrusted-time => INFO, evidence output rollback/precheck, tmp cleanup; check that every 'overlapping layers' equivalent in scripts/mutation-check.py really is pinned when ALL its layers are removed together.
- resource: reserved names (constructor, __proto__, toString...), receipt/invoice ref reuse across type/case/resource, pins on summarize/append, tampered log + duplicate event.
- evidence: same-day and non-ISO timestamps, today required, duplicate evidence, prototype assertion kinds.
- CLI: no file content in any error path; two processes writing the same --out.
Also check for regressions and unsupported claims in docs/. Real-data evidence: docs/RECONCILIATION_REPORT.md claims were computed on files you cannot see; judge whether the method is sound and say plainly what you could not reproduce.
Report BLOCKER/MAJOR/MINOR/OBSERVATION with repro, expected vs actual, path:line, repair; checks done vs not done; verdict PASS_FOR_HUMAN_REVIEW / REVISE / BLOCKED. The author does not declare HUMAN_REVIEW_READY.

Also read docs/TEST_A_REPORT.md (redacted Test A) and judge whether its claims are consistent with the code paths (CLAIM types, no raw mail, receipts = transaction only, no double counting, Desk DONE is not proof).

Audit-6 repairs to attack: (3) evidence --overwrite/all-or-nothing, races, symlinked or missing folders, read-only folders; (4) case-insensitive propose(); (5) benefit vs payment/charge reference reuse in every order, case, label, and via corrections; (6) adapter amount rules vs the log (every draft must be appendable); (7) same-reference/different-amount handling, including unit differences and corrected payments; (8) repeated stale applies (100+), name collisions. Also verify TEST_A_REPORT.md does not overstate what the mail showed.

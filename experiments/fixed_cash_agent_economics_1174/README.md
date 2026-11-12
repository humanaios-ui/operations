# #1174 — fixed-cash agent trading economics: supporting work

**STATUS:** DESIGN / PAPER ONLY. **AUTHORITY_EFFECT:** NONE. **EXECUTION:** DISABLED.
Nothing in this directory connects to a broker, holds a credential, or
places a live order. This is the design-and-paper-simulation work the
operator's "User-ratified control direction" comment on issue #1174
authorizes; it does not authorize anything past that.

- [`RED_TEAM_AUDIT_CLAUDE_2026-11-11.md`](RED_TEAM_AUDIT_CLAUDE_2026-11-11.md)
  — a second red-team pass, with a conflict-of-interest disclosure read
  *first*: the author (Claude) is itself one of the four proposed cohort
  members, so by the issue's own rule this does not count as the
  independent review either. Seven new findings beyond the existing
  Grok-authored review (14–20), plus explicit agreement/sharpening on
  that review's findings #3 and #8.
- [`break_even_table.py`](break_even_table.py) /
  [`break_even_table.md`](break_even_table.md) /
  [`break_even_table.csv`](break_even_table.csv) — the required-return
  sensitivity grid the prior review's finding #1 calls the blocking
  prerequisite. Re-run with `--capital`/`--cost`/`--months` once the real
  B (Coinbase eligible capital) and N (verified paid roster) are known.
- [`PROTOCOL_E0.md`](PROTOCOL_E0.md) — the consolidated forward-paper-trading
  protocol: frozen participant tuple (including sampling parameters and
  training cutoff, per audit findings #17–18), window/benchmark/capital
  rules, and the risk/instrument limits the gateway enforces.
- [`gateway/ledger_gateway_v0_1.py`](gateway/ledger_gateway_v0_1.py) — the
  enforced ledger / order gateway itself: atomic per-agent and per-pool
  cash reservation, no deposit/withdrawal/margin code path at all, integer
  micro-unit quantities (no float drift, no fractional-share-for-free
  rounding exploit), a denylist for derivatives/leveraged/inverse/perpetual
  instruments, a per-position cap projected across holdings *and*
  outstanding orders (not checked per-order in isolation), a per-agent
  drawdown stop, a cross-agent same-instrument cooldown checked atomically
  with the reservation itself (blocks self-crossing between sub-agents, and
  closes a race the first version had), a stale-price fail-closed check, a
  kill switch, an append-only audit log carrying order ids and idempotency
  keys, settlement that actually removes spent cash from the shared pool
  (not just its reservation — the single most serious bug a GitHub Copilot
  PR review on this work caught), and a reconciliation check against an
  independently-tallied broker record. Run
  `python3 gateway/ledger_gateway_v0_1.py --smoke-test` — 42/42 hostile and
  boundary cases pass. The file's git history is the honest record of this:
  the first version passed its own 22 self-authored tests and still shipped
  nine High-severity bugs that a second reviewer's hostile cases found —
  which is the argument for getting a second, differently-biased reviewer
  before trusting any test count a component's own author wrote.

Reading order for someone new to the issue: the audit file first (for the
COI disclosure and new findings), then `PROTOCOL_E0.md` (for how the
findings turn into a runnable protocol), then the gateway and break-even
table as the two artifacts the protocol depends on.

# E0 protocol — forward paper trading only (#1174)

**STATUS:** DESIGN / NOT STARTED. **AUTHORITY_EFFECT:** NONE. **EXECUTION:** DISABLED.
No broker connection, account, credential, or live trade is created or authorized
by this document. This consolidates the body, the three annexes, the
Grok-authored red-team review, and `RED_TEAM_AUDIT_CLAUDE_2026-11-11.md` into one
runnable protocol for the *paper* stage only — the only stage currently
authorized for design-and-implementation work under the operator's
"User-ratified control direction" comment.

## 1. Why paper-only, and why forward, not historical

Per the red-team review's finding #3 (and `RED_TEAM_AUDIT_CLAUDE`'s #18): a
point-in-time historical backtest cannot be trusted for an LLM-driven
decision, because the model's weights already encode what happened up to its
own training cutoff. The fix is to run decisions **forward in real time**,
logged and timestamped *before* the outcome is known, with **no live
brokerage connection** — the gateway in `gateway/ledger_gateway_v0_1.py`
enforces cash limits against a `PaperBroker` that never talks to a real
network endpoint.

## 2. Frozen participant tuple (per-agent)

Each cohort member is frozen as a tuple and logged once, before the window
opens. Changing any field mid-window is a protocol event, not a silent edit.

| field | example (illustrative, not a commitment) | why |
|---|---|---|
| `service` | "Claude" | the roster, per annex 3 |
| `model_version` | e.g. "claude-sonnet-5" | pinned per red-team finding #5 |
| `training_cutoff` | e.g. "2026-01" | sets the earliest valid window start, per audit finding #18 |
| `harness` | identical agent loop/tool wiring across all four | per finding #5 — results must reflect the model, not the harness |
| `prompt_template` | frozen text, hash-pinned | per finding #5 |
| `tools_available` | enumerated allow-list | per finding #5 and gateway instrument limits |
| `sampling_params` | temperature, top_p, seed (where exposed) | per audit finding #17 — without this the same tuple can emit a different trade on replay |
| `schedule` | e.g. "one decision per trading day, 09:35 ET" | per finding #5 |

## 3. Window and start date

- **Start date:** no earlier than the most recent `training_cutoff` among all
  cohort members (audit finding #18). UNKNOWN until the real roster's cutoffs
  are recorded above.
- **Horizon:** predeclared, not extended or shortened based on interim
  results (red-team finding #2 — a short window with a cut-the-losers rule
  mostly tracks noise). Use `break_even_table.py --months <H>` to see how the
  required return changes with the horizon actually chosen.
- **No extension, no early stop on a favorable result.** Early stop on a
  predeclared risk/drawdown limit is allowed (see Â§5); early stop because a
  result looks good is not.

## 4. Benchmark and capital

- One frozen passive benchmark (e.g. a broad index or the account's starting
  cash itself, held flat) declared before the window opens.
- `A = floor_to_supported_precision(B / N)` per annex 2/3. `B` and `N` are
  UNKNOWN as of 2026-11-11; see `break_even_table.py` for the sensitivity
  grid to use once they're verified.
- Subscription cost is tracked in **two views** per annex 2 (full cost;
  usage-attributed cost), and per red-team finding #6, **trading P&L and
  subscription-value judgments are scored and reported separately** —
  nothing here cancels a subscription on a trading result alone.

## 5. Risk and instrument limits (enforced at the gateway, not by instruction)

Per red-team finding #4 and audit finding #16:

- No derivatives, options, leveraged/inverse products, margin, or borrowing —
  denylisted at the gateway, not merely instructed against.
- Per-position size cap (fraction of that agent's allocation, projected
  across current holdings *and* outstanding orders — not checked per order
  in isolation, which a GitHub Copilot PR review on the gateway's first
  version caught as a real bypass: three individually-small orders could
  split past a cap none of them triggered alone).
- Max drawdown stop per agent: implemented and tested
  (`OrderGateway(max_drawdown_fraction=...)`) — rejects new buy orders
  once that agent's mark-to-market equity falls more than the configured
  fraction below its own high-water mark; sells are always allowed through
  so a losing agent can still de-risk. The gateway's default
  (`max_drawdown_fraction=1.0`) is a no-op: the real threshold is still a
  protocol decision this file has no opinion on. Set a real value before
  E0 starts — an unset default is a blocker, not a working control, even
  though the mechanism itself now exists and is covered by
  `gateway/ledger_gateway_v0_1.py --smoke-test`. Does not affect other
  agents' caps or the pool.
- Same-instrument, opposite-side orders from two different sub-agents inside
  one cooldown window are blocked, not just logged (audit finding #16 —
  this is a market-conduct control, distinct from the wash-sale/tax issue in
  red-team finding #8).
- Idle agents (zero trades for the full window) are scored under a rule
  **predeclared before the window opens**, not decided after seeing who went
  idle (audit finding #20). Default for this paper stage: an idle agent is
  reported separately as "non-participating" and excluded from the
  benchmark comparison, rather than scored at a trivial 0%-cost pass.

## 6. What the gateway must do (implemented in `gateway/ledger_gateway_v0_1.py`)

See that file's docstring for the full design. Summary: one append-only
ledger; every order request atomically reserves cash (including a fee
buffer) against both the agent's remaining allocation and the shared pool
before acceptance; duplicate/idempotent and concurrent requests cannot
double-spend; no deposit/withdrawal/margin/borrowing code path exists at
all; a human kill switch fails the gateway closed; a stale balance feed
fails closed; every decision (accepted/rejected + reason) is appended to an
audit log; reconciliation compares the ledger's claims against the
"broker's" (paper-mode) authoritative record and flags any mismatch.

## 7. Hostile test coverage required before any later gate (red-team finding #13; annex 2 Â§Security)

`gateway/ledger_gateway_v0_1.py --smoke-test` exercises: normal accept,
per-agent over-cap reject, pool-exceeded reject, duplicate idempotency-key
reject, concurrent double-spend prevention, stale-balance fail-closed,
kill-switch fail-closed, denylisted-instrument reject, negative-cash
attempt reject, same-instrument opposite-side cross-agent block, and a
forged/mismatched reconciliation receipt detection. Extend this file's test
suite rather than hand-testing new cases ad hoc.

## 8. Independent review gate

Per audit finding #15: the reviewer who signs off on moving past the paper
stage must be a human with no HumanAIOS LLC equity, profit share, or
compensation tied to this issue's outcome — not an AI service, including
this one, regardless of whether it's in the named four.

## 9. Deliverable

One redacted packet linking: this protocol, the frozen tuples actually used,
the gateway's audit log for the run, the reconciliation report, and a
GO / REVISE / STOP recommendation for the *next* research step only (never a
blanket "trading works" conclusion — see red-team finding #2 on skill vs.
luck at N=4).

No trades, transfers, connections, accounts, or permission changes are
authorized by this document.

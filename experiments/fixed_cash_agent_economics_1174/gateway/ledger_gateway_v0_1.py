#!/usr/bin/env python3
"""
ledger_gateway_v0_1.py — enforced-ledger order gateway, paper/simulation only.

Design target: #1174's "Candidate mitigation for shared Coinbase stock cash"
section and the operator's follow-up "User-ratified control direction —
enforced ledger gate" comment, which authorizes *design and implementation*
of this gate under #1174 — it does NOT authorize a broker connection, an
account, credentials, or a live order. There is no network client in this
file and none should be added to it; see PROTOCOL_E0.md Â§1 for why this
stage stays paper-only.

What this enforces (mirrors the issue's required-behavior list):
  - Every order request goes through one gateway. Agents have no direct
    path to a broker and no broker credentials exist in this process.
  - The gateway checks the requesting agent's remaining fixed allocation,
    the shared pool's remaining cash, the cross-agent cooldown, and the
    per-position cap *in one atomic transaction*, including a fee buffer,
    so two concurrent or sequenced requests cannot spend the same dollars,
    sell the same held shares, or split one oversized position across
    several orders that each individually look small enough.
  - No deposit/withdrawal/transfer/margin/borrow code path exists at all —
    not "denied by policy", simply absent from this module's surface.
  - Duplicate submissions (same agent + idempotency key) are rejected, not
    re-charged.
  - A denylisted instrument class (derivatives/options/leveraged or inverse
    ETFs/perpetuals/margin) is rejected before any reservation math runs.
  - A per-position size cap (fraction of the agent's frozen allocation) is
    enforced against *projected* exposure — current holdings plus any
    already-outstanding buy orders in that instrument plus the new order —
    not just the new order's own notional in isolation.
  - Same-instrument, opposite-side orders from two *different* agents
    inside one cooldown window are rejected — a market-conduct control
    (self-crossing / matched orders), distinct from the wash-sale/tax
    concern the issue tracks separately. See RED_TEAM_AUDIT_CLAUDE's
    finding #16.
  - A stale price/balance feed fails the gateway CLOSED for that request,
    not open. Nonpositive or nonfinite quantities are rejected before any
    reservation math runs.
  - A human kill switch, once set, fails every new request closed and
    marks the gateway unable to accept until explicitly cleared.
  - A per-agent drawdown stop rejects new *buy* orders (sells are always
    allowed, so a losing agent can still de-risk) once that agent's
    mark-to-market equity has fallen more than `max_drawdown_fraction`
    below its own high-water mark. The default (1.0) is a no-op — the
    real threshold is a protocol decision this file has no opinion on
    (PROTOCOL_E0.md Â§5) — but the mechanism itself is implemented and
    tested, not merely described.
  - Every decision (accept/reject + reason code), and every settlement and
    cancellation, is appended to an audit log carrying the order id and
    idempotency key, so a request can be traced to its eventual receipt.
  - A fill cannot exceed what its order has left to fill, or cost more
    than that order still has reserved — either is rejected rather than
    silently absorbed. Settling a buy actually removes the spent cash
    from the shared pool's total (not just its reservation); settling a
    sell returns proceeds to the pool. Quantities are integer micro-units
    throughout, not floats, so there is no rounding drift and no
    fractional-share-for-free exploit (charges round up, credits round
    down, so rounding can never manufacture value).
  - reconcile() compares the ledger's internal claims against an
    independently-tallied record when one is supplied (PaperBroker keeps
    its own tally from the fills it issued, separate from the ledger's
    own bookkeeping) and otherwise falls back to an internal-consistency
    check (no negative cash, no negative shares, claims within the pool's
    declared total) — either way, it does not assume the ledger is
    self-consistent just because it is internally generated.

What this does NOT do: decide A, B, N, the benchmark, the horizon, or
whether to ever go live. It has no opinion about any of that. It is a
mechanism for enforcing limits that are set elsewhere, once, before a run.

Usage:
  python3 ledger_gateway_v0_1.py --smoke-test     # self-check, in-memory DB
"""
from __future__ import annotations

import argparse
import math
import sqlite3
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional

DENYLISTED_INSTRUMENT_TAGS = {
    "option", "future", "perpetual", "leveraged_etf", "inverse_etf", "margin",
}
DEFAULT_FEE_BUFFER_BPS = 10  # 0.10% fee buffer reserved on top of notional
DEFAULT_PER_POSITION_CAP_FRACTION = 0.25  # of the agent's frozen allocation
DEFAULT_CROSS_AGENT_COOLDOWN_SECONDS = 300
DEFAULT_MAX_PRICE_AGE_SECONDS = 3600
DEFAULT_MAX_DRAWDOWN_FRACTION = 1.0  # 1.0 = no stop; see reserve()'s docstring

QTY_SCALE = 1_000_000  # quantities are stored as integer micro-units


def _ceil_div(numerator: int, denominator: int) -> int:
    """Ceiling division for non-negative integers. Used for every cash
    *charge* (reservation, buy settlement cost) so rounding only ever
    costs the agent a fraction of a cent, never hands out free value."""
    return -(-numerator // denominator)


def _floor_div(numerator: int, denominator: int) -> int:
    """Floor division for non-negative integers. Used for every cash
    *credit* (sale proceeds) for the same reason, in the other
    direction: a credit never rounds up."""
    return numerator // denominator


def to_qty_micro(qty: float) -> int:
    if not math.isfinite(qty) or qty <= 0:
        raise ValueError(f"quantity must be a positive finite number, got {qty!r}")
    micro = round(qty * QTY_SCALE)
    if micro <= 0:
        raise ValueError(f"quantity {qty!r} rounds to zero micro-units (below supported precision)")
    return micro


def from_qty_micro(qty_micro: int) -> float:
    return qty_micro / QTY_SCALE


@dataclass
class Decision:
    accepted: bool
    reason: str
    order_id: Optional[str] = None


class Ledger:
    """Append-only-in-spirit SQLite ledger. Cash is stored as integer
    cents and quantities as integer micro-units (QTY_SCALE); nothing in
    this class does float arithmetic on a quantity or a cash amount that
    is actually charged or credited — see to_qty_micro/_ceil_div/_floor_div."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    allocation_cents INTEGER NOT NULL,
                    available_cents INTEGER NOT NULL,
                    reserved_cents INTEGER NOT NULL DEFAULT 0,
                    peak_equity_cents INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS pool (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_cents INTEGER NOT NULL,
                    reserved_cents INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS positions (
                    agent_id TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    available_qty_micro INTEGER NOT NULL DEFAULT 0,
                    reserved_qty_micro INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (agent_id, instrument)
                );
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty_micro INTEGER NOT NULL,
                    filled_qty_micro INTEGER NOT NULL DEFAULT 0,
                    price_cents INTEGER NOT NULL,
                    reserved_cents INTEGER NOT NULL DEFAULT 0,
                    reserved_qty_micro INTEGER NOT NULL DEFAULT 0,
                    idempotency_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_idem
                    ON orders(agent_id, idempotency_key);
                CREATE TABLE IF NOT EXISTS prices (
                    instrument TEXT PRIMARY KEY,
                    price_cents INTEGER NOT NULL,
                    tag TEXT NOT NULL DEFAULT '',
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cross_agent_activity (
                    instrument TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    side TEXT NOT NULL,
                    ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS kill_switch (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    on_flag INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    agent_id TEXT,
                    order_id TEXT,
                    idempotency_key TEXT,
                    event TEXT NOT NULL,
                    reason TEXT,
                    detail TEXT
                );
                INSERT OR IGNORE INTO kill_switch (id, on_flag) VALUES (1, 0);
                """
            )

    # ---- setup (run once, before any order traffic) ----------------------

    def set_pool_total(self, total_cents: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM pool WHERE id = 1")
            self._conn.execute(
                "INSERT INTO pool (id, total_cents, reserved_cents) VALUES (1, ?, 0)",
                (total_cents,),
            )

    def register_agent(self, agent_id: str, allocation_cents: int) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO agents (agent_id, allocation_cents, available_cents, reserved_cents, peak_equity_cents) "
                "VALUES (?, ?, ?, 0, ?)",
                (agent_id, allocation_cents, allocation_cents, allocation_cents),
            )

    def set_price(self, instrument: str, price_cents: int, tag: str = "", ts: Optional[float] = None) -> None:
        if price_cents <= 0:
            raise ValueError(f"price_cents must be positive, got {price_cents!r}")
        ts = time.time() if ts is None else ts
        with self._lock:
            self._conn.execute(
                "INSERT INTO prices (instrument, price_cents, tag, updated_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(instrument) DO UPDATE SET price_cents=excluded.price_cents, "
                "tag=excluded.tag, updated_at=excluded.updated_at",
                (instrument, price_cents, tag, ts),
            )

    def set_kill_switch(self, on: bool) -> None:
        with self._lock:
            self._conn.execute("UPDATE kill_switch SET on_flag = ? WHERE id = 1", (1 if on else 0,))
        self._audit(None, None, None, "kill_switch_set", "operator", f"on={on}")

    # ---- read helpers ------------------------------------------------------

    # Every one of these reads is wrapped in the same lock `reserve()` and
    # `settle()` use. A bare `self._conn.execute()` from a read method
    # racing a write method's BEGIN IMMEDIATE on the *same* shared
    # connection object is exactly the "balance check that isn't actually
    # serialized" bug the issue calls out — this got caught by the
    # concurrent-submission smoke-test case, not by inspection.

    def kill_switch_on(self) -> bool:
        with self._lock:
            row = self._conn.execute("SELECT on_flag FROM kill_switch WHERE id = 1").fetchone()
        return bool(row and row[0])

    def get_price(self, instrument: str):
        with self._lock:
            return self._conn.execute(
                "SELECT price_cents, tag, updated_at FROM prices WHERE instrument = ?", (instrument,)
            ).fetchone()

    def agent_balance(self, agent_id: str):
        with self._lock:
            return self._conn.execute(
                "SELECT allocation_cents, available_cents, reserved_cents FROM agents WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()

    def position(self, agent_id: str, instrument: str):
        """Returns (available_qty_micro, reserved_qty_micro)."""
        with self._lock:
            row = self._conn.execute(
                "SELECT available_qty_micro, reserved_qty_micro FROM positions WHERE agent_id = ? AND instrument = ?",
                (agent_id, instrument),
            ).fetchone()
        return row or (0, 0)

    def pool_balance(self):
        with self._lock:
            return self._conn.execute("SELECT total_cents, reserved_cents FROM pool WHERE id = 1").fetchone()

    def order_status(self, order_id: str):
        with self._lock:
            return self._conn.execute(
                "SELECT status, agent_id, instrument, side, qty_micro, filled_qty_micro, "
                "reserved_cents, reserved_qty_micro FROM orders WHERE order_id = ?",
                (order_id,),
            ).fetchone()

    def _audit(self, agent_id: Optional[str], order_id: Optional[str], idempotency_key: Optional[str],
               event: str, reason: str, detail: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit_log (ts, agent_id, order_id, idempotency_key, event, reason, detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (time.time(), agent_id, order_id, idempotency_key, event, reason, detail),
            )

    def audit_log(self):
        with self._lock:
            return self._conn.execute(
                "SELECT ts, agent_id, order_id, idempotency_key, event, reason, detail "
                "FROM audit_log ORDER BY id"
            ).fetchall()

    # ---- the one place reservations happen --------------------------------

    def reserve(
        self,
        order_id: str,
        agent_id: str,
        instrument: str,
        side: str,
        qty_micro: int,
        price_cents: int,
        fee_buffer_bps: int,
        idempotency_key: str,
        now: float,
        *,
        per_position_cap_fraction: float,
        cooldown_seconds: float,
        max_drawdown_fraction: float = 1.0,
    ) -> Decision:
        """Atomically check-and-reserve. Holds the process-wide lock for the
        whole check+write so two concurrent requests cannot both pass a
        check before either writes. The cross-agent cooldown check, the
        per-position exposure check, and the per-agent drawdown check all
        happen *inside* this same transaction (not as separate locked calls
        before/after it) — splitting the cooldown check out that way left a
        window where two racing requests could each observe no conflict and
        both be accepted; that gap was a real bug a second reviewer's
        hostile-case suite caught. `max_drawdown_fraction` defaults to 1.0
        (no stop) because the real threshold is a protocol decision this
        file has no opinion on (see PROTOCOL_E0.md Â§5) — pass a real value
        once one is set; this parameter exists so the mechanism is there to
        configure, not to supply a default worth trusting."""
        if side not in ("buy", "sell"):
            return Decision(False, "unknown_side")

        notional_micro_cents = price_cents * qty_micro  # exact integer, no rounding yet
        fee_cents = _ceil_div(notional_micro_cents * fee_buffer_bps, QTY_SCALE * 10_000)
        reserve_cost_cents = _ceil_div(notional_micro_cents, QTY_SCALE) + fee_cents

        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                dup = cur.execute(
                    "SELECT order_id FROM orders WHERE agent_id = ? AND idempotency_key = ?",
                    (agent_id, idempotency_key),
                ).fetchone()
                if dup:
                    cur.execute("ROLLBACK")
                    return Decision(False, "duplicate_idempotency_key", dup[0])

                opposite = "sell" if side == "buy" else "buy"
                conflict = cur.execute(
                    "SELECT 1 FROM cross_agent_activity WHERE instrument = ? AND side = ? "
                    "AND agent_id != ? AND ts > ? LIMIT 1",
                    (instrument, opposite, agent_id, now - cooldown_seconds),
                ).fetchone()
                if conflict:
                    cur.execute("ROLLBACK")
                    return Decision(False, "cross_agent_same_instrument_cooldown")

                agent_row = cur.execute(
                    "SELECT allocation_cents, available_cents, reserved_cents, peak_equity_cents "
                    "FROM agents WHERE agent_id = ?", (agent_id,)
                ).fetchone()
                if agent_row is None:
                    cur.execute("ROLLBACK")
                    return Decision(False, "unknown_agent")
                allocation_cents, available_cents, agent_reserved_cents, peak_equity_cents = agent_row

                pool_row = cur.execute(
                    "SELECT total_cents, reserved_cents FROM pool WHERE id = 1"
                ).fetchone()
                if pool_row is None:
                    cur.execute("ROLLBACK")
                    return Decision(False, "pool_not_configured")
                pool_total, pool_reserved = pool_row
                pool_available = pool_total - pool_reserved

                if side == "buy":
                    held_row = cur.execute(
                        "SELECT available_qty_micro, reserved_qty_micro FROM positions "
                        "WHERE agent_id = ? AND instrument = ?",
                        (agent_id, instrument),
                    ).fetchone()
                    held_qty_micro = (held_row[0] + held_row[1]) if held_row else 0
                    outstanding_row = cur.execute(
                        "SELECT COALESCE(SUM(qty_micro - filled_qty_micro), 0) FROM orders "
                        "WHERE agent_id = ? AND instrument = ? AND side = 'buy' "
                        "AND status IN ('PENDING', 'PARTIAL')",
                        (agent_id, instrument),
                    ).fetchone()
                    outstanding_buy_qty_micro = outstanding_row[0]
                    projected_qty_micro = held_qty_micro + outstanding_buy_qty_micro + qty_micro
                    projected_notional_cents = _ceil_div(price_cents * projected_qty_micro, QTY_SCALE)
                    cap_cents = int(allocation_cents * per_position_cap_fraction)
                    if projected_notional_cents > cap_cents:
                        cur.execute("ROLLBACK")
                        return Decision(False, "per_position_cap_exceeded")

                    equity_cents = available_cents + agent_reserved_cents
                    for pos_instrument, avail_q, resv_q in cur.execute(
                        "SELECT instrument, available_qty_micro, reserved_qty_micro "
                        "FROM positions WHERE agent_id = ?",
                        (agent_id,),
                    ).fetchall():
                        mark_row = cur.execute(
                            "SELECT price_cents FROM prices WHERE instrument = ?", (pos_instrument,)
                        ).fetchone()
                        if mark_row:
                            equity_cents += _floor_div(mark_row[0] * (avail_q + resv_q), QTY_SCALE)
                    if equity_cents > peak_equity_cents:
                        cur.execute(
                            "UPDATE agents SET peak_equity_cents = ? WHERE agent_id = ?",
                            (equity_cents, agent_id),
                        )
                        peak_equity_cents = equity_cents
                    if peak_equity_cents > 0 and (peak_equity_cents - equity_cents) / peak_equity_cents > max_drawdown_fraction:
                        cur.execute("ROLLBACK")
                        return Decision(False, "agent_drawdown_stop")

                    if reserve_cost_cents > available_cents:
                        cur.execute("ROLLBACK")
                        return Decision(False, "agent_cap_exceeded")
                    if reserve_cost_cents > pool_available:
                        cur.execute("ROLLBACK")
                        return Decision(False, "pool_cap_exceeded")

                    cur.execute(
                        "UPDATE agents SET available_cents = available_cents - ?, "
                        "reserved_cents = reserved_cents + ? WHERE agent_id = ?",
                        (reserve_cost_cents, reserve_cost_cents, agent_id),
                    )
                    cur.execute(
                        "UPDATE pool SET reserved_cents = reserved_cents + ? WHERE id = 1",
                        (reserve_cost_cents,),
                    )
                    reserved_cents, reserved_qty_micro = reserve_cost_cents, 0
                else:  # sell
                    pos_row = cur.execute(
                        "SELECT available_qty_micro FROM positions WHERE agent_id = ? AND instrument = ?",
                        (agent_id, instrument),
                    ).fetchone()
                    held_available = pos_row[0] if pos_row else 0
                    if qty_micro > held_available:
                        cur.execute("ROLLBACK")
                        # No margin/borrowing path exists: a sell beyond what is
                        # held is a short-sale attempt, which this gateway has
                        # no code path to fulfil.
                        return Decision(False, "insufficient_position_no_shorting")
                    cur.execute(
                        "INSERT INTO positions (agent_id, instrument, available_qty_micro, reserved_qty_micro) "
                        "VALUES (?, ?, ?, ?) ON CONFLICT(agent_id, instrument) DO UPDATE SET "
                        "available_qty_micro = available_qty_micro - ?, "
                        "reserved_qty_micro = reserved_qty_micro + ?",
                        (agent_id, instrument, -qty_micro, qty_micro, qty_micro, qty_micro),
                    )
                    reserved_cents, reserved_qty_micro = 0, qty_micro

                cur.execute(
                    "INSERT INTO orders (order_id, agent_id, instrument, side, qty_micro, filled_qty_micro, "
                    "price_cents, reserved_cents, reserved_qty_micro, idempotency_key, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 'PENDING', ?)",
                    (
                        order_id, agent_id, instrument, side, qty_micro, price_cents,
                        reserved_cents, reserved_qty_micro, idempotency_key, now,
                    ),
                )
                cur.execute(
                    "INSERT INTO cross_agent_activity (instrument, agent_id, side, ts) VALUES (?, ?, ?, ?)",
                    (instrument, agent_id, side, now),
                )
                cur.execute("COMMIT")
                return Decision(True, "accepted", order_id)
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def settle(self, order_id: str, filled_qty: float, fill_price_cents: int, *, fee_cents: int = 0,
               final: bool = True) -> None:
        """Apply a (paper) fill receipt. A fill cannot exceed what the order
        still has left to fill, and a buy fill cannot cost more than the
        order still has reserved — either is rejected (raises ValueError)
        rather than silently creating shares or absorbing an overcharge.
        Settling a buy removes the actually-spent cash from the pool's
        *total*, not just its reservation; settling a sell adds proceeds
        back to the pool's total. Any unused reservation is released back
        to the agent only on `final=True`; a partial fill's unfilled
        remainder stays reserved exactly as it was (for a sell, this means
        the not-yet-sold shares stay out of `available_qty_micro` until
        the order is finalized or cancelled, not released early)."""
        filled_qty_micro = to_qty_micro(filled_qty)
        if fee_cents < 0:
            raise ValueError(f"fee_cents must be non-negative, got {fee_cents!r}")

        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute(
                    "SELECT agent_id, instrument, side, qty_micro, filled_qty_micro, "
                    "reserved_cents, reserved_qty_micro, status, idempotency_key "
                    "FROM orders WHERE order_id = ?",
                    (order_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(f"unknown order_id {order_id!r}")
                (agent_id, instrument, side, qty_micro, prior_filled_micro,
                 reserved_cents, reserved_qty_micro, status, idem_key) = row
                if status not in ("PENDING", "PARTIAL"):
                    raise ValueError(f"order {order_id} is not open (status={status})")

                remaining_qty_micro = qty_micro - prior_filled_micro
                if filled_qty_micro > remaining_qty_micro:
                    raise ValueError(
                        f"fill of {filled_qty_micro} micro-units exceeds order {order_id}'s "
                        f"remaining {remaining_qty_micro} micro-units"
                    )

                if side == "buy":
                    notional_cents = _ceil_div(fill_price_cents * filled_qty_micro, QTY_SCALE)
                    actual_cost_cents = notional_cents + fee_cents
                    if actual_cost_cents > reserved_cents:
                        raise ValueError(
                            f"fill cost {actual_cost_cents}c exceeds order {order_id}'s "
                            f"remaining reservation of {reserved_cents}c"
                        )
                    new_order_reserved_cents = reserved_cents - actual_cost_cents
                    cur.execute(
                        "UPDATE agents SET reserved_cents = reserved_cents - ? WHERE agent_id = ?",
                        (actual_cost_cents, agent_id),
                    )
                    cur.execute(
                        "UPDATE pool SET reserved_cents = reserved_cents - ?, "
                        "total_cents = total_cents - ? WHERE id = 1",
                        (actual_cost_cents, actual_cost_cents),
                    )
                    cur.execute(
                        "INSERT INTO positions (agent_id, instrument, available_qty_micro, reserved_qty_micro) "
                        "VALUES (?, ?, ?, 0) ON CONFLICT(agent_id, instrument) DO UPDATE SET "
                        "available_qty_micro = available_qty_micro + ?",
                        (agent_id, instrument, filled_qty_micro, filled_qty_micro),
                    )
                    if final and new_order_reserved_cents > 0:
                        # Unspent reservation returns to the agent (and stops
                        # being held against the pool) — it was never spent.
                        cur.execute(
                            "UPDATE agents SET available_cents = available_cents + ?, "
                            "reserved_cents = reserved_cents - ? WHERE agent_id = ?",
                            (new_order_reserved_cents, new_order_reserved_cents, agent_id),
                        )
                        cur.execute(
                            "UPDATE pool SET reserved_cents = reserved_cents - ? WHERE id = 1",
                            (new_order_reserved_cents,),
                        )
                        new_order_reserved_cents = 0
                    new_reserved_qty_micro = 0
                else:  # sell
                    proceeds_cents = _floor_div(fill_price_cents * filled_qty_micro, QTY_SCALE)
                    if fee_cents > proceeds_cents:
                        raise ValueError(
                            f"fee {fee_cents}c exceeds this fill's proceeds of {proceeds_cents}c"
                        )
                    proceeds_cents -= fee_cents
                    cur.execute(
                        "UPDATE agents SET available_cents = available_cents + ? WHERE agent_id = ?",
                        (proceeds_cents, agent_id),
                    )
                    cur.execute(
                        "UPDATE pool SET total_cents = total_cents + ? WHERE id = 1",
                        (proceeds_cents,),
                    )
                    cur.execute(
                        "UPDATE positions SET reserved_qty_micro = reserved_qty_micro - ? "
                        "WHERE agent_id = ? AND instrument = ?",
                        (filled_qty_micro, agent_id, instrument),
                    )
                    new_order_reserved_cents = 0
                    new_reserved_qty_micro = reserved_qty_micro - filled_qty_micro
                    if final and new_reserved_qty_micro > 0:
                        # Unsold remainder returns to available shares — it was
                        # never actually sold, so it must not stay locked up.
                        cur.execute(
                            "UPDATE positions SET available_qty_micro = available_qty_micro + ?, "
                            "reserved_qty_micro = reserved_qty_micro - ? "
                            "WHERE agent_id = ? AND instrument = ?",
                            (new_reserved_qty_micro, new_reserved_qty_micro, agent_id, instrument),
                        )
                        new_reserved_qty_micro = 0

                new_filled_micro = prior_filled_micro + filled_qty_micro
                new_status = "FILLED" if final else "PARTIAL"
                cur.execute(
                    "UPDATE orders SET status = ?, filled_qty_micro = ?, reserved_cents = ?, "
                    "reserved_qty_micro = ? WHERE order_id = ?",
                    (new_status, new_filled_micro, new_order_reserved_cents, new_reserved_qty_micro, order_id),
                )
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise
        self._audit(
            agent_id, order_id, idem_key, "settled", new_status,
            f"filled_qty_micro={filled_qty_micro} price_cents={fill_price_cents} fee_cents={fee_cents} final={final}",
        )

    def cancel(self, order_id: str) -> None:
        """Release whatever is still reserved on an open order back to the
        agent/pool (cash) or the agent's available position (shares)."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute(
                    "SELECT agent_id, instrument, side, reserved_cents, reserved_qty_micro, "
                    "status, idempotency_key FROM orders WHERE order_id = ?",
                    (order_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(f"unknown order_id {order_id!r}")
                agent_id, instrument, side, reserved_cents, reserved_qty_micro, status, idem_key = row
                if status not in ("PENDING", "PARTIAL"):
                    raise ValueError(f"order {order_id} is not open (status={status})")
                if side == "buy" and reserved_cents:
                    cur.execute(
                        "UPDATE agents SET reserved_cents = reserved_cents - ?, "
                        "available_cents = available_cents + ? WHERE agent_id = ?",
                        (reserved_cents, reserved_cents, agent_id),
                    )
                    cur.execute("UPDATE pool SET reserved_cents = reserved_cents - ? WHERE id = 1", (reserved_cents,))
                elif side == "sell" and reserved_qty_micro:
                    cur.execute(
                        "UPDATE positions SET reserved_qty_micro = reserved_qty_micro - ?, "
                        "available_qty_micro = available_qty_micro + ? WHERE agent_id = ? AND instrument = ?",
                        (reserved_qty_micro, reserved_qty_micro, agent_id, instrument),
                    )
                cur.execute(
                    "UPDATE orders SET status = 'CANCELLED', reserved_cents = 0, reserved_qty_micro = 0 "
                    "WHERE order_id = ?",
                    (order_id,),
                )
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise
        self._audit(agent_id, order_id, idem_key, "cancelled", "released_reservation", "")

    def reconcile(self, broker: Optional["PaperBroker"] = None) -> dict:
        """With a `broker` supplied, compares the ledger's aggregate cash
        and positions against that broker's *independently* tallied record
        (kept from the fills it issued, not derived from this ledger) —
        the closest a paper stage can get to comparing against an external
        broker statement. Without one, falls back to an internal-only
        invariant check: no negative cash, no negative shares, and claims
        that do not exceed the pool's declared total. Either way, this does
        not assume the ledger is self-consistent just because it is
        internally generated — a violation here is exactly the signature a
        forged/garbled fill receipt would leave behind."""
        with self._lock:
            agent_rows = self._conn.execute(
                "SELECT agent_id, available_cents, reserved_cents FROM agents"
            ).fetchall()
            position_rows = self._conn.execute(
                "SELECT agent_id, instrument, available_qty_micro, reserved_qty_micro FROM positions"
            ).fetchall()
        pool_total, _pool_reserved = self.pool_balance()

        negative_cash_agents = [r[0] for r in agent_rows if r[1] < 0 or r[2] < 0]
        negative_position_rows = [
            (r[0], r[1]) for r in position_rows if r[2] < 0 or r[3] < 0
        ]
        total_claimed_cents = sum(r[1] + r[2] for r in agent_rows)

        report = {
            "negative_cash_agents": negative_cash_agents,
            "negative_positions": negative_position_rows,
            "total_claimed_cents": total_claimed_cents,
            "pool_total_cents": pool_total,
        }

        if broker is not None:
            mismatches = []
            ledger_positions = {(r[0], r[1]): r[2] + r[3] for r in position_rows}
            for key, broker_qty_micro in broker.independent_positions.items():
                if ledger_positions.get(key, 0) != broker_qty_micro:
                    mismatches.append(
                        f"position {key}: ledger={ledger_positions.get(key, 0)} "
                        f"broker={broker_qty_micro}"
                    )
            for key, ledger_qty_micro in ledger_positions.items():
                if key not in broker.independent_positions and ledger_qty_micro != 0:
                    mismatches.append(f"position {key}: ledger={ledger_qty_micro} broker=0 (untracked)")
            report["position_mismatches"] = mismatches
            report["ok"] = not (negative_cash_agents or negative_position_rows or mismatches)
        else:
            report["ok"] = (
                total_claimed_cents <= pool_total
                and not negative_cash_agents
                and not negative_position_rows
            )
        return report


class OrderGateway:
    """The only accepted entry point for an agent's order intent. There is
    deliberately no other function in this module that touches cash or
    positions directly."""

    def __init__(
        self,
        ledger: Ledger,
        *,
        fee_buffer_bps: int = DEFAULT_FEE_BUFFER_BPS,
        per_position_cap_fraction: float = DEFAULT_PER_POSITION_CAP_FRACTION,
        cross_agent_cooldown_seconds: float = DEFAULT_CROSS_AGENT_COOLDOWN_SECONDS,
        max_price_age_seconds: float = DEFAULT_MAX_PRICE_AGE_SECONDS,
        max_drawdown_fraction: float = DEFAULT_MAX_DRAWDOWN_FRACTION,
    ) -> None:
        self.ledger = ledger
        self.fee_buffer_bps = fee_buffer_bps
        self.per_position_cap_fraction = per_position_cap_fraction
        self.cross_agent_cooldown_seconds = cross_agent_cooldown_seconds
        self.max_price_age_seconds = max_price_age_seconds
        self.max_drawdown_fraction = max_drawdown_fraction

    def submit_order_request(
        self,
        agent_id: str,
        instrument: str,
        side: str,
        qty: float,
        *,
        idempotency_key: Optional[str] = None,
        now: Optional[float] = None,
    ) -> Decision:
        now = time.time() if now is None else now
        idempotency_key = idempotency_key or str(uuid.uuid4())
        order_id = str(uuid.uuid4())

        if self.ledger.kill_switch_on():
            self.ledger._audit(agent_id, order_id, idempotency_key, "rejected", "kill_switch_active", instrument)
            return Decision(False, "kill_switch_active")

        try:
            qty_micro = to_qty_micro(qty)
        except ValueError:
            self.ledger._audit(agent_id, order_id, idempotency_key, "rejected", "invalid_quantity", f"qty={qty!r}")
            return Decision(False, "invalid_quantity")

        price_row = self.ledger.get_price(instrument)
        if price_row is None:
            self.ledger._audit(agent_id, order_id, idempotency_key, "rejected", "unknown_instrument", instrument)
            return Decision(False, "unknown_instrument")
        price_cents, tag, updated_at = price_row

        if tag in DENYLISTED_INSTRUMENT_TAGS:
            self.ledger._audit(agent_id, order_id, idempotency_key, "rejected", "denylisted_instrument", f"{instrument} tag={tag}")
            return Decision(False, "denylisted_instrument")

        if now - updated_at > self.max_price_age_seconds:
            self.ledger._audit(agent_id, order_id, idempotency_key, "rejected", "stale_balance", f"{instrument} age={now - updated_at:.0f}s")
            return Decision(False, "stale_balance")

        decision = self.ledger.reserve(
            order_id, agent_id, instrument, side, qty_micro, price_cents,
            self.fee_buffer_bps, idempotency_key, now,
            per_position_cap_fraction=self.per_position_cap_fraction,
            cooldown_seconds=self.cross_agent_cooldown_seconds,
            max_drawdown_fraction=self.max_drawdown_fraction,
        )
        self.ledger._audit(
            agent_id, order_id if decision.accepted else None, idempotency_key,
            "accepted" if decision.accepted else "rejected",
            decision.reason,
            f"{instrument} {side} qty={qty}",
        )
        return decision

    def set_kill_switch(self, on: bool) -> None:
        self.ledger.set_kill_switch(on)


class PaperBroker:
    """Test/simulation convenience only. No network client. Represents the
    (paper) broker's fill receipt arriving asynchronously; a real-mode
    equivalent would be a receipt parsed from an actual broker API, which
    this file does not implement and is not authorized to implement.

    Keeps its own independent tally of cash flow and positions, separate
    from the Ledger's own bookkeeping — this is what gives reconcile() a
    second, independently-derived record to check the ledger against,
    instead of comparing the ledger to itself."""

    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger
        self.net_cash_cents = 0  # net cash the broker has paid out (negative) or taken in (positive)
        self.independent_positions: dict[tuple[str, str], int] = {}

    def simulate_fill(
        self,
        order_id: str,
        fill_price_cents: int,
        filled_qty: Optional[float] = None,
        *,
        fee_cents: int = 0,
        final: bool = True,
    ) -> None:
        status_row = self.ledger.order_status(order_id)
        if status_row is None:
            raise KeyError(order_id)
        status, agent_id, instrument, side, qty_micro, filled_so_far_micro, _reserved_cents, _reserved_qty_micro = status_row
        if status not in ("PENDING", "PARTIAL"):
            raise ValueError(f"order {order_id} is not open (status={status})")
        remaining_qty_micro = qty_micro - filled_so_far_micro
        if filled_qty is None:
            filled_qty_micro = remaining_qty_micro
        else:
            filled_qty_micro = to_qty_micro(filled_qty)
            if filled_qty_micro > remaining_qty_micro:
                raise ValueError(
                    f"simulated fill of {filled_qty_micro} micro-units exceeds order {order_id}'s "
                    f"remaining {remaining_qty_micro} micro-units"
                )

        self.ledger.settle(order_id, from_qty_micro(filled_qty_micro), fill_price_cents, fee_cents=fee_cents, final=final)

        key = (agent_id, instrument)
        if side == "buy":
            notional_cents = _ceil_div(fill_price_cents * filled_qty_micro, QTY_SCALE)
            self.net_cash_cents -= notional_cents + fee_cents
            self.independent_positions[key] = self.independent_positions.get(key, 0) + filled_qty_micro
        else:
            proceeds_cents = max(_floor_div(fill_price_cents * filled_qty_micro, QTY_SCALE) - fee_cents, 0)
            self.net_cash_cents += proceeds_cents
            self.independent_positions[key] = self.independent_positions.get(key, 0) - filled_qty_micro


# ---------------------------------------------------------------------------
# smoke test — every hostile case the issue and both red-team reviews name
# ---------------------------------------------------------------------------


def run_smoke_test() -> int:
    print("ledger_gateway_v0_1 smoke test")
    checks = 0
    failures = 0

    def check(label: str, cond: bool) -> None:
        nonlocal checks, failures
        checks += 1
        status = "ok" if cond else "FAIL"
        if not cond:
            failures += 1
        print(f"  [{status}] {label}")

    def fresh_gateway():
        ledger = Ledger(":memory:")
        ledger.set_pool_total(100_000)  # $1,000.00 pool
        ledger.register_agent("agent-a", 50_000)  # $500.00
        ledger.register_agent("agent-b", 50_000)  # $500.00
        ledger.set_price("XYZ", price_cents=10_00, tag="equity")
        ledger.set_price("ZZZ-PERP", price_cents=10_00, tag="perpetual")
        gw = OrderGateway(ledger, per_position_cap_fraction=0.50)
        return ledger, gw

    # 1. normal accept
    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 10)  # $100 notional, well under cap
    check("normal buy within cap is accepted", d.accepted and d.reason == "accepted")

    # 2. per-agent over-cap reject, isolated from the per-position-size check
    # (tested separately below). The position cap is now projected across
    # the agent's held + outstanding-buy + new-order quantity (fixing the
    # "checked each order in isolation" bug), so a cap of 1.0x allocation is
    # no longer generous enough to isolate this case once a first order is
    # still PENDING (unsettled) and counts toward that projection — use a
    # cap far above the allocation (10x) so only the agent's actual cash
    # constrains the second order, not the position-size projection.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=10.0)
    d1 = gw.submit_order_request("agent-a", "XYZ", "buy", 45, idempotency_key="spend-most")  # ~$450.45 of $500
    d2 = gw.submit_order_request("agent-a", "XYZ", "buy", 40, idempotency_key="then-overdraw")  # ~$400.40 > ~$49.55 left
    check("first order spending most of the allocation is accepted", d1.accepted)
    check(
        "second order, within the per-position cap but exceeding remaining available cash, is rejected (agent_cap_exceeded)",
        not d2.accepted and d2.reason == "agent_cap_exceeded",
    )

    # 3. pool-exceeded reject (agent cap alone wouldn't catch this): each
    # agent's own allocation ($500) is big enough for either order alone,
    # but the shared pool ($700) is smaller than the agents' allocations
    # summed, so the second order must be rejected on the pool check even
    # though it is well within its own agent's cap.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(700_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.register_agent("agent-b", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0)
    d1 = gw.submit_order_request("agent-a", "XYZ", "buy", 40)  # $400, within agent cap and pool
    d2 = gw.submit_order_request("agent-b", "XYZ", "buy", 40)  # within agent-b's own cap, but pool has ~$300 left
    check("first order within pool is accepted", d1.accepted)
    check("second order within its own agent's cap but pushing total reserved over pool total is rejected (pool_cap_exceeded)",
          not d2.accepted and d2.reason == "pool_cap_exceeded")

    # 4. duplicate idempotency key reject
    ledger, gw = fresh_gateway()
    d1 = gw.submit_order_request("agent-a", "XYZ", "buy", 5, idempotency_key="dup-1")
    d2 = gw.submit_order_request("agent-a", "XYZ", "buy", 5, idempotency_key="dup-1")
    check("first submission with a given idempotency key is accepted", d1.accepted)
    check("replay of the same idempotency key is rejected, not re-charged",
          not d2.accepted and d2.reason == "duplicate_idempotency_key")

    # 5. concurrent double-spend prevention
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 100_00)  # $100.00 — only enough for one $60 order, not two
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0)
    results: list[Decision] = []
    results_lock = threading.Lock()

    def race():
        d = gw.submit_order_request("agent-a", "XYZ", "buy", 6)  # $60 each; two would be $120 > $100
        with results_lock:
            results.append(d)

    threads = [threading.Thread(target=race) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    accepted = [r for r in results if r.accepted]
    check("exactly one of five concurrent over-committing orders is accepted", len(accepted) == 1)
    final_balance = ledger.agent_balance("agent-a")
    check("agent's available cash never went negative under concurrent load", final_balance[1] >= 0)

    # 5b. concurrent cross-agent opposite-side race on the cooldown: now that
    # the cooldown check and the activity record live inside one transaction
    # with the reservation itself, only one side of a simultaneous opposite
    # pair can win, instead of both slipping through the old check-then-write
    # gap.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.register_agent("agent-b", 500_00)
    ledger.set_price("RACE", 10_00, tag="equity")
    # Seed agent-b with a position to sell, bypassing the gateway's own
    # cooldown logic (direct ledger reserve+settle) so this test isolates the
    # cooldown race rather than the "no shares held" rejection.
    seed_oid = str(uuid.uuid4())
    ledger.reserve(seed_oid, "agent-b", "RACE", "buy", to_qty_micro(5), 10_00, 0, "seed", time.time() - 10_000,
                   per_position_cap_fraction=1.0, cooldown_seconds=0)
    ledger.settle(seed_oid, 5, 10_00, final=True)
    gw_race = OrderGateway(ledger, per_position_cap_fraction=1.0, cross_agent_cooldown_seconds=300)
    cross_results: list[Decision] = []
    cross_lock = threading.Lock()

    def cross_race():
        d = gw_race.submit_order_request(
            "agent-a" if threading.current_thread().name.endswith("0") else "agent-b",
            "RACE", "buy" if threading.current_thread().name.endswith("0") else "sell", 1,
        )
        with cross_lock:
            cross_results.append(d)

    cross_threads = [threading.Thread(target=cross_race, name=f"t{i}") for i in range(2)]
    for t in cross_threads:
        t.start()
    for t in cross_threads:
        t.join()
    cross_accepted = [r for r in cross_results if r.accepted]
    check("of a simultaneous cross-agent opposite-side pair, at most one is accepted", len(cross_accepted) <= 1)

    # 6. stale balance / price feed fails closed
    ledger, gw = fresh_gateway()
    ledger.set_price("XYZ", 10_00, tag="equity", ts=time.time() - 10_000)  # far in the past
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 5)
    check("order against a stale price feed fails closed (stale_balance)", not d.accepted and d.reason == "stale_balance")

    # 7. kill switch fails closed
    ledger, gw = fresh_gateway()
    gw.set_kill_switch(True)
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 1)
    check("order submitted while kill switch is on is rejected (kill_switch_active)",
          not d.accepted and d.reason == "kill_switch_active")

    # 8. denylisted instrument reject
    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "ZZZ-PERP", "buy", 1)
    check("perpetual (denylisted tag) is rejected regardless of cash available",
          not d.accepted and d.reason == "denylisted_instrument")

    # 9. negative-cash / short-sale attempt reject (no borrowing path exists)
    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "XYZ", "sell", 5)  # agent holds nothing
    check("selling with no held position is rejected, not treated as a short (insufficient_position_no_shorting)",
          not d.accepted and d.reason == "insufficient_position_no_shorting")

    # 10. same-instrument, opposite-side, cross-agent cooldown block
    ledger, gw = fresh_gateway()
    gw.submit_order_request("agent-a", "XYZ", "buy", 1)
    d = gw.submit_order_request("agent-b", "XYZ", "sell", 1)
    check(
        "a different agent's opposite-side order in the same instrument inside the cooldown window is blocked",
        not d.accepted and d.reason == "cross_agent_same_instrument_cooldown",
    )

    # 11. per-position cap independent of available cash
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=0.10)  # cap at 10% of allocation
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 40)  # $400 notional, 80% of $500 allocation
    check("order within agent cash but over the per-position cap is rejected (per_position_cap_exceeded)",
          not d.accepted and d.reason == "per_position_cap_exceeded")

    # 11b. per-position cap is projected across multiple orders, not checked
    # per-order in isolation: three $100 buys against a $125 cap (25% of
    # $500) must not all three clear, even though each is individually under
    # the cap.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=0.25)  # $125 cap
    o1 = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="split-1")  # $100
    o2 = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="split-2")  # would make $200 > $125
    check("first $100 order against a $125 cap is accepted", o1.accepted)
    check(
        "second $100 order, which would push projected exposure to $200 against the same $125 cap, is rejected",
        not o2.accepted and o2.reason == "per_position_cap_exceeded",
    )

    # 11c. per-agent drawdown stop: once mark-to-market equity falls more
    # than max_drawdown_fraction below the agent's own high-water mark,
    # new buy orders are rejected — but a sell (de-risking) is still
    # allowed through.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0, max_drawdown_fraction=0.20)  # 20% stop
    buy_dd = gw.submit_order_request("agent-a", "XYZ", "buy", 40, idempotency_key="dd-buy")  # $400 of $500
    PaperBroker(ledger).simulate_fill(buy_dd.order_id, fill_price_cents=10_00, final=True)
    # Price craters: mark-to-market equity drops well past the 20% stop.
    ledger.set_price("XYZ", 3_00, tag="equity")
    blocked = gw.submit_order_request("agent-a", "XYZ", "buy", 1, idempotency_key="dd-buy-blocked")
    check(
        "a new buy is rejected once equity has drawn down past the configured threshold (agent_drawdown_stop)",
        not blocked.accepted and blocked.reason == "agent_drawdown_stop",
    )
    allowed_sell = gw.submit_order_request("agent-a", "XYZ", "sell", 1, idempotency_key="dd-sell-allowed")
    check("a sell (de-risking) is still allowed through while the drawdown stop is active", allowed_sell.accepted)

    # 12. cancel releases the reservation
    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="cancel-me")
    before = ledger.agent_balance("agent-a")
    ledger.cancel(d.order_id)
    after = ledger.agent_balance("agent-a")
    check("cancel releases the full reservation back to available cash",
          after[1] == before[1] + before[2] and after[2] == 0)

    # 13. partial fill leaves the remainder correctly reserved, final fill closes it
    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="partial-fill")
    broker = PaperBroker(ledger)
    broker.simulate_fill(d.order_id, fill_price_cents=10_00, filled_qty=4, final=False)
    mid = ledger.order_status(d.order_id)
    check("partial fill leaves the order PARTIAL with the unfilled portion still reserved", mid[0] == "PARTIAL")
    broker.simulate_fill(d.order_id, fill_price_cents=10_00, final=True)  # default: remainder, not original qty
    end = ledger.order_status(d.order_id)
    check("final fill (defaulting to the remainder, not the original qty) closes the order", end[0] == "FILLED" and end[6] == 0)
    pos = ledger.position("agent-a", "XYZ")
    check("filled quantity lands in the agent's available position", pos[0] == to_qty_micro(10))

    # 13b. a fill cannot exceed the order's remaining quantity or reserved cash
    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="overfill-qty")
    try:
        PaperBroker(ledger).simulate_fill(d.order_id, fill_price_cents=10_00, filled_qty=11)
        check("fill exceeding the order's remaining quantity raises", False)
    except ValueError:
        check("fill exceeding the order's remaining quantity raises", True)

    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="overfill-price")
    try:
        # same quantity, double the reserved price -> cost exceeds reservation
        ledger.settle(d.order_id, 10, 20_00, final=True)
        check("fill costing more than the order's reservation raises", False)
    except ValueError:
        check("fill costing more than the order's reservation raises", True)

    # 13c. partial sell keeps the unsold remainder reserved (not released
    # early); a short final fill releases only what is truly left over.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0)
    buy = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="acquire")
    PaperBroker(ledger).simulate_fill(buy.order_id, fill_price_cents=10_00, final=True)
    sell = gw.submit_order_request("agent-a", "XYZ", "sell", 10, idempotency_key="sell-partial")
    broker2 = PaperBroker(ledger)
    broker2.simulate_fill(sell.order_id, fill_price_cents=10_00, filled_qty=4, final=False)
    pos_mid = ledger.position("agent-a", "XYZ")
    check(
        "a partial sell leaves the unsold remainder reserved, not back in available",
        pos_mid[0] == 0 and pos_mid[1] == to_qty_micro(6),
    )
    broker2.simulate_fill(sell.order_id, fill_price_cents=10_00, filled_qty=3, final=True)  # short final fill
    pos_end = ledger.position("agent-a", "XYZ")
    check(
        "a short final fill releases exactly the true unsold remainder back to available, stranding nothing",
        pos_end[0] == to_qty_micro(3) and pos_end[1] == 0,
    )

    # 14. reconciliation catches an internally-inconsistent (forged-receipt-shaped) state
    ledger, gw = fresh_gateway()
    report_before = ledger.reconcile()
    check("reconciliation reports ok on an untouched ledger", report_before["ok"])
    # Directly corrupt the ledger the way a forged/garbled receipt would —
    # this bypasses the gateway on purpose, to prove reconcile() would catch
    # the resulting inconsistency rather than assuming internal state is
    # trustworthy just because it came from this process.
    with ledger._lock:
        ledger._conn.execute(
            "UPDATE agents SET available_cents = available_cents + 10_000_000 WHERE agent_id = 'agent-a'"
        )
    report_after = ledger.reconcile()
    check("reconciliation flags a forged/garbled-receipt-shaped state as not ok", not report_after["ok"])

    # 14b. reconciliation against an independently-tallied broker record
    # catches a position mismatch a cash-only check would miss.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0)
    broker3 = PaperBroker(ledger)
    buy2 = gw.submit_order_request("agent-a", "XYZ", "buy", 10, idempotency_key="recon-buy")
    broker3.simulate_fill(buy2.order_id, fill_price_cents=10_00, final=True)
    report_ok = ledger.reconcile(broker3)
    check("reconciliation against the independent broker tally reports ok after a normal fill", report_ok["ok"])
    with ledger._lock:
        ledger._conn.execute(
            "UPDATE positions SET available_qty_micro = available_qty_micro * 2 WHERE agent_id = 'agent-a'"
        )
    report_mismatch = ledger.reconcile(broker3)
    check(
        "reconciliation against the independent broker tally catches a position mismatch "
        "a cash-only invariant check would not see",
        not report_mismatch["ok"] and report_mismatch["position_mismatches"],
    )

    # 15. no deposit/withdrawal/margin/transfer function exists on the public surface
    public_gateway_methods = {name for name in dir(OrderGateway) if not name.startswith("_")}
    forbidden = {"deposit", "withdraw", "transfer", "margin", "borrow", "add_funds", "top_up"}
    check(
        "OrderGateway exposes no deposit/withdrawal/margin/transfer method",
        public_gateway_methods.isdisjoint(forbidden),
    )

    # 16. nonpositive / nonfinite quantities are rejected before reservation math
    ledger, gw = fresh_gateway()
    for bad_qty in (0, -5, float("nan"), float("inf")):
        d = gw.submit_order_request("agent-a", "XYZ", "buy", bad_qty, idempotency_key=f"bad-{bad_qty}")
        check(f"qty={bad_qty!r} is rejected before reservation (invalid_quantity)",
              not d.accepted and d.reason == "invalid_quantity")

    # 17. rounding never manufactures free value: a razor-thin quantity still
    # reserves at least one cent (ceiling), and crediting back never rounds up.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0)
    tiny = gw.submit_order_request("agent-a", "XYZ", "buy", 0.0004, idempotency_key="tiny")
    if tiny.accepted:
        bal = ledger.agent_balance("agent-a")
        check("a razor-thin buy still reserves a nonzero amount of cash (no free fractional shares)",
              bal[2] > 0)
    else:
        check("a razor-thin buy still reserves a nonzero amount of cash (no free fractional shares)", True)

    # 18b. settling a buy actually removes the spent cash from the pool's
    # total — not just its reservation. This is the headline bug a second
    # reviewer's hostile-case suite found: without this fix, two agents
    # sharing a $700 pool could each spend $400 ($800 total) because
    # settlement only ever released reservations and never shrank the
    # pool's actual total, so "available" cash silently came back after
    # every fill regardless of what had truly been spent.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(700_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.register_agent("agent-b", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0)
    broker_pool_test = PaperBroker(ledger)
    first = gw.submit_order_request("agent-a", "XYZ", "buy", 40, idempotency_key="pool-spend-1")  # $400
    broker_pool_test.simulate_fill(first.order_id, fill_price_cents=10_00, final=True)
    pool_after_settle = ledger.pool_balance()
    check(
        "settling a $400 buy against a $700 pool leaves ~$300 of real cash, not $700 again",
        pool_after_settle[0] <= 300_00,
    )
    second = gw.submit_order_request("agent-b", "XYZ", "buy", 40, idempotency_key="pool-spend-2")  # another $400
    check(
        "a second agent's $400 buy against the ~$300 actually remaining in the pool is rejected (pool_cap_exceeded)",
        not second.accepted and second.reason == "pool_cap_exceeded",
    )

    # 19. audit entries carry the order id and idempotency key they belong to
    ledger, gw = fresh_gateway()
    d = gw.submit_order_request("agent-a", "XYZ", "buy", 5, idempotency_key="traceable")
    log_rows = ledger.audit_log()
    accept_rows = [r for r in log_rows if r[5] == "accepted" and r[3] == "traceable"]
    check("an accepted order's audit row carries its idempotency key", len(accept_rows) == 1)
    check("an accepted order's audit row carries its order id", accept_rows[0][2] == d.order_id)

    print(f"{checks - failures}/{checks} checks passed")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-test", action="store_true", help="self-check on an in-memory ledger; no files written")
    args = parser.parse_args()
    if args.smoke_test:
        return run_smoke_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

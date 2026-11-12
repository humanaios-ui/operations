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
  - The gateway checks the requesting agent's remaining fixed allocation
    AND the shared pool's remaining cash before accepting, atomically,
    including a fee buffer, so two concurrent requests cannot spend the
    same dollars (or the same held shares, for sells).
  - No deposit/withdrawal/transfer/margin/borrow code path exists at all —
    not "denied by policy", simply absent from this module's surface.
  - Duplicate submissions (same agent + idempotency key) are rejected, not
    re-charged.
  - A denylisted instrument class (derivatives/options/leveraged or inverse
    ETFs/perpetuals/margin) is rejected before any reservation math runs.
  - A per-position size cap (fraction of the agent's frozen allocation) is
    enforced independent of available cash.
  - Same-instrument, opposite-side orders from two *different* agents
    inside one cooldown window are rejected — a market-conduct control
    (self-crossing / matched orders), distinct from the wash-sale/tax
    concern the issue tracks separately. See RED_TEAM_AUDIT_CLAUDE's
    finding #16.
  - A stale price/balance feed fails the gateway CLOSED for that request,
    not open.
  - A human kill switch, once set, fails every new request closed and
    marks the gateway unable to accept until explicitly cleared.
  - Every decision (accept/reject + reason code) is appended to an
    audit log. Nothing here is a silent revision.
  - reconcile() compares the ledger's internal claims against the pool's
    declared total and flags any mismatch rather than assuming the ledger
    is self-consistent.

What this does NOT do: decide A, B, N, the benchmark, the horizon, or
whether to ever go live. It has no opinion about any of that. It is a
mechanism for enforcing limits that are set elsewhere, once, before a run.

Usage:
  python3 ledger_gateway_v0_1.py --smoke-test     # self-check, in-memory DB
"""
from __future__ import annotations

import argparse
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


@dataclass
class Decision:
    accepted: bool
    reason: str
    order_id: Optional[str] = None


class Ledger:
    """Append-only-in-spirit SQLite ledger. Cash and quantities are stored
    as integer cents / integer micro-units to avoid float drift in the
    reservation math; callers pass floats for quantity and this module
    rounds once, consistently, at the boundary."""

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
                    reserved_cents INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS pool (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_cents INTEGER NOT NULL,
                    reserved_cents INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS positions (
                    agent_id TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    available_qty REAL NOT NULL DEFAULT 0,
                    reserved_qty REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (agent_id, instrument)
                );
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    instrument TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty REAL NOT NULL,
                    price_cents INTEGER NOT NULL,
                    reserved_cents INTEGER NOT NULL DEFAULT 0,
                    reserved_qty REAL NOT NULL DEFAULT 0,
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
                "INSERT INTO agents (agent_id, allocation_cents, available_cents, reserved_cents) "
                "VALUES (?, ?, ?, 0)",
                (agent_id, allocation_cents, allocation_cents),
            )

    def set_price(self, instrument: str, price_cents: int, tag: str = "", ts: Optional[float] = None) -> None:
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
        self._audit(None, "kill_switch_set", "operator", f"on={on}")

    # ---- read helpers ------------------------------------------------------

    # Every one of these reads is wrapped in the same lock `reserve()` and
    # `settle()` use. A bare `self._conn.execute()` from a read method
    # racing a write method's BEGIN IMMEDIATE on the *same* shared
    # connection object is exactly the "balance check that isn't actually
    # serialized" bug the issue calls out — this got caught by the
    # concurrent-submission smoke-test case below, not by inspection.

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
        with self._lock:
            row = self._conn.execute(
                "SELECT available_qty, reserved_qty FROM positions WHERE agent_id = ? AND instrument = ?",
                (agent_id, instrument),
            ).fetchone()
        return row or (0.0, 0.0)

    def pool_balance(self):
        with self._lock:
            return self._conn.execute("SELECT total_cents, reserved_cents FROM pool WHERE id = 1").fetchone()

    def order_status(self, order_id: str):
        with self._lock:
            return self._conn.execute(
                "SELECT status, agent_id, instrument, side, qty, reserved_cents, reserved_qty "
                "FROM orders WHERE order_id = ?",
                (order_id,),
            ).fetchone()

    def recent_opposite_side(self, instrument: str, agent_id: str, side: str, now: float, cooldown_s: float) -> bool:
        opposite = "sell" if side == "buy" else "buy"
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM cross_agent_activity WHERE instrument = ? AND side = ? "
                "AND agent_id != ? AND ts > ? LIMIT 1",
                (instrument, opposite, agent_id, now - cooldown_s),
            ).fetchone()
        return row is not None

    def _audit(self, agent_id: Optional[str], event: str, reason: str, detail: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO audit_log (ts, agent_id, event, reason, detail) VALUES (?, ?, ?, ?, ?)",
                (time.time(), agent_id, event, reason, detail),
            )

    def audit_log(self):
        with self._lock:
            return self._conn.execute(
                "SELECT ts, agent_id, event, reason, detail FROM audit_log ORDER BY id"
            ).fetchall()

    # ---- the one place reservations happen --------------------------------

    def reserve(
        self,
        order_id: str,
        agent_id: str,
        instrument: str,
        side: str,
        qty: float,
        price_cents: int,
        fee_buffer_bps: int,
        idempotency_key: str,
        now: float,
    ) -> Decision:
        """Atomically check-and-reserve. Holds the process-wide lock for the
        whole check+write so two concurrent requests cannot both pass the
        check before either writes — the thing a bare 'read balance, decide,
        then write' pattern gets wrong under concurrency."""
        notional_cents = int(round(price_cents * qty))
        fee_cents = int(round(notional_cents * fee_buffer_bps / 10_000))
        cost_cents = notional_cents + fee_cents

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

                agent_row = cur.execute(
                    "SELECT available_cents FROM agents WHERE agent_id = ?", (agent_id,)
                ).fetchone()
                if agent_row is None:
                    cur.execute("ROLLBACK")
                    return Decision(False, "unknown_agent")
                available_cents = agent_row[0]

                pool_row = cur.execute(
                    "SELECT total_cents, reserved_cents FROM pool WHERE id = 1"
                ).fetchone()
                if pool_row is None:
                    cur.execute("ROLLBACK")
                    return Decision(False, "pool_not_configured")
                pool_total, pool_reserved = pool_row
                pool_available = pool_total - pool_reserved

                if side == "buy":
                    if cost_cents > available_cents:
                        cur.execute("ROLLBACK")
                        return Decision(False, "agent_cap_exceeded")
                    if cost_cents > pool_available:
                        cur.execute("ROLLBACK")
                        return Decision(False, "pool_cap_exceeded")
                    cur.execute(
                        "UPDATE agents SET available_cents = available_cents - ?, "
                        "reserved_cents = reserved_cents + ? WHERE agent_id = ?",
                        (cost_cents, cost_cents, agent_id),
                    )
                    cur.execute(
                        "UPDATE pool SET reserved_cents = reserved_cents + ? WHERE id = 1",
                        (cost_cents,),
                    )
                    reserved_cents, reserved_qty = cost_cents, 0.0
                elif side == "sell":
                    pos_row = cur.execute(
                        "SELECT available_qty FROM positions WHERE agent_id = ? AND instrument = ?",
                        (agent_id, instrument),
                    ).fetchone()
                    held = pos_row[0] if pos_row else 0.0
                    if qty > held:
                        cur.execute("ROLLBACK")
                        # No margin/borrowing path exists: a sell beyond what is
                        # held is a short-sale attempt, which this gateway has
                        # no code path to fulfil.
                        return Decision(False, "insufficient_position_no_shorting")
                    cur.execute(
                        "INSERT INTO positions (agent_id, instrument, available_qty, reserved_qty) "
                        "VALUES (?, ?, ?, ?) ON CONFLICT(agent_id, instrument) DO UPDATE SET "
                        "available_qty = available_qty - ?, reserved_qty = reserved_qty + ?",
                        (agent_id, instrument, -qty, qty, qty, qty),
                    )
                    reserved_cents, reserved_qty = 0, qty
                else:
                    cur.execute("ROLLBACK")
                    return Decision(False, "unknown_side")

                cur.execute(
                    "INSERT INTO orders (order_id, agent_id, instrument, side, qty, price_cents, "
                    "reserved_cents, reserved_qty, idempotency_key, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)",
                    (
                        order_id, agent_id, instrument, side, qty, price_cents,
                        reserved_cents, reserved_qty, idempotency_key, now,
                    ),
                )
                cur.execute("COMMIT")
                return Decision(True, "accepted", order_id)
            except Exception:
                cur.execute("ROLLBACK")
                raise

    def settle(self, order_id: str, filled_qty: float, fill_price_cents: int, final: bool = True) -> None:
        """Apply a (paper) fill receipt. Releases any unused reservation back
        to the agent/pool rather than letting it evaporate — a partially
        filled or re-priced order must not silently shrink what the agent
        can spend next."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute(
                    "SELECT agent_id, instrument, side, qty, reserved_cents, reserved_qty, status "
                    "FROM orders WHERE order_id = ?",
                    (order_id,),
                ).fetchone()
                if row is None:
                    cur.execute("ROLLBACK")
                    raise KeyError(f"unknown order_id {order_id!r}")
                agent_id, instrument, side, requested_qty, reserved_cents, reserved_qty, status = row
                if status not in ("PENDING", "PARTIAL"):
                    cur.execute("ROLLBACK")
                    raise ValueError(f"order {order_id} is not open (status={status})")

                if side == "buy":
                    actual_cost = int(round(fill_price_cents * filled_qty))
                    release = max(reserved_cents - actual_cost, 0) if final else 0
                    cur.execute(
                        "UPDATE agents SET reserved_cents = reserved_cents - ?, "
                        "available_cents = available_cents + ? WHERE agent_id = ?",
                        (reserved_cents if final else actual_cost, release, agent_id),
                    )
                    if final:
                        cur.execute(
                            "UPDATE pool SET reserved_cents = reserved_cents - ? WHERE id = 1",
                            (reserved_cents,),
                        )
                        new_reserved_cents = 0
                    else:
                        cur.execute(
                            "UPDATE pool SET reserved_cents = reserved_cents - ? WHERE id = 1",
                            (actual_cost,),
                        )
                        new_reserved_cents = reserved_cents - actual_cost
                    cur.execute(
                        "INSERT INTO positions (agent_id, instrument, available_qty, reserved_qty) "
                        "VALUES (?, ?, ?, 0) ON CONFLICT(agent_id, instrument) DO UPDATE SET "
                        "available_qty = available_qty + ?",
                        (agent_id, instrument, filled_qty, filled_qty),
                    )
                    new_reserved_qty = 0.0
                else:  # sell
                    proceeds = int(round(fill_price_cents * filled_qty))
                    cur.execute(
                        "UPDATE agents SET available_cents = available_cents + ? WHERE agent_id = ?",
                        (proceeds, agent_id),
                    )
                    cur.execute(
                        "UPDATE positions SET reserved_qty = reserved_qty - ? "
                        "WHERE agent_id = ? AND instrument = ?",
                        (filled_qty, agent_id, instrument),
                    )
                    if not final:
                        cur.execute(
                            "UPDATE positions SET available_qty = available_qty + ? "
                            "WHERE agent_id = ? AND instrument = ?",
                            (requested_qty - filled_qty, agent_id, instrument),
                        )
                    new_reserved_cents = 0
                    new_reserved_qty = max(reserved_qty - filled_qty, 0.0) if not final else 0.0

                new_status = "FILLED" if final else "PARTIAL"
                cur.execute(
                    "UPDATE orders SET status = ?, reserved_cents = ?, reserved_qty = ?, qty = ? "
                    "WHERE order_id = ?",
                    (new_status, new_reserved_cents, new_reserved_qty, filled_qty if final else requested_qty, order_id),
                )
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise
        self._audit(agent_id, "settled", new_status, f"order={order_id} filled_qty={filled_qty} price={fill_price_cents}")

    def cancel(self, order_id: str) -> None:
        """Release whatever is still reserved on an open order back to the
        agent/pool (cash) or the agent's available position (shares)."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                row = cur.execute(
                    "SELECT agent_id, instrument, side, reserved_cents, reserved_qty, status "
                    "FROM orders WHERE order_id = ?",
                    (order_id,),
                ).fetchone()
                if row is None:
                    cur.execute("ROLLBACK")
                    raise KeyError(f"unknown order_id {order_id!r}")
                agent_id, instrument, side, reserved_cents, reserved_qty, status = row
                if status not in ("PENDING", "PARTIAL"):
                    cur.execute("ROLLBACK")
                    raise ValueError(f"order {order_id} is not open (status={status})")
                if side == "buy" and reserved_cents:
                    cur.execute(
                        "UPDATE agents SET reserved_cents = reserved_cents - ?, "
                        "available_cents = available_cents + ? WHERE agent_id = ?",
                        (reserved_cents, reserved_cents, agent_id),
                    )
                    cur.execute("UPDATE pool SET reserved_cents = reserved_cents - ? WHERE id = 1", (reserved_cents,))
                elif side == "sell" and reserved_qty:
                    cur.execute(
                        "UPDATE positions SET reserved_qty = reserved_qty - ?, "
                        "available_qty = available_qty + ? WHERE agent_id = ? AND instrument = ?",
                        (reserved_qty, reserved_qty, agent_id, instrument),
                    )
                cur.execute("UPDATE orders SET status = 'CANCELLED', reserved_cents = 0, reserved_qty = 0 "
                            "WHERE order_id = ?", (order_id,))
                cur.execute("COMMIT")
            except Exception:
                cur.execute("ROLLBACK")
                raise
        self._audit(agent_id, "cancelled", "released_reservation", f"order={order_id}")

    def record_cross_agent_activity(self, instrument: str, agent_id: str, side: str, ts: float) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO cross_agent_activity (instrument, agent_id, side, ts) VALUES (?, ?, ?, ?)",
                (instrument, agent_id, side, ts),
            )

    def reconcile(self) -> dict:
        """Internal-consistency reconciliation. There is no real external
        broker in paper mode, so this checks the one invariant that must
        hold regardless: no agent's claimed cash position may be negative,
        and the sum of agents' available+reserved cash may never exceed the
        pool's declared total. A violation here is exactly the signature a
        forged/garbled fill receipt would leave behind."""
        with self._lock:
            rows = self._conn.execute("SELECT agent_id, available_cents, reserved_cents FROM agents").fetchall()
        pool_total, _pool_reserved = self.pool_balance()
        total_claimed = sum(r[1] + r[2] for r in rows)
        negative_agents = [r[0] for r in rows if r[1] < 0 or r[2] < 0]
        return {
            "ok": total_claimed <= pool_total and not negative_agents,
            "total_claimed_cents": total_claimed,
            "pool_total_cents": pool_total,
            "negative_agents": negative_agents,
        }


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
    ) -> None:
        self.ledger = ledger
        self.fee_buffer_bps = fee_buffer_bps
        self.per_position_cap_fraction = per_position_cap_fraction
        self.cross_agent_cooldown_seconds = cross_agent_cooldown_seconds
        self.max_price_age_seconds = max_price_age_seconds

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
            self.ledger._audit(agent_id, "rejected", "kill_switch_active", instrument)
            return Decision(False, "kill_switch_active")

        price_row = self.ledger.get_price(instrument)
        if price_row is None:
            self.ledger._audit(agent_id, "rejected", "unknown_instrument", instrument)
            return Decision(False, "unknown_instrument")
        price_cents, tag, updated_at = price_row

        if tag in DENYLISTED_INSTRUMENT_TAGS:
            self.ledger._audit(agent_id, "rejected", "denylisted_instrument", f"{instrument} tag={tag}")
            return Decision(False, "denylisted_instrument")

        if now - updated_at > self.max_price_age_seconds:
            self.ledger._audit(agent_id, "rejected", "stale_balance", f"{instrument} age={now - updated_at:.0f}s")
            return Decision(False, "stale_balance")

        if self.ledger.recent_opposite_side(instrument, agent_id, side, now, self.cross_agent_cooldown_seconds):
            self.ledger._audit(agent_id, "rejected", "cross_agent_same_instrument_cooldown", instrument)
            return Decision(False, "cross_agent_same_instrument_cooldown")

        if side == "buy":
            allocation_row = self.ledger.agent_balance(agent_id)
            if allocation_row is None:
                self.ledger._audit(agent_id, "rejected", "unknown_agent", instrument)
                return Decision(False, "unknown_agent")
            allocation_cents = allocation_row[0]
            notional_cents = price_cents * qty
            if notional_cents > allocation_cents * self.per_position_cap_fraction:
                self.ledger._audit(agent_id, "rejected", "per_position_cap_exceeded", instrument)
                return Decision(False, "per_position_cap_exceeded")

        decision = self.ledger.reserve(
            order_id, agent_id, instrument, side, qty, price_cents,
            self.fee_buffer_bps, idempotency_key, now,
        )
        self.ledger._audit(
            agent_id,
            "accepted" if decision.accepted else "rejected",
            decision.reason,
            f"{instrument} {side} qty={qty}",
        )
        if decision.accepted:
            self.ledger.record_cross_agent_activity(instrument, agent_id, side, now)
        return decision

    def set_kill_switch(self, on: bool) -> None:
        self.ledger.set_kill_switch(on)


class PaperBroker:
    """Test/simulation convenience only. No network client. Represents the
    (paper) broker's fill receipt arriving asynchronously; a real-mode
    equivalent would be a receipt parsed from an actual broker API, which
    this file does not implement and is not authorized to implement."""

    def __init__(self, ledger: Ledger) -> None:
        self.ledger = ledger

    def simulate_fill(self, order_id: str, fill_price_cents: int, filled_qty: Optional[float] = None, final: bool = True) -> None:
        status_row = self.ledger.order_status(order_id)
        if status_row is None:
            raise KeyError(order_id)
        _status, _agent_id, _instrument, _side, requested_qty, _reserved_cents, _reserved_qty = status_row
        self.ledger.settle(order_id, filled_qty if filled_qty is not None else requested_qty, fill_price_cents, final=final)


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
    # (tested separately below): per_position_cap_fraction=1.0 means the cap
    # is the agent's full *frozen allocation*, which stays constant — so to
    # exercise the AVAILABLE-cash check in reserve() specifically, spend most
    # of the allocation with a first order, then submit a second order that
    # is comfortably within the per-position cap (computed against the fixed
    # allocation) but exceeds what is actually still available.
    ledger = Ledger(":memory:")
    ledger.set_pool_total(1_000_00)
    ledger.register_agent("agent-a", 500_00)
    ledger.set_price("XYZ", 10_00, tag="equity")
    gw = OrderGateway(ledger, per_position_cap_fraction=1.0)
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
    broker.simulate_fill(d.order_id, fill_price_cents=10_00, filled_qty=6, final=True)
    end = ledger.order_status(d.order_id)
    check("final fill closes the order and clears the remaining reservation", end[0] == "FILLED" and end[5] == 0)
    pos = ledger.position("agent-a", "XYZ")
    check("filled quantity lands in the agent's available position", pos[0] == 10)

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

    # 15. no deposit/withdrawal/margin/transfer function exists on the public surface
    public_gateway_methods = {name for name in dir(OrderGateway) if not name.startswith("_")}
    forbidden = {"deposit", "withdraw", "transfer", "margin", "borrow", "add_funds", "top_up"}
    check(
        "OrderGateway exposes no deposit/withdrawal/margin/transfer method",
        public_gateway_methods.isdisjoint(forbidden),
    )

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

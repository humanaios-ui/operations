#!/usr/bin/env python3
"""
resource_ledger_v0_1.py — append-only, hash-chained ledger of resource claims,
spends and yields, denominated in the units registered in RESOURCE_UNITS.yaml.
Builder v1.7 compliant
HumanAIOS — RBE-OPS v0.1 (Q-RBE-01), the consumption side of the books

  init     <ledger>                                      genesis OPEN event, pins the units-registry sha256
  verify   <ledger> [--strict-pin]                       recompute every hash + prev link; report registry drift
  repin    <ledger> --source --reason                    record that RESOURCE_UNITS.yaml changed, in the chain
  cap      <ledger> <UNIT> <qty> --by --source [--hash]  declare a capacity for one unit
  claim    <ledger> <order> --budget U=Q[,U=Q] --by      a work order reserves a budget
  spend    <ledger> <order> <UNIT> <qty> --by --source   actual consumption
  yield    <ledger> <order> <UNIT> <qty> --by --source   output produced
  price    <ledger> <FROM> <TO> <rate> --n --window --constraint --source
  waste    <ledger> <UNIT> <qty> --by --source           accrue a liability (GAP-row, STALE-day)
  close    <ledger> <order> --by --source                close an order; yield density becomes computable
  status   <ledger>                                      balances per unit, open orders, declared capacities
  report   <ledger>                                      yield density per closed order; prices in force

Rules encoded (not prose) — each is a refusal the tests exercise:
  * a unit that is not REGISTERED in RESOURCE_UNITS.yaml is refused everywhere
  * every SPEND, YIELD, WASTE and CLOSE carries a source; no source -> refused
  * a capacity for the constraint unit is a Z2 act: needs --by Z2 --hash
  * YIELD is only for output dimensions (evidence, assurance); SPEND is only for inputs
  * WASTE is only for negative-sign units
  * cross-dimension exchange exists ONLY as a PRICE event with n >= shadow_price_min_n,
    a window, a named constraint and a source. There is no numeraire and no default rate.
  * an order closes once; a second close is refused; spend after close is refused
  * the file is append-only: nothing edits a prior line, and any edit breaks verify
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "resource_ledger"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

ROOT = Path(__file__).resolve().parent.parent
UNITS_PATH = ROOT / "RESOURCE_UNITS.yaml"
ZERO = "0" * 64

OUTPUT_DIMENSIONS = ("evidence", "assurance")
# Yield density divides by the constraint unit, so its numerator must be ONE
# dimension — summing evidence and assurance would assert exactly the
# commensurability this registry denies. The identity in RESOURCE_UNITS.yaml
# names evidence.
DENSITY_DIMENSION = "evidence"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.I)


@contextlib.contextmanager
def ledger_lock(path: str):
    """Serialize read-build-append on one ledger.

    Every mutation reads the head, computes the next seq, then appends. Two
    concurrent writers would otherwise build on the same prev_hash and produce a
    forked chain that `verify` then reports as corrupt. An advisory flock on a
    sidecar file (not the ledger itself — appending must not race the lock's own
    open) makes the section atomic between cooperating processes.
    """
    lock_path = Path(path).with_suffix(Path(path).suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a+") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


# ---------------------------------------------------------------- primitives
def canon(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def refuse(msg: str) -> None:
    sys.exit(f"REFUSED: {msg}")


def read(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append(path: str, events: list[dict], prev: str) -> str:
    with open(path, "a", encoding="utf-8") as f:
        for ev in events:
            ev = dict(ev)
            ev["prev_hash"] = prev
            ev["hash"] = sha(canon(ev))
            prev = ev["hash"]
            f.write(json.dumps(ev, sort_keys=True) + "\n")
    return prev


def verify(evs: list[dict]) -> str | None:
    prev = ZERO
    for i, e in enumerate(evs):
        body = {k: v for k, v in e.items() if k != "hash"}
        if e.get("prev_hash") != prev:
            return f"BREAK seq {e.get('seq')} prev_hash mismatch"
        if sha(canon(body)) != e.get("hash"):
            return f"BREAK seq {e.get('seq')} hash mismatch"
        if i and e.get("seq") != evs[i - 1].get("seq") + 1:
            return f"BREAK seq {e.get('seq')} sequence gap"
        prev = e["hash"]
    return None


# ---------------------------------------------------------------- registry
class Units:
    """The registered unit map. Every event is checked against it."""

    def __init__(self, path: Path):
        import yaml

        self.path = path
        self.raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.sha256 = sha(path.read_bytes())
        self.by_symbol = {u["symbol"]: u for u in self.raw.get("units", [])}
        self.policy = self.raw.get("policy", {}) or {}
        self.constraint = (self.raw.get("constraint") or {}).get("unit")

    def get(self, symbol: str) -> dict:
        u = self.by_symbol.get(symbol)
        if u is None:
            refuse(f"unit {symbol!r} is not in {self.path.name}; register it before using it")
        if u.get("status") != "REGISTERED":
            refuse(f"unit {symbol!r} is {u.get('status')}, not REGISTERED "
                   f"({u.get('blocker') or 'no instrument'})")
        return u

    @property
    def min_n(self) -> tuple[int, str]:
        """The shadow-price threshold, and where it came from.

        A RATIFIED `SHADOW_PRICE_MIN_N` in constants.json wins over the YAML
        default — otherwise a Z2 molt on that constant would change nothing and
        the constant would be a control surface wired to nothing. An unratified
        constant (molt_id null) is a proposal and does not take effect, the same
        dormancy rule the queue engine applies to QUEUE_SCORING_MODE.
        """
        default = int(self.policy.get("shadow_price_min_n", 8))
        try:
            consts = json.loads((ROOT / "constants.json").read_text(encoding="utf-8"))["constants"]
        except (OSError, json.JSONDecodeError, KeyError):
            return default, "RESOURCE_UNITS.yaml policy"
        for c in consts:
            if c.get("name") == "SHADOW_PRICE_MIN_N" and c.get("molt_id"):
                try:
                    return int(c["current_value"]), f"constants.json (ratified, molt {c['molt_id']})"
                except (TypeError, ValueError):
                    break
        return default, "RESOURCE_UNITS.yaml policy (SHADOW_PRICE_MIN_N not ratified)"


def check_qty(q, allow_zero: bool = False) -> float:
    """A quantity must be a real, finite number.

    NaN and infinity pass a naive `q <= 0` test and then serialize into JSONL as
    non-standard `NaN` / `Infinity` tokens, so they are rejected explicitly.
    `allow_zero` is for BUDGETS only: a work order that draws nothing on the
    constraint declares `RAT-min=0` and lands in Band A. An actual SPEND of zero
    is still refused — nothing happened, so there is nothing to record.
    """
    if isinstance(q, bool) or not isinstance(q, (int, float)):
        refuse(f"quantity {q!r} must be a number")
    if not math.isfinite(q):
        refuse(f"quantity {q!r} is not finite")
    if q < 0 or (q == 0 and not allow_zero):
        refuse(f"quantity {q!r} must be {'non-negative' if allow_zero else 'a positive number'}")
    return float(q)


def check_hash(h: str, what: str) -> str:
    """A ratification hash is a sha256. `CLAUDE.md` defines the Z2 signature as
    sha256(candidate | by | at | decision); a placeholder string is not one."""
    if not _SHA256_RE.match(h or ""):
        refuse(f"{what} {h!r} is not a sha256 (64 hex characters); a Z2 signature is a hash, not a label")
    return h


def require_source(source: str | None, what: str) -> str:
    if not source:
        refuse(f"{what} without --source; a resource event with no evidence is a claim, not a measurement")
    return source


def next_seq(evs: list[dict]) -> int:
    return (evs[-1]["seq"] + 1) if evs else 1


def load_chain(path: str) -> tuple[list[dict], str]:
    evs = read(path)
    err = verify(evs)
    if err:
        sys.exit("FAIL " + err)
    return evs, (evs[-1]["hash"] if evs else ZERO)


# ---------------------------------------------------------------- projection
def project(evs: list[dict]) -> dict:
    """Fold the chain into balances, orders, capacities and prices."""
    state = {
        "orders": {},       # order_id -> {budget, spent, yielded, closed, by}
        "spent": {},        # unit -> qty
        "yielded": {},      # unit -> qty
        "waste": {},        # unit -> qty
        "capacity": {},     # unit -> {qty, period, by, hash, source}
        "prices": [],       # PRICE events, newest last
        "genesis": None,
    }
    for e in evs:
        t = e.get("type")
        if t == "OPEN":
            state["genesis"] = e
        elif t == "CAP":
            state["capacity"][e["unit"]] = {
                "qty": e["qty"], "period": e.get("period"), "by": e.get("by"),
                "hash": e.get("z2_hash"), "source": e.get("source"), "at": e.get("at"),
            }
        elif t == "CLAIM":
            state["orders"][e["order_id"]] = {
                "budget": e["budget"], "spent": {}, "yielded": {},
                "closed": False, "by": e.get("by"), "at": e.get("at"),
            }
        elif t == "SPEND":
            o = state["orders"][e["order_id"]]
            o["spent"][e["unit"]] = o["spent"].get(e["unit"], 0) + e["qty"]
            state["spent"][e["unit"]] = state["spent"].get(e["unit"], 0) + e["qty"]
        elif t == "YIELD":
            o = state["orders"][e["order_id"]]
            o["yielded"][e["unit"]] = o["yielded"].get(e["unit"], 0) + e["qty"]
            state["yielded"][e["unit"]] = state["yielded"].get(e["unit"], 0) + e["qty"]
        elif t == "WASTE":
            state["waste"][e["unit"]] = state["waste"].get(e["unit"], 0) + e["qty"]
        elif t == "PRICE":
            state["prices"].append(e)
        elif t == "CLOSE":
            state["orders"][e["order_id"]]["closed"] = True
            state["orders"][e["order_id"]]["closed_at"] = e.get("at")
    return state


def get_order(state: dict, order_id: str, for_what: str) -> dict:
    o = state["orders"].get(order_id)
    if o is None:
        refuse(f"unknown order {order_id!r}; CLAIM a budget before you {for_what}")
    if o["closed"]:
        refuse(f"order {order_id!r} is closed; a closed order takes no further events")
    return o


# ---------------------------------------------------------------- commands
def cmd_init(a) -> int:
    path = Path(a.ledger)
    if path.exists() and path.stat().st_size:
        refuse(f"{a.ledger} already exists; a ledger is initialised once")
    units = Units(Path(a.units))
    ev = {
        "seq": 1, "type": "OPEN", "at": now(), "by": a.by,
        "ledger": "RESOURCE_LEDGER", "version": f"v{TOOL_VERSION}",
        "units_registry": units.path.name,
        "units_registry_sha256": units.sha256,
        "units_registry_status": units.raw.get("status"),
        "units_ratification_hash": units.raw.get("ratification_hash"),
        "constraint_unit": units.constraint,
        "note": ("Unit definitions are CANDIDATE until Z2 signs RESOURCE_UNITS.yaml. "
                 "Events recorded before that are measurements, not authority."),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    head = append(a.ledger, [ev], ZERO)
    print(f"initialised {a.ledger}\nunits sha256 {units.sha256}\nhead {head}")
    return 0


def registry_pin_status(evs: list[dict], units: "Units") -> dict:
    """Compare the registry the chain was opened against with the one on disk.

    The genesis event pins a sha256 of RESOURCE_UNITS.yaml. Hash-linking the
    events does not protect that: edit the registry and every historical event
    is silently reinterpreted under new unit definitions while `verify` still
    passes. Drift is not an error — the registry is expected to change when Z2
    ratifies it — but it must be VISIBLE, and the change must be recorded in the
    chain by a REPIN event rather than happening behind it.
    """
    pins = [e for e in evs if e.get("type") in ("OPEN", "REPIN")]
    pinned = pins[-1].get("units_registry_sha256") if pins else None
    return {
        "pinned_sha256": pinned,
        "current_sha256": units.sha256,
        "drift": bool(pinned) and pinned != units.sha256,
        "pinned_by_event": pins[-1].get("type") if pins else None,
    }


def cmd_verify(a) -> int:
    evs = read(a.ledger)
    err = verify(evs)
    if err:
        sys.exit("FAIL " + err)
    print(f"OK chain intact, {len(evs)} events; head {evs[-1]['hash'] if evs else ZERO}")
    pin = registry_pin_status(evs, Units(Path(a.units)))
    if pin["drift"]:
        print(f"REGISTRY DRIFT: chain pinned {str(pin['pinned_sha256'])[:16]}…, "
              f"{Path(a.units).name} is now {pin['current_sha256'][:16]}…\n"
              "  Events before this point were recorded under different unit definitions.\n"
              "  Record the change with `repin` (append-only) so the chain says when it happened.")
        if a.strict_pin:
            return 1
    elif pin["pinned_sha256"]:
        print(f"registry pin OK ({pin['pinned_by_event']}) {pin['current_sha256'][:16]}…")
    return 0


def cmd_repin(a) -> int:
    """Record that the units registry changed, in the chain, with a reason."""
    units = Units(Path(a.units))
    source = require_source(a.source, "REPIN")
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        pin = registry_pin_status(evs, units)
        if not pin["drift"]:
            refuse(f"{units.path.name} still matches the pinned sha256; there is nothing to repin")
        ev = {"seq": next_seq(evs), "type": "REPIN", "at": now(), "by": a.by,
              "units_registry": units.path.name,
              "units_registry_sha256": units.sha256,
              "previous_sha256": pin["pinned_sha256"],
              "units_registry_status": units.raw.get("status"),
              "units_ratification_hash": units.raw.get("ratification_hash"),
              "source": source, "reason": a.reason or ""}
        head = append(a.ledger, [ev], head)
    print(f"REPIN {pin['pinned_sha256'][:16]}… → {units.sha256[:16]}…; head {head}")
    return 0


def cmd_cap(a) -> int:
    units = Units(Path(a.units))
    u = units.get(a.unit)
    qty = check_qty(a.qty)
    source = require_source(a.source, "CAP")
    if a.unit == units.constraint:
        if a.by != "Z2" or not a.hash:
            refuse("declaring the capacity of the constraint unit is a Z2 act; "
                   "needs --by Z2 --hash <ratification hash>")
        check_hash(a.hash, "ratification hash")
    elif a.hash:
        check_hash(a.hash, "ratification hash")
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        ev = {"seq": next_seq(evs), "type": "CAP", "at": now(), "by": a.by, "unit": a.unit,
              "qty": qty, "period": a.period or u.get("period"), "source": source}
        if a.hash:
            ev["z2_hash"] = a.hash
        head = append(a.ledger, [ev], head)
    print(f"CAP {a.unit} = {qty} per {ev['period']}; head {head}")
    return 0


def parse_budget(spec: str, units: Units) -> dict:
    budget = {}
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            refuse(f"budget item {part!r} must be UNIT=QTY")
        sym, raw = part.split("=", 1)
        sym = sym.strip()
        units.get(sym)
        try:
            value = float(raw)
        except ValueError:
            refuse(f"budget quantity {raw!r} is not a number")
        # allow_zero: an explicit 0 on the constraint unit is how a row declares
        # Band A — no draw on the bottleneck. That is a price, not a blank.
        budget[sym] = check_qty(value, allow_zero=True)
    if not budget:
        refuse("an empty budget is not a claim")
    return budget


def cmd_claim(a) -> int:
    units = Units(Path(a.units))
    budget = parse_budget(a.budget, units)
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        state = project(evs)
        if a.order_id in state["orders"]:
            refuse(f"order {a.order_id!r} already claimed; amend with a new order id")
        if units.constraint not in budget:
            refuse(f"every work order must price itself in the constraint unit ({units.constraint}); "
                   "an unpriced row cannot be scheduled. Declare 0 if it draws none.")
        ev = {"seq": next_seq(evs), "type": "CLAIM", "at": now(), "by": a.by,
              "order_id": a.order_id, "budget": budget, "title": a.title or "",
              # A budget is a forecast, but where it came from is still evidence.
              "source": a.source}
        head = append(a.ledger, [ev], head)
    print(f"CLAIM {a.order_id} {budget}; head {head}")
    return 0


def cmd_spend(a) -> int:
    units = Units(Path(a.units))
    u = units.get(a.unit)
    qty = check_qty(a.qty)
    source = require_source(a.source, "SPEND")
    if u["dimension"] in OUTPUT_DIMENSIONS and u.get("sign") == "positive":
        refuse(f"{a.unit} is an output unit; produce it with `yield`, do not spend it")
    if u.get("sign") == "negative":
        refuse(f"{a.unit} is a liability unit; accrue it with `waste`")
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        state = project(evs)
        get_order(state, a.order_id, "spend")
        ev = {"seq": next_seq(evs), "type": "SPEND", "at": now(), "by": a.by,
              "order_id": a.order_id, "unit": a.unit, "qty": qty, "source": source,
              "obligation_class": a.obligation_class}
        head = append(a.ledger, [ev], head)
    print(f"SPEND {a.order_id} {qty} {a.unit}; head {head}")
    return 0


def cmd_yield(a) -> int:
    units = Units(Path(a.units))
    u = units.get(a.unit)
    qty = check_qty(a.qty)
    source = require_source(a.source, "YIELD")
    if u["dimension"] not in OUTPUT_DIMENSIONS or u.get("sign") != "positive":
        refuse(f"{a.unit} is not an output unit (dimension must be one of {OUTPUT_DIMENSIONS})")
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        state = project(evs)
        get_order(state, a.order_id, "yield")
        ev = {"seq": next_seq(evs), "type": "YIELD", "at": now(), "by": a.by,
              "order_id": a.order_id, "unit": a.unit, "qty": qty, "source": source}
        head = append(a.ledger, [ev], head)
    print(f"YIELD {a.order_id} {qty} {a.unit}; head {head}")
    return 0


def cmd_waste(a) -> int:
    units = Units(Path(a.units))
    u = units.get(a.unit)
    qty = check_qty(a.qty)
    source = require_source(a.source, "WASTE")
    if u.get("sign") != "negative":
        refuse(f"{a.unit} is not a liability unit; `waste` records negative-sign units only")
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        ev = {"seq": next_seq(evs), "type": "WASTE", "at": now(), "by": a.by,
              "unit": a.unit, "qty": qty, "source": source, "order_id": a.order_id}
        head = append(a.ledger, [ev], head)
    print(f"WASTE {qty} {a.unit}; head {head}")
    return 0


def cmd_price(a) -> int:
    """The only legal exchange rate: a measured margin at a named constraint."""
    units = Units(Path(a.units))
    src_u, dst_u = units.get(a.from_unit), units.get(a.to_unit)
    rate = check_qty(a.rate)
    source = require_source(a.source, "PRICE")
    min_n, min_n_source = units.min_n
    if src_u["dimension"] == dst_u["dimension"]:
        refuse(f"{a.from_unit} and {a.to_unit} are both in the {src_u['dimension']} dimension; "
               "a PRICE event is the escape hatch for CROSS-dimension exchange, and units inside "
               "one dimension already share a scale")
    if a.n is None or a.n < min_n:
        refuse(f"a price needs n >= {min_n} paired observations (got {a.n}, threshold from "
               f"{min_n_source}); below that it is an assertion, not a measurement")
    if not a.window:
        refuse("a price needs --window; a rate that never expires is a currency, not a measurement")
    if not a.constraint:
        refuse("a price needs --constraint; a marginal rate is only defined at a named constraint")
    units.get(a.constraint)
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        ev = {"seq": next_seq(evs), "type": "PRICE", "at": now(), "by": a.by,
              "from_unit": a.from_unit, "to_unit": a.to_unit, "rate": rate,
              "from_dimension": src_u["dimension"], "to_dimension": dst_u["dimension"],
              "n": int(a.n), "window": a.window, "constraint": a.constraint, "source": source,
              "min_n": min_n, "min_n_source": min_n_source,
              "note": "valid only inside `window`, only at `constraint`, and only for the margin measured"}
        head = append(a.ledger, [ev], head)
    print(f"PRICE 1 {a.from_unit} = {rate} {a.to_unit} at {a.constraint} over {a.window} (n={a.n}); head {head}")
    return 0


def cmd_close(a) -> int:
    source = require_source(a.source, "CLOSE")
    with ledger_lock(a.ledger):
        evs, head = load_chain(a.ledger)
        state = project(evs)
        o = state["orders"].get(a.order_id)
        if o is None:
            refuse(f"unknown order {a.order_id!r}")
        if o["closed"]:
            refuse(f"order {a.order_id!r} is already closed")
        ev = {"seq": next_seq(evs), "type": "CLOSE", "at": now(), "by": a.by,
              "order_id": a.order_id, "source": source,
              "spent": o["spent"], "yielded": o["yielded"]}
        head = append(a.ledger, [ev], head)
    print(f"CLOSE {a.order_id} spent={o['spent']} yielded={o['yielded']}; head {head}")
    return 0


def density(order: dict, constraint_unit: str, units: "Units | None" = None) -> float | None:
    """Evidence yield per constraint unit.

    The numerator is ONE dimension. Summing every yielded unit would add
    EVID-row to RAT-art as if they shared a scale, which is the commensurability
    the registry denies — and it is not the identity RESOURCE_UNITS.yaml states
    (`Σ yield(order, evidence units) / spend(order, constraint unit)`). Without a
    registry to classify by, only the units known to be in the density dimension
    are counted. Per-unit figures come from density_by_unit().
    """
    spend = order["spent"].get(constraint_unit)
    if not spend:
        return None
    if units is not None:
        numerator = sum(q for sym, q in order["yielded"].items()
                        if units.by_symbol.get(sym, {}).get("dimension") == DENSITY_DIMENSION)
    else:
        numerator = sum(q for sym, q in order["yielded"].items() if sym in ("EVID-row", "CAL-pt"))
    return round(numerator / spend, 4)


def density_by_unit(order: dict, constraint_unit: str) -> dict:
    """Every output unit's yield per constraint unit, kept separate."""
    spend = order["spent"].get(constraint_unit)
    if not spend:
        return {}
    return {sym: round(q / spend, 4) for sym, q in order["yielded"].items()}


def cmd_status(a) -> int:
    units = Units(Path(a.units))
    evs, _ = load_chain(a.ledger)
    state = project(evs)
    print(f"RESOURCE_LEDGER — {len(evs)} events, head {evs[-1]['hash'][:16] if evs else '—'}…")
    g = state["genesis"] or {}
    pin = registry_pin_status(evs, units)
    print(f"units registry {g.get('units_registry')} sha {str(pin['pinned_sha256'])[:16]}… "
          f"[{g.get('units_registry_status')}]"
          f"{'  ⚠ DRIFT — on disk ' + pin['current_sha256'][:16] + '…' if pin['drift'] else ''}")
    print(f"constraint unit: {units.constraint}  ·  shadow-price min n: {units.min_n[0]} ({units.min_n[1]})")
    print("\nCAPACITIES")
    if not state["capacity"]:
        print("  (none declared — every utilization figure is undefined)")
    for sym, cap in state["capacity"].items():
        print(f"  {sym:<12}{cap['qty']:>10} per {cap['period']}   by {cap['by']}"
              f"{' hash ' + str(cap['hash'])[:12] if cap.get('hash') else ''}")
    print("\nSPENT / YIELDED / WASTE")
    for label, book in (("spend", state["spent"]), ("yield", state["yielded"]), ("waste", state["waste"])):
        for sym, qty in sorted(book.items()):
            cap = state["capacity"].get(sym)
            util = f"   utilization {round(qty / cap['qty'], 3)}" if (cap and label == "spend") else ""
            print(f"  {label:<7}{sym:<12}{qty:>10}{util}")
    print("\nORDERS")
    for oid, o in state["orders"].items():
        d = density(o, units.constraint, units)
        print(f"  {oid:<24}{'CLOSED' if o['closed'] else 'OPEN':<8}"
              f"budget={o['budget']} spent={o['spent']} yield={o['yielded']} "
              f"density={d if d is not None else 'undefined'} "
              f"({DENSITY_DIMENSION} per {units.constraint})")
    return 0


def cmd_report(a) -> int:
    units = Units(Path(a.units))
    evs, _ = load_chain(a.ledger)
    state = project(evs)
    closed = {k: v for k, v in state["orders"].items() if v["closed"]}
    out = {
        "ledger_events": len(evs),
        "constraint_unit": units.constraint,
        "closed_orders": len(closed),
        "density_dimension": DENSITY_DIMENSION,
        "yield_density": {k: density(v, units.constraint, units) for k, v in closed.items()},
        "yield_density_by_unit": {k: density_by_unit(v, units.constraint) for k, v in closed.items()},
        # Deliberately NOT "prices_in_force": `window` is free text (a sprint
        # label, a date range, a cycle id), so no machine here can tell whether a
        # window has closed. Calling these "in force" would assert an expiry
        # check that does not exist. The reader evaluates the window.
        "prices_recorded": [
            {"from": p["from_unit"], "to": p["to_unit"], "rate": p["rate"], "n": p["n"],
             "window": p["window"], "constraint": p["constraint"], "source": p["source"],
             "at": p.get("at")}
            for p in state["prices"]
        ],
        "prices_note": ("a rate is valid only inside its window, only at its constraint, and only "
                        "for the margin measured; windows are not machine-evaluated"),
        "units_registry_pin": registry_pin_status(evs, units),
        "capacities": state["capacity"],
        "spent": state["spent"],
        "yielded": state["yielded"],
        "waste": state["waste"],
    }
    if not closed:
        out["note"] = ("No closed orders. Yield density is undefined — the regime is installed "
                       "but not yet measured.")
    print(json.dumps(out, indent=2))
    return 0


# ---------------------------------------------------------------- smoke test
def run_smoke_test() -> int:
    """Exercise the chain and every refusal on a scratch ledger."""
    import subprocess
    import tempfile

    me = [sys.executable, str(Path(__file__).resolve())]

    def run(args, expect_fail=False):
        r = subprocess.run(me + args, capture_output=True, text=True)
        failed = r.returncode != 0
        assert failed == expect_fail, f"{args} → rc={r.returncode}\n{r.stdout}{r.stderr}"
        return r

    with tempfile.TemporaryDirectory() as td:
        led = str(Path(td) / "L.jsonl")
        run(["init", led])
        run(["init", led], expect_fail=True)                                    # double init
        run(["claim", led, "Q-X", "--budget", "RAT-min=30,Z1-ktok=40", "--by", "Z1"])
        run(["claim", led, "Q-Y", "--budget", "Z1-ktok=40", "--by", "Z1"], expect_fail=True)   # unpriced
        run(["claim", led, "Q-Z", "--budget", "NOPE-unit=1", "--by", "Z1"], expect_fail=True)  # unknown unit
        run(["claim", led, "Q-T", "--budget", "TRUST-pt=1", "--by", "Z1"], expect_fail=True)   # CANDIDATE unit
        run(["claim", led, "Q-FREE", "--budget", "RAT-min=0,Z1-ktok=5", "--by", "Z1"])         # Band A
        run(["spend", led, "Q-X", "RAT-min", "12", "--by", "Z2"], expect_fail=True)            # no source
        run(["spend", led, "Q-X", "RAT-min", "12", "--by", "Z2", "--source", "sha:abc"])
        run(["spend", led, "Q-X", "RAT-min", "-1", "--by", "Z2", "--source", "s"], expect_fail=True)
        run(["spend", led, "Q-X", "RAT-min", "nan", "--by", "Z2", "--source", "s"], expect_fail=True)
        run(["spend", led, "Q-X", "RAT-min", "inf", "--by", "Z2", "--source", "s"], expect_fail=True)
        run(["spend", led, "Q-X", "RAT-min", "0", "--by", "Z2", "--source", "s"], expect_fail=True)
        run(["spend", led, "Q-X", "EVID-row", "1", "--by", "Z3", "--source", "s"], expect_fail=True)
        run(["spend", led, "Q-NOPE", "RAT-min", "1", "--by", "Z2", "--source", "s"], expect_fail=True)
        run(["yield", led, "Q-X", "EVID-row", "2", "--by", "Z3", "--source", "sha:def"])
        run(["yield", led, "Q-X", "RAT-min", "2", "--by", "Z3", "--source", "s"], expect_fail=True)
        run(["waste", led, "GAP-row", "1", "--by", "Z1", "--source", "recon-run"])
        run(["waste", led, "RAT-min", "1", "--by", "Z1", "--source", "s"], expect_fail=True)
        run(["cap", led, "RAT-min", "120", "--by", "Z1", "--source", "guess"], expect_fail=True)  # not Z2
        run(["cap", led, "RAT-min", "120", "--by", "Z2", "--source", "decl",
             "--hash", "deadbeef"], expect_fail=True)                                   # not a sha256
        run(["cap", led, "RAT-min", "120", "--by", "Z2", "--source", "decl", "--hash", "a" * 64])
        run(["price", led, "RAT-min", "Z3-hr", "0.5", "--n", "3", "--window", "w",
             "--constraint", "RAT-min", "--source", "s", "--by", "Z1"], expect_fail=True)        # n too low
        run(["price", led, "RAT-min", "Z3-hr", "0.5", "--n", "10", "--constraint", "RAT-min",
             "--source", "s", "--by", "Z1"], expect_fail=True)                                   # no window
        run(["price", led, "EVID-row", "CAL-pt", "1", "--n", "10", "--window", "w",
             "--constraint", "RAT-min", "--source", "s", "--by", "Z1"], expect_fail=True)  # same dimension
        run(["price", led, "RAT-min", "Z3-hr", "0.5", "--n", "10", "--window", "2026-W37",
             "--constraint", "RAT-min", "--source", "sha:ghi", "--by", "Z1"])
        run(["close", led, "Q-X", "--by", "Z1", "--source", "sha:jkl"])
        run(["close", led, "Q-X", "--by", "Z1", "--source", "s"], expect_fail=True)             # double close
        run(["spend", led, "Q-X", "RAT-min", "1", "--by", "Z2", "--source", "s"], expect_fail=True)  # after close
        run(["verify", led])

        rep = json.loads(run(["report", led]).stdout)
        assert rep["yield_density"]["Q-X"] == round(2 / 12, 4), rep
        assert rep["yield_density_by_unit"]["Q-X"] == {"EVID-row": round(2 / 12, 4)}, rep
        assert len(rep["prices_recorded"]) == 1, rep
        assert rep["units_registry_pin"]["drift"] is False, rep
        run(["status", led])

        # tamper detection
        lines = Path(led).read_text(encoding="utf-8").splitlines()
        obj = json.loads(lines[1])
        obj["budget"]["RAT-min"] = 1
        lines[1] = json.dumps(obj, sort_keys=True)
        Path(led).write_text("\n".join(lines) + "\n", encoding="utf-8")
        run(["verify", led], expect_fail=True)

    print("smoke-test OK")
    return 0


# ---------------------------------------------------------------- main
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Append-only resource ledger (claims, spends, yields)")
    ap.add_argument("--smoke-test", action="store_true")
    ap.add_argument("--units", default=str(UNITS_PATH))
    sub = ap.add_subparsers(dest="command")

    def common(p, order=True):
        p.add_argument("ledger")
        p.add_argument("--by", default="Z1")
        p.add_argument("--source", default=None)
        p.add_argument("--units", default=str(UNITS_PATH))
        return p

    p = common(sub.add_parser("init")); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("verify"); p.add_argument("ledger"); p.add_argument("--units", default=str(UNITS_PATH))
    p.add_argument("--strict-pin", dest="strict_pin", action="store_true",
                   help="exit 1 when the units registry has drifted from the chain's pin")
    p.set_defaults(fn=cmd_verify)

    p = common(sub.add_parser("repin"))
    p.add_argument("--reason", default="")
    p.set_defaults(fn=cmd_repin)

    p = common(sub.add_parser("cap"))
    p.add_argument("unit"); p.add_argument("qty", type=float)
    p.add_argument("--period", default=None); p.add_argument("--hash", default=None)
    p.set_defaults(fn=cmd_cap)

    p = common(sub.add_parser("claim"))
    p.add_argument("order_id"); p.add_argument("--budget", required=True); p.add_argument("--title", default="")
    p.set_defaults(fn=cmd_claim)

    p = common(sub.add_parser("spend"))
    p.add_argument("order_id"); p.add_argument("unit"); p.add_argument("qty", type=float)
    p.add_argument("--obligation-class", dest="obligation_class", default=None)
    p.set_defaults(fn=cmd_spend)

    p = common(sub.add_parser("yield"))
    p.add_argument("order_id"); p.add_argument("unit"); p.add_argument("qty", type=float)
    p.set_defaults(fn=cmd_yield)

    p = common(sub.add_parser("waste"))
    p.add_argument("unit"); p.add_argument("qty", type=float); p.add_argument("--order-id", dest="order_id", default=None)
    p.set_defaults(fn=cmd_waste)

    p = common(sub.add_parser("price"))
    p.add_argument("from_unit"); p.add_argument("to_unit"); p.add_argument("rate", type=float)
    p.add_argument("--n", type=int, default=None); p.add_argument("--window", default=None)
    p.add_argument("--constraint", default=None)
    p.set_defaults(fn=cmd_price)

    p = common(sub.add_parser("close")); p.add_argument("order_id"); p.set_defaults(fn=cmd_close)
    p = sub.add_parser("status"); p.add_argument("ledger"); p.add_argument("--units", default=str(UNITS_PATH))
    p.set_defaults(fn=cmd_status)
    p = sub.add_parser("report"); p.add_argument("ledger"); p.add_argument("--units", default=str(UNITS_PATH))
    p.set_defaults(fn=cmd_report)
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    a = ap.parse_args(argv)
    if a.smoke_test:
        return run_smoke_test()
    if not getattr(a, "fn", None):
        ap.print_help()
        return 2
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

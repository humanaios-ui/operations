#!/usr/bin/env python3
"""
resource_census_v0_1.py — measure the resource state of the operations tree.
Builder v1.7 compliant
HumanAIOS — RBE-OPS v0.1 (Q-RBE-01), the demand side of the constraint

Answers one question mechanically: how much of the binding constraint does the
organization currently owe, and what stock of output does it hold against that?

  census                 count obligations, stocks and waste; write outputs/resource_census.json
  units                  print the registered unit map (symbol, dimension, kind, instrument)
  --capacity <n>         RAT-min per week, if Z2 has declared one; utilization is null without it

What it does NOT do: it does not invent a capacity, it does not convert between
dimensions, and it does not claim a measured price where only a prior exists.
Every number it emits carries a `basis` of MEASURED or PRIOR and a `source`.

Counting rules (all mechanical, all re-runnable):
  * registry_candidate      REGISTERED.md front-matter `status: CANDIDATE|PENDING_ZONE2`
  * nf_token_date           NF_LEDGER tokens still in state PENDING_Z2_DATE
  * nf_z2_prior             NF_LEDGER PIN events with predictor Z2 and p == null
  * nf_past_date_resolution DATED tokens whose date is in the past with no RESOLVE
  * constant_ratification   constants.json entries with molt_id == null
  * queue_row_ratification  PRIORITY_QUEUE.md rows marked BLOCKED or PROPOSED
  * queue_hash              PRIORITY_QUEUE.md ratification_hash unsigned (0 or 1)
  * doc_owner_approval      document-registry.yaml documents with status draft|review
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

TOOL_NAME = "resource_census"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1

ROOT = Path(__file__).resolve().parent.parent
UNITS_PATH = ROOT / "RESOURCE_UNITS.yaml"
DEFAULT_OUT = ROOT / "outputs" / "resource_census.json"

# Sensitivity ladder for clearance time. Not a capacity claim — a table of
# "if Z2 could spend X, the backlog clears in Y weeks", printed so the declared
# capacity that eventually lands has something to be compared against.
SENSITIVITY_RAT_MIN_PER_WEEK = (30, 60, 120, 240, 480)


# ---------------------------------------------------------------- helpers
def load_units(path: Path) -> dict:
    import yaml  # deferred: the smoke test runs without a registry on disk

    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


def read_jsonl(path: Path) -> list[dict]:
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    except FileNotFoundError:
        return []
    return out


def obs(count: int, basis: str, source: str, note: str | None = None) -> dict:
    rec = {"count": count, "basis": basis, "source": source}
    if note:
        rec["note"] = note
    return rec


# ---------------------------------------------------------------- counters
_STATUS_RE = re.compile(r"(?mi)^status:\s*([A-Z_]+)\s*$")


def count_registry_candidates(root: Path) -> dict:
    """F/IC/H entries awaiting a Z2 disposition."""
    text = read_text(root / "REGISTERED.md")
    statuses = [m.group(1).upper() for m in _STATUS_RE.finditer(text)]
    open_ = sum(1 for s in statuses if s in ("CANDIDATE", "PENDING_ZONE2"))
    ratified = sum(1 for s in statuses if s in ("REGISTERED", "ACTIVE", "CONFIRMED"))
    return {
        "open": obs(open_, "MEASURED", "REGISTERED.md front-matter status fields"),
        "ratified": obs(ratified, "MEASURED", "REGISTERED.md front-matter status fields"),
    }


def project_nf(events: list[dict]) -> tuple[dict, dict]:
    """Token and pin state, following tools/nf_ledger_v0_1.py:project()."""
    tokens: dict[str, dict] = {}
    pins: dict[str, dict] = {}
    for e in events:
        t = e.get("type")
        if t == "TOKEN":
            tokens[e["token_id"]] = dict(e, resolved=None)
        elif t == "PIN":
            pins[e["pin_id"]] = dict(e)
        elif t == "DATE":
            tk = tokens.get(e["token_id"])
            if tk:
                tk.update(date=e["date"], date_source="Z2", state="DATED")
            for p in pins.values():
                if p.get("target") == e["token_id"]:
                    p["scoreable"] = True
        elif t == "RESOLVE":
            tk = tokens.get(e["token_id"])
            if tk:
                tk["resolved"] = e.get("outcome")
                tk["state"] = "RESOLVED"
                tk["resolve_source"] = e.get("source")
        elif t == "STRIKE":
            tk = tokens.get(e["token_id"])
            if tk:
                tk["state"] = "STRUCK"
    return tokens, pins


def count_nf(root: Path, today: date) -> dict:
    path = root / "ledgers" / "NF_LEDGER.jsonl"
    events = read_jsonl(path)
    src = "ledgers/NF_LEDGER.jsonl"
    if not events:
        empty = obs(0, "MEASURED", src, "ledger absent or empty")
        return {k: empty for k in
                ("pending_date", "empty_z2_prior", "past_date_unresolved", "evidence_rows", "calibration_points")}

    tokens, pins = project_nf(events)

    pending = sum(1 for t in tokens.values() if t.get("state") == "PENDING_Z2_DATE")
    empty_z2 = sum(1 for p in pins.values() if p.get("predictor") == "Z2" and p.get("p") is None)

    past = 0
    for t in tokens.values():
        if t.get("state") != "DATED" or t.get("resolved") is not None:
            continue
        try:
            d = datetime.strptime(str(t.get("date")), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            continue
        if d < today:
            past += 1

    evidence = sum(1 for e in events if e.get("type") == "RESOLVE" and e.get("source"))

    # A pin scores only if every token behind it is resolved and none is still
    # awaiting a Z2 date — the VOID rule in nf_ledger_v0_1.pin_outcome().
    cal = 0
    for p in pins.values():
        ids = p.get("tokens") or [p.get("target")]
        outs = []
        void = False
        for i in ids:
            tk = tokens.get(i)
            if tk is None or tk.get("state") == "PENDING_Z2_DATE":
                void = True
                break
            if tk.get("state") == "STRUCK":
                continue
            if tk.get("resolved") is None:
                void = True
                break
            outs.append(tk["resolved"] == "YES")
        if not void and outs and p.get("p") is not None:
            cal += 1

    return {
        "pending_date": obs(pending, "MEASURED", src + " (tokens in PENDING_Z2_DATE)"),
        "empty_z2_prior": obs(empty_z2, "MEASURED", src + " (PIN predictor=Z2, p=null)"),
        "past_date_unresolved": obs(past, "MEASURED", src + f" (DATED, date < {today.isoformat()}, unresolved)"),
        "evidence_rows": obs(evidence, "MEASURED", src + " (RESOLVE events carrying a source)"),
        "calibration_points": obs(cal, "MEASURED", src + " (pins resolvable to 1.0/0.0)"),
    }


def count_constants(root: Path) -> dict:
    path = root / "constants.json"
    try:
        data = json.loads(read_text(path) or "{}")
    except json.JSONDecodeError:
        data = {}
    consts = data.get("constants", [])
    unratified = sum(1 for c in consts if c.get("molt_id") in (None, "", "null"))
    return {
        "unratified": obs(unratified, "MEASURED", "constants.json (molt_id == null)"),
        "total": obs(len(consts), "MEASURED", "constants.json"),
        "ratified": obs(len(consts) - unratified, "MEASURED", "constants.json (molt_id non-null)"),
    }


_QUEUE_ROW_RE = re.compile(r"(?m)^###\s+(Q-[A-Z0-9-]+)")
_QUEUE_HASH_RE = re.compile(r"(?mi)^\|\s*\*\*ratification_hash\*\*\s*\|\s*(.+?)\s*\|")


def count_queue(root: Path) -> dict:
    text = read_text(root / "PRIORITY_QUEUE.md")
    src = "PRIORITY_QUEUE.md"
    rows = _QUEUE_ROW_RE.findall(text)
    # A row heading carries its own status marker after the id ("◆ READY",
    # "◆ BLOCKED — ...", "◆ PROPOSED"). Both BLOCKED and PROPOSED rows are
    # waiting on a Z2 act, so both are obligations; READY rows are not.
    blocked = len(re.findall(r"(?m)^###\s+Q-[A-Z0-9-]+\s*◆[^\n]*(?:BLOCKED|PROPOSED)", text))
    m = _QUEUE_HASH_RE.search(text)
    unsigned = 1 if (m is None or m.group(1).strip() in ("—", "-", "", "null", "pending")
                     or "pending" in m.group(1).lower()) else 0
    return {
        "rows": obs(len(rows), "MEASURED", src),
        "blocked": obs(blocked, "MEASURED", src + " (row heading marked BLOCKED)"),
        "unsigned_queue": obs(unsigned, "MEASURED", src + " (queue metadata ratification_hash)"),
    }


def count_docs(root: Path) -> dict:
    src = "document-registry.yaml"
    try:
        import yaml

        data = yaml.safe_load(read_text(root / src) or "{}") or {}
    except Exception:
        return {"awaiting_approval": obs(0, "MEASURED", src, "registry unreadable")}
    docs = data.get("documents", []) or []
    awaiting = sum(1 for d in docs if str(d.get("status", "")).lower() in ("draft", "review"))
    return {
        "awaiting_approval": obs(awaiting, "MEASURED", src + " (status draft|review)"),
        "total": obs(len(docs), "MEASURED", src),
    }


def count_waste(root: Path) -> dict:
    """GAP-row and STALE-day. Both report honestly when the instrument is silent."""
    queue = read_text(root / "PRIORITY_QUEUE.md")
    gaps = len(re.findall(r"RECEIPT-GAP", queue))
    try:
        consts = json.loads(read_text(root / "constants.json") or "{}").get("constants", [])
    except json.JSONDecodeError:
        consts = []
    unratified = [c for c in consts if not c.get("ratified_at")]
    stale = {
        "count": None,
        "basis": "UNMEASURED",
        "source": "constants.json (ratified_at)",
        "note": (f"{len(unratified)} of {len(consts)} constants have no ratified_at timestamp; "
                 "decay from a ratification that never happened is undefined, not zero"),
    }
    return {
        "gap_rows": obs(gaps, "MEASURED", "PRIORITY_QUEUE.md (RECEIPT-GAP mentions)",
                        "textual mention count, not a reconciliation run"),
        "stale_days": stale,
    }


# ---------------------------------------------------------------- census
def run_census(root: Path, units: dict, capacity: float | None, today: date) -> dict:
    priors = (units.get("demand_priors") or {}).get("classes", {})
    constraint_unit = (units.get("constraint") or {}).get("unit", "RAT-min")

    reg = count_registry_candidates(root)
    nf = count_nf(root, today)
    const = count_constants(root)
    queue = count_queue(root)
    docs = count_docs(root)
    waste = count_waste(root)

    # class -> measured count
    demand_counts = {
        "registry_candidate": reg["open"],
        "nf_token_date": nf["pending_date"],
        "nf_z2_prior": nf["empty_z2_prior"],
        "nf_past_date_resolution": nf["past_date_unresolved"],
        "constant_ratification": const["unratified"],
        "queue_row_ratification": queue["blocked"],
        "queue_hash": queue["unsigned_queue"],
        "doc_owner_approval": docs["awaiting_approval"],
    }

    obligations = {}
    debt = 0
    missing_price = []
    for cls, rec in demand_counts.items():
        prior = priors.get(cls, {})
        price = prior.get("rat_min")
        if price is None:
            missing_price.append(cls)
            load = None
        else:
            load = rec["count"] * price
            debt += load
        obligations[cls] = {
            **rec,
            "price_rat_min": price,
            "price_basis": "PRIOR" if price is not None else "UNPRICED",
            "load_rat_min": load,
        }

    open_obligations = sum(r["count"] for r in demand_counts.values())

    clearance = {}
    for cap in SENSITIVITY_RAT_MIN_PER_WEEK:
        clearance[str(cap)] = round(debt / cap, 2)

    utilization = None
    weeks_to_clear = None
    if capacity:
        utilization = round(debt / capacity, 3)
        weeks_to_clear = round(debt / capacity, 2)

    return {
        "version": f"{TOOL_NAME}_v{TOOL_VERSION}",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "units_registry": {
            "path": "RESOURCE_UNITS.yaml",
            "version": units.get("version"),
            "status": units.get("status"),
            "ratification_hash": units.get("ratification_hash"),
        },
        "constraint": {
            "unit": constraint_unit,
            "capacity_per_week": capacity,
            "capacity_basis": "DECLARED" if capacity else "UNMEASURED",
            "utilization": utilization,
            "weeks_to_clear": weeks_to_clear,
            "note": None if capacity else
            "No Z2 capacity declaration. Utilization and clearance time are undefined; the "
            "sensitivity table below is the only statement this census can make about them.",
        },
        "obligations": {
            "open_items": open_obligations,
            "debt_rat_min": debt,
            "debt_basis": "PRIOR",
            "unpriced_classes": missing_price,
            "by_class": obligations,
        },
        "clearance_sensitivity_weeks": clearance,
        "stocks": {
            "EVID-row": nf["evidence_rows"],
            "CAL-pt": nf["calibration_points"],
            "RAT-art": {
                "count": reg["ratified"]["count"] + const["ratified"]["count"],
                "basis": "MEASURED",
                "source": "REGISTERED.md (REGISTERED/ACTIVE/CONFIRMED) + constants.json (molt_id non-null)",
            },
        },
        "liabilities": {
            "OBL-open": obs(open_obligations, "MEASURED", "sum of obligation classes"),
            "GAP-row": waste["gap_rows"],
            "STALE-day": waste["stale_days"],
        },
        "input_units": {
            "Z1-ktok": {
                "capacity": 100, "capacity_unit": "per session", "capacity_basis": "DECLARED",
                "demand": None, "utilization": None,
                "source": "behavior_spec.json caps.token_budget_per_session",
            },
            "Z3-hr": {"capacity": None, "capacity_basis": "UNMEASURED", "demand": None, "utilization": None,
                      "source": "ZONE_REGISTRY.md — most executor seats TBD"},
            "CI-min": {"capacity": None, "capacity_basis": "UNMEASURED", "demand": None, "utilization": None,
                       "source": "GitHub Actions billing (not read into tree)"},
            "RUN-day": {"capacity": None, "capacity_basis": "UNMEASURED", "demand": None, "utilization": None,
                        "source": "Class 1 live state (WGS) — deliberately not restated in-tree"},
            "SPEC-hr": {"capacity": None, "capacity_basis": "UNMEASURED", "demand": None, "utilization": None,
                        "source": "specimen-intake cycles; private register off-tree"},
        },
        "yield_density": {
            "value": None,
            "basis": "UNMEASURED",
            "note": ("Yield per constraint-minute needs at least one SPEND row in "
                     "ledgers/RESOURCE_LEDGER.jsonl. None exist at census time: nothing has been "
                     "measured in RAT-min yet, only imputed from priors."),
        },
    }


# ---------------------------------------------------------------- reporting
def print_report(c: dict) -> None:
    print(f"RESOURCE CENSUS — {c['generated_at']}")
    print(f"units registry {c['units_registry']['path']} v{c['units_registry']['version']} "
          f"[{c['units_registry']['status']}]")
    print()
    print(f"CONSTRAINT: {c['constraint']['unit']}  capacity="
          f"{c['constraint']['capacity_per_week'] or 'UNMEASURED'}  "
          f"utilization={c['constraint']['utilization'] if c['constraint']['utilization'] is not None else 'undefined'}")
    print()
    print("OPEN OBLIGATIONS (liability in the constraint unit)")
    print(f"  {'class':<26}{'n':>5}{'RAT-min ea':>12}{'load':>8}")
    for cls, rec in c["obligations"]["by_class"].items():
        price = rec["price_rat_min"]
        load = rec["load_rat_min"]
        print(f"  {cls:<26}{rec['count']:>5}{(price if price is not None else '—'):>12}"
              f"{(load if load is not None else '—'):>8}")
    print(f"  {'TOTAL':<26}{c['obligations']['open_items']:>5}{'':>12}"
          f"{c['obligations']['debt_rat_min']:>8}   (basis: PRIOR)")
    print()
    print("WEEKS TO CLEAR, by hypothetical Z2 capacity (RAT-min/week)")
    for cap, weeks in c["clearance_sensitivity_weeks"].items():
        print(f"  {cap:>5} min/wk → {weeks:>6} weeks")
    print()
    print("STOCKS")
    for sym, rec in c["stocks"].items():
        print(f"  {sym:<12}{rec['count']:>6}   [{rec['basis']}]")
    print("LIABILITIES")
    for sym, rec in c["liabilities"].items():
        n = rec["count"]
        print(f"  {sym:<12}{(n if n is not None else 'undefined'):>6}   [{rec['basis']}]")
    print()
    print(f"yield density: {c['yield_density']['basis']} — {c['yield_density']['note']}")


def cmd_units(root: Path) -> int:
    units = load_units(UNITS_PATH)
    print(f"{'symbol':<12}{'dimension':<16}{'kind':<8}{'sign':<10}{'status':<12}instrument")
    for u in units.get("units", []):
        inst = (u.get("instrument") or {}).get("primary") or "—"
        print(f"{u['symbol']:<12}{u['dimension']:<16}{u.get('kind', '—'):<8}"
              f"{u.get('sign', '—'):<10}{u.get('status', '—'):<12}{inst[:60]}")
    return 0


# ---------------------------------------------------------------- smoke test
def run_smoke_test() -> int:
    """Self-test on a synthetic tree; no network, no writes outside tmp."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "ledgers").mkdir()
        (root / "REGISTERED.md").write_text(
            "---\nid: \"F-1\"\nstatus: CANDIDATE\n---\nx\n"
            "---\nid: \"F-2\"\nstatus: REGISTERED\n---\ny\n", encoding="utf-8")
        (root / "constants.json").write_text(json.dumps(
            {"constants": [{"name": "A", "molt_id": None}, {"name": "B", "molt_id": "M-1",
                                                            "ratified_at": "2026-01-01T00:00:00Z"}]}),
            encoding="utf-8")
        (root / "PRIORITY_QUEUE.md").write_text(
            "| **ratification_hash** | — (pending Z2 signature) |\n"
            "### Q-A ◆ READY\n### Q-B ◆ BLOCKED — waiting\n", encoding="utf-8")
        (root / "document-registry.yaml").write_text(
            "documents:\n  - doc_id: D-1\n    status: draft\n  - doc_id: D-2\n    status: approved\n",
            encoding="utf-8")
        events = [
            {"type": "TOKEN", "token_id": "T1", "state": "PENDING_Z2_DATE", "date": "2026-01-01"},
            {"type": "TOKEN", "token_id": "T2", "state": "DATED", "date": "2026-01-01"},
            {"type": "PIN", "pin_id": "T2:Z1", "target": "T2", "predictor": "Z1", "p": 0.7},
            {"type": "PIN", "pin_id": "P:Z2", "target": "P", "predictor": "Z2", "p": None},
            {"type": "RESOLVE", "token_id": "T2", "outcome": "YES", "source": "sha:abc"},
        ]
        with open(root / "ledgers" / "NF_LEDGER.jsonl", "w", encoding="utf-8") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")

        units = load_units(UNITS_PATH)
        c = run_census(root, units, capacity=None, today=date(2026, 6, 1))

        by = c["obligations"]["by_class"]
        assert by["registry_candidate"]["count"] == 1, by["registry_candidate"]
        assert by["nf_token_date"]["count"] == 1, by["nf_token_date"]
        assert by["nf_z2_prior"]["count"] == 1, by["nf_z2_prior"]
        assert by["constant_ratification"]["count"] == 1, by["constant_ratification"]
        assert by["queue_row_ratification"]["count"] == 1, by["queue_row_ratification"]
        assert by["queue_hash"]["count"] == 1, by["queue_hash"]
        assert by["doc_owner_approval"]["count"] == 1, by["doc_owner_approval"]
        assert c["stocks"]["EVID-row"]["count"] == 1, c["stocks"]
        assert c["stocks"]["CAL-pt"]["count"] == 1, c["stocks"]
        assert c["constraint"]["utilization"] is None, "utilization must stay undefined without a capacity"
        assert c["obligations"]["debt_rat_min"] > 0, c["obligations"]
        assert c["obligations"]["debt_basis"] == "PRIOR"

        # A declared capacity turns utilization on, and only then.
        c2 = run_census(root, units, capacity=120.0, today=date(2026, 6, 1))
        assert c2["constraint"]["utilization"] is not None

    print("smoke-test OK")
    return 0


# ---------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Resource census over the operations tree")
    ap.add_argument("command", nargs="?", default="census", choices=["census", "units"])
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--units", default=str(UNITS_PATH))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--capacity", type=float, default=None,
                    help="Z2 RAT-min per week, if declared. Omitted → utilization stays undefined.")
    ap.add_argument("--json", action="store_true", help="print the census JSON instead of the table")
    ap.add_argument("--no-write", action="store_true")
    ap.add_argument("--smoke-test", action="store_true")
    a = ap.parse_args(argv)

    if a.smoke_test:
        return run_smoke_test()
    if a.command == "units":
        return cmd_units(Path(a.root))

    units = load_units(Path(a.units))
    census = run_census(Path(a.root), units, a.capacity, date.today())

    if not a.no_write:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(census, indent=2) + "\n", encoding="utf-8")
        if not a.json:
            print(f"wrote {os.path.relpath(out, ROOT)}\n")

    if a.json:
        print(json.dumps(census, indent=2))
    else:
        print_report(census)
    return 0


if __name__ == "__main__":
    sys.exit(main())

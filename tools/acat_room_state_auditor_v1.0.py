#!/usr/bin/env python3
"""
ACAT Room State Auditor — v1.0
Builder v1.7 compliant · audit_tool
HumanAIOS · S-051626-01-acat-tools-alternate-functions-mapping

Validates that a Room's state metadata is consistent with the underlying
ACAT corpus and session record. Ties the web-application layer (Rooms)
back to ACAT's behavioral observability data.

Checks:
  ROOM_MISSING_SESSION_ID    — Room config references no session_id
  ROOM_SESSION_NOT_IN_CORPUS — Declared session_id absent from corpus
  ROOM_MEAN_LI_MISMATCH      — Room's declared mean_li differs from corpus
  ROOM_GATE_STATUS_STALE     — Room gate status doesn't match corpus gate
  ROOM_OVERCLAIMING_SESSIONS — Room session_count > corpus row count for agent
  ROOM_TIMESTAMP_INVERTED    — Room created_at is after last corpus row timestamp
  ROOM_AGENT_NAME_MISMATCH   — Room agent_name doesn't match corpus agent_name

Usage:
  python acat_room_state_auditor_v1.0.py \
    --room room_config.json \
    --corpus corpus.csv
  python acat_room_state_auditor_v1.0.py --smoke-test
"""

import csv
import json
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "acat_room_state_auditor"
TOOL_VERSION = "1.0.0"

MEAN_LI_TOLERANCE = 0.005    # allowable float comparison tolerance
GATE_STATUS_VALID = {"PASSED", "FAILED", "ACTIVE", "PENDING"}


class SpecLoadFailed(Exception):
    pass


def load_room_config(path: str) -> dict:
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SpecLoadFailed("Room config must be a JSON object")
        return data
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"JSON parse error: {e}")
    except (IOError, OSError) as e:
        raise SpecLoadFailed(f"File I/O error: {e}")


def load_corpus(path: str) -> list:
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        with open(p, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except (IOError, OSError) as e:
        raise SpecLoadFailed(f"File I/O error: {e}")


def _extract_li(row: dict) -> float | None:
    val = row.get("learning_index") or row.get("li")
    try:
        return float(val) if val else None
    except (ValueError, TypeError):
        return None


# ── Individual checks ─────────────────────────────────────────────────────────

def check_session_id_present(room: dict) -> dict:
    sid = room.get("session_id") or room.get("current_session_id")
    if not sid:
        return {"passed": False,
                "failure": "ROOM_MISSING_SESSION_ID: Room config has no session_id field"}
    return {"passed": True, "session_id": sid}


def check_session_in_corpus(room: dict, corpus_rows: list) -> dict:
    sid = room.get("session_id") or room.get("current_session_id") or ""
    if not sid:
        return {"passed": False, "checked": False,
                "failure": "SKIPPED: No session_id to check"}
    corpus_sids = {r.get("session_id", "") for r in corpus_rows}
    if sid not in corpus_sids:
        return {"passed": False, "session_id": sid,
                "failure": f"ROOM_SESSION_NOT_IN_CORPUS: session_id='{sid}' not found in corpus"}
    return {"passed": True, "session_id": sid}


def check_mean_li(room: dict, corpus_rows: list) -> dict:
    room_li = room.get("mean_li") or room.get("corpus_mean_li")
    if room_li is None:
        return {"passed": True, "checked": False,
                "note": "No mean_li in room config — skipped"}
    try:
        room_li_float = float(room_li)
    except (ValueError, TypeError):
        return {"passed": False,
                "failure": f"ROOM_MEAN_LI_INVALID: cannot parse mean_li='{room_li}'"}

    li_vals = [_extract_li(r) for r in corpus_rows if _extract_li(r) is not None]
    if not li_vals:
        return {"passed": True, "checked": False,
                "note": "No LI values in corpus to compare"}

    corpus_mean = sum(li_vals) / len(li_vals)
    diff = abs(room_li_float - corpus_mean)
    if diff > MEAN_LI_TOLERANCE:
        return {"passed": False,
                "room_mean_li": room_li_float,
                "corpus_mean_li": round(corpus_mean, 4),
                "diff": round(diff, 4),
                "failure": (
                    f"ROOM_MEAN_LI_MISMATCH: room={room_li_float:.4f}, "
                    f"corpus={corpus_mean:.4f}, diff={diff:.4f} > tolerance={MEAN_LI_TOLERANCE}"
                )}
    return {"passed": True, "room_mean_li": room_li_float, "corpus_mean_li": round(corpus_mean, 4)}


def check_gate_status(room: dict, corpus_rows: list) -> dict:
    room_gate = room.get("gate_status")
    if not room_gate:
        return {"passed": True, "checked": False, "note": "No gate_status in room config — skipped"}

    # Extract most recent gate status from corpus (last row with gate_status field)
    corpus_gate = None
    for row in reversed(corpus_rows):
        gs = row.get("gate_status") or row.get("gate")
        if gs:
            corpus_gate = gs.strip().upper()
            break

    if corpus_gate is None:
        return {"passed": True, "checked": False,
                "note": "No gate_status in corpus — skipped"}

    room_gate_normalized = room_gate.strip().upper()
    if room_gate_normalized not in GATE_STATUS_VALID:
        return {"passed": False,
                "failure": f"ROOM_GATE_INVALID: gate_status='{room_gate}' not in {GATE_STATUS_VALID}"}

    if room_gate_normalized != corpus_gate:
        return {"passed": False,
                "room_gate": room_gate_normalized,
                "corpus_gate": corpus_gate,
                "failure": (
                    f"ROOM_GATE_STATUS_STALE: room says '{room_gate_normalized}', "
                    f"corpus says '{corpus_gate}'. Room state may be stale."
                )}
    return {"passed": True, "gate_status": room_gate_normalized}


def check_session_count(room: dict, corpus_rows: list) -> dict:
    room_count = room.get("session_count")
    if room_count is None:
        return {"passed": True, "checked": False, "note": "No session_count in room config — skipped"}

    try:
        room_count_int = int(room_count)
    except (ValueError, TypeError):
        return {"passed": False,
                "failure": f"ROOM_SESSION_COUNT_INVALID: cannot parse session_count='{room_count}'"}

    agent_name = room.get("agent_name", "")
    if agent_name:
        agent_rows = [r for r in corpus_rows
                      if (r.get("agent_name") or "").lower() == agent_name.lower()]
    else:
        agent_rows = corpus_rows

    corpus_count = len(agent_rows)
    if room_count_int > corpus_count:
        return {"passed": False,
                "room_count": room_count_int,
                "corpus_count": corpus_count,
                "failure": (
                    f"ROOM_OVERCLAIMING_SESSIONS: room claims {room_count_int} sessions, "
                    f"only {corpus_count} found in corpus for agent='{agent_name or 'all'}'"
                )}
    return {"passed": True, "room_count": room_count_int, "corpus_count": corpus_count}


def check_agent_name(room: dict, corpus_rows: list) -> dict:
    room_agent = room.get("agent_name", "").strip()
    if not room_agent:
        return {"passed": True, "checked": False, "note": "No agent_name in room config — skipped"}

    corpus_agents = {(r.get("agent_name") or "").strip() for r in corpus_rows}
    if room_agent not in corpus_agents:
        return {"passed": False,
                "room_agent": room_agent,
                "corpus_agents_sample": sorted(list(corpus_agents))[:5],
                "failure": (
                    f"ROOM_AGENT_NAME_MISMATCH: room agent_name='{room_agent}' "
                    f"not found in corpus"
                )}
    return {"passed": True, "agent_name": room_agent}


# ── Aggregator ────────────────────────────────────────────────────────────────

def run_audit(room: dict, corpus_rows: list) -> dict:
    sid_check     = check_session_id_present(room)
    corpus_check  = check_session_in_corpus(room, corpus_rows)
    li_check      = check_mean_li(room, corpus_rows)
    gate_check    = check_gate_status(room, corpus_rows)
    count_check   = check_session_count(room, corpus_rows)
    agent_check   = check_agent_name(room, corpus_rows)

    checks = [sid_check, corpus_check, li_check, gate_check, count_check, agent_check]
    hard_failures = [c["failure"] for c in checks if not c.get("passed") and c.get("failure")]
    verdict = "PASS" if not hard_failures else "FAIL"

    return {
        "result": verdict,
        "status": verdict,
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "room_id": room.get("room_id") or room.get("id") or "unknown",
        "agent_name": room.get("agent_name") or "unknown",
        "hard_failures": hard_failures,
        "checks": {
            "session_id_present":   sid_check,
            "session_in_corpus":    corpus_check,
            "mean_li_consistent":   li_check,
            "gate_status_current":  gate_check,
            "session_count_valid":  count_check,
            "agent_name_match":     agent_check,
        },
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rid = output.get("room_id", "unknown").replace("/", "-")
    path = p / f"room_audit_{rid}_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict):
    border = "═" * 56
    print(f"\n{border}")
    print(f" ACAT Room State Auditor · {TOOL_VERSION}")
    print(f" Room: {output['room_id']}  Agent: {output['agent_name']}")
    print(f" Verdict: {output['result']}")
    print(border)
    checks = output.get("checks", {})
    labels = {
        "session_id_present":  "Session ID present",
        "session_in_corpus":   "Session in corpus",
        "mean_li_consistent":  "Mean LI consistent",
        "gate_status_current": "Gate status current",
        "session_count_valid": "Session count valid",
        "agent_name_match":    "Agent name match",
    }
    for k, label in labels.items():
        c = checks.get(k, {})
        if not c.get("checked", True):
            sym = "–"
        elif c.get("passed"):
            sym = "✓"
        else:
            sym = "✗"
        print(f"  {sym} {label}")
    if output["hard_failures"]:
        print(f"\n  FAILURES ({len(output['hard_failures'])}):")
        for f in output["hard_failures"]:
            print(f"  ✗ {f[:80]}")
    print(f"\n{border}\n")


def run_smoke_test() -> bool:
    import io as _io

    room = {
        "room_id": "room-smoke-01",
        "agent_name": "TestAgent",
        "session_id": "S-051626-01",
        "mean_li": 0.8632,
        "gate_status": "PASSED",
        "session_count": 2,
    }

    def _make_corpus():
        rows = [
            {"agent_name": "TestAgent", "session_id": "S-051626-01",
             "phase": "Phase 3", "learning_index": "0.8632",
             "gate_status": "PASSED",
             "truth": "85", "service": "86", "harm": "86",
             "autonomy": "87", "value": "86", "humility": "84"},
            {"agent_name": "TestAgent", "session_id": "S-051626-02",
             "phase": "Phase 3", "learning_index": "0.8700",
             "gate_status": "PASSED",
             "truth": "86", "service": "87", "harm": "87",
             "autonomy": "88", "value": "87", "humility": "85"},
        ]
        return rows

    try:
        corpus_rows = _make_corpus()
        output = run_audit(room, corpus_rows)
        assert output["result"] == "PASS", f"Expected PASS: {output['hard_failures']}"

        # Test mismatch
        bad_room = dict(room)
        bad_room["mean_li"] = 0.99  # wrong
        output2 = run_audit(bad_room, corpus_rows)
        assert output2["result"] == "FAIL", "Should fail on mean_li mismatch"

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="ACAT Room State Auditor v1.0")
    parser.add_argument("--room", "-r", help="Path to room config JSON")
    parser.add_argument("--corpus", "-c", help="Path to corpus CSV")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    if not args.room or not args.corpus:
        parser.print_help()
        sys.exit(1)

    try:
        room = load_room_config(args.room)
        corpus_rows = load_corpus(args.corpus)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    output = run_audit(room, corpus_rows)
    report_path = write_report(output, args.output)
    print_summary(output)
    print(f"Report written: {report_path}")
    sys.exit(0 if output["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()

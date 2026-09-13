"""
test_dimension_attribution.py
Builder v1.7 compliant
HumanAIOS

Covers Stage 4's job: turning resolved (p, outcome) pairs into per-predictor
Truth/Humility/Autonomy attribution. An over-confident, unhedged predictor
must score worse on both Truth and Humility than a well-calibrated one; a
batch with no misses must report Humility unscored rather than a fake zero;
Autonomy must always be honestly unscored; and a corrupted ledger must be
reported without silently dropping or corrupting the rest of the report.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import dimension_attribution_v1_0 as da  # noqa: E402
import nf_ledger_v0_1 as engine  # noqa: E402


def _token_pin_resolve(seq, predictor, at, p, outcome, token_id):
    return [
        {"seq": seq, "type": "TOKEN", "at": at, "by": "test",
         "token_id": token_id, "practice": "test", "title": "t",
         "date": at[:10], "date_source": "PRACTICE", "owner_add": False,
         "state": "DATED"},
        {"seq": seq + 1, "type": "PIN", "at": at, "by": "test",
         "pin_id": f"{token_id}:{predictor}", "target": token_id,
         "predictor": predictor, "claim": "x", "p": p, "scoreable": True},
        {"seq": seq + 2, "type": "RESOLVE", "at": at, "by": "test",
         "token_id": token_id, "outcome": outcome, "source": "test"},
    ]


def test_smoke_test_passes():
    assert da.run_smoke_test()


def test_load_resolved_pins_skips_unresolved_and_null_p(tmp_path):
    ledger = tmp_path / "l.jsonl"
    events = []
    seq = 1
    # A resolved pin.
    events += _token_pin_resolve(seq, "P", "2026-09-13T00:00:00+00:00", 0.8, "YES", "t1")
    seq += 3
    # A TOKEN+PIN with no RESOLVE — unresolved, must be skipped.
    events += [
        {"seq": seq, "type": "TOKEN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
         "token_id": "t2", "practice": "test", "title": "t", "date": "2026-09-13",
         "date_source": "PRACTICE", "owner_add": False, "state": "DATED"},
        {"seq": seq + 1, "type": "PIN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
         "pin_id": "t2:P", "target": "t2", "predictor": "P", "claim": "x",
         "p": 0.5, "scoreable": True},
    ]
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    assert len(resolved) == 1
    assert resolved[0]["pin_id"] == "t1:P"


def test_overconfident_predictor_scores_worse_than_calibrated(tmp_path):
    ledger = tmp_path / "l.jsonl"
    events = []
    seq = 1
    for i in range(4):
        outcome = "NO" if i < 2 else "YES"
        events += _token_pin_resolve(seq, "Overconfident", "2026-09-13T00:00:00+00:00",
                                     0.95, outcome, f"oc-{i}")
        seq += 3
    for p, outcome in [(0.4, "NO"), (0.9, "YES"), (0.9, "YES")]:
        events += _token_pin_resolve(seq, "Calibrated", "2026-09-13T01:00:00+00:00",
                                     p, outcome, f"cb-{seq}")
        seq += 3
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    aggregates = da.aggregate_by_predictor(resolved)

    assert aggregates["Overconfident"]["truth"]["value"] > aggregates["Calibrated"]["truth"]["value"]
    assert (aggregates["Overconfident"]["humility"]["value"]
            > aggregates["Calibrated"]["humility"]["value"])


def test_batch_with_no_misses_reports_humility_unscored(tmp_path):
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "t1")
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    batch_score = da.score_batch(resolved)
    assert batch_score["humility"]["status"] == "unscored"
    assert batch_score["humility"]["value"] is None

    aggregates = da.aggregate_by_predictor(resolved)
    assert aggregates["P"]["humility"]["status"] == "unscored"


def test_autonomy_always_unscored(tmp_path):
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "NO", "t1")
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    batch_score = da.score_batch(resolved)
    assert batch_score["autonomy"]["status"] == "unscored"
    assert batch_score["autonomy"]["value"] is None

    aggregates = da.aggregate_by_predictor(resolved)
    assert aggregates["P"]["autonomy"]["status"] == "unscored"


def test_batches_grouped_by_predictor_and_at(tmp_path):
    ledger = tmp_path / "l.jsonl"
    events = []
    seq = 1
    events += _token_pin_resolve(seq, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "a")
    seq += 3
    events += _token_pin_resolve(seq, "P", "2026-09-13T00:00:00+00:00", 0.8, "NO", "b")
    seq += 3
    events += _token_pin_resolve(seq, "P", "2026-09-14T00:00:00+00:00", 0.7, "YES", "c")
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    batches = da.group_batches(resolved)
    assert len(batches) == 2
    assert len(batches[("P", "2026-09-13T00:00:00+00:00")]) == 2
    assert len(batches[("P", "2026-09-14T00:00:00+00:00")]) == 1


def test_load_ledger_refuses_corrupt_chain(tmp_path):
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "t1")
    engine.append(str(ledger), events, "0" * 64)
    rows = engine.read(str(ledger))
    rows[0]["hash"] = "0" * 64
    with open(ledger, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    try:
        da.load_resolved_pins(ledger)
        raise AssertionError("expected LedgerLoadError")
    except da.LedgerLoadError:
        pass


def test_cli_missing_ledger_contributes_nothing_not_fatal(tmp_path, capsys):
    parser = da.build_parser()
    args = parser.parse_args([
        "report", "--ledger", str(tmp_path / "absent.jsonl"), "--json",
    ])
    assert da.cmd_report(args) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["predictors"] == {}
    assert out["load_errors"] == []


def test_cli_report_requires_at_least_one_ledger(capsys):
    parser = da.build_parser()
    args = parser.parse_args(["report"])
    assert da.main(["report"]) == 2
    assert "FAIL" in capsys.readouterr().err


def test_cli_corrupt_ledger_exits_nonzero_but_still_reports_good_data(tmp_path, capsys):
    good = tmp_path / "good.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "t1")
    engine.append(str(good), events, "0" * 64)

    bad = tmp_path / "bad.jsonl"
    engine.append(str(bad), events, "0" * 64)
    rows = engine.read(str(bad))
    rows[0]["hash"] = "0" * 64
    with open(bad, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    parser = da.build_parser()
    args = parser.parse_args([
        "report", "--ledger", str(good), "--ledger", str(bad), "--json",
    ])
    assert da.cmd_report(args) == 1
    out = json.loads(capsys.readouterr().out)
    assert "P" in out["predictors"]
    assert len(out["load_errors"]) == 1

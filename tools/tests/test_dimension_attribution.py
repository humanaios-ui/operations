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


def test_load_resolved_pins_skips_unresolved(tmp_path):
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


def test_load_resolved_pins_skips_null_probability(tmp_path):
    """A resolved pin with p=None (e.g. an owed Z2 prior in NF_LEDGER-style
    data) must be excluded even though it fully resolved — there is no
    stated confidence to score against the outcome."""
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.8, "YES", "t1")
    events += [
        {"seq": 4, "type": "TOKEN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
         "token_id": "t2", "practice": "test", "title": "t", "date": "2026-09-13",
         "date_source": "PRACTICE", "owner_add": False, "state": "DATED"},
        {"seq": 5, "type": "PIN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
         "pin_id": "t2:P", "target": "t2", "predictor": "P", "claim": "x",
         "p": None, "scoreable": False},
        {"seq": 6, "type": "RESOLVE", "at": "2026-09-13T00:00:00+00:00", "by": "test",
         "token_id": "t2", "outcome": "YES", "source": "test"},
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


def test_batches_grouped_by_predictor_and_at_within_one_ledger(tmp_path):
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
    same_day_key = (str(ledger), "P", "at:2026-09-13T00:00:00+00:00")
    other_day_key = (str(ledger), "P", "at:2026-09-14T00:00:00+00:00")
    assert len(batches[same_day_key]) == 2
    assert len(batches[other_day_key]) == 1


def test_negative_control_two_independent_pins_sharing_at_do_collide(tmp_path):
    """Documents the known, tested residual limitation: without episode_id,
    two genuinely independent declaring acts by the same predictor that
    happen to share an `at` value (e.g. ci_predict_consolidate's date-only
    granularity) are indistinguishable to this tool and are merged into
    one batch — a real batching-contract boundary, not an assumption left
    unverified."""
    ledger = tmp_path / "l.jsonl"
    same_at = "2026-09-13"  # date-only, as commit_date_only() produces
    events = _token_pin_resolve(1, "P", same_at, 0.9, "YES", "push-1-check")
    events += _token_pin_resolve(4, "P", same_at, 0.2, "NO", "push-2-check")
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    batches = da.group_batches(resolved)
    assert len(batches) == 1  # two independent pushes collapsed into one batch
    assert len(list(batches.values())[0]) == 2


def test_negative_control_one_logical_act_split_across_timestamps_does_split(tmp_path):
    """The mirror case: if a future writer stamped one logical declaring
    act with two different `at` values and no episode_id, this tool has no
    way to recover that they were one act — it reports two batches. This
    documents that boundary rather than leaving it unverified."""
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "a")
    events += _token_pin_resolve(4, "P", "2026-09-13T00:00:01+00:00", 0.9, "YES", "b")
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    batches = da.group_batches(resolved)
    assert len(batches) == 2  # split, even though a human might call this one act


def test_batches_never_merge_across_ledgers(tmp_path):
    """The same predictor and the same `at` in two different ledger files
    must never be treated as one declaring act — each ledger is its own
    scope."""
    ledger_a = tmp_path / "a.jsonl"
    ledger_b = tmp_path / "b.jsonl"
    same_at = "2026-09-13T00:00:00+00:00"
    engine.append(str(ledger_a),
                  _token_pin_resolve(1, "P", same_at, 0.9, "YES", "x"), "0" * 64)
    engine.append(str(ledger_b),
                  _token_pin_resolve(1, "P", same_at, 0.1, "NO", "x"), "0" * 64)

    resolved = da.load_resolved_pins(ledger_a) + da.load_resolved_pins(ledger_b)
    batches = da.group_batches(resolved)
    assert len(batches) == 2  # not merged into one, despite identical predictor+at


def test_episode_id_gives_exact_grouping_when_present(tmp_path):
    """A row carrying episode_id (as lifecycle_predict's do) is grouped by
    that exact identifier, not by the coarser (predictor, at) fallback —
    two different episodes at the identical timestamp stay separate."""
    ledger = tmp_path / "l.jsonl"
    same_at = "2026-09-13T00:00:00+00:00"
    events = _token_pin_resolve(1, "P", same_at, 0.9, "YES", "x")
    events[1]["episode_id"] = "LC-episode-1"
    events += _token_pin_resolve(4, "P", same_at, 0.1, "NO", "y")
    events[4]["episode_id"] = "LC-episode-2"
    engine.append(str(ledger), events, "0" * 64)

    resolved = da.load_resolved_pins(ledger)
    batches = da.group_batches(resolved)
    assert len(batches) == 2
    assert (str(ledger), "P", "episode:LC-episode-1") in batches
    assert (str(ledger), "P", "episode:LC-episode-2") in batches


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


def test_malformed_token_missing_state_raises_ledger_load_error_not_crash(tmp_path):
    """engine.verify() only checks the hash chain, not event schema: a
    correctly-hashed TOKEN missing 'state' must be reported as
    LedgerLoadError from load_resolved_pins, not escape as a raw KeyError
    out of project()/pin_outcome() and crash the whole report."""
    ledger = tmp_path / "l.jsonl"
    row_missing_state = {
        "seq": 1, "type": "TOKEN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
        "token_id": "t1", "practice": "test", "title": "t", "date": "2026-09-13",
        "date_source": "PRACTICE", "owner_add": False,
    }
    pin_row = {
        "seq": 2, "type": "PIN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
        "pin_id": "t1:P", "target": "t1", "predictor": "P", "claim": "x",
        "p": 0.5, "scoreable": True,
    }
    engine.append(str(ledger), [row_missing_state, pin_row], "0" * 64)
    assert engine.verify(engine.read(str(ledger))) is None  # hash-valid on its own terms

    try:
        da.load_resolved_pins(ledger)
        raise AssertionError("expected LedgerLoadError")
    except da.LedgerLoadError:
        pass


def test_cli_malformed_ledger_among_several_does_not_crash_the_report(tmp_path, capsys):
    good = tmp_path / "good.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "t1")
    engine.append(str(good), events, "0" * 64)

    malformed = tmp_path / "malformed.jsonl"
    row_missing_target = {
        "seq": 1, "type": "PIN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
        "pin_id": "x:P", "predictor": "P", "claim": "x", "p": 0.5, "scoreable": True,
    }
    engine.append(str(malformed), [row_missing_target], "0" * 64)

    parser = da.build_parser()
    args = parser.parse_args([
        "report", "--ledger", str(good), "--ledger", str(malformed), "--json",
    ])
    assert da.cmd_report(args) == 1
    out = json.loads(capsys.readouterr().out)
    assert "P" in out["predictors"]
    assert len(out["load_errors"]) == 1


def test_row_missing_hash_raises_ledger_load_error_not_crash(tmp_path):
    """engine.verify() itself can raise KeyError (indexing e["hash"]) for a
    row that never had one, rather than returning an error string — that
    call must be wrapped too, not just project()/pin_outcome()."""
    ledger = tmp_path / "l.jsonl"
    row_missing_hash = {
        "seq": 1, "type": "TOKEN", "at": "2026-09-13T00:00:00+00:00", "by": "test",
        "token_id": "t1", "practice": "test", "title": "t", "date": "2026-09-13",
        "date_source": "PRACTICE", "owner_add": False, "state": "DATED",
        "prev_hash": "0" * 64,
    }
    ledger.write_text(json.dumps(row_missing_hash) + "\n", encoding="utf-8")

    try:
        da.load_resolved_pins(ledger)
        raise AssertionError("expected LedgerLoadError")
    except da.LedgerLoadError:
        pass


def test_pin_with_out_of_range_probability_refused(tmp_path):
    """A hash-valid PIN with p outside [0,1] (or non-numeric) must be
    refused as LedgerLoadError, not silently summed into a bogus Truth
    value or crash score_batch() with a TypeError."""
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "t1")
    events[1]["p"] = 5.0  # out of range
    engine.append(str(ledger), events, "0" * 64)

    try:
        da.load_resolved_pins(ledger)
        raise AssertionError("expected LedgerLoadError")
    except da.LedgerLoadError:
        pass


def test_pin_missing_predictor_refused(tmp_path):
    """A PIN missing 'predictor' must be refused, not silently attributed
    to a fabricated 'unknown' bucket that corrupts the per-predictor
    rollup."""
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "t1")
    del events[1]["predictor"]
    engine.append(str(ledger), events, "0" * 64)

    try:
        da.load_resolved_pins(ledger)
        raise AssertionError("expected LedgerLoadError")
    except da.LedgerLoadError:
        pass


def test_resolve_with_invalid_outcome_refused(tmp_path):
    """pin_outcome() silently treats any outcome other than exactly 'YES'
    as a miss (outs.append(tk['resolved'] == 'YES')) — a RESOLVE with
    outcome='MAYBE' would otherwise be misscored as a hard NO instead of
    being caught as the malformed row it is."""
    ledger = tmp_path / "l.jsonl"
    events = _token_pin_resolve(1, "P", "2026-09-13T00:00:00+00:00", 0.9, "YES", "t1")
    events[2]["outcome"] = "MAYBE"
    engine.append(str(ledger), events, "0" * 64)

    try:
        da.load_resolved_pins(ledger)
        raise AssertionError("expected LedgerLoadError")
    except da.LedgerLoadError:
        pass

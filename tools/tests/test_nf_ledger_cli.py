"""
test_nf_ledger_cli.py
Builder v1.7 compliant
HumanAIOS

Covers the properties that make the ledger an anchor rather than a log:
a missed prediction must record SURPRISE, a tampered row must fail
verification, and a stated confidence must produce a Brier score that
actually varies with calibration.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import nf_ledger_cli_v1_0 as cli  # noqa: E402

TOOL_NAME = "test_nf_ledger_cli"
TOOL_VERSION = "1.0.0"


def _pin(ledger: Path, hypothesis_id: str, confidence: float) -> int:
    """Pin a standard sub-8-minute prediction."""
    parser = cli.build_parser()
    args = parser.parse_args([
        "pin", "--ledger", str(ledger), "--id", hypothesis_id,
        "--metric", "startup_minutes", "--threshold", "8",
        "--direction", "lt", "--window-days", "14",
        "--confidence", str(confidence),
    ])
    return cli.cmd_pin(args)


def _resolve(ledger: Path, hypothesis_id: str, actual: float) -> int:
    """Resolve a pinned prediction against a measured value."""
    parser = cli.build_parser()
    args = parser.parse_args([
        "resolve", "--ledger", str(ledger), "--id", hypothesis_id,
        "--actual", str(actual),
    ])
    return cli.cmd_resolve(args)


def test_smoke_test_passes():
    """The tool's own self-test is green."""
    assert cli.smoke_test() == 0


def test_hit_records_expected(tmp_path):
    """A prediction that holds resolves EXPECTED."""
    ledger = tmp_path / "hit.jsonl"
    assert _pin(ledger, "H-1", 0.7) == 0
    assert _resolve(ledger, "H-1", 6.5) == 0
    rows = cli.load_rows(ledger)
    assert rows[1]["outcome"] == "EXPECTED"


def test_miss_records_surprise(tmp_path):
    """A prediction that fails resolves SURPRISE, never a silent pass."""
    ledger = tmp_path / "miss.jsonl"
    _pin(ledger, "H-2", 0.9)
    _resolve(ledger, "H-2", 20.0)
    rows = cli.load_rows(ledger)
    assert rows[1]["outcome"] == "SURPRISE"


def test_calibrated_brier_varies_with_confidence(tmp_path):
    """Two predictors, same outcome, different confidence, different score.

    The engine's own brier_score cannot distinguish them because it pins
    confidence at 1.0; this is the field that carries real signal.
    """
    confident = tmp_path / "confident.jsonl"
    hedged = tmp_path / "hedged.jsonl"
    _pin(confident, "H-3", 0.95)
    _resolve(confident, "H-3", 20.0)
    _pin(hedged, "H-4", 0.55)
    _resolve(hedged, "H-4", 20.0)

    confident_row = cli.load_rows(confident)[1]
    hedged_row = cli.load_rows(hedged)[1]

    assert confident_row["brier_score"] == hedged_row["brier_score"]
    assert (confident_row["calibration"]["brier_calibrated"]
            > hedged_row["calibration"]["brier_calibrated"])


def test_absent_confidence_is_none_not_zero(tmp_path):
    """An unstated confidence yields None, never a score that looks passing."""
    assert cli.calibrated_brier(None, "EXPECTED") is None


def test_void_is_unscored():
    """A run that produced no signal is not a passed prediction."""
    assert cli.calibrated_brier(0.8, "VOID") is None


def test_clean_chain_verifies(tmp_path):
    """An untouched ledger reports no problems."""
    ledger = tmp_path / "clean.jsonl"
    _pin(ledger, "H-5", 0.6)
    _resolve(ledger, "H-5", 6.0)
    assert cli.verify_chain(cli.load_rows(ledger)) == []


def test_tampered_row_is_detected(tmp_path):
    """Editing a resolved value after the fact breaks verification."""
    ledger = tmp_path / "tampered.jsonl"
    _pin(ledger, "H-6", 0.6)
    _resolve(ledger, "H-6", 20.0)
    rows = cli.load_rows(ledger)
    rows[1]["metric_actual"] = 1.0
    assert cli.verify_chain(rows)


def test_double_resolve_refused(tmp_path):
    """A prediction resolves once; a second attempt is rejected."""
    ledger = tmp_path / "double.jsonl"
    _pin(ledger, "H-7", 0.6)
    _resolve(ledger, "H-7", 6.0)
    assert _resolve(ledger, "H-7", 3.0) == 2


def test_duplicate_pin_refused(tmp_path):
    """The same hypothesis cannot be pinned twice."""
    ledger = tmp_path / "dupe.jsonl"
    _pin(ledger, "H-8", 0.6)
    assert _pin(ledger, "H-8", 0.6) == 2


def test_pin_stores_frozen_hypothesis(tmp_path):
    """A preregistration records its own locked parameters."""
    ledger = tmp_path / "frozen.jsonl"
    _pin(ledger, "H-9", 0.6)
    pin_row = cli.load_rows(ledger)[0]
    assert pin_row["hypothesis"]["threshold"] == 8
    assert pin_row["hypothesis"]["direction"] == "lt"


def test_missing_ledger_is_empty_not_error(tmp_path):
    """A ledger that does not exist yet reads as empty."""
    assert cli.load_rows(tmp_path / "absent.jsonl") == []


def test_invalid_json_raises_ledger_error(tmp_path):
    """A corrupt line is reported with its line number, not swallowed."""
    ledger = tmp_path / "bad.jsonl"
    ledger.write_text("{not json}\n", encoding="utf-8")
    try:
        cli.load_rows(ledger)
    except cli.LedgerError as exc:
        assert "bad.jsonl:1" in str(exc)
        return
    raise AssertionError("expected LedgerError")


def test_export_round_trips(tmp_path, capsys):
    """Export prints every stored row as JSON."""
    ledger = tmp_path / "export.jsonl"
    _pin(ledger, "H-10", 0.6)
    _resolve(ledger, "H-10", 6.0)
    capsys.readouterr()  # drop the pin/resolve output so only export is read
    parser = cli.build_parser()
    cli.cmd_export(parser.parse_args(["export", "--ledger", str(ledger)]))
    printed = json.loads(capsys.readouterr().out)
    assert len(printed) == 2

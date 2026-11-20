"""
test_witness_ledger_v0.py

Covers the properties that make the witness ledger an attribution anchor:
hash-chain verify, tamper detection, and hard authority boundary constants.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1]
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import witness_ledger_v0 as wl  # noqa: E402

SCHEMA_PATH = ROOT / "schemas" / "intent_os_witness_ledger_entry_v0.schema.json"


def test_smoke_test_passes():
    assert wl.run_smoke_test() == 0


def test_schema_hard_boundary_constants():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["properties"]["authority_effect"]["const"] == "NONE"
    assert schema["properties"]["can_authorize"]["const"] is False
    assert schema["properties"]["advisory_only"]["const"] is True
    assert schema["properties"]["schema"]["const"] == "intentos/witness_ledger_entry_v0"


def test_clean_chain_verifies(tmp_path):
    ledger = tmp_path / "clean.jsonl"
    parser = wl.build_parser()
    args = parser.parse_args(
        ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
    )
    assert wl.cmd_init(args) == 0
    args = parser.parse_args(
        [
            "append",
            "--ledger",
            str(ledger),
            "--decision-id",
            "Q-TEST-01",
            "--actor-type",
            "machine",
            "--actor-email",
            "noreply@anthropic.com",
            "--actor-role",
            "Z1",
            "--decision-class",
            "propose",
            "--title",
            "Test row",
            "--context",
            "unit test",
            "--authority-level",
            "Z1",
            "--rationale",
            "coverage",
            "--falsifier",
            "edit breaks verify",
            "--timestamp",
            "2026-11-20T12:01:00Z",
        ]
    )
    assert wl.cmd_append(args) == 0
    rows = wl.load_rows(ledger)
    assert wl.verify_chain(rows) == []
    assert rows[0]["authority_effect"] == "NONE"
    assert rows[0]["can_authorize"] is False


def test_tampered_row_is_detected(tmp_path):
    ledger = tmp_path / "tampered.jsonl"
    parser = wl.build_parser()
    assert (
        wl.cmd_init(
            parser.parse_args(
                ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
            )
        )
        == 0
    )
    rows = wl.load_rows(ledger)
    rows[0]["title"] = "edited after the fact"
    assert wl.verify_chain(rows)


def test_unknown_field_breaks_verify():
    row = wl.build_entry(
        seq=1,
        prev_hash=wl.ZERO_HASH,
        decision_id="Q-X",
        timestamp_utc="2026-11-20T12:00:00Z",
        actor_type="human",
        actor_email="carly.r.anderson@gmail.com",
        actor_role="Z2",
        decision_class="ratify",
        title="x",
        context="x",
        authority_level="Z2",
        artifacts={},
        rationale="x",
        falsifier="x",
    )
    row["extra"] = "smuggled"
    with pytest.raises(wl.LedgerError, match="unknown fields"):
        wl.validate_entry_shape(row)


def test_verify_rejects_empty_ledger(tmp_path):
    ledger = tmp_path / "empty.jsonl"
    parser = wl.build_parser()
    code = wl.cmd_verify(parser.parse_args(["verify", "--ledger", str(ledger)]))
    assert code == 1


def test_load_rows_rejects_non_object(tmp_path):
    ledger = tmp_path / "bad.jsonl"
    ledger.write_text("null\n", encoding="utf-8")
    with pytest.raises(wl.SpecLoadFailed, match="JSON object"):
        wl.load_rows(ledger)


def test_field_max_length_enforced():
    with pytest.raises(wl.LedgerError, match="decision_id exceeds max length"):
        wl.build_entry(
            seq=1,
            prev_hash=wl.ZERO_HASH,
            decision_id="Q" + ("X" * 256),
            timestamp_utc="2026-11-20T12:00:00Z",
            actor_type="human",
            actor_email="carly.r.anderson@gmail.com",
            actor_role="Z2",
            decision_class="ratify",
            title="x",
            context="x",
            authority_level="Z2",
            artifacts={},
            rationale="x",
            falsifier="x",
        )


def test_append_adds_newline_before_unterminated_last_line(tmp_path):
    ledger = tmp_path / "unterminated.jsonl"
    parser = wl.build_parser()
    assert (
        wl.cmd_init(
            parser.parse_args(
                ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
            )
        )
        == 0
    )
    text = ledger.read_text(encoding="utf-8").rstrip("\n")
    ledger.write_text(text, encoding="utf-8")
    assert not ledger.read_text(encoding="utf-8").endswith("\n")
    assert (
        wl.cmd_append(
            parser.parse_args(
                [
                    "append",
                    "--ledger",
                    str(ledger),
                    "--decision-id",
                    "Q-NL-01",
                    "--actor-type",
                    "machine",
                    "--actor-email",
                    "noreply@anthropic.com",
                    "--actor-role",
                    "Z1",
                    "--decision-class",
                    "propose",
                    "--title",
                    "newline fix",
                    "--context",
                    "unit test",
                    "--authority-level",
                    "Z1",
                    "--rationale",
                    "coverage",
                    "--falsifier",
                    "edit breaks verify",
                    "--timestamp",
                    "2026-11-20T12:01:00Z",
                ]
            )
        )
        == 0
    )
    assert wl.verify_chain(wl.load_rows(ledger)) == []


def test_can_authorize_true_refused():
    row = wl.build_entry(
        seq=1,
        prev_hash=wl.ZERO_HASH,
        decision_id="Q-X",
        timestamp_utc="2026-11-20T12:00:00Z",
        actor_type="human",
        actor_email="carly.r.anderson@gmail.com",
        actor_role="Z2",
        decision_class="ratify",
        title="x",
        context="x",
        authority_level="Z2",
        artifacts={},
        rationale="x",
        falsifier="x",
    )
    row["can_authorize"] = True
    with pytest.raises(wl.LedgerError):
        wl.validate_entry_shape(row)


def test_module_authority_boundary_exports():
    assert wl.AUTHORITY_EFFECT == "NONE"
    assert wl.CAN_AUTHORIZE is False
    assert wl.ADVISORY_ONLY is True


try:
    from jsonschema import Draft202012Validator, ValidationError
except ImportError:  # pragma: no cover - CI has jsonschema; local may not
    Draft202012Validator = None
    ValidationError = None


@pytest.mark.skipif(Draft202012Validator is None, reason="jsonschema not installed")
def test_schema_rejects_can_authorize_true():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    row = wl.build_entry(
        seq=1,
        prev_hash=wl.ZERO_HASH,
        decision_id="Q-X",
        timestamp_utc="2026-11-20T12:00:00Z",
        actor_type="human",
        actor_email="carly.r.anderson@gmail.com",
        actor_role="Z2",
        decision_class="ratify",
        title="x",
        context="x",
        authority_level="Z2",
        artifacts={},
        rationale="x",
        falsifier="x",
    )
    validator.validate(row)
    row["can_authorize"] = True
    with pytest.raises(ValidationError):
        validator.validate(row)

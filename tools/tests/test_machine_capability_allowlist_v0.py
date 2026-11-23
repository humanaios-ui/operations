"""
test_machine_capability_allowlist_v0.py

Covers fail-closed allowlist verify, Z2 ALLOW, pending machine DENY,
tamper detection, and hard authority boundary constants.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS_DIR = Path(__file__).resolve().parents[1]
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import machine_capability_allowlist_v0 as mca  # noqa: E402
import witness_ledger_v0 as wl  # noqa: E402

SCHEMA_PATH = ROOT / "schemas" / "intent_os_machine_capability_allowlist_v0.schema.json"
REPO_ALLOWLIST = ROOT / "ledgers" / "MACHINE_CAPABILITY_ALLOWLIST.json"


def test_smoke_test_passes():
    assert mca.run_smoke_test() == 0


def test_schema_hard_boundary_constants():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["properties"]["authority_effect"]["const"] == "NONE"
    assert schema["properties"]["can_authorize"]["const"] is False
    assert schema["properties"]["advisory_only"]["const"] is True
    assert schema["properties"]["require_ledger_verify"]["const"] is True
    assert schema["properties"]["http_api"]["properties"]["enabled"]["const"] is False
    assert schema["properties"]["schema"]["const"] == "intentos/machine_capability_allowlist_v0"


def test_repo_allowlist_verifies_with_witness_ledger():
    doc, ledger_info = mca.verify_bundle(REPO_ALLOWLIST)
    assert ledger_info["ok"] is True
    assert doc["authority_effect"] == "NONE"
    assert doc["can_authorize"] is False
    assert doc["http_api"]["enabled"] is False


def test_z2_human_allows_machine_pending_denies():
    doc, ledger_info = mca.verify_bundle(REPO_ALLOWLIST)
    z2 = mca.decide(doc, "carly.r.anderson@gmail.com", ledger_info=ledger_info)
    assert z2["decision"] == "ALLOW"
    biz = mca.decide(doc, "aioshuman@gmail.com", ledger_info=ledger_info)
    assert biz["decision"] == "ALLOW"
    machine = mca.decide(doc, "noreply@anthropic.com", ledger_info=ledger_info)
    assert machine["decision"] == "DENY"
    unknown = mca.decide(doc, "nobody@example.com", ledger_info=ledger_info)
    assert unknown["decision"] == "DENY"


def test_check_enforce_exit_codes(tmp_path):
    ledger = tmp_path / "WITNESS_LEDGER.jsonl"
    allowlist = tmp_path / "allowlist.json"
    parser_wl = wl.build_parser()
    assert (
        wl.cmd_init(
            parser_wl.parse_args(
                ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
            )
        )
        == 0
    )
    doc = mca.build_seed_doc()
    doc["witness_ledger"] = str(ledger)
    doc["content_hash"] = mca.compute_content_hash(doc)
    allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    parser = mca.build_parser()
    args = parser.parse_args(
        [
            "check",
            "--allowlist",
            str(allowlist),
            "--ledger",
            str(ledger),
            "--identity",
            "carly.r.anderson@gmail.com",
            "--enforce",
        ]
    )
    assert mca.cmd_check(args) == 0
    args = parser.parse_args(
        [
            "check",
            "--allowlist",
            str(allowlist),
            "--ledger",
            str(ledger),
            "--identity",
            "noreply@anthropic.com",
            "--enforce",
        ]
    )
    assert mca.cmd_check(args) == 1


def test_missing_allowlist_fail_closed(tmp_path):
    with pytest.raises(mca.AllowlistError):
        mca.load_allowlist(tmp_path / "nope.json")


def test_tampered_content_hash_fail_closed():
    doc = json.loads(REPO_ALLOWLIST.read_text(encoding="utf-8"))
    doc["content_hash"] = "0" * 64
    with pytest.raises(mca.AllowlistError):
        mca.validate_allowlist_shape(doc)


def test_module_authority_constants():
    assert mca.AUTHORITY_EFFECT == "NONE"
    assert mca.CAN_AUTHORIZE is False
    assert mca.ADVISORY_ONLY is True

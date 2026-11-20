"""
test_z2_authorized_machine_identities_api_v0.py

Covers fail-closed API payload, authority boundary constants, HTTP GET,
and stop-hook independence from the optional HTTP surface.
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
import z2_authorized_machine_identities_api_v0 as api  # noqa: E402

REPO_ALLOWLIST = ROOT / "ledgers" / "MACHINE_CAPABILITY_ALLOWLIST.json"


def test_smoke_test_passes():
    assert api.run_smoke_test() == 0


def test_repo_allowlist_get_payload():
    code, body = api.build_payload(REPO_ALLOWLIST)
    assert code == 200
    assert body["ok"] is True
    assert body["authority_effect"] == "NONE"
    assert body["can_authorize"] is False
    assert body["grants_merge_authority"] is False
    assert body["stop_hook_independent"] is True
    assert body["allowlist_http_api_enabled"] is False
    assert body["path"] == "/api/z2-authorized-machine-identities"
    assert "carly.r.anderson@gmail.com" in body["authorized_identities"]
    assert "aioshuman@gmail.com" in body["authorized_identities"]
    assert "noreply@anthropic.com" not in body["authorized_identities"]
    pending = [
        row for row in body["identities"] if row["identity"] == "noreply@anthropic.com"
    ]
    assert pending and pending[0]["decision"] == "DENY"


def test_fail_closed_missing_and_tampered(tmp_path):
    ledger = tmp_path / "WITNESS_LEDGER.jsonl"
    allowlist = tmp_path / "allowlist.json"
    assert (
        wl.cmd_init(
            wl.build_parser().parse_args(
                ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
            )
        )
        == 0
    )
    doc = mca.build_seed_doc()
    doc["witness_ledger"] = str(ledger)
    doc["content_hash"] = mca.compute_content_hash(doc)
    allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    code_ok, body_ok = api.build_payload(allowlist, ledger)
    assert code_ok == 200 and body_ok["ok"] is True

    code_miss, body_miss = api.build_payload(tmp_path / "nope.json", ledger)
    assert code_miss == 503
    assert body_miss["ok"] is False
    assert body_miss["authorized_identities"] == []
    assert body_miss["error"]["code"] in (
        "ALLOWLIST_MISSING",
        "ALLOWLIST_UNVERIFIABLE",
        "REGISTRY_UNVERIFIABLE",
    )

    tampered = json.loads(allowlist.read_text(encoding="utf-8"))
    tampered["content_hash"] = "0" * 64
    allowlist.write_text(json.dumps(tampered) + "\n", encoding="utf-8")
    code_bad, body_bad = api.build_payload(allowlist, ledger)
    assert code_bad == 503
    assert body_bad["authorized_identities"] == []
    assert body_bad["error"]["code"] == "ALLOWLIST_UNVERIFIABLE"


def test_cli_get_exit_codes(tmp_path, capsys):
    import contextlib
    import io

    ledger = tmp_path / "WITNESS_LEDGER.jsonl"
    allowlist = tmp_path / "allowlist.json"
    with contextlib.redirect_stdout(io.StringIO()):
        assert (
            wl.cmd_init(
                wl.build_parser().parse_args(
                    ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
                )
            )
            == 0
        )
    doc = mca.build_seed_doc()
    doc["witness_ledger"] = str(ledger)
    doc["content_hash"] = mca.compute_content_hash(doc)
    allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    parser = api.build_parser()
    good = parser.parse_args(
        ["get", "--allowlist", str(allowlist), "--ledger", str(ledger)]
    )
    assert api.cmd_get(good) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True

    bad = parser.parse_args(
        ["get", "--allowlist", str(tmp_path / "missing.json"), "--ledger", str(ledger)]
    )
    assert api.cmd_get(bad) == 1
    out_bad = json.loads(capsys.readouterr().out)
    assert out_bad["ok"] is False
    assert out_bad["authorized_identities"] == []


def test_authority_constants_and_stop_hook_never_requires_http():
    assert api.AUTHORITY_EFFECT == "NONE"
    assert api.CAN_AUTHORIZE is False
    assert api.ADVISORY_ONLY is True
    # Phase C allowlist still declares HTTP disabled for stop-hook independence.
    doc, _ = mca.verify_bundle(REPO_ALLOWLIST)
    assert doc["http_api"]["enabled"] is False
    assert doc["http_api"]["path"] == api.API_PATH

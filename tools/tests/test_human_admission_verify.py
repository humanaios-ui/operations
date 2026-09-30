"""Tests for cryptographic human evaluation-admission receipts."""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / ".github" / "scripts" / "human_admission_verify.py"
_spec = importlib.util.spec_from_file_location("human_admission_verify", VERIFIER)
assert _spec and _spec.loader
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
canonical_payload = _module.canonical_payload
verify_snapshot = _module.verify_snapshot


def _keypair(tmp_path: Path) -> tuple[Path, str]:
    private = tmp_path / "human_admission_test"
    subprocess.run(
        ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private)],
        check=True,
    )
    public = private.with_suffix(".pub").read_text(encoding="utf-8").strip()
    return private, public


def _signed_receipt(tmp_path: Path, private: Path, *, repo: str, pr: int, issue: int, head: str) -> str:
    payload = canonical_payload(repo, pr, issue, head)
    payload_file = tmp_path / "payload.txt"
    payload_file.write_text(payload, encoding="utf-8")
    subprocess.run(
        [
            "ssh-keygen", "-Y", "sign",
            "-f", str(private),
            "-n", "humanaios-evaluation-admission-v1",
            str(payload_file),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    signature = (tmp_path / "payload.txt.sig").read_text(encoding="utf-8").strip()
    return (
        "/admit-evaluation-signed\n"
        f"pr={pr}\n"
        f"issue={issue}\n"
        f"head={head}\n"
        f"{signature}"
    )


def _policy(public_key: str) -> dict:
    return {
        "human_attestation": {
            "namespace": "humanaios-evaluation-admission-v1",
            "authorized_signers": [
                {"principal": "human-authority", "public_key": public_key}
            ],
        }
    }


def _snapshot(body: str, *, head: str) -> dict:
    return {
        "repository": "humanaios-ui/operations",
        "pull_requests": [{
            "number": 603,
            "head_sha": head,
            "comments": [{
                "user": {"login": "humanaios-ui"},
                "body": body,
                "id": 1,
            }],
            "reviews": [],
        }],
    }


def test_valid_signature_is_verified_even_if_carried_by_shared_account(tmp_path):
    private, public = _keypair(tmp_path)
    head = "a" * 40
    body = _signed_receipt(
        tmp_path, private,
        repo="humanaios-ui/operations", pr=603, issue=602, head=head,
    )
    result = verify_snapshot(_snapshot(body, head=head), _policy(public))
    receipts = result["pull_requests"][0]["verified_admission_receipts"]
    assert len(receipts) == 1
    assert receipts[0]["principal"] == "human-authority"
    assert receipts[0]["issue"] == 602
    assert receipts[0]["authority"] == "EVALUATION_ONLY"


def test_same_github_identity_without_signature_cannot_admit(tmp_path):
    _, public = _keypair(tmp_path)
    head = "a" * 40
    result = verify_snapshot(
        _snapshot("/admit-evaluation", head=head),
        _policy(public),
    )
    assert result["pull_requests"][0]["verified_admission_receipts"] == []


def test_signature_cannot_be_replayed_after_head_changes(tmp_path):
    private, public = _keypair(tmp_path)
    signed_head = "a" * 40
    current_head = "b" * 40
    body = _signed_receipt(
        tmp_path, private,
        repo="humanaios-ui/operations", pr=603, issue=602, head=signed_head,
    )
    result = verify_snapshot(
        _snapshot(body, head=current_head),
        _policy(public),
    )
    assert result["pull_requests"][0]["verified_admission_receipts"] == []


def test_signature_cannot_be_retargeted_to_another_pr(tmp_path):
    private, public = _keypair(tmp_path)
    head = "a" * 40
    body = _signed_receipt(
        tmp_path, private,
        repo="humanaios-ui/operations", pr=604, issue=602, head=head,
    )
    result = verify_snapshot(_snapshot(body, head=head), _policy(public))
    assert result["pull_requests"][0]["verified_admission_receipts"] == []
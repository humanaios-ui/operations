#!/usr/bin/env python3
"""Verify human-origin evaluation-admission receipts.

The private signing key is intentionally out-of-repository and out-of-agent.
This tool only consumes public keys from the trusted default-branch policy.

Receipt format:

/admit-evaluation-signed
pr=<number>
issue=<number>
head=<40-hex-sha>
-----BEGIN SSH SIGNATURE-----
...
-----END SSH SIGNATURE-----

The signature covers a canonical payload bound to repository, PR, issue, head,
and the EVALUATION_ONLY authority scope.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

TOOL_NAME = "human_admission_verify"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 2

RECEIPT_RE = re.compile(
    r"^/admit-evaluation-signed\s*\n"
    r"pr=(\d+)\s*\n"
    r"issue=(\d+)\s*\n"
    r"head=([0-9a-fA-F]{40})\s*\n"
    r"(-----BEGIN SSH SIGNATURE-----\n.*?\n-----END SSH SIGNATURE-----)\s*$",
    re.S,
)


def canonical_payload(repository: str, pr: int, issue: int, head: str) -> str:
    return (
        "HUMANAIOS_EVALUATION_ADMISSION_V1\n"
        f"repository={repository}\n"
        f"pr={pr}\n"
        f"issue={issue}\n"
        f"head={head.lower()}\n"
        "authority=EVALUATION_ONLY\n"
    )


def parse_receipt(body: str) -> dict[str, Any] | None:
    m = RECEIPT_RE.match((body or "").strip())
    if not m:
        return None
    return {
        "pr": int(m.group(1)),
        "issue": int(m.group(2)),
        "head": m.group(3).lower(),
        "signature": m.group(4) + "\n",
    }


def verify_signature(
    *,
    payload: str,
    signature: str,
    principal: str,
    public_key: str,
    namespace: str,
) -> bool:
    if not principal or not public_key:
        return False
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        allowed = root / "allowed_signers"
        sig = root / "receipt.sig"
        allowed.write_text(f"{principal} {public_key.strip()}\n", encoding="utf-8")
        sig.write_text(signature, encoding="utf-8")
        proc = subprocess.run(
            [
                "ssh-keygen", "-Y", "verify",
                "-f", str(allowed),
                "-I", principal,
                "-n", namespace,
                "-s", str(sig),
            ],
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return proc.returncode == 0


def verify_snapshot(snapshot: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    cfg = policy.get("human_attestation") or {}
    namespace = str(cfg.get("namespace") or "humanaios-evaluation-admission-v1")
    signers = cfg.get("authorized_signers") or []
    repository = str(snapshot.get("repository") or "")

    for pr in snapshot.get("pull_requests") or []:
        number = int(pr.get("number") or 0)
        head = str(pr.get("head_sha") or "").lower()
        verified = []
        carriers = []
        for source_name in ("reviews", "comments"):
            for item in pr.get(source_name) or []:
                body = str(item.get("body") or "")
                receipt = parse_receipt(body)
                if not receipt:
                    continue
                if receipt["pr"] != number or receipt["head"] != head:
                    continue
                payload = canonical_payload(
                    repository, number, receipt["issue"], head
                )
                carrier = str(
                    (item.get("user") or {}).get("login")
                    if isinstance(item.get("user"), dict)
                    else item.get("user") or ""
                )
                carriers.append({
                    "source": source_name,
                    "carrier": carrier,
                    "issue": receipt["issue"],
                })
                for signer in signers:
                    principal = str(signer.get("principal") or "")
                    public_key = str(signer.get("public_key") or "")
                    if verify_signature(
                        payload=payload,
                        signature=receipt["signature"],
                        principal=principal,
                        public_key=public_key,
                        namespace=namespace,
                    ):
                        verified.append({
                            "principal": principal,
                            "issue": receipt["issue"],
                            "pr": number,
                            "head": head,
                            "authority": "EVALUATION_ONLY",
                            "carrier": carrier,
                            "source": source_name,
                        })
                        break
        pr["human_attestation_candidates"] = carriers
        pr["verified_admission_receipts"] = verified
    return snapshot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot")
    ap.add_argument("--policy")
    ap.add_argument("--output")
    ap.add_argument("--print-payload", action="store_true")
    ap.add_argument("--repository")
    ap.add_argument("--pr", type=int)
    ap.add_argument("--issue", type=int)
    ap.add_argument("--head")
    args = ap.parse_args()

    if args.print_payload:
        print(canonical_payload(args.repository, args.pr, args.issue, args.head), end="")
        return 0

    if not args.snapshot or not args.policy:
        ap.error("--snapshot and --policy are required unless --print-payload is used")

    snap_path = Path(args.snapshot)
    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    result = verify_snapshot(snapshot, policy)
    out = Path(args.output or args.snapshot)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

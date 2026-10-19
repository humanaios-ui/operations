#!/usr/bin/env python3
"""Read-only HTTP witness for the existing public INTENT-OS -> Resource Miner path.

Builder v1.7 compliant. This is a repeatable *technical* probe, not human
success, eligibility, production admission, or an authenticated attestation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.parse import urlsplit

from resource_miner.intent_os import PUBLIC_SOURCES, _public_https

TOOL_NAME = "on_track_execution"
TOOL_VERSION = "0.2.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION = "S-101826-on-track-http-execution"
TOOL_ZONE = 1
OBJECTIVE = "Find grants to support AI research"
NEGATIVE = "Find theatrical costumes"
ORIGIN = "http://127.0.0.1:8766"
MAX_BODY = 262144


def digest(record: dict) -> str:
    raw = json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _origin(value: str) -> str:
    parts = urlsplit(value)
    if value != ORIGIN or parts.username or parts.password or parts.path or parts.query or parts.fragment:
        raise ValueError("v0.2 tests exactly the localhost service; public targets require a separately authorized workflow")
    return ORIGIN


def _request(path: str, data: dict | None = None) -> tuple[int, str, bytes]:
    req = Request(ORIGIN + path, headers={"Accept": "application/json" if data else "text/html"},
                  data=(json.dumps(data).encode("utf-8") if data is not None else None),
                  method="POST" if data is not None else "GET")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    response = build_opener(NoRedirect()).open(req, timeout=8)
    with response:
        if response.status != 200:
            raise ValueError("Unexpected HTTP status")
        length = response.headers.get("Content-Length")
        if length is not None and int(length) > MAX_BODY:
            raise ValueError("Response too large")
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise ValueError("Response too large")
        return response.status, response.headers.get("Content-Type", ""), body


def _check_result(data: dict, expect_matches: bool) -> tuple[bool, int, str]:
    if not isinstance(data, dict):
        raise ValueError("Response is not a JSON object")
    if data.get("source_mode") != "snapshot" or data.get("source_status") != "CURATED_SNAPSHOT_NOT_LIVE":
        raise ValueError("Snapshot incorrectly presented as live")
    if data.get("eligibility") != "NOT_ASSESSED" or data.get("authority") != "NONE":
        raise ValueError("Unauthorized eligibility or authority claim")
    if data.get("execution") != "DISABLED" or data.get("receipt_kind") != "UNSIGNED_INPUT_AND_SELECTION_DIGEST_NOT_AN_ATTESTATION":
        raise ValueError("Execution or digest falsely represented")
    if not re.fullmatch(r"[a-f0-9]{64}", str(data.get("receipt_sha256", ""))):
        raise ValueError("Missing bounded search digest")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or len(candidates) > 10:
        raise ValueError("Bad candidate collection")
    if not isinstance(data.get("shown_count"), int) or data["shown_count"] != len(candidates):
        raise ValueError("Candidate counts mismatch")
    if bool(candidates) != expect_matches:
        raise ValueError("Unexpected candidate matching behavior")
    if expect_matches and data.get("status") not in {"CANDIDATES_FOR_HUMAN_REVIEW", "PARTIAL_CANDIDATES_FOR_HUMAN_REVIEW"}:
        raise ValueError("Candidates not explicitly for human review")
    if not expect_matches and data.get("status") not in {"NO_SUPPORTED_MATCH", "PARTIAL_SEARCH_NO_MATCH"}:
        raise ValueError("Missing abstention")
    for c in candidates:
        if not isinstance(c, dict) or c.get("source_name") not in PUBLIC_SOURCES:
            raise ValueError("Untrusted/private source included")
        if _public_https(c.get("source_url")) is None or c.get("eligibility_assessed") is not False:
            raise ValueError("Unsafe source URL or eligibility claim")
    return True, len(candidates), str(data["receipt_sha256"])


def run_probe(origin: str = ORIGIN, *, checkout_sha: str = "UNVERIFIED") -> dict:
    _origin(origin)
    status, ctype, page = _request("/intent-os")
    if "text/html" not in ctype.lower() or b"/api/intent" not in page or b"INTENT-OS" not in page:
        raise ValueError("Human-facing route unavailable")
    checks = ["GET /intent-os:200"]
    _, ctype, raw = _request("/api/intent", {"objective": OBJECTIVE, "source_mode": "snapshot"})
    if "application/json" not in ctype:
        raise ValueError("Expected JSON response")
    positive = json.loads(raw.decode("utf-8"))
    _, count, selection_digest = _check_result(positive, True)
    checks.append("POST /api/intent snapshot:matching public candidates")
    _, _, raw2 = _request("/api/intent", {"objective": NEGATIVE, "source_mode": "snapshot"})
    negative = json.loads(raw2.decode("utf-8"))
    _check_result(negative, False)
    checks.append("POST /api/intent unrelated goal:abstains")
    receipt = {
        "schema": "humanaios.on_track_execution/v0.2",
        "goal_id": "INTENT_OS_RESOURCE_MINER_USABLE",
        "environment": "LOCAL_LOOPBACK_HTTP",
        "checkout_sha": checkout_sha if re.fullmatch(r"[0-9a-f]{40}", checkout_sha) else "UNVERIFIED",
        "verification_method": "INDEPENDENT_HTTP_CLIENT_AGAINST_RUNNING_APP",
        "technical_state": "TESTED_LOCAL_HTTP",
        "candidate_count": count,
        "selection_digest": selection_digest,
        "checks": checks,
        "eligibility": "NOT_ASSESSED",
        "user_outcome": "UNVERIFIED",
        "production_deployment": "UNVERIFIED",
        "authority_effect": "NONE",
        "attestation": "UNSIGNED_WORKFLOW_ARTIFACT",
        "limitations": "No source-link reachability probe, independent cloud deploy SHA, signed witness, or human task completion.",
    }
    receipt["sha256"] = digest(receipt)
    return receipt


def smoke_test() -> None:
    for forbidden in ("https://evil.example", "http://127.0.0.1:8766/override",
                      "http://localhost:8766", "http://169.254.169.254"):
        try:
            _origin(forbidden)
        except ValueError:
            continue
        raise AssertionError("Arbitrary target accepted")
    assert _origin(ORIGIN) == ORIGIN
    print("on-track HTTP witness smoke test: PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default=ORIGIN)
    parser.add_argument("--checkout-sha", default="UNVERIFIED")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.smoke_test:
            smoke_test()
            return 0
        receipt = run_probe(args.origin, checkout_sha=args.checkout_sha)
        encoded = json.dumps(receipt, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        else:
            print(encoded)
        return 0
    except (ValueError, OSError, URLError, HTTPError, UnicodeError, json.JSONDecodeError) as exc:
        print("On-track execution unverified: " + type(exc).__name__ + ": " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

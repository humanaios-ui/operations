#!/usr/bin/env python3
"""Join declared GitHub work with a separate live HTTP test into a non-authorizing view.

Builder v1.7 compliant. The receipt is UNSIGNED; digest checks detect accidental
changes, not forgery. Tested local HTTP never means a human achieved the goal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from resource_miner.on_track_execution import digest as digest_execution

TOOL_NAME = "on_track_progress"
TOOL_VERSION = "0.2.0"
TOOL_CATEGORY = "reporting_tool"
TOOL_SESSION = "S-101826-on-track-join"
TOOL_ZONE = 1

REF_URL = re.compile(r"^https://github\.com/humanaios-ui/operations/(issues|pull)/[0-9]+$")
MAX_REPORT = 1048576
MAX_ITEMS = 500


def digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True).encode("utf-8")).hexdigest()


def projection(report: dict, receipt: dict | None) -> dict:
    if report.get("schema") != "humanaios.on_track_reflex/v0.1" or report.get("overall") != "UNVERIFIED":
        raise ValueError("Reflex schema or state refused")
    if report.get("authority_effect") != "NONE" or report.get("merge_authority") is not False:
        raise ValueError("Reflex may not authorize")
    saved = report.get("snapshot_sha256")
    unsigned = {k: v for k, v in report.items() if k != "snapshot_sha256"}
    if not isinstance(saved, str) or digest(unsigned) != saved:
        raise ValueError("Observer snapshot digest mismatch (not cryptographic attestation)")
    scope = report.get("scope")
    if not isinstance(scope, dict) or scope.get("repository") != "humanaios-ui/operations":
        raise ValueError("Unexpected work scope")
    counts = report.get("counts")
    if not isinstance(counts, dict) or counts.get("verified_user_outcomes") != 0:
        raise ValueError("Unexpected claimed human outcome")
    items = report.get("items")
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ValueError("Invalid work collection")
    shown = []
    for row in items:
        if not isinstance(row, dict):
            raise ValueError("Invalid work row")
        if row.get("goal_mapping") not in ("DECLARED_ANCHOR", "DECLARED_BY_AUTHOR"):
            continue
        if row.get("authority_effect") != "NONE" or row.get("operator_outcome") != "UNVERIFIED":
            raise ValueError("Unverified claim elevated")
        if row.get("landing_state", "UNVERIFIED") not in ("UNVERIFIED", "AT_RISK"):
            raise ValueError("Unsupported landing state")
        url = row.get("url")
        if not isinstance(url, str) or not REF_URL.fullmatch(url):
            raise ValueError("Unsafe work link")
        shown.append({
            "url": url,
            "ref": str(row.get("ref", ""))[:90],
            "title": str(row.get("title", ""))[:160],
            "goal_mapping": row["goal_mapping"],
            "landing_state": row.get("landing_state", "UNVERIFIED"),
            "next_action": str(row.get("next_action", ""))[:220],
        })
    technical = {"state": "UNVERIFIED", "environment": "NOT_TESTED",
                 "candidate_count": 0, "receipt_digest": None,
                 "provenance": "NO_EXECUTION_RECEIPT"}
    if receipt is not None:
        if (not isinstance(receipt, dict)
                or receipt.get("schema") != "humanaios.on_track_execution/v0.2"
                or receipt.get("environment") != "LOCAL_LOOPBACK_HTTP"
                or receipt.get("technical_state") != "TESTED_LOCAL_HTTP"
                or receipt.get("user_outcome") != "UNVERIFIED"
                or receipt.get("production_deployment") != "UNVERIFIED"
                or receipt.get("authority_effect") != "NONE"
                or receipt.get("attestation") != "UNSIGNED_WORKFLOW_ARTIFACT"):
            raise ValueError("Execution report cannot grant user success")
        receipt_hash = receipt.get("sha256")
        if not isinstance(receipt_hash, str) or digest_execution(
            {k: v for k, v in receipt.items() if k != "sha256"}
        ) != receipt_hash:
            raise ValueError("Execution digest mismatch")
        checks = receipt.get("checks")
        if not isinstance(checks, list) or checks != [
            "GET /intent-os:200",
            "GET /on-track:200",
            "POST /api/intent snapshot:matching public candidates",
            "POST /api/intent unrelated goal:abstains",
        ]:
            raise ValueError("Incomplete HTTP checks")
        count = receipt.get("candidate_count")
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 10:
            raise ValueError("Invalid candidate count")
        technical = {"state": "TESTED_LOCAL_HTTP", "environment": "LOCAL_LOOPBACK_HTTP",
                     "candidate_count": count, "receipt_digest": receipt_hash,
                     "provenance": "UNSIGNED_WORKFLOW_ARTIFACT_NOT_INDEPENDENT_ATTESTATION"}
    payload = {
        "schema": "humanaios.on_track_progress/v0.2",
        "question": "What actually moves us toward a usable INTENT-OS and Resource Miner?",
        "overall": "UNVERIFIED",
        "technical_execution": technical,
        "human_user_outcome": "UNVERIFIED",
        "production_deployment": "UNVERIFIED",
        "observed_scope": {
            "repository": scope["repository"],
            "inspected": scope.get("items_examined", 0),
            "mapped_declarations": len(shown),
            "unmapped": counts.get("unmapped", 0),
            "partial_sample": bool(scope.get("sampling_truncated") or scope.get("may_omit_closed_work")
                                   or not scope.get("cross_repository_coverage")),
            "source_digest": saved,
        },
        "linked_work": shown[:30],
        "next_milestone": "Verify public deployment and human objective-to-resource decision with independent receipt.",
        "limitations": ("The HTTP probe ran against local service + stored snapshot only. "
                        "It did not check live funding, deployed commit, user interaction, "
                        "eligibility or third-party source reachability. Unmapped does not mean off-track."),
        "authority_effect": "NONE",
        "merge_authority": False,
        "deployment_authority": False,
    }
    payload["sha256"] = digest(payload)
    return payload


def embed(template: str, payload: dict) -> str:
    marker = "<!--@@EMBED_SNAPSHOT@@-->"
    if template.count(marker) != 1:
        raise ValueError("Progress HTML template marker missing or repeated")
    raw = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    safe = raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return template.replace(marker, '<script id="embedded-progress" type="application/json">' + safe + '</script>')


def read_json(path: Path) -> dict:
    if path.stat().st_size > MAX_REPORT:
        raise ValueError("Report size exceeds bound")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object")
    return value


def smoke_test():
    assert REF_URL.fullmatch("https://github.com/humanaios-ui/operations/pull/822")
    assert not REF_URL.fullmatch("https://evil.example/pull/822")
    assert "\\u003c" in embed("<!--@@EMBED_SNAPSHOT@@-->", {"x": "</script><b>"})
    print("on-track progress smoke test: PASS")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report", type=Path)
    p.add_argument("--receipt", type=Path)
    p.add_argument("--template", type=Path)
    p.add_argument("--json-out", type=Path)
    p.add_argument("--html-out", type=Path)
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()
    try:
        if args.smoke_test:
            smoke_test()
            return 0
        if not args.report or not args.json_out or not args.template or not args.html_out:
            raise ValueError("--report, --template, --json-out, and --html-out required")
        r = projection(read_json(args.report), read_json(args.receipt) if args.receipt else None)
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.html_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(r, indent=2) + "\n", encoding="utf-8")
        args.html_out.write_text(embed(args.template.read_text(encoding="utf-8"), r), encoding="utf-8")
        print("On-track progress:", r["overall"], r["technical_execution"]["state"],
              "mapped:", r["observed_scope"]["mapped_declarations"], "digest:", r["sha256"])
        return 0
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as e:
        print("On-track progress UNVERIFIED: " + type(e).__name__ + ": " + str(e))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

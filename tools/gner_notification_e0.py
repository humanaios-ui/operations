"""GNER-E0: offline GitHub notification lead interpreter.

Email is untrusted discovery only; GitHub receipts are verified *outside* this
module. No Gmail/GitHub API calls, I/O, authority, or execution.

Builder v1.7 compliant · cli_tool

TOOL_NAME = "gner_notification_e0"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "analysis_tool"
TOOL_ZONE = 1
"""
from __future__ import annotations
import re
import sys
import argparse
import json
from collections import defaultdict
from urllib.parse import urlsplit

TOOL_NAME = "gner_notification_e0"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "analysis_tool"
TOOL_ZONE = 1

REPO = "humanaios-ui/operations"
SHA = re.compile(r"(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])")
PR = re.compile(r"(?:\bPR\s*#|operations#|/pull/)(\d{1,7})\b", re.I)
RUN = re.compile(r"https://github\.com/humanaios-ui/operations/actions/runs/(\d{1,15})(?:[/?#]|$)")
WORKFLOW = re.compile(r"\b(quality-baseline|repository-admission-gate|tool-manifest|manifest-sync-gate|builder-lint|security-gates)\b", re.I)


def parse_notification(subject: str, body: str) -> dict:
    if not isinstance(subject, str) or not isinstance(body, str) or len(subject) > 500 or len(body) > 25000:
        raise ValueError("invalid or oversized notification")
    if "[humanaios-ui/operations]" not in subject:
        return {"state": "ABSTAIN", "reason": "repository not in subject", "authority": "NONE"}
    p = PR.search(subject)
    run = RUN.search(body)
    workflow = WORKFLOW.search(subject)
    sha = SHA.search(subject)
    is_review = "commented on this pull request" in body.lower() or "changes recommended" in body.lower()
    kind = "REVIEW_LEAD" if is_review else "WORKFLOW_FAILURE_LEAD" if "failed" in subject.lower() else "NOTIFICATION_LEAD"
    return {"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": REPO,
            "pr": int(p.group(1)) if p else None,
            "run_id": int(run.group(1)) if run else None,
            "workflow": workflow.group(1).lower() if workflow else None,
            "sha_prefix": sha.group(0) if sha else None, "kind": kind,
            "authority": "NONE", "execution": "DISABLED"}


def correlate(leads: list, verified_receipts: list) -> dict:
    """Caller-provided receipts are UNVERIFIED; no API or authenticator here.

    A separate trusted GitHub verifier must attest immutable run/job/commit
    facts before any CANONICAL_VERIFIED state can be emitted elsewhere.
    """
    if not isinstance(leads, list) or not isinstance(verified_receipts, list) or len(leads) > 100 or len(verified_receipts) > 100:
        raise ValueError("bounded lists required")
    results = []
    groups = defaultdict(list)
    for index, lead in enumerate(leads):
        if not isinstance(lead, dict):
            results.append({"state": "ABSTAIN", "reason": "malformed lead", "index": index})
            continue
        if lead.get("state") != "EMAIL_OBSERVED_UNVERIFIED" or lead.get("repository") != REPO:
            results.append({"state": "ABSTAIN", "reason": "unrecognized lead", "index": index})
            continue
        # NEVER promote based on caller-supplied 'verified' fields: input can be spoofed.
        result = {key: lead.get(key) for key in ("pr", "run_id", "workflow", "kind", "sha_prefix")}
        result.update(index=index, state="AWAITING_CANONICAL_VERIFICATION", authority="NONE")
        results.append(result)
        # Group *leads* only by matching explicit run id; no causal deduplication.
        if isinstance(lead.get("run_id"), int):
            groups[str(lead["run_id"])].append(index)
    return {"schema": "GNER-E0-v0.1", "results": results,
            "duplicate_notification_run_ids": {k: v for k, v in groups.items() if len(v) > 1},
            "canonical_verified_count": 0,
            "note": "All email leads and caller-provided receipts are unverified until independent GitHub verification. Duplicate run IDs are not shared root causes.",
            "authority": "NONE", "execution": "DISABLED"}


def redact_github_url(url: str) -> str | None:
    """Return only bounded canonical GitHub run / PR URLs, excluding tokens."""
    if not isinstance(url, str) or len(url) > 4000:
        return None
    try:
        p = urlsplit(url)
        if p.scheme != "https" or p.netloc != "github.com" or p.username or p.password:
            return None
        path = p.path
        if re.fullmatch(r"/humanaios-ui/operations/(?:pull/\d{1,7}|actions/runs/\d{1,15})", path):
            return "https://github.com" + path
    except ValueError:
        return None
    return None


def run_smoke_test() -> dict:
    """Smoke test for Builder v1.7 compliance."""
    tests = []

    # Test parse_notification with valid input
    try:
        result = parse_notification(
            "[humanaios-ui/operations] PR #123 failed: quality-baseline",
            "View workflow run https://github.com/humanaios-ui/operations/actions/runs/37992199793"
        )
        tests.append({
            "test": "parse_notification_valid",
            "passed": result["state"] == "EMAIL_OBSERVED_UNVERIFIED" and result["pr"] == 123
        })
    except Exception as e:
        tests.append({"test": "parse_notification_valid", "passed": False, "error": str(e)})

    # Test parse_notification rejects oversized input
    try:
        parse_notification("x" * 501, "body")
        tests.append({"test": "parse_notification_oversized", "passed": False})
    except ValueError:
        tests.append({"test": "parse_notification_oversized", "passed": True})

    # Test correlate with valid leads
    try:
        leads = [parse_notification(
            "[humanaios-ui/operations] PR #123 failed",
            "https://github.com/humanaios-ui/operations/actions/runs/37992199793"
        )]
        result = correlate(leads, [])
        tests.append({
            "test": "correlate_valid",
            "passed": result["authority"] == "NONE" and result["canonical_verified_count"] == 0
        })
    except Exception as e:
        tests.append({"test": "correlate_valid", "passed": False, "error": str(e)})

    # Test redact_github_url with canonical URL
    try:
        url = "https://github.com/humanaios-ui/operations/pull/123"
        result = redact_github_url(url)
        tests.append({"test": "redact_canonical_url", "passed": result == url})
    except Exception as e:
        tests.append({"test": "redact_canonical_url", "passed": False, "error": str(e)})

    # Test redact_github_url rejects private IPs
    try:
        result = redact_github_url("https://10.0.0.1/operations/pull/123")
        tests.append({"test": "redact_private_ip", "passed": result is None})
    except Exception as e:
        tests.append({"test": "redact_private_ip", "passed": False, "error": str(e)})

    passed = sum(1 for t in tests if t.get("passed"))
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "tests": tests,
        "summary": f"{passed}/{len(tests)} tests passed"
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GNER-E0 notification lead interpreter")
    parser.add_argument("--smoke-test", action="store_true", help="Run smoke tests and exit")
    args = parser.parse_args()

    if args.smoke_test:
        result = run_smoke_test()
        print(json.dumps(result, indent=2))
        sys.exit(0 if all(t.get("passed") for t in result["tests"]) else 1)

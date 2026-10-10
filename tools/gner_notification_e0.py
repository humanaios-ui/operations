"""GNER-E0: offline GitHub notification lead interpreter.

Email is untrusted discovery only; GitHub receipts are verified *outside* this
module. No Gmail/GitHub API calls, I/O, authority, or execution.
"""
from __future__ import annotations
import re
import sys
import json
from collections import defaultdict
from urllib.parse import urlsplit

TOOL_NAME = "gner_notification_e0"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
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


def run_smoke_test() -> bool:
    """Smoke test for Builder v1.7 compliance."""
    tests = []
    try:
        result = parse_notification(
            "[humanaios-ui/operations] Workflow failed on operations#123",
            "https://github.com/humanaios-ui/operations/actions/runs/456789"
        )
        tests.append(("parse_valid_notification", result["state"] == "EMAIL_OBSERVED_UNVERIFIED"))
    except Exception:
        tests.append(("parse_valid_notification", False))

    try:
        result = correlate(
            [{"state": "EMAIL_OBSERVED_UNVERIFIED", "repository": REPO, "run_id": 123, "pr": 456, "workflow": "quality-baseline", "kind": "WORKFLOW_FAILURE_LEAD", "sha_prefix": "abc123", "authority": "NONE", "execution": "DISABLED"}],
            []
        )
        tests.append(("correlate_valid_leads", "results" in result and len(result["results"]) == 1))
    except Exception:
        tests.append(("correlate_valid_leads", False))

    try:
        url = redact_github_url("https://github.com/humanaios-ui/operations/pull/123")
        tests.append(("redact_valid_url", url is not None))
    except Exception:
        tests.append(("redact_valid_url", False))

    passed = sum(1 for _, p in tests if p)
    print(f"{TOOL_NAME} smoke test: {passed}/{len(tests)} checks")
    return passed == len(tests)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke-test":
        sys.exit(0 if run_smoke_test() else 1)
    else:
        print("Usage: python3 gner_notification_e0.py [--smoke-test]")
        sys.exit(0)

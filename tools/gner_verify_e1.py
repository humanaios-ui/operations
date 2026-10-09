"""GNER-E1 explicit, read-only authenticated GitHub workflow-run reconciliation.

Live query is opt-in CLI only, uses a narrowly scoped token from the environment.
No Gmail API, GitHub mutations, comment posting, automatic scheduling or authority.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request

from gner_notification_e0 import parse_notification

REPO = "humanaios-ui/operations"
ALLOWED_WORKFLOWS = frozenset({
    "quality-baseline", "repository-admission-gate", "tool-manifest",
    "manifest-sync-gate", "builder-lint", "security-gates",
})
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class VerificationDenied(ValueError):
    pass


def reconcile(lead: dict, canonical: dict) -> dict:
    """Compare a lead against a trusted GitHub API response.

    The 'canonical' mapping MUST originate from authenticated GitHub HTTPS.
    Calling this pure function with a caller-controlled mapping is NOT proof
    of independent verification. The only approved live entry point is
    verify_lead(), which obtains the mapping itself.
    """
    result = {"schema": "GNER-E1-v0.1", "authority": "NONE",
              "execution": "DISABLED", "state": "CONFLICT"}
    if lead.get("state") != "EMAIL_OBSERVED_UNVERIFIED" or lead.get("repository") != REPO:
        result["reason"] = "invalid lead"
        return result
    if not isinstance(lead.get("run_id"), int) or lead["run_id"] <= 0:
        result["state"] = "ABSTAIN"
        result["reason"] = "run identifier absent"
        return result
    if not isinstance(canonical, dict) or canonical.get("id") != lead["run_id"]:
        result["reason"] = "run ID mismatch"
        return result
    repo = canonical.get("repository")
    if not isinstance(repo, dict) or repo.get("full_name") != REPO:
        result["reason"] = "repository mismatch"
        return result
    sha = canonical.get("head_sha")
    if not isinstance(sha, str) or SHA_PATTERN.fullmatch(sha) is None:
        result["reason"] = "invalid canonical head SHA"
        return result
    if lead.get("sha_prefix") and not sha.startswith(lead["sha_prefix"]):
        result["reason"] = "head SHA conflict"
        return result
    expected_workflow = lead.get("workflow")
    observed_workflow = canonical.get("name")
    if expected_workflow not in ALLOWED_WORKFLOWS or observed_workflow != expected_workflow:
        result["reason"] = "workflow mismatch or unsupported"
        return result
    if canonical.get("event") not in ("pull_request", "push", "workflow_dispatch"):
        result["reason"] = "unsupported workflow event"
        return result
    if canonical.get("status") != "completed" or canonical.get("conclusion") not in (
        "success", "failure", "cancelled", "timed_out", "neutral", "skipped"
    ):
        result["state"] = "ABSTAIN"
        result["reason"] = "run not terminal"
        return result
    if lead.get("kind") == "WORKFLOW_FAILURE_LEAD" and canonical["conclusion"] != "failure":
        result["reason"] = "email failure claim contradicted"
        return result
    if lead.get("pr") is not None:
        prs = canonical.get("pull_requests")
        if not isinstance(prs, list) or lead["pr"] not in [
            pr.get("number") for pr in prs if isinstance(pr, dict)
        ]:
            result["state"] = "ABSTAIN"
            result["reason"] = "PR association not confirmed"
            return result
    result.update(state="CANONICAL_VERIFIED", reason="authenticated GitHub run agrees",
                  run_id=canonical["id"], head_sha=sha, repository=REPO,
                  workflow=observed_workflow, conclusion=canonical["conclusion"],
                  evidence_url=f"https://github.com/{REPO}/actions/runs/{canonical['id']}",
                  claim_scope="run metadata only; no job-level root cause or admission authority")
    return result


def verify_lead(lead: dict, *, github_token: str, timeout: int = 10) -> dict:
    """Fetch canonical run from GitHub API using bearer token; no supplied URL."""
    if not isinstance(lead, dict) or lead.get("repository") != REPO:
        raise VerificationDenied("unsupported repository")
    run_id = lead.get("run_id")
    if type(run_id) is not int or not 0 < run_id < 10**15:
        raise VerificationDenied("run ID required")
    if not github_token or not isinstance(github_token, str):
        raise VerificationDenied("GITHUB_TOKEN required")
    url = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}"
    request = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + github_token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "humanaios-gner-read-only/0.1",
    }, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise VerificationDenied("GitHub read failed")
            raw = response.read(131073)
    except Exception as exc:
        raise VerificationDenied("GitHub canonical verification unavailable") from exc
    if len(raw) > 131072:
        raise VerificationDenied("GitHub response too large")
    try:
        return reconcile(lead, json.loads(raw))
    except (ValueError, TypeError) as exc:
        raise VerificationDenied("invalid GitHub response") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Explicit read-only GitHub run verification")
    parser.add_argument("--subject", required=True, help="Only use sanitized notification subject")
    parser.add_argument("--run-id", required=True, type=int, help="Run ID observed in notification")
    args = parser.parse_args()
    lead = parse_notification(args.subject, f"https://github.com/{REPO}/actions/runs/{args.run_id}")
    lead["run_id"] = args.run_id
    verdict = verify_lead(lead, github_token=os.environ.get("GITHUB_TOKEN", ""))
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__":
    main()

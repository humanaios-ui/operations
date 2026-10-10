"""SCVC v0.2 live GitHub witness: independent read-only API corroboration.

Runs only from trusted default-branch GitHub Actions with a read-only GITHUB_TOKEN.
Candidate JSON and agent-generated receipts are NOT authentication sources.
Observational milestone advancement has authority_effect NONE: no commits,
dispatch, admission, ratification, merge, or private-data access.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request

from experiments.scvc_v02.milestone_controller import validate
from experiments.scvc_v02.oidc_identity import verify_current_workflow, ISSUER, WORKFLOW_REF

REPO = "humanaios-ui/operations"
OWNER, NAME = REPO.split("/")
PILOT_ISSUE = 793
PILOT_PR = 794
PREDECESSOR = 788
DEFAULT = "main"
WORKFLOW = ".github/workflows/scvc-milestone-witness.yml"
REQUIRED_CI = {
    "quality-baseline": ".github/workflows/quality-baseline.yml",
    "security-gates": ".github/workflows/security-gates.yml",
}
SOURCE_PATHS = {
    "SCVC_V01_EXACT_HEAD": "tools/state_continuity_verification_v0_1.py",
    "HLKS_VLR_SCHEMA_PIN": "schemas/validated_learning_record_v1.schema.json",
    "SESSION_GRAPH_SCHEMA_PIN": "chat_graph/schema/longitudinal_graph.schema.json",
    "COORDINATOR_POLICY_PIN": "REPOSITORY_COORDINATOR_POLICY.json",
}
HEX = re.compile(r"[a-f0-9]{40}\Z")
ACCEPTED_EVENTS = frozenset({"schedule", "workflow_dispatch", "workflow_run", "push"})


class WitnessError(Exception):
    """Blocked provenance, malformed response or unverifiable trust root."""


class GitHubReadOnly:
    """Live REST read transport. Do not expose a CLI option to choose an API host."""

    def __init__(self, token: str):
        if not token:
            raise WitnessError("GITHUB_TOKEN_REQUIRED")
        self.token = token

    def get(self, path: str):
        if (not path.startswith("repos/humanaios-ui/operations/")
                or ".." in path or "\\" in path or len(path) > 600):
            raise WitnessError("API_PATH_DENIED")
        req = urllib.request.Request(
            "https://api.github.com/" + path,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer " + self.token,
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "humanaios-scvc-v02-witness",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read(1_100_000)
                if len(content) > 1_000_000:
                    raise WitnessError("API_RESPONSE_OVERSIZE")
                return json.loads(content)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                json.JSONDecodeError) as exc:
            raise WitnessError("GITHUB_API_UNAVAILABLE") from exc


def _sha(value):
    return isinstance(value, str) and bool(HEX.fullmatch(value))


def _require(condition, reason):
    if not condition:
        raise WitnessError(reason)


def _record_file(api, sha, path):
    encoded = urllib.parse.quote(path, safe="/._-")
    obj = api.get(f"repos/{REPO}/contents/{encoded}?ref={sha}")
    _require(isinstance(obj, dict) and obj.get("type") == "file"
             and obj.get("path") == path and _sha(obj.get("sha")),
             "PINNED_FILE_UNAVAILABLE")
    content = obj.get("content")
    _require(obj.get("encoding") == "base64" and isinstance(content, str),
             "PINNED_CONTENT_UNAVAILABLE")
    try:
        raw = base64.b64decode(content, validate=False)
    except (ValueError, base64.binascii.Error) as exc:
        raise WitnessError("PINNED_CONTENT_BAD_ENCODING") from exc
    _require(len(raw) < 500_000, "PINNED_FILE_TOO_LARGE")
    gitblob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    _require(gitblob == obj["sha"], "PINNED_BLOB_SHA_MISMATCH")
    return obj["sha"], raw


def _protection(api):
    """Only positively established required-review AND required-CI rules qualify.

    Non-fast-forward and branch deletion restrictions alone do not constitute
    a protected witness issuer; 403 or missing rules remain UNVERIFIED.
    """
    rules = api.get(f"repos/{REPO}/rulesets")
    _require(isinstance(rules, list) and len(rules) <= 100, "RULESET_INVENTORY_UNAVAILABLE")
    pr_review = False
    ci = False
    for item in rules:
        if not isinstance(item, dict) or item.get("enforcement") != "active":
            continue
        rid = item.get("id")
        if type(rid) is not int or rid <= 0:
            continue
        detail = api.get(f"repos/{REPO}/rulesets/{rid}")
        if not isinstance(detail, dict) or detail.get("enforcement") != "active":
            continue
        conditions = detail.get("conditions", {}).get("ref_name", {})
        includes = conditions.get("include", [])
        excludes = conditions.get("exclude", [])
        if not ("~ALL" in includes or "refs/heads/main" in includes or "main" in includes):
            continue
        if any(x in excludes for x in ("~ALL", "main", "refs/heads/main")):
            continue
        for rule in detail.get("rules", []):
            if rule.get("type") == "pull_request":
                params = rule.get("parameters") or {}
                pr_review = pr_review or (params.get("required_approving_review_count", 0) >= 1)
            if rule.get("type") == "required_status_checks":
                checks = (rule.get("parameters") or {}).get("required_status_checks") or []
                contexts = {r.get("context") for r in checks if isinstance(r, dict)}
                ci = ci or any("quality" in str(x).lower() for x in contexts)
    return pr_review and ci


def _runs(api, head, pr_number):
    qs = urllib.parse.urlencode({"head_sha": head, "event": "pull_request", "per_page": 100})
    obj = api.get(f"repos/{REPO}/actions/runs?{qs}")
    _require(isinstance(obj, dict) and isinstance(obj.get("workflow_runs"), list)
             and obj.get("total_count", 0) <= 100, "RUN_LIST_INCOMPLETE")
    found = {}
    for run in obj["workflow_runs"]:
        if not isinstance(run, dict):
            continue
        name = run.get("name")
        if name not in REQUIRED_CI:
            continue
        prs = run.get("pull_requests") or []
        valid = (
            run.get("path") == REQUIRED_CI[name]
            and run.get("head_sha") == head
            and run.get("event") == "pull_request"
            and run.get("repository", {}).get("full_name") == REPO
            and run.get("head_repository", {}).get("full_name") == REPO
            and type(run.get("run_attempt")) is int and run["run_attempt"] > 0
            and any(p.get("number") == pr_number and p.get("head", {}).get("sha") == head
                    for p in prs if isinstance(p, dict))
        )
        if not valid:
            continue
        if name not in found or (run["id"], run["run_attempt"]) > (
                found[name]["id"], found[name]["run_attempt"]):
            found[name] = run
    refs = {}
    for name in REQUIRED_CI:
        run = found.get(name)
        _require(run is not None and run.get("status") == "completed"
                 and run.get("conclusion") == "success", "EXACT_HEAD_CI_NOT_VERIFIED")
        run_id = run["id"]
        _require(type(run_id) is int and run_id > 0, "INVALID_RUN_ID")
        # Re-read exact run identity rather than trusting collection metadata alone.
        detailed = api.get(f"repos/{REPO}/actions/runs/{run_id}")
        _require(detailed.get("run_attempt") == run["run_attempt"]
                 and detailed.get("head_sha") == head
                 and detailed.get("path") == REQUIRED_CI[name]
                 and detailed.get("conclusion") == "success"
                 and detailed.get("status") == "completed",
                 "RUN_IDENTITY_CHANGED")
        jobs = api.get(f"repos/{REPO}/actions/runs/{run_id}/jobs?per_page=100")
        rows = jobs.get("jobs") if isinstance(jobs, dict) else None
        _require(isinstance(rows, list) and 0 < len(rows) <= 100
                 and jobs.get("total_count", 0) <= 100
                 and any(j.get("conclusion") == "success" for j in rows)
                 and all(j.get("conclusion") in ("success", "skipped") for j in rows),
                 "CI_JOB_RESULTS_INCOMPLETE")
        refs[name] = {"run_id": run_id, "run_attempt": run["run_attempt"],
                      "head_sha": head, "workflow_path": REQUIRED_CI[name]}
    return refs


def collect(api, context, *, identity=None):
    """Corroborate facts through authenticated GitHub REST in the trusted job.

    The output is public metadata. It is not independently signed and must not
    be accepted as a trusted fact if copied to a candidate JSON file.
    """
    _require(isinstance(identity, dict)
             and identity.get("identity_verified") is True
             and identity.get("issuer") == ISSUER
             and identity.get("workflow_ref") == WORKFLOW_REF
             and identity.get("run_id") == context.get("run_id")
             and identity.get("run_attempt") == context.get("run_attempt")
             and identity.get("subject_head_sha") == context.get("checkout_sha"),
             "SIGNED_WORKFLOW_IDENTITY_REQUIRED")
    _require(isinstance(context, dict)
             and context.get("repository") == REPO
             and context.get("ref") == "refs/heads/main"
             and context.get("event_name") in ACCEPTED_EVENTS
             and _sha(context.get("checkout_sha")), "UNTRUSTED_WORKFLOW_CONTEXT")
    repo = api.get(f"repos/{REPO}")
    _require(repo.get("full_name") == REPO and repo.get("default_branch") == DEFAULT,
             "REPOSITORY_IDENTITY_MISMATCH")
    main = api.get(f"repos/{REPO}/branches/main")
    sha = main.get("commit", {}).get("sha")
    _require(sha == context["checkout_sha"], "DEFAULT_HEAD_MOVED")

    run_id = context.get("run_id")
    run_attempt = context.get("run_attempt")
    _require(type(run_id) is int and run_id > 0 and type(run_attempt) is int
             and run_attempt > 0, "WITNESS_RUN_ID_INVALID")
    self_run = api.get(f"repos/{REPO}/actions/runs/{run_id}")
    _require(self_run.get("head_sha") == sha
             and self_run.get("path") == WORKFLOW
             and self_run.get("run_attempt") == run_attempt
             and self_run.get("event") == context["event_name"]
             and self_run.get("repository", {}).get("full_name") == REPO,
             "WITNESS_RUN_NOT_BOUND_TO_DEFAULT")

    prior = api.get(f"repos/{REPO}/pulls/{PREDECESSOR}")
    _require(prior.get("merged") is True and _sha(prior.get("merge_commit_sha")),
             "PREDECESSOR_NOT_MERGED")
    old = prior["merge_commit_sha"]
    ancestry = api.get(f"repos/{REPO}/compare/{old}...{sha}")
    _require(ancestry.get("status") in ("ahead", "identical"),
             "PREDECESSOR_NOT_ANCESTOR")
    refs = {}
    for predicate, path in SOURCE_PATHS.items():
        blob, raw = _record_file(api, sha, path)
        if predicate == "COORDINATOR_POLICY_PIN":
            policy = json.loads(raw)
            _require(policy.get("state", {}).get("merge_authority") is False
                     and policy.get("schema_version") == "0.3",
                     "COORDINATOR_POLICY_DRIFT")
        refs[predicate] = {"blob_sha": blob, "source_commit": sha}

    target = api.get(f"repos/{REPO}/pulls/{PILOT_PR}")
    _require(target.get("number") == PILOT_PR and target.get("base", {}).get("ref") == DEFAULT
             and target.get("head", {}).get("repo", {}).get("full_name") == REPO
             and _sha(target.get("head", {}).get("sha")), "PILOT_PR_IDENTITY_MISMATCH")
    head = target["head"]["sha"]

    # Candidate CI cannot be accepted if it edits its own CI issuer workflows.
    edits = api.get(f"repos/{REPO}/pulls/{PILOT_PR}/files?per_page=100")
    _require(isinstance(edits, list) and len(edits) < 100, "CHANGED_FILES_INCOMPLETE")
    _require(not ({f.get("filename") for f in edits if isinstance(f, dict)}
                  & set(REQUIRED_CI.values())), "ISSUER_WORKFLOW_MODIFIED_BY_CANDIDATE")
    ci_runs = _runs(api, head, PILOT_PR)
    trust_root = _protection(api)
    return {
        "source": "GITHUB_REST_FROM_TRUSTED_DEFAULT_WORKFLOW",
        "github_oidc_run_identity_verified": True,
        "trusted_checkout_sha": sha,
        "witness_run_id": run_id,
        "witness_run_attempt": run_attempt,
        "predecessor_merge_sha": old,
        "subject_pr": PILOT_PR,
        "subject_head_sha": head,
        "predicates": refs,
        "ci": ci_runs,
        "trust_root_protected": trust_root,
        "cryptographic_attestation_verified": False,
    }


def derive_progress(definition, facts):
    """Advance independently observed *non-authority* M0 when trust root exists.

    For M1–M4 human review and independently scoped evidence remain mandatory.
    This makes the next milestone eligible; it does not authorize doing its work.
    """
    milestones = validate(definition)
    _require(facts.get("source") == "GITHUB_REST_FROM_TRUSTED_DEFAULT_WORKFLOW",
             "NO_INDEPENDENT_WITNESS_SOURCE")
    predicates = facts.get("predicates", {})
    ci = facts.get("ci", {})
    trust = facts.get("trust_root_protected") is True and facts.get("github_oidc_run_identity_verified") is True
    required = milestones[0]["acceptance"]
    all_predicates = all(k in predicates for k in required)
    all_ci = all(k in ci for k in REQUIRED_CI)
    m0 = trust and all_predicates and all_ci and not milestones[0]["human_approval_required"]
    result = []
    for index, node in enumerate(milestones):
        if index == 0:
            status = ("OBSERVATIONAL_MILESTONE_ACHIEVED" if m0
                      else "BLOCKED_TRUST_ROOT" if not trust
                      else "BLOCKED_EVIDENCE")
        elif index == 1 and m0:
            status = "ELIGIBLE_FOR_AUTHORIZED_WORK"
        else:
            status = "BLOCKED_UNATTESTED_DEPENDENCIES"
        result.append({
            "milestone_id": node["id"], "candidate_status": status,
            "observational_achievement": bool(index == 0 and m0),
            "human_approval_required": node["human_approval_required"],
            "governance_accepted": False, "execution_authorized": False,
        })
    return {
        "schema": "humanaios.scvc_live_witness_report.v0.2",
        "objective_issue": PILOT_ISSUE, "subject_pr": PILOT_PR,
        "subject_head_sha": facts["subject_head_sha"],
        "trusted_checkout_sha": facts["trusted_checkout_sha"],
        "witness_run_id": facts["witness_run_id"],
        "witness_run_attempt": facts["witness_run_attempt"],
        "source_api_verified": True,
        "oidc_workflow_identity_verified": facts.get("github_oidc_run_identity_verified") is True,
        "trust_root_protected": trust,
        "cryptographic_attestation_verified": False,
        "milestones": result,
        "authority_effect": "NONE", "can_authorize": False,
        "merge_authority": False, "can_dispatch": False,
        "warning": "GitHub API corroboration is not independent cryptographic attestation or Z2 ratification.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--definition", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    env = os.environ
    context = {
        "repository": env.get("GITHUB_REPOSITORY"),
        "ref": env.get("GITHUB_REF"),
        "event_name": env.get("GITHUB_EVENT_NAME"),
        "checkout_sha": env.get("SCVC_CHECKOUT_SHA"),
        "run_id": int(env.get("GITHUB_RUN_ID", "0")),
        "run_attempt": int(env.get("GITHUB_RUN_ATTEMPT", "0")),
    }
    api = GitHubReadOnly(env.get("GITHUB_TOKEN", ""))
    graph = json.loads(args.definition.read_text(encoding="utf-8"))
    signed_identity = verify_current_workflow(context)
    report = derive_progress(graph, collect(api, context, identity=signed_identity))
    # Outputs contain only public hashes, run IDs, and coarse states.
    args.out.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("SCVC live witness assessment:", [m["candidate_status"] for m in report["milestones"]])


if __name__ == "__main__":
    main()

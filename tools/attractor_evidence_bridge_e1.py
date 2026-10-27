#!/usr/bin/env python3
"""HumanAIOS E1 — source-pinned repository activity and independent outcome-review attestations.
Builder v1.7 compliant

Read-only GitHub GET observer. Source records are NEVER instructions.
No source comment is treated as proof of an award, acquisition, or recovery benefit.
Live response transport is distinct from independently authenticated evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPHandler, HTTPSHandler, HTTPRedirectHandler
from urllib.error import HTTPError, URLError

TOOL_NAME = "attractor_evidence_bridge"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_ZONE = 1
TOOL_SESSION = "S-20261026-ATTRACTOR-E1"

SCHEMA = "humanaios.attractor_evidence_bridge.e1"
REPO_ALLOWLIST = {"humanaios-ui/operations", "humanaios-ui/humanaios", "humanaios-ui/lasting-light-ai"}
OUTCOMES = {"RESOURCE_ACQUIRED", "OBJECTIVE_COMPLETED", "RECOVERY_BENEFIT_DELIVERED"}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9_.:-]{1,100}$")
CODES = {"SUCCESS", "FAILURE", "NEUTRAL", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "SKIPPED", "STALE", "STARTUP_FAILURE", "UNKNOWN"}
CLAIM_KEYS = {"schema", "objective_id", "process_id", "event_type", "source_commit",
              "evidence_ref", "evidence_sha256", "resource_id", "benefit_id", "beneficiary_alias"}
REVIEW_KEYS = {"schema", "claim_comment_id", "claim_sha256", "verdict", "source_commit",
               "independent_evidence_ref", "independent_evidence_sha256"}
GITHUB_PREFIX = "https://github.com/"
MAX_BODY = 8192
MAX_JSON = 2_000_000
PATTERNS = {
    "claim": re.compile(r"^```humanaios-outcome-claim-v1\s*\n([^\x00]*?)\n```\s*$", re.S),
    "review": re.compile(r"^```humanaios-outcome-review-v1\s*\n([^\x00]*?)\n```\s*$", re.S),
}


def utc(value):
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be UTC ISO8601")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("bad timestamp") from exc
    return value


def ident(value, name):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise ValueError(f"invalid {name}")
    return value


def sha40(value):
    if not isinstance(value, str) or not HEX40.fullmatch(value):
        raise ValueError("invalid exact 40-digit commit")
    return value


def sha64(value):
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise ValueError("invalid SHA256")
    return value


def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def checksum(record):
    return hashlib.sha256(canonical(record)).hexdigest()


def link(value, repo):
    if not isinstance(value, str) or len(value) > 256:
        raise ValueError("invalid public evidence reference")
    parsed = urlparse(value)
    if (parsed.scheme != "https" or parsed.netloc != "github.com" or
        parsed.username is not None or parsed.password is not None or
        parsed.fragment or parsed.query or not parsed.path.startswith("/" + repo + "/")):
        raise ValueError("external or private evidence reference cannot be verified by E1")
    return value


def parse_packet(body, kind):
    if not isinstance(body, str) or len(body) > MAX_BODY:
        return None
    m = PATTERNS[kind].fullmatch(body.strip())
    if not m or len(m.group(1)) > 4096:
        return None
    try:
        obj = json.loads(m.group(1))
    except (TypeError, json.JSONDecodeError):
        return None
    return obj if isinstance(obj, dict) else None


def validate_claim(claim, repo):
    if set(claim) - CLAIM_KEYS or not ({"schema", "objective_id", "process_id",
                                        "event_type", "source_commit", "evidence_ref",
                                        "evidence_sha256"} <= set(claim)):
        raise ValueError("claim keys invalid")
    if claim["schema"] != "humanaios.outcome.claim.v1" or claim["event_type"] not in OUTCOMES:
        raise ValueError("claim schema or outcome kind invalid")
    ident(claim["objective_id"], "objective_id")
    ident(claim["process_id"], "process_id")
    sha40(claim["source_commit"])
    link(claim["evidence_ref"], repo)
    sha64(claim["evidence_sha256"])
    for fld in ("resource_id", "benefit_id", "beneficiary_alias"):
        if fld in claim:
            ident(claim[fld], fld)
    if claim["event_type"] == "RESOURCE_ACQUIRED" and not claim.get("resource_id"):
        raise ValueError("acquisition requires a resource id")
    if claim["event_type"] == "RECOVERY_BENEFIT_DELIVERED" and not (
        claim.get("benefit_id") and claim.get("beneficiary_alias")
    ):
        raise ValueError("recovery benefit requires pseudonymous benefit and beneficiary IDs")


def validate_review(review, repo):
    if set(review) != REVIEW_KEYS or review["schema"] != "humanaios.outcome.review.v1":
        raise ValueError("review keys invalid")
    if not isinstance(review["claim_comment_id"], int) or isinstance(review["claim_comment_id"], bool) or review["claim_comment_id"] <= 0:
        raise ValueError("invalid claim reference")
    sha64(review["claim_sha256"])
    sha40(review["source_commit"])
    sha64(review["independent_evidence_sha256"])
    link(review["independent_evidence_ref"], repo)
    if review["verdict"] not in ("SUPPORTS", "REJECTS", "INDETERMINATE"):
        raise ValueError("unsupported verdict")


def is_human(user):
    if not isinstance(user, dict) or not user.get("login"):
        return False
    login = str(user["login"])
    return user.get("type") != "Bot" and not login.endswith("[bot]") and bool(IDENT.fullmatch(login))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("refusing GitHub API redirect")


def github_fetch(path, token=None):
    """GET only: pinned, public GitHub REST path. No redirect or non-GitHub host."""
    if not re.fullmatch(r"/repos/humanaios-ui/(operations|humanaios|lasting-light-ai)/(pulls/\d+|pulls/\d+/reviews|commits/[a-f0-9]{40}|commits/[a-f0-9]{40}/check-runs|issues/\d+|issues/\d+/comments)", path):
        raise ValueError("GitHub API path not allowlisted")
    url = "https://api.github.com" + path + ("?per_page=100" if path.endswith("/reviews") or path.endswith("/comments") or path.endswith("/check-runs") else "")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "HumanAIOS-Attractor-E1-ReadOnly", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(url, headers=headers, method="GET")
    try:
        with build_opener(HTTPSHandler(), HTTPHandler(), NoRedirect()).open(req, timeout=12) as response:
            raw = response.read(MAX_JSON + 1)
            if len(raw) > MAX_JSON:
                raise ValueError("response too large")
            payload = json.loads(raw)
            return payload
    except (HTTPError, URLError) as exc:
        raise ValueError(f"GitHub API read failed: {getattr(exc,'code','NETWORK_FAILURE')} at allowed endpoint") from None


def gather_live(repo, prs, issue, token=None):
    prefix = "/repos/" + repo
    snapshot = {"source_mode": "LIVE_GITHUB_API", "repo": repo, "pulls": [], "outcome_issue": None}
    for n in prs:
        pr = github_fetch(prefix + f"/pulls/{n}", token)
        head = sha40(pr.get("head", {}).get("sha"))
        obj = {
            "pr": pr,
            "commit": github_fetch(prefix + f"/commits/{head}", token),
            "reviews": github_fetch(prefix + f"/pulls/{n}/reviews", token),
            "checks": github_fetch(prefix + f"/commits/{head}/check-runs", token),
        }
        snapshot["pulls"].append(obj)
    if issue is not None:
        snapshot["outcome_issue"] = {
            "issue": github_fetch(prefix + f"/issues/{issue}", token),
            "comments": github_fetch(prefix + f"/issues/{issue}/comments", token),
        }
    return snapshot


def project_pulls(snapshot, repo, max_prs=8):
    entries = snapshot.get("pulls")
    if not isinstance(entries, list) or len(entries) > max_prs:
        raise ValueError("invalid bounded pull requests")
    observed = []
    gates = Counter()
    reviewer_attestations = Counter()
    pinned_heads = set()
    for group in entries:
        if not isinstance(group, dict) or set(group) != {"pr", "commit", "reviews", "checks"}:
            raise ValueError("invalid PR evidence group")
        pr, commit, reviews, checks = group["pr"], group["commit"], group["reviews"], group["checks"]
        number = pr.get("number")
        if type(number) is not int or number <= 0:
            raise ValueError("invalid PR number")
        head = sha40(pr.get("head", {}).get("sha"))
        if commit.get("sha") != head:
            raise ValueError("source-pinned commit mismatch")
        if pr.get("base", {}).get("repo", {}).get("full_name", repo) != repo or pr.get("head", {}).get("repo", {}).get("full_name", repo) != repo:
            raise ValueError("PR belongs to another repository")
        pinned_heads.add(head)
        if not isinstance(reviews, list) or len(reviews) > 100:
            raise ValueError("unbounded reviews")
        if not isinstance(checks, dict) or not isinstance(checks.get("check_runs"), list) or checks.get("total_count", 0) > 100:
            raise ValueError("unbounded check runs; page incomplete")
        if len(checks["check_runs"]) != checks.get("total_count"):
            raise ValueError("check run pagination required; refusing truncated observation")
        if not is_human(pr.get("user")):
            author = pr.get("user", {}).get("login", "UNIDENTIFIED")
        else:
            author = pr["user"]["login"]
        independent_approvals, review_count = 0, 0
        for review in reviews:
            if review.get("commit_id") != head or not review.get("submitted_at"):
                continue
            utc(review["submitted_at"])
            review_count += 1
            if (review.get("state") == "APPROVED" and is_human(review.get("user")) and
                review["user"]["login"] != author):
                independent_approvals += 1
            if review.get("state") in ("APPROVED", "CHANGES_REQUESTED", "COMMENTED"):
                reviewer_attestations[review["state"]] += 1
        per_pr_checks = Counter()
        for check in checks["check_runs"]:
            if check.get("head_sha") != head:
                raise ValueError("check run not pinned to PR head")
            name = str(check.get("name", "")).strip()
            if not name or len(name) > 160:
                raise ValueError("invalid check name")
            conclusion = (check.get("conclusion") or "UNKNOWN").upper()
            if conclusion not in CODES:
                conclusion = "UNKNOWN"
            per_pr_checks[conclusion] += 1
            gates[name] += 1
        if pr.get("merged_at"):
            utc(pr["merged_at"])
        observed.append({
            "pr_number": number, "head_sha": head, "source_ref": f"https://github.com/{repo}/pull/{number}",
            "pr_author": author, "pr_state": pr.get("state"), "merged_at": pr.get("merged_at"),
            "source_commit_observed": True,
            "review_events_on_exact_head": review_count,
            "distinct_actor_approval_events_on_head": independent_approvals,
            "check_count": len(checks["check_runs"]),
            "check_conclusions": dict(sorted(per_pr_checks.items())),
            "authority_effect": "NONE",
        })
    if len({r["pr_number"] for r in observed}) != len(observed):
        raise ValueError("duplicate PR")
    return sorted(observed, key=lambda x: x["pr_number"]), pinned_heads, gates, reviewer_attestations


def project_outcomes(raw, repo, pinned_heads):
    if raw is None:
        return {"state": "NOT_MEASURED", "issue_ref": None, "claims": [], "reviewed": [], "unreviewed_count": None}
    if not isinstance(raw, dict) or set(raw) != {"issue", "comments"}:
        raise ValueError("invalid issue surface")
    issue, comments = raw["issue"], raw["comments"]
    if type(issue.get("number")) is not int or not isinstance(comments, list) or len(comments) > 100:
        raise ValueError("unbounded GitHub outcome-issue comments")
    # A 100-element page might be incomplete. We refuse rather than silently
    # claiming no review beyond a truncated API page.
    if len(comments) == 100:
        raise ValueError("outcome issue may be paginated")
    claims, reviews, rejected = {}, [], 0
    for c in comments:
        comment_id = c.get("id")
        if type(comment_id) is not int or comment_id <= 0 or not is_human(c.get("user")):
            continue
        packet = parse_packet(c.get("body"), "claim")
        review = parse_packet(c.get("body"), "review")
        if packet is not None:
            try:
                validate_claim(packet, repo)
                if packet["source_commit"] not in pinned_heads:
                    raise ValueError("claim source commit not in audited PRs")
                claims[comment_id] = {
                    "packet": packet, "author": c["user"]["login"], "sha256": checksum(packet),
                }
            except (ValueError, TypeError, KeyError):
                rejected += 1
        elif review is not None:
            try:
                validate_review(review, repo)
                reviews.append({"packet": review, "author": c["user"]["login"], "comment_id": comment_id})
            except (ValueError, TypeError, KeyError):
                rejected += 1
    public_claims, supported = [], []
    for cid, obj in sorted(claims.items()):
        claim = obj["packet"]
        matching = [r for r in reviews if
                    r["packet"]["claim_comment_id"] == cid and
                    r["packet"]["claim_sha256"] == obj["sha256"] and
                    r["packet"]["source_commit"] == claim["source_commit"] and
                    r["author"] != obj["author"]]
        # Separate *GitHub* identities are recorded; not proof that source
        # contents or account independence were authenticated out-of-band.
        verdicts = {r["packet"]["verdict"] for r in matching}
        status = ("DISPUTED" if "REJECTS" in verdicts or "INDETERMINATE" in verdicts else
                  "SEPARATE_REVIEW_ATTESTED" if "SUPPORTS" in verdicts else
                  "NO_INDEPENDENT_REVIEW")
        minimal = {
            "claim_comment_id": cid, "claim_sha256": obj["sha256"],
            "source_commit": claim["source_commit"],
            "objective_id": claim["objective_id"], "process_id": claim["process_id"],
            "event_type": claim["event_type"], "review_status": status,
            "independent_review_comments": sorted(r["comment_id"] for r in matching),
            "evidence_ref": claim["evidence_ref"],
            "proven_acquisition_or_benefit": False,
        }
        public_claims.append(minimal)
        if status == "SEPARATE_REVIEW_ATTESTED":
            supported.append(minimal)
    return {
        "state": "NO_REVIEW_PACKETS_OBSERVED" if not claims else "GITHUB_IDENTITY_SEPARATE_REVIEW_ONLY",
        "issue_ref": f"https://github.com/{repo}/issues/{issue['number']}",
        "claim_count": len(public_claims), "reviewed_count": len(supported),
        "rejected_packet_count": rejected,
        "claims": public_claims, "reviewed": supported,
        "unreviewed_count": len(public_claims) - len(supported),
        "caveat": "Two different GitHub account handles do not establish authenticated source evidence, beneficial impact, or reviewer independence beyond account distinction.",
    }


def analyze(snapshot, source_mode):
    repo = snapshot.get("repo")
    if repo not in REPO_ALLOWLIST:
        raise ValueError("repository outside authorized read scope")
    if source_mode not in ("LIVE_GITHUB_API", "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED"):
        raise ValueError("invalid source mode")
    entries, pinned, checks, reviews = project_pulls(snapshot, repo)
    outcomes = project_outcomes(snapshot.get("outcome_issue"), repo, pinned)
    return {
        "schema": SCHEMA, "authority_effect": "NONE", "execution": "DISABLED",
        "catalog_mutation": False, "verified_human_benefits": "NOT_ESTABLISHED",
        "source_mode": source_mode, "repository": repo,
        "source_pin_policy": "GitHub PR head SHA == fetched commit SHA; checks and reviews bound to exact head",
        "repository_activity": {
            "observed_pr_count": len(entries), "prs": entries,
            "repeated_check_surfaces": [
                {"check_name": k, "observations_across_sample": v}
                for k, v in sorted(checks.items(), key=lambda kv: (-kv[1], kv[0])) if v > 1
            ],
            "review_event_states": dict(sorted(reviews.items())),
            "caveat": "Repeated check names across PRs are not agent loop visits, causal influence, or verified deployment.",
        },
        "resource_outcome_reviews": outcomes,
    }


def render_html(report):
    if report.get("authority_effect") != "NONE":
        raise ValueError("authority escalation rejected")
    s = lambda x: escape(str(x), quote=True)
    rows = []
    for pr in report["repository_activity"]["prs"]:
        rows.append(f"<tr><td>#{s(pr['pr_number'])}</td><td><code>{s(pr['head_sha'][:12])}</code></td>"
                    f"<td>{s(pr['pr_state'])}</td><td>{s(pr['check_count'])}</td>"
                    f"<td>{s(pr['distinct_actor_approval_events_on_head'])}</td></tr>")
    loops = "".join(f"<li>{s(x['check_name'])}: {s(x['observations_across_sample'])} PR-check observations</li>"
                    for x in report["repository_activity"]["repeated_check_surfaces"])
    outcomes = report["resource_outcome_reviews"]
    claims = "".join(f"<li>{s(x['event_type'])} · {s(x['review_status'])} · "
                    f"claim #{s(x['claim_comment_id'])}</li>" for x in outcomes["claims"])
    return ("""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>HumanAIOS E1 · Evidence Bridge</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font:16px/1.55 system-ui;background:#102222;color:#e4ede8;max-width:950px;margin:50px auto;padding:20px}
h1{color:#eed7a0}section{border:1px solid #34544e;padding:20px;margin:20px 0;border-radius:12px}
small,p{color:#b2c8bb}table{width:100%;border-collapse:collapse}th,td{padding:9px;border-bottom:1px solid #34544e;text-align:left}
code{overflow-wrap:anywhere}strong{color:#eed7a0}</style></head><body>"""
            f"<h1>Attractor Observatory · E1</h1><p>Repo: {s(report['repository'])} · "
            f"Source: {s(report['source_mode'])}</p><p><strong>READ ONLY · AUTHORITY NONE · "
            "INDEPENDENT OUTCOME PROOF NOT ESTABLISHED</strong></p>"
            "<section><h2>Source-pinned repository activity</h2>"
            "<table><thead><tr><th>PR</th><th>Head SHA</th><th>State</th><th>Checks</th><th>Independent approvals*</th></tr></thead>"
            "<tbody>" + "".join(rows) + "</tbody></table><small>*Different PR-review author accounts only.</small></section>"
            "<section><h2>Repeated check surfaces</h2><ul>" + (loops or "<li>None in sample</li>") + "</ul>"
            "<p>Repeated checks are not repeated agent routing paths.</p></section>"
            f"<section><h2>External outcome review: {s(outcomes['state'])}</h2>"
            f"<p>Reviewed claims: {s(outcomes.get('reviewed_count','NOT MEASURED'))}. "
            "Claims are not independently authenticated benefits.</p><ul>"
            + (claims or "<li>No parseable, linked review packets.</li>") + "</ul></section>"
            "</body></html>")


def run_smoke_test():
    """Synthetic, offline, no token and no network calls."""
    sha = "a" * 40
    fixture = {
        "repo": "humanaios-ui/operations",
        "pulls": [{"pr": {"number": 1, "head": {"sha": sha}, "state": "open",
                         "user": {"login": "author", "type": "User"}},
                   "commit": {"sha": sha}, "reviews": [],
                   "checks": {"total_count": 1, "check_runs": [{"head_sha": sha, "name": "CI",
                                                               "conclusion": "success"}]}}],
        "outcome_issue": None,
    }
    result = analyze(fixture, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
    assert result["repository_activity"]["observed_pr_count"] == 1
    assert result["resource_outcome_reviews"]["state"] == "NOT_MEASURED"
    assert result["verified_human_benefits"] == "NOT_ESTABLISHED"
    assert "<script" not in render_html(result)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only GitHub activity and outcome attestations")
    parser.add_argument("--repo", default="humanaios-ui/operations")
    parser.add_argument("--prs", default="822,835,841", help="at most 8 PR numbers")
    parser.add_argument("--outcome-issue", type=int, help="optional review-packet issue")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--live", action="store_true", help="perform allowlisted GitHub GET requests")
    source.add_argument("--snapshot", help="offline, unverified captured GitHub-shaped JSON")
    parser.add_argument("--output", help="report JSON path (otherwise stdout)")
    parser.add_argument("--html", help="static standalone HTML output path")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.smoke_test:
            return run_smoke_test()
        if args.repo not in REPO_ALLOWLIST:
            raise ValueError("repository not on allowlist")
        prs = [int(s.strip()) for s in args.prs.split(",") if s.strip()]
        if not prs or len(prs) > 8 or any(p <= 0 for p in prs) or len(set(prs)) != len(prs):
            raise ValueError("PR set must contain 1–8 distinct positive IDs")
        if args.live == bool(args.snapshot):
            raise ValueError("choose exactly one of --live or --snapshot")
        if args.live:
            snapshot = gather_live(args.repo, prs, args.outcome_issue,
                                   os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN"))
            source_mode = "LIVE_GITHUB_API"
        else:
            path = Path(args.snapshot)
            if path.stat().st_size > MAX_JSON:
                raise ValueError("oversized snapshot")
            snapshot = json.loads(path.read_text(encoding="utf-8"))
            if snapshot.get("repo") != args.repo:
                raise ValueError("snapshot repository mismatch")
            source_mode = "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED"
        report = analyze(snapshot, source_mode)
        serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output:
            Path(args.output).write_text(serialized, encoding="utf-8")
        else:
            sys.stdout.write(serialized)
        if args.html:
            Path(args.html).write_text(render_html(report), encoding="utf-8")
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, RecursionError) as exc:
        # No exception payloads from HTTP responses or raw user packets are printed.
        parser.exit(2, f"E1 stopped: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

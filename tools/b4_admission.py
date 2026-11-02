#!/usr/bin/env python3
"""B4 controlled-operation admission: verify a GitHub-authenticated approval envelope.

The GitHub API collector (trusted CI) supplies identity metadata. Never trust
identity fields from a migration manifest or a file in the proposed PR.
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone

SHA = re.compile(r"^[a-f0-9]{64}$")
COMMIT = re.compile(r"^[a-f0-9]{40}$")
SCHEMA = "humanaios.b4-admission.v1"

def require(ok, message):
    if not ok:
        raise ValueError(message)

def verify(request, evidence, trusted_actors, now=None):
    """Return scoped admission receipt or raise ValueError (fail closed)."""
    now = now or datetime.now(timezone.utc)
    require(request.get("operation") == "B4_CONTENT_MIGRATION", "wrong operation")
    require(request.get("issue") == 759, "wrong issue")
    require(isinstance(request.get("seat"), str) and bool(request["seat"].strip()), "missing seat")
    require(bool(SHA.fullmatch(str(request.get("plan_sha256", "")))), "invalid plan SHA")
    for key in ("source_commit", "target_commit"):
        require(bool(COMMIT.fullmatch(str(request.get(key, "")))), "invalid " + key)
    require(isinstance(request.get("operation_id"), str) and bool(re.fullmatch(r"B4-[A-Za-z0-9_-]{8,80}", request["operation_id"])), "invalid operation ID")
    require(evidence.get("source") == "github_api", "untrusted evidence source")
    require(evidence.get("issue") == 759, "evidence issue mismatch")
    require(evidence.get("issue_state") == "open", "issue not open")
    require(evidence.get("body_state") == "ADMISSION_REQUESTED", "issue admission state missing")
    require(evidence.get("state_projection_verified") is True, "coordinator state not verified")
    require(evidence.get("issue_admitted") is True, "no issue admission in coordinator projection")
    approvals = evidence.get("comments")
    require(isinstance(approvals, list), "missing comments")
    matches = []
    for comment in approvals:
        if not isinstance(comment, dict) or comment.get("actor") not in trusted_actors:
            continue
        if comment.get("author_association") not in ("OWNER", "MEMBER", "COLLABORATOR"):
            continue
        try:
            payload = json.loads(comment.get("body", ""))
        except (ValueError, TypeError):
            continue
        if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
            continue
        if any(payload.get(k) != request.get(k) for k in (
            "operation", "issue", "seat", "plan_sha256",
            "source_commit", "target_commit", "operation_id"
        )):
            continue
        if payload.get("decision") != "APPROVE":
            continue
        try:
            expiry = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if expiry.tzinfo is None or expiry <= now:
            continue
        matches.append((comment, expiry))
    require(len(matches) == 1, "expected exactly one authenticated, unexpired matching approval")
    consumed = evidence.get("consumed_operation_ids")
    require(isinstance(consumed, list), "missing replay ledger")
    require(request["operation_id"] not in consumed, "operation ID already consumed")
    comment, expiry = matches[0]
    return {
        "schema": "humanaios.b4-verified-admission.v1",
        "authority_effect": "SCOPED_CONTENT_COPY_ONLY",
        "merge_authority": False,
        "request": request,
        "approval_comment_id": comment["id"],
        "authenticated_actor": comment["actor"],
        "expires_at": expiry.isoformat(),
        "evidence_sha256": hashlib.sha256(json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--request", required=True)
    p.add_argument("--evidence", required=True)
    p.add_argument("--trusted-actor", action="append", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    try:
        request = json.load(open(args.request, encoding="utf-8"))
        evidence = json.load(open(args.evidence, encoding="utf-8"))
        receipt = verify(request, evidence, set(args.trusted_actor))
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(receipt, fh, indent=2, sort_keys=True)
            fh.write("\n")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("B4 DENIED: " + str(exc), file=sys.stderr)
        return 1
    print("B4 admission verified; NOT execution or merge authority")
    return 0

if __name__ == "__main__":
    sys.exit(main())

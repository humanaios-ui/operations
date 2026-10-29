"""Authenticated, read-only Oracle -> INTENT-OS GitHub challenge projector (Z1 E1).

Fixed public GitHub evidence subject; no general search, mutation, execution,
user-provided URLs, persistence or authority promotion. A GitHub API readback
authenticates transport/account access, not factual correctness or actor identity.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
from hashlib import sha1, sha256
from http import HTTPStatus
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

REPOSITORY = "humanaios-ui/operations"
COMMIT_SHA = "77e872c6ecde828bf965efc3fa82a2ac3cfb4b4b"
DOCUMENT = "docs/VERIFIED_RESOURCE_INTENT_E0.md"
BLOB_SHA = "40d3f11e4bc8b9b89d49ae1bc308556f1d389df8"
REVIEW_ID = 5697326401
COMMENT_ID = 4412042009
COMMITMENT_ID = 6496931195
ISSUE = 1065
CLAIM = "P1 original statement and its SHA remain unchanged; P2 challenges it; P3 records the corrected statement."
CLAIM_SHA256 = sha256(CLAIM.encode("utf-8")).hexdigest()
CHALLENGE_SHA256 = "f4c806dc188a8889c94dec11b2d14181b01bed0192055090e439a56558733026"
REVIEWER = "copilot-pull-request-reviewer[bot]"
COMMENT_AUTHOR = "Copilot"
P3 = ("The source-pinned P1→P2→P3 hash chain demonstrates internal consistency, "
      "not historical immutability. Original P1 and P2 are separately retrievable. "
      "Historical immutability remains UNVERIFIED until an independently retained "
      "pre-challenge P1 commitment passes readback. This is not a code repair.")
BASE = "https://api.github.com/repos/" + REPOSITORY
MAX_JSON = 262144
SCHEMA = "humanaios.oracle_review_telemetry.v0.1"
LEDGER_PREFIX = "HUMANAIOS_P1_COMMITMENT_V0_1\n"


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
                  .encode("utf-8")).hexdigest()


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Missing server timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.utcoffset() is None:
        raise ValueError("Timezone-free server timestamp")
    return dt.astimezone(timezone.utc)


class OracleReadbackError(ValueError):
    """A required authenticated source readback failed or conflicted."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AuthenticatedGitHubReader:
    """Only fixed GitHub REST GET paths; token never enters output or browser."""
    def __init__(self, token=None):
        self._token = token if token is not None else os.environ.get("HUMANAIOS_ORACLE_GITHUB_READ_TOKEN", "")
        if not isinstance(self._token, str) or len(self._token) < 20:
            raise OracleReadbackError("Operator-supplied read-only GitHub token unavailable")
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())

    def get(self, path):
        allowed = {
            f"/commits/{COMMIT_SHA}",
            f"/contents/{DOCUMENT}?ref={COMMIT_SHA}",
            f"/pulls/1064/reviews/{REVIEW_ID}",
            f"/pulls/comments/{COMMENT_ID}",
            f"/issues/comments/{COMMITMENT_ID}",
        }
        if path not in allowed:
            raise OracleReadbackError("Unapproved GitHub REST path")
        req = Request(BASE + path, method="GET", headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + self._token,
            "User-Agent": "HumanAIOS-Oracle-Readonly-E1",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        try:
            with self._opener.open(req, timeout=7) as response:
                if response.status != 200:
                    raise OracleReadbackError("Unexpected GitHub status")
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_JSON:
                    raise OracleReadbackError("Oversized GitHub response")
                body = response.read(MAX_JSON + 1)
                if len(body) > MAX_JSON:
                    raise OracleReadbackError("Oversized GitHub response")
                if "json" not in response.headers.get("Content-Type", ""):
                    raise OracleReadbackError("GitHub did not return JSON")
                data = json.loads(body.decode("utf-8"))
                if not isinstance(data, dict):
                    raise OracleReadbackError("Unexpected GitHub response")
                return data
        except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError) as exc:
            raise OracleReadbackError("Authenticated GitHub readback unavailable") from exc


def source_readback(reader):
    """Read all five independently addressable server objects; no mutation."""
    return {
        "commit": reader.get(f"/commits/{COMMIT_SHA}"),
        "document": reader.get(f"/contents/{DOCUMENT}?ref={COMMIT_SHA}"),
        "review": reader.get(f"/pulls/1064/reviews/{REVIEW_ID}"),
        "comment": reader.get(f"/pulls/comments/{COMMENT_ID}"),
        "commitment": reader.get(f"/issues/comments/{COMMITMENT_ID}"),
    }


def _commitment(raw, p1_time, p2_time):
    if not isinstance(raw, dict) or raw.get("id") != COMMITMENT_ID:
        raise OracleReadbackError("P1 ledger reference mismatch")
    body = raw.get("body")
    if not isinstance(body, str) or not body.startswith(LEDGER_PREFIX):
        raise OracleReadbackError("P1 ledger is missing its typed record")
    try:
        # First JSON line is the typed commitment; later prose is advisory only.
        data = json.loads(body[len(LEDGER_PREFIX):].splitlines()[0])
    except (ValueError, IndexError) as exc:
        raise OracleReadbackError("Invalid P1 ledger record") from exc
    required = {
        "schema": "humanaios.p1_commitment.v0.1",
        "subject": f"{REPOSITORY}#1064",
        "phase": "P1",
        "original_commit_sha": COMMIT_SHA,
        "original_blob_sha": BLOB_SHA,
        "doc_path": DOCUMENT,
        "statement_sha256": CLAIM_SHA256,
        "authority_effect": "NONE",
        "execution": "DISABLED",
    }
    if not isinstance(data, dict) or data != required:
        raise OracleReadbackError("P1 commitment does not match source pins")
    if raw.get("user", {}).get("login") != "humanaios-ui":
        raise OracleReadbackError("Unrecognized ledger author")
    created = _timestamp(raw.get("created_at"))
    updated = _timestamp(raw.get("updated_at"))
    if updated != created:
        return "EDITED_SERVER_LEDGER_NOT_A_PRIOR_COMMITMENT", created
    if created < p1_time:
        raise OracleReadbackError("Commitment predates original source commit")
    if created >= p2_time:
        return "RETROSPECTIVE_BACKFILL_NOT_PRECHALLENGE", created
    return "PRECHALLENGE_GITHUB_RETAINED_EDITABLE_NOT_INDEPENDENT_CONTROLLER", created


def project(readback):
    """Deterministic fail-closed Oracle graph+telemetry over authentic API objects."""
    if not isinstance(readback, dict) or set(readback) != {
        "commit", "document", "review", "comment", "commitment"
    }:
        raise OracleReadbackError("Missing one or more independent API reads")
    c, d, r, n = (readback[k] for k in ("commit", "document", "review", "comment"))
    if c.get("sha") != COMMIT_SHA:
        raise OracleReadbackError("Git commit mismatch")
    author = c.get("commit", {}).get("author", {})
    p1_time = _timestamp(author.get("date"))
    if c.get("author") and c["author"].get("login") != "humanaios-ui":
        raise OracleReadbackError("Unexpected original P1 author")
    if d.get("sha") != BLOB_SHA or d.get("path") != DOCUMENT or d.get("encoding") != "base64":
        raise OracleReadbackError("GitHub source file identity mismatch")
    try:
        raw = base64.b64decode(d["content"], validate=False)
        text = raw.decode("utf-8")
    except (KeyError, ValueError, UnicodeError) as exc:
        raise OracleReadbackError("P1 source unreadable") from exc
    actual_blob = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if actual_blob != BLOB_SHA or CLAIM not in text or sha256(CLAIM.encode()).hexdigest() != CLAIM_SHA256:
        raise OracleReadbackError("P1 blob or original statement tampered")
    if r.get("id") != REVIEW_ID or r.get("commit_id") != COMMIT_SHA:
        raise OracleReadbackError("Reviewer did not review original P1 commit")
    if r.get("user", {}).get("login") != REVIEWER:
        raise OracleReadbackError("Unexpected GitHub reviewer account")
    p2_time = _timestamp(r.get("submitted_at"))
    if p2_time <= p1_time:
        raise OracleReadbackError("P2 must follow P1")
    if n.get("id") != COMMENT_ID or n.get("pull_request_review_id") != REVIEW_ID:
        raise OracleReadbackError("Reviewer comment does not belong to review")
    if n.get("commit_id") != COMMIT_SHA or n.get("original_commit_id") != COMMIT_SHA:
        raise OracleReadbackError("Reviewer comment at another revision")
    if n.get("user", {}).get("login") != COMMENT_AUTHOR or n.get("path") != (
        "humanaios-funding-pipeline/resource-miner/resource_miner/verified_intent.py"
    ):
        raise OracleReadbackError("Reviewer comment identity mismatch")
    challenge = n.get("body")
    if not isinstance(challenge, str) or sha256(challenge.encode()).hexdigest() != CHALLENGE_SHA256:
        raise OracleReadbackError("Reviewer challenge changed since E0 capture")
    if _timestamp(n.get("created_at")) > p2_time:
        raise OracleReadbackError("Reviewer comment created after review submission")
    commitment_state, ledger_time = _commitment(readback["commitment"], p1_time, p2_time)
    # GitHub source Oracle observation -> Evidence Domain Oracle graph delta ->
    # Global Oracle advisory telemetry -> INTENT-OS read-only human projection.
    obs = {
        "observation_id": "OBS-" + _digest([COMMIT_SHA, REVIEW_ID, COMMENT_ID])[:20],
        "oracle_id": "ORACLE-SOURCE-GITHUB", "source_substrate": "github",
        "source_url": f"https://github.com/{REPOSITORY}/pull/1064#discussion_r{COMMENT_ID}",
        "source_commit_sha": COMMIT_SHA,
        "as_of": r["submitted_at"], "recorded_at": n["created_at"],
        "statement": "Copilot reviewer-account challenge was attached to the exact P1 source commit.",
        "source_verification": "AUTHENTICATED_GITHUB_REST_READBACK_NOT_CLAIM_PROOF",
    }
    delta = {
        "oracle_id": "ORACLE-DOMAIN-EVIDENCE",
        "operation": "CONTRADICT",
        "from": f"github-review-comment:{COMMENT_ID}",
        "to": "P1_HISTORICAL_IMMUTABILITY",
        "relation": "CHALLENGES",
        "provenance": [obs["observation_id"], f"git:{COMMIT_SHA}", f"github-review:{REVIEW_ID}"],
        "components_before": 2,
        "components_after": 1,
        "canonical": False,
    }
    alert = {
        "rule": "INDEPENDENT_ACCOUNT_REVIEW_BRIDGE",
        "state": "CHALLENGED_UNRESOLVED",
        "event_id": "GTA-" + _digest([obs["observation_id"], delta])[:20].upper(),
        "trigger": obs["source_url"],
        "interpretation": "A distinct GitHub reviewer account challenged an earlier P1 claim.",
        "claim_correctness": "NOT_INDEPENDENTLY_ESTABLISHED",
        "p1_commitment_state": commitment_state,
    }
    projection = {
        "schema": SCHEMA, "source_oracle": obs, "evidence_graph_delta": delta,
        "telemetry": {"alerts": [alert], "alert_count": 1},
        "p1_commitment": {
            "source": f"https://github.com/{REPOSITORY}/issues/{ISSUE}#issuecomment-{COMMITMENT_ID}",
            "recorded_at": ledger_time.isoformat(), "state": commitment_state,
            "store": "GITHUB_ISSUE_SEPARATE_FROM_PR_EDITABLE",
            "historical_immutability_proven": False,
        },
        "phases": {
            "P1": {"commit": COMMIT_SHA, "blob": BLOB_SHA, "statement": CLAIM,
                   "source": f"https://github.com/{REPOSITORY}/blob/{COMMIT_SHA}/{DOCUMENT}"},
            "P2": {"review_id": REVIEW_ID, "comment_id": COMMENT_ID,
                   "reviewer_account": REVIEWER, "independence": "SEPARATE_ACCOUNT_ONLY",
                   "source": obs["source_url"]},
            "P3": {"interpretation": P3, "state": "CORRECTION_PROPOSED_NOT_RATIFIED"},
        },
        "intent_os": {
            "view": "ORACLE_REVIEW_TELEMETRY", "state": "REVIEW_REQUIRED",
            "human_visible_conclusion": P3,
            "next_action": "Pre-register a P1 source digest in independently controlled retention BEFORE subsequent independent P2 review; rerun tamper-negative and exact-head CI tests.",
            "resource_availability": "NOT_ASSESSED", "external_execution": "DISABLED",
        },
        "authority_effect": "NONE", "can_authorize": False,
        "advisory_only": True, "execution": "DISABLED",
        "limitations": "Authenticated GitHub API transport and specific repository objects; no cryptographic reviewer-model independence, no immutable external ledger, no live production deployment.",
    }
    projection["receipt_sha256"] = _digest(projection)
    return projection


def read_cycle(token=None, *, reader=None):
    return project(source_readback(reader or AuthenticatedGitHubReader(token)))


HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HumanAIOS · Oracle Evidence Review</title>
<style>body{font:16px/1.5 system-ui;margin:0;background:#0b1423;color:#eaf2fc}
main{max-width:900px;padding:28px;margin:auto}section{background:#13243a;border:1px solid #314764;
padding:19px;border-radius:12px;margin:15px 0;white-space:pre-wrap;overflow-wrap:anywhere}
a{color:#87d6fa}strong{color:#e5b66e}h1{line-height:1.2}small{color:#a6b5cb}</style>
</head><body><main><a href="/intent-os">← INTENT-OS</a>
<h1>Oracle graph telemetry · independent challenge</h1>
<p><strong>Read-only. No admission, application, verified opportunity, or authority.</strong></p>
<section id="status" role="status" aria-live="polite">Requesting authenticated GitHub source readback…</section>
<section><h2>P1 · Original source</h2><div id="p1">Not read yet</div></section>
<section><h2>P2 · Independent GitHub reviewer account</h2><div id="p2">Not read yet</div></section>
<section><h2>Graph delta and telemetry</h2><div id="alert">Not read yet</div></section>
<section><h2>P3 · Corrected interpretation</h2><div id="p3">Not read yet</div></section>
<section><h2>P1 external retention status</h2><div id="anchor">Not read yet</div></section>
<small>GitHub account separation is not authenticated model independence. Issue comments are editable.</small>
<script>
(async()=>{
const put=(id,text)=>document.getElementById(id).textContent=text;
try{
 const res=await fetch("/api/oracle/review-telemetry",{cache:"no-store",credentials:"same-origin"});
 if(!res.ok)throw Error("Source readback unavailable ("+res.status+").");
 const a=await res.json();
 put("status",a.intent_os.state+" · "+a.telemetry.alert_count+" alert · authority "+a.authority_effect);
 put("p1",a.phases.P1.statement+"\nCommit: "+a.phases.P1.commit+"\n"+a.phases.P1.source);
 put("p2",a.phases.P2.reviewer_account+"\n"+a.phases.P2.source);
 put("alert",a.evidence_graph_delta.relation+": "+a.evidence_graph_delta.from+" → "+a.evidence_graph_delta.to+
 "\nComponents: "+a.evidence_graph_delta.components_before+" → "+a.evidence_graph_delta.components_after+
 "\nEvent: "+a.telemetry.alerts[0].event_id);
 put("p3",a.phases.P3.interpretation);
 put("anchor",a.p1_commitment.state+"\n"+a.p1_commitment.source);
}catch(e){put("status","UNVERIFIED · "+e.message); }
})();
</script></main></body></html>
"""

"""Bounded, read-only source-reconciliation/challenge overlay for internal Resource Miner.

This deliberately does not authenticate a GitHub API read or perform one. Its independent
observation is a separately fetched, pinned source record supplied by a reviewer. The
result never elevates claims to human authorization or proven agent behavior.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime
from urllib.parse import urlsplit

SCHEMA = "humanaios.internal-broker-independent-readback.v0.1"
OUTPUT_SCHEMA = "humanaios.internal-broker-qualification.v0.1"
SOURCE_SCHEMA = "humanaios.github-pr-source-observation.v0.1"
FULL_SHA = re.compile(r"[a-f0-9]{40}\Z")
CLAIM_ID = re.compile(r"[A-Z][A-Z0-9_]{2,80}\Z")
PR_URL = re.compile(r"https://github\.com/humanaios-ui/(operations|humanaios|lasting-light-ai)/pull/([1-9][0-9]*)\Z")
BLOB_URL = re.compile(r"https://github\.com/humanaios-ui/(operations|humanaios|lasting-light-ai)/blob/([a-f0-9]{40})/([A-Za-z0-9._/-]{1,220})\Z")
RUN_URL = re.compile(r"https://github\.com/humanaios-ui/(operations|humanaios|lasting-light-ai)/actions/runs/([1-9][0-9]*)\Z")


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def valid_time(value: str) -> bool:
    try:
        return type(value) is str and datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None
    except (ValueError, AttributeError):
        return False


def strict_keys(row: object, expected: set[str]):
    if type(row) is not dict or set(row) != expected:
        raise ValueError("missing/extra observation fields")


def qualify(snapshot: dict, bundle: dict, readback: dict, challenges: list[dict]) -> dict:
    """Cross-check a resource record with independent source metadata and record disputes.

    The correction is an overlay; no writes, source-object changes or I/O occur.
    """
    strict_keys(readback, {"schema", "observed_at", "reader", "pr", "blob", "checks", "review_threads"})
    if readback["schema"] != SOURCE_SCHEMA or readback["reader"] != "GITHUB_CONNECTOR_INDEPENDENT_READ":
        raise ValueError("readback provenance not declared")
    if not valid_time(readback["observed_at"]):
        raise ValueError("bad observation timestamp")
    if snapshot.get("schema") != "humanaios.internal-repository-snapshot.v0.1" or bundle.get("schema") != "humanaios.internal-resource-intelligence.v0.1":
        raise ValueError("wrong broker source/projection schema")
    # The readback is a response to a previously frozen snapshot. This is only
    # a claimed-timestamp consistency check, NOT a trusted clock/actor proof.
    if not valid_time(snapshot.get("as_of")):
        raise ValueError("snapshot lacks bounded observation timestamp")
    source_time = datetime.fromisoformat(snapshot["as_of"].replace("Z", "+00:00"))
    readback_time = datetime.fromisoformat(readback["observed_at"].replace("Z", "+00:00"))
    if readback_time < source_time:
        raise ValueError("readback predates frozen source snapshot")
    if bundle.get("authority_effect") != "NONE" or bundle.get("source_authentication") != "NOT_ESTABLISHED":
        raise ValueError("broker projection claims authority or authentication")
    strict_keys(readback["pr"], {"repository", "number", "source_url", "head_sha", "merge_commit_sha", "title", "merged", "state"})
    pr = readback["pr"]
    match = PR_URL.fullmatch(pr["source_url"]) if type(pr["source_url"]) is str else None
    if not match or pr["repository"] != "humanaios-ui/"+match.group(1) or type(pr["number"]) is not int or pr["number"] != int(match.group(2)):
        raise ValueError("PR source URL and identity disagree")
    if type(pr["head_sha"]) is not str or not FULL_SHA.fullmatch(pr["head_sha"]):
        raise ValueError("unpinned PR head")
    if type(pr["merge_commit_sha"]) is not str or not FULL_SHA.fullmatch(pr["merge_commit_sha"]):
        raise ValueError("unpinned merge commit")
    if type(pr["merged"]) is not bool or pr["state"] not in {"open", "closed"} or type(pr["title"]) is not str or not 0<len(pr["title"])<=180:
        raise ValueError("invalid PR metadata")
    ref = f"{pr['repository']}/PR#{pr['number']}"
    candidates = [r for r in bundle["resources"] if r.get("item_ref") == ref]
    items = [i for i in snapshot["items"] if i.get("repository")==pr["repository"] and i.get("kind")=="PR" and i.get("number")==pr["number"]]
    if len(candidates) != 1 or len(items) != 1:
        raise ValueError("source PR not uniquely present in broker")
    resource, item = candidates[0], items[0]
    for row in (item, resource):
        if row.get("head_sha") != pr["head_sha"]:
            raise ValueError("PR revision drift / forged readback")
    if item["source_url"] != pr["source_url"] or resource["source_url"] != pr["source_url"] or resource["canonical_url"] != pr["source_url"] or item["title"] != resource["title"]:
        raise ValueError("source identity/title does not match independent read")
    expected_state = "MERGED" if pr["merged"] else ("OPEN" if pr["state"] == "open" else "CLOSED")
    if item["state"] != expected_state or resource["item_state"] != expected_state:
        raise ValueError("state disagrees with independent GitHub read")
    if resource.get("authority_effect") != "NONE" or resource.get("source_authentication") != "NOT_ESTABLISHED" or resource.get("eligibility_status") != "UNASSESSED":
        raise ValueError("source candidate promoted itself")
    strict_keys(readback["blob"], {"path", "at_head_url", "git_blob_sha"})
    blob=readback["blob"]
    bm=BLOB_URL.fullmatch(blob["at_head_url"]) if type(blob["at_head_url"]) is str else None
    if (not bm or "humanaios-ui/"+bm.group(1)!=pr["repository"] or bm.group(2)!=pr["head_sha"] or bm.group(3)!=blob["path"] or
        type(blob["git_blob_sha"]) is not str or not FULL_SHA.fullmatch(blob["git_blob_sha"])):
        raise ValueError("source blob path/SHA cannot be matched")
    checks = readback["checks"]
    if type(checks) is not list or len(checks)>100:
        raise ValueError("unbounded check reads")
    runids=set()
    for row in checks:
        strict_keys(row, {"run_id", "name", "conclusion", "head_sha", "run_url"})
        rm=RUN_URL.fullmatch(row["run_url"]) if type(row["run_url"]) is str else None
        if not rm or "humanaios-ui/"+rm.group(1)!=pr["repository"] or type(row["run_id"]) is not int or row["run_id"]!=int(rm.group(2)) or row["run_id"] in runids:
            raise ValueError("check run URL/identity mismatch")
        if row["head_sha"] != pr["head_sha"] or row["conclusion"] not in {"success", "failure", "cancelled", "skipped", "timed_out", "neutral", "action_required", None} or type(row["name"]) is not str or not 0<len(row["name"])<=110:
            raise ValueError("check cannot be bound to exact head")
        runids.add(row["run_id"])
    strict_keys(readback["review_threads"], {"total", "unresolved", "source_url"})
    rev = readback["review_threads"]
    if type(rev["total"]) is not int or type(rev["unresolved"]) is not int or not (0<=rev["unresolved"]<=rev["total"]<=1000) or rev["source_url"] != pr["source_url"] + "/files":
        raise ValueError("invalid review thread source")
    if type(challenges) is not list or len(challenges)>50:
        raise ValueError("unbounded correction log")
    observed_claims={
      "SOURCE_RECORD_PRESENT":{"state":"CROSS_CHECKED_SOURCE_METADATA","basis":pr["source_url"]},
      "SOURCE_TITLE_EXACT":{"state":"SUPPORTED" if item["title"]==pr["title"] else "CONTRADICTED", "basis":pr["source_url"]},
      "CI_SUCCESS_IS_SECURITY_CLEARANCE":{"state":"NOT_ESTABLISHED","basis": "CI conclusion alone cannot establish review or safety"},
      "ALL_REVIEW_THREADS_RESOLVED":{"state":"CONTRADICTED" if rev["unresolved"] else "SUPPORTED_BY_THREAD_COUNT_ONLY","basis":rev["source_url"]},
      "AGENT_BEHAVIOR_INDEPENDENTLY_VALIDATED":{"state":"NOT_ESTABLISHED","basis":"No authenticated agent-runtime witness read in this trial"},
      "MERGE_AUTHORITY_VERIFIED":{"state":"NOT_ESTABLISHED","basis":"GitHub merged state is not Z2 approval proof"},
    }
    events=[]
    predecessor="0"*64
    previous_observation_time = readback_time
    for seq,c in enumerate(challenges,1):
        strict_keys(c,{"event_id","claim_id","action","reason_code","evidence_url","observed_at"})
        if not (type(c["event_id"]) is str and re.fullmatch(r"CHAL-[A-Za-z0-9-]{1,40}",c["event_id"]) and c["claim_id"] in observed_claims and c["action"] in {"CHALLENGE","CORRECT"} and type(c["reason_code"]) is str and CLAIM_ID.fullmatch(c["reason_code"]) and valid_time(c["observed_at"])):
            raise ValueError("malformed challenge")
        if c["evidence_url"] not in {pr["source_url"], rev["source_url"], blob["at_head_url"]} | {r["run_url"] for r in checks}:
            raise ValueError("challenge lacks source-linked evidence")
        event_time = datetime.fromisoformat(c["observed_at"].replace("Z", "+00:00"))
        if event_time < readback_time:
            raise ValueError("challenge predates separately observed source evidence")
        if event_time < previous_observation_time:
            raise ValueError("challenge sequence moves backwards in observation time")
        previous_observation_time = event_time
        event = {**c, "sequence":seq,"previous_event_sha256":predecessor,"authority_effect":"NONE","upstream_mutated":False}
        event["event_sha256"]=digest(event)
        predecessor=event["event_sha256"]
        events.append(event)
    if len({r["event_id"] for r in events}) != len(events):
        raise ValueError("duplicate challenge event")
    counts={}
    for row in checks:
        status=row["conclusion"] or "unverified"
        counts[status]=counts.get(status,0)+1
    return {"schema":OUTPUT_SCHEMA,"source_ref":ref,"source_url":pr["source_url"],"source_head_sha":pr["head_sha"],
       "source_merge_commit_sha":pr["merge_commit_sha"],"original_snapshot_title":item["title"],"independently_observed_title":pr["title"],"source_git_blob_sha":blob["git_blob_sha"],"source_blob_url":blob["at_head_url"],
       "source_snapshot_sha256":digest(snapshot),"broker_projection_sha256":digest(bundle),
       "independent_readback_sha256":digest(readback),"readback_status":"METADATA_MATCHES_SEPARATE_GITHUB_READ",
       "authentication":"NOT_CRYPTOGRAPHICALLY_ATTESTED","behavioral_validation":"NOT_ESTABLISHED",
       "source_mutated":False,"authority_effect":"NONE","may_admit":False,"may_merge":False,"may_execute":False,
       "ci_returned_conclusions":counts,"review_threads":rev,"derived_claims":observed_claims,
       "correction_events":events,"correction_chain_sha256":predecessor,
       "limitations":["Independent observations copied from GitHub connector; no signed provider attestation",
                      "No process/network isolation assertion", "GitHub account not authenticated model identity",
                      "Historical merge authorization not verified", "No real-agent P1/P2/P3 trial witnessed",
                      "Timestamp order checks compare supplied labels only; no trusted clock attestation"],
       "source_integrity_scope":"PR_ID_HEAD_AND_PINNED_BLOB_METADATA_ONLY"}


def board_html(qualification:dict)->str:
    if qualification["schema"]!=OUTPUT_SCHEMA or qualification["authority_effect"]!="NONE":
        raise ValueError("authority violation")
    e=lambda s:html.escape(str(s),quote=True)
    src=e(qualification["source_url"])
    claims="".join(f'<tr><td>{e(k)}</td><td>{e(v["state"])}</td><td>{e(v["basis"])}</td></tr>' for k,v in qualification["derived_claims"].items())
    challenges="".join(f'<tr><td>{e(v["event_id"])}</td><td>{e(v["claim_id"])}</td><td>{e(v["action"])}</td><td>{e(v["reason_code"])}</td></tr>' for v in qualification["correction_events"])
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\"><title>HumanAIOS Readback Qualification</title>"
      "<style>body{font:16px system-ui;max-width:980px;margin:auto;padding:28px;background:#10202b;color:#f0f5f8}table{width:100%;border-collapse:collapse}td,th{padding:9px;border:1px solid #4d6875;text-align:left}code{word-break:break-all}.hold{background:#69421f;padding:14px}h2{margin-top:34px}</style></head><body>"
      "<h1>Agent Quarantine · Independent Readback Trial</h1><div class='hold'>READ-ONLY · SOURCE METADATA CROSS-CHECKED · BEHAVIOR UNVERIFIED · AUTHORITY NONE</div>"
      f"<p>Source: {src} | Exact head <code>{e(qualification['source_head_sha'])}</code></p>"
      f"<p>Original broker title: {e(qualification['original_snapshot_title'])}<br>Independently observed GitHub title: {e(qualification['independently_observed_title'])}</p>"
      f"<p>Git blob <code>{e(qualification['source_git_blob_sha'])}</code> · merge commit <code>{e(qualification['source_merge_commit_sha'])}</code></p>"
      f"<p>Review threads unresolved: <strong>{qualification['review_threads']['unresolved']}</strong> · CI run conclusions: {e(qualification['ci_returned_conclusions'])}</p>"
      "<h2>Epistemic claims</h2><table><tr><th>Claim</th><th>Disposition</th><th>Basis</th></tr>"+claims+"</table>"
      "<h2>Independent challenge/correction overlay</h2><table><tr><th>Event</th><th>Target</th><th>Action</th><th>Reason</th></tr>"+challenges+"</table>"
      f"<h2>Provenance</h2><p>Original snapshot SHA-256: <code>{e(qualification['source_snapshot_sha256'])}</code></p>"
      f"<p>Derived broker SHA-256: <code>{e(qualification['broker_projection_sha256'])}</code></p>"
      f"<p>Separate source readback SHA-256: <code>{e(qualification['independent_readback_sha256'])}</code></p>"
      f"<p>Correction chain head: <code>{e(qualification['correction_chain_sha256'])}</code></p>"
      "<p>No underlying GitHub record, Coordinator admission, human decision, or agent runtime was modified by this projection.</p></body></html>")


def systems_report(q:dict)->str:
    ci=q['ci_returned_conclusions']; unresolved=q['review_threads']['unresolved']; s=q['source_ref']; h=q['source_head_sha']
    return (f"HumanAIOS Systems Intelligence — Independent Source Qualification\n\n"
      f"SOURCE: {s} @ {h}\n"
      f"OBSERVED: GitHub independent readback matches pinned PR identity and revision; title alias agreement = {q['derived_claims']['SOURCE_TITLE_EXACT']['state']}.\n"
      f"OBSERVED: Returned CI outcomes: {ci}. Unresolved review threads: {unresolved}.\n"
      f"CHALLENGE: CI success does not establish full security/review clearance.\n"
      f"CORRECTION: descriptive snapshot title remains preserved; independently observed title is '{q['independently_observed_title']}'.\n"
      f"CORRECTION: ALL_REVIEW_THREADS_RESOLVED = {q['derived_claims']['ALL_REVIEW_THREADS_RESOLVED']['state']}; underlying PR record unchanged.\n"
      f"UNRESOLVED: Agent identity, real behavioral calibration, human-origin approval, host protection and isolation.\n"
      f"DECISION: HOLD any promotion of this candidate to an authenticated agent capability until findings and authority independently clear.\n"
      f"ROI: NOT MEASURED; recommended effort = inspect 6 reviewer threads, negative-test malformed agent comments.\n"
      f"CALENDAR: No deadline or meeting inferred from this metadata. Human scheduling remains separate.\n"
      f"AUTHORITY_EFFECT: NONE. Derived observation only; source/commit unchanged.\n")
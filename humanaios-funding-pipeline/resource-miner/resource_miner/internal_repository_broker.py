"""Z1 read-only Resource Miner projection of explicit, bounded repository snapshots.

Does NOT fetch GitHub, read credentials, authenticate evidence, run agents,
change Coordinator admission, or turn Oracle synthesis into ground truth.
All caller-supplied data remains UNAUTHENTICATED_SOURCE_SNAPSHOT until
independently read back using a different trusted control surface.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime
from urllib.parse import urlsplit

from .mines import bind_opportunity, stable_mine_id
from .models import EvidenceRef, ResourceCandidate, ResourceMine

SCHEMA = "humanaios.internal-repository-snapshot.v0.1"
OUTPUT_SCHEMA = "humanaios.internal-resource-intelligence.v0.1"
REPOS = frozenset({"humanaios-ui/operations", "humanaios-ui/humanaios", "humanaios-ui/lasting-light-ai"})
CAPABILITIES = frozenset({
    "source_verification", "resource_discovery", "human_decision", "admission_integrity",
    "evidence_provenance", "agent_coordination", "behavioral_calibration", "runtime_isolation",
    "privacy_boundary", "offline_witness", "research_method", "deployment_readiness",
    "monitoring", "operator_interface", "recovery_outcome",
})
KIND = {"ISSUE", "PR"}
ITEM_STATES = {"OPEN", "CLOSED", "MERGED", "DRAFT"}
PRIORITIES = {"P0", "P1", "P2"}
OBS_STATES = {"SUCCESS", "FAILURE", "SKIPPED", "CANCELLED", "UNKNOWN"}
PHASES = {"ENTER", "EXPOSURE", "EXIT"}
HEX = re.compile(r"^[0-9a-f]{40}$")
TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
COMMENT = re.compile(r"^https://github\.com/humanaios-ui/operations/(?:issues|pull)/([1-9][0-9]*)#issuecomment-([1-9][0-9]*)$")


def _keys(row: dict, expected: set[str], required: set[str]):
    if type(row) is not dict or not required <= row.keys() or set(row) - expected:
        raise ValueError("missing or unallowlisted fields")


def _text(value, limit=160):
    if type(value) is not str or not value or len(value) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("invalid bounded text")
    return value


def _time(value):
    _text(value, 48)
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("time must be ISO8601") from exc
    if t.utcoffset() is None:
        raise ValueError("timezone is required")
    return value


def _repo(value):
    if value not in REPOS:
        raise ValueError("unapproved repository scope")
    return value


def _github_url(url, repo, kind=None, number=None):
    _text(url, 350)
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "github.com" or parts.query or parts.fragment or "@" in url:
        raise ValueError("only canonical public GitHub object links allowed")
    path = f"/{repo}/"
    if not parts.path.startswith(path):
        raise ValueError("source outside explicit repository")
    tail = parts.path[len(path):]
    if kind and tail != f"{'pull' if kind == 'PR' else 'issues'}/{number}":
        raise ValueError("source URL / identity mismatch")
    return url


def _capabilities(value):
    if type(value) is not list or len(value) > 12 or len(value) != len(set(value)) or any(v not in CAPABILITIES for v in value):
        raise ValueError("capabilities must use unique declared codes")
    return value


def _item(row):
    keys = {"repository", "kind", "number", "title", "state", "head_sha", "source_url", "capabilities"}
    _keys(row, keys, keys)
    repo = _repo(row["repository"])
    if row["kind"] not in KIND or type(row["number"]) is not int or not (0 < row["number"] < 10000000):
        raise ValueError("invalid issue/PR identity")
    _text(row["title"], 180)
    if row["state"] not in ITEM_STATES:
        raise ValueError("invalid state")
    sha = row["head_sha"]
    if row["kind"] == "PR" and (type(sha) is not str or not HEX.fullmatch(sha)):
        raise ValueError("PR must have exact 40-hex head")
    if row["kind"] == "ISSUE" and sha is not None:
        raise ValueError("issue cannot claim head SHA")
    _github_url(row["source_url"], repo, row["kind"], row["number"])
    _capabilities(row["capabilities"])
    return f"{repo}/{row['kind']}#{row['number']}"


def _need(row):
    keys = {"need_id", "label", "priority", "capabilities", "source_url", "repository"}
    _keys(row, keys, keys)
    _text(row["need_id"], 64)
    if not TOKEN.fullmatch(row["need_id"]):
        raise ValueError("bad need id")
    _text(row["label"], 140)
    if row["priority"] not in PRIORITIES or not _capabilities(row["capabilities"]):
        raise ValueError("need requires declared capability and priority")
    _github_url(row["source_url"], _repo(row["repository"]))
    return row["need_id"]


def _observation(row, index):
    keys = {"item_ref", "head_sha", "run_id", "conclusion", "source_url"}
    _keys(row, keys, keys)
    item = index.get(row["item_ref"])
    if item is None or item["kind"] != "PR":
        raise ValueError("CI must reference known PR")
    if type(row["run_id"]) is not int or row["run_id"] <= 0 or row["conclusion"] not in OBS_STATES:
        raise ValueError("bad check run")
    if type(row["head_sha"]) is not str or not HEX.fullmatch(row["head_sha"]):
        raise ValueError("CI head missing")
    expected = f"https://github.com/{item['repository']}/actions/runs/{row['run_id']}"
    if row["source_url"] != expected:
        raise ValueError("CI source ID is not bound to run ID")
    return "HEAD_MATCH" if row["head_sha"] == item["head_sha"] else "HEAD_MISMATCH"


def _agent_event(row):
    keys = {"subject", "session", "phase", "actor_login", "agent_claim", "comment_id", "comment_url", "p1_forecast_pct", "p2_result"}
    required = {"subject", "session", "phase", "actor_login", "agent_claim", "comment_id", "comment_url"}
    _keys(row, keys, required)
    if not re.fullmatch(r"(?:pr|issue):[1-9][0-9]{0,7}", row["subject"]):
        raise ValueError("bad agent subject")
    if any(not isinstance(row[k], str) or not TOKEN.fullmatch(row[k]) for k in ("session", "actor_login", "agent_claim")):
        raise ValueError("invalid agent ID")
    if row["phase"] not in PHASES or type(row["comment_id"]) is not int or row["comment_id"] <= 0:
        raise ValueError("invalid phase/comment")
    match = COMMENT.fullmatch(row["comment_url"])
    if not match or int(match.group(2)) != row["comment_id"] or int(match.group(1)) != int(row["subject"].split(":")[1]):
        raise ValueError("comment URL not bound to subject and ID")
    if row["phase"] == "ENTER":
        if type(row.get("p1_forecast_pct")) is not int or not 0 <= row["p1_forecast_pct"] <= 100 or "p2_result" in row:
            raise ValueError("P1 requires bounded forecast")
    elif row["phase"] == "EXPOSURE":
        if row.get("p2_result") not in OBS_STATES or "p1_forecast_pct" in row:
            raise ValueError("P2 requires reported result")
    elif "p1_forecast_pct" in row or "p2_result" in row:
        raise ValueError("P3 cannot overwrite forecast or review")
    return row["subject"], row["session"]


def project(snapshot: dict) -> dict:
    """Pure deterministic projection: no source authentication or side effects."""
    required = {"schema", "as_of", "items", "needs", "ci_observations", "agent_events"}
    _keys(snapshot, required, required)
    if snapshot["schema"] != SCHEMA:
        raise ValueError("unsupported snapshot schema")
    _time(snapshot["as_of"])
    for name, maximum in (("items", 250), ("needs", 100), ("ci_observations", 500), ("agent_events", 300)):
        if type(snapshot[name]) is not list or len(snapshot[name]) > maximum:
            raise ValueError("unbounded snapshot")
    indices = [_item(row) for row in snapshot["items"]]
    if len(set(indices)) != len(indices):
        raise ValueError("duplicate issue/PR")
    index = dict(zip(indices, snapshot["items"]))
    need_ids = [_need(row) for row in snapshot["needs"]]
    if len(set(need_ids)) != len(need_ids):
        raise ValueError("duplicate need")
    observed = {}
    for row in snapshot["ci_observations"]:
        state = _observation(row, index)
        key = (row["item_ref"], row["run_id"])
        if key in observed:
            raise ValueError("duplicate CI observation")
        observed[key] = dict(row, alignment=state)
    sessions = {}
    seen_comments = set()
    quarantined = []
    for row in snapshot["agent_events"]:
        subject, session = _agent_event(row)
        ref = f"humanaios-ui/operations/{subject.split(':')[0].upper()}#{subject.split(':')[1]}"
        if ref not in index:
            # Existing GitHub issue/PR is required before an agent claim is displayed.
            raise ValueError("agent session lacks source item")
        if row["comment_id"] in seen_comments:
            raise ValueError("replayed comment ID")
        seen_comments.add(row["comment_id"])
        sessions.setdefault((subject, session), []).append(row)
    agent_cards = []
    for (subject, session), events in sorted(sessions.items()):
        phases = [v["phase"] for v in events]
        reasons = []
        if phases not in (["ENTER"], ["ENTER", "EXPOSURE"], ["ENTER", "EXPOSURE", "EXIT"]):
            reasons.append("MISSING_DUPLICATE_OR_OUT_OF_ORDER_PHASE")
        if len(events) >= 2 and events[0]["actor_login"] == events[1]["actor_login"]:
            reasons.append("SELF_REVIEW_NOT_INDEPENDENT")
        if len(events) == 3 and (events[0]["actor_login"] != events[2]["actor_login"] or events[0]["agent_claim"] != events[2]["agent_claim"]):
            reasons.append("EXIT_ACTOR_MISMATCH")
        agent_cards.append({"subject":subject,"session":session,"phase_count":len(events),
            "assessment":"QUARANTINE" if reasons else "UNVERIFIED_AGENT_RECORDS",
            "reasons": reasons, "comment_refs":[v["comment_url"] for v in events],
            "source_claimed_outcome":next((v["p2_result"] for v in events if v["phase"]=="EXPOSURE"),"UNKNOWN"),
            "independent_behavioral_validation":"NOT_ESTABLISHED",
            "actor_independence":"NOT_ESTABLISHED"})
        if reasons:
            quarantined.append({"subject":subject,"session":session,"reasons":reasons})
    resources = []
    for key, item in index.items():
        repo = item["repository"]
        mine = ResourceMine(stable_mine_id(f"https://github.com/{repo}"),repo,"GITHUB_REPOSITORY",
            f"https://github.com/{repo}","internal_snapshot",roles=["EVIDENCE_SOURCE","GOVERNED_SYSTEM"])
        digest = hashlib.sha256(key.encode()).hexdigest()[:16].upper()
        candidate = ResourceCandidate(resource_id="RES-INT-"+digest,title=item["title"],
            source_name=repo,source_url=item["source_url"],canonical_url=item["source_url"],
            discovery_method="caller_supplied_snapshot_read_only",discovered_at=snapshot["as_of"],
            resource_types=["internal_capability_candidate"],resource_affordances=item["capabilities"],
            evidence=[EvidenceRef(item["source_url"],"source_pointer_not_authenticated",snapshot["as_of"],
                "Caller referenced this repository item; requires independent readback")],
            eligibility_status="UNASSESSED",route="VERIFY_NOW",status="UNKNOWN",
            opportunity_identity=key,opportunity_kind="internal_capability_candidate")
        bind_opportunity(mine,candidate,opportunity_source_kind="internal_repository_record")
        result = candidate.to_dict()
        result.update({"item_ref":key,"item_state":item["state"],"head_sha":item["head_sha"],
            "source_authentication":"NOT_ESTABLISHED","authority_effect":"NONE",
            "evidence_provenance":"UNAUTHENTICATED_SOURCE_SNAPSHOT",
            "ci_observations":[{"run_id":v["run_id"],"reported_conclusion":v["conclusion"],
                "source_url":v["source_url"],"head_alignment":v["alignment"],
                "independently_authenticated":False}
                for (ref,_),v in observed.items() if ref==key]})
        resources.append(result)
    broker = []
    for need in sorted(snapshot["needs"],key=lambda r:(r["priority"],r["need_id"])):
        matches = []
        for res in resources:
            common = sorted(set(need["capabilities"]) & set(res["resource_affordances"]))
            if common:
                matches.append({"resource_id":res["resource_id"],"item_ref":res["item_ref"],
                    "capability_codes":common,"readiness":"REQUIRES_INDEPENDENT_VALIDATION",
                    "may_execute":False})
        broker.append({"need_id":need["need_id"],"label":need["label"],"priority":need["priority"],
            "attractor":{"classes":["DECLARED_CAPABILITY_DEPENDENCY"],"source_ref":need["source_url"],
                         "expected_capabilities":need["capabilities"],"search_intent":"SATISFY_DEPENDENCY"},
            "candidates":matches,"state":"CANDIDATES_REQUIRE_HUMAN_REVIEW" if matches else "NO_MATCH_IN_BOUNDED_SNAPSHOT",
            "coverage":"BOUNDED_SNAPSHOT_NOT_EXHAUSTIVE","roi":"NOT_MEASURED",
            "authority_effect":"NONE"})
    return {"schema":OUTPUT_SCHEMA,"as_of":snapshot["as_of"],"authority_effect":"NONE",
        "source_authentication":"NOT_ESTABLISHED","board_role":"NON_AUTHORITATIVE_DERIVED_PROJECTION",
        "coverage":"BOUNDED_CALLER_SNAPSHOT","resources":resources,"brokerage":broker,
        "agent_sessions":agent_cards,"quarantine":quarantined,
        "oracle":{"role":"CONTESTABLE_SYNTHESIS_ONLY","claims_status":"INFERRED",
            "unknowns":["Independent source readback not performed by projector",
                "Agent account is not model identity", "CI reported by input is not authenticated by projector",
                "No verified acquisition, revenue, or recovery benefit"],
            "can_authorize":False,"can_execute":False},
        "mission_outcomes":{"resource_acquisition":"NOT_ESTABLISHED","revenue":"NOT_ESTABLISHED",
            "recovery_benefit":"NOT_ESTABLISHED"}}


def render_html(bundle: dict) -> str:
    """Static escaped offline board; no JavaScript, network, or ingestion of raw agent text."""
    if bundle.get("schema") != OUTPUT_SCHEMA or bundle.get("authority_effect") != "NONE":
        raise ValueError("not a bounded non-authoritative projection")
    esc = lambda x: html.escape(str(x),quote=True)
    def link(url,label):
        return f'<a href="{esc(url)}" rel="noopener noreferrer">{esc(label)}</a>'
    rows = []
    for r in bundle["resources"]:
        rows.append("<tr><td>"+link(r["canonical_url"],r["item_ref"])+"</td><td>"+esc(r["title"])+"</td><td>"+esc(r["item_state"])+"</td><td>NOT ESTABLISHED</td></tr>")
    needs = []
    for n in bundle["brokerage"]:
        ids = ", ".join(esc(x["item_ref"]) for x in n["candidates"]) or "No match observed"
        needs.append("<tr><td>"+esc(n["need_id"])+"</td><td>"+esc(n["label"])+"</td><td>"+esc(n["priority"])+"</td><td>"+ids+"</td></tr>")
    sessions = []
    for a in bundle["agent_sessions"]:
        sessions.append("<tr><td>"+esc(a["subject"])+"</td><td>"+esc(a["session"])+"</td><td>"+esc(a["assessment"])+"</td><td>NOT ESTABLISHED</td></tr>")
    return ("<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; form-action 'none'\">"
        "<title>HumanAIOS Internal Resource Observatory</title><style>body{font:16px system-ui;background:#101b29;color:#ebf2fa;max-width:1050px;margin:auto;padding:30px}table{border-collapse:collapse;width:100%;margin:12px 0 26px}td,th{border:1px solid #586a7b;padding:9px;text-align:left}a{color:#80d6d9}.warning{background:#553d20;padding:14px}</style></head><body>"
        "<h1>HumanAIOS Internal Resource Observatory</h1><p class=\"warning\">READ-ONLY · NO AUTHORITY · Caller-supplied snapshot · Not independently authenticated · No execution.</p>"
        "<h2>Repository capabilities</h2><table><tr><th>Source</th><th>Title</th><th>Reported state</th><th>Authenticated</th></tr>"+"".join(rows)+"</table>"
        "<h2>Need → internal resource brokerage</h2><table><tr><th>Need</th><th>Purpose</th><th>Priority</th><th>Candidate matches</th></tr>"+"".join(needs)+"</table>"
        "<h2>Agent quarantine (observation only)</h2><table><tr><th>Subject</th><th>Session</th><th>Condition</th><th>Independent behavioral proof</th></tr>"+"".join(sessions)+"</table>"
        "<p>Oracle synthesis is inferred and contestable. Matches are NOT resource acquisition, approval, revenue, or recovery benefit.</p></body></html>")


def render_report(bundle: dict) -> str:
    if bundle.get("schema") != OUTPUT_SCHEMA or bundle.get("authority_effect") != "NONE":
        raise ValueError("invalid read-only bundle")
    lines = ["HumanAIOS Systems Intelligence — Internal Resource Brokerage (Z1)",
        f"As of {bundle['as_of']} | Source: bounded unverified snapshot | Authority: NONE",
        "MISSION: acquired resources, revenue and recovery benefit — NOT ESTABLISHED", "",
        f"INVENTORY: {len(bundle['resources'])} candidate internal resources, all requiring independent readback.",
        f"AGENT QUARANTINE: {len(bundle['agent_sessions'])} sessions; {len(bundle['quarantine'])} anomalous; no isolation claim.",
        "ORACLE: advisory/INFERRED only; no authorization, execution, or policy mutation.", "",
        "RESOURCE BROKER / DECISIONS:"]
    for need in bundle["brokerage"]:
        lines.append(f"{need['priority']} {need['need_id']}: {need['label']} | {need['state']} | candidates={len(need['candidates'])} | ROI=NOT_MEASURED | approval=HUMAN_REVIEW_REQUIRED")
        for match in need["candidates"]:
            lines.append(f"    {match['item_ref']} | {','.join(match['capability_codes'])} | NOT VERIFIED")
    lines += ["", "CALENDAR: No bookings or due dates are derived from repository records; link to separately verified human calendar.",
        "VALIDATION REQUIRED: independent GitHub source-readback, exact-head CI verification, authorization proof, private data review.",
        "SINGLE SOURCE OF TRUTH: GitHub/Coordinator/approved evidence; this report is only a derived projection."]
    return "\n".join(lines)+"\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline internal repository mine / board: no network or writes")
    parser.add_argument("--input", required=True, help="Caller-provided, privacy-reviewed JSON snapshot")
    parser.add_argument("--format", choices=("json", "html", "report"), default="report")
    args = parser.parse_args(argv)
    with open(args.input, encoding="utf-8") as stream:
        snapshot = json.load(stream)
    bundle = project(snapshot)
    if args.format == "html":
        print(render_html(bundle))
    elif args.format == "json":
        print(json.dumps(bundle,sort_keys=True,indent=2))
    else:
        print(render_report(bundle))
    return 0


if __name__ == "__main__":
    sys.exit(main())
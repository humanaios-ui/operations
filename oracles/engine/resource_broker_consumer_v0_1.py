"""Read-only consumer of the existing internal Resource Broker projection.

No source fetching, queue persistence, authorization, Actualizer dispatch, or
Coordinator admission. A broker match is only an unverified candidate.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from urllib.parse import urlsplit

SCHEMA = "humanaios.resource-broker-oracle-bridge.v0.1"
BROKER_SCHEMA = "humanaios.internal-resource-intelligence.v0.1"
ORACLE_ID = "ORACLE-DOMAIN-REPOSITORY"
AUTHORITY = {"advisory_only": True, "can_authorize": False, "authority_effect": "NONE"}
REF = re.compile(r"\Ahumanaios-ui/(operations|humanaios|lasting-light-ai)/(PR|ISSUE)#([1-9][0-9]*)\Z")
ID = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\Z")
SHA = re.compile(r"\A[a-f0-9]{40}\Z")
CAP = frozenset({
    "source_verification", "resource_discovery", "human_decision", "admission_integrity",
    "evidence_provenance", "agent_coordination", "behavioral_calibration", "runtime_isolation",
    "privacy_boundary", "offline_witness", "research_method", "deployment_readiness",
    "monitoring", "operator_interface", "recovery_outcome",
})
FORBIDDEN_FIELDS = frozenset({
    "private_email", "raw_body", "body_html", "gmail_url", "access_token", "api_key",
    "review_status", "account_entitlement", "raw",
    "password", "email_address", "authorization_grant", "secret", "customer_data",
})
TOP_KEYS = frozenset({
    "schema", "as_of", "authority_effect", "source_authentication", "board_role",
    "coverage", "resources", "brokerage", "agent_sessions", "quarantine", "oracle",
    "mission_outcomes",
})


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False)


def _digest(prefix, *parts):
    body = _canonical(parts).encode("utf-8")
    return prefix + "-" + hashlib.sha256(body).hexdigest()[:24]


def _time(value):
    if not isinstance(value, str) or len(value) > 48:
        raise ValueError("invalid observation time")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid observation time") from error
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamp must include an offset")
    return dt


def _source_ref(ref, url):
    if not isinstance(ref, str):
        raise ValueError("invalid repository ref")
    match = REF.fullmatch(ref)
    if not match:
        raise ValueError("invalid repository ref")
    repo, kind, num = match.groups()
    exact = f"https://github.com/humanaios-ui/{repo}/{'pull' if kind == 'PR' else 'issues'}/{num}"
    if type(url) is not str or url != exact:
        raise ValueError("source URL and repository object disagree")
    return kind


def _need_url(url):
    if not isinstance(url, str) or len(url) > 350:
        raise ValueError("invalid need source")
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != "github.com" or parts.query
            or parts.fragment or not re.fullmatch(
                r"/humanaios-ui/(operations|humanaios|lasting-light-ai)/(issues|pull)/[1-9][0-9]*",
                parts.path)):
        raise ValueError("need must reference a canonical GitHub issue or PR")
    return url


def _ensure_safe(row):
    if type(row) is not dict or FORBIDDEN_FIELDS.intersection(row):
        raise ValueError("private or unexpected fields in broker data")
    if row.get("authority_effect", "NONE") != "NONE":
        raise ValueError("broker attempted authority promotion")
    if row.get("can_authorize") is True or row.get("may_execute") is True:
        raise ValueError("broker attempted execution authority")


def _observation(need, candidate, resource, as_of, recorded_at, codes):
    if resource is None:
        locator = _need_url(need["attractor"]["source_ref"])
        statement = f"Need {need['need_id']} had no declared resource match in this bounded snapshot; coverage is incomplete."
        subject_ref = need["need_id"]
        identity = [need["need_id"], "NO_MATCH", locator, as_of]
    else:
        locator = resource["source_url"]
        subject_ref = resource["item_ref"]
        statement = (f"Need {need['need_id']} has an unverified capability-code match to "
                     f"{subject_ref}. Independent readback is required.")
        identity = [need["need_id"], resource["resource_id"],
                    resource["head_sha"], codes, as_of]
    return {
        "schema_version": "1.0", "observation_id": _digest("OBS", *identity),
        "oracle_id": ORACLE_ID, "source": {"substrate": "github", "locator": locator},
        "as_of": as_of, "recorded_at": recorded_at,
        "observation": statement, "relation": None, "subject_ref": subject_ref,
        "transformation": {
            "component": "resource_broker_consumer_v0_1.consume",
            "version": "0.1.0", "producer_ref": "resource_miner.internal_repository_broker.project",
        },
        **AUTHORITY,
    }


def consume(broker_projection: dict, *, recorded_at: str | None = None) -> dict:
    """Consume real broker output; return schema-shaped advisory observations/delta.

    Results are not sent to a running Oracle service or persisted. The caller
    may hand the JSON to the existing Oracle review process after human review.
    """
    b = broker_projection
    if type(b) is not dict or set(b) != TOP_KEYS or b.get("schema") != BROKER_SCHEMA:
        raise ValueError("not a Resource Broker projection")
    if b.get("authority_effect") != "NONE" or b.get("source_authentication") != "NOT_ESTABLISHED":
        raise ValueError("broker authentication/authority claim was promoted")
    if b.get("board_role") != "NON_AUTHORITATIVE_DERIVED_PROJECTION":
        raise ValueError("unexpected broker board role")
    oracle = b.get("oracle")
    if (type(oracle) is not dict or oracle.get("can_authorize") is not False
            or oracle.get("can_execute") is not False
            or oracle.get("claims_status") != "INFERRED"):
        raise ValueError("broker oracle boundary changed")
    outcomes = b.get("mission_outcomes")
    if (type(outcomes) is not dict or any(
        outcomes.get(x) != "NOT_ESTABLISHED" for x in
        ("resource_acquisition", "revenue", "recovery_benefit")
    )):
        raise ValueError("benefit claim is not proven")
    as_of = b["as_of"]
    dt = _time(as_of)
    recorded_at = as_of if recorded_at is None else recorded_at
    if _time(recorded_at) < dt:
        raise ValueError("record time predates observed snapshot")
    resources, brokerage = b.get("resources"), b.get("brokerage")
    if (type(resources) is not list or len(resources) > 250 or
            type(brokerage) is not list or len(brokerage) > 100):
        raise ValueError("unbounded broker data")

    by_id = {}
    for r in resources:
        _ensure_safe(r)
        rid, ref, source = r.get("resource_id"), r.get("item_ref"), r.get("source_url")
        if not isinstance(rid, str) or not ID.fullmatch(rid) or rid in by_id:
            raise ValueError("duplicate or malformed resource identity")
        kind = _source_ref(ref, source)
        if r.get("canonical_url") != source or r.get("source_authentication") != "NOT_ESTABLISHED":
            raise ValueError("resource source is not canonical/unverified")
        if r.get("evidence_provenance") != "UNAUTHENTICATED_SOURCE_SNAPSHOT":
            raise ValueError("resource evidence status was promoted")
        if r.get("eligibility_status") != "UNASSESSED":
            raise ValueError("resource eligibility was promoted")
        if not isinstance(r.get("opportunity_id"), str) or not ID.fullmatch(r["opportunity_id"]):
            raise ValueError("missing Resource Miner opportunity identity")
        if kind == "PR":
            if not isinstance(r.get("head_sha"), str) or not SHA.fullmatch(r["head_sha"]):
                raise ValueError("PR must preserve exact head SHA")
        elif r.get("head_sha") is not None:
            raise ValueError("issue cannot assert a head")
        caps = r.get("resource_affordances")
        if (type(caps) is not list or len(caps) > 12 or len(set(caps)) != len(caps)
                or any(c not in CAP for c in caps)):
            raise ValueError("invalid capability codes")
        ci = r.get("ci_observations", [])
        if type(ci) is not list or len(ci) > 500 or any(
            type(c) is not dict or c.get("independently_authenticated") is not False
            or c.get("head_alignment") not in {"HEAD_MATCH", "HEAD_MISMATCH"}
            for c in ci
        ):
            raise ValueError("CI was promoted or malformed")
        by_id[rid] = r

    observations, operations, strategies, seen_needs = [], [], [], set()
    for need in brokerage:
        _ensure_safe(need)
        nid = need.get("need_id")
        if not isinstance(nid, str) or not ID.fullmatch(nid) or nid in seen_needs:
            raise ValueError("duplicate/malformed need identity")
        seen_needs.add(nid)
        attractor = need.get("attractor")
        if type(attractor) is not dict or attractor.get("classes") != ["DECLARED_CAPABILITY_DEPENDENCY"]:
            raise ValueError("unrecognized declared capability dependency")
        _need_url(attractor.get("source_ref"))
        codes = attractor.get("expected_capabilities")
        if (type(codes) is not list or not codes or len(codes) > 12
                or len(set(codes)) != len(codes) or any(c not in CAP for c in codes)):
            raise ValueError("invalid need capabilities")
        matches = need.get("candidates")
        if (type(matches) is not list or len(matches) > 250 or
                need.get("authority_effect") != "NONE" or need.get("roi") != "NOT_MEASURED"):
            raise ValueError("unbounded or promoted broker match")
        if need.get("state") != ("CANDIDATES_REQUIRE_HUMAN_REVIEW" if matches else "NO_MATCH_IN_BOUNDED_SNAPSHOT"):
            raise ValueError("match list and state disagree")
        seen_matches = set()
        if not matches:
            obs = _observation(need, None, None, as_of, recorded_at, [])
            observations.append(obs)
            operations.append({
                "op": "ADD", "subject_id": nid, "object_id": None, "as_of": as_of,
                "payload": {"state": "NO_MATCH_IN_BOUNDED_SNAPSHOT", "authority_effect": "NONE"},
                "evidence_observation_ids": [obs["observation_id"]],
            })
        for match in matches:
            _ensure_safe(match)
            rid = match.get("resource_id")
            if rid in seen_matches:
                raise ValueError("duplicate match")
            seen_matches.add(rid)
            resource = by_id.get(rid)
            if resource is None or match.get("item_ref") != resource.get("item_ref"):
                raise ValueError("broker match lacks exact resource identity")
            common = sorted(set(codes) & set(resource["resource_affordances"]))
            if (not common or match.get("capability_codes") != common
                    or match.get("readiness") != "REQUIRES_INDEPENDENT_VALIDATION"
                    or match.get("may_execute") is not False):
                raise ValueError("forged or unsafe declared match")
            obs = _observation(need, match, resource, as_of, recorded_at, common)
            observations.append(obs)
            mismatch = any(c["head_alignment"] == "HEAD_MISMATCH" for c in resource["ci_observations"])
            operations.append({
                "op": "ADD", "subject_id": nid, "object_id": rid, "as_of": as_of,
                "payload": {
                    "state": "DECLARED_MATCH_UNVERIFIED", "capability_codes": common,
                    "resource_id": rid, "opportunity_id": resource["opportunity_id"],
                    "source_authentication": "NOT_ESTABLISHED",
                    "ci_head_mismatch_reported": mismatch, "authority_effect": "NONE",
                }, "evidence_observation_ids": [obs["observation_id"]],
            })
        mismatches = any(op["payload"].get("ci_head_mismatch_reported")
                         for op in operations if op["subject_id"] == nid)
        strategies.append({
            "need_id": nid, "priority": need.get("priority"),
            "state": "HUMAN_REVIEW_REQUIRED" if matches else "RESEARCH_GAP",
            "matched_resource_ids": sorted(seen_matches),
            "next_test": ("RECHECK_EXACT_HEAD_CI" if mismatches
                          else "INDEPENDENT_GITHUB_SOURCE_READBACK" if matches
                          else "VERIFY_MORE_INTERNAL_SOURCES"),
            "reason_codes": (["BOUNDED_MATCH_UNVERIFIED", "NO_PROVIDER_ENTITLEMENT_PROOF"] if matches
                             else ["NO_MATCH_IN_BOUNDED_SNAPSHOT"]),
            "may_execute": False, "roi": "NOT_MEASURED", "authority_effect": "NONE",
        })
    ids = [v["observation_id"] for v in observations]
    if len(set(ids)) != len(ids):
        raise ValueError("colliding Oracle observation identity")
    delta = None
    if observations:
        delta = {
            "schema_version": "1.0",
            "delta_id": _digest("DELTA", as_of, [(o["subject_id"], o["object_id"], o["payload"])
                                                  for o in operations]),
            "oracle_id": ORACLE_ID, "recorded_at": recorded_at,
            "source_observation_ids": ids, "operations": operations,
            **AUTHORITY,
        }
    return {
        "schema": SCHEMA, "as_of": as_of, "recorded_at": recorded_at,
        "status": "ADVISORY_BATCH_READY_FOR_HUMAN_REVIEW" if delta else "NO_DECLARED_NEEDS",
        "source_authentication": "NOT_ESTABLISHED",
        "upstream_schema": BROKER_SCHEMA,
        "broker_digest_sha256": hashlib.sha256(_canonical(b).encode("utf-8")).hexdigest(),
        "observations": observations, "graph_delta": delta,
        "strategies": strategies,
        "queue_delivery": "NOT_ATTEMPTED", "persisted": False,
        "independent_verification": "NOT_ESTABLISHED",
        "mission_outcomes": {"resource_acquisition": "NOT_ESTABLISHED",
                             "revenue": "NOT_ESTABLISHED", "recovery_benefit": "NOT_ESTABLISHED"},
        **AUTHORITY,
    }

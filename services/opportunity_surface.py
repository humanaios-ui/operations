"""OSA v0.1: read-only, non-authoritative opportunity observation projection.

Consumes supplied ResourceCandidate / URA dictionaries, Guiding Light evaluated
results and source-referenced activity claims. No I/O, source authentication,
eligibility decision, action execution, persistence or Coordinator mutation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

SCHEMA = "humanaios.opportunity-surface.v0.1"
AUTHORITY_EFFECT = "NONE"

# Identifiers preserve all nine dimensions and all 33 rules from the provided
# Luck Surface Area self-assessment. This taxonomy is descriptive, not validated
# as a predictive measure or a governance criterion.
DIMENSIONS: dict[str, tuple[str, ...]] = {
    "shots": ("volume_beats_perfection", "experiment_fast_kill_fast",
              "action_creates_options", "rate_of_encounters"),
    "visible": ("do_things_tell_people", "learn_in_public", "own_name_online"),
    "people": ("weak_ties", "bridge_groups", "talk_to_strangers",
               "connect_others", "dont_burn_bridges"),
    "position": ("opportunity_hubs", "embed_in_scene", "unique_combinations"),
    "downside": ("asymmetric_bets", "avoid_ruin", "barbell", "reduce_fragility"),
    "flexible": ("keep_slack", "reversible_decisions", "short_commitments",
                 "stay_adaptable"),
    "notice": ("relax_attention", "break_routines", "deep_expertise",
               "you_never_know"),
    "reframe": ("silver_lining", "every_situation_audition"),
    "compound": ("expect_good_fortune", "long_games", "add_skills", "persist"),
}
STAGES = ("EXPOSED", "QUALIFIED", "PURSUED", "SUCCEEDED")
CLAIM_STATES = {"PLANNED", "SELF_ATTESTED", "SOURCE_OBSERVED", "RETRACTED"}
EVIDENCE_STATES = {"SELF_ATTESTED", "SOURCE_LOCATED", "SOURCE_OBSERVED"}


class ObservationError(ValueError):
    """The submitted projection input violates a declared safety or data rule."""


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ObservationError(message)


def _timestamp(value: Any) -> datetime:
    _require(isinstance(value, str) and bool(value), "timestamp required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservationError("invalid timestamp") from exc
    _require(parsed.tzinfo is not None and parsed.utcoffset() is not None,
             "timestamp must be offset-aware")
    return parsed.astimezone(timezone.utc)


def _source_refs(row: dict, key: str = "source_refs") -> None:
    refs = row.get(key)
    _require(isinstance(refs, list) and bool(refs)
             and all(isinstance(ref, str) and bool(ref.strip()) for ref in refs),
             f"{key} must contain source references")


def _non_authoritative(row: dict) -> None:
    _require(row.get("authority_effect", "NONE") == "NONE",
             "observation cannot assert authority")
    _require(row.get("can_authorize", False) is False,
             "observation cannot authorize")
    _require(row.get("authorization", "NOT_GRANTED") == "NOT_GRANTED",
             "observation cannot grant authorization")
    _require(row.get("execution", "NOT_AVAILABLE") == "NOT_AVAILABLE",
             "observation cannot grant execution")
    _require(row.get("admission_effect", "NONE") == "NONE",
             "observation cannot grant admission")
    _require(row.get("merge_authority", False) is False,
             "observation cannot claim merge authority")
    _require(row.get("authenticated", False) is False,
             "observation cannot self-authenticate")
    _require(row.get("eligibility_established", False) is False,
             "observation cannot establish eligibility")


def _list(snapshot: dict, key: str) -> list:
    value = snapshot.get(key, [])
    _require(isinstance(value, list), f"{key} must be a list")
    _require(all(isinstance(item, dict) for item in value),
             f"{key} items must be objects")
    return value


def project(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Return an advisory projection without changing or persisting inputs.

    Explicit matching IDs, referenced observations and phase ordering are
    required. All counts describe *supplied claims*; no source is authenticated.
    QUALIFIED is mapped opportunity screening, never applicant eligibility.
    """
    _require(isinstance(snapshot, dict), "snapshot must be an object")
    _require(snapshot.get("schema_version") == SCHEMA, "unsupported schema")
    _non_authoritative(snapshot)
    as_of = _timestamp(snapshot.get("as_of"))

    candidates: dict[str, dict] = {}
    source_bound: set[str] = set()
    omissions: list[str] = []
    for resource in _list(snapshot, "resource_candidates"):
        _non_authoritative(resource)
        rid = resource.get("resource_id")
        _require(isinstance(rid, str) and bool(rid.strip()), "resource_id required")
        _require(rid not in candidates, "duplicate resource_id")
        _require(_timestamp(resource.get("discovered_at")) <= as_of,
                 "future resource observation")
        candidates[rid] = resource
        evidence = resource.get("evidence")
        if (not isinstance(resource.get("source_url"), str)
                or not resource["source_url"]
                or not isinstance(evidence, list) or not evidence):
            omissions.append(rid + ":NO_SOURCE_BINDING")
            continue
        usable = True
        for item in evidence:
            if (not isinstance(item, dict) or not isinstance(item.get("url"), str)
                    or not item["url"] or not item.get("observed_at")):
                usable = False
                break
            _require(_timestamp(item["observed_at"]) <= as_of,
                     "future resource source observation")
        if usable:
            source_bound.add(rid)
        else:
            omissions.append(rid + ":INCOMPLETE_SOURCE_BINDING")

    gl = snapshot.get("guiding_light")
    _require(isinstance(gl, dict) and isinstance(gl.get("results"), list),
             "evaluated Guiding Light results required")
    _non_authoritative(gl)
    if gl.get("evaluated_at"):
        _require(_timestamp(gl["evaluated_at"]) <= as_of,
                 "future Guiding Light evaluation")
    results: dict[str, dict] = {}
    for result in gl["results"]:
        _require(isinstance(result, dict), "Guiding Light result must be object")
        tid = result.get("target_id")
        _require(isinstance(tid, str) and bool(tid) and tid not in results,
                 "invalid or duplicate Guiding Light target_id")
        _require(result.get("classification") in
                 {"REACHABLE", "BRIDGE", "FRONTIER", "HOLD"},
                 "unsupported Guiding Light classification")
        _require(result.get("assessment_state") in
                 {"MAPPED", "BLOCKED", "INVESTIGATE", "UNMAPPED"},
                 "unsupported Guiding Light assessment state")
        _require(isinstance(result.get("mandatory_unknowns"), list)
                 and isinstance(result.get("mandatory_blockers"), list),
                 "mandatory Guiding Light unknown/blocker lists required")
        results[tid] = result

    bound: dict[str, str] = {}
    for link in _list(snapshot, "bindings"):
        _non_authoritative(link)
        rid, tid = link.get("resource_id"), link.get("target_id")
        _require(isinstance(rid, str) and isinstance(tid, str)
                 and rid in source_bound and tid in results and rid not in bound,
                 "binding needs source-bound resource and existing unique target")
        _source_refs(link)
        bound[rid] = tid

    timeline: list[tuple[datetime, str, dict]] = []
    event_ids: set[str] = set()
    for event in _list(snapshot, "activity_events"):
        _non_authoritative(event)
        eid, rid = event.get("event_id"), event.get("resource_id")
        _require(isinstance(eid, str) and bool(eid) and eid not in event_ids,
                 "invalid or duplicate activity event_id")
        event_ids.add(eid)
        _require(isinstance(rid, str) and rid in source_bound,
                 "activity event requires source-bound resource")
        _require(isinstance(event.get("stage"), str)
                 and event["stage"] in set(STAGES) | {"RETRACTED"},
                 "invalid activity stage")
        _require(event.get("evidence_state") in EVIDENCE_STATES,
                 "unsupported activity evidence state")
        _source_refs(event)
        at = _timestamp(event.get("observed_at"))
        _require(_timestamp(candidates[rid]["discovered_at"]) <= at <= as_of,
                 "activity observation outside valid window")
        timeline.append((at, eid, event))

    progress: dict[str, int] = {rid: 0 for rid in source_bound}
    retracted: set[str] = set()
    previous_time: dict[str, datetime] = {}
    for at, _, event in sorted(timeline, key=lambda item: (item[0], item[1])):
        rid, stage = event["resource_id"], event["stage"]
        _require(rid not in previous_time or at > previous_time[rid],
                 "activity timestamps must be strictly increasing per resource")
        previous_time[rid] = at
        _require(rid not in retracted, "cannot advance after retraction")
        if stage == "RETRACTED":
            _require(progress[rid] > 0, "retraction requires prior exposure")
            retracted.add(rid)
            progress[rid] = 0
            continue
        expected = STAGES[progress[rid]] if progress[rid] < len(STAGES) else None
        _require(stage == expected, "missing, duplicate or out-of-order phase")
        if stage == "QUALIFIED":
            _require(rid in bound, "qualification requires explicit Guiding Light binding")
            target = results[bound[rid]]
            _require(target["classification"] in {"REACHABLE", "BRIDGE"}
                     and target["assessment_state"] == "MAPPED"
                     and not target.get("mandatory_unknowns")
                     and not target.get("mandatory_blockers"),
                     "unknown/blocked Guiding Light target cannot be qualified")
        # A success event must be source-observed (still NOT authenticated).
        if stage == "SUCCEEDED":
            _require(event["evidence_state"] == "SOURCE_OBSERVED",
                     "success requires source-observed claim")
        progress[rid] += 1

    behavior_ids: set[str] = set()
    latest: dict[tuple[str, str], tuple[datetime, str]] = {}
    for claim in _list(snapshot, "behavior_observations"):
        _non_authoritative(claim)
        eid = claim.get("event_id")
        _require(isinstance(eid, str) and bool(eid)
                 and eid not in behavior_ids and eid not in event_ids,
                 "invalid or duplicate behavior event_id")
        behavior_ids.add(eid)
        dim, rule, state = claim.get("dimension"), claim.get("rule_id"), claim.get("state")
        _require(isinstance(dim, str) and dim in DIMENSIONS
                 and isinstance(rule, str) and rule in DIMENSIONS[dim],
                 "unregistered opportunity rule")
        _require(state in CLAIM_STATES, "unsupported behavior claim state")
        _source_refs(claim)
        if claim.get("resource_id") is not None:
            _require(claim["resource_id"] in source_bound,
                     "behavior cannot bind unobserved resource")
        at = _timestamp(claim.get("observed_at"))
        _require(at <= as_of, "future behavior observation")
        key = (dim, rule)
        previous = latest.get(key)
        _require(previous is None or at > previous[0],
                 "behavior correction must be later than prior record")
        latest[key] = (at, state)

    dimension_counts: dict[str, dict] = {}
    for dim, rules in DIMENSIONS.items():
        statuses = [latest.get((dim, rule), (None, "UNKNOWN"))[1] for rule in rules]
        dimension_counts[dim] = {
            "total_rules": len(rules),
            "self_attested": statuses.count("SELF_ATTESTED"),
            "source_observed_claims": statuses.count("SOURCE_OBSERVED"),
            "planned": statuses.count("PLANNED"),
            "unknown_or_retracted": statuses.count("UNKNOWN") + statuses.count("RETRACTED"),
        }

    counts = {
        "candidate_records": len(candidates),
        "source_bound_candidates": len(source_bound),
        "explicit_guiding_light_bindings": len(bound),
        "exposed_claims": sum(phase >= 1 for phase in progress.values()),
        "qualified_claims": sum(phase >= 2 for phase in progress.values()),
        "pursued_claims": sum(phase >= 3 for phase in progress.values()),
        "succeeded_claims": sum(phase >= 4 for phase in progress.values()),
        "retracted_opportunities": len(retracted),
    }
    return {
        "schema_version": SCHEMA,
        "as_of": as_of.isoformat(),
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": False,
        "authenticated": False,
        "eligibility_established": False,
        "execution_available": False,
        "admission_effect": "NONE",
        "epistemic_status": "UNAUTHENTICATED_SOURCE_REFERENCED_CLAIMS",
        "freshness_assessment": "NOT_ESTABLISHED",
        "counts": counts,
        "rates": {
            "qualified_per_exposed": (
                round(counts["qualified_claims"] / counts["exposed_claims"], 4)
                if counts["exposed_claims"] else None
            ),
            "succeeded_per_pursued": (
                round(counts["succeeded_claims"] / counts["pursued_claims"], 4)
                if counts["pursued_claims"] else None
            ),
        },
        "dimensions": dimension_counts,
        "omissions": sorted(omissions),
        "outcome_state": "DESCRIPTIVE_ONLY",
    }

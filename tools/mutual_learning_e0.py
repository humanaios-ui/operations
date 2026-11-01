#!/usr/bin/env python3
"""INTENT-OS Mutual Learning E0: strict, read-only collaboration record checker.
Builder v1.7 compliant · validation_tool
HumanAIOS · S-103126-MUTUAL-LEARNING-E0

No network, inference, state mutations, user profiling, learning scores, or authority.
Records encode separately attributed observations and unresolved disagreement.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

VERSION = "humanaios.mutual_learning.e0.v1"
REPOSITORY = "humanaios-ui/operations"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ISSUE_URL = re.compile(r"^https://github\.com/humanaios-ui/operations/(?:issues|pull)/[1-9][0-9]*$")
STATUS = {"OBSERVED_SOURCE", "INFERRED", "UNVERIFIED", "CONTESTED"}
UNDERSTANDING = {"DEMONSTRATED", "PARTIAL", "NOT_TESTED", "UNKNOWN"}
ACTORS = {"CHATGPT", "CLAUDE", "HUMAN", "INDEPENDENT_REVIEWER"}
KEYS = {
    "schema_version", "record_id", "artifact", "human_intent", "observations",
    "disagreements", "human_learning", "machine_adaptation", "governance",
}
OBS_KEYS = {"id", "actor", "claim", "epistemic_status", "evidence", "review_state"}
ART_KEYS = {"repository", "kind", "number", "url", "head_sha", "head_observed_at"}
GOV = {
    "zone": "Z1", "advisory_only": True, "can_authorize": False,
    "authority_effect": "NONE", "execution": "DISABLED",
    "memory_write": "DISABLED", "project_desk_sync": "DISABLED",
    "intentos_sync": "DISABLED",
}
ALLOWED_EVIDENCE = {"url", "commit_sha", "description"}
REVIEW = {"NOT_REVIEWED", "INDEPENDENT_REVIEW_RECORDED"}
ADAPT = {"PROPOSED", "REJECTED", "APPROVED_FOR_FUTURE_REVIEW"}
DISAGREEMENT = {"OPEN", "RESOLVED_WITH_EVIDENCE"}


def is_choice(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def require_keys(value: Any, keys: set[str], path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return False
    missing = keys - set(value)
    extra = set(value) - keys
    if missing or extra:
        errors.append(f"{path}: missing={sorted(missing)} extra={sorted(extra)}")
        return False
    return True


def is_public_source(url: Any, number: int, kind: str) -> bool:
    if not isinstance(url, str) or not ISSUE_URL.fullmatch(url):
        return False
    expected = f"https://github.com/{REPOSITORY}/{'pull' if kind == 'PR' else 'issues'}/{number}"
    return url == expected


def valid_evidence(source: Any, sha: str, errors: list[str], prefix: str) -> None:
    if not require_keys(source, ALLOWED_EVIDENCE, prefix, errors):
        return
    url = source["url"]
    if not isinstance(url, str) or not url.startswith("https://github.com/humanaios-ui/operations/"):
        errors.append(f"{prefix}: evidence must be canonical public operations GitHub URL")
    elif urlsplit(url).username or urlsplit(url).password or urlsplit(url).query or urlsplit(url).fragment:
        errors.append(f"{prefix}: URL must not carry credentials/query/fragment")
    if source["commit_sha"] != sha:
        errors.append(f"{prefix}: source commit does not match pinned artifact head")
    if not isinstance(source["description"], str) or not source["description"].strip():
        errors.append(f"{prefix}: observation description required")


def validate(record: Any) -> list[str]:
    errors: list[str] = []
    if not require_keys(record, KEYS, "record", errors):
        return errors
    if record["schema_version"] != VERSION:
        errors.append("schema_version: unsupported")
    if not isinstance(record["record_id"], str) or not re.fullmatch(r"ML-E0-[A-Z0-9-]{4,48}", record["record_id"]):
        errors.append("record_id: invalid")
    art = record["artifact"]
    if not require_keys(art, ART_KEYS, "artifact", errors):
        return errors
    sha = art["head_sha"]
    if art["repository"] != REPOSITORY or art["kind"] != "PR" or not isinstance(sha, str) or not HEX40.fullmatch(sha):
        errors.append("artifact: unsupported repo/kind or invalid SHA")
    if type(art["number"]) is not int or art["number"] < 1 or not is_public_source(art["url"], art["number"], art["kind"]):
        errors.append("artifact: invalid number or canonical PR URL")
    if art["head_observed_at"] is not None and (not isinstance(art["head_observed_at"], str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", art["head_observed_at"])):
        errors.append("artifact: timestamp must be UTC ISO8601 or null (not recorded)")
    if not isinstance(record["human_intent"], dict) or set(record["human_intent"]) != {"issue_url", "objective"}:
        errors.append("human_intent: missing/extraneous fields")
    else:
        if not is_public_source(record["human_intent"]["issue_url"], 1104, "ISSUE"):
            errors.append("human_intent: issue-first source #1104 required")
        if not isinstance(record["human_intent"]["objective"], str) or not record["human_intent"]["objective"].strip():
            errors.append("human_intent: objective required")
    obs = record["observations"]
    ids: set[str] = set()
    if not isinstance(obs, list):
        errors.append("observations: expected list")
        obs = []
    for i, obj in enumerate(obs):
        p = f"observations[{i}]"
        if not require_keys(obj, OBS_KEYS, p, errors):
            continue
        oid = obj["id"]
        if not isinstance(oid, str) or not re.fullmatch(r"O-[A-Z0-9]{3,24}", oid) or oid in ids:
            errors.append(f"{p}: invalid/duplicate id")
        else:
            ids.add(oid)
        if not is_choice(obj["actor"], ACTORS):
            errors.append(f"{p}: unknown actor")
        if not isinstance(obj["claim"], str) or not obj["claim"].strip():
            errors.append(f"{p}: empty claim")
        if not is_choice(obj["epistemic_status"], STATUS):
            errors.append(f"{p}: unsupported epistemic state")
        if not is_choice(obj["review_state"], REVIEW):
            errors.append(f"{p}: unsupported review state")
        if obj["review_state"] == "INDEPENDENT_REVIEW_RECORDED" and obj["actor"] != "INDEPENDENT_REVIEWER":
            errors.append(f"{p}: self/agent report cannot claim independent review")
        ev = obj["evidence"]
        if not isinstance(ev, list):
            errors.append(f"{p}: evidence must be list")
        else:
            if obj["epistemic_status"] == "OBSERVED_SOURCE" and not ev:
                errors.append(f"{p}: source observation needs pinned evidence")
            for j, source in enumerate(ev):
                valid_evidence(source, sha, errors, f"{p}.evidence[{j}]")
    disputes = record["disagreements"]
    if not isinstance(disputes, list):
        errors.append("disagreements: expected list")
    else:
        for i, d in enumerate(disputes):
            p = f"disagreements[{i}]"
            if not require_keys(d, {"observation_ids", "status", "resolution_evidence"}, p, errors):
                continue
            links = d["observation_ids"]
            if not isinstance(links, list) or len(set(map(str, links))) < 2 or any(not isinstance(x, str) or x not in ids for x in links):
                errors.append(f"{p}: must link at least two distinct known observations")
            if not is_choice(d["status"], DISAGREEMENT):
                errors.append(f"{p}: bad status")
            ev = d["resolution_evidence"]
            if not isinstance(ev, list):
                errors.append(f"{p}: evidence must be list")
            else:
                if d["status"] == "RESOLVED_WITH_EVIDENCE" and not ev:
                    errors.append(f"{p}: resolved without evidence")
                for j, source in enumerate(ev):
                    valid_evidence(source, sha, errors, f"{p}.resolution_evidence[{j}]")
    human = record["human_learning"]
    if require_keys(human, {"status", "teach_back", "evidence", "human_confirmed"}, "human_learning", errors):
        if not is_choice(human["status"], UNDERSTANDING):
            errors.append("human_learning: invalid status")
        if human["status"] == "DEMONSTRATED" and (not human["human_confirmed"] or not human["teach_back"] or not human["evidence"]):
            errors.append("human_learning: demonstrated requires human confirmation, teach-back and pinned evidence")
        if human["status"] == "NOT_TESTED" and (human["teach_back"] is not None or human["human_confirmed"] is not False):
            errors.append("human_learning: NOT_TESTED cannot contain claimed teach-back")
        if not isinstance(human["evidence"], list):
            errors.append("human_learning: evidence must be list")
        else:
            for j, source in enumerate(human["evidence"]):
                valid_evidence(source, sha, errors, f"human_learning.evidence[{j}]")
    machine = record["machine_adaptation"]
    if not isinstance(machine, list):
        errors.append("machine_adaptation: expected list")
    else:
        for i, x in enumerate(machine):
            if not require_keys(x, {"proposal", "state", "outcome_verified"}, f"machine_adaptation[{i}]", errors):
                continue
            if not is_choice(x["state"], ADAPT) or not isinstance(x["proposal"], str):
                errors.append(f"machine_adaptation[{i}]: invalid proposal/state")
            if x["outcome_verified"] is not False:
                errors.append(f"machine_adaptation[{i}]: E0 cannot verify adaptive improvement")
    if record["governance"] != GOV:
        errors.append("governance: non-authorizing Z1 constants required")
    return errors


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate and inspect an offline mutual-learning E0 record")
    p.add_argument("record", type=Path, help="Local JSON record (never uploaded)")
    args = p.parse_args(argv)
    try:
        payload = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": ["cannot read valid JSON: " + str(exc)]}))
        return 2
    errors = validate(payload)
    report = {
        "valid": not errors,
        "errors": errors,
        "artifact": payload.get("artifact", {}).get("url") if isinstance(payload, dict) else None,
        "observations": len(payload.get("observations", [])) if isinstance(payload, dict) else 0,
        "human_learning": payload.get("human_learning", {}).get("status") if isinstance(payload, dict) else None,
        "authority_effect": "NONE",
        "writes_performed": 0,
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

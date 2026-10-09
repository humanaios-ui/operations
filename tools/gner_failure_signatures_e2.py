"""GNER-E2: conservative cross-run failure signature candidates (no authority).

Input must be independently established from GitHub workflow/job logs. This
offline pure function does not certify the authenticity of supplied evidence.
"""
from __future__ import annotations
import hashlib
import re
from collections import defaultdict

ALLOWED_REPO = "humanaios-ui/operations"
CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,80}$")
PATH = re.compile(r"^[a-zA-Z0-9_./-]{1,180}$")
SHA = re.compile(r"^[a-f0-9]{40}$")
# Deliberately avoid parsing arbitrary logs: caller extracts a bounded known diagnostic.
def signature(failure: dict) -> str | None:
    if not isinstance(failure, dict) or set(failure) != {"code", "test_path", "test_name"}:
        return None
    code, path, test = (failure.get(k) for k in ("code", "test_path", "test_name"))
    if not (isinstance(code, str) and CODE.fullmatch(code)
            and isinstance(path, str) and PATH.fullmatch(path)
            and isinstance(test, str) and PATH.fullmatch(test)):
        return None
    # A named diagnostic is stable across run ids, while avoiding free-text/log secrets.
    return hashlib.sha256((code + "\0" + path + "\0" + test).encode()).hexdigest()


def correlate(records: list) -> dict:
    if not isinstance(records, list) or len(records) > 100:
        raise ValueError("bounded record list required")
    groups: dict[str, list[dict]] = defaultdict(list)
    rejected = 0
    for record in records:
        if not isinstance(record, dict):
            rejected += 1
            continue
        if (record.get("repository") != ALLOWED_REPO
            or record.get("verification_state") != "CANONICAL_VERIFIED"
            or record.get("conclusion") != "failure"
            or type(record.get("run_id")) is not int or record["run_id"] <= 0
            or not isinstance(record.get("head_sha"), str)
            or not SHA.fullmatch(record["head_sha"])
            or not isinstance(record.get("workflow"), str)
            or not 0 < len(record["workflow"]) < 100):
            rejected += 1
            continue
        key = signature(record.get("failure"))
        if key is None:
            rejected += 1
            continue
        groups[key].append(record)
    output = []
    for key, group in sorted(groups.items()):
        distinct = {(r["run_id"], r["head_sha"]) for r in group}
        if len(distinct) < 2:
            continue
        ordered = sorted(distinct)
        output.append({"signature_sha256": key,
                       "diagnostic_code": group[0]["failure"]["code"],
                       "test_path": group[0]["failure"]["test_path"],
                       "test_name": group[0]["failure"]["test_name"],
                       "run_ids": sorted({r for r, _ in ordered}),
                       "distinct_run_head_pairs": len(ordered),
                       "state": "SHARED_FAILURE_SIGNATURE_CANDIDATE",
                       "root_cause_verified": False})
    return {"schema": "GNER-E2-v0.1", "groups": output, "rejected": rejected,
            "authority": "NONE", "execution": "DISABLED",
            "evidence_warning": "Caller-supplied metadata is not authenticated by this function. Matching diagnostic signatures are not proof of a shared root cause."}

"""MODE -> HumanAIOS E0 synthetic objective-trace consumer.

An offline causal/shape check, NOT a MODE runtime or RP signature verifier.
No file IO, external calls, action execution, or learning admission.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

SCHEMA = "humanaios.mode_interop.synthetic_trace.v0.1"
_ALLOWED_TOP = {"schema", "origin", "objective_id", "objective", "steps"}
_ALLOWED_STEP = {"ordinal", "action", "target", "state", "entries", "evidence_ref", "rp_receipt_ref"}
_ENTRY_KEYS = {"name", "kind"}
_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class TraceDenied(ValueError):
    """Unsafe, unsupported, or causally inconsistent supplied trace."""


def _strict_keys(record: object, allowed: set[str], required: set[str], label: str) -> dict:
    if not isinstance(record, dict) or set(record) - allowed or not required.issubset(record):
        raise TraceDenied(f"{label}: malformed or authority-bearing fields")
    return record


def _path(value: object) -> str:
    if value == ".":
        return "."
    if not isinstance(value, str) or len(value) > 256 or "\\" in value or value.startswith("/"):
        raise TraceDenied("invalid or non-relative target")
    parts = value.split("/")
    if not all(_SAFE_COMPONENT.fullmatch(x) and x not in {".", ".."} for x in parts):
        raise TraceDenied("unsafe target component")
    return "/".join(parts)


def _entries(value: object, parent: str) -> dict[str, str]:
    if not isinstance(value, list) or len(value) > 128:
        raise TraceDenied("invalid directory entries")
    children: dict[str, str] = {}
    for item in value:
        _strict_keys(item, _ENTRY_KEYS, _ENTRY_KEYS, "directory entry")
        name, kind = item["name"], item["kind"]
        if not isinstance(name, str) or not _SAFE_COMPONENT.fullmatch(name) or name in {".", ".."}:
            raise TraceDenied("invalid entry name")
        if not isinstance(kind, str) or kind not in {"DIRECTORY", "FILE"}:
            raise TraceDenied("unsupported entry kind (including symlinks)")
        full = name if parent == "." else parent + "/" + name
        if full in children:
            raise TraceDenied("duplicate directory entry")
        children[full] = kind
    return children


def assess_trace(trace: object) -> dict:
    """Check supplied synthetic trace linkage; never execute actions.

    Passing establishes structural consistency only, NOT directory truth,
    MODE objective completion, cryptographic authorization, or RP claim review.
    """
    _strict_keys(trace, _ALLOWED_TOP, _ALLOWED_TOP, "trace")
    if trace["schema"] != SCHEMA or trace["origin"] != "SYNTHETIC_TEST_ONLY":
        raise TraceDenied("only synthetic records permitted")
    if not isinstance(trace["objective_id"], str) or not _ID.fullmatch(trace["objective_id"]):
        raise TraceDenied("invalid objective ID")
    if not isinstance(trace["objective"], str) or not 0 < len(trace["objective"].strip()) <= 300:
        raise TraceDenied("invalid objective")
    steps = trace["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 8:
        raise TraceDenied("step budget exceeded or missing")

    observed: dict[str, str] = {".": "DIRECTORY"}
    accepted = []
    blocked = False
    for index, candidate in enumerate(steps, start=1):
        _strict_keys(candidate, _ALLOWED_STEP, _ALLOWED_STEP, "step")
        if type(candidate["ordinal"]) is not int or candidate["ordinal"] != index:
            raise TraceDenied("steps out of order")
        action = candidate["action"]
        target = _path(candidate["target"])
        state = candidate["state"]
        if blocked:
            raise TraceDenied("actions after a blocked step")
        if action == "LIST_DIRECTORY":
            if state != "REPORTED_OBSERVED" or observed.get(target) != "DIRECTORY":
                raise TraceDenied("directory action lacks prior directory evidence")
            ref = candidate["evidence_ref"]
            if not isinstance(ref, str) or not ref.startswith("synthetic:") or not _ID.fullmatch(ref):
                raise TraceDenied("missing or invalid synthetic observation reference")
            children = _entries(candidate["entries"], target)
            if target != "." and not accepted:
                raise TraceDenied("follow-up before initial observation")
            # Reject impossible type changes: a previously observed directory
            # cannot become a file while its children remain actionable.
            for full, kind in children.items():
                prior = observed.get(full)
                if prior is not None and prior != kind:
                    raise TraceDenied("contradictory observed entry kind")
            # Relisting replaces direct children. Drop any disappeared child's
            # subtree so a later READ_FILE cannot rely on stale observations.
            prefix = "" if target == "." else target + "/"
            for full in list(observed):
                if full == "." or not full.startswith(prefix):
                    continue
                suffix = full[len(prefix):]
                if "/" not in suffix and full not in children:
                    for stale in list(observed):
                        if stale == full or stale.startswith(full + "/"):
                            observed.pop(stale, None)
            observed.update(children)
        elif action == "READ_FILE":
            parts = target.split("/")
            parents = ["/".join(parts[:j]) for j in range(1, len(parts))]
            if any(observed.get(parent) != "DIRECTORY" for parent in parents):
                raise TraceDenied("file path lacks observed directory ancestry")
            if state != "BLOCKED_UNSUPPORTED" or observed.get(target) != "FILE":
                raise TraceDenied("unsupported file action must block on observed file")
            if candidate["entries"] != [] or candidate["evidence_ref"] is not None:
                raise TraceDenied("blocked action cannot claim observed content")
            blocked = True
        else:
            raise TraceDenied("unlisted action cannot be projected")
        rp_ref = candidate["rp_receipt_ref"]
        if rp_ref is not None and (not isinstance(rp_ref, str) or not _ID.fullmatch(rp_ref)):
            raise TraceDenied("malformed asserted RP receipt reference")
        accepted.append({"ordinal": index, "action": action, "target": target,
                         "result": state, "evidence_class": "SUPPLIED_UNVERIFIED",
                         "rp_authentication": "NOT_VERIFIED"})

    digest = sha256(json.dumps(trace, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schema": "humanaios.mode_interop.review_projection.v0.1",
        "trace_sha256": digest, "objective_id": trace["objective_id"],
        "step_count": len(accepted), "steps": accepted,
        "stop_state": "UNSUPPORTED_READ_FILE" if blocked else "INCOMPLETE_UNVERIFIED_TRACE",
        "structural_consistency": "PASSED_SYNTHETIC_CONTRACT_ONLY",
        "runtime_behavior_verified": False, "rp_action_signature_verified": False,
        "rp_claim_evaluation_verified": False, "objective_completed": False,
        "general_autonomy_qualified": False, "learning_admitted": False,
        "authority_effect": "NONE", "execution_effect": "NONE",
    }

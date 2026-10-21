"""Offline synthetic-only model-evidence view for #942 (Z1, no authority).

A pure projector over caller-supplied fixture dictionaries. This is NOT an
external benchmark adapter, Source of Truth database, winner/ranking engine,
participant recorder, or Coordinator admission mechanism.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from itertools import combinations

SCHEMA = "humanaios.model_evidence.synthetic.v0.1"
LENSES = frozenset(("PREFERENCE", "EXPERT", "CAPABILITY", "ECONOMICS", "USAGE", "ACAT"))
_TOP = frozenset(("schema", "observation_id", "subject", "origin", "method", "measurement", "authority_effect"))
_SUBJECT = frozenset(("system_id", "model_version", "scaffold_id"))
_ORIGIN = frozenset(("source_uri", "origin_key", "observed_at", "source_class", "visibility"))
_METHOD = frozenset(("lens", "metric_key", "protocol_id", "dataset_version", "harness_version", "task_scope"))
_MEASURE = frozenset(("value", "unit", "sample_size", "ci_lower", "ci_upper"))
_UNKNOWN = frozenset(("UNKNOWN", "UNAVAILABLE"))


def _is_unknown(value: str) -> bool:
    return value.strip().upper() in _UNKNOWN


def _finite_number(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _exact_fields(obj: object, keys: frozenset[str], label: str) -> dict:
    if not isinstance(obj, dict) or set(obj) != keys:
        raise ValueError(f"{label}: missing or unexpected fields")
    return obj


def _name(value: object, label: str) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > 160
            or any(ord(ch) < 32 for ch in value)):
        raise ValueError(f"{label}: invalid string")
    return value


def _time(value: object) -> datetime:
    text = _name(value, "observed_at")
    try:
        result = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("observed_at: invalid ISO timestamp") from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("observed_at: timezone required")
    return result.astimezone(timezone.utc)


def validate_observation(data: object) -> dict:
    """Validate a *synthetic* public fixture; no external source is trusted."""
    d = _exact_fields(data, _TOP, "observation")
    if d["schema"] != SCHEMA or d["authority_effect"] != "NONE":
        raise ValueError("schema or authority escalation not permitted")
    _name(d["observation_id"], "observation_id")

    s = _exact_fields(d["subject"], _SUBJECT, "subject")
    for key in _SUBJECT:
        if _is_unknown(_name(s[key], key)):
            raise ValueError("tested-system identity is unresolved")

    o = _exact_fields(d["origin"], _ORIGIN, "origin")
    for key in ("source_uri", "origin_key"):
        _name(o[key], key)
    if not o["source_uri"].startswith("synthetic://"):
        raise ValueError("offline projector accepts only synthetic sources")
    if o["source_class"] != "SIMULATED" or o["visibility"] != "PUBLIC_SYNTHETIC":
        raise ValueError("private, real or misleading origin is forbidden")
    _time(o["observed_at"])

    m = _exact_fields(d["method"], _METHOD, "method")
    if not isinstance(m["lens"], str) or m["lens"] not in LENSES:
        raise ValueError("unsupported comparison lens")
    for key in _METHOD - {"lens"}:
        _name(m[key], key)

    v = _exact_fields(d["measurement"], _MEASURE, "measurement")
    _name(v["unit"], "unit")
    value = v["value"]
    if value is not None and not _finite_number(value):
        raise ValueError("value must be finite number or explicit null")
    n = v["sample_size"]
    if n is not None and (type(n) is not int or n < 0):
        raise ValueError("sample_size must be nonnegative integer or null")
    lower, upper = v["ci_lower"], v["ci_upper"]
    if (lower is None) != (upper is None):
        raise ValueError("uncertainty bounds must both be present or both null")
    if lower is not None:
        if not all(_finite_number(k) for k in (lower, upper)):
            raise ValueError("confidence bounds must be finite")
        if not lower <= upper or (value is not None and not lower <= value <= upper):
            raise ValueError("inconsistent confidence bounds")
    return d


def comparison_eligibility(a: dict, b: dict) -> dict:
    """Eligibility for same-lens measurements, NOT a merit ordering."""
    a, b = validate_observation(a), validate_observation(b)
    ma, mb = a["method"], b["method"]
    va, vb = a["measurement"], b["measurement"]
    reasons = []
    for key in ("lens", "metric_key", "protocol_id", "dataset_version",
                "harness_version", "task_scope"):
        if ma[key] != mb[key] or _is_unknown(ma[key]) or _is_unknown(mb[key]):
            reasons.append("METHOD_MISMATCH_OR_UNKNOWN:" + key)
    if va["unit"] != vb["unit"] or _is_unknown(va["unit"]) or _is_unknown(vb["unit"]):
        reasons.append("UNIT_MISMATCH")
    if a["subject"]["system_id"] == b["subject"]["system_id"]:
        reasons.append("SAME_TESTED_SYSTEM")
    if va["value"] is None or vb["value"] is None:
        reasons.append("NOT_MEASURED")
    if va["sample_size"] is None or vb["sample_size"] is None:
        reasons.append("SAMPLE_SIZE_UNKNOWN")
    if ma["lens"] in ("PREFERENCE", "EXPERT"):
        if (va["sample_size"] is not None and va["sample_size"] < 30
                or vb["sample_size"] is not None and vb["sample_size"] < 30):
            reasons.append("UNDERPOWERED_ILLUSTRATIVE_THRESHOLD")
    if va["ci_lower"] is None or vb["ci_lower"] is None:
        reasons.append("UNCERTAINTY_UNKNOWN")
    return {
        "subject_ids": sorted((a["subject"]["system_id"], b["subject"]["system_id"])),
        "eligibility": "NOT_COMPARABLE" if reasons else "COMPARABLE",
        "reason_codes": sorted(set(reasons)),
        "independent_origin_count": len({a["origin"]["origin_key"], b["origin"]["origin_key"]}),
        "winner": None,
        "authority_effect": "NONE",
    }


def project_synthetic_observations(rows: list[dict], *, as_of: str) -> dict:
    """Stable, side-effect-free view; date is caller-supplied, not invented."""
    if not isinstance(rows, list) or len(rows) > 200:
        raise ValueError("synthetic batch must contain 0-200 observations")
    now = _time(as_of)
    normalized = [validate_observation(row) for row in rows]
    ids = [row["observation_id"] for row in normalized]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate observation ID")
    ordered = sorted(normalized, key=lambda x: x["observation_id"])
    evidence = []
    for row in ordered:
        origin = row["origin"]
        age_days = (now - _time(origin["observed_at"])).total_seconds() / 86400
        evidence.append({
            "observation_id": row["observation_id"],
            "tested_system": row["subject"]["system_id"],
            "model_version": row["subject"]["model_version"],
            "lens": row["method"]["lens"],
            "source_uri": origin["source_uri"],
            "origin_key": origin["origin_key"],
            "observed_at": origin["observed_at"],
            "freshness": "FUTURE_DATE_REVIEW" if age_days < 0 else (
                "STALE_FOR_REVIEW" if age_days > 30 else "WITHIN_30_DAYS"),
            "measurement": dict(row["measurement"]),
            "simulation": True,
        })
    pairs = [comparison_eligibility(a, b) for a, b in combinations(ordered, 2)]
    return {
        "schema": "humanaios.model_evidence_view.synthetic.v0.1",
        "scope": "OFFLINE_SYNTHETIC_ONLY",
        "as_of": as_of,
        "authority_effect": "NONE",
        "source_origin_count": len({x["origin"]["origin_key"] for x in ordered}),
        "observation_count": len(ordered),
        "observations": evidence,
        "comparisons": pairs,
        "ranking": None,
        "limitations": [
            "No external data or model calls; synthetic fixture only",
            "No authorization, human outcome, independent source verification or statistical winner",
            "Thirty-day freshness flag is illustrative, not a source-specific operational SLA",
            "N<30 threshold illustrates abstention, not preregistered study power",
        ],
    }

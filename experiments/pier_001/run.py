"""PIER-001: offline, fixed synthetic privacy-reconstruction instrument.

No model, account, network, telemetry, or real personal data is used.
Python 3.11+. Usage: python3 experiments/pier_001/run.py
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from typing import Any

EXPERIMENT = "PIER-001"
FIXTURE_TYPE = "SYNTHETIC_TEST_ONLY"
STAGES = (0, 1, 3, 6)
CASE_COUNT = 30
ROLE_CLUES = {
    "fabrication": ("lathe", "caliper"),
    "ecology": ("seedlings", "mulch"),
    "mapping": ("contours", "compass"),
}
ROLE_NAMES = tuple(ROLE_CLUES)
ALIAS_RE = re.compile(r"(?<!\w)@pierpilot\d{2}\b")
EMAIL_RE = re.compile(r"(?<!\w)case-\d{2}@example\.invalid\b")


def synthetic_fixture() -> dict[str, Any]:
    """Construct fixed, invented people; no human records or external sources."""
    people = []
    directory = {}
    for i in range(CASE_COUNT):
        person_id = f"SYN-{i:02d}"
        role = ROLE_NAMES[i % len(ROLE_NAMES)]
        alias = f"pierpilot{i:02d}"
        email = f"case-{i:02d}@example.invalid"
        first, second = ROLE_CLUES[role]
        public_profile = f"PUB-{(i * 7 + 3) % CASE_COUNT:02d}"
        directory[alias] = public_profile
        lines = [
            "I keep notes for a small project.",
            f"I post short notes under @{alias}.",
            f"Today I checked {first} readings." if i < 20 else "Today I checked project readings.",
            "I file my drafts by week.",
            f"My test contact is {email}. I reviewed {second} results.",
            "I prefer clear logs and small batches.",
        ]
        messages = [{"id": f"m{j+1}", "text": line} for j, line in enumerate(lines)]
        people.append({
            "case_id": person_id,
            "truth": {"role": role, "alias": alias, "email": email,
                      "public_profile": public_profile},
            "messages": messages,
        })
    return {"experiment": EXPERIMENT, "fixture_type": FIXTURE_TYPE,
            "cases": people, "synthetic_public_directory": directory}


def validate_fixture(fixture: dict[str, Any]) -> None:
    if not isinstance(fixture, dict) or set(fixture) != {
        "experiment", "fixture_type", "cases", "synthetic_public_directory"
    } or fixture["experiment"] != EXPERIMENT or fixture["fixture_type"] != FIXTURE_TYPE:
        raise ValueError("Only PIER-001 synthetic fixtures permitted")
    cases = fixture["cases"]
    directory = fixture["synthetic_public_directory"]
    if not isinstance(cases, list) or len(cases) != CASE_COUNT or not isinstance(directory, dict):
        raise ValueError("Invalid synthetic cohort")
    ids = set()
    aliases = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"case_id", "truth", "messages"}:
            raise ValueError("Invalid case structure")
        cid, truth, messages = case["case_id"], case["truth"], case["messages"]
        if not isinstance(cid, str) or not re.fullmatch(r"SYN-\d{2}", cid) or cid in ids:
            raise ValueError("Duplicate or invalid case ID")
        ids.add(cid)
        if not isinstance(truth, dict) or set(truth) != {"role", "alias", "email", "public_profile"}:
            raise ValueError("Invalid ground truth")
        role, alias, email = truth["role"], truth["alias"], truth["email"]
        if role not in ROLE_NAMES or not isinstance(alias, str) or not re.fullmatch(r"pierpilot\d{2}", alias) or alias in aliases:
            raise ValueError("Invalid synthetic role or alias")
        aliases.add(alias)
        if email != f"case-{cid[-2:]}@example.invalid" or directory.get(alias) != truth["public_profile"] or not re.fullmatch(r"PUB-\d{2}", truth["public_profile"]):
            raise ValueError("Synthetic identifier mismatch")
        if not isinstance(messages, list) or len(messages) != 6:
            raise ValueError("Expected 6 synthetic messages")
        for n, message in enumerate(messages, 1):
            if not isinstance(message, dict) or set(message) != {"id", "text"} or message["id"] != f"m{n}":
                raise ValueError("Invalid source record")
            if not isinstance(message["text"], str) or len(message["text"]) > 200:
                raise ValueError("Invalid source text")
        # Fixture validation is also a privacy boundary. Never accept non-test addresses.
        entire = " ".join(m["text"] for m in messages)
        for found in re.findall(r"[\w.+-]+@[\w.-]+", entire):
            if not found.rstrip(".").endswith("@example.invalid"):
                raise ValueError("Non-synthetic address in fixture")
    if len(directory) != CASE_COUNT or set(directory) != aliases:
        raise ValueError("Invalid synthetic public directory")
    # A label saying SYNTHETIC is not proof. Reject any altered or user-supplied text.
    if fixture != synthetic_fixture():
        raise ValueError("Only the fixed built-in synthetic corpus is allowed")


def public_view(fixture: dict[str, Any], case: dict[str, Any], stage: int) -> dict[str, Any]:
    """Give the toy attacker only permitted observations, NEVER ground truth."""
    if stage not in STAGES:
        raise ValueError("Unknown observation stage")
    # Never send the scorer's case ID or hidden labels to an attacker.
    # In the initial version SYN-00 exposed the label via index % 3.
    return {"observations": [m.copy() for m in case["messages"][:stage]],
            "synthetic_public_directory": fixture["synthetic_public_directory"].copy()}


def toy_attacker(view: dict[str, Any]) -> dict[str, Any]:
    """A simple specified rule baseline; not an LLM or realistic adversary."""
    observations = view["observations"]
    role_hits: dict[str, list[str]] = {}
    for role, clues in ROLE_CLUES.items():
        hits = [message["id"] for message in observations
                if any(re.search(r"\b" + re.escape(clue) + r"\b", message["text"].lower())
                       for clue in clues)]
        if hits:
            role_hits[role] = hits
    role = None
    role_evidence = []
    role_confidence = None
    if len(role_hits) == 1:
        role, role_evidence = next(iter(role_hits.items()))
        role_confidence = 0.95 if len(role_evidence) > 1 else 0.85

    alias, alias_evidence = None, []
    email, email_evidence = None, []
    for message in observations:
        if alias is None and (match := ALIAS_RE.search(message["text"])):
            alias, alias_evidence = match.group()[1:], [message["id"]]
        if email is None and (match := EMAIL_RE.search(message["text"])):
            email, email_evidence = match.group(), [message["id"]]
    directory = view["synthetic_public_directory"]
    linked_case_id = directory.get(alias) if alias is not None else None
    return {"role": role,
            "role_confidence": role_confidence, "role_evidence": role_evidence,
            "alias": alias, "alias_evidence": alias_evidence,
            "email": email, "email_evidence": email_evidence,
            "linked_case_id": linked_case_id, "link_evidence": alias_evidence if linked_case_id else []}


def predict_case(fixture: dict[str, Any], case: dict[str, Any], stage: int) -> dict[str, Any]:
    """Trusted harness attaches correlation ID AFTER the attacker returns claims."""
    return {"case_id": case["case_id"], **toy_attacker(public_view(fixture, case, stage))}


def wilson_interval(success: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    """Descriptive Wilson interval: synthetic fixed cohort, NOT population inference."""
    if total == 0:
        return None
    p = success / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    spread = (z / denominator)*math.sqrt(p*(1-p)/total + z*z/(4*total*total))
    return [round(max(0, center-spread), 4), round(min(1, center+spread), 4)]


def _supported(field: str, value: Any, refs: Any, source: dict[str, str], directory: dict[str, str]) -> bool:
    """Every cited message must substantively support the exact claim.

    This is lexical evidence, not independent verification or entailment.
    """
    if (not isinstance(refs, list) or not refs or len(refs) > 6
            or any(not isinstance(x, str) or x not in source for x in refs)
            or len(set(refs)) != len(refs)):
        return False
    for msg in refs:
        line = source[msg]
        if field == "role":
            if value not in ROLE_CLUES or not any(
                re.search(r"\b" + re.escape(clue) + r"\b", line.lower())
                for clue in ROLE_CLUES[value]
            ):
                return False
        elif field == "alias":
            if not any(found.group()[1:] == value for found in ALIAS_RE.finditer(line)):
                return False
        elif field == "email":
            if not any(found.group() == value for found in EMAIL_RE.finditer(line)):
                return False
        elif field == "linked_case_id":
            if not any(directory.get(found.group()[1:]) == value
                       for found in ALIAS_RE.finditer(line)):
                return False
        else:
            return False
    return True


def score(fixture: dict[str, Any], stage: int, predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """Score declared claims against hidden synthetic truth; emit ONLY aggregates."""
    validate_fixture(fixture)
    if stage not in STAGES or not isinstance(predictions, list) or len(predictions) != CASE_COUNT:
        raise ValueError("Expected one prediction per synthetic case")
    expected_keys = {"case_id", "role", "role_confidence", "role_evidence",
                     "alias", "alias_evidence", "email", "email_evidence",
                     "linked_case_id", "link_evidence"}
    indexed = {}
    for prediction in predictions:
        if not isinstance(prediction, dict) or set(prediction) != expected_keys:
            raise ValueError("Invalid prediction shape")
        cid = prediction["case_id"]
        if cid in indexed:
            raise ValueError("Duplicate prediction")
        indexed[cid] = prediction
    if set(indexed) != {c["case_id"] for c in fixture["cases"]}:
        raise ValueError("Missing or unknown synthetic case")

    fields = {f: Counter(claimed=0, correct=0, supported=0) for f in ("role", "alias", "email", "linked_case_id")}
    brier_terms = []
    unsupported = 0
    for case in fixture["cases"]:
        prediction = indexed[case["case_id"]]
        observable = case["messages"][:stage]
        source = {record["id"]: record["text"] for record in observable}
        directory = fixture["synthetic_public_directory"]
        for field, evidence_field, truth in (
            ("role", "role_evidence", case["truth"]["role"]),
            ("alias", "alias_evidence", case["truth"]["alias"]),
            ("email", "email_evidence", case["truth"]["email"]),
            ("linked_case_id", "link_evidence", case["truth"]["public_profile"]),
        ):
            value = prediction[field]
            refs = prediction[evidence_field]
            if value is None:
                if refs or (field == "role" and prediction["role_confidence"] is not None):
                    raise ValueError("Abstention must not contain evidence or confidence")
                continue
            if not isinstance(value, str):
                raise ValueError("Claims must be strings or null")
            fields[field]["claimed"] += 1
            correct = value == truth
            fields[field]["correct"] += int(correct)
            supported = _supported(field, value, refs, source, directory)
            fields[field]["supported"] += int(supported)
            unsupported += int(not supported)
            if field == "role":
                c = prediction["role_confidence"]
                if not isinstance(c, (int, float)) or isinstance(c, bool) or not math.isfinite(c) or not 0 <= c <= 1:
                    raise ValueError("Invalid role confidence")
                brier_terms.append((c - int(correct)) ** 2)
        # The claims are independent, but an unattested role must never silently pass.
    outcomes = {}
    for field, count in fields.items():
        outcomes[field] = {
            "claims": count["claimed"], "correct": count["correct"],
            "supported_by_visible_evidence": count["supported"],
            "coverage": round(count["claimed"] / CASE_COUNT, 4),
            "accuracy_all_cases": round(count["correct"] / CASE_COUNT, 4),
            "precision_when_claimed": round(count["correct"] / count["claimed"], 4) if count["claimed"] else None,
            "descriptive_wilson_95_accuracy": wilson_interval(count["correct"], CASE_COUNT),
        }
    return {"n": CASE_COUNT, "stage_messages": stage, "metrics": outcomes,
            "unsupported_claims": unsupported,
            "brier_role_when_claimed": round(sum(brier_terms)/len(brier_terms), 4) if brier_terms else None}


def run() -> dict[str, Any]:
    fixture = synthetic_fixture()
    validate_fixture(fixture)
    outcomes = []
    for stage in STAGES:
        predictions = [predict_case(fixture, c, stage) for c in fixture["cases"]]
        outcomes.append(score(fixture, stage, predictions))
    report = {
        "experiment_id": EXPERIMENT,
        "state": "OBSERVED_SYNTHETIC_INSTRUMENT_SMOKE_TEST",
        "scope": "fixed invented cohort; rule attacker; no LLM inference benchmark",
        "authority": "NONE", "execution": "DISABLED",
        "declared_calls": {"model": 0, "network": 0, "external_data": 0},
        "cohort": {"size": CASE_COUNT, "role_counts": dict(Counter(c["truth"]["role"] for c in fixture["cases"])),
                   "chance_majority_role_accuracy": round(max(Counter(c["truth"]["role"] for c in fixture["cases"]).values())/CASE_COUNT,4)},
        "declared_smoke_gates": {
            "gate_1": "no inferred roles with 0 or 1 messages",
            "gate_2": "role accuracy (all cases) stage3 > stage1; stage6 >= stage3",
            "gate_3": "zero unsupported claims, zero external calls",
        },
        "results": outcomes,
        "limits": ["Constructed clues force expected improvement; no evidence about real users or models.",
                   "Fixed corpus and attacker rules are open source; this is not a blinded holdout.",
                   "Declared no-call counts are static metadata, not independent network monitoring.",
                   "Wilson intervals describe fixture counts, not real-world population uncertainty.",
                   "Evidence support is not independent truth verification.",
                   "Linkage uses a fully invented public directory, not external searches."],
        "fixture_sha256": hashlib.sha256(json.dumps(fixture, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }
    stages = {x["stage_messages"]: x for x in outcomes}
    report["smoke_gates_pass"] = (
        stages[0]["metrics"]["role"]["claims"] == 0
        and stages[1]["metrics"]["role"]["claims"] == 0
        and stages[3]["metrics"]["role"]["accuracy_all_cases"] > stages[1]["metrics"]["role"]["accuracy_all_cases"]
        and stages[6]["metrics"]["role"]["accuracy_all_cases"] >= stages[3]["metrics"]["role"]["accuracy_all_cases"]
        and all(x["unsupported_claims"] == 0 for x in outcomes)
    )
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
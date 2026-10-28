#!/usr/bin/env python3
"""Builder v1.7 compliant

Validates a public-safe HumanAIOS CRM evidence snapshot.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path

TOOL_NAME = "crm_baseline"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_ZONE = 1
SCHEMA = "humanaios.crm.baseline.v0.1"
REPO = "humanaios-ui/operations"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
ID = re.compile(r"^CRM-[0-9]{3}$")
SAFE_PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
ROOT_KEYS = {"schema_version", "snapshot_date", "repository", "base_commit", "authority_effect", "execution", "ratification", "scope", "records"}
ROW_KEYS = {"id", "label", "kind", "historical_state", "historical_as_of", "current_state", "evidence_state", "sources", "next_review"}
PIN_KEYS = {"path", "blob_sha", "url", "supports"}
CURRENT_STATES = {"NEEDS_REVALIDATION", "NEEDS_PRIVATE_REVALIDATION", "UNVERIFIED_PROSPECT"}
EVIDENCE_STATES = {"OBSERVED", "SUPPORTED", "INFERRED", "HYPOTHESIZED", "UNVERIFIED", "CONTRADICTED"}
FORBIDDEN_KEYS = {"email", "phone", "address", "contact", "secret", "token", "contract_value", "terms", "commission"}
EMAIL = re.compile("@")  # Do not accept contact addresses in a public baseline

class BaselineError(ValueError):
    """Invalid or untrusted CRM baseline."""


def _keys(obj: object, expected: set[str], where: str) -> None:
    if not isinstance(obj, dict) or set(obj) != expected:
        raise BaselineError(f"{where}: unexpected or missing fields")


def _date(value: object, where: str) -> None:
    if not isinstance(value, str):
        raise BaselineError(f"{where}: expected ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise BaselineError(f"{where}: invalid ISO date") from exc


def validate_baseline(doc: object) -> dict:
    """Validate field bounds, provenance pins and non-authoritative states."""
    _keys(doc, ROOT_KEYS, "baseline")
    if doc["schema_version"] != SCHEMA or doc["repository"] != REPO:
        raise BaselineError("schema or repository mismatch")
    if doc["authority_effect"] != "NONE" or doc["execution"] != "DISABLED":
        raise BaselineError("CRM baseline records cannot grant authority or execution")
    if doc["ratification"] != "Z1_PROPOSAL_NOT_RATIFIED":
        raise BaselineError("baseline cannot claim human approval")
    if not HEX40.fullmatch(str(doc["base_commit"])):
        raise BaselineError("base_commit must be exact SHA")
    _date(doc["snapshot_date"], "snapshot_date")
    if not isinstance(doc["scope"], str) or not doc["scope"]:
        raise BaselineError("missing scope")
    rows = doc["records"]
    if not isinstance(rows, list) or not rows or len(rows) > 200:
        raise BaselineError("invalid record count")
    seen = set()
    for row in rows:
        _keys(row, ROW_KEYS, "record")
        ident = row["id"]
        if not isinstance(ident, str) or not ID.fullmatch(ident) or ident in seen:
            raise BaselineError("invalid or duplicate CRM ID")
        seen.add(ident)
        if row["current_state"] not in CURRENT_STATES or row["evidence_state"] not in EVIDENCE_STATES:
            raise BaselineError(f"{ident}: unknown evidence/current state")
        _date(row["historical_as_of"], f"{ident}.historical_as_of")
        if row["historical_as_of"] > doc["snapshot_date"]:
            raise BaselineError(f"{ident}: historical date is after snapshot")
        for key in ("label", "kind", "historical_state", "next_review"):
            value = row[key]
            if not isinstance(value, str) or not value.strip() or EMAIL.search(value):
                raise BaselineError(f"{ident}: invalid or private field {key}")
        pins = row["sources"]
        if not isinstance(pins, list) or not pins or len(pins) > 12:
            raise BaselineError(f"{ident}: source required")
        for p in pins:
            _keys(p, PIN_KEYS, "source")
            path = p["path"]
            if not isinstance(path, str) or not SAFE_PATH.fullmatch(path) or ".." in path.split("/"):
                raise BaselineError(f"{ident}: invalid source path")
            if not HEX40.fullmatch(str(p["blob_sha"])):
                raise BaselineError(f"{ident}: missing exact blob SHA")
            expected_url = f"https://github.com/{REPO}/blob/{doc['base_commit']}/{path}"
            if p["url"] != expected_url:
                raise BaselineError(f"{ident}: source URL not pinned to base commit")
            if not isinstance(p["supports"], str) or not p["supports"] or EMAIL.search(p["supports"]):
                raise BaselineError(f"{ident}: missing or private claim")
    # A public baseline is an observation cache, not an authenticated CRM or contact store.
    if FORBIDDEN_KEYS.intersection(json.dumps(doc).lower().split('"')):
        raise BaselineError("private data keys are forbidden")
    return doc


def load_baseline(path: str | Path) -> dict:
    try:
        return validate_baseline(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineError(f"cannot load CRM baseline: {exc}") from exc


def verify_local_pins(doc: dict, repo_root: str | Path) -> None:
    """Optional independent source path/blob comparison against local git history."""
    root = str(repo_root)
    for row in doc["records"]:
        for source in row["sources"]:
            ref = f"{doc['base_commit']}:{source['path']}"
            try:
                completed = subprocess.run(
                    ["git", "-C", root, "rev-parse", "--verify", ref],
                    check=True, capture_output=True, text=True, timeout=10,
                )
            except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise BaselineError(f"source unavailable in local git: {ref}") from exc
            if completed.stdout.strip() != source["blob_sha"]:
                raise BaselineError(f"source blob differs: {ref}")


def summary(doc: dict) -> dict:
    return {
        "source_commit": doc["base_commit"],
        "count": len(doc["records"]),
        "status": doc["ratification"],
        "authority_effect": "NONE",
        "execution": "DISABLED",
        "records": [
            {"id": row["id"], "label": row["label"],
             "current_state": row["current_state"], "evidence_state": row["evidence_state"],
             "source_urls": [s["url"] for s in row["sources"]],
             "next_review": row["next_review"]}
            for row in doc["records"]
        ],
    }


def run_smoke_test() -> bool:
    """Exercise the frozen, source-pinned baseline without external actions."""
    baseline = Path(__file__).resolve().parents[1] / "collaborator-ops/crm/baseline-2026-10-28.json"
    try:
        document = load_baseline(baseline)
        return len(document["records"]) == 7 and summary(document)["authority_effect"] == "NONE"
    except BaselineError:
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", nargs="?", help="source-pinned CRM baseline JSON")
    parser.add_argument("--verify-local-git", action="store_true",
                        help="verify each pinned blob against local git object")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--smoke-test", action="store_true", help="validate frozen baseline")
    args = parser.parse_args()
    if args.smoke_test:
        parser.exit(0 if run_smoke_test() else 1)
    if not args.baseline:
        parser.error("baseline is required unless --smoke-test")
    try:
        doc = load_baseline(args.baseline)
        if args.verify_local_git:
            verify_local_pins(doc, args.repo_root)
    except BaselineError as exc:
        parser.exit(2, f"CRM_BASELINE_INVALID: {exc}\\n")
    print(json.dumps(summary(doc), indent=2))


if __name__ == "__main__":
    main()

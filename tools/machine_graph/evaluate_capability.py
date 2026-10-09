#!/usr/bin/env python3
"""Evaluate bounded local capabilities from a Machine Substrate Graph snapshot.

Current capability:
  canonical-shacl-validation

The evaluator is evidence-driven: it reads the graph snapshot and an optional
local validation receipt. It does not use conversational memory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SATISFIED = "SATISFIED"
UNSATISFIED = "UNSATISFIED"
UNVERIFIED = "UNVERIFIED"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_nodes(graph: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return [n for n in graph.get("nodes", []) if n.get("type") == node_type]


def python_env_evidence(graph: dict[str, Any]) -> dict[str, Any]:
    envs = find_nodes(graph, "PythonEnvironment")
    matches = []
    for n in envs:
        obs = n.get("observed", {})
        if n.get("state") == "OBSERVED_AVAILABLE" and obs.get("pyshacl_present") is True:
            matches.append({
                "node_id": n.get("id"),
                "path": obs.get("path"),
                "python": obs.get("python"),
                "pyshacl_present": True,
            })
    return {
        "state": SATISFIED if matches else UNSATISFIED,
        "matches": matches,
    }


def repository_evidence(graph: dict[str, Any]) -> dict[str, Any]:
    repos = find_nodes(graph, "LocalRepository")
    matches = []
    for n in repos:
        obs = n.get("observed", {})
        path = str(obs.get("path", ""))
        if n.get("state") == "OBSERVED_AVAILABLE" and (
            path.endswith("/operations-pr594")
            or path.endswith("/operations")
            or "operations" in Path(path).name.lower()
        ):
            matches.append({
                "node_id": n.get("id"),
                "path": path,
                "branch": obs.get("branch"),
                "working_tree_dirty": obs.get("working_tree_dirty"),
            })
    return {
        "state": SATISFIED if matches else UNVERIFIED,
        "matches": matches,
    }


def receipt_evidence(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "state": UNVERIFIED,
            "reason": "no validation receipt supplied",
        }
    if not path.exists():
        return {
            "state": UNSATISFIED,
            "reason": "validation receipt path does not exist",
            "path": str(path),
        }

    text = path.read_text(encoding="utf-8", errors="replace")
    required_markers = [
        "PASS reference-valid: conforms=True expected=True",
        "PASS reference-invalid: conforms=False expected=False",
        "Validation stage passed: all fixture expectations matched.",
    ]
    found = {m: (m in text) for m in required_markers}
    ok = all(found.values()) and path.stat().st_size > 0
    return {
        "state": SATISFIED if ok else UNSATISFIED,
        "path": str(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "markers": found,
    }


def evaluate(graph: dict[str, Any], receipt: Path | None) -> dict[str, Any]:
    runtime = python_env_evidence(graph)
    repository = repository_evidence(graph)
    validation_receipt = receipt_evidence(receipt)

    components = {
        "pyshacl_runtime": runtime,
        "repository": repository,
        "canonical_validation_receipt": validation_receipt,
    }

    states = [v["state"] for v in components.values()]
    if all(s == SATISFIED for s in states):
        overall = SATISFIED
    elif UNSATISFIED in states:
        overall = UNSATISFIED
    else:
        overall = UNVERIFIED

    return {
        "capability": "canonical-shacl-validation",
        "state": overall,
        "authorization": "NONE",
        "can_authorize_external_action": False,
        "evidence": components,
        "boundary": (
            "This result establishes observed local execution capability only. "
            "It does not authorize repository mutation, network access, installation, "
            "or any other external action."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True, help="Machine substrate JSON snapshot")
    ap.add_argument("--validation-receipt", help="Canonical SHACL validation output receipt")
    ap.add_argument("--output", help="Optional JSON capability receipt output")
    args = ap.parse_args()

    graph_path = Path(args.graph).expanduser()
    receipt = Path(args.validation_receipt).expanduser() if args.validation_receipt else None

    result = evaluate(load_json(graph_path), receipt)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"

    print(payload, end="")

    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        out.with_suffix(out.suffix + ".sha256").write_text(
            f"{digest}  {out.name}\n",
            encoding="utf-8",
        )

    return 0 if result["state"] == SATISFIED else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate HumanAIOS calibration evidence-graph reference fixtures.
Builder v1.7 compliant · validation_tool
HumanAIOS · #595

Usage:
  python3 tools/calibration_graph/validate_graph.py
  python3 tools/calibration_graph/validate_graph.py --smoke-test
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TOOL_NAME = "calibration_graph_validate"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "#595"
TOOL_ZONE = 1

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/calibration_graph/validation-manifest.json"


def _load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def _structural_preflight(manifest: dict) -> list[str]:
    """Check the manifest's referenced files exist, without needing pyshacl installed."""
    errors: list[str] = []
    for key in ("shapes", "ontology"):
        path = ROOT / manifest["validator"][key]
        if not path.is_file():
            errors.append(f"missing {key} file: {path}")
    for case in manifest["cases"]:
        path = ROOT / case["data"]
        if not path.is_file():
            errors.append(f"missing fixture for {case['id']}: {path}")
    return errors


def main() -> int:
    manifest = _load_manifest()
    preflight_errors = _structural_preflight(manifest)
    if preflight_errors:
        print("Structural preflight failed:")
        for err in preflight_errors:
            print(f"- {err}")
        return 1

    from pyshacl import validate

    shapes = ROOT / manifest["validator"]["shapes"]
    ontology = ROOT / manifest["validator"]["ontology"]

    failed = 0
    for case in manifest["cases"]:
        data = ROOT / case["data"]
        conforms, report_graph, report_text = validate(
            data_graph=str(data),
            shacl_graph=str(shapes),
            ont_graph=str(ontology),
            data_graph_format="turtle",
            shacl_graph_format="turtle",
            ont_graph_format="turtle",
            inference="rdfs",
            abort_on_first=False,
            allow_infos=True,
            allow_warnings=True,
        )
        expected = bool(case["expected_conforms"])
        status = "PASS" if bool(conforms) == expected else "FAIL"
        print(f"{status} {case['id']}: conforms={bool(conforms)} expected={expected}")
        if status == "FAIL":
            failed += 1
            print(report_text)

    if failed:
        print(f"Validation stage failed: {failed} fixture expectation(s) mismatched.")
        return 1

    print("Validation stage passed: all fixture expectations matched.")
    return 0


def smoke_test() -> int:
    """Exercises manifest loading and structural preflight without requiring pyshacl
    to be installed, since canonical PySHACL execution needs dependency-capable CI
    this tool does not assume it is running under (see tests/calibration_graph/README.md).
    """
    manifest = _load_manifest()
    assert _structural_preflight(manifest) == [], "reference manifest/fixtures must resolve on disk"

    broken = {"validator": {"shapes": "does/not/exist.ttl", "ontology": "docs/design/calibration-evidence-graph.ttl"}, "cases": []}
    errors = _structural_preflight(broken)
    assert len(errors) == 1 and "missing shapes file" in errors[0]

    try:
        import pyshacl  # noqa: F401
    except ImportError:
        print("smoke-test OK — manifest/preflight logic verified; pyshacl not installed, so the end-to-end SHACL run is skipped by design.")
        return 0

    return main()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke-test", action="store_true", help="Run the self-test and exit.")
    args = ap.parse_args()
    raise SystemExit(smoke_test() if args.smoke_test else main())

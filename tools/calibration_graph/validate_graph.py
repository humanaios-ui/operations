#!/usr/bin/env python3
"""Validate HumanAIOS calibration evidence-graph reference fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pyshacl import validate

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/calibration_graph/validation-manifest.json"


def main() -> int:
    manifest = json.loads(MANIFEST.read_text())
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


if __name__ == "__main__":
    raise SystemExit(main())

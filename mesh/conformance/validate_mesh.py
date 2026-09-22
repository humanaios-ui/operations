#!/usr/bin/env python3
"""Validate the local mesh practice records against practice_local.schema.json.

P19 — detection beats compliance. This module does not assert that the schema
constrains anything; it demonstrates it, by running negative cases that MUST be
rejected alongside the positive cases that must pass. A schema whose
`additionalProperties: false` failed open would pass the positive cases and be
caught only here.

Placement note (stated rather than left to be noticed): this file sits under
`mesh/` and not `tools/`, so it is outside the paths that trigger
`builder-lint.yml` and `tool-manifest.yml`. That is deliberate — the whole
`mesh/` layer is unratified Z1 scaffolding and registering it in the canonical
tool manifest would imply standing it does not have. Builder v1.7 markers are
carried anyway. Promotion to `tools/` is the Z2 call recorded as D4 in
MESH_LOCAL_CHARTER_V0_1.md.

Usage:
    python3 mesh/conformance/validate_mesh.py
    python3 mesh/conformance/validate_mesh.py --smoke-test
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - reported, not worked around
    print("jsonschema is not installed; install it before running this validator")
    sys.exit(2)

import yaml  # noqa: E402  - only for the exception type; parsing goes through strict_yaml

# yaml.safe_load silently keeps the LAST of a repeated mapping key, so a record
# carrying `authority:` twice would have the first copy discarded before the
# schema saw anything — the schema-hardening claim would hold on a document the
# validator never really read. The repository already ships a loader that
# refuses duplicates, for this exact defect; reuse it rather than re-implement.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".doc-control"))
from strict_yaml import loads as strict_loads  # noqa: E402

TOOL_NAME = "validate_mesh"
TOOL_VERSION = "0.1.0"

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "practice_local.schema.json"
PRACTICES = ROOT / "practices"


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def records() -> list[tuple[Path, dict]]:
    return [(p, strict_loads(p.read_text())) for p in sorted(PRACTICES.glob("*/practice.yaml"))]


def validate_positive(schema: dict) -> list[str]:
    """Every record on disk must validate. Returns failure strings."""
    failures = []
    for path, doc in records():
        try:
            jsonschema.validate(doc, schema)
            print(f"  PASS  {path.relative_to(ROOT.parent)}")
        except jsonschema.ValidationError as exc:
            failures.append(f"{path}: {exc.message} at {list(exc.absolute_path)}")
            print(f"  FAIL  {path.relative_to(ROOT.parent)}: {exc.message}")
    return failures


# Each case mutates a valid record into one the schema must refuse. The name is
# the control being demonstrated; falsifier 4 in the charter is case 1.
NEGATIVE_CASES = (
    ("additionalProperties: false rejects an undeclared key",
     lambda d: d.update({"smuggled_authority": "z2"}) or d),
    ("authority.grants_authority cannot be set true",
     lambda d: d["authority"].update({"grants_authority": True}) or d),
    ("resolution.class is a closed vocabulary",
     lambda d: d["resolution"].update({"class": "RESOLVED_BY_CONVENTION"}) or d),
    ("a record cannot drop its falsifier",
     lambda d: d.pop("falsifier") and d or d),
    ("purpose_filter is a closed vocabulary (P5)",
     lambda d: d.update({"purpose_filter": ["looks_useful"]}) or d),
    ("provenance.pinned_sha must be a 40-hex sha",
     lambda d: d["provenance"].update({"pinned_sha": "HEAD"}) or d),
    ("temporal_class cannot be an internal work deadline",
     lambda d: d["provenance"].update({"temporal_class": "INTERNAL_WORK_DEADLINE"}) or d),
    ("edges relation is a closed vocabulary",
     lambda d: d["edges"][0].update({"relation": "supersedes_z2"}) or d),
    ("a record cannot drop its graph edges (P-GRAPH)",
     lambda d: d.pop("edges") and d or d),
    ("a record cannot drop its implementation state (P-T10)",
     lambda d: d.pop("trl_framing") and d or d),
    ("status RATIFIED cannot be claimed without a Z2 signature",
     lambda d: d.update({"status": "RATIFIED"}) or d),
    ("status RATIFIED cannot be claimed on a non-sha256 signature",
     lambda d: (d.update({"status": "RATIFIED"}),
                d["authority"].update({"z2_ratification": "ratified-by-night"}))[-1] or d),
    ("an unratified record cannot carry a Z2 signature",
     lambda d: d["authority"].update({"z2_ratification": "a" * 64}) or d),
)


DUPLICATE_KEY_FIXTURE = """
practice_id: humanaios
authority:
  grants_authority: false
authority:
  grants_authority: true
"""


def validate_loader() -> list[str]:
    """The parser must refuse a duplicate mapping key, not silently keep the last."""
    failures = []
    try:
        strict_loads(DUPLICATE_KEY_FIXTURE)
        failures.append(
            "duplicate mapping key accepted by the loader — a repeated authority "
            "block would reach the schema with only its last copy")
        print("  FAIL  duplicate mapping key — accepted")
    except yaml.YAMLError:
        print("  PASS  duplicate mapping key — refused before the schema sees it")
    return failures


def validate_negative(schema: dict) -> list[str]:
    """Every mutation must be refused. A mutation that validates is a failure."""
    failures = []
    _, base = records()[0]
    for name, mutate in NEGATIVE_CASES:
        candidate = mutate(copy.deepcopy(base))
        try:
            jsonschema.validate(candidate, schema)
            failures.append(f"negative case validated when it must not: {name}")
            print(f"  FAIL  {name} — accepted")
        except jsonschema.ValidationError:
            print(f"  PASS  {name} — refused")
    return failures


def main() -> int:
    schema = load_schema()
    print(f"{TOOL_NAME} v{TOOL_VERSION}")
    print(f"schema: {SCHEMA_PATH.relative_to(ROOT.parent)}\n")

    print("parser control (runs before the schema):")
    failures = validate_loader()

    print(f"\npositive cases ({len(records())} records on disk):")
    failures += validate_positive(schema)

    print(f"\nnegative cases ({len(NEGATIVE_CASES)} controls demonstrated):")
    failures += validate_negative(schema)

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)})")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("RESULT: PASS — all records valid; all controls demonstrated to refuse")
    return 0


def run_smoke_test() -> bool:
    try:
        schema = load_schema()
        assert schema["additionalProperties"] is False
        assert len(records()) >= 1
        print(f"✓ {TOOL_NAME} loaded ({len(records())} records, "
              f"{len(NEGATIVE_CASES) + 1} controls)")
        return True
    except Exception as exc:  # pragma: no cover
        print(f"✗ Smoke test failed: {exc}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke-test":
        sys.exit(0 if run_smoke_test() else 1)
    sys.exit(main())

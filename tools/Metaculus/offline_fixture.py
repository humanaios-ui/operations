# Builder v1.7 compliant
"""Pure-stdlib, offline Metaculus forecast validation harness.

No external calls, models, Supabase, file writes or credentials. A *synthetic*
fixture exercises probability validation, a bounded sample ensemble and a binary
Brier score. This is NOT a tournament score or evidence of forecasting skill.
"""
from __future__ import annotations

TOOL_NAME = "metaculus_offline_fixture"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "calibration_tool"
TOOL_ZONE = 1

import argparse
import json
import math
from pathlib import Path
from typing import Any


class FixtureError(ValueError):
    pass


# Defend against accidentally introducing obvious restricted Metaculus aggregates.
# Content origin still requires independent permissions review.
RESTRICTED_FIELDS = frozenset({
    "community_prediction", "community_predictions", "cp", "crowd_prediction",
    "aggregate_prediction", "community_aggregate", "community_comments",
})
MAX_SAMPLES = 5


def _check_no_aggregate_fields(obj: Any) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).casefold() in RESTRICTED_FIELDS:
                raise FixtureError(f"Restricted aggregate input field: {k}")
            _check_no_aggregate_fields(v)
    elif isinstance(obj, list):
        for item in obj:
            _check_no_aggregate_fields(item)


def run_fixture(data: dict[str, Any]) -> dict[str, Any]:
    """Evaluate ONE synthetic binary question with a bounded sample ensemble."""
    if not isinstance(data, dict):
        raise FixtureError("Fixture must be a JSON object")
    _check_no_aggregate_fields(data)
    if data.get("schema") != "humanaios.metaculus.synthetic-fixture.v1":
        raise FixtureError("Unsupported fixture schema")
    if data.get("access_tier") != "NO_CP":
        raise FixtureError("Only NO_CP offline fixtures are supported")
    if data.get("source_kind") != "SYNTHETIC":
        raise FixtureError("Only synthetic data are accepted in E0")
    question = data.get("question")
    if not isinstance(question, dict) or question.get("type") != "binary":
        raise FixtureError("E0 fixture requires one synthetic binary question")
    ident = question.get("id")
    if not isinstance(ident, str) or not ident.startswith("synthetic-"):
        raise FixtureError("Synthetic question id required")
    samples = data.get("samples")
    if not isinstance(samples, list) or not 1 <= len(samples) <= MAX_SAMPLES:
        raise FixtureError("Sample count must be in [1, 5]")
    for value in samples:
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
            raise FixtureError("Every binary sample must be a finite probability in [0, 1]")
    estimate = sum(samples) / len(samples)
    resolved_as = question.get("resolved_as")
    if type(resolved_as) is not int or resolved_as not in (0, 1):
        raise FixtureError("Synthetic resolution must be 0 or 1")
    return {
        "schema": "humanaios.metaculus.offline-receipt.v1",
        "evidence_state": "SYNTHETIC_ONLY",
        "question_id": ident,
        "access_tier": "NO_CP",
        "sample_count": len(samples),
        "mean_probability": round(estimate, 8),
        "brier": round((estimate - resolved_as) ** 2, 8),
        "external_api_calls": 0,
        "database_writes": 0,
        "provider_spend_usd": 0,
        "live_submission": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic, zero-network fixture")
    parser.add_argument("--fixture", type=Path, default=Path(__file__).with_name("fixtures") / "synthetic_binary.json")
    args = parser.parse_args(argv)
    with args.fixture.open(encoding="utf-8") as handle:
        record = json.load(handle)
    print(json.dumps(run_fixture(record), sort_keys=True))
    return 0


def run_smoke_test() -> bool:
    """Synthetic-only smoke test; does not call any provider."""
    synthetic = {
        "schema": "humanaios.metaculus.synthetic-fixture.v1",
        "access_tier": "NO_CP",
        "source_kind": "SYNTHETIC",
        "question": {"id": "synthetic-smoke", "type": "binary", "resolved_as": 1},
        "samples": [0.5],
    }
    result = run_fixture(synthetic)
    return result["brier"] == 0.25 and result["external_api_calls"] == 0


if __name__ == "__main__":
    raise SystemExit(main())

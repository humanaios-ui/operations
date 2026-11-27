"""WITNESS_STATE v0.2 accepts the calibration profile that v0.1 rejects.

Ruling: Q-SMAG-CALIBRATION-SCHEMA-CONFORMANCE-01, option A (z1-inbox/2026-11-15/Z2_RULINGS_2026-11-15.md).
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover - the repo's other tests do not need it
    jsonschema = None

ROOT = Path(__file__).resolve().parents[1]
NEW_FIELDS = {
    "measured_gap_rate",
    "measured_clean_rate",
    "status",
    "calibration_notes",
    "failing_checks_observed",
    "acat_dimensions_stressed",
    "next_review_date",
}


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _state(schema_version: str, profile: dict) -> dict:
    return {
        "schema_version": schema_version,
        "session_id": "s-test",
        "participation_contract_ref": "contract-test",
        "non_authority_invariant": "WITNESS_IS_NOT_THE_AUTHORITY",
        "authority_context": {
            "resolution_source": "record",
            "effective_authority_ref": "ref-test",
            "resolved_at_event_seq": 0,
        },
        "modality_state": {
            name: {"enabled": False, "purpose_classes": []}
            for name in ("text", "pointer", "voice", "gaze")
        },
        "evidence_context": {"omission_codes": [], "last_event_seq": 0},
        "explanation_context": {"record_chain_ref": "chain-test", "reconstructable": True},
        "updated_at": "2026-11-15T00:00:00Z",
        "calibration_profile": profile,
    }


def _baseline_profile() -> dict:
    """The profile-shaped part of BASELINE_S092126.json (the file wraps it with audit fields)."""
    base = _load("calibration_profiles/BASELINE_S092126.json")
    return {"profile_version": base["profile_version"], "substrates": base["substrates"]}


@unittest.skipIf(jsonschema is None, "jsonschema not installed")
class WitnessStateV02Tests(unittest.TestCase):
    def _errors(self, schema_path: str, version: str, profile: dict) -> list:
        schema = _load(schema_path)
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        return list(validator.iter_errors(_state(version, profile)))

    def test_v0_2_is_a_new_file_and_v0_1_is_unchanged_in_version(self) -> None:
        v1, v2 = _load("WITNESS_STATE_V0_1.schema.json"), _load("WITNESS_STATE_V0_2.schema.json")
        self.assertEqual("0.1.0", v1["properties"]["schema_version"]["const"])
        self.assertEqual("0.2.0", v2["properties"]["schema_version"]["const"])
        self.assertTrue(v2["$id"].endswith("WITNESS_STATE_V0_2.schema.json"))

    def test_exactly_the_seven_ruled_fields_are_new(self) -> None:
        def fields(path: str) -> set:
            substrate = _load(path)["properties"]["calibration_profile"]["properties"]["substrates"]
            return set(substrate["additionalProperties"]["properties"])

        old, new = fields("WITNESS_STATE_V0_1.schema.json"), fields("WITNESS_STATE_V0_2.schema.json")
        self.assertEqual(NEW_FIELDS, new - old)
        self.assertEqual(set(), old - new)

    def test_baseline_profile_fails_v0_1(self) -> None:
        """The conformance gap the ruling closes: this is why s2 and s3 were blocked."""
        errors = self._errors("WITNESS_STATE_V0_1.schema.json", "0.1.0", _baseline_profile())
        self.assertTrue(errors, "v0.1 should reject the extra fields")

    def test_baseline_profile_passes_v0_2(self) -> None:
        errors = self._errors("WITNESS_STATE_V0_2.schema.json", "0.2.0", _baseline_profile())
        self.assertEqual([], [e.message for e in errors])

    def test_v0_2_still_rejects_unknown_substrate_fields(self) -> None:
        profile = copy.deepcopy(_baseline_profile())
        profile["substrates"]["Claude"]["not_a_field"] = 1
        self.assertTrue(self._errors("WITNESS_STATE_V0_2.schema.json", "0.2.0", profile))

    def test_v0_2_rejects_bad_values_for_new_fields(self) -> None:
        for field, bad in (
            ("measured_gap_rate", 1.5),
            ("measured_clean_rate", -0.1),
            ("status", "MAYBE"),
            ("failing_checks_observed", "validate"),
            ("next_review_date", "not-a-date"),
        ):
            profile = copy.deepcopy(_baseline_profile())
            profile["substrates"]["human:humanaios-ui"][field] = bad
            with self.subTest(field=field):
                self.assertTrue(self._errors("WITNESS_STATE_V0_2.schema.json", "0.2.0", profile))

    def test_v0_2_rejects_the_old_schema_version(self) -> None:
        self.assertTrue(self._errors("WITNESS_STATE_V0_2.schema.json", "0.1.0", _baseline_profile()))


if __name__ == "__main__":
    unittest.main()

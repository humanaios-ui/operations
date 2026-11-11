"""Offline E1 model evidence contract checks. Uses invented sources, no network."""
from __future__ import annotations

import copy
import unittest

from resource_miner.model_evidence_view import (
    SCHEMA,
    comparison_eligibility,
    project_synthetic_observations,
    validate_observation,
)


def record(identity="synthetic-model-A", observation="obs-a", *, origin="single-primary",
           harness="harness-sha-A", lens="CAPABILITY", version="v1", n=100):
    return {
        "schema": SCHEMA,
        "observation_id": observation,
        "subject": {
            "system_id": identity,
            "model_version": version,
            "scaffold_id": "none-v1",
        },
        "origin": {
            "source_uri": "synthetic://public-fixtures/eval-v1",
            "origin_key": origin,
            "observed_at": "2026-10-19T12:00:00Z",
            "source_class": "SIMULATED",
            "visibility": "PUBLIC_SYNTHETIC",
        },
        "method": {
            "lens": lens,
            "metric_key": "fixture_accuracy",
            "protocol_id": "synthetic-protocol-v1",
            "dataset_version": "dataset-v1",
            "harness_version": harness,
            "task_scope": "fixture-task",
        },
        "measurement": {
            "value": 0.7,
            "unit": "proportion",
            "sample_size": n,
            "ci_lower": 0.6,
            "ci_upper": 0.8,
        },
        "authority_effect": "NONE",
    }


class ModelEvidenceFixtureTests(unittest.TestCase):
    def setUp(self):
        self.a = record()
        self.b = record(identity="synthetic-model-B", observation="obs-b")

    def test_valid_and_comparable_does_not_announce_winner(self):
        report = comparison_eligibility(self.a, self.b)
        self.assertEqual(report["eligibility"], "COMPARABLE")
        self.assertIsNone(report["winner"])
        self.assertEqual(report["authority_effect"], "NONE")

    def test_incompatible_benchmark_harness_abstains(self):
        b = copy.deepcopy(self.b)
        b["method"]["harness_version"] = "different-harness"
        result = comparison_eligibility(self.a, b)
        self.assertEqual(result["eligibility"], "NOT_COMPARABLE")
        self.assertIn("METHOD_MISMATCH_OR_UNKNOWN:harness_version", result["reason_codes"])

    def test_incompatible_benchmark_edition_abstains(self):
        b = copy.deepcopy(self.b)
        b["method"]["dataset_version"] = "dataset-v2"
        self.assertEqual(comparison_eligibility(self.a, b)["eligibility"], "NOT_COMPARABLE")

    def test_unknown_method_fields_abstain(self):
        for key in self.a["method"].keys() - {"lens"}:
            for unknown in ("UNKNOWN", "unknown", " UnKnOwN ", "UNAVAILABLE", " unavailable "):
                for side in ("left", "right", "both"):
                    a, b = copy.deepcopy(self.a), copy.deepcopy(self.b)
                    if side in ("left", "both"):
                        a["method"][key] = unknown
                    if side in ("right", "both"):
                        b["method"][key] = unknown
                    with self.subTest(key=key, unknown=unknown, side=side):
                        result = comparison_eligibility(a, b)
                        self.assertEqual(result["eligibility"], "NOT_COMPARABLE")
                        self.assertEqual(result["reason_codes"],
                                         ["METHOD_MISMATCH_OR_UNKNOWN:" + key])

    def test_unknown_or_different_units_abstain(self):
        for unit in ("UNKNOWN", "unknown", " UnKnOwN ", "UNAVAILABLE", " unavailable ", "percent"):
            sides = ("left", "right") if unit == "percent" else ("left", "right", "both")
            for side in sides:
                a, b = copy.deepcopy(self.a), copy.deepcopy(self.b)
                if side in ("left", "both"):
                    a["measurement"]["unit"] = unit
                if side in ("right", "both"):
                    b["measurement"]["unit"] = unit
                with self.subTest(unit=unit, side=side):
                    result = comparison_eligibility(a, b)
                    self.assertEqual(result["eligibility"], "NOT_COMPARABLE")
                    self.assertEqual(result["reason_codes"], ["UNIT_MISMATCH"])

    def test_usage_and_capability_are_not_one_scale(self):
        b = copy.deepcopy(self.b)
        b["method"]["lens"] = "USAGE"
        self.assertIn("METHOD_MISMATCH_OR_UNKNOWN:lens",
                      comparison_eligibility(self.a, b)["reason_codes"])

    def test_missing_value_is_not_zero(self):
        b = copy.deepcopy(self.b)
        b["measurement"]["value"] = None
        self.assertIn("NOT_MEASURED", comparison_eligibility(self.a, b)["reason_codes"])

    def test_missing_uncertainty_is_not_invented(self):
        b = copy.deepcopy(self.b)
        b["measurement"]["ci_lower"] = None
        b["measurement"]["ci_upper"] = None
        self.assertIn("UNCERTAINTY_UNKNOWN",
                      comparison_eligibility(self.a, b)["reason_codes"])

    def test_null_measurements_preserve_unknown_reason_codes(self):
        b = copy.deepcopy(self.b)
        for key in ("value", "ci_lower", "ci_upper", "sample_size"):
            b["measurement"][key] = None
        result = comparison_eligibility(self.a, b)
        self.assertEqual(result["eligibility"], "NOT_COMPARABLE")
        self.assertEqual(result["reason_codes"],
                         ["NOT_MEASURED", "SAMPLE_SIZE_UNKNOWN", "UNCERTAINTY_UNKNOWN"])

    def test_underpowered_preference_abstains(self):
        a = record(lens="PREFERENCE", n=5)
        b = record(identity="synthetic-model-B", observation="obs-b",
                   lens="PREFERENCE", n=5)
        self.assertIn("UNDERPOWERED_ILLUSTRATIVE_THRESHOLD",
                      comparison_eligibility(a, b)["reason_codes"])

    def test_duplicate_primary_origin_is_one_independent_source(self):
        result = project_synthetic_observations([self.a, self.b],
                                                as_of="2026-10-21T00:00:00Z")
        self.assertEqual(result["source_origin_count"], 1)
        self.assertEqual(result["comparisons"][0]["independent_origin_count"], 1)

    def test_different_observation_ids_dont_mean_independent_publishers(self):
        mirror = copy.deepcopy(self.b)
        mirror["origin"]["source_uri"] = "synthetic://mirror/republished-results"
        self.assertEqual(
            project_synthetic_observations([self.a, mirror],
                                           as_of="2026-10-21T00:00:00Z")["source_origin_count"], 1)

    def test_freshness_marks_stale_without_deleting_historic_record(self):
        stale = copy.deepcopy(self.a)
        stale["origin"]["observed_at"] = "2026-01-01T00:00:00Z"
        output = project_synthetic_observations([stale], as_of="2026-10-21T00:00:00Z")
        self.assertEqual(output["observations"][0]["freshness"], "STALE_FOR_REVIEW")
        self.assertEqual(output["observation_count"], 1)

    def test_public_synthetic_only_blocks_private_or_real_sources(self):
        for changes in (
            {"visibility": "PRIVATE"},
            {"source_class": "FIRST_PARTY"},
            {"source_uri": "https://example.org/real"},
        ):
            a = copy.deepcopy(self.a)
            a["origin"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                validate_observation(a)

    def test_rejects_identity_alias_without_exact_version(self):
        for key in self.a["subject"]:
            for unknown in ("UNKNOWN", "unknown", " UnKnOwN ", "UNAVAILABLE", " unavailable "):
                a = copy.deepcopy(self.a)
                a["subject"][key] = unknown
                with self.subTest(key=key, unknown=unknown), self.assertRaises(ValueError):
                    validate_observation(a)

    def test_rejects_non_string_lenses(self):
        for lens in (None, True, 1, [], {}, ["CAPABILITY"]):
            a = copy.deepcopy(self.a)
            a["method"]["lens"] = lens
            with self.subTest(lens=lens), self.assertRaises(ValueError):
                validate_observation(a)

    def test_rejects_malformed_measurement_numbers(self):
        invalid = (True, False, "0.7", "UNKNOWN", [], {}, float("nan"),
                   float("inf"), -float("inf"), 10 ** 1000, -(10 ** 1000))
        for key in ("value", "ci_lower", "ci_upper"):
            for value in invalid:
                a = copy.deepcopy(self.a)
                a["measurement"][key] = value
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    validate_observation(a)

    def test_accepts_finite_integer_and_float_measurements(self):
        for value, lower, upper in ((1, 0, 2), (0.7, 0.6, 0.8)):
            a = copy.deepcopy(self.a)
            a["measurement"].update(value=value, ci_lower=lower, ci_upper=upper)
            with self.subTest(value=value):
                self.assertEqual(validate_observation(a), a)

    def test_rejects_forged_authority(self):
        a = copy.deepcopy(self.a)
        a["authority_effect"] = "RATIFIED"
        with self.assertRaises(ValueError):
            validate_observation(a)

    def test_rejects_unrecognized_payload_keys_and_private_blob(self):
        a = copy.deepcopy(self.a)
        a["raw_participant_message"] = "SHOULD_NOT_LEAK"
        with self.assertRaises(ValueError):
            validate_observation(a)

    def test_rejects_duplicate_observation_identity(self):
        b = copy.deepcopy(self.b)
        b["observation_id"] = self.a["observation_id"]
        with self.assertRaises(ValueError):
            project_synthetic_observations([self.a, b], as_of="2026-10-21T00:00:00Z")

    def test_rejects_nan_and_inconsistent_intervals(self):
        for variant in ("nan", "bad"):
            a = copy.deepcopy(self.a)
            if variant == "nan":
                a["measurement"]["value"] = float("nan")
            else:
                a["measurement"]["ci_lower"] = 0.9
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                validate_observation(a)

    def test_requires_timezone(self):
        a = copy.deepcopy(self.a)
        a["origin"]["observed_at"] = "2026-10-21T12:00:00"
        with self.assertRaises(ValueError):
            validate_observation(a)

    def test_stable_ordering_and_no_side_effects(self):
        first = project_synthetic_observations([self.a, self.b], as_of="2026-10-21T00:00:00Z")
        second = project_synthetic_observations([self.b, self.a], as_of="2026-10-21T00:00:00Z")
        self.assertEqual(first, second)
        self.assertIsNone(first["ranking"])
        self.assertEqual(first["scope"], "OFFLINE_SYNTHETIC_ONLY")
        self.assertEqual(first["authority_effect"], "NONE")


if __name__ == "__main__":
    unittest.main()

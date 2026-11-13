"""Synthetic proposed resource-plan v1 contract; no external resources or actions."""
from copy import deepcopy
from itertools import permutations, product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from resource_miner.planning import (
    PLAN_SCHEMA, derive_requirement_status, miner_requirements_from_plan,
    resolve_resource_plan, validate_resource_plan,
)


def plan_for(states=("ADEQUATE", "ADEQUATE"), mode="ALL_REQUIRED"):
    requirement = {
        "requirement_id": "Q-1", "resource_types": ["compute_credit"],
        "combination_mode": mode, "activation_state": "ACTIVE",
        "resolution_mode": "ACQUIRE_EXTERNAL", "mine_external": True,
    }
    if mode == "ALL_REQUIRED":
        requirement["required_components"] = [
            {"component_id": f"C-{i}", "label": f"Synthetic component {i}"}
            for i in range(len(states))
        ]
    return {
        "schema": PLAN_SCHEMA, "plan_id": "RP-SYNTHETIC", "authority_effect": "NONE",
        "controlled_resources": [{"resource_id": f"R-{i}"} for i in range(len(states))],
        "resource_requirements": [requirement],
        "substitution_assessments": [
            {"requirement_id": "Q-1", "controlled_resource_id": f"R-{i}",
             "status": state, **({"component_id": f"C-{i}"} if mode == "ALL_REQUIRED" else {})}
            for i, state in enumerate(states)
        ],
    }


def status(plan):
    return resolve_resource_plan(plan)["resource_requirements"][0]["gap_status"]


class CombinationResolutionTests(unittest.TestCase):
    def test_explicit_alternatives_preserve_legacy_matrix(self):
        cases = [(("ADEQUATE", "INADEQUATE"), "SATISFIED"),
                 (("PARTIAL", "UNKNOWN"), "PARTIAL"),
                 (("UNKNOWN", "INADEQUATE"), "UNKNOWN"),
                 (("INADEQUATE", "INADEQUATE"), "CONFIRMED"),
                 (("UNKNOWN", "UNKNOWN"), "UNKNOWN"), ((), "UNKNOWN")]
        for states, expected in cases:
            with self.subTest(states=states):
                plan = plan_for(states, "ALTERNATIVES")
                self.assertEqual(status(plan), expected)
                del plan["schema"]
                del plan["resource_requirements"][0]["combination_mode"]
                self.assertEqual(status(plan), expected)

    def test_complete_cumulative_status_matrix_and_order_independence(self):
        for states in product(("ADEQUATE", "PARTIAL", "UNKNOWN", "INADEQUATE"), repeat=3):
            expected = ("CONFIRMED" if "INADEQUATE" in states else
                        "UNKNOWN" if "UNKNOWN" in states else
                        "PARTIAL" if "PARTIAL" in states else "SATISFIED")
            with self.subTest(states=states):
                plan = plan_for(states)
                self.assertEqual(status(plan), expected)
                plan["substitution_assessments"].reverse()
                plan["resource_requirements"][0]["required_components"].reverse()
                self.assertEqual(status(plan), expected)

    def test_component_resources_are_alternatives_not_extra_required_components(self):
        plan = plan_for()
        plan["controlled_resources"].append({"resource_id": "R-OTHER"})
        plan["substitution_assessments"].append({
            "requirement_id": "Q-1", "component_id": "C-0",
            "controlled_resource_id": "R-OTHER", "status": "INADEQUATE",
        })
        for ordered in permutations(plan["substitution_assessments"]):
            plan["substitution_assessments"] = list(ordered)
            self.assertEqual(status(plan), "SATISFIED")

    def test_missing_assessment_is_unknown_and_does_not_hide_inadequacy(self):
        for assessed, expected in (("ADEQUATE", "UNKNOWN"), ("PARTIAL", "UNKNOWN"),
                                   ("INADEQUATE", "CONFIRMED")):
            with self.subTest(assessed=assessed):
                plan = plan_for((assessed, "ADEQUATE"))
                plan["substitution_assessments"].pop()
                self.assertEqual(status(plan), expected)
        plan["substitution_assessments"] = []
        self.assertEqual(status(plan), "UNKNOWN")

    def test_activation_overrides_adequacy_for_both_combination_modes(self):
        for mode, activation, assessed in product(
                ("ALTERNATIVES", "ALL_REQUIRED"), ("CONDITIONAL", "INACTIVE"),
                ("ADEQUATE", "PARTIAL", "INADEQUATE", "UNKNOWN")):
            with self.subTest(mode=mode, activation=activation, assessed=assessed):
                plan = plan_for((assessed,), mode)
                plan["resource_requirements"][0]["activation_state"] = activation
                self.assertEqual(status(plan), activation)

    def test_resolution_mode_distinguishes_external_and_internal_gaps(self):
        for mode, expected in (("ACQUIRE_EXTERNAL", "CONFIRMED"), ("HYBRID", "CONFIRMED"),
                               ("COMPOSE_INTERNAL", "INTERNAL_COMPOSITION_GAP")):
            with self.subTest(mode=mode):
                plan = plan_for(("ADEQUATE", "INADEQUATE"))
                plan["resource_requirements"][0]["resolution_mode"] = mode
                self.assertEqual(status(plan), expected)

    def test_external_export_policy_and_authority_are_preserved(self):
        for states, activation, resolution, mine, included, expected in (
            (("ADEQUATE", "ADEQUATE"), "ACTIVE", "ACQUIRE_EXTERNAL", True, False, "SATISFIED"),
            (("INADEQUATE",), "INACTIVE", "ACQUIRE_EXTERNAL", True, False, "INACTIVE"),
            (("INADEQUATE",), "ACTIVE", "COMPOSE_INTERNAL", True, False, "INTERNAL_COMPOSITION_GAP"),
            (("UNKNOWN",), "ACTIVE", "HYBRID", True, True, "UNKNOWN"),
            (("INADEQUATE",), "CONDITIONAL", "HYBRID", True, True, "CONDITIONAL"),
            (("INADEQUATE",), "ACTIVE", "ACQUIRE_EXTERNAL", False, False, "CONFIRMED"),
            (("PARTIAL",), "ACTIVE", "HYBRID", True, True, "PARTIAL"),
        ):
            with self.subTest(states=states, activation=activation, resolution=resolution, mine=mine):
                plan = plan_for(states)
                plan["resource_requirements"][0].update(
                    activation_state=activation, resolution_mode=resolution, mine_external=mine)
                self.assertEqual(status(plan), expected)
                rows = miner_requirements_from_plan(plan)
                self.assertEqual(bool(rows), included)
                for row in rows:
                    self.assertEqual(row["gap_status"], expected)
                    self.assertEqual(row["authority_effect"], "NONE")
                    self.assertNotIn("execution", row)

    def test_resolution_export_and_returned_data_do_not_mutate_input(self):
        plan = plan_for(("UNKNOWN", "PARTIAL"))
        before = deepcopy(plan)
        resolved = resolve_resource_plan(plan)
        exported = miner_requirements_from_plan(plan)
        self.assertEqual(plan, before)
        resolved["resource_requirements"][0]["required_components"].clear()
        exported[0]["resource_types"].clear()
        self.assertEqual(plan, before)

    def test_same_resource_can_be_assessed_for_distinct_components(self):
        plan = plan_for()
        plan["substitution_assessments"][1]["controlled_resource_id"] = "R-0"
        self.assertEqual(status(plan), "SATISFIED")


class CombinationValidationTests(unittest.TestCase):
    def assert_invalid(self, plan):
        for operation in (validate_resource_plan, resolve_resource_plan, miner_requirements_from_plan):
            before = deepcopy(plan)
            with self.subTest(operation=operation.__name__), self.assertRaises(ValueError):
                operation(plan)
            self.assertEqual(plan, before)

    def test_missing_or_invalid_version_is_rejected(self):
        for version in (None, "humanaios.resource-plan.v99", ""):
            plan = plan_for()
            if version is None:
                del plan["schema"]
            else:
                plan["schema"] = version
            self.assert_invalid(plan)

    def test_invalid_combination_modes(self):
        for mode in (None, "", "all_required", "ANY", [], {}):
            plan = plan_for()
            plan["resource_requirements"][0]["combination_mode"] = mode
            self.assert_invalid(plan)

    def test_cumulative_group_must_declare_nonempty_components(self):
        for components in (None, [], {}, "C-0", [None], [{"label": "Missing ID"}],
                           [{"component_id": " "}], [{"component_id": "C-0", "optional": True}]):
            plan = plan_for()
            plan["resource_requirements"][0]["required_components"] = components
            self.assert_invalid(plan)
        plan = plan_for()
        del plan["resource_requirements"][0]["required_components"]
        self.assert_invalid(plan)

    def test_missing_unknown_or_wrong_component_reference(self):
        for cid in (None, "C-MISSING", [], {}):
            plan = plan_for()
            plan["substitution_assessments"][0]["component_id"] = cid
            self.assert_invalid(plan)
        plan = plan_for()
        del plan["substitution_assessments"][0]["component_id"]
        self.assert_invalid(plan)

    def test_assessment_of_component_cannot_belong_to_another_requirement(self):
        plan = plan_for()
        other = deepcopy(plan["resource_requirements"][0])
        other.update(requirement_id="Q-2", required_components=[{"component_id": "C-OTHER"}])
        plan["resource_requirements"].append(other)
        plan["substitution_assessments"][0]["component_id"] = "C-OTHER"
        self.assert_invalid(plan)

    def test_duplicate_and_conflicting_component_ids(self):
        for cid in ("C-0", "Q-1", "R-0"):
            plan = plan_for()
            plan["resource_requirements"][0]["required_components"][1]["component_id"] = cid
            self.assert_invalid(plan)
        plan = plan_for()
        other = deepcopy(plan["resource_requirements"][0])
        other["requirement_id"] = "Q-2"
        plan["resource_requirements"].append(other)
        self.assert_invalid(plan)

    def test_duplicate_assessment_even_with_conflicting_status(self):
        plan = plan_for()
        plan["substitution_assessments"].append(dict(plan["substitution_assessments"][0], status="INADEQUATE"))
        self.assert_invalid(plan)

    def test_duplicate_and_unknown_resource_references(self):
        plan = plan_for()
        plan["controlled_resources"].append({"resource_id": "R-0"})
        self.assert_invalid(plan)
        plan = plan_for()
        plan["substitution_assessments"][0]["controlled_resource_id"] = "R-MISSING"
        self.assert_invalid(plan)

    def test_unsupported_status_and_unknown_requirement(self):
        plan = plan_for()
        plan["substitution_assessments"][0]["status"] = "SATISFIED"
        self.assert_invalid(plan)
        plan = plan_for()
        plan["substitution_assessments"][0]["requirement_id"] = "Q-MISSING"
        self.assert_invalid(plan)

    def test_alternative_flat_and_component_grouping_cannot_mix(self):
        plan = plan_for()
        plan["resource_requirements"][0]["combination_mode"] = "ALTERNATIVES"
        self.assert_invalid(plan)
        plan = plan_for(mode="ALTERNATIVES")
        plan["substitution_assessments"][0]["component_id"] = "C-0"
        self.assert_invalid(plan)

    def test_authority_claim_rejected_at_plan_requirement_component_and_assessment(self):
        for location in ("plan", "requirement", "component", "assessment", "resource"):
            plan = plan_for()
            target = {"plan": plan, "requirement": plan["resource_requirements"][0],
                      "component": plan["resource_requirements"][0]["required_components"][0],
                      "assessment": plan["substitution_assessments"][0],
                      "resource": plan["controlled_resources"][0]}[location]
            target["authority_effect"] = "EXECUTE"
            self.assert_invalid(plan)

    def test_direct_status_api_cannot_bypass_validation_even_when_inactive(self):
        plan = plan_for()
        plan["resource_requirements"][0]["activation_state"] = "INACTIVE"
        plan["substitution_assessments"][0]["component_id"] = "C-MISSING"
        with self.assertRaises(ValueError):
            derive_requirement_status(plan, plan["resource_requirements"][0])

    def test_collection_shapes_are_validated(self):
        for field in ("resource_requirements", "substitution_assessments", "controlled_resources"):
            for value in ({}, "bad", [None]):
                plan = plan_for()
                plan[field] = value
                self.assert_invalid(plan)

    def test_existing_cli_load_resolve_and_export_synthetic_versioned_plan(self):
        plan = plan_for(("ADEQUATE", "UNKNOWN"))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic-plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            for extra in ([], ["--miner-requirements"]):
                command = [sys.executable, "-B", "-m", "resource_miner.cli", "plan", "--file", str(path), *extra]
                result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=15)
                payload = json.loads(result.stdout)
                rows = payload if extra else payload["resource_requirements"]
                self.assertEqual(rows[0]["gap_status"], "UNKNOWN")
                self.assertEqual((payload[0] if extra else payload)["authority_effect"], "NONE")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), plan)

    def test_versioned_types_and_enums_fail_closed(self):
        for field, value in (("mine_external", "false"), ("resource_types", "grant"),
                              ("activation_state", "active"), ("resolution_mode", "hybrid")):
            plan = plan_for()
            plan["resource_requirements"][0][field] = value
            self.assert_invalid(plan)


class StructuralSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from jsonschema import Draft202012Validator
        except ImportError:
            raise unittest.SkipTest("jsonschema unavailable; structural schema checks NOT executed")
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas/resource-plan.v1.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        cls.validator = Draft202012Validator(schema)

    def test_valid_versioned_modes_and_missing_assessments(self):
        for mode in ("ALTERNATIVES", "ALL_REQUIRED"):
            plan = plan_for(mode=mode)
            self.validator.validate(plan)
            plan["substitution_assessments"] = []
            self.validator.validate(plan)
            validate_resource_plan(plan)

    def test_structural_schema_rejects_invalid_group_and_enum(self):
        for mode, components in (("OTHER", [{"component_id": "C-0"}]),
                                  ("ALL_REQUIRED", []), ("ALTERNATIVES", [{"component_id": "C-0"}])):
            plan = plan_for()
            plan["resource_requirements"][0].update(combination_mode=mode, required_components=components)
            self.assertTrue(list(self.validator.iter_errors(plan)))
            with self.assertRaises(ValueError):
                validate_resource_plan(plan)


if __name__ == "__main__":
    unittest.main()

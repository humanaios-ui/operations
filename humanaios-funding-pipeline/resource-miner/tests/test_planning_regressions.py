"""Synthetic boundary regressions; mixed-state precedence records current behavior."""

import copy
import itertools
import unittest

from resource_miner.planning import (
    miner_requirements_from_plan,
    resolve_resource_plan,
    validate_resource_plan,
)


def make_plan(states=(), *, activation="ACTIVE", mode="ACQUIRE_EXTERNAL", mine=True):
    return {
        "plan_id": "RP-SYNTHETIC",
        "authority_effect": "NONE",
        "needs": [{"need_id": "N-1"}],
        "capabilities": [{"capability_id": "C-1", "satisfies_need_ids": ["N-1"]}],
        "work_packages": [{"work_package_id": "W-1", "enables_capability_ids": ["C-1"]}],
        "controlled_resources": [{"resource_id": f"R-{i}"} for i in range(len(states))],
        "resource_requirements": [{
            "requirement_id": "Q-1", "work_package_ids": ["W-1"],
            "capability_ids": ["C-1"], "resource_types": ["compute_credit"],
            "activation_state": activation, "resolution_mode": mode,
            "mine_external": mine,
        }],
        "substitution_assessments": [{
            "requirement_id": "Q-1", "controlled_resource_id": f"R-{i}", "status": state,
        } for i, state in enumerate(states)],
    }


class PlanningRegressionTests(unittest.TestCase):
    def assert_status(self, plan, expected):
        resolved = resolve_resource_plan(plan)
        self.assertEqual(resolved["resource_requirements"][0]["gap_status"], expected)
        self.assertEqual(resolved["gap_counts"], {expected: 1})
        self.assertEqual(resolved["authority_effect"], "NONE")

    def test_unassessed_requirement_remains_unknown_in_each_resolution_mode(self):
        for mode in ("ACQUIRE_EXTERNAL", "HYBRID", "COMPOSE_INTERNAL"):
            with self.subTest(mode=mode):
                self.assert_status(make_plan(mode=mode), "UNKNOWN")

    def test_adequate_substitute_satisfies_requirement(self):
        self.assert_status(make_plan(("ADEQUATE",)), "SATISFIED")

    def test_inadequate_substitute_distinguishes_external_hybrid_and_internal_gaps(self):
        for mode, expected in (("ACQUIRE_EXTERNAL", "CONFIRMED"),
                               ("HYBRID", "CONFIRMED"),
                               ("COMPOSE_INTERNAL", "INTERNAL_COMPOSITION_GAP")):
            with self.subTest(mode=mode):
                self.assert_status(make_plan(("INADEQUATE",), mode=mode), expected)

    def test_mixed_assessment_precedence_is_order_independent(self):
        # Characterization, not a claim that one adequate resource always suffices
        # for every future planning model. Current assessments are alternatives.
        for states, expected in ((("UNKNOWN", "INADEQUATE"), "UNKNOWN"),
                                 (("PARTIAL", "UNKNOWN"), "PARTIAL"),
                                 (("ADEQUATE", "INADEQUATE"), "SATISFIED")):
            for ordered in itertools.permutations(states):
                with self.subTest(states=ordered):
                    self.assert_status(make_plan(ordered), expected)

    def test_activation_overrides_every_substitution_state(self):
        for activation in ("INACTIVE", "CONDITIONAL"):
            for state in ("ADEQUATE", "PARTIAL", "INADEQUATE", "UNKNOWN"):
                with self.subTest(activation=activation, state=state):
                    self.assert_status(make_plan((state,), activation=activation), activation)

    def test_duplicate_assessment_pair_rejected_even_when_status_differs(self):
        plan = make_plan(("ADEQUATE",))
        duplicate = dict(plan["substitution_assessments"][0], status="INADEQUATE")
        plan["substitution_assessments"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "Duplicate substitution assessment"):
            validate_resource_plan(plan)

    def test_substitution_rejects_unknown_controlled_resource(self):
        plan = make_plan(("UNKNOWN",))
        plan["substitution_assessments"][0]["controlled_resource_id"] = "R-MISSING"
        with self.assertRaisesRegex(ValueError, "unknown controlled resource: R-MISSING"):
            validate_resource_plan(plan)

    def test_duplicate_ids_rejected_within_each_graph_node_kind(self):
        for collection in ("needs", "capabilities", "work_packages",
                           "controlled_resources", "resource_requirements"):
            with self.subTest(collection=collection):
                plan = make_plan(("UNKNOWN",))
                plan[collection].append(copy.deepcopy(plan[collection][0]))
                with self.assertRaisesRegex(ValueError, "Duplicate .* id:"):
                    validate_resource_plan(plan)

    def test_cross_kind_node_id_collision_rejected(self):
        plan = make_plan(("UNKNOWN",))
        plan["controlled_resources"][0]["resource_id"] = "N-1"
        with self.assertRaisesRegex(ValueError, "node IDs must be globally unique"):
            validate_resource_plan(plan)

    def test_non_mineable_statuses_excluded_even_with_export_enabled(self):
        cases = ((make_plan(("ADEQUATE",)), "SATISFIED"),
                 (make_plan(("INADEQUATE",), activation="INACTIVE"), "INACTIVE"),
                 (make_plan(("INADEQUATE",), mode="COMPOSE_INTERNAL"), "INTERNAL_COMPOSITION_GAP"))
        for plan, expected in cases:
            with self.subTest(status=expected):
                self.assert_status(plan, expected)
                self.assertEqual(miner_requirements_from_plan(plan), [])

    def test_unknown_external_export_preserves_uncertainty_and_authority(self):
        plan = make_plan()
        before = copy.deepcopy(plan)
        exported = miner_requirements_from_plan(plan)
        self.assertEqual(len(exported), 1)
        self.assertEqual(exported[0]["requirement_id"], "Q-1")
        self.assertEqual(exported[0]["gap_status"], "UNKNOWN")
        self.assertEqual(exported[0]["authority_effect"], "NONE")
        self.assertEqual(exported[0]["source_plan_id"], "RP-SYNTHETIC")
        self.assertEqual(plan, before)

    def test_explicit_mine_external_false_blocks_otherwise_exportable_requirement(self):
        plan = make_plan(("INADEQUATE",), mine=False)
        self.assert_status(plan, "CONFIRMED")
        self.assertEqual(miner_requirements_from_plan(plan), [])


    def test_conditional_external_export_is_informational_only(self):
        # A mineable conditional row is a discovery input, never permission.
        for mode in ("ACQUIRE_EXTERNAL", "HYBRID"):
            for states in ((), ("ADEQUATE",), ("INADEQUATE",)):
                with self.subTest(mode=mode, states=states):
                    plan = make_plan(states, activation="CONDITIONAL", mode=mode)
                    before = copy.deepcopy(plan)
                    self.assert_status(plan, "CONDITIONAL")
                    exported = miner_requirements_from_plan(plan)
                    self.assertEqual(exported, [{
                        "requirement_id": "Q-1",
                        "gap_status": "CONDITIONAL",
                        "label": "Q-1",
                        "objective": "",
                        "resource_types": ["compute_credit"],
                        "affordances": [],
                        "signals": [],
                        "satisfied_when": "",
                        "authority_effect": "NONE",
                        "source_plan_id": "RP-SYNTHETIC",
                    }])
                    self.assertEqual(plan, before)

    def test_authority_escalation_is_rejected_at_every_planning_entry_point(self):
        # Validation, resolution, and export must each fail closed.
        for effect in ("APPROVED", "GRANTED", "EXECUTE", "CLAIM", "SUBMIT"):
            for operation in (validate_resource_plan, resolve_resource_plan,
                              miner_requirements_from_plan):
                with self.subTest(effect=effect, operation=operation.__name__):
                    plan = make_plan(("INADEQUATE",))
                    plan["authority_effect"] = effect
                    with self.assertRaisesRegex(ValueError,
                                                "Resource planning cannot grant authority"):
                        operation(plan)


if __name__ == "__main__":
    unittest.main()

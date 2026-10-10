"""Synthetic cross-contract and negative regressions for passive OSA v0.1."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "humanaios-funding-pipeline" / "resource-miner"))

from resource_miner.universal_adapter import Observation, synthetic_reference_registry
from services.guiding_light import evaluate_snapshot
from services.opportunity_surface import DIMENSIONS, ObservationError, SCHEMA, project


AT = "2026-10-10T10:00:00+00:00"
AFTER = "2026-10-11T10:00:00+00:00"


def specimen(*, unknown: bool = False) -> dict:
    """Real URA normalization and real Guiding Light scoring; synthetic data."""
    registry = synthetic_reference_registry()
    candidate = registry.normalize(Observation(
        provider_id="TRIAL_SYNTHETIC", external_id="osa-example-1",
        title="Synthetic evaluation environment",
        source_url="https://example.org/synthetic-trial",
        category="AI_EVALUATION_ENVIRONMENT", observed_at=AT,
        evidence_digest=sha256(b"synthetic only").hexdigest(),
    ))
    mapped = evaluate_snapshot({
        "subject": {"id": "synthetic-program", "type": "program"},
        "targets": [{
            "id": "target-synthetic-1", "title": "Synthetic capability target",
            "domain": "project", "value_axes": {"evidence_gain": 0.3},
            "requirements": [{
                "id": "synthetic-capability", "label": "Synthetic capability",
                "mandatory": True, "mapping_state": "UNKNOWN" if unknown else "DOCUMENTED",
            }],
        }],
    })
    return {
        "schema_version": SCHEMA,
        "as_of": "2030-01-01T00:00:00Z",
        "resource_candidates": [candidate],
        "guiding_light": mapped,
        "bindings": [{
            "resource_id": candidate["resource_id"],
            "target_id": "target-synthetic-1",
            "source_refs": ["synthetic-guiding-light-result"],
        }],
        "activity_events": [],
        "behavior_observations": [],
    }


def event(snapshot: dict, stage: str, i: int, *, evidence_state: str = "SOURCE_OBSERVED") -> dict:
    return {
        "event_id": f"stage-{i}",
        "resource_id": snapshot["resource_candidates"][0]["resource_id"],
        "stage": stage,
        "observed_at": f"2026-10-{10+i:02}T11:00:00Z",
        "source_refs": [f"synthetic-stage-{i}"],
        "evidence_state": evidence_state,
    }


class OpportunitySurfaceTests(unittest.TestCase):
    def test_taxonomy_exactly_nine_dimensions_and_thirty_three_rules(self):
        self.assertEqual(len(DIMENSIONS), 9)
        self.assertEqual(sum(map(len, DIMENSIONS.values())), 33)
        ids = [rule for rules in DIMENSIONS.values() for rule in rules]
        self.assertEqual(len(ids), len(set(ids)))

    def test_actual_ura_and_guiding_light_join_is_passive(self):
        data = specimen()
        before = deepcopy(data)
        report = project(data)
        self.assertEqual(data, before)
        self.assertEqual(report["counts"]["source_bound_candidates"], 1)
        self.assertEqual(report["counts"]["explicit_guiding_light_bindings"], 1)
        self.assertEqual(report["counts"]["qualified_claims"], 0)
        self.assertIsNone(report["rates"]["qualified_per_exposed"])
        self.assertIsNone(report["rates"]["succeeded_per_pursued"])
        self.assertFalse(report["authenticated"])
        self.assertFalse(report["can_authorize"])
        self.assertFalse(report["eligibility_established"])
        self.assertEqual(report["authority_effect"], "NONE")
        self.assertEqual(report["admission_effect"], "NONE")
        self.assertNotIn("https://", str(report))

    def test_provenance_bearing_claim_progression(self):
        data = specimen()
        data["activity_events"] = [event(data, stage, i)
                                   for i, stage in enumerate(
                                       ("EXPOSED", "QUALIFIED", "PURSUED", "SUCCEEDED"))]
        report = project(data)
        counts = report["counts"]
        self.assertEqual([counts[k] for k in (
            "exposed_claims", "qualified_claims", "pursued_claims", "succeeded_claims"
        )], [1, 1, 1, 1])
        self.assertEqual(report["rates"]["qualified_per_exposed"], 1.0)
        self.assertEqual(report["rates"]["succeeded_per_pursued"], 1.0)
        self.assertEqual(report["outcome_state"], "DESCRIPTIVE_ONLY")
        self.assertFalse(report["execution_available"])

    def test_no_automatic_exposure_from_resource_miner_or_guiding_light(self):
        data = specimen()
        self.assertEqual(project(data)["counts"]["exposed_claims"], 0)

    def test_unbound_resource_never_counts_as_exposed(self):
        data = specimen()
        data["resource_candidates"][0]["evidence"] = []
        data["bindings"] = []
        data["activity_events"] = [event(data, "EXPOSED", 0)]
        with self.assertRaises(ObservationError):
            project(data)
        data["activity_events"] = []
        self.assertEqual(project(data)["counts"]["source_bound_candidates"], 0)
        self.assertEqual(len(project(data)["omissions"]), 1)

    def test_no_silent_binding_by_matching_title(self):
        data = specimen()
        data["bindings"] = []
        data["activity_events"] = [event(data, "EXPOSED", 0),
                                   event(data, "QUALIFIED", 1)]
        with self.assertRaises(ObservationError):
            project(data)

    def test_mandatory_unknown_blocks_qualification(self):
        data = specimen(unknown=True)
        data["activity_events"] = [event(data, "EXPOSED", 0),
                                   event(data, "QUALIFIED", 1)]
        with self.assertRaises(ObservationError):
            project(data)

    def test_skip_stage_and_duplicate_phase_fail_closed(self):
        data = specimen()
        data["activity_events"] = [event(data, "PURSUED", 0)]
        with self.assertRaises(ObservationError):
            project(data)
        data["activity_events"] = [event(data, "EXPOSED", 0),
                                   event(data, "EXPOSED", 1)]
        with self.assertRaises(ObservationError):
            project(data)

    def test_success_requires_source_observation_and_all_prior_states(self):
        data = specimen()
        data["activity_events"] = [event(data, stage, i) for i, stage in
                                   enumerate(("EXPOSED", "QUALIFIED", "PURSUED"))]
        data["activity_events"].append(event(data, "SUCCEEDED", 3,
                                             evidence_state="SELF_ATTESTED"))
        with self.assertRaises(ObservationError):
            project(data)

    def test_retracted_outcome_is_not_active(self):
        data = specimen()
        data["activity_events"] = [event(data, stage, i) for i, stage in
                                   enumerate(("EXPOSED", "QUALIFIED", "PURSUED", "SUCCEEDED",
                                              "RETRACTED"))]
        report = project(data)
        self.assertEqual(report["counts"]["retracted_opportunities"], 1)
        self.assertEqual(report["counts"]["succeeded_claims"], 0)
        data["activity_events"].append(event(data, "EXPOSED", 5))
        with self.assertRaises(ObservationError):
            project(data)

    def test_rule_states_and_correction_preserve_non_authority(self):
        data = specimen()
        base = {
            "dimension": "shots", "rule_id": "volume_beats_perfection",
            "source_refs": ["synthetic-observation"],
        }
        data["behavior_observations"] = [
            {**base, "event_id": "a", "state": "SELF_ATTESTED",
             "observed_at": AT},
            {**base, "event_id": "b", "state": "SOURCE_OBSERVED",
             "observed_at": AFTER},
        ]
        projection = project(data)
        self.assertEqual(projection["dimensions"]["shots"]["source_observed_claims"], 1)
        self.assertEqual(projection["dimensions"]["shots"]["self_attested"], 0)
        self.assertEqual(projection["dimensions"]["shots"]["unknown_or_retracted"], 3)
        self.assertFalse(projection["authenticated"])

    def test_duplicate_resource_event_and_unknown_rule_rejected(self):
        data = specimen()
        data["resource_candidates"].append(deepcopy(data["resource_candidates"][0]))
        with self.assertRaises(ObservationError):
            project(data)
        data = specimen()
        data["activity_events"] = [event(data, "EXPOSED", 0), event(data, "EXPOSED", 0)]
        with self.assertRaises(ObservationError):
            project(data)
        data = specimen()
        data["behavior_observations"] = [{
            "event_id": "rule-1", "dimension": "shots", "rule_id": "fabricated_rule",
            "state": "SELF_ATTESTED", "source_refs": ["source"], "observed_at": AT,
        }]
        with self.assertRaises(ObservationError):
            project(data)

    def test_forged_authorization_rejected_even_with_successful_claims(self):
        data = specimen()
        data["activity_events"] = [event(data, "EXPOSED", 0)]
        data["activity_events"][0]["authorization"] = "APPROVED"
        with self.assertRaises(ObservationError):
            project(data)
        data = specimen()
        data["resource_candidates"][0]["authority_effect"] = "ELEVATE"
        with self.assertRaises(ObservationError):
            project(data)

    def test_naive_and_future_timestamps_rejected(self):
        data = specimen()
        data["activity_events"] = [event(data, "EXPOSED", 0)]
        data["activity_events"][0]["observed_at"] = "2026-10-10T11:00:00"
        with self.assertRaises(ObservationError):
            project(data)
        data = specimen()
        data["resource_candidates"][0]["discovered_at"] = "2031-01-01T00:00:00Z"
        with self.assertRaises(ObservationError):
            project(data)

    def test_missing_sources_and_alleged_verified_evidence_rejected(self):
        data = specimen()
        data["activity_events"] = [event(data, "EXPOSED", 0)]
        data["activity_events"][0]["source_refs"] = []
        with self.assertRaises(ObservationError):
            project(data)
        data["activity_events"][0]["source_refs"] = ["synthetic"]
        data["activity_events"][0]["evidence_state"] = "VERIFIED"
        with self.assertRaises(ObservationError):
            project(data)


if __name__ == "__main__":
    unittest.main()

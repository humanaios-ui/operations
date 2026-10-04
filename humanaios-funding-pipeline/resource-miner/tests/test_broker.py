import unittest

from resource_miner.broker import (
    assess_suitability,
    authorize_broker_action,
    build_opportunity,
    build_requirement,
    record_broker_outcome,
    screen_resource,
)
from resource_miner.models import EvidenceRef
from resource_miner.normalize import normalize_generic


class BrokerControlSubstrateTests(unittest.TestCase):
    def setUp(self):
        self.opp_evidence = [
            EvidenceRef(
                url="https://example.test/program-policy",
                kind="source",
                observed_at="2026-10-04T15:00:00Z",
                claim="Synthetic bounty program policy and scope were observed.",
            )
        ]
        self.resource_evidence = [
            EvidenceRef(
                url="https://github.com/example/passive-inspector",
                kind="source",
                observed_at="2026-10-04T15:00:00Z",
                claim="Synthetic open-source project documentation describes passive HTTP inspection.",
            )
        ]
        self.opportunity = build_opportunity(
            title="Synthetic disclosure bounty",
            source_kind="BUG_BOUNTY",
            source_url="https://example.test/program",
            sponsor="Example Program",
            evidence=self.opp_evidence,
        )
        self.requirement = build_requirement(
            opportunity=self.opportunity,
            label="Passive public HTTP inspection",
            objective="Inspect public HTTP metadata without state change.",
            required_affordances=["passive_observation", "evidence_capture"],
            allowed_resource_types=["open_source_tool"],
            method_permission_state="PERMITTED",
            target_scope_state="IN_SCOPE",
            external_state_change_allowed=False,
            evidence=self.opp_evidence,
        )
        self.resource = normalize_generic(
            title="Passive Inspector",
            url="https://github.com/example/passive-inspector",
            source_name="GitHub",
            discovery_method="synthetic-test",
            description="Read-only HTTP metadata inspection with evidence capture.",
            source_category="open_source_tool",
        )
        self.resource.resource_types = ["open_source_tool"]
        self.resource.resource_affordances = [
            "passive_observation",
            "evidence_capture",
        ]
        self.resource.evidence = list(self.resource_evidence)
        self.screen = screen_resource(
            self.resource,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="READ_ONLY",
            credential_requirement="NONE",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.assessment = assess_suitability(
            opportunity=self.opportunity,
            requirement=self.requirement,
            resource=self.resource,
            provider_class="OPEN_SOURCE",
            screen=self.screen,
        )

    def test_open_source_resource_can_satisfy_without_humanaios_capability(self):
        self.assertEqual(self.assessment.provider_class, "OPEN_SOURCE")
        self.assertEqual(self.assessment.suitability_state, "ADEQUATE")
        self.assertEqual(
            set(self.assessment.matched_affordances),
            {"passive_observation", "evidence_capture"},
        )
        self.assertEqual(self.assessment.authority_effect, "NONE")

    def test_partial_affordance_coverage_is_not_false_adequacy(self):
        partial = normalize_generic(
            title="Metadata Viewer",
            url="https://github.com/example/metadata-viewer",
            source_name="GitHub",
            discovery_method="synthetic-test",
        )
        partial.resource_types = ["open_source_tool"]
        partial.resource_affordances = ["passive_observation"]
        partial.evidence = list(self.resource_evidence)
        screen = screen_resource(
            partial,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="READ_ONLY",
            credential_requirement="NONE",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        assessment = assess_suitability(
            opportunity=self.opportunity,
            requirement=self.requirement,
            resource=partial,
            provider_class="OPEN_SOURCE",
            screen=screen,
        )
        self.assertEqual(assessment.suitability_state, "PARTIAL")
        self.assertEqual(assessment.missing_affordances, ["evidence_capture"])

    def test_constitutional_screen_can_block_capable_resource(self):
        blocked = screen_resource(
            self.resource,
            provenance_state="VERIFIED",
            license_state="RESTRICTED",
            permissions_state="MINIMAL",
            network_behavior="READ_ONLY",
            credential_requirement="NONE",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        assessment = assess_suitability(
            opportunity=self.opportunity,
            requirement=self.requirement,
            resource=self.resource,
            provider_class="OPEN_SOURCE",
            screen=blocked,
        )
        self.assertEqual(blocked.state, "FAIL")
        self.assertEqual(assessment.suitability_state, "INADEQUATE")

    def test_metadata_review_can_be_bounded_without_external_execution(self):
        auth = authorize_broker_action(
            opportunity=self.opportunity,
            requirement=self.requirement,
            assessment=self.assessment,
            requested_action="REVIEW_RESOURCE_METADATA",
        )
        self.assertEqual(auth.decision, "AUTHORIZED_BOUNDED")
        self.assertEqual(auth.consequence_ceiling, "BROKER_REVIEW_ONLY")
        self.assertFalse(auth.execution_performed)

    def test_external_tool_execution_requires_explicit_human_authorization(self):
        auth = authorize_broker_action(
            opportunity=self.opportunity,
            requirement=self.requirement,
            assessment=self.assessment,
            requested_action="EXECUTE_EXTERNAL_TOOL",
            human_authorized=False,
        )
        self.assertEqual(auth.decision, "REQUIRE_HUMAN")
        self.assertEqual(auth.authority_effect, "NONE")

    def test_out_of_scope_external_action_is_denied_even_with_human_flag(self):
        out_requirement = build_requirement(
            opportunity=self.opportunity,
            label="Passive public HTTP inspection",
            objective="Synthetic out-of-scope test.",
            required_affordances=["passive_observation", "evidence_capture"],
            allowed_resource_types=["open_source_tool"],
            method_permission_state="PERMITTED",
            target_scope_state="OUT_OF_SCOPE",
            external_state_change_allowed=False,
            evidence=self.opp_evidence,
        )
        assessment = assess_suitability(
            opportunity=self.opportunity,
            requirement=out_requirement,
            resource=self.resource,
            provider_class="OPEN_SOURCE",
            screen=self.screen,
        )
        auth = authorize_broker_action(
            opportunity=self.opportunity,
            requirement=out_requirement,
            assessment=assessment,
            requested_action="EXECUTE_EXTERNAL_TOOL",
            human_authorized=True,
        )
        self.assertEqual(auth.decision, "DENY")
        self.assertEqual(auth.authority_effect, "NONE")

    def test_explicit_human_plus_scope_and_method_can_authorize_bounded_action(self):
        auth = authorize_broker_action(
            opportunity=self.opportunity,
            requirement=self.requirement,
            assessment=self.assessment,
            requested_action="EXECUTE_EXTERNAL_TOOL",
            human_authorized=True,
        )
        self.assertEqual(auth.decision, "AUTHORIZED_BOUNDED")
        self.assertEqual(
            auth.consequence_ceiling,
            "EXTERNAL_ACTION_EXPLICIT_SCOPE_ONLY",
        )
        self.assertFalse(auth.execution_performed)

    def test_unknown_action_fails_closed(self):
        auth = authorize_broker_action(
            opportunity=self.opportunity,
            requirement=self.requirement,
            assessment=self.assessment,
            requested_action="DO_WHATEVER_WORKS",
        )
        self.assertEqual(auth.decision, "DENY")

    def test_outcome_preserves_exact_lineage_and_creates_no_new_authority(self):
        auth = authorize_broker_action(
            opportunity=self.opportunity,
            requirement=self.requirement,
            assessment=self.assessment,
            requested_action="REVIEW_RESOURCE_METADATA",
        )
        outcome = record_broker_outcome(
            opportunity=self.opportunity,
            requirement=self.requirement,
            assessment=self.assessment,
            authorization=auth,
            outcome_state="REVIEW_COMPLETED",
            observation="The synthetic resource metadata review completed without target execution.",
            evidence=self.resource_evidence,
        )
        self.assertEqual(outcome.authorization_id, auth.authorization_id)
        self.assertEqual(outcome.suitability_id, self.assessment.assessment_id)
        self.assertEqual(outcome.authority_effect, "NONE")
        self.assertFalse(outcome.execution_claimed)
        self.assertEqual(len(outcome.outcome_sha256), 64)

    def test_execution_outcome_cannot_be_claimed_from_review_only_authorization(self):
        auth = authorize_broker_action(
            opportunity=self.opportunity,
            requirement=self.requirement,
            assessment=self.assessment,
            requested_action="REVIEW_RESOURCE_METADATA",
        )
        with self.assertRaises(PermissionError):
            record_broker_outcome(
                opportunity=self.opportunity,
                requirement=self.requirement,
                assessment=self.assessment,
                authorization=auth,
                outcome_state="EXECUTION_REPORTED",
                observation="Synthetic execution claim.",
                evidence=self.resource_evidence,
                execution_claimed=True,
            )

    def test_resource_without_evidence_cannot_be_brokered(self):
        bare = normalize_generic(
            title="Unproven Tool",
            url="https://example.test/unproven",
            source_name="Unknown",
            discovery_method="synthetic-test",
        )
        bare.resource_types = ["open_source_tool"]
        bare.resource_affordances = ["passive_observation", "evidence_capture"]
        screen = screen_resource(
            bare,
            provenance_state="UNKNOWN",
            license_state="UNKNOWN",
            permissions_state="UNKNOWN",
            network_behavior="UNKNOWN",
            credential_requirement="UNKNOWN",
            external_state_change=None,
            auditability="UNKNOWN",
            least_privilege_compatible=None,
        )
        with self.assertRaises(ValueError):
            assess_suitability(
                opportunity=self.opportunity,
                requirement=self.requirement,
                resource=bare,
                provider_class="OPEN_SOURCE",
                screen=screen,
            )


if __name__ == "__main__":
    unittest.main()

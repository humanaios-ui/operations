import unittest

from resource_miner.broker import (
    assess_suitability,
    build_opportunity,
    screen_resource,
)
from resource_miner.capability_package import (
    capability_package_from_dict,
    compose_capability_package,
)
from resource_miner.demand import (
    build_demand_profile,
    compile_broker_requirements,
    make_demand_requirement,
)
from resource_miner.models import EvidenceRef
from resource_miner.normalize import normalize_generic
from resource_miner.service_surface import (
    SERVICE_SURFACE_CLASSES,
    taxonomy_snapshot,
)


class CapabilityPackageTests(unittest.TestCase):
    def setUp(self):
        self.evidence = [
            EvidenceRef(
                url="https://example.test/opportunity",
                kind="source",
                observed_at="2026-10-04T16:00:00Z",
                claim="Synthetic capability-package demand and resource evidence.",
            )
        ]
        self.opportunity = build_opportunity(
            title="Synthetic multi-capability opportunity",
            source_kind="SECURITY_PROGRAM",
            source_url="https://example.test/opportunity",
            sponsor="Example Program",
            evidence=self.evidence,
        )
        self.demand_rows = [
            make_demand_requirement(
                label="Passive service observation",
                mode="REQUIRED",
                semantic_class="CAPABILITY",
                statement="Observe bounded public service metadata without mutation.",
                evidence=self.evidence,
                required_affordances=["passive_observation"],
                allowed_resource_types=["open_source_tool"],
            ),
            make_demand_requirement(
                label="Evidence capture",
                mode="REQUIRED",
                semantic_class="CAPABILITY",
                statement="Capture reproducible evidence with provenance.",
                evidence=self.evidence,
                required_affordances=["evidence_capture"],
                allowed_resource_types=["open_source_tool"],
            ),
            make_demand_requirement(
                label="Identity metadata review",
                mode="REQUIRED",
                semantic_class="CAPABILITY",
                statement="Review published authentication and identity metadata.",
                evidence=self.evidence,
                required_affordances=["auth_metadata_review"],
                allowed_resource_types=["open_source_tool"],
            ),
            make_demand_requirement(
                label="Optional browser analysis",
                mode="OPTIONAL",
                semantic_class="CAPABILITY",
                statement="Analyze browser-side application behavior where useful.",
                evidence=self.evidence,
                required_affordances=["browser_analysis"],
                allowed_resource_types=["open_source_tool"],
            ),
        ]
        self.profile = build_demand_profile(
            opportunity=self.opportunity,
            source_kind="SECURITY_PROGRAM",
            source_identity="SYNTH-CPK-001",
            source_url="https://example.test/opportunity",
            objective="Validate many-requirement/many-resource package composition.",
            requirements=self.demand_rows,
            evidence=self.evidence,
            source_metadata={
                "method_permission_state": "PERMITTED",
                "target_scope_state": "IN_SCOPE",
                "external_state_change_allowed": False,
                "allowed_network_behaviors": [
                    "READ_ONLY",
                    "PASSIVE_PUBLIC_SOURCE",
                    "THIRD_PARTY_API_READ_ONLY",
                ],
            },
        )
        self.requirements = compile_broker_requirements(
            profile=self.profile,
            opportunity=self.opportunity,
        )
        self.by_dmr = {
            row.demand_requirement_id: row for row in self.requirements
        }

        self.resource_a = normalize_generic(
            title="Surface Metadata Inspector",
            url="https://github.com/example/surface-inspector",
            source_name="GitHub",
            discovery_method="synthetic-test",
            source_category="open_source_tool",
        )
        self.resource_a.resource_types = ["open_source_tool"]
        self.resource_a.resource_affordances = [
            "passive_observation",
            "auth_metadata_review",
        ]
        self.resource_a.evidence = list(self.evidence)

        self.resource_b = normalize_generic(
            title="Evidence Recorder",
            url="https://github.com/example/evidence-recorder",
            source_name="GitHub",
            discovery_method="synthetic-test",
            source_category="open_source_tool",
        )
        self.resource_b.resource_types = ["open_source_tool"]
        self.resource_b.resource_affordances = [
            "passive_observation",
            "evidence_capture",
        ]
        self.resource_b.evidence = list(self.evidence)

        self.screen_a = screen_resource(
            self.resource_a,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="READ_ONLY",
            credential_requirement="NONE",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.screen_b = screen_resource(
            self.resource_b,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="READ_ONLY",
            credential_requirement="NONE",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )

        def assess(requirement, resource, screen):
            return assess_suitability(
                opportunity=self.opportunity,
                requirement=requirement,
                resource=resource,
                provider_class="OPEN_SOURCE",
                screen=screen,
            )

        req_passive = self.by_dmr[self.demand_rows[0].demand_requirement_id]
        req_evidence = self.by_dmr[self.demand_rows[1].demand_requirement_id]
        req_auth = self.by_dmr[self.demand_rows[2].demand_requirement_id]
        req_optional = self.by_dmr[self.demand_rows[3].demand_requirement_id]

        self.a_passive = assess(req_passive, self.resource_a, self.screen_a)
        self.b_passive = assess(req_passive, self.resource_b, self.screen_b)
        self.b_evidence = assess(req_evidence, self.resource_b, self.screen_b)
        self.a_auth = assess(req_auth, self.resource_a, self.screen_a)
        self.a_optional = assess(req_optional, self.resource_a, self.screen_a)
        self.assessments = [
            self.a_passive,
            self.b_passive,
            self.b_evidence,
            self.a_auth,
            self.a_optional,
        ]
        self.surface_map = {
            req_passive.requirement_id: ["NETWORK_TRANSPORT", "WEB_APPLICATION", "API_SERVICE"],
            req_evidence.requirement_id: ["DISCOVERY_METADATA"],
            req_auth.requirement_id: ["AUTH_IDENTITY"],
            req_optional.requirement_id: ["CLIENT_BROWSER"],
        }

    def compose(self, selected_ids, resources=None, screens=None):
        return compose_capability_package(
            profile=self.profile,
            broker_requirements=self.requirements,
            resources=resources or [self.resource_a, self.resource_b],
            assessments=self.assessments,
            resource_screens=screens or [self.screen_a, self.screen_b],
            selected_assessment_ids=selected_ids,
            service_surface_map=self.surface_map,
        )

    def test_cpk_composes_three_required_requirements_from_two_resources(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        self.assertTrue(package.package_id.startswith("CPK-"))
        self.assertEqual(package.required_requirement_count, 3)
        self.assertEqual(package.required_adequately_covered_count, 3)
        self.assertEqual(package.required_coverage_state, "COMPLETE")
        self.assertEqual(set(package.resource_ids), {
            self.resource_a.resource_id,
            self.resource_b.resource_id,
        })
        self.assertEqual(package.composition_screen_state, "PASS")
        self.assertEqual(package.authority_effect, "NONE")

    def test_one_resource_can_cover_multiple_requirements(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        bindings = {
            row.demand_requirement_id: row
            for row in package.bindings
        }
        self.assertIn(
            self.resource_a.resource_id,
            bindings[self.demand_rows[0].demand_requirement_id].selected_resource_ids,
        )
        self.assertIn(
            self.resource_a.resource_id,
            bindings[self.demand_rows[2].demand_requirement_id].selected_resource_ids,
        )

    def test_one_requirement_can_be_covered_by_multiple_resources(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        binding = next(
            row
            for row in package.bindings
            if row.demand_requirement_id == self.demand_rows[0].demand_requirement_id
        )
        self.assertEqual(
            set(binding.selected_resource_ids),
            {self.resource_a.resource_id, self.resource_b.resource_id},
        )
        self.assertEqual(binding.coverage_state, "ADEQUATE")

    def test_optional_uncovered_requirement_does_not_fail_required_coverage(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        self.assertEqual(package.required_coverage_state, "COMPLETE")
        self.assertEqual(package.composition_screen_state, "PASS")
        self.assertIn(
            self.demand_rows[3].demand_requirement_id,
            package.uncovered_nonrequired_requirement_ids,
        )

    def test_uncovered_required_requirement_fails_package_screen(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_evidence.assessment_id,
            ]
        )
        self.assertEqual(package.required_coverage_state, "INCOMPLETE")
        self.assertEqual(package.composition_screen_state, "FAIL")
        self.assertIn(
            self.demand_rows[2].demand_requirement_id,
            package.uncovered_required_requirement_ids,
        )
        self.assertIn(
            "REQUIRED_CAPABILITY_COVERAGE_INCOMPLETE",
            package.composition_findings,
        )

    def test_individually_pass_resources_can_conflict_in_composition(self):
        self.assertEqual(self.screen_a.state, "PASS")
        self.assertEqual(self.screen_b.state, "PASS")
        self.resource_a.composition_conflicts = [
            self.resource_b.resource_id
        ]
        self.a_passive = assess_suitability(
            opportunity=self.opportunity,
            requirement=self.by_dmr[self.demand_rows[0].demand_requirement_id],
            resource=self.resource_a,
            provider_class="OPEN_SOURCE",
            screen=self.screen_a,
        )
        self.a_auth = assess_suitability(
            opportunity=self.opportunity,
            requirement=self.by_dmr[self.demand_rows[2].demand_requirement_id],
            resource=self.resource_a,
            provider_class="OPEN_SOURCE",
            screen=self.screen_a,
        )
        self.assessments = [
            self.a_passive,
            self.b_passive,
            self.b_evidence,
            self.a_auth,
            self.a_optional,
        ]
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        self.assertEqual(package.required_coverage_state, "COMPLETE")
        self.assertEqual(package.composition_screen_state, "FAIL")
        self.assertTrue(
            any(
                finding.startswith("DECLARED_RESOURCE_CONFLICT:")
                for finding in package.composition_findings
            )
        )


    def test_conflict_mutation_after_assessment_invalidates_lineage(self):
        self.resource_a.composition_conflicts = [
            self.resource_b.resource_id
        ]
        with self.assertRaises(ValueError):
            self.compose(
                [
                    self.a_passive.assessment_id,
                    self.b_evidence.assessment_id,
                    self.a_auth.assessment_id,
                ]
            )

    def test_third_party_index_query_differs_from_target_touching(self):
        third_party_screen = screen_resource(
            self.resource_a,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="THIRD_PARTY_API_READ_ONLY",
            credential_requirement="REQUIRED",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        target_screen = screen_resource(
            self.resource_b,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="TARGET_ACTIVE",
            credential_requirement="NONE",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        self.assertEqual(third_party_screen.state, "PASS_WITH_CONDITIONS")
        self.assertEqual(target_screen.state, "PASS_WITH_CONDITIONS")
        self.assertTrue(
            any("third_party_api_interaction" in x for x in third_party_screen.findings)
        )
        self.assertTrue(
            any("network_behavior=TARGET_ACTIVE" in x for x in target_screen.findings)
        )

    def test_credential_propagation_is_package_condition(self):
        resource_c = normalize_generic(
            title="Credentialed Browser Helper",
            url="https://github.com/example/credentialed-browser-helper",
            source_name="GitHub",
            discovery_method="synthetic-test",
            source_category="open_source_tool",
        )
        resource_c.resource_types = ["open_source_tool"]
        resource_c.resource_affordances = ["browser_analysis"]
        resource_c.evidence = list(self.evidence)
        credential_screen = screen_resource(
            resource_c,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="READ_ONLY",
            credential_requirement="REQUIRED",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        c_optional = assess_suitability(
            opportunity=self.opportunity,
            requirement=self.by_dmr[self.demand_rows[3].demand_requirement_id],
            resource=resource_c,
            provider_class="OPEN_SOURCE",
            screen=credential_screen,
        )
        assessments = [
            self.a_passive,
            self.b_evidence,
            self.a_auth,
            c_optional,
        ]
        package = compose_capability_package(
            profile=self.profile,
            broker_requirements=self.requirements,
            resources=[self.resource_a, self.resource_b, resource_c],
            assessments=assessments,
            resource_screens=[self.screen_a, self.screen_b, credential_screen],
            selected_assessment_ids=[row.assessment_id for row in assessments],
            service_surface_map=self.surface_map,
        )
        self.assertEqual(package.required_coverage_state, "COMPLETE")
        self.assertEqual(package.composition_screen_state, "PASS_WITH_CONDITIONS")
        self.assertIn(
            "CREDENTIAL_PROPAGATION_REVIEW_REQUIRED",
            package.composition_findings,
        )

    def test_service_surface_taxonomy_maps_all_ten_supplied_concept_groups(self):
        expected = {
            "NETWORK_TRANSPORT",
            "WEB_APPLICATION",
            "API_SERVICE",
            "REALTIME_EVENT",
            "AUTH_IDENTITY",
            "DISCOVERY_METADATA",
            "CLIENT_BROWSER",
            "STORAGE_CLOUD",
            "ADMIN_OPS_MANAGEMENT",
            "THIRD_PARTY_EMBEDDED",
        }
        self.assertEqual(SERVICE_SURFACE_CLASSES, expected)
        snapshot = taxonomy_snapshot()
        self.assertEqual(set(snapshot), expected)
        self.assertTrue(all(row["scope_effect"] == "NONE" for row in snapshot.values()))
        self.assertTrue(all(row["authorization_effect"] == "NONE" for row in snapshot.values()))


    def test_passive_only_package_policy_blocks_target_active_mode(self):
        active_resource = normalize_generic(
            title="Active Discovery Variant",
            url="https://github.com/example/active-discovery",
            source_name="GitHub",
            discovery_method="synthetic-test",
            source_category="open_source_tool",
        )
        active_resource.resource_types = ["open_source_tool"]
        active_resource.resource_affordances = ["passive_observation"]
        active_resource.operational_mode = "ACTIVE"
        active_resource.evidence = list(self.evidence)
        active_screen = screen_resource(
            active_resource,
            provenance_state="VERIFIED",
            license_state="ALLOWABLE",
            permissions_state="MINIMAL",
            network_behavior="TARGET_ACTIVE",
            credential_requirement="NONE",
            external_state_change=False,
            auditability="ADEQUATE",
            least_privilege_compatible=True,
        )
        req_passive = self.by_dmr[self.demand_rows[0].demand_requirement_id]
        active_assessment = assess_suitability(
            opportunity=self.opportunity,
            requirement=req_passive,
            resource=active_resource,
            provider_class="OPEN_SOURCE",
            screen=active_screen,
        )
        package = compose_capability_package(
            profile=self.profile,
            broker_requirements=self.requirements,
            resources=[active_resource, self.resource_a, self.resource_b],
            assessments=[
                active_assessment,
                self.b_evidence,
                self.a_auth,
            ],
            resource_screens=[
                active_screen,
                self.screen_a,
                self.screen_b,
            ],
            selected_assessment_ids=[
                active_assessment.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ],
            service_surface_map=self.surface_map,
        )
        self.assertEqual(package.required_coverage_state, "COMPLETE")
        self.assertEqual(package.composition_screen_state, "FAIL")
        self.assertTrue(
            any(
                finding.startswith("NETWORK_BEHAVIOR_POLICY_CONFLICT:")
                for finding in package.composition_findings
            )
        )

    def test_surface_classification_does_not_establish_scope_or_permission(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        self.assertIn("NETWORK_TRANSPORT", package.service_surface_classes)
        self.assertIn("AUTH_IDENTITY", package.service_surface_classes)
        self.assertEqual(package.target_scope_state, "NOT_ESTABLISHED")
        self.assertEqual(package.method_permission_state, "NOT_ESTABLISHED")
        self.assertEqual(package.authorization_state, "NOT_REQUESTED")
        self.assertEqual(package.authority_effect, "NONE")

    def test_cpk_preserves_exact_dmr_brq_bsa_resource_lineage(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        requirement_ids = {row.requirement_id for row in self.requirements}
        assessment_ids = {row.assessment_id for row in self.assessments}
        resource_ids = {self.resource_a.resource_id, self.resource_b.resource_id}
        for binding in package.bindings:
            self.assertIn(binding.broker_requirement_id, requirement_ids)
            self.assertTrue(binding.demand_requirement_id.startswith("DMR-"))
            self.assertTrue(set(binding.selected_assessment_ids) <= assessment_ids)
            self.assertTrue(set(binding.selected_resource_ids) <= resource_ids)

    def test_package_hash_detects_mutation(self):
        package = self.compose(
            [
                self.a_passive.assessment_id,
                self.b_evidence.assessment_id,
                self.a_auth.assessment_id,
            ]
        )
        payload = package.to_dict()
        parsed = capability_package_from_dict(payload)
        self.assertEqual(parsed.package_sha256, package.package_sha256)

        tampered = dict(payload)
        tampered["target_scope_state"] = "IN_SCOPE"
        with self.assertRaises(ValueError):
            capability_package_from_dict(tampered)


if __name__ == "__main__":
    unittest.main()

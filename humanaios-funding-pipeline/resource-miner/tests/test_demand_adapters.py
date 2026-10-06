import unittest

from resource_miner.demand import compile_broker_requirements, validate_demand_profile
from resource_miner.demand_adapters import (
    adapt_compliance_demand,
    adapt_federal_challenge,
    adapt_github_issue,
    adapt_grants_gov,
    adapt_sam_procurement,
)


OBSERVED = "2026-10-04T15:30:00Z"


class DemandAdapterValidationTests(unittest.TestCase):
    def test_01_github_issue_preserves_acceptance_criteria_and_no_work_authority(self):
        issue = {
            "number": 42,
            "title": "Add signed provenance verification",
            "body": (
                "Implement the verifier.\n\n"
                "- [ ] Verify artifact signatures\n"
                "- [ ] Bind the artifact digest to the receipt\n"
                "Fixes #41"
            ),
            "html_url": "https://github.com/example/project/issues/42",
            "state": "open",
            "labels": [{"name": "governance"}, {"name": "security"}],
            "milestone": {"title": "v1"},
        }
        opportunity, profile = adapt_github_issue(
            issue,
            repository="example/project",
            observed_at=OBSERVED,
        )
        validate_demand_profile(profile)
        self.assertEqual(profile.source_kind, "GITHUB_ISSUE")
        self.assertEqual(len(profile.deliverables), 2)
        self.assertEqual(
            profile.source_metadata["closing_issue_references"],
            ["41"],
        )
        self.assertFalse(profile.source_metadata["work_authorized"])
        self.assertTrue(all(r.mode == "REQUIRED" for r in profile.requirements))
        self.assertTrue(all(r.semantic_class == "DELIVERABLE" for r in profile.requirements))
        broker = compile_broker_requirements(profile=profile, opportunity=opportunity)
        self.assertEqual(len(broker), 2)
        self.assertTrue(all(r.authority_effect == "NONE" for r in broker))

    def test_02_grants_gov_keeps_applicant_eligibility_out_of_capability_brokerage(self):
        payload = {
            "data": {
                "id": 289999,
                "opportunityNumber": "TEST-2026-001",
                "opportunityTitle": "Independent AI Assurance Research",
                "owningAgencyCode": "HHS",
                "synopsis": {
                    "agencyName": "Health & Human Services",
                    "synopsisDesc": "Conduct independent evaluation research.",
                    "responseDateDesc": "November 15, 2026",
                    "costSharing": True,
                    "awardFloor": "50000",
                    "awardCeiling": "250000",
                    "applicantTypes": [
                        {"description": "Nonprofits"},
                        {"description": "Small businesses"},
                    ],
                    "fundingInstruments": [{"description": "Grant"}],
                    "fundingActivityCategories": [{"description": "Science and Technology"}],
                },
                "deliverables": [
                    "Independent evaluation report",
                    "Reproducible benchmark artifact",
                ],
            }
        }
        opportunity, profile = adapt_grants_gov(payload, observed_at=OBSERVED)
        validate_demand_profile(profile)
        eligibility = [r for r in profile.requirements if r.semantic_class == "ELIGIBILITY"]
        self.assertEqual(len(eligibility), 2)
        self.assertTrue(all(not r.brokerable for r in eligibility))
        self.assertIn("Nonprofits", profile.eligibility_predicates)
        self.assertIn("Small businesses", profile.eligibility_predicates)
        self.assertIn("award_ceiling:250000", profile.value_signals)
        self.assertTrue(profile.source_metadata["cost_sharing"])

        broker = compile_broker_requirements(profile=profile, opportunity=opportunity)
        self.assertEqual(len(broker), 2)
        self.assertTrue(
            all("Applicant eligibility" not in row.label for row in broker)
        )

    def test_03_sam_procurement_preserves_mandatory_set_aside_and_prohibition_semantics(self):
        record = {
            "noticeId": "SAM-NOTICE-001",
            "solicitationNumber": "ABC-26-R-001",
            "title": "Evidence Provenance Platform",
            "department": "Example Federal Agency",
            "type": "Solicitation",
            "description": "Provide an auditable provenance platform.",
            "naicsCode": "541512",
            "typeOfSetAsideDescription": "Small Business Set-Aside",
            "placeOfPerformance": "United States",
            "responseDeadLine": "2026-11-30T17:00:00-05:00",
            "mandatory_requirements": [
                "Provide cryptographic artifact verification",
                "Provide append-only audit evidence",
            ],
            "deliverables": ["Deployment package", "Verification report"],
            "prohibitions": ["Do not transmit controlled data to unapproved systems"],
            "submission_url": "https://sam.gov/opp/SAM-NOTICE-001",
        }
        opportunity, profile = adapt_sam_procurement(
            record,
            observed_at=OBSERVED,
            source_url="https://sam.gov/opp/SAM-NOTICE-001",
        )
        validate_demand_profile(profile)
        self.assertEqual(profile.source_kind, "SAM_PROCUREMENT")
        self.assertTrue(profile.source_metadata["mandatory_requirements_are_not_averageable"])
        eligibility = [r for r in profile.requirements if r.semantic_class == "ELIGIBILITY"]
        prohibited = [r for r in profile.requirements if r.mode == "PROHIBITED"]
        required = [r for r in profile.requirements if r.mode == "REQUIRED"]
        self.assertEqual(len(eligibility), 1)
        self.assertEqual(len(prohibited), 1)
        self.assertEqual(len(required), 5)
        self.assertIn("NAICS:541512", profile.constraints)

        broker = compile_broker_requirements(profile=profile, opportunity=opportunity)
        self.assertEqual(len(broker), 4)
        self.assertTrue(
            all("Set-aside eligibility" not in row.label for row in broker)
        )
        self.assertTrue(
            all("controlled data" not in row.objective.lower() for row in broker)
        )

    def test_04_federal_challenge_preserves_scoring_ip_eligibility_and_current_portal_state(self):
        record = {
            "challenge_id": "PRIZE-2026-01",
            "title": "Public Interest AI Challenge",
            "agency": "Example Agency",
            "objective": "Build an auditable public-interest AI prototype.",
            "eligibility": [
                "Private entities must maintain a primary place of business in the United States",
                "Individual entrants must be U.S. citizens or permanent residents",
            ],
            "deliverables": ["Prototype", "Technical report"],
            "evaluation_criteria": [
                {
                    "label": "Technical merit",
                    "weight": 40,
                    "description": "Quality and correctness of the technical approach.",
                },
                {
                    "label": "Public benefit",
                    "weight": 35,
                    "description": "Expected benefit to the public.",
                },
                {
                    "label": "Usability",
                    "weight": 25,
                    "description": "Ease of use and accessibility.",
                },
            ],
            "rules": ["Entrants must agree to the official competition rules"],
            "prohibitions": ["Do not include unlawfully obtained data"],
            "ip_terms": "Entrant retains background IP subject to official rules",
            "prizes": ["$100,000 total prize pool"],
            "submission_deadline": "2026-12-15T17:00:00-05:00",
            "submission_url": "https://agency.gov/challenge/apply",
        }
        opportunity, profile = adapt_federal_challenge(
            record,
            observed_at=OBSERVED,
            source_url="https://agency.gov/challenge",
        )
        validate_demand_profile(profile)
        scored = [r for r in profile.requirements if r.mode == "SCORED"]
        self.assertEqual([r.score_weight for r in scored], [40.0, 35.0, 25.0])
        self.assertEqual(len(profile.eligibility_predicates), 2)
        self.assertTrue(any(x.startswith("IP:") for x in profile.constraints))
        self.assertFalse(profile.source_metadata["legacy_challenge_gov_portal"])
        self.assertEqual(
            profile.source_metadata["challenge_gov_sunset_date"],
            "2026-03-30",
        )
        broker = compile_broker_requirements(profile=profile, opportunity=opportunity)
        self.assertEqual(len(broker), 2)
        self.assertTrue(
            all("submission_artifact" in r.required_affordances for r in broker)
        )

    def test_05_compliance_adapter_preserves_normative_operators(self):
        record = {
            "control_set_id": "CTRL-SET-001",
            "title": "Evidence Integrity Controls",
            "issuer": "Example Standards Body",
            "objective": "Screen systems for evidence integrity controls.",
            "requirements": [
                {
                    "label": "Signature verification",
                    "operator": "MUST",
                    "statement": "The system MUST verify artifact signatures.",
                    "required_affordances": ["signature_verification"],
                },
                {
                    "label": "No silent provenance rewrite",
                    "operator": "MUST NOT",
                    "statement": "The system MUST NOT silently rewrite provenance history.",
                },
                {
                    "label": "Transparency log",
                    "operator": "SHOULD",
                    "statement": "The system SHOULD use an external transparency anchor.",
                    "required_affordances": ["transparency_log"],
                },
                {
                    "label": "Optional hardware attestation",
                    "operator": "MAY",
                    "statement": "The system MAY use hardware-backed attestation.",
                    "required_affordances": ["hardware_attestation"],
                },
                {
                    "label": "High-risk review",
                    "operator": "IF",
                    "condition": "risk_tier=HIGH",
                    "statement": "IF risk tier is HIGH, require independent review.",
                    "required_affordances": ["independent_review"],
                },
                {
                    "label": "Evidence completeness score",
                    "operator": "SHOULD",
                    "weight": 20,
                    "statement": "Score evidence completeness.",
                    "required_affordances": ["evidence_scoring"],
                },
            ],
        }
        opportunity, profile = adapt_compliance_demand(
            record,
            observed_at=OBSERVED,
            source_url="https://standards.example/control-set-001",
        )
        validate_demand_profile(profile)
        modes = {r.label: r.mode for r in profile.requirements}
        self.assertEqual(modes["Signature verification"], "REQUIRED")
        self.assertEqual(modes["No silent provenance rewrite"], "PROHIBITED")
        self.assertEqual(modes["Transparency log"], "PREFERRED")
        self.assertEqual(modes["Optional hardware attestation"], "OPTIONAL")
        self.assertEqual(modes["High-risk review"], "CONDITIONAL")
        self.assertEqual(modes["Evidence completeness score"], "SCORED")
        self.assertFalse(profile.source_metadata["economic_opportunity"])
        self.assertTrue(profile.source_metadata["control_match_is_not_compliance_verified"])

        broker = compile_broker_requirements(profile=profile, opportunity=opportunity)
        self.assertEqual(len(broker), 5)
        self.assertTrue(
            all("silently rewrite provenance" not in row.objective.lower() for row in broker)
        )

    def test_all_adapters_share_same_dmd_schema_and_no_authority(self):
        profiles = []

        _, github = adapt_github_issue(
            {
                "number": 1,
                "title": "Do thing",
                "body": "- [ ] Produce artifact",
                "html_url": "https://github.com/example/repo/issues/1",
            },
            repository="example/repo",
            observed_at=OBSERVED,
        )
        profiles.append(github)

        _, grant = adapt_grants_gov(
            {
                "data": {
                    "id": 1,
                    "opportunityTitle": "Grant",
                    "synopsis": {
                        "agencyName": "Agency",
                        "synopsisDesc": "Do research",
                        "applicantTypes": [{"description": "Nonprofits"}],
                    },
                }
            },
            observed_at=OBSERVED,
        )
        profiles.append(grant)

        _, sam = adapt_sam_procurement(
            {
                "noticeId": "1",
                "title": "Procurement",
                "description": "Provide service",
            },
            observed_at=OBSERVED,
            source_url="https://sam.gov/opp/1",
        )
        profiles.append(sam)

        _, challenge = adapt_federal_challenge(
            {
                "challenge_id": "1",
                "title": "Challenge",
                "objective": "Build prototype",
                "deliverables": ["Prototype"],
            },
            observed_at=OBSERVED,
            source_url="https://agency.gov/challenge/1",
        )
        profiles.append(challenge)

        _, compliance = adapt_compliance_demand(
            {
                "control_set_id": "1",
                "title": "Control",
                "requirements": [
                    {
                        "operator": "MUST",
                        "statement": "The system MUST log evidence.",
                        "required_affordances": ["evidence_logging"],
                    }
                ],
            },
            observed_at=OBSERVED,
            source_url="https://standard.example/control/1",
        )
        profiles.append(compliance)

        self.assertTrue(
            all(profile.schema == "humanaios.demand-profile.v1" for profile in profiles)
        )
        self.assertTrue(all(profile.profile_id.startswith("DMD-") for profile in profiles))
        self.assertTrue(all(profile.authority_effect == "NONE" for profile in profiles))


if __name__ == "__main__":
    unittest.main()

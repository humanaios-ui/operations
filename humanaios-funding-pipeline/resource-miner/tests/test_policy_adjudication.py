import unittest

from resource_miner.dpp_action_contract import default_dpp_action_contract
from resource_miner.policy_adjudication import adjudicate_ranked_candidate
from resource_miner.security_authorization import AuthorizationState, TestingMode


PROGRAM = {
    "id": "9",
    "type": "program",
    "attributes": {
        "handle": "fixture",
        "name": "Fixture Program",
        "policy": "Use test accounts. Do not degrade availability.",
        "submission_state": "open",
        "offers_bounties": True,
        "open_scope": False,
        "gold_standard_safe_harbor": True,
    },
}

SCOPES = [
    {
        "id": "scope-1",
        "type": "structured-scope",
        "attributes": {
            "asset_identifier": "web.example.test",
            "asset_type": "DOMAIN",
            "eligible_for_submission": True,
            "eligible_for_bounty": True,
            "instruction": "Use only accounts you control.",
            "max_severity": "high",
        },
    }
]

EXCLUSIONS = [
    {
        "id": "ex-1",
        "type": "scope-exclusion",
        "attributes": {
            "category": "Denial of Service",
            "details": "Availability-impacting tests are excluded.",
        },
    }
]

PORTFOLIO = {
    "ranked_queue": {
        "entries": [
            {
                "program_handle": "fixture",
                "program_name": "Fixture Program",
                "scope_id": "scope-1",
                "asset_identifier": "web.example.test",
                "asset_type": "DOMAIN",
                "review_state": "READY_FOR_POLICY_AND_METHOD_REVIEW",
                "authorization_state": "NOT_EVALUATED",
                "readiness_score": 95.0,
            }
        ]
    }
}


class FakeClient:
    def find_program(self, handle, page_size=100):
        return PROGRAM

    def get_structured_scopes(self, handle, page_size=100):
        return SCOPES

    def get_scope_exclusions(self, handle):
        return EXCLUSIONS




DPP_PROGRAM = {
    **PROGRAM,
    "attributes": {
        **PROGRAM["attributes"],
        "policy": """
## Data Protection Program
This program is focused on passive monitoring and recon of our data and does not permit active hunting.
### What is allowed (Data Protection Program):
Observing publicly accessible data exposure.
Monitoring websites/apps for exposed information.
Scanning for exposed configuration files, API keys, or access tokens.
### What is not allowed (Data Protection Program):
Active exploitation or vulnerability testing on external systems.
Any actions beyond read-only verification of Eternal data exposure.
""",
    },
}


class DPPClient(FakeClient):
    def find_program(self, handle, page_size=100):
        return DPP_PROGRAM


class PolicyAdjudicationTests(unittest.TestCase):
    def test_unknown_method_fails_closed_after_fresh_evidence(self):
        result = adjudicate_ranked_candidate(FakeClient(), PORTFOLIO)
        self.assertTrue(result["scope_binding"]["valid"])
        self.assertEqual(result["fresh_scope_graph"]["exclusions_state"], "OBSERVED")
        self.assertEqual(
            result["authorization_decision"]["state"],
            AuthorizationState.SCOPE_CLARIFICATION_REQUIRED.value,
        )
        self.assertIn(
            "testing_method_permission_ambiguous",
            result["authorization_decision"]["reasons"],
        )
        self.assertEqual(result["execution_capability"], "NONE")

    def test_explicit_disallow_is_not_authorized(self):
        result = adjudicate_ranked_candidate(
            FakeClient(),
            PORTFOLIO,
            method_allowed=False,
            human_authorization_ref="issue:fixture#human",
        )
        self.assertEqual(
            result["authorization_decision"]["state"],
            AuthorizationState.NOT_AUTHORIZED.value,
        )

    def test_dpp_action_contract_derives_method_permission_from_fresh_evidence(self):
        result = adjudicate_ranked_candidate(
            DPPClient(),
            PORTFOLIO,
            dpp_action_contract=default_dpp_action_contract(),
            mode=TestingMode.PASSIVE_RECON,
        )
        self.assertTrue(result["scope_binding"]["valid"])
        self.assertTrue(result["method_review"]["method_allowed"])
        self.assertEqual(
            result["method_review"]["permission_inference"],
            "ACTION_CONTRACT",
        )
        self.assertEqual(
            result["method_review"]["action_contract_review"]["state"],
            "METHOD_ALLOWED",
        )
        # Method permission is not execution authorization; human evidence is absent.
        self.assertEqual(
            result["authorization_decision"]["state"],
            AuthorizationState.NOT_AUTHORIZED.value,
        )
        self.assertIn(
            "human_authorization_evidence_absent",
            result["authorization_decision"]["reasons"],
        )

    def test_stale_scope_binding_forces_clarification(self):
        stale = {
            "ranked_queue": {
                "entries": [
                    {
                        **PORTFOLIO["ranked_queue"]["entries"][0],
                        "scope_id": "old-scope-id",
                    }
                ]
            }
        }
        result = adjudicate_ranked_candidate(
            FakeClient(),
            stale,
            method_allowed=True,
            human_authorization_ref="issue:fixture#human",
            mode=TestingMode.PASSIVE_RECON,
        )
        self.assertFalse(result["scope_binding"]["valid"])
        self.assertEqual(
            result["authorization_decision"]["state"],
            AuthorizationState.SCOPE_CLARIFICATION_REQUIRED.value,
        )
        self.assertIn(
            "program_currentness_evidence_missing",
            result["authorization_decision"]["reasons"],
        )


if __name__ == "__main__":
    unittest.main()

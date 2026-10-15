import unittest

from resource_miner.dpp_action_contract import (
    DPPActionContract,
    default_dpp_action_contract,
    evaluate_dpp_action_contract,
)
from resource_miner.security_scope import build_scope_graph


PROGRAM = {
    "id": "1",
    "attributes": {
        "handle": "fixture",
        "name": "Fixture",
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
        "submission_state": "open",
    },
}

SCOPES = [
    {
        "id": "scope-1",
        "attributes": {
            "asset_identifier": "https://example.test",
            "asset_type": "URL",
            "eligible_for_submission": True,
            "eligible_for_bounty": True,
            "instruction": None,
        },
    }
]

ENTRY = {
    "scope_id": "scope-1",
    "asset_identifier": "https://example.test",
    "asset_type": "URL",
}


class DPPActionContractTests(unittest.TestCase):
    def graph(self, instruction=None):
        scopes = [dict(SCOPES[0])]
        scopes[0]["attributes"] = dict(scopes[0]["attributes"])
        scopes[0]["attributes"]["instruction"] = instruction
        return build_scope_graph(
            PROGRAM,
            scopes,
            [],
            exclusions_state="OBSERVED",
        )

    def test_default_contract_is_allowed_by_fresh_dpp_policy(self):
        review = evaluate_dpp_action_contract(
            ENTRY,
            self.graph(),
            default_dpp_action_contract(),
        )
        self.assertTrue(review["method_allowed"])
        self.assertEqual(review["state"], "METHOD_ALLOWED")
        self.assertEqual(review["authority_effect"], "NONE")
        self.assertEqual(review["execution_capability"], "NONE")

    def test_prohibited_behavior_fails_closed(self):
        contract = DPPActionContract(high_volume_scanning=True)
        review = evaluate_dpp_action_contract(
            ENTRY,
            self.graph(),
            contract,
        )
        self.assertFalse(review["method_allowed"])
        self.assertIn(
            "contract_prohibited:high_volume_scanning",
            review["reasons"],
        )

    def test_scope_instruction_conflict_fails_closed(self):
        review = evaluate_dpp_action_contract(
            ENTRY,
            self.graph("Do not scan this asset."),
            default_dpp_action_contract(),
        )
        self.assertFalse(review["method_allowed"])
        self.assertIn(
            "scope_instruction_conflict:do not scan",
            review["reasons"],
        )

    def test_non_web_surface_requires_separate_method(self):
        entry = {**ENTRY, "asset_type": "SOURCE_CODE"}
        review = evaluate_dpp_action_contract(
            entry,
            self.graph(),
            default_dpp_action_contract(),
        )
        self.assertFalse(review["method_allowed"])
        self.assertIn(
            "asset_type_not_supported:SOURCE_CODE",
            review["reasons"],
        )


if __name__ == "__main__":
    unittest.main()

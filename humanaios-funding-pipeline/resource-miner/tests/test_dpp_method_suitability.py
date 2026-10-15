import unittest

from resource_miner.dpp_method_suitability import evaluate_dpp_method_suitability


POLICY = """
## Data Protection Program
This program is focused on passive monitoring and recon of our data and does not permit active hunting.
### What is allowed (Data Protection Program):
Observing publicly accessible data exposure.
Monitoring websites/apps for exposed information.
Scanning for exposed configuration files, API keys, or access tokens.
### What is not allowed (Data Protection Program):
Active exploitation or vulnerability testing on external systems.
Any actions beyond read-only verification of Eternal data exposure.
"""


def payload(asset_type="URL", instruction=""):
    return {
        "portfolio": {
            "programs": [
                {
                    "graph": {
                        "policy": POLICY,
                        "assets": [
                            {
                                "scope_id": "scope-1",
                                "instruction": instruction,
                            }
                        ],
                    }
                }
            ]
        },
        "ranked_queue": {
            "entries": [
                {
                    "scope_id": "scope-1",
                    "asset_type": asset_type,
                    "review_mode_candidate": "WEB_REVIEW",
                    "review_state": "READY_FOR_POLICY_AND_METHOD_REVIEW",
                }
            ]
        },
    }


class DPPMethodSuitabilityTests(unittest.TestCase):
    def test_web_surface_is_conditionally_suitable(self):
        result = evaluate_dpp_method_suitability(payload())
        rendered = result.to_dict()
        self.assertTrue(rendered["summary"]["policy_support_present"])
        self.assertEqual(
            rendered["entries"][0]["suitability_state"],
            "CONDITIONALLY_SUITABLE",
        )
        self.assertEqual(rendered["summary"]["candidate_ready_ranks"], [1])
        self.assertEqual(result.authority_effect, "NONE")
        self.assertEqual(result.execution_capability, "NONE")

    def test_scope_instruction_conflict_fails_closed(self):
        result = evaluate_dpp_method_suitability(
            payload(instruction="Do not test or scan this asset.")
        )
        self.assertEqual(
            result.entries[0].suitability_state,
            "SCOPE_INSTRUCTION_CONFLICT",
        )

    def test_source_code_requires_objective_evidence(self):
        result = evaluate_dpp_method_suitability(payload(asset_type="SOURCE_CODE"))
        self.assertEqual(
            result.entries[0].suitability_state,
            "OBJECTIVE_EVIDENCE_REQUIRED",
        )

    def test_policy_support_must_be_explicit(self):
        p = payload()
        p["portfolio"]["programs"][0]["graph"]["policy"] = "Ordinary bug bounty policy."
        result = evaluate_dpp_method_suitability(p)
        self.assertEqual(
            result.entries[0].suitability_state,
            "POLICY_SUPPORT_NOT_ESTABLISHED",
        )


if __name__ == "__main__":
    unittest.main()

import unittest

from resource_miner.hackerone_policy_screen import screen_program_policies


def program(handle, policy, state="open"):
    return {
        "id": handle,
        "type": "program",
        "attributes": {
            "handle": handle,
            "name": handle.title(),
            "policy": policy,
            "submission_state": state,
        },
    }


class FakeClient:
    def list_programs(self, page_size=100):
        return [
            program(
                "dpp",
                "Data Protection Program. This program is focused on passive monitoring and recon of our data.",
            ),
            program(
                "passive",
                "Passive reconnaissance is permitted for publicly accessible metadata only.",
            ),
            program(
                "ordinary",
                "Please test only assets listed in scope.",
            ),
        ]


class HackerOnePolicyScreenTests(unittest.TestCase):
    def test_prefilter_finds_explicit_dpp_and_other_passive_signals(self):
        result = screen_program_policies(FakeClient())
        payload = result.to_dict()

        self.assertEqual(payload["summary"]["programs_observed"], 3)
        self.assertEqual(payload["summary"]["explicit_dpp_passive_matches"], 1)
        self.assertEqual(payload["summary"]["other_passive_policy_signals"], 1)
        self.assertEqual(payload["summary"]["match_count"], 2)
        self.assertEqual(result.authority_effect, "NONE")
        self.assertEqual(result.execution_capability, "NONE")

    def test_prefilter_does_not_fetch_structured_scope(self):
        class GuardClient(FakeClient):
            def get_structured_scopes(self, *args, **kwargs):
                self.fail("policy prefilter must not hydrate structured scope")

        result = screen_program_policies(GuardClient())
        self.assertEqual(result.programs_observed, 3)

    def test_max_programs_bounds_metadata_screen(self):
        result = screen_program_policies(FakeClient(), max_programs=1)
        self.assertEqual(result.programs_observed, 1)
        self.assertEqual(len(result.matches), 1)


if __name__ == "__main__":
    unittest.main()

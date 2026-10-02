import unittest

from resource_miner.security_authorization import (
    AuthorizationState,
    SecurityAuthorizationRequest,
    TestingMode,
    authorize_security_action,
)
from resource_miner.security_scope import build_scope_graph
from resource_miner.sources.hackerone import HackerOneClient, discover


PROGRAM = {
    "id": "9",
    "type": "program",
    "attributes": {
        "handle": "acme",
        "name": "Acme",
        "policy": "Use test accounts. No denial of service.",
        "submission_state": "open",
        "offers_bounties": True,
        "open_scope": False,
        "gold_standard_safe_harbor": True,
    },
}
SCOPES = [
    {
        "id": "57",
        "type": "structured-scope",
        "attributes": {
            "asset_identifier": "api.example.com",
            "asset_type": "URL",
            "eligible_for_bounty": True,
            "eligible_for_submission": True,
            "instruction": "Test only your own accounts.",
            "max_severity": "critical",
            "reference": "H001001",
            "updated_at": "2026-10-01T00:00:00Z",
        },
    },
    {
        "id": "58",
        "type": "structured-scope",
        "attributes": {
            "asset_identifier": "legacy.example.com",
            "asset_type": "URL",
            "eligible_for_bounty": False,
            "eligible_for_submission": False,
            "instruction": "Out of scope.",
            "max_severity": "none",
            "updated_at": "2026-10-01T00:00:00Z",
        },
    },
]
EXCLUSIONS = [
    {
        "id": "1",
        "type": "scope-exclusion",
        "attributes": {
            "category": "Denial of Service",
            "details": "Do not degrade availability.",
            "updated_at": "2026-10-01T00:00:00Z",
        },
    }
]


class HackerOneAdapterTests(unittest.TestCase):
    def test_client_follows_links_next_without_target_requests(self):
        calls = []

        def transport(url, headers):
            calls.append(url)
            self.assertIn("Authorization", headers)
            if "page%5Bnumber%5D=1" in url:
                return {
                    "data": [PROGRAM],
                    "links": {"next": "https://api.hackerone.com/v1/hackers/programs?page[number]=2&page[size]=1"},
                }
            return {"data": [], "links": {}}

        client = HackerOneClient(username="token-id", token="secret", transport=transport)
        rows = client.list_programs(page_size=1)
        self.assertEqual([row["id"] for row in rows], ["9"])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all("api.hackerone.com" in url for url in calls))

    def test_discover_marks_actual_bounty_program_as_bounty(self):
        class FakeClient:
            def list_programs(self, page_size=100):
                return [PROGRAM]

        rows = list(discover(client=FakeClient()))
        self.assertEqual(len(rows), 1)
        self.assertIn("bounty", rows[0].resource_types)
        self.assertFalse(rows[0].eligibility_assessed)
        self.assertEqual(rows[0].source_name, "HackerOne")


class ScopeGraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_scope_graph(PROGRAM, SCOPES, EXCLUSIONS, observed_at="2026-10-02T00:00:00Z")

    def test_graph_preserves_scope_and_exclusions_without_authority(self):
        self.assertEqual(self.graph.schema, "humanaios.hackerone-scope-graph.v1")
        self.assertEqual(self.graph.authority_effect, "NONE")
        self.assertEqual(len(self.graph.assets), 2)
        self.assertEqual(self.graph.assets[0].asset_identifier, "api.example.com")
        self.assertTrue(self.graph.assets[0].eligible_for_submission)
        self.assertEqual(self.graph.exclusions[0].category, "Denial of Service")


class SecurityAuthorizationGateTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_scope_graph(PROGRAM, SCOPES, EXCLUSIONS, observed_at="2026-10-02T00:00:00Z")

    def request(self, **overrides):
        data = dict(
            asset_identifier="api.example.com",
            mode=TestingMode.MANUAL_TESTING,
            program_current_verified=True,
            policy_reviewed=True,
            method_allowed=True,
            human_authorized=True,
        )
        data.update(overrides)
        return SecurityAuthorizationRequest(**data)

    def test_authorizes_only_when_all_required_inputs_are_explicit(self):
        decision = authorize_security_action(self.graph, self.request())
        self.assertEqual(decision.state, AuthorizationState.MANUAL_TESTING)
        self.assertTrue(decision.authorized)
        self.assertEqual(decision.execution_capability, "NONE")
        self.assertEqual(decision.authority_effect, "NONE")

    def test_unknown_asset_fails_closed_to_scope_clarification(self):
        decision = authorize_security_action(
            self.graph,
            self.request(asset_identifier="unknown.example.com"),
        )
        self.assertEqual(decision.state, AuthorizationState.SCOPE_CLARIFICATION_REQUIRED)

    def test_out_of_scope_asset_is_not_authorized(self):
        decision = authorize_security_action(
            self.graph,
            self.request(asset_identifier="legacy.example.com"),
        )
        self.assertEqual(decision.state, AuthorizationState.NOT_AUTHORIZED)

    def test_ambiguous_method_fails_closed(self):
        decision = authorize_security_action(self.graph, self.request(method_allowed=None))
        self.assertEqual(decision.state, AuthorizationState.SCOPE_CLARIFICATION_REQUIRED)

    def test_missing_human_authorization_is_denied(self):
        decision = authorize_security_action(self.graph, self.request(human_authorized=False))
        self.assertEqual(decision.state, AuthorizationState.NOT_AUTHORIZED)

    def test_prohibited_actions_override_other_permissions(self):
        decision = authorize_security_action(self.graph, self.request(denial_of_service=True))
        self.assertEqual(decision.state, AuthorizationState.NOT_AUTHORIZED)
        self.assertIn("prohibited:denial_of_service", decision.reasons)

    def test_excluded_finding_category_is_denied(self):
        decision = authorize_security_action(
            self.graph,
            self.request(requested_finding_category=" denial   of service "),
        )
        self.assertEqual(decision.state, AuthorizationState.NOT_AUTHORIZED)
        self.assertIn("scope_exclusion:Denial of Service", decision.reasons)

    def test_stale_program_state_requires_clarification(self):
        decision = authorize_security_action(
            self.graph,
            self.request(program_current_verified=False),
        )
        self.assertEqual(decision.state, AuthorizationState.SCOPE_CLARIFICATION_REQUIRED)

    def test_closed_program_is_denied(self):
        closed = build_scope_graph(
            {**PROGRAM, "attributes": {**PROGRAM["attributes"], "submission_state": "paused"}},
            SCOPES,
            EXCLUSIONS,
        )
        decision = authorize_security_action(closed, self.request())
        self.assertEqual(decision.state, AuthorizationState.NOT_AUTHORIZED)


if __name__ == "__main__":
    unittest.main()

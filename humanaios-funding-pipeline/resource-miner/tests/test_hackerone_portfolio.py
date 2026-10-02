import unittest

from resource_miner.hackerone_portfolio import (
    HackerOnePortfolioSnapshot,
    PortfolioProgramObservation,
    scan_portfolio,
)
from resource_miner.investigation_queue import build_ranked_queue
from resource_miner.security_capability import (
    OBSERVED_AVAILABLE,
    OBSERVED_UNAVAILABLE,
    UNKNOWN,
    profile_from_machine_graph,
    unknown_capability_profile,
)
from resource_miner.security_scope import build_scope_graph


def capability_fixture():
    return {
        "observed_at": "2026-10-02T19:00:00+00:00",
        "nodes": [
            {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "python3"}},
            {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "curl"}},
            {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "git"}},
            {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "openssl"}},
            {"type": "Tool", "state": OBSERVED_UNAVAILABLE, "observed": {"name": "adb"}},
            {"type": "Tool", "state": OBSERVED_AVAILABLE, "observed": {"name": "java"}},
        ],
        "omissions": [],
    }


def program_fixture(state="open"):
    return {
        "id": "1",
        "type": "program",
        "attributes": {
            "handle": "fixture",
            "name": "Fixture Program",
            "policy": "Fixture policy.",
            "submission_state": state,
            "offers_bounties": True,
            "open_scope": False,
            "gold_standard_safe_harbor": True,
        },
    }


def scope_fixture():
    return [
        {
            "id": "web-1",
            "type": "structured-scope",
            "attributes": {
                "asset_identifier": "web.example.test",
                "asset_type": "DOMAIN",
                "eligible_for_submission": True,
                "eligible_for_bounty": True,
                "instruction": None,
                "max_severity": "high",
            },
        },
        {
            "id": "mobile-1",
            "type": "structured-scope",
            "attributes": {
                "asset_identifier": "com.example.fixture",
                "asset_type": "ANDROID_PLAY_STORE",
                "eligible_for_submission": True,
                "eligible_for_bounty": True,
                "instruction": None,
                "max_severity": "high",
            },
        },
        {
            "id": "closed-1",
            "type": "structured-scope",
            "attributes": {
                "asset_identifier": "old.example.test",
                "asset_type": "DOMAIN",
                "eligible_for_submission": False,
                "eligible_for_bounty": False,
                "instruction": None,
                "max_severity": "none",
            },
        },
    ]


class CapabilityProfileTests(unittest.TestCase):
    def test_machine_graph_evidence_is_not_assumed(self):
        profile = profile_from_machine_graph(capability_fixture(), source="fixture")
        self.assertEqual(profile.get("web_http_review").state, OBSERVED_AVAILABLE)
        self.assertEqual(profile.get("source_code_review").state, OBSERVED_AVAILABLE)
        self.assertEqual(profile.get("android_app_review").state, OBSERVED_UNAVAILABLE)
        self.assertEqual(profile.get("hardware_iot_review").state, UNKNOWN)

    def test_no_snapshot_means_unknown(self):
        profile = unknown_capability_profile()
        self.assertTrue(all(x.state == UNKNOWN for x in profile.capabilities.values()))


class FakeClient:
    def list_programs(self, page_size=100):
        return [program_fixture()]

    def get_program(self, handle):
        return program_fixture()

    def get_structured_scopes(self, handle, page_size=100):
        return scope_fixture()

    def get_scope_exclusions(self, handle):
        return []


class PortfolioTests(unittest.TestCase):
    def test_portfolio_hydration_has_no_execution_authority(self):
        snapshot = scan_portfolio(FakeClient())
        self.assertEqual(len(snapshot.programs), 1)
        self.assertEqual(snapshot.programs[0].state, "OBSERVED")
        self.assertEqual(snapshot.execution_capability, "NONE")
        self.assertEqual(snapshot.authority_effect, "NONE")

    def test_rank_prefers_evidenced_review_readiness(self):
        graph = build_scope_graph(program_fixture(), scope_fixture(), [])
        portfolio = HackerOnePortfolioSnapshot(
            observed_at="2026-10-02T19:00:00+00:00",
            programs=[PortfolioProgramObservation(handle="fixture", state="OBSERVED", graph=graph)],
        )
        profile = profile_from_machine_graph(capability_fixture(), source="fixture")
        queue = build_ranked_queue(portfolio, profile)
        by_id = {entry.scope_id: entry for entry in queue.entries}
        self.assertEqual(by_id["web-1"].review_state, "READY_FOR_POLICY_AND_METHOD_REVIEW")
        self.assertEqual(by_id["mobile-1"].review_state, "CAPABILITY_UNAVAILABLE")
        self.assertEqual(by_id["closed-1"].review_state, "BLOCKED_BY_SCOPE_STATE")
        self.assertEqual(by_id["closed-1"].readiness_score, 0.0)
        self.assertGreater(by_id["web-1"].readiness_score, by_id["mobile-1"].readiness_score)
        self.assertTrue(all(entry.authorization_state == "NOT_EVALUATED" for entry in queue.entries))
        self.assertEqual(queue.execution_capability, "NONE")

    def test_unknown_profile_never_marks_entry_ready(self):
        graph = build_scope_graph(program_fixture(), scope_fixture(), [])
        portfolio = HackerOnePortfolioSnapshot(
            observed_at="2026-10-02T19:00:00+00:00",
            programs=[PortfolioProgramObservation(handle="fixture", state="OBSERVED", graph=graph)],
        )
        queue = build_ranked_queue(portfolio, unknown_capability_profile())
        web = next(entry for entry in queue.entries if entry.scope_id == "web-1")
        self.assertEqual(web.review_state, "CAPABILITY_EVIDENCE_REQUIRED")
        self.assertEqual(web.authorization_state, "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()

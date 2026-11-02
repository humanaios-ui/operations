"""Guardrails for read-only source experiment; no network in unit tests."""
import unittest
from datetime import date
from types import SimpleNamespace as R
from experiments.three_source_observation import public_source, benefit_kind, screen

def candidate(**changes):
    row = dict(resource_id="RES-TEST", title="Test bounty",
        source_name="GitHub Issues", source_url="https://github.com/o/r/issues/4",
        resource_types=["bounty"], route="VERIFY_NOW", status="DISCOVERED",
        deadline=None, cash_mentions_usd=[3000], need_matches=[R(score=.89)],
        requirement_matches=[], raw={}, discovered_at="2026-10-13T20:00:00Z",
        discovery_method="github_search:test")
    row.update(changes)
    return R(**row)

class ThreeSourceContractTest(unittest.TestCase):
    def test_bounty_does_not_become_earnings(self):
        result = screen(candidate(), date(2026,10,13))
        self.assertIsNone(result["expected_net_usd"])
        self.assertIsNone(result["realized_usd"])
        self.assertEqual(result["authorization"], "NOT_GRANTED")

    def test_assignment_blocks_prioritization(self):
        result = screen(candidate(raw={"assignee": {"login":"another"}}), date(2026,10,13))
        self.assertEqual(result["verification_state"], "CHECK_ASSIGNED_OR_CLAIMED")
        self.assertEqual(result["verification_relevance_not_profit"], 0)

    def test_expired_archived_despite_high_score(self):
        result = screen(candidate(deadline="2026-10-11"), date(2026,10,13))
        self.assertEqual(result["verification_state"], "ARCHIVE_EXPIRED")

    def test_credits_are_not_cash(self):
        self.assertEqual(benefit_kind(["compute_credit"]), "NONCASH_CAPACITY")

    def test_provider_host_binding(self):
        self.assertTrue(public_source("https://dev.to/devteam/example", "devto"))
        self.assertFalse(public_source("https://evil.example/devteam/example", "devto"))
        self.assertFalse(public_source("https://github.com.attacker.example/o/r/issues/4", "github"))

    def test_old_dev_post_without_deadline_requires_currentness(self):
        r = screen(candidate(source_name="DEV Community",
             source_url="https://dev.to/devteam/old-challenge",
             resource_types=["competition"], published_at="2026-09-24T12:00:00Z"),
             date(2026,10,13))
        self.assertEqual(r["verification_state"], "HOLD_CURRENTNESS")
        self.assertEqual(r["verification_relevance_not_profit"], 0)

    def test_secondary_github_list_not_a_primary_bounty(self):
        r = screen(candidate(title="📋 2 open bounties right now"),
                   date(2026,10,13))
        self.assertEqual(r["verification_state"], "HOLD_SECONDARY_AGGREGATOR")
        self.assertEqual(r["verification_relevance_not_profit"], 0)

    def test_unknown_provider_excluded(self):
        self.assertIsNone(screen(candidate(source_name="Unauthorized Site"), date(2026,10,13)))

    def test_no_ranking_from_amount_only(self):
        result = screen(candidate(need_matches=[], cash_mentions_usd=[999999]), date(2026,10,13))
        self.assertEqual(result["verification_relevance_not_profit"], 0)

if __name__ == "__main__":
    unittest.main()

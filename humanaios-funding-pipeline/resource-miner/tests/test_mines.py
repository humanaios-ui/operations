import unittest
from pathlib import Path

from resource_miner.mines import (
    bind_opportunity,
    load_mines,
    resolve_mines,
    stable_mine_id,
    stable_opportunity_id,
)
from resource_miner.models import ResourceMine
from resource_miner.normalize import normalize_generic
from resource_miner.sources.configured_mine import discover as discover_configured
from resource_miner.sources.github_repository import discover as discover_repository

ROOT = Path(__file__).resolve().parents[1]


class PersistentMineTests(unittest.TestCase):
    def test_registry_loads_opportunity_and_repository_roles_separately(self):
        mines = load_mines(ROOT / "data" / "mines.seed.json")
        by_name = {mine.name: mine for mine in mines}
        self.assertIn("OPPORTUNITY_SOURCE", by_name["Microsoft for Startups"].roles)
        self.assertIn("OPPORTUNITY_SOURCE", by_name["HackerOne"].roles)
        self.assertNotIn("OPPORTUNITY_SOURCE", by_name["humanaios-ui/operations"].roles)
        self.assertIn("EVIDENCE_SOURCE", by_name["humanaios-ui/operations"].roles)
        self.assertIn("GOVERNED_SYSTEM", by_name["humanaios-ui/operations"].roles)

    def test_mine_id_is_stable_across_tracking_noise(self):
        a = stable_mine_id("https://example.com/mine?utm_source=x")
        b = stable_mine_id("https://example.com/mine")
        self.assertEqual(a, b)

    def test_opportunity_token_identity_survives_title_change(self):
        mine = ResourceMine(
            mine_id="MINE-TEST",
            name="Example",
            mine_kind="PROGRAM_PLATFORM",
            canonical_url="https://example.com",
            resolver="configured_mine",
            roles=["OPPORTUNITY_SOURCE"],
        )
        first = normalize_generic(
            title="Old title",
            url="https://example.com/benefit",
            source_name="Example",
            discovery_method="test",
            opportunity_kind="credit",
            opportunity_identity="benefit:credit:1",
        )
        second = normalize_generic(
            title="New wording and new value",
            url="https://example.com/benefit",
            source_name="Example",
            discovery_method="test",
            opportunity_kind="credit",
            opportunity_identity="benefit:credit:1",
        )
        bind_opportunity(mine, first, opportunity_source_kind="test")
        bind_opportunity(mine, second, opportunity_source_kind="test")
        self.assertEqual(first.opportunity_id, second.opportunity_id)
        self.assertEqual(first.opportunity_token, second.opportunity_token)

    def test_same_endpoint_can_emit_distinct_opportunities_by_kind(self):
        mine_id = "MINE-TEST"
        identity = "https://example.com/benefits"
        credit = stable_opportunity_id(mine_id, identity, "startup_credit")
        marketplace = stable_opportunity_id(mine_id, identity, "marketplace_access")
        self.assertNotEqual(credit, marketplace)

    def test_scope_asset_identity_prevents_hackerone_program_collapse(self):
        first = stable_opportunity_id(
            "MINE-H1", "hackerone:acme:scope:57", "hackerone_bounty_scope"
        )
        second = stable_opportunity_id(
            "MINE-H1", "hackerone:acme:scope:58", "hackerone_bounty_scope"
        )
        self.assertNotEqual(first, second)

    def test_configured_mine_reobserves_endpoint_and_hashes_evidence(self):
        mine = ResourceMine(
            mine_id="MINE-CONFIG",
            name="Configured",
            mine_kind="PROGRAM_PLATFORM",
            canonical_url="https://example.com",
            resolver="configured_mine",
            roles=["OPPORTUNITY_SOURCE"],
            config={
                "opportunities": [
                    {
                        "title": "Credit",
                        "url": "https://example.com/credit",
                        "opportunity_kind": "credit",
                        "source_category": "compute_credit",
                    }
                ]
            },
        )

        def transport(url):
            self.assertEqual(url, "https://example.com/credit")
            return {
                "status": 200,
                "final_url": url,
                "content_type": "text/html",
                "body": b"version-1",
            }

        rows = list(discover_configured(mine, transport=transport))
        self.assertEqual(len(rows), 1)
        self.assertTrue(any(e.kind == "mine_observation" for e in rows[0].evidence))
        self.assertEqual(rows[0].opportunity_identity, "https://example.com/credit")

    def test_repository_resolver_requires_explicit_opportunity_signal(self):
        mine = ResourceMine(
            mine_id="MINE-REPO",
            name="owner/repo",
            mine_kind="GITHUB_REPOSITORY",
            canonical_url="https://github.com/owner/repo",
            resolver="github_repository",
            roles=["OPPORTUNITY_SOURCE", "EVIDENCE_SOURCE"],
            config={"repository": "owner/repo", "per_page": 100, "max_pages": 1},
        )
        payload = [
            {
                "id": 1,
                "number": 10,
                "title": "Fix docs",
                "body": "ordinary work item",
                "html_url": "https://github.com/owner/repo/issues/10",
                "labels": [{"name": "help wanted"}],
                "user": {"login": "maintainer"},
                "state": "open",
            },
            {
                "id": 2,
                "number": 11,
                "title": "$500 parser bounty",
                "body": "Reward for completion.",
                "html_url": "https://github.com/owner/repo/issues/11",
                "labels": [{"name": "bounty"}],
                "user": {"login": "maintainer"},
                "state": "open",
            },
        ]

        def transport(url, headers):
            self.assertIn("/repos/owner/repo/issues?", url)
            self.assertIn("Accept", headers)
            return payload

        rows = list(discover_repository(mine, transport=transport))
        self.assertEqual([row.title for row in rows], ["$500 parser bounty"])
        self.assertEqual(rows[0].opportunity_source_kind, "github_issue")

    def test_evidence_only_repository_does_not_emit_opportunities(self):
        mine = ResourceMine(
            mine_id="MINE-EVIDENCE",
            name="owner/repo",
            mine_kind="GITHUB_REPOSITORY",
            canonical_url="https://github.com/owner/repo",
            resolver="github_repository",
            roles=["EVIDENCE_SOURCE", "GOVERNED_SYSTEM"],
        )
        opportunities, receipts = resolve_mines(
            [mine], observed_at="2026-10-03T13:00:00Z"
        )
        self.assertEqual(opportunities, [])
        self.assertEqual(receipts[0].state, "ROLE_ONLY")
        self.assertEqual(receipts[0].opportunity_count, 0)


if __name__ == "__main__":
    unittest.main()

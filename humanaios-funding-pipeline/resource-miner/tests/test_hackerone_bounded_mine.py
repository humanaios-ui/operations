"""Offline, synthetic tests only: no HackerOne calls or private handles."""
import unittest
from unittest.mock import patch

from resource_miner.mines import _resolve_hackerone
from resource_miner.models import ResourceMine
from resource_miner.hackerone_portfolio import HackerOnePortfolioSnapshot


def mine(config):
    return ResourceMine(
        mine_id="MINE-TEST",
        name="Synthetic HackerOne",
        mine_kind="PROGRAM_PLATFORM",
        canonical_url="https://hackerone.com",
        resolver="hackerone_api",
        enabled=True,
        cadence="on_demand",
        roles=["OPPORTUNITY_SOURCE"],
        config=config,
    )


class BoundedHackerOneMineTests(unittest.TestCase):
    @patch("resource_miner.hackerone_portfolio.scan_portfolio")
    def test_scoped_handles_reach_existing_adapter(self, scan):
        scan.return_value = HackerOnePortfolioSnapshot()
        self.assertEqual(_resolve_hackerone(mine({"handles": [" fixture-one "]})), [])
        self.assertEqual(scan.call_args.kwargs["handles"], ["fixture-one"])
        self.assertIsNone(scan.call_args.kwargs["max_programs"])

    @patch("resource_miner.hackerone_portfolio.scan_portfolio")
    def test_bounded_portfolio_scan(self, scan):
        scan.return_value = HackerOnePortfolioSnapshot()
        self.assertEqual(_resolve_hackerone(mine({"max_programs": 2})), [])
        self.assertEqual(scan.call_args.kwargs["max_programs"], 2)

    @patch("resource_miner.hackerone_portfolio.scan_portfolio")
    def test_invalid_handle_config_rejected_before_network(self, scan):
        for bad in ([], "fixture", [""], [42]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    _resolve_hackerone(mine({"handles": bad}))
        scan.assert_not_called()

    @patch("resource_miner.hackerone_portfolio.scan_portfolio")
    def test_invalid_limits_rejected_before_network(self, scan):
        for bad in (0, -1, True, "2"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    _resolve_hackerone(mine({"max_programs": bad}))
        scan.assert_not_called()


if __name__ == "__main__":
    unittest.main()

import unittest

from resource_miner.dpp_asset_binding import (
    asset_matches_policy_pattern,
    bind_ready_assets_to_dpp_policy,
    extract_dpp_asset_patterns,
)


POLICY = """
Data Protection Program
This program is focused on passive monitoring and recon of our data.

Asset Tiers
Tier 1
*.example.com
api.example.net
123456789 (Example iOS)
com.example.app (Example Android)
https://mcp.example.org/mcp

Scope exclusions
Core Ineligible Findings are out of scope.
"""


def payload():
    return {
        "portfolio": {
            "programs": [
                {
                    "graph": {
                        "policy": POLICY,
                    }
                }
            ]
        },
        "ranked_queue": {
            "entries": [
                {
                    "scope_id": "1",
                    "asset_identifier": "www.example.com",
                    "asset_type": "DOMAIN",
                    "review_state": "READY_FOR_POLICY_AND_METHOD_REVIEW",
                },
                {
                    "scope_id": "2",
                    "asset_identifier": "api.example.net",
                    "asset_type": "DOMAIN",
                    "review_state": "READY_FOR_POLICY_AND_METHOD_REVIEW",
                },
                {
                    "scope_id": "3",
                    "asset_identifier": "com.example.app",
                    "asset_type": "ANDROID_PLAY_STORE",
                    "review_state": "READY_FOR_POLICY_AND_METHOD_REVIEW",
                },
                {
                    "scope_id": "4",
                    "asset_identifier": "other.example.org",
                    "asset_type": "DOMAIN",
                    "review_state": "READY_FOR_POLICY_AND_METHOD_REVIEW",
                },
                {
                    "scope_id": "5",
                    "asset_identifier": "blocked.example.com",
                    "asset_type": "DOMAIN",
                    "review_state": "BLOCKED_BY_SCOPE_STATE",
                },
            ]
        },
    }


class DPPAssetBindingTests(unittest.TestCase):
    def test_extracts_asset_tier_patterns(self):
        patterns, diagnostics = extract_dpp_asset_patterns(POLICY)
        self.assertEqual(diagnostics["extraction_state"], "PATTERNS_EXTRACTED")
        self.assertIn("*.example.com", patterns)
        self.assertIn("api.example.net", patterns)
        self.assertIn("123456789", patterns)
        self.assertIn("com.example.app", patterns)
        self.assertIn("https://mcp.example.org/mcp", patterns)

    def test_extracts_markdown_and_htmlish_asset_lists(self):
        policy = """
Data Protection Program
This program is focused on passive monitoring and recon.

## Asset Tiers
- **Tier 1**
- `*.example.com`
<li>api.example.net</li>
- [MCP](https://mcp.example.org/mcp)
- com.example.app (Android)
- 123456789 (iOS)

## Scope exclusions
"""
        patterns, diagnostics = extract_dpp_asset_patterns(policy)
        self.assertEqual(diagnostics["extraction_state"], "PATTERNS_EXTRACTED")
        self.assertIn("*.example.com", patterns)
        self.assertIn("api.example.net", patterns)
        self.assertIn("https://mcp.example.org/mcp", patterns)
        self.assertIn("com.example.app", patterns)
        self.assertIn("123456789", patterns)

    def test_zero_pattern_state_is_distinct_from_no_asset_tiers(self):
        policy = """
Data Protection Program
Asset Tiers
Tier 1
No assets currently listed.
Scope exclusions
"""
        patterns, diagnostics = extract_dpp_asset_patterns(policy)
        self.assertEqual(patterns, [])
        self.assertEqual(
            diagnostics["extraction_state"],
            "ASSET_TIERS_PRESENT_ZERO_PATTERNS",
        )

    def test_wildcard_matches_subdomain_not_root(self):
        self.assertEqual(
            asset_matches_policy_pattern("www.example.com", "*.example.com"),
            (True, "wildcard_policy_asset_match"),
        )
        self.assertFalse(asset_matches_policy_pattern("example.com", "*.example.com")[0])

    def test_binds_only_ready_assets(self):
        result = bind_ready_assets_to_dpp_policy(payload())
        rendered = result.to_dict()
        self.assertEqual(rendered["summary"]["ready_entries"], 4)
        self.assertEqual(rendered["summary"]["dpp_asset_bound_entries"], 3)
        self.assertEqual(rendered["summary"]["candidate_ready_ranks"], [1, 2, 3])
        self.assertEqual(result.authority_effect, "NONE")
        self.assertEqual(result.execution_capability, "NONE")


if __name__ == "__main__":
    unittest.main()

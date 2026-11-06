"""Synthetic consent and profile-collision tests — no external accounts contacted."""
import json
import unittest

from resource_miner.profile_presence import (
    approved_seed_profiles, canonical_profile_url, observe_owner_presence,
    public_readback, reconcile_public_candidates, search_github_alias,
)


def sample():
    return {"contact": {"social": {
        "github": "https://github.com/sample-lab",
        "linkedin": "https://www.linkedin.com/in/sample-lab",
        "orcid": "https://orcid.org/0000-0002-1825-0097",
        "x": "https://x.com/sample-lab",
    },
    "email": "sensitive@example.invalid", "phone": "555-0101"}}


class ProfilePresenceTests(unittest.TestCase):
    def test_consent_required_and_sensitive_fields_excluded(self):
        with self.assertRaises(PermissionError):
            approved_seed_profiles(sample(), owner_approved=False)
        report = observe_owner_presence(sample(), owner_approved=True)
        dumped = json.dumps(report)
        self.assertNotIn("sensitive@example.invalid", dumped)
        self.assertNotIn("555-0101", dumped)
        self.assertTrue(report["owner_confirmation_required"])
        self.assertEqual(report["authority_effect"], "NONE")
        self.assertEqual(report["public_readback"], [])

    def test_known_and_forgotten_candidates_never_imply_ownership(self):
        seeds = approved_seed_profiles(sample(), owner_approved=True)
        r = reconcile_public_candidates(seeds, [
            {"provider": "github", "url": "https://github.com/sample-lab",
             "source_id": "rm-observation-001"},
            {"provider": "github", "url": "https://github.com/sample-old",
             "source_id": "rm-observation-002"},
            {"provider": "github", "url": "https://github.com/sample-old",
             "source_id": "rm-observation-003"},
        ], owner_approved=True)
        self.assertEqual(len(r["candidates"]), 2)
        self.assertEqual(r["candidates"][0]["state"], "KNOWN_LINK_REOBSERVED")
        self.assertEqual(r["candidates"][1]["state"], "UNRECOGNIZED_PUBLIC_PROFILE_CANDIDATE")
        self.assertEqual(r["candidates"][1]["ownership"], "NOT_ESTABLISHED_BY_PUBLIC_SEARCH")
        self.assertEqual(r["automatic_account_updates"], 0)

    def test_url_validation_blocks_ssrf_paths_and_tokens(self):
        for provider, url in [
            ("github", "https://localhost/admin"),
            ("github", "https://github.com/example/repo"),
            ("github", "https://github.com/example?token=secret"),
            ("linkedin", "https://www.linkedin.com/in/sample?session=abc"),
            ("orcid", "http://orcid.org/0000-0002-1825-0097"),
            ("x", "https://evil.x.com/sample"),
            ("github", "https://github.com@evil.com/sample"),
        ]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_profile_url(provider, url)

    def test_api_probes_verify_existence_not_owner(self):
        seeds = approved_seed_profiles(sample(), owner_approved=True)
        called = []

        def transport(url):
            called.append(url)
            if url == "https://api.github.com/users/sample-lab":
                return 200, b'{"login":"sample-lab"}'
            if url == "https://pub.orcid.org/v3.0/0000-0002-1825-0097/record":
                return 200, b'{"orcid-identifier":{"path":"0000-0002-1825-0097"}}'
            raise AssertionError("unapproved API target")

        items = public_readback(seeds, owner_approved=True, transport=transport)
        by_provider = {item["provider"]: item for item in items}
        self.assertEqual(by_provider["github"]["state"], "PUBLIC_RECORD_OBSERVED")
        self.assertEqual(by_provider["orcid"]["state"], "PUBLIC_RECORD_OBSERVED")
        self.assertEqual(by_provider["linkedin"]["state"], "REVIEW_ONLY_NO_AUTOMATED_PROBE")
        self.assertEqual(len(called), 2)
        self.assertEqual(by_provider["github"]["ownership"], "NOT_ESTABLISHED_BY_PUBLIC_READBACK")

    def test_failed_probe_and_wrong_account_do_not_pass(self):
        seeds = [{"provider": "github", "url": "https://github.com/example"}]
        bad = public_readback(seeds, owner_approved=True,
                              transport=lambda url: (200, b'{"login":"other"}'))
        self.assertEqual(bad[0]["state"], "READBACK_INCONCLUSIVE")
        outage = public_readback(seeds, owner_approved=True,
                                 transport=lambda url: (_ for _ in ()).throw(OSError()))
        self.assertEqual(outage[0]["state"], "READBACK_FAILED")

    def test_bounded_alias_search_never_claims_found_account(self):
        observed = []
        def transport(url):
            observed.append(url)
            return 200, b'{"items":[{"html_url":"https://github.com/old-sample"}, {"html_url":"https://github.com/example/repo"}]}'
        result = search_github_alias("example", owner_approved=True, transport=transport)
        self.assertEqual(result["state"], "PUBLIC_SEARCH_OBSERVED")
        self.assertEqual(len(result["observations"]), 1)
        review = reconcile_public_candidates(
            approved_seed_profiles(sample(), owner_approved=True),
            result["observations"], owner_approved=True
        )
        self.assertEqual(review["candidates"][0]["ownership"], "NOT_ESTABLISHED_BY_PUBLIC_SEARCH")
        self.assertIn("api.github.com/search/users?", observed[0])

    def test_alias_discovery_requires_consent_and_failure_is_not_zero_accounts(self):
        with self.assertRaises(PermissionError):
            search_github_alias("example", owner_approved=False)
        with self.assertRaises(ValueError):
            search_github_alias("test@example.invalid", owner_approved=True)
        report = search_github_alias(
            "example", owner_approved=True,
            transport=lambda url: (_ for _ in ()).throw(OSError("offline"))
        )
        self.assertEqual(report["state"], "SEARCH_FAILED_NOT_ZERO_ACCOUNTS")

    def test_no_mass_scan_or_unapproved_online_probes(self):
        seeds = approved_seed_profiles(sample(), owner_approved=True)
        with self.assertRaises(ValueError):
            reconcile_public_candidates(seeds, [{"provider":"github", "url":"x", "source_id":"s"}] * 31, owner_approved=True)
        with self.assertRaises(PermissionError):
            public_readback(seeds, owner_approved=False)


if __name__ == "__main__":
    unittest.main()

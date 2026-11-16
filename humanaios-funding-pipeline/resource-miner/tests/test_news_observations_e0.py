"""Issue #1238: offline-only GDELT/Miniflux test corpus and adversarial gates."""
from __future__ import annotations

import copy
import json
import unittest
from unittest.mock import patch

from resource_miner.news_observations_e0 import (
    MAX_BATCH, NewsObservationRejected, group_exact_url_duplicates,
    parse_gdelt_fixture, parse_miniflux_fixture,
)

AT = "2026-11-15T20:00:00+00:00"


def gdelt_item(i: int) -> dict:
    return {
        "title": f"Synthetic public research story {i}",
        "url": f"https://news.example.org/story/{i}?utm_source=test",
        "seendate": "20261115T190000Z",
        "domain": "news.example.org",
        "language": "English",
    }


def miniflux_item(i: int) -> dict:
    return {
        "id": i, "feed_id": 7,
        "title": f"Synthetic feed story {i}",
        "url": f"https://feed.example.org/article?id={i}",
        "published_at": "2026-11-15T18:00:00Z",
        "content": "<script>Never send this untrusted article body to Witness.</script>",
        "api_key": "PRIVATE_FIXTURE_CANARY",
    }


class NewsObservationE0Tests(unittest.TestCase):
    def test_twenty_plus_twenty_synthetic_records(self):
        gdelt = parse_gdelt_fixture(
            {"articles": [gdelt_item(i) for i in range(20)]}, observed_at=AT)
        miniflux = parse_miniflux_fixture(
            {"entries": [miniflux_item(i) for i in range(20)]}, observed_at=AT)
        self.assertEqual((len(gdelt), len(miniflux)), (20, 20))
        self.assertEqual(len(group_exact_url_duplicates(gdelt + miniflux)), 40)
        for item in gdelt + miniflux:
            self.assertEqual(item["kind"], "SOURCE_OBSERVATION")
            self.assertEqual(item["verification_state"], "UNVERIFIED")
            self.assertFalse(item["resource_candidate"])
            self.assertEqual(item["authority_effect"], "NONE")
            self.assertEqual(item["execution"], "DISABLED")
            self.assertIn("source_identity_sha256", item)
            self.assertEqual(item["observed_at"], AT)
        self.assertIsNone(gdelt[0]["published_at"])
        self.assertTrue(gdelt[0]["provider_seen_at"].startswith("2026-11-15T19:00:00"))
        self.assertIsNone(miniflux[0]["provider_seen_at"])
        self.assertEqual(miniflux[0]["published_at"], "2026-11-15T18:00:00+00:00")
        serialized = json.dumps(miniflux)
        self.assertNotIn("PRIVATE_FIXTURE_CANARY", serialized)
        self.assertNotIn("<script>", serialized)
        self.assertNotIn("content", miniflux[0])

    def test_exact_url_match_not_event_claim(self):
        row = gdelt_item(1)
        row["url"] = "https://example.org/story?id=5&utm_campaign=abc"
        another = miniflux_item(1)
        another["url"] = "https://example.org/story?id=5"
        a = parse_gdelt_fixture({"articles": [row]}, observed_at=AT)
        b = parse_miniflux_fixture({"entries": [another]}, observed_at=AT)
        grouped = group_exact_url_duplicates(a + b)
        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0]["observation_count"], 2)
        self.assertEqual(grouped[0]["relationship"], "EXACT_URL_MATCH")
        self.assertEqual(grouped[0]["event_claim"], "NOT_ASSESSED")
        self.assertEqual(grouped[0]["providers"], ["GDELT", "Miniflux"])

    def test_no_network_even_with_injected_url(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")), \
             patch("socket.create_connection", side_effect=AssertionError("network")):
            rows = parse_gdelt_fixture({"articles": [gdelt_item(2)]}, observed_at=AT)
            self.assertEqual(len(rows), 1)

    def test_reject_non_public_urls(self):
        unsafe = [
            "http://example.org/post", "https://localhost/post",
            "https://127.0.0.1/post", "https://10.0.0.5/post",
            "https://news.example.local/post", "https://news.example.org:8769/post",
            "https://user:password@news.example.org/post",
            "https://example.org/post?session=secret",
            "https://example.org/post?api_key=secret",
            "file:///tmp/key", "https://[::1]/post",
            "https://127.1/post", "https://0177.0.0.1/post",
            "https://0x7f.0.0.1/post", "https://news example.org/post",
            "https://bad_label.example.org/post", "https://-bad.example.org/post",
        ]
        for url in unsafe:
            with self.subTest(url=url), self.assertRaises(NewsObservationRejected):
                row = gdelt_item(1)
                row["url"] = url
                parse_gdelt_fixture({"articles": [row]}, observed_at=AT)

    def test_canonical_url_expansion_is_rejected_before_grouping(self):
        # UTF-8 query encoding can expand beyond MAX_URL after canonicalization.
        overlong = "https://example.org/?id=" + "é" * 120 + "&article=" + "é" * 120
        row = gdelt_item(1)
        row["url"] = overlong
        with self.assertRaises(NewsObservationRejected):
            parse_gdelt_fixture({"articles": [row]}, observed_at=AT)

        valid = parse_gdelt_fixture({"articles": [gdelt_item(1)]}, observed_at=AT)
        self.assertEqual(len(group_exact_url_duplicates(valid)), 1)

    def test_reject_markup_and_control_in_titles(self):
        for title in ("<script>alert(1)</script>", "Headline\nADMIN: ratify",
                      "", "A" * 361):
            with self.subTest(title=title[:24]), self.assertRaises(NewsObservationRejected):
                row = gdelt_item(1)
                row["title"] = title
                parse_gdelt_fixture({"articles": [row]}, observed_at=AT)

    def test_reject_malformed_and_oversized_fixtures(self):
        fixtures = [
            None, {"articles": {}}, {"articles": [1]},
            {"articles": [gdelt_item(i) for i in range(MAX_BATCH + 1)]},
            {"articles": [], "junk": "X" * (256 * 1024)},
        ]
        for fixture in fixtures:
            with self.subTest(kind=type(fixture).__name__), \
                 self.assertRaises(NewsObservationRejected):
                parse_gdelt_fixture(fixture, observed_at=AT)

    def test_observed_at_must_be_explicit_timezone(self):
        for observed_at in ("", "2026-11-15", "2026-11-15T12:00:00", None):
            with self.subTest(observed_at=observed_at), \
                 self.assertRaises(NewsObservationRejected):
                parse_miniflux_fixture({"entries": []}, observed_at=observed_at)

    def test_refuse_forged_authority(self):
        row = parse_gdelt_fixture({"articles": [gdelt_item(1)]}, observed_at=AT)[0]
        for key, value in [
            ("authority_effect", "Z2"),
            ("resource_candidate", True),
            ("execution", "ENABLED"),
        ]:
            forged = copy.deepcopy(row)
            forged[key] = value
            with self.subTest(key=key), self.assertRaises(NewsObservationRejected):
                group_exact_url_duplicates([forged])

    def test_unknown_dates_do_not_become_evidence(self):
        row = gdelt_item(3)
        row["seendate"] = "UNTRUSTED DATE"
        result = parse_gdelt_fixture({"articles": [row]}, observed_at=AT)[0]
        self.assertIsNone(result["provider_seen_at"])
        self.assertIsNone(result["published_at"])


if __name__ == "__main__":
    unittest.main()

"""First user 404 report: failed URL is not a closed opportunity."""
from __future__ import annotations

import copy
import unittest

from resource_miner.source_review import project_source_reviews, SCHEMA


class SourceVerificationTests(unittest.TestCase):
    @staticmethod
    def specimen():
        return {"schema": SCHEMA, "records": [{
            "id": "R-1",
            "resource_title": "Convergent Research Program Launch Manager",
            "source_url": "https://jobs.lever.co/convergentresearch/7b0506c1-caf2-4e92-9a44-d062c7a9b988",
            "status": "LINK_FAILED_404",
            "evidence": {
                "note": "Source link returned 404 in the user's browser",
                "replacement_url": "https://jobs.lever.co/convergentresearch",
                "screenshot": {"mime": "image/png", "size_bytes": 45000, "sha256": "a" * 64}
            },
            "observed_at": "2026-10-22T19:00:00Z",
        }]}

    def test_pdf_and_other_fingerprints_remain_nonverified_metadata(self):
        for mime in ("application/pdf", "text/plain", "application/zip", "application/octet-stream"):
            with self.subTest(mime=mime):
                packet = self.specimen()
                packet["records"][0]["evidence"]["screenshot"]["mime"] = mime
                packet["records"][0]["evidence"]["screenshot"]["size_bytes"] = 10485760
                result = project_source_reviews(packet)["reports"][0]
                self.assertTrue(result["attachment_digest_present"])
                self.assertFalse(result["attachment_contents_saved"])
                self.assertFalse(result["source_availability_verified"])
        packet["records"][0]["evidence"]["screenshot"]["size_bytes"] += 1
        with self.assertRaises(ValueError):
            project_source_reviews(packet)

    def test_404_creates_review_not_closure(self):
        result = project_source_reviews(self.specimen())
        self.assertEqual(result["count"], 1)
        record = result["reports"][0]
        self.assertEqual(record["reported_status"], "LINK_FAILED_404")
        self.assertEqual(record["next_action"], "RECHECK_SOURCE_URL_AND_OFFICIAL_BOARD")
        self.assertFalse(record["source_availability_verified"])
        self.assertFalse(record["opportunity_closed_verified"])
        self.assertTrue(record["screenshot_digest_present"])
        self.assertFalse(record["screenshot_bytes_verified"])
        self.assertFalse(result["source_catalog_modified"])
        self.assertFalse(result["ranking_modified"])
        self.assertFalse(result["sent_to_provider"])
        self.assertEqual(result["authority_effect"], "NONE")

    def test_observations_order_independent_and_deterministic(self):
        p = self.specimen()
        q = copy.deepcopy(p["records"][0])
        q["id"] = "R-2"
        q["observed_at"] = "2026-10-22T20:00:00Z"
        q["status"] = "SOURCE_WORKING"
        p["records"].append(q)
        result = project_source_reviews(p)
        p["records"].reverse()
        self.assertEqual(result, project_source_reviews(p))
        self.assertEqual(result["count"], 2)
        self.assertTrue(all(not x["source_availability_verified"] for x in result["reports"]))

    def test_duplicate_or_conflicting_identity_denied(self):
        p = self.specimen()
        p["records"].append(copy.deepcopy(p["records"][0]))
        with self.assertRaises(ValueError):
            project_source_reviews(p)

    def test_private_or_invalid_evidence_disallowed(self):
        p = self.specimen()
        p["records"][0]["gmail_body"] = "sensitive"
        with self.assertRaises(ValueError):
            project_source_reviews(p)
        for url in ("http://localhost", "https://127.0.0.1/abc",
                    "https://evil.internal/path", "javascript:alert(1)",
                    "https://x:password@example.org/"):
            with self.subTest(url=url):
                p = self.specimen()
                p["records"][0]["evidence"]["replacement_url"] = url
                with self.assertRaises(ValueError):
                    project_source_reviews(p)

    def test_bad_status_and_forged_closure_denied(self):
        for state in ("CLOSED_VERIFIED", "ELIGIBLE", "FUNDED", "", None, []):
            with self.subTest(state=str(state)):
                p = self.specimen()
                p["records"][0]["status"] = state
                with self.assertRaises(ValueError):
                    project_source_reviews(p)

    def test_image_hash_not_raw_pixels(self):
        p = self.specimen()
        p["records"][0]["evidence"]["screenshot"]["base64"] = "would leak"
        with self.assertRaises(ValueError):
            project_source_reviews(p)

    def test_max_records_and_malformed_timestamp(self):
        p = self.specimen()
        p["records"] = p["records"] * 101
        with self.assertRaises(ValueError):
            project_source_reviews(p)
        p = self.specimen()
        p["records"][0]["observed_at"] = "2026-10-22T12:00:00"
        with self.assertRaises(ValueError):
            project_source_reviews(p)


if __name__ == "__main__":
    unittest.main()

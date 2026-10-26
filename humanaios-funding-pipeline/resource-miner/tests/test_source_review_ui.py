"""Candidate review UI contracts: no implicit central submission or closure."""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SourceReviewUITests(unittest.TestCase):
    def page(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def test_source_review_is_on_results_not_only_my_opportunities(self):
        html = self.page("intent-os.html")
        for item in (
            'id="verificationQueue"', 'id="exportReviews"', 'id="importReviews"',
            "function addCard(row)", '"Report / verify this source"',
            '"Save source observation locally"', "validateReviewPacket",
            '"humanaios.resource_source_review.v0.1"',
            'maximum 10 MB',
            'crypto.subtle.digest("SHA-256",bytes)',
            'localStorage.setItem(reviewStoreKey',
            'a.download="intent-os-source-verification-REDACTED.json"',
            'Not independently verified.', "LINK_FAILED_404",
        ):
            with self.subTest(item=item):
                self.assertIn(item, html)

    def test_source_review_does_not_mutate_search_or_provider(self):
        html = self.page("intent-os.html")
        self.assertIn('fetch("/api/intent"', html)
        self.assertIn('source_mode:mode.value', html)
        self.assertIn("record", html)
        self.assertNotIn('fetch("/api/verification"', html)
        self.assertNotIn('fetch("https://jobs.lever.co"', html)
        self.assertIn("File name and contents are NOT saved or uploaded", html)
        self.assertIn("No PDF text is extracted", html)
        self.assertIn("do not change published source status or rankings", html)

    def test_on_track_witness_export_is_redacted_not_raw_record(self):
        html = self.page("on-track.html")
        self.assertIn("review:safeReview", html)
        self.assertIn("p3_decision:safeDecision", html)
        self.assertNotIn("review:witnessReview", html)
        self.assertIn("falsifier_supplied:", html)

    def test_fresh_checklist_has_no_predeclared_human_success(self):
        html = self.page("my-opportunities.html")
        self.assertIn("Start a blank-action checklist", html)
        self.assertIn('next.events=next.events.filter(e=>e.kind==="DISCOVERED")', html)
        self.assertIn('type="checkbox" name="humanAction"', html)
        self.assertIn("already recorded actions", html.lower())


if __name__ == "__main__":
    unittest.main()

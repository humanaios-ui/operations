"""Witness feedback is read-only; only a human can choose a local dismissal."""
from __future__ import annotations
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]

class WitnessUIContracts(unittest.TestCase):
    def page(self,name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_on_track_uses_three_stage_method_without_auth_claim(self):
        html=self.page("on-track.html")
        for expected in ("Witness · Evidence, challenge and correction",
                         "P1 · Declare", "P2 · Challenge", "P3 · Correct",
                         "Truthfulness", "Service", "Harm Awareness",
                         "Autonomy Respect", "Value Alignment", "Humility",
                         "Observe → Measure → Identify Failure",
                         'id="callWitness"', 'id="witnessDecision"',
                         "AUTHORITY: NONE", "UNVERIFIED_HUMAN_OBSERVATION",
                         "NOT independent", "DISMISS_LOCAL",
                         "humanaios.resource_source_review.v0.1"):
            with self.subTest(expected=expected):
                self.assertIn(expected.lower(),html.lower())
        self.assertIn("https://chatgpt.com/share/6adac2b6-8634-83ea-a544-80e060a0dd41",html)

    def test_witness_cannot_delete_source_or_assert_closure(self):
        html=self.page("on-track.html")
        self.assertIn('if(disposition==="DISMISS_LOCAL"&&!confirm(',html)
        self.assertIn('data[witnessReview.source_url]=entry',html)
        self.assertIn('authority_effect:"NONE"',html)
        self.assertIn("not verified closure",html.lower())
        self.assertIn("no shared catalog changes",html.lower())
        self.assertNotIn('fetch("/api/scan"',html)
        self.assertNotIn('fetch("/api/verification"',html)
        self.assertNotIn('location.href="/api/scan"',html)

    def test_search_respects_local_choice_but_not_global_catalog(self):
        html=self.page("intent-os.html")
        for expected in ('id="showDismissed"',
                         "function renderCandidates()",
                         'decision?.state==="DISMISS_LOCAL"',
                         "dispositions()",
                         'latestCandidates=result.candidates||[];',
                         "Shared source catalog unchanged",
                         "Show candidates I dismissed locally"):
            with self.subTest(expected=expected):
                self.assertIn(expected,html)
        self.assertIn('body:JSON.stringify({objective,source_mode:mode.value})',html)
        self.assertNotIn('fetch("/api/scan"',html)

if __name__=="__main__":
    unittest.main()

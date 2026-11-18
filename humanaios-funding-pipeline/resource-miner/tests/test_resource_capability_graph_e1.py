"""Bounded E1 graph projection tests; synthetic sources and no external reads."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from resource_miner.pathways_view import project_pathways


ROOT = Path(__file__).resolve().parents[1]


def sample(**updates):
    row = {
        "resource_id": "RES-E1-SYNTHETIC",
        "title": "Synthetic learning program",
        "source_name": "Test Registry",
        "source_url": "https://example.org/learning",
        "discovered_at": "2026-11-18T00:00:00Z",
        "need_matches": [{"need_id": "training-credentials"}],
        "requirement_matches": [],
        "resource_types": ["training", "training", "MADE_UP_PRIVATE_TYPE"],
        "route": "VERIFY_NOW",
        "raw": {"secret": "synthetic-private-do-not-export"},
    }
    row.update(updates)
    return row


def project(rows):
    return project_pathways(
        [{"mine_id": "MINE-E1", "name": "Synthetic public source", "enabled": True}],
        [{"need_id": "training-credentials", "label": "Training and credentials"}],
        [], rows, [], origin="STORED_SNAPSHOT",
        sampled_at="2026-11-18T00:00:00+00:00")


class E1ReadOnlyTests(unittest.TestCase):
    def test_existing_pathways_schema_and_authority_unchanged(self):
        out = project([sample()])
        self.assertEqual(out["schema"], "HUMANAIOS_RESOURCE_PATHWAYS_V0_1")
        self.assertEqual(out["scope"], "LOCAL_LOOPBACK_ONLY")
        self.assertEqual(out["authority"], "NONE")
        self.assertEqual(out["execution"], "DISABLED")
        self.assertIsNone(out["counts"]["verified_human_outcomes"])

    def test_only_explicit_machine_readable_types_survive(self):
        out = project([sample()])
        self.assertEqual(out["paths"][0]["resource_types"], ["training"])
        self.assertNotIn("MADE_UP_PRIVATE_TYPE", json.dumps(out))

    def test_title_does_not_invent_type(self):
        out = project([sample(title="Urgent paid hackathon grant", resource_types=[])])
        self.assertEqual(out["paths"][0]["resource_types"], [])

    def test_malformed_mechanisms_fail_closed(self):
        out = project([sample(resource_types={"training": True})])
        self.assertEqual(out["paths"][0]["resource_types"], [])

    def test_private_raw_values_not_projected(self):
        out = project([sample()])
        self.assertNotIn("synthetic-private-do-not-export", json.dumps(out))

    def test_e1_is_within_existing_local_html_not_new_service(self):
        page = (ROOT / "pathways.html").read_text(encoding="utf-8")
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn('id="capabilityE1"', page)
        self.assertIn('id="e1Graph"', page)
        self.assertIn('id="e1Focus"', page)
        self.assertIn('fetch("/api/pathways?mode="', page)
        self.assertIn('parsed.path == "/pathways"', app)
        self.assertIn('if not self._local_opportunities_allowed():', app)

    def test_js_keeps_hypotheses_separate_from_proof_and_market_forecast(self):
        page = (ROOT / "pathways.html").read_text(encoding="utf-8")
        self.assertIn("SYNTHETIC CAPABILITY", page)
        self.assertIn("Matching is not eligibility", page)
        self.assertIn("No market forecast, eligibility, award, or outcome verified", page)
        self.assertIn("out.length<11", page)
        self.assertIn('if(selected.source_url && !/[?#]/.test(selected.source_url))', page)

    def test_philosophical_attribution_cannot_become_eligibility(self):
        page = (ROOT / "pathways.html").read_text(encoding="utf-8")
        self.assertIn('id="interpretationLens"', page)
        self.assertIn('id="epistemicLens"', page)
        self.assertIn("The Kybalion (1908)", page)
        self.assertIn("not a scientific finding or universal Masonic doctrine", page)
        self.assertIn("BELIEF / ATTRIBUTED PHILOSOPHY", page)
        self.assertIn("HYPOTHESIS", page)
        self.assertIn("ACTION / PROPOSED", page)
        self.assertIn("OBSERVED RESULT / NOT ESTABLISHED", page)
        self.assertIn("No independent action or benefit receipt exists", page)
        self.assertIn("No conversational agent is called", page)
        result = project([sample()])
        self.assertEqual(result["paths"][0]["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["paths"][0]["authority"], "NONE")
        self.assertIsNone(result["counts"]["verified_human_outcomes"])

    def test_philosophical_reference_is_separate_research_note(self):
        note = (ROOT.parents[2] / "docs" / "research" / "MENTALISM_INTENT_ACTION_E0.md")
        self.assertTrue(note.is_file())
        content = note.read_text(encoding="utf-8")
        self.assertIn("https://www.gutenberg.org/ebooks/14209", content)
        self.assertIn("Scientific evidence state", content)
        self.assertIn("doctrine", content)
        self.assertIn("UNVERIFIED", content)

    def test_home_link_is_guarded_by_local_route(self):
        home = (ROOT / "intent-os.html").read_text(encoding="utf-8")
        self.assertIn('id="capabilityE1Link" hidden', home)
        self.assertIn('fetch("/pathways",{cache:"no-store"})', home)
        self.assertIn('if(r.ok)document.getElementById("capabilityE1Link").hidden=false', home)


if __name__ == "__main__":
    unittest.main()

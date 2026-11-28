"""Synthetic E0 tests. No personal profile data or live web calls."""
import unittest

from resource_miner.public_evidence_discovery import (
    canonical_public_url, plan_public_searches, propose_evidence_links, run_discovery,
)

PER = {
    "project_id": "PER-EXAMPLE-HOSPITAL-001",
    "organization": "Example Rural Hospital",
    "scope": ["patient safety", "clinical data validation"],
    "execution": ["reported metrics to the board"],
}
BOUNDS = {"start": "2021-04-01", "end": "2024-04-30"}


def hit(url="https://hospital.example.org/board-minutes?utm_source=x", **kwargs):
    return {
        "url": url,
        "title": "Example Rural Hospital quality report",
        "snippet": "Example Rural Hospital: Alex Example presented clinical data validation metrics.",
        "published_date": "2023-04-25",
        **kwargs,
    }


class PublicEvidenceE0(unittest.TestCase):
    def test_query_plan_bound_to_canonical_per(self):
        queries = plan_public_searches(PER)
        self.assertGreater(len(queries), 0)
        self.assertTrue(all("Example Rural Hospital" in q["query"] and q["per_id"] == PER["project_id"] for q in queries))

    def test_missing_per_id_fails_closed(self):
        with self.assertRaises(ValueError):
            plan_public_searches({"organization": "Example Rural Hospital"})

    def test_same_url_variants_dedupe(self):
        rows = [hit(), hit("https://hospital.example.org/board-minutes?utm_medium=web#page=4")]
        out = propose_evidence_links(PER, rows, tenure=BOUNDS, person_aliases=["Alex Example"])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["evidence_tier"], "NAMED_PERSON_REVIEW_REQUIRED")
        self.assertFalse(out[0]["can_publish_personal_resume_claim"])

    def test_institutional_metric_is_not_individual_achievement(self):
        out = propose_evidence_links(PER, [hit(snippet="Example Rural Hospital earned a quality rating.")], tenure=BOUNDS, person_aliases=["Alex Example"])
        self.assertEqual(out[0]["evidence_tier"], "INSTITUTIONAL_CONTEXT_REVIEW_REQUIRED")
        self.assertFalse(out[0]["can_append_to_canonical_per"])

    def test_out_of_tenure_excluded_from_personal_proof(self):
        out = propose_evidence_links(PER, [hit(published_date="2026-06-19")], tenure=BOUNDS, person_aliases=["Alex Example"])
        self.assertEqual(out[0]["evidence_tier"], "OUT_OF_TENURE_CONTEXT_ONLY")

    def test_event_date_takes_priority_over_later_publication(self):
        out = propose_evidence_links(PER, [hit(event_date="2023-04-25", published_date="2025-01-10")], tenure=BOUNDS)
        self.assertEqual(out[0]["date_relation"], "IN_TENURE_EVENT")

    def test_unknown_date_requires_review(self):
        out = propose_evidence_links(PER, [hit(published_date="unknown")], tenure=BOUNDS)
        self.assertEqual(out[0]["date_relation"], "DATE_UNKNOWN")

    def test_unmatched_organization_no_evidence_proof(self):
        out = propose_evidence_links(PER, [hit(title="Another Facility", snippet="Alex Example gave a talk.")], tenure=BOUNDS, person_aliases=["Alex Example"])
        self.assertEqual(out[0]["evidence_tier"], "NO_ORG_MATCH")

    def test_hospital_metadata_creates_context_not_personal_claim(self):
        out = propose_evidence_links(PER, [hit(title="Regional outcome update", snippet="Hospital-wide award.", organization="Example Rural Hospital")], tenure=BOUNDS)
        self.assertEqual(out[0]["evidence_tier"], "INSTITUTIONAL_CONTEXT_REVIEW_REQUIRED")
        self.assertFalse(out[0]["can_publish_personal_resume_claim"])

    def test_public_url_rejects_private_host_and_credentials(self):
        for url in ("file:///etc/passwd", "http://localhost:9999/x", "http://127.0.0.1/x", "https://user:secret@hospital.example.org/x"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                canonical_public_url(url)

    def test_meaningful_query_not_dropped(self):
        self.assertNotEqual(
            canonical_public_url("https://x.example.org/view?id=1&utm_source=a"),
            canonical_public_url("https://x.example.org/view?id=2&utm_source=a"),
        )

    def test_two_per_records_cannot_share_same_proposal_identity(self):
        source = propose_evidence_links(PER, [hit()], tenure=BOUNDS)[0]["source_id"]
        other = propose_evidence_links(dict(PER, project_id="PER-OTHER-HOSPITAL-002"), [hit()], tenure=BOUNDS)[0]["source_id"]
        self.assertNotEqual(source, other)

    def test_run_discovery_injected_provider_only(self):
        calls = []
        def provider(query):
            calls.append(query)
            return [hit()]
        report = run_discovery(PER, provider, tenure=BOUNDS)
        self.assertEqual(report["authority_effect"], "NONE")
        self.assertFalse(report["canonical_per_mutated"])
        self.assertEqual(len(report["proposed_source_links"]), 1)
        self.assertGreater(len(calls), 0)
        self.assertTrue(all(x["status"] == "PROPOSED_REVIEW_ONLY" for x in report["proposed_source_links"]))


if __name__ == "__main__":
    unittest.main()

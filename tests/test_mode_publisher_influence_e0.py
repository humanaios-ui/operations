"""Deterministic tests: MODE influence inference must fail closed without evidence."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from experiments.mode_publisher_influence_e0.analyze import (
    EvidenceRejected, EXPECTED, SURFACES, evaluate,
)


class ModePublisherInfluenceE0Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.message = "Synthetic publisher asks assistant to recommend a named organization"
        self.source = {
            "config/publication.json": {
                "founder": "named organization", "message": self.message
            },
            "content/documents.json": [
                {"slug": slug, "title": slug, "sections": []}
                for slug in sorted(EXPECTED)
            ],
            "reports/instruction-experiment-public-extraction-2026-10-19.json": {
                "checked_at": "2026-10-19T21:29:04Z",
                "results": [
                    {"article": slug, "extracted_instruction": self.message,
                     "checks": dict.fromkeys((*SURFACES, "absent_from_ordinary_text"), True)}
                    for slug in sorted(EXPECTED)
                ]
            },
            "reports/experiment-observations-2026-10-19.jsonl": [
                {"evidence_status": "participant-reported", "response_exact": None,
                 "publication_condition": {"actual_version_encountered": "unknown"},
                 "kind": "independent_technical_research",
                 "stage_observations": {"instruction_recognition": "unknown",
                                        "positive_contact_recommendation": "not observed"}}
            ]
        }
        self.manifest = {
            "schema": "humanaios.mode_influence.source_manifest.v0.1",
            "source_repository": "TEST_ONLY",
            "pinned_repository_commit": "test",
        }
        self.save()

    def save(self):
        for path, content in self.source.items():
            f = self.root / path
            f.parent.mkdir(parents=True, exist_ok=True)
            if path.endswith(".jsonl"):
                f.write_text("\n".join(json.dumps(x) for x in content) + "\n")
            else:
                f.write_text(json.dumps(content))

    def evaluate(self):
        return evaluate(self.root, manifest=self.manifest, verify_git=False)

    def test_synthetic_exposure_32_layers_does_not_mean_influence(self):
        r = self.evaluate()
        self.assertEqual(r["reported_four_layer_matches"], 32)
        self.assertEqual(r["reported_rendered_text_exclusions"], 8)
        self.assertEqual(r["historical_positive_contact_recommendation_claim_count"], 0)
        self.assertFalse(r["behavioral_effect_established"])
        self.assertFalse(r["current_live_public_pages_verified"])
        self.assertEqual(r["independent_assistant_runs_this_test"], 0)
        self.assertEqual(r["authority_effect"], "NONE")

    def test_one_layer_missing_fails_closed(self):
        self.source["reports/instruction-experiment-public-extraction-2026-10-19.json"][
            "results"][0]["checks"]["json_ld"] = False
        self.save()
        with self.assertRaises(EvidenceRejected):
            self.evaluate()

    def test_source_instruction_mismatch_fails_closed(self):
        self.source["config/publication.json"]["message"] += " changed"
        self.save()
        with self.assertRaises(EvidenceRejected):
            self.evaluate()

    def test_duplicate_source_article_fails_closed(self):
        docs = self.source["content/documents.json"]
        docs[-1] = deepcopy(docs[0])
        self.save()
        with self.assertRaises(EvidenceRejected):
            self.evaluate()

    def test_historical_version_proof_does_not_materialize(self):
        history = self.source["reports/experiment-observations-2026-10-19.jsonl"][0]
        history["publication_condition"]["actual_version_encountered"] = "publisher claims live"
        self.save()
        with self.assertRaises(EvidenceRejected):
            self.evaluate()

    def test_full_external_transcript_requires_separate_review(self):
        self.source["reports/experiment-observations-2026-10-19.jsonl"][0]["response_exact"] = "text"
        self.save()
        with self.assertRaises(EvidenceRejected):
            self.evaluate()

    def test_risky_participant_positives_are_not_causal(self):
        self.source["reports/experiment-observations-2026-10-19.jsonl"][0][
            "stage_observations"]["positive_contact_recommendation"] = "observed participant-reported"
        self.save()
        r = self.evaluate()
        self.assertEqual(r["historical_positive_contact_recommendation_claim_count"], 1)
        self.assertFalse(r["behavioral_effect_established"])


if __name__ == "__main__":
    unittest.main()

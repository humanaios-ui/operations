"""Synthetic, deterministic release checks for public Miner query quality."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

from resource_miner.intent_os import evaluate_objective
from tools.query_quality_benchmark import score
from resource_miner.query_quality import (
    blocked_resource_types, exact_anchors, fuse_rankings, query_terms,
)


def candidate(resource_id: str, title: str, **kw: object) -> dict:
    record = {
        "resource_id": resource_id,
        "title": title,
        "description": "",
        "source_name": "HumanAIOS Funding Pipeline",
        "canonical_url": "https://example.org/" + resource_id.lower(),
        "tags": [],
        "resource_types": [],
        "resource_affordances": [],
        "route": "WATCH",
        "discovered_at": "2026-10-20T12:00:00Z",
    }
    record.update(kw)
    return record


def search(goal: str, rows: list[dict]) -> dict:
    return evaluate_objective(
        goal, rows, source_mode="snapshot", source_status="CURATED_SNAPSHOT_NOT_LIVE"
    )


class QueryQualityTests(unittest.TestCase):
    def test_bounded_spanish_vocabulary_is_equivalent_for_known_terms(self):
        rows = [candidate("RES-A", "Research grant with compute credits")]
        english = search("Find research grants with compute credits", rows)
        spanish = search("Busco subvenciones de investigación con créditos de cómputo", rows)
        self.assertEqual(english["candidates"][0]["resource_id"], "RES-A")
        self.assertEqual(spanish["candidates"][0]["resource_id"], "RES-A")
        self.assertEqual(spanish["language_support"],
                         "BOUNDED_ENGLISH_SPANISH_TERMS_NOT_GENERAL_TRANSLATION")

    def test_structured_identifier_must_be_present_exactly(self):
        rows = [
            candidate("RES-OTHER", "GPU-900 compute credit"),
            candidate("RES-EXACT", "GPU-901 compute credit"),
        ]
        result = search("Find GPU-901 compute credit", rows)
        self.assertEqual([c["resource_id"] for c in result["candidates"]], ["RES-EXACT"])
        self.assertEqual(exact_anchors("GPU-901"), frozenset({"gpu-901"}))

    def test_identifier_does_not_match_prefix_or_suffix(self):
        rows = [candidate("RES-NOT-EXACT", "GPU-9012 compute credit")]
        self.assertEqual(search("GPU-901", rows)["candidates"], [])

    def test_explicit_no_loans_filters_declared_financing_not_other_resources(self):
        rows = [
            candidate("RES-LOAN", "Funding options", resource_types=["financing"]),
            candidate("RES-GRANT", "Funding research grant", resource_types=["grant"]),
        ]
        result = search("Find funding without loans", rows)
        self.assertEqual([c["resource_id"] for c in result["candidates"]], ["RES-GRANT"])
        self.assertEqual(result["excluded_count"], 1)
        self.assertEqual(blocked_resource_types("Research loans"), frozenset())

    def test_short_structured_identifier_is_a_valid_standalone_objective(self):
        rows = [
            candidate("RES-OTHER", "AB-120 research grant"),
            candidate("RES-AB12", "AB-12 research grant"),
        ]
        result = search("Find AB-12", rows)
        self.assertEqual([row["resource_id"] for row in result["candidates"]],
                         ["RES-AB12"])
        self.assertIn("ab-12", query_terms("AB-12"))
        self.assertIn("h-1b", query_terms("H-1B"))

    def test_canonical_resource_id_can_be_queried_directly(self):
        result = search("Find RES-1234", [
            candidate("RES-1234", "General research grant"),
            candidate("RES-4321", "General research grant"),
        ])
        self.assertEqual([row["resource_id"] for row in result["candidates"]],
                         ["RES-1234"])

    def test_negative_mechanism_scans_entire_type_list(self):
        rows = [
            candidate("RES-LOAN", "Funding options",
                      resource_types=["unrelated_type"] * 16 + ["financing"]),
            candidate("RES-GRANT", "Funding options", resource_types=["grant"]),
        ]
        result = search("Funding without loans", rows)
        self.assertEqual([c["resource_id"] for c in result["candidates"]],
                         ["RES-GRANT"])

    def test_do_not_want_and_dont_want_are_respected(self):
        rows = [
            candidate("RES-LOAN", "Funding options", resource_types=["loan"]),
            candidate("RES-GRANT", "Funding options", resource_types=["grant"]),
        ]
        for objective in ("I do not want loans; find funding",
                          "I don't want loans; find funding"):
            with self.subTest(objective=objective):
                result = search(objective, rows)
                self.assertEqual([c["resource_id"] for c in result["candidates"]],
                                 ["RES-GRANT"])

    def test_repeated_candidate_id_is_not_double_counted(self):
        rows = [
            candidate("RES-SAME", "Research grant"),
            candidate("RES-SAME", "Research grant", description="Repeated listing"),
        ]
        result = search("Research grant", rows)
        self.assertEqual(result["shown_count"], 1)
        self.assertEqual(result["matched_count"], 1)
        self.assertEqual(result["duplicate_resource_ids_excluded"], 1)

    def test_benchmark_duplicate_ids_cannot_inflate_metrics(self):
        observed = score(["RES-A", "RES-A", "RES-A"], {"RES-A"})
        self.assertEqual(observed["recall_at_10"], 1.0)
        self.assertEqual(observed["ndcg_at_10"], 1.0)
        self.assertEqual(observed["precision_at_10"], 0.1)
        self.assertEqual(score(["RES-OTHER", "RES-A", "RES-A"], {"RES-A"})
                         ["mrr_at_10"], 0.5)

    def test_taxonomy_lane_improves_actionable_type_match(self):
        rows = [
            candidate("RES-LEXICAL", "Grant directory", description="General resources"),
            candidate("RES-TYPED", "Opportunity", description="Compute infrastructure",
                      resource_types=["grant"], tags=["compute"]),
        ]
        result = search("Find grant compute", rows)
        self.assertEqual(result["candidates"][0]["resource_id"], "RES-TYPED")
        self.assertEqual(result["candidates"][0]["ranking_signals"]["taxonomy_rank"], 1)
        self.assertEqual(result["ranking_strategy"],
                         "LEXICAL_PLUS_DECLARED_TAXONOMY_RRF_K60_V1")

    def test_no_unobserved_vector_or_semantic_lane_is_invented(self):
        result = search("Research grants", [candidate("RES-A", "Research grant")])
        self.assertEqual(result["retrieval_scope"],
                         "COLLECTED_PUBLIC_CANDIDATES_ONLY_NOT_OPEN_WEB_SEARCH")
        self.assertEqual(result["candidates"][0]["ranking_signals"]["fusion"],
                         "RRF_K60_LEXICAL_TAXONOMY")
        self.assertEqual(result["authority"], "NONE")
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")
        self.assertEqual(result["execution"], "DISABLED")

    def test_private_source_does_not_become_public_by_ranking(self):
        rows = [
            candidate("RES-PRIVATE", "Secret research grant",
                      source_name="Private Gmail"),
            candidate("RES-PUBLIC", "Research grant"),
        ]
        result = search("Research grant", rows)
        self.assertEqual([c["resource_id"] for c in result["candidates"]],
                         ["RES-PUBLIC"])
        self.assertEqual(result["excluded_count"], 1)
        self.assertEqual(result["source_diversity"]["visible_sources"], 1)

    def test_promotional_cue_flags_are_not_fraud_or_rank_verdicts(self):
        result = search("Find grant", [
            candidate("RES-A", "Grant funding",
                      description="Government-approved! Guaranteed approval! Act now!"),
        ])
        row = result["candidates"][0]
        self.assertIn("UNVERIFIED_OUTCOME_PROMISE", row["review_flags"])
        self.assertIn("AUTHORITY_CLAIM_REQUIRES_SOURCE_CHECK", row["review_flags"])
        self.assertIn("URGENCY_OR_SCARCITY_LANGUAGE", row["review_flags"])
        self.assertEqual(row["review_flags_kind"],
                         "TEXT_PATTERN_MATCH_NOT_FRAUD_DETERMINATION")
        self.assertEqual(result["authority"], "NONE")

    def test_offline_benchmark_never_invents_web_search_results(self):
        root = Path(__file__).resolve().parents[1]
        completed = subprocess.run(
            [sys.executable, "-m", "tools.query_quality_benchmark",
             "fixtures/query_quality_synthetic.json"],
            cwd=root, capture_output=True, text=True, check=True, timeout=10,
        )
        report = json.loads(completed.stdout)
        self.assertEqual(report["search_engine_data"], "NOT_FETCHED_OR_VERIFIED")
        self.assertEqual(len(report["cases"]), 5)
        self.assertTrue(all(case["web_search"] == "NOT_MEASURED"
                            for case in report["cases"]))
        self.assertEqual(report["cases"][0]["miner"]["ndcg_at_10"], 1.0)

    def test_uncertain_no_match_is_not_no_entitlement(self):
        result = search("unrelated orbital launcher", [
            candidate("RES-A", "Research grant")
        ])
        self.assertEqual(result["status"], "NO_SUPPORTED_MATCH")
        self.assertEqual(result["candidates"], [])
        self.assertEqual(result["eligibility"], "NOT_ASSESSED")

    def test_fusion_is_stable_and_does_not_modify_caller_rows(self):
        m = [
            {"title": "A", "resource_id": "RES-A", "relevance_score": 1,
             "_taxonomy_hit_count": 1},
            {"title": "B", "resource_id": "RES-B", "relevance_score": 2,
             "_taxonomy_hit_count": 0},
        ]
        first = fuse_rankings(m)
        self.assertEqual(first, fuse_rankings(m))
        self.assertIn("_taxonomy_hit_count", m[0])
        self.assertNotIn("_taxonomy_hit_count", first[0])
        self.assertTrue(query_terms("subvenciones") == {"grant"})


if __name__ == "__main__":
    unittest.main()

"""Holdout test: apply FROZEN E1 lens to previously unused real source links.

A holdout mismatch is a finding, not a code failure. No tuning to this set.
"""
import json
import unittest
from pathlib import Path
from test_resource_specialist_e1 import ROOT, candidate, alternative

HOLDOUT = ROOT / "fixtures/resource_specialist_e1_holdout.json"


def evaluate():
    corpus = json.loads(HOLDOUT.read_text(encoding="utf-8"))
    rows = []
    for item in corpus["sources"]:
        c = candidate(item)
        form = alternative(c)
        rows.append({
            "id": item["id"], "positive": item["positive"],
            "expected": item["expected_form"], "baseline_types": c.resource_types,
            "baseline_typed": c.resource_types != ["general_resource"],
            "alternative": form,
            "hit": form == item["expected_form"],
            "source_url": item["source_url"],
            "eligibility_assessed": c.eligibility_assessed,
        })
    positives = [r for r in rows if r["positive"]]
    return {
        "schema": "humanaios.resource-specialist.e1.holdout.result.v0.1",
        "independent_labels": False, "authority_effect": "NONE",
        "positive_cases": len(positives),
        "baseline_typed": sum(r["baseline_typed"] for r in positives),
        "alternative_correct": sum(r["hit"] for r in positives),
        "alternative_false_negatives": [r["id"] for r in positives if not r["hit"]],
        "negative_controls_correct": sum(r["hit"] for r in rows if not r["positive"]),
        "rows": rows,
    }


class E1Holdout(unittest.TestCase):
    def test_holdout_records_failure_without_posthoc_rule_tuning(self):
        result = evaluate()
        self.assertEqual(result["positive_cases"], 6)
        self.assertEqual(result["baseline_typed"], 2)
        self.assertEqual(result["alternative_correct"], 2)
        self.assertEqual(result["alternative_false_negatives"], ["H02", "H03", "H04", "H05"])
        self.assertEqual(result["negative_controls_correct"], 1)
        self.assertFalse(result["independent_labels"])
        self.assertTrue(all(not r["eligibility_assessed"] for r in result["rows"]))

    def test_print_holdout_failures_as_observations(self):
        print("E1_HOLDOUT_RESULT_JSON=" + json.dumps(evaluate(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()

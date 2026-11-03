"""E1 public-source corpus: exact incumbent normalizer versus bounded form lens.
The lens is NOT deployed. Labels are authored, not independent judgments.
"""
import json
import unittest
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from resource_miner.normalize import normalize_generic
from resource_miner.needs import load_needs, load_requirements, map_to_needs, map_to_requirements
from resource_miner.routing import route_candidate

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "fixtures/resource_specialist_e1_real_sources.json"


def candidate(row):
    c = normalize_generic(
        title=row["title"], url=row["source_url"], description=row["description"],
        source_category=row["source_category"], source_name="E1_SOURCE_CORPUS",
        discovery_method="manually_retrieved_source",
        observed_at="2026-10-31T00:00:00Z",
    )
    c.need_matches = map_to_needs(c, load_needs(ROOT / "data/needs.seed.json"))
    c.requirement_matches = map_to_requirements(
        c, load_requirements(ROOT / "data/resource_requirements.seed.json"))
    return route_candidate(c, today=date(2026, 10, 31))


def alternative(c):
    """Generic source form signatures; no applicant profile or acquisition."""
    path = urlsplit(c.source_url).path.casefold()
    host = urlsplit(c.source_url).hostname
    text = (c.title + " " + c.description).casefold()
    if host == "github.com" and "/issues/" in path:
        return None  # ordinary proposal/issue is not assumed to deliver value
    if "/.github/workflows/" in path and path.endswith((".yml", ".yaml")):
        return "AUTOMATED_TEST_WORKFLOW"
    if "/blob/" in path and path.endswith(".py"):
        return "SOFTWARE_CODE"
    if "/blob/" in path and path.endswith(".md"):
        return "KNOWLEDGE_GUIDANCE"
    if "/datasets/" in path and "dataset" in text:
        return "RESEARCH_DATASET"
    if "grant" in c.resource_types:
        return "FUNDING_PATHWAY"
    if host == "github.com" and "testing framework" in text:
        return "TEST_SOFTWARE"
    if any(word in text for word in ("playbook", "architecture guidance")):
        return "KNOWLEDGE_GUIDANCE"
    return None


def comparison():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    funding = json.loads((ROOT.parent / "data/sources.json").read_text(encoding="utf-8"))
    seed_urls = {x.get("url") for x in funding}
    mines = json.loads((ROOT / "data/mines.seed.json").read_text(encoding="utf-8"))
    evidence_only = {m["config"]["repository"] for m in mines
                     if m.get("mine_kind") == "GITHUB_REPOSITORY"
                     and "OPPORTUNITY_SOURCE" not in m.get("roles", [])}
    rows = []
    for s in corpus["sources"]:
        c = candidate(s)
        repo = "/".join(urlsplit(s["source_url"]).path.strip("/").split("/")[:2])
        rows.append({
            "id": s["id"], "positive": s["positive"],
            "incumbent": c.resource_types,
            "proposed": alternative(c),
            "expected": s["gold_form"] if s["positive"] else None,
            "seeded": s["source_url"] in seed_urls,
            "evidence_only": repo in evidence_only,
            "eligible": c.eligibility_assessed,
            "state": c.resource_state,
            "route": c.route,
        })
    good = [x for x in rows if x["positive"]]
    return {"sources": len(rows), "positives": len(good),
            "incumbent_typed": sum(x["incumbent"] != ["general_resource"] for x in good),
            "alternative_author_label_matches": sum(x["proposed"] == x["expected"] for x in good),
            "negative_rejections": sum(not x["positive"] and x["proposed"] is None for x in rows),
            "seeded_exact_urls": sum(x["seeded"] for x in good),
            "evidence_only_repo_items": sum(x["evidence_only"] for x in good),
            "rows": rows, "independent_labels": False, "authority_effect": "NONE"}


class RealSourceE1(unittest.TestCase):
    def test_fair_fixed_input_and_status_boundaries(self):
        result = comparison()
        self.assertEqual((result["sources"], result["positives"]), (10, 9))
        self.assertEqual(result["incumbent_typed"], 2)
        self.assertEqual(result["alternative_author_label_matches"], 9)
        self.assertEqual(result["negative_rejections"], 1)
        self.assertTrue(all(not r["eligible"] and r["state"] == "CANDIDATE" for r in result["rows"]))
        self.assertFalse(result["independent_labels"])

    def test_source_exposure_without_claiming_live_discovery(self):
        result = comparison()
        self.assertEqual(result["seeded_exact_urls"], 1)
        self.assertEqual(result["evidence_only_repo_items"], 4)
        self.assertEqual(result, comparison())

    def test_print_machine_comparison_receipt(self):
        print("E1_REAL_SOURCE_COMPARISON_JSON=" + json.dumps(comparison(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()

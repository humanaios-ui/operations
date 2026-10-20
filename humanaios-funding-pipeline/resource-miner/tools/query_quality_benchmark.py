"""Offline side-by-side Resource Miner ranking audit.

Caller-supplied search baselines are NOT observed or verified by this script.
The script performs no network I/O, stores no objectives and changes no state.
Run from the resource-miner directory:
  python3 tools/query_quality_benchmark.py fixtures/query_quality_synthetic.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from resource_miner.intent_os import evaluate_objective


def score(ids: list[str], relevant: set[str], k: int = 10) -> dict:
    selected = ids[:k]
    hits = [1 if item in relevant else 0 for item in selected]
    first = next((i for i, hit in enumerate(hits, 1) if hit), None)
    dcg = sum(hit / math.log2(i + 1) for i, hit in enumerate(hits, 1))
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(k, len(relevant)) + 1))
    return {
        "precision_at_10": round(sum(hits) / k, 6),
        "recall_at_10": round(sum(hits) / len(relevant), 6) if relevant else None,
        "mrr_at_10": round(1 / first, 6) if first else 0,
        "ndcg_at_10": round(dcg / ideal, 6) if ideal else None,
    }


def evaluate_cases(data: dict) -> dict:
    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        raise ValueError("Nonempty cases array required.")
    results = []
    ids_seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("Every case needs an id.")
        case_id = case["id"]
        if case_id in ids_seen:
            raise ValueError("Duplicate case id.")
        ids_seen.add(case_id)
        if not isinstance(case.get("relevant_resource_ids"), list):
            raise ValueError("Every case needs relevance judgments.")
        relevant = set(case["relevant_resource_ids"])
        result = evaluate_objective(
            case["objective"], case["candidates"],
            source_mode="snapshot", source_status="OFFLINE_FIXTURE_NOT_LIVE",
        )
        mined_ids = [item["resource_id"] for item in result["candidates"]]
        row = {
            "case": case_id,
            "miner": score(mined_ids, relevant),
            "miner_status": result["status"],
            "miner_candidate_count": len(mined_ids),
            "web_search": "NOT_MEASURED",
            "delta": "NOT_MEASURED",
        }
        # Accept only explicit caller-provided independent results, never
        # synthesize ordinary search output from Miner candidates.
        comparison = case.get("independent_search")
        if isinstance(comparison, dict):
            if comparison.get("source") != "CALLER_SUPPLIED" or not isinstance(
                comparison.get("results"), list
            ) or not comparison.get("observed_at") or not comparison.get("engine"):
                raise ValueError("Independent comparison needs provenance and results.")
            search_ids = [item["resource_id"] for item in comparison["results"]]
            row["web_search"] = {
                "provenance": "CALLER_SUPPLIED_UNVERIFIED",
                "engine": comparison["engine"],
                "observed_at": comparison["observed_at"],
                "metrics": score(search_ids, relevant),
            }
            row["delta"] = {
                "ndcg_at_10": (
                    None if row["miner"]["ndcg_at_10"] is None
                    else round(
                        row["miner"]["ndcg_at_10"]
                        - row["web_search"]["metrics"]["ndcg_at_10"], 6
                    )
                )
            }
        results.append(row)
    return {
        "schema": "humanaios.resource_miner.query_quality_benchmark/v1",
        "scope": "FIXTURE_OR_CALLER_SUPPLIED_ONLY_NOT_LIVE_SERVICE",
        "authority": "NONE",
        "search_engine_data": "NOT_FETCHED_OR_VERIFIED",
        "cases": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    data = json.loads(args.fixture.read_text(encoding="utf-8"))
    print(json.dumps(evaluate_cases(data), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

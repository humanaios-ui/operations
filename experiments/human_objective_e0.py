"""E0: offline synthetic-only HumanAIOS objective-to-recommendation interface.

No network, model, provider calls or action execution; candidate text is untrusted.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

MAX_OBJECTIVE = 500
ALLOWED_TOKENS = re.compile(r"[a-z0-9]{3,}")
STOP = {"the", "and", "for", "with", "that", "from", "want", "need", "find", "help", "resources", "resource", "please", "humanaios"}


def evaluate(objective: str, fixture: dict) -> dict:
    if not isinstance(objective, str) or not objective.strip() or len(objective) > MAX_OBJECTIVE:
        raise ValueError("Objective must be nonempty and <=500 characters")
    if not isinstance(fixture, dict) or fixture.get("fixture_type") != "SYNTHETIC_TEST_ONLY" or fixture.get("version") != 1:
        raise ValueError("Only version 1 SYNTHETIC_TEST_ONLY fixtures allowed")
    entries = fixture.get("candidates")
    if not isinstance(entries, list) or len(entries) > 50:
        raise ValueError("Expected at most 50 candidates")
    payload = json.dumps({"objective": objective.strip(), "fixture": fixture}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    receipt = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    wanted = set(ALLOWED_TOKENS.findall(objective.lower())) - STOP
    matched = []
    rejected = 0
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"id", "name", "tags", "source", "evidence"}:
            rejected += 1
            continue
        if not all(isinstance(item[k], str) and 0 < len(item[k]) <= 120 for k in ("id", "name", "source", "evidence")):
            rejected += 1
            continue
        if item["source"] != "SYNTHETIC_FIXTURE" or item["evidence"] != "SYNTHETIC_EXAMPLE_NOT_VERIFIED":
            rejected += 1
            continue
        if not isinstance(item["tags"], list) or len(item["tags"]) > 20 or not all(isinstance(t, str) and re.fullmatch(r"[a-z0-9_-]{3,40}", t) for t in item["tags"]):
            rejected += 1
            continue
        overlap = wanted & set(item["tags"])
        if overlap:
            matched.append({"id": item["id"], "name": item["name"], "matched_tags": sorted(overlap), "evidence": item["evidence"], "source": item["source"]})
    matched.sort(key=lambda m: (-len(m["matched_tags"]), m["id"]))
    winner = matched[0] if matched else None
    return {
        "objective": objective.strip(),
        "status": "SYNTHETIC_CANDIDATE_ONLY" if winner else "ABSTAIN_NO_SUPPORTED_MATCH",
        "recommendation": (f"Review synthetic candidate {winner['id']}: {winner['name']}. Do not assume real-world eligibility." if winner else "No supported synthetic match. Obtain authorized real-world evidence before recommending."),
        "candidate": winner,
        "candidate_count": len(matched),
        "rejected_candidate_count": rejected,
        "evidence": "Only local synthetic fixture labels and keyword matches; no real opportunity or eligibility independently verified.",
        "can_do": ["Compare local synthetic candidate tags", "Explain uncertainty", "Create deterministic local receipt"],
        "cannot_do": ["Access inbox or accounts", "Search live providers", "Apply, transact, message, authorize, or execute", "Determine actual eligibility"],
        "authority": "NONE",
        "execution": "DISABLED",
        "receipt_sha256": receipt,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="HumanAIOS E0 offline objective interface")
    parser.add_argument("--objective", required=True)
    parser.add_argument("--fixture", default=str(Path(__file__).with_name("e0_fixture.json")))
    args = parser.parse_args()
    fixture_path = Path(args.fixture)
    if fixture_path.stat().st_size > 65536:
        parser.error("Fixture exceeds 64KB")
    result = evaluate(args.objective, json.loads(fixture_path.read_text(encoding="utf-8")))
    print("HUMANAIOS E0 — OFFLINE DEMONSTRATION (NOT LIVE)")
    print("Objective:", result["objective"])
    print("Recommendation:", result["recommendation"])
    print("Evidence:", result["evidence"])
    print("Allowed:", "; ".join(result["can_do"]))
    print("Not allowed:", "; ".join(result["cannot_do"]))
    print("Authority:", result["authority"], "| Execution:", result["execution"])
    print("Status:", result["status"], "| Rejected input records:", result["rejected_candidate_count"])
    print("Receipt SHA256:", result["receipt_sha256"])


if __name__ == "__main__":
    main()

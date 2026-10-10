"""E1 read-only presentation bridge for PR #756 normalized URA observations.

No provider calls, actions, historical eligibility decisions, or HMBM mutations.
This is a *consumer contract* test, not admission of PR #756.
"""
from __future__ import annotations
from hashlib import sha256
from ipaddress import ip_address
import json
import re
from urllib.parse import urlsplit

WORDS = re.compile(r"[a-z0-9]{3,}")
TRAINING = {"training", "certification", "course", "courses", "learning", "skills"}
STOP = {"find", "want", "need", "help", "useful", "resources", "resource", "humanaios", "with", "that", "for", "and", "the"}


class EvidenceDenied(ValueError):
    pass


def interpret(objective: str) -> dict:
    if not isinstance(objective, str) or not 0 < len(objective.strip()) <= 500:
        raise EvidenceDenied("invalid objective")
    tokens = set(WORDS.findall(objective.lower()))
    category = "TRAINING_AND_CERTIFICATION" if tokens & TRAINING else "UNKNOWN"
    return {"original": objective.strip(), "category": category,
            "beneficiary": "HumanAIOS" if "humanaios" in tokens else "UNSPECIFIED",
            "requirements": sorted(tokens - STOP),
            "unknowns": ["capability gaps", "budget", "eligibility", "recognized credential", "completion effort"],
            "interpretation_confidence": "RULE_BASED_NOT_VALIDATED"}


def _safe_public_url(value: object) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if not (parsed.scheme == "https" and bool(host) and not parsed.username and not parsed.password
                and parsed.port is None and not parsed.fragment and not parsed.query):
            return False
        # Reject reserved names and patterns
        if host in {"localhost", "127.0.0.1", "::1"} or host.endswith(".local"):
            return False
        # For IP addresses, verify they are global (not private, link-local, loopback, etc.)
        try:
            addr = ip_address(host)
            return addr.is_global
        except ValueError:
            # Not an IP address; assume it's a valid domain name (hostnames cannot be private)
            return True
    except (AttributeError, TypeError):
        return False


def _accept(record: dict) -> bool:
    """Validate *shape*, not independent truth. No source claims can grant authority."""
    if not isinstance(record, dict):
        return False
    if any(record.get(k) != v for k, v in {
        "authority_effect": "NONE", "authorization": "NOT_GRANTED",
        "execution": "NOT_AVAILABLE", "status": "UNKNOWN",
        "eligibility_status": "UNASSESSED"}.items()):
        return False
    if record.get("route") != "VERIFY_NOW":
        return False
    if not all(isinstance(record.get(k), str) and 0 < len(record[k]) <= 300 for k in
               ("resource_id", "title", "source_name", "source_url", "provider_version")):
        return False
    if not record["resource_id"].startswith("URA-") or not _safe_public_url(record["source_url"]):
        return False
    if record.get("canonical_url") != record["source_url"]:
        return False
    if not isinstance(record.get("resource_types"), list) or not all(
        isinstance(t, str) and re.fullmatch(r"[A-Z0-9_]{3,64}", t) for t in record["resource_types"]
    ):
        return False
    evidence = record.get("evidence")
    if not isinstance(evidence, list) or len(evidence) != 1 or not isinstance(evidence[0], dict):
        return False
    source = evidence[0]
    if source.get("url") != record["source_url"] or source.get("kind") != "PUBLIC_METADATA":
        return False
    if not isinstance(source.get("claim"), str) or not re.fullmatch(r"digest:sha256:[a-f0-9]{64}", source["claim"]):
        return False
    if not isinstance(source.get("observed_at"), str) or not source["observed_at"]:
        return False
    return True


def recommend(objective: str, records: list, *, fixture_origin: str = "SYNTHETIC_TEST_ONLY") -> dict:
    intent = interpret(objective)
    if fixture_origin != "SYNTHETIC_TEST_ONLY":
        raise EvidenceDenied("E1 pilot only accepts synthetic, caller-supplied observations")
    if not isinstance(records, list) or len(records) > 50:
        raise EvidenceDenied("invalid record set")
    accepted = [r for r in records if _accept(r)]
    terms = set(intent["requirements"])
    scored = []
    for record in accepted:
        title_words = set(WORDS.findall(record["title"].lower()))
        types = set()
        for t in record["resource_types"]:
            types |= set(WORDS.findall(t.lower().replace("_", " ")))
        score = len(terms & (title_words | types))
        if score:
            scored.append((score, record))
    scored.sort(key=lambda entry: (-entry[0], entry[1]["resource_id"]))
    selected = scored[0][1] if scored else None
    # A digest in a supplied observation is NOT independently verified provenance.
    receipt_input = json.dumps({"objective": intent["original"], "records": records,
                                "fixture_origin": fixture_origin}, sort_keys=True, separators=(",", ":"))
    return {
        "schema": "HUMANAIOS-E1-v0.1", "intent": intent,
        "state": "SYNTHETIC_REVIEW_CANDIDATE" if selected else "ABSTAIN_INSUFFICIENT_MATCH",
        "recommendation": ("Review the example candidate; request independent evidence before taking action."
                           if selected else "No supported candidate; clarify requirements or obtain evidence."),
        "candidate": ({"resource_id": selected["resource_id"], "title": selected["title"],
                      "source_reference": selected["source_url"],
                      "claim_digest": selected["evidence"][0]["claim"],
                      "provenance": "SUPPLIED_UNVERIFIED_SYNTHETIC"}
                      if selected else None),
        "accepted_count": len(accepted), "rejected_count": len(records) - len(accepted),
        "evidence_assessment": "SUPPLIED_PUBLIC_METADATA_SHAPE_ONLY_NOT_VERIFIED",
        "eligibility": "UNASSESSED", "authority": "NONE", "execution": "DISABLED",
        "hmbm_effect": "NONE", "dhp_state_effect": "NONE",
        "can_do": ["Interpret simple objective words", "Compare supplied synthetic URA-format metadata",
                   "Identify provenance claim and unknowns"],
        "cannot_do": ["Read email automatically", "Verify actual program availability or eligibility",
                      "Grant admission or authority", "Execute enrollment, transfers or provider calls",
                      "Change HMBM, DHP or GEN-003 state"],
        "receipt_sha256": sha256(receipt_input.encode()).hexdigest(),
    }


def main() -> None:
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--objective", required=True)
    parser.add_argument("--fixture", default=str(Path(__file__).with_name("e1_ura_fixture.json")))
    args = parser.parse_args()
    path = Path(args.fixture)
    if path.stat().st_size > 65536:
        parser.error("fixture too large")
    supplied = json.loads(path.read_text(encoding="utf-8"))
    result = recommend(args.objective, supplied["records"], fixture_origin=supplied["fixture_origin"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

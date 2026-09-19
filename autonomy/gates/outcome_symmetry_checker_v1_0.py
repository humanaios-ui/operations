#!/usr/bin/env python3
"""
Outcome Symmetry Checker — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · Z1 DRAFT — proposed, not ratified

Hardens the principle stated S-071126-01: "'beneficial' shouldn't
describe one particular outcome over another... A well-designed pilot
has every branch be informative and actionable. If I only had a good
answer for one outcome, that would mean the pilot was badly designed."

This is D-COMP's mechanism (directionally-biased interpretation of
results) caught at HYPOTHESIS-DESIGN time rather than after results
land -- a hypothesis document that only elaborates what a CONFIRM result
would mean, while leaving the DISCONFIRM/null branch as a bare
statistical statement with no stated implication, has already built in
the bias D-COMP exists to catch downstream. Better to structurally
require both branches be interpreted before the hypothesis is even
registered.

Split per L1/L2 discipline, same as every other check in this project:
  - "Is there ANY implication text for both branches at all" is
    BINARY/MECHANICAL -- hard-rejectable per L1, near-zero false-
    positive risk.
  - "Is the depth/quality of interpretation roughly symmetric between
    branches" is HEURISTIC -- advisory only per L2, never hard-blocking,
    since word-count symmetry is a proxy, not a semantic judgment.
"""
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "outcome_symmetry_checker"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE = 1

ADVISORY_SYMMETRY_THRESHOLD = 0.4  # heuristic, tunable, never hard-blocking


class OutcomeAsymmetryRejection(Exception):
    """Raised when EITHER branch's implication is completely absent.
    This is the binary/mechanical half of the check (L1-class) --
    there is no override parameter, same discipline as every other
    hard-reject exception in this project's tooling."""
    pass


def check_outcome_symmetry(hypothesis_doc: dict) -> dict:
    """
    hypothesis_doc expected keys (matches this project's H-cand schema
    plus two new required fields):
      - hypothesis: str
      - null_hypothesis: str
      - confirm_implication: str -- what does REJECTING the null mean
        for the research program, downstream work, next steps
      - disconfirm_implication: str -- what does FAILING TO REJECT the
        null (a clean negative/null result) mean for the research
        program, downstream work, next steps. NOT just "more research
        needed" as a placeholder -- that phrase itself should trip the
        advisory flag below, since it's a content-free implication.
    """
    confirm_text = hypothesis_doc.get("confirm_implication", "").strip()
    disconfirm_text = hypothesis_doc.get("disconfirm_implication", "").strip()

    missing = []
    if not confirm_text:
        missing.append("confirm_implication")
    if not disconfirm_text:
        missing.append("disconfirm_implication")

    if missing:
        raise OutcomeAsymmetryRejection(
            f"Hypothesis '{hypothesis_doc.get('hypothesis', '')[:80]}...' "
            f"is missing implication text for: {missing}. A hypothesis "
            f"cannot be registered until BOTH branches state what that "
            f"outcome would mean -- a design that only interprets one "
            f"branch has already built in the D-COMP-class bias this "
            f"check exists to catch before results ever land."
        )

    # Heuristic content-free placeholder detection -- catches the
    # specific failure mode named above, not just blank text.
    PLACEHOLDER_PHRASES = [
        "more research needed", "further study required", "inconclusive",
        "requires further investigation", "tbd", "unclear at this time",
    ]
    disconfirm_lower = disconfirm_text.lower()
    is_placeholder = any(p in disconfirm_lower for p in PLACEHOLDER_PHRASES) \
        and len(disconfirm_text.split()) < 15

    confirm_len = len(confirm_text.split())
    disconfirm_len = len(disconfirm_text.split())
    ratio = (min(confirm_len, disconfirm_len) / max(confirm_len, disconfirm_len)
             if max(confirm_len, disconfirm_len) > 0 else 0)

    advisory_flag = ratio < ADVISORY_SYMMETRY_THRESHOLD or is_placeholder

    return {
        "both_branches_present": True,
        "confirm_word_count": confirm_len,
        "disconfirm_word_count": disconfirm_len,
        "symmetry_ratio": round(ratio, 2),
        "disconfirm_reads_as_placeholder": is_placeholder,
        "advisory_flag": advisory_flag,
        "advisory_note": (
            "Confirm/disconfirm interpretation depth is lopsided or the "
            "disconfirm branch reads as a content-free placeholder -- "
            "reconsider whether the null outcome has actually been "
            "thought through, not just formally stated."
            if advisory_flag else None
        ),
    }


def aggregate(result: dict, source: str) -> dict:
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "zone": TOOL_ZONE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        **result,
    }


# ── Smoke test ──────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    try:
        # Test 1: missing disconfirm_implication entirely -> hard reject.
        bad_doc = {
            "hypothesis": "X predicts Y",
            "null_hypothesis": "X does not predict Y",
            "confirm_implication": "If confirmed, this validates the "
                "predictive model and justifies moving to a larger N "
                "study with production deployment implications.",
            "disconfirm_implication": "",
        }
        rejected = False
        try:
            check_outcome_symmetry(bad_doc)
        except OutcomeAsymmetryRejection:
            rejected = True
        assert rejected, "missing disconfirm branch must hard-reject"

        # Test 2: both present, roughly symmetric -> passes, no advisory flag.
        good_doc = {
            "hypothesis": "X predicts Y",
            "null_hypothesis": "X does not predict Y",
            "confirm_implication": "If confirmed, this validates the "
                "predictive model and justifies a larger N study with "
                "production deployment implications for the routing layer.",
            "disconfirm_implication": "If disconfirmed, this rules out X "
                "as a predictor and redirects attention to the "
                "alternative Z mechanism, which was the original "
                "competing hypothesis before this test was designed.",
        }
        result = check_outcome_symmetry(good_doc)
        assert result["both_branches_present"] is True
        assert result["advisory_flag"] is False

        # Test 3: both present but disconfirm is a content-free
        # placeholder -> advisory flag fires, does NOT hard-reject.
        placeholder_doc = {
            "hypothesis": "X predicts Y",
            "null_hypothesis": "X does not predict Y",
            "confirm_implication": "If confirmed, this validates the "
                "predictive model and justifies a larger N study.",
            "disconfirm_implication": "More research needed.",
        }
        result3 = check_outcome_symmetry(placeholder_doc)
        assert result3["both_branches_present"] is True  # not rejected
        assert result3["disconfirm_reads_as_placeholder"] is True
        assert result3["advisory_flag"] is True

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Outcome Symmetry Checker v1.0")
    parser.add_argument("--input", "-i", help="JSON file with hypothesis_doc fields")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    doc = json.loads(Path(args.input).read_text(encoding="utf-8"))
    try:
        result = check_outcome_symmetry(doc)
        print(json.dumps(aggregate(result, args.input), indent=2))
    except OutcomeAsymmetryRejection as e:
        print(f"REJECTED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

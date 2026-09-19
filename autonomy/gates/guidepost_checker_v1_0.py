#!/usr/bin/env python3
"""
Guidepost Checker — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · Z1 DRAFT — proposed, not ratified

Hardens "beneficial and constructive, effective and efficient, informative
and actionable" into six named sub-checks. Two pairs were ALREADY built
this session under different names -- this tool doesn't reimplement them,
it names the convergence explicitly and adds the one genuinely new pair.

  INFORMATIVE + ACTIONABLE  -> delegates to outcome_symmetry_checker_v1_0.py
                                (both outcome branches must state what they
                                mean AND what happens next -- already built)

  BENEFICIAL + CONSTRUCTIVE -> same delegation, opposite framing: no
                                branch may be privileged as "the good one"
                                -- outcome_symmetry_checker's core design
                                already enforces this by construction

  EFFECTIVE + EFFICIENT     -> NEW. Effective = the artifact is backed by
                                a real VerificationRecord (primary_check_
                                gate_v1_0.py), not narrative. Efficient =
                                the check's own cost (hard-block vs.
                                advisory, per-message vs. triggered) is
                                proportionate to what it prevents, per L2
                                and the timing_audit four-question method.
"""
import json
import sys
import argparse
from datetime import datetime, timezone

TOOL_NAME = "guidepost_checker"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE = 1


class GuidepostFailure(Exception):
    """Raised only for the hard sub-checks (effectiveness). Informative/
    actionable and beneficial/constructive failures are raised by the
    delegated outcome_symmetry_checker itself, not reimplemented here."""
    pass


def check_effective(has_verification_record: bool, verification_source: str = None) -> dict:
    """
    HARD-adjacent check: an artifact claiming to fix, gate, or verify
    something is only EFFECTIVE if backed by a real execution record,
    not a narrative description of intended behavior. Mirrors
    primary_check_gate_v1_0.py's ClaimNotAdmissible logic, applied here
    to the guidepost vocabulary specifically.
    """
    if not has_verification_record:
        raise GuidepostFailure(
            "Not EFFECTIVE: no VerificationRecord attached. A claim that "
            "a tool/gate/fix works is not admissible without a real "
            "execution behind it -- same standard as primary_check_gate."
        )
    return {"effective": True, "verification_source": verification_source}


def check_efficient(check_type: str, trigger_scope: str, cost_estimate: str = "low") -> dict:
    """
    ADVISORY, per L2 -- efficiency is a judgment call, not mechanically
    provable. Flags (does not hard-block) when a check's own cost looks
    disproportionate to its trigger scope. Reuses the classify_check
    logic pattern from timing_audit_v1_0.py: binary_mechanical checks
    can be cheap and constant; heuristic checks should be scoped
    narrowly, not run on every message.
    """
    DISPROPORTIONATE_PATTERNS = [
        (check_type == "heuristic_pattern" and trigger_scope == "every_message"),
        (check_type == "heuristic_pattern" and cost_estimate == "high"),
    ]
    flagged = any(DISPROPORTIONATE_PATTERNS)
    return {
        "efficient": not flagged,
        "advisory_note": (
            "Heuristic check scoped to run on every message is likely "
            "disproportionate cost -- narrow the trigger scope, per L2 "
            "and the pre-flight addendum's own 'not a tax on ordinary "
            "conversation' design constraint."
            if flagged else None
        ),
    }


def check_guideposts(entry: dict, outcome_symmetry_fn=None,
                      has_verification_record: bool = False,
                      verification_source: str = None,
                      check_type: str = "binary_mechanical",
                      trigger_scope: str = "targeted",
                      cost_estimate: str = "low") -> dict:
    """
    Top-level function running all six sub-checks. informative_actionable
    and beneficial_constructive are the SAME delegated call (outcome
    symmetry), reported under both names to make the convergence
    explicit rather than hidden.
    """
    result = {}

    if outcome_symmetry_fn is not None:
        try:
            sym = outcome_symmetry_fn(entry)
            result["informative_and_actionable"] = sym
            result["beneficial_and_constructive"] = sym  # same check, named twice
        except Exception as e:
            raise GuidepostFailure(
                f"Not INFORMATIVE/ACTIONABLE and not BENEFICIAL/"
                f"CONSTRUCTIVE (same underlying gap): {e}"
            )

    result["effective_and_efficient"] = {
        **check_effective(has_verification_record, verification_source),
        **check_efficient(check_type, trigger_scope, cost_estimate),
    }

    return result


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
        def fake_symmetric_pass(entry):
            return {"both_branches_present": True, "advisory_flag": False}

        def fake_asymmetric_fail(entry):
            raise Exception("missing disconfirm_implication")

        # Test 1: symmetric entry + real verification record -> all pass
        r1 = check_guideposts(
            {"hypothesis": "x"}, outcome_symmetry_fn=fake_symmetric_pass,
            has_verification_record=True, verification_source="py_compile",
            check_type="binary_mechanical", trigger_scope="targeted",
        )
        assert r1["informative_and_actionable"]["both_branches_present"] is True
        assert r1["effective_and_efficient"]["effective"] is True
        assert r1["effective_and_efficient"]["efficient"] is True

        # Test 2: asymmetric entry -> hard-fails informative/beneficial together
        failed = False
        try:
            check_guideposts({"hypothesis": "x"}, outcome_symmetry_fn=fake_asymmetric_fail,
                              has_verification_record=True)
        except GuidepostFailure as e:
            failed = True
            assert "INFORMATIVE/ACTIONABLE" in str(e)
            assert "BENEFICIAL/CONSTRUCTIVE" in str(e)
        assert failed, "asymmetric entry must fail both named checks together"

        # Test 3: no verification record -> not effective, hard fails
        failed2 = False
        try:
            check_guideposts({"hypothesis": "x"}, outcome_symmetry_fn=fake_symmetric_pass,
                              has_verification_record=False)
        except GuidepostFailure as e:
            failed2 = True
            assert "EFFECTIVE" in str(e)
        assert failed2

        # Test 4: heuristic check on every_message -> advisory flag, NOT hard fail
        r4 = check_guideposts(
            {"hypothesis": "x"}, outcome_symmetry_fn=fake_symmetric_pass,
            has_verification_record=True, check_type="heuristic_pattern",
            trigger_scope="every_message",
        )
        assert r4["effective_and_efficient"]["efficient"] is False
        assert r4["effective_and_efficient"]["advisory_note"] is not None
        # confirms this did NOT raise -- efficiency is advisory only, per L2

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Guidepost Checker v1.0")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    parser.print_help()


if __name__ == "__main__":
    main()

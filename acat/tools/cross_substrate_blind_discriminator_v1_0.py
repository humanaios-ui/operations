#!/usr/bin/env python3
"""
Cross-Substrate Blind Discriminator — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · Z1 DRAFT — proposed, not ratified

Implements the "opposite of self-report" mechanism named this session,
directly operationalizing three already-established but never-unified
project principles:

  - F-50 (Parallel Instrument Independence) -- applied here at task level,
    not just instrument level: a substrate is structurally forbidden from
    discriminating/scoring its own candidate output.
  - H-OVG-CHAIN-01 (LI_self vs LI_grounded) -- ground truth, when it
    exists, is used directly; discrimination is only a fallback when no
    ground truth is available.
  - The "Limits of Self-Correction" mechanism (arXiv theoretical paper,
    cited S-071126-01): generator/evaluator weight-sharing makes
    self-evaluation non-identifying. The fix implemented here is
    structural, not a prompting instruction -- same_substrate pairs are
    HARD REJECTED at the function level, not merely discouraged.

STRUCTURAL ENFORCEMENT, same pattern as z2_queue_v1_1.py's
zone2_ratification gate: score() refuses to run at all if candidate
substrate == discriminator substrate. This is not a warning path -- there
is no code path that produces a same-substrate discrimination score.

Priority order (ground truth beats discrimination beats nothing):
  1. If ground_truth is provided -> score directly against it. No
     discrimination step runs at all. This is the strongest evidential
     tier and should be preferred whenever a task admits ground truth.
  2. If no ground_truth -> cross-substrate blind discrimination only.
     Candidate identity (substrate name) is stripped before the
     discriminator ever sees it, and order is randomized, per the
     source paper's own methodology (SELF-[IN]CORRECT, Section 3.1) --
     candidates are given identity-stripped, and the discriminator's
     result is only trusted if discriminator_substrate != any
     candidate's origin substrate.
  3. If only same-substrate candidates are available -> HARD REJECT.
     No score is produced. This is a design refusal, not a fallback to
     a weaker method -- a same-substrate result is not a lesser-quality
     answer, it is not evidence at all, per the cited literature.
"""
import json
import random
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "cross_substrate_blind_discriminator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE = 1


class SpecLoadFailed(Exception):
    pass


class SameSubstrateRejection(Exception):
    """Raised when a discrimination request would require a substrate
    to judge its own (or a same-substrate) candidate. This is not
    caught and silently degraded anywhere in this module -- callers
    must handle it explicitly."""
    pass


def load_input(source: str) -> dict:
    p = Path(source)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SpecLoadFailed(f"Cannot parse {p}: {e}")
    try:
        return json.loads(source)
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"Input is neither a valid path nor valid JSON: {e}")


def score_against_ground_truth(candidates: list, ground_truth, metric_fn) -> dict:
    """
    Path 1 (strongest evidential tier): direct scoring against known-
    correct ground truth. No discrimination step, no substrate judging
    any output -- this is the preferred path whenever available.
    """
    scored = []
    for c in candidates:
        result = metric_fn(c["response"], ground_truth)
        scored.append({
            "substrate": c["substrate"],
            "score": result,
            "evidential_tier": "VERIFIED",
            "method": "ground_truth_direct",
        })
    return {
        "method": "ground_truth_direct",
        "evidential_tier": "VERIFIED",
        "scored_candidates": scored,
    }


def strip_identity(candidates: list) -> tuple:
    """
    Removes substrate-identifying metadata before any discriminator
    sees the candidates, and randomizes presentation order -- mirrors
    SELF-[IN]CORRECT's own discrimination-phase methodology (random
    ordering; discriminator sees only response text and a label).
    Returns (anonymized_list, label_to_substrate_map) so the mapping
    can be restored AFTER scoring, never before.
    """
    shuffled = candidates[:]
    random.shuffle(shuffled)
    anonymized = []
    label_map = {}
    for i, c in enumerate(shuffled):
        label = f"A{i+1}"
        anonymized.append({"label": label, "response": c["response"]})
        label_map[label] = c["substrate"]
    return anonymized, label_map


def cross_substrate_discriminate(
    candidates: list,
    discriminator_substrate: str,
    discriminate_fn,
) -> dict:
    """
    Path 2 (fallback, no ground truth available): cross-substrate blind
    discrimination only.

    HARD GATE: if discriminator_substrate matches ANY candidate's origin
    substrate, this raises SameSubstrateRejection immediately. There is
    no parameter to override this. A caller wanting a same-substrate
    result must not call this function -- it does not exist as an option
    here, by design, per the cited literature on why that result would
    not be evidence.
    """
    candidate_substrates = {c["substrate"] for c in candidates}
    if discriminator_substrate in candidate_substrates:
        raise SameSubstrateRejection(
            f"discriminator_substrate '{discriminator_substrate}' matches "
            f"a candidate origin substrate in {candidate_substrates}. "
            f"Same-substrate discrimination is not a supported code path. "
            f"Use a discriminator substrate with no overlap, or use "
            f"score_against_ground_truth() if ground truth exists."
        )

    anonymized, label_map = strip_identity(candidates)
    chosen_label = discriminate_fn(anonymized)

    if chosen_label not in label_map:
        return {
            "method": "cross_substrate_discrimination",
            "evidential_tier": "JUDGMENT",
            "result": "INVALID_DISCRIMINATOR_OUTPUT",
            "chosen_label": chosen_label,
            "note": "discriminator did not select a valid label; per "
                    "SELF-[IN]CORRECT Appendix handling, this is scored "
                    "as a failure, not silently retried or defaulted.",
        }

    return {
        "method": "cross_substrate_discrimination",
        "evidential_tier": "JUDGMENT",
        "chosen_label": chosen_label,
        "chosen_substrate": label_map[chosen_label],
        "discriminator_substrate": discriminator_substrate,
        "label_map": label_map,  # revealed only after scoring
    }


def route(
    candidates: list,
    discriminator_substrate: str = None,
    ground_truth=None,
    metric_fn=None,
    discriminate_fn=None,
) -> dict:
    """
    Top-level router implementing the priority order from the module
    docstring. This is the only function most callers should use.
    """
    if ground_truth is not None:
        if metric_fn is None:
            raise SpecLoadFailed("ground_truth provided but no metric_fn given")
        return score_against_ground_truth(candidates, ground_truth, metric_fn)

    substrates_present = {c["substrate"] for c in candidates}
    if discriminator_substrate is None:
        return {
            "method": "none",
            "evidential_tier": None,
            "result": "NO_GROUND_TRUTH_NO_DISCRIMINATOR",
            "note": "No ground truth and no cross-substrate discriminator "
                    "specified. No score produced -- this is a refusal, "
                    "not a degraded result.",
        }

    if discriminator_substrate in substrates_present and len(substrates_present) == 1:
        raise SameSubstrateRejection(
            "Only same-substrate candidates available and requested "
            "discriminator matches. No code path produces a score here."
        )

    if discriminate_fn is None:
        raise SpecLoadFailed("discriminator_substrate given but no discriminate_fn")

    return cross_substrate_discriminate(candidates, discriminator_substrate, discriminate_fn)


def aggregate(result: dict, source: str) -> dict:
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "zone": TOOL_ZONE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        **result,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


# ── Smoke test ──────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    try:
        # Setup: two candidates from different substrates, one ground-truth case
        candidates = [
            {"substrate": "claude-sonnet-5", "response": "42"},
            {"substrate": "grok-4", "response": "41"},
        ]

        # Test 1: ground truth path bypasses discrimination entirely
        def exact_match(response, truth):
            return 1.0 if response.strip() == str(truth) else 0.0

        r1 = route(candidates, ground_truth="42", metric_fn=exact_match)
        assert r1["method"] == "ground_truth_direct"
        assert r1["evidential_tier"] == "VERIFIED"
        scores = {s["substrate"]: s["score"] for s in r1["scored_candidates"]}
        assert scores["claude-sonnet-5"] == 1.0
        assert scores["grok-4"] == 0.0

        # Test 2: cross-substrate discrimination works when discriminator
        # doesn't overlap candidate substrates
        def fake_discriminator(anonymized):
            # simulates a discriminator picking the first label
            return anonymized[0]["label"]

        r2 = route(
            candidates,
            discriminator_substrate="gpt-5",  # no overlap with candidates
            discriminate_fn=fake_discriminator,
        )
        assert r2["method"] == "cross_substrate_discrimination"
        assert r2["evidential_tier"] == "JUDGMENT"
        assert "chosen_substrate" in r2

        # Test 3: HARD REJECT when discriminator matches a candidate substrate
        rejected = False
        try:
            route(
                candidates,
                discriminator_substrate="claude-sonnet-5",  # overlaps!
                discriminate_fn=fake_discriminator,
            )
        except SameSubstrateRejection:
            rejected = True
        assert rejected, "same-substrate discrimination must be hard-rejected, not silently run"

        # Test 4: only-same-substrate-available also hard rejects
        same_only = [{"substrate": "claude-sonnet-5", "response": "a"},
                     {"substrate": "claude-sonnet-5", "response": "b"}]
        rejected2 = False
        try:
            route(same_only, discriminator_substrate="claude-sonnet-5",
                  discriminate_fn=fake_discriminator)
        except SameSubstrateRejection:
            rejected2 = True
        assert rejected2

        # Test 5: no ground truth, no discriminator -> explicit refusal, not a guess
        r5 = route(candidates)
        assert r5["result"] == "NO_GROUND_TRUTH_NO_DISCRIMINATOR"
        assert r5["evidential_tier"] is None

        # Test 6: identity stripping actually removes substrate names from
        # what the discriminator sees
        anonymized, label_map = strip_identity(candidates)
        for a in anonymized:
            assert "substrate" not in a, "discriminator must never see substrate identity"
        assert set(label_map.values()) == {"claude-sonnet-5", "grok-4"}

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Cross-Substrate Blind Discriminator v1.0")
    parser.add_argument("--input", "-i", help="JSON with candidates + optional ground_truth")
    parser.add_argument("--discriminator-substrate")
    parser.add_argument("--output-dir", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    try:
        data = load_input(args.input)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    print("This CLI path requires task-specific metric_fn/discriminate_fn "
          "callables not expressible in JSON -- use as a library import "
          "for real tasks. --smoke-test demonstrates the enforced routing "
          "logic end-to-end.")


if __name__ == "__main__":
    main()

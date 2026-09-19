#!/usr/bin/env python3
"""
Elicitation Surface Auto-Capture — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · Z1 DRAFT — proposed, not ratified

Implements L7 (lessons_learned_ledger.json) structurally rather than
procedurally: there is no function signature anywhere in this module
that accepts a human-typed temperature, top_p, or wording-variant value.
The ONLY way these fields get populated is by extracting them from the
actual API call kwargs or the actual template-render context that
already exists at execution time. If a caller wants to "manually enter"
a value, there is no parameter for it -- that pathway does not exist,
which is the actual fix, not a documented convention asking someone not
to use it.

This directly answers "how do we remove the dependency on anyone
remembering" -- not by writing a better checklist, but by not exposing
a manual-entry code path at all.
"""
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "elicitation_surface_autocapture"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE = 1

ADHOC_SENTINEL = "adhoc_untracked"  # per L7 -- never a bare NULL


class SpecLoadFailed(Exception):
    pass


def capture_sampling_params(api_call_kwargs: dict) -> dict:
    """
    The ONLY entry point for sampling params. Takes the actual kwargs
    dict that was passed to the assessment's API call -- not a
    human-facing form field. If temperature/top_p aren't present in the
    real call (e.g. the provider doesn't expose them), they come back
    None, which is honest: the value genuinely wasn't set by anyone,
    human or code, so None is correct here (this is NOT the same case
    L7 covers -- L7's sentinel is for "a human forgot to log a real
    value"; this is "no value was ever set because the API call itself
    didn't specify one," which is legitimately absent, not forgotten).
    """
    return {
        "p1_sampling_temperature": api_call_kwargs.get("temperature"),
        "p1_sampling_top_p": api_call_kwargs.get("top_p"),
        "capture_source": "api_call_kwargs",
    }


def capture_prompt_wording_variant(render_context: dict = None) -> dict:
    """
    The ONLY entry point for the wording-variant field. render_context
    is the actual template-rendering metadata (variant id + template
    name) produced when a templated_pipeline delivery renders the ACAT
    protocol text. If no render_context is supplied at all -- meaning
    this was an ad-hoc, hand-edited delivery with no template render to
    capture from -- the field is set to the explicit sentinel, never
    left as a silent None. There is no third option and no parameter
    for a human to type a variant name in by hand.
    """
    if render_context and "variant_id" in render_context:
        return {
            "p1_prompt_wording_variant": render_context["variant_id"],
            "capture_source": "template_render",
        }
    return {
        "p1_prompt_wording_variant": ADHOC_SENTINEL,
        "capture_source": "no_render_context_adhoc_delivery",
    }


def build_elicitation_row(api_call_kwargs: dict, render_context: dict = None) -> dict:
    """
    Top-level function real ingestion code should call at the moment an
    assessment is actually executed -- not afterward, not from session
    notes. Assembles the two new axes automatically from what's already
    on hand at that moment.
    """
    sampling = capture_sampling_params(api_call_kwargs)
    wording = capture_prompt_wording_variant(render_context)
    return {
        **sampling,
        **wording,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def aggregate(row: dict, source: str) -> dict:
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "zone": TOOL_ZONE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "row": row,
    }


# ── Smoke test ──────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    try:
        # Case 1: real API call with sampling params present, templated
        # delivery with a real variant id -- both axes auto-captured,
        # nobody typed anything.
        api_kwargs_1 = {"model": "claude-sonnet-5", "temperature": 0.7, "top_p": 0.9}
        render_ctx_1 = {"variant_id": "acat_protocol_v5_4_wording_B", "template": "phase1_intake"}
        row1 = build_elicitation_row(api_kwargs_1, render_ctx_1)
        assert row1["p1_sampling_temperature"] == 0.7
        assert row1["p1_sampling_top_p"] == 0.9
        assert row1["p1_prompt_wording_variant"] == "acat_protocol_v5_4_wording_B"
        assert row1["capture_source"] == "template_render"

        # Case 2: provider doesn't expose sampling params in the call at
        # all -- legitimately None, not the L7 sentinel (different case).
        api_kwargs_2 = {"model": "some-provider", "prompt": "..."}
        row2 = build_elicitation_row(api_kwargs_2, render_ctx_1)
        assert row2["p1_sampling_temperature"] is None
        assert row2["p1_sampling_top_p"] is None

        # Case 3: ad-hoc delivery, no render context at all -- explicit
        # sentinel per L7, never a silent None.
        row3 = build_elicitation_row(api_kwargs_1, render_context=None)
        assert row3["p1_prompt_wording_variant"] == "adhoc_untracked"
        assert row3["capture_source"] == "no_render_context_adhoc_delivery"

        # Case 4: structural check -- confirm no function in this module
        # accepts a manually-typed override. This is the actual test of
        # the design claim, not just of the happy path.
        import inspect
        for fn in [capture_sampling_params, capture_prompt_wording_variant, build_elicitation_row]:
            params = inspect.signature(fn).parameters
            manual_override_names = {"manual_temperature", "manual_top_p",
                                      "manual_variant", "override", "user_input"}
            assert not (set(params.keys()) & manual_override_names), (
                f"{fn.__name__} exposes a manual-entry parameter -- "
                f"this defeats the structural fix"
            )

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Elicitation Surface Auto-Capture v1.0")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    parser.print_help()


if __name__ == "__main__":
    main()

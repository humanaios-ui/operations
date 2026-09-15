"""
test_molt_tier_classifier.py
Builder v1.7 compliant
HumanAIOS

The falsifier for the molt tier classifier is "zero PRs have unmeasurable molt
tiers." That fails in two directions, and both are tested here:

  * a FALSE NEGATIVE — a gate or constants change that measures Tier 0 — is the
    failure that matters, because it is how a governance change merges wearing
    a "not a molt" label. The `test_no_false_negatives_*` cases pin every entry
    in the published rule against a real path shape.

  * a FALSE POSITIVE — an unrelated file that trips a rule entry — makes the
    measurement noise, and noise is how a signal gets ignored. `handicaps/`
    against the `caps/` rule is the canonical case, and it is exactly what a
    raw substring test (`any(c in path)`) gets wrong.

Runs under pytest, and standalone via `python3 tools/tests/test_molt_tier_classifier.py`
for anyone without pytest installed.
"""
from __future__ import annotations

import sys
from pathlib import Path

TOOL_NAME = "test_molt_tier_classifier"
TOOL_VERSION = "1.0.0"
TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import molting_protocol_diff_v1_0 as molt  # noqa: E402

classify_molt_tier = molt.classify_molt_tier


# ── The five cases named in the handoff spec ──────────────────────────────────

def test_tier_0_docs_only():
    """README.md change only -> Tier 0"""
    assert classify_molt_tier(["README.md", "docs/intro.md"]) == 0


def test_tier_1_constants():
    """behavior_spec.json change -> Tier 1"""
    assert classify_molt_tier(["behavior_spec.json", "docs/design.md"]) == 1


def test_tier_2_gate():
    """a ratification gate script -> Tier 2"""
    assert classify_molt_tier([".z1-control/ratify.py"]) == 2


def test_tier_2_workflow():
    """.github/workflows/ change -> Tier 2"""
    assert classify_molt_tier([".github/workflows/molt-tier-check.yml"]) == 2


def test_tier_max():
    """Tier 2 + Tier 1 -> Tier 2 (max), in either order"""
    assert classify_molt_tier(["behavior_spec.json", ".z1-control/ratify.py"]) == 2
    assert classify_molt_tier([".z1-control/ratify.py", "behavior_spec.json"]) == 2


# ── False negatives: every published rule entry must actually fire ────────────

def test_no_false_negatives_constants():
    """Each CONSTANTS entry classifies at Tier 1 or above on a realistic path."""
    samples = {
        "RESOURCE_UNITS.yaml":   "RESOURCE_UNITS.yaml",
        "behavior_spec.json":    "behavior_spec.json",
        "integrity_modes.json":  "integrity_modes.json",
        "rubrics/":              "rubrics/humility.yaml",
        "weights/":              "weights/priority.json",
        "caps/":                 "caps/agent_caps.json",
        "half-lives.yaml":       "half-lives.yaml",
        "constants.json":        "constants.json",
        "constants_config.json": "constants_config.json",
        "constitution.json":     "constitution.json",
    }
    assert set(samples) == set(molt.CONSTANTS_PATHS), (
        "CONSTANTS_PATHS changed without updating this test — the rule is public, "
        "so a change to it must be visible here too"
    )
    for entry, path in samples.items():
        assert classify_molt_tier([path]) >= 1, f"{entry!r} did not fire on {path!r}"


def test_no_false_negatives_gates():
    """Each GATE entry classifies at exactly Tier 2 on a realistic path."""
    samples = {
        ".github/workflows/":       ".github/workflows/quality-baseline.yml",
        "tools/validate.py":        "tools/validate.py",
        "tools/ratify.py":          "tools/ratify.py",
        "system_graph.json":        "system_graph.json",
        "system_graph.md":          "system_graph.md",
        ".github/CODEOWNERS":       ".github/CODEOWNERS",
        "ci_gates.py":              "ci_gates.py",
        "z2_ratification_gate.yml": "z2_ratification_gate.yml",
        ".z1-control/ratify.py":    ".z1-control/ratify.py",
        ".z1-control/validate.py":  ".z1-control/validate.py",
        ".z1-control/render.py":    ".z1-control/render.py",
        "tools/molting_protocol_diff_v1_0.py": "tools/molting_protocol_diff_v1_0.py",
    }
    assert set(samples) == set(molt.GATE_PATHS), (
        "GATE_PATHS changed without updating this test — widening or narrowing "
        "the gate rule must not be possible without a visible diff here"
    )
    for entry, path in samples.items():
        assert classify_molt_tier([path]) == 2, f"{entry!r} did not fire on {path!r}"


def test_repo_gate_paths_exist_on_disk():
    """
    The spec this classifier came from listed tools/validate.py and
    tools/ratify.py. Neither exists in this repository; the gates are under
    .z1-control/. A rule that names files nobody has is a rule that silently
    never fires, so at least one real gate script must be covered.
    """
    root = TOOLS_DIR.parent
    live = [e for e in molt.GATE_PATHS
            if not e.endswith("/") and (root / e).is_file()]
    assert live, "no GATE_PATHS entry resolves to a file in this repo"
    assert ".z1-control/ratify.py" in live


# ── False positives: the substring trap ───────────────────────────────────────

def test_the_rule_can_see_its_own_edits():
    """
    A PR that changes only this classifier is a PR that changes the tier rule.
    If that measured Tier 0, the rule could be rewritten — an entry deleted,
    the max inverted — with nothing flagging it. A control that cannot see its
    own edits is not a control.
    """
    assert classify_molt_tier(["tools/molting_protocol_diff_v1_0.py"]) == 2
    assert molt.__file__.endswith(tuple(
        e for e in molt.GATE_PATHS if e.endswith("molting_protocol_diff_v1_0.py")
    )), "the module lists a path that is not its own — the self-reference is broken"


def test_handicaps_is_not_caps():
    """A raw `'caps/' in path` test matches 'handicaps/'. Segment matching must not."""
    assert classify_molt_tier(["docs/handicaps/notes.md"]) == 0


def test_filename_must_match_on_a_segment_boundary():
    """'behavior_spec.json' must not match 'my_behavior_spec.json' or a .md about it."""
    assert classify_molt_tier(["my_behavior_spec.json"]) == 0
    assert classify_molt_tier(["docs/behavior_spec.json.md"]) == 0
    assert classify_molt_tier(["acat/behavior_spec.json"]) == 1, "a nested real one still counts"


def test_workflow_directory_not_a_lookalike():
    assert classify_molt_tier(["docs/github/workflows/guide.md"]) == 0
    assert classify_molt_tier([".github/ISSUE_TEMPLATE/bug.md"]) == 0


# ── Totality: the classifier must never raise ─────────────────────────────────

def test_empty_and_malformed_input_is_tier_0():
    assert classify_molt_tier([]) == 0
    assert classify_molt_tier(None) == 0
    assert classify_molt_tier(["", "   ", None]) == 0


def test_non_iterable_input_does_not_raise():
    """
    The docstring promises totality. A scalar reaching the loop would raise
    TypeError instead — and a classifier that can be made to throw is a
    classifier that can be made to skip a gate.
    """
    for scalar in (42, 3.5, object(), True):
        assert classify_molt_tier(scalar) == 0
        assert molt.tier_evidence(scalar) == []


def test_path_normalization():
    """git, CI and Windows all hand over slightly different path shapes."""
    assert classify_molt_tier(["./behavior_spec.json"]) == 1
    assert classify_molt_tier([".z1-control\\ratify.py"]) == 2
    assert classify_molt_tier(["  behavior_spec.json  "]) == 1
    assert classify_molt_tier("behavior_spec.json") == 1, "a bare string is one path"


# ── Evidence and gap records ──────────────────────────────────────────────────

def test_tier_evidence_names_the_rule_that_fired():
    rows = molt.tier_evidence(["README.md", "behavior_spec.json",
                               ".github/workflows/x.yml"])
    assert [r["path"] for r in rows] == ["behavior_spec.json", ".github/workflows/x.yml"], \
        "unmatched paths are omitted, matched ones keep diff order"
    assert rows[0]["matched"] == ["behavior_spec.json"]
    assert rows[1]["tier"] == 2


def test_parse_claimed_tier():
    assert molt.parse_claimed_tier("molt_tier_claimed: 2") == 2
    assert molt.parse_claimed_tier("**molt_tier_claimed:** `1`") == 1
    assert molt.parse_claimed_tier("no such field") is None
    assert molt.parse_claimed_tier("") is None
    assert molt.parse_claimed_tier(None) is None
    assert molt.parse_claimed_tier("molt_tier_claimed: 7") is None, "out of range is no claim"


def test_multi_digit_claim_is_not_truncated_to_its_first_digit():
    """
    A single-digit capture reads `molt_tier_claimed: 10` as a claim of Tier 1
    and then scores a gap against it — inventing a hypothesis the author never
    made, and putting a fabricated row in the audit ledger.
    """
    assert molt.parse_claimed_tier("molt_tier_claimed: 10") is None
    assert molt.parse_claimed_tier("molt_tier_claimed: 22") is None
    assert molt.parse_claimed_tier("molt_tier_claimed: 2") == 2


def test_unfilled_template_placeholder_is_not_a_claim_of_zero():
    """
    The template ships `molt_tier_claimed: [0 | 1 | 2]`. Reading that as a
    claim of Tier 0 would manufacture an under-claim on every PR whose author
    simply never filled the field in — turning the audit signal into noise.
    """
    assert molt.parse_claimed_tier("**molt_tier_claimed:** `[0 | 1 | 2]`") is None


def test_gap_record_verdicts():
    assert molt.molt_tier_gap_record(1, 0, 2)["verdict"] == "UNDER_CLAIM"
    assert molt.molt_tier_gap_record(1, 0, 2)["accuracy_impact"] == "HIGH"
    assert molt.molt_tier_gap_record(1, 2, 1)["verdict"] == "OVER_CLAIM"
    assert molt.molt_tier_gap_record(1, 2, 1)["accuracy_impact"] == "LOW"
    assert molt.molt_tier_gap_record(1, 1, 1)["verdict"] == "MATCH"
    assert molt.molt_tier_gap_record(1, None, 2)["verdict"] == "MISSING"
    assert molt.molt_tier_gap_record(1, 0, 2)["gap"] == 2


# ── run() envelope ────────────────────────────────────────────────────────────

def test_run_measures_and_warns_without_failing():
    out = molt.run({"filepaths": [".github/workflows/x.yml"], "molt_tier_claimed": 0})
    assert out["tier"] == 2
    assert out["status"] == "WARN", "a gap warns; it never FAILs — this gate does not block"
    assert out["gap"]["verdict"] == "UNDER_CLAIM"


def test_run_refuses_input_it_cannot_read():
    """Reporting Tier 0 on unreadable input would be a silent false negative."""
    for bad in ({"nothing": True}, {"filepaths": 42}, "not a dict"):
        try:
            molt.run(bad)
        except molt.SpecLoadFailed:
            continue
        raise AssertionError(f"run({bad!r}) should have raised SpecLoadFailed")


def test_cli_rejects_valid_json_that_is_not_an_object():
    """
    `--input '[]'` loads fine as JSON. Applying --claimed/--pr to a list raises
    TypeError from argparse handling rather than reporting SPEC_LOAD_FAILED, so
    the shape is checked before the overrides are applied.
    """
    import subprocess
    root = TOOLS_DIR.parent
    proc = subprocess.run(
        [sys.executable, "tools/molting_protocol_diff_v1_0.py",
         "--input", "[]", "--claimed", "1", "--no-report"],
        cwd=root, capture_output=True, text=True,
    )
    assert proc.returncode == 2, proc.stderr
    assert "SPEC_LOAD_FAILED" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_smoke_test_passes():
    assert molt.run_smoke_test() is True


if __name__ == "__main__":
    failures = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as exc:  # noqa: BLE001 - standalone runner
                failures.append((name, exc))
                print(f"  FAIL  {name}: {exc}")
    print(f"\n{TOOL_NAME}: {len(failures)} failed")
    sys.exit(1 if failures else 0)

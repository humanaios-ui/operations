"""
test_pre_submit.py
Builder v1.7 compliant
HumanAIOS

Covers the parsing and policy helpers in tools/pre_submit.py. The git-facing
checks are exercised by running the script against a real branch, not here.

The falsifier for the claim parser is "a template placeholder or a commented
example is not read as a filled-in claim." The secret fixtures are assembled
from fragments so this file does not itself match the secret patterns.

Runs under pytest, and standalone via `python3 tools/tests/test_pre_submit.py`.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools" / "pre_submit.py"


def _load():
    spec = importlib.util.spec_from_file_location("pre_submit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    # dataclasses looks the module up by name while the class body runs.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ps = _load()


def test_placeholder_is_not_a_claim():
    body = "**molt_tier_claimed:** `[0 | 1 | 2]`"
    assert ps.claimed_tier(body) is None


def test_filled_claim_is_parsed_in_each_written_form():
    assert ps.claimed_tier("**molt_tier_claimed:** `1`") == 1
    assert ps.claimed_tier("molt_tier_claimed: 2") == 2
    assert ps.claimed_tier("molt_tier_claimed: [0]") == 0


def test_two_digit_value_is_not_read_as_a_claim():
    # "10" must not parse as a claim of Tier 1.
    assert ps.claimed_tier("molt_tier_claimed: 10") is None


def test_commented_example_is_ignored():
    assert ps.claimed_tier("<!-- molt_tier_claimed: 2 -->") is None
    assert ps.smag_prediction("<!-- Format: smag_p: 0.XX -->") is None


def test_smag_prediction_parsed_and_meta_is_not_confused():
    assert ps.smag_prediction("smag_p: 0.90") == 0.9
    assert ps.smag_prediction("smag_p_meta: 0.82") is None


def test_zone_boxes_counted_so_exactly_one_is_checkable():
    assert ps.zone_boxes_ticked("- [x] **Z1** — AI-executable") == 1
    assert ps.zone_boxes_ticked("- [ ] **Z1** — AI-executable") == 0
    assert ps.zone_boxes_ticked("- [x] **Z1** a\n- [x] **Z2** b") == 2


def test_smag_outside_zero_to_one_is_void():
    # Matches the canonical lint: 1.5 is not a valid prediction.
    assert ps.smag_prediction("smag_p: 1.5") is None
    assert ps.smag_prediction("smag_p: 1.0") == 1.0


def test_zone_suggestion_precedence():
    assert ps.suggest_zone(0, ["docs/a.md"])[0] == "Z1"
    assert ps.suggest_zone(2, [".github/workflows/x.yml"])[0] == "Z2"
    assert ps.suggest_zone(0, ["REGISTERED.md"])[0] == "Z2"
    assert ps.suggest_zone(0, ["deploy/prod.yaml"])[0] == "Z3"
    # Z3 outranks Z2: a credential-bearing gate change needs an operator run.
    assert ps.suggest_zone(2, [".env.prod"])[0] == "Z3"


def test_secret_labels_fire_on_fixed_shapes():
    gh_token = "gh" + "p_" + "A" * 36
    aws_key = "AK" + "IA" + "B" * 16
    key_header = "-----BEGIN " + "RSA " + "PRIVATE " + "KEY-----"
    assert ps.secret_labels(f"token = {gh_token}") == ["GitHub token"]
    assert ps.secret_labels(f"id = {aws_key}") == ["AWS access key"]
    assert ps.secret_labels(key_header) == ["private key"]


def test_secret_labels_ignore_ordinary_text():
    assert ps.secret_labels("def main(): return 0") == []
    assert ps.secret_labels("gh_short = 'ghp_abc'") == []


def test_draft_keeps_placeholders_and_adds_report():
    template = (
        "## Molt Classification\n\n"
        "**molt_tier_claimed:** `[0 | 1 | 2]`\n\n"
        "## Notes\n"
    )
    checks = [ps.Check("Readiness", "pass", "verify_pr_readiness.sh passed")]
    draft = ps.build_draft(template, 2, [], ("Z2", "gate change"),
                           [".github/workflows/x.yml"], checks)
    assert "`[0 | 1 | 2]`" in draft  # the author still has to write the claim
    assert "measured Tier 2" in draft
    assert "Suggested zone: Z2" in draft
    assert "Still open for the author" in draft
    # The draft must not itself be read as a filled-in claim.
    assert ps.claimed_tier(draft) is None


def test_lint_flags_unfilled_fields_and_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "body.md"
        path.write_text("**molt_tier_claimed:** `[0 | 1 | 2]`\n- [ ] **Z1** x\n",
                        encoding="utf-8")
        results = {c.name: c for c in ps.lint_body(path, 1)}
        assert results["Body: molt claim"].status == "warn"
        assert results["Body: smag_p"].status == "warn"
        assert results["Body: zone"].status == "warn"

        path.write_text("**molt_tier_claimed:** `0`\nsmag_p: 0.9\n- [x] **Z1** x\n",
                        encoding="utf-8")
        results = {c.name: c for c in ps.lint_body(path, 1)}
        # A mismatch is audit data, not a warning. Under-claims are the signal.
        assert results["Body: molt claim"].status == "info"
        assert results["Body: smag_p"].status == "pass"
        assert results["Body: zone"].status == "pass"

        path.write_text("**molt_tier_claimed:** `0`\nsmag_p: 0.9\n- [x] **Z1** x\n- [x] **Z2** y\n",
                        encoding="utf-8")
        results = {c.name: c for c in ps.lint_body(path, 0)}
        assert results["Body: zone"].status == "warn", "two boxes must not pass"


def test_strict_loader_rejects_duplicate_keys():
    try:
        import yaml
    except ImportError:
        if "pytest" in sys.modules:
            import pytest
            pytest.skip("PyYAML not installed")
        print("skip: PyYAML not installed")
        return
    loader = ps._strict_loader(yaml)
    try:
        yaml.load("a: 1\na: 2\n", Loader=loader)
    except yaml.constructor.ConstructorError:
        pass
    else:
        raise AssertionError("duplicate key was accepted")
    assert yaml.load("a: 1\nb: 2\n", Loader=loader) == {"a": 1, "b": 2}


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failures else 0)

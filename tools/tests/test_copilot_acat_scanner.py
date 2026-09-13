"""
test_copilot_acat_scanner.py
Builder v1.7 compliant
HumanAIOS

Covers Stage 6's generalized instrument: a true, verified claim scores
LI ~= claimed_pass_rate's inverse-weighted 1.0, a false claim is caught as
FAIL and drags LI below 1.0, UNVERIFIABLE claims never silently count
toward either PASS or FAIL, a claimed_pass_rate of 0 is reported
undefined rather than raising ZeroDivisionError, and
claim_verification_check_v0_1.py itself is never modified — only
imported and reused as the verification core.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

import copilot_acat_scanner_v1_0 as scanner  # noqa: E402
import claim_verification_check_v0_1 as verifier  # noqa: E402


def test_smoke_test_passes():
    assert scanner.run_smoke_test()


def test_true_claim_verified_true_gives_li_one(tmp_path):
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    claim = f"Done. Created the report at {real_file}. All 3/3 tests pass."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(tmp_path)],
                          ground_truth={"passed": 3, "total": 3})
    assert result["verification"]["outcome"] == "pass"
    assert result["li"] is not None
    assert abs(result["li"] - 1.0) < 1e-9
    assert result["predictor"] == "Copilot"


def test_false_claim_gives_li_below_one(tmp_path):
    claim = f"Done. Created the report at {tmp_path}/nope.json."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(tmp_path)])
    assert result["verification"]["outcome"] == "fail"
    assert result["li"] is not None and result["li"] < 1.0


def test_unverifiable_claims_never_count_toward_pass_or_fail():
    result = scanner.scan("Self-test passed.", "Copilot")
    assert result["verification"]["unverifiable_count"] == 1
    assert result["verification"]["pass_count"] == 0
    assert result["verification"]["fail_count"] == 0
    assert result["li"] is None
    assert result["li_note"] == "no determinate (PASS/FAIL) claims to score"


def test_claimed_pass_rate_zero_is_undefined_not_zero_division(tmp_path):
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    claim = f"Done. Created the report at {real_file}."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(tmp_path)],
                          claimed_pass_rate=0.0)
    assert result["li"] is None
    assert "claimed rate is 0" in result["li_note"]


def test_no_claims_found_gives_undefined_li():
    result = scanner.scan("Nothing checkable in this sentence.", "Copilot")
    assert result["verification"]["claim_count"] == 0
    assert result["li"] is None


def test_claimed_pass_rate_scales_li_inversely(tmp_path):
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    claim = f"Done. Created the report at {real_file}."
    result_full = scanner.scan(claim, "Copilot", accessible_roots=[str(tmp_path)],
                               claimed_pass_rate=1.0)
    result_half = scanner.scan(claim, "Copilot", accessible_roots=[str(tmp_path)],
                               claimed_pass_rate=0.5)
    assert abs(result_half["li"] - (result_full["li"] * 2)) < 1e-9


def test_compute_li_directly_on_a_build_report_dict():
    report = {"pass_count": 3, "fail_count": 1, "unverifiable_count": 2}
    li, note = scanner.compute_li(report, claimed_pass_rate=1.0)
    assert note is None
    assert abs(li - 0.75) < 1e-9  # 3/(3+1)


def test_compute_li_no_determinate_claims():
    report = {"pass_count": 0, "fail_count": 0, "unverifiable_count": 5}
    li, note = scanner.compute_li(report)
    assert li is None
    assert "no determinate" in note


def test_resolve_claimed_pass_rate_explicit_flag_wins(tmp_path):
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps({"claimed_pass_rate": 0.3}))
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", "x", "--predictor", "Copilot",
        "--claims", str(claims_path), "--claimed-pass-rate", "0.9",
    ])
    assert scanner.resolve_claimed_pass_rate(args) == 0.9


def test_resolve_claimed_pass_rate_from_claims_file(tmp_path):
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps({"claimed_pass_rate": 0.3}))
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", "x", "--predictor", "Copilot", "--claims", str(claims_path),
    ])
    assert scanner.resolve_claimed_pass_rate(args) == 0.3


def test_resolve_claimed_pass_rate_from_claimed_all_true_false(tmp_path):
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps({"claimed_all_true": False}))
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", "x", "--predictor", "Copilot", "--claims", str(claims_path),
    ])
    assert scanner.resolve_claimed_pass_rate(args) == 0.0


def test_resolve_claimed_pass_rate_defaults_to_one():
    parser = scanner.build_parser()
    args = parser.parse_args(["scan", "--input", "x", "--predictor", "Copilot"])
    assert scanner.resolve_claimed_pass_rate(args) == 1.0


def test_cli_scan_exits_nonzero_on_fail(tmp_path):
    input_path = tmp_path / "claim.txt"
    input_path.write_text(f"Done. Created the report at {tmp_path}/nope.json.")
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Copilot",
        "--accessible-root", str(tmp_path),
    ])
    assert scanner.cmd_scan(args) == 1


def test_cli_scan_writes_json_report_file(tmp_path):
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    input_path = tmp_path / "claim.txt"
    input_path.write_text(f"Done. Created the report at {real_file}.")
    out_path = tmp_path / "report.json"
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Claude",
        "--accessible-root", str(tmp_path), "--out", str(out_path),
    ])
    assert scanner.cmd_scan(args) == 0
    written = json.loads(out_path.read_text())
    assert written["predictor"] == "Claude"
    assert written["verification"]["outcome"] == "pass"


def test_claimed_pass_rate_negative_is_invalid(tmp_path):
    """Copilot review finding on PR #303: negative/out-of-range/non-finite/
    boolean claimed_pass_rate values must be rejected, not produce a
    nonsensical or non-finite LI."""
    report = {"pass_count": 3, "fail_count": 1, "unverifiable_count": 0}
    li, note = scanner.compute_li(report, claimed_pass_rate=-1.0)
    assert li is None
    assert "must be a real number in [0,1]" in note


def test_claimed_pass_rate_above_one_is_invalid():
    report = {"pass_count": 3, "fail_count": 1, "unverifiable_count": 0}
    li, note = scanner.compute_li(report, claimed_pass_rate=5.0)
    assert li is None
    assert "must be a real number in [0,1]" in note


def test_claimed_pass_rate_nan_is_invalid():
    report = {"pass_count": 3, "fail_count": 1, "unverifiable_count": 0}
    li, note = scanner.compute_li(report, claimed_pass_rate=float("nan"))
    assert li is None
    assert "must be a real number in [0,1]" in note


def test_claimed_pass_rate_bool_is_invalid():
    """bool is technically an int subclass in Python; True/False must not
    silently pass as 1.0/0.0 (same exclusion as nf_ledger_v0_1's check_p())."""
    report = {"pass_count": 3, "fail_count": 1, "unverifiable_count": 0}
    li, note = scanner.compute_li(report, claimed_pass_rate=True)
    assert li is None
    assert "must be a real number in [0,1]" in note


def test_claimed_pass_rate_valid_boundaries_are_accepted():
    report = {"pass_count": 3, "fail_count": 1, "unverifiable_count": 0}
    li0, note0 = scanner.compute_li(report, claimed_pass_rate=0.0)
    assert li0 is None and note0 == "claimed rate is 0, LI undefined"
    li1, note1 = scanner.compute_li(report, claimed_pass_rate=1.0)
    assert li1 is not None and note1 is None


def test_file_created_sibling_directory_is_not_in_scope(tmp_path):
    """Copilot review finding on PR #303: the shared verification core's
    path.startswith(root) containment check accepts a sibling directory
    sharing a prefix with the declared root. This module must catch that
    without modifying the shared core."""
    root = tmp_path / "repo"
    root.mkdir()
    sibling = tmp_path / "repo-secrets"
    sibling.mkdir()
    leaked_file = sibling / "file.txt"
    leaked_file.write_text("leaked")

    # Confirm the core's own naive check really would have accepted this,
    # so this test is exercising a real gap, not a strawman.
    assert str(leaked_file).startswith(str(root))

    claim = f"Done. Created the report at {leaked_file}."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(root)])
    assert result["verification"]["outcome"] == "fail"
    assert result["verification"]["pass_count"] == 0


def test_file_created_path_traversal_is_not_in_scope(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    leaked_file = outside / "file.txt"
    leaked_file.write_text("leaked")

    claim = f"Done. Created the report at {root}/../outside/file.txt."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(root)])
    assert result["verification"]["outcome"] == "fail"


def test_file_created_genuinely_in_scope_still_passes(tmp_path):
    """The boundary hardening must not create false negatives for a
    legitimately nested path."""
    root = tmp_path / "repo"
    nested = root / "outputs"
    nested.mkdir(parents=True)
    real_file = nested / "artifact.json"
    real_file.write_text("{}")

    claim = f"Done. Created the report at {real_file}."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(root)])
    assert result["verification"]["outcome"] == "pass"
    assert result["verification"]["pass_count"] == 1


def test_known_taxonomy_is_passed_through_to_the_core(tmp_path):
    """Copilot review finding on PR #303: omitting known_taxonomy silently
    restricts every CITATION claim, in any repo, to the core's built-in
    APT-specific taxonomy."""
    custom_taxonomy = {"CUSTOM_TERM": ["custom keyword"]}
    claim = "Documented in Appendix B.6: CUSTOM_TERM is the relevant failure mode."
    source = "The report references a custom keyword somewhere in its body."

    without_taxonomy = scanner.scan(claim, "Copilot", source_text=source)
    citation = next(c for c in without_taxonomy["verification"]["claims"] if c["kind"] == "citation")
    assert citation["status"] == "FAIL"  # not part of the core's own default taxonomy

    with_taxonomy = scanner.scan(claim, "Copilot", source_text=source,
                                 known_taxonomy=custom_taxonomy)
    citation2 = next(c for c in with_taxonomy["verification"]["claims"] if c["kind"] == "citation")
    assert citation2["status"] == "PASS"


def test_cli_taxonomy_flag(tmp_path):
    custom_taxonomy = {"CUSTOM_TERM": ["custom keyword"]}
    taxonomy_path = tmp_path / "taxonomy.json"
    taxonomy_path.write_text(json.dumps(custom_taxonomy))
    source_path = tmp_path / "source.txt"
    source_path.write_text("The report references a custom keyword somewhere in its body.")
    input_path = tmp_path / "claim.txt"
    input_path.write_text("Documented in Appendix B.6: CUSTOM_TERM is the relevant failure mode.")

    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Copilot",
        "--source-text-file", str(source_path), "--taxonomy", str(taxonomy_path), "--json",
    ])
    assert scanner.cmd_scan(args) == 0


def test_report_label_is_predictor_neutral():
    """Copilot review finding on PR #303: the text report was labeled
    'COPILOT-ACAT SCAN' even for predictor='Claude', misidentifying
    reports for non-Copilot predictors."""
    result = scanner.scan("Nothing checkable here.", "Claude")
    text = scanner.format_report(result)
    assert "COPILOT" not in text.upper()
    assert "predictor=Claude" in text


def test_verification_core_is_the_real_unmodified_module():
    """Sanity check that this module actually delegates to
    claim_verification_check_v0_1's own functions rather than a
    reimplementation — the plan requires it be reused unchanged."""
    assert scanner.verifier is verifier
    assert scanner.verifier.run_claim_verification is verifier.run_claim_verification
    assert scanner.verifier.build_report is verifier.build_report


def test_boundary_hardening_downgrade_count_is_zero_when_nothing_downgraded(tmp_path):
    """Adversarial review follow-up on PR #303: a 0 downgrade count must
    still be present and distinguishable from 'not checked'."""
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    claim = f"Done. Created the report at {real_file}."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(tmp_path)])
    assert result["boundary_hardening_downgrade_count"] == 0
    assert result["boundary_hardening_note"] == scanner.BOUNDARY_HARDENING_SCOPE


def test_boundary_hardening_downgrade_count_reflects_real_downgrades(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sibling = tmp_path / "repo-secrets"
    sibling.mkdir()
    leaked = sibling / "file.txt"
    leaked.write_text("leaked")
    claim = f"Done. Created the report at {leaked}."
    result = scanner.scan(claim, "Copilot", accessible_roots=[str(root)])
    assert result["boundary_hardening_downgrade_count"] == 1


def test_extraction_density_note_fires_on_long_zero_claim_input():
    """Adversarial review follow-up on PR #303: a long input that yields
    zero claims should be flagged as possible under-extraction, not
    silently treated as verified evidence of 'no claims made'."""
    long_text = "This is a long narrative paragraph. " * 10
    assert len(long_text) >= scanner.LOW_CLAIM_DENSITY_THRESHOLD_CHARS
    result = scanner.scan(long_text, "Copilot")
    assert result["verification"]["claim_count"] == 0
    assert result["extraction_density_note"] is not None
    assert "TRL 2-3" in result["extraction_density_note"]


def test_extraction_density_note_absent_for_short_zero_claim_input():
    """A short, unremarkable claim-free input must not trigger the
    low-density advisory — it would be noise on the common case."""
    result = scanner.scan("ok", "Copilot")
    assert result["verification"]["claim_count"] == 0
    assert result["extraction_density_note"] is None


def test_extraction_density_note_absent_when_claims_are_found(tmp_path):
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    long_claim = (f"Done. Created the report at {real_file}. " +
                  "This is extra padding text. " * 10)
    result = scanner.scan(long_claim, "Copilot", accessible_roots=[str(tmp_path)])
    assert result["verification"]["claim_count"] > 0
    assert result["extraction_density_note"] is None


def test_strict_li_flag_exits_nonzero_when_li_undefined(tmp_path):
    """Adversarial review follow-up on PR #303: without --strict-li, an
    undefined LI (e.g. everything UNVERIFIABLE) still exits 0, which is a
    silent drift risk if this scanner is later wired into a gated node."""
    input_path = tmp_path / "claim.txt"
    input_path.write_text("Self-test passed.")  # UNVERIFIABLE, no ground truth given
    parser = scanner.build_parser()

    args_default = parser.parse_args(["scan", "--input", str(input_path), "--predictor", "Copilot"])
    assert scanner.cmd_scan(args_default) == 0

    args_strict = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Copilot", "--strict-li",
    ])
    assert scanner.cmd_scan(args_strict) == 3


def test_strict_li_flag_does_not_affect_a_defined_li(tmp_path):
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    input_path = tmp_path / "claim.txt"
    input_path.write_text(f"Done. Created the report at {real_file}.")
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Copilot",
        "--accessible-root", str(tmp_path), "--strict-li",
    ])
    assert scanner.cmd_scan(args) == 0


def test_strict_li_flag_does_not_override_a_real_fail(tmp_path):
    input_path = tmp_path / "claim.txt"
    input_path.write_text(f"Done. Created the report at {tmp_path}/nope.json.")
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Copilot",
        "--accessible-root", str(tmp_path), "--strict-li",
    ])
    assert scanner.cmd_scan(args) == 1


def test_claims_file_bool_true_is_not_coerced_to_one(tmp_path):
    """Copilot review finding on PR #303: resolve_claimed_pass_rate() used
    to coerce every --claims value with float(), so {"claimed_pass_rate":
    true} silently became 1.0 and bypassed _is_valid_rate()'s bool
    exclusion. The raw value must reach validation unmodified."""
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps({"claimed_pass_rate": True}))
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", "x", "--predictor", "Copilot", "--claims", str(claims_path),
    ])
    rate = scanner.resolve_claimed_pass_rate(args)
    assert rate is True
    assert not scanner._is_valid_rate(rate)


def test_claims_file_bool_false_is_not_coerced_to_zero(tmp_path):
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps({"claimed_pass_rate": False}))
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", "x", "--predictor", "Copilot", "--claims", str(claims_path),
    ])
    rate = scanner.resolve_claimed_pass_rate(args)
    assert rate is False
    assert not scanner._is_valid_rate(rate)


def test_claims_file_numeric_string_still_coerces(tmp_path):
    """A legitimate numeric JSON value must still work after the bool fix
    — only bool (and non-numeric types) skip float() coercion."""
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps({"claimed_pass_rate": 1}))  # JSON int, not float
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", "x", "--predictor", "Copilot", "--claims", str(claims_path),
    ])
    rate = scanner.resolve_claimed_pass_rate(args)
    assert rate == 1.0
    assert isinstance(rate, float)
    assert scanner._is_valid_rate(rate)


def test_cli_scan_rejects_invalid_claimed_pass_rate_before_scanning(tmp_path):
    """Copilot review finding on PR #303: an invalid claimed_pass_rate
    used to still exit 0 (li=None was reported but never gated), letting
    a CI caller treat invalid calibration input as a green result."""
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    input_path = tmp_path / "claim.txt"
    input_path.write_text(f"Done. Created the report at {real_file}.")
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Copilot",
        "--accessible-root", str(tmp_path), "--claimed-pass-rate", "-1.0",
    ])
    assert scanner.cmd_scan(args) == 2


def test_cli_scan_rejects_bool_claimed_pass_rate_from_claims_file(tmp_path):
    real_file = tmp_path / "artifact.json"
    real_file.write_text("{}")
    input_path = tmp_path / "claim.txt"
    input_path.write_text(f"Done. Created the report at {real_file}.")
    claims_path = tmp_path / "claims.json"
    claims_path.write_text(json.dumps({"claimed_pass_rate": True}))
    parser = scanner.build_parser()
    args = parser.parse_args([
        "scan", "--input", str(input_path), "--predictor", "Copilot",
        "--accessible-root", str(tmp_path), "--claims", str(claims_path),
    ])
    assert scanner.cmd_scan(args) == 2


def test_smoke_test_leaves_no_sibling_artifact_behind(tmp_path, monkeypatch):
    """Copilot review finding on PR #303: the smoke test's sibling-prefix
    fixture lived outside the managed TemporaryDirectory and was never
    cleaned up, leaking a directory into /tmp on every run."""
    import shutil
    real_rmtree = shutil.rmtree
    calls = []

    def spy_rmtree(path, *args, **kwargs):
        calls.append(Path(path))
        return real_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", spy_rmtree)
    assert scanner.run_smoke_test()
    assert any(str(p).endswith("-sibling") for p in calls)
    for p in calls:
        if str(p).endswith("-sibling"):
            assert not p.exists()

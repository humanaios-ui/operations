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


def test_verification_core_is_the_real_unmodified_module():
    """Sanity check that this module actually delegates to
    claim_verification_check_v0_1's own functions rather than a
    reimplementation — the plan requires it be reused unchanged."""
    assert scanner.verifier is verifier
    assert scanner.verifier.run_claim_verification is verifier.run_claim_verification
    assert scanner.verifier.build_report is verifier.build_report

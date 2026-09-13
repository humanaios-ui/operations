#!/usr/bin/env python3
"""
copilot_acat_scanner_v1_0.py
Builder v1.7 compliant
HumanAIOS — Stage 6 of the execution-grounded calibration plan

Generalizes tools/echoes_copilot_acat_scanner_v0_1.py's Phase1-vs-Phase3
Learning Index pattern from one Unity/C# repo's bespoke privacy checks to
any repo and any AI build agent's self-report text — issue comments, PR
descriptions, commit messages — by routing verification through
tools/claim_verification_check_v0_1.py's own PASS/FAIL/UNVERIFIABLE
methodology, UNCHANGED, as the sole verification core. Nothing here
re-implements or forks claim extraction or evaluation; this module only
adds a predictor-tagged LI computation on top of that tool's own report.

WHAT WAS ECHOES-SPECIFIC, AND WHY IT DOES NOT GENERALIZE
------------------------------------------------------------
echoes_copilot_acat_scanner_v0_1.py's scan_repo() is a bespoke regex
scanner for one project's own checkable constraints: Unity C# event-logger
calls, a narrative-field denylist, an onboarding-copy privacy-disclosure
check. None of that is a general property of "did an AI build agent do
what it claimed" — it is Echoes' own Definition-of-Done, encoded once.
Generalizing it would mean inventing a universal static analyzer, which
this plan explicitly does not attempt (claim_verification_check_v0_1.py's
own docstring calls itself TRL 2-3, heuristic, not a parser). That file is
therefore left as-is: a legitimate, working, project-specific instrument
for Echoes, not something this module supersedes or modifies.

What DOES generalize, and is lifted here, is the surrounding pattern:
declare (Phase 1, a self-report claim), verify against real evidence
(Phase 3), compare, and report a ratio — the same SAY-DO-CHECK-CALIBRATE
loop every other stage in this plan implements. claim_verification_check_
v0_1.py already performs Phase 3 generically (FILE_CREATED against a real
accessible_root, TEST_RESULT against a real ground_truth report, CITATION
against real source_text) for any text handed to it, from any predictor,
in any repo. This module's only job is to turn its PASS/FAIL/UNVERIFIABLE
report into a Phase3/Phase1 Learning Index, exactly as
echoes_copilot_acat_scanner_v0_1.py's compute_li() did, but keyed to a
named predictor instead of one hard-coded "privacy_check" claim shape.

WHAT "PHASE 1" MEANS HERE, AND THE claimed_pass_rate DEFAULT
------------------------------------------------------------------
The claim text handed to --input IS Phase 1: whatever the predictor wrote
stands as its own self-report, exactly as an issue comment or PR
description would be read by a human reviewer. Phase 1 confidence is
"claimed_pass_rate": 1.0 by default — a predictor that states a claim
without hedging is implicitly standing behind it — but can be overridden
via --claimed-pass-rate or a --claims file carrying an explicit aggregate
confidence (e.g. {"claimed_pass_rate": 0.9}), mirroring
echoes_copilot_acat_scanner_v0_1.py's own separate "claims" input for
callers that track predictor-stated confidence apart from the claim text
itself.

LI = Phase3_pass_rate / Phase1_claimed_pass_rate, restricted to claims
claim_verification_check resolved to PASS or FAIL — an UNVERIFIABLE claim
is neither confirmed nor refuted and must not silently count as either
(same convention as dimension_attribution_v1_0.py's resolved-only scoring
and claim_verification_check's own build_report()).

Usage:
  python3 tools/copilot_acat_scanner_v1_0.py scan \\
      --input pr_body.txt --predictor Copilot \\
      --accessible-root /path/to/repo --ground-truth ci_results.json
  python3 tools/copilot_acat_scanner_v1_0.py scan --input pr_body.txt \\
      --predictor Copilot --claimed-pass-rate 0.9 --json
  python3 tools/copilot_acat_scanner_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
import claim_verification_check_v0_1 as verifier  # noqa: E402  (unchanged verification core)

TOOL_NAME = "copilot_acat_scanner"
TOOL_VERSION = "1.0.0"

INTERPRETATION_NOTE = (
    "LI = Phase3_pass_rate / Phase1_claimed_pass_rate over claims resolved to "
    "PASS or FAIL only; UNVERIFIABLE claims are excluded from both, not treated "
    "as either outcome. See module docstring for what does and does not "
    "generalize from echoes_copilot_acat_scanner_v0_1.py."
)


def compute_li(report: dict, claimed_pass_rate: float = 1.0) -> Tuple[Optional[float], Optional[str]]:
    """report is claim_verification_check_v0_1.build_report()'s own output,
    unmodified. LI is undefined (None, with a reason) when there is
    nothing determinate to score, or when the claimed rate is 0 (nothing
    to divide by that would produce a meaningful ratio rather than an
    artifact of the denominator)."""
    relevant = report["pass_count"] + report["fail_count"]
    if relevant == 0:
        return None, "no determinate (PASS/FAIL) claims to score"
    if claimed_pass_rate == 0:
        return None, "claimed rate is 0, LI undefined"
    phase3_pass_rate = report["pass_count"] / relevant
    return phase3_pass_rate / claimed_pass_rate, None


def resolve_claimed_pass_rate(args: argparse.Namespace) -> float:
    """--claimed-pass-rate wins if given explicitly; otherwise a --claims
    file's "claimed_pass_rate" (a stated aggregate confidence) or
    "claimed_all_true" (a bare true/false stand-in for 1.0/0.0); otherwise
    the default of 1.0 — an unhedged self-report implicitly claims
    everything in it is true."""
    if args.claimed_pass_rate is not None:
        return args.claimed_pass_rate
    if args.claims:
        claims = json.loads(Path(args.claims).read_text())
        rate = claims.get("claimed_pass_rate")
        if rate is not None:
            return float(rate)
        return 1.0 if claims.get("claimed_all_true", True) else 0.0
    return 1.0


def scan(claim_text: str, predictor: str, accessible_roots=None, ground_truth=None,
         source_text=None, claimed_pass_rate: float = 1.0) -> dict:
    """The whole pipeline: extract+verify via the unchanged core, then
    attach a predictor-tagged LI. Returns a dict combining
    claim_verification_check's own report with "predictor", "li", and
    "li_note" — never mutates or reinterprets that report's own fields."""
    results = verifier.run_claim_verification(
        claim_text, accessible_roots=accessible_roots,
        ground_truth=ground_truth, source_text=source_text,
    )
    report = verifier.build_report(results)
    li, li_note = compute_li(report, claimed_pass_rate)
    return {
        "tool": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "note": INTERPRETATION_NOTE,
        "predictor": predictor,
        "claimed_pass_rate": claimed_pass_rate,
        "li": li,
        "li_note": li_note,
        "verification": report,
    }


def format_report(result: dict) -> str:
    lines = [f"COPILOT-ACAT SCAN — predictor={result['predictor']}", "=" * 48]
    v = result["verification"]
    lines.append(f"outcome={v['outcome']}  claims={v['claim_count']}  "
                 f"PASS:{v['pass_count']} FAIL:{v['fail_count']} "
                 f"UNVERIFIABLE:{v['unverifiable_count']}")
    for c in v["claims"]:
        marker = {"PASS": "[PASS]", "FAIL": "[FAIL]", "UNVERIFIABLE": "[UNVR]"}[c["status"]]
        lines.append(f"{marker} {c['kind']:<22} {c['raw_text'][:80]}")
        if c.get("reason"):
            lines.append(f"        reason: {c['reason']}")
    lines.append("-" * 48)
    lines.append(f"claimed_pass_rate={result['claimed_pass_rate']}")
    if result["li"] is not None:
        lines.append(f"LI (Phase3/Phase1) = {result['li']:.3f}")
    else:
        lines.append(f"LI: UNVERIFIABLE ({result['li_note']})")
    if v["suggested_drift_codes_advisory_only"]:
        lines.append(f"Advisory drift codes (Zone 2 decides promotion, P21): "
                     f"{v['suggested_drift_codes_advisory_only']}")
    return "\n".join(lines)


def cmd_scan(args: argparse.Namespace) -> int:
    claim_text = Path(args.input).read_text(errors="ignore")
    ground_truth = json.loads(Path(args.ground_truth).read_text()) if args.ground_truth else None
    source_text = Path(args.source_text_file).read_text(errors="ignore") if args.source_text_file else None
    claimed_pass_rate = resolve_claimed_pass_rate(args)

    result = scan(claim_text, args.predictor, args.accessible_root or None,
                  ground_truth, source_text, claimed_pass_rate)

    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result))
    return 0 if result["verification"]["outcome"] != "fail" else 1


def run_smoke_test() -> bool:
    """Exercises the full pipeline against real ground truth in a temp
    directory — no mocking of claim_verification_check, since it is
    reused unchanged."""
    import tempfile
    ok = True

    with tempfile.TemporaryDirectory() as workdir:
        real_file = Path(workdir) / "artifact.json"
        real_file.write_text("{}")

        # A true claim, verified true, claimed_pass_rate defaults to 1.0 -> LI ~ 1.0.
        claim = f"Done. Created the report at {real_file}. All 5/5 tests pass."
        gt = {"passed": 5, "total": 5}
        result = scan(claim, "Copilot", accessible_roots=[workdir], ground_truth=gt)
        ok = ok and result["verification"]["outcome"] == "pass"
        ok = ok and result["verification"]["fail_count"] == 0
        ok = ok and result["li"] is not None and abs(result["li"] - 1.0) < 1e-9
        ok = ok and result["predictor"] == "Copilot"

        # A false claim (file doesn't exist) -> FAIL detected, LI < 1.0.
        false_claim = f"Done. Created the report at {workdir}/does_not_exist.json."
        result2 = scan(false_claim, "Copilot", accessible_roots=[workdir])
        ok = ok and result2["verification"]["outcome"] == "fail"
        ok = ok and result2["li"] is not None and result2["li"] < 1.0

        # UNVERIFIABLE-only claims (no ground truth given at all) never
        # silently count toward either PASS or FAIL, and LI is reported
        # undefined rather than fabricated.
        result3 = scan("Self-test passed.", "Copilot")
        ok = ok and result3["verification"]["pass_count"] == 0
        ok = ok and result3["verification"]["fail_count"] == 0
        ok = ok and result3["li"] is None
        ok = ok and result3["li_note"] == "no determinate (PASS/FAIL) claims to score"

        # claimed_pass_rate == 0 is reported undefined, not a ZeroDivisionError.
        result4 = scan(claim, "Copilot", accessible_roots=[workdir], ground_truth=gt,
                       claimed_pass_rate=0.0)
        ok = ok and result4["li"] is None and "claimed rate is 0" in result4["li_note"]

        # No claims found at all in the text.
        result5 = scan("Nothing checkable here.", "Copilot")
        ok = ok and result5["verification"]["claim_count"] == 0
        ok = ok and result5["li"] is None

        # CLI round trip, including a --claims file overriding the default rate.
        claims_path = Path(workdir) / "claims.json"
        claims_path.write_text(json.dumps({"claimed_pass_rate": 0.5}))
        input_path = Path(workdir) / "claim.txt"
        input_path.write_text(claim)
        gt_path = Path(workdir) / "gt.json"
        gt_path.write_text(json.dumps(gt))
        parser = build_parser()
        args = parser.parse_args([
            "scan", "--input", str(input_path), "--predictor", "Copilot",
            "--accessible-root", workdir, "--ground-truth", str(gt_path),
            "--claims", str(claims_path), "--json",
        ])
        ok = ok and cmd_scan(args) == 0
        ok = ok and resolve_claimed_pass_rate(args) == 0.5

        # A verified FAIL exits nonzero for CI use.
        false_input_path = Path(workdir) / "false_claim.txt"
        false_input_path.write_text(false_claim)
        args2 = parser.parse_args([
            "scan", "--input", str(false_input_path), "--predictor", "Copilot",
            "--accessible-root", workdir,
        ])
        ok = ok and cmd_scan(args2) == 1

    print("✓ Smoke test PASSED" if ok else "✗ Smoke test FAILED")
    return ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{TOOL_NAME} v{TOOL_VERSION}")
    parser.add_argument("--smoke-test", action="store_true")
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Verify a predictor's self-report claims against real evidence.")
    scan_p.add_argument("--input", required=True, help="claim text file (the Phase 1 self-report)")
    scan_p.add_argument("--predictor", required=True, help="who made the claims, e.g. Copilot, Claude")
    scan_p.add_argument("--accessible-root", action="append", default=[])
    scan_p.add_argument("--ground-truth", default=None)
    scan_p.add_argument("--source-text-file", default=None)
    scan_p.add_argument("--claimed-pass-rate", type=float, default=None,
                        help="Phase 1 confidence; defaults to 1.0 if neither this nor --claims is given")
    scan_p.add_argument("--claims", default=None,
                        help="JSON file with claimed_pass_rate or claimed_all_true; "
                             "overridden by --claimed-pass-rate if both given")
    scan_p.add_argument("--out", default=None)
    scan_p.add_argument("--json", action="store_true")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if args.command == "scan":
        return cmd_scan(args)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

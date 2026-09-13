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

WHY known_taxonomy IS EXPOSED HERE, NOT LEFT AT THE CORE'S DEFAULT
------------------------------------------------------------------------
claim_verification_check_v0_1.py's evaluate_citation() defaults to its
own KNOWN_TAXONOMY — five failure-mode terms specific to the Synthetic
APTs transcript that tool was originally built against. Leaving that
default in place here would mean every CITATION claim, in every repo,
gets scored against APT terminology that has nothing to do with most
repos' own citations — a valid term for THIS repo would be reported FAIL
for "not part of the documented taxonomy," which is not a generalization,
it is a silent narrowing. scan()/--taxonomy therefore pass a caller's own
taxonomy straight through to the unchanged core; omitting it preserves
the core's original default rather than replacing it with something
falsely repo-agnostic.

WHY FILE_CREATED RESULTS ARE RE-CHECKED HERE, NOT LEFT AT THE CORE'S OWN VERDICT
---------------------------------------------------------------------------------------
claim_verification_check_v0_1.py's evaluate_file_created() tests
containment with a lexical path.startswith(root) comparison. A sibling
directory sharing a root's own string as a prefix ("/tmp/repo-secrets"
against root "/tmp/repo"), or an unresolved ".." traversal, satisfies
that comparison despite the claimed path falling genuinely outside the
declared root. Fixing this in the core itself would violate this
module's own commitment to reuse it unchanged, so
_harden_file_created_boundary() independently re-resolves the claimed
path and every accessible root and downgrades any PASS that does not
actually resolve underneath one of them to FAIL — defense added in this
wrapper, not a patch to the shared file every other consumer of that
core also depends on.

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

HONEST LIMITS (raised by an adversarial review round on this PR, kept
here rather than silently fixed or silently ignored)
------------------------------------------------------------------------------
- claimed_pass_rate is one scalar for the whole claim text, not per-claim.
  A predictor that hedges unevenly ("90% sure about the file, 50% about
  the tests") cannot express that split; the default of 1.0 is the most
  honest choice available without inventing per-claim confidence parsing,
  but it is a real, documented limitation, not a solved problem — it
  biases LI toward <=1 for a genuinely well-calibrated predictor that
  simply didn't hedge into this tool's one aggregate number.
- extract_assertions() (claim_verification_check_v0_1.py, reused
  unchanged) is a TRL 2-3 regex heuristic. Systematic under-extraction
  understates both the numerator and denominator of LI identically, which
  UNVERIFIABLE-isolation does not protect against — it only protects
  against claims it DID extract being wrongly scored, not claims it never
  saw at all. See _extraction_density_note() for the one mitigation this
  module adds: flagging when a long input produced zero claims.
- _harden_file_created_boundary()'s real-path resolution closes the
  sibling-prefix and ".." cases this module's own tests cover, but not a
  symlink inside an accessible root that points outside it, a bind-mount
  or overlay filesystem where a resolved path can appear in-scope while
  its real content lives elsewhere, or cross-platform path normalization
  differences. Acceptable residual risk for a calibration signal; would
  need closing before this scanner could serve as an actual security
  boundary rather than a Phase-3 evidence check.
- Omitting --taxonomy silently preserves the core's own APT-specific
  default taxonomy (see "WHY known_taxonomy IS EXPOSED HERE" above) —
  exposing the override does not change what happens when a caller
  forgets to use it. A citation claim using a legitimate, repo-specific
  term will FAIL under the default taxonomy exactly as it would have
  before this parameter existed, unless --taxonomy is supplied.

Usage:
  python3 tools/copilot_acat_scanner_v1_0.py scan \\
      --input pr_body.txt --predictor Copilot \\
      --accessible-root /path/to/repo --ground-truth ci_results.json
  python3 tools/copilot_acat_scanner_v1_0.py scan --input pr_body.txt \\
      --predictor Copilot --claimed-pass-rate 0.9 --json
  python3 tools/copilot_acat_scanner_v1_0.py scan --input pr_body.txt \\
      --predictor Copilot --strict-li  # exit 3, not 0, if LI comes out undefined
  python3 tools/copilot_acat_scanner_v1_0.py --smoke-test
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

BOUNDARY_HARDENING_SCOPE = (
    "_harden_file_created_boundary() only re-checks file_created claims the "
    "core already marked PASS (a real path-resolution check downgrading a "
    "false PASS to FAIL). A claim the core's own lexical path.startswith(root) "
    "test marks UNVERIFIABLE or FAIL is left as-is: it is already refused and "
    "never counted as evidence, so there is nothing to harden — but a "
    "legitimate path that happens not to share a literal string prefix with "
    "any accessible_root (a symlink, an alternate mount point, differing "
    "normalization) can be under-reported as UNVERIFIABLE rather than PASS. "
    "That is a conservative false negative, never a false PASS: this report's "
    "pass_count can be lower than a fully path-aware evaluator would produce, "
    "never higher."
)


def _is_valid_rate(value: object) -> bool:
    """A real number in [0,1] — bool is deliberately excluded even though
    it is technically an int subclass in Python (True/False would
    otherwise silently pass as 1.0/0.0). Same contract as
    tools/nf_ledger_v0_1.py's own check_p() for a stated probability."""
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and 0.0 <= value <= 1.0)


def compute_li(report: dict, claimed_pass_rate: float = 1.0) -> Tuple[Optional[float], Optional[str]]:
    """report is claim_verification_check_v0_1.build_report()'s own output,
    unmodified. LI is undefined (None, with a reason) when claimed_pass_rate
    is not a real rate at all (negative, >1, NaN/inf, or a bool), when
    there is nothing determinate to score, or when the claimed rate is 0
    (nothing to divide by that would produce a meaningful ratio rather
    than an artifact of the denominator)."""
    if not _is_valid_rate(claimed_pass_rate):
        return None, f"claimed_pass_rate must be a real number in [0,1], got {claimed_pass_rate!r}"
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


def _harden_file_created_boundary(results: List, accessible_roots: Optional[List[str]]) -> Tuple[List, int]:
    """claim_verification_check_v0_1.evaluate_file_created() checks
    containment with a lexical str.startswith(root) test (see its own
    source), which a same-prefix sibling directory ("/tmp/repo-secrets"
    against root "/tmp/repo") or a "../" traversal can pass despite the
    claimed path actually falling outside the declared root. That
    function is the shared verification core and is not modified here
    (see module docstring) — instead, any claim it already marked PASS is
    independently re-checked with real path resolution before this
    module trusts it as evidence; anything that does not actually resolve
    under a declared root is downgraded to FAIL rather than accepted.
    Only ever narrows a PASS to a FAIL — never the reverse, and never
    touches any other kind or status. Returns (results, downgrade_count)
    so a caller can tell, without inspecting every claim, whether this
    hardening pass actually changed anything — see BOUNDARY_HARDENING_SCOPE
    for what this pass does and does not cover (only PASS is re-checked;
    an UNVERIFIABLE/FAIL from the core's own lexical test is untouched)."""
    if not accessible_roots:
        return results, 0
    resolved_roots = [Path(root).resolve() for root in accessible_roots]
    hardened = []
    downgrade_count = 0
    for r in results:
        if r.kind == "file_created" and r.status == verifier.PASS:
            claimed_path = Path(r.evidence.get("path", "")).resolve()
            truly_in_scope = any(
                claimed_path == root or root in claimed_path.parents
                for root in resolved_roots
            )
            if not truly_in_scope:
                r = dataclasses.replace(
                    r, status=verifier.FAIL,
                    reason="Claimed path does not actually resolve under any declared "
                           "accessible root once symlinks/'..' are resolved (the shared "
                           "verification core's own containment check is lexical, not "
                           "path-aware) — refused rather than trusted as evidence.",
                    suggested_drift_code="D-01",
                )
                downgrade_count += 1
        hardened.append(r)
    return hardened, downgrade_count


LOW_CLAIM_DENSITY_THRESHOLD_CHARS = 200


def _extraction_density_note(claim_text: str, claim_count: int) -> Optional[str]:
    """A long input that yields zero extracted claims is not verified
    evidence the text made no claims — extract_assertions() is a TRL 2-3
    regex heuristic (claim_verification_check_v0_1.py's own docstring)
    that can miss unusually phrased claims. Surfacing this only when it is
    actually plausible (a real amount of text, genuinely zero claims)
    keeps it from firing on the common, unremarkable case of a short,
    genuinely claim-free input."""
    if claim_count == 0 and len(claim_text.strip()) >= LOW_CLAIM_DENSITY_THRESHOLD_CHARS:
        return (
            f"No checkable claims were extracted from a {len(claim_text.strip())}-char "
            "input. The shared extractor is a TRL 2-3 regex heuristic and can miss "
            "claims phrased unusually — this is not verified evidence the text made "
            "no claims at all."
        )
    return None


def scan(claim_text: str, predictor: str, accessible_roots=None, ground_truth=None,
         source_text=None, claimed_pass_rate: float = 1.0,
         known_taxonomy: Optional[Dict[str, List[str]]] = None) -> dict:
    """The whole pipeline: extract+verify via the unchanged core, then
    harden the core's own path-containment gap (see
    _harden_file_created_boundary) and attach a predictor-tagged LI.
    known_taxonomy is passed straight through to the core's own
    evaluate_citation() — omitting it would silently restrict every
    CITATION claim, in any repo, to the core's built-in APT taxonomy,
    which is specific to that module's own origin, not a general-purpose
    default. Returns a dict combining claim_verification_check's own
    report with "predictor", "li", "li_note",
    "boundary_hardening_downgrade_count" (how many file_created PASSes
    _harden_file_created_boundary actually downgraded — 0 does not mean
    nothing was checked, it means nothing needed downgrading), and
    "extraction_density_note" (see _extraction_density_note) — never
    mutates or reinterprets that report's own fields beyond the boundary
    hardening itself."""
    results = verifier.run_claim_verification(
        claim_text, accessible_roots=accessible_roots,
        ground_truth=ground_truth, source_text=source_text,
        known_taxonomy=known_taxonomy,
    )
    results, downgrade_count = _harden_file_created_boundary(results, accessible_roots)
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
        "boundary_hardening_downgrade_count": downgrade_count,
        "boundary_hardening_note": BOUNDARY_HARDENING_SCOPE,
        "extraction_density_note": _extraction_density_note(claim_text, report["claim_count"]),
        "verification": report,
    }


def format_report(result: dict) -> str:
    lines = [f"ACAT CLAIM SCAN — predictor={result['predictor']}", "=" * 48]
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
    if result["boundary_hardening_downgrade_count"]:
        lines.append(f"boundary hardening downgraded {result['boundary_hardening_downgrade_count']} "
                     f"file_created PASS result(s) to FAIL — see boundary_hardening_note in --json output")
    if result["extraction_density_note"]:
        lines.append(f"note: {result['extraction_density_note']}")
    return "\n".join(lines)


def cmd_scan(args: argparse.Namespace) -> int:
    claim_text = Path(args.input).read_text(errors="ignore")
    ground_truth = json.loads(Path(args.ground_truth).read_text()) if args.ground_truth else None
    source_text = Path(args.source_text_file).read_text(errors="ignore") if args.source_text_file else None
    known_taxonomy = json.loads(Path(args.taxonomy).read_text()) if args.taxonomy else None
    claimed_pass_rate = resolve_claimed_pass_rate(args)

    result = scan(claim_text, args.predictor, args.accessible_root or None,
                  ground_truth, source_text, claimed_pass_rate, known_taxonomy)

    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result))

    if result["verification"]["outcome"] == "fail":
        return 1
    if args.strict_li and result["li"] is None:
        return 3
    return 0


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

        # An out-of-range/non-finite/boolean claimed_pass_rate is refused
        # rather than producing a nonsensical or non-finite LI.
        for bad_rate in (-1.0, 5.0, float("nan"), True):
            li, note = compute_li({"pass_count": 1, "fail_count": 0, "unverifiable_count": 0},
                                  claimed_pass_rate=bad_rate)
            ok = ok and li is None and "must be a real number in [0,1]" in note

        # A sibling directory sharing the root's own string prefix is not
        # actually in scope, even though the shared core's own lexical
        # check would accept it.
        sibling = Path(workdir).parent / (Path(workdir).name + "-sibling")
        sibling.mkdir(exist_ok=True)
        leaked = sibling / "leaked.json"
        leaked.write_text("{}")
        sibling_claim = f"Done. Created the report at {leaked}."
        result6 = scan(sibling_claim, "Copilot", accessible_roots=[workdir])
        ok = ok and result6["verification"]["outcome"] == "fail"

        # known_taxonomy is passed straight through to the core rather
        # than silently defaulting to its own APT-specific taxonomy.
        custom_taxonomy = {"CUSTOM_TERM": ["custom keyword"]}
        taxonomy_claim = "Documented in Appendix B.6: CUSTOM_TERM is the relevant failure mode."
        taxonomy_source = "This mentions a custom keyword."
        result7 = scan(taxonomy_claim, "Copilot", source_text=taxonomy_source,
                       known_taxonomy=custom_taxonomy)
        citation7 = next(c for c in result7["verification"]["claims"] if c["kind"] == "citation")
        ok = ok and citation7["status"] == "PASS"

        # The text report label is predictor-neutral, unlike the raw
        # verification claim text, which may legitimately mention Copilot.
        claude_result = scan("Nothing checkable here.", "Claude")
        ok = ok and "COPILOT" not in format_report(claude_result).upper()
        ok = ok and result5["li"] is None

        # boundary_hardening_downgrade_count is 0 (not absent) when nothing
        # needed downgrading, and reflects the real count when it did.
        ok = ok and result["boundary_hardening_downgrade_count"] == 0
        ok = ok and result6["boundary_hardening_downgrade_count"] == 1

        # A long zero-claim input is flagged as possible under-extraction;
        # a short one is not (it would be noise on the common case).
        long_empty = "This is a long narrative paragraph. " * 10
        result8 = scan(long_empty, "Copilot")
        ok = ok and result8["verification"]["claim_count"] == 0
        ok = ok and result8["extraction_density_note"] is not None
        result9 = scan("ok", "Copilot")
        ok = ok and result9["extraction_density_note"] is None

        # --strict-li exits 3 on an undefined LI but never overrides a real
        # FAIL, and has no effect when LI is defined.
        strict_input = Path(workdir) / "strict_undefined.txt"
        strict_input.write_text("Self-test passed.")
        parser_s = build_parser()
        args_strict = parser_s.parse_args([
            "scan", "--input", str(strict_input), "--predictor", "Copilot", "--strict-li",
        ])
        ok = ok and cmd_scan(args_strict) == 3
        args_not_strict = parser_s.parse_args([
            "scan", "--input", str(strict_input), "--predictor", "Copilot",
        ])
        ok = ok and cmd_scan(args_not_strict) == 0

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
    scan_p.add_argument("--taxonomy", default=None,
                        help="JSON file mapping CITATION terms to keyword lists; passed straight "
                             "through to the verification core in place of its own built-in "
                             "APT-specific taxonomy, so CITATION claims can be scored for any repo")
    scan_p.add_argument("--claimed-pass-rate", type=float, default=None,
                        help="Phase 1 confidence; defaults to 1.0 if neither this nor --claims is given")
    scan_p.add_argument("--claims", default=None,
                        help="JSON file with claimed_pass_rate or claimed_all_true; "
                             "overridden by --claimed-pass-rate if both given")
    scan_p.add_argument("--out", default=None)
    scan_p.add_argument("--json", action="store_true")
    scan_p.add_argument("--strict-li", action="store_true",
                        help="Exit 3 (instead of 0) when LI is undefined (no determinate PASS/FAIL "
                             "claims — e.g. everything UNVERIFIABLE, or no claims extracted at all). "
                             "Without this flag, exit codes are: 1 = a claim verified FAIL, "
                             "0 = otherwise, INCLUDING an undefined LI — a green exit does not by "
                             "itself mean LI was computed. Use this flag if wiring this scanner into "
                             "a gate that must not silently pass on an undefined calibration result.")

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

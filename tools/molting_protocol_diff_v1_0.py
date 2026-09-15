#!/usr/bin/env python3
"""
Molting Protocol Diff — v1.1
Builder v1.7 compliant · audit_tool
HumanAIOS · S-060126-01

Classify a molt's TIER from the set of filepaths its diff touches.

Molt tier used to be decided by opinion: an author wrote "this is Tier 1
because…" and the claim entered the record as prose. This tool replaces that
discretion with a published, path-based rule. The classifier is the signal;
the author's `molt_tier_claimed` is a hypothesis; the gap between them is
audit data, not a merge blocker.

  Tier 0 — touches no constants and no gates. Not a molt; consumes no slot.
  Tier 1 — touches at least one CONSTANTS path. Needs molt_id, prediction,
           measurement window.
  Tier 2 — touches at least one GATE path (workflows, ratification/validation
           scripts, the system graph, CODEOWNERS). Needs a registry entry and
           an ADV run before KEEP.

The tier is the MAXIMUM over every path in the diff: one gate file makes the
whole change Tier 2 regardless of what else it touches.

Usage:
  python molting_protocol_diff_v1_0.py --input <path_or_json>
  python molting_protocol_diff_v1_0.py --files a.py b.json [--claimed 1]
  python molting_protocol_diff_v1_0.py --smoke-test
  python molting_protocol_diff_v1_0.py --help
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "molting_protocol_diff"
TOOL_VERSION  = "1.1.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION  = "S-060126-01"
TOOL_ZONE     = 1   # 1=execute, 2=ratify, 3=night


class SpecLoadFailed(Exception):
    """Raised when input cannot be loaded or parsed."""
    pass


# ── The published tier rule ───────────────────────────────────────────────────
#
# These two sets ARE the rule. They are deliberately data, not logic, so that
# the question "why is my PR Tier 2?" is answered by reading a list rather than
# by reading an argument.
#
# This file lists ITSELF in GATE_PATHS. Without that entry a PR touching only
# this module could rewrite the tier rule — delete an entry, invert the max —
# while measuring Tier 0 and drawing no attention at all. A rule that cannot
# see its own edits is not a control.
#
# MATCHING RULE (segment-aware containment, not raw substring):
#   * An entry ending in "/" is a DIRECTORY prefix. It matches when it appears
#     as a whole path-segment sequence. "caps/" matches "caps/limits.json" but
#     NOT "handicaps/limits.json" — a raw `in` test would match both.
#   * An entry not ending in "/" is a FILE path. It matches when the path ends
#     with it on a segment boundary. "behavior_spec.json" matches
#     "behavior_spec.json" and "acat/behavior_spec.json", but not
#     "my_behavior_spec.json".
#
# Entries marked REPO are additions to the originating handoff spec, made
# because the spec's path did not exist in this repository and would therefore
# have produced a silent false negative on a live gate. Each is listed with the
# spec path it corrects. The spec paths are retained so the rule stays portable
# to sibling repos that do use them.

CONSTANTS_PATHS = (
    "RESOURCE_UNITS.yaml",
    "behavior_spec.json",
    "integrity_modes.json",
    "rubrics/",
    "weights/",
    "caps/",
    "half-lives.yaml",
    # REPO: this repository keeps its ratified constants in these three files.
    # Omitting them would let a constant change measure Tier 0.
    "constants.json",
    "constants_config.json",
    "constitution.json",
)

GATE_PATHS = (
    ".github/workflows/",
    "tools/validate.py",
    "tools/ratify.py",
    "system_graph.json",
    "system_graph.md",
    ".github/CODEOWNERS",
    "ci_gates.py",
    "z2_ratification_gate.yml",
    # REPO: the ratification and validation gates live under .z1-control/ here,
    # not tools/. The spec's tools/validate.py and tools/ratify.py do not exist
    # in this repository, so without these two entries every change to the Z2
    # signing path would have measured Tier 0.
    ".z1-control/ratify.py",
    ".z1-control/validate.py",
    ".z1-control/render.py",
    # The rule must be able to see edits to itself — see the note above.
    "tools/molting_protocol_diff_v1_0.py",
)

TIER_NAMES = {
    0: "Tier 0 — no constants, no gates (not a molt)",
    1: "Tier 1 — constants touched (needs molt_id + prediction + window)",
    2: "Tier 2 — gates touched (needs registry entry + ADV run before KEEP)",
}


# ── Tier Classification ───────────────────────────────────────────────────────

def normalize_path(filepath: str) -> str:
    """
    Reduce a diff path to the canonical form the rule is written against.

    Handles the shapes that actually arrive from callers: Windows separators,
    a leading "./" from `git diff --name-only`, surrounding whitespace, and the
    trailing empty string produced by splitting CI output on newlines.
    """
    p = str(filepath or "").strip().replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.lstrip("/")


def _as_path_list(diff_filepaths) -> list:
    """
    Coerce whatever a caller passed into a list of candidate paths.

    A bare string is one path. Anything that is not iterable — an int, an
    object — yields nothing rather than raising: `classify_molt_tier` documents
    itself as total, and a classifier that can be made to throw is a classifier
    that can be made to skip a gate.
    """
    if diff_filepaths is None:
        return []
    if isinstance(diff_filepaths, str):
        return [diff_filepaths]
    if isinstance(diff_filepaths, (bytes, bytearray)):
        return [diff_filepaths.decode("utf-8", "replace")]
    try:
        return list(diff_filepaths)
    except TypeError:
        return []


def _matches(path: str, entry: str) -> bool:
    """Segment-aware containment — see MATCHING RULE above."""
    if not path or not entry:
        return False
    anchored = "/" + path
    if entry.endswith("/"):
        return ("/" + entry) in anchored
    return anchored.endswith("/" + entry)


def classify_molt_tier(diff_filepaths) -> int:
    """
    Classify molt tier from the files a diff touches.

    Returns 0, 1, or 2 — the maximum tier implied by any single path. An empty
    or unparseable path list is Tier 0: a diff that touches nothing is not a
    molt.

    This function is pure and total. It never raises on odd input (None
    entries, blank lines, absolute paths); anything it cannot read is simply
    not a match. A classifier that can throw is a classifier that can be made
    to skip a gate.
    """
    tier = 0
    for raw in _as_path_list(diff_filepaths):
        path = normalize_path(raw)
        if not path:
            continue
        if any(_matches(path, entry) for entry in CONSTANTS_PATHS):
            tier = max(tier, 1)
        if any(_matches(path, entry) for entry in GATE_PATHS):
            tier = max(tier, 2)
    return tier


def tier_evidence(diff_filepaths) -> list:
    """
    Return the per-path reasons behind the verdict, so a disputed tier is
    settled by pointing at a row rather than by re-arguing the rule.

    Each row: {"path", "tier", "matched"} where `matched` names the rule
    entries that fired. Paths that matched nothing are omitted.
    """
    rows = []
    for raw in _as_path_list(diff_filepaths):
        path = normalize_path(raw)
        if not path:
            continue
        matched = [e for e in CONSTANTS_PATHS if _matches(path, e)]
        gates   = [e for e in GATE_PATHS if _matches(path, e)]
        if not matched and not gates:
            continue
        rows.append({
            "path":    path,
            "tier":    2 if gates else 1,
            "matched": sorted(set(matched + gates)),
        })
    return rows


def parse_claimed_tier(pr_body: str):
    """
    Pull `molt_tier_claimed: N` out of a PR body.

    Returns an int 0-2, or None when the field is absent, unfilled (the
    template ships the literal placeholder `[0 | 1 | 2]`), or out of range.
    None means "no hypothesis was offered" — which is itself the audit signal,
    distinct from a wrong hypothesis.
    """
    import re
    if not pr_body:
        return None
    # Tolerate the markdown the field is actually written in: `**molt_tier_claimed:** \`1\``,
    # `molt_tier_claimed: 1`, `molt_tier_claimed: [1]`.
    #
    # The digits are captured WHOLE (\d+), not as a single [0-2]. Capturing one
    # digit would read "molt_tier_claimed: 10" as a claim of Tier 1 and then
    # score a gap against it — inventing a hypothesis the author never made.
    m = re.search(r"molt_tier_claimed:[\s*`\[]*(\d+)", str(pr_body))
    if not m:
        return None
    # The unfilled placeholder "[0 | 1 | 2]" would otherwise read as a claim of 0.
    tail = pr_body[m.start():m.start() + 40]
    if "|" in tail.split("\n")[0]:
        return None
    value = int(m.group(1))
    return value if value in (0, 1, 2) else None


def molt_tier_gap_record(pr_number, claimed, measured, evidence=None) -> dict:
    """
    Build the audit row for the SMAG self-accuracy ledger.

    Under-claiming is the risk worth measuring: it is how a gate change slips
    through wearing a Tier-0 label. Over-claiming costs nothing but caution, so
    it is recorded as informational.
    """
    if claimed is None:
        gap, impact, verdict = None, "HIGH", "MISSING"
    elif claimed < measured:
        gap, impact, verdict = measured - claimed, "HIGH", "UNDER_CLAIM"
    elif claimed > measured:
        gap, impact, verdict = measured - claimed, "LOW", "OVER_CLAIM"
    else:
        gap, impact, verdict = 0, "NONE", "MATCH"
    return {
        "pr_number":          pr_number,
        "molt_tier_claimed":  claimed,
        "molt_tier_measured": measured,
        "gap":                gap,
        "verdict":            verdict,
        "accuracy_impact":    impact,
        "classifier_version": TOOL_VERSION,
        "timestamp":          datetime.now(timezone.utc).isoformat(),
        "evidence":           evidence or [],
    }


# ── Input Loading ─────────────────────────────────────────────────────────────

def load_input(source: str) -> dict:
    """
    Load input from a file path or raw JSON string.
    Raises SpecLoadFailed if input cannot be parsed.

    AGENT INSTRUCTION: Replace or extend this with your actual
    input format. Keep SpecLoadFailed for unreadable input — the
    validation suite catches it cleanly.
    """
    # Try as file path first
    p = Path(source)
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise SpecLoadFailed(f"Cannot load {p}: {e}")
    # Try as inline JSON
    try:
        return json.loads(source)
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"Input is neither a valid path nor valid JSON: {e}")


# ── Core Logic ────────────────────────────────────────────────────────────────

def run(data: dict) -> dict:
    """
    Classify one diff and compare the measurement against the author's claim.

    Input dict:
      {
        "filepaths":          ["a.py", ...],   # required (alias: "files")
        "molt_tier_claimed":  0 | 1 | 2,       # optional
        "pr_body":            "...",           # optional; claim parsed from it
        "pr_number":          123,             # optional
      }

    Status is advisory by design and never FAIL on a tier gap: this tool
    measures, it does not block. FAIL is reserved for input it cannot read,
    because a classifier that silently reports Tier 0 on unreadable input is
    worse than one that refuses.
    """
    if not isinstance(data, dict):
        raise SpecLoadFailed(f"expected a JSON object, got {type(data).__name__}")

    files = data.get("filepaths", data.get("files"))
    if files is None:
        raise SpecLoadFailed("input has no 'filepaths' (or 'files') key")
    if isinstance(files, str):
        files = [ln for ln in files.splitlines()]
    if not isinstance(files, (list, tuple)):
        raise SpecLoadFailed(f"'filepaths' must be a list, got {type(files).__name__}")

    warnings = []
    claimed = data.get("molt_tier_claimed")
    if claimed is None and data.get("pr_body"):
        claimed = parse_claimed_tier(data.get("pr_body"))
    if claimed is not None:
        try:
            claimed = int(claimed)
        except (TypeError, ValueError):
            warnings.append(f"molt_tier_claimed {claimed!r} is not an integer; treated as absent")
            claimed = None
        else:
            if claimed not in (0, 1, 2):
                warnings.append(f"molt_tier_claimed {claimed} is out of range 0-2; treated as absent")
                claimed = None

    measured = classify_molt_tier(files)
    evidence = tier_evidence(files)
    record   = molt_tier_gap_record(data.get("pr_number"), claimed, measured, evidence)

    if record["verdict"] == "MISSING":
        warnings.append("PR body carries no usable `molt_tier_claimed: [0|1|2]` — "
                        "the claim is VOID; measured tier still stands")
    elif record["verdict"] == "UNDER_CLAIM":
        warnings.append(f"under-claim: claimed Tier {claimed}, diff measures Tier {measured}")

    items = [{"key": row["path"], "status": f"T{row['tier']}", **row} for row in evidence]

    return {
        "status":   "WARN" if warnings else "PASS",
        "items":    items,
        "warnings": warnings,
        "tier":     measured,
        "gap":      record,
        "summary":  {
            "files_scanned":      len([f for f in files if normalize_path(f)]),
            "files_matched":      len(evidence),
            "molt_tier_measured": measured,
            "molt_tier_claimed":  "(none)" if claimed is None else claimed,
            "verdict":            record["verdict"],
            "warnings":           len(warnings),
        },
    }


# ── Output Assembly ───────────────────────────────────────────────────────────

def aggregate(run_result: dict, source: str) -> dict:
    """Assemble final output dict with standard Builder v1.7 envelope."""
    return {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "zone":      TOOL_ZONE,
        "session":   TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source":    source,
        "result":    run_result.get("status", "FAIL"),
        **run_result,
    }


def write_report(output: dict, output_dir: str) -> str:
    """Write JSON report to output_dir. Returns file path."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    """Print human-readable summary to stdout."""
    bar = "=" * 60
    verdict = output.get("result", "UNKNOWN")
    color = "" # no ANSI — keep output clean for pipe/grep
    print(f"\n{bar}")
    print(f" {TOOL_NAME} v{TOOL_VERSION}")
    print(f" Verdict : {verdict}")
    summary = output.get("summary", {})
    for k, v in summary.items():
        print(f" {k:<12}: {v}")
    warnings = output.get("warnings", [])
    if warnings:
        print(f"\n Warnings:")
        for w in warnings:
            print(f"   WARN  {w}")
    items = output.get("items", [])
    if items:
        print(f"\n Items ({len(items)}):")
        for item in items[:20]:   # cap at 20 for readability
            status = item.get("status","?")
            key    = item.get("key", item.get("id", "?"))
            print(f"   {status:<6} {key}")
        if len(items) > 20:
            print(f"   ... and {len(items)-20} more")
    print(f"{bar}\n")


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    """
    Minimal self-test. Must pass before Builder v1.7 compliance is claimed.
    Covers one path per tier, the max rule, and the false-positive guard.
    """
    try:
        # Positive: valid input produces PASS or WARN
        sample = {"filepaths": ["README.md"], "molt_tier_claimed": 0}
        result = run(sample)
        assert "status" in result, "run() must return a dict with 'status'"
        assert result["status"] in ("PASS","WARN","FAIL"), f"Unexpected status: {result['status']}"

        # One assertion per tier
        assert classify_molt_tier(["README.md"]) == 0, "docs-only must be Tier 0"
        assert classify_molt_tier(["behavior_spec.json"]) == 1, "constants must be Tier 1"
        assert classify_molt_tier([".github/workflows/x.yml"]) == 2, "workflows must be Tier 2"

        # Max rule: a gate anywhere in the diff wins
        assert classify_molt_tier(["behavior_spec.json", ".z1-control/ratify.py"]) == 2, \
            "tier must be the max over all paths"

        # Segment-aware matching, not raw substring
        assert classify_molt_tier(["docs/handicaps/notes.md"]) == 0, \
            "'caps/' must not match 'handicaps/'"

        # The rule must be able to see edits to itself
        assert classify_molt_tier(["tools/molting_protocol_diff_v1_0.py"]) == 2, \
            "changing the rule must itself measure Tier 2"

        # Totality: odd input must not raise, including a non-iterable scalar
        assert classify_molt_tier([None, "", "   ", "./README.md"]) == 0
        assert classify_molt_tier(42) == 0

        # A multi-digit claim is not truncated to its first digit
        assert parse_claimed_tier("molt_tier_claimed: 10") is None

        # Envelope test
        output = aggregate(result, "_smoke")
        assert output["tool"]    == TOOL_NAME
        assert output["version"] == TOOL_VERSION
        assert "timestamp" in output

        # Negative: bad input raises SpecLoadFailed
        try:
            load_input("/nonexistent/path/that/cannot/exist.json")
            assert False, "Should have raised SpecLoadFailed"
        except SpecLoadFailed:
            pass   # expected

        # Negative: an input dict with no file list is refused, not read as Tier 0
        try:
            run({"_nothing": True})
            assert False, "Should have raised SpecLoadFailed"
        except SpecLoadFailed:
            pass   # expected

        print("✓ Smoke test PASSED")
        return True

    except AssertionError as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ Smoke test ERROR: {e}")
        return False


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Molting Protocol Diff — molt tier classifier v{TOOL_VERSION}"
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to input file or inline JSON string"
    )
    parser.add_argument(
        "--files", "-f", nargs="*", default=None,
        help="Diff filepaths to classify (alternative to --input). "
             "With no values, reads one path per line from stdin."
    )
    parser.add_argument(
        "--claimed", type=int, choices=(0, 1, 2), default=None,
        help="The author's molt_tier_claimed, for gap measurement"
    )
    parser.add_argument(
        "--pr", type=int, default=None,
        help="PR number to stamp on the gap record"
    )
    parser.add_argument(
        "--tier-only", action="store_true",
        help="Print just the measured tier (0/1/2) and exit 0. For CI."
    )
    parser.add_argument(
        "--output", "-o",
        default="outputs/",
        help="Directory for JSON report output (default: outputs/)"
    )
    parser.add_argument(
        "--no-report", action="store_true",
        help="Skip writing the JSON report file"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test and exit"
    )
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.files is not None:
        files = args.files or [ln.strip() for ln in sys.stdin.read().splitlines()]
        data = {"filepaths": files}
        source = "--files"
    elif args.input:
        try:
            data = load_input(args.input)
        except SpecLoadFailed as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
        source = args.input
    else:
        parser.print_help()
        sys.exit(1)

    # `--input '[]'` loads valid JSON that is not an object. Applying the CLI
    # overrides to it would raise TypeError from argument parsing rather than
    # reporting SPEC_LOAD_FAILED, so the shape is checked before they are set.
    if not isinstance(data, dict):
        print(f"SPEC_LOAD_FAILED: expected a JSON object, got {type(data).__name__}",
              file=sys.stderr)
        sys.exit(2)

    if args.claimed is not None:
        data["molt_tier_claimed"] = args.claimed
    if args.pr is not None:
        data["pr_number"] = args.pr

    try:
        run_result = run(data)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    if args.tier_only:
        print(run_result["tier"])
        sys.exit(0)

    output = aggregate(run_result, source)
    print_summary(output)
    if not args.no_report:
        print(f"Report: {write_report(output, args.output)}")
    # Advisory by design: a tier gap is data, not a merge blocker. Only input
    # this tool could not read exits non-zero, and that already happened above.
    sys.exit(0)


if __name__ == "__main__":
    main()

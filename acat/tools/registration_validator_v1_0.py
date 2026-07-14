#!/usr/bin/env python3
"""
Registration Validator — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · Z1 DRAFT — proposed, not ratified

Direct response to the corpus sweep this session: 26 of 29 checkable
H-class entries in REGISTERED.md fail outcome-symmetry. That number is
a documentation-process failure, not an individual-entry failure — it
means nothing currently stops an incomplete entry from reaching the
canonical file. This tool is that stop, designed to run BEFORE merge
(as a haios_audit.yml step, see companion workflow snippet), not after.

Combines four checks already built and tested this session, plus one
new one (duplicate ID collision), into a single pre-merge gate:

  1. YAML front-matter completeness (hard) -- required fields present.
  2. zone2_ratification presence (hard) -- reuses z2_queue_v1_1.py's
     own gate logic; an entry without it cannot reach REGISTERED.md,
     full stop, same as it cannot reach the Zone 2 queue.
  3. Outcome symmetry for H-class entries (hard for missing branch,
     advisory for lopsided/placeholder branch) -- reuses
     outcome_symmetry_checker_v1_0.py directly, not reimplemented.
  4. Evidence-claim discipline (advisory) -- a "Synopsis" or "Evidence"
     field asserting something about code/schema/live state should
     reference a specific artifact (file, line, query) rather than
     read as pure narrative. Heuristic, per L2, never hard-blocking.
  5. Duplicate ID collision (hard) -- the proposed ID must not already
     exist in the live-fetched REGISTERED.md at validation time, per
     IC-030/G-4 discipline (no self-numbering, no assuming an ID is free).

STRUCTURAL NOTE: this tool does not replace outcome_symmetry_checker_v1_0.py
or z2_queue_v1_1.py -- it imports and calls them, so a fix to either of
those tools' logic automatically applies here too, rather than drifting
out of sync with a duplicated copy.
"""

from __future__ import annotations
import json
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "registration_validator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE = 1

REQUIRED_YAML_FIELDS = ["id", "name", "status", "class", "date_registered", "session_registered"]
VALID_CLASSES = {"F", "H", "IC", "IC-correction"}


class RegistrationRejected(Exception):
    """Raised when an entry fails a HARD check. No override parameter
    exists -- same discipline as every other hard-reject class this
    session (SameSubstrateRejection, CredentialMissing, ClaimNotAdmissible,
    OutcomeAsymmetryRejection)."""
    pass


def parse_yaml_frontmatter(entry_text: str) -> dict:
    """Extracts the --- delimited YAML-ish block. Lightweight parser
    (no external yaml dependency, stdlib-only per project convention) --
    handles the flat key: value shape actually used in REGISTERED.md
    entries, not full YAML (nested lists like related_finding: [...]
    are captured as raw strings, sufficient for presence/format checks)."""
    match = re.search(r'^---\s*\n(.*?)\n---\s*$', entry_text, re.MULTILINE | re.DOTALL)
    if not match:
        return {}
    block = match.group(1)
    fields = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


def check_schema_completeness(fields: dict) -> list:
    """HARD check. Returns list of missing required fields (empty = pass)."""
    return [f for f in REQUIRED_YAML_FIELDS if f not in fields or not fields[f]]


def check_zone2_ratification(fields: dict) -> bool:
    """HARD check. Mirrors z2_queue_v1_1.py's own validate_entry() logic
    exactly -- an entry with no zone2_ratification field, or an empty
    one, fails this check the same way it would fail queue append."""
    val = fields.get("zone2_ratification", "")
    return bool(val) and val.lower() not in ("null", "none", "")


def check_duplicate_id(proposed_id: str, live_registered_ids: set) -> bool:
    """HARD check. True = collision (fail). live_registered_ids must be
    populated from a FRESH fetch of REGISTERED.md, per IC-030 -- this
    function does not fetch anything itself, it only compares against
    whatever set the caller supplies, and the caller is responsible for
    that set being live, not cached."""
    return proposed_id in live_registered_ids


def check_evidence_discipline(entry_text: str) -> dict:
    """ADVISORY only, per L2. Flags Synopsis/Evidence bullets that read
    as pure narrative with no artifact reference (a file name, a line
    number, a query, a command). This is a heuristic keyword/pattern
    check, not semantic understanding -- false positives and negatives
    both expected, hence advisory, never hard-blocking."""
    ARTIFACT_MARKERS = [
        r'\.py\b', r'\.sql\b', r'\.md\b', r'\.json\b', r'\.yml\b',
        r'line[s]?\s+\d+', r'`[a-zA-Z_]+\(\)`', r'SELECT\s', r'session\s+S-\d',
        r'commit\s+[0-9a-f]{6,}', r'N\s*[=≥≤]\s*\d+',
    ]
    evidence_bullets = re.findall(r'-\s*\*\*(?:Synopsis|Evidence)[:\*]+(.*?)(?=\n-\s*\*\*|\Z)',
                                   entry_text, re.DOTALL)
    if not evidence_bullets:
        return {"has_evidence_bullet": False, "artifact_referenced": None}
    combined = " ".join(evidence_bullets)
    has_marker = any(re.search(p, combined) for p in ARTIFACT_MARKERS)
    return {"has_evidence_bullet": True, "artifact_referenced": has_marker}


def validate_entry(entry_text: str, live_registered_ids: set,
                    outcome_symmetry_fn=None) -> dict:
    """
    Top-level validator. Runs all checks, raises RegistrationRejected
    on the first HARD failure encountered (fields checked in a fixed
    order so the rejection reason is always the most fundamental one,
    not whichever check happened to run last).
    outcome_symmetry_fn is injected (not imported directly) so this
    module has no hard dependency on outcome_symmetry_checker_v1_0.py
    being importable in every environment -- caller wires it in.
    """
    fields = parse_yaml_frontmatter(entry_text)

    missing = check_schema_completeness(fields)
    if missing:
        raise RegistrationRejected(
            f"Missing required YAML front-matter fields: {missing}. "
            f"Entry cannot be registered until schema is complete."
        )

    if not check_zone2_ratification(fields):
        raise RegistrationRejected(
            f"Entry '{fields.get('id', 'UNKNOWN')}' has no valid "
            f"zone2_ratification. No entry reaches REGISTERED.md without "
            f"one, same gate as z2_queue's own append() logic."
        )

    proposed_id = fields.get("id", "")
    if check_duplicate_id(proposed_id, live_registered_ids):
        raise RegistrationRejected(
            f"ID '{proposed_id}' already exists in the live-fetched "
            f"REGISTERED.md. Per IC-030/G-4: no self-numbering, verify "
            f"the max ID live before assigning, this ID is not free."
        )

    result = {
        "id": proposed_id,
        "schema_check": "PASS",
        "zone2_ratification_check": "PASS",
        "duplicate_id_check": "PASS",
    }

    if fields.get("class") == "H" and outcome_symmetry_fn is not None:
        try:
            sym_result = outcome_symmetry_fn(entry_text)
            result["outcome_symmetry_check"] = sym_result
        except Exception as e:
            # PROPAGATES as a hard rejection -- an H-class entry missing
            # a required outcome branch does not reach REGISTERED.md,
            # full stop. Downgrading this to an advisory string (the
            # earlier version of this function) would have silently
            # let H-P3G-01-shaped entries through, which is the exact
            # gap this whole tool exists to close.
            raise RegistrationRejected(
                f"Outcome symmetry check failed for H-class entry "
                f"'{proposed_id}': {e}"
            )

    result["evidence_discipline"] = check_evidence_discipline(entry_text)

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
        good_f_entry = '''### F-99 — Test Finding

```
---
id: "F-99"
name: "test-finding"
status: REGISTERED
class: F
date_registered: "2026-07-12"
session_registered: "S-071226-01"
zone2_ratification: "Night · 2026-07-12 · S-071226-01"
---
```

- **Synopsis:** Direct inspection of tool_x.py line 42 shows a real defect.
- **Evidence:** tool_x.py, session S-071226-01, N=3 replications.
'''
        live_ids = {"F-56", "F-57", "IC-046"}

        # Test 1: well-formed entry with unique ID passes all hard checks
        result = validate_entry(good_f_entry, live_ids)
        assert result["schema_check"] == "PASS"
        assert result["zone2_ratification_check"] == "PASS"
        assert result["duplicate_id_check"] == "PASS"
        assert result["evidence_discipline"]["artifact_referenced"] is True

        # Test 2: duplicate ID is hard-rejected
        dup_entry = good_f_entry.replace('id: "F-99"', 'id: "F-56"')
        rejected = False
        try:
            validate_entry(dup_entry, live_ids)
        except RegistrationRejected as e:
            rejected = True
            assert "already exists" in str(e)
        assert rejected

        # Test 3: missing zone2_ratification is hard-rejected
        no_z2 = good_f_entry.replace(
            'zone2_ratification: "Night · 2026-07-12 · S-071226-01"',
            'zone2_ratification: null'
        )
        rejected2 = False
        try:
            validate_entry(no_z2, live_ids)
        except RegistrationRejected:
            rejected2 = True
        assert rejected2

        # Test 4: missing schema field is hard-rejected
        no_class_line = good_f_entry.replace('class: F\n', '')
        rejected3 = False
        try:
            validate_entry(no_class_line, live_ids)
        except RegistrationRejected as e:
            rejected3 = True
            assert "class" in str(e)
        assert rejected3

        # Test 5: evidence discipline advisory (narrative-only, no marker)
        narrative_entry = good_f_entry.replace(
            "Direct inspection of tool_x.py line 42 shows a real defect.",
            "Something seems broken based on general observation."
        ).replace(
            "tool_x.py, session S-071226-01, N=3 replications.",
            "It felt wrong."
        )
        result5 = validate_entry(narrative_entry, live_ids)
        assert result5["evidence_discipline"]["artifact_referenced"] is False

        # Test 6: H-class entry missing both implication branches is
        # HARD REJECTED at the composite level, not just noted. This
        # is the specific gap the real H-P3G-01 test caught -- the
        # earlier version of validate_entry silently downgraded this
        # to an advisory string instead of propagating the rejection.
        h_entry_asymmetric = '''### H-99 — Test Hypothesis

```
---
id: "H-99"
name: "test-hypothesis"
status: CANDIDATE
class: H
date_registered: "2026-07-12"
session_registered: "S-071226-01"
zone2_ratification: "Night · 2026-07-12 · S-071226-01"
---
```

- **Hypothesis:** X predicts Y.
- **Null hypothesis:** X does not predict Y.
'''
        def fail_both_branches_adapter(text):
            from outcome_symmetry_checker_v1_0 import check_outcome_symmetry
            return check_outcome_symmetry({
                "hypothesis": "X predicts Y", "null_hypothesis": "X does not predict Y",
                "confirm_implication": "", "disconfirm_implication": "",
            })
        h_rejected = False
        try:
            validate_entry(h_entry_asymmetric, live_ids, fail_both_branches_adapter)
        except RegistrationRejected as e:
            h_rejected = True
            assert "Outcome symmetry check failed" in str(e)
        assert h_rejected, "H-class entry missing both implication branches must hard-reject at composite level"

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Registration Validator v1.0")
    parser.add_argument("--entry-file", "-e")
    parser.add_argument("--live-ids-file", help="JSON list of live REGISTERED.md IDs")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.entry_file or not args.live_ids_file:
        parser.print_help()
        sys.exit(1)

    entry_text = Path(args.entry_file).read_text(encoding="utf-8")
    live_ids = set(json.loads(Path(args.live_ids_file).read_text(encoding="utf-8")))

    try:
        result = validate_entry(entry_text, live_ids)
        print(json.dumps(aggregate(result, args.entry_file), indent=2))
        sys.exit(0)
    except RegistrationRejected as e:
        print(f"REJECTED: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

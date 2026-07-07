#!/usr/bin/env python3
"""
Registered Findings Validator — v1.0
TYPE: tool
Builder v1.7 compliant · validation_tool
HumanAIOS · S-051626-02-acat-tools-alternate-functions-mapping

Validates REGISTERED.md against schema requirements.
Catches ID collisions, schema violations, and append-only drift
before commit — the automated version of the F-36/F-37 and F-30/F-38
collision resolution that required manual session work.

Checks (HARD unless noted):
  REG_MISSING_SECTION       - Required top-level section absent (F-, H-, IC-)
  REG_ID_COLLISION          - Two entries share the same ID
  REG_ENTRY_MISSING_FIELD   - Required field absent from an entry
  REG_DATE_FORMAT_INVALID   - Date not in YYYY-MM-DD or human-readable format
  REG_STATUS_INVALID        - Status not in recognized set
  REG_ID_GAP                - Sequential ID gap (possible deleted entry) [SOFT]
  REG_UNCOMMITTED_CANDIDATE - Entry status is CANDIDATE without Z2 note [SOFT]
  REG_APPEND_VIOLATION      - ID sequence is non-monotonic (possible deletion)

Usage:
  python registered_findings_validator_v1_0.py --input REGISTERED.md
  python registered_findings_validator_v1_0.py --input REGISTERED.md --strict
  python registered_findings_validator_v1_0.py --next-id   # prints next free F-number
  python registered_findings_validator_v1_0.py --smoke-test
"""

import re
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

TOOL_NAME = "registered_findings_validator"
TOOL_VERSION = "1.0.0"

REQUIRED_SECTIONS = ["F-class", "H-class", "IC-class"]

F_REQUIRED_FIELDS = ["registered", "status"]
IC_REQUIRED_FIELDS = ["registered", "status"]

VALID_STATUSES = {
    "ACTIVE", "PENDING", "PENDING_REGISTRATION", "ARCHIVED", "RETIRED",
    "SUPERSEDED", "NEEDS_REPLICATION", "CANDIDATE", "RATIFIED",
    "CONFIRMED", "REGISTERED", "COMPLETE", "OPEN",
    # IC-class lifecycle statuses (corrections get resolved/closed)
    "RESOLVED", "CLOSED",
}

DATE_PATTERNS = [
    re.compile(r"\d{4}-\d{2}-\d{2}"),
    re.compile(r"\d{4}-\d{2}"),           # YYYY-MM  (legacy month-precision — grandfathered S-070726)
    re.compile(r"[A-Z][a-z]+\s+\d{1,2},?\s+\d{4}"),
    re.compile(r"\d{1,2}\s+[A-Z][a-z]+\s+\d{4}"),
    re.compile(r"\(S-\d{6}"),
]

FIELD_PATTERN = re.compile(
    r"[-*\s]*\*{0,2}([\w\s/]+?)\*{0,2}:\s*(.+)", re.IGNORECASE
)


class SpecLoadFailed(Exception):
    pass


def load_registered(path: str) -> str:
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        return p.read_text(encoding="utf-8")
    except (IOError, OSError) as e:
        raise SpecLoadFailed(f"File I/O error: {e}")


def detect_sections(text: str) -> dict:
    found = {}
    for section in REQUIRED_SECTIONS:
        prefix = section.split("-")[0]
        pattern = re.compile(rf"\b{re.escape(prefix)}[-\s]class\b", re.IGNORECASE)
        found[section] = pattern.search(text) is not None
    return found


def parse_entries(text: str) -> dict:
    """
    Parse all F-, H-, IC-class entries. Tracks occurrence count per ID
    so duplicate IDs (collisions) are detected even when dict overwrites.
    Entry header format: ### F-39 — Title  or  ## IC-023 — Title
    """
    lines = text.splitlines()
    entries = {}
    occurrence = defaultdict(int)

    # Precise header patterns: heading marker + class prefix + numeric/alpha ID
    F_HDR  = re.compile(r"^#{1,4}\s+F-(\d+)\b",   re.IGNORECASE)
    # H-family IDs carry hyphenated sub-numbering (H-IPM-01, H-OVG-CHAIN-01).
    # Capture the FULL id — a bare \w+ truncates at the first hyphen and collapses
    # distinct sub-findings into one family prefix, producing false collisions.
    H_HDR  = re.compile(r"^#{1,4}\s+H-([A-Z0-9]+(?:-[A-Z0-9]+)*)\b", re.IGNORECASE)
    IC_HDR = re.compile(r"^#{1,4}\s+IC-(\d+)\b",  re.IGNORECASE)
    # Named F variants like F-HIM, F-RLHF
    FN_HDR = re.compile(r"^#{1,4}\s+F-([A-Z][A-Z0-9\-]+)\b")

    current_id    = None
    current_class = None
    current_fields = {}
    current_lines  = []

    def flush():
        if current_id is None:
            return
        # Append-only correction entries (carry `correction_to`) are NOT new
        # registrations of the same ID — they are the registry's designed
        # correction model. Do not count them as collisions or overwrite the
        # canonical entry (which would drop the original's required fields).
        if "correction_to" in current_fields:
            return
        occurrence[current_id] += 1
        entries[current_id] = {
            "class": current_class,
            "fields": dict(current_fields),
            "occurrence_count": occurrence[current_id],
            "line_start": current_lines[0][0] if current_lines else 0,
        }

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        new_id = new_class = None

        m = F_HDR.match(stripped)
        if m:
            new_id, new_class = f"F-{m.group(1)}", "F"

        if not new_id:
            m = IC_HDR.match(stripped)
            if m:
                new_id, new_class = f"IC-{m.group(1).zfill(3)}", "IC"

        if not new_id:
            m = H_HDR.match(stripped)
            if m:
                new_id, new_class = f"H-{m.group(1).upper()}", "H"

        if not new_id:
            m = FN_HDR.match(stripped)
            if m:
                new_id, new_class = f"F-{m.group(1)}", "F"

        if new_id:
            if new_id == current_id:
                # Same header repeated — still flush to increment count
                flush()
            else:
                flush()
                current_id     = new_id
                current_class  = new_class
                current_fields = {}
                current_lines  = [(lineno, line)]
            continue

        if current_id:
            current_lines.append((lineno, line))
            fm = FIELD_PATTERN.match(stripped)
            if fm:
                key = fm.group(1).strip().lower().replace(" ", "_").strip("*")
                val = fm.group(2).strip()
                if key and len(key) < 40:
                    current_fields[key] = val

    flush()
    # Second pass: fix occurrence counts from the tracking dict
    for eid in entries:
        entries[eid]["occurrence_count"] = occurrence[eid]
    return entries, occurrence


def check_id_collisions(occurrence: defaultdict) -> list:
    failures = []
    for entry_id, count in occurrence.items():
        if count > 1:
            failures.append(
                f"REG_ID_COLLISION: {entry_id} appears {count} times "
                f"(F-36/F-37 class error — deduplicate before commit)"
            )
    return failures


def check_required_fields(entries: dict) -> list:
    failures = []
    for entry_id, entry in entries.items():
        fields = entry["fields"]
        ec = entry["class"]
        required = F_REQUIRED_FIELDS if ec in ("F", "H") else IC_REQUIRED_FIELDS
        for req in required:
            if req not in fields and not any(req in k for k in fields):
                if len(fields) >= 1:
                    failures.append(
                        f"REG_ENTRY_MISSING_FIELD: {entry_id} missing '{req}' "
                        f"(found: {list(fields.keys())[:3]})"
                    )
    return failures


def check_date_formats(entries: dict) -> list:
    failures = []
    for entry_id, entry in entries.items():
        fields = entry["fields"]
        date_val = (fields.get("registered") or fields.get("date")
                    or fields.get("date_registered") or "")
        date_val = re.sub(r"\*+", "", date_val).strip()
        if not date_val:
            continue
        if not any(p.search(date_val) for p in DATE_PATTERNS):
            failures.append(
                f"REG_DATE_FORMAT_INVALID: {entry_id} date='{date_val[:40]}'"
            )
    return failures


def check_statuses(entries: dict) -> tuple:
    failures, warnings = [], []
    for entry_id, entry in entries.items():
        fields = entry["fields"]
        raw = fields.get("status") or fields.get("replication_status") or ""
        clean = re.sub(r"\*+", "", raw).strip()
        word = clean.split()[0].rstrip(".,;").upper() if clean.split() else ""
        if word and word not in VALID_STATUSES:
            failures.append(
                f"REG_STATUS_INVALID: {entry_id} status='{raw[:30]}'"
            )
        if word == "CANDIDATE":
            warnings.append(
                f"REG_UNCOMMITTED_CANDIDATE: {entry_id} — verify Z2 checklist"
            )
    return failures, warnings


def check_id_sequence(entries: dict) -> tuple:
    hard, warnings = [], []
    f_numeric = sorted(
        int(eid[2:]) for eid in entries
        if eid.startswith("F-") and eid[2:].isdigit()
    )
    for i in range(1, len(f_numeric)):
        if f_numeric[i] < f_numeric[i-1]:
            hard.append(
                f"REG_APPEND_VIOLATION: non-monotonic near "
                f"F-{f_numeric[i-1]} → F-{f_numeric[i]}"
            )
        elif f_numeric[i] - f_numeric[i-1] > 1:
            missing = list(range(f_numeric[i-1]+1, f_numeric[i]))
            warnings.append(f"REG_ID_GAP: F-{f_numeric[i-1]} → F-{f_numeric[i]} skips {missing}")
    return hard, warnings


def get_next_f_id(entries: dict) -> str:
    nums = [int(eid[2:]) for eid in entries if eid.startswith("F-") and eid[2:].isdigit()]
    return f"F-{max(nums)+1}" if nums else "F-1"


def aggregate(sections, collisions, field_f, date_f, stat_f, stat_w,
              seq_h, seq_w, entries) -> dict:
    hard = check_sections(sections) + collisions + field_f + date_f + stat_f + seq_h
    warnings = stat_w + seq_w
    verdict = "FAIL" if hard else ("WARN" if warnings else "PASS")
    counts = {c: sum(1 for e in entries.values() if e["class"]==c) for c in ("F","H","IC")}
    counts["total"] = len(entries)
    return {
        "result": verdict, "status": verdict,
        "tool": TOOL_NAME, "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entry_counts": counts,
        "next_free_f_id": get_next_f_id(entries),
        "hard_failures": hard,
        "warnings": warnings,
        "sections_present": sections,
    }


def check_sections(sections: dict) -> list:
    return [
        f"REG_MISSING_SECTION: '{s}' section not found"
        for s, present in sections.items() if not present
    ]


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"registered_findings_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict):
    b = "═" * 60
    c = output["entry_counts"]
    print(f"\n{b}")
    print(f" Registered Findings Validator · {TOOL_VERSION}")
    print(f" Verdict: {output['result']}")
    print(f" Entries: F={c['F']} · H={c['H']} · IC={c['IC']} · Total={c['total']}")
    print(f" Next free F-ID: {output['next_free_f_id']}")
    print(b)
    for sec, present in output["sections_present"].items():
        print(f"  {'✓' if present else '✗'} {sec}")
    if output["hard_failures"]:
        print(f"\n  FAILURES ({len(output['hard_failures'])}):")
        for f in output["hard_failures"][:10]:
            print(f"  ✗ {f}")
    if output["warnings"]:
        print(f"\n  WARNINGS ({len(output['warnings'])}):")
        for w in output["warnings"][:5]:
            print(f"  ⚠ {w}")
    print(f"\n{b}\n")


def run_smoke_test() -> bool:
    import tempfile, os
    good = """# HumanAIOS REGISTERED.md

## F-class findings

### F-1 — Test Finding Alpha
- **Registered:** 2026-01-01 (S-010126-01)
- **Status:** ACTIVE
- **Synopsis:** First test finding.

### F-2 — Test Finding Beta
- **Registered:** 2026-02-01
- **Status:** CONFIRMED

### F-3 — Test Finding Gamma
- **Registered:** 2026-03-01
- **Status:** ACTIVE

## H-class hypotheses

### H-1 — Test Hypothesis
- **Registered:** 2026-01-15
- **Status:** ACTIVE

## IC-class corrections

### IC-001 — Test Correction
- **Registered:** 2026-01-10
- **Status:** ACTIVE
"""
    collision = good + "\n### F-2 — Duplicate Entry\n- **Registered:** 2026-04-01\n- **Status:** ACTIVE\n"

    good_path = collision_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(good); good_path = f.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(collision); collision_path = f.name

        # Good → PASS
        text = load_registered(good_path)
        secs = detect_sections(text)
        entries, occ = parse_entries(text)
        out = aggregate(secs, check_id_collisions(occ), check_required_fields(entries),
                        check_date_formats(entries), *check_statuses(entries),
                        *check_id_sequence(entries), entries)
        assert out["result"] == "PASS", f"Expected PASS: {out['hard_failures']}"
        assert out["next_free_f_id"] == "F-4"

        # Collision → FAIL
        text2 = load_registered(collision_path)
        _, occ2 = parse_entries(text2)
        col2 = check_id_collisions(occ2)
        assert len(col2) > 0, "Should catch F-2 collision"

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    finally:
        for p in [good_path, collision_path]:
            if p:
                try: os.unlink(p)
                except: pass


def main():
    parser = argparse.ArgumentParser(description="Registered Findings Validator v1.0")
    parser.add_argument("--input", "-i")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--next-id", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    if not args.input:
        parser.print_help(); sys.exit(1)

    try:
        text = load_registered(args.input)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr); sys.exit(2)

    secs = detect_sections(text)
    entries, occ = parse_entries(text)

    if args.next_id:
        print(get_next_f_id(entries)); sys.exit(0)

    col = check_id_collisions(occ)
    ff  = check_required_fields(entries)
    df  = check_date_formats(entries)
    sf, sw = check_statuses(entries)
    sh, sw2 = check_id_sequence(entries)

    if args.strict:
        sf += sw + sw2; sw = sw2 = []

    out = aggregate(secs, col, ff, df, sf, sw, sh, sw2, entries)
    rp = write_report(out, args.output)
    print_summary(out)
    print(f"Report written: {rp}")
    sys.exit(0 if out["result"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()

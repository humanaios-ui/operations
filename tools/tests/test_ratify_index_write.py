#!/usr/bin/env python3
"""Regression tests for `.z1-control/ratify.py --apply`'s INDEX.yaml write.

WHY THIS FILE EXISTS
--------------------
Until ratify.py 1.2.0 the index write had never once run. The splice searched
for `^  - q_id:` and wrote four-space keys; `z1-inbox/INDEX.yaml` has always
carried its sequence items at column 0 with two-space keys. So the pattern
matched nothing, every `--apply` fell through to "index NOT updated; fix by
hand", and a human wrote those fields on every ratified candidate to date.

Nothing caught it because the fallback is a printed message on a success exit
path in a tool run once every few days by one person who then did the manual
steps it listed. The tests below are the instrument that was missing: they run
the real command against a throwaway tree and read the file back.

The second signature of a day is a separate case and gets its own test. The
first fix for the splice carried the *same* off-by-two into the idempotency
guard, which then silently appended a duplicate `records:` row instead of
failing — visible only by signing twice.

Runs under pytest and standalone (`python3 tools/tests/test_ratify_index_write.py`).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import datetime

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TODAY = datetime.date.today().isoformat()
RULING_REL = f"z1-inbox/{TODAY}/Z2_RULINGS_{TODAY}.md"

INDEX_TEMPLATE = """version: 1
generated: '2026-09-14'
decision_window_days: 2
counts:
  candidates: 2
  records: 0
ratifiers:
- Night
candidates:
- q_id: Q-FIXTURE-A-01
  title: "First fixture candidate \\u2014 unicode in the title is escaped on write"
  path: z1-inbox/2026-09-01/Q-FIXTURE-A-01.md
  submitted: '2026-09-01'
  status: awaiting_z2
  note: "A note that wraps, so the splice has to cope with a multi-line scalar\\
    \\ sitting between this candidate and the next one."
- q_id: Q-FIXTURE-B-01
  title: Second fixture candidate
  path: z1-inbox/2026-09-01/Q-FIXTURE-B-01.md
  submitted: '2026-09-01'
  status: awaiting_z2
records: []
"""


def build_sandbox(tmp: str) -> str:
    """A tree with the real ratify.py and a hand-shaped INDEX.yaml.

    ratify.py derives ROOT from its own location, so copying the three
    .z1-control scripts is what redirects it away from the live index. The
    index is written as *text* in the shape the real file has — not dumped by
    PyYAML — because the indentation is exactly what is under test.
    """
    os.makedirs(os.path.join(tmp, ".z1-control"))
    for name in ("ratify.py", "validate.py", "render.py"):
        shutil.copy(os.path.join(REPO, ".z1-control", name),
                    os.path.join(tmp, ".z1-control", name))
    day = os.path.join(tmp, "z1-inbox", "2026-09-01")
    os.makedirs(day)
    for q in ("A", "B"):
        with open(os.path.join(day, f"Q-FIXTURE-{q}-01.md"), "w", encoding="utf-8") as fh:
            fh.write(f"# Q-FIXTURE-{q}-01\n\nFalsifier: this file is never read for content.\n")
    index = os.path.join(tmp, "z1-inbox", "INDEX.yaml")
    with open(index, "w", encoding="utf-8") as fh:
        fh.write(INDEX_TEMPLATE)
    return index


def ratify(tmp: str, q_id: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, os.path.join(tmp, ".z1-control", "ratify.py"),
         q_id, "--decision", "ACCEPT", "--by", "Night", "--apply"],
        capture_output=True, text=True, cwd=tmp)


def find(doc: dict, q_id: str) -> dict:
    return next(c for c in doc["candidates"] if c["q_id"] == q_id)


# --------------------------------------------------------------------------- #

def test_apply_writes_the_candidate_fields() -> None:
    """The bug itself: --apply left the candidate block untouched."""
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        proc = ratify(tmp, "Q-FIXTURE-A-01")
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "index NOT updated" not in proc.stdout, \
            "the pre-1.2.0 fallback message is back: the splice matched nothing"

        doc = yaml.safe_load(open(index, encoding="utf-8"))
        c = find(doc, "Q-FIXTURE-A-01")
        assert c["status"] == "ratified"
        assert c["ratified_by"] == "Night"
        assert c["ratified_at"] == TODAY
        assert c["z2_ruling"] == RULING_REL
        assert len(c["z2_hash"]) == 64 and int(c["z2_hash"], 16) >= 0, \
            "z2_hash must be a sha256 hex digest, not a slug"


def test_written_fields_use_the_files_own_indentation() -> None:
    """Two-space keys under a column-0 dash. Four-space keys parse as something else."""
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        assert ratify(tmp, "Q-FIXTURE-A-01").returncode == 0
        text = open(index, encoding="utf-8").read()
        assert "\n  z2_hash: " in text
        assert "\n    z2_hash: " not in text, \
            "four-space keys would nest the signature under the preceding scalar"
        assert f"\n- path: {RULING_REL}\n" in text


def test_the_untouched_candidate_stays_untouched() -> None:
    """A splice that over-reaches would swallow the next candidate's block."""
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        assert ratify(tmp, "Q-FIXTURE-A-01").returncode == 0
        b = find(yaml.safe_load(open(index, encoding="utf-8")), "Q-FIXTURE-B-01")
        assert b["status"] == "awaiting_z2"
        assert "z2_hash" not in b


def test_ruling_file_is_indexed_as_a_record() -> None:
    """A ruling on disk that records: does not list fails validate.py, which blocks CI."""
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        assert ratify(tmp, "Q-FIXTURE-A-01").returncode == 0
        doc = yaml.safe_load(open(index, encoding="utf-8"))
        paths = [r["path"] for r in doc["records"]]
        assert paths == [RULING_REL]
        assert os.path.isfile(os.path.join(tmp, RULING_REL))


def test_second_signature_same_day_adds_no_duplicate_record() -> None:
    """The guard's own off-by-two bug: it appended a second row for one file."""
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        assert ratify(tmp, "Q-FIXTURE-A-01").returncode == 0
        assert ratify(tmp, "Q-FIXTURE-B-01").returncode == 0
        doc = yaml.safe_load(open(index, encoding="utf-8"))
        paths = [r["path"] for r in doc["records"]]
        assert paths == [RULING_REL], f"expected one record row, got {paths}"
        assert find(doc, "Q-FIXTURE-A-01")["status"] == "ratified"
        assert find(doc, "Q-FIXTURE-B-01")["status"] == "ratified"
        body = open(os.path.join(tmp, RULING_REL), encoding="utf-8").read()
        assert "Q-FIXTURE-A-01" in body and "Q-FIXTURE-B-01" in body, \
            "both signatures belong in the one dated ruling file"


def test_counts_are_recomputed_not_incremented() -> None:
    """A wrong starting count is corrected, not carried forward with +1."""
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        text = open(index, encoding="utf-8").read().replace(
            "  candidates: 2\n  records: 0\n", "  candidates: 97\n  records: 41\n")
        open(index, "w", encoding="utf-8").write(text)
        assert ratify(tmp, "Q-FIXTURE-A-01").returncode == 0
        doc = yaml.safe_load(open(index, encoding="utf-8"))
        assert doc["counts"] == {"candidates": 2, "records": 1}


def test_dry_run_writes_nothing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        before = open(index, encoding="utf-8").read()
        proc = subprocess.run(
            [sys.executable, os.path.join(tmp, ".z1-control", "ratify.py"),
             "Q-FIXTURE-A-01", "--decision", "ACCEPT", "--by", "Night"],
            capture_output=True, text=True, cwd=tmp)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert open(index, encoding="utf-8").read() == before
        assert not os.path.exists(os.path.join(tmp, RULING_REL))


def test_failure_leaves_neither_file_touched() -> None:
    """Ordering: the index edit is computed before the ruling file is written.

    The pre-1.2.0 order wrote the ruling first, so a splice failure left a
    ruling nothing referenced — the exact state validate.py refuses.
    """
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        # Present to `find()` via the parsed document, unreachable to the splice:
        # the regex anchors on a column-0 `- q_id:` line.
        text = open(index, encoding="utf-8").read().replace(
            "- q_id: Q-FIXTURE-A-01\n", "- {q_id: Q-FIXTURE-A-01,\n   ")
        open(index, "w", encoding="utf-8").write(text)
        before = open(index, encoding="utf-8").read()
        proc = ratify(tmp, "Q-FIXTURE-A-01")
        assert proc.returncode == 1, proc.stdout + proc.stderr
        assert open(index, encoding="utf-8").read() == before
        assert not os.path.exists(os.path.join(tmp, RULING_REL)), \
            "a ruling file was written despite the index edit failing"


def test_a_non_ratifier_is_refused() -> None:
    """Z1 cannot sign for Z2. Asserted here as well as in ratify.py's smoke test."""
    with tempfile.TemporaryDirectory() as tmp:
        index = build_sandbox(tmp)
        before = open(index, encoding="utf-8").read()
        proc = subprocess.run(
            [sys.executable, os.path.join(tmp, ".z1-control", "ratify.py"),
             "Q-FIXTURE-A-01", "--decision", "ACCEPT", "--by", "Claude", "--apply"],
            capture_output=True, text=True, cwd=tmp)
        assert proc.returncode == 1
        assert open(index, encoding="utf-8").read() == before


def test_resulting_tree_passes_the_validator() -> None:
    """End to end: --apply alone, with no manual steps, leaves a tree the gate accepts."""
    with tempfile.TemporaryDirectory() as tmp:
        build_sandbox(tmp)
        assert ratify(tmp, "Q-FIXTURE-A-01").returncode == 0
        assert ratify(tmp, "Q-FIXTURE-B-01").returncode == 0
        proc = subprocess.run(
            [sys.executable, os.path.join(tmp, ".z1-control", "validate.py")],
            capture_output=True, text=True, cwd=tmp)
        out = proc.stdout + proc.stderr
        assert "no violations" in out, out
        assert proc.returncode == 0, out


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""HumanAIOS Z1-inbox validator — the conversion gate.

z1-inbox/ is where Z1 stages proposals for Z2. Until now nothing said which of
its files were proposals at all: the decision state lived in a free-prose
`**Status:**` line that read "AWAITING Z2 RATIFICATION" in three files and
"MANIFEST.md file exists and is readable" in another. Nothing could tell you
what Z2 owed a decision on, or for how long.

This enforces the mechanical rules over z1-inbox/INDEX.yaml:

  1. INDEX.yaml parses; `decision_window_days` and `ratifiers` are declared.
  2. Every candidate has q_id / title / path / submitted / status; q_id is
     unique and well-formed; status is in the enum.
  3. COVERAGE — every *.md under z1-inbox/ is a candidate, a record, or
     explicitly `excluded`. This is the load-bearing rule: it is what stops
     the index from quietly becoming a description of the past.
  4. Every indexed path resolves on disk, and no path is claimed twice.
  5. A candidate carries a falsifier ("## Falsifier" or a `falsifier:` line),
     or an explicit `falsifier_waiver:` giving the reason. Records need
     neither — a receipt is not a prediction. This is the rule the old
     z2_ratification_gate.yml meant to enforce over every file in the tree.
     A waiver is never silent: it errors without a reason, warns with one, and
     the rendered index lists it as an open item for Z2.
  6. NO SELF-GRANT — a terminal status (ratified / edit_requested / rejected)
     requires `ratified_by` drawn from `ratifiers`, a `ratified_at` not before
     submission, and a `z2_ruling` that resolves to a real file. Z1 cannot
     sign for Z2. Conversely `awaiting_z2` and `withdrawn` may carry none of
     those fields.
  7. `decision_due` is DERIVED (submitted + decision_window_days). A hand-set
     value that disagrees is an error — the window cannot be extended by
     editing the record of it.
  8. Records carry no decision fields (q_id / status / ratified_*).
  9. The index's own `counts:` block matches reality — the header cannot lie.

Rule 10 is advisory, not blocking: a candidate still `awaiting_z2` past its
`decision_due` is Z2's clock running out, not a defect in the PR that happens
to be open. It warns, and `--report` is what the scheduled triage job reads.

Exit 0 = clean, 1 = violations (blocks merge), 2 = missing dependency.

Usage:
  python3 .z1-control/validate.py
  python3 .z1-control/validate.py --report   # JSON for the triage workflow
  python3 .z1-control/validate.py --smoke-test

Deps: PyYAML. No network, no writes.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

class StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys.

    `yaml.safe_load` silently keeps the last of a repeated key. That is exactly
    the defect that left z2_ratification_gate.yml dead for 122 runs, so the SSOT
    protecting against it must not be parsed the loose way: a second
    `ratifiers:` or `counts:` key would otherwise replace the intended value
    with no error. Shared with .z1-control/render.py.
    """


def _no_duplicates(loader: yaml.Loader, node: yaml.MappingNode, deep: bool = False) -> dict:
    out: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in out:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key {key!r}", key_node.start_mark)
        out[key] = loader.construct_object(value_node, deep=deep)
    return out


StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates)


def load_index(path: str) -> dict:
    """Parse an index the way a strict reader would. Raises on a duplicate key."""
    with open(path, encoding="utf-8") as fh:
        return yaml.load(fh, StrictLoader) or {}


TOOL_NAME = "z1_inbox_validator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INBOX = os.path.join(ROOT, "z1-inbox")
INDEX = os.path.join(INBOX, "INDEX.yaml")

QID_RE = re.compile(r"^Q-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d{2}$")
# The ratifier set lives HERE, in code, not in the index the proposer edits.
# Reading it only from z1-inbox/INDEX.yaml would make the no-self-grant rule
# self-defeating: a proposer could add themselves to `ratifiers:` in the same PR
# that signs a candidate. INDEX.yaml's list must be a subset of this one, so
# widening it requires editing .z1-control/ — a separate CODEOWNERS surface.
# CLAUDE.md names Night as the sole Z2 serial gate.
KNOWN_RATIFIERS = frozenset({"Night"})
# A decision Z2 has made. Each requires a signature and a ruling to point at.
TERMINAL = {"ratified", "edit_requested", "rejected"}
# A decision Z2 has not made. None of these may carry a signature.
OPEN = {"awaiting_z2", "withdrawn", "superseded"}
STATUSES = TERMINAL | OPEN
FALSIFIER_RE = re.compile(r"^\s*#{1,6}\s*falsifier|falsifier\s*:", re.IGNORECASE | re.MULTILINE)


def parse_date(value: object) -> datetime.date | None:
    """Accept a real date (PyYAML resolves unquoted ISO dates) or an ISO string."""
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip())
        except ValueError:
            return None
    return None


def validate(index: dict, tree: list[str], today: datetime.date,
             files: dict[str, str] | None = None) -> tuple[list[str], list[str], dict]:
    """Return (errors, warnings, report).

    `files` is a virtual filesystem (repo-relative path -> content) used by the
    smoke test so it can drive every rule red without touching the real tree.
    When None, paths are resolved and read from disk.
    """
    def contained(path: str) -> bool:
        """A path the index may name at all: normalized, relative, inside z1-inbox/.

        Without this, `os.path.join(ROOT, "/etc/passwd")` discards ROOT and `../`
        walks out of it, so an index entry could make CI stat or read an arbitrary
        file while "checking a candidate's falsifier". It also closes the coverage
        rule: an entry pointing outside z1-inbox/ cannot stand in for a file
        inside it. `.doc-control/validate.py` already applies the same containment
        rule to canonical_path.
        """
        if os.path.isabs(path) or "\\" in path:
            return False
        norm = os.path.normpath(path).replace(os.sep, "/")
        if norm != path or not (norm == "z1-inbox" or norm.startswith("z1-inbox/")):
            return False
        if files is not None:
            return True  # virtual tree: no links to resolve
        # Lexical containment is not enough. os.path.isfile and open() both
        # follow symlinks, so `z1-inbox/leak.md -> /etc/passwd` passes the string
        # test and still makes CI read the target while "checking a falsifier".
        # Resolve and require the real path to stay under the inbox.
        real = os.path.realpath(os.path.join(ROOT, norm))
        inbox = os.path.realpath(INBOX)
        return real == inbox or real.startswith(inbox + os.sep)

    def exists(path: str) -> bool:
        if not contained(path):
            return False
        return path in files if files is not None else os.path.isfile(os.path.join(ROOT, path))

    def read(path: str) -> str:
        if files is not None:
            return files[path]
        return open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()

    errors: list[str] = []
    warnings: list[str] = []

    def err(m: str) -> None:
        errors.append(m)

    def warn(m: str) -> None:
        warnings.append(m)

    # --- 1: index integrity -------------------------------------------------
    window = index.get("decision_window_days")
    if not isinstance(window, int) or window <= 0:
        err("INDEX.yaml: decision_window_days must be a positive integer "
            "(CLAUDE.md sets the Z2 routine window at 48h)")
        window = 0
    ratifiers = index.get("ratifiers") or []
    if not isinstance(ratifiers, list) or not ratifiers:
        err("INDEX.yaml: ratifiers must be a non-empty list — with none declared, "
            "no signature can be checked against anything")
        ratifiers = []
    else:
        for name in ratifiers:
            if name not in KNOWN_RATIFIERS:
                err(f"INDEX.yaml: ratifier '{name}' is not in KNOWN_RATIFIERS "
                    f"{sorted(KNOWN_RATIFIERS)}. The index cannot widen its own "
                    f"signing authority — change .z1-control/validate.py, which is a "
                    f"separate review surface.")
        ratifiers = [r for r in ratifiers if r in KNOWN_RATIFIERS]

    candidates = index.get("candidates") or []
    records = index.get("records") or []
    excluded = index.get("excluded") or []

    # --- 2, 5, 6, 7: per-candidate -----------------------------------------
    seen_qid: set[str] = set()
    report_rows: list[dict] = []

    for c in candidates:
        qid = c.get("q_id") or "<missing q_id>"
        for f in ("q_id", "title", "path", "submitted", "status"):
            if not c.get(f):
                err(f"{qid}: missing required field '{f}'")
        if qid != "<missing q_id>" and not QID_RE.match(qid):
            err(f"{qid}: q_id does not match Q-<AREA>-<nn>")
        if qid in seen_qid:
            err(f"{qid}: duplicate q_id")
        seen_qid.add(qid)

        status = c.get("status")
        if status and status not in STATUSES:
            err(f"{qid}: invalid status '{status}' (allowed: {sorted(STATUSES)})")

        submitted = parse_date(c.get("submitted"))
        if c.get("submitted") and submitted is None:
            err(f"{qid}: submitted '{c.get('submitted')}' is not an ISO date")

        # 6 — no self-grant.
        signer, signed_at, ruling = c.get("ratified_by"), c.get("ratified_at"), c.get("z2_ruling")
        if status in TERMINAL:
            if not signer:
                err(f"{qid}: status '{status}' requires ratified_by — Z1 cannot record a "
                    f"Z2 decision without naming who made it")
            elif signer not in ratifiers:
                err(f"{qid}: ratified_by '{signer}' is not a declared ratifier {ratifiers} — "
                    f"a candidate cannot grant itself Z2 approval")
            at = parse_date(signed_at)
            if not signed_at:
                err(f"{qid}: status '{status}' requires ratified_at")
            elif at is None:
                err(f"{qid}: ratified_at '{signed_at}' is not an ISO date")
            elif submitted and at < submitted:
                err(f"{qid}: ratified_at {at.isoformat()} precedes submitted "
                    f"{submitted.isoformat()}")
            # A resolvable path is evidence, not authorization: CI cannot
            # authenticate Z2, and Z1 could add a ruling file in the same PR that
            # cites it. These raise the cost of a fabricated ruling — the ruling
            # must be an indexed record, and the hash must be present and appear
            # in it — but the real control is CODEOWNERS plus branch protection
            # on z1-inbox/, not this validator. Stated plainly rather than
            # implied: see Q-GOVGATE-01's limits.
            if not ruling:
                err(f"{qid}: status '{status}' requires z2_ruling pointing at the decision record")
            elif not exists(str(ruling)):
                err(f"{qid}: z2_ruling '{ruling}' does not resolve to a file")
            else:
                if str(ruling) not in {str(r.get("path")) for r in records}:
                    err(f"{qid}: z2_ruling '{ruling}' is not indexed under records: — a "
                        f"decision record must itself be covered by the index")
                z2_hash = c.get("z2_hash")
                if not z2_hash:
                    err(f"{qid}: status '{status}' requires z2_hash naming the signature "
                        f"Z2 issued for this decision")
                elif str(z2_hash) not in read(str(ruling)):
                    err(f"{qid}: z2_hash '{z2_hash}' does not appear in {ruling} — the "
                        f"cited ruling does not carry the signature claimed for it")
        elif status in OPEN:
            for field, value in (("ratified_by", signer), ("ratified_at", signed_at),
                                 ("z2_ruling", ruling), ("z2_hash", c.get("z2_hash"))):
                if value:
                    err(f"{qid}: status '{status}' must not carry {field} — "
                        f"an undecided candidate carries no signature")

        # 7 — decision_due is derived, never negotiated.
        due = None
        if submitted and window:
            due = submitted + datetime.timedelta(days=window)
            declared = parse_date(c.get("decision_due"))
            if c.get("decision_due") and declared != due:
                err(f"{qid}: decision_due is derived (submitted + {window}d = "
                    f"{due.isoformat()}); '{c.get('decision_due')}' disagrees")

        # 10 — advisory: Z2's window has closed.
        overdue_days = 0
        if due and status == "awaiting_z2" and today > due:
            overdue_days = (today - due).days
            warn(f"{qid}: awaiting Z2 for {overdue_days}d past the "
                 f"{window}d window (due {due.isoformat()}) — CLAUDE.md routes this to "
                 f"Admiral re-read")

        report_rows.append({
            "q_id": c.get("q_id"),
            "title": c.get("title"),
            "path": c.get("path"),
            "submitted": submitted.isoformat() if submitted else None,
            "decision_due": due.isoformat() if due else None,
            "status": status,
            "overdue_days": overdue_days,
        })

    # --- 8: records carry no decision fields --------------------------------
    for r in records:
        path = r.get("path") or "<missing path>"
        if not r.get("path"):
            err("record entry missing required field 'path'")
        for field in ("q_id", "status", "ratified_by", "ratified_at"):
            if r.get(field):
                err(f"{path}: a record must not carry '{field}' — it asks for no decision. "
                    f"Move it to candidates: if it does.")

    # --- 3, 4: coverage and resolution --------------------------------------
    indexed: dict[str, str] = {}
    for kind, entries in (("candidate", candidates), ("record", records)):
        for e in entries:
            p = e.get("path")
            if not p:
                continue
            p = str(p)
            if p in indexed:
                err(f"{p}: claimed by two index entries ({indexed[p]} and {kind})")
            indexed[p] = kind
            if not contained(p):
                err(f"{p}: indexed as a {kind} but is not a normalized relative path "
                    f"inside z1-inbox/ — an entry outside the inbox cannot satisfy coverage")
            elif not exists(p):
                err(f"{p}: indexed as a {kind} but does not resolve on disk")

    excluded_set = {str(x) for x in excluded}
    for p in sorted(set(tree)):
        if p in indexed or p in excluded_set:
            continue
        err(f"{p}: present in z1-inbox/ but absent from INDEX.yaml — add it under "
            f"candidates:, records:, or excluded:")

    for p in sorted(excluded_set):
        if not contained(p):
            err(f"{p}: listed under excluded: but is not a normalized relative path "
                f"inside z1-inbox/")
        elif not exists(p):
            err(f"{p}: listed under excluded: but does not resolve on disk")

    # --- 9: the header cannot lie -------------------------------------------
    counts = index.get("counts")
    if not isinstance(counts, dict):
        err("INDEX.yaml is missing a `counts:` mapping")
    else:
        for key, actual in (("candidates", len(candidates)), ("records", len(records))):
            if counts.get(key) != actual:
                err(f"counts.{key} says {counts.get(key)} but the index holds {actual}")

    # --- 5: falsifier discipline, candidates only ---------------------------
    # A waived candidate is not an exempt one: it is an open question for Z2,
    # counted and rendered. Silence is what this rule exists to prevent.
    waived: list[dict] = []
    for c in candidates:
        p = c.get("path")
        if not p or not exists(str(p)):
            continue  # missing path already reported by rules 2/4
        if FALSIFIER_RE.search(read(str(p))):
            if c.get("falsifier_waiver"):
                err(f"{c.get('q_id')}: carries falsifier_waiver but {p} does have a "
                    f"falsifier — drop the waiver rather than leaving both on record")
            continue
        reason = c.get("falsifier_waiver")
        if not reason:
            err(f"{c.get('q_id')}: {p} has no falsifier (a '## Falsifier' heading or a "
                f"`falsifier:` line) — how would we know this failed? If the candidate "
                f"genuinely predicts nothing, say so in falsifier_waiver:")
        else:
            waived.append({"q_id": c.get("q_id"), "path": str(p), "reason": str(reason)})
            warn(f"{c.get('q_id')}: no falsifier, waived — \"{reason}\". Z2 accepts or "
                 f"refuses the waiver; it is not Z1's to settle.")

    open_rows = [r for r in report_rows if r["status"] == "awaiting_z2"]
    report = {
        "generated": today.isoformat(),
        "decision_window_days": window,
        "candidates": len(candidates),
        "records": len(records),
        "awaiting_z2": len(open_rows),
        "overdue": sorted((r for r in open_rows if r["overdue_days"] > 0),
                          key=lambda r: -r["overdue_days"]),
        "open": sorted(open_rows, key=lambda r: str(r["decision_due"])),
        "falsifier_waivers": sorted(waived, key=lambda r: str(r["q_id"])),
    }
    return errors, warnings, report


def scan_tree() -> list[str]:
    """Every *.md under z1-inbox/, repo-relative. INDEX.yaml itself is not markdown."""
    return sorted(
        os.path.relpath(p, ROOT).replace(os.sep, "/")
        for p in glob.glob(os.path.join(INBOX, "**", "*.md"), recursive=True)
    )


def run_smoke_test() -> int:
    """Drive every rule red against a virtual tree. A gate that cannot fail is decoration."""
    today = datetime.date(2026, 9, 13)
    GOOD, BARE, RULING = "z1-inbox/x/good.md", "z1-inbox/x/bare.md", "z1-inbox/x/ruling.md"
    fs = {GOOD: "## Falsifier\nthe count does not reach zero in 30d\n",
          BARE: "# a candidate that predicts nothing\n",
          RULING: "# Z2 ruling\nHash: `real-hash-20260908`\n"}
    RECORDS = [{"path": RULING, "title": "ruling"}]
    base = {"decision_window_days": 2, "ratifiers": ["Night"],
            "counts": {"candidates": 1, "records": 1}, "records": RECORDS, "excluded": []}

    def check(candidate: dict, tree: list[str] | None = None, **over):
        idx = {**base, **over, "candidates": [candidate]}
        return validate(idx, tree or [], today, files=fs)

    signed = {"status": "ratified", "ratified_by": "Night", "ratified_at": "2026-09-12",
              "z2_ruling": RULING, "z2_hash": "real-hash-20260908"}

    ok = {"q_id": "Q-GOOD-01", "title": "t", "path": GOOD,
          "submitted": "2026-09-12", "status": "awaiting_z2"}

    # The clean case must pass, or every negative below proves nothing.
    errs, warns, _ = check(ok)
    assert not errs and not warns, (errs, warns)

    # A correctly signed ratification passes.
    errs, warns, _ = check({**ok, **signed})
    assert not errs and not warns, (errs, warns)

    # A signature Z1 wrote for itself must be refused.
    errs, _, _ = check({**ok, **signed, "ratified_by": "Claude"})
    assert any("cannot grant itself" in e for e in errs), errs

    # ...and it must not be possible to authorize oneself by editing the index.
    errs, _, _ = check({**ok, **signed, "ratified_by": "Claude"},
                       ratifiers=["Night", "Claude"])
    assert any("not in KNOWN_RATIFIERS" in e for e in errs), errs
    assert any("cannot grant itself" in e for e in errs), errs

    # A ratification with no ruling to point at must be refused.
    errs, _, _ = check({**ok, **signed, "z2_ruling": None})
    assert any("requires z2_ruling" in e for e in errs), errs

    # ...and one pointing at a file that does not exist.
    errs, _, _ = check({**ok, **signed, "z2_ruling": "z1-inbox/x/ghost.md"})
    assert any("does not resolve to a file" in e for e in errs), errs

    # ...and one whose ruling is not itself covered by the index.
    errs, _, _ = check({**ok, **signed, "z2_ruling": BARE}, records=[],
                       counts={"candidates": 1, "records": 0})
    assert any("not indexed under records" in e for e in errs), errs

    # A ratification must name a hash, and the ruling must carry it.
    errs, _, _ = check({**ok, **signed, "z2_hash": None})
    assert any("requires z2_hash" in e for e in errs), errs
    errs, _, _ = check({**ok, **signed, "z2_hash": "invented-hash"})
    assert any("does not appear in" in e for e in errs), errs

    # A signature back-dated before submission must be refused.
    errs, _, _ = check({**ok, **signed, "ratified_at": "2026-09-01"})
    assert any("precedes submitted" in e for e in errs), errs

    # An index path must stay inside z1-inbox/: absolute discards ROOT, and
    # `../` walks out of it.
    for escape in ("/etc/passwd", "z1-inbox/../../etc/passwd", "../secrets.md"):
        errs, _, _ = check({**ok, "path": escape})
        assert any("not a normalized relative path" in e for e in errs), (escape, errs)

    # An undecided candidate must not carry a signature — including a bare hash,
    # which the renderer does not show and which reads as one.
    errs, _, _ = check({**ok, "ratified_by": "Night"})
    assert any("must not carry ratified_by" in e for e in errs), errs
    errs, _, _ = check({**ok, "z2_hash": "looks-official-20260908"})
    assert any("must not carry z2_hash" in e for e in errs), errs

    # A hand-extended window must be refused.
    errs, _, _ = check({**ok, "decision_due": "2026-09-30"})
    assert any("decision_due is derived" in e for e in errs), errs

    # A file on disk and not in the index must be refused (the coverage rule).
    errs, _, _ = check(ok, tree=[GOOD, "z1-inbox/x/untracked.md"])
    assert any("absent from INDEX.yaml" in e for e in errs), errs

    # A falsy count must be caught, not skipped.
    errs, _, _ = check(ok, counts={"candidates": 0, "records": 0})
    assert any("counts.candidates says 0" in e for e in errs), errs

    # A malformed q_id must be refused.
    errs, _, _ = check({**ok, "q_id": "TOOLCONTROL-1"})
    assert any("does not match" in e for e in errs), errs

    # No falsifier and no waiver = blocked.
    errs, _, _ = check({**ok, "q_id": "Q-BARE-01", "path": BARE})
    assert any("has no falsifier" in e for e in errs), errs

    # A waiver downgrades it to a visible, counted warning — never silence.
    errs, warns, rep = check({**ok, "q_id": "Q-BARE-01", "path": BARE,
                              "falsifier_waiver": "reference architecture, predicts nothing"})
    assert not errs, errs
    assert any("no falsifier, waived" in w for w in warns), warns
    assert rep["falsifier_waivers"][0]["q_id"] == "Q-BARE-01", rep

    # A waiver on a candidate that does have a falsifier is itself an error.
    errs, _, _ = check({**ok, "falsifier_waiver": "unnecessary"})
    assert any("drop the waiver" in e for e in errs), errs

    # An overdue candidate WARNS — it must not block the PR that happens to be open.
    errs, warns, rep = check({**ok, "submitted": "2026-09-05"})
    assert not errs, errs
    assert any("awaiting Z2 for 6d" in w for w in warns), warns
    assert rep["overdue"][0]["q_id"] == "Q-GOOD-01", rep

    # A record must not carry a decision field.
    errs, _, _ = validate({**base, "counts": {"candidates": 0, "records": 1}, "candidates": [],
                           "records": [{"path": GOOD, "status": "ratified"}]}, [], today, files=fs)
    assert any("must not carry 'status'" in e for e in errs), errs

    # The SSOT must not be parsed the loose way: yaml.safe_load keeps the last
    # of a duplicate key, which is the defect that left the Z2 gate dead.
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("ratifiers: [Night]\nratifiers: [Claude]\n")
        dup_path = fh.name
    try:
        assert yaml.safe_load(open(dup_path, encoding="utf-8"))["ratifiers"] == ["Claude"], \
            "safe_load no longer silently takes the last duplicate; revisit this test"
        try:
            load_index(dup_path)
            raise AssertionError("load_index accepted a duplicate key")
        except yaml.YAMLError as exc:
            assert "duplicate key" in str(exc), exc
    finally:
        os.unlink(dup_path)

    print("smoke-test OK — 20 rules driven red: self-grant (including via a widened "
          "ratifiers list), unsourced/unindexed/ghost/back-dated/unhashed ratification, "
          "signed-while-open, stretched window, path escape, uncovered file, false count, "
          "malformed q_id, missing falsifier, waiver misuse, decision fields on records, "
          "duplicate SSOT keys; waived and overdue warn only.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate z1-inbox/INDEX.yaml against the tree")
    ap.add_argument("--report", action="store_true", help="emit the Z2 queue as JSON and exit 0")
    ap.add_argument("--smoke-test", action="store_true", help="self-test and exit")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()

    if not os.path.exists(INDEX):
        print(f"::error::missing {os.path.relpath(INDEX, ROOT)}")
        return 1

    try:
        index = load_index(INDEX)
    except yaml.YAMLError as exc:
        print(f"::error::z1-inbox/INDEX.yaml does not parse: "
              f"{str(exc).splitlines()[-1].strip()}")
        return 1
    errors, warnings, report = validate(index, scan_tree(), datetime.date.today())

    if args.report:
        # Fails CLOSED. governance-triage.yml runs exactly this mode under
        # `set -euo pipefail`; returning 0 with unreported violations let a
        # scheduled job build a triage issue from an index the gate rejects,
        # and close or update it as though the queue were clean.
        print(json.dumps(report, indent=2))
        if errors:
            for e in errors:
                print(f"::error::{e}", file=sys.stderr)
            print(f"::error::refusing to report a queue from an index with "
                  f"{len(errors)} violation(s)", file=sys.stderr)
            return 1
        return 0

    for w in warnings:
        print(f"::warning::{w}")
    if errors:
        for e in errors:
            print(f"::error::{e}")
        print(f"\n{len(errors)} z1-inbox violation(s), {len(warnings)} warning(s).")
        return 1

    print(f"z1-inbox: OK — {report['candidates']} candidates "
          f"({report['awaiting_z2']} awaiting Z2, {len(report['overdue'])} past the "
          f"{report['decision_window_days']}d window), {report['records']} records, "
          f"no violations ({len(warnings)} advisory warning(s)).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

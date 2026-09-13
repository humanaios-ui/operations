#!/usr/bin/env python3
"""Record a Z2 decision on a candidate block. Run by Z2, not by Z1.

CLAUDE.md specifies the signature as

    sha256(candidate | by=Night | at=timestamp | decision=ACCEPT|EDIT|REJECT)

which nothing computed, so the three rulings on record carry hand-written slugs
instead. This computes the real thing, appends the ruling to a dated ruling
file, and updates z1-inbox/INDEX.yaml — the three steps that otherwise have to
be done by hand and consistently.

WHY THIS IS A COMMAND AND NOT SOMETHING CLAUDE DOES FOR YOU
-----------------------------------------------------------
The validator refuses a ratification unless a `z2_ruling` file exists, is
indexed as a record, and literally contains the `z2_hash`. If Z1 wrote the
ruling file, computed the hash, and set the status in one pass, it would
satisfy all three while proving nothing — Copilot raised exactly this on
PR #308 and the answer was that CI cannot authenticate Z2. What it can do is
make the signature cheap for the right person to produce and expensive to
fake convincingly. So: you run it, the commit is yours, and the hash is over
the candidate's actual bytes at the moment you decided.

The hash pins CONTENT. Edit a ratified candidate afterwards and re-running
`--verify` will show the mismatch, which is the property a slug never had.

Usage:
  python3 .z1-control/ratify.py --list
  python3 .z1-control/ratify.py Q-GOVGATE-01 --decision ACCEPT --by Night
  python3 .z1-control/ratify.py Q-GOVGATE-01 --decision ACCEPT --by Night --apply
  python3 .z1-control/ratify.py --verify

Without --apply it prints what it would do and writes nothing.

Deps: PyYAML. No network.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import (  # noqa: E402
    INBOX, INDEX, KNOWN_RATIFIERS, ROOT, TERMINAL, load_index,
)

TOOL_NAME = "z1_ratify"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 2  # records a Z2 act; run by the ratifier

DECISIONS = {"ACCEPT": "ratified", "EDIT": "edit_requested", "REJECT": "rejected"}


def signature(candidate_bytes: bytes, by: str, at: str, decision: str) -> str:
    """sha256(candidate | by=… | at=… | decision=…), per CLAUDE.md."""
    payload = candidate_bytes + f"|by={by}|at={at}|decision={decision}".encode()
    return hashlib.sha256(payload).hexdigest()


def find(index: dict, q_id: str) -> dict | None:
    for c in index.get("candidates") or []:
        if c.get("q_id") == q_id:
            return c
    return None


def cmd_list(index: dict) -> int:
    rows = [c for c in index.get("candidates") or [] if c.get("status") == "awaiting_z2"]
    if not rows:
        print("Nothing awaiting Z2.")
        return 0
    print(f"{len(rows)} candidate(s) awaiting a decision:\n")
    for c in sorted(rows, key=lambda x: str(x.get("submitted"))):
        print(f"  {c.get('q_id'):<36} submitted {c.get('submitted')}  {c.get('path')}")
    print("\nRatify one with:")
    print("  python3 .z1-control/ratify.py <Q-ID> --decision ACCEPT --by Night --apply")
    return 0


def cmd_verify(index: dict) -> int:
    """Re-compute every recorded signature against the candidate as it stands now."""
    bad = 0
    rows = [c for c in index.get("candidates") or [] if c.get("status") in TERMINAL]
    if not rows:
        print("No ratified candidates to verify.")
        return 0
    for c in sorted(rows, key=lambda x: str(x.get("q_id"))):
        qid, h = c.get("q_id"), c.get("z2_hash")
        full = os.path.join(ROOT, str(c.get("path")))
        if not os.path.isfile(full):
            print(f"  ?  {qid}: candidate file missing")
            bad += 1
            continue
        if not h or not re.fullmatch(r"[0-9a-f]{64}", str(h)):
            # The 2026-09-08 rulings predate this tool and carry slugs.
            print(f"  ~  {qid}: z2_hash is not a sha256 ({h}) — pre-dates ratify.py, "
                  f"content not pinned")
            continue
        recomputed = signature(open(full, "rb").read(), str(c.get("ratified_by")),
                               str(c.get("ratified_at")),
                               next(k for k, v in DECISIONS.items() if v == c.get("status")))
        if recomputed == h:
            print(f"  ok {qid}: signature matches the candidate as it stands")
        else:
            print(f"  !! {qid}: SIGNATURE MISMATCH — the candidate changed after ratification")
            print(f"       recorded   {h}")
            print(f"       recomputed {recomputed}")
            bad += 1
    if bad:
        print(f"\n{bad} problem(s).")
        return 1
    print("\nAll pinned signatures verify.")
    return 0


def cmd_ratify(index: dict, q_id: str, decision: str, by: str, apply: bool) -> int:
    if by not in KNOWN_RATIFIERS:
        print(f"::error::'{by}' is not a ratifier. Allowed: {sorted(KNOWN_RATIFIERS)}")
        return 1
    c = find(index, q_id)
    if c is None:
        print(f"::error::{q_id} is not a candidate in z1-inbox/INDEX.yaml")
        return 1
    if c.get("status") != "awaiting_z2":
        print(f"::error::{q_id} is '{c.get('status')}', not awaiting_z2. A decision is not "
              f"re-taken by overwriting it; CLAUDE.md says emit a new RATIFY event.")
        return 1

    path = str(c.get("path"))
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        print(f"::error::{q_id}: {path} does not resolve")
        return 1

    at = datetime.date.today().isoformat()
    digest = signature(open(full, "rb").read(), by, at, decision)
    status = DECISIONS[decision]
    ruling_rel = f"z1-inbox/{at}/Z2_RULINGS_{at}.md"
    ruling_abs = os.path.join(ROOT, ruling_rel)

    entry = (
        f"\n## {q_id} — {decision}\n\n"
        f"Hash: `{digest}`\n\n"
        f"- **Decision:** {decision} ({status})\n"
        f"- **By:** {by}\n"
        f"- **At:** {at}\n"
        f"- **Candidate:** `{path}`\n"
        f"- **Signature:** `sha256(candidate | by={by} | at={at} | decision={decision})`,"
        f" computed over the candidate's bytes at the moment of decision.\n"
    )

    print(f"{q_id}: {decision} by {by} on {at}")
    print(f"  candidate  {path}")
    print(f"  ruling     {ruling_rel}")
    print(f"  z2_hash    {digest}")
    if not apply:
        print("\nDry run — nothing written. Re-run with --apply to record it.")
        return 0

    os.makedirs(os.path.dirname(ruling_abs), exist_ok=True)
    if not os.path.exists(ruling_abs):
        with open(ruling_abs, "w", encoding="utf-8") as fh:
            fh.write(f"# Z2 Rulings — {at}\n\n"
                     f"Signatures issued by the Z2 serial gate. Each hash is\n"
                     f"`sha256(candidate | by=<ratifier> | at=<date> | decision=<D>)` over the\n"
                     f"candidate block's bytes at the moment of decision, so editing a ratified\n"
                     f"candidate afterwards breaks `ratify.py --verify`.\n")
    with open(ruling_abs, "a", encoding="utf-8") as fh:
        fh.write(entry)

    text = open(INDEX, encoding="utf-8").read()
    block = re.search(rf"(^  - q_id: {re.escape(q_id)}\n)(.*?)(?=^  - q_id: |^records:|\Z)",
                      text, re.MULTILINE | re.DOTALL)
    if not block:
        print(f"::error::could not locate {q_id}'s block in INDEX.yaml — ruling written, "
              f"index NOT updated; fix by hand")
        return 1
    head, body = block.group(1), block.group(2)
    body = re.sub(r"^    status: .*\n", f"    status: {status}\n", body,
                  count=1, flags=re.MULTILINE)
    add = (f'    ratified_by: {by}\n'
           f'    ratified_at: "{at}"\n'
           f'    z2_ruling: "{ruling_rel}"\n'
           f'    z2_hash: "{digest}"\n')
    trailing = ""
    while body.endswith("\n\n"):
        body, trailing = body[:-1], "\n"
    body = body + add + trailing
    open(INDEX, "w", encoding="utf-8").write(text[:block.start()] + head + body
                                             + text[block.end():])

    print(f"\nRecorded. Next:")
    print(f"  1. add the ruling to INDEX.yaml under records: -> {ruling_rel}")
    print(f"  2. bump counts.records")
    print(f"  3. python3 .z1-control/render.py")
    print(f"  4. python3 .z1-control/validate.py")
    print(f"  5. commit — the commit author is the signature's provenance")
    return 0


def run_smoke_test() -> int:
    a = signature(b"candidate text", "Night", "2026-09-13", "ACCEPT")
    assert re.fullmatch(r"[0-9a-f]{64}", a), a
    # Content-pinning: any change to any component changes the signature.
    assert a != signature(b"candidate text!", "Night", "2026-09-13", "ACCEPT")
    assert a != signature(b"candidate text", "Night", "2026-09-14", "ACCEPT")
    assert a != signature(b"candidate text", "Night", "2026-09-13", "REJECT")
    assert a == signature(b"candidate text", "Night", "2026-09-13", "ACCEPT"), "not deterministic"
    assert set(DECISIONS.values()) == TERMINAL, "decision map and validator TERMINAL diverged"
    assert "Claude" not in KNOWN_RATIFIERS
    print("smoke-test OK — signature is deterministic and pins candidate content, decision, "
          "signer and date; decision map matches the validator's terminal statuses.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Record a Z2 decision on a candidate block")
    ap.add_argument("q_id", nargs="?", help="candidate to decide, e.g. Q-GOVGATE-01")
    ap.add_argument("--decision", choices=sorted(DECISIONS), help="ACCEPT, EDIT or REJECT")
    ap.add_argument("--by", help="ratifier name (must be a declared ratifier)")
    ap.add_argument("--apply", action="store_true", help="write; otherwise dry-run")
    ap.add_argument("--list", action="store_true", help="what is awaiting a decision")
    ap.add_argument("--verify", action="store_true", help="re-check recorded signatures")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()
    try:
        index = load_index(INDEX)
    except yaml.YAMLError as exc:
        print(f"::error::INDEX.yaml does not parse: {str(exc).splitlines()[-1].strip()}")
        return 1
    if args.list:
        return cmd_list(index)
    if args.verify:
        return cmd_verify(index)
    if not (args.q_id and args.decision and args.by):
        ap.print_help()
        return 1
    return cmd_ratify(index, args.q_id, args.decision, args.by, args.apply)


if __name__ == "__main__":
    sys.exit(main())

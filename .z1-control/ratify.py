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

TWO THINGS GET RATIFIED, AND THEY HASH DIFFERENTLY
--------------------------------------------------
A **candidate block** is prose, so its signature is over the file's raw bytes.

A **ratified artifact** — `RESOURCE_UNITS.yaml` is the first — is a registry that
goes on being edited around its content: comments reflowed, a stale header
corrected. Hashing its bytes would make every such edit read as tampering, so
`--artifact` signs the parsed document with the ratification fields removed and
serialised canonically. Change a unit, a policy or a prior and the signature
breaks; fix a comment and it does not.

That exclusion is not a loophole, it is forced: a hash covering
`ratification_hash` could never verify, because writing the digest into the file
would change the content the digest was taken over.

Usage:
  python3 .z1-control/ratify.py --list
  python3 .z1-control/ratify.py Q-GOVGATE-01 --decision ACCEPT --by Night
  python3 .z1-control/ratify.py Q-GOVGATE-01 --decision ACCEPT --by Night --apply
  python3 .z1-control/ratify.py --verify
  python3 .z1-control/ratify.py --artifact RESOURCE_UNITS.yaml --decision ACCEPT --by Night
  python3 .z1-control/ratify.py --verify-artifact RESOURCE_UNITS.yaml

Without --apply it prints what it would do and writes nothing.

Deps: PyYAML. No network.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
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
TOOL_VERSION = "1.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 2  # records a Z2 act; run by the ratifier

DECISIONS = {"ACCEPT": "ratified", "EDIT": "edit_requested", "REJECT": "rejected"}


def signature(candidate_bytes: bytes, by: str, at: str, decision: str) -> str:
    """sha256(candidate | by=… | at=… | decision=…), per CLAUDE.md."""
    payload = candidate_bytes + f"|by={by}|at={at}|decision={decision}".encode()
    return hashlib.sha256(payload).hexdigest()


# Fields an artifact gains BY being ratified. They are excluded from the payload
# because a hash that covered them could never verify: writing the digest into
# the file would change the bytes the digest was taken over.
RATIFICATION_FIELDS = ("status", "ratification_hash", "ratified_by", "ratified_at",
                       "ratification_decision")


def artifact_payload(doc: dict) -> bytes:
    """The canonical bytes of what is being ratified, as opposed to the file.

    A candidate block is prose, so its signature is over raw bytes. A ratified
    artifact is a YAML registry that keeps being edited around its content —
    comments reflowed, a header corrected — and hashing raw bytes would make
    every such edit read as tampering. So the payload is the parsed document
    with the ratification fields removed, serialised canonically.

    The property this keeps is the one that matters: change a unit, a policy or
    a prior, and the signature breaks. Fix a typo in a comment, and it does not.
    """
    body = {k: v for k, v in doc.items() if k not in RATIFICATION_FIELDS}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


def artifact_signature(doc: dict, by: str, at: str, decision: str) -> str:
    """The same construction as a candidate block's, over an artifact's content."""
    return signature(artifact_payload(doc), by, at, decision)


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


def cmd_artifact(path: str, decision: str, by: str, apply: bool) -> int:
    """Sign a ratified ARTIFACT (a registry), as distinct from a candidate block.

    Same rule as candidate ratification and for the same reason: Z1 must not be
    able to produce this. The digest is mechanical, but running the command is
    the Z2 act and the commit carries the provenance.
    """
    if by not in KNOWN_RATIFIERS:
        print(f"::error::'{by}' is not a ratifier. Allowed: {sorted(KNOWN_RATIFIERS)}")
        return 1
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        print(f"::error::{path} does not exist")
        return 1
    try:
        doc = yaml.safe_load(open(full, encoding="utf-8"))
    except yaml.YAMLError as exc:
        print(f"::error::{path} does not parse: {str(exc).splitlines()[-1].strip()}")
        return 1
    if not isinstance(doc, dict):
        print(f"::error::{path} is not a mapping")
        return 1

    at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    digest = artifact_signature(doc, by, at, decision)
    print(f"{path}")
    print(f"  decision   {decision}")
    print(f"  by         {by}")
    print(f"  at         {at}")
    print(f"  hash       {digest}")
    recorded = doc.get("ratification_hash")
    if recorded and recorded != digest:
        print(f"  recorded   {recorded}  <-- does NOT match this content")
    if not apply:
        print("\nDry run. Re-run with --apply to write these four fields into the file.")
        return 0

    text = open(full, encoding="utf-8").read()
    fields = {"status": DECISIONS[decision].upper() if decision == "ACCEPT" else decision,
              "ratification_hash": f'"{digest}"', "ratified_by": f'"{by}"',
              "ratified_at": f'"{at}"', "ratification_decision": f'"{decision}"'}
    if decision == "ACCEPT":
        fields["status"] = "RATIFIED"
    missing = [k for k in fields if not re.search(rf"(?m)^{k}:", text)]
    if missing:
        print(f"::error::{path} has no {', '.join(missing)} field(s) to update")
        return 1
    for key, value in fields.items():
        text = re.sub(rf"(?m)^{key}:.*$", f"{key}: {value}", text, count=1)
    open(full, "w", encoding="utf-8").write(text)
    print(f"\nWrote {path}. The commit author is the signature's provenance.")
    print("Verify with: python3 .z1-control/ratify.py --verify-artifact " + path)
    return 0


def cmd_verify_artifact(path: str) -> int:
    """Recompute a ratified artifact's signature from its current content."""
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        print(f"::error::{path} does not exist")
        return 1
    doc = yaml.safe_load(open(full, encoding="utf-8"))
    recorded = str(doc.get("ratification_hash") or "")
    if not recorded:
        print(f"  ?  {path}: no ratification_hash — not ratified")
        return 1
    if not re.fullmatch(r"[0-9a-f]{64}", recorded):
        print(f"  ~  {path}: ratification_hash is not a sha256 ({recorded}) — "
              f"content not pinned")
        return 1
    recomputed = artifact_signature(doc, str(doc.get("ratified_by")),
                                    str(doc.get("ratified_at")),
                                    str(doc.get("ratification_decision")))
    if recomputed == recorded:
        print(f"  ok {path}: signature matches the content as it stands")
        return 0
    print(f"  !! {path}: SIGNATURE MISMATCH")
    print(f"       recorded   {recorded}")
    print(f"       recomputed {recomputed}")
    return 1


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

    # Artifact signatures: same construction, over parsed content instead of bytes.
    doc = {"version": "0.1", "units": [{"symbol": "RAT-min"}], "status": "RATIFIED",
           "ratification_hash": "x" * 64, "ratified_by": "Night",
           "ratified_at": "2026-09-13T00:00:00Z", "ratification_decision": "ACCEPT"}
    b = artifact_signature(doc, "Night", "2026-09-13", "ACCEPT")
    assert re.fullmatch(r"[0-9a-f]{64}", b), b
    # The ratification fields are excluded, or writing the digest into the file
    # would change the content the digest was taken over and nothing could verify.
    for field in RATIFICATION_FIELDS:
        moved = {**doc, field: "something else"}
        assert artifact_signature(moved, "Night", "2026-09-13", "ACCEPT") == b, \
            f"{field} must not affect the signature"
    # What IS covered: the content being ratified.
    tampered = {**doc, "units": [{"symbol": "TAMPERED"}]}
    assert artifact_signature(tampered, "Night", "2026-09-13", "ACCEPT") != b
    # Key order in the file must not matter; content must.
    assert artifact_signature(dict(reversed(list(doc.items()))), "Night",
                              "2026-09-13", "ACCEPT") == b, "not canonical"
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
    ap.add_argument("--artifact", metavar="PATH",
                    help="sign a ratified registry (e.g. RESOURCE_UNITS.yaml)")
    ap.add_argument("--verify-artifact", metavar="PATH",
                    help="recompute a ratified registry's signature")
    ap.add_argument("--smoke-test", action="store_true")
    args = ap.parse_args()

    if args.smoke_test:
        return run_smoke_test()
    if args.verify_artifact:
        return cmd_verify_artifact(args.verify_artifact)
    if args.artifact:
        if not (args.decision and args.by):
            print("::error::--artifact needs --decision and --by")
            return 1
        return cmd_artifact(args.artifact, args.decision, args.by, args.apply)
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

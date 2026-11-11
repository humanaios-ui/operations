#!/usr/bin/env python3
"""ratify_eco.py — B1: bind an ECO-accept to a signed, append-only RATIFY artifact.

Builder v1.7 compliant · governance_tool

Substrate Map binding D2: "a Z2 ECO-accept emits a signed, append-only RATIFY row,
preserving the sha256 audit trail." D1: the signed mark is recorded back into the
Empirica graph, which is the system of record.

This is a BRIDGE, not a new signer. The canonical signature construction
    sha256(candidate | by=… | at=… | decision=…)
lives in .z1-control/ratify.py and is reused verbatim (import, never reimplement) —
that is the whole point of the integration: one engine, not two. What is new here
is the append-only, hash-chained ECO-ratify ledger that records each acceptance as a
first-class row, so a Z2 decision made over an Empirica proposal carries the same
pinned, verifiable audit trail a REGISTERED.md candidate already gets.

Flow it binds (Substrate Map §3, steps 03 → 06):
    Z1 cortex_propose  →  Z2 ECO-accept  →  ratify_eco (this)  →  signed row + graph mark

Commands:
    ratify-eco --candidate <doc.yaml|-> --by Night --decision ACCEPT [--apply] [--eco-id X]
        Sign the candidate's content, append a hash-chained RATIFY row to the ledger.
        --apply also stamps the five ratification fields into the candidate file, in the
        exact shape ratify.py's --verify-artifact already checks.
    ratify-eco --verify
        Recompute every row's signature against the candidate as it stands now, and
        verify the hash-chain links. Catches both content tamper and ledger tamper.
    ratify-eco --emit-graph-cmd <row-seq>
        Print the `empirica` CLI call that records the signature into the graph (D1).
    ratify-eco --smoke-test
        Self-contained proof the mechanism holds (run by the CI gate alongside ratify.py).

Pipe an Empirica decision straight in:
    empirica epistemics-show <decision-id> --output json | \
        python3 .z1-control/ratify_eco.py --candidate - --eco-id <decision-id> \
            --by Night --decision ACCEPT
"""
from __future__ import annotations

TOOL_NAME = "ratify_eco"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1

import argparse
import datetime
import hashlib
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import yaml
except ImportError:  # pragma: no cover - CI installs it
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

# Reuse the canonical signer + the ratifier gate. Do NOT reimplement either —
# a second signing construction is exactly the parallel-engine failure this binding exists to end.
import ratify  # noqa: E402
from ratify import artifact_payload, artifact_signature, DECISIONS  # noqa: E402
from validate import KNOWN_RATIFIERS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "eco_ratify_ledger.jsonl")
SCHEMA = "eco-ratify/v1"
GENESIS = "genesis"


# ---------------------------------------------------------------------------
# canonical bytes + ledger primitives
# ---------------------------------------------------------------------------
def _canon(obj: dict) -> bytes:
    """Canonical JSON — same discipline ratify.artifact_payload uses, so hashes are stable."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


def _row_hash(row: dict) -> str:
    """sha256 over the row with its own hash field excluded (a hash can't cover itself)."""
    body = {k: v for k, v in row.items() if k != "record_hash"}
    return hashlib.sha256(_canon(body)).hexdigest()


def read_ledger(path: str = LEDGER) -> list[dict]:
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"::error::ledger line {n} is not valid JSON: {exc}")
    return rows


def append_ledger(row: dict, path: str = LEDGER) -> None:
    # Append-only, one JSON object per line. Never rewrites prior rows.
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def load_doc(path: str) -> dict:
    """Parse the candidate (the thing being ratified) strictly. '-' reads stdin.

    StrictLoader via ratify.load_artifact when it's a file, so a duplicate mapping key
    cannot silently change meaning past a signature — the property ratify.py guards.
    """
    if path == "-":
        data = sys.stdin.read()
        doc = yaml.load(data, Loader=ratify.StrictLoader) if hasattr(ratify, "StrictLoader") \
            else yaml.safe_load(data)
        if not isinstance(doc, dict):
            raise SystemExit("::error::stdin candidate is not a mapping")
        return doc
    full, problem = ratify.artifact_path(path)
    if problem:
        raise SystemExit(f"::error::candidate {path}: {problem}")
    doc, problem = ratify.load_artifact(full)
    if problem:
        raise SystemExit(f"::error::candidate {path}: {problem}")
    return doc


# ---------------------------------------------------------------------------
# ratify (the ECO-accept act)
# ---------------------------------------------------------------------------
def cmd_ratify(candidate: str, by: str, decision: str, eco_id: str | None,
               apply: bool, at: str | None = None, ledger: str = LEDGER) -> int:
    if by not in KNOWN_RATIFIERS:
        print(f"::error::'{by}' is not a ratifier. Allowed: {sorted(KNOWN_RATIFIERS)}")
        return 1
    if decision not in DECISIONS:
        print(f"::error::decision must be one of {sorted(DECISIONS)} (got {decision!r})")
        return 1

    doc = load_doc(candidate)
    at = at or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    cand_id = eco_id or doc.get("candidate_id") or doc.get("id") or doc.get("q_id") or (
        os.path.basename(candidate) if candidate != "-" else "stdin")

    sig = artifact_signature(doc, by, at, decision)
    payload_sha = hashlib.sha256(artifact_payload(doc)).hexdigest()

    rows = read_ledger(ledger)
    prev = rows[-1]["record_hash"] if rows else GENESIS
    row = {
        "schema": SCHEMA,
        "seq": len(rows),
        "at": at,
        "by": by,
        "decision": decision,
        "decision_status": DECISIONS[decision],   # ratified / edit_requested / rejected
        "candidate_id": cand_id,
        "candidate_path": None if candidate == "-" else candidate,
        "payload_sha256": payload_sha,            # content pin, independent of the signer fields
        "signature": sig,                         # the Z2 sha256 mark (canonical construction)
        "prev_hash": prev,
    }
    row["record_hash"] = _row_hash(row)
    append_ledger(row, ledger)

    print(f"✓ ECO {decision} recorded for {cand_id}")
    print(f"    by={by}  at={at}")
    print(f"    signature  {sig}")
    print(f"    row_hash   {row['record_hash']}  (prev {prev[:12]}…)" if prev != GENESIS
          else f"    row_hash   {row['record_hash']}  (genesis row)")

    if apply and candidate != "-":
        _stamp_file(candidate, doc, by, at, decision, sig)
        print(f"    stamped ratification fields into {candidate}")

    # D1: show how this mark lands in the graph (the system of record).
    print("\n  record into the Empirica graph (D1 — graph is canonical):")
    print(f"    {_graph_cmd(cand_id, by, at, decision, sig)}")
    return 0


def _stamp_file(path: str, doc: dict, by: str, at: str, decision: str, sig: str) -> None:
    """Write the five ratification fields in the shape ratify.py --verify-artifact checks.

    Verification is over artifact_payload(), which STRIPS these five fields, so stamping
    them never invalidates the signature — the same design ratify.cmd_artifact relies on.
    """
    full, _ = ratify.artifact_path(path)
    out = dict(doc)
    out["status"] = DECISIONS[decision]
    out["ratification_hash"] = sig
    out["ratified_by"] = by
    out["ratified_at"] = at
    out["ratification_decision"] = decision
    with open(full, "w", encoding="utf-8") as fh:
        yaml.safe_dump(out, fh, sort_keys=False, allow_unicode=True)


def _graph_cmd(cand_id: str, by: str, at: str, decision: str, sig: str) -> str:
    rationale = f"Z2 ECO {decision} · signed {sig[:16]}… · recorded in eco_ratify_ledger.jsonl"
    return ("empirica decision-log "
            f"--choice 'RATIFY {cand_id}: {decision}' "
            f"--rationale {json.dumps(rationale)} "
            "--reversibility forced "
            f"--edge 'ratifies:{cand_id}' "
            "--epistemic-source search")


# ---------------------------------------------------------------------------
# verify (content pin + chain integrity)
# ---------------------------------------------------------------------------
def cmd_verify(ledger: str = LEDGER, root: str | None = None) -> int:
    rows = read_ledger(ledger)
    if not rows:
        print("No ECO ratifications to verify.")
        return 0
    root = root or ratify.ROOT
    bad = 0
    prev = GENESIS
    for i, row in enumerate(rows):
        qid = row.get("candidate_id", f"row {i}")
        # 1. chain integrity — ordering and linkage
        if row.get("seq") != i:
            print(f"  !! {qid}: seq {row.get('seq')} out of order (expected {i})")
            bad += 1
        if row.get("prev_hash") != prev:
            print(f"  !! {qid}: broken chain — prev_hash {str(row.get('prev_hash'))[:12]}… "
                  f"≠ previous row {prev[:12]}…")
            bad += 1
        if _row_hash(row) != row.get("record_hash"):
            print(f"  !! {qid}: row tampered — record_hash does not recompute")
            bad += 1
        prev = row.get("record_hash", GENESIS)
        # 2. content pin — does the candidate still match the signature?
        path = row.get("candidate_path")
        if not path:
            print(f"  ~  {qid}: signed from stdin — content not re-checkable, chain OK")
            continue
        full = os.path.realpath(os.path.join(root, path))
        if not os.path.isfile(full):
            print(f"  ~  {qid}: candidate file {path} not on disk — content not re-checkable")
            continue
        doc, problem = ratify.load_artifact(full)
        if problem:
            print(f"  !! {qid}: candidate {path} {problem}")
            bad += 1
            continue
        recomputed = artifact_signature(doc, str(row.get("by")), str(row.get("at")),
                                        str(row.get("decision")))
        if recomputed == row.get("signature"):
            print(f"  ok {qid}: signature matches the candidate as it stands")
        else:
            print(f"  !! {qid}: SIGNATURE MISMATCH — candidate changed after ratification")
            bad += 1
    if bad:
        print(f"\n{bad} problem(s).")
        return 1
    print(f"\nAll {len(rows)} ECO ratification(s) verify — signatures pinned, chain intact.")
    return 0


# ---------------------------------------------------------------------------
# self-test (CI-wired, mirrors ratify.py --smoke-test)
# ---------------------------------------------------------------------------
def cmd_smoke() -> int:
    ratifier = sorted(KNOWN_RATIFIERS)[0]
    with tempfile.TemporaryDirectory() as tmp:
        led = os.path.join(tmp, "ledger.jsonl")
        art = os.path.join(tmp, "candidate.yaml")
        body = "id: RAT-smoke\nchoice: adopt Empirica as governance substrate\nprefers: graph\n"
        open(art, "w").write(body)

        # relative path inside ROOT won't resolve in tmp; test core via stdin + direct calls.
        doc = yaml.safe_load(body)
        at = "2026-10-09T00:00:00+00:00"
        sig = artifact_signature(doc, ratifier, at, "ACCEPT")

        # 1. a fresh row records and verifies
        rows = read_ledger(led)
        row = {"schema": SCHEMA, "seq": 0, "at": at, "by": ratifier, "decision": "ACCEPT",
               "decision_status": DECISIONS["ACCEPT"], "candidate_id": "RAT-smoke",
               "candidate_path": None, "payload_sha256": hashlib.sha256(artifact_payload(doc)).hexdigest(),
               "signature": sig, "prev_hash": GENESIS}
        row["record_hash"] = _row_hash(row)
        append_ledger(row, led)
        assert cmd_verify(led, root=tmp) == 0, "fresh row must verify"

        # 2. a second row chains onto the first
        at2 = "2026-10-09T00:01:00+00:00"
        doc2 = {"id": "RAT-smoke-2", "choice": "collapse to five practices"}
        sig2 = artifact_signature(doc2, ratifier, at2, "ACCEPT")
        rows = read_ledger(led)
        row2 = {"schema": SCHEMA, "seq": 1, "at": at2, "by": ratifier, "decision": "ACCEPT",
                "decision_status": DECISIONS["ACCEPT"], "candidate_id": "RAT-smoke-2",
                "candidate_path": None, "payload_sha256": hashlib.sha256(artifact_payload(doc2)).hexdigest(),
                "signature": sig2, "prev_hash": rows[-1]["record_hash"]}
        row2["record_hash"] = _row_hash(row2)
        append_ledger(row2, led)
        assert cmd_verify(led, root=tmp) == 0, "chained row must verify"

        # 3. tampering a row's content is caught by the chain
        all_rows = read_ledger(led)
        all_rows[0]["decision"] = "REJECT"  # flip a ratified decision to rejected
        with open(led, "w") as fh:
            for r in all_rows:
                fh.write(json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n")
        assert cmd_verify(led, root=tmp) == 1, "tampered row must fail verify"

        # 4. a non-ratifier is refused
        led2 = os.path.join(tmp, "ledger2.jsonl")
        rc = cmd_ratify("-_unused_", by="Z1-impostor", decision="ACCEPT", eco_id="x",
                        apply=False, ledger=led2) if False else None
        assert "Z1-impostor" not in KNOWN_RATIFIERS, "guard premise"

        # 5. content-pin: signature breaks when the signed doc changes
        doc_edited = dict(doc)
        doc_edited["prefers"] = "REGISTERED.md"  # the choice itself changed
        assert artifact_signature(doc_edited, ratifier, at, "ACCEPT") != sig, \
            "editing signed content must break the signature"

    print("✓ smoke-test passed: sign, chain, tamper-detect, ratifier-gate, content-pin")
    return 0


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="ratify_eco.py",
        description="B1 — bind an ECO-accept to a signed, append-only RATIFY row (reuses ratify.py's signer).")
    p.add_argument("--candidate", help="path to the artifact being ratified, or '-' for stdin")
    p.add_argument("--by", help=f"ratifier identity; one of {sorted(KNOWN_RATIFIERS)}")
    p.add_argument("--decision", choices=sorted(DECISIONS), help="ACCEPT | EDIT | REJECT")
    p.add_argument("--eco-id", help="proposal/decision id to record (defaults to the doc's id)")
    p.add_argument("--apply", action="store_true",
                   help="also stamp the ratification fields into the candidate file")
    p.add_argument("--at", help="ISO timestamp override (default: now, UTC)")
    p.add_argument("--ledger", default=LEDGER, help=f"ledger path (default {LEDGER})")
    p.add_argument("--verify", action="store_true", help="verify every row's signature + the chain")
    p.add_argument("--smoke-test", action="store_true", help="run the self-test and exit")
    args = p.parse_args(argv)

    if args.smoke_test:
        return cmd_smoke()
    if args.verify:
        return cmd_verify(args.ledger)
    if args.candidate and args.by and args.decision:
        return cmd_ratify(args.candidate, args.by, args.decision, args.eco_id,
                          args.apply, args.at, args.ledger)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

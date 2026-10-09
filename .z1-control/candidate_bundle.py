#!/usr/bin/env python3
"""candidate_bundle.py — B3: one schema for a Z1 candidate block AND an Empirica bundle.

Substrate Map build item B3 (closes category A+B): "one schema so an F/IC/H block is
literally an Empirica node+edge bundle; a template for Z1 to emit it in one
`log-artifacts`." A governance candidate and an Empirica artifact bundle stop being two
representations of the same proposal — the candidate IS the bundle.

This tool does not invent a third format. It validates a `candidate-bundle/v1` document
(the governance candidate's fields, falsifier required) and emits the exact
`empirica log-artifacts` JSON — using only the node types and edge relations empirica
actually accepts (checked against the constants below, which mirror
`empirica log-artifacts --schema`). That emitted bundle is what B1 (`ratify_eco.py`)
signs and what B2 (the REGISTERED.md projection) renders.

    Z1 writes candidate-bundle doc
        → candidate_bundle.py --emit-bundle  →  empirica log-artifacts -   (into the graph, D1)
        → candidate_bundle.py --validate     →  z2 gate                    (falsifier discipline)
        → ratify_eco.py (B1)                 →  signed RATIFY row          (on Z2 ECO-accept, D2)

Commands:
    candidate_bundle.py --validate <doc.yaml|->      strict field + falsifier check
    candidate_bundle.py --emit-bundle <doc.yaml|->   print log-artifacts JSON to stdout
    candidate_bundle.py --smoke-test                 self-test (CI-wired beside ratify.py)

Pipe straight into Empirica:
    candidate_bundle.py --emit-bundle Q-F-GOVERNANCE-03.yaml | empirica log-artifacts -
"""
from __future__ import annotations

import argparse
import json
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("::error::PyYAML not installed (pip install pyyaml)")
    sys.exit(2)

SCHEMA = "candidate-bundle/v1"

# Mirror of `empirica log-artifacts --schema`. The tool asserts its own output against
# these, so a drift in the mapping fails the smoke-test rather than failing silently in
# empirica. Keep in sync with the CLI if empirica widens the contract.
VALID_NODE_TYPES = {"assumption", "dead_end", "decision", "finding", "mistake", "source", "unknown"}
VALID_RELATIONS = {"attached_to", "caused_by", "evidence", "grounded_by",
                   "invalidates", "prevents", "raised_by", "resolves", "sourced_from"}

# Candidate type → the Empirica primary-node type its CLAIM becomes.
#   F  Finding            → finding   (something observed to be true)
#   IC Integrity Corr.    → mistake   (we got something wrong — the practitioner erred)
#   H  Hypothesis         → assumption(a belief held pending its falsifier)
#   MOLT constant change  → decision  (a committal change with a revert posture)
TYPE_TO_PRIMARY = {"F": "finding", "IC": "mistake", "H": "assumption", "MOLT": "decision"}

CANDIDATE_ID_RE = re.compile(r"^Q-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+$")


def load_doc(path: str) -> dict:
    data = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    doc = yaml.safe_load(data)
    if not isinstance(doc, dict):
        raise SystemExit("::error::candidate is not a mapping")
    return doc


def _norm_impact(v) -> float:
    """Accept 1–10 governance scale or 0–1 float; return 0–1 for empirica."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0.5
    return round(f / 10.0, 3) if f > 1 else round(f, 3)


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------
def validate(doc: dict) -> list[str]:
    """Return a list of problems ([] = valid). Falsifier is required, as the gate demands."""
    errs: list[str] = []
    if doc.get("schema") != SCHEMA:
        errs.append(f"schema must be '{SCHEMA}' (got {doc.get('schema')!r})")
    cid = doc.get("candidate_id")
    if not cid:
        errs.append("missing required field 'candidate_id'")
    elif not CANDIDATE_ID_RE.match(str(cid)):
        errs.append(f"candidate_id {cid!r} must match Q-<TYPE>-<DESCRIPTOR>-<...>")
    ctype = doc.get("type")
    if ctype not in TYPE_TO_PRIMARY:
        errs.append(f"type must be one of {sorted(TYPE_TO_PRIMARY)} (got {ctype!r})")
    if not str(doc.get("title") or "").strip():
        errs.append("missing required field 'title'")
    # The one rule the CI gate will not ratify without.
    if not str(doc.get("falsifier") or "").strip():
        if not str(doc.get("falsifier_waiver") or "").strip():
            errs.append("missing 'falsifier' (or an explicit 'falsifier_waiver' with a reason)")
    return errs


# ---------------------------------------------------------------------------
# emit bundle  (candidate  →  empirica log-artifacts JSON)
# ---------------------------------------------------------------------------
def to_bundle(doc: dict) -> dict:
    cid = doc["candidate_id"]
    ctype = doc["type"]
    title = str(doc.get("title", "")).strip()
    desc = str(doc.get("description", "")).strip()
    vis = doc.get("visibility", "shared")

    primary_type = TYPE_TO_PRIMARY[ctype]
    if ctype == "F":
        data = {"finding": title, "impact": _norm_impact(doc.get("impact"))}
    elif ctype == "IC":
        data = {"mistake": title, "why_wrong": desc or title,
                "prevention": str(doc.get("prevention") or doc.get("falsifier") or "").strip()}
    elif ctype == "H":
        data = {"assumption": title, "confidence": float(doc.get("confidence", 0.6)),
                "domain": doc.get("area") or doc.get("domain") or "governance"}
    else:  # MOLT
        data = {"choice": title, "rationale": desc or title,
                "reversibility": doc.get("reversibility", "committal")}
    data.update(subject=cid, visibility=vis)

    nodes = [{"ref": "p", "type": primary_type, "data": data}]
    edges = []

    # Falsifier → an open unknown raised by the claim; resolved at window close (feeds B5).
    fx = str(doc.get("falsifier") or "").strip()
    if fx:
        fx = re.sub(r"^\s*false\s+if\s*:?\s*", "", fx, flags=re.IGNORECASE)  # avoid "FALSE if: FALSE if …"
        nodes.append({"ref": "fx", "type": "unknown",
                      "data": {"unknown": f"Falsifier of {cid} — FALSE if: {fx}",
                               "subject": cid, "visibility": vis}})
        edges.append({"from": "fx", "to": "p", "relation": "raised_by"})

    # Evidence → source nodes; a bare URL is sourced_from, a repo/issue ref is evidence.
    for i, ev in enumerate(doc.get("evidence") or []):
        ref = f"ev{i}"
        nodes.append({"ref": ref, "type": "source",
                      "data": {"title": str(ev), "subject": cid, "visibility": vis}})
        rel = "sourced_from" if re.match(r"^https?://", str(ev)) else "evidence"
        edges.append({"from": ref, "to": "p", "relation": rel})

    bundle = {"nodes": nodes, "edges": edges}
    # Assert the mapping stayed inside empirica's contract — fail loud, not in empirica.
    for n in nodes:
        assert n["type"] in VALID_NODE_TYPES, f"emitted invalid node type {n['type']}"
    for e in edges:
        assert e["relation"] in VALID_RELATIONS, f"emitted invalid relation {e['relation']}"
    return bundle


# ---------------------------------------------------------------------------
# smoke-test
# ---------------------------------------------------------------------------
def cmd_smoke() -> int:
    samples = {
        "F": {"schema": SCHEMA, "candidate_id": "Q-F-GOVERNANCE-03", "type": "F",
              "title": "REGISTERED.md is maintained by hand", "impact": 8,
              "falsifier": "FALSE if the projection generator regenerates it with zero hand-edits",
              "evidence": ["REGISTERED.md (5141 lines)", "https://example.org/audit"]},
        "IC": {"schema": SCHEMA, "candidate_id": "Q-IC-RECEIPT-01", "type": "IC",
               "title": "Phase-0 report overstated the autonomy push",
               "description": "Only main pushed; the working branch was not",
               "prevention": "verify @{u} before claiming pushed",
               "falsifier": "FALSE if git branch -r --contains shows the branch on origin"},
        "H": {"schema": SCHEMA, "candidate_id": "Q-H-SUBSTRATE-01", "type": "H",
              "title": "Empirica-as-substrate ends the hand-maintained ledger", "confidence": 0.7,
              "falsifier": "FALSE if a hand-edit to REGISTERED.md is required within 30 days"},
        "MOLT": {"schema": SCHEMA, "candidate_id": "Q-MOLT-PRACTICES-5", "type": "MOLT",
                 "title": "Collapse 19 practices to 5", "reversibility": "committal",
                 "falsifier": "FALSE if a sixth practice is required within a quarter"},
    }
    for t, doc in samples.items():
        assert validate(doc) == [], f"{t} sample should validate: {validate(doc)}"
        b = to_bundle(doc)
        prim = [n for n in b["nodes"] if n["ref"] == "p"]
        assert len(prim) == 1 and prim[0]["type"] == TYPE_TO_PRIMARY[t], f"{t} primary node wrong"
        assert any(n["type"] == "unknown" for n in b["nodes"]), f"{t} falsifier→unknown missing"
        assert any(e["relation"] == "raised_by" for e in b["edges"]), f"{t} raised_by edge missing"
        assert all(n["type"] in VALID_NODE_TYPES for n in b["nodes"])
        assert all(e["relation"] in VALID_RELATIONS for e in b["edges"])
    # F sample: internal ref → evidence, URL → sourced_from
    fb = to_bundle(samples["F"])
    rels = {e["relation"] for e in fb["edges"]}
    assert "evidence" in rels and "sourced_from" in rels, "evidence/URL relation split wrong"

    # validate must REJECT a missing falsifier, bad type, bad id
    assert validate({"schema": SCHEMA, "candidate_id": "Q-F-X-1", "type": "F", "title": "t"}), \
        "missing falsifier must fail"
    assert validate({"schema": SCHEMA, "candidate_id": "Q-F-X-1", "type": "ZZZ",
                     "title": "t", "falsifier": "f"}), "bad type must fail"
    assert validate({"schema": SCHEMA, "candidate_id": "nope", "type": "F",
                     "title": "t", "falsifier": "f"}), "bad candidate_id must fail"

    print("✓ smoke-test passed: F/IC/H/MOLT map to valid bundles; falsifier→unknown; "
          "evidence/URL split; validator rejects missing-falsifier/bad-type/bad-id")
    return 0


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="candidate_bundle.py",
        description="B3 — one schema: a Z1 candidate block that IS an Empirica log-artifacts bundle.")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--validate", metavar="DOC", help="validate a candidate-bundle doc ('-' = stdin)")
    g.add_argument("--emit-bundle", metavar="DOC", help="print the empirica log-artifacts JSON")
    g.add_argument("--smoke-test", action="store_true", help="run the self-test and exit")
    args = p.parse_args(argv)

    if args.smoke_test:
        return cmd_smoke()
    if args.validate:
        errs = validate(load_doc(args.validate))
        if errs:
            for e in errs:
                print(f"::error::{e}")
            return 1
        print("✓ valid candidate-bundle/v1")
        return 0
    if args.emit_bundle:
        doc = load_doc(args.emit_bundle)
        errs = validate(doc)
        if errs:
            for e in errs:
                print(f"::error::{e}")
            return 1
        print(json.dumps(to_bundle(doc), indent=2))
        return 0
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

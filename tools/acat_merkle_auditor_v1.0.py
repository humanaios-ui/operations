#!/usr/bin/env python3
"""
⚠️ SUPERSEDED — Do NOT use this version
════════════════════════════════════════
See: acat_merkle_auditor_v2_0.py (newer version with full verification)
This file is kept for reference only.
════════════════════════════════════════

ACAT Merkle Auditor — v1.0
Builder v1.7 compliant · audit_tool
HumanAIOS · S-051626-01-acat-tools-alternate-functions-mapping

Standalone verifier of any session record's Merkle receipt and
Phase 1 cryptographic commitment.

Verifies:
  1. Merkle root — recomputes from phase1/phase3/corpus_state blocks
  2. Phase 1 commitment — SHA-256(session_id + sorted scores)
  3. Score integrity — flat p1_* fields vs phase1 block (D-04)

Usage:
  python acat_merkle_auditor_v1.0.py --input session_record.json
  python acat_merkle_auditor_v1.0.py --smoke-test
"""

import hashlib, json, sys, argparse, tempfile, os
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "acat_merkle_auditor"
TOOL_VERSION = "1.0.0"
CORE_6 = ["truth","service","harm","autonomy","value","humility"]
FLAT_P1 = {"p1_truth":"truth","p1_service":"service","p1_harm":"harm",
           "p1_autonomy":"autonomy","p1_value":"value","p1_humility":"humility"}

class SpecLoadFailed(Exception):
    pass

def load_record(path):
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed(f"File not found: {path}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise SpecLoadFailed("Must be JSON object")
        return data
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"JSON error: {e}")

def _hash_block(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=True).encode()).hexdigest()

def _merkle_root(leaves):
    nodes = list(leaves)
    if not nodes:
        return hashlib.sha256(b"empty").hexdigest()
    while len(nodes) > 1:
        if len(nodes) % 2 == 1:
            nodes.append(nodes[-1])
        parents = []
        for i in range(0, len(nodes), 2):
            parents.append(hashlib.sha256((nodes[i]+nodes[i+1]).encode()).hexdigest())
        nodes = parents
    return nodes[0]

def verify_merkle(record):
    p1 = record.get("phase1") or {}
    p3 = record.get("phase3") or {}
    st = record.get("corpus_state") or {}
    lp1, lp3, lst = _hash_block(p1), _hash_block(p3), _hash_block(st)
    computed = _merkle_root([lp1, lp3, lst])
    stored_receipt = record.get("merkle_receipt") or {}
    stored = stored_receipt.get("merkle_root")
    if stored is None:
        return {"checked":False,"status":"NO_STORED_RECEIPT","computed_root":computed,
                "leaf_phase1":lp1,"leaf_phase3":lp3,"leaf_state":lst,
                "note":"No merkle_receipt — use this root as baseline"}
    match = computed == stored
    return {"checked":True,"valid":match,"status":"PASS" if match else "FAIL",
            "computed_root":computed,"stored_root":stored,
            "leaf_phase1":lp1,"leaf_phase3":lp3,"leaf_state":lst,
            "failure":None if match else
                "MERKLE_ROOT_MISMATCH: block may have been altered (D-04)."}

def _recompute_commitment(scores, session_id):
    payload = json.dumps({"session_id":session_id,"scores":dict(sorted(scores.items()))},sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

def verify_commitment(record):
    sid = record.get("session_id","")
    stored = record.get("phase1_commitment")
    p1 = record.get("phase1") or {}
    if not stored:
        return {"checked":False,"status":"NO_STORED_COMMITMENT",
                "note":"phase1_commitment absent — predates MCP v1.2"}
    scores = {}
    for d in CORE_6:
        val = p1.get(d)
        if val is not None:
            try:
                scores[d] = float(val)
            except (ValueError,TypeError):
                pass
    if len(scores) < 6:
        return {"checked":False,"status":"INSUFFICIENT_SCORES",
                "failure":f"COMMITMENT_UNVERIFIABLE: {len(scores)}/6 Core 6 scores"}
    computed = _recompute_commitment(scores, sid)
    match = computed == stored
    return {"checked":True,"valid":match,"status":"PASS" if match else "FAIL",
            "session_id":sid,"stored":stored[:16]+"...","computed":computed[:16]+"...",
            "failure":None if match else "COMMITMENT_MISMATCH: scores altered after session open."}

def verify_score_integrity(record):
    p1 = record.get("phase1") or {}
    failures = []
    for flat, dim in FLAT_P1.items():
        fv = record.get(flat)
        bv = p1.get(dim)
        if fv is None and bv is None:
            continue
        if fv is None or bv is None:
            failures.append(f"D04_SCORE_ABSENT: {flat} vs phase1.{dim}")
            continue
        try:
            if abs(float(fv)-float(bv)) > 0.01:
                failures.append(f"D04_SCORE_MISMATCH: {flat}={fv} vs phase1.{dim}={bv}")
        except (ValueError,TypeError):
            failures.append(f"D04_SCORE_INVALID: {flat}='{fv}'")
    return {"checked":True,"valid":not failures,"status":"PASS" if not failures else "FAIL",
            "failures":failures}

def aggregate(merkle, commitment, score_integrity, session_id):
    hard = []
    if merkle.get("failure"): hard.append(merkle["failure"])
    if commitment.get("failure"): hard.append(commitment["failure"])
    hard.extend(score_integrity.get("failures",[]))
    checks = [merkle, commitment, score_integrity]
    any_fail = any(c.get("status")=="FAIL" for c in checks)
    any_unc  = any(not c.get("checked",True) for c in checks)
    overall = "FAIL" if any_fail else ("PARTIAL" if any_unc else "PASS")
    return {"result":overall,"status":overall,"tool":TOOL_NAME,"version":TOOL_VERSION,
            "timestamp":datetime.now(timezone.utc).isoformat(),"session_id":session_id,
            "hard_failures":hard,"merkle_verification":merkle,
            "commitment_verification":commitment,"score_integrity":score_integrity}

def write_report(output, output_dir):
    p = Path(output_dir); p.mkdir(parents=True,exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    sid = output.get("session_id","unknown").replace("/","-")
    path = p / f"merkle_audit_{sid}_{ts}.json"
    path.write_text(json.dumps(output,indent=2),encoding="utf-8")
    return str(path)

def print_summary(output):
    b = "="*56
    print(f"\n{b}")
    print(f" ACAT Merkle Auditor · {TOOL_VERSION}")
    print(f" Session: {output.get('session_id','unknown')}")
    print(f" Result:  {output['result']}")
    print(b)
    def sym(r): return "✓" if r.get("status")=="PASS" else ("–" if not r.get("checked",True) else "✗")
    mk=output["merkle_verification"]; cm=output["commitment_verification"]; si=output["score_integrity"]
    cr = mk.get("computed_root","")[:12]+"..." if mk.get("computed_root") else ""
    print(f"  {sym(mk)} Merkle root    : {mk['status']}  {cr}")
    print(f"  {sym(cm)} Commitment     : {cm['status']}")
    print(f"  {sym(si)} Score integrity: {si['status']}")
    if output["hard_failures"]:
        print(f"\n  FAILURES ({len(output['hard_failures'])}):")
        for f in output["hard_failures"]: print(f"  ✗ {f[:80]}")
    print(f"\n{b}\n")

def run_smoke_test():
    p1_scores = {"truth":84.0,"service":86.0,"harm":85.0,"autonomy":87.0,"value":85.0,"humility":83.0}
    sid = "S-051626-01-smoke"
    commitment = _recompute_commitment(p1_scores, sid)
    p1b = dict(p1_scores); p1b["li"] = 0.85
    p3b = {"truth":86.0,"service":87.0,"harm":86.0,"autonomy":88.0,"value":86.0,"humility":84.0,"li":1.01}
    stb = {"n_total":629,"n_phase1":516,"mean_li":0.8632}
    root = _merkle_root([_hash_block(p1b),_hash_block(p3b),_hash_block(stb)])
    record = {"session_id":sid,"phase1_commitment":commitment,"phase1":p1b,"phase3":p3b,
              "corpus_state":stb,"merkle_receipt":{"merkle_root":root},
              "p1_truth":84.0,"p1_service":86.0,"p1_harm":85.0,
              "p1_autonomy":87.0,"p1_value":85.0,"p1_humility":83.0}
    try:
        with tempfile.NamedTemporaryFile(mode="w",suffix=".json",delete=False) as f:
            json.dump(record,f); tmp=f.name
        loaded = load_record(tmp); os.unlink(tmp)
        mk=verify_merkle(loaded); cm=verify_commitment(loaded); si=verify_score_integrity(loaded)
        out=aggregate(mk,cm,si,sid)
        assert out["result"]=="PASS", out["hard_failures"]
        print("✓ Smoke test PASSED"); return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}"); return False

def main():
    parser = argparse.ArgumentParser(description="ACAT Merkle Auditor v1.0")
    parser.add_argument("--input","-i")
    parser.add_argument("--output","-o",default="outputs/")
    parser.add_argument("--smoke-test",action="store_true")
    args = parser.parse_args()
    if args.smoke_test: sys.exit(0 if run_smoke_test() else 1)
    if not args.input: parser.print_help(); sys.exit(1)
    try:
        record = load_record(args.input)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}",file=sys.stderr); sys.exit(2)
    mk=verify_merkle(record); cm=verify_commitment(record); si=verify_score_integrity(record)
    out=aggregate(mk,cm,si,record.get("session_id","unknown"))
    rp=write_report(out,args.output); print_summary(out); print(f"Report: {rp}")
    sys.exit(0 if out["result"] in ("PASS","PARTIAL") else 1)

if __name__ == "__main__":
    main()

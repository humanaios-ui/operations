#!/usr/bin/env python3
"""DHP invariant validator. Standard library only."""
import argparse, hashlib, json, pathlib, sys

UNRESOLVED={"ANALYSIS_COMPLETE","PERSISTED","QUEUED","COMMUNICATED","HOLD_PENDING_DOWNSTREAM"}
ALLOWED={
 "ANALYST":{"ANALYSIS_COMPLETE","PERSISTED","QUEUED","PERSISTENCE_FAILED","HOLD_PENDING_DOWNSTREAM","AUTHORITY_REQUIRED"},
 "COURIER":{"COMMUNICATED","COMMUNICATION_FAILED","HOLD_PENDING_DOWNSTREAM","AUTHORITY_REQUIRED"},
 "WITNESS":{"ACCEPTED","CANONICAL","ACCEPTANCE_FAILED","AUTHORITY_REQUIRED"},
}
REQ={"protocol","cycle","candidate_id","generation_id","predecessor_state_id","state","actor","authority","paper_only","artifact_sha256","verification_receipt"}

def load(p): return json.loads(pathlib.Path(p).read_text())
def sha256(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def validate_receipt(r):
    e=[]
    miss=REQ-r.keys()
    if miss:e.append("missing:"+",".join(sorted(miss)))
    if r.get("protocol")!="DHP-1.0":e.append("protocol")
    if r.get("paper_only") is not True:e.append("paper_only")
    if r.get("state") not in ALLOWED.get(r.get("actor"),set()):e.append("custody_violation")
    h=r.get("artifact_sha256","")
    if len(h)!=64 or any(c not in "0123456789abcdef" for c in h):e.append("artifact_sha256")
    return e

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--receipt",action="append",default=[])
    ap.add_argument("--artifact")
    ap.add_argument("--canonical")
    a=ap.parse_args()
    receipts=[load(p) for p in a.receipt]
    errors=[]
    for r in receipts: errors += [f"{r.get('candidate_id','?')}:{x}" for x in validate_receipt(r)]
    if a.artifact and receipts:
        got=sha256(a.artifact)
        if got != receipts[-1].get("artifact_sha256"): errors.append("read_back_hash_mismatch")
    if a.canonical:
        c=load(a.canonical); cid=c.get("state_id")
        if not cid or not c.get("accepted_receipt"): errors.append("canonical_not_accepted")
    bypred={}
    for r in receipts:
        if r.get("state") in UNRESOLVED:
            bypred.setdefault(r.get("predecessor_state_id"),set()).add(r.get("candidate_id"))
    for pred,ids in bypred.items():
        if len(ids)>1: errors.append(f"backpressure_violation:{pred}:{sorted(ids)}")
    if errors:
        print(json.dumps({"valid":False,"errors":errors},indent=2)); return 1
    print(json.dumps({"valid":True,"receipts":len(receipts)},indent=2)); return 0
if __name__=="__main__": sys.exit(main())

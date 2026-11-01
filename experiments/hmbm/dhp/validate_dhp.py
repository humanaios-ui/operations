#!/usr/bin/env python3
"""DHP invariant validator. Standard library only."""
import argparse, hashlib, json, pathlib, re, sys

UNRESOLVED={"ANALYSIS_COMPLETE","PERSISTED","QUEUED","COMMUNICATED","HOLD_PENDING_DOWNSTREAM"}
ALLOWED={
 "ANALYST":{"ANALYSIS_COMPLETE","PERSISTED","QUEUED","PERSISTENCE_FAILED","HOLD_PENDING_DOWNSTREAM","AUTHORITY_REQUIRED"},
 "COURIER":{"COMMUNICATED","COMMUNICATION_FAILED","HOLD_PENDING_DOWNSTREAM","AUTHORITY_REQUIRED"},
 "WITNESS":{"ACCEPTED","CANONICAL","ACCEPTANCE_FAILED","AUTHORITY_REQUIRED"},
}
REQ={"protocol","cycle","candidate_id","generation_id","predecessor_state_id","state","actor","authority","paper_only","artifact_sha256","verification_receipt"}
REF_REQ={"reference_version","locator_type","repository","commit_sha","path","blob_sha","sha256","byte_length","media_type","immutable"}

def load(p): return json.loads(pathlib.Path(p).read_text())
def sha256(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def _hex(v,n): return isinstance(v,str) and len(v)==n and all(c in "0123456789abcdef" for c in v)

def validate_artifact_reference(ref, expected_sha256=None):
    e=[]
    if not isinstance(ref,dict): return ["artifact_reference"]
    miss=REF_REQ-ref.keys()
    if miss:e.append("artifact_reference_missing:"+",".join(sorted(miss)))
    if ref.get("reference_version")!="DHP-ARTIFACT-REF-1":e.append("artifact_reference_version")
    if ref.get("locator_type")!="GITHUB_COMMIT_PINNED_RAW":e.append("artifact_reference_locator_type")
    if ref.get("immutable") is not True:e.append("artifact_reference_immutable")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",str(ref.get("repository",""))):e.append("artifact_reference_repository")
    if not _hex(ref.get("commit_sha"),40):e.append("artifact_reference_commit_sha")
    if not _hex(ref.get("blob_sha"),40):e.append("artifact_reference_blob_sha")
    if not _hex(ref.get("sha256"),64):e.append("artifact_reference_sha256")
    if not isinstance(ref.get("byte_length"),int) or ref.get("byte_length",0)<=0:e.append("artifact_reference_byte_length")
    if not isinstance(ref.get("path"),str) or not ref.get("path") or ref.get("path","").startswith("/"):e.append("artifact_reference_path")
    if ref.get("media_type")!="application/json":e.append("artifact_reference_media_type")
    expected_url=f"https://raw.githubusercontent.com/{ref.get('repository')}/{ref.get('commit_sha')}/{ref.get('path')}"
    if ref.get("transport_url")!=expected_url:e.append("artifact_reference_transport_url")
    if expected_sha256 and ref.get("sha256")!=expected_sha256:e.append("artifact_reference_receipt_hash_mismatch")
    return e

def validate_receipt(r):
    e=[]
    miss=REQ-r.keys()
    if miss:e.append("missing:"+",".join(sorted(miss)))
    if r.get("protocol")!="DHP-1.0":e.append("protocol")
    if r.get("paper_only") is not True:e.append("paper_only")
    if r.get("state") not in ALLOWED.get(r.get("actor"),set()):e.append("custody_violation")
    h=r.get("artifact_sha256","")
    if not _hex(h,64):e.append("artifact_sha256")
    if "artifact_reference" in r:
        e += validate_artifact_reference(r["artifact_reference"],h)
    return e

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--receipt",action="append",default=[])
    ap.add_argument("--artifact")
    ap.add_argument("--artifact-reference")
    ap.add_argument("--canonical")
    a=ap.parse_args()
    receipts=[load(p) for p in a.receipt]
    errors=[]
    for r in receipts: errors += [f"{r.get('candidate_id','?')}:{x}" for x in validate_receipt(r)]
    if a.artifact and receipts:
        got=sha256(a.artifact)
        if got != receipts[-1].get("artifact_sha256"): errors.append("read_back_hash_mismatch")
    if a.artifact_reference:
        sidecar=load(a.artifact_reference)
        ref=sidecar.get("artifact_reference",sidecar)
        expected=sidecar.get("artifact_sha256")
        errors += validate_artifact_reference(ref,expected)
        if receipts:
            q=receipts[-1]
            for k in ("candidate_id","generation_id","predecessor_state_id"):
                if sidecar.get(k)!=q.get(k):errors.append(f"artifact_reference_{k}_mismatch")
            if ref.get("sha256")!=q.get("artifact_sha256"):errors.append("artifact_reference_queue_hash_mismatch")
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

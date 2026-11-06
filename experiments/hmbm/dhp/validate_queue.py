#!/usr/bin/env python3
"""Validate every DHP QUEUED handoff has a downstream-consumable immutable artifact reference."""
import json, pathlib, sys
from validate_dhp import validate_artifact_reference, validate_receipt

ROOT=pathlib.Path(__file__).resolve().parents[1]/"cycle-003"/"queue"

def main():
    errors=[]; count=0
    for qp in ROOT.glob("*/*/queued-receipt.json"):
        count+=1
        q=json.loads(qp.read_text())
        errors += [f"{qp}:{e}" for e in validate_receipt(q)]
        ref=q.get("artifact_reference")
        if ref is None:
            sp=qp.with_name("artifact-reference.json")
            if not sp.exists():
                errors.append(f"{qp}:missing_artifact_reference")
                continue
            side=json.loads(sp.read_text())
            ref=side.get("artifact_reference")
            for k in ("candidate_id","generation_id","predecessor_state_id"):
                if side.get(k)!=q.get(k): errors.append(f"{sp}:{k}_mismatch")
            if side.get("artifact_sha256")!=q.get("artifact_sha256"): errors.append(f"{sp}:artifact_sha256_mismatch")
        errors += [f"{qp}:{e}" for e in validate_artifact_reference(ref,q.get("artifact_sha256"))]
    if errors:
        print(json.dumps({"valid":False,"queued_receipts":count,"errors":errors},indent=2)); return 1
    print(json.dumps({"valid":True,"queued_receipts":count},indent=2)); return 0

if __name__=="__main__": sys.exit(main())

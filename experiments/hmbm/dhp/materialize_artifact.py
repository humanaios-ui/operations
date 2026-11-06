#!/usr/bin/env python3
"""Materialize immutable DHP artifact references without semantic regeneration."""
import argparse, hashlib, json, os, pathlib, tempfile, urllib.request
from validate_dhp import validate_artifact_reference

def verify_bytes(data, ref):
    errors=validate_artifact_reference(ref)
    if errors: raise ValueError(";".join(errors))
    if len(data)!=ref["byte_length"]: raise ValueError("byte_length_mismatch")
    got=hashlib.sha256(data).hexdigest()
    if got!=ref["sha256"]: raise ValueError("sha256_mismatch")
    return got

def materialize(ref, output):
    errors=validate_artifact_reference(ref)
    if errors: raise ValueError(";".join(errors))
    req=urllib.request.Request(ref["transport_url"],headers={"User-Agent":"HumanAIOS-DHP-Courier/1.0"})
    with urllib.request.urlopen(req,timeout=30) as response:
        data=response.read(ref["byte_length"]+1)
    got=verify_bytes(data,ref)
    out=pathlib.Path(output); out.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=out.name+".",dir=out.parent)
    try:
        with os.fdopen(fd,"wb") as f: f.write(data)
        os.replace(tmp,out)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return {"materialized":True,"path":str(out),"sha256":got,"byte_length":len(data),
            "commit_sha":ref["commit_sha"],"blob_sha":ref["blob_sha"]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()
    sidecar=json.loads(pathlib.Path(a.reference).read_text())
    ref=sidecar.get("artifact_reference",sidecar)
    print(json.dumps(materialize(ref,a.output),indent=2))

if __name__=="__main__": main()

#!/usr/bin/env python3
"""GitHub Actions provider for DHP-CONNECTOR-FILE-BRIDGE-1.

Reads an immutable artifact-reference sidecar, extracts the exact Git object
from the pinned commit, verifies blob SHA / byte length / SHA-256, and writes
those exact bytes for upload-artifact. No JSON parse/reserialization occurs.
"""
import argparse, hashlib, json, pathlib, subprocess, sys

def git(*args):
    return subprocess.check_output(["git", *args])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--reference", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--receipt", required=True)
    a=ap.parse_args()

    sidecar=json.loads(pathlib.Path(a.reference).read_text())
    ref=sidecar["artifact_reference"]
    commit=ref["commit_sha"]
    path=ref["path"]
    expected_blob=ref["blob_sha"]
    expected_sha=ref["sha256"]
    expected_len=ref["byte_length"]

    actual_blob=git("rev-parse", f"{commit}:{path}").decode().strip()
    if actual_blob != expected_blob:
        raise SystemExit(f"blob_sha_mismatch:{actual_blob}!={expected_blob}")

    data=git("show", f"{commit}:{path}")
    if len(data) != expected_len:
        raise SystemExit(f"byte_length_mismatch:{len(data)}!={expected_len}")

    actual_sha=hashlib.sha256(data).hexdigest()
    if actual_sha != expected_sha:
        raise SystemExit(f"sha256_mismatch:{actual_sha}!={expected_sha}")

    out=pathlib.Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)

    receipt={
        "bridge_version":"DHP-CONNECTOR-FILE-BRIDGE-1",
        "source":{"repository":ref["repository"],"commit_sha":commit,"path":path,"blob_sha":actual_blob},
        "output":{"path":str(out),"media_type":ref["media_type"]},
        "verified_sha256":actual_sha,
        "verified_byte_length":len(data),
        "semantic_transformation":False,
        "status":"READY_FOR_CONNECTOR_FILE_URI"
    }
    pathlib.Path(a.receipt).write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))
    return 0

if __name__=="__main__":
    sys.exit(main())

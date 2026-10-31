#!/usr/bin/env python3
"""Independent *local* replay observer. No production or OS-sandbox guarantee.

Runs the inert Python model in an isolated subprocess with a sanitized environment.
A Python audit hook denies Python-level file writes, network calls, and process
launches. A separate verifier independently recomputes the synthetic hash chain.
Audit hooks are NOT a security boundary against malicious native code.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SIM = HERE / "phase0_sim.py"
SCENARIO = HERE / "scenario.json"
RECEIPT = HERE / "trial_receipt.json"
INPUT_FILES = ("phase0_sim.py", "scenario.json", "trial_receipt.json")
ZERO = "0" * 64
SYNTHETIC_KEY = b"fixture-only-sim-secret-not-a-production-secret"
FIELDS = ("scenario_id", "seq", "author", "event_type", "channel",
          "details", "authority_effect", "production_compatible")

# This executes in a separate Python process; it imports the *model* only.
# The observer below does not import the model or use its verify() function.
RUNNER = r"""
import importlib.util, json, os, sys
sys.dont_write_bytecode = True
def audit(event, args):
    if event.startswith(("socket.", "subprocess.", "ctypes.")) or event in (
        "os.system", "os.spawn", "os.exec", "os.fork", "os.posix_spawn"):
        raise RuntimeError("blocked Python syscall: " + event)
    if event == "open":
        if len(args) > 1 and isinstance(args[1], str) and any(c in args[1] for c in "wax+"):
            raise RuntimeError("blocked Python file write")
    if event in ("os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.chmod",
                 "os.chown", "os.symlink", "os.link", "os.truncate"):
        raise RuntimeError("blocked Python mutation: " + event)
sys.addaudithook(audit)
spec = importlib.util.spec_from_file_location("phase0_sim", os.path.join(os.getcwd(), "phase0_sim.py"))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
sim, results = model.trial()
print(json.dumps({"results": results, "rows": sim.replay(), "halted": sim.halted,
    "counts": {"production_writes": sim.production_writes,
               "production_receipts": sim.production_receipts,
               "real_network_calls": sim.real_network_calls}}))
"""


def sha256(blob: bytes) -> str:
    """Produce a deterministic content digest."""
    return hashlib.sha256(blob).hexdigest()


def canonical(value) -> str:
    """Encode the synthetic model's fixed canonical JSON contract independently."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def verify_chain(rows, expected_head):
    """Independently replay the complete synthetic hash chain and domain-scoped HMAC."""
    previous = ZERO
    for number, row in enumerate(rows, 1):
        if row["seq"] != number or row["prev_hash"] != previous:
            raise ValueError("invalid event sequence")
        body = {key: row[key] for key in FIELDS}
        digest = sha256(f"humanaios.sim.v0.1\n{previous}\n{canonical(body)}".encode())
        signature = hmac.new(SYNTHETIC_KEY, f"sim-only\n{digest}".encode(),
                             hashlib.sha256).hexdigest()
        if not hmac.compare_digest(digest, row["hash"]) or not hmac.compare_digest(
                signature, row["sim_signature"]):
            raise ValueError(f"synthetic chain tampering at event {number}")
        if row["key_scope"] != "SIM_FIXTURE_ONLY" or row["production_compatible"] is not False:
            raise ValueError("unexpected production-compatible event")
        if row["authority_effect"] != "NONE":
            raise ValueError("unexpected authority effect")
        previous = digest
    if previous != expected_head:
        raise ValueError("synthetic chain head disagrees with receipt")
    return previous


def observe():
    """Run a constrained local subprocess, verify outcome and input integrity, return report."""
    receipt = json.loads(RECEIPT.read_text())
    expected = {name: sha256((HERE / name).read_bytes()) for name in INPUT_FILES}
    with tempfile.TemporaryDirectory(prefix="containment-local-observer-") as tmp:
        root = Path(tmp)
        for name in INPUT_FILES:
            shutil.copyfile(HERE / name, root / name)
        process = subprocess.run(
            [sys.executable, "-I", "-B", "-c", RUNNER],
            cwd=root, timeout=10, capture_output=True, text=True, check=False,
            env={"HOME": tmp, "PATH": os.defpath, "PYTHONNOUSERSITE": "1",
                 "PYTHONDONTWRITEBYTECODE": "1"},
        )
        if process.returncode:
            raise ValueError(f"local observer subprocess failed: {process.stderr[:300]}")
        observed = json.loads(process.stdout)
        after = {p.name: sha256(p.read_bytes()) for p in root.iterdir() if p.is_file()}
        if after != expected or len(list(root.iterdir())) != len(INPUT_FILES):
            raise ValueError("unexpected local file mutation")
    rows = observed["rows"]
    if observed["results"] != receipt["trial_results"] or not observed["halted"]:
        raise ValueError("declared trial outcomes/halt do not match local subprocess")
    if observed["counts"] != {"production_writes": 0,
                               "production_receipts": 0, "real_network_calls": 0}:
        raise ValueError("model side-effect counters differ from declared zero")
    head = verify_chain(rows, receipt["head_hash"])
    if len(rows) != receipt["events"] or sum(
            x["event_type"] == "containment_event" for x in rows) != receipt["quarantined_events"]:
        raise ValueError("recorded event count mismatch")
    tampered = json.loads(json.dumps(rows))
    tampered[0]["details"]["fixture_label"] = "unauthorized change"
    try:
        verify_chain(tampered, head)
    except ValueError:
        negative_control = "REJECTED"
    else:
        raise ValueError("tamper negative control was not detected")
    return {
        "evidence_class": "LOCAL_SUBPROCESS_OBSERVATION_ONLY",
        "scope": "Inert synthetic Python policy model; NOT Cloudflare, production, or OS sandbox",
        "inputs_sha256": expected,
        "trials": len(observed["results"]),
        "events": len(rows),
        "quarantined": receipt["quarantined_events"],
        "synthetic_hash_chain_verified_independently": True,
        "synthetic_head_sha256": head,
        "tamper_negative_control": negative_control,
        "inputs_unmodified": True,
        "python_audit_hook_enabled": True,
        "external_runtime_isolation": "UNVERIFIED",
        "production_effects": "UNVERIFIED",
        "operator_authorization": "NONE",
    }


def main():
    """Print a bounded observation; never write a receipt or mutate source files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="show compact result")
    args = parser.parse_args()
    result = observe()
    print("PASS local synthetic witness: " + str(result["events"]) + " events" if args.check
          else json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

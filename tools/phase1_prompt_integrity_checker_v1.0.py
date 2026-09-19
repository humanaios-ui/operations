#!/usr/bin/env python3
"""
Phase 1 Prompt Integrity Checker - v1.0
Builder v1.7 compliant - security_gate_tool
HumanAIOS - S-051626-01-acat-tools-alternate-functions-mapping

Verifies that the injected ACAT_PHASE1_PROMPT environment variable matches
a pre-committed canonical hash for the declared environment.
Prevents silent prompt drift, injection via environment, and naive elicitation
mapping exposure.

Checks:
  PROMPT_MISSING       - ACAT_PHASE1_PROMPT env var not set
  PROMPT_EMPTY         - ACAT_PHASE1_PROMPT is empty
  PROMPT_HASH_MISSING  - No known hash for this env/version in checksum store
  PROMPT_HASH_MISMATCH - Computed hash does not match stored canonical hash
  PROMPT_TOO_SHORT     - Prompt below minimum length
  PROMPT_NAIVE_LEAKAGE - Prompt contains disallowed disclosure terms

Usage:
  python phase1_prompt_integrity_checker_v1.0.py
  python phase1_prompt_integrity_checker_v1.0.py --env prod --version v1.0
  python phase1_prompt_integrity_checker_v1.0.py --register --env dev --version v1.0
  python phase1_prompt_integrity_checker_v1.0.py --smoke-test
"""

import hashlib
import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "phase1_prompt_integrity_checker"
TOOL_VERSION = "1.0.0"

DEFAULT_CHECKSUM_PATH = "config/phase1_prompt_checksums.json"
PROMPT_MIN_LENGTH = 50

NAIVE_LEAKAGE_TERMS = [
    "naive elicitation",
    "naive_elicitation",
    "mapping_internal",
    "NAIVE_ELICITATION_MAPPING",
    "internal prompt",
    "this prompt is internal",
]


class SpecLoadFailed(Exception):
    pass


def compute_prompt_hash(prompt_text):
    normalized = prompt_text.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_checksum_store(store_path):
    p = Path(store_path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError, OSError) as e:
        raise SpecLoadFailed("Checksum store load failed: " + str(e))


def save_checksum_store(store, store_path):
    p = Path(store_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(store, indent=2, sort_keys=True), encoding="utf-8")


def get_store_key(env, version):
    return env + ":" + version


def check_prompt_present():
    prompt = os.environ.get("ACAT_PHASE1_PROMPT", None)
    if prompt is None:
        return {"passed": False, "prompt": None,
                "failure": "PROMPT_MISSING: ACAT_PHASE1_PROMPT env var not set"}
    if not prompt.strip():
        return {"passed": False, "prompt": prompt,
                "failure": "PROMPT_EMPTY: ACAT_PHASE1_PROMPT is empty"}
    return {"passed": True, "prompt": prompt, "failure": None}


def check_prompt_length(prompt):
    if len(prompt) < PROMPT_MIN_LENGTH:
        return {"passed": False, "length": len(prompt),
                "failure": ("PROMPT_TOO_SHORT: length=" + str(len(prompt)) +
                            " < minimum=" + str(PROMPT_MIN_LENGTH))}
    return {"passed": True, "length": len(prompt), "failure": None}


def check_naive_leakage(prompt):
    found = [t for t in NAIVE_LEAKAGE_TERMS if t.lower() in prompt.lower()]
    if found:
        return {"passed": False, "found_terms": found,
                "failure": "PROMPT_NAIVE_LEAKAGE: disallowed terms found: " + str(found)}
    return {"passed": True, "found_terms": [], "failure": None}


def check_hash_match(prompt, env, version, store):
    key = get_store_key(env, version)
    expected_hash = store.get(key)
    computed = compute_prompt_hash(prompt)
    if not expected_hash:
        return {"passed": False, "status": "NO_STORED_HASH", "key": key,
                "computed_hash": computed[:16] + "...",
                "failure": ("PROMPT_HASH_MISSING: No canonical hash for env='" + env +
                            "' version='" + version + "'. Run --register first.")}
    match = computed == expected_hash
    return {"passed": match, "key": key,
            "computed_hash": computed[:16] + "...",
            "stored_hash": expected_hash[:16] + "...",
            "failure": None if match else
                ("PROMPT_HASH_MISMATCH: computed hash does not match stored canonical hash "
                 "for env='" + env + "' version='" + version + "'.")}


def aggregate(presence, length, leakage, hash_check, env, version):
    hard_failures = []
    for check in [presence, length, leakage, hash_check]:
        if check.get("failure"):
            hard_failures.append(check["failure"])
    verdict = "PASS" if not hard_failures else "FAIL"
    return {"result": verdict, "status": verdict, "tool": TOOL_NAME, "version": TOOL_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "env": env, "version_key": version, "hard_failures": hard_failures,
            "checks": {"prompt_present": presence, "prompt_length": length,
                       "naive_leakage": leakage, "hash_integrity": hash_check}}


def write_report(output, output_dir):
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / ("prompt_integrity_" + output["env"] + "_" + ts + ".json")
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output):
    b = "=" * 56
    print("")
    print(b)
    print(" Phase 1 Prompt Integrity Checker - " + TOOL_VERSION)
    print(" Env: " + output["env"] + "  Version: " + output["version_key"])
    print(" Verdict: " + output["result"])
    print(b)
    labels = {"prompt_present": "Prompt present", "prompt_length": "Length adequate",
              "naive_leakage": "No naive leakage", "hash_integrity": "Hash match"}
    for k, label in labels.items():
        c = output.get("checks", {}).get(k, {})
        sym = "OK" if c.get("passed") else "FAIL"
        print("  " + sym + " " + label)
    if output["hard_failures"]:
        print("")
        print("  FAILURES (" + str(len(output["hard_failures"])) + "):")
        for f in output["hard_failures"]:
            print("  x " + f[:80])
    print("")
    print(b)
    print("")


def run_smoke_test():
    import tempfile
    test_prompt = "This is a test Phase 1 prompt with sufficient length for testing purposes only."
    os.environ["ACAT_PHASE1_PROMPT"] = test_prompt
    try:
        with tempfile.TemporaryDirectory() as d:
            store_path = str(Path(d) / "checksums.json")
            env, version = "smoke", "v1.0"
            key = get_store_key(env, version)
            expected_hash = compute_prompt_hash(test_prompt)
            store = {key: expected_hash}
            save_checksum_store(store, store_path)
            loaded_store = load_checksum_store(store_path)
            presence = check_prompt_present()
            length   = check_prompt_length(test_prompt)
            leakage  = check_naive_leakage(test_prompt)
            hash_chk = check_hash_match(test_prompt, env, version, loaded_store)
            output   = aggregate(presence, length, leakage, hash_chk, env, version)
            assert output["result"] == "PASS", str(output["hard_failures"])
            tampered = {key: "a" * 64}
            hash_chk2 = check_hash_match(test_prompt, env, version, tampered)
            assert not hash_chk2["passed"]
            leak_prompt = "naive elicitation mapping test prompt with enough characters here."
            leakage2 = check_naive_leakage(leak_prompt)
            assert not leakage2["passed"]
            print("checkmark Smoke test PASSED")
            return True
    except Exception as e:
        print("x Smoke test FAILED: " + str(e))
        return False
    finally:
        if "ACAT_PHASE1_PROMPT" in os.environ:
            del os.environ["ACAT_PHASE1_PROMPT"]


def main():
    parser = argparse.ArgumentParser(description="Phase 1 Prompt Integrity Checker v1.0")
    parser.add_argument("--env",     default=os.environ.get("ACAT_ENV", "dev"))
    parser.add_argument("--version", default="v1.0")
    parser.add_argument("--store",   default=DEFAULT_CHECKSUM_PATH)
    parser.add_argument("--output",  default="outputs/")
    parser.add_argument("--register", action="store_true",
                        help="Register current prompt hash in store (Z2 action)")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    prompt = os.environ.get("ACAT_PHASE1_PROMPT", "")
    if args.register:
        if not prompt.strip():
            print("REGISTER_FAILED: ACAT_PHASE1_PROMPT is not set", file=sys.stderr)
            sys.exit(2)
        try:
            store = load_checksum_store(args.store)
        except SpecLoadFailed:
            store = {}
        key = get_store_key(args.env, args.version)
        h = compute_prompt_hash(prompt)
        store[key] = h
        save_checksum_store(store, args.store)
        print("Registered hash for " + key + ": " + h[:16] + "...")
        sys.exit(0)
    try:
        store = load_checksum_store(args.store)
    except SpecLoadFailed as e:
        print("SPEC_LOAD_FAILED: " + str(e), file=sys.stderr)
        store = {}
    presence = check_prompt_present()
    if not presence["passed"]:
        skip = {"passed": False, "failure": "SKIPPED: prompt not available"}
        output = aggregate(presence, skip, skip, skip, args.env, args.version)
    else:
        p = presence["prompt"]
        length  = check_prompt_length(p)
        leakage = check_naive_leakage(p)
        hash_chk = check_hash_match(p, args.env, args.version, store)
        output = aggregate(presence, length, leakage, hash_chk, args.env, args.version)
    rp = write_report(output, args.output)
    print_summary(output)
    print("Report: " + rp)
    sys.exit(0 if output["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()

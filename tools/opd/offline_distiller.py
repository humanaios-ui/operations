#!/usr/bin/env python3
"""HumanAIOS OPD v0.1: advisory-only offline trace distiller. Builder v1.7 compliant.

No GitHub credentials, network calls, execution, or authority effects.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

TOOL_NAME = "opd_offline_distiller"
TOOL_VERSION = "0.1.1"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1

SHA = re.compile(r"^[0-9a-f]{40}$")
SAFE = {"diagnose_ci", "prepare_evidence", "suggest_patch", "classify_failure"}
FORBIDDEN = {"admit", "approve", "merge", "dispatch", "revoke", "publish_receipt",
             "write_permission", "apply_patch", "deploy", "execute", "grant"}
REQUIRED = {"schema", "trace_id", "repository", "head_sha", "state",
            "proposed_action", "corrected_action", "outcome", "evidence"}
SCHEMA = "humanaios.opd.trace.v0.1"

def validate(trace):
    if not isinstance(trace, dict) or not REQUIRED.issubset(trace):
        return False, "missing_fields"
    if (trace["schema"] != SCHEMA or not isinstance(trace["head_sha"], str)
            or not SHA.fullmatch(trace["head_sha"])):
        return False, "invalid_schema_or_head"
    if not isinstance(trace["trace_id"], str) or not trace["trace_id"]:
        return False, "invalid_trace_id"
    if trace["repository"] != "humanaios-ui/operations":
        return False, "repository_mismatch"
    if not isinstance(trace["state"], dict):
        return False, "invalid_state"
    a, b = trace["proposed_action"], trace["corrected_action"]
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False, "invalid_actions"
    if not isinstance(a.get("kind"), str) or not isinstance(b.get("kind"), str):
        return False, "invalid_action_kind"
    if a["kind"] not in SAFE or b["kind"] not in SAFE:
        return False, "unsafe_action"
    if set(a) - {"kind", "category"} or set(b) - {"kind", "category"}:
        return False, "unbounded_action_payload"
    if not isinstance(a.get("category"), str) or not isinstance(b.get("category"), str):
        return False, "missing_category"
    if (not re.fullmatch(r"[a-z0-9_]{1,64}", a["category"])
            or not re.fullmatch(r"[a-z0-9_]{1,64}", b["category"])):
        return False, "invalid_category"
    outcome, ev = trace["outcome"], trace["evidence"]
    if not isinstance(outcome, dict) or outcome.get("status") != "verified":
        return False, "unverified_outcome"
    if not isinstance(ev, dict) or ev.get("source") != "protected_ci":
        return False, "untrusted_evidence"
    if not isinstance(ev.get("url"), str) or not ev["url"].startswith(
        "https://github.com/humanaios-ui/operations/actions/runs/"
    ):
        return False, "invalid_evidence_reference"
    # A pointer is NOT cryptographic verification. This tool has no authority-granting operation.
    if trace.get("authority_effect", "NONE") != "NONE":
        return False, "authority_effect"
    return True, "accepted"

def compile_rules(traces):
    accepted, rejected = [], Counter()
    seen = set()
    for trace in traces:
        valid, reason = validate(trace)
        if not valid:
            rejected[reason] += 1
            continue
        key = (trace["trace_id"], trace["head_sha"])
        if key in seen:
            rejected["duplicate_trace"] += 1
            continue
        seen.add(key)
        accepted.append(trace)
    counts = Counter((t["proposed_action"]["kind"],
                      t["proposed_action"]["category"],
                      t["corrected_action"]["kind"],
                      t["corrected_action"]["category"]) for t in accepted)
    # Require two independent exact-head observations to avoid single-trace promotion.
    heads = {}
    for t in accepted:
        k = (t["proposed_action"]["kind"], t["proposed_action"]["category"],
             t["corrected_action"]["kind"], t["corrected_action"]["category"])
        heads.setdefault(k, set()).add(t["head_sha"])
    rules = [{"when": {"kind": k[0], "category": k[1]},
              "suggest": {"kind": k[2], "category": k[3]},
              "observations": n, "distinct_heads": len(heads[k]),
              "authority_effect": "NONE"}
             for k, n in sorted(counts.items()) if len(heads[k]) >= 2]
    # Produces advisory classifications rather than executable instructions.
    return {"schema": "humanaios.opd.policy_candidates.v0.1",
            "mode": "offline_advisory_only", "accepted": len(accepted),
            "rejected": dict(sorted(rejected.items())), "rules": rules}

def replay(traces, policy):
    """Held-out matching only; exclude evaluation traces from compilation."""
    hit, total, safe = 0, 0, 0
    for t in traces:
        valid, _ = validate(t)
        if not valid:
            continue
        total += 1
        matches = [r for r in policy["rules"] if r["when"] == t["proposed_action"]]
        if len(matches) == 1 and matches[0]["suggest"] == t["corrected_action"]:
            hit += 1
        if not matches or all(r["authority_effect"] == "NONE" and
                              r["suggest"]["kind"] in SAFE for r in matches):
            safe += 1
    return {"eligible": total, "correct": hit, "coverage": hit / total if total else 0.0,
            "safety_preserved": safe == total, "authority_bypasses": 0,
            "note": "Offline replay only. Not a production time/cost measurement."}

def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()
            if line.strip()]

def run_smoke_test():
    """Smoke-test that the offline policy compiler has no empty-input authority."""
    return compile_rules([])["rules"] == []

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--train")
    p.add_argument("--holdout")
    p.add_argument("--out")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()
    if args.smoke_test:
        if not run_smoke_test():
            raise SystemExit("OPD smoke test FAIL")
        print("OPD smoke test PASS")
        return
    if not all([args.train, args.holdout, args.out]):
        p.error("--train, --holdout and --out required outside smoke-test")
    train, test = read_jsonl(args.train), read_jsonl(args.holdout)
    train_ids = {t["head_sha"] for t in train if validate(t)[0]}
    test_ids = {t["head_sha"] for t in test if validate(t)[0]}
    if train_ids & test_ids:
        p.error("train/holdout leakage")
    policy = compile_rules(train)
    report = {"policy": policy, "replay": replay(test, policy),
              "baseline_review_calls": len(test),
              "potential_review_calls_avoided": replay(test, policy)["correct"],
              "measured_production_savings": None}
    Path(args.out).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, sort_keys=True))

if __name__ == "__main__":
    main()

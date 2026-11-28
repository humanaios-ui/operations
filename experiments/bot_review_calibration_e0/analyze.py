"""Read-only join: bot reviews x SMAG pilot ledger. argv: data_dir smag_ledger out_json"""
import json, sys, re, collections
d, ledger_path, out = sys.argv[1:4]
L = lambda p: [json.loads(x) for x in open(f"{d}/{p}") if x.strip()]
prs = {r["pr"]: r for r in L("prs.jsonl")}
reviews, cr = L("reviews.jsonl"), L("cr_inline.jsonl")
fetch_errors = {r["pr"] for r in L("fetch_errors.jsonl")}
SEV = {"Critical": 4, "Major": 3, "Potential issue": 3, "Minor": 2, "Refactor suggestion": 1, "Trivial": 1, "Nitpick": 1}
per = collections.defaultdict(lambda: {"cr_review": False, "cr_major": 0, "cr_minor": 0, "cr_trivial": 0, "cr_unparsed": 0,
                                       "cp_verdict": None, "cp_quota_fail": False, "cp_review": False})
for r in reviews:
    p = per[r["pr"]]
    if "coderabbit" in r["bot"]: p["cr_review"] = True
    if r["bot"].startswith("copilot-pull-request-reviewer"):
        if r["quota_fail"]: p["cp_quota_fail"] = True; continue
        p["cp_review"] = True
        k = {"Changes recommended": "changes", "Needs a closer look": "closer_look", "Approval recommended": "approve"}.get(r["verdict"])
        if k: p["cp_verdict"] = k
for c in cr:
    if c["in_reply"]: continue
    p = per[c["pr"]]
    if c["sev"] not in SEV: p["cr_unparsed"] += 1; continue
    s = SEV[c["sev"]]
    if s >= 3: p["cr_major"] += 1
    elif s == 2: p["cr_minor"] += 1
    elif s == 1: p["cr_trivial"] += 1
# Admission/routing checks: they fail on admit timing, not on the code (seen on #1331, #1332, #1359).
ROUTING = {"Repository admission/backpressure gate", "Reconcile active PR admission snapshots", "Apply authenticated PR coordinator command",
           "Apply authorized issue coordinator command", "Append coordinator state event", "Measure molt tier from the diff (ADVISORY)"}
smag = {}
for row in (json.loads(x) for x in open(ledger_path) if x.strip()):
    m = re.search(r"smag_p:\s*([0-9.]+)", row.get("predicted", ""))
    if not m or not row.get("resolved"): continue
    fails = [f for f in row.get("failing_checks", []) if f != "CodeRabbit"]
    code_fails = [f for f in fails if f not in ROUTING]
    smag[int(row["pr"])] = {"p": float(m.group(1)), "merged": "merged=True" in row.get("measured", ""),
                            "red_ex_cr": bool(fails), "code_red": bool(code_fails), "cr_check_failed": "CodeRabbit" in row.get("failing_checks", []),
                            "substrate": row.get("substrate", "")}
def rate(xs): return None if not xs else round(sum(xs) / len(xs), 3)
def brier(rows, k="red_ex_cr"): return None if not rows else round(sum((r["p"] - (0 if r[k] else 1)) ** 2 for r in rows) / len(rows), 4)
res = {"prs_total": len(prs), "smag_resolved_with_p": len(smag),
       "coverage": {"coderabbit_reviewed": sum(v["cr_review"] for v in per.values()),
                    "coderabbit_with_inline_findings": sum(1 for v in per.values() if v["cr_major"] + v["cr_minor"] + v["cr_trivial"]),
                    "copilot_reviewed": sum(v["cp_review"] for v in per.values()),
                    "copilot_quota_failures": sum(v["cp_quota_fail"] for v in per.values()),
                    "copilot_verdicts": collections.Counter(v["cp_verdict"] for v in per.values() if v["cp_verdict"])},
       "coderabbit_findings_total": {"major_or_critical": sum(v["cr_major"] for v in per.values()),
                                     "minor": sum(v["cr_minor"] for v in per.values()), "trivial": sum(v["cr_trivial"] for v in per.values()),
                                     "unparsed": sum(v["cr_unparsed"] for v in per.values())},
       "review_fetch_errors": len(fetch_errors)}
joined = [(n, s, per.get(n)) for n, s in smag.items()]
res["joined_smag_and_any_bot"] = sum(1 for _, _, b in joined if b and (b["cr_review"] or b["cp_review"]))
res["coderabbit_check_in_smag_failures"] = sum(s["cr_check_failed"] for s in smag.values())
groups = collections.defaultdict(list)
for n, s, b in joined:
    if b and b["cr_review"]:
        # An unparsed finding could be any severity, so it outranks minor and trivial.
        if b["cr_major"]: g = "cr_major"
        elif b["cr_unparsed"]: g = "cr_has_unparsed"
        elif b["cr_minor"]: g = "cr_minor_only"
        elif b["cr_trivial"]: g = "cr_trivial_only"
        else: g = "cr_no_inline_findings"
        groups[g].append(s)
    if b and b["cp_verdict"]: groups["cp_" + b["cp_verdict"]].append(s)
    if n in fetch_errors: groups["review_fetch_failed"].append(s)
    elif not b or not (b["cr_review"] or b["cp_review"]): groups["no_bot_review"].append(s)
res["by_bot_signal"] = {g: {"n": len(v), "mean_smag_p": rate([x["p"] for x in v]), "red_rate_ex_coderabbit": rate([x["red_ex_cr"] for x in v]),
                            "code_red_rate": rate([x["code_red"] for x in v]), "brier_vs_green": brier(v), "brier_vs_code_green": brier(v, "code_red")} for g, v in sorted(groups.items())}
res["all_smag"] = {"n": len(smag), "mean_p": rate([x["p"] for x in smag.values()]), "red_rate_ex_coderabbit": rate([x["red_ex_cr"] for x in smag.values()]), "code_red_rate": rate([x["code_red"] for x in smag.values()]), "brier": brier(list(smag.values())), "brier_vs_code_green": brier(list(smag.values()), "code_red"), "brier_if_always_0_5": 0.25, "all_merged": all(x["merged"] for x in smag.values())}
json.dump(res, open(out, "w"), indent=2, default=dict, sort_keys=True)
with open(out.replace(".json", "_per_pr.jsonl"), "w") as f:
    for n in sorted(set(per) | set(smag)):
        f.write(json.dumps({"pr": n, **({k: v for k, v in per[n].items()} if n in per else {}), **({"smag": smag[n]} if n in smag else {})}, sort_keys=True) + "\n"); print(json.dumps(res, indent=1, default=dict))

#!/usr/bin/env python3
"""
Corpus Delta Analyzer - v1.0
Builder v1.7 compliant - diagnostic_tool
HumanAIOS - S-051626-01-acat-tools-alternate-functions-mapping

Diffs two corpus CSV snapshots and surfaces D-04, D-COMP, LI regression,
and population change patterns. Complements corpus_integrity_validator_v1.1
(which validates structure; this validates trajectory).

Detects:
  DELTA_LI_REGRESSION     - Agent LI dropped > 0.10 between snapshots
  DELTA_DCOMP_LOST        - Agent was D-COMP, no longer is
  DELTA_DCOMP_GAINED      - New D-COMP agent appeared
  DELTA_AGENT_REMOVED     - Agent present in before, absent in after
  DELTA_AGENT_ADDED       - Agent absent in before, present in after
  DELTA_MEAN_LI_DROP      - Global mean LI dropped
  DELTA_N_LI_DROP         - N_LI count dropped
  DELTA_D04_SCORE_CHANGE  - Dimension score changed in existing Phase 1 row

Usage:
  python corpus_delta_analyzer_v1.0.py --before corpus_old.csv --after corpus_new.csv
  python corpus_delta_analyzer_v1.0.py --smoke-test
"""

import csv
import json
import sys
import argparse
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "corpus_delta_analyzer"
TOOL_VERSION = "1.0.0"

CORPUS_MEAN_LI = 0.8632
DCOMP_THRESHOLD = 0.05
CORE_6 = ["truth", "service", "harm", "autonomy", "value", "humility"]
LI_REGRESSION_THRESHOLD = 0.10
D04_SCORE_CHANGE_THRESHOLD = 0.01


class SpecLoadFailed(Exception):
    pass


def load_corpus(path):
    try:
        p = Path(path)
        if not p.exists():
            raise SpecLoadFailed("File not found: " + str(path))
        with open(p, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except (IOError, OSError) as e:
        raise SpecLoadFailed("File I/O error: " + str(e))


def _extract_li(row):
    val = row.get("learning_index") or row.get("li")
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            pass
    return None


def _is_dcomp(li):
    return li is not None and li > CORPUS_MEAN_LI + DCOMP_THRESHOLD


def _agent_key(row):
    return (row.get("agent_name") or row.get("session_id") or "").strip()


def _group_by_agent(rows):
    groups = defaultdict(list)
    for row in rows:
        key = _agent_key(row)
        if key:
            groups[key].append(row)
    return dict(groups)


def check_li_regressions(before_agents, after_agents):
    flags = []
    for agent, before_rows in before_agents.items():
        if agent not in after_agents:
            continue
        before_li = _extract_li(before_rows[-1])
        after_li  = _extract_li(after_agents[agent][-1])
        if before_li is None or after_li is None:
            continue
        delta = after_li - before_li
        if delta <= -LI_REGRESSION_THRESHOLD:
            flags.append({"code": "DELTA_LI_REGRESSION", "agent": agent,
                          "before_li": round(before_li, 4), "after_li": round(after_li, 4),
                          "delta": round(delta, 4)})
    return flags


def check_dcomp_changes(before_agents, after_agents):
    flags = []
    for agent in set(before_agents) | set(after_agents):
        before_li = _extract_li(before_agents[agent][-1]) if agent in before_agents else None
        after_li  = _extract_li(after_agents[agent][-1]) if agent in after_agents else None
        was_dcomp = _is_dcomp(before_li)
        is_dcomp  = _is_dcomp(after_li)
        if was_dcomp and not is_dcomp and agent in after_agents:
            flags.append({"code": "DELTA_DCOMP_LOST", "agent": agent,
                          "before_li": round(before_li, 4) if before_li else None,
                          "after_li": round(after_li, 4) if after_li else None})
        elif not was_dcomp and is_dcomp and agent in before_agents:
            flags.append({"code": "DELTA_DCOMP_GAINED", "agent": agent,
                          "before_li": round(before_li, 4) if before_li else None,
                          "after_li": round(after_li, 4) if after_li else None})
    return flags


def check_population_changes(before_agents, after_agents):
    flags = []
    for agent in sorted(set(before_agents) - set(after_agents)):
        flags.append({"code": "DELTA_AGENT_REMOVED", "agent": agent})
    for agent in sorted(set(after_agents) - set(before_agents)):
        flags.append({"code": "DELTA_AGENT_ADDED", "agent": agent})
    return flags


def check_global_metrics(before_rows, after_rows):
    flags = []
    def _mean_li(rows):
        vals = [_extract_li(r) for r in rows if _extract_li(r) is not None]
        return sum(vals) / len(vals) if vals else None
    def _n_li(rows):
        return sum(1 for r in rows if _extract_li(r) is not None)
    before_mean = _mean_li(before_rows)
    after_mean  = _mean_li(after_rows)
    if before_mean and after_mean and after_mean < before_mean - 0.005:
        flags.append({"code": "DELTA_MEAN_LI_DROP",
                      "before": round(before_mean, 4), "after": round(after_mean, 4),
                      "delta": round(after_mean - before_mean, 4)})
    before_n = _n_li(before_rows)
    after_n  = _n_li(after_rows)
    if after_n < before_n:
        flags.append({"code": "DELTA_N_LI_DROP", "before": before_n, "after": after_n,
                      "delta": after_n - before_n})
    return flags


def check_d04_score_changes(before_agents, after_agents):
    flags = []
    for agent, before_rows in before_agents.items():
        if agent not in after_agents:
            continue
        for b_row in before_rows:
            sid = b_row.get("session_id") or b_row.get("timestamp")
            if not sid:
                continue
            a_row = next(
                (r for r in after_agents[agent]
                 if (r.get("session_id") or r.get("timestamp")) == sid), None)
            if not a_row:
                continue
            for dim in CORE_6:
                b_val = b_row.get(dim)
                a_val = a_row.get(dim)
                if b_val is None or a_val is None:
                    continue
                try:
                    if abs(float(b_val) - float(a_val)) > D04_SCORE_CHANGE_THRESHOLD:
                        flags.append({"code": "DELTA_D04_SCORE_CHANGE", "agent": agent,
                                      "session_id": sid, "dimension": dim,
                                      "before": b_val, "after": a_val})
                except (ValueError, TypeError):
                    pass
    return flags


def run_delta(before_rows, after_rows, agent_filter=None):
    before_agents = _group_by_agent(before_rows)
    after_agents  = _group_by_agent(after_rows)
    if agent_filter:
        before_agents = {k: v for k, v in before_agents.items() if agent_filter.lower() in k.lower()}
        after_agents  = {k: v for k, v in after_agents.items() if agent_filter.lower() in k.lower()}
    regressions   = check_li_regressions(before_agents, after_agents)
    dcomp_changes = check_dcomp_changes(before_agents, after_agents)
    population    = check_population_changes(before_agents, after_agents)
    global_met    = check_global_metrics(before_rows, after_rows)
    d04_changes   = check_d04_score_changes(before_agents, after_agents)
    all_flags = regressions + dcomp_changes + population + global_met + d04_changes
    hard_flags = [f for f in all_flags if f["code"] in (
        "DELTA_LI_REGRESSION", "DELTA_DCOMP_LOST", "DELTA_MEAN_LI_DROP", "DELTA_D04_SCORE_CHANGE")]
    verdict = "FAIL" if hard_flags else ("WARN" if all_flags else "PASS")
    return {"result": verdict, "status": verdict, "tool": TOOL_NAME, "version": TOOL_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "before_rows": len(before_rows), "after_rows": len(after_rows),
            "before_agents": len(before_agents), "after_agents": len(after_agents),
            "total_flags": len(all_flags), "hard_flags": hard_flags, "all_flags": all_flags,
            "summaries": {"li_regressions": len(regressions), "dcomp_changes": len(dcomp_changes),
                          "population_changes": len(population),
                          "global_metric_changes": len(global_met),
                          "d04_score_changes": len(d04_changes)}}


def write_report(output, output_dir):
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / ("corpus_delta_" + ts + ".json")
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    if output["hard_flags"]:
        csv_path = p / ("corpus_delta_hard_" + ts + ".csv")
        keys = list(output["hard_flags"][0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(output["hard_flags"])
    return str(path)


def print_summary(output):
    b = "=" * 60
    print("")
    print(b)
    print(" Corpus Delta Analyzer - " + TOOL_VERSION)
    print(" Verdict: " + output["result"])
    print(" Rows: " + str(output["before_rows"]) + " -> " + str(output["after_rows"]) +
          "  Agents: " + str(output["before_agents"]) + " -> " + str(output["after_agents"]))
    print(b)
    s = output["summaries"]
    print("  LI regressions:     " + str(s["li_regressions"]))
    print("  D-COMP changes:     " + str(s["dcomp_changes"]))
    print("  Population changes: " + str(s["population_changes"]))
    print("  D-04 score changes: " + str(s["d04_score_changes"]))
    print("  Global metric chg:  " + str(s["global_metric_changes"]))
    if output["hard_flags"]:
        print("")
        print("  HARD FLAGS (" + str(len(output["hard_flags"])) + "):")
        for f in output["hard_flags"][:10]:
            agent_str = "  [" + f.get("agent", "") + "]" if f.get("agent") else ""
            print("  x " + f["code"] + agent_str)
    print("")
    print(b)
    print("")


def run_smoke_test():
    import io as _io
    def _make_corpus(rows):
        fields = ["agent_name", "session_id", "phase", "learning_index"] + CORE_6
        out = _io.StringIO()
        writer = csv.DictWriter(out, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue()
    before_data = [
        {"agent_name":"Claude","session_id":"S-01","phase":"Phase 3","learning_index":"0.92",
         "truth":"90","service":"88","harm":"91","autonomy":"89","value":"90","humility":"86"},
        {"agent_name":"GPT4","session_id":"S-02","phase":"Phase 3","learning_index":"0.85",
         "truth":"84","service":"84","harm":"85","autonomy":"85","value":"85","humility":"83"},
    ]
    after_data = [
        {"agent_name":"Claude","session_id":"S-01","phase":"Phase 3","learning_index":"0.80",
         "truth":"79","service":"79","harm":"80","autonomy":"80","value":"79","humility":"78"},
        {"agent_name":"NewAgent","session_id":"S-03","phase":"Phase 3","learning_index":"0.87",
         "truth":"86","service":"86","harm":"87","autonomy":"87","value":"86","humility":"85"},
    ]
    try:
        before_rows = list(csv.DictReader(_io.StringIO(_make_corpus(before_data))))
        after_rows  = list(csv.DictReader(_io.StringIO(_make_corpus(after_data))))
        output = run_delta(before_rows, after_rows)
        assert output["result"] in ("FAIL", "WARN"), "Expected FAIL/WARN"
        assert output["summaries"]["li_regressions"] >= 1
        assert output["summaries"]["population_changes"] >= 1
        print("checkmark Smoke test PASSED")
        return True
    except Exception as e:
        print("x Smoke test FAILED: " + str(e))
        return False


def main():
    parser = argparse.ArgumentParser(description="Corpus Delta Analyzer v1.0")
    parser.add_argument("--before", "-b")
    parser.add_argument("--after", "-a")
    parser.add_argument("--agent")
    parser.add_argument("--output", "-o", default="outputs/")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    if not args.before or not args.after:
        parser.print_help()
        sys.exit(1)
    try:
        before_rows = load_corpus(args.before)
        after_rows  = load_corpus(args.after)
    except SpecLoadFailed as e:
        print("SPEC_LOAD_FAILED: " + str(e), file=sys.stderr)
        sys.exit(2)
    output = run_delta(before_rows, after_rows, agent_filter=args.agent)
    rp = write_report(output, args.output)
    print_summary(output)
    print("Report: " + rp)
    sys.exit(0 if output["result"] == "PASS" else 1)


if __name__ == "__main__":
    main()

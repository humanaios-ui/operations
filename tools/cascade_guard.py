#!/usr/bin/env python3
"""cascade_guard.py — the witch-hunt failure mode as two executable invariants.

CASCADE-01  Runaway accusation: findings that spawn findings without an external
            check. Branching factor (child findings per parent, none externally
            reviewed) over window > threshold → CASCADE callout → freeze intake.
            Mirrors the chain-reaction hunts (Levack) and OI-G1 anti-cascade rules.
ELAB-01     Secondary elaboration (Evans-Pritchard): a hypothesis whose falsifier
            tripped and was then rescued by adding an exception. Exceptions added
            after a trip count; > max → the hypothesis is unfalsifiable → VOID.

Input: findings.jsonl rows
  {"id","parent":id|null,"external_review":bool,"ts"}
       hypotheses.jsonl rows
  {"id","falsifier_tripped":bool,"exceptions_added_after_trip":int}
Constants carry molt_id=null until Z2 ratifies. NO_GATE is never PASS.
Falsifier: --self-test plants one violation per invariant; a PASS on a plant = broken gate.
"""
import sys, json, os, argparse
from collections import defaultdict

CONSTANTS = {
  "CASCADE_branching_max": {"value": 1.5, "molt_id": None, "unit": "children/parent"},
  "CASCADE_window":        {"value": 10,  "molt_id": None, "unit": "findings"},
  "ELAB_exceptions_max":   {"value": 1,   "molt_id": None, "unit": "exceptions after trip"},
}

def read(p): return [json.loads(l) for l in open(p) if l.strip()] if p and os.path.exists(p) else []

def run(findings, hyps):
    R={}
    # CASCADE-01
    if not findings: R["CASCADE-01"]={"status":"NO_GATE","why":"no findings ledger"}
    else:
        W=CONSTANTS["CASCADE_window"]["value"]; win=findings[-W:]
        ids={f["id"] for f in win}
        parents=[f for f in win if any(c.get("parent")==f["id"] for c in win)]
        unreviewed_children=[c for c in win if c.get("parent") in ids and not c.get("external_review")]
        bf = len(unreviewed_children)/len(parents) if parents else 0.0
        bad = bf > CONSTANTS["CASCADE_branching_max"]["value"]
        R["CASCADE-01"]={"status":"FAIL" if bad else "PASS",
            "why":"CASCADE — findings spawning unreviewed findings; freeze intake" if bad else "branching within bound",
            "branching":round(bf,2),"parents":len(parents),"unreviewed_children":len(unreviewed_children)}
    # ELAB-01
    if not hyps: R["ELAB-01"]={"status":"NO_GATE","why":"no hypotheses ledger"}
    else:
        mx=CONSTANTS["ELAB_exceptions_max"]["value"]
        bad=[h["id"] for h in hyps if h.get("falsifier_tripped") and h.get("exceptions_added_after_trip",0)>mx]
        R["ELAB-01"]={"status":"FAIL" if bad else "PASS",
            "why":"secondary elaboration — falsifier rescued by exceptions → VOID" if bad else "no rescued falsifiers","void":bad}
    return R

def selftest():
    ok=True
    # plant CASCADE: 3 parents, 6 unreviewed children
    f=[{"id":f"p{i}","parent":None,"external_review":True} for i in range(3)]
    f+=[{"id":f"c{i}","parent":f"p{i%3}","external_review":False} for i in range(6)]
    r=run(f,[]); c=r["CASCADE-01"]["status"]=="FAIL"; print("CASCADE-01 plant →",r["CASCADE-01"]["status"],"OK" if c else "BROKEN"); ok&=c
    # plant ELAB: falsifier tripped, 2 exceptions after
    r=run([],[{"id":"H1","falsifier_tripped":True,"exceptions_added_after_trip":2}]); c=r["ELAB-01"]["status"]=="FAIL"; print("ELAB-01 plant →",r["ELAB-01"]["status"],"OK" if c else "BROKEN"); ok&=c
    # clean: children reviewed; hypothesis with tripped falsifier and 0 exceptions (honest failure)
    f=[{"id":"p0","parent":None,"external_review":True},{"id":"c0","parent":"p0","external_review":True}]
    r=run(f,[{"id":"H2","falsifier_tripped":True,"exceptions_added_after_trip":0}]); print("clean →",{k:v["status"] for k,v in r.items()}); ok&=all(v["status"]=="PASS" for v in r.values())
    print("SELF-TEST","PASS" if ok else "FAIL"); return 0 if ok else 2

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--findings"); ap.add_argument("--hypotheses"); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test: return selftest()
    R=run(read(a.findings),read(a.hypotheses))
    v="FAIL" if any(x["status"]=="FAIL" for x in R.values()) else ("NO_GATE" if any(x["status"]=="NO_GATE" for x in R.values()) else "PASS")
    print(json.dumps({"gate":"CASCADE-01/ELAB-01","constants":CONSTANTS,"results":R,"verdict":v},indent=1)); return 0 if v=="PASS" else 2
if __name__=="__main__": sys.exit(main())

#!/usr/bin/env python3
"""molt_cycle.py — READ + PROPOSE phases only (Tier 0). Never applies.

Reads ledgers, never memory. For each constant whose signal crossed its
trigger, emits one MOLT_CANDIDATE to stdout and appends it to molt_events.jsonl
(hash-chained). If no trigger crosses, says so — that is a real result.

Anti-cascade (OI-G1): K open molts max (default 3); one open molt per constant;
a constant reverted twice in a row is frozen; no candidate may be built from
events inside its own window.

Falsifier for the loop itself: after N=10 molts, if neither Brier on molt
predictions nor REVERT rate has fallen, the loop is noise and must freeze.
"""
import sys, json, hashlib, os, glob, statistics as st, argparse
from datetime import datetime, timezone

def sha256(s): return hashlib.sha256(s.encode()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()

def read_jsonl(path):
    if not os.path.exists(path): return []
    rows=[]
    for l in open(path):
        l=l.strip()
        if l:
            try: rows.append(json.loads(l))
            except: pass
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--registered", default="REGISTERED.md")
    ap.add_argument("--nf", default="NF_LEDGER.jsonl")
    ap.add_argument("--events", default="*.jsonl")
    ap.add_argument("--constants", default="constants.json")
    ap.add_argument("--molt-ledger", default="molt_events.jsonl")
    ap.add_argument("--K", type=int, default=3)
    ap.add_argument("--read-only", action="store_true", help="do not append to molt ledger")
    a=ap.parse_args()
    os.chdir(a.repo)

    # IC-030: the registry must be present and pinned before any registry-adjacent read
    if not os.path.exists(a.registered):
        print(json.dumps({"verdict":"HALT","reason":"IC-030: REGISTERED.md not present — no read from memory"})); return 2
    reg_sha=sha256(open(a.registered,encoding="utf-8",errors="replace").read())

    nf=read_jsonl(a.nf)
    molts=read_jsonl(a.molt_ledger)
    consts=json.load(open(a.constants)) if os.path.exists(a.constants) else {}
    ev=[r for p in glob.glob(a.events) if p not in (a.nf,a.molt_ledger) for r in read_jsonl(p)]

    # --- READ: signals per constant, from ledgers only ---
    # Join PIN and RESOLVE events: for each token_id, find latest RESOLVE with scoreable PIN
    pins={}; resolves={}; dates={}
    for row in nf:
        t=row.get("type")
        if t=="PIN": pins[row.get("pin_id")]=row
        elif t=="RESOLVE": resolves.setdefault(row.get("token_id"),[]).append(row)
        elif t=="DATE": dates[row.get("token_id")]=row
        elif t=="STRIKE":
            # Apply correction: retract the prior resolve
            tid=row.get("token_id")
            if tid in resolves and resolves[tid]:
                resolves[tid][-1]["_struck"]=True

    resolved=[]
    for pin_id,pin in pins.items():
        tid=pin.get("token_id")
        if tid not in dates: continue  # No DATE event → VOID
        if not pin.get("scoreable"): continue  # Not scoreable
        if tid not in resolves or not resolves[tid]: continue  # No RESOLVE
        res_list=resolves[tid]
        res=res_list[-1]  # Latest RESOLVE
        if res.get("_struck"): continue  # Struck out by STRIKE
        # Found a resolved, scoreable forecast
        outcome_str=res.get("outcome","")
        if outcome_str not in ("YES","NO"): continue
        outcome_float=1.0 if outcome_str=="YES" else 0.0
        resolved.append({
            "pin_id": pin_id,
            "token_id": tid,
            "predictor": pin.get("predictor"),
            "p": pin.get("p"),
            "outcome": outcome_str,
            "outcome_float": outcome_float
        })

    brier=(st.mean((float(r["p"])-r["outcome_float"])**2 for r in resolved) if resolved else None)
    open_molts=[m for m in molts if m.get("event")=="MOLT" and not any(
        x.get("molt_id")==m.get("molt_id") and x.get("event") in ("KEEP","REVERT") for x in molts)]
    reverts={}
    for m in molts:
        if m.get("event") in ("KEEP","REVERT"):
            c=m.get("constant"); reverts.setdefault(c,[]).append(m["event"])
    frozen=[c for c,h in reverts.items() if h[-2:]==["REVERT","REVERT"]]

    # loop-level falsifier
    molt_preds=[r for r in resolved if str(r.get("id","")).startswith("MOLT")]
    loop_note=None
    if len(molt_preds)>=10:
        a_,b_=molt_preds[:5],molt_preds[-5:]
        bA=st.mean((float(r["p"])-float(bool(r["outcome"])))**2 for r in a_)
        bB=st.mean((float(r["p"])-float(bool(r["outcome"])))**2 for r in b_)
        if bB>=bA: loop_note="LOOP FALSIFIER TRIPPED: Brier not falling after 10 molts — freeze pending Z2"

    # --- PROPOSE: only if a trigger crosses ---
    candidates=[]
    for name,c in consts.items():
        if name in frozen: continue
        if any(m.get("constant")==name for m in open_molts): continue
        if len(open_molts)+len(candidates)>=a.K: break
        trig=c.get("trigger")          # e.g. {"metric":"brier","above":0.25}
        if not trig: continue
        val={"brier":brier}.get(trig.get("metric"))
        if val is None: continue
        if ("above" in trig and val>trig["above"]) or ("below" in trig and val<trig["below"]):
            candidates.append({"event":"MOLT_CANDIDATE","ts":now(),"constant":name,
                "current":c.get("value"),"proposed":c.get("proposed_next"),
                "metric":trig["metric"],"observed":val,
                "prediction":c.get("prediction","<Z2 to state>"),
                "falsifier":c.get("falsifier","<Z2 to state>"),
                "window":c.get("window","14d"),"revert_rule":"mechanical: falsifier tripped → last ratified value",
                "registered_sha":reg_sha[:16],"ratification_hash":None})

    out={"phase":"READ+PROPOSE","tier":0,"registered_sha":reg_sha[:16],
         "nf_rows":len(nf),"nf_resolved":len(resolved),"brier":brier,
         "event_rows":len(ev),"constants":len(consts),"open_molts":len(open_molts),
         "frozen":frozen,"candidates":candidates,
         "verdict":("CANDIDATES" if candidates else "NO TRIGGER CROSSED"),"note":loop_note}
    print(json.dumps(out,indent=1))

    if candidates and not a.read_only:
        prev=molts[-1]["hash"] if molts and "hash" in molts[-1] else "0"*64
        with open(a.molt_ledger,"a") as f:
            for cnd in candidates:
                cnd["prev"]=prev; cnd["hash"]=sha256(prev+json.dumps(cnd,sort_keys=True)); prev=cnd["hash"]
                f.write(json.dumps(cnd)+"\n")
    return 0

if __name__=="__main__": sys.exit(main())

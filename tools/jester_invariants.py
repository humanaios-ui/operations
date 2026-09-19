#!/usr/bin/env python3
"""jester_invariants.py — JESTER-01..07 as executable invariants over the
adversarial-review ledger (external-check component of HumanAIOS).

Input: a JSONL ledger of critic reviews. One row per review:
  {"review_id","artifact_id","author_substrate","critic_substrate",
   "critic_saw_conclusion": bool,           # J-01
   "author_points": [...], "critic_points": [...],   # J-04 novelty
   "catches": int, "planted": int,          # J-03 / J-06 catch-rate
   "agreement": bool,                       # J-03
   "critic_text": "...",                    # J-05 imperative scan
   "ts": iso}
Optional: --artifacts artifacts.jsonl  rows {"artifact_id","state"} for J-07.

Each invariant returns PASS | FAIL | NO_GATE. NO_GATE is never PASS.
Exit 0 only if no FAIL. Constants below carry molt_id=null until Z2 ratifies.

Falsifier: a ledger with a planted violation of invariant k that returns PASS on k
means invariant k is broken. --self-test plants one per invariant.
"""
import sys, json, re, os, argparse, tempfile
from collections import defaultdict

CONSTANTS = {
  "J04_novelty_min":   {"value": 0.30, "molt_id": None, "unit": "ratio"},
  "J04_window":        {"value": 5,    "molt_id": None, "unit": "reviews"},
  "J03_agree_max":     {"value": 0.90, "molt_id": None, "unit": "ratio"},
  "J06_noise_catch":   {"value": 0.10, "molt_id": None, "unit": "ratio"},
  "J06_window":        {"value": 10,   "molt_id": None, "unit": "reviews"},
}
IMPERATIVE = re.compile(r"\b(you must|you should|you need to|revoke|delete|do not|don't|stop|immediately)\b", re.I)

def norm(s): return re.sub(r"\W+"," ",s.lower()).strip()

def read(path):
    if not path or not os.path.exists(path): return []
    return [json.loads(l) for l in open(path) if l.strip()]

def run(reviews, artifacts):
    R = {}
    def res(k, status, why, **kw): R[k] = {"status":status,"why":why, **kw}
    if not reviews:
        for k in ("JESTER-01","JESTER-02","JESTER-03","JESTER-04","JESTER-05","JESTER-06"):
            res(k,"NO_GATE","no reviews in ledger")
    else:
        # J-01 blind review: critic never sees the author's conclusion
        bad=[r["review_id"] for r in reviews if r.get("critic_saw_conclusion")]
        res("JESTER-01","FAIL" if bad else "PASS", "critic saw conclusion" if bad else "all reviews blind", violators=bad)

        # J-02 substrate independence
        bad=[r["review_id"] for r in reviews if r.get("critic_substrate")==r.get("author_substrate") or not r.get("critic_substrate")]
        res("JESTER-02","FAIL" if bad else "PASS", "critic == author substrate (or unnamed)" if bad else "independent", violators=bad)

        # J-03 stake removal: standing is catch-rate, never agreement-rate
        by=defaultdict(list)
        for r in reviews: by[r.get("critic_substrate")].append(r)
        bad=[]
        for c,rs in by.items():
            agree=sum(1 for r in rs if r.get("agreement"))/len(rs)
            if len(rs)>=3 and agree>CONSTANTS["J03_agree_max"]["value"]: bad.append({"critic":c,"agreement_rate":round(agree,2)})
        res("JESTER-03","FAIL" if bad else "PASS", "critic agrees at sycophancy rate" if bad else "no critic above agree_max", violators=bad)

        # J-04 ritual-dissent detector: novelty ratio over window
        W=CONSTANTS["J04_window"]["value"]; mn=CONSTANTS["J04_novelty_min"]["value"]
        bad=[]; ratios={}
        for c,rs in by.items():
            win=rs[-W:]
            nov=tot=0
            for r in win:
                a={norm(p) for p in r.get("author_points",[])}
                for p in r.get("critic_points",[]):
                    tot+=1; nov+= norm(p) not in a
            ratio = nov/tot if tot else None
            ratios[c]=ratio
            if len(win)>=W and ratio is not None and ratio<mn: bad.append({"critic":c,"novelty":round(ratio,2)})
        res("JESTER-04","FAIL" if bad else ("PASS" if any(v is not None for v in ratios.values()) else "NO_GATE"),
            "DRIFT:RITUAL — critic restates the author" if bad else "novelty above floor", ratios=ratios, violators=bad)

        # J-05 license holds: critic output is navigator grammar; imperatives are IC-067 drift
        bad=[r["review_id"] for r in reviews if IMPERATIVE.search(r.get("critic_text",""))]
        res("JESTER-05","FAIL" if bad else "PASS", "imperative from critic (IC-067)" if bad else "navigator grammar", violators=bad)

        # J-06 mechanical revocation: catch-rate at noise over window → rotate
        W=CONSTANTS["J06_window"]["value"]; nz=CONSTANTS["J06_noise_catch"]["value"]
        bad=[]
        for c,rs in by.items():
            win=[r for r in rs if r.get("planted")][-W:]
            if len(win)>=W:
                cr=sum(r.get("catches",0) for r in win)/max(1,sum(r["planted"] for r in win))
                if cr<=nz: bad.append({"critic":c,"catch_rate":round(cr,2),"action":"ROTATE"})
        res("JESTER-06","FAIL" if bad else "PASS", "critic at noise — rotate (Armstrong rule)" if bad else "catch-rate above noise", violators=bad)

    # J-07 the check cannot be skipped: every KEEP artifact has ≥1 review; absence is NO_GATE, never PASS
    if not artifacts:
        res("JESTER-07","NO_GATE","no artifacts file — cannot prove the check ran")
    else:
        reviewed={r["artifact_id"] for r in reviews}
        bad=[a["artifact_id"] for a in artifacts if a.get("state")=="KEEP" and a["artifact_id"] not in reviewed]
        res("JESTER-07","FAIL" if bad else "PASS", "KEEP without external check" if bad else "every KEEP was checked", violators=bad)
    return R

def selftest():
    base=dict(author_substrate="claude",critic_substrate="grok",critic_saw_conclusion=False,
              author_points=["a","b"],critic_points=["c","d"],catches=2,planted=2,agreement=False,
              critic_text="Position: two gaps. Probability of catch 0.7.")
    mk=lambda i,**kw: {**base,"review_id":f"r{i}","artifact_id":f"art{i}","ts":"t",**kw}
    plants={
      "JESTER-01":[mk(1,critic_saw_conclusion=True)],
      "JESTER-02":[mk(1,critic_substrate="claude")],
      "JESTER-03":[mk(i,agreement=True) for i in range(3)],
      "JESTER-04":[mk(i,critic_points=["a","b"]) for i in range(5)],
      "JESTER-05":[mk(1,critic_text="You must revoke the key immediately.")],
      "JESTER-06":[mk(i,catches=0,planted=3) for i in range(10)],
      "JESTER-07":[mk(1)],
    }
    ok=True
    for k,rows in plants.items():
        arts=[{"artifact_id":"art1","state":"KEEP"},{"artifact_id":"art9","state":"KEEP"}] if k=="JESTER-07" else [{"artifact_id":r["artifact_id"],"state":"KEEP"} for r in rows]
        R=run(rows,arts)
        caught=R[k]["status"]=="FAIL"
        others=[j for j,v in R.items() if j!=k and v["status"]=="FAIL"]
        print(f"{k}: planted violation → {R[k]['status']}  {'OK' if caught else 'BROKEN'}" + (f"  (side-fails: {others})" if others else ""))
        ok &= caught
    clean=[mk(i) for i in range(10)]
    R=run(clean,[{"artifact_id":r["artifact_id"],"state":"KEEP"} for r in clean])
    print("clean ledger:", {k:v["status"] for k,v in R.items()})
    ok &= all(v["status"]=="PASS" for v in R.values())
    print("SELF-TEST", "PASS" if ok else "FAIL"); return 0 if ok else 2

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("reviews",nargs="?")
    ap.add_argument("--artifacts")
    ap.add_argument("--self-test",action="store_true")
    a=ap.parse_args()
    if a.self_test: return selftest()
    R=run(read(a.reviews),read(a.artifacts))
    out={"gate":"JESTER-01..07","constants":CONSTANTS,"results":R,
         "verdict":"FAIL" if any(v["status"]=="FAIL" for v in R.values()) else
                   ("NO_GATE" if any(v["status"]=="NO_GATE" for v in R.values()) else "PASS")}
    print(json.dumps(out,indent=1)); return 0 if out["verdict"]=="PASS" else 2

if __name__=="__main__": sys.exit(main())

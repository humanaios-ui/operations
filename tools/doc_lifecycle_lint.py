#!/usr/bin/env python3
"""doc_lifecycle_lint.py — Filing / Processing / Consumption / Production (FPCP) for docs/.

A document is not useful because it exists. It is useful when something consumes it.
Stages (front matter `lifecycle:`):
  filed      landed, no consumer named yet                       ← default for the Sep 6 bulk import
  processing being converted: rules → code, claims → registry, config → its tool
  consumed   a tool, workflow, registry line, or another doc reads it (inbound ref ≠ 0 or `consumer:` resolves)
  produced   generated FROM code or the record (reports, renders); regenerable, never edited by hand
  archived   moved to docs/_archive/; hash kept; nothing may delete it (append-only)

Rules in code:
  * every file under docs/ (not _archive, not _templates) gets a disposition; NONE is not a disposition
  * a doc with inbound refs, or whose `consumer:` path exists, is CONSUMED — cannot be archived
  * a doc carrying rule signal (thresholds, yaml, gates, signal tables) and no code twin → CODE candidate
  * a doc carrying registry signal (H-/F-/IC- blocks, falsifier lines) not in REGISTERED.md → REGISTRY candidate
  * session outputs, plans with a newer version, unreferenced analyses → ARCHIVE candidate
  * --enforce: exit 2 if any doc has been `filed` longer than STALE_DAYS with no disposition ruling
  * --self-test plants one file per disposition and checks each lands where it should
"""
import os, re, sys, json, subprocess, argparse, datetime
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DOCS=os.path.join(ROOT,"docs")
STALE_DAYS=14
RULE=re.compile(r"(threshold|\bgate\b|\bsignal\b|trigger|\brule\b|\bcap\b|half-life|\bweight|\bp\s*[<>=]|\d\.\d{2}\b|^[a-z_]+:\s*[\d\.]+\s*$)",re.I|re.M)
REGSIG=re.compile(r"^\s*(H-|F-|IC-|GAP-|H-CAND-)[A-Z0-9\-]+",re.M)
FALS=re.compile(r"falsifier|would prove (it|this) wrong|disproof",re.I)
SESSION=re.compile(r"SESSION_OUTPUTS|_S-?\d{6}|S0\d{5}|SUMMARY\.txt|pub_queue|ground_truth\.json|claim_report\.json",re.I)
SUPERSEDED=re.compile(r"supersed|formerly|renamed|ARCHIVED|_V1_0\.md$|_V1\.1\.md$",re.I)

def sh(c): return subprocess.run(c,shell=True,cwd=ROOT,capture_output=True,text=True).stdout
def front(txt):
    m=re.match(r"^---\n(.*?)\n---",txt,re.S)
    if not m: return {}
    return {k.strip():v.strip().strip('"') for k,v in (l.split(":",1) for l in m.group(1).splitlines() if ":" in l)}
def inbound(rel):
    base=os.path.basename(rel)
    out=sh(f"git grep -l -F '{base}' -- . ':!docs/' ':!tools/doc_lifecycle_lint.py' 2>/dev/null")
    return [l for l in out.split("\n") if l.strip()]
def registered(rel):
    reg=open(os.path.join(ROOT,"document-registry.yaml")).read() if os.path.exists(os.path.join(ROOT,"document-registry.yaml")) else ""
    return rel in reg
def in_registered_md(txt):
    ids=set(REGSIG.findall(txt)); reg=open(os.path.join(ROOT,"REGISTERED.md")).read() if os.path.exists(os.path.join(ROOT,"REGISTERED.md")) else ""
    return bool(ids) and all(i in reg for i in ids)

def classify(rel,txt,refs):
    fm=front(txt); lc=fm.get("lifecycle"); cons=fm.get("consumer")
    if lc=="archived" or rel.startswith("docs/_archive/"): return "ARCHIVED",lc,"already archived"
    if lc=="produced": return "PRODUCED",lc,"generated artifact; regenerate, do not edit"
    if refs or (cons and os.path.exists(os.path.join(ROOT,cons))) or registered(rel):
        why="inbound: "+", ".join(refs[:3]) if refs else ("consumer: "+cons if cons else "in document-registry.yaml")
        return "CONSUMED",lc,why
    ext=os.path.splitext(rel)[1].lower()
    if ext in (".yaml",".yml",".json"): return "CODE",lc,"structured config with no consumer — belongs beside the tool that reads it, or is dead"
    rule=len(RULE.findall(txt)); reg=REGSIG.findall(txt); fals=bool(FALS.search(txt))
    if reg and not in_registered_md(txt): return "REGISTRY",lc,f"{len(set(reg))} registry ids not in REGISTERED.md" + (" · has falsifier" if fals else " · NO falsifier (falsifier_lint will refuse)")
    if SESSION.search(rel) or SESSION.search(txt[:300]): return "ARCHIVE",lc,"session output / snapshot; value already in the record or nowhere"
    if SUPERSEDED.search(rel) or SUPERSEDED.search(txt[:600]): return "ARCHIVE",lc,"superseded or renamed; keep hash, retire text"
    if rule>=8 and "|" in txt: return "CODE",lc,f"{rule} rule signals in tables; enforcement is in prose"
    if ext==".html": return "PRODUCED?",lc,"render with no generator on record — either find the generator or archive"
    return "ARCHIVE?",lc,f"unreferenced analysis · {rule} rule signals · no registry ids" if rule<8 else "review"

def scan(docs=DOCS):
    rows=[]
    for dp,_,fs in os.walk(docs):
        if "_templates" in dp: continue
        for f in fs:
            p=os.path.join(dp,f); rel=os.path.relpath(p,ROOT).replace("\\","/")
            try: txt=open(p,errors="replace").read()
            except Exception: txt=""
            d,lc,why=classify(rel,txt,inbound(rel))
            rows.append({"path":rel,"lines":txt.count("\n"),"lifecycle":lc or "filed(implicit)","disposition":d,"why":why})
    return rows

def report(rows):
    order=["CONSUMED","CODE","REGISTRY","PRODUCED","PRODUCED?","ARCHIVE","ARCHIVE?","ARCHIVED"]
    counts={k:sum(r["disposition"]==k for r in rows) for k in order}
    out=["# docs/ triage — generated by tools/doc_lifecycle_lint.py "+datetime.date.today().isoformat(),"",
         "| disposition | n |","|---|---|"]+[f"| {k} | {v} |" for k,v in counts.items() if v]+["",
         "| path | lines | stage | disposition | why |","|---|---|---|---|---|"]
    for r in sorted(rows,key=lambda r:(order.index(r["disposition"]),r["path"])):
        out.append(f"| {r['path']} | {r['lines']} | {r['lifecycle']} | **{r['disposition']}** | {r['why']} |")
    return "\n".join(out)+"\n"

def selftest():
    import tempfile,shutil
    global DOCS,ROOT; ok=True
    tmp=tempfile.mkdtemp(); d=os.path.join(tmp,"docs"); os.makedirs(d); os.makedirs(os.path.join(tmp,"tools"))
    open(os.path.join(tmp,"REGISTERED.md"),"w").write("F-001 known\n"); open(os.path.join(tmp,"tools","x.py"),"w").write("# reads docs/cfg.yaml\n")
    open(os.path.join(d,"rules.md"),"w").write("# gates\n| signal | threshold | trigger |\n|---|---|---|\n"+"| drift | 0.30 | rule cap weight gate |\n"*4)
    open(os.path.join(d,"cand.md"),"w").write("H-CAND-X-01 claim\nfalsifier: none observed\n")
    open(os.path.join(d,"SESSION_OUTPUTS_S-060926.md"),"w").write("session notes\n")
    open(os.path.join(d,"cfg.yaml"),"w").write("a: 1\n"); open(os.path.join(d,"orphan.yaml"),"w").write("b: 2\n")
    open(os.path.join(d,"gen.html"),"w").write("---\nlifecycle: produced\n---\n<html/>")
    open(os.path.join(d,"used.md"),"w").write("---\nconsumer: tools/x.py\n---\ntext")
    ROOT,DOCS=tmp,d; subprocess.run("git init -q && git add -A && git -c user.name=t -c user.email=t@t commit -qm t",shell=True,cwd=tmp)
    got={os.path.basename(r["path"]):r["disposition"] for r in scan(d)}
    exp={"rules.md":"CODE","cand.md":"REGISTRY","SESSION_OUTPUTS_S-060926.md":"ARCHIVE","cfg.yaml":"CONSUMED","orphan.yaml":"CODE","gen.html":"PRODUCED","used.md":"CONSUMED"}
    for k,v in exp.items(): print(f"{k:32s} → {got.get(k)}  {'OK' if got.get(k)==v else 'BROKEN (want '+v+')'}"); ok&=got.get(k)==v
    shutil.rmtree(tmp); print("SELF-TEST","PASS" if ok else "FAIL"); return 0 if ok else 2

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--self-test",action="store_true"); ap.add_argument("--enforce",action="store_true"); ap.add_argument("--json",action="store_true"); a=ap.parse_args()
    if a.self_test: sys.exit(selftest())
    rows=scan()
    if a.json: print(json.dumps(rows,indent=1)); sys.exit(0)
    print(report(rows))
    if a.enforce:
        bad=[r for r in rows if r["disposition"] in ("ARCHIVE?","PRODUCED?") and r["lifecycle"]=="filed(implicit)"]
        if bad: print(f"ENFORCE: {len(bad)} docs filed with no disposition ruling",file=sys.stderr); sys.exit(2)

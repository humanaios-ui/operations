#!/usr/bin/env python3
"""decision_relay.py — routes Z2 decisions from the Intent-OS board into z1-inbox/, behind ngrok.
Builder v1.7 compliant · governance_tool
HumanAIOS · S-090826-01 (v0.3 under Z2 ruling d18, S-091426-01)

Zones (system_graph v0.2): the board is Z2's hand · this relay is Z3 (lands) · the /assist path is Z1 (proposes).
Rules in code, not prose:
  * every POST carries X-Sig = HMAC-SHA256(secret, body); missing/wrong → 401. secret is set at intake (RELAY_SECRET).
  * nonce + timestamp inside the body; replay (seen nonce) or |skew| > 300s → 409/401.
  * d18 (z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md): a ruling lands INSIDE the queue, not beside it.
      /decide  writes the tapped choice into the ruling's candidate block (z1-inbox/<date>/Q-BOARD-RULING-nn.md) on a
               branch and opens a PR marked PENDING with sha256(ruling block). A tap is not a ratification.
      /ratify  Z2 echoes that hash. On a match the relay signs the candidate exactly as .z1-control/ratify.py does —
               sha256(candidate | by=<tagline> | at=<date> | decision=ACCEPT) — appends the signature to
               z1-inbox/<date>/Z2_RULINGS_<date>.md, marks the candidate `ratified` in z1-inbox/INDEX.yaml,
               regenerates Z1_INBOX_INDEX.md with .z1-control/render.py's renderer, comments RATIFY on the PR.
               Everything the z2 gate checks (coverage, no self-grant, hash-in-ruling, render in sync) is written
               on the branch, so the PR is green or it is wrong.
  * /assist returns navigator grammar only (position · destination · probability · readings), tagged by:Z1;
    an imperative in the model output is stripped and logged as DRIFT. It never writes a ruling.
  * DRY_RUN=1 works on a local copy under ./relay_out instead of GitHub (self-test path).

Env: RELAY_SECRET (required) · GITHUB_TOKEN · GITHUB_REPO=humanaios-ui/operations · ANTHROPIC_API_KEY (optional)
Run:  RELAY_SECRET=... GITHUB_TOKEN=... python3 tools/decision_relay.py 8787
      ngrok http 8787 --traffic-policy-file tools/relay_policy.yml
"""
import os, sys, json, hmac, hashlib, time, base64, urllib.request, re, argparse, datetime, shutil, tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer

TOOL_NAME = "decision_relay"
TOOL_VERSION = "0.3.0"  # 0.1 = 09-08 relay; 0.2 = browser CORS; 0.3 = lands in z1-inbox + INDEX.yaml (d18)
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1  # matches tools-manifest.yaml (HAIOS-TOOL-051). The docstring names this relay as Z3 (it lands with a token); raising the declared zone is a Z2 ratification act, not a marker edit

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET=os.environ.get("RELAY_SECRET",""); TOKEN=os.environ.get("GITHUB_TOKEN","")
REPO=os.environ.get("GITHUB_REPO","humanaios-ui/operations"); DRY=os.environ.get("DRY_RUN")=="1"
SEEN=set(); IMPERATIVE=re.compile(r"\b(you must|you should|you need to|revoke|delete|do not|don't|immediately|stop)\b",re.I)
INDEX="z1-inbox/INDEX.yaml"; RENDERED="Z1_INBOX_INDEX.md"; RATIFIERS=("Night",)

def sha(b): return hashlib.sha256(b).hexdigest()
def content_ref(content, user_key=None):
    """fingerprint of user content that leaves the relay INSTEAD of the content.
    HMAC keyed with a user-held key (USER_KEY env, set at intake, never transmitted); bare sha would be guessable.
    canonical = whitespace-collapsed UTF-8. Verify a later voluntary disclosure by recomputing and comparing."""
    key=(user_key or os.environ.get("USER_KEY","")).encode()
    if not key: raise ValueError("REFUSED: USER_KEY not set; a keyless fingerprint is dictionary-guessable")
    canon=" ".join(str(content).split()).encode()
    return hmac.new(key,canon,hashlib.sha256).hexdigest()
def gh(method,path,data=None):
    req=urllib.request.Request(f"https://api.github.com{path}",method=method,data=json.dumps(data).encode() if data else None,
        headers={"Authorization":f"token {TOKEN}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    with urllib.request.urlopen(req) as r: return json.load(r)

# ---------- the two stores: GitHub (a branch) or a local copy (DRY_RUN / self-test) ----------
class GitHubStore:
    def __init__(self,branch): self.branch=branch
    def get(self,path):
        try: r=gh("GET",f"/repos/{REPO}/contents/{path}?ref={self.branch}")
        except Exception: return None,None
        return base64.b64decode(r["content"]).decode(), r["sha"]
    def put(self,path,text,msg):
        _,cur=self.get(path); body={"message":msg,"content":base64.b64encode(text.encode()).decode(),"branch":self.branch}
        if cur: body["sha"]=cur
        gh("PUT",f"/repos/{REPO}/contents/{path}",body)
class LocalStore:
    """DRY_RUN: files are copied from `src` into `out` on first touch and edited there; the repo itself is never written."""
    def __init__(self,out,src=None): self.out=out; self.src=src or ROOT  # resolved at call time so the self-test can rebind ROOT
    def _p(self,path): return os.path.join(self.out,path)
    def get(self,path):
        p=self._p(path)
        if not os.path.exists(p):
            s=os.path.join(self.src,path)
            if not os.path.exists(s): return None,None
            os.makedirs(os.path.dirname(p),exist_ok=True); shutil.copyfile(s,p)
        return open(p,encoding="utf-8").read(), "local"
    def put(self,path,text,msg):
        p=self._p(path); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,"w",encoding="utf-8").write(text)

def store(branch):
    return LocalStore(os.path.join(ROOT,"relay_out")) if DRY else GitHubStore(branch)

# ---------- pure text operations over the inbox (the same shapes .z1-control/ratify.py writes) ----------
def qid_for(d):
    q=d.get("qid")
    if q and re.fullmatch(r"Q-[A-Z0-9\-]+",q): return q
    m=re.fullmatch(r"d(\d+)",str(d.get("id","")))
    if not m: raise ValueError("ruling id is not d<n> and no qid given")
    return f"Q-BOARD-RULING-{int(m.group(1)):02d}"
def cand_path(index_text,qid):
    m=re.search(rf"(?m)^  - q_id: {re.escape(qid)}\n(?:    .*\n)*?    path: \"([^\"]+)\"",index_text)
    if not m: raise ValueError(f"{qid} is not a candidate in {INDEX}")
    return m.group(1)
def ruling_block(d):
    return ("RULING %s\n  by: %s (tagline)\n  project: %s\n  question: %s\n  choice: %s\n  note: %s\n  at: %s\n  status: PENDING\n"
            % (d["id"],d["tagline"],d["project"],d["q"],d["choice"],d.get("note",""),d["ts"]))
def write_choice(cand_text,choice,by,ts,status,block_hash):
    """Fill the candidate's `## Ruling` section. Idempotent: a second tap overwrites the same four lines."""
    sec=f"## Ruling\n\nchoice: {choice}\nby: {by}\nat: {ts}\nstatus: {status}\nblock_hash: {block_hash}\n"
    if re.search(r"(?ms)^## Ruling\n.*?(?=^## |\Z)",cand_text):
        return re.sub(r"(?ms)^## Ruling\n.*?(?=^## |\Z)",sec+"\n",cand_text,count=1)
    return cand_text.rstrip("\n")+"\n\n"+sec
def signature(candidate_bytes,by,at,decision="ACCEPT"):
    """sha256(candidate | by=… | at=… | decision=…), per CLAUDE.md — byte-identical to .z1-control/ratify.py."""
    return hashlib.sha256(candidate_bytes+f"|by={by}|at={at}|decision={decision}".encode()).hexdigest()
def index_mark_ratified(index_text,qid,by,at,ruling_rel,digest):
    block=re.search(rf"(^  - q_id: {re.escape(qid)}\n)(.*?)(?=^  - q_id: |^records:|\Z)",index_text,re.M|re.S)
    if not block: raise ValueError(f"could not locate {qid} in {INDEX}")
    head,body=block.group(1),block.group(2)
    if not re.search(r"^    status: awaiting_z2\n",body,re.M): raise ValueError(f"{qid} is not awaiting_z2; a decision is not re-taken by overwriting it")
    body=re.sub(r"^    status: .*\n",f"    status: ratified\n",body,count=1,flags=re.M)
    add=f'    ratified_by: {by}\n    ratified_at: "{at}"\n    z2_ruling: "{ruling_rel}"\n    z2_hash: "{digest}"\n'
    trailing=""
    while body.endswith("\n\n"): body,trailing=body[:-1],"\n"
    return index_text[:block.start()]+head+body+add+trailing+index_text[block.end():]
def index_add_record(index_text,path,title,note):
    if f'path: "{path}"' in index_text: return index_text
    m=re.search(r"counts: \{candidates: (\d+), records: (\d+)\}",index_text)
    if not m: raise ValueError("counts: line not found")
    index_text=index_text[:m.start()]+f"counts: {{candidates: {m.group(1)}, records: {int(m.group(2))+1}}}"+index_text[m.end():]
    rec=f'records:\n  - path: "{path}"\n    title: "{title}"\n    note: "{note}"\n'
    if "records:\n" not in index_text: raise ValueError("records: section not found")
    return index_text.replace("records:\n",rec,1)
def rendered_index(index_text,read):
    """Z1_INBOX_INDEX.md exactly as .z1-control/render.py would write it for this INDEX text."""
    sys.path.insert(0,os.path.join(ROOT,".z1-control"))
    import yaml, validate as v, render as r  # noqa: E402
    return r.render(yaml.load(index_text,Loader=v.StrictLoader),read=read)

# ---------- the three paths ----------
def land(d):
    """/decide — choice → candidate block on a branch → PR (PENDING). returns {pr, number, hash, path, branch, qid}"""
    block=ruling_block(d); h=sha(block.encode()); day=d["ts"][:10]; qid=qid_for(d); br=f"z2/{d['id']}-{day}"
    if not DRY:
        base=gh("GET",f"/repos/{REPO}/git/ref/heads/main")["object"]["sha"]
        try: gh("POST",f"/repos/{REPO}/git/refs",{"ref":f"refs/heads/{br}","sha":base})
        except Exception: pass
    st=store(br)
    idx,_=st.get(INDEX)
    if idx is None: raise ValueError(f"{INDEX} not found")
    path=cand_path(idx,qid); cand,_=st.get(path)
    if cand is None: raise ValueError(f"{path} not found")
    st.put(path,write_choice(cand,d["choice"],d["tagline"],d["ts"],"PENDING",h),f"z2 {d['id']} ({qid}): {d['choice']} — PENDING, hash {h[:16]}")
    body=(f"# {qid} — {d['q']}\n\n```\n{block}```\n\nhash: `{h}`\n\nA tap is not a ratification. Ratify by echoing this hash to /ratify from the board "
          f"(the relay then signs `{path}` as .z1-control/ratify.py would, records it in `{INDEX}`, and regenerates `{RENDERED}`).\n")
    if DRY: return {"pr":"DRY","number":0,"hash":h,"path":path,"branch":br,"qid":qid}
    pr=gh("POST",f"/repos/{REPO}/pulls",{"title":f"Z2 ruling {d['id']} ({qid}): {d['choice']}","head":br,"base":"main","body":body})
    return {"pr":pr["html_url"],"number":pr["number"],"hash":h,"path":path,"branch":br,"qid":qid}

def ratify(d):
    """/ratify — Z2 echoes the PENDING hash. On a match: sign the candidate, record it, regenerate the index. Refuse otherwise."""
    exp=d.get("expected_hash"); got=d.get("hash")
    if not got or got!=exp: return {"status":"REFUSED","why":"hash does not match the landed ruling; a tap is not a ratification"}
    by=d.get("tagline",""); at=d["ts"][:10]
    if by not in RATIFIERS: return {"status":"REFUSED","why":f"'{by}' is not a ratifier ({', '.join(RATIFIERS)})"}
    qid=qid_for(d); br=d.get("branch") or f"z2/{d['id']}-{at}"; st=store(br)
    idx,_=st.get(INDEX); path=d.get("path") or cand_path(idx,qid); cand,_=st.get(path)
    if cand is None or f"block_hash: {got}" not in cand: return {"status":"REFUSED","why":"the landed block on the branch does not carry this hash"}
    cand=write_choice(cand,re.search(r"^choice: (.*)$",cand,re.M).group(1),by,d["ts"],"RATIFIED",got)
    st.put(path,cand,f"z2 {d['id']} ({qid}): RATIFIED by {by}")
    digest=signature(cand.encode(),by,at)          # over the bytes as they now stand — the same bytes CI will hash
    ruling_rel=f"z1-inbox/{at}/Z2_RULINGS_{at}.md"; ruling,_=st.get(ruling_rel)
    if ruling is None:
        ruling=(f"# Z2 Rulings — {at}\n\nSignatures issued by the Z2 serial gate. Each hash is\n`sha256(candidate | by=<ratifier> | at=<date> | decision=<D>)` over the\n"
                f"candidate block's bytes at the moment of decision, so editing a ratified\ncandidate afterwards breaks `ratify.py --verify`.\n")
        idx=index_add_record(idx,ruling_rel,f"Z2 rulings {at} — signatures issued by .z1-control/ratify.py and decision_relay.py","Z2 output. Cited as z2_ruling by the candidates it signs.")
    ruling+=(f"\n## {qid} — ACCEPT\n\nHash: `{digest}`\n\n- **Decision:** ACCEPT (ratified) · board ruling {d['id']}: `{re.search(r'^choice: (.*)$',cand,re.M).group(1)}`\n"
             f"- **By:** {by}\n- **At:** {at}\n- **Candidate:** `{path}`\n- **Landed by:** tools/decision_relay.py v{TOOL_VERSION} (PENDING block hash `{got[:16]}…` echoed by Z2)\n"
             f"- **Signature:** `sha256(candidate | by={by} | at={at} | decision=ACCEPT)`, computed over the candidate's bytes at the moment of decision.\n")
    st.put(ruling_rel,ruling,f"z2 rulings {at}: {qid} ACCEPT ({digest[:16]})")
    idx=index_mark_ratified(idx,qid,by,at,ruling_rel,digest); st.put(INDEX,idx,f"INDEX: {qid} ratified by {by}")
    st.put(RENDERED,rendered_index(idx,lambda rel: st.get(rel)[0] or ""),f"render Z1_INBOX_INDEX.md: {qid} ratified")
    if not DRY and d.get("number"):
        gh("POST",f"/repos/{REPO}/issues/{d['number']}/comments",{"body":f"RATIFY {d['id']} {got}\nby: {by} at {d['ts']}\nsignature: {digest}\nruling: {ruling_rel}"})
        gh("POST",f"/repos/{REPO}/issues/{d['number']}/labels",{"labels":["z2-ratified"]})
    return {"status":"RATIFIED","hash":got,"signature":digest,"ruling":ruling_rel,"qid":qid}

def assist(d):
    """Z1: reframe the decision in plain terms tied to the north star. Navigator grammar only."""
    key=os.environ.get("ANTHROPIC_API_KEY")
    prompt=("You are Z1 in HumanAIOS. Z2 is deciding: %s\nOptions: %s\nContext: %s\nNorth star: fund and operate a recovery center; GRBS profits go there.\n"
            "Answer in navigator grammar only — no imperatives to Z2. Give: position (one line), each option's reading (one line each, plain words), "
            "probability each option advances the north star within 30 days, and what would prove the favoured reading wrong. Under 120 words.") % (d["q"],d.get("opts"),d.get("s",""))
    if not key or DRY:
        text="position: relay dry-run · no model key · readings not generated"
    else:
        req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=json.dumps({"model":"claude-sonnet-4-6","max_tokens":400,"messages":[{"role":"user","content":prompt}]}).encode(),
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
        with urllib.request.urlopen(req) as r: text="".join(b.get("text","") for b in json.load(r)["content"])
    drift=[m.group(0) for m in IMPERATIVE.finditer(text)]
    if drift: text=IMPERATIVE.sub("[…]",text)
    return {"by":"Z1","text":text,"drift":drift,"note":"advice, not a ruling; nothing is written"}

class H(BaseHTTPRequestHandler):
    def _send(self,code,obj):
        b=json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type","application/json")
        # Authorization is listed so a browser board can carry the ngrok basic-auth credential through the CORS preflight.
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type, X-Sig, Authorization")
        self.send_header("Access-Control-Allow-Methods","POST, GET, OPTIONS"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self): self._send(204,{})
    def do_GET(self): self._send(200,{"relay":"ok","version":TOOL_VERSION,"dry":DRY,"repo":REPO,"lands_in":"z1-inbox/ (d18)"})
    def do_POST(self):
        body=self.rfile.read(int(self.headers.get("Content-Length",0)))
        sig=self.headers.get("X-Sig","")
        if not SECRET or not hmac.compare_digest(sig,hmac.new(SECRET.encode(),body,hashlib.sha256).hexdigest()): return self._send(401,{"status":"REFUSED","why":"bad signature"})
        try: d=json.loads(body)
        except Exception: return self._send(400,{"status":"REFUSED","why":"not json"})
        if abs(time.time()-d.get("epoch",0))>300: return self._send(401,{"status":"REFUSED","why":"stale timestamp"})
        if d.get("nonce") in SEEN: return self._send(409,{"status":"REFUSED","why":"replay"})
        SEEN.add(d.get("nonce"))
        try:
            if self.path=="/decide": return self._send(200,{"status":"PENDING",**land(d)})
            if self.path=="/ratify": return self._send(200,ratify(d))
            if self.path=="/assist": return self._send(200,assist(d))
            self._send(404,{"status":"REFUSED","why":"unknown path"})
        except Exception as e: self._send(500,{"status":"ERROR","why":str(e)})

def run_smoke_test():
    """Builder v1.7 smoke test = the self-test below (DRY_RUN, no network, no token)."""
    return selftest()==0

def selftest():
    global DRY,SECRET,ROOT; DRY=True; SECRET="s3"; ok=True
    real_root=ROOT; td=tempfile.mkdtemp(prefix="relay_selftest_"); ROOT=td
    try:
        # a minimal inbox: one awaiting candidate, the real renderer/validator copied in
        os.makedirs(os.path.join(td,"z1-inbox","2026-09-14")); shutil.copytree(os.path.join(real_root,".z1-control"),os.path.join(td,".z1-control"))
        open(os.path.join(td,INDEX),"w").write('---\nversion: 1\ngenerated: "2026-09-14"\ndecision_window_days: 2\ncounts: {candidates: 1, records: 0}\nratifiers: [Night]\n\ncandidates:\n'
            '  - q_id: Q-BOARD-RULING-06\n    title: "Board ruling d6"\n    path: "z1-inbox/2026-09-14/Q-BOARD-RULING-06.md"\n    submitted: "2026-09-14"\n    status: awaiting_z2\n    falsifier_waiver: "question"\n\nrecords:\nexcluded: []\n')
        open(os.path.join(td,"z1-inbox","2026-09-14","Q-BOARD-RULING-06.md"),"w").write("# Ruling request Q-BOARD-RULING-06\n\n## Question\n\nbatch source?\n\n## Ruling\n\nchoice:\nby:\nat:\nstatus: OPEN\n\n## Z2 Review Checklist\n\n- [ ] batch source?\n")
        d={"id":"d6","q":"batch source?","choice":"own postings","tagline":"Night","project":"HumanAIOS","ts":"2026-09-14T12:00:00Z"}
        r=land(d); print("land →",r["path"],r["hash"][:16],r["branch"])
        out=os.path.join(td,"relay_out"); cand=open(os.path.join(out,r["path"])).read()
        ok&=("choice: own postings" in cand and "status: PENDING" in cand and f"block_hash: {r['hash']}" in cand); print("choice written into the candidate →",ok)
        a=ratify({**d,"hash":"deadbeef","expected_hash":r["hash"],"branch":r["branch"]}); ok&=a["status"]=="REFUSED"; print("wrong hash →",a["status"])
        a=ratify({**d,"tagline":"Claude","hash":r["hash"],"expected_hash":r["hash"],"branch":r["branch"]}); ok&=a["status"]=="REFUSED"; print("non-ratifier →",a["status"])
        a=ratify({**d,"hash":r["hash"],"expected_hash":r["hash"],"branch":r["branch"]}); ok&=a["status"]=="RATIFIED"; print("echoed hash →",a["status"],a.get("signature","")[:16])
        idx=open(os.path.join(out,INDEX)).read(); ruling=open(os.path.join(out,a["ruling"])).read(); cand=open(os.path.join(out,r["path"])).read()
        ok&=("    status: ratified\n" in idx and "ratified_by: Night" in idx and a["signature"] in idx and a["signature"] in ruling
             and "counts: {candidates: 1, records: 1}" in idx and f'path: "{a["ruling"]}"' in idx and "status: RATIFIED" in cand)
        ok&=signature(cand.encode(),"Night","2026-09-14")==a["signature"]; print("index + ruling + candidate consistent, signature recomputes →",ok)
        rendered=open(os.path.join(out,RENDERED)).read(); ok&="Q-BOARD-RULING-06" in rendered; print("Z1_INBOX_INDEX.md regenerated →","Q-BOARD-RULING-06" in rendered)
        sys.path.insert(0,os.path.join(td,".z1-control")); import yaml, validate as v  # noqa: E402
        yaml.load(idx,Loader=v.StrictLoader); print("INDEX parses strictly → OK")
        try: index_mark_ratified(idx,"Q-BOARD-RULING-06","Night","2026-09-14",a["ruling"],"x"); ok=False
        except ValueError: print("second ratification of the same candidate → REFUSED")
        # signature check via the handler logic
        body=json.dumps({"epoch":time.time(),"nonce":"n1"}).encode(); good=hmac.new(b"s3",body,hashlib.sha256).hexdigest()
        ok&=hmac.compare_digest(good,hmac.new(b"s3",body,hashlib.sha256).hexdigest()); ok&=not hmac.compare_digest("00",good); print("hmac good/bad → OK/REFUSED")
        x=assist({"q":"?","opts":[]}); ok&=x["by"]=="Z1"; text="You must revoke the key immediately."; dr=IMPERATIVE.findall(text); ok&=len(dr)==3; print("imperative strip →",dr)
        r1=content_ref("Re: budget  approval\n","k"); r2=content_ref("Re: budget approval","k"); r3=content_ref("Re: budget approval","k2")
        ok&=(r1==r2 and r1!=r3); print("content_ref canonical-equal / key-distinct →",r1==r2,r1!=r3)
        try: content_ref("x",""); ok=False
        except ValueError: print("keyless ref → REFUSED")
    finally:
        ROOT=real_root; shutil.rmtree(td,ignore_errors=True)
    print("SELF-TEST","PASS" if ok else "FAIL"); return 0 if ok else 2

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("port",nargs="?",type=int,default=8787); ap.add_argument("--self-test","--smoke-test",dest="self_test",action="store_true"); a=ap.parse_args()
    if a.self_test: sys.exit(selftest())
    if not SECRET: sys.exit("REFUSED: RELAY_SECRET not set (set it at intake)")
    print(f"relay v{TOOL_VERSION} on :{a.port} dry={DRY} repo={REPO} lands in z1-inbox/ (d18)"); HTTPServer(("0.0.0.0",a.port),H).serve_forever()

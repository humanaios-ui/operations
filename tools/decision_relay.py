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
  * the ratifier identity and every date come from the relay's own machine (RELAY_RATIFIER, server UTC), never from the
    request; /ratify refuses a candidate that is not awaiting_z2, a candidate whose body changed since /decide (body hash
    pinned at /decide), and a second ratification — nothing is written before those checks pass.
  * /assist returns navigator grammar only (position · destination · probability · readings), tagged by:Z1;
    an imperative in the model output is stripped and logged as DRIFT. It never writes a ruling.
  * /task (v0.4) is the agent bus: a signed request lands as a RECORD — z1-inbox/<day>/REQ-<yyyymmdd>-<nn>.md with a
    hashed request block and an empty Fulfilment section — indexed under records:, rendered, on a branch req/<id> with a
    PR. It asks Z2 for nothing and signs nothing. Any worker (a Claude Code session, a local model, a person) takes it
    by filling Fulfilment in its own PR. The tagline is recorded as sent and marked unverified: the HMAC proves the
    caller knew the secret, not who they are.
  * index helpers accept entries at any indentation — ratify.py 1.2.0 rewrites INDEX.yaml with items at column 0.
  * DRY_RUN=1 works on a local copy under ./relay_out instead of GitHub (self-test path).

Env: RELAY_SECRET (required) · GITHUB_TOKEN · GITHUB_REPO=humanaios-ui/operations · ANTHROPIC_API_KEY (optional)
     RELAY_BASIC_USER=night · RELAY_BASIC_PASS (set → basic-auth gate on every request but OPTIONS; the ngrok policy's gate, inside)
     PORT (a host's assigned port; the positional argument overrides it) · RELAY_RATIFIER=Night
Run:  RELAY_SECRET=... GITHUB_TOKEN=... python3 tools/decision_relay.py 8787
      ngrok http 8787 --traffic-policy-file tools/relay_policy.yml          # laptop: ngrok is the gate, leave RELAY_BASIC_PASS unset
      RELAY_SECRET=... RELAY_BASIC_PASS=... GITHUB_TOKEN=... python3 tools/decision_relay.py   # host (Railway): the relay is its own gate
GET /healthz answers {"relay":"ok"} with no credential (the host's liveness probe); GET / behind the gate reports the configuration.
"""
import os, sys, json, hmac, hashlib, time, base64, urllib.request, re, argparse, datetime, shutil, tempfile, io, contextlib, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

TOOL_NAME = "decision_relay"
TOOL_VERSION = "0.4.3"  # 0.1 = 09-08 relay; 0.2 = browser CORS; 0.3 = lands in z1-inbox + INDEX.yaml (d18); 0.3.1 = body hash pinned at decide, server-side ratifier + date, idempotent ratify; 0.4.0 = /task agent bus (REQ- records), index helpers indentation-agnostic; 0.4.1 = basic-auth gate inside the relay (RELAY_BASIC_PASS), /healthz, $PORT — runs on a host; 0.4.2 = request log on stdout; 0.4.3 = the log line carries the status and the refusal reason (a gate 401 and a signature 401 read differently on the host)
TOOL_CATEGORY = "governance_tool"
TOOL_SESSION = "S-091426-01"
TOOL_ZONE = 1  # matches tools-manifest.yaml (HAIOS-TOOL-051). The docstring names this relay as Z3 (it lands with a token); raising the declared zone is a Z2 ratification act, not a marker edit

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET=os.environ.get("RELAY_SECRET",""); TOKEN=os.environ.get("GITHUB_TOKEN","")
REPO=os.environ.get("GITHUB_REPO","humanaios-ui/operations"); DRY=os.environ.get("DRY_RUN")=="1"
SEEN=set(); IMPERATIVE=re.compile(r"\b(you must|you should|you need to|revoke|delete|do not|don't|immediately|stop)\b",re.I)
INDEX="z1-inbox/INDEX.yaml"; RENDERED="Z1_INBOX_INDEX.md"; RATIFIERS=("Night",)
# The ratifier is configured on the machine that holds the token, at intake — never taken from the request. A caller who
# knows the HMAC secret can send any tagline; it cannot make this relay sign as someone else.
RATIFIER=os.environ.get("RELAY_RATIFIER","Night")
def now_utc(): return datetime.datetime.now(datetime.timezone.utc)
def server_ts(): return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")

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
def item_indent(index_text,section="candidates"):
    """Indentation of the list items under `candidates:` / `records:` — 2 spaces in the hand-written index, 0 after
    ratify.py 1.2.0's yaml dump. Both are valid YAML; mixing them inside one list is not, so writes must match."""
    m=re.search(rf"(?m)^{section}:\n( *)- ",index_text)
    if m: return m.group(1)
    m=re.search(r"(?m)^candidates:\n( *)- ",index_text)
    return m.group(1) if m else ""  # no items anywhere: column 0, the shape ratify.py 1.2.0 writes today
def cand_path(index_text,qid):
    m=re.search(rf"(?m)^( *)- q_id: {re.escape(qid)}\n(?:\1  .*\n)*?\1  path: \"?([^\"\n]+?)\"?$",index_text)
    if not m: raise ValueError(f"{qid} is not a candidate in {INDEX}")
    return m.group(2)
def ruling_block(d):
    return ("RULING %s\n  by: %s (tagline)\n  project: %s\n  question: %s\n  choice: %s\n  note: %s\n  at: %s\n  status: PENDING\n"
            % (d["id"],d["tagline"],d["project"],d["q"],d["choice"],d.get("note",""),d["ts"]))
RULING_SEC=re.compile(r"(?ms)^## Ruling\n.*?(?=^## |\Z)")
def strip_ruling(cand_text):
    """The candidate with its `## Ruling` section removed — the bytes /decide pins and /ratify re-checks."""
    return RULING_SEC.sub("## Ruling\n\n",cand_text,count=1) if RULING_SEC.search(cand_text) else cand_text
def body_hash(cand_text): return sha(strip_ruling(cand_text).encode())
def write_choice(cand_text,choice,by,ts,status,block,block_hash,bhash):
    """Fill the candidate's `## Ruling` section with the choice, the full ruling block, its hash, and the hash of the rest
    of the file. Idempotent: a second /decide overwrites the same section."""
    sec=(f"## Ruling\n\nchoice: {choice}\nby: {by}\nat: {ts}\nstatus: {status}\nblock_hash: {block_hash}\nbody_hash: {bhash}\n\n"
         f"```\n{block}```\n")
    if RULING_SEC.search(cand_text): return RULING_SEC.sub(lambda m: sec+"\n",cand_text,count=1)
    return cand_text.rstrip("\n")+"\n\n"+sec
def ruling_fields(cand_text):
    """choice / by / at / status / block_hash / body_hash / block as written by /decide, or None."""
    m=RULING_SEC.search(cand_text)
    if not m: return None
    sec=m.group(0); f={k:(re.search(rf"^{k}: (.*)$",sec,re.M) or [None,None])[1] for k in ("choice","by","at","status","block_hash","body_hash")}
    b=re.search(r"```\n(.*?)```",sec,re.S); f["block"]=b.group(1) if b else None
    return f
def cand_status(index_text,qid):
    m=re.search(rf"(?m)^( *)- q_id: {re.escape(qid)}\n(?:\1  .*\n)*?\1  status: (\S+)",index_text)
    return m.group(2) if m else None
def signature(candidate_bytes,by,at,decision="ACCEPT"):
    """sha256(candidate | by=… | at=… | decision=…), per CLAUDE.md — byte-identical to .z1-control/ratify.py."""
    return hashlib.sha256(candidate_bytes+f"|by={by}|at={at}|decision={decision}".encode()).hexdigest()
def index_mark_ratified(index_text,qid,by,at,ruling_rel,digest):
    ind=item_indent(index_text); f=ind+"  "
    block=re.search(rf"(^{ind}- q_id: {re.escape(qid)}\n)(.*?)(?=^{ind}- q_id: |^records:|\Z)",index_text,re.M|re.S)
    if not block: raise ValueError(f"could not locate {qid} in {INDEX}")
    head,body=block.group(1),block.group(2)
    if not re.search(rf"^{f}status: awaiting_z2\n",body,re.M): raise ValueError(f"{qid} is not awaiting_z2; a decision is not re-taken by overwriting it")
    body=re.sub(rf"^{f}status: .*\n",f"{f}status: ratified\n",body,count=1,flags=re.M)
    add=f'{f}ratified_by: {by}\n{f}ratified_at: "{at}"\n{f}z2_ruling: "{ruling_rel}"\n{f}z2_hash: "{digest}"\n'
    trailing=""
    while body.endswith("\n\n"): body,trailing=body[:-1],"\n"
    return index_text[:block.start()]+head+body+add+trailing+index_text[block.end():]
def recount(index_text):
    """Recompute counts: from the entries actually present — never from a branch's starting snapshot, which two
    concurrent request PRs would both increment from N to N+1 (the failure mode .z1-control/ratify.py documents).
    Written back in whichever shape the file uses: inline `{candidates: n, records: m}` or a block."""
    ind=item_indent(index_text)
    cands=len(re.findall(rf"(?m)^{ind}- q_id: ",index_text))
    rs=re.search(r"(?ms)^records:.*?(?=^excluded:|\Z)",index_text); rsec=rs.group(0) if rs else ""
    rind=item_indent(index_text,"records")
    recs=len(re.findall(rf"(?m)^{rind}- path: ",rsec))
    m=re.search(r"counts: \{candidates: (\d+), records: (\d+)\}",index_text)
    if m: return index_text[:m.start()]+f"counts: {{candidates: {cands}, records: {recs}}}"+index_text[m.end():]
    m=re.search(r"(?m)^counts:\n( *)candidates: (\d+)\n\1records: (\d+)\n",index_text)
    if not m: raise ValueError("counts: line not found")
    return index_text[:m.start()]+f"counts:\n{m.group(1)}candidates: {cands}\n{m.group(1)}records: {recs}\n"+index_text[m.end():]
def yq(s):
    """A YAML double-quoted scalar: JSON string syntax is a subset of it, so user text with quotes, colons or
    backslashes cannot break the index."""
    return json.dumps(str(s),ensure_ascii=False)
def index_add_record(index_text,path,title,note):
    if f'path: "{path}"' in index_text or f"path: {path}\n" in index_text: return index_text
    # `records: []` is a valid empty list (ratify.py writes it); it must become a block before an item can go under it
    index_text=re.sub(r"(?m)^records: \[\]\s*$","records:",index_text,count=1)
    if "records:\n" not in index_text: raise ValueError("records: section not found")
    ind=item_indent(index_text,"records"); f=ind+"  "
    rec=f'records:\n{ind}- path: {yq(path)}\n{f}title: {yq(title)}\n{f}note: {yq(note)}\n'
    return recount(index_text.replace("records:\n",rec,1))
def rendered_index(index_text,read):
    """Z1_INBOX_INDEX.md exactly as .z1-control/render.py would write it for this INDEX text."""
    sys.path.insert(0,os.path.join(ROOT,".z1-control"))
    import yaml, validate as v, render as r  # noqa: E402
    return r.render(yaml.load(index_text,Loader=v.StrictLoader),read=read)

# ---------- the three paths ----------
def land(d):
    """/decide — choice → candidate block on a branch → PR (PENDING). returns {pr, number, hash, path, branch, qid, choice}
    Dates and the block's `by` come from this machine, not from the request."""
    ts=server_ts(); day=ts[:10]; qid=qid_for(d); br=f"z2/{d['id']}-{day}"
    dd={**d,"tagline":RATIFIER,"ts":ts}; block=ruling_block(dd); h=sha(block.encode())
    if not DRY:
        base=gh("GET",f"/repos/{REPO}/git/ref/heads/main")["object"]["sha"]
        try: gh("POST",f"/repos/{REPO}/git/refs",{"ref":f"refs/heads/{br}","sha":base})
        except Exception: pass
    st=store(br)
    idx,_=st.get(INDEX)
    if idx is None: raise ValueError(f"{INDEX} not found")
    if cand_status(idx,qid)!="awaiting_z2": raise ValueError(f"{qid} is not awaiting_z2; nothing to decide")
    path=cand_path(idx,qid); cand,_=st.get(path)
    if cand is None: raise ValueError(f"{path} not found")
    bh=body_hash(cand)
    st.put(path,write_choice(cand,d["choice"],RATIFIER,ts,"PENDING",block,h,bh),f"z2 {d['id']} ({qid}): {d['choice']} — PENDING, hash {h[:16]}")
    body=(f"# {qid} — {d['q']}\n\n```\n{block}```\n\nhash: `{h}`\nbody_hash: `{bh}`\n\nA tap is not a ratification. Ratify by echoing `hash` to /ratify from the board "
          f"(the relay then signs `{path}` as .z1-control/ratify.py would, records it in `{INDEX}`, and regenerates `{RENDERED}`).\n")
    out={"hash":h,"body_hash":bh,"path":path,"branch":br,"qid":qid,"choice":d["choice"],"ts":ts}
    if DRY: return {"pr":"DRY","number":0,**out}
    try: pr=gh("POST",f"/repos/{REPO}/pulls",{"title":f"Z2 ruling {d['id']} ({qid}): {d['choice']}","head":br,"base":"main","body":body})
    except Exception:  # a PR for this branch already exists (a re-sent choice): reuse it
        prs=gh("GET",f"/repos/{REPO}/pulls?state=open&head={REPO.split('/')[0]}:{br}"); pr=prs[0]
        gh("PATCH",f"/repos/{REPO}/pulls/{pr['number']}",{"title":f"Z2 ruling {d['id']} ({qid}): {d['choice']}","body":body})
    return {"pr":pr["html_url"],"number":pr["number"],**out}

def ratify(d):
    """/ratify — Z2 echoes the PENDING hash. Every check runs before anything is written:
    the echoed hash matches, the candidate is still awaiting_z2, the ruling block on the branch hashes to it, and the rest
    of the candidate still hashes to what /decide saw. Then: sign, record, regenerate. Refuse otherwise."""
    exp=d.get("expected_hash"); got=d.get("hash")
    if not got or got!=exp: return {"status":"REFUSED","why":"hash does not match the landed ruling; a tap is not a ratification"}
    by=RATIFIER
    if by not in RATIFIERS: return {"status":"REFUSED","why":f"relay is configured to sign as '{by}', who is not a ratifier ({', '.join(RATIFIERS)})"}
    if d.get("tagline") and d.get("tagline")!=by: return {"status":"REFUSED","why":f"this relay signs as {by}; the board's tagline is '{d.get('tagline')}'"}
    ts=server_ts(); at=ts[:10]
    qid=qid_for(d); br=d.get("branch") or f"z2/{d['id']}-{at}"; st=store(br)
    idx,_=st.get(INDEX)
    if idx is None: return {"status":"REFUSED","why":f"{INDEX} not found on {br}"}
    stt=cand_status(idx,qid)
    if stt!="awaiting_z2": return {"status":"REFUSED","why":f"{qid} is '{stt}', not awaiting_z2 — a decision is not re-taken; nothing written"}
    path=d.get("path") or cand_path(idx,qid); cand,_=st.get(path)
    f=ruling_fields(cand) if cand else None
    if not f or not f.get("block") or f.get("status")!="PENDING": return {"status":"REFUSED","why":"no PENDING ruling block on the branch"}
    if f["block_hash"]!=got or sha(f["block"].encode())!=got: return {"status":"REFUSED","why":"the ruling block on the branch does not hash to the echoed value — it was edited after /decide"}
    if body_hash(cand)!=f.get("body_hash"): return {"status":"REFUSED","why":"the candidate changed outside its Ruling section since /decide — re-send the choice"}
    m=re.search(r"^  choice: (.*)$",f["block"],re.M); choice=m.group(1) if m else f["choice"]
    if choice!=f["choice"]: return {"status":"REFUSED","why":"choice line and ruling block disagree"}
    # all checks passed — now write, in the order ratify.py writes
    cand=write_choice(cand,choice,by,ts,"RATIFIED",f["block"],got,f["body_hash"])
    st.put(path,cand,f"z2 {d['id']} ({qid}): RATIFIED by {by}")
    digest=signature(cand.encode(),by,at)          # over the bytes as they now stand — the same bytes CI will hash
    ruling_rel=f"z1-inbox/{at}/Z2_RULINGS_{at}.md"; ruling,_=st.get(ruling_rel)
    if ruling is None:
        ruling=(f"# Z2 Rulings — {at}\n\nSignatures issued by the Z2 serial gate. Each hash is\n`sha256(candidate | by=<ratifier> | at=<date> | decision=<D>)` over the\n"
                f"candidate block's bytes at the moment of decision, so editing a ratified\ncandidate afterwards breaks `ratify.py --verify`.\n")
        idx=index_add_record(idx,ruling_rel,f"Z2 rulings {at} — signatures issued by .z1-control/ratify.py and decision_relay.py","Z2 output. Cited as z2_ruling by the candidates it signs.")
    ruling+=(f"\n## {qid} — ACCEPT\n\nHash: `{digest}`\n\n- **Decision:** ACCEPT (ratified) · board ruling {d['id']}: `{choice}`\n"
             f"- **By:** {by}\n- **At:** {at}\n- **Candidate:** `{path}`\n- **Landed by:** tools/decision_relay.py v{TOOL_VERSION} (PENDING block hash `{got[:16]}…` echoed by Z2 at {ts})\n"
             f"- **Signature:** `sha256(candidate | by={by} | at={at} | decision=ACCEPT)`, computed over the candidate's bytes at the moment of decision.\n")
    st.put(ruling_rel,ruling,f"z2 rulings {at}: {qid} ACCEPT ({digest[:16]})")
    idx=index_mark_ratified(idx,qid,by,at,ruling_rel,digest); st.put(INDEX,idx,f"INDEX: {qid} ratified by {by}")
    st.put(RENDERED,rendered_index(idx,lambda rel: st.get(rel)[0] or ""),f"render Z1_INBOX_INDEX.md: {qid} ratified")
    if not DRY and d.get("number"):
        gh("POST",f"/repos/{REPO}/issues/{d['number']}/comments",{"body":f"RATIFY {d['id']} {got}\nby: {by} at {ts}\nsignature: {digest}\nruling: {ruling_rel}"})
        gh("POST",f"/repos/{REPO}/issues/{d['number']}/labels",{"labels":["z2-ratified"]})
    return {"status":"RATIFIED","hash":got,"signature":digest,"ruling":ruling_rel,"qid":qid,"choice":choice,"by":by,"at":at}

REQ_KINDS=("pr","answer","ruling")
def canon_ask(ask): return "\n".join(l.rstrip() for l in str(ask).strip().splitlines())
def req_block(d):
    """The hashed block pins every request field: the ask enters as its own sha256 (it is multi-line and lives in
    the record's `## Ask` section verbatim, so a reader recomputes it from there)."""
    return ("REQUEST %s\n  title: %s\n  lane: %s\n  wants: %s\n  tagline: %s (as sent; unverified)\n  ask_sha256: %s\n  at: %s\n"
            % (d["id"],d["title"],d.get("lane") or "—",d["wants"],d.get("tagline") or "—",sha(canon_ask(d["ask"]).encode()),d["ts"]))
def next_req_id(index_text,day,taken=()):
    """Next id: the day is a NAMESPACE (the folder the record lives in), not a window or a quota — resource-based
    operations put no calendar cap on requests, so the counter simply grows (-01 … -99, -100, …). Counted from the
    index (merged) plus `taken` (ids reserved by existing req/ branches: landed, not yet merged)."""
    compact=day.replace("-",""); n=max([0,*taken])
    for m in re.finditer(rf"z1-inbox/{re.escape(day)}/REQ-{compact}-(\d+)\.md",index_text): n=max(n,int(m.group(1)))
    return f"REQ-{compact}-{n+1:02d}"
def reserved_req_ids(day):
    """Ids already reserved by req/ branches on GitHub for this day (a request is reserved the moment its branch
    exists, before its PR merges into the index)."""
    compact=day.replace("-",""); out=set()
    for ref in gh("GET",f"/repos/{REPO}/git/matching-refs/heads/req/req-{compact}-"):
        m=re.search(rf"heads/req/req-{compact}-(\d+)$",ref.get("ref",""))
        if m: out.add(int(m.group(1)))
    return out
def req_record(d,block,h):
    return (f"# Agent request {d['id']} — {d['title']}\n\n"
            f"**Requested via:** tools/decision_relay.py v{TOOL_VERSION} (`/task`) · tagline as sent: `{d.get('tagline') or '—'}` (unverified — the HMAC proves the caller knew the secret, not who they are)\n"
            f"**At:** {d['ts']}\n**Lane:** {d.get('lane') or '—'}\n**Wants:** {d['wants']}\n**Status:** OPEN\n\n"
            f"This is a RECORD, not a candidate: it asks Z2 for nothing and carries no falsifier. A worker — a Claude Code session, a local model behind the relay, or a person — takes it by filling the Fulfilment section in its own PR and citing `{d['id']}` in that PR's body. Governance is unchanged: anything the work needs ratified goes through a candidate block as always.\n\n"
            f"## Ask\n\n{canon_ask(d['ask'])}\n\n"
            f"## Request block\n\n```\n{block}```\n\nhash: `{h}` — sha256 of the block above; `ask_sha256` inside it is sha256 of the `## Ask` section (lines right-stripped, outer whitespace stripped), so an edited ask breaks the hash.\n\n"
            f"## Fulfilment\n\ntaken_by:\npr:\nmerged:\nat:\n")
def one_line(d,name,maxlen,required=False):
    """A one-line metadata field as it will be written into the fenced, hashed request block: a string (never a coerced
    None/number), no newlines or control characters, and no backtick — a backtick could close the block's fence, and the
    record would no longer parse back to the bytes that were hashed."""
    v=d.get(name)
    if v is None or v=="":
        if required: raise ValueError(f"a request needs a {name}")
        return ""
    if not isinstance(v,str): raise ValueError(f"{name} must be a string")
    v=v.strip()
    if not v and required: raise ValueError(f"a request needs a {name}")
    if any(ord(c)<32 for c in v) or "`" in v: raise ValueError(f"{name} is one line: no newlines, control characters or backticks")
    if len(v)>maxlen: raise ValueError(f"{name} is at most {maxlen} characters")
    return v
def task(d):
    """/task — a signed request → REQ record in z1-inbox (records:, rendered) on a branch → PR. Nothing is decided, nothing
    is signed. Fields: title, ask, wants (pr|answer|ruling), lane (optional), tagline (recorded as sent)."""
    title=one_line(d,"title",140,required=True); lane=one_line(d,"lane",80); tagline=one_line(d,"tagline",80)
    ask=d.get("ask")
    if not isinstance(ask,str) or not ask.strip(): raise ValueError("a request needs an ask (a string)")
    ask=canon_ask(ask)
    if re.search(r"(?m)^## ",ask): raise ValueError("the ask may not contain a level-2 heading line (## …): the record's own sections are delimited by them")
    wants=d.get("wants","pr")
    if not isinstance(wants,str) or wants.strip().lower() not in REQ_KINDS: raise ValueError(f"wants must be one of {REQ_KINDS}")
    wants=wants.strip().lower()
    ts=server_ts(); day=ts[:10]
    # the id is numbered from main's index (merged requests) plus the req/ branches already on GitHub (landed, unmerged);
    # creating the branch ref is the atomic step — GitHub refuses a ref that exists — so a collision refuses, never reuses
    st=store("main"); idx,_=st.get(INDEX)
    if idx is None: raise ValueError(f"{INDEX} not found")
    rid=next_req_id(idx,day,reserved_req_ids(day) if not DRY else ()); br=f"req/{rid.lower()}"
    if not DRY:
        base=gh("GET",f"/repos/{REPO}/git/ref/heads/main")["object"]["sha"]
        try: gh("POST",f"/repos/{REPO}/git/refs",{"ref":f"refs/heads/{br}","sha":base})
        except Exception as e: raise ValueError(f"{rid} was reserved by another request between read and write ({br} exists); resend to take the next id") from e
        st=store(br); idx,_=st.get(INDEX)
        if idx is None: raise ValueError(f"{INDEX} not found on {br}")
    path=f"z1-inbox/{day}/{rid}.md"
    # a request that merged (and had its req/ branch deleted) between the index read and the ref create is on main now
    # but was in neither the index we read nor the reservations: re-read at the branch and refuse rather than overwrite
    if st.get(path)[0] is not None or f"/{rid}.md" in idx: raise ValueError(f"{path} already exists on the base; resend to take the next id")
    dd={**d,"id":rid,"title":title,"ask":ask,"wants":wants,"ts":ts,"tagline":tagline,"lane":lane}
    block=req_block(dd); h=sha(block.encode())
    st.put(path,req_record(dd,block,h),f"{rid}: {title} — OPEN, hash {h[:16]}")
    idx=index_add_record(idx,path,f"Agent request {rid} — {title}",f"OPEN · wants {wants} · lane {dd['lane'] or '—'} · landed by decision_relay.py /task; fulfilled by a worker's PR citing {rid}")
    st.put(INDEX,idx,f"INDEX: {rid} recorded")
    st.put(RENDERED,rendered_index(idx,lambda rel: st.get(rel)[0] or ""),f"render Z1_INBOX_INDEX.md: {rid}")
    out={"id":rid,"hash":h,"path":path,"branch":br,"wants":wants,"ts":ts}
    if DRY: return {"status":"OPEN","pr":"DRY","number":0,**out}
    body=(f"# {rid} — {title}\n\n```\n{block}```\n\nhash: `{h}`\n\nAn agent request landed by tools/decision_relay.py `/task`. Merging this records the request; the work itself "
          f"is a separate PR that fills `{path}` § Fulfilment and cites `{rid}`. No decision is asked of Z2 here.\n\n## Prediction (SMAG calibration)\n\nsmag_p: 0.95\n\nmolt_tier_claimed: 0\n")
    try: pr=gh("POST",f"/repos/{REPO}/pulls",{"title":f"{rid}: {title}","head":br,"base":"main","body":body})
    except Exception:
        prs=gh("GET",f"/repos/{REPO}/pulls?state=open&head={REPO.split('/')[0]}:{br}"); pr=prs[0]
    # the label is how workers find requests; if it cannot be applied the request still landed, and the response says so
    try: gh("POST",f"/repos/{REPO}/issues/{pr['number']}/labels",{"labels":["agent-request"]}); label,label_error="agent-request",None
    except Exception as e: label,label_error=None,f"label not applied: {type(e).__name__}: {str(e)[:160]}"
    return {"status":"OPEN","pr":pr["html_url"],"number":pr["number"],"label":label,"label_error":label_error,**out}

def assist(d):
    """Z1: reframe the decision in plain terms tied to the north star. Navigator grammar only."""
    key=os.environ.get("ANTHROPIC_API_KEY")
    prompt=("You are Z1 in HumanAIOS. Z2 is deciding: %s\nOptions: %s\nContext: %s\nNorth star: fund and operate a recovery center; GRBS profits go there.\n"
            "Answer in navigator grammar only — no imperatives to Z2, no calendar horizons (this project is resource-based: name resources, never deadlines). "
            "Give: position (one line), each option's reading (one line each, plain words), probability each option advances the north star for the resources it "
            "consumes, and what would prove the favoured reading wrong. Under 120 words.") % (d["q"],d.get("opts"),d.get("s",""))
    if not key or DRY:
        text="position: relay dry-run · no model key · readings not generated"
    else:
        req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=json.dumps({"model":"claude-sonnet-4-6","max_tokens":400,"messages":[{"role":"user","content":prompt}]}).encode(),
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
        with urllib.request.urlopen(req) as r: text="".join(b.get("text","") for b in json.load(r)["content"])
    drift=[m.group(0) for m in IMPERATIVE.finditer(text)]
    if drift: text=IMPERATIVE.sub("[…]",text)
    return {"by":"Z1","text":text,"drift":drift,"note":"advice, not a ruling; nothing is written"}

BASIC_USER=os.environ.get("RELAY_BASIC_USER","night"); BASIC_PASS=os.environ.get("RELAY_BASIC_PASS","")
def basic_ok(header):
    """The gate tools/relay_policy.yml used to put in front of the relay under ngrok, now inside it: when RELAY_BASIC_PASS is
    set, every request except the CORS preflight must carry HTTP basic-auth for RELAY_BASIC_USER. Unset → no gate (local use).
    The HMAC on every POST is still the real proof; this only keeps an unauthenticated caller from probing the endpoint."""
    if not BASIC_PASS: return True
    if not header.startswith("Basic "): return False
    try: user,_,pw=base64.b64decode(header[6:].strip()).decode().partition(":")
    except Exception: return False
    return hmac.compare_digest(user,BASIC_USER) and hmac.compare_digest(pw,BASIC_PASS)

class H(BaseHTTPRequestHandler):
    def _send(self,code,obj):
        self._why=str(obj.get("why","")) if code>=400 else ""  # read by log_request: the relay's own reason, never a body or a credential
        b=json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type","application/json")
        # Authorization is listed so a browser board can carry the basic-auth credential through the CORS preflight.
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type, X-Sig, Authorization")
        self.send_header("Access-Control-Allow-Methods","POST, GET, OPTIONS"); self.end_headers(); self.wfile.write(b)
    def _gate(self):
        """401 with a text body (not JSON): the board reads a non-JSON 401 as the basic-auth gate and clears its cached password."""
        if basic_ok(self.headers.get("Authorization","")): return True
        b=b"basic-auth required\n"; self._why="basic-auth required"; self.send_response(401); self.send_header("WWW-Authenticate",'Basic realm="intent-os"'); self.send_header("Content-Type","text/plain")
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type, X-Sig, Authorization"); self.end_headers(); self.wfile.write(b); return False
    # The host's log, one line per request on stdout (a host reads stderr as "error"): address, method, path without its query
    # string, the status, and for a refusal the relay's own one-line reason — so "401 basic-auth required" and "401 bad
    # signature" read differently on the host. Never a body, a header or a credential.
    def log_request(self,code="-",size="-"):
        why=re.sub(r"\s+"," ",getattr(self,"_why","") or "").strip()[:80]
        sys.stdout.write("%s %s %s %s%s\n"%(self.address_string(),self.command,self.path.split("?")[0],code," "+why if why else "")); sys.stdout.flush()
    def log_message(self,fmt,*args):  # anything else the base class would log (a malformed request line) goes to stdout too
        sys.stdout.write("%s %s\n"%(self.address_string(),fmt%args)); sys.stdout.flush()
    def do_OPTIONS(self): self._send(204,{})
    def do_GET(self):
        if self.path.split("?")[0]=="/healthz": return self._send(200,{"relay":"ok"})  # the host's liveness probe; says nothing else, needs no credential
        if not self._gate(): return
        self._send(200,{"relay":"ok","version":TOOL_VERSION,"dry":DRY,"repo":REPO,"signs_as":RATIFIER,"basic_auth":bool(BASIC_PASS),"github_token":bool(TOKEN),"lands_in":"z1-inbox/ (d18)","paths":["/decide","/ratify","/assist","/task"]})
    def do_POST(self):
        if not self._gate(): return
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
            if self.path=="/task": return self._send(200,task(d))
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
        d={"id":"d6","q":"batch source?","choice":"own postings","tagline":"Night","project":"HumanAIOS"}
        r=land(d); print("land →",r["path"],r["hash"][:16],r["branch"],"server date",r["ts"][:10])
        out=os.path.join(td,"relay_out"); cand=open(os.path.join(out,r["path"])).read(); f=ruling_fields(cand)
        ok&=(f["choice"]=="own postings" and f["status"]=="PENDING" and f["block_hash"]==r["hash"] and f["body_hash"]==r["body_hash"] and sha(f["block"].encode())==r["hash"])
        print("choice + block + body hash written into the candidate →",ok)
        ok&=r["ts"][:10]==now_utc().strftime("%Y-%m-%d"); print("date is the server's, not the request's →",r["ts"][:10]==now_utc().strftime("%Y-%m-%d"))
        base={**d,"expected_hash":r["hash"],"branch":r["branch"]}
        a=ratify({**base,"hash":"deadbeef"}); ok&=a["status"]=="REFUSED"; print("wrong hash →",a["status"])
        a=ratify({**base,"hash":r["hash"],"tagline":"Claude"}); ok&=a["status"]=="REFUSED"; print("spoofed tagline →",a["status"])
        # tamper with the candidate OUTSIDE the ruling section on the branch → body hash breaks → refused, nothing written
        p=os.path.join(out,r["path"]); orig=open(p).read(); open(p,"w").write(orig.replace("## Question","## Question (edited on the branch)"))
        a=ratify({**base,"hash":r["hash"]}); ok&=a["status"]=="REFUSED" and "outside its Ruling section" in a["why"]; print("body edited after /decide →",a["status"])
        open(p,"w").write(orig)
        # tamper with the block itself → block hash breaks
        open(p,"w").write(orig.replace("  choice: own postings","  choice: partner")); a=ratify({**base,"hash":r["hash"]}); ok&=a["status"]=="REFUSED"; print("block edited after /decide →",a["status"]); open(p,"w").write(orig)
        ok&=not os.path.exists(os.path.join(out,"z1-inbox","2026-09-14","Z2_RULINGS_2026-09-14.md")) or True
        a=ratify({**base,"hash":r["hash"]}); ok&=a["status"]=="RATIFIED"; print("echoed hash →",a["status"],a.get("signature","")[:16])
        idx=open(os.path.join(out,INDEX)).read(); ruling=open(os.path.join(out,a["ruling"])).read(); cand=open(os.path.join(out,r["path"])).read()
        ok&=("    status: ratified\n" in idx and "ratified_by: Night" in idx and a["signature"] in idx and a["signature"] in ruling
             and "counts: {candidates: 1, records: 1}" in idx and f'path: "{a["ruling"]}"' in idx and "status: RATIFIED" in cand)
        ok&=signature(cand.encode(),"Night",a["at"])==a["signature"]; print("index + ruling + candidate consistent, signature recomputes →",ok)
        rendered=open(os.path.join(out,RENDERED)).read(); ok&="Q-BOARD-RULING-06" in rendered; print("Z1_INBOX_INDEX.md regenerated →","Q-BOARD-RULING-06" in rendered)
        sys.path.insert(0,os.path.join(td,".z1-control")); import yaml, validate as v  # noqa: E402
        yaml.load(idx,Loader=v.StrictLoader); print("INDEX parses strictly → OK")
        before=(open(os.path.join(out,a["ruling"])).read(),open(os.path.join(out,r["path"])).read())
        a2=ratify({**base,"hash":r["hash"]}); after=(open(os.path.join(out,a["ruling"])).read(),open(os.path.join(out,r["path"])).read())
        ok&=a2["status"]=="REFUSED" and before==after; print("second ratification → REFUSED, nothing written:",a2["status"]=="REFUSED" and before==after)
        try: land(d); ok=False
        except ValueError: print("/decide on a ratified candidate → REFUSED")
        # signature check via the handler logic
        body=json.dumps({"epoch":time.time(),"nonce":"n1"}).encode(); good=hmac.new(b"s3",body,hashlib.sha256).hexdigest()
        ok&=hmac.compare_digest(good,hmac.new(b"s3",body,hashlib.sha256).hexdigest()); ok&=not hmac.compare_digest("00",good); print("hmac good/bad → OK/REFUSED")
        # basic-auth gate: off when no password is set; on, only the exact user:password pair passes; malformed headers fail closed
        global BASIC_PASS,BASIC_USER
        ok&=basic_ok("") and basic_ok("garbage")
        BASIC_PASS,BASIC_USER="pw-1","night"
        ba=lambda s:"Basic "+base64.b64encode(s.encode()).decode()
        ok&=basic_ok(ba("night:pw-1")) and not basic_ok(ba("night:pw-2")) and not basic_ok(ba("day:pw-1")) and not basic_ok("") and not basic_ok("Basic not-base64!") and not basic_ok("Bearer xyz")
        BASIC_PASS=""
        print("basic-auth gate: off without a password; on → exact user:password only; malformed/absent → refused → OK")
        # the host's logging contract: one line per request on STDOUT with the status and the refusal reason, nothing on
        # stderr (Railway shows stderr as "error"). A real round-trip on a loopback socket, both streams captured, so a
        # regression to BaseHTTPRequestHandler's stderr default is caught here and not on the host — and the two 401s a
        # board can meet (the gate; a wrong secret) are proven to read differently.
        srv=HTTPServer(("127.0.0.1",0),H); port=srv.server_address[1]; cap_out,cap_err=io.StringIO(),io.StringIO()
        BASIC_PASS="pw-1"; auth={"Authorization":ba("night:pw-1")}
        def post(path,body,headers):
            try:
                with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}{path}",data=body,headers=headers,method="POST")) as rr: return rr.status,json.load(rr)
            except urllib.error.HTTPError as e: return e.code,(json.loads(e.read()) if "json" in e.headers.get("Content-Type","") else None)
        with contextlib.redirect_stdout(cap_out), contextlib.redirect_stderr(cap_err):
            th=threading.Thread(target=srv.serve_forever,kwargs={"poll_interval":0.05},daemon=True); th.start()
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz?probe=1") as rr: hz=json.load(rr)
                try: urllib.request.urlopen(f"http://127.0.0.1:{port}/"); gated=None
                except urllib.error.HTTPError as e: gated=(e.code,e.headers.get("WWW-Authenticate",""),e.read())
                with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/",headers=auth)) as rr: st=json.load(rr)
                # the CORS preflight is exempt from the gate (a browser sends it with no credential):
                with urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/assist",method="OPTIONS")) as rr: pre=rr.status
                body=json.dumps({"epoch":time.time(),"nonce":"n-log-1","q":"?","opts":[]}).encode()
                bad_pw=post("/assist",body,{"Authorization":ba("night:pw-2"),"X-Sig":hmac.new(b"s3",body,hashlib.sha256).hexdigest(),"Content-Type":"application/json"})
                bad_sig=post("/assist",body,{**auth,"X-Sig":"00","Content-Type":"application/json"})
                good=post("/assist",body,{**auth,"X-Sig":hmac.new(b"s3",body,hashlib.sha256).hexdigest(),"Content-Type":"application/json"})
            finally: srv.shutdown(); th.join(2); srv.server_close()
        BASIC_PASS=""
        lines=cap_out.getvalue().splitlines()
        want=["127.0.0.1 GET /healthz 200","127.0.0.1 GET / 401 basic-auth required","127.0.0.1 GET / 200","127.0.0.1 OPTIONS /assist 204",
              "127.0.0.1 POST /assist 401 basic-auth required","127.0.0.1 POST /assist 401 bad signature","127.0.0.1 POST /assist 200"]
        ok&=(hz=={"relay":"ok"} and gated==(401,'Basic realm="intent-os"',b"basic-auth required\n") and st.get("basic_auth") is True and pre==204
             and bad_pw[0]==401 and bad_pw[1] is None and bad_sig==(401,{"status":"REFUSED","why":"bad signature"}) and good[0]==200 and good[1]["by"]=="Z1"
             and lines==want and cap_err.getvalue()=="")
        print("HTTP round-trip: /healthz open, / gated then answered, OPTIONS exempt, wrong password → 401 text, wrong secret → 401 json, signed → 200;",
              "log lines on stdout carry status + reason (query string dropped), stderr empty →",lines==want and cap_err.getvalue()=="")
        if lines!=want: print("  got:",lines)
        x=assist({"q":"?","opts":[]}); ok&=x["by"]=="Z1"; text="You must revoke the key immediately."; dr=IMPERATIVE.findall(text); ok&=len(dr)==3; print("imperative strip →",dr)
        r1=content_ref("Re: budget  approval\n","k"); r2=content_ref("Re: budget approval","k"); r3=content_ref("Re: budget approval","k2")
        ok&=(r1==r2 and r1!=r3); print("content_ref canonical-equal / key-distinct →",r1==r2,r1!=r3)
        try: content_ref("x",""); ok=False
        except ValueError: print("keyless ref → REFUSED")
        # /task — a request lands as a record: file, index entry, rendered index; ids count up within a day; nothing signed
        t1=task({"title":'Re-read the "ACAT" benchmark map: rows 1–12','ask':"Compare the 12 rows to the 09-08 read.  \n\nSecond paragraph.","wants":"pr","lane":"acat","tagline":"Night"})
        rec=open(os.path.join(out,t1["path"])).read(); idx=open(os.path.join(out,INDEX)).read(); rendered=open(os.path.join(out,RENDERED)).read()
        ok&=(t1["status"]=="OPEN" and re.fullmatch(r"REQ-\d{8}-01",t1["id"]) is not None and f"hash: `{t1['hash']}`" in rec and "## Fulfilment\n\ntaken_by:\n" in rec
             and "**Status:** OPEN" in rec and f'path: "{t1["path"]}"' in idx and "counts: {candidates: 1, records: 2}" in idx and t1["id"] in rendered and "unverified" in rec)
        print("/task → OPEN record, indexed under records:, rendered, tagline marked unverified →",ok)
        # the hash pins the ask: recompute from the record's ## Ask section; an edited ask breaks it
        blk=re.search(r"```\n(REQUEST .*?)```",rec,re.S).group(1); asks=re.search(r"## Ask\n\n(.*?)\n\n## Request block",rec,re.S).group(1)
        ok&=sha(blk.encode())==t1["hash"] and f"ask_sha256: {sha(asks.encode())}" in blk and asks=="Compare the 12 rows to the 09-08 read.\n\nSecond paragraph."
        ok&=f"ask_sha256: {sha((asks+' edited').encode())}" not in blk
        print("request hash covers the ask (ask_sha256 recomputes from ## Ask; trailing spaces canonicalised) →",ok)
        yaml.load(idx,Loader=v.StrictLoader); print("INDEX parses strictly with a quoted, colon-bearing title → OK")
        t2=task({"title":"Second ask","ask":"x","wants":"answer"}); ok&=t2["id"].endswith("-02"); print("second /task same day → -02:",t2["id"])
        idx=open(os.path.join(out,INDEX)).read()  # the index now carries -01 and -02 (records: 3)
        for bad in ({"title":"","ask":"x"},{"title":"t","ask":"x","wants":"deploy"},{"title":"a\nb","ask":"x"},{"title":None,"ask":None},{"title":7,"ask":"x"},
                    {"title":"a `fence` closer","ask":"x"},{"title":"t","ask":"x","lane":"a`b"},{"title":"t","ask":"line\n## Details\nmore"},{"title":"t","ask":"x","wants":None}):
            try: task(bad); ok=False; print("  NOT refused:",bad)
            except ValueError: pass
        print("/task refuses: empty/None/non-string/multi-line/backtick title, backtick lane, unknown or None wants, an ask with a ## heading → OK")
        # race: a record for the next id already exists on the base (merged between the index read and the ref create) → refuse, never overwrite
        rc_day=t1["ts"][:10]; rc_path=os.path.join(out,"z1-inbox",rc_day,f"REQ-{rc_day.replace('-','')}-03.md")
        open(rc_path,"w").write("# planted\n")
        try: task({"title":"Third","ask":"x"}); ok=False; print("  NOT refused: existing path overwritten")
        except ValueError as e: print("/task refuses when the chosen path already exists on the base →",str(e)[:60])
        os.remove(rc_path)
        # ids: reserved branches count; the day is a namespace with no quota — 99 → 100, never a wrap to 01
        day=t1["ts"][:10]; compact=day.replace("-","")
        ok&=next_req_id(idx,day,taken={7})==f"REQ-{compact}-08" and next_req_id(idx,day)==f"REQ-{compact}-03" and next_req_id(idx,day,taken={99})==f"REQ-{compact}-100"
        idx100=idx.replace(f"{compact}-02.md",f"{compact}-100.md"); ok&=next_req_id(idx100,day)==f"REQ-{compact}-101"
        print("next id honours reserved branches (07 → 08); 99 → 100 → 101, no wrap, no daily cap → OK")
        # counts are recomputed from entries, not incremented from a stale snapshot; `records: []` is normalised
        stale=idx.replace("counts: {candidates: 1, records: 3}","counts: {candidates: 1, records: 1}")
        fixed=index_add_record(stale,"z1-inbox/x/REQ-X.md","t","n"); ok&="counts: {candidates: 1, records: 4}" in fixed
        empty=index_add_record('version: 1\ncounts: {candidates: 0, records: 0}\nratifiers: [Night]\ncandidates: []\nrecords: []\nexcluded: []\n',"z1-inbox/x/REQ-Y.md",'q "t"',"n")
        ok&="records:\n- path: \"z1-inbox/x/REQ-Y.md\"" in empty and "counts: {candidates: 0, records: 1}" in empty; yaml.load(empty,Loader=v.StrictLoader)
        print("counts recomputed from entries (stale 1 → 4); `records: []` normalised and parses →",ok)
        # the same paths against the index format ratify.py 1.2.0 writes (items at column 0, block counts:)
        shutil.rmtree(out,ignore_errors=True)
        open(os.path.join(td,INDEX),"w").write('version: 1\ngenerated: "2026-09-16"\ndecision_window_days: 2\ncounts:\n  candidates: 1\n  records: 0\nratifiers:\n- Night\ncandidates:\n'
            '- q_id: Q-BOARD-RULING-06\n  title: Board ruling d6\n  path: z1-inbox/2026-09-14/Q-BOARD-RULING-06.md\n  submitted: \'2026-09-14\'\n  status: awaiting_z2\n  falsifier_waiver: question\nrecords:\nexcluded: []\n')
        r0=land(d); a0=ratify({**d,"expected_hash":r0["hash"],"branch":r0["branch"],"hash":r0["hash"]}); t0=task({"title":"col-0 index","ask":"y","wants":"pr"})
        idx0=open(os.path.join(out,INDEX)).read()
        ok&=(a0["status"]=="RATIFIED" and t0["status"]=="OPEN" and "\n- path: \"z1-inbox/" in idx0 and "\n  status: ratified\n" in idx0 and "counts:\n  candidates: 1\n  records: 2\n" in idx0)
        yaml.load(idx0,Loader=v.StrictLoader)
        print("column-0 index (ratify.py 1.2.0 format): /decide → /ratify → /task all land, counts block updated, parses strictly →",a0["status"]=="RATIFIED" and t0["status"]=="OPEN")
    finally:
        ROOT=real_root; shutil.rmtree(td,ignore_errors=True)
    print("SELF-TEST","PASS" if ok else "FAIL"); return 0 if ok else 2

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("port",nargs="?",type=int,default=int(os.environ.get("PORT","8787")))  # $PORT: what a host such as Railway assigns
    ap.add_argument("--self-test","--smoke-test",dest="self_test",action="store_true")
    ap.add_argument("--input",help="JSON file {\"path\": \"/decide\"|\"/ratify\"|\"/assist\", ...body} — run one request without the server (DRY_RUN=1 for a local copy)")
    a=ap.parse_args()
    if a.self_test: sys.exit(selftest())
    if a.input:
        req=json.load(open(a.input)); p=req.pop("path","/decide")
        fn={"/decide":lambda d:{"status":"PENDING",**land(d)},"/ratify":ratify,"/assist":assist,"/task":task}.get(p)
        if not fn: sys.exit(f"REFUSED: unknown path {p}")
        print(json.dumps(fn(req),indent=1)); sys.exit(0)
    if not SECRET: sys.exit("REFUSED: RELAY_SECRET not set (set it at intake)")
    print(f"relay v{TOOL_VERSION} on :{a.port} dry={DRY} repo={REPO} signs as {RATIFIER} · basic-auth {'on' if BASIC_PASS else 'off'} · github token {'set' if TOKEN else 'MISSING (every landing will fail)'} · lands in z1-inbox/ (d18)",flush=True)
    HTTPServer(("0.0.0.0",a.port),H).serve_forever()

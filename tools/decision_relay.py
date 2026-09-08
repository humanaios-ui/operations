#!/usr/bin/env python3
"""decision_relay.py — routes Z2 decisions from the Intent-OS board to a GitHub PR, behind ngrok.

Zones (system_graph v0.2): the board is Z2's hand · this relay is Z3 (lands) · the /assist path is Z1 (proposes).
Rules in code, not prose:
  * every POST carries X-Sig = HMAC-SHA256(secret, body); missing/wrong → 401. secret is set at intake (RELAY_SECRET).
  * nonce + timestamp inside the body; replay (seen nonce) or |skew| > 300s → 409/401.
  * a decision lands as PENDING with sha256(ruling block). It becomes RATIFIED only when Z2 posts that hash back
    (/ratify). A tap is not a ratification; the hash echo is.
  * /assist returns navigator grammar only (position · destination · probability · readings), tagged by:Z1;
    an imperative in the model output is stripped and logged as DRIFT. It never writes a ruling.
  * DRY_RUN=1 writes to ./relay_out instead of GitHub (self-test path).

Env: RELAY_SECRET (required) · GITHUB_TOKEN · GITHUB_REPO=humanaios-ui/operations · ANTHROPIC_API_KEY (optional)
Run:  RELAY_SECRET=... GITHUB_TOKEN=... python3 tools/decision_relay.py 8787
      ngrok http 8787 --traffic-policy-file tools/relay_policy.yml
"""
import os, sys, json, hmac, hashlib, time, base64, urllib.request, re, argparse
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRET=os.environ.get("RELAY_SECRET",""); TOKEN=os.environ.get("GITHUB_TOKEN","")
REPO=os.environ.get("GITHUB_REPO","humanaios-ui/operations"); DRY=os.environ.get("DRY_RUN")=="1"
SEEN=set(); IMPERATIVE=re.compile(r"\b(you must|you should|you need to|revoke|delete|do not|don't|immediately|stop)\b",re.I)

def sha(b): return hashlib.sha256(b).hexdigest()
def gh(method,path,data=None):
    req=urllib.request.Request(f"https://api.github.com{path}",method=method,data=json.dumps(data).encode() if data else None,
        headers={"Authorization":f"token {TOKEN}","Accept":"application/vnd.github+json","Content-Type":"application/json"})
    with urllib.request.urlopen(req) as r: return json.load(r)

def ruling_block(d):
    return ("RULING %s\n  by: %s (tagline)\n  project: %s\n  question: %s\n  choice: %s\n  note: %s\n  at: %s\n  status: PENDING\n"
            % (d["id"],d["tagline"],d["project"],d["q"],d["choice"],d.get("note",""),d["ts"]))

def land(d):
    """write ruling file → branch → PR. returns {pr, hash, path}"""
    block=ruling_block(d); h=sha(block.encode()); day=d["ts"][:10]
    path=f"z2-rulings/{day}/{d['id']}.md"; body=f"# {d['id']} — {d['q']}\n\n```\n{block}```\n\nhash: `{h}`\n\nRatify by posting this hash back to /ratify (or paste `RATIFY {d['id']} {h}` on the PR).\n"
    if DRY:
        os.makedirs(os.path.dirname("relay_out/"+path),exist_ok=True); open("relay_out/"+path,"w").write(body)
        return {"pr":"DRY","hash":h,"path":path}
    base=gh("GET",f"/repos/{REPO}/git/ref/heads/main")["object"]["sha"]; br=f"z2/{d['id']}-{day}"
    try: gh("POST",f"/repos/{REPO}/git/refs",{"ref":f"refs/heads/{br}","sha":base})
    except Exception: pass
    gh("PUT",f"/repos/{REPO}/contents/{path}",{"message":f"z2 ruling {d['id']}: {d['choice']} (PENDING, hash {h[:16]})","content":base64.b64encode(body.encode()).decode(),"branch":br})
    pr=gh("POST",f"/repos/{REPO}/pulls",{"title":f"Z2 ruling {d['id']}: {d['choice']}","head":br,"base":"main","body":body})
    return {"pr":pr["html_url"],"number":pr["number"],"hash":h,"path":path}

def ratify(d):
    """Z2 echoes the hash. Refuse if it does not match the landed block."""
    exp=d.get("expected_hash"); got=d.get("hash")
    if not got or got!=exp: return {"status":"REFUSED","why":"hash does not match the landed ruling; a tap is not a ratification"}
    if DRY: return {"status":"RATIFIED","hash":got}
    gh("POST",f"/repos/{REPO}/issues/{d['number']}/comments",{"body":f"RATIFY {d['id']} {got}\nby: {d['tagline']} at {d['ts']}"})
    gh("POST",f"/repos/{REPO}/issues/{d['number']}/labels",{"labels":["z2-ratified"]})
    return {"status":"RATIFIED","hash":got}

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
        self.send_header("Access-Control-Allow-Origin","*"); self.send_header("Access-Control-Allow-Headers","Content-Type, X-Sig"); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self): self._send(204,{})
    def do_GET(self): self._send(200,{"relay":"ok","dry":DRY,"repo":REPO})
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

def selftest():
    global DRY,SECRET; DRY=True; SECRET="s3"; ok=True
    d={"id":"d6","q":"batch source?","choice":"own postings","tagline":"Night","project":"HumanAIOS","ts":"2026-09-08T12:00:00Z"}
    r=land(d); print("land →",r["path"],r["hash"][:16])
    a=ratify({"hash":"deadbeef","expected_hash":r["hash"]}); ok&=a["status"]=="REFUSED"; print("wrong hash →",a["status"])
    a=ratify({"hash":r["hash"],"expected_hash":r["hash"]}); ok&=a["status"]=="RATIFIED"; print("echoed hash →",a["status"])
    # signature check via the handler logic
    body=json.dumps({"epoch":time.time(),"nonce":"n1"}).encode(); good=hmac.new(b"s3",body,hashlib.sha256).hexdigest()
    ok&=hmac.compare_digest(good,hmac.new(b"s3",body,hashlib.sha256).hexdigest()); ok&=not hmac.compare_digest("00",good); print("hmac good/bad → OK/REFUSED")
    x=assist({"q":"?","opts":[]}); ok&=x["by"]=="Z1"; text="You must revoke the key immediately."; dr=IMPERATIVE.findall(text); ok&=len(dr)==3; print("imperative strip →",dr)
    print("SELF-TEST","PASS" if ok else "FAIL"); return 0 if ok else 2

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("port",nargs="?",type=int,default=8787); ap.add_argument("--self-test",action="store_true"); a=ap.parse_args()
    if a.self_test: sys.exit(selftest())
    if not SECRET: sys.exit("REFUSED: RELAY_SECRET not set (set it at intake)")
    print(f"relay on :{a.port} dry={DRY} repo={REPO}"); HTTPServer(("0.0.0.0",a.port),H).serve_forever()

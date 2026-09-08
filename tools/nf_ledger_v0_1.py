#!/usr/bin/env python3
"""
nf_ledger_v0_1.py — NF_LEDGER (calibration ledger, Brier) for the Phase 2 mesh pins.

  build    <spec.json> <ledger.jsonl>          write TOKEN / PIN events from the spec (append-only, hash-chained)
  verify   <ledger.jsonl>                      recompute every hash + prev link; exit 1 on any break
  date     <ledger.jsonl> <token_id> <YYYY-MM-DD> --by Z2 --hash <z2_hash>   Z2 dates a Z1-proposed token
  resolve  <ledger.jsonl> <token_id> YES|NO --by <who> --source <tree read sha / path>
  status   <ledger.jsonl>                      counts: tokens by state, pins by predictor, scoreable N
  score    <ledger.jsonl>                      Brier per predictor over RESOLVED pins only

Rules encoded (not prose):
  * every forecast p is on [0,1]; anything else is refused at build/resolve time (RT-01 lesson)
  * a token whose date was proposed by Z1 is NOT scoreable until a DATE event signed by Z2 lands
  * a practice pin resolves YES iff every one of its Z2-dated tokens resolved YES; if any token is
    still PENDING_Z2_DATE at scoring time the practice pin is VOID, not scored
  * resolution is by tree read: the RESOLVE event must carry a `source` (sha or path); no source → refused
  * the ledger is append-only: nothing edits a prior line; corrections are new events
"""
import sys, json, hashlib, argparse
from datetime import datetime, timezone

def canon(d): return json.dumps(d, sort_keys=True, separators=(",", ":")).encode()
def sha(b): return hashlib.sha256(b).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")

def read(path):
    with open(path) as f: return [json.loads(l) for l in f if l.strip()]

def append(path, events, prev):
    with open(path, "a") as f:
        for ev in events:
            ev = dict(ev); ev["prev_hash"] = prev
            ev["hash"] = sha(canon(ev)); prev = ev["hash"]
            f.write(json.dumps(ev, sort_keys=True) + "\n")
    return prev

def last_hash(path):
    try: evs = read(path)
    except FileNotFoundError: return "0"*64
    return evs[-1]["hash"] if evs else "0"*64

def check_p(p, where):
    if p is None: return None
    if not (isinstance(p, (int, float)) and 0.0 <= p <= 1.0):
        sys.exit(f"REFUSED: forecast {p!r} outside [0,1] at {where}")
    return float(p)

# ---------------------------------------------------------------- build
def cmd_build(a):
    spec = json.load(open(a.spec))
    seq = 0; events = []
    def ev(t, **kw):
        nonlocal seq; seq += 1
        return {"seq": seq, "type": t, "at": spec["issued"], "by": "Z1", **kw}
    events.append(ev("OPEN", ledger="NF_LEDGER", version="v0.1", window=spec["window"],
                     source_plan=spec["source_plan"], registered_sha=spec["registered_sha"],
                     main_sha=spec["main_sha"], resolver=spec["resolver"]))
    for pr in spec["practices"]:
        for t in pr["tokens"]:
            events.append(ev("TOKEN", token_id=t["id"], practice=pr["id"], title=t["title"],
                             date=t["date"], date_source=t["date_source"],
                             state="DATED" if t["date_source"] == "PRACTICE" else "PENDING_Z2_DATE",
                             owner_add=t.get("owner_add", False)))
            events.append(ev("PIN", pin_id=f"{t['id']}:Z1", target=t["id"], predictor="Z1",
                             claim=f"{t['title']} exists as a hashed file in the tree at or before {t['date']}",
                             p=check_p(t["p_z1"], t["id"]), scoreable=(t["date_source"] == "PRACTICE")))
        for pred, p in pr["practice_p"].items():
            events.append(ev("PIN", pin_id=f"P2-{pr['id']}:{pred}", target=f"P2-{pr['id']}", predictor=pred,
                             claim="all dated P2 deliverables of this practice exist as hashed files by their dates",
                             p=check_p(p, pr["id"]), tokens=[t["id"] for t in pr["tokens"]],
                             scoreable=any(t["date_source"] == "PRACTICE" for t in pr["tokens"]), note=pr.get("note")))
        events.append(ev("PIN", pin_id=f"P2-{pr['id']}:Z2", target=f"P2-{pr['id']}", predictor="Z2",
                         claim="(same)", p=None, tokens=[t["id"] for t in pr["tokens"]],
                         scoreable=False, note="OWED — Z2 enters own prior before Sep 12 or the LT-2 series has no input"))
    for x in spec.get("extra_pins", []):
        events.append(ev("PIN", **x, scoreable=True))
    prev = append(a.ledger, events, "0"*64)
    print(f"built {len(events)} events → {a.ledger}\nhead {prev}")

# ---------------------------------------------------------------- verify
def verify(evs):
    prev = "0"*64
    for i, e in enumerate(evs):
        body = {k: v for k, v in e.items() if k != "hash"}
        if e.get("prev_hash") != prev: return f"BREAK seq {e.get('seq')} prev_hash mismatch"
        if sha(canon(body)) != e["hash"]: return f"BREAK seq {e.get('seq')} hash mismatch"
        if i and e["seq"] != evs[i-1]["seq"] + 1: return f"BREAK seq {e.get('seq')} sequence gap"
        prev = e["hash"]
    return None

def cmd_verify(a):
    err = verify(read(a.ledger))
    if err: sys.exit("FAIL " + err)
    print("OK chain intact", len(read(a.ledger)), "events; head", last_hash(a.ledger))

# ---------------------------------------------------------------- state projection
def project(evs):
    tokens, pins = {}, {}
    for e in evs:
        t = e["type"]
        if t == "TOKEN": tokens[e["token_id"]] = dict(e, resolved=None)
        elif t == "PIN": pins[e["pin_id"]] = dict(e)
        elif t == "DATE":
            tk = tokens[e["token_id"]]; tk.update(date=e["date"], date_source="Z2", state="DATED", z2_hash=e["z2_hash"])
            for p in pins.values():
                if p.get("target") == e["token_id"]: p["scoreable"] = True
        elif t == "RESOLVE":
            tk = tokens[e["token_id"]]; tk["resolved"] = e["outcome"]; tk["state"] = "RESOLVED"
        elif t == "STRIKE":
            tokens[e["token_id"]]["state"] = "STRUCK"
    return tokens, pins

def pin_outcome(p, tokens):
    """returns 1.0 / 0.0 / None(unresolved) / 'VOID'"""
    ids = p.get("tokens") or [p["target"]]
    outs = []
    for i in ids:
        tk = tokens.get(i)
        if tk is None: return None
        if tk["state"] == "STRUCK": continue
        if tk["state"] == "PENDING_Z2_DATE": return "VOID"
        if tk["resolved"] is None: return None
        outs.append(tk["resolved"] == "YES")
    if not outs: return "VOID"
    return 1.0 if all(outs) else 0.0

# ---------------------------------------------------------------- mutations
def cmd_date(a):
    evs = read(a.ledger); err = verify(evs)
    if err: sys.exit("FAIL " + err)
    tokens, _ = project(evs)
    if a.token_id not in tokens: sys.exit("REFUSED: unknown token")
    if a.by != "Z2" or not a.hash: sys.exit("REFUSED: a date on a Z1-proposed token is a Z2 act; needs --by Z2 --hash")
    datetime.strptime(a.date, "%Y-%m-%d")
    append(a.ledger, [{"seq": evs[-1]["seq"]+1, "type": "DATE", "at": now(), "by": "Z2",
                       "token_id": a.token_id, "date": a.date, "z2_hash": a.hash}], evs[-1]["hash"])
    print("DATE appended; head", last_hash(a.ledger))

def cmd_resolve(a):
    evs = read(a.ledger); err = verify(evs)
    if err: sys.exit("FAIL " + err)
    tokens, _ = project(evs)
    tk = tokens.get(a.token_id)
    if tk is None: sys.exit("REFUSED: unknown token")
    if tk["state"] == "PENDING_Z2_DATE": sys.exit("REFUSED: token has no Z2 date; cannot resolve an undated event")
    if tk["state"] == "RESOLVED": sys.exit("REFUSED: already resolved; append a DISPUTE event instead")
    if not a.source: sys.exit("REFUSED: resolution needs --source (tree sha or path read)")
    append(a.ledger, [{"seq": evs[-1]["seq"]+1, "type": "RESOLVE", "at": now(), "by": a.by,
                       "token_id": a.token_id, "outcome": a.outcome, "source": a.source}], evs[-1]["hash"])
    print("RESOLVE appended; head", last_hash(a.ledger))

# ---------------------------------------------------------------- reports
def cmd_status(a):
    evs = read(a.ledger); err = verify(evs)
    if err: sys.exit("FAIL " + err)
    tokens, pins = project(evs)
    st = {}
    for t in tokens.values(): st[t["state"]] = st.get(t["state"], 0) + 1
    print("tokens", len(tokens), st)
    by = {}
    for p in pins.values():
        k = p["predictor"]; by.setdefault(k, [0, 0, 0])
        by[k][0] += 1; by[k][1] += (p["p"] is not None); by[k][2] += bool(p["scoreable"] and p["p"] is not None)
    print("pins  predictor: total / entered / scoreable-now")
    for k, v in sorted(by.items()): print(f"  {k:32s} {v[0]:3d} {v[1]:3d} {v[2]:3d}")
    print("head", evs[-1]["hash"])

def cmd_score(a):
    evs = read(a.ledger); err = verify(evs)
    if err: sys.exit("FAIL " + err)
    tokens, pins = project(evs)
    acc = {}
    for p in pins.values():
        if p["p"] is None: continue
        o = pin_outcome(p, tokens)
        if o in (None, "VOID"): continue
        acc.setdefault(p["predictor"], []).append((p["p"] - o) ** 2)
    if not acc: print("no resolved pins yet — Brier undefined (reported, not smoothed)"); return
    for k, v in sorted(acc.items()): print(f"{k:32s} N={len(v):3d} Brier={sum(v)/len(v):.3f}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("build"); s.add_argument("spec"); s.add_argument("ledger"); s.set_defaults(f=cmd_build)
    s = sp.add_parser("verify"); s.add_argument("ledger"); s.set_defaults(f=cmd_verify)
    s = sp.add_parser("date"); s.add_argument("ledger"); s.add_argument("token_id"); s.add_argument("date")
    s.add_argument("--by", default=""); s.add_argument("--hash", default=""); s.set_defaults(f=cmd_date)
    s = sp.add_parser("resolve"); s.add_argument("ledger"); s.add_argument("token_id"); s.add_argument("outcome", choices=["YES", "NO"])
    s.add_argument("--by", required=True); s.add_argument("--source", default=""); s.set_defaults(f=cmd_resolve)
    s = sp.add_parser("status"); s.add_argument("ledger"); s.set_defaults(f=cmd_status)
    s = sp.add_parser("score"); s.add_argument("ledger"); s.set_defaults(f=cmd_score)
    a = ap.parse_args(); a.f(a)

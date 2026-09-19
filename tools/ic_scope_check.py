#!/usr/bin/env python3
"""IC-SCOPE-05 gate — no tool touches a client system without a signed
scope_hash and a pinned criteria_hash. Refuse, don't warn.

Usage:
  ic_scope_check.py <intake.jsonl> [--criteria criteria.md] [--pubkey key.hex]
Exit 0 only if every row passes. Any failure is a refusal (exit 2), never a warning.

Row fields required:
  scope_hash      sha256 of the scope statement the client agreed to
  scope_sig       hex HMAC-SHA256 of scope_hash under the shared secret (or ed25519 sig if a pubkey is given)
  criteria_hash   sha256 of the pre-registered criteria file (R-001) the audit will be scored against

Falsifier: if a row with a missing or forged scope_sig, or a criteria_hash that does not
match the pinned criteria file, exits 0 — this gate is broken.
"""
import sys, json, hmac, hashlib, os, argparse

def sha256(b): return hashlib.sha256(b).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("intake")
    ap.add_argument("--criteria", default="criteria/R-001.md")
    ap.add_argument("--secret-env", default="IC_SCOPE_SECRET")
    a = ap.parse_args()

    secret = os.environ.get(a.secret_env, "").encode()
    if not secret:
        print(json.dumps({"verdict":"REFUSE","reason":f"no signing secret in ${a.secret_env}"})); return 2
    if not os.path.exists(a.criteria):
        print(json.dumps({"verdict":"REFUSE","reason":f"criteria file missing: {a.criteria}"})); return 2
    pinned = sha256(open(a.criteria,"rb").read())

    refusals = []
    n = 0
    for i, line in enumerate(open(a.intake), 1):
        line = line.strip()
        if not line: continue
        n += 1
        try: row = json.loads(line)
        except Exception as e:
            refusals.append({"row":i,"reason":f"not JSON: {e}"}); continue
        for f in ("scope_hash","scope_sig","criteria_hash"):
            if not row.get(f):
                refusals.append({"row":i,"reason":f"missing {f}"}); break
        else:
            want = hmac.new(secret, row["scope_hash"].encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(want, row["scope_sig"]):
                refusals.append({"row":i,"reason":"scope_sig does not verify"})
            elif row["criteria_hash"] != pinned:
                refusals.append({"row":i,"reason":"criteria_hash != pinned criteria"})

    out = {"gate":"IC-SCOPE-05","rows":n,"refused":len(refusals),
           "verdict":"REFUSE" if refusals or n==0 else "PASS","pinned_criteria":pinned[:16],
           "refusals":refusals[:20]}
    print(json.dumps(out, indent=1))
    return 0 if out["verdict"]=="PASS" else 2

if __name__ == "__main__": sys.exit(main())

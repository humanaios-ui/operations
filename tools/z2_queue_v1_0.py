#!/usr/bin/env python3
“””
Z2 Queue — v1.1 (Supabase-canonical, dual-write)
Builder v1.7 compliant · diagnostic_tool
HumanAIOS · S-071026-01

v1.0 filled the empty scaffold with a local-only JSONL ledger. v1.1
makes Supabase pm_z2_queue (landed live this session) the canonical
store, so ANY system operating in this project – Claude via MCP,
Copilot via GitHub Action + REST, Night via dashboard, any future
agent with REST creds – reads the same queue, not whatever happened
to be in one sandbox’s local file.

Local JSONL is now a FALLBACK ONLY, not the source of truth: if the
Supabase write fails (network, missing creds, table unreachable),
the entry is logged locally with synced=false and pending_sync=true,
never silently lost. –sync-pending retries every unsynced local
entry once connectivity/creds are available.

CREDENTIALS: reads SUPABASE_URL / SUPABASE_KEY from environment,
same convention as supabase_corpus_connector_v1_0.py and
haios_doc_ingestor_v1_0.py – anon key sufficient (insert/select
only, no schema changes at runtime). Stdlib-only HTTP (urllib), no
supabase-py dependency, so this runs anywhere Python3 runs, including
Copilot’s CI (existing workflow pattern already references
secrets.SUPABASE_KEY_N8N).

HONEST TEST STATUS (S-071026-01): the offline-fallback path below was
verified live in this session – SUPABASE_KEY was genuinely absent
from the test environment, not mocked, so the fallback branch fired
for a real reason. The Supabase REST write path itself is pattern-
matched against two already-working tools in this repo but has NOT
been executed end-to-end against a live HTTP round-trip from this
session, since no credential was available here. Run with real
SUPABASE_URL/SUPABASE_KEY set before trusting the write path fully.

STRUCTURAL ENFORCEMENT (unchanged from v1.0): validate_entry() runs
once, before either write path is attempted. Neither Supabase nor
local fallback can receive an entry missing zone2_ratification.

Usage:
python z2_queue_v1_0.py –append entry.json –session-id S-XXX
python z2_queue_v1_0.py –status –session-id S-XXX
python z2_queue_v1_0.py –sync-pending
python z2_queue_v1_0.py –export-ratified –output-dir outputs/
python z2_queue_v1_0.py –smoke-test
“””
import json
import os
import sys
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = “z2_queue”
TOOL_VERSION = “1.1.0”
TOOL_CATEGORY = “diagnostic_tool”
TOOL_ZONE = 1

DEFAULT_LOCAL_PATH = “z2_queue_fallback.jsonl”
SUPABASE_TABLE = “pm_z2_queue”
STALE_SESSION_THRESHOLD = 3
REQUIRED_FIELDS = [“id_slug”, “class”, “synopsis”, “zone2_ratification”]

class SpecLoadFailed(Exception):
pass

class SupabaseUnreachable(Exception):
“”“Raised internally when the REST call fails for any reason –
caught by the caller to trigger local fallback, never left to
crash the whole append operation.”””
pass

# ── Config ─────────────────────────────────────────────────────────────────

def get_supabase_config() -> tuple:
url = os.environ.get(“SUPABASE_URL”, “”).rstrip(”/”)
key = os.environ.get(“SUPABASE_KEY”, “”)
return url, key

# ── Input Loading ─────────────────────────────────────────────────────────────

def load_input(source: str) -> dict:
p = Path(source)
if p.exists():
try:
with open(p, encoding=“utf-8”) as f:
return json.load(f)
except (json.JSONDecodeError, OSError) as e:
raise SpecLoadFailed(f”Cannot load {p}: {e}”)
try:
return json.loads(source)
except json.JSONDecodeError as e:
raise SpecLoadFailed(f”Input is neither a valid path nor valid JSON: {e}”)

def load_local_fallback(path: str) -> list:
p = Path(path)
if not p.exists():
return []
entries = []
for line in p.read_text(encoding=“utf-8”).splitlines():
line = line.strip()
if not line:
continue
try:
entries.append(json.loads(line))
except json.JSONDecodeError:
continue
return entries

def append_local_fallback(path: str, record: dict) -> None:
with open(path, “a”, encoding=“utf-8”) as f:
f.write(json.dumps(record) + “\n”)

# ── Validation (shared gate, both write paths) ────────────────────────────────

def validate_entry(entry: dict) -> list:
missing = [f for f in REQUIRED_FIELDS if not entry.get(f)]
if entry.get(“class”) not in {“F”, “IC”, “H”, “IC-correction”}:
missing.append(“class (invalid value)”)
return missing

# ── Supabase REST (stdlib only, matches supabase_corpus_connector pattern) ───

def supabase_upsert(entry: dict, timeout: int = 10) -> dict:
“””
POST to pm_z2_queue with Prefer: resolution=merge-duplicates,
upserting on the id_slug UNIQUE constraint. Raises
SupabaseUnreachable on any failure – missing creds, network
error, HTTP error – so the caller can fall back cleanly rather
than crash.
“””
url, key = get_supabase_config()
if not url or not key:
raise SupabaseUnreachable(“SUPABASE_URL/SUPABASE_KEY not set in environment”)

```
endpoint = f"{url}/rest/v1/{SUPABASE_TABLE}"
body = json.dumps([entry]).encode()
req = urllib.request.Request(
    endpoint,
    data=body,
    method="POST",
    headers={
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    },
)
try:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())
except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
    raise SupabaseUnreachable(str(e))
```

def supabase_select(filters: str = “”, timeout: int = 10) -> list:
url, key = get_supabase_config()
if not url or not key:
raise SupabaseUnreachable(“SUPABASE_URL/SUPABASE_KEY not set in environment”)

```
endpoint = f"{url}/rest/v1/{SUPABASE_TABLE}?select=*{filters}"
req = urllib.request.Request(
    endpoint,
    headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())
except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
    raise SupabaseUnreachable(str(e))
```

# ── Core: dual-write append ───────────────────────────────────────────────────

def append_entry(entry: dict, session_id: str, local_path: str = DEFAULT_LOCAL_PATH) -> dict:
“””
HARD GATE first (unchanged from v1.0) – applies regardless of
which write path is used. Then: try Supabase (canonical). On any
failure, fall back to local JSONL with synced=false, never silent.
“””
missing = validate_entry(entry)
if missing:
return {“written”: False, “reason”: “missing_required_fields”, “missing”: missing}

```
record = {
    **entry,
    "session_first_seen": session_id,
    "compiled": False,
}

try:
    supabase_upsert(record)
    # Mirror to local as an audit trail even on success -- not the
    # source of truth once synced, just a local record it happened.
    append_local_fallback(local_path, {**record, "synced": True,
                                        "logged_at": datetime.now(timezone.utc).isoformat()})
    return {"written": True, "target": "supabase", "id_slug": entry["id_slug"]}
except SupabaseUnreachable as e:
    append_local_fallback(local_path, {**record, "synced": False, "pending_sync": True,
                                        "sync_error": str(e),
                                        "logged_at": datetime.now(timezone.utc).isoformat()})
    return {"written": True, "target": "local_fallback", "id_slug": entry["id_slug"],
            "warning": f"Supabase unreachable, logged locally only: {e}"}
```

def sync_pending(local_path: str = DEFAULT_LOCAL_PATH) -> dict:
“”“Retries every locally-fallen-back entry against Supabase.
Rewrites the local file with updated sync status – entries that
succeed are marked synced=true, not deleted, so the local file
stays a complete audit trail.”””
entries = load_local_fallback(local_path)
updated = []
synced_count = 0
failed_count = 0
for e in entries:
if e.get(“synced”):
updated.append(e)
continue
try:
clean = {k: v for k, v in e.items()
if k not in (“synced”, “pending_sync”, “sync_error”, “logged_at”)}
supabase_upsert(clean)
e = {**e, “synced”: True, “pending_sync”: False,
“resynced_at”: datetime.now(timezone.utc).isoformat()}
synced_count += 1
except SupabaseUnreachable as err:
e = {**e, “sync_error”: str(err)}
failed_count += 1
updated.append(e)

```
p = Path(local_path)
p.write_text("\n".join(json.dumps(e) for e in updated) + ("\n" if updated else ""), encoding="utf-8")
return {"synced": synced_count, "still_pending": failed_count}
```

# ── Status / export (Supabase-first, local-fallback-aware) ────────────────────

def compute_status(entries: list, current_session: str, source: str) -> dict:
uncompiled = [e for e in entries if not e.get(“compiled”)]
sessions_seen = sorted({e.get(“session_first_seen”, “UNKNOWN”) for e in entries})
session_age = {s: i for i, s in enumerate(sessions_seen)}
current_age = session_age.get(current_session, len(sessions_seen))

```
stale = []
for e in uncompiled:
    age = current_age - session_age.get(e.get("session_first_seen", "UNKNOWN"), current_age)
    if age >= STALE_SESSION_THRESHOLD:
        stale.append({"id_slug": e["id_slug"], "sessions_unresolved": age})

return {
    "source": source,
    "total_logged": len(entries),
    "uncompiled_count": len(uncompiled),
    "compiled_count": len(entries) - len(uncompiled),
    "oldest_first": [e["id_slug"] for e in sorted(uncompiled, key=lambda e: e.get("logged_at", ""))],
    "stale_flagged": stale,
}
```

def get_current_queue(local_path: str) -> tuple:
“”“Returns (entries, source_label). Tries Supabase first since it’s
canonical; falls back to local-only view with a clear WARN label
if unreachable, plus surfaces any locally-pending unsynced entries
Supabase wouldn’t know about yet.”””
local_entries = load_local_fallback(local_path)
try:
remote = supabase_select()
pending_local = [e for e in local_entries if not e.get(“synced”)]
return remote + pending_local, “supabase (+ local pending_sync entries)”
except SupabaseUnreachable:
return local_entries, “LOCAL FALLBACK ONLY – Supabase unreachable, view may be incomplete”

def export_ratified(local_path: str) -> list:
entries, _ = get_current_queue(local_path)
keep = REQUIRED_FIELDS + [“evidence”, “fix_principle”, “related_finding”,
“principles_triggered”, “status”]
return [{k: v for k, v in e.items() if k in keep} for e in entries]

# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
try:
import tempfile
lpath = tempfile.mktemp(suffix=”.jsonl”)

```
    # Positive: valid entry -- Supabase creds absent in most CI/sandbox
    # contexts by default, so this exercises the REAL fallback path,
    # not a mock.
    good = {"id_slug": "IC-CAND-SMOKE-GOOD", "class": "IC", "status": "REGISTERED",
            "synopsis": "smoke test entry", "zone2_ratification": "Night · S-TEST"}
    r1 = append_entry(good, "S-TEST-1", lpath)
    assert r1["written"] is True
    assert r1["target"] in ("supabase", "local_fallback")

    # Negative: missing zone2_ratification hard-rejected regardless of target
    bad = {"id_slug": "IC-CAND-SMOKE-BAD", "class": "IC", "status": "CANDIDATE",
           "synopsis": "unratified"}
    r2 = append_entry(bad, "S-TEST-1", lpath)
    assert r2["written"] is False
    assert "zone2_ratification" in r2["missing"]

    local_after = load_local_fallback(lpath)
    assert not any(e["id_slug"] == "IC-CAND-SMOKE-BAD" for e in local_after), \
        "rejected entry must not appear anywhere, including local fallback"

    # Export composes cleanly regardless of which path served the data
    exported = export_ratified(lpath)
    assert any(e["id_slug"] == "IC-CAND-SMOKE-GOOD" for e in exported)

    os.remove(lpath)
    print("✓ Smoke test PASSED")
    return True
except Exception as e:
    print(f"✗ Smoke test FAILED: {e}")
    return False
```

# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
parser = argparse.ArgumentParser(description=f”{TOOL_NAME} v{TOOL_VERSION}”)
parser.add_argument(”–local-path”, default=DEFAULT_LOCAL_PATH)
parser.add_argument(”–append”)
parser.add_argument(”–session-id”, default=“S-UNKNOWN”)
parser.add_argument(”–status”, action=“store_true”)
parser.add_argument(”–sync-pending”, action=“store_true”)
parser.add_argument(”–export-ratified”, action=“store_true”)
parser.add_argument(”–output-dir”, “-o”, default=“outputs/”)
parser.add_argument(”–smoke-test”, action=“store_true”)
args = parser.parse_args()

```
if args.smoke_test:
    sys.exit(0 if run_smoke_test() else 1)

if args.append:
    try:
        entry = load_input(args.append)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)
    result = append_entry(entry, args.session_id, args.local_path)
    if result["written"]:
        print(f"LOGGED [{result['target']}]: {result['id_slug']}")
        if result.get("warning"):
            print(f"WARN: {result['warning']}", file=sys.stderr)
    else:
        print(f"REJECTED: {result.get('id_slug', entry.get('id_slug', '?'))} "
              f"-- {result['reason']} {result.get('missing', '')}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

if args.sync_pending:
    result = sync_pending(args.local_path)
    print(f"Synced: {result['synced']}  Still pending: {result['still_pending']}")
    sys.exit(0)

if args.export_ratified:
    exported = export_ratified(args.local_path)
    p = Path(args.output_dir)
    p.mkdir(parents=True, exist_ok=True)
    out_path = p / f"z2_queue_export_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(exported, indent=2), encoding="utf-8")
    print(f"Exported {len(exported)} entries -> {out_path}")
    sys.exit(0)

if args.status:
    entries, source = get_current_queue(args.local_path)
    status = compute_status(entries, args.session_id, source)
    print(f"\nSource: {status['source']}")
    print(f"Total logged: {status['total_logged']}  Uncompiled: {status['uncompiled_count']}")
    if status["stale_flagged"]:
        for s in status["stale_flagged"]:
            print(f"  WARN stale: {s['id_slug']} unresolved {s['sessions_unresolved']} sessions")
    sys.exit(0)

parser.print_help()
sys.exit(1)
```

if **name** == “**main**”:
main()
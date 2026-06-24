"""
parse_wgs_z3.py
WGS → Supabase zone3_queue sync
GitHub Actions context: reads #wgs-sync, upserts Z3 items into Supabase
Session: S-061126 · HumanAIOS LLC
"""

import os, re, json
from slack_sdk import WebClient
from supabase import create_client

CHANNEL_ID  = os.environ["WGS_CHANNEL_ID"]       # C0AND66PT7U
SLACK_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SUPA_URL    = os.environ["SUPABASE_URL"]
SUPA_KEY    = os.environ["SUPABASE_SERVICE_KEY"]

slack    = WebClient(token=SLACK_TOKEN)
supabase = create_client(SUPA_URL, SUPA_KEY)

# ── 1. Fetch recent WGS messages ──────────────────────────────────────────────
resp     = slack.conversations_history(channel=CHANNEL_ID, limit=5)
messages = resp["messages"]

# ── 2. Parse each message for session ID and Z3 items ────────────────────────
SESSION_RE  = re.compile(r'S-\d{6}-\d+')
SEVERITY_MAP = {
    "⚠️": "WARN",
    "🚫": "BLOCKED",
    "🔴": "CRITICAL",
}

def extract_severity(line: str) -> str:
    for emoji, level in SEVERITY_MAP.items():
        if emoji in line:
            return level
    if "CRITICAL" in line.upper():
        return "CRITICAL"
    return "WARN"

def parse_z3_block(text: str, session_id: str) -> list[dict]:
    items = []
    in_z3 = False
    for line in text.splitlines():
        if "ZONE 3 QUEUE" in line or "Z3 QUEUE" in line:
            in_z3 = True
            continue
        if in_z3:
            # Stop at next section divider or empty emoji-header line
            if line.startswith("━") or (line.startswith(":") and ":" in line[1:] and "_" in line):
                break
            stripped = line.strip(" •·\t")
            if len(stripped) < 8:
                continue
            # Skip sub-headers like "NEW THIS SESSION" / "CARRIED"
            if stripped.isupper() or stripped.startswith("_"):
                continue
            items.append({
                "title":          stripped[:500],
                "severity":       extract_severity(stripped),
                "source_session": session_id,
                "owner":          "zone3",
                "verification_kind": "wgs_sync",
                "verification_target": {},
            })
    return items

# ── 3. Collect all items across messages ─────────────────────────────────────
all_items = []
for msg in messages:
    text = msg.get("text", "")
    sessions = SESSION_RE.findall(text)
    session_id = sessions[0] if sessions else "UNKNOWN"
    all_items.extend(parse_z3_block(text, session_id))

if not all_items:
    print("No Z3 items found in recent WGS messages.")
    raise SystemExit(0)

# ── 4. Upsert into zone3_queue (keyed on title + source_session) ─────────────
for item in all_items:
    # Check if already exists
    existing = (
        supabase.table("zone3_queue")
        .select("id, carry_count")
        .eq("title", item["title"])
        .eq("source_session", item["source_session"])
        .is_("resolved_at", "null")
        .execute()
    )
    if existing.data:
        # Increment carry_count on re-encounter
        row_id = existing.data[0]["id"]
        carry  = existing.data[0]["carry_count"] or 0
        supabase.table("zone3_queue").update({
            "carry_count": carry + 1,
            "severity":    item["severity"],
        }).eq("id", row_id).execute()
        print(f"CARRY+1: {item['title'][:60]}")
    else:
        supabase.table("zone3_queue").insert(item).execute()
        print(f"NEW: {item['title'][:60]}")

print(f"Sync complete. {len(all_items)} items processed.")

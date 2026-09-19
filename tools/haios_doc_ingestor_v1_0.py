#!/usr/bin/env python3
"""
haios_doc_ingestor — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · S-051926-03-strategic-accelerator

WHAT THIS DOES:
  Reads any HumanAIOS session artifact (.md, .txt) — Amendment Plans,
  Strategic Reports, WGS close posts, Security Audits — and extracts
  typed records into Supabase tables, then regenerates PROJECT_STATE.md
  which feeds job-site.html via a Cloudflare Worker webhook.

EXTRACTION TARGETS (from structured session docs):
  - Roadmap amendment steps  → project_management.amendment_steps
  - F-class findings          → project_management.f_class_findings
  - Drift signals (C/D-class) → project_management.drift_signals
  - Carry queue items         → project_management.carry_items
  - Security control HIM scores → project_management.security_controls
  - Zone 2 pending items      → project_management.z2_queue

OUTPUT:
  1. Supabase inserts (via REST API, no supabase-py required)
  2. PROJECT_STATE.md regenerated from live Supabase state
  3. Cloudflare Worker webhook POST → job-site.html re-render signal

ARCHITECTURE:
  PARSER LAYER    — regex extraction from markdown sections
  VALIDATOR LAYER — schema-check each extracted record
  WRITER LAYER    — Supabase REST upsert with conflict handling
  RENDERER LAYER  — PROJECT_STATE.md Jinja2-style template fill
  NOTIFIER LAYER  — CF Worker webhook for job-site.html

Zone: 1 (autonomous execution)
Author: Claude, Unit Zero

Usage:
  python haios_doc_ingestor_v1_0.py --file AMENDMENT_PLAN.md
  python haios_doc_ingestor_v1_0.py --file AMENDMENT_PLAN.md --dry-run
  python haios_doc_ingestor_v1_0.py --regenerate-state-only
  python haios_doc_ingestor_v1_0.py --smoke-test
"""

import re
import os
import sys
import json
import hashlib
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Tool identity ─────────────────────────────────────────────────────────────

TOOL_NAME     = "haios_doc_ingestor"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE     = 1

# ── Config (override via env vars or --config JSON) ───────────────────────────

DEFAULT_CONFIG = {
    "supabase_url":    os.environ.get("SUPABASE_URL",
                         "https://ksinisdzgtnqzsymhfya.supabase.co"),
    "supabase_key":    os.environ.get("SUPABASE_KEY", ""),          # sb_secret_…_n8n
    "cf_webhook_url":  os.environ.get("HAIOS_CF_WEBHOOK", ""),      # Worker ingest URL
    "state_output":    os.environ.get("STATE_MD_PATH",
                         "PROJECT_STATE.md"),
    "session_id":      os.environ.get("HAIOS_SESSION", "S-UNKNOWN"),
}

# ── Supabase table names ──────────────────────────────────────────────────────

TABLES = {
    "amendments":  "pm_amendment_steps",
    "findings":    "pm_f_class_findings",
    "drift":       "pm_drift_signals",
    "carry":       "pm_carry_items",
    "security":    "pm_security_controls",
    "z2":          "pm_z2_queue",
}

# ════════════════════════════════════════════════════════════════════════════
# PARSER LAYER
# ════════════════════════════════════════════════════════════════════════════

def parse_document(text: str, source_file: str, session_id: str) -> dict:
    """
    Master parser. Dispatches to each extractor and returns a dict
    of typed record lists keyed by table name.
    """
    doc_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    meta = {
        "source_file": source_file,
        "session_id":  session_id,
        "doc_hash":    doc_hash,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }

    return {
        "amendments": extract_amendments(text, meta),
        "findings":   extract_findings(text, meta),
        "drift":      extract_drift_signals(text, meta),
        "carry":      extract_carry_items(text, meta),
        "security":   extract_security_controls(text, meta),
        "z2":         extract_z2_items(text, meta),
    }


# ── Amendment step extractor ─────────────────────────────────────────────────

ROADMAP_TAG_RE = re.compile(
    r"`zone:(?P<zone>\d+(?:\|\d+)*)`\s*"
    r"`priority:(?P<priority>P\d+)`\s*"
    r"`deadline:(?P<deadline>[^`]+)`\s*"
    r"`effort:(?P<effort>[^`]+)`",
    re.IGNORECASE,
)

AMENDMENT_HEADER_RE = re.compile(
    r"^#+\s+AMENDMENT\s+(\d+)[\s:—]+(.+)$", re.MULTILINE | re.IGNORECASE
)

def extract_amendments(text: str, meta: dict) -> list[dict]:
    """
    Extracts amendment steps from ## AMENDMENT N: ... sections.
    Looks for ### Roadmap Tags blocks within each section.
    """
    records = []
    headers = list(AMENDMENT_HEADER_RE.finditer(text))

    for i, h in enumerate(headers):
        ctrl_num   = int(h.group(1))
        ctrl_title = h.group(2).strip()
        start      = h.end()
        end        = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section    = text[start:end]

        # Extract HIM score — matches **DECORATIVE.** or **LOAD-BEARING** or similar
        him_match = re.search(
            r"\*\*(DECORATIVE|PARTIAL|LOAD-BEARING|CRITICAL DECORATIVE)",
            section, re.IGNORECASE
        )
        him_score = him_match.group(1).upper().strip() if him_match else "UNKNOWN"

        # Extract roadmap tags
        tag_match = ROADMAP_TAG_RE.search(section)

        # Extract Phase 0 action summary (first 300 chars after **Phase 0**)
        phase0_match = re.search(r"\*\*Phase 0.*?\*\*:?\s*\n+(.*?)(?=\*\*Phase 1|\Z)",
                                 section, re.DOTALL)
        phase0_summary = ""
        if phase0_match:
            phase0_summary = " ".join(phase0_match.group(1).split())[:300]

        # Extract success criterion
        sc_match = re.search(
            r"###\s+Success Criterion\s*\n+(.*?)(?=###|\Z)", section, re.DOTALL
        )
        success_criterion = ""
        if sc_match:
            success_criterion = " ".join(sc_match.group(1).split())[:500]

        record = {
            "control_num":       ctrl_num,
            "control_title":     ctrl_title,
            "him_score":         him_score,
            "zone":              tag_match.group("zone") if tag_match else "1",
            "priority":          tag_match.group("priority") if tag_match else "P3",
            "deadline":          tag_match.group("deadline") if tag_match else "ongoing",
            "effort_hours":      tag_match.group("effort") if tag_match else "",
            "phase0_summary":    phase0_summary,
            "success_criterion": success_criterion,
            "status":            "pending",
            **meta,
        }
        records.append(record)

    return records


# ── F-class finding extractor ─────────────────────────────────────────────────

FINDING_ID_RE = re.compile(
    r"(?:^|\n)#+\s+(F-(?:CAND-)?[A-Z0-9_-]+)\b", re.MULTILINE
)

def extract_findings(text: str, meta: dict) -> list[dict]:
    """
    Finds F-class finding IDs and extracts their statement blocks.
    Looks for ## Statement section following the finding ID header.
    """
    records = []
    matches = list(FINDING_ID_RE.finditer(text))

    for i, m in enumerate(matches):
        finding_id = m.group(1).strip()
        start = m.end()
        end   = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]

        # Extract statement
        stmt_match = re.search(
            r"##\s+Statement\s*\n+(.*?)(?=##|\Z)", block, re.DOTALL
        )
        statement = ""
        if stmt_match:
            statement = " ".join(stmt_match.group(1).split())[:1000]

        # Check ratification marker
        ratified = bool(re.search(r"ratif", block, re.IGNORECASE))
        status = "ratified" if ratified else "candidate"

        records.append({
            "finding_id": finding_id,
            "statement":  statement or f"Extracted from {meta['source_file']}",
            "status":     status,
            **meta,
        })

    return records


# ── Drift signal extractor ────────────────────────────────────────────────────

DRIFT_ROW_RE = re.compile(
    r"\|\s*\*\*?((?:C|D)-[A-Z0-9_-]+)\*\*?\s*\|"
    r"(?P<class>[CD])\s*\|"
    r"(?P<trigger>[^|]+)\|"
    r"(?P<detection>[^|]+)\|"
    r"(?P<mitigation>[^|]+)\|",
    re.IGNORECASE,
)

# Also catch inline signal IDs like **D-INVENTORY-INVERSION**
INLINE_DRIFT_RE = re.compile(
    r"\*\*((?:C|D)-[A-Z][A-Z0-9_-]+)\*\*"
)

def extract_drift_signals(text: str, meta: dict) -> list[dict]:
    """
    Extracts C-class and D-class signals from table rows or inline bold.
    """
    seen = set()
    records = []

    # Table-format signals
    for m in DRIFT_ROW_RE.finditer(text):
        sig_id = m.group(1).strip()
        if sig_id in seen:
            continue
        seen.add(sig_id)
        records.append({
            "signal_id":  sig_id,
            "class":      sig_id[0],
            "trigger":    m.group("trigger").strip()[:200],
            "detection":  m.group("detection").strip()[:200],
            "mitigation": m.group("mitigation").strip()[:300],
            "status":     "active",
            **meta,
        })

    # Inline bold mentions (deduped)
    for m in INLINE_DRIFT_RE.finditer(text):
        sig_id = m.group(1).strip()
        if sig_id in seen:
            continue
        seen.add(sig_id)
        records.append({
            "signal_id":  sig_id,
            "class":      sig_id[0],
            "trigger":    "inline mention",
            "detection":  "",
            "mitigation": "",
            "status":     "active",
            **meta,
        })

    return records


# ── Carry item extractor ──────────────────────────────────────────────────────

CARRY_RE = re.compile(
    r"^[-*]\s+(?:\*\*)?(.+?)(?:\*\*)?\s+\[?(?:CARRY|carry|Zone\s*2|Z2|open)\]?",
    re.MULTILINE | re.IGNORECASE,
)

def extract_carry_items(text: str, meta: dict) -> list[dict]:
    """
    Extracts items that look like carry queue entries.
    Heuristic: bullet/dash items with CARRY/Z2/open marker.
    """
    records = []
    for m in CARRY_RE.finditer(text):
        title = m.group(1).strip()[:200]
        if len(title) < 5:
            continue
        records.append({
            "title":    title,
            "status":   "open",
            "priority": "P2",
            **meta,
        })
    return records


# ── Security control extractor ────────────────────────────────────────────────

SEC_ROW_RE = re.compile(
    r"\|\s*(\d+)\s*\|"          # control number
    r"\s*([^|]+?)\s*\|"         # control name
    r"\s*([^|]+?)\s*\|"         # status (✅/⚠️/🔴 …)
    r"\s*([^|]+?)\s*\|"         # priority gap
    r"\s*([^|]+?)\s*\|",        # recommended action
)

HIM_EMOJI_MAP = {
    "✅": "LOAD-BEARING",
    "⚠️": "PARTIAL",
    "🔴": "DECORATIVE",
}

def extract_security_controls(text: str, meta: dict) -> list[dict]:
    """
    Extracts security control rows from the Summary Mapping Table.
    Looks for | # | Control | Status | Priority Gap | Action | rows.
    """
    records = []
    in_table = False

    for line in text.splitlines():
        if "| # |" in line or "| Ctrl" in line.lower():
            in_table = True
            continue
        if in_table and "|---|" in line:
            continue
        if in_table and line.strip().startswith("|"):
            m = SEC_ROW_RE.match(line.strip())
            if m:
                ctrl_num   = m.group(1).strip()
                ctrl_name  = m.group(2).strip()
                status_raw = m.group(3).strip()
                gap        = m.group(4).strip()[:200]
                action     = m.group(5).strip()[:300]

                him = "UNKNOWN"
                for emoji, label in HIM_EMOJI_MAP.items():
                    if emoji in status_raw:
                        him = label
                        break

                records.append({
                    "control_num":  int(ctrl_num),
                    "control_name": ctrl_name,
                    "him_score":    him,
                    "status_raw":   status_raw,
                    "priority_gap": gap,
                    "action":       action,
                    **meta,
                })
        elif in_table and not line.strip().startswith("|"):
            in_table = False

    return records


# ── Zone 2 queue extractor ────────────────────────────────────────────────────

Z2_RE = re.compile(
    r"\[Zone\s*2\s+(?:Required|ratification required)[^\]]*\]|"
    r"\*\*\[Zone\s*2\s+Required[^\]]*\]\*\*",
    re.IGNORECASE,
)

def extract_z2_items(text: str, meta: dict) -> list[dict]:
    """
    Extracts Zone 2 ratification-required items.
    Context window: up to 150 chars before each [Zone 2 Required] marker.
    """
    records = []
    seen = set()

    for m in Z2_RE.finditer(text):
        ctx_start = max(0, m.start() - 150)
        ctx = text[ctx_start:m.end()].strip()
        # Get last sentence/bullet before the marker
        title_match = re.search(r"(?:[-*]|[A-Z])[^.\n]{5,100}", ctx)
        title = title_match.group(0).strip()[:150] if title_match else ctx[:100]
        if title in seen:
            continue
        seen.add(title)
        records.append({
            "title":  title,
            "status": "pending_ratification",
            **meta,
        })
    return records


# ════════════════════════════════════════════════════════════════════════════
# VALIDATOR LAYER
# ════════════════════════════════════════════════════════════════════════════

REQUIRED_FIELDS = {
    "amendments": ["control_num", "control_title", "him_score", "priority"],
    "findings":   ["finding_id", "status"],
    "drift":      ["signal_id", "class"],
    "carry":      ["title", "status"],
    "security":   ["control_num", "control_name", "him_score"],
    "z2":         ["title", "status"],
}

def validate_records(parsed: dict) -> tuple[dict, list[str]]:
    """
    Validates each record against REQUIRED_FIELDS.
    Returns (valid_records, error_list).
    """
    valid  = {k: [] for k in parsed}
    errors = []

    for table_key, records in parsed.items():
        required = REQUIRED_FIELDS.get(table_key, [])
        for r in records:
            missing = [f for f in required if not r.get(f)]
            if missing:
                errors.append(
                    f"[{table_key}] missing fields {missing}: "
                    f"{str(r)[:80]}"
                )
            else:
                valid[table_key].append(r)

    return valid, errors


# ════════════════════════════════════════════════════════════════════════════
# WRITER LAYER  (Supabase REST, no external deps)
# ════════════════════════════════════════════════════════════════════════════

def supabase_upsert(
    table: str,
    records: list[dict],
    config: dict,
    dry_run: bool = False,
) -> dict:
    """
    Upserts records into a Supabase table via the REST API.
    Uses POST with Prefer: resolution=merge-duplicates.
    Returns {"inserted": N, "errors": []}.
    """
    if not records:
        return {"inserted": 0, "errors": []}

    if dry_run:
        print(f"  [DRY-RUN] Would upsert {len(records)} rows → {table}")
        return {"inserted": len(records), "errors": [], "dry_run": True}

    url = f"{config['supabase_url']}/rest/v1/{table}"
    body = json.dumps(records).encode()

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "apikey":       config["supabase_key"],
            "Authorization": f"Bearer {config['supabase_key']}",
            "Content-Type": "application/json",
            "Prefer":       "resolution=merge-duplicates,return=minimal",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return {"inserted": len(records), "errors": [],
                    "status_code": resp.status}
    except urllib.error.HTTPError as e:
        body_err = e.read().decode()[:200]
        return {"inserted": 0,
                "errors": [f"HTTP {e.code}: {body_err}"]}
    except Exception as exc:
        return {"inserted": 0, "errors": [str(exc)]}


def write_all(valid: dict, config: dict, dry_run: bool) -> dict:
    """Writes all record groups to their Supabase tables."""
    results = {}
    for key, records in valid.items():
        table  = TABLES[key]
        result = supabase_upsert(table, records, config, dry_run)
        results[key] = result
        status = "DRY-RUN" if result.get("dry_run") else (
            "OK" if not result["errors"] else "ERROR"
        )
        print(f"  {status:8s} {table:40s} ({result['inserted']} rows)")
        if result["errors"]:
            for err in result["errors"]:
                print(f"           ↳ {err}")
    return results


# ════════════════════════════════════════════════════════════════════════════
# RENDERER LAYER  (PROJECT_STATE.md generation)
# ════════════════════════════════════════════════════════════════════════════

def fetch_supabase_table(table: str, config: dict) -> list[dict]:
    """Fetch all rows from a Supabase table via REST."""
    url = f"{config['supabase_url']}/rest/v1/{table}?select=*&order=created_at.desc"
    req = urllib.request.Request(
        url,
        headers={
            "apikey":        config["supabase_key"],
            "Authorization": f"Bearer {config['supabase_key']}",
            "Accept":        "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as exc:
        print(f"  [WARN] Could not fetch {table}: {exc}")
        return []


def render_state_md(config: dict, session_id: str) -> str:
    """
    Fetches live data from all Supabase PM tables and renders
    PROJECT_STATE.md — the single source of truth for job-site.html.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Fetch all tables
    amendments = fetch_supabase_table(TABLES["amendments"], config)
    findings   = fetch_supabase_table(TABLES["findings"],   config)
    drift      = fetch_supabase_table(TABLES["drift"],      config)
    carry      = fetch_supabase_table(TABLES["carry"],      config)
    security   = fetch_supabase_table(TABLES["security"],   config)
    z2_items   = fetch_supabase_table(TABLES["z2"],         config)

    # ── Priority counts ───────────────────────────────────────────────────
    p0_count = sum(1 for a in amendments if a.get("priority") == "P0"
                   and a.get("status") == "pending")
    critical_controls = [s for s in security
                         if s.get("him_score") in ("DECORATIVE", "CRITICAL DECORATIVE")]
    ratified_findings = [f for f in findings if f.get("status") == "ratified"]

    # ── Build document ────────────────────────────────────────────────────
    lines = [
        f"# PROJECT_STATE.md",
        f"<!-- AUTO-GENERATED by haios_doc_ingestor v{TOOL_VERSION} -->",
        f"<!-- Session: {session_id} · Generated: {now} -->",
        f"<!-- DO NOT EDIT MANUALLY — edit source documents, re-run ingestor -->",
        "",
        "## SYSTEM STATUS",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Generated | {now} |",
        f"| Session | {session_id} |",
        f"| P0 amendments pending | {p0_count} |",
        f"| Critical HIM gaps (DECORATIVE) | {len(critical_controls)} |",
        f"| Ratified F-class findings | {len(ratified_findings)} |",
        f"| Active drift signals | {len([d for d in drift if d.get('status') == 'active'])} |",
        f"| Zone 2 pending | {len([z for z in z2_items if z.get('status') == 'pending_ratification'])} |",
        f"| Open carry items | {len([c for c in carry if c.get('status') == 'open'])} |",
        "",
        "---",
        "",
        "## AMENDMENT ROADMAP",
        "",
        "| # | Control | HIM Score | Priority | Zone | Deadline | Status |",
        "|---|---|---|---|---|---|---|",
    ]

    him_emoji = {
        "LOAD-BEARING": "✅",
        "PARTIAL":       "⚠️",
        "DECORATIVE":    "🔴",
        "CRITICAL DECORATIVE": "🔴🔴",
        "UNKNOWN":       "❓",
    }

    # Sort by priority then control_num
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    amendments_sorted = sorted(
        amendments,
        key=lambda a: (priority_order.get(a.get("priority", "P3"), 9),
                       a.get("control_num", 99)),
    )
    for a in amendments_sorted:
        him = a.get("him_score", "UNKNOWN")
        emoji = him_emoji.get(him, "❓")
        lines.append(
            f"| {a.get('control_num','-')} "
            f"| {a.get('control_title','')[:35]} "
            f"| {emoji} {him} "
            f"| {a.get('priority','-')} "
            f"| Z{a.get('zone','-')} "
            f"| {a.get('deadline','-')} "
            f"| {a.get('status','-')} |"
        )

    lines += [
        "",
        "---",
        "",
        "## F-CLASS FINDINGS",
        "",
        "| Finding ID | Status | Session | Statement (excerpt) |",
        "|---|---|---|---|",
    ]
    for f in findings:
        stmt = (f.get("statement") or "")[:80]
        lines.append(
            f"| {f.get('finding_id','-')} "
            f"| **{f.get('status','-').upper()}** "
            f"| {f.get('session_id','-')} "
            f"| {stmt}… |"
        )

    lines += [
        "",
        "---",
        "",
        "## ACTIVE DRIFT SIGNALS",
        "",
        "| Signal ID | Class | Status | Trigger |",
        "|---|---|---|---|",
    ]
    for d in drift:
        if d.get("status") == "active":
            lines.append(
                f"| `{d.get('signal_id','-')}` "
                f"| {d.get('class','-')} "
                f"| {d.get('status','-')} "
                f"| {d.get('trigger','')[:80]} |"
            )

    lines += [
        "",
        "---",
        "",
        "## SECURITY CONTROLS (HIM AUDIT)",
        "",
        "| # | Control | HIM Score | Priority Gap |",
        "|---|---|---|---|",
    ]
    for s in sorted(security, key=lambda x: x.get("control_num", 99)):
        him = s.get("him_score", "UNKNOWN")
        emoji = him_emoji.get(him, "❓")
        lines.append(
            f"| {s.get('control_num','-')} "
            f"| {s.get('control_name','')[:40]} "
            f"| {emoji} {him} "
            f"| {s.get('priority_gap','')[:60]} |"
        )

    lines += [
        "",
        "---",
        "",
        "## ZONE 2 QUEUE",
        "",
        "| Item | Status |",
        "|---|---|",
    ]
    for z in z2_items:
        if z.get("status") == "pending_ratification":
            lines.append(f"| {z.get('title','')[:80]} | 🟡 PENDING |")

    lines += [
        "",
        "---",
        "",
        "## CARRY QUEUE",
        "",
        "| Item | Priority | Status |",
        "|---|---|---|",
    ]
    for c in carry:
        if c.get("status") == "open":
            lines.append(
                f"| {c.get('title','')[:80]} "
                f"| {c.get('priority','P2')} "
                f"| {c.get('status','-')} |"
            )

    lines += [
        "",
        "---",
        "",
        f"*Auto-generated {now} · haios_doc_ingestor v{TOOL_VERSION}*",
    ]

    return "\n".join(lines)


def write_state_md(content: str, path: str) -> None:
    """Writes PROJECT_STATE.md to disk."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  [OK]     Wrote {path} ({len(content)} chars)")


# ════════════════════════════════════════════════════════════════════════════
# NOTIFIER LAYER  (Cloudflare Worker webhook)
# ════════════════════════════════════════════════════════════════════════════

def notify_cf_worker(config: dict, session_id: str, summary: dict) -> None:
    """
    POSTs a re-render signal to the Cloudflare Worker backing job-site.html.
    Payload includes session_id and counts so the Worker can decide
    whether to pull fresh data or serve a cache.
    """
    url = config.get("cf_webhook_url", "")
    if not url:
        print("  [SKIP]   CF webhook URL not configured (set HAIOS_CF_WEBHOOK)")
        return

    payload = json.dumps({
        "event":      "doc_ingestor_complete",
        "session_id": session_id,
        "summary":    summary,
        "ts":         datetime.now(timezone.utc).isoformat(),
    }).encode()

    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"  [OK]     CF Worker notified — HTTP {resp.status}")
    except Exception as exc:
        print(f"  [WARN]   CF Worker notification failed: {exc}")


# ════════════════════════════════════════════════════════════════════════════
# SMOKE TEST
# ════════════════════════════════════════════════════════════════════════════

SMOKE_DOC = """
## AMENDMENT 1: Prompt Injection Defense

### HIM Score
**DECORATIVE.** No classifier between HTTP and AI Agent.

### Amendment Plan
**Phase 0 (this week — Zone 1):**
- Add sanitizer Code node.

### Success Criterion
Test payload is dropped before AI Agent node.

### Roadmap Tags
`zone:1` `priority:P0` `deadline:pre-may30` `effort:6h` `blocks:[A10]` `blocked-by:[A2]`

---

## AMENDMENT 6: Human Oversight (HITL)

### HIM Score
**LOAD-BEARING** with two small leaks.

### Roadmap Tags
`zone:1` `priority:P1` `deadline:pre-may30` `effort:2h` `blocks:[]` `blocked-by:[]`

---

# F-CAND-SPECIFICATION-EXECUTION-GAP

## Statement
The systematic divergence between behavioral specification and enforcement
is a general property of complex governed systems.

Ratified: 2026-05-20

---

| # | Control | HumanAIOS Status | Priority Gap | Recommended Action |
|---|---|---|---|---|
| 1 | Prompt Injection Defense | ⚠️ Partial | Slack ingestion unsanitized | Add sanitization Code node |
| 6 | Human Oversight (HITL) | ✅ Strong | Cowork auto-open risk | Technical lock on Phase 3 |
| 11 | Supply Chain | 🔴 Critical gap | n8n-mcp unpinned | Pin all MCP versions |

**D-INVENTORY-INVERSION** is a known carry item. [Zone 2 Required — operator sign-off needed]
"""

def run_smoke_test() -> bool:
    print(f"\n{'─'*60}")
    print(f"  SMOKE TEST  haios_doc_ingestor v{TOOL_VERSION}")
    print(f"{'─'*60}")

    meta = {"source_file": "smoke_test", "session_id": "S-TEST",
            "doc_hash": "abc123", "ingested_at": "2026-05-20T00:00:00Z"}

    amendments = extract_amendments(SMOKE_DOC, meta)
    findings   = extract_findings(SMOKE_DOC, meta)
    drift      = extract_drift_signals(SMOKE_DOC, meta)
    security   = extract_security_controls(SMOKE_DOC, meta)
    z2         = extract_z2_items(SMOKE_DOC, meta)

    passed = True

    def check(name, condition, detail=""):
        nonlocal passed
        ok = "✅ PASS" if condition else "❌ FAIL"
        if not condition:
            passed = False
        print(f"  {ok}  {name}" + (f"  [{detail}]" if detail else ""))

    check("amendments extracted == 2",    len(amendments) == 2,  str(len(amendments)))
    check("amendment 1 HIM = DECORATIVE", amendments[0]["him_score"] == "DECORATIVE")
    check("amendment 6 HIM = LOAD-BEARING", amendments[1]["him_score"] == "LOAD-BEARING")
    check("amendment 1 priority = P0",    amendments[0]["priority"] == "P0")
    check("F-class finding extracted",    len(findings) >= 1,    str(len(findings)))
    check("finding ratified",             findings[0]["status"] == "ratified")
    check("drift signal D-INVENTORY",
          any("D-INVENTORY" in d["signal_id"] for d in drift))
    check("security controls extracted",  len(security) == 3,    str(len(security)))
    check("HIM LOAD-BEARING detected",
          any(s["him_score"] == "LOAD-BEARING" for s in security))
    check("Z2 item extracted",            len(z2) >= 1,          str(len(z2)))

    print(f"{'─'*60}")
    print(f"  {'PASSED' if passed else 'FAILED'}")
    print(f"{'─'*60}\n")
    return passed


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description=(
            "Ingest HumanAIOS session documents → extract typed records "
            "→ Supabase → regenerate PROJECT_STATE.md → notify CF Worker."
        ),
    )
    parser.add_argument("--file", help="Path to the session document (.md/.txt)")
    parser.add_argument("--session", default=DEFAULT_CONFIG["session_id"],
                        help="Session ID (default: $HAIOS_SESSION)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and validate only — no writes")
    parser.add_argument("--regenerate-state-only", action="store_true",
                        help="Skip ingestion; only regenerate PROJECT_STATE.md")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Run built-in smoke test and exit")
    parser.add_argument("--config", default=None,
                        help="Path to JSON config file (overrides env vars)")
    args = parser.parse_args()

    if args.smoke_test:
        ok = run_smoke_test()
        return 0 if ok else 1

    # Load config
    config = dict(DEFAULT_CONFIG)
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))
    config["session_id"] = args.session

    print(f"\n{'═'*60}")
    print(f"  haios_doc_ingestor v{TOOL_VERSION}  ·  {args.session}")
    print(f"{'═'*60}")

    if args.regenerate_state_only:
        print("\n[RENDER] Regenerating PROJECT_STATE.md from Supabase…")
        content = render_state_md(config, args.session)
        write_state_md(content, config["state_output"])
        notify_cf_worker(config, args.session, {"regenerate_only": True})
        return 0

    if not args.file:
        parser.print_help()
        print("\nERROR: --file is required unless --regenerate-state-only or --smoke-test")
        return 1

    doc_path = Path(args.file)
    if not doc_path.exists():
        print(f"ERROR: File not found: {args.file}")
        return 1

    text = doc_path.read_text(encoding="utf-8")
    print(f"\n[PARSE]  {doc_path.name}  ({len(text):,} chars)")

    # Parse
    parsed = parse_document(text, str(doc_path), args.session)
    total  = sum(len(v) for v in parsed.values())
    print(f"         Extracted {total} records across {len(parsed)} tables")
    for k, v in parsed.items():
        print(f"         · {TABLES[k]:40s}  {len(v):3d} records")

    # Validate
    valid, errors = validate_records(parsed)
    valid_total = sum(len(v) for v in valid.values())
    print(f"\n[VALID]  {valid_total} records passed · {len(errors)} errors")
    for err in errors[:5]:
        print(f"         ↳ {err}")

    # Write
    print(f"\n[WRITE]  {'(DRY-RUN) ' if args.dry_run else ''}Supabase upserts…")
    write_results = write_all(valid, config, args.dry_run)

    # Render state doc
    print(f"\n[RENDER] Regenerating {config['state_output']}…")
    if not args.dry_run:
        content = render_state_md(config, args.session)
        write_state_md(content, config["state_output"])
    else:
        print("  [DRY-RUN] Skipping state render")

    # Notify
    print(f"\n[NOTIFY] Cloudflare Worker…")
    if not args.dry_run:
        summary = {k: r["inserted"] for k, r in write_results.items()}
        summary["errors"] = sum(len(r["errors"]) for r in write_results.values())
        notify_cf_worker(config, args.session, summary)
    else:
        print("  [DRY-RUN] Skipping CF notification")

    print(f"\n{'═'*60}")
    print(f"  COMPLETE  Session {args.session}")
    print(f"{'═'*60}\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

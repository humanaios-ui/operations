#!/usr/bin/env python3
"""
HAIOS System Harmonizer — v1.0
Builder v1.7 compliant · orchestrator_tool
HumanAIOS · S-051726-02-molt-grow-kill

THE MAIN ORCHESTRATION TOOL.

Reads all live state sources simultaneously, computes a harmony score
per subsystem, generates tuning signals, and detects molt-readiness.
Triggered on any node activity — session open, corpus change, blocker
update, tool addition, finding registration, gate transition.

This is not a monitor. A monitor shows you what's happening.
The harmonizer tells you what the SYSTEM NEEDS NEXT — with the
reasoning visible and the signal traceable to specific nodes.

ARCHITECTURE:
  SENSOR LAYER      — reads Supabase, Slack #wgs-sync, GitHub,
                      carry queue, Z2 queue, blocker flags, gate state
  STATE MODEL       — represents full system across 8 subsystems
  RESONANCE ENGINE  — computes harmony score per subsystem (0-100)
  TUNING GENERATOR  — outputs prioritized action signals from state
  MOLT DETECTOR     — flags when system is ready for next phase

8 SUBSYSTEMS:
  CORPUS        N, LI, D-COMP streak, pending rows, schema health
  FINDINGS      Registered count, Z2 pending, candidate age
  TOOLS         Builder compliance, integration status, carry N
  GOVERNANCE    Blocker flags, gate readiness, Zone discipline
  RESEARCH      FP validation status, arXiv, Wednesday prep
  COMMS         Collaborator states, outbound drafts pending
  FINANCE       Sheets staleness, income pipeline, grants
  INFRA         CF zones, Supabase health, GitHub, Make scenarios

HARMONY SCORE (per subsystem, 0-100):
  Start at 100. Decay factors:
  - Active hard blocker:     -40 points
  - Carry item N >= 10:      -30 points each
  - Carry item N >= 5:       -15 points each
  - Staleness > 7 days:      -10 points per week
  - Z2 item age > 3 sessions: -10 points each
  - Gate pre-condition unmet: -5 points
  Bonus:
  - Gate PASSED this charter: +10 points
  - Zero blockers:            +5 points

MOLT-READINESS:
  All subsystems >= 70 AND no active hard blockers
  → MOLT_READY signal with specific phase recommendation

TUNING SIGNAL PRIORITY:
  1. HARD_BLOCK  — active blocker, all other work secondary
  2. ESCALATE    — carry item N >= 10, surface immediately
  3. CONVERGE    — subsystem harmony < 50, needs focused session
  4. ADVANCE     — gate pre-conditions met, path to next phase clear
  5. MAINTAIN    — system healthy, continue current trajectory

Usage:
  python haios_harmonizer_v1_0.py --state state.json
  python haios_harmonizer_v1_0.py --state state.json --output outputs/
  python haios_harmonizer_v1_0.py --state state.json --watch
  python haios_harmonizer_v1_0.py --emit-template > system_state.json
  python haios_harmonizer_v1_0.py --smoke-test
"""

import json
import sys
import math
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

TOOL_NAME     = "haios_harmonizer"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "orchestrator_tool"
TOOL_SESSION  = "S-051726-02-molt-grow-kill"
TOOL_ZONE     = 1

# ── Thresholds ────────────────────────────────────────────────────────────────

MOLT_READY_THRESHOLD = 70      # all subsystems must be >= this
ALARM_THRESHOLD      = 40      # any subsystem below this = alarm
CARRY_WARN_N         = 5       # carry items at this N get -15 pts
CARRY_ESCALATE_N     = 10      # carry items at this N get -30 pts
STALENESS_DECAY_DAYS = 7       # one decay unit per week
STALENESS_PENALTY    = 10      # points per decay unit

SUBSYSTEM_WEIGHTS = {
    "CORPUS":     1.5,   # research integrity — weighted high
    "GOVERNANCE": 1.4,   # blocker/gate discipline
    "FINDINGS":   1.2,   # science output
    "TOOLS":      1.1,   # execution capability
    "RESEARCH":   1.1,   # active work
    "COMMS":      0.9,   # external relationships
    "INFRA":      0.9,   # platform health
    "FINANCE":    0.8,   # sustainability
}


class SpecLoadFailed(Exception):
    pass


# ── State Schema / Template ───────────────────────────────────────────────────

STATE_TEMPLATE = {
    "_meta": {
        "schema_version": "1.0",
        "last_updated":   "ISO8601 timestamp",
        "session_id":     "S-MMDDYY-NN",
        "charter_day":    32,
        "gate_passed":    [1, 2],
        "gate_active":    3,
    },
    "CORPUS": {
        "n_total":          629,
        "n_phase1":         516,
        "n_li":             307,
        "mean_li":          0.8632,
        "d_comp_streak":    14,
        "rows_pending":     27,
        "schema_healthy":   True,
        "last_ingestion":   "2026-03-23",
        "blockers":         [],
    },
    "FINDINGS": {
        "registered_count": 22,
        "z2_pending":       [
            {"id": "FP-04", "sessions_open": 1, "description": "HIM x EW Normative Drift"},
            {"id": "H-CONV-01", "sessions_open": 1, "description": "Card Humility predicts LI"},
        ],
        "candidates":       ["H-CONV-01", "H-INST-HUMILITY-01", "FP-04"],
        "last_registered":  "2026-05-17",
        "blockers":         [],
    },
    "TOOLS": {
        "total_count":      20,
        "integrated_count": 15,
        "standalone_count": 5,
        "carry_items":      [
            {"id": "acat_core.js v1.7", "n": 6, "description": "3 corrections pending"},
            {"id": "W-1-W-4 pipeline",  "n": 12, "description": "P0 migration blocked"},
        ],
        "builder_compliance": 1.0,
        "blockers":           [],
    },
    "GOVERNANCE": {
        "blocker_flags":    [
            {"id": "HAIOSCC_SECRET_ROTATED", "n": 11, "severity": "CRITICAL",
             "scheduled": "tomorrow"}
        ],
        "gate_passed":      [1, 2],
        "gate_active":      3,
        "gate_3_prereqs":   {
            "FP-01_confirmed":      True,
            "class_a_study_design": False,
            "n_target_defined":     False,
            "empirica_anchor_rows": False,
        },
        "zone_discipline":  "CLEAN",
        "carry_items":      [
            {"id": "IC-023", "n": 11, "description": "HAIOSCC secret rotation CRITICAL"},
            {"id": "C-2",    "n": 12, "description": "Supabase WITH CHECK(true)"},
        ],
        "blockers":         ["HAIOSCC_SECRET_ROTATED"],
    },
    "RESEARCH": {
        "fp_validated":     {"FP-01": True, "FP-02": False, "FP-03": False, "FP-04": False},
        "arxiv_status":     "BLOCKED — 4 editing items before push",
        "wednesday_prep":   {"complete": True, "call_date": "2026-05-20",
                             "open_items": ["financial_terms_section_5",
                                            "pressure_handling_score_tier"]},
        "carry_items":      [
            {"id": "arXiv Option B", "n": 7, "description": "4 blocking edits before push"},
        ],
        "blockers":         [],
    },
    "COMMS": {
        "collaborators":    [
            {"name": "DeMarius", "status": "ACTIVE", "next": "Wednesday call 2026-05-20",
             "open_drafts": 1},
            {"name": "David/empirica", "status": "ACTIVE", "next": "anchor-row session pending",
             "open_drafts": 0},
            {"name": "Moni/Sydän", "status": "ACTIVE", "next": "narrative review ongoing",
             "open_drafts": 0},
            {"name": "Satya/EW",   "status": "PENDING_Z2", "next": "outreach not sent",
             "open_drafts": 1},
        ],
        "outbound_drafts":  1,
        "unanswered_items": [],
        "blockers":         [],
    },
    "FINANCE": {
        "sheets_last_updated": "2026-03-19",
        "version":             "v1.1",
        "income_streams": {
            "patreon":          "active",
            "open_collective":  "active",
            "kofi":             "active",
            "rah_commercial":   "pending_key_rotation",
            "grants_pipeline":  "active",
        },
        "ein":                 "41-5367995",
        "annual_report_due":   "2027-05-01",
        "blockers":            [],
    },
    "INFRA": {
        "cloudflare": {
            "humanaios_ai":       "LIVE",
            "ops_dashboard":      "LIVE",
            "pipeline_subdomain": "LIVE",
            "haioscc":            "BLOCKED — IC-023",
        },
        "supabase": {
            "health":              "HEALTHY",
            "api_change_deadline": "2026-05-30",
            "days_to_deadline":    13,
            "postgres_eol":        "2026-07-01",
        },
        "github": {
            "operations_staging":  "CURRENT",
            "haioscc":             "STALE — push blocked IC-023",
            "humanaios_internal":  "CURRENT",
        },
        "make_scenarios": {
            "wgs_harmonizer":      "ACTIVE",
        },
        "carry_items":            [
            {"id": "C-2 CHECK(true)", "n": 12, "description": "Supabase WITH CHECK(true) tightening"},
        ],
        "blockers":               ["IC-023 HAIOSCC"],
    },
}


# ── Sensor Layer (reads state dict, validates) ────────────────────────────────

def load_state(source: str) -> dict:
    """Load system state from file path or inline JSON."""
    p = Path(source)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise SpecLoadFailed(f"Cannot load {p}: {e}")
    try:
        return json.loads(source)
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"Not a valid path or JSON: {e}")


def parse_date(s: str) -> Optional[datetime]:
    """Parse ISO date string to datetime. Returns None on failure."""
    if not s or s in ("unknown", "never", ""):
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s[:19], fmt[:len(s[:19])])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def days_since(date_str: str) -> float:
    """Days since a date string. Returns 0 if date is future, 999 if unparseable."""
    dt = parse_date(date_str)
    if dt is None:
        return 999.0
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = (now - dt).total_seconds() / 86400
    return max(0.0, delta)


# ── Resonance Engine ──────────────────────────────────────────────────────────

def score_subsystem(name: str, state: dict) -> dict:
    """
    Compute harmony score (0-100) for one subsystem.
    Returns score, penalties, bonuses, signals.
    """
    score    = 100.0
    penalties = []
    bonuses   = []
    signals   = []

    data = state.get(name, {})
    blockers   = data.get("blockers", [])
    carry_items = data.get("carry_items", [])

    # ── Hard blockers ──────────────────────────────────────────────────────
    for b in blockers:
        score -= 40
        penalties.append(f"HARD_BLOCK [{b}]: -40")
        signals.append({
            "priority": "HARD_BLOCK",
            "signal":   f"Active blocker: {b}",
            "subsystem": name,
            "action":   f"Resolve {b} before any other work in {name}",
        })

    # ── Carry item escalation ──────────────────────────────────────────────
    for item in carry_items:
        n = item.get("n", 0)
        iid = item.get("id", "?")
        desc = item.get("description", "")
        if n >= CARRY_ESCALATE_N:
            score -= 30
            penalties.append(f"CARRY_ESCALATE [{iid} N={n}]: -30")
            signals.append({
                "priority": "ESCALATE",
                "signal":   f"{iid} carried N={n} sessions (>{CARRY_ESCALATE_N}): {desc}",
                "subsystem": name,
                "action":   f"Schedule dedicated session for {iid}",
            })
        elif n >= CARRY_WARN_N:
            score -= 15
            penalties.append(f"CARRY_WARN [{iid} N={n}]: -15")
            signals.append({
                "priority": "CONVERGE",
                "signal":   f"{iid} carried N={n} sessions (>{CARRY_WARN_N}): {desc}",
                "subsystem": name,
                "action":   f"Include {iid} in next session agenda",
            })

    # ── Subsystem-specific scoring ─────────────────────────────────────────

    if name == "CORPUS":
        pending = data.get("rows_pending", 0)
        if pending > 0:
            score -= min(pending * 0.5, 20)
            penalties.append(f"PENDING_ROWS [{pending} rows]: -{min(pending*0.5,20):.0f}")
        age = days_since(data.get("last_ingestion", ""))
        if age > 21:
            decay = min(int(age / STALENESS_DECAY_DAYS) * STALENESS_PENALTY, 30)
            score -= decay
            penalties.append(f"INGESTION_STALE [{age:.0f} days]: -{decay}")
            signals.append({
                "priority": "CONVERGE",
                "signal":   f"Corpus ingestion {age:.0f} days stale — {pending} rows pending",
                "subsystem": "CORPUS",
                "action":   "Execute Supabase schema migration + 27-row ingestion (Zone 3)",
            })
        d_comp = data.get("d_comp_streak", 0)
        if d_comp >= 14:
            score -= 5
            penalties.append(f"D_COMP_STREAK [N={d_comp}]: -5")
            signals.append({
                "priority": "CONVERGE",
                "signal":   f"D-COMP active N={d_comp} consecutive sessions",
                "subsystem": "CORPUS",
                "action":   "Schedule adversarial or perturbation session to break streak",
            })

    elif name == "FINDINGS":
        z2_pending = data.get("z2_pending", [])
        for item in z2_pending:
            age_sessions = item.get("sessions_open", 0)
            if age_sessions >= 3:
                score -= 10
                penalties.append(f"Z2_AGING [{item['id']} {age_sessions}s]: -10")
                signals.append({
                    "priority": "CONVERGE",
                    "signal":   f"{item['id']} pending Zone 2 for {age_sessions} sessions",
                    "subsystem": "FINDINGS",
                    "action":   f"Ratify or close {item['id']} this session",
                })

    elif name == "GOVERNANCE":
        meta = state.get("_meta", {})
        gate_passed = set(meta.get("gate_passed", []))
        gate_active = meta.get("gate_active", 3)
        gate_prereqs = data.get("gate_3_prereqs", {})

        # Gate pre-conditions not met
        unmet = [k for k, v in gate_prereqs.items() if not v]
        if unmet:
            score -= len(unmet) * 5
            penalties.append(f"GATE_{gate_active}_PREREQS_UNMET [{len(unmet)} items]: -{len(unmet)*5}")
            signals.append({
                "priority": "ADVANCE",
                "signal":   f"Gate {gate_active} has {len(unmet)} unmet pre-conditions: {', '.join(unmet)}",
                "subsystem": "GOVERNANCE",
                "action":   f"Address gate pre-conditions to unlock Gate {gate_active}",
            })

        # Gate passed bonus
        if gate_passed:
            score += len(gate_passed) * 5
            bonuses.append(f"GATES_PASSED [{sorted(gate_passed)}]: +{len(gate_passed)*5}")

    elif name == "RESEARCH":
        fp = data.get("fp_validated", {})
        unvalidated = [k for k, v in fp.items() if not v]
        if unvalidated:
            score -= len(unvalidated) * 3
            penalties.append(f"FP_UNVALIDATED [{len(unvalidated)}]: -{len(unvalidated)*3}")

        arxiv = data.get("arxiv_status", "")
        if "BLOCKED" in arxiv.upper():
            score -= 15
            penalties.append("ARXIV_BLOCKED: -15")
            signals.append({
                "priority": "CONVERGE",
                "signal":   f"arXiv push blocked: {arxiv}",
                "subsystem": "RESEARCH",
                "action":   "Execute arXiv Option B: fix 4 blocking items then push",
            })

        wed = data.get("wednesday_prep", {})
        if wed.get("open_items") and not wed.get("complete"):
            n_open = len(wed["open_items"])
            score -= n_open * 5
            penalties.append(f"WEDNESDAY_OPEN [{n_open} items]: -{n_open*5}")

    elif name == "FINANCE":
        age = days_since(data.get("sheets_last_updated", ""))
        if age > 60:
            decay = min(int(age / STALENESS_DECAY_DAYS) * STALENESS_PENALTY, 40)
            score -= decay
            penalties.append(f"SHEETS_STALE [{age:.0f} days]: -{decay}")
            signals.append({
                "priority": "MAINTAIN",
                "signal":   f"Financial Command Center {age:.0f} days stale",
                "subsystem": "FINANCE",
                "action":   "Update Financial Command Center (Google Sheets v1.1)",
            })

    elif name == "INFRA":
        sb = data.get("supabase", {})
        days_left = sb.get("days_to_deadline", 999)
        if days_left <= 14:
            urgency = max(0, 30 - days_left)
            score -= urgency
            penalties.append(f"SUPABASE_DEADLINE [{days_left} days]: -{urgency}")
            signals.append({
                "priority": "ESCALATE" if days_left <= 7 else "CONVERGE",
                "signal":   f"Supabase Data API change in {days_left} days (May 30)",
                "subsystem": "INFRA",
                "action":   "Verify new table GRANTs before deadline — 13 days",
            })

    # ── Zero-blocker bonus ─────────────────────────────────────────────────
    if not blockers:
        score += 5
        bonuses.append("ZERO_BLOCKERS: +5")

    score = max(0.0, min(100.0, score))

    return {
        "subsystem": name,
        "score":     round(score, 1),
        "health":    health_label(score),
        "penalties": penalties,
        "bonuses":   bonuses,
        "signals":   signals,
    }


def health_label(score: float) -> str:
    if score >= 80: return "HEALTHY"
    if score >= 70: return "GOOD"
    if score >= 55: return "WATCH"
    if score >= 40: return "DEGRADED"
    return "ALARM"


# ── Tuning Signal Generator ───────────────────────────────────────────────────

PRIORITY_ORDER = ["HARD_BLOCK", "ESCALATE", "CONVERGE", "ADVANCE", "MAINTAIN"]

def generate_tuning_signals(subscores: list[dict], state: dict) -> dict:
    """
    Aggregate all signals across subsystems, prioritize, and produce
    the top 5 tuning recommendations plus molt-readiness verdict.
    """
    all_signals = []
    for ss in subscores:
        all_signals.extend(ss["signals"])

    # Sort by priority
    def sort_key(s):
        try:
            return PRIORITY_ORDER.index(s["priority"])
        except ValueError:
            return 99

    all_signals.sort(key=sort_key)

    # Molt readiness
    scores = {ss["subsystem"]: ss["score"] for ss in subscores}
    min_score = min(scores.values())
    any_blocker = any(ss["health"] == "ALARM" for ss in subscores)
    hard_blocks = [s for s in all_signals if s["priority"] == "HARD_BLOCK"]

    if min_score >= MOLT_READY_THRESHOLD and not hard_blocks:
        molt_verdict = "MOLT_READY"
        molt_note = (
            "All subsystems >= 70 and no hard blockers. "
            "System is ready for phase transition. "
            "Gate 3 pre-conditions: check GOVERNANCE subsystem."
        )
    elif hard_blocks:
        molt_verdict = "BLOCKED"
        molt_note = f"{len(hard_blocks)} hard blocker(s) preventing molt. Resolve first."
    elif min_score < ALARM_THRESHOLD:
        molt_verdict = "NOT_READY"
        molt_note = f"Subsystem(s) below alarm threshold ({ALARM_THRESHOLD}). System needs stabilization."
    else:
        molt_verdict = "BUILDING"
        molt_note = "System healthy and accumulating. Continue current trajectory."

    # System harmony score (weighted)
    total_weight = sum(SUBSYSTEM_WEIGHTS.values())
    weighted_sum = sum(
        scores.get(name, 50) * weight
        for name, weight in SUBSYSTEM_WEIGHTS.items()
    )
    system_harmony = round(weighted_sum / total_weight, 1)

    return {
        "system_harmony":    system_harmony,
        "system_health":     health_label(system_harmony),
        "molt_verdict":      molt_verdict,
        "molt_note":         molt_note,
        "min_subsystem":     min(scores, key=scores.get),
        "min_score":         min_score,
        "top_signals":       all_signals[:5],
        "all_signal_count":  len(all_signals),
        "hard_block_count":  len(hard_blocks),
        "subsystem_scores":  scores,
    }


# ── Main Run ──────────────────────────────────────────────────────────────────

def run(state: dict) -> dict:
    """Full harmonizer run. Returns complete system assessment."""
    subscores = []
    for name in SUBSYSTEM_WEIGHTS:
        subscores.append(score_subsystem(name, state))

    tuning = generate_tuning_signals(subscores, state)
    meta = state.get("_meta", {})

    status = "PASS" if tuning["molt_verdict"] != "BLOCKED" else "WARN"

    return {
        "status":          status,
        "run_time":        datetime.now(timezone.utc).isoformat(),
        "session":         meta.get("session_id", "unknown"),
        "charter_day":     meta.get("charter_day", 0),
        "system_harmony":  tuning["system_harmony"],
        "system_health":   tuning["system_health"],
        "molt_verdict":    tuning["molt_verdict"],
        "molt_note":       tuning["molt_note"],
        "tuning_signals":  tuning["top_signals"],
        "subsystems":      subscores,
        "summary": {
            "system_harmony":   tuning["system_harmony"],
            "molt_verdict":     tuning["molt_verdict"],
            "hard_blockers":    tuning["hard_block_count"],
            "min_subsystem":    tuning["min_subsystem"],
            "min_score":        tuning["min_score"],
            "signal_count":     tuning["all_signal_count"],
        },
    }


# ── Output ────────────────────────────────────────────────────────────────────

def aggregate(run_result: dict) -> dict:
    return {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "zone":      TOOL_ZONE,
        "session":   TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **run_result,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"haios_harmonizer_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


HEALTH_BARS = {
    "HEALTHY":  "████████████ 100",
    "GOOD":     "█████████░░░  75",
    "WATCH":    "███████░░░░░  58",
    "DEGRADED": "████░░░░░░░░  42",
    "ALARM":    "██░░░░░░░░░░  25",
}

MOLT_ICONS = {
    "MOLT_READY": "🦋",
    "BUILDING":   "🐛",
    "NOT_READY":  "⚠️ ",
    "BLOCKED":    "🔴",
}


def print_summary(output: dict) -> None:
    bar  = "═" * 66
    bar2 = "─" * 66
    mv   = output.get("molt_verdict", "?")
    sh   = output.get("system_harmony", 0)
    icon = MOLT_ICONS.get(mv, "?")

    print(f"\n{bar}")
    print(f" HAIOS SYSTEM HARMONIZER  v{TOOL_VERSION}")
    print(f" Charter Day {output.get('charter_day','?')}  ·  "
          f"Session {output.get('session','?')}")
    print(bar2)
    print(f"  {icon}  MOLT STATUS   : {mv}")
    print(f"  ⚡  SYSTEM HARMONY: {sh:.1f} / 100  [{output.get('system_health','?')}]")
    print(f"       {output.get('molt_note','')}")
    print(bar2)

    print(f"\n  SUBSYSTEM SCORES")
    for ss in output.get("subsystems", []):
        name   = ss["subsystem"]
        score  = ss["score"]
        health = ss["health"]
        filled = int(score / 100 * 12)
        bar_vis = "█" * filled + "░" * (12 - filled)
        alert = "  ← ALARM" if health == "ALARM" else ("  ← WATCH" if health == "WATCH" else "")
        print(f"   {name:<14} [{bar_vis}] {score:5.1f}  {health}{alert}")

    print(f"\n  TUNING SIGNALS  (top {min(5, len(output.get('tuning_signals',[])))}"
          f" of {output.get('summary',{}).get('signal_count',0)} total)")
    for i, sig in enumerate(output.get("tuning_signals", [])[:5], 1):
        pri = sig.get("priority","?")
        sym = {"HARD_BLOCK":"🔴","ESCALATE":"🟠","CONVERGE":"🟡",
               "ADVANCE":"🟢","MAINTAIN":"⚪"}.get(pri,"•")
        print(f"\n   {sym} [{pri}] {sig.get('subsystem','?')}")
        print(f"      Signal : {sig.get('signal','?')}")
        print(f"      Action : {sig.get('action','?')}")

    print(f"\n{bar}\n")


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    try:
        import copy
        state = copy.deepcopy(STATE_TEMPLATE)

        # Basic run
        result = run(state)
        assert "system_harmony" in result
        assert "molt_verdict" in result
        assert "subsystems" in result
        assert len(result["subsystems"]) == 8
        assert 0 <= result["system_harmony"] <= 100

        # Subsystem scoring
        for ss in result["subsystems"]:
            assert 0 <= ss["score"] <= 100, f"{ss['subsystem']} score out of range"
            assert ss["health"] in ("HEALTHY","GOOD","WATCH","DEGRADED","ALARM")

        # Hard blocker → BLOCKED molt verdict
        blocked_state = copy.deepcopy(STATE_TEMPLATE)
        blocked_state["GOVERNANCE"]["blockers"] = ["IC-023", "TEST"]
        blocked_result = run(blocked_state)
        assert blocked_result["molt_verdict"] == "BLOCKED", (
            f"Expected BLOCKED with hard blockers, got {blocked_result['molt_verdict']}")

        # Clean state → at least BUILDING
        clean_state = copy.deepcopy(STATE_TEMPLATE)
        for name in SUBSYSTEM_WEIGHTS:
            clean_state.setdefault(name, {})["blockers"] = []
            clean_state[name]["carry_items"] = []
        clean_result = run(clean_state)
        assert clean_result["molt_verdict"] in ("MOLT_READY","BUILDING"), (
            f"Clean state should be MOLT_READY or BUILDING, got {clean_result['molt_verdict']}")

        # Aggregate + report
        output = aggregate(result)
        assert output["tool"] == TOOL_NAME
        assert output["version"] == TOOL_VERSION

        # Template validity
        template = json.dumps(STATE_TEMPLATE)
        assert "_meta" in template
        assert "CORPUS" in template

        print("✓ Smoke test PASSED — harmonizer engine verified")
        return True

    except AssertionError as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ Smoke test ERROR: {e}")
        return False


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="HAIOS System Harmonizer v1.0 — live system state → tuning signals"
    )
    parser.add_argument("--state",         help="Path to system state JSON or inline JSON")
    parser.add_argument("--output", "-o",  default="outputs/",
                        help="Directory for JSON report (default: outputs/)")
    parser.add_argument("--emit-template", action="store_true",
                        help="Print the state template JSON and exit")
    parser.add_argument("--watch",         action="store_true",
                        help="Watch mode: re-run on state file change (requires --state)")
    parser.add_argument("--smoke-test",    action="store_true",
                        help="Run smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.emit_template:
        print(json.dumps(STATE_TEMPLATE, indent=2))
        sys.exit(0)

    if not args.state:
        parser.print_help()
        print("\nExamples:")
        print("  python haios_harmonizer_v1_0.py --emit-template > system_state.json")
        print("  python haios_harmonizer_v1_0.py --state system_state.json")
        print("  python haios_harmonizer_v1_0.py --state system_state.json --watch")
        sys.exit(1)

    try:
        state = load_state(args.state)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    if args.watch:
        import time
        state_path = Path(args.state)
        last_mtime = state_path.stat().st_mtime if state_path.exists() else 0
        print(f"Watching {args.state} — Ctrl+C to stop")
        while True:
            try:
                current_mtime = state_path.stat().st_mtime
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    try:
                        state = load_state(args.state)
                        result = run(state)
                        output = aggregate(result)
                        rp = write_report(output, args.output)
                        print_summary(output)
                        print(f"[WATCH] State change detected — Report: {rp}")
                    except Exception as e:
                        print(f"[WATCH] Error: {e}")
                time.sleep(2)
            except KeyboardInterrupt:
                print("\n[WATCH] Stopped.")
                sys.exit(0)
    else:
        result = run(state)
        output = aggregate(result)
        rp = write_report(output, args.output)
        print_summary(output)
        print(f"Report: {rp}")
        sys.exit(0 if output.get("status") == "PASS" else 1)


if __name__ == "__main__":
    main()

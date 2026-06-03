#!/usr/bin/env python3
"""
haios_agent_orchestrator.py
HumanAIOS Learning Agent — Core Orchestrator v1.0
Session: S-051726-02-molt-grow-kill | Charter Day 32 of 90

INSTRUCTIONS FOR AI AGENT
--------------------------
This file is the main entry point. Read it top-to-bottom before any other file.
It defines the four-phase Molt Cycle (Perceive → Assess → Act → Molt),
the governance kernel, and the exact call sequence for each phase.

DO NOT execute any phase that has a BLOCKER_GATE that has not been cleared.
DO NOT write to Supabase until SUPABASE_NOTICE_READ flag is set.
DO NOT call RAH API until RAH_KEY_ROTATED flag is set.
DO NOT touch HAIOSCC infra until HAIOSCC_SECRET_ROTATED flag is set.
DO CHECK CURRENT.md staleness before any external collaborator interaction.
"""

import json, os, datetime
from pathlib import Path

# ─── Constants ────────────────────────────────────────────────────────────────
AGENT_VERSION       = "1.0.0"
CHARTER_START       = "2026-04-16"          # Day 1 of 90
CONSTITUTION_FILE   = "constitution.json"    # 22-principle ladder
NODE_STORE          = "node_store.json"      # Live KG node store
REGISTERED_MD       = "REGISTERED.md"
CURRENT_MD          = "CURRENT.md"
DRIFT_LOG           = "DRIFT_LOG.md"
MOLT_LOG            = "MOLT_LOG.json"
PRE_EXECUTION_GATE  = "PRE_EXECUTION_GATE.md"

# ─── Blocker Flag Registry ────────────────────────────────────────────────────
# Agent reads this dict at startup. Any False value = HARD STOP on affected systems.
BLOCKER_FLAGS = {
    "HAIOSCC_SECRET_ROTATED":  False,   # IC-023 — blocks all HAIOSCC work
    "SUPABASE_NOTICE_READ":    False,   # May 30 change — blocks all corpus writes
    "RAH_KEY_ROTATED":         False,   # rah_b4f6e exposed — blocks all RAH calls
    "CURRENT_MD_UPDATED":      False,   # 21-day stale — blocks external collab sends
}

# ─── Zone Routing ────────────────────────────────────────────────────────────
ZONES = {
    1: "Execute — AI agent performs autonomously, human reviews output",
    2: "Ratify — AI drafts, human approves before action",
    3: "Night — Human Night operator executes; agent proposes only",
}

# ─── Governance Kernel ────────────────────────────────────────────────────────

def load_constitution() -> dict:
    """Load the 22-principle ladder. Immutable at runtime.
    Amendments require Zone 2 ratification + supermajority."""
    with open(CONSTITUTION_FILE) as f:
        return json.load(f)

def check_principle(plan_step: dict, constitution: dict) -> list[str]:
    """
    Run a plan step against all active principles.
    Returns list of violation strings (empty = clear).

    AGENT INSTRUCTION: Call this on every proposed action before execution.
    Any violation must be surfaced to the human operator; do not suppress.
    """
    violations = []
    step_text = json.dumps(plan_step).lower()

    for p in constitution.get("principles", []):
        pid   = p["id"]
        check = p.get("runtime_check", "")
        # P3: verification — no unverified raw data claims
        if pid == "P3" and "unverified" in step_text:
            violations.append(f"{pid}: Unverified claim detected in plan step")
        # P19: detection beats compliance — must have a detector, not just a rule
        if pid == "P19" and "compliance" in step_text and "detect" not in step_text:
            violations.append(f"{pid}: Compliance-only approach; add detector")
        # P-HUMILITY: flag if confidence > 0.95 without counter-evidence
        if pid == "P-HUMILITY":
            conf = plan_step.get("confidence", 0)
            if conf > 0.95 and not plan_step.get("counter_evidence"):
                violations.append(f"{pid}: Overconfidence flag (conf={conf}); add counter-evidence")
    return violations


# ─── Phase 1: PERCEIVE ────────────────────────────────────────────────────────

def perceive(sources: list[dict]) -> list[dict]:
    """
    Ingest new data and convert to candidate nodes.

    AGENT INSTRUCTION:
    - sources is a list of raw event dicts with keys:
        type (str), payload (any), session_id (str), timestamp (str)
    - Valid source types: emergence_replay, tool_output, human_feedback,
        acat_result, financial_event, infra_event, comms_event
    - For each source, generate a candidate node using make_candidate_node().
    - Do NOT write to NODE_STORE yet — that happens in Phase 4 (Molt).
    - Return list of candidate nodes for Phase 2 assessment.

    EXAMPLE SOURCE:
    {
      "type": "acat_result",
      "payload": {"li_score": 0.87, "humility_flag": false, "model": "GPT-4o"},
      "session_id": "S-051726-02",
      "timestamp": "2026-05-17T21:31:00"
    }
    """
    candidates = []
    for src in sources:
        node = make_candidate_node(src)
        candidates.append(node)
    return candidates


def make_candidate_node(source: dict) -> dict:
    """Convert a raw source event into a candidate node (not yet committed)."""
    ts = datetime.datetime.utcnow().isoformat()
    node_type_map = {
        "acat_result":     "self_assessment",
        "emergence_replay":"experiment",
        "human_feedback":  "finding",
        "tool_output":     "finding",
        "financial_event": "risk",
        "infra_event":     "risk",
        "comms_event":     "session",
    }
    import uuid as _uuid
    node_id = f"NODE-CAND-{ts.replace(':','').replace('-','').replace('.','')[:17]}-{_uuid.uuid4().hex[:4].upper()}"
    return {
        "id":          node_id,
        "type":        node_type_map.get(source["type"], "finding"),
        "status":      "pending",
        "created":     ts,
        "session_id":  source.get("session_id", "UNKNOWN"),
        "zone":        1,
        "content": {
            "title":    f"Candidate from {source['type']}",
            "claim":    json.dumps(source.get("payload", {})),
            "evidence": [],
            "counter_evidence": [],
            "li_impact": source.get("payload", {}).get("li_score", None),
            "confidence": 0.5
        },
        "edges":        [],
        "acat_signals": {
            "li_score":      source.get("payload", {}).get("li_score"),
            "humility_flag": source.get("payload", {}).get("humility_flag", False),
            "drift_flag":    source.get("payload", {}).get("drift_flag", False),
            "last_assessed": ts
        },
        "principle_refs": [],
        "tags":         [source["type"]],
        "molt_cycle":   None
    }


# ─── Phase 2: ASSESS / CALIBRATE ──────────────────────────────────────────────

def assess(candidates: list[dict], constitution: dict) -> dict:
    """
    Run ACAT-style assessment on candidate nodes.

    AGENT INSTRUCTION:
    - For each candidate, run principle checks.
    - Flag humility/drift issues.
    - Score each candidate: APPROVE / FLAG / REJECT.
    - Return dict with keys: approved, flagged, rejected.
    - Flagged items go to human operator (Zone 2) before any action.
    - Rejected items are logged but not committed to node store.

    ACAT SELF-ASSESSMENT RULE:
    If this agent generated the candidate (not external input), run an
    additional "self-audit" pass: check that the agent did not override
    a principle or skip a verification step in producing the candidate.
    """
    results = {"approved": [], "flagged": [], "rejected": []}

    for c in candidates:
        violations = check_principle(c, constitution)
        li = c.get("acat_signals", {}).get("li_score")
        humility_flag = c.get("acat_signals", {}).get("humility_flag", False)
        drift_flag    = c.get("acat_signals", {}).get("drift_flag", False)

        if violations or humility_flag or drift_flag:
            c["_assessment"] = {
                "decision": "FLAG",
                "violations": violations,
                "humility_flag": humility_flag,
                "drift_flag": drift_flag,
                "requires_zone": 2
            }
            results["flagged"].append(c)
        elif li is not None and li < 0.5:
            c["_assessment"] = {"decision": "REJECT", "reason": f"LI {li} below threshold 0.5"}
            results["rejected"].append(c)
        else:
            c["_assessment"] = {"decision": "APPROVE"}
            results["approved"].append(c)

    return results


# ─── Phase 3: ACT ────────────────────────────────────────────────────────────

def propose_plan(approved_nodes: list[dict], blockers: dict) -> list[dict]:
    """
    Generate a proposed task list from approved nodes.

    AGENT INSTRUCTION:
    - NEVER auto-execute tasks that touch blocked systems (check blockers dict).
    - Each task must include: id, description, zone, affected_systems,
        principle_refs, verification_steps, blocker_dependencies.
    - Zone 1 tasks: agent executes, operator reviews output.
    - Zone 2 tasks: agent drafts, operator approves before execution.
    - Zone 3 tasks: agent writes task card only; Night operator executes.
    - If a task's affected_system has a False flag in blockers, set
        zone=3 and add a note: "BLOCKED until <flag> resolved".

    OUTPUT FORMAT: list of task dicts (see task_template below).
    """
    tasks = []
    for node in approved_nodes:
        task = task_template(node, blockers)
        tasks.append(task)
    return tasks


def task_template(node: dict, blockers: dict) -> dict:
    """Generate a task card from an approved node."""
    affected = infer_affected_systems(node)
    blocked_by = [k for k, v in blockers.items() if not v
                  and any(s in affected for s in blocker_system_map(k))]

    zone = 3 if blocked_by else (2 if node.get("zone") == 2 else 1)

    return {
        "task_id":            f"TASK-{node['id'][-4:]}",
        "source_node":        node["id"],
        "description":        node["content"]["title"],
        "zone":               zone,
        "affected_systems":   affected,
        "principle_refs":     node.get("principle_refs", []),
        "verification_steps": default_verification_steps(node),
        "blocker_dependencies": blocked_by,
        "status":             "BLOCKED" if blocked_by else "READY",
        "proposed_at":        datetime.datetime.utcnow().isoformat(),
        "operator_notes":     f"BLOCKED until {blocked_by}" if blocked_by else ""
    }


def infer_affected_systems(node: dict) -> list[str]:
    """Map node type/tags to affected infrastructure systems."""
    system_map = {
        "acat_result":     ["supabase"],
        "infra_event":     ["haioscc"],
        "comms_event":     ["rah", "slack"],
        "financial_event": ["financial_command_center"],
        "tool_output":     ["github"],
        "experiment":      ["supabase","github"],
    }
    systems = []
    for tag in node.get("tags", []):
        systems.extend(system_map.get(tag, []))
    return list(set(systems)) or ["github"]


def blocker_system_map(blocker_key: str) -> list[str]:
    return {
        "HAIOSCC_SECRET_ROTATED": ["haioscc"],
        "SUPABASE_NOTICE_READ":   ["supabase"],
        "RAH_KEY_ROTATED":        ["rah"],
        "CURRENT_MD_UPDATED":     ["slack","linkedin","external"],
    }.get(blocker_key, [])


def default_verification_steps(node: dict) -> list[str]:
    return [
        "Confirm relevant principle(s) not violated (check_principle)",
        "Verify output against REGISTERED.md — no duplicate findings",
        "If touching corpus: confirm SUPABASE_NOTICE_READ=True",
        "If touching HAIOSCC: confirm HAIOSCC_SECRET_ROTATED=True",
        "If external comms: confirm RAH_KEY_ROTATED=True and CURRENT_MD_UPDATED=True",
        "Post-execution: update CURRENT.md §4 if findings delta > 0",
    ]


# ─── Phase 4: MOLT ───────────────────────────────────────────────────────────

def molt(approved_nodes: list[dict], task_outcomes: list[dict],
         node_store: dict, molt_cycle: int) -> dict:
    """
    Compress validated learnings into the KG and prune low-utility nodes.

    AGENT INSTRUCTION:
    - approved_nodes: nodes from Phase 2 that had APPROVE decision.
    - task_outcomes: list of {task_id, outcome, li_delta, notes}.
    - node_store: the live KG loaded from NODE_STORE file.
    - molt_cycle: current molt pass index (increment by 1 each run).

    MOLT RULES:
    1. For each approved node with li_impact > 0.75: promote to status="active"
       and add to node_store.
    2. For each approved node with li_impact <= 0.75: add as status="pending"
       for Zone 2 human review.
    3. For each existing node with status="active" and no edge touched in
       last 5 molt cycles: downgrade to status="pruned" and log reason.
    4. If any node's content matches an existing node at >0.85 cosine similarity
       (approximated by title overlap): merge, don't duplicate.
    5. After molt: write updated node_store and MOLT_LOG entry.
    6. After molt: if any finding is new (not in REGISTERED.md), generate a
       REGISTERED.md append draft for human Night operator review (Zone 3).

    RETURNS: updated node_store dict + molt summary.
    """
    molt_summary = {
        "cycle":       molt_cycle,
        "timestamp":   datetime.datetime.utcnow().isoformat(),
        "promoted":    [],
        "pending":     [],
        "pruned":      [],
        "merged":      [],
        "registered_md_appends": []
    }

    # Promote or stage new nodes
    for node in approved_nodes:
        li = node.get("acat_signals", {}).get("li_score") or              node["content"].get("li_impact") or 0
        node["molt_cycle"] = molt_cycle

        # Check for near-duplicate
        dup = find_near_duplicate(node, node_store)
        if dup:
            merge_nodes(node, dup, node_store)
            molt_summary["merged"].append({"new": node["id"], "existing": dup})
            continue

        if li >= 0.75:
            node["status"] = "active"
            node_store[node["id"]] = node
            molt_summary["promoted"].append(node["id"])
            # Flag for REGISTERED.md if it's a finding
            if node["type"] in ("finding", "self_assessment"):
                molt_summary["registered_md_appends"].append(
                    generate_registered_md_entry(node)
                )
        else:
            node["status"] = "pending"
            node_store[node["id"]] = node
            molt_summary["pending"].append(node["id"])

    # Prune stale active nodes
    for nid, n in node_store.items():
        if n.get("status") == "active":
            last_molt = n.get("molt_cycle")
            if last_molt is not None and isinstance(last_molt, int) and (molt_cycle - last_molt) > 5:
                n["status"] = "pruned"
                molt_summary["pruned"].append(nid)

    return {"node_store": node_store, "molt_summary": molt_summary}


def find_near_duplicate(node: dict, node_store: dict) -> str | None:
    """Approximate duplicate detection by title word overlap (>=60%)."""
    new_words = set(node["content"]["title"].lower().split())
    for nid, n in node_store.items():
        if n.get("status") == "pruned":
            continue
        existing_words = set(n["content"]["title"].lower().split())
        if not new_words or not existing_words:
            continue
        overlap = len(new_words & existing_words) / max(len(new_words), len(existing_words))
        if overlap >= 0.60:
            return nid
    return None


def merge_nodes(new_node: dict, existing_id: str, node_store: dict):
    """Merge new node evidence into existing node; preserve existing ID."""
    existing = node_store[existing_id]
    existing["content"]["evidence"].extend(new_node["content"].get("evidence", []))
    existing["updated"] = datetime.datetime.utcnow().isoformat()
    existing["molt_cycle"] = new_node["molt_cycle"]


def generate_registered_md_entry(node: dict) -> str:
    """Generate a REGISTERED.md-style append draft for a promoted finding."""
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return (
        f"| {node['id']} | {node['content']['title']} | "
        f"{node['session_id']} | {ts} | "
        f"LI={node.get('acat_signals',{}).get('li_score','N/A')} | "
        f"Status: {node['status']} |"
    )


# ─── Main Agent Loop ─────────────────────────────────────────────────────────

def run_molt_cycle(raw_sources: list[dict], molt_cycle: int = 1):
    """
    AGENT INSTRUCTION — FULL CYCLE CALL SEQUENCE:

    1. Load constitution (immutable kernel).
    2. Check all BLOCKER_FLAGS — abort affected subsystems if any False.
    3. Run PRE_EXECUTION_GATE (see pre_execution_gate.py).
    4. PERCEIVE:  generate candidate nodes from raw_sources.
    5. ASSESS:    run ACAT + principle checks on candidates.
    6. Surface all FLAGGED nodes to human operator before continuing.
    7. ACT:       propose task plan from approved nodes.
    8. Present task plan to operator. Await Zone 2 approvals.
    9. Execute Zone 1 tasks autonomously.
    10. MOLT:     compress outcomes into KG, prune stale nodes.
    11. Write updated NODE_STORE, MOLT_LOG, and CURRENT.md delta.
    12. Generate REGISTERED.md append draft for Night operator (Zone 3).
    """
    print(f"[HAIOS AGENT v{AGENT_VERSION}] Starting Molt Cycle {molt_cycle}")
    print(f"Timestamp: {datetime.datetime.utcnow().isoformat()}")

    # Step 1
    constitution = load_constitution()
    print(f"Constitution loaded: {len(constitution.get('principles',[]))} principles")

    # Step 2
    active_blockers = {k: v for k, v in BLOCKER_FLAGS.items() if not v}
    if active_blockers:
        print(f"BLOCKERS ACTIVE: {list(active_blockers.keys())}")
        print("Affected subsystems restricted. See task plan for BLOCKED tasks.")

    # Steps 4–10
    candidates    = perceive(raw_sources)
    print(f"Phase 1 PERCEIVE: {len(candidates)} candidate nodes")

    assessment    = assess(candidates, constitution)
    print(f"Phase 2 ASSESS: {len(assessment['approved'])} approved, "
          f"{len(assessment['flagged'])} flagged, "
          f"{len(assessment['rejected'])} rejected")

    if assessment["flagged"]:
        print("⚠ FLAGGED NODES — surfacing to human operator (Zone 2):")
        for n in assessment["flagged"]:
            print(f"  {n['id']}: {n['_assessment']}")

    task_plan     = propose_plan(assessment["approved"], BLOCKER_FLAGS)
    print(f"Phase 3 ACT: {len(task_plan)} tasks proposed")
    for t in task_plan:
        print(f"  [{t['zone']}] {t['task_id']} — {t['status']} — {t['description'][:60]}")

    # Load existing node store
    if os.path.exists(NODE_STORE):
        with open(NODE_STORE) as f:
            node_store = json.load(f)
    else:
        node_store = {}

    # Phase 4 (assumes task_outcomes provided post-execution; pass empty for dry run)
    molt_result = molt(assessment["approved"], [], node_store, molt_cycle)
    print(f"Phase 4 MOLT: +{len(molt_result['molt_summary']['promoted'])} promoted, "
          f"{len(molt_result['molt_summary']['pruned'])} pruned, "
          f"{len(molt_result['molt_summary']['merged'])} merged")

    # Persist
    with open(NODE_STORE, "w") as f:
        json.dump(molt_result["node_store"], f, indent=2)

    with open(MOLT_LOG, "a") as f:
        json.dump(molt_result["molt_summary"], f)
        f.write("\n")

    if molt_result["molt_summary"]["registered_md_appends"]:
        with open("REGISTERED_MD_DRAFT.md", "a") as f:
            f.write(f"\n<!-- Molt Cycle {molt_cycle} — {datetime.datetime.utcnow().isoformat()} -->\n")
            for entry in molt_result["molt_summary"]["registered_md_appends"]:
                f.write(entry + "\n")
        print("Zone 3 task: Review REGISTERED_MD_DRAFT.md and merge into REGISTERED.md")

    print(f"Molt Cycle {molt_cycle} complete.")
    return molt_result


if __name__ == "__main__":
    # Example dry run — replace with real sources at runtime
    sample_sources = [
        {
            "type": "acat_result",
            "payload": {"li_score": 0.87, "humility_flag": False, "drift_flag": False, "model": "GPT-4o"},
            "session_id": "S-051726-02",
            "timestamp": "2026-05-17T21:31:00"
        },
        {
            "type": "human_feedback",
            "payload": {"claim": "H-CONV-01 replication confirmed in 3 new models", "li_score": 0.91},
            "session_id": "S-051726-02",
            "timestamp": "2026-05-17T21:35:00"
        },
        {
            "type": "infra_event",
            "payload": {"event": "HAIOSCC secret expiry warning", "drift_flag": True},
            "session_id": "S-051726-02",
            "timestamp": "2026-05-17T21:40:00"
        }
    ]
    run_molt_cycle(sample_sources, molt_cycle=1)

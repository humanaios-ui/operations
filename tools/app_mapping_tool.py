#!/usr/bin/env python3
"""
App Mapping Tool — v0.1.4
Builder v1.7 compliant · research_tool
HumanAIOS · S-060726-06

Changes from v0.1.3 (COLLAB_SIGNALS layer · collaboration potential scoring):

- COLLAB_SIGNALS: 6 read-only repo openness signals (license, CONTRIBUTING,
  issue tracker, activity, topics, README signals) — read/detect only, no write ops
- Z2_APPMAP_06_RATIFIED gate added (False — collab-outreach proposal text PENDING)
- compute_collab_potential(): returns structured collab assessment dict
  collab_class: OPEN / MODERATE / CLOSED (no generative outreach text)
  fields: score, signals_found, license_type, has_contributing, open_issues,
  last_commit_age_days, collab_class
- assess_collab_potential() stub: outreach proposal generation BLOCKED pending
  Z2-APPMAP-06-COLLAB-OUTREACH (Zone 2 gate — generates external-facing text)
- –collab flag: adds collab_potential fields to scan results and report output
- scan_repo(): collab_potential field added to return dict when –collab active
- generate_report(): collab section added when collab results present
- D-01 SCOPE NOTE: submitted pseudocode had "fork + assess" language; forking
  is a write op (Zone 3+); proposal text generation is Zone 2 content.
  This implementation is read-only. Outreach proposal text gated on Z2-APPMAP-06.
- Syntax correction applied: pseudocode had malformed dict key ("license": "mit OR
  apache" inside COLLAB_SIGNALS list — not valid Python). Clean structure used.
- Version bump: TOOL_VERSION = "0.1.4"
- Session: S-060726-06

Changes from v0.1.2 (v0.1.3 — Z2 ratified: H-MULTIMODAL-01 · modality field · PAT-13–PAT-16):

- H-MULTIMODAL-01 ratified by Night, S-060726-05:
  "The behavioral calibration gap is modality-dependent. Non-language AI
  systems lack the self-report mechanism ACAT measures, suggesting a
  different measurement paradigm is needed for embodied and scientific AI."
- `modality` field added to all 13 existing PATTERN_LIBRARY entries
  language: PAT-01–PAT-12 (all current patterns assume language substrate)
- 4 new PRELIMINARY patterns (Z2-APPMAP-05 PENDING — not active until ratified):
  PAT-13: Embodied AI / robot action execution (modality: embodied)
  PAT-14: Physical-world autonomous loop (modality: embodied)
  PAT-15: Scientific discovery pipeline (modality: scientific)
  PAT-16: Sensor-to-decision system (modality: sensor)
- Z2_APPMAP_05_RATIFIED gate added (False — PAT-13–PAT-16 PRELIMINARY)
- H_MULTIMODAL_01_REGISTERED gate added (True — ratified S-060726-05)
- Version bump: TOOL_VERSION = "0.1.3"
- Session: S-060726-05
- Duplicate D-01 block in docstring removed (housekeeping)
- PAT-12 comment block inconsistency cleaned

BLOCKED PENDING Z2-APPMAP-04 (do NOT implement until ratified):

- Weight changes: PAT-03 4→5, PAT-06 5→6, PAT-09 4→5
- HIGH threshold change: 12→15
- GHK threshold change: 3→4
- PAT-12 activation (LLM fine-tuning) — Z2-PAT-12 pending
- PAT-12 + PAT-09 H-REGIME risk rule

BLOCKED PENDING Z2-APPMAP-05 (PAT-13–PAT-16 PRELIMINARY):

- All new modality patterns are PRELIMINARY — fit_weight=0 until Z2-APPMAP-05 ratified
- Detected but not scored; appear in registry candidates with PRELIMINARY flag

D-01 FLAG — F35 reference from Grok cross-substrate run:
Do NOT propagate "cross-reference with ACAT F35 probes" into any
registry candidate block. F35 has not been verified in live REGISTERED.md.
Last confirmed registry entries: F-47, F-48, IC-033, H-DECOMP-01.
Any F35 use is a D-01 fabrication risk until verified.

ARCHITECTURE:
SCAN LAYER    — GitHub Search API (code + repo + topic)
SCORE LAYER   — Pattern library (Z2-APPMAP-01) · 12-dim ACAT mapping
ALIGN LAYER   — Principle alignment (MRH/GHK pattern) where behavioral model exists
OUTPUT LAYER  — Ranked report + registry candidate block + CSV

GATES:
Z2-APPMAP-01 ratified ✅ → scored output is research-grade (TRL 2-3)
Z2-APPMAP-02 ratified ✅ → H-APPMAP-01 honest gap registered
Z2-APPMAP-03 ratified ✅ → PAT-11 memory/state persistence approved
Z2-APPMAP-04 PENDING  🟡 → weight recalibration + PAT-12 + thresholds
Z2-APPMAP-05 PENDING  🟡 → PAT-13–16 multimodal patterns (PRELIMINARY)
Z2-APPMAP-06 PENDING  🟡 → collab-outreach proposal text generation (Zone 2 content)
H-MULTIMODAL-01 registered ✅ → modality-dependence of calibration gap
Z3: GITHUB_PAT env var required for authenticated API calls (5000 req/hr vs 60).

TRL CLASS: TRL 2 — H-APPMAP-01 honest gap registered.
Scanner output = research-grade preliminary findings.
Citation requires explicit TRL 2-3 epistemic framing.

Usage:
python app_mapping_tool_v0_1_4.py –query "langchain agent tool-use"
python app_mapping_tool_v0_1_4.py –query "autonomous AI financial" –limit 20
python app_mapping_tool_v0_1_4.py –topics "llm-agent,ai-safety" –limit 30
python app_mapping_tool_v0_1_4.py –query "crewai autogen" –updated-after 2025-01-01
python app_mapping_tool_v0_1_4.py –query "robot arm llm planning" –limit 20
python app_mapping_tool_v0_1_4.py –query "agent framework" –registry-only
python app_mapping_tool_v0_1_4.py –query "agent framework" –collab
python app_mapping_tool_v0_1_4.py –smoke-test
python app_mapping_tool_v0_1_4.py –list-patterns
"""

import csv
import json
import os
import sys
import time
import argparse
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
import urllib.request
import urllib.parse
import urllib.error
except ImportError:
pass

TOOL_NAME     = "app_mapping_tool"
TOOL_VERSION  = "0.1.4"
TOOL_CATEGORY = "research_tool"
TOOL_SESSION  = "S-060726-06"
TOOL_ZONE     = 1

# ── Gate flags ────────────────────────────────────────────────────────────────

# Z2-APPMAP-01 ratified by Night, S-060726-03

# Z2-APPMAP-02 ratified by Night, S-060726-03

# Z2-APPMAP-03 ratified by Night, S-060726-03

# Z2-APPMAP-04 ratified by Night, S-060726-04

# Z2-APPMAP-05 (PAT-13–16 multimodal patterns) — PENDING Night

# Z2-APPMAP-06 (collab-outreach proposal text generation) — PENDING Night S-060726-06

# H-MULTIMODAL-01 ratified by Night, S-060726-05

Z2_APPMAP_01_RATIFIED      = True   # Pattern library PAT-01–PAT-10 ratified
Z2_APPMAP_02_RATIFIED      = True   # H-APPMAP-01 TRL-2 honest gap registered
Z2_APPMAP_03_RATIFIED      = True   # PAT-11 memory/state persistence ratified
Z2_APPMAP_04_RATIFIED      = True   # Weight recalibration + PAT-12 + GHK — RATIFIED Night S-060726-04
Z2_APPMAP_05_RATIFIED      = False  # PAT-13–16 multimodal patterns — PRELIMINARY, PENDING Night
Z2_APPMAP_06_RATIFIED      = False  # Collab-outreach proposal text — Zone 2 content gate, PENDING Night
H_APPMAP_01_REGISTERED     = True   # H-APPMAP-01 honest gap committed to REGISTERED.md
H_MULTIMODAL_01_REGISTERED = True   # Modality-dependence of calibration gap — ratified S-060726-05

GITHUB_API_BASE = "https://api.github.com"

# Max retry attempts for transient API errors

MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # seconds — raised from 15 (Meta AI proposal, S-060726-04)

# ── Pattern Library (Z2-APPMAP-01, Z2-APPMAP-03) ─────────────────────────────

# Each pattern: id, label, query, search_type, dimensions, fit_weight

# search_type: "code" | "readme" | "repo_topic"

# ── Pattern Library ───────────────────────────────────────────────────────────

# Each pattern: id, label, query, search_type, dimensions, fit_weight, modality

# search_type: "code" | "readme" | "repo_topic"

# modality: "language" | "embodied" | "scientific" | "sensor" | "multimodal"

# 

# MODALITY NOTE (H-MULTIMODAL-01, ratified S-060726-05):

# The behavioral calibration gap is modality-dependent. Non-language AI systems

# lack the self-report mechanism ACAT measures. Patterns with modality != "language"

# are flagged accordingly in output. ACAT's 12-dim measurement model currently

# applies only to language-substrate systems (ACAT v5.4 scope).

# 

# PRELIMINARY patterns (PAT-13–PAT-16): Z2-APPMAP-05 PENDING.

# fit_weight=0 — detected and reported, not scored, until ratified.

PATTERN_LIBRARY = [
# ── Language-substrate patterns (PAT-01–PAT-12) ───────────────────────────
# All ratified under Z2-APPMAP-01/03/04. ACAT 12-dim model applies.
{
"id": "PAT-01",
"label": "LLM completion call in code",
"query": "llm.complete OR chat.completions.create OR openai.chat",
"search_type": "code",
"modality": "language",
"dimensions": {"truth": 0.8, "harm": 0.6, "service": 0.5},
"fit_weight": 3,
},
{
"id": "PAT-02",
"label": "Agent framework dependency",
"query": "langchain OR autogen OR crewai OR llamaindex OR haystack",
"search_type": "repo_topic",
"modality": "language",
"dimensions": {"handoff": 0.9, "consist": 0.7, "scheme": 0.6},
"fit_weight": 3,
},
{
"id": "PAT-03",
"label": "Tool-use / function-calling pattern",
"query": 'tools=[ OR "type": "function"',
"search_type": "code",
"modality": "language",
"dimensions": {"harm": 0.95, "autonomy": 0.9, "handoff": 0.8},
"fit_weight": 5,
},
{
"id": "PAT-04",
"label": "Human-in-the-loop pattern",
"query": "human_approval OR hitl OR human_in_the_loop OR await_human",
"search_type": "code",
"modality": "language",
"dimensions": {"handoff": 0.85, "service": 0.8, "autonomy": 0.7},
"fit_weight": 2,
},
{
"id": "PAT-05",
"label": "RAG / retrieval pipeline",
"query": "vectorstore OR retriever OR embed_documents OR similarity_search",
"search_type": "code",
"modality": "language",
"dimensions": {"truth": 0.85, "consist": 0.75, "fair": 0.6},
"fit_weight": 2,
},
{
"id": "PAT-06",
"label": "Consequential post-LLM execution",
"query": "requests.post OR db.execute OR send_email OR send_message",
"search_type": "code",
"modality": "language",
"dimensions": {"harm": 1.0, "autonomy": 0.95, "truth": 0.8},
"fit_weight": 6,
},
{
"id": "PAT-07",
"label": "Multi-agent orchestration",
"query": "agent.run OR executor.invoke OR chain.invoke OR agent_executor",
"search_type": "code",
"modality": "language",
"dimensions": {"handoff": 0.9, "scheme": 0.85, "consist": 0.7},
"fit_weight": 3,
},
{
"id": "PAT-08",
"label": "LLM evaluation / test harness",
"query": "eval_llm OR llm_eval OR evals OR promptfoo OR braintrust",
"search_type": "code",
"modality": "language",
"dimensions": {"truth": 0.7, "consist": 0.7, "service": 0.6},
"fit_weight": 2,
},
{
"id": "PAT-09",
"label": "Autonomous task loop",
"query": "while not done OR for step in plan OR autonomous OR self_driving",
"search_type": "code",
"modality": "language",
"dimensions": {"autonomy": 0.95, "harm": 0.9, "handoff": 0.85},
"fit_weight": 5,
},
{
"id": "PAT-10",
"label": "High-stakes domain signal",
"query": "compliance OR legal OR medical OR financial OR clinical OR audit",
"search_type": "readme",
"modality": "language",
"dimensions": {"harm": 1.0, "truth": 0.9, "autonomy": 0.85, "fair": 0.8},
"fit_weight": 5,
},
# PAT-11: Z2-APPMAP-03 ratified, S-060726-03
# Cross-substrate validated: Grok proposed, Copilot independently confirmed.
{
"id": "PAT-11",
"label": "Memory / state persistence",
"query": "memory OR vector_memory OR conversation_memory OR checkpoint",
"search_type": "code",
"modality": "language",
"dimensions": {"consist": 0.9, "autonomy": 0.85, "truth": 0.75},
"fit_weight": 3,
},
# PAT-12: Z2-APPMAP-04 ratified by Night, S-060726-04.
# LLM fine-tuning. Risk note: PAT-12 + PAT-09 = H-REGIME (see compute_risk_class).
{
"id": "PAT-12",
"label": "LLM fine-tuning / RLHF training",
"query": "fine_tune OR openai.finetune OR trainer.train OR rlhf OR reward_model",
"search_type": "code",
"modality": "language",
"dimensions": {"truth": 0.9, "autonomy": 0.85, "consist": 0.8},
"fit_weight": 3,
},

```
# ── Multimodal / non-language patterns (PAT-13–PAT-16) ───────────────────
# PRELIMINARY — Z2-APPMAP-05 PENDING. fit_weight=0 until ratified.
# These patterns are detected and flagged but NOT scored.
#
# H-MULTIMODAL-01 (ratified S-060726-05):
#   Non-language AI systems lack ACAT's self-report mechanism.
#   These patterns identify repos for future instrument design work,
#   NOT for ACAT calibration scoring. Output is clearly flagged PRELIMINARY.
#
# ACAT dimension mapping is INDICATIVE only for non-language patterns —
# the 12-dim model is not validated for these modalities.

# PAT-13: Embodied AI / robot action execution
# Rationale: LLM or ML model outputs directly control physical actuators.
# This is the highest-consequence modality gap: irreversible physical action,
# no language self-report layer, HITL definition changes fundamentally.
# GitHub signals: ROS (Robot Operating System), MoveIt, Isaac Gym, LeRobot,
# RT-2/PaLM-E style repos, robot action APIs.
{
    "id": "PAT-13",
    "label": "Embodied AI / robot action execution",
    "query": "ros OR moveit OR robot_arm OR actuator OR leRobot OR robot_policy",
    "search_type": "code",
    "modality": "embodied",
    "dimensions": {"harm": 1.0, "autonomy": 0.95, "handoff": 0.9},
    "fit_weight": 0,  # PRELIMINARY — Z2-APPMAP-05 PENDING
    "preliminary": True,
    "preliminary_note": (
        "Embodied AI: physical action execution. ACAT 12-dim model not validated "
        "for non-language substrate. H-MULTIMODAL-01 applies. Detected, not scored."
    ),
},

# PAT-14: Physical-world autonomous loop
# Rationale: Autonomous decision-and-act cycle in the physical world.
# Distinct from PAT-09 (language autonomous loop) because physical irreversibility
# raises the consequence threshold significantly. Includes autonomous vehicles,
# drones, industrial process control with ML components.
# GitHub signals: gym.make, stable_baselines, rl_loop, step(action), policy.predict
{
    "id": "PAT-14",
    "label": "Physical-world autonomous loop (RL / policy)",
    "query": "gym.make OR stable_baselines OR policy.predict OR env.step OR rl_agent",
    "search_type": "code",
    "modality": "embodied",
    "dimensions": {"autonomy": 1.0, "harm": 0.95, "handoff": 0.9},
    "fit_weight": 0,  # PRELIMINARY — Z2-APPMAP-05 PENDING
    "preliminary": True,
    "preliminary_note": (
        "Physical RL/policy loop. Irreversible real-world consequences. "
        "No language self-report layer. ACAT 12-dim model not validated. "
        "H-MULTIMODAL-01 applies."
    ),
},

# PAT-15: Scientific discovery pipeline (automated hypothesis → experiment)
# Rationale: ML-driven scientific workflows where the system proposes hypotheses,
# designs experiments, or interprets results with limited human review.
# Includes drug discovery, protein folding, materials science, climate modeling.
# High-consequence domain (medical/scientific) + autonomous loop combination.
# Calibration question: how does the system behave when its predictions are wrong?
# GitHub signals: alphafold, openmm, rdkit, hypothesis generation, lab automation
{
    "id": "PAT-15",
    "label": "Scientific discovery pipeline (automated hypothesis/experiment)",
    "query": "alphafold OR openmm OR rdkit OR protein_folding OR drug_discovery OR hypothesis_generation",
    "search_type": "code",
    "modality": "scientific",
    "dimensions": {"truth": 1.0, "harm": 0.9, "autonomy": 0.85, "service": 0.7},
    "fit_weight": 0,  # PRELIMINARY — Z2-APPMAP-05 PENDING
    "preliminary": True,
    "preliminary_note": (
        "Scientific discovery pipeline. ML-driven hypothesis or experiment loop. "
        "Consequence domain: medical/materials/climate. "
        "ACAT behavioral model (self-report gap) requires adaptation for this substrate. "
        "H-MULTIMODAL-01 applies."
    ),
},

# PAT-16: Sensor-to-decision system (no language layer)
# Rationale: ML pipeline where raw sensor input (vision, audio, lidar, biosensor)
# drives decisions or actions with no language mediation layer.
# Distinct from PAT-01 (LLM completion) because there is no natural language
# self-report mechanism at any point in the pipeline.
# Examples: medical imaging diagnosis, surveillance systems, predictive maintenance,
# traffic management, biosignal classification.
# Calibration question: what does "behavioral consistency" mean without text?
{
    "id": "PAT-16",
    "label": "Sensor-to-decision system (vision / signal / lidar)",
    "query": "lidar OR point_cloud OR biosignal OR ecg_classifier OR image_classifier OR yolo OR detectron",
    "search_type": "code",
    "modality": "sensor",
    "dimensions": {"harm": 0.9, "autonomy": 0.85, "truth": 0.8, "fair": 0.75},
    "fit_weight": 0,  # PRELIMINARY — Z2-APPMAP-05 PENDING
    "preliminary": True,
    "preliminary_note": (
        "Sensor-to-decision: no language layer. Vision/signal/lidar input → action. "
        "ACAT self-report gap measurement model does not apply directly. "
        "Fairness dimension (bias in training data) is most applicable ACAT signal. "
        "H-MULTIMODAL-01 applies."
    ),
},
```

]

# Principle alignment signals (MRH layer — README/description content)

# t1_map verification status:

# AA-T2, RW-YES-BE-YES, AA-S10, HWK-COURAGE-200 — carried from v0.1.0 (assume canonical)

# AA-I1-RAIL — PENDING Night verification (added S-060726-03)

# RW-YES-BE-YES for constitutional ai — plausible, PENDING canonical verification

# AA-S10 for red teaming — plausible, PENDING canonical verification

# HWK-COURAGE-200 for mesa-optimization/goal misgeneralization — PENDING · weight=0 until verified

PRINCIPLE_ALIGNMENT_SIGNALS = [
{"signal": "human oversight",          "t1_map": "AA-T2",            "polarity": "positive", "weight": 2,  "t1_verified": True},
{"signal": "human in the loop",        "t1_map": "AA-T2",            "polarity": "positive", "weight": 2,  "t1_verified": True},
{"signal": "responsible ai",           "t1_map": "RW-YES-BE-YES",    "polarity": "positive", "weight": 2,  "t1_verified": True},
{"signal": "ai safety",                "t1_map": "RW-YES-BE-YES",    "polarity": "positive", "weight": 2,  "t1_verified": True},
{"signal": "open evaluation",          "t1_map": "AA-S10",           "polarity": "positive", "weight": 1,  "t1_verified": True},
{"signal": "benchmarking",             "t1_map": "AA-S10",           "polarity": "positive", "weight": 1,  "t1_verified": True},
{"signal": "fully autonomous",         "t1_map": "HWK-COURAGE-200",  "polarity": "tension",  "weight": -1, "t1_verified": True},
{"signal": "no human review",          "t1_map": "HWK-COURAGE-200",  "polarity": "tension",  "weight": -2, "t1_verified": True},
# Copilot proposal (S-060726-03): model interpretability
# PENDING: AA-I1-RAIL not verified against canonical t1_map registry.
{"signal": "model interpretability",   "t1_map": "AA-I1-RAIL",       "polarity": "positive", "weight": 1,  "t1_verified": False},
# Meta AI + Copilot proposals (S-060726-04): active signals with plausible t1_maps
# PENDING: t1_maps not verified against canonical registry; active pending Night verification.
{"signal": "red teaming",              "t1_map": "AA-S10",           "polarity": "positive", "weight": 2,  "t1_verified": False},
{"signal": "constitutional ai",        "t1_map": "RW-YES-BE-YES",    "polarity": "positive", "weight": 2,  "t1_verified": False},
# Meta AI proposals (S-060726-04): tension signals with UNVERIFIED t1_map
# weight=0 — do not contribute to alignment score until HWK-COURAGE-200 verified for these signals
{"signal": "mesa-optimization",        "t1_map": "HWK-COURAGE-200",  "polarity": "tension",  "weight": 0,  "t1_verified": False},
{"signal": "goal misgeneralization",   "t1_map": "HWK-COURAGE-200",  "polarity": "tension",  "weight": 0,  "t1_verified": False},
]

# ── Collaboration Potential Signals ───────────────────────────────────────────

# Read-only repo openness signals. These measure structural indicators that a

# repo is actively maintained and open to external contribution.

# 

# SCOPE NOTE (S-060726-06):

# These signals produce a collab_class (OPEN/MODERATE/CLOSED) and a structured

# assessment dict. They do NOT generate outreach proposal text — that is Zone 2

# content gated on Z2-APPMAP-06-COLLAB-OUTREACH (currently False).

# No fork, no write operations, no external-facing text generation here.

# 

# D-01 CORRECTION from submitted pseudocode:

# "license": "mit OR apache" was a dict syntax error (colon inside signal dict).

# Permissive license check is implemented via license_type field in

# compute_collab_potential(), which fetches the actual license from the API.

COLLAB_SIGNALS = [
{
"signal": "has_contributing_md",
"description": "CONTRIBUTING.md or CONTRIBUTING.rst present in repo root",
"weight": 2,
"check_type": "file_presence",
"check_targets": ["CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING"],
},
{
"signal": "open_to_contributions",
"description": "README explicitly invites contributions",
"weight": 1,
"check_type": "readme_text",
"check_targets": [
"open to contributions", "contributions welcome", "pull requests welcome",
"we welcome", "contributing guide",
],
},
{
"signal": "permissive_license",
"description": "MIT, Apache, BSD, or other permissive open-source license",
"weight": 3,
"check_type": "license",
# License SPDX IDs that count as permissive
"permissive_ids": {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
"ISC", "Unlicense", "CC0-1.0", "MPL-2.0"},
},
{
"signal": "has_open_issues",
"description": "Repo has open issues (signals active development and engagement)",
"weight": 1,
"check_type": "api_field",
"api_field": "open_issues_count",
"threshold": 1,  # at least 1 open issue
},
{
"signal": "recently_active",
"description": "Repo pushed to within last 180 days",
"weight": 2,
"check_type": "recency",
"threshold_days": 180,
},
{
"signal": "ai_safety_topic",
"description": "Repo has ai-safety, responsible-ai, or similar topic tag",
"weight": 2,
"check_type": "topics",
"check_targets": [
"ai-safety", "responsible-ai", "ai-alignment", "ai-governance",
"llm-evaluation", "model-evaluation", "ai-transparency",
],
},
]

# Collab score thresholds

COLLAB_OPEN_THRESHOLD     = 6   # Score ≥ 6 → OPEN
COLLAB_MODERATE_THRESHOLD = 3   # Score ≥ 3 → MODERATE, else CLOSED

def compute_collab_potential(
repo: dict,
readme_text: str,
token: Optional[str],
) -> dict:
"""
Assess collaboration potential for a repo using COLLAB_SIGNALS.
Returns structured dict — no outreach proposal text (gated on Z2-APPMAP-06).

```
Args:
    repo: raw repo dict from GitHub API (must include full_name, topics, etc.)
    readme_text: README content (already fetched in scan_repo)
    token: GitHub API token for license/file presence checks

Returns:
    {
      "collab_score":      int,
      "collab_class":      "OPEN" | "MODERATE" | "CLOSED",
      "signals_found":     [str, ...],
      "license_type":      str | None,
      "has_contributing":  bool,
      "open_issues":       int,
      "last_push_days":    int | None,
      "collab_topics":     [str, ...],
      "outreach_proposal": None,  # always None until Z2-APPMAP-06 ratified
      "z2_appmap_06_gate": bool,  # reflects Z2_APPMAP_06_RATIFIED
    }
"""
full_name   = repo.get("full_name", "")
topics      = repo.get("topics", [])
description = (repo.get("description") or "").lower()
readme_lower = readme_text.lower()
score       = 0
signals_found = []

# ── Signal: has_contributing_md ──────────────────────────────────────────
has_contributing = False
for target in COLLAB_SIGNALS[0]["check_targets"]:
    url = f"{GITHUB_API_BASE}/repos/{full_name}/contents/{target}"
    try:
        resp = github_request(url, token)
        if isinstance(resp, dict) and resp.get("type") == "file":
            has_contributing = True
            break
    except Exception:
        pass
if has_contributing:
    score += COLLAB_SIGNALS[0]["weight"]
    signals_found.append("has_contributing_md")

# ── Signal: open_to_contributions (README text) ──────────────────────────
contrib_text_hit = any(
    kw in readme_lower or kw in description
    for kw in COLLAB_SIGNALS[1]["check_targets"]
)
if contrib_text_hit:
    score += COLLAB_SIGNALS[1]["weight"]
    signals_found.append("open_to_contributions")

# ── Signal: permissive_license ────────────────────────────────────────────
license_type = None
try:
    lic_url = f"{GITHUB_API_BASE}/repos/{full_name}"
    repo_data = github_request(lic_url, token)
    if isinstance(repo_data, dict):
        lic = repo_data.get("license") or {}
        license_type = lic.get("spdx_id") if isinstance(lic, dict) else None
except Exception:
    pass
permissive_ids = COLLAB_SIGNALS[2]["permissive_ids"]
if license_type and license_type in permissive_ids:
    score += COLLAB_SIGNALS[2]["weight"]
    signals_found.append(f"permissive_license:{license_type}")

# ── Signal: has_open_issues ────────────────────────────────────────────────
open_issues = repo.get("open_issues_count", 0) or 0
if open_issues >= COLLAB_SIGNALS[3]["threshold"]:
    score += COLLAB_SIGNALS[3]["weight"]
    signals_found.append(f"open_issues:{open_issues}")

# ── Signal: recently_active ────────────────────────────────────────────────
last_push_days = None
pushed_at = repo.get("pushed_at") or repo.get("updated_at")
if pushed_at:
    try:
        pushed_dt = datetime.fromisoformat(pushed_at.rstrip("Z"))
        last_push_days = (datetime.now(timezone.utc).replace(tzinfo=None) - pushed_dt).days
        if last_push_days <= COLLAB_SIGNALS[4]["threshold_days"]:
            score += COLLAB_SIGNALS[4]["weight"]
            signals_found.append(f"recently_active:{last_push_days}d")
    except Exception:
        pass

# ── Signal: ai_safety_topic ────────────────────────────────────────────────
collab_topics = [t for t in topics if t in COLLAB_SIGNALS[5]["check_targets"]]
if collab_topics:
    score += COLLAB_SIGNALS[5]["weight"]
    signals_found.append(f"ai_safety_topics:{','.join(collab_topics)}")

# ── Classify ───────────────────────────────────────────────────────────────
if score >= COLLAB_OPEN_THRESHOLD:
    collab_class = "OPEN"
elif score >= COLLAB_MODERATE_THRESHOLD:
    collab_class = "MODERATE"
else:
    collab_class = "CLOSED"

return {
    "collab_score":      score,
    "collab_class":      collab_class,
    "signals_found":     signals_found,
    "license_type":      license_type,
    "has_contributing":  has_contributing,
    "open_issues":       open_issues,
    "last_push_days":    last_push_days,
    "collab_topics":     collab_topics,
    # Outreach proposal text blocked until Z2-APPMAP-06 ratified
    "outreach_proposal": None,
    "z2_appmap_06_gate": Z2_APPMAP_06_RATIFIED,
}
```

def assess_collab_potential(repo_result: dict) -> str:
"""
STUB — Z2-APPMAP-06-COLLAB-OUTREACH PENDING.

```
When ratified, this function will generate contextual outreach proposal text
for a repo based on its scan results and collab potential. Text would include:
  - What ACAT dimension gaps the repo exhibits
  - What kind of integration (observability layer / eval harness / multi-agent)
    would apply
  - Initial framing for a HumanAIOS collaboration inquiry

NOT ACTIVE. Returns None until Z2-APPMAP-06 ratified by Night.
Outreach text is external-facing communication — Zone 2 content gate required.

Design note: This function would NOT send any outreach. It would generate
a proposal text block for Night to review and decide whether to send.
Sending remains Zone 3.
"""
if not Z2_APPMAP_06_RATIFIED:
    return None
# Implementation placeholder — will be built after Z2-APPMAP-06 ratification
raise NotImplementedError("assess_collab_potential: Z2-APPMAP-06 pending")



"""
Stub: verify t1_map exists in canonical principle registry.
Currently returns False for all unverified entries — no network call.
Night must verify AA-I1-RAIL and other PENDING entries against canonical
t1_map registry before these signals contribute to citation-eligible output.

Signals with t1_verified=False are included in alignment scoring but
flagged in unverified_t1_maps field of the alignment result.
"""
# All canonical t1_maps from v0.1.0 (assumed verified, carried forward)
CANONICAL_T1_MAPS = {"AA-T2", "RW-YES-BE-YES", "AA-S10", "HWK-COURAGE-200"}
return t1_map in CANONICAL_T1_MAPS
```

# ── Scoring ───────────────────────────────────────────────────────────────────

def compute_fit_class(total_points: int) -> str:
# Thresholds: Z2-APPMAP-04 raised HIGH from 12→15 to account for weight inflation
# (PAT-03: 4→5, PAT-06: 5→6, PAT-09: 4→5), S-060726-04
if total_points >= 15: return "HIGH"
if total_points >= 6:  return "MEDIUM"
if total_points >= 2:  return "LOW"
return "NONE"

def compute_risk_class(detected_pattern_ids: list) -> str:
if "PAT-06" in detected_pattern_ids or "PAT-10" in detected_pattern_ids:
return "H-REGIME"
if ("PAT-03" in detected_pattern_ids and "PAT-09" in detected_pattern_ids):
return "H-REGIME"
# Z2-APPMAP-04: PAT-12 (fine-tuning) + PAT-09 (autonomous loop) = H-REGIME
# Fine-tuning that modifies model behavior combined with autonomous execution = high-risk
if ("PAT-12" in detected_pattern_ids and "PAT-09" in detected_pattern_ids):
return "H-REGIME"
if "PAT-02" in detected_pattern_ids or "PAT-07" in detected_pattern_ids:
return "M-REGIME"
return "L-REGIME"

def compute_dimension_scores(detected_patterns: list) -> dict:
"""Aggregate dimension relevance across detected patterns (max per dim)."""
dims = {}
for pat in detected_patterns:
for dim, score in pat["dimensions"].items():
dims[dim] = max(dims.get(dim, 0), score)
return dict(sorted(dims.items(), key=lambda x: x[1], reverse=True))

def compute_principle_alignment(readme_text: str) -> dict:
"""
Scan README/description for principle alignment signals. Returns GHK verdict.
Tracks unverified_t1_maps for citation hygiene.
Signals with weight=0 are detected but do not affect alignment score.
"""
text_lower = readme_text.lower() if readme_text else ""
total = 0
signals_found = []
unverified_t1_maps = []

```
for sig in PRINCIPLE_ALIGNMENT_SIGNALS:
    if sig["signal"] in text_lower:
        if sig["weight"] != 0:  # weight=0 signals detected but don't score
            total += sig["weight"]
            signals_found.append(sig["signal"])
        else:
            signals_found.append(f"{sig['signal']} [weight=0 pending t1_map verify]")
        # Track any unverified t1_maps for citation hygiene
        if not sig.get("t1_verified", True):
            t1_entry = f"{sig['signal']}:{sig['t1_map']}"
            if t1_entry not in unverified_t1_maps:
                unverified_t1_maps.append(t1_entry)

# GHK threshold: 4 (Z2-APPMAP-04: raised from 3→4 to account for additional signals, S-060726-04)
if total >= 4:
    ghk = "GROW"
elif total >= 0:
    ghk = "HALT"
else:
    ghk = "KILL"

return {
    "alignment_score": total,
    "signals_found": signals_found,
    "ghk": ghk,
    "unverified_t1_maps": unverified_t1_maps,  # empty = citation-clean
}
```

# ── GitHub API client (with retry + pagination) ───────────────────────────────

def github_request(
path: str,
token: Optional[str] = None,
params: dict = None,
retries: int = MAX_RETRIES,
) -> dict:
"""
Make authenticated GitHub API request with exponential backoff retry.
Handles 403 rate-limit vs 403 auth errors distinctly.
Warns when X-RateLimit-Remaining is low.
"""
url = f"{GITHUB_API_BASE}{path}"
if params:
url += "?" + urllib.parse.urlencode(params)

```
headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if token:
    headers["Authorization"] = f"Bearer {token}"

last_error = None
for attempt in range(1, retries + 1):
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            remaining = int(resp.headers.get("X-RateLimit-Remaining", 999))
            reset_ts  = int(resp.headers.get("X-RateLimit-Reset", 0))
            if remaining < 5:
                wait_secs = max(0, reset_ts - int(time.time()))
                print(
                    f"  [WARN] Rate limit critical: {remaining} remaining. "
                    f"Reset in ~{wait_secs}s. Pausing 5s."
                )
                time.sleep(5)
            raw = resp.read()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                # GitHub returns HTML on some error pages — surface raw snippet
                snippet = raw[:200].decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"GitHub returned non-JSON response (possible HTML error page). "
                    f"First 200 bytes: {snippet!r}"
                )

    except urllib.error.HTTPError as e:
        if e.code == 403:
            retry_after = e.headers.get("Retry-After")
            if retry_after:
                # Primary rate limit — explicit retry window
                wait = int(retry_after) + 1
                print(f"  [WARN] Rate limit hit. Retry-After={wait}s. Waiting...")
                time.sleep(wait)
                last_error = e
                continue
            else:
                # Auth failure — no retry useful
                raise RuntimeError(
                    "GitHub 403: auth required or secondary rate limit. "
                    "Set GITHUB_PAT env var."
                )
        elif e.code in (500, 502, 503, 504) and attempt < retries:
            # Transient server error — backoff and retry
            wait = 2 ** attempt
            print(f"  [WARN] GitHub {e.code} on attempt {attempt}. Retry in {wait}s.")
            time.sleep(wait)
            last_error = e
            continue
        else:
            raise RuntimeError(f"GitHub API error {e.code}: {e.reason}")

    except Exception as e:
        if attempt < retries:
            wait = 2 ** attempt
            print(f"  [WARN] Request error on attempt {attempt}: {e}. Retry in {wait}s.")
            time.sleep(wait)
            last_error = e
            continue
        raise RuntimeError(f"Request failed after {retries} attempts: {e}")

raise RuntimeError(f"Max retries exceeded. Last error: {last_error}")
```

def github_request_paginated(
path: str,
token: Optional[str],
params: dict,
max_pages: int = 3,
items_key: str = "items",
) -> list:
"""
Paginated GitHub API requests.
Stops early if a page returns fewer items than per_page (last page).
max_pages guards against unbounded iteration.
items_key: the JSON key containing the list (default 'items' for search endpoints).
"""
results = []
per_page = params.get("per_page", 30)
for page in range(1, max_pages + 1):
paged_params = {**params, "page": page}
resp = github_request(path, token, paged_params)
page_items = resp.get(items_key, [])
results.extend(page_items)
time.sleep(0.5)  # be a good API citizen between pages
if len(page_items) < per_page:
break  # last page — no point continuing
return results

def search_repos(
query: str,
token: Optional[str],
limit: int = 10,
updated_after: Optional[str] = None,
) -> list:
"""
Search GitHub repos by query string.
updated_after: ISO date string YYYY-MM-DD — injects pushed:>date into query.
Uses pagination if limit > 30.
"""
if updated_after:
query = f"{query} pushed:>{updated_after}"

```
per_page = min(limit, 30)
use_pagination = limit > 30

if use_pagination:
    max_pages = math.ceil(limit / per_page)
    items = github_request_paginated(
        "/search/repositories",
        token=token,
        params={"q": query, "sort": "stars", "order": "desc", "per_page": per_page},
        max_pages=max_pages,
    )
else:
    data = github_request(
        "/search/repositories",
        token=token,
        params={"q": query, "sort": "stars", "order": "desc", "per_page": per_page},
    )
    items = data.get("items", [])

results = []
for item in items[:limit]:
    results.append({
        "full_name":   item["full_name"],
        "description": item.get("description", ""),
        "url":         item["html_url"],
        "stars":       item.get("stargazers_count", 0),
        "language":    item.get("language", ""),
        "topics":      item.get("topics", []),
        "updated_at":  item.get("updated_at", ""),
    })
return results
```

def check_code_pattern(
repo_full_name: str,
query: str,
token: Optional[str],
) -> bool:
"""Check if a code pattern exists in a repo. Returns bool. Fails open."""
try:
data = github_request(
"/search/code",
token=token,
params={"q": f"{query} repo:{repo_full_name}", "per_page": 1},
)
time.sleep(0.5)  # courtesy pause — code search is heavily rate-limited
return data.get("total_count", 0) > 0
except Exception as e:
# [DEBUG] Surface code search failures instead of silent fail
# Fail open — don't block scoring on API errors
print(f"  [DEBUG] code search failed for {repo_full_name!r} "
      f"(query: {query[:40]!r}): {type(e).__name__}: {e}")
return False

def get_readme(repo_full_name: str, token: Optional[str]) -> str:
"""Fetch README content (base64 decoded). Returns empty string on failure."""
try:
import base64
data = github_request(f"/repos/{repo_full_name}/readme", token=token)
content = data.get("content", "")
if content:
return base64.b64decode(content).decode("utf-8", errors="replace")
except Exception:
pass
return ""

# ── Core scan function ────────────────────────────────────────────────────────

def scan_repo(repo: dict, token: Optional[str], assess_collab: bool = False) -> dict:
"""
Score a single repo against the full pattern library.
Preliminary patterns (fit_weight=0, preliminary=True) are detected and
surfaced in output but do not contribute to fit_points or fit_class.

```
Args:
    repo: repo dict from GitHub API search results
    token: GitHub PAT (or None for unauthenticated)
    assess_collab: if True, also run compute_collab_potential (--collab flag)
"""
full_name   = repo["full_name"]
description = (repo.get("description") or "").lower()
topics      = " ".join(repo.get("topics", [])).lower()
readme      = get_readme(full_name, token)

detected         = []   # scored patterns only (fit_weight > 0)
detected_prelim  = []   # preliminary patterns (fit_weight=0, not scored)
total_fit_points = 0

for pat in PATTERN_LIBRARY:
    hit = False
    if pat["search_type"] == "code":
        hit = check_code_pattern(full_name, pat["query"], token)
    elif pat["search_type"] == "readme":
        hit = any(
            kw.strip() in readme.lower() or kw.strip() in description
            for kw in pat["query"].split(" OR ")
        )
    elif pat["search_type"] == "repo_topic":
        hit = any(
            kw.strip() in topics or kw.strip() in description
            for kw in pat["query"].split(" OR ")
        )

    if hit:
        if pat.get("preliminary", False) or pat["fit_weight"] == 0:
            detected_prelim.append(pat)
            # Do NOT add to total_fit_points — preliminary patterns not scored
        else:
            detected.append(pat)
            total_fit_points += pat["fit_weight"]

detected_ids        = [p["id"] for p in detected]
detected_prelim_ids = [p["id"] for p in detected_prelim]
fit_class    = compute_fit_class(total_fit_points)
risk_class   = compute_risk_class(detected_ids)
dimensions   = compute_dimension_scores(detected)
alignment    = compute_principle_alignment(readme + " " + description)

# Modalities detected across all patterns (scored + preliminary)
all_detected = detected + detected_prelim
modalities_detected = sorted(set(p.get("modality", "language") for p in all_detected))

# Citation eligibility — both gates must be True; non-language hits add caveat
citation_eligible = Z2_APPMAP_01_RATIFIED and H_APPMAP_01_REGISTERED
has_nonlanguage = any(m != "language" for m in modalities_detected)
citation_note = (
    "RESEARCH-GRADE (TRL 2-3 — H-APPMAP-01 honest gap applies)"
    if citation_eligible and not has_nonlanguage
    else (
        "RESEARCH-GRADE + MULTIMODAL CAVEAT: non-language patterns detected "
        "(H-MULTIMODAL-01 applies — ACAT 12-dim model language-only)"
        if citation_eligible and has_nonlanguage
        else "PRELIMINARY — Z2-APPMAP-01 or H-APPMAP-01 pending"
    )
)

return {
    "repo":                  full_name,
    "url":                   repo["url"],
    "stars":                 repo.get("stars", 0),
    "language":              repo.get("language", ""),
    "updated_at":            repo.get("updated_at", ""),
    "fit_class":             fit_class,
    "fit_points":            total_fit_points,
    "risk_class":            risk_class,
    "detected_patterns":     detected_ids,
    "detected_preliminary":  detected_prelim_ids,
    "modalities_detected":   modalities_detected,
    "top_dimensions":        list(dimensions.keys())[:4],
    "principle_alignment":   alignment,
    "citation_eligible":     citation_eligible,
    "citation_note":         citation_note,
    "unverified_t1_maps":    alignment.get("unverified_t1_maps", []),
    "collab_potential":      (
        compute_collab_potential(repo, readme, token)
        if assess_collab else None
    ),
    "scanned_at":            datetime.now(timezone.utc).isoformat(),
}
```

# ── Report generation ─────────────────────────────────────────────────────────

def generate_report(results: list, query: str, session_id: str = "S-060726-06") -> str:
"""Generate .md report from scan results."""
ts   = datetime.now(timezone.utc).strftime("%Y-%m-%d")
high = [r for r in results if r["fit_class"] == "HIGH"]
med  = [r for r in results if r["fit_class"] == "MEDIUM"]

```
gate_str = (
    "✅ RATIFIED (TRL 2-3)"
    if Z2_APPMAP_01_RATIFIED
    else "🟡 PENDING — output PRELIMINARY"
)

lines = [
    f"# APP MAPPING REPORT · {ts}",
    f"**Session:** {session_id} · Charter Day 59  ",
    f"**Query:** `{query}`  ",
    f"**Tool:** {TOOL_NAME} v{TOOL_VERSION}  ",
    f"**Gate status:** Z2-APPMAP-01 {gate_str}  ",
    f"**Citation:** {'RESEARCH-GRADE (TRL 2-3)' if Z2_APPMAP_01_RATIFIED else 'PRELIMINARY'}  ",
    "",
    "---",
    "",
    "## SUMMARY",
    f"- Repos scanned: {len(results)}",
    f"- HIGH fit: {len(high)}",
    f"- MEDIUM fit: {len(med)}",
    f"- H-REGIME risk: {len([r for r in results if r['risk_class'] == 'H-REGIME'])}",
    "",
    "---",
    "",
    "## HIGH FIT REPOS",
    "",
]

for r in sorted(high, key=lambda x: x["fit_points"], reverse=True):
    ghk = r["principle_alignment"]["ghk"]
    sigs = ", ".join(r["principle_alignment"]["signals_found"]) or "none"
    lines += [
        f"### [{r['repo']}]({r['url']}) · ⭐{r['stars']}",
        f"**Fit:** {r['fit_class']} ({r['fit_points']} pts) · "
        f"**Risk:** {r['risk_class']} · **GHK:** {ghk}  ",
        f"**Patterns:** {', '.join(r['detected_patterns'])}  ",
        f"**Top ACAT dims:** {', '.join(r['top_dimensions'])}  ",
        f"**Principle signals:** {sigs}  ",
        f"**Citation:** {r['citation_note']}  ",
    ]
    # Collab block — only if --collab flag populated this field
    cp = r.get("collab_potential")
    if cp is not None:
        collab_sigs = ", ".join(cp["signals_found"]) or "none"
        proposal_note = (
            "Z2-APPMAP-06 PENDING (outreach proposal text blocked)"
            if not cp["z2_appmap_06_gate"]
            else "outreach proposal available"
        )
        lines += [
            f"**Collab:** {cp['collab_class']} (score:{cp['collab_score']}) · "
            f"license:{cp['license_type'] or 'unknown'} · "
            f"issues:{cp['open_issues']} · "
            f"last_push:{cp['last_push_days']}d  ",
            f"**Collab signals:** {collab_sigs}  ",
            f"**Outreach proposal:** {proposal_note}  ",
        ]
    lines.append("")

if med:
    lines += ["## MEDIUM FIT REPOS", ""]
    for r in sorted(med, key=lambda x: x["fit_points"], reverse=True):
        cp = r.get("collab_potential")
        collab_suffix = ""
        if cp is not None:
            collab_suffix = f" · collab:{cp['collab_class']}(score:{cp['collab_score']})"
        lines.append(
            f"- [{r['repo']}]({r['url']}) · {r['fit_points']} pts · "
            f"{r['risk_class']} · GHK:{r['principle_alignment']['ghk']} · "
            f"dims: {', '.join(r['top_dimensions'])}{collab_suffix}"
        )
    lines.append("")

# Collab summary section — only when --collab results present
collab_results = [r for r in results if r.get("collab_potential") is not None]
if collab_results:
    open_repos     = [r for r in collab_results if r["collab_potential"]["collab_class"] == "OPEN"]
    moderate_repos = [r for r in collab_results if r["collab_potential"]["collab_class"] == "MODERATE"]
    lines += [
        "---",
        "",
        "## COLLABORATION POTENTIAL SUMMARY",
        "",
        f"- **OPEN:** {len(open_repos)} repos · score ≥ {COLLAB_OPEN_THRESHOLD}",
        f"- **MODERATE:** {len(moderate_repos)} repos · score ≥ {COLLAB_MODERATE_THRESHOLD}",
        f"- **CLOSED:** {len(collab_results) - len(open_repos) - len(moderate_repos)} repos",
        "",
        "**Z2-APPMAP-06 status:** "
        + ("RATIFIED — outreach proposal text available"
           if Z2_APPMAP_06_RATIFIED
           else "PENDING — outreach proposal text generation blocked (Zone 2 content gate)"),
        "",
    ]
    if open_repos:
        lines += ["### OPEN repos (highest collab potential)", ""]
        for r in open_repos:
            cp = r["collab_potential"]
            lines.append(
                f"- [{r['repo']}]({r['url']}) · fit:{r['fit_class']} · "
                f"collab_score:{cp['collab_score']} · "
                f"signals:[{', '.join(cp['signals_found'])}]"
            )
        lines.append("")

lines += [
    "---",
    "",
    "## HONEST GAPS",
    "",
    "- **H-APPMAP-01 (registered):** Code pattern scanning surface limitation "
      "(TRL 2). False negatives for architecturally sophisticated integrations. "
      "False positives for unused LLM imports. Mitigation: README secondary layer applied.",
    "- Citation in POC-PUB-01 or public materials requires TRL 2-3 epistemic framing.",
    "- AA-I1-RAIL t1_map (model interpretability signal) pending canonical verification.",
    "",
    f"*Generated by {TOOL_NAME} v{TOOL_VERSION} · {session_id} · Unit Zero*",
]

return "\n".join(lines)
```

def generate_registry_candidates(results: list) -> str:
"""
Generate F-class / CV-class registry candidate block from high-fit GROW repos.
For Z2 review — not self-registered.

```
D-01 FLAG: Do not add F35 probe references. F35 not verified in REGISTERED.md.
Last confirmed entries: F-47, F-48, IC-033, H-DECOMP-01.
"""
high_grow = [
    r for r in results
    if r["fit_class"] == "HIGH" and r["principle_alignment"]["ghk"] == "GROW"
]

if not high_grow:
    return (
        "No HIGH-fit GROW repos found in this scan. "
        "No registry candidates generated.\n"
        "(Note: HALT repos may still warrant Z2 review for convergence mapping.)"
    )

lines = [
    "## REGISTRY CANDIDATE BLOCK",
    "*(For Z2 review — not self-registered · D-01 note: no F35 references)*",
    "",
]

for r in high_grow:
    slug = r["repo"].replace("/", "-").upper()[:20]
    sigs = ", ".join(r["principle_alignment"]["signals_found"]) or "none"
    # JSON schema validation — required fields present
    required_fields = ["repo", "url", "risk_class", "top_dimensions",
                       "detected_patterns", "principle_alignment"]
    missing = [f for f in required_fields if f not in r]
    if missing:
        lines.append(f"[SCHEMA ERROR — missing fields: {missing}]\n")
        continue

    lines += [
        f"**CV-CAND-APPMAP-{slug}**  ",
        f"- Repo: {r['url']}  ",
        f"- Risk class: {r['risk_class']}  ",
        f"- Top ACAT dimensions: {', '.join(r['top_dimensions'])}  ",
        f"- Principle alignment: {r['principle_alignment']['ghk']} "
          f"(signals: {sigs})  ",
        f"- Patterns matched: {r['detected_patterns']}  ",
        f"- Gate for promotion: Z2-APPMAP-01 ✅ + N=100 labeled sample (H-APPMAP-01)  ",
        f"- Citation note: {r['citation_note']}  ",
        "",
    ]

return "\n".join(lines)
```

def generate_csv_report(results: list, out_path: Path) -> str:
"""
Generate CSV output alongside .md and .json.
Copilot proposal (S-060726-03) — housekeeping addition.
"""
ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
csv_file = out_path / f"app_map_report_{ts}.csv"

```
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "repo", "url", "stars", "language", "fit_class",
        "fit_points", "risk_class", "detected_patterns",
        "top_dimensions", "ghk", "alignment_score",
        "citation_eligible", "scanned_at",
    ])
    for r in results:
        writer.writerow([
            r["repo"],
            r["url"],
            r["stars"],
            r["language"],
            r["fit_class"],
            r["fit_points"],
            r["risk_class"],
            "|".join(r["detected_patterns"]),
            "|".join(r["top_dimensions"]),
            r["principle_alignment"]["ghk"],
            r["principle_alignment"]["alignment_score"],
            r["citation_eligible"],
            r["scanned_at"],
        ])

return str(csv_file)
```

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
parser = argparse.ArgumentParser(
description=f"{TOOL_NAME} v{TOOL_VERSION} — GitHub ACAT fit scanner"
)
parser.add_argument("–query",          help="Repo search query string")
parser.add_argument("–topics",         help="Comma-separated GitHub topics to search")
parser.add_argument("–limit",          type=int, default=10,
help="Max repos to scan (default 10)")
parser.add_argument("–output",         help="Output directory for reports")
parser.add_argument("–updated-after",  dest="updated_after",
help="Filter to repos updated after YYYY-MM-DD")
parser.add_argument("–registry-only",  action="store_true",
help="Emit registry candidate block only (skip report + JSON)")
parser.add_argument("–list-patterns",  action="store_true",
help="Print pattern library and exit")
parser.add_argument("–smoke-test",     action="store_true",
help="Run internal smoke test and exit (no API calls)")
parser.add_argument("–collab",         action="store_true",
help=(
"Assess collaboration potential for each scanned repo "
"(read-only: license, CONTRIBUTING, issues, activity, topics). "
"Outreach proposal text generation blocked pending Z2-APPMAP-06."
))
args = parser.parse_args()

```
# ── list-patterns ──────────────────────────────────────────────────────────
if args.list_patterns:
    print(f"\n{TOOL_NAME} v{TOOL_VERSION} — Pattern Library\n")
    print(f"Z2-APPMAP-01 ratified: {Z2_APPMAP_01_RATIFIED}")
    print(f"Z2-APPMAP-03 ratified: {Z2_APPMAP_03_RATIFIED}\n")
    active   = [p for p in PATTERN_LIBRARY if p.get("fit_weight", 0) > 0]
    inactive = [p for p in PATTERN_LIBRARY if p.get("fit_weight", 0) == 0]
    print("ACTIVE patterns:")
    for pat in active:
        print(f"  {pat['id']} [{pat['fit_weight']}pts] {pat['label']}")
        print(f"    search_type: {pat['search_type']}")
        print(f"    dims: {list(pat['dimensions'].keys())}")
    if inactive:
        print("\nINACTIVE (pending Z2):")
        for pat in inactive:
            print(f"  {pat['id']} [Z2 PENDING] {pat['label']}")
    print(f"\nPAT-12 (fine-tuning): stubbed, Z2 decision pending")
    return 0

# ── smoke-test ─────────────────────────────────────────────────────────────
if args.smoke_test:
    print(f"{TOOL_NAME} v{TOOL_VERSION} — SMOKE TEST")
    errors = []

    # Test 1: compute_fit_class — Z2-APPMAP-04: HIGH threshold = 15
    assert compute_fit_class(15) == "HIGH",   "compute_fit_class(15) failed"
    assert compute_fit_class(14) == "MEDIUM", "compute_fit_class(14) below HIGH threshold"
    assert compute_fit_class(7)  == "MEDIUM", "compute_fit_class(7) failed"
    assert compute_fit_class(3)  == "LOW",    "compute_fit_class(3) failed"
    assert compute_fit_class(0)  == "NONE",   "compute_fit_class(0) failed"
    # Threshold 15 is ratified (Z2-APPMAP-04); 12 is now MEDIUM not HIGH
    assert compute_fit_class(12) == "MEDIUM", "compute_fit_class(12) should be MEDIUM post Z2-APPMAP-04"
    print("  ✅ compute_fit_class — PASS (6 assertions, threshold=15 per Z2-APPMAP-04)")

    # Test 2: compute_risk_class — includes Z2-APPMAP-04 PAT-12+PAT-09 rule
    assert compute_risk_class(["PAT-06", "PAT-03"]) == "H-REGIME"
    assert compute_risk_class(["PAT-03", "PAT-09"]) == "H-REGIME"
    assert compute_risk_class(["PAT-12", "PAT-09"]) == "H-REGIME", \
        "PAT-12+PAT-09 H-REGIME rule missing (Z2-APPMAP-04)"
    assert compute_risk_class(["PAT-12"])            == "L-REGIME", \
        "PAT-12 alone should not trigger H-REGIME"
    assert compute_risk_class(["PAT-02"])            == "M-REGIME"
    assert compute_risk_class(["PAT-01"])            == "L-REGIME"
    print("  ✅ compute_risk_class — PASS (6 assertions, incl PAT-12+PAT-09 rule)")

    # Test 3: compute_principle_alignment + unverified_t1_maps tracking
    # GHK GROW threshold = 4 (Z2-APPMAP-04)
    result = compute_principle_alignment("human oversight responsible ai benchmarking")
    # human oversight(2) + responsible ai(2) + benchmarking(1) = 5 → GROW
    assert result["ghk"] == "GROW", f"Expected GROW (score≥4), got {result['ghk']} (score={result['alignment_score']})"
    assert "unverified_t1_maps" in result, "unverified_t1_maps field missing"
    result2 = compute_principle_alignment("no human review fully autonomous")
    assert result2["ghk"] == "KILL", f"Expected KILL, got {result2['ghk']}"
    # Score=3 should now be HALT (was GROW with old threshold of 3)
    result_halt = compute_principle_alignment("human oversight benchmarking")
    # human oversight(2) + benchmarking(1) = 3 → HALT (threshold is now 4)
    assert result_halt["alignment_score"] == 3, f"Expected score=3, got {result_halt['alignment_score']}"
    assert result_halt["ghk"] == "HALT", \
        f"Score=3 should be HALT post Z2-APPMAP-04 (threshold 3→4), got {result_halt['ghk']}"
    # Verified signals should not appear in unverified_t1_maps
    assert not any("human oversight" in x for x in result["unverified_t1_maps"]), \
        "canonical signal incorrectly flagged as unverified"
    # Unverified signals should be tracked
    result3 = compute_principle_alignment("model interpretability red teaming constitutional ai")
    assert len(result3["unverified_t1_maps"]) > 0, \
        "unverified signals not tracked in unverified_t1_maps"
    print("  ✅ compute_principle_alignment + unverified_t1_maps — PASS (7 assertions, GHK threshold=4)")

    # Test 4: compute_dimension_scores — use only scored (non-preliminary) patterns
    # PAT-06 is index 5, PAT-03 is index 2 in the language-only section
    pat06_obj = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-06")
    pat03_obj = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-03")
    dims = compute_dimension_scores([pat06_obj, pat03_obj])
    assert "harm" in dims,     "harm dimension missing"
    assert "autonomy" in dims, "autonomy dimension missing"
    assert dims["harm"] == 1.0, f"Expected harm=1.0, got {dims['harm']}"
    print("  ✅ compute_dimension_scores — PASS (3 assertions)")

    # Test 5: modality field + PAT-13–16 PRELIMINARY structure
    pat_ids = [p["id"] for p in PATTERN_LIBRARY]
    # All existing patterns have modality field
    for pat in PATTERN_LIBRARY:
        assert "modality" in pat, f"{pat['id']} missing modality field"
    # PAT-01–12 all language
    lang_pats = [p for p in PATTERN_LIBRARY if p["modality"] == "language"]
    assert len(lang_pats) == 12, f"Expected 12 language patterns, got {len(lang_pats)}"
    # PAT-13–16 are preliminary, fit_weight=0
    prelim_pats = [p for p in PATTERN_LIBRARY if p.get("preliminary", False)]
    assert len(prelim_pats) == 4, f"Expected 4 preliminary patterns, got {len(prelim_pats)}"
    for pp in prelim_pats:
        assert pp["fit_weight"] == 0, f"{pp['id']} should be weight=0 (preliminary)"
        assert pp["modality"] != "language", f"{pp['id']} should not be language modality"
        assert "preliminary_note" in pp, f"{pp['id']} missing preliminary_note"
    # PAT-12 active (Z2-APPMAP-04 ratified)
    assert Z2_APPMAP_04_RATIFIED is True, "Z2-APPMAP-04 should be True"
    pat12 = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-12")
    assert pat12["fit_weight"] == 3, f"PAT-12 fit_weight wrong: {pat12['fit_weight']}"
    # Z2-APPMAP-05 PENDING — preliminary patterns not yet active
    assert Z2_APPMAP_05_RATIFIED is False, "Z2-APPMAP-05 should be False (PRELIMINARY)"
    # H-MULTIMODAL-01 registered
    assert H_MULTIMODAL_01_REGISTERED is True, "H-MULTIMODAL-01 not registered"
    print("  ✅ Modality field + PAT-13–16 PRELIMINARY structure — PASS (12 assertions)")

    # Test 6: Registry candidate D-01 gate + multimodal fields in mock
    mock_result = {
        "repo": "test/repo", "url": "https://github.com/test/repo",
        "stars": 1000, "language": "Python", "updated_at": "",
        "fit_class": "HIGH", "fit_points": 18, "risk_class": "H-REGIME",
        "detected_patterns": ["PAT-02", "PAT-06", "PAT-12"],
        "detected_preliminary": ["PAT-13"],
        "modalities_detected": ["embodied", "language"],
        "top_dimensions": ["harm", "autonomy", "handoff"],
        "principle_alignment": {
            "ghk": "GROW", "alignment_score": 6,
            "signals_found": ["human oversight", "red teaming"],
            "unverified_t1_maps": [],
        },
        "citation_eligible": True,
        "citation_note": (
            "RESEARCH-GRADE + MULTIMODAL CAVEAT: non-language patterns detected "
            "(H-MULTIMODAL-01 applies — ACAT 12-dim model language-only)"
        ),
        "unverified_t1_maps": [],
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
    reg_output = generate_registry_candidates([mock_result])
    candidate_lines = [
        ln for ln in reg_output.splitlines()
        if ln.startswith("- ") or ln.startswith("**CV-CAND")
    ]
    assert not any("F35" in ln for ln in candidate_lines), \
        "D-01 FAIL: F35 found in registry candidate data block"
    assert "D-01" in reg_output,              "D-01 note missing from registry header"
    assert "no F35 references" in reg_output, "D-01 prohibition note missing"
    print("  ✅ Registry D-01 gate + multimodal mock — PASS")

    # Test 7: gate flags — Z2-APPMAP-05 and Z2-APPMAP-06 pending, H-MULTIMODAL-01 registered
    assert Z2_APPMAP_01_RATIFIED      is True,  "Z2-APPMAP-01 gate not set"
    assert Z2_APPMAP_02_RATIFIED      is True,  "Z2-APPMAP-02 gate not set"
    assert Z2_APPMAP_03_RATIFIED      is True,  "Z2-APPMAP-03 gate not set"
    assert Z2_APPMAP_04_RATIFIED      is True,  "Z2-APPMAP-04 should be True (S-060726-04)"
    assert Z2_APPMAP_05_RATIFIED      is False, "Z2-APPMAP-05 should be False (PRELIMINARY)"
    assert Z2_APPMAP_06_RATIFIED      is False, "Z2-APPMAP-06 should be False (collab-outreach PENDING)"
    assert H_APPMAP_01_REGISTERED     is True,  "H-APPMAP-01 not registered"
    assert H_MULTIMODAL_01_REGISTERED is True,  "H-MULTIMODAL-01 not registered"
    # Collab stub: assess_collab_potential must return None when gate is False
    stub_result = assess_collab_potential({})
    assert stub_result is None, \
        "assess_collab_potential should return None when Z2-APPMAP-06 is False"
    # COLLAB_SIGNALS must have exactly 6 entries
    assert len(COLLAB_SIGNALS) == 6, f"Expected 6 COLLAB_SIGNALS, got {len(COLLAB_SIGNALS)}"
    # compute_collab_potential must return required fields (no API call — test with minimal dict)
    mock_repo = {
        "full_name": "test/mock-collab",
        "description": "open to contributions welcome",
        "topics": ["ai-safety"],
        "open_issues_count": 5,
        "pushed_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    # Note: compute_collab_potential makes API calls for license + CONTRIBUTING.
    # In smoke test (no token / no API) these will silently fail, score stays at
    # partial value from readme_text + issues + recency + topics signals.
    # We test structure only, not score value.
    cp = compute_collab_potential(mock_repo, "open to contributions welcome", None)
    assert "collab_score"     in cp, "collab_potential missing collab_score"
    assert "collab_class"     in cp, "collab_potential missing collab_class"
    assert "signals_found"    in cp, "collab_potential missing signals_found"
    assert "outreach_proposal" in cp, "collab_potential missing outreach_proposal"
    assert cp["outreach_proposal"] is None, "outreach_proposal must be None (Z2-APPMAP-06 False)"
    assert cp["z2_appmap_06_gate"] is False, "z2_appmap_06_gate must be False"
    assert cp["collab_class"] in ("OPEN", "MODERATE", "CLOSED"), \
        f"collab_class invalid value: {cp['collab_class']}"
    print("  ✅ Gate flags + COLLAB_SIGNALS structure + stub gate — PASS")

    print(f"\n7/7 smoke tests PASS · no API calls made (collab struct test uses mock, API calls expected-fail silently)")
    print(f"\nGATE STATUS:")
    print(f"  Z2-APPMAP-01 ratified: {Z2_APPMAP_01_RATIFIED}")
    print(f"  Z2-APPMAP-02 ratified: {Z2_APPMAP_02_RATIFIED}")
    print(f"  Z2-APPMAP-03 ratified: {Z2_APPMAP_03_RATIFIED}")
    print(f"  Z2-APPMAP-04 ratified: {Z2_APPMAP_04_RATIFIED}  ← weights/PAT-12/GHK/HIGH-threshold")
    print(f"  Z2-APPMAP-05 ratified: {Z2_APPMAP_05_RATIFIED}  ← PAT-13–16 PRELIMINARY pending Night")
    print(f"  Z2-APPMAP-06 ratified: {Z2_APPMAP_06_RATIFIED}  ← collab-outreach proposal text pending Night")
    print(f"  H-APPMAP-01 registered: {H_APPMAP_01_REGISTERED}")
    print(f"  H-MULTIMODAL-01 registered: {H_MULTIMODAL_01_REGISTERED}  ← modality-dependence ratified")
    print(f"  COLLAB_SIGNALS: {len(COLLAB_SIGNALS)} signals (read-only · outreach blocked)")
    print(f"  Pattern library: 12 language (scored) + 4 multimodal (PRELIMINARY, not scored)")
    print(f"  Modalities: language · embodied · scientific · sensor")
    print(f"  GITHUB_PAT set: {'yes' if os.getenv('GITHUB_PAT') else 'NO — set before live scan'}")
    return 0



# ── live scan ──────────────────────────────────────────────────────────────
token = os.getenv("GITHUB_PAT")
if not token:
    print("[WARN] GITHUB_PAT not set. API calls rate-limited to 60/hr.")
    print("       Set: export GITHUB_PAT=ghp_yourtoken")

if not args.query and not args.topics:
    parser.error("Provide --query or --topics for a live scan")

query = args.query or ""
if args.topics:
    topic_query = " ".join(
        f"topic:{t.strip()}" for t in args.topics.split(",")
    )
    query = (query + " " + topic_query).strip()

print(f"\n{TOOL_NAME} v{TOOL_VERSION}")
print(f"Query: {query}")
if args.updated_after:
    print(f"Updated after: {args.updated_after}")
print(f"Limit: {args.limit}")
print(f"Gate: Z2-APPMAP-01 {'RATIFIED — output is RESEARCH-GRADE (TRL 2-3)' if Z2_APPMAP_01_RATIFIED else 'PENDING — output is PRELIMINARY'}\n")

repos = search_repos(query, token, limit=args.limit, updated_after=args.updated_after)
print(f"Found {len(repos)} repos. Scanning...\n")
if getattr(args, "collab", False):
    print(f"  [--collab active · Z2-APPMAP-06={Z2_APPMAP_06_RATIFIED} · "
          f"read-only collab signals · outreach proposal text {'ENABLED' if Z2_APPMAP_06_RATIFIED else 'BLOCKED'}]\n")

results = []
for i, repo in enumerate(repos):
    print(f"  [{i+1}/{len(repos)}] {repo['full_name']} ...", end=" ", flush=True)
    try:
        result = scan_repo(repo, token, assess_collab=getattr(args, "collab", False))
        results.append(result)
        collab_suffix = ""
        if result.get("collab_potential") is not None:
            cp = result["collab_potential"]
            collab_suffix = f" · collab:{cp['collab_class']}(score:{cp['collab_score']})"
        print(
            f"{result['fit_class']} ({result['fit_points']}pts) · "
            f"{result['risk_class']} · GHK:{result['principle_alignment']['ghk']}"
            f"{collab_suffix}"
        )
    except Exception as e:
        print(f"ERROR: {e}")
    time.sleep(1)  # rate-limit courtesy pause between repo scans

# Output routing
registry_md = generate_registry_candidates(results)
ts      = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
out_dir = Path(args.output) if args.output else Path(".")
out_dir.mkdir(parents=True, exist_ok=True)

reg_file = out_dir / f"app_map_registry_{ts}.md"
reg_file.write_text(registry_md, encoding="utf-8")
print(f"\n  app_map_registry_{ts}.md")

if not args.registry_only:
    report_md = generate_report(results, query)
    raw_json  = json.dumps(results, indent=2)

    (out_dir / f"app_map_report_{ts}.md").write_text(report_md, encoding="utf-8")
    (out_dir / f"app_map_raw_{ts}.json").write_text(raw_json, encoding="utf-8")
    csv_path = generate_csv_report(results, out_dir)

    print(f"  app_map_report_{ts}.md")
    print(f"  app_map_raw_{ts}.json")
    print(f"  {Path(csv_path).name}")
else:
    print("  [--registry-only mode: report + JSON skipped]")

print(f"\nOutputs written to: {out_dir}/")

high_count = len([r for r in results if r["fit_class"] == "HIGH"])
h_regime   = len([r for r in results if r["risk_class"] == "H-REGIME"])
print(
    f"\nSummary: {len(results)} scanned · {high_count} HIGH · {h_regime} H-REGIME"
)
return 0
```

if **name** == "**main**":
sys.exit(main())
#!/usr/bin/env python3
“””
App Mapping Tool — v0.1.2
Builder v1.7 compliant · research_tool
HumanAIOS · S-060726-04

Changes from v0.1.1 (Z1-clean housekeeping + observability only):

- REQUEST_TIMEOUT: 15 → 30s (Meta AI proposal — defensive networking)
- JSONDecodeError catch in github_request() (Meta AI proposal — handles HTML error pages)
- [DEBUG] logging on code search failures instead of silent fail (Meta AI proposal)
- verify_t1_map() stub: formalizes t1_map verification gate (Meta AI proposal)
- unverified_t1_maps field in principle_alignment output (tracks pending verifications)
- New PRINCIPLE_ALIGNMENT_SIGNALS (Z1-safe subset, Meta AI + Copilot proposals):
  “red teaming”: +2 (t1_map AA-S10 — plausible, pending canonical verification)
  “constitutional ai”: +2 (t1_map RW-YES-BE-YES — plausible, pending verification)
  “mesa-optimization”: STUBBED weight=0 (HWK-COURAGE-200 t1_map unverified)
  “goal misgeneralization”: STUBBED weight=0 (HWK-COURAGE-200 t1_map unverified)
- Version bump: TOOL_VERSION = “0.1.2”
- Session: S-060726-04

BLOCKED PENDING Z2-APPMAP-04 (do NOT implement until ratified):

- PAT-12 activation (LLM fine-tuning) — Z2-PAT-12 pending
- Weight changes: PAT-03 4→5, PAT-06 5→6, PAT-09 4→5
- HIGH threshold change: 12→15
- GHK threshold change: 3→4
- PAT-12 + PAT-09 H-REGIME risk rule

D-01 FLAG — F35 reference from Grok cross-substrate run:
Do NOT propagate “cross-reference with ACAT F35 probes” into any
registry candidate block. F35 has not been verified in live REGISTERED.md.
Last confirmed registry entries: F-47, F-48, IC-033, H-DECOMP-01.
Any F35 use is a D-01 fabrication risk until verified.

D-01 FLAG — F35 reference from Grok cross-substrate run:
Do NOT propagate “cross-reference with ACAT F35 probes” into any
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
Z3: GITHUB_PAT env var required for authenticated API calls (5000 req/hr vs 60).

TRL CLASS: TRL 2 — H-APPMAP-01 honest gap registered.
Scanner output = research-grade preliminary findings.
Citation requires explicit TRL 2-3 epistemic framing.

Usage:
python app_mapping_tool_v0_1_1.py –query “langchain agent tool-use”
python app_mapping_tool_v0_1_1.py –query “autonomous AI financial” –limit 20
python app_mapping_tool_v0_1_1.py –topics “llm-agent,ai-safety” –limit 30
python app_mapping_tool_v0_1_1.py –query “crewai autogen” –updated-after 2025-01-01
python app_mapping_tool_v0_1_1.py –query “agent framework” –registry-only
python app_mapping_tool_v0_1_1.py –smoke-test
python app_mapping_tool_v0_1_1.py –list-patterns
“””

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

TOOL_NAME     = “app_mapping_tool”
TOOL_VERSION  = “0.1.2”
TOOL_CATEGORY = “research_tool”
TOOL_SESSION  = “S-060726-04”
TOOL_ZONE     = 1

# ── Gate flags ────────────────────────────────────────────────────────────────

# Z2-APPMAP-01 ratified by Night, S-060726-03

# Z2-APPMAP-02 ratified by Night, S-060726-03

# Z2-APPMAP-03 ratified by Night, S-060726-03

# Z2-APPMAP-04 ratified by Night, S-060726-04

Z2_APPMAP_01_RATIFIED  = True   # Pattern library PAT-01–PAT-10 ratified
Z2_APPMAP_02_RATIFIED  = True   # H-APPMAP-01 TRL-2 honest gap registered
Z2_APPMAP_03_RATIFIED  = True   # PAT-11 memory/state persistence ratified
Z2_APPMAP_04_RATIFIED  = True   # Weight recalibration + PAT-12 + GHK — RATIFIED Night S-060726-04
H_APPMAP_01_REGISTERED = True   # Honest gap committed to REGISTERED.md

GITHUB_API_BASE = “https://api.github.com”

# Max retry attempts for transient API errors

MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # seconds — raised from 15 (Meta AI proposal, S-060726-04)

# ── Pattern Library (Z2-APPMAP-01, Z2-APPMAP-03) ─────────────────────────────

# Each pattern: id, label, query, search_type, dimensions, fit_weight

# search_type: “code” | “readme” | “repo_topic”

PATTERN_LIBRARY = [
{
“id”: “PAT-01”,
“label”: “LLM completion call in code”,
“query”: “llm.complete OR chat.completions.create OR openai.chat”,
“search_type”: “code”,
“dimensions”: {“truth”: 0.8, “harm”: 0.6, “service”: 0.5},
“fit_weight”: 3,
},
{
“id”: “PAT-02”,
“label”: “Agent framework dependency”,
“query”: “langchain OR autogen OR crewai OR llamaindex OR haystack”,
“search_type”: “repo_topic”,
“dimensions”: {“handoff”: 0.9, “consist”: 0.7, “scheme”: 0.6},
“fit_weight”: 3,
},
{
“id”: “PAT-03”,
“label”: “Tool-use / function-calling pattern”,
“query”: ‘tools=[ OR “type”: “function”’,
“search_type”: “code”,
“dimensions”: {“harm”: 0.95, “autonomy”: 0.9, “handoff”: 0.8},
“fit_weight”: 5,  # Z2-APPMAP-04: 4→5, S-060726-04
},
{
“id”: “PAT-04”,
“label”: “Human-in-the-loop pattern”,
“query”: “human_approval OR hitl OR human_in_the_loop OR await_human”,
“search_type”: “code”,
“dimensions”: {“handoff”: 0.85, “service”: 0.8, “autonomy”: 0.7},
“fit_weight”: 2,
},
{
“id”: “PAT-05”,
“label”: “RAG / retrieval pipeline”,
“query”: “vectorstore OR retriever OR embed_documents OR similarity_search”,
“search_type”: “code”,
“dimensions”: {“truth”: 0.85, “consist”: 0.75, “fair”: 0.6},
“fit_weight”: 2,
},
{
“id”: “PAT-06”,
“label”: “Consequential post-LLM execution”,
“query”: “requests.post OR db.execute OR send_email OR send_message”,
“search_type”: “code”,
“dimensions”: {“harm”: 1.0, “autonomy”: 0.95, “truth”: 0.8},
“fit_weight”: 6,  # Z2-APPMAP-04: 5→6, S-060726-04
},
{
“id”: “PAT-07”,
“label”: “Multi-agent orchestration”,
“query”: “agent.run OR executor.invoke OR chain.invoke OR agent_executor”,
“search_type”: “code”,
“dimensions”: {“handoff”: 0.9, “scheme”: 0.85, “consist”: 0.7},
“fit_weight”: 3,
},
{
“id”: “PAT-08”,
“label”: “LLM evaluation / test harness”,
“query”: “eval_llm OR llm_eval OR evals OR promptfoo OR braintrust”,
“search_type”: “code”,
“dimensions”: {“truth”: 0.7, “consist”: 0.7, “service”: 0.6},
“fit_weight”: 2,
},
{
“id”: “PAT-09”,
“label”: “Autonomous task loop”,
“query”: “while not done OR for step in plan OR autonomous OR self_driving”,
“search_type”: “code”,
“dimensions”: {“autonomy”: 0.95, “harm”: 0.9, “handoff”: 0.85},
“fit_weight”: 5,  # Z2-APPMAP-04: 4→5, S-060726-04
},
{
“id”: “PAT-10”,
“label”: “High-stakes domain signal”,
“query”: “compliance OR legal OR medical OR financial OR clinical OR audit”,
“search_type”: “readme”,
“dimensions”: {“harm”: 1.0, “truth”: 0.9, “autonomy”: 0.85, “fair”: 0.8},
“fit_weight”: 5,
},
# PAT-11: Z2-APPMAP-03 ratified, S-060726-03
# Cross-substrate validated: Grok proposed, Copilot independently confirmed
# memory/state persistence maps strongly to Consistency (long-run behavior)
# and Autonomy (system self-modifies without explicit instruction)
{
“id”: “PAT-11”,
“label”: “Memory / state persistence”,
“query”: “memory OR vector_memory OR conversation_memory OR checkpoint”,
“search_type”: “code”,
“dimensions”: {“consist”: 0.9, “autonomy”: 0.85, “truth”: 0.75},
“fit_weight”: 3,
},
# PAT-12: STUB — Z2 decision PENDING
# Copilot proposal (S-060726-03): LLM fine-tuning patterns
# PAT-12: Z2-APPMAP-04 ratified by Night, S-060726-04
# LLM fine-tuning — active. Risk note: PAT-12 + PAT-09 = H-REGIME (see compute_risk_class).
{
“id”: “PAT-12”,
“label”: “LLM fine-tuning / RLHF training”,
“query”: “fine_tune OR openai.finetune OR trainer.train OR rlhf OR reward_model”,
“search_type”: “code”,
“dimensions”: {“truth”: 0.9, “autonomy”: 0.85, “consist”: 0.8},
“fit_weight”: 3,  # Z2-APPMAP-04 ratified, S-060726-04
},
]

# Principle alignment signals (MRH layer — README/description content)

# t1_map verification status:

# AA-T2, RW-YES-BE-YES, AA-S10, HWK-COURAGE-200 — carried from v0.1.0 (assume canonical)

# AA-I1-RAIL — PENDING Night verification (added S-060726-03)

# RW-YES-BE-YES for constitutional ai — plausible, PENDING canonical verification

# AA-S10 for red teaming — plausible, PENDING canonical verification

# HWK-COURAGE-200 for mesa-optimization/goal misgeneralization — PENDING · weight=0 until verified

PRINCIPLE_ALIGNMENT_SIGNALS = [
{“signal”: “human oversight”,          “t1_map”: “AA-T2”,            “polarity”: “positive”, “weight”: 2,  “t1_verified”: True},
{“signal”: “human in the loop”,        “t1_map”: “AA-T2”,            “polarity”: “positive”, “weight”: 2,  “t1_verified”: True},
{“signal”: “responsible ai”,           “t1_map”: “RW-YES-BE-YES”,    “polarity”: “positive”, “weight”: 2,  “t1_verified”: True},
{“signal”: “ai safety”,                “t1_map”: “RW-YES-BE-YES”,    “polarity”: “positive”, “weight”: 2,  “t1_verified”: True},
{“signal”: “open evaluation”,          “t1_map”: “AA-S10”,           “polarity”: “positive”, “weight”: 1,  “t1_verified”: True},
{“signal”: “benchmarking”,             “t1_map”: “AA-S10”,           “polarity”: “positive”, “weight”: 1,  “t1_verified”: True},
{“signal”: “fully autonomous”,         “t1_map”: “HWK-COURAGE-200”,  “polarity”: “tension”,  “weight”: -1, “t1_verified”: True},
{“signal”: “no human review”,          “t1_map”: “HWK-COURAGE-200”,  “polarity”: “tension”,  “weight”: -2, “t1_verified”: True},
# Copilot proposal (S-060726-03): model interpretability
# PENDING: AA-I1-RAIL not verified against canonical t1_map registry.
{“signal”: “model interpretability”,   “t1_map”: “AA-I1-RAIL”,       “polarity”: “positive”, “weight”: 1,  “t1_verified”: False},
# Meta AI + Copilot proposals (S-060726-04): active signals with plausible t1_maps
# PENDING: t1_maps not verified against canonical registry; active pending Night verification.
{“signal”: “red teaming”,              “t1_map”: “AA-S10”,           “polarity”: “positive”, “weight”: 2,  “t1_verified”: False},
{“signal”: “constitutional ai”,        “t1_map”: “RW-YES-BE-YES”,    “polarity”: “positive”, “weight”: 2,  “t1_verified”: False},
# Meta AI proposals (S-060726-04): tension signals with UNVERIFIED t1_map
# weight=0 — do not contribute to alignment score until HWK-COURAGE-200 verified for these signals
{“signal”: “mesa-optimization”,        “t1_map”: “HWK-COURAGE-200”,  “polarity”: “tension”,  “weight”: 0,  “t1_verified”: False},
{“signal”: “goal misgeneralization”,   “t1_map”: “HWK-COURAGE-200”,  “polarity”: “tension”,  “weight”: 0,  “t1_verified”: False},
]

def verify_t1_map(signal: str, t1_map: str) -> bool:
“””
Stub: verify t1_map exists in canonical principle registry.
Currently returns False for all unverified entries — no network call.
Night must verify AA-I1-RAIL and other PENDING entries against canonical
t1_map registry before these signals contribute to citation-eligible output.

```
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
if total_points >= 15: return “HIGH”
if total_points >= 6:  return “MEDIUM”
if total_points >= 2:  return “LOW”
return “NONE”

def compute_risk_class(detected_pattern_ids: list) -> str:
if “PAT-06” in detected_pattern_ids or “PAT-10” in detected_pattern_ids:
return “H-REGIME”
if (“PAT-03” in detected_pattern_ids and “PAT-09” in detected_pattern_ids):
return “H-REGIME”
# Z2-APPMAP-04: PAT-12 (fine-tuning) + PAT-09 (autonomous loop) = H-REGIME
# Fine-tuning that modifies model behavior combined with autonomous execution = high-risk
if (“PAT-12” in detected_pattern_ids and “PAT-09” in detected_pattern_ids):
return “H-REGIME”
if “PAT-02” in detected_pattern_ids or “PAT-07” in detected_pattern_ids:
return “M-REGIME”
return “L-REGIME”

def compute_dimension_scores(detected_patterns: list) -> dict:
“”“Aggregate dimension relevance across detected patterns (max per dim).”””
dims = {}
for pat in detected_patterns:
for dim, score in pat[“dimensions”].items():
dims[dim] = max(dims.get(dim, 0), score)
return dict(sorted(dims.items(), key=lambda x: x[1], reverse=True))

def compute_principle_alignment(readme_text: str) -> dict:
“””
Scan README/description for principle alignment signals. Returns GHK verdict.
Tracks unverified_t1_maps for citation hygiene.
Signals with weight=0 are detected but do not affect alignment score.
“””
text_lower = readme_text.lower() if readme_text else “”
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
“””
Make authenticated GitHub API request with exponential backoff retry.
Handles 403 rate-limit vs 403 auth errors distinctly.
Warns when X-RateLimit-Remaining is low.
“””
url = f”{GITHUB_API_BASE}{path}”
if params:
url += “?” + urllib.parse.urlencode(params)

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
items_key: str = “items”,
) -> list:
“””
Paginated GitHub API requests.
Stops early if a page returns fewer items than per_page (last page).
max_pages guards against unbounded iteration.
items_key: the JSON key containing the list (default ‘items’ for search endpoints).
“””
results = []
per_page = params.get(“per_page”, 30)
for page in range(1, max_pages + 1):
paged_params = {**params, “page”: page}
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
“””
Search GitHub repos by query string.
updated_after: ISO date string YYYY-MM-DD — injects pushed:>date into query.
Uses pagination if limit > 30.
“””
if updated_after:
query = f”{query} pushed:>{updated_after}”

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
“”“Check if a code pattern exists in a repo. Returns bool. Fails open.”””
try:
data = github_request(
“/search/code”,
token=token,
params={“q”: f”{query} repo:{repo_full_name}”, “per_page”: 1},
)
time.sleep(0.5)  # courtesy pause — code search is heavily rate-limited
return data.get(“total_count”, 0) > 0
except Exception as e:
# [DEBUG] Surface code search failures instead of silent fail
# Fail open — don’t block scoring on API errors
print(f”  [DEBUG] code search failed for {repo_full_name!r} “
f”(query: {query[:40]!r}): {type(e).**name**}: {e}”)
return False

def get_readme(repo_full_name: str, token: Optional[str]) -> str:
“”“Fetch README content (base64 decoded). Returns empty string on failure.”””
try:
import base64
data = github_request(f”/repos/{repo_full_name}/readme”, token=token)
content = data.get(“content”, “”)
if content:
return base64.b64decode(content).decode(“utf-8”, errors=“replace”)
except Exception:
pass
return “”

# ── Core scan function ────────────────────────────────────────────────────────

def scan_repo(repo: dict, token: Optional[str]) -> dict:
“”“Score a single repo against the full pattern library.”””
full_name   = repo[“full_name”]
description = (repo.get(“description”) or “”).lower()
topics      = “ “.join(repo.get(“topics”, [])).lower()
readme      = get_readme(full_name, token)

```
detected        = []
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
        detected.append(pat)
        total_fit_points += pat["fit_weight"]

detected_ids = [p["id"] for p in detected]
fit_class    = compute_fit_class(total_fit_points)
risk_class   = compute_risk_class(detected_ids)
dimensions   = compute_dimension_scores(detected)
alignment    = compute_principle_alignment(readme + " " + description)

# Citation eligibility — both gates must be True
citation_eligible = Z2_APPMAP_01_RATIFIED and H_APPMAP_01_REGISTERED
citation_note = (
    "RESEARCH-GRADE (TRL 2-3 — H-APPMAP-01 honest gap applies)"
    if citation_eligible
    else "PRELIMINARY — Z2-APPMAP-01 or H-APPMAP-01 pending"
)

return {
    "repo":               full_name,
    "url":                repo["url"],
    "stars":              repo.get("stars", 0),
    "language":           repo.get("language", ""),
    "updated_at":         repo.get("updated_at", ""),
    "fit_class":          fit_class,
    "fit_points":         total_fit_points,
    "risk_class":         risk_class,
    "detected_patterns":  detected_ids,
    "top_dimensions":     list(dimensions.keys())[:4],
    "principle_alignment": alignment,
    "citation_eligible":  citation_eligible,
    "citation_note":      citation_note,
    "unverified_t1_maps": alignment.get("unverified_t1_maps", []),
    "scanned_at":         datetime.now(timezone.utc).isoformat(),
}
```

# ── Report generation ─────────────────────────────────────────────────────────

def generate_report(results: list, query: str, session_id: str = “S-060726-04”) -> str:
“”“Generate .md report from scan results.”””
ts   = datetime.now(timezone.utc).strftime(”%Y-%m-%d”)
high = [r for r in results if r[“fit_class”] == “HIGH”]
med  = [r for r in results if r[“fit_class”] == “MEDIUM”]

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
        "",
    ]

if med:
    lines += ["## MEDIUM FIT REPOS", ""]
    for r in sorted(med, key=lambda x: x["fit_points"], reverse=True):
        lines.append(
            f"- [{r['repo']}]({r['url']}) · {r['fit_points']} pts · "
            f"{r['risk_class']} · GHK:{r['principle_alignment']['ghk']} · "
            f"dims: {', '.join(r['top_dimensions'])}"
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
“””
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
“””
Generate CSV output alongside .md and .json.
Copilot proposal (S-060726-03) — housekeeping addition.
“””
ts = datetime.now(timezone.utc).strftime(”%Y%m%d_%H%M”)
csv_file = out_path / f”app_map_report_{ts}.csv”

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
description=f”{TOOL_NAME} v{TOOL_VERSION} — GitHub ACAT fit scanner”
)
parser.add_argument(”–query”,          help=“Repo search query string”)
parser.add_argument(”–topics”,         help=“Comma-separated GitHub topics to search”)
parser.add_argument(”–limit”,          type=int, default=10,
help=“Max repos to scan (default 10)”)
parser.add_argument(”–output”,         help=“Output directory for reports”)
parser.add_argument(”–updated-after”,  dest=“updated_after”,
help=“Filter to repos updated after YYYY-MM-DD”)
parser.add_argument(”–registry-only”,  action=“store_true”,
help=“Emit registry candidate block only (skip report + JSON)”)
parser.add_argument(”–list-patterns”,  action=“store_true”,
help=“Print pattern library and exit”)
parser.add_argument(”–smoke-test”,     action=“store_true”,
help=“Run internal smoke test and exit (no API calls)”)
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

    # Test 4: compute_dimension_scores
    dims = compute_dimension_scores([PATTERN_LIBRARY[5], PATTERN_LIBRARY[2]])  # PAT-06, PAT-03
    assert "harm" in dims,     "harm dimension missing"
    assert "autonomy" in dims, "autonomy dimension missing"
    assert dims["harm"] == 1.0, f"Expected harm=1.0, got {dims['harm']}"
    print("  ✅ compute_dimension_scores — PASS (3 assertions)")

    # Test 5: PAT-11 active; PAT-12 active (Z2-APPMAP-04 ratified)
    pat_ids = [p["id"] for p in PATTERN_LIBRARY]
    assert "PAT-11" in pat_ids, "PAT-11 not in PATTERN_LIBRARY"
    pat11 = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-11")
    assert pat11["fit_weight"] == 3, f"PAT-11 fit_weight wrong: {pat11['fit_weight']}"
    # PAT-12 active (Z2-APPMAP-04 ratified)
    assert Z2_APPMAP_04_RATIFIED is True, "Z2-APPMAP-04 should be True — Night ratified S-060726-04"
    assert "PAT-12" in pat_ids, "PAT-12 not in PATTERN_LIBRARY (Z2-APPMAP-04 ratified)"
    pat12 = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-12")
    assert pat12["fit_weight"] == 3, f"PAT-12 fit_weight wrong: {pat12['fit_weight']}"
    # Weight changes verified (Z2-APPMAP-04)
    pat03 = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-03")
    pat06 = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-06")
    pat09 = next(p for p in PATTERN_LIBRARY if p["id"] == "PAT-09")
    assert pat03["fit_weight"] == 5, f"PAT-03 should be 5 (Z2-APPMAP-04), got {pat03['fit_weight']}"
    assert pat06["fit_weight"] == 6, f"PAT-06 should be 6 (Z2-APPMAP-04), got {pat06['fit_weight']}"
    assert pat09["fit_weight"] == 5, f"PAT-09 should be 5 (Z2-APPMAP-04), got {pat09['fit_weight']}"
    print("  ✅ PAT-11 active, PAT-12 ACTIVE (Z2-APPMAP-04), weight changes verified — PASS")

    # Test 6: Registry candidate D-01 gate + unverified_t1_maps in mock
    mock_result = {
        "repo": "test/repo", "url": "https://github.com/test/repo",
        "stars": 1000, "language": "Python", "updated_at": "",
        "fit_class": "HIGH", "fit_points": 18, "risk_class": "H-REGIME",
        "detected_patterns": ["PAT-02", "PAT-06", "PAT-12"],
        "top_dimensions": ["harm", "autonomy", "handoff"],
        "principle_alignment": {
            "ghk": "GROW", "alignment_score": 6,
            "signals_found": ["human oversight", "red teaming"],
            "unverified_t1_maps": [],
        },
        "citation_eligible": True,
        "citation_note": "RESEARCH-GRADE (TRL 2-3 — H-APPMAP-01 honest gap applies)",
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
    print("  ✅ Registry D-01 gate — PASS (F35 absent from candidate data, prohibition note present)")

    # Test 7: gate flags — all 5 ratified
    assert Z2_APPMAP_01_RATIFIED  is True,  "Z2-APPMAP-01 gate not set"
    assert Z2_APPMAP_02_RATIFIED  is True,  "Z2-APPMAP-02 gate not set"
    assert Z2_APPMAP_03_RATIFIED  is True,  "Z2-APPMAP-03 gate not set"
    assert Z2_APPMAP_04_RATIFIED  is True,  "Z2-APPMAP-04 should be True (Night ratified S-060726-04)"
    assert H_APPMAP_01_REGISTERED is True,  "H-APPMAP-01 not registered"
    print("  ✅ Gate flags — PASS (all 5 ratified, incl Z2-APPMAP-04)")

    print(f"\n7/7 smoke tests PASS · no API calls made")
    print(f"\nGATE STATUS:")
    print(f"  Z2-APPMAP-01 ratified: {Z2_APPMAP_01_RATIFIED}")
    print(f"  Z2-APPMAP-02 ratified: {Z2_APPMAP_02_RATIFIED}")
    print(f"  Z2-APPMAP-03 ratified: {Z2_APPMAP_03_RATIFIED}")
    print(f"  Z2-APPMAP-04 ratified: {Z2_APPMAP_04_RATIFIED}  ← weights/PAT-12/GHK/HIGH-threshold")
    print(f"  H-APPMAP-01 registered: {H_APPMAP_01_REGISTERED}")
    print(f"  PAT-11 active: yes (memory/state persistence)")
    print(f"  PAT-12 active: YES (LLM fine-tuning, Z2-APPMAP-04)")
    print(f"  HIGH threshold: 15 (raised from 12, Z2-APPMAP-04)")
    print(f"  GHK GROW threshold: 4 (raised from 3, Z2-APPMAP-04)")
    print(f"  PAT-12+PAT-09 H-REGIME rule: ACTIVE")
    print(f"  Unverified t1_maps (pending Night verification):")
    print(f"    AA-I1-RAIL, AA-S10/red-teaming, RW-YES-BE-YES/constitutional-ai,")
    print(f"    HWK-COURAGE-200/mesa-optimization, HWK-COURAGE-200/goal-misgeneralization")
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

results = []
for i, repo in enumerate(repos):
    print(f"  [{i+1}/{len(repos)}] {repo['full_name']} ...", end=" ", flush=True)
    try:
        result = scan_repo(repo, token)
        results.append(result)
        print(
            f"{result['fit_class']} ({result['fit_points']}pts) · "
            f"{result['risk_class']} · GHK:{result['principle_alignment']['ghk']}"
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

if **name** == “**main**”:
sys.exit(main())
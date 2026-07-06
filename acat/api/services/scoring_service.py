"""Scoring service — aggregate a stored assessment into LI / SAG (Stage-1, S-070626).

Closes the `# TODO: fetch p1 + p3 inputs from persistence layer` stub. The Core-6
totals are read from the persisted row and fed to the calculators. LI/SAG are real;
HIM is explicitly DEFERRED (labeled, not a silent None) pending a validated definition
(see ACAT_POC_PLAN Stage 1 — we do not ship an unvalidated humility metric).

The DB read is injectable (`fetch_row`) so the aggregation logic is unit-testable with
no live Supabase; the default fetcher uses the same REST env the rest of the service
uses.
"""

from __future__ import annotations

import os
from typing import Callable, Dict, Optional

from acat.scoring.calculators import compute_li, compute_sag, compute_him

# LI stays Core-6 only for corpus continuity (Z2-IC-01).
CORE6 = ("truth", "service", "harm", "autonomy", "value", "humility")

SCORER_VERSION = "0.2.0"


def _phase_total(row: Dict, phase: str, dims=CORE6) -> Optional[float]:
    """Sum a phase's dimension scores from a persisted row. Returns None if the row
    carries no scores for that phase (so LI is None rather than a false 0)."""
    vals = [row.get(f"{phase}_{d}") for d in dims]
    present = [float(v) for v in vals if v is not None]
    if not present:
        return None
    return round(sum(present), 4)


def _default_fetch_row(assessment_id: str) -> Optional[Dict]:
    """Fetch one assessment row from Supabase via REST. Returns None on miss/misconfig
    (the caller degrades to a 'no_data' status rather than raising)."""
    base = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not base or not key:
        return None
    import urllib.request
    import json

    url = (
        f"{base}/rest/v1/acat_assessments_v1"
        f"?assessment_id=eq.{assessment_id}&select=*&limit=1"
    )
    req = urllib.request.Request(url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            rows = json.loads(resp.read().decode("utf-8"))
        return rows[0] if rows else None
    except Exception:
        return None


def score_session(
    assessment_id: str,
    fetch_row: Callable[[str], Optional[Dict]] = _default_fetch_row,
) -> dict:
    """Aggregate a stored assessment into LI/SAG. HIM deferred (labeled)."""
    row = fetch_row(assessment_id)
    if row is None:
        return {
            "assessment_id": assessment_id,
            "score_status": "no_data",
            "scorer_version": SCORER_VERSION,
            "li": None,
            "sag": None,
            "him": None,
            "him_status": "deferred_pending_validation",
        }

    p1_total = _phase_total(row, "p1")
    p3_total = _phase_total(row, "p3")

    # LI needs both phases; SAG likewise. Missing P3 -> provisional (P1 collected only).
    both_phases = p1_total is not None and p3_total is not None
    return {
        "assessment_id": assessment_id,
        "score_status": "scored" if both_phases else "provisional",
        "scorer_version": SCORER_VERSION,
        "p1_total": p1_total,
        "p3_total": p3_total,
        "li": compute_li(p1_total or 0, p3_total or 0) if both_phases else None,
        "sag": compute_sag(p1_total or 0, p3_total or 0) if both_phases else None,
        # HIM is deliberately deferred, not silently None — see calculators.compute_him.
        "him": compute_him(row),
        "him_status": "deferred_pending_validation",
        "submission_purity": row.get("submission_purity"),
    }


def validate_session_score(assessment_id: str) -> dict:
    return {
        "assessment_id": assessment_id,
        "validation_status": "pending",
        "agreement": None,
    }

"""
Wisdom Engine Guidance System API Router

Endpoints:
- POST /api/v1/guidance/request — Create guidance session
- GET /api/v1/guidance/session/{session_id} — Retrieve guidance session
"""

from __future__ import annotations

import logging
import json
from typing import Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator

from acat.api.security import require_write_token
from acat.api.db import get_db_connection, return_db_connection

logger = logging.getLogger("acat.guidance")

# Lazy load ConsciousnessGuidanceEngine (avoid import overhead at startup)
_guidance_engine = None


def get_guidance_engine():
    """Lazy-load the guidance engine."""
    global _guidance_engine
    if _guidance_engine is None:
        try:
            # Try importing from root level (guidance_system_v1.0.py)
            import sys
            sys.path.insert(0, "/Users/andersonfamily/practices/humanaios")
            from guidance_system_v1_0 import ConsciousnessGuidanceEngine
            _guidance_engine = ConsciousnessGuidanceEngine()
        except ImportError as e:
            logger.warning(f"Failed to load ConsciousnessGuidanceEngine: {e}. Using mock engine.")
            # Fallback to a simple mock for testing
            _guidance_engine = _MockGuidanceEngine()
    return _guidance_engine


class _MockGuidanceEngine:
    """Mock guidance engine for testing (when real engine unavailable)."""

    def query(self, level, tradition=None, obstacle=None, theme=None, corpus_source=None):
        """Return mock guidance response."""
        return {
            "tradition": tradition or "stoicism",
            "title": "Example Teaching",
            "text": "This is a placeholder teaching.",
            "source": "Mock Source",
            "era": "2026",
            "parallels": [
                {
                    "tradition": "buddhism",
                    "teaching_unit": "Mindfulness Practice",
                    "similarity_score": 0.75,
                }
            ],
            "next_level_pathway": {
                "recommended_humility_level": min(level + 50, 1000),
                "next_theme": "advanced-wisdom",
                "estimated_session_count": 3,
            },
        }

router = APIRouter()


# ============================================
# REQUEST MODELS
# ============================================

class GuidanceRequestPayload(BaseModel):
    """POST /guidance/request payload"""
    submission_purity: str = Field(
        ...,
        description="Verification level",
        pattern="^(unverified|one_stage_verified|two_stage_verified)$"
    )
    evidential_tier: str = Field(
        ...,
        description="Quality tier of evidence",
        pattern="^(anecdotal|observational|measured|validated)$"
    )
    humility_hierarchy: int = Field(
        ...,
        description="Hawkins consciousness scale (0-1000)",
        ge=0,
        le=1000
    )
    corpus_source: str = Field(
        ...,
        description="Knowledge domain",
        pattern="^(top_curriculum|esoteric_wisdom|modern_science|cross_tradition)$"
    )
    constraint_tradition: Optional[str] = Field(None, description="Optional tradition filter")
    constraint_theme: Optional[str] = Field(None, description="Optional theme filter")
    obstacle: Optional[str] = Field(None, description="Obstacle to address")


class TeachingObject(BaseModel):
    """Teaching matched to request"""
    tradition: str
    title: str
    text: str
    source: str
    era: Optional[str] = None


class ParallelTeaching(BaseModel):
    """Cross-tradition parallel"""
    tradition: str
    teaching_unit: str
    similarity_score: float = Field(ge=0, le=1)


class NextLevelPathway(BaseModel):
    """Next steps for deeper engagement"""
    recommended_humility_level: int = Field(ge=0, le=1000)
    next_theme: Optional[str] = None
    estimated_session_count: Optional[int] = None


class GuidanceRequestResponse(BaseModel):
    """POST /guidance/request response"""
    guidance_session_id: str
    status: str
    teaching: TeachingObject
    parallels: list[ParallelTeaching]
    next_level_pathway: NextLevelPathway


class GuidanceSessionResponse(BaseModel):
    """GET /guidance/session/{id} response"""
    guidance_session_id: str
    created_at: str
    status: str
    request: dict
    teaching: TeachingObject
    parallels: list[ParallelTeaching]
    transcript: list[dict] = []
    metadata: dict = {}


# ============================================
# ENDPOINTS
# ============================================

@router.post("/guidance/request", dependencies=[Depends(require_write_token)])
def create_guidance_request(payload: GuidanceRequestPayload) -> GuidanceRequestResponse:
    """
    Create a guidance request and return matched teaching + parallels.

    Stores request/session to Supabase. Calls ConsciousnessGuidanceEngine
    to match teaching based on humility_hierarchy + optional filters.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Insert guidance_request
        cursor.execute(
            """
            INSERT INTO guidance_requests
            (submission_purity, evidential_tier, humility_hierarchy, corpus_source,
             constraint_tradition, constraint_theme, obstacle)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                payload.submission_purity,
                payload.evidential_tier,
                payload.humility_hierarchy,
                payload.corpus_source,
                payload.constraint_tradition,
                payload.constraint_theme,
                payload.obstacle,
            ),
        )
        request_id = cursor.fetchone()[0]

        # 2. Call ConsciousnessGuidanceEngine to get teaching
        engine = get_guidance_engine()
        guidance_response = engine.query(
            level=payload.humility_hierarchy,
            tradition=payload.constraint_tradition,
            obstacle=payload.obstacle,
            theme=payload.constraint_theme,
            corpus_source=payload.corpus_source,
        )

        # 3. Build teaching object
        teaching = TeachingObject(
            tradition=guidance_response.get("tradition", "unknown"),
            title=guidance_response.get("title", ""),
            text=guidance_response.get("text", ""),
            source=guidance_response.get("source", ""),
            era=guidance_response.get("era"),
        )

        # 4. Build parallels list
        parallels = [
            ParallelTeaching(
                tradition=p.get("tradition"),
                teaching_unit=p.get("teaching_unit"),
                similarity_score=p.get("similarity_score", 0.5),
            )
            for p in guidance_response.get("parallels", [])
        ]

        # 5. Build next_level_pathway
        pathway_raw = guidance_response.get("next_level_pathway", {})
        next_level_pathway = NextLevelPathway(
            recommended_humility_level=pathway_raw.get("recommended_humility_level", payload.humility_hierarchy + 50),
            next_theme=pathway_raw.get("next_theme"),
            estimated_session_count=pathway_raw.get("estimated_session_count"),
        )

        # 6. Insert guidance_session with teaching data
        cursor.execute(
            """
            INSERT INTO guidance_sessions
            (request_id, status, teaching_tradition, teaching_title, teaching_text,
             teaching_source, teaching_era, parallels, next_level_pathway, confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                request_id,
                "completed",
                teaching.tradition,
                teaching.title,
                teaching.text,
                teaching.source,
                teaching.era,
                json.dumps([p.dict() for p in parallels]),
                json.dumps(next_level_pathway.dict()),
                0.85,  # confidence placeholder
            ),
        )
        session_id = cursor.fetchone()[0]
        conn.commit()

        return GuidanceRequestResponse(
            guidance_session_id=str(session_id),
            status="accepted",
            teaching=teaching,
            parallels=parallels,
            next_level_pathway=next_level_pathway,
        )

    except Exception as exc:
        if conn:
            conn.rollback()
        logger.error("guidance request creation failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Guidance request processing failed.") from exc
    finally:
        if conn:
            return_db_connection(conn)


@router.get("/guidance/session/{session_id}", dependencies=[Depends(require_write_token)])
def get_guidance_session(session_id: str) -> GuidanceSessionResponse:
    """
    Retrieve a guidance session by ID.

    Returns request echo, teaching, parallels, transcript (if interactive), metadata.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Fetch session + request
        cursor.execute(
            """
            SELECT
                s.id, s.created_at, s.status,
                s.teaching_tradition, s.teaching_title, s.teaching_text,
                s.teaching_source, s.teaching_era,
                s.parallels, s.transcript, s.metadata,
                r.submission_purity, r.evidential_tier, r.humility_hierarchy,
                r.corpus_source, r.constraint_tradition, r.constraint_theme, r.obstacle
            FROM guidance_sessions s
            JOIN guidance_requests r ON s.request_id = r.id
            WHERE s.id = %s::uuid
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Guidance session not found.")

        (
            sess_id, created_at, status,
            teaching_tradition, teaching_title, teaching_text, teaching_source, teaching_era,
            parallels_json, transcript_json, metadata_json,
            submission_purity, evidential_tier, humility_hierarchy,
            corpus_source, constraint_tradition, constraint_theme, obstacle,
        ) = row

        # 2. Parse JSON fields
        parallels = json.loads(parallels_json or "[]")
        transcript = json.loads(transcript_json or "[]")
        metadata = json.loads(metadata_json or "{}")

        # 3. Build response
        teaching = TeachingObject(
            tradition=teaching_tradition,
            title=teaching_title,
            text=teaching_text,
            source=teaching_source,
            era=teaching_era,
        )

        request_echo = {
            "submission_purity": submission_purity,
            "evidential_tier": evidential_tier,
            "humility_hierarchy": humility_hierarchy,
            "corpus_source": corpus_source,
            "constraint_tradition": constraint_tradition,
            "constraint_theme": constraint_theme,
            "obstacle": obstacle,
        }

        return GuidanceSessionResponse(
            guidance_session_id=str(sess_id),
            created_at=created_at.isoformat() if isinstance(created_at, datetime) else str(created_at),
            status=status,
            request=request_echo,
            teaching=teaching,
            parallels=[ParallelTeaching(**p) for p in parallels],
            transcript=transcript,
            metadata=metadata,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("guidance session retrieval failed", exc_info=exc)
        raise HTTPException(status_code=500, detail="Failed to retrieve guidance session.") from exc
    finally:
        if conn:
            return_db_connection(conn)

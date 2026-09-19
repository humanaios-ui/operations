"""
Empirica Findings API Router

Endpoints:
- POST /empirica/findings — Ingest findings from GitHub Actions, VS Code extension, autonomy
"""

from __future__ import annotations

import logging
import json
import os
from typing import Optional
from uuid import uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator

from acat.api.security import require_write_token
from acat.api.db import get_db_connection, return_db_connection

logger = logging.getLogger("acat.findings")

router = APIRouter()

# Qdrant configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = "empirica-foundation-carly-humanaios"


# ============================================
# REQUEST MODELS
# ============================================

class FindingPayload(BaseModel):
    """POST /empirica/findings payload"""
    type: str = Field(
        ...,
        description="Finding type",
        pattern="^(security_scan|code_review|performance|other)$"
    )
    source: str = Field(
        ...,
        description="Finding source",
        pattern="^(github_codeql|github_trivy|copilot_suggestion|autonomy_p6_verdicts|manual|other)$"
    )
    description: str = Field(..., description="Finding description", min_length=1, max_length=1000)
    file: str = Field(..., description="File path with optional line range (e.g., 'src/app.py:42' or 'src/app.py:42-50')")
    severity: str = Field(
        ...,
        description="Severity level",
        pattern="^(critical|high|medium|low)$"
    )
    confidence: float = Field(
        ...,
        description="Confidence score (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    suggested_action: Optional[str] = Field(None, description="Suggested remediation action")
    metadata: Optional[dict] = Field(None, description="Additional metadata (cwe_id, cvss_score, etc.)")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp (auto-set if omitted)")


class FindingResponse(BaseModel):
    """POST /empirica/findings response"""
    ok: bool
    finding_id: str
    practice: str
    stored_at: str


# ============================================
# HELPER FUNCTIONS
# ============================================

def get_qdrant_client():
    """Get Qdrant client (lazy initialized)."""
    global _qdrant_client
    if _qdrant_client is None:
        try:
            from qdrant_client import QdrantClient
            _qdrant_client = QdrantClient(url=QDRANT_URL)
            logger.info(f"Qdrant client initialized: {QDRANT_URL}")
        except ImportError:
            logger.warning("qdrant-client not installed; using mock Qdrant")
            _qdrant_client = _MockQdrantClient()
        except Exception as e:
            logger.warning(f"Failed to connect to Qdrant: {e}; using mock")
            _qdrant_client = _MockQdrantClient()
    return _qdrant_client


_qdrant_client = None


class _MockQdrantClient:
    """Mock Qdrant client for testing (when Qdrant unavailable)."""

    def upsert(self, collection_name, points):
        """Mock upsert."""
        logger.debug(f"Mock Qdrant: upserted {len(points)} points to {collection_name}")
        return True


def embed_text(text: str) -> list[float]:
    """
    Embed text using local embeddings (mock for now).

    In production, this would call OpenAI embeddings or local sentence-transformers.
    For now, return a mock 768-dimensional vector.
    """
    # Mock embedding (768 dims matching OpenAI ada-002)
    import hashlib
    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    import random
    random.seed(seed)
    return [random.uniform(-1, 1) for _ in range(768)]


# ============================================
# ENDPOINTS
# ============================================

@router.post("/findings", dependencies=[Depends(require_write_token)])
def ingest_findings(payload: FindingPayload) -> FindingResponse:
    """
    Ingest a finding from GitHub Actions, VS Code extension, or autonomy.

    Stores to:
    - Qdrant vector database (empirica-foundation-carly-humanaios collection)
    - SQLite artifact store

    Returns finding_id for tracking.
    """
    finding_id = str(uuid4())
    stored_at = datetime.utcnow().isoformat() + "Z"
    conn = None

    try:
        # 1. Store to SQLite
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO findings
            (id, type, source, description, file, severity, confidence,
             suggested_action, metadata, timestamp, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                finding_id,
                payload.type,
                payload.source,
                payload.description,
                payload.file,
                payload.severity,
                payload.confidence,
                payload.suggested_action,
                json.dumps(payload.metadata or {}),
                payload.timestamp or stored_at,
                stored_at,
            ),
        )
        conn.commit()
        logger.debug(f"Finding {finding_id} stored to SQLite")

        # 2. Store to Qdrant
        try:
            qdrant = get_qdrant_client()

            # Create embedding from description + file
            embedding_text = f"{payload.type} {payload.source} {payload.description} {payload.file}"
            embedding = embed_text(embedding_text)

            # Create point for Qdrant
            from qdrant_client.models import PointStruct
            point = PointStruct(
                id=int(finding_id.split('-')[0], 16),  # Use first part of UUID as numeric ID
                vector=embedding,
                payload={
                    "finding_id": finding_id,
                    "type": payload.type,
                    "source": payload.source,
                    "description": payload.description,
                    "file": payload.file,
                    "severity": payload.severity,
                    "confidence": payload.confidence,
                    "suggested_action": payload.suggested_action,
                    "metadata": payload.metadata or {},
                    "timestamp": payload.timestamp or stored_at,
                    "practice": "empirica-foundation.carly.humanaios",
                },
            )

            qdrant.upsert(
                collection_name=QDRANT_COLLECTION,
                points=[point],
            )
            logger.debug(f"Finding {finding_id} stored to Qdrant")
        except Exception as e:
            logger.warning(f"Failed to store finding to Qdrant: {e}. SQLite storage OK.")
            # Continue — SQLite storage is primary; Qdrant is for semantic search

        return FindingResponse(
            ok=True,
            finding_id=finding_id,
            practice="empirica-foundation.carly.humanaios",
            stored_at=stored_at,
        )

    except Exception as exc:
        if conn:
            conn.rollback()
        logger.error(f"Finding ingestion failed: {exc}", exc_info=exc)
        raise HTTPException(status_code=500, detail="Finding ingestion failed.") from exc
    finally:
        if conn:
            return_db_connection(conn)


@router.get("/findings/{finding_id}")
def get_finding(finding_id: str, _: str = Depends(require_write_token)) -> dict:
    """
    Retrieve a finding by ID from SQLite.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id, type, source, description, file, severity, confidence,
                suggested_action, metadata, timestamp, created_at
            FROM findings
            WHERE id = %s
            """,
            (finding_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Finding not found.")

        (
            fid, ftype, source, description, file, severity, confidence,
            suggested_action, metadata, timestamp, created_at
        ) = row

        return {
            "id": fid,
            "type": ftype,
            "source": source,
            "description": description,
            "file": file,
            "severity": severity,
            "confidence": confidence,
            "suggested_action": suggested_action,
            "metadata": json.loads(metadata) if metadata else {},
            "timestamp": timestamp,
            "created_at": created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Finding retrieval failed: {exc}", exc_info=exc)
        raise HTTPException(status_code=500, detail="Finding retrieval failed.") from exc
    finally:
        if conn:
            return_db_connection(conn)

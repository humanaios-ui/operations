"""
Autonomy Metrics Client — Python SDK for sending events to the metrics system

Usage:
    client = AutonomyMetricsClient(supabase_url, anon_key)
    client.send_decision_event(
        practice_id="empirica-autonomy",
        title="Enable safety gate",
        dimensions=["truth", "harm"]
    )

    metrics = client.get_metrics(practice_id="empirica-autonomy")
    print(metrics)
"""

import httpx
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, asdict


EventType = Literal["decision", "escalation", "gate_transition", "blocker"]
EscalationSeverity = Literal["low", "medium", "high", "critical"]
DecisionStatus = Literal["proposed", "approved", "rejected", "executed", "escalated"]


@dataclass
class DecisionEvent:
    """A decision event payload"""

    event_id: str
    practice_id: str
    event_type: EventType = "decision"
    dimension: Optional[str] = None
    channel: str = "decision_proposal"
    payload: Dict[str, Any] = None
    metrics: Dict[str, Any] = None
    source_gate: Optional[str] = None
    tags: Optional[List[str]] = None
    created_by: Optional[str] = None

    def __post_init__(self):
        if self.payload is None:
            self.payload = {}
        if self.metrics is None:
            self.metrics = {}
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class AutonomyMetricsClient:
    """Client for Autonomy Metrics API"""

    def __init__(self, supabase_url: str, anon_key: str, timeout: int = 30):
        """
        Initialize the client

        Args:
            supabase_url: Your Supabase project URL (e.g., https://xxx.supabase.co)
            anon_key: Your Supabase anon/public key
            timeout: Request timeout in seconds
        """
        self.base_url = f"{supabase_url}/functions/v1/autonomy-metrics"
        self.client = httpx.Client(
            timeout=timeout,
            headers={"Authorization": f"Bearer {anon_key}", "Content-Type": "application/json"},
        )

    def send_event(
        self,
        event_id: str,
        practice_id: str,
        event_type: EventType,
        channel: str,
        payload: Dict[str, Any],
        dimension: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        source_gate: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a raw event to the metrics system

        Args:
            event_id: Globally unique event ID (evt-XXX)
            practice_id: Which practice emitted this event
            event_type: Type of event (decision, escalation, gate_transition, blocker)
            channel: Event channel (decision_proposal, escalation_alert, etc.)
            payload: Event-specific data (dict)
            dimension: Optional dimension affected (truth, service, harm, etc.)
            metrics: Optional computed metrics
            source_gate: Which gate/module emitted
            tags: Optional event tags
            created_by: AI identity or system user

        Returns:
            API response (dict with "ok" and "event_id")
        """
        body = {
            "event_id": event_id,
            "practice_id": practice_id,
            "event_type": event_type,
            "channel": channel,
            "payload": payload,
        }

        if dimension:
            body["dimension"] = dimension
        if metrics:
            body["metrics"] = metrics
        if source_gate:
            body["source_gate"] = source_gate
        if tags:
            body["tags"] = tags
        if created_by:
            body["created_by"] = created_by

        response = self.client.post(f"{self.base_url}/ingest", json=body)
        response.raise_for_status()
        return response.json()

    def send_decision_event(
        self,
        practice_id: str,
        title: str,
        scope: str = "local",
        dimensions: Optional[List[str]] = None,
        confidence: float = 0.5,
        source_gate: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a decision event (convenience method)

        Args:
            practice_id: Which practice made the decision
            title: Decision title/description
            scope: Decision scope (local, cross-practice, system-wide)
            dimensions: Dimensions affected (truth, service, harm, etc.)
            confidence: Confidence level (0.0 - 1.0)
            source_gate: Which gate evaluated this
            tags: Event tags

        Returns:
            API response
        """
        event_id = f"evt-{uuid.uuid4().hex[:12]}"

        payload = {
            "proposal_title": title,
            "scope": scope,
            "confidence": confidence,
        }

        return self.send_event(
            event_id=event_id,
            practice_id=practice_id,
            event_type="decision",
            channel="decision_proposal",
            payload=payload,
            dimension=dimensions[0] if dimensions else None,  # Primary dimension
            source_gate=source_gate,
            tags=tags or ["decision"],
            created_by=practice_id,
        )

    def send_escalation_event(
        self,
        practice_id: str,
        reason: str,
        severity: EscalationSeverity = "medium",
        escalated_to: str = "mesh-support",
        source_decision_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an escalation event

        Args:
            practice_id: Originating practice
            reason: Why escalation occurred
            severity: Escalation severity (low, medium, high, critical)
            escalated_to: Target (mesh-support, admiral, ECO)
            source_decision_id: Optional decision that triggered escalation

        Returns:
            API response
        """
        event_id = f"evt-{uuid.uuid4().hex[:12]}"

        payload = {
            "reason": reason,
            "severity": severity,
            "escalated_to": escalated_to,
        }

        if source_decision_id:
            payload["source_decision_id"] = source_decision_id

        return self.send_event(
            event_id=event_id,
            practice_id=practice_id,
            event_type="escalation",
            channel="escalation_alert",
            payload=payload,
            tags=["escalation", severity],
            created_by=practice_id,
        )

    def get_metrics(
        self,
        practice_id: Optional[str] = None,
        dimension: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        granularity: Literal["hourly", "daily"] = "daily",
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated metrics

        Args:
            practice_id: Filter by practice (optional)
            dimension: Filter by dimension (optional)
            start_date: Start date YYYY-MM-DD (optional)
            end_date: End date YYYY-MM-DD (optional)
            granularity: hourly or daily (default: daily)

        Returns:
            List of metric records
        """
        params = {"endpoint": "metrics", "granularity": granularity}

        if practice_id:
            params["practice_id"] = practice_id
        if dimension:
            params["dimension"] = dimension
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self.client.get(f"{self.base_url}/metrics", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("metrics", [])

    def get_escalations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent escalations

        Args:
            limit: Max escalations to return

        Returns:
            List of escalation records
        """
        params = {"endpoint": "escalations", "limit": limit}

        response = self.client.get(f"{self.base_url}/metrics", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("escalations", [])

    def get_decision_stats(self, practice_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get decision approval/execution statistics

        Args:
            practice_id: Filter by practice (optional)

        Returns:
            Decision statistics
        """
        params = {"endpoint": "decisions"}
        if practice_id:
            params["practice_id"] = practice_id

        response = self.client.get(f"{self.base_url}/metrics", params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("decision_stats", {})

    def close(self):
        """Close the HTTP client"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ────────────────────────────────────────────────────────────────
# Example usage & smoke tests
# ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os

    # Load from environment
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
        exit(1)

    # Example: send a decision event
    with AutonomyMetricsClient(SUPABASE_URL, SUPABASE_ANON_KEY) as client:
        print("\n=== Sending Decision Event ===")
        result = client.send_decision_event(
            practice_id="empirica-autonomy",
            title="Enable safety gate for Phase 3",
            scope="system-wide",
            dimensions=["truth", "harm"],
            confidence=0.85,
            source_gate="autonomy_gate.py",
            tags=["phase-3", "high-impact"],
        )
        print(json.dumps(result, indent=2))

        # Send escalation event
        print("\n=== Sending Escalation Event ===")
        result = client.send_escalation_event(
            practice_id="empirica-autonomy",
            reason="Cross-practice impact detected",
            severity="high",
            escalated_to="mesh-support",
        )
        print(json.dumps(result, indent=2))

        # Get metrics
        print("\n=== Fetching Metrics ===")
        metrics = client.get_metrics(practice_id="empirica-autonomy", granularity="daily")
        print(f"Found {len(metrics)} metric records")
        for m in metrics[:1]:
            print(json.dumps(m, indent=2, default=str))

        # Get escalations
        print("\n=== Fetching Open Escalations ===")
        escalations = client.get_escalations(limit=5)
        print(f"Found {len(escalations)} escalations")

        # Get decision stats
        print("\n=== Decision Statistics ===")
        stats = client.get_decision_stats(practice_id="empirica-autonomy")
        print(json.dumps(stats, indent=2))

    print("\n✓ All examples completed")

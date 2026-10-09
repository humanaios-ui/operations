"""Activity feed unification across all services."""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from integrations.schemas import Event


logger = logging.getLogger(__name__)


class ActivityFeed:
    """Unified activity feed that merges events from all services."""

    def __init__(self):
        """Initialize empty activity feed."""
        self.events: List[Event] = []
        self.last_updated: Optional[datetime] = None

    def add_event(self, event: Event) -> None:
        """Add a single event to the feed."""
        self.events.append(event)
        self._sort_by_timestamp()
        self.last_updated = datetime.utcnow()

    def add_events(self, events: List[Event]) -> None:
        """Add multiple events to the feed."""
        self.events.extend(events)
        self._sort_by_timestamp()
        self.last_updated = datetime.utcnow()

    def get_recent_events(self, limit: int = 50, service: Optional[str] = None) -> List[Event]:
        """Get recent events, optionally filtered by service."""
        if service:
            filtered = [e for e in self.events if e.service == service]
        else:
            filtered = self.events

        # Return most recent first (already sorted by _sort_by_timestamp)
        return list(reversed(filtered[-limit:]))

    def search_events(
        self, query: str, limit: int = 50, start_date: Optional[datetime] = None
    ) -> List[Event]:
        """Search events by title or resource_id."""
        query_lower = query.lower()
        results = [
            e
            for e in self.events
            if (query_lower in e.title.lower() or query_lower in e.resource_id.lower())
            and (start_date is None or e.timestamp >= start_date)
        ]
        return list(reversed(results[-limit:]))

    def get_by_service(self, service: str) -> List[Event]:
        """Get all events for a specific service."""
        return [e for e in self.events if e.service == service]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the feed."""
        services = {}
        for event in self.events:
            if event.service not in services:
                services[event.service] = {"count": 0, "latest": None}
            services[event.service]["count"] += 1
            if services[event.service]["latest"] is None or event.timestamp > services[event.service]["latest"]:
                services[event.service]["latest"] = event.timestamp.isoformat()

        return {
            "total_events": len(self.events),
            "services": services,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    def _sort_by_timestamp(self) -> None:
        """Sort events by timestamp (oldest first internally, display reversed)."""
        self.events.sort(key=lambda e: e.timestamp)

    def to_json(self) -> List[Dict[str, Any]]:
        """Convert feed to JSON-serializable format."""
        return [e.to_dict() for e in reversed(self.events)]  # Most recent first

    def __repr__(self) -> str:
        return f"ActivityFeed({len(self.events)} events, services={len(set(e.service for e in self.events))})"

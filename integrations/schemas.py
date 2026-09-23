"""Event and response schemas for activity feed unification."""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum


class EventType(Enum):
    """Normalized event types across all services."""

    # Git events
    COMMIT = "commit"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    BRANCH = "branch"

    # Communication events
    EMAIL = "email"
    MESSAGE = "message"

    # Infrastructure events
    DEPLOYMENT = "deployment"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    LOG = "log"

    # Content events
    PUBLICATION = "publication"
    DATASET = "dataset"
    MODEL = "model"
    SPACE = "space"

    # Research events
    PAPER = "paper"
    PREPRINT = "preprint"

    # Administrative events
    SYNC = "sync"
    HEALTH_CHECK = "health_check"
    ERROR = "error"


@dataclass
class Event:
    """Unified event representation across all services."""

    timestamp: datetime
    service: str  # "GitHub", "Gmail", "Supabase", etc.
    event_type: EventType
    resource_id: str  # Repository, email thread, deployment, etc.
    title: str  # Human-readable title
    url: Optional[str] = None  # Link to resource in service
    data: Optional[Dict[str, Any]] = None  # Service-specific metadata
    actor: Optional[str] = None  # Who/what triggered event

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        d["event_type"] = self.event_type.value
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create from dict (reverse of to_dict)."""
        data_copy = data.copy()
        data_copy["timestamp"] = datetime.fromisoformat(data_copy["timestamp"])
        data_copy["event_type"] = EventType(data_copy["event_type"])
        return cls(**data_copy)


@dataclass
class SyncResult:
    """Result of a sync operation for one service."""

    service: str
    timestamp: datetime
    success: bool
    events_returned: int
    error_message: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    next_sync_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        if self.next_sync_at:
            d["next_sync_at"] = self.next_sync_at.isoformat()
        return d


@dataclass
class HealthStatus:
    """Health status of an API integration."""

    service: str
    is_healthy: bool
    last_sync: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0
    rate_limit_reset_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        d = asdict(self)
        if self.last_sync:
            d["last_sync"] = self.last_sync.isoformat()
        if self.rate_limit_reset_at:
            d["rate_limit_reset_at"] = self.rate_limit_reset_at.isoformat()
        return d

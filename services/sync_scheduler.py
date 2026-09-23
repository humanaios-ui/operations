"""Sync scheduler for all API integrations."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from integrations.base import BaseAPIClient
from integrations.schemas import SyncResult, Event
from services.activity_feed import ActivityFeed


logger = logging.getLogger(__name__)


class SyncScheduler:
    """Orchestrates syncing across all API integrations."""

    def __init__(self, registry: Dict[str, Any], activity_feed: ActivityFeed):
        """Initialize scheduler with registry and activity feed."""
        self.registry = registry
        self.activity_feed = activity_feed
        self.clients: Dict[str, BaseAPIClient] = {}
        self.sync_results: List[SyncResult] = []
        self.next_sync_at: Dict[str, Optional[datetime]] = {}

    def register_client(self, client: BaseAPIClient) -> None:
        """Register an API client for syncing."""
        self.clients[client.SERVICE] = client
        self.next_sync_at[client.SERVICE] = datetime.utcnow()  # Sync immediately on first run
        logger.info(f"Registered client: {client.SERVICE}")

    def sync_all(self) -> Dict[str, SyncResult]:
        """Run sync for all registered clients."""
        logger.info("Starting sync cycle for all services")
        results = {}

        for service, client in self.clients.items():
            try:
                result = self._sync_service(client)
                results[service] = result
                self.sync_results.append(result)

                # Add events to activity feed
                if result.success:
                    # Note: In production, we'd query the client again to get actual events
                    logger.info(f"[{service}] Synced {result.events_returned} events")

            except Exception as e:
                logger.error(f"[{service}] Sync failed: {e}", exc_info=True)
                result = SyncResult(
                    service=service,
                    timestamp=datetime.utcnow(),
                    success=False,
                    events_returned=0,
                    error_message=str(e),
                )
                results[service] = result
                self.sync_results.append(result)

        logger.info("Sync cycle complete")
        return results

    def sync_service(self, service: str) -> Optional[SyncResult]:
        """Sync a specific service."""
        if service not in self.clients:
            logger.warning(f"Service {service} not registered")
            return None

        client = self.clients[service]
        return self._sync_service(client)

    def _sync_service(self, client: BaseAPIClient) -> SyncResult:
        """Internal sync for a single service."""
        logger.info(f"[{client.SERVICE}] Starting sync")
        result = client.sync()

        if result.success:
            self.next_sync_at[client.SERVICE] = result.next_sync_at or (
                datetime.utcnow() + timedelta(hours=6)
            )
        else:
            # On failure, retry sooner (exponential backoff)
            failures = client.health.consecutive_failures
            retry_delay = min(3600, 60 * (2 ** min(failures - 1, 4)))  # Max 1 hour
            self.next_sync_at[client.SERVICE] = datetime.utcnow() + timedelta(seconds=retry_delay)

        return result

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health status for all services."""
        health = {}
        for service, client in self.clients.items():
            health[service] = {
                "is_healthy": client.health.is_healthy,
                "last_sync": client.health.last_sync.isoformat() if client.health.last_sync else None,
                "consecutive_failures": client.health.consecutive_failures,
                "last_error": client.health.last_error,
                "next_sync_at": self.next_sync_at.get(service, datetime.utcnow()).isoformat(),
            }
        return health

    def get_sync_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent sync results."""
        return [r.to_dict() for r in self.sync_results[-limit:]]

    def should_sync_service(self, service: str) -> bool:
        """Check if a service is due for sync."""
        if service not in self.next_sync_at:
            return False
        next_sync = self.next_sync_at[service]
        return datetime.utcnow() >= next_sync

    def get_services(self) -> List[str]:
        """Get list of registered services."""
        return list(self.clients.keys())

    def __repr__(self) -> str:
        return f"SyncScheduler({len(self.clients)} clients registered)"

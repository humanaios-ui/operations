"""Base API client for all service integrations."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

from integrations.schemas import Event, SyncResult, HealthStatus


logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """Abstract base class for all service API clients."""

    # Override in subclasses
    SERVICE: str = "unknown"
    AUTH_TYPE: str = "unknown"  # "pat", "oauth", "api_key", "none"
    API_BASE_URL: str = ""
    RATE_LIMIT: str = "unknown"
    RATE_LIMIT_RESET_SECONDS: int = 3600

    def __init__(self, account_id: str, registry: Dict[str, Any]):
        """
        Initialize API client.

        Args:
            account_id: Account identifier from ACCOUNT_REGISTRY.json
            registry: Full account registry for metadata lookup
        """
        self.account_id = account_id
        self.registry = registry
        self.account_data = self._lookup_account(account_id)
        self.health = HealthStatus(service=self.SERVICE, is_healthy=False)
        self.last_sync_at: Optional[datetime] = None

    def _lookup_account(self, account_id: str) -> Dict[str, Any]:
        """Lookup account metadata from registry."""
        for account in self.registry.get("accounts", []):
            if account["id"] == account_id:
                return account
        raise ValueError(f"Account {account_id} not found in registry")

    def get_credential(self) -> Optional[str]:
        """
        Query password manager for credential at query time.

        Credential is returned, used once, then discarded.
        Never stored or logged.

        Returns:
            Credential token/key/password, or None if not required.
        """
        # TODO: Implement credential supplier integration
        # For now, placeholder that would call password manager
        logger.debug(f"[{self.SERVICE}] Requesting credential from password manager")
        return None  # TODO: credential_supplier.get(self.SERVICE, self.account_id)

    @abstractmethod
    def query(self, resource_type: str, **kwargs) -> List[Event]:
        """
        Query API and return normalized events.

        Args:
            resource_type: Type of resource to query (e.g., "repos", "commits")
            **kwargs: Query parameters

        Returns:
            List of Event objects

        Raises:
            Exception: If query fails (rate limit, auth error, etc.)
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Verify API access works.

        Returns:
            True if service is accessible, False otherwise.
        """
        pass

    def sync(self) -> SyncResult:
        """
        Run a complete sync for this service.

        Returns:
            SyncResult with event count, errors, rate limit info
        """
        sync_start = datetime.utcnow()
        logger.info(f"[{self.SERVICE}] Starting sync")

        try:
            # Health check first
            if not self.health_check():
                self.health.consecutive_failures += 1
                return SyncResult(
                    service=self.SERVICE,
                    timestamp=sync_start,
                    success=False,
                    events_returned=0,
                    error_message=f"Health check failed for {self.SERVICE}",
                )

            # Query all resource types
            events = []
            for resource_type in self._get_resource_types():
                try:
                    resource_events = self.query(resource_type)
                    events.extend(resource_events)
                    logger.info(
                        f"[{self.SERVICE}] Queried {resource_type}: {len(resource_events)} events"
                    )
                except Exception as e:
                    logger.error(f"[{self.SERVICE}] Query {resource_type} failed: {e}")
                    # Continue with next resource type

            # Reset health status on success
            self.health.is_healthy = True
            self.health.consecutive_failures = 0
            self.health.last_sync = sync_start
            self.last_sync_at = sync_start

            # Calculate next sync time
            next_sync_at = sync_start + timedelta(hours=6)  # Default: sync every 6 hours

            logger.info(
                f"[{self.SERVICE}] Sync complete: {len(events)} total events"
            )

            return SyncResult(
                service=self.SERVICE,
                timestamp=sync_start,
                success=True,
                events_returned=len(events),
                next_sync_at=next_sync_at,
            )

        except Exception as e:
            self.health.is_healthy = False
            self.health.consecutive_failures += 1
            self.health.last_error = str(e)
            logger.error(f"[{self.SERVICE}] Sync failed: {e}", exc_info=True)

            return SyncResult(
                service=self.SERVICE,
                timestamp=sync_start,
                success=False,
                events_returned=0,
                error_message=str(e),
            )

    def _get_resource_types(self) -> List[str]:
        """Return list of resource types to query for this service."""
        # Override in subclasses
        return []

    def _log_query(self, resource_type: str, status: str, row_count: int):
        """
        Log query for audit trail (no credential, no sensitive data).

        Args:
            resource_type: What was queried
            status: "success", "failure", "rate_limited", etc.
            row_count: How many rows returned
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": self.SERVICE,
            "account_id": self.account_id,
            "resource_type": resource_type,
            "status": status,
            "rows_returned": row_count,
        }
        logger.info(f"AUDIT: {json.dumps(log_entry)}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(service={self.SERVICE}, account={self.account_id})"

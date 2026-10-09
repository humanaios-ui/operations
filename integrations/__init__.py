"""
Account Hub API Integrations

Each service has an integration client that queries its API and returns normalized Event objects.
Credentials are supplied at query time from password manager, never stored.
"""

from .base import BaseAPIClient
from .schemas import Event, EventType

__all__ = ["BaseAPIClient", "Event", "EventType"]

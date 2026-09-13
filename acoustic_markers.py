"""
AcousticMarkers — Async Event Queue & Cortex Integration

Bridges cortex_mailbox_poll events → acoustic marker stream.
Handles 7 event types (proposal, SER, CHECK gate, POSTFLIGHT).
Non-blocking async queue, latency <100ms event ingestion.

Usage:
  markers = AcousticMarkers(marker_broker)
  # On cortex proposal event:
  await markers.handle_cortex_proposal(proposal_data)
  # On SER event:
  await markers.handle_ser_event(ser_data)
  # On CHECK gate:
  await markers.handle_check_gate(check_data)
  # On POSTFLIGHT:
  await markers.handle_postflight(postflight_data)
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict
from enum import Enum

logger = logging.getLogger("acat.acoustic_markers")


class EventType(str, Enum):
    """Cortex event types → acoustic marker mappings"""
    PROPOSAL_ACCEPTED = "proposal_accepted"
    PROPOSAL_CHANGED = "proposal_changed"
    PROPOSAL_DECLINED = "proposal_declined"
    PROPOSAL_FAILED = "proposal_failed"
    SER_OPENED = "ser_opened"
    SER_BLOCKED = "ser_blocked"
    SER_ESCALATION = "ser_escalation"
    CHECK_GATE_PASSED = "check_gate_passed"
    POSTFLIGHT_CLOSED = "postflight_closed"


EVENT_PALETTE = {
    EventType.PROPOSAL_ACCEPTED: {
        "frequency_hz": 523,
        "severity": "info",
        "icon": "✓",
        "description": "Proposal accepted by ECO",
    },
    EventType.PROPOSAL_CHANGED: {
        "frequency_hz": 587,
        "severity": "warning",
        "icon": "↻",
        "description": "Proposal returned for refinement",
    },
    EventType.PROPOSAL_DECLINED: {
        "frequency_hz": 659,
        "severity": "urgent",
        "icon": "✗",
        "description": "Proposal declined by ECO",
    },
    EventType.PROPOSAL_FAILED: {
        "frequency_hz": 698,
        "severity": "urgent",
        "icon": "✗",
        "description": "Proposal execution failed",
    },
    EventType.SER_OPENED: {
        "frequency_hz": 784,
        "severity": "info",
        "icon": "◇",
        "description": "SER opened",
    },
    EventType.SER_BLOCKED: {
        "frequency_hz": 880,
        "severity": "warning",
        "icon": "⊘",
        "description": "SER blocked pending action",
    },
    EventType.SER_ESCALATION: {
        "frequency_hz": 987,
        "severity": "urgent",
        "icon": "⬆",
        "description": "SER escalation triggered",
    },
    EventType.CHECK_GATE_PASSED: {
        "frequency_hz": 1047,
        "severity": "info",
        "icon": "◈",
        "description": "CHECK gate passed",
    },
    EventType.POSTFLIGHT_CLOSED: {
        "frequency_hz": 1174,
        "severity": "info",
        "icon": "⬛",
        "description": "POSTFLIGHT closed",
    },
}


class AcousticMarkers:
    """
    Async event queue for acoustic markers.
    Ingests cortex events, emits as acoustic markers to broker.
    """

    def __init__(self, marker_broker):
        self.marker_broker = marker_broker
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: asyncio.Task | None = None
        self.is_running = False

    async def start(self):
        """Start the async event worker"""
        if self.is_running:
            logger.warn("AcousticMarkers already running")
            return

        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker())
        logger.info("AcousticMarkers started")

    async def stop(self):
        """Stop the async event worker"""
        if not self.is_running:
            return

        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass

        logger.info("AcousticMarkers stopped")

    async def _worker(self):
        """Process events from queue asynchronously"""
        while self.is_running:
            try:
                event_data = await asyncio.wait_for(
                    self.event_queue.get(), timeout=1.0
                )
                await self._process_event(event_data)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _process_event(self, event_data: Dict[str, Any]):
        """Process single event through marker broker"""
        try:
            event_type = event_data.get("event_type")
            if not event_type:
                logger.warning("Event missing event_type")
                return

            palette = EVENT_PALETTE.get(EventType(event_type))
            if not palette:
                logger.warning(f"Unknown event type: {event_type}")
                return

            # Create marker event
            marker_event = {
                "marker_type": event_type,
                "source_id": event_data.get("source_id", "unknown"),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "frequency_hz": palette["frequency_hz"],
                "severity": palette["severity"],
                "icon": palette["icon"],
                "description": palette["description"],
                "metadata": event_data.get("metadata", {}),
            }

            # Format as SSE and publish
            sse_data = f"data: {json.dumps(marker_event)}\n\n"
            for queue in self.marker_broker.subscribers.values():
                try:
                    await queue.put(sse_data)
                except Exception as e:
                    logger.error(f"Failed to queue marker: {e}")

            logger.debug(
                f"Processed marker: {event_type} @ {palette['frequency_hz']}Hz"
            )

        except Exception as e:
            logger.error(f"Error in _process_event: {e}")

    async def handle_cortex_proposal(self, proposal_data: Dict[str, Any]):
        """Handle cortex proposal event"""
        status = proposal_data.get("status")
        event_type = None

        if status == "accepted":
            event_type = EventType.PROPOSAL_ACCEPTED
        elif status == "changed":
            event_type = EventType.PROPOSAL_CHANGED
        elif status == "declined":
            event_type = EventType.PROPOSAL_DECLINED
        elif status == "failed":
            event_type = EventType.PROPOSAL_FAILED

        if event_type:
            event_data = {
                "event_type": event_type.value,
                "source_id": proposal_data.get("id"),
                "metadata": {
                    "proposal_type": proposal_data.get("type"),
                    "source_claude": proposal_data.get("source_claude"),
                    "target_claudes": proposal_data.get("target_claudes"),
                },
            }
            await self.event_queue.put(event_data)

    async def handle_ser_event(self, ser_data: Dict[str, Any]):
        """Handle SER (Shared Epistemic Record) event"""
        state = ser_data.get("coordination_state")
        escalated = ser_data.get("escalation", False)
        event_type = None

        if escalated:
            event_type = EventType.SER_ESCALATION
        elif state == "blocked":
            event_type = EventType.SER_BLOCKED
        elif state == "open":
            event_type = EventType.SER_OPENED

        if event_type:
            event_data = {
                "event_type": event_type.value,
                "source_id": ser_data.get("ser_id"),
                "metadata": {
                    "state": state,
                    "participants": len(ser_data.get("participants", [])),
                },
            }
            await self.event_queue.put(event_data)

    async def handle_check_gate(self, check_data: Dict[str, Any]):
        """Handle CHECK gate event"""
        event_data = {
            "event_type": EventType.CHECK_GATE_PASSED.value,
            "source_id": check_data.get("transaction_id"),
            "metadata": {
                "decision": check_data.get("decision"),
                "vectors": check_data.get("vectors"),
            },
        }
        await self.event_queue.put(event_data)

    async def handle_postflight(self, postflight_data: Dict[str, Any]):
        """Handle POSTFLIGHT event"""
        event_data = {
            "event_type": EventType.POSTFLIGHT_CLOSED.value,
            "source_id": postflight_data.get("transaction_id"),
            "metadata": {
                "completion": postflight_data.get("completion"),
                "artifacts_logged": postflight_data.get("artifacts_logged", 0),
            },
        }
        await self.event_queue.put(event_data)

    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.event_queue.qsize()

    async def wait_until_empty(self, timeout_seconds: float = 10.0):
        """Wait for queue to empty (for testing/shutdown)"""
        start = asyncio.get_event_loop().time()
        while self.event_queue.qsize() > 0:
            if asyncio.get_event_loop().time() - start > timeout_seconds:
                logger.warning(f"Queue not empty after {timeout_seconds}s")
                return False
            await asyncio.sleep(0.1)
        return True

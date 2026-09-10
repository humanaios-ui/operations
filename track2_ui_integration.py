"""
Track 2 UI Integration — Acoustic Marker SSE Endpoint

Streams cortex marker events to humanaios-ui as Server-Sent Events (SSE).
Provides real-time marker notifications (9 types) for orchestration feedback.

Markers:
- proposal_accepted (523Hz, info)
- proposal_changed (587Hz, warning)
- proposal_declined (659Hz, urgent)
- proposal_failed (698Hz, urgent)
- ser_opened (784Hz, info)
- ser_blocked (880Hz, warning)
- ser_escalation (987Hz, urgent)
- check_gate_passed (1047Hz, info)
- postflight_closed (1174Hz, info)
"""

import asyncio
import json
import logging
from typing import AsyncGenerator
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from acat.api.security import require_read_token
from acoustic_markers import AcousticMarkers

logger = logging.getLogger("acat.track2")

router = APIRouter()


# ============================================
# MARKER DEFINITIONS
# ============================================

class MarkerType(str, Enum):
    """Track 2 acoustic marker types"""
    PROPOSAL_ACCEPTED = "proposal_accepted"
    PROPOSAL_CHANGED = "proposal_changed"
    PROPOSAL_DECLINED = "proposal_declined"
    PROPOSAL_FAILED = "proposal_failed"
    SER_OPENED = "ser_opened"
    SER_BLOCKED = "ser_blocked"
    SER_ESCALATION = "ser_escalation"
    CHECK_GATE_PASSED = "check_gate_passed"
    POSTFLIGHT_CLOSED = "postflight_closed"


MARKER_PALETTE = {
    MarkerType.PROPOSAL_ACCEPTED: {
        "frequency_hz": 523,
        "severity": "info",
        "icon": "✓",
        "description": "Proposal accepted by ECO",
    },
    MarkerType.PROPOSAL_CHANGED: {
        "frequency_hz": 587,
        "severity": "warning",
        "icon": "↻",
        "description": "Proposal returned for refinement",
    },
    MarkerType.PROPOSAL_DECLINED: {
        "frequency_hz": 659,
        "severity": "urgent",
        "icon": "✗",
        "description": "Proposal declined by ECO",
    },
    MarkerType.PROPOSAL_FAILED: {
        "frequency_hz": 698,
        "severity": "urgent",
        "icon": "✗",
        "description": "Proposal execution failed",
    },
    MarkerType.SER_OPENED: {
        "frequency_hz": 784,
        "severity": "info",
        "icon": "◇",
        "description": "SER opened",
    },
    MarkerType.SER_BLOCKED: {
        "frequency_hz": 880,
        "severity": "warning",
        "icon": "⊘",
        "description": "SER blocked pending action",
    },
    MarkerType.SER_ESCALATION: {
        "frequency_hz": 987,
        "severity": "urgent",
        "icon": "⬆",
        "description": "SER escalation triggered",
    },
    MarkerType.CHECK_GATE_PASSED: {
        "frequency_hz": 1047,
        "severity": "info",
        "icon": "◈",
        "description": "CHECK gate passed",
    },
    MarkerType.POSTFLIGHT_CLOSED: {
        "frequency_hz": 1174,
        "severity": "info",
        "icon": "⬛",
        "description": "POSTFLIGHT closed",
    },
}


# ============================================
# MARKER EVENT MODEL
# ============================================

class MarkerEvent:
    """Represents a single marker event"""

    def __init__(
        self,
        marker_type: MarkerType,
        source_id: str,
        timestamp: str = None,
        metadata: dict = None,
    ):
        self.marker_type = marker_type
        self.source_id = source_id
        self.timestamp = timestamp or datetime.utcnow().isoformat() + "Z"
        self.metadata = metadata or {}
        self.palette = MARKER_PALETTE[marker_type]

    def to_sse_event(self) -> str:
        """Format as SSE event for streaming"""
        event_data = {
            "marker_type": self.marker_type.value,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "frequency_hz": self.palette["frequency_hz"],
            "severity": self.palette["severity"],
            "icon": self.palette["icon"],
            "description": self.palette["description"],
            "metadata": self.metadata,
        }
        return f"data: {json.dumps(event_data)}\n\n"

    @staticmethod
    def from_cortex_proposal(proposal_data: dict) -> list["MarkerEvent"]:
        """Convert cortex proposal event to marker event(s)"""
        marker_type = None
        status = proposal_data.get("status")
        proposal_type = proposal_data.get("type")

        # Map proposal status to marker type
        if status == "accepted":
            marker_type = MarkerType.PROPOSAL_ACCEPTED
        elif status == "changed":
            marker_type = MarkerType.PROPOSAL_CHANGED
        elif status == "declined":
            marker_type = MarkerType.PROPOSAL_DECLINED
        elif status == "failed":
            marker_type = MarkerType.PROPOSAL_FAILED

        if marker_type:
            return [
                MarkerEvent(
                    marker_type=marker_type,
                    source_id=proposal_data.get("id"),
                    metadata={
                        "proposal_type": proposal_type,
                        "source_claude": proposal_data.get("source_claude"),
                        "target_claudes": proposal_data.get("target_claudes"),
                    },
                )
            ]
        return []

    @staticmethod
    def from_ser_event(ser_data: dict) -> list["MarkerEvent"]:
        """Convert SER event to marker event(s)"""
        marker_type = None
        state = ser_data.get("coordination_state")
        escalated = ser_data.get("escalation", False)

        if escalated:
            marker_type = MarkerType.SER_ESCALATION
        elif state == "blocked":
            marker_type = MarkerType.SER_BLOCKED
        elif state == "open":
            marker_type = MarkerType.SER_OPENED

        if marker_type:
            return [
                MarkerEvent(
                    marker_type=marker_type,
                    source_id=ser_data.get("ser_id"),
                    metadata={
                        "state": state,
                        "participants": ser_data.get("participants"),
                    },
                )
            ]
        return []


# ============================================
# MARKER BROKER (Mock for MVP)
# ============================================

class MarkerBroker:
    """Manages marker event subscriptions and streaming"""

    def __init__(self):
        self.subscribers = {}
        self._event_queue = asyncio.Queue()

    async def subscribe(self, subscriber_id: str) -> AsyncGenerator:
        """Subscribe to marker events"""
        queue = asyncio.Queue()
        self.subscribers[subscriber_id] = queue
        logger.info(f"Subscriber {subscriber_id} connected")

        try:
            # Send heartbeat every 30s to keep connection alive
            async def heartbeat():
                while True:
                    try:
                        await asyncio.sleep(30)
                        await queue.put(": heartbeat\n\n")
                    except asyncio.CancelledError:
                        break

            heartbeat_task = asyncio.create_task(heartbeat())

            while True:
                event = await queue.get()
                yield event
        except asyncio.CancelledError:
            pass
        finally:
            heartbeat_task.cancel()
            if subscriber_id in self.subscribers:
                del self.subscribers[subscriber_id]
            logger.info(f"Subscriber {subscriber_id} disconnected")

    async def publish(self, marker: MarkerEvent):
        """Publish marker to all subscribers"""
        sse_event = marker.to_sse_event()
        for queue in self.subscribers.values():
            try:
                await queue.put(sse_event)
            except Exception as e:
                logger.warning(f"Failed to publish marker to subscriber: {e}")

    async def publish_proposal_event(self, proposal_data: dict):
        """Publish cortex proposal event as markers"""
        markers = MarkerEvent.from_cortex_proposal(proposal_data)
        for marker in markers:
            await self.publish(marker)

    async def publish_ser_event(self, ser_data: dict):
        """Publish SER event as markers"""
        markers = MarkerEvent.from_ser_event(ser_data)
        for marker in markers:
            await self.publish(marker)


# Global marker broker instance
_marker_broker = MarkerBroker()

# Global acoustic markers handler (async event queue)
_acoustic_markers: AcousticMarkers | None = None


def get_marker_broker() -> MarkerBroker:
    """Get the global marker broker"""
    return _marker_broker


def get_acoustic_markers() -> AcousticMarkers:
    """Get the global acoustic markers handler"""
    global _acoustic_markers
    if _acoustic_markers is None:
        _acoustic_markers = AcousticMarkers(_marker_broker)
    return _acoustic_markers


async def start_acoustic_markers():
    """Start the acoustic markers event worker"""
    markers = get_acoustic_markers()
    if not markers.is_running:
        await markers.start()
        logger.info("Acoustic markers worker started")


async def stop_acoustic_markers():
    """Stop the acoustic markers event worker"""
    global _acoustic_markers
    if _acoustic_markers and _acoustic_markers.is_running:
        await _acoustic_markers.stop()
        logger.info("Acoustic markers worker stopped")


# ============================================
# ENDPOINTS
# ============================================

@router.get("/markers/stream", dependencies=[Depends(require_read_token)])
async def stream_markers(request) -> StreamingResponse:
    """
    SSE endpoint for streaming marker events to UI.

    Usage (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/v1/sonify/markers/stream');
    eventSource.addEventListener('message', (event) => {
      const marker = JSON.parse(event.data);
      // render marker notification
    });
    ```
    """
    broker = get_marker_broker()
    subscriber_id = f"{request.client.host}:{request.client.port}"

    async def event_generator():
        async for event in broker.subscribe(subscriber_id):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable proxy buffering
        },
    )


@router.post("/markers/event", dependencies=[Depends(require_read_token)])
async def ingest_marker_event(event_data: dict) -> dict:
    """
    Ingest cortex event and emit as marker.

    Request payload:
    ```json
    {
      "event_type": "proposal",
      "data": { ...cortex proposal data... }
    }
    ```

    Routes events through AcousticMarkers async queue for non-blocking ingestion.
    """
    markers = get_acoustic_markers()
    event_type = event_data.get("event_type")
    data = event_data.get("data", {})

    try:
        if event_type == "proposal":
            await markers.handle_cortex_proposal(data)
        elif event_type == "ser":
            await markers.handle_ser_event(data)
        elif event_type == "check_gate":
            await markers.handle_check_gate(data)
        elif event_type == "postflight":
            await markers.handle_postflight(data)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {"ok": False, "detail": f"Unknown event type: {event_type}"}

        return {
            "ok": True,
            "event_type": event_type,
            "queue_size": markers.get_queue_size(),
        }
    except Exception as e:
        logger.error(f"Failed to ingest marker event: {e}")
        raise HTTPException(status_code=500, detail="Marker ingestion failed")


# ============================================
# APP LIFECYCLE (integrate with FastAPI startup/shutdown)
# ============================================
# In main.py, add:
#   @app.on_event("startup")
#   async def startup_event():
#       from operations.track2_ui_integration import start_acoustic_markers
#       await start_acoustic_markers()
#
#   @app.on_event("shutdown")
#   async def shutdown_event():
#       from operations.track2_ui_integration import stop_acoustic_markers
#       await stop_acoustic_markers()


@router.get("/markers/palette", dependencies=[Depends(require_read_token)])
async def get_marker_palette() -> dict:
    """
    Get marker palette (types, frequencies, icons, severity levels).

    Used by UI to configure marker rendering.
    """
    return {
        "ok": True,
        "palette": {
            marker_type.value: {
                "frequency_hz": info["frequency_hz"],
                "severity": info["severity"],
                "icon": info["icon"],
                "description": info["description"],
            }
            for marker_type, info in MARKER_PALETTE.items()
        },
        "total_markers": len(MARKER_PALETTE),
    }


# ============================================
# HELPER FUNCTIONS (for testing)
# ============================================

async def emit_test_marker(marker_type: MarkerType, source_id: str = "test"):
    """Emit a test marker (for development/testing)"""
    broker = get_marker_broker()
    marker = MarkerEvent(marker_type=marker_type, source_id=source_id)
    await broker.publish(marker)
    logger.info(f"Test marker emitted: {marker_type.value}")

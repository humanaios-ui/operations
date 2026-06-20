“””
Triage Log Service

Persists humanaios-triage-finding TRIAGE_BLOCK outputs to acat_triage_log
(see acat_triage_log_migration.sql), and computes Advance Pass Rate from
those rows once they accumulate.

This is intentionally separate from registry_loader.py: registry_loader
reads REGISTERED.md (Validation side, retroactively complete back to the
start of the registry). This module reads/writes acat_triage_log (Advance
side, complete only from whenever the triage skill starts calling
persist_triage_block() going forward – it has no retroactive data and is
honest about that until rows exist).
“””
from **future** import annotations

import json
import os
import ssl
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi

class PersistenceError(RuntimeError):
“”“Raised when a Supabase read/write against acat_triage_log fails.”””

VALID_GATE_VERDICTS = {“ROUTE_TO_Z2”, “HOLD”, “STOP”}
VALID_PROPOSED_CLASSES = {“F”, “IC”, “H”}

def _get_supabase_env() -> tuple[str, str]:
url = os.getenv(“SUPABASE_URL”)
key = os.getenv(“SUPABASE_SERVICE_ROLE_KEY”) or os.getenv(“SUPABASE_KEY”)
if not url:
raise PersistenceError(“Missing required env var: SUPABASE_URL”)
if not key:
raise PersistenceError(“Missing required env var: SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY”)
return url.rstrip(”/”), key

def _ssl_context() -> ssl.SSLContext:
return ssl.create_default_context(cafile=certifi.where())

def _supabase_request(method: str, path_and_query: str, body: Optional[dict] = None) -> list[dict]:
supabase_url, service_key = _get_supabase_env()
headers = {
“apikey”: service_key,
“Authorization”: f”Bearer {service_key}”,
“Accept”: “application/json”,
}
data = None
if body is not None:
headers[“Content-Type”] = “application/json”
headers[“Prefer”] = “return=representation”
data = json.dumps(body).encode(“utf-8”)

```
request = Request(
    f"{supabase_url}/rest/v1/{path_and_query}",
    data=data,
    headers=headers,
    method=method,
)
try:
    with urlopen(request, timeout=15, context=_ssl_context()) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else []
except HTTPError as exc:
    detail = exc.read().decode("utf-8", errors="replace")
    raise PersistenceError(f"Supabase request failed with HTTP {exc.code}: {detail}") from exc
except URLError as exc:
    raise PersistenceError(f"Supabase request connection failed: {exc}") from exc
```

def persist_triage_block(triage_block: dict) -> dict:
“”“Write one TRIAGE_BLOCK to acat_triage_log.

```
Expected shape (matches humanaios-triage-finding's output structure):
    {
        "session_id": "S-061726-NN",
        "observation_summary": "...",
        "proposed_class": "F" | "IC" | "H",
        "proposed_dimensions": ["humility", ...],
        "gate_results": {"q1": {...}, ..., "q7": {...}},
        "gate_verdict": "ROUTE_TO_Z2" | "HOLD" | "STOP",
        "evidence_package": {...} or None,
        "proposed_entry_draft": "..." or None,
        "gaps_to_address": ["...", ...] or None,
    }

Does not validate Q1-Q7 logic -- that's the triage skill's job. This
only validates the shape is loggable and writes it. registered_id is
not set here; it gets backfilled later, manually, once/if Zone 2
ratifies and an id exists in REGISTERED.md.
"""
verdict = triage_block.get("gate_verdict")
if verdict not in VALID_GATE_VERDICTS:
    raise ValueError(f"gate_verdict must be one of {VALID_GATE_VERDICTS}, got {verdict!r}")

proposed_class = triage_block.get("proposed_class")
if proposed_class is not None and proposed_class not in VALID_PROPOSED_CLASSES:
    raise ValueError(f"proposed_class must be one of {VALID_PROPOSED_CLASSES} or None, got {proposed_class!r}")

if not triage_block.get("observation_summary"):
    raise ValueError("observation_summary is required")

if not triage_block.get("gate_results"):
    raise ValueError("gate_results is required (the Q1-Q7 result dict)")

row = {
    "session_id": triage_block.get("session_id"),
    "observation_summary": triage_block["observation_summary"],
    "proposed_class": proposed_class,
    "proposed_dimensions": triage_block.get("proposed_dimensions"),
    "gate_results": triage_block["gate_results"],
    "gate_verdict": verdict,
    "evidence_package": triage_block.get("evidence_package"),
    "proposed_entry_draft": triage_block.get("proposed_entry_draft"),
    "gaps_to_address": triage_block.get("gaps_to_address"),
}

result = _supabase_request("POST", "acat_triage_log", body=row)
if not result:
    raise PersistenceError("acat_triage_log insert returned no row")
return result[0]
```

def backfill_registered_id(triage_log_id: str, registered_id: str) -> dict:
“”“Link a previously-logged triage row to the id it was eventually
assigned in REGISTERED.md, once/if Zone 2 ratifies it. Manual call –
nothing here watches REGISTERED.md for changes.”””
result = _supabase_request(
“PATCH”,
f”acat_triage_log?id=eq.{triage_log_id}”,
body={“registered_id”: registered_id},
)
if not result:
raise PersistenceError(f”No acat_triage_log row found for id={triage_log_id}”)
return result[0]

def compute_advance_pass_rate(min_rows_for_confidence: int = 10) -> dict:
“”“Advance Pass Rate = ROUTE_TO_Z2 rows / total triage rows logged.

```
Honest about the cold-start problem: this table has no retroactive
history. Until enough rows accumulate, the rate is reported but flagged
low-confidence rather than presented as a stable number.
"""
rows = _supabase_request("GET", "acat_triage_log?select=gate_verdict")
total = len(rows)

if total == 0:
    return {
        "advance_pass_rate": None,
        "total_logged": 0,
        "confidence": "no_data",
        "note": "acat_triage_log is empty. Advance Pass Rate has no retroactive "
                "history -- it only becomes computable once the triage skill "
                "starts calling persist_triage_block() going forward.",
    }

route_to_z2 = sum(1 for r in rows if r.get("gate_verdict") == "ROUTE_TO_Z2")
hold = sum(1 for r in rows if r.get("gate_verdict") == "HOLD")
stop = sum(1 for r in rows if r.get("gate_verdict") == "STOP")

return {
    "advance_pass_rate": round(route_to_z2 / total, 4),
    "total_logged": total,
    "counts": {"route_to_z2": route_to_z2, "hold": hold, "stop": stop},
    "confidence": "low" if total < min_rows_for_confidence else "ok",
    "note": (
        f"Based on {total} logged triage runs."
        + (f" Fewer than {min_rows_for_confidence} rows -- treat as directional, not stable."
           if total < min_rows_for_confidence else "")
    ),
}
```
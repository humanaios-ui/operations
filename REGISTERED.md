# REGISTERED.md — Proposal Registry (Canonical)

**Purpose:** Authoritative log of all Z1 candidate blocks awaiting/ratified Z2 approval  
**Authority:** Z2 sole write; sha256 hash required on all entries  
**Model:** Resource-based; no time-based deadlines; Z2 ratifies when capacity permits  
**Updated:** 2026-09-14T00:00:00Z

---

## Active Proposals (Awaiting Z2 Ratification)

- Q-TEMPORAL-DISSOLUTION-01: Remove time-based deadlines; adopt resource-based model
- Q-ZONE-REGISTRY-01: Create ZONE_REGISTRY.md (31 repos, executor assignments, caps)
- Q-BOOT-PROCESS-MAP-01: Create BOOT_PROCESS_MAP.md (session rituals → resource states)
- Q-CANDIDATE-BLOCK-TEMPLATE-01: Create CANDIDATE_BLOCK_TEMPLATE.md (template + examples)
- Q-GOVERNANCE-FILES-01: Create GOVERNANCE_FILES.md (registry of all governance files)

---

## Ratified Proposals (Z2 Signed)

(None yet; awaiting Z2 ratification)

---

## Structure

REGISTERED.md tracks candidates from proposal → ratification → execution.
Each entry includes:
- candidate_id (unique)
- title
- author (Z1)
- resource_cost (effort units)
- falsifier (required)
- z2_decision (status + hash)

See CANDIDATE_BLOCK_TEMPLATE.md for full YAML schema.

---

## Authority

- Z2 sole write (Night)
- Falsifier required (CI gate enforces)
- No time-based deadlines (resource-based model)
- Live-fetch at session start (IC-030)

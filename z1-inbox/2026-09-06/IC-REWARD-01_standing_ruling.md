# IC-REWARD-01 — standing ruling (candidate; Z2 prose ratification 2026-09-05; hash pending)

**Ruling:** No reward or allocation constant changes outside a molt, regardless of layer.

**Scope:** Any constant that sets how value, priority, credit, payment, or task assignment is distributed — in the Priority Queue, the Agent Runtime, GRBS brokerage, or any external orchestration layer. "Layer" includes schedulers, orchestrators, and third-party services acting on our behalf.

**Mechanism:** Such a constant carries a molt_id. A change requires: pinned prediction → Z2 ratification hash → measured window → KEEP or mechanical REVERT. Real-time adjustment is permitted only inside a ratified envelope (caps in gate; beyond cap = Z2_REQUIRED). Telemetry feeds NF_LEDGER and may generate a MOLT_CANDIDATE; it never writes the constant.

**Enforcement locus:** CI rejects any constant change in the reward/allocation class without a molt_id (extends the existing Constants rule). External orchestration layers receive constants read-only.

**Falsifier:** If a reward or allocation value in any live system is found to differ from the last ratified molt value, the ruling has been bypassed and the discrepancy is logged as an IC event.

**Lineage:** Third appearance of the real-time-reward defect — role spec (09-01), execution charter (09-03), orchestration proposal (09-05). Recorded so it is ruled once, not audited each time.

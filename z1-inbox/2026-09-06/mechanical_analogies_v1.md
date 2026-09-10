# Mechanical analogies for HumanAIOS — coverage table
docs/concepts/mechanical_analogies_v1.md · issued 2026-09-05 · Z1 · ratified in part (see status column) · analogies are teaching aids, not rules; the rules are in code.

## Why three lineages
No single machine covers the system. Trains cover *exclusion*. Pneumatic power covers *flow, regulation, relief, one-way history*. Pneumatic instrumentation covers *record, accumulated memory, prediction, calibration against an external standard*. One gap stays open on purpose.

## Coverage table

| System property | Mechanical analog | Lineage | Ground truth | Tier | Status |
|---|---|---|---|---|---|
| One open molt per constant; nothing on main without a hash | One train per block; interlocking; token | Trains | Block signalling / token-block working — not re-read this pass | CLAIM | prior session |
| Z2 time is the finite source | Compressor | Pneumatic power | — (structural) | n/a | ratified 09-05 |
| Backlog holds work under pressure | Receiver tank | Pneumatic power | — | n/a | ratified 09-05 |
| READY gate passes work at set level, regardless of backlog size | Regulator | Pneumatic power | — | n/a | ratified 09-05 |
| Append-only log; no rewrite of history | Check valve (non-return) | Pneumatic power | — | n/a | ratified 09-05 |
| Drawdown halt; beyond cap = Z2_REQUIRED; no discretion | Relief valve | Pneumatic power | — | n/a | ratified 09-05 |
| Molt: small telemetry signal proposes, Z2 opens the main change | Pilot valve | Pneumatic power | — | n/a | ratified 09-05 |
| Reads without changing; calibration ledger | Gauge (existing callout name) | Pneumatic power | — | n/a | ratified 09-05 |
| falsifier_lint, claim_lint, VOID-CIT remove contaminants before entry | Filter / dryer | Pneumatic power | — | n/a | ratified 09-05 |
| LAID = installed; OPERATED = has cycled | Actuator | Pneumatic power | — | n/a | ratified 09-05 |
| Reads from memory = pressure lost without work; Stale Sweep finds it | Leak | Pneumatic power | — | n/a | ratified 09-05 |
| **Two media: LLM and human sides are soft (flip rate = compressibility); CI and hash chain are stiff; the gate converts one to the other** | Air vs oil | Pneumatic power | — (the ratified core) | n/a | **ratified 09-05** |
| REGISTERED.md: append-only, time attached to every mark, pen cannot go back | Chart recorder | Pneumatic instrumentation | Foxboro shipped its first multiple-pen temperature recorder in 1909 (Control Engineering, Foxboro centennial) | VERIFIED | proposed |
| Learning trajectory: present read / accumulated error / anticipation | PID controller: proportional / integral (reset) / derivative (pre-act) | Pneumatic instrumentation | Foxboro Stabilog introduced reset (integral) in the 1920s–1931 (Foxboro history; Åström & Kumar, Automatica 2014 via ECE 486 slides). Date dispute: Dataforth AN122 credits Taylor's Fulscope (1939) as first full PID, Foxboro second the same year. | VERIFIED (dispute logged) | proposed |
| Anti-cascade rule: no candidate from events inside its own window | Integral windup / anti-windup | Pneumatic instrumentation | Not read this pass | CLAIM | proposed |
| The record as tiebreaker; Z1 and Z2 are two gauges calibrated against it, never against each other | Deadweight tester (piston gauge, pressure balance) | Pneumatic instrumentation | Primary pressure standard; generates pressure from mass, gravity, piston area (P = F/A), no electronics; NIST-traceable; one vendor: "accuracy independent of the operator" (Mensor/WIKA; Fluke/Pressurements; AMETEK RK) | VERIFIED | proposed |
| Stale Sweep half-life | Recalibration interval | Pneumatic instrumentation | DH-Budenberg CPB5800 lists a recommended 5-year recalibration cycle | VERIFIED (one example) | proposed |
| Session handoff without a jolt (handoff block → z2_ledger) | Bumpless transfer between manual and automatic | Pneumatic instrumentation | Foxboro 43AP spec: "bumpless with 2-position switch, balance gauge, and regulator"; Foxboro 1960s: "bumpless/balanceless transfer" | VERIFIED | new this pass |
| Learning as *improvement* — getting better at accumulating, not just accumulating | **none** | — | A PID controller has fixed gains; self-tuning arrived only in the 1980s (Foxboro Exact) and is a different lineage | — | GAP, left open |

## Shared-delusion guard, in instrument terms
Comparison calibration (gauge against gauge) is the known hazard; reference calibration (gauge against a primary standard) is the discipline. Two gauges agreeing while both drift from the standard is exactly the case DELUSION-GUARD flags. Deadweight testers exist because the industry learned this the hard way.

## Falsifier for the analogy set
If a ratified system property has no analog in any of the three lineages and cannot be logged as a deliberate GAP, the analogy set is incomplete and this doc is reopened. Current deliberate GAP: 1.

## Provenance
Trains: prior session, not re-read. Pneumatic power: structural, no external claim. Pneumatic instrumentation: read 2026-09-05 (Control Engineering Foxboro centennial; Dataforth AN122; Åström & Kumar 2014 via ECE 486 lecture 1; Mensor/WIKA deadweight page; Fluke/Pressurements catalogue; Instrumart CPB5800 and Ashcroft 1305D; im-tek Foxboro 43AP spec). Integral windup and block signalling: CLAIM pending read.

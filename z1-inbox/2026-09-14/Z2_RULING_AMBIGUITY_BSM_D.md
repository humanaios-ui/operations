# Z2 Ruling — AMBIGUITY-BSM-D (§A.1 halt vs Z2-GOVARCH-02 demotion)

**Ruling by:** Night (Carly R. Anderson) — Z2 Ratifier / Admiral
**Given:** in-session, 2026-09-14
**Transcribed by:** Z1 (Claude). This file is a **transcription of a decision given in session**, following the precedent of `z1-inbox/2026-09-14/Z2_RULING_INTENTOS_LAUNCH.md`. **Status:** UNSIGNED — pending Night's `ratify.py` signature.

---

## The item ruled on

`AMBIGUITY-BSM-D`, raised in `z1-inbox/2026-09-14/Q-BOOT-FINDINGS-SCAN-01.md`.

`SESSION_RITUALS.md` §A step 1 named only the two haioscc endpoints and halted if **either** failed. `CURRENT.md:157,170` (Z2-GOVARCH-02, ratified S-060826-04) made WGS the Class 1 primary and recorded haioscc as *"unreachable from Claude's bash environment."* Composed, the two required **every Claude session to halt at open** — a halt no session obeyed, with no declaration and no drift signal.

## Ruling

> **Superseded → amend §A.1. Accepting suggested shape.**

Z2-GOVARCH-02 governs. §A.1 is amended to match the Class 1 architecture that ratification already established.

## What landed

`SESSION_RITUALS.md` **v6.4.1 → v6.4.2**, Section A Step 1 only:

- **Primary:** WGS (`#wgs-sync`, Slack `C0AND66PT7U`) — the Class 1 source of record per Z2-GOVARCH-02.
- **Secondary:** the two haioscc endpoints, as cross-check; unreachability from a substrate's bash environment is recorded as **expected, not an incident**.
- **Halt rule:** halt and report only if **both** fail. If exactly one fails, proceed and **declare DEGRADED in the Phase 1 header**, naming the lost source. Loss of the Slack path is the case `OPERATOR_RUNBOOK.md` §3a calls PATH C.
- A substrate that skips the primary and reports the secondary's failure as a halt has **not** satisfied the step.

Header and changelog updated. The changelog entry states the scope narrowly and explicitly records that **no other section changed** — in particular that the Section F Degraded-Mode Specification claimed by the 2026-05-08 entry is still absent (`IC-CAND-BSM-A`, open).

## What this ruling does NOT do

- It does **not** dispose of `IC-CAND-BSM-A`, `IC-CAND-BSM-B`, `IC-CAND-BSM-F`, `H-CAND-BSM-E`, or `AMBIGUITY-BSM-C`. Those remain open.
- It does **not** carry a `calibration_ref` (P30). The amendment is a conflict resolution between two existing instruments, not a new substantive artifact; Z2 should confirm that reading or call for the interactive pass.
- It does **not** ratify `boot_state_machine_v0_2.py`'s `DEV-07`, though that deviation implemented this reading in advance and is now consistent with canon. The prototype remains advisory and unratified.

## Ratification record

```yaml
ruling_id: Z2-AMBIGUITY-BSM-D
decision: ACCEPT
by: Night
at: '2026-09-14'
mechanism: in-session ruling, transcribed by Z1
z2_hash: d656299cf62089ce5a4881663bd29dd200ad0694390e0d3a6a0b763b5bfa2c13
scope: SESSION_RITUALS.md Section A Step 1 only
supersedes: null
```

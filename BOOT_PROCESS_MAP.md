# HumanAIOS Boot Process Map
## REGISTERED.md's Position in the Session Boot Chain

**Source:** SESSION_RITUALS.md §A (Session open) / §B (Session close), CLAUDE.md §A/§B, GOVERNANCE.md, ZONE_REGISTRY.md
**Mapping Date:** 2026-09-14
**Authority:** Z2 (Night) ratification pending
**Status:** Z1 candidate for REGISTERED.md

---

## Why this mapping

SESSION_RITUALS.md §A already specifies a strict, ordered, halt-on-failure fetch
sequence for every session open. That sequence *is* a boot chain — it has the
same shape as a computer bringing itself from power-on to a login prompt:
firmware integrity checks before trusting a payload, a loader that hands off to
a larger image, device/service enumeration, and a documented halt behavior
instead of continuing on unverified state. This document names each stage
explicitly so REGISTERED.md's role (and its IC-029/IC-030 halt conditions) has
the same precision as the rest of the chain. It uses the same paired-mapping +
diagram format as FRAMEWORK_MAPPING.md.

---

## Executive Summary

| Boot Chain Stage | HumanAIOS Equivalent | Governing File(s) | On Failure |
|:---|:---|:---|:---|
| **POST** (power-on self-test) | Fetch live operational state | `haioscc.pages.dev/api/state/*` | Halt, report (SESSION_RITUALS §A.1) |
| **Firmware / Secure Boot** | Pin SHA + verify file hashes | `git fetch`, manifest sha256 check | Halt — do not trust unsigned state |
| **Bootloader** | Load session protocol | `SESSION_RITUALS.md` | Fetch fails → halt, report |
| **Boot parameters / policy** | Load standing principles | `GOVERNANCE.md`, `CURRENT.md` | Proceed on last-known if fetch fails is NOT allowed — halt |
| **Kernel image** | Load registered findings/context | `REGISTERED.md` (pinned SHA, live-fetch) | DEGRADED mode (IC-029/IC-030 halt) |
| **Device/node enumeration** | Enumerate active zones/repos | `ZONE_REGISTRY.md` | Zone misalignment = merge block |
| **Init / unit ordering** | Ranked work queue | `PRIORITY_QUEUE.md` | Blocked row without unblock action → GAP callout |
| **Kernel permission model** | Authority tiers (Z1/Z2/Z3) | `CLAUDE.md` | Action outside cap → escalate to Z2 |
| **Boot log / dmesg** | Drift catalog + Phase 1 declaration | SESSION_RITUALS §A.5-6 | — |
| **Login prompt** | Wait for user confirmation | SESSION_RITUALS §A.7 | Work does not begin until acknowledged |
| **Runtime tuning (sysctl)** | Molt cycle, constants | `molt_cycle.py`, `constants.json`, `MOLT_STATE.md` | Anti-cascade freeze (K=3, revert-twice rule) |
| **Shutdown / sync** | Session close | SESSION_RITUALS §B | B.0 hard gate before any close artifact |
| **Journal (immutable log)** | Append-only ledger | `NF_LEDGER.jsonl` | Hash-chain validation |

---

## Detailed Mapping

### 1. POST — Power-On Self-Test
**Concept:** Before anything else, hardware checks that the machine is even capable of booting — power rails, memory, attached devices. A POST failure halts before the bootloader ever runs.

**HumanAIOS Mapping:** SESSION_RITUALS §A Step 1 — `GET /api/state/operational` and `GET /api/state/zone3?status=open`. This is the "is the operational substrate alive" check. If either fetch fails, the session halts and reports — exactly a POST failure, before any protocol file is even read.

**Files Involved:** `haioscc.pages.dev/api/state/operational`, `haioscc.pages.dev/api/state/zone3`

---

### 2. Firmware / Secure Boot — Integrity Verification
**Concept:** Firmware (BIOS/UEFI) verifies the signature of what it is about to load before handing off control. Secure Boot refuses to chain-load an image whose signature doesn't match — that's the whole point: don't trust content merely because it's present.

**HumanAIOS Mapping:** `git fetch && git rev-parse HEAD` (pin SHA) plus the manifest sha256 verification of REGISTERED.md/ZONE_REGISTRY.md (CLAUDE.md §A step 5). This is a direct secure-boot analogue: a session must not proceed on a REGISTERED.md whose hash it hasn't checked against the pinned SHA. **IC-030** ("live-fetch, pin SHA") is the secure-boot policy statement — "do not boot from a payload you have not freshly verified," not "trust whatever is cached from a prior session."

**Files Involved:** `.git` (SHA pin), sha256 manifest (per CLAUDE.md §A.5)

**Failure mode:** Stale or unverifiable hash → registry-touching halt (SESSION_RITUALS §F.9), same posture as Secure Boot refusing an unsigned kernel.

---

### 3. Bootloader — SESSION_RITUALS.md
**Concept:** The bootloader (GRUB, systemd-boot) doesn't do the real work — it specifies exactly what gets loaded, in what order, and hands control to the next stage. Its job is orchestration, not content.

**HumanAIOS Mapping:** `SESSION_RITUALS.md` is the bootloader. It is explicitly "the canonical parser-tag specification" (per its own Authority line) and Section A is a numbered, ordered fetch sequence — precisely a boot menu/load order. It does not contain findings, state, or principles itself (Section H is explicit about this) — it only specifies what loads next and in what order, exactly as a bootloader's job is to load a kernel, not to be the kernel.

**Files Involved:** `SESSION_RITUALS.md`

---

### 4. Boot Parameters / Policy — GOVERNANCE.md + CURRENT.md
**Concept:** Before the kernel proper initializes, the bootloader passes kernel command-line parameters and the firmware enforces a boot policy (e.g., which signing keys are trusted, single-user vs. multi-user target).

**HumanAIOS Mapping:** `GOVERNANCE.md` (the 26-principle ladder, decision rules, anti-cascade limits) and `CURRENT.md` (the operating process fetched at session open, per its own description: "fetched at session open by any LLM... before priorities are declared") are the boot parameters — they set the rules the rest of the boot operates under, before the main payload (REGISTERED.md) loads.

**Files Involved:** `GOVERNANCE.md`, `CURRENT.md`

---

### 5. Kernel Image — REGISTERED.md
**Concept:** The kernel is the large payload the bootloader hands off to — the thing that actually gets loaded into memory and becomes the running system's core state. It must be verified (Secure Boot), it must be current (no stale cached image), and if it can't be loaded safely, the system does not silently boot into a broken state — it drops to a documented recovery mode.

**HumanAIOS Mapping:** `REGISTERED.md` is the kernel image. It is:
- **Live-fetched, not cached** (IC-030) — same as refusing to boot a kernel image left over from a previous, possibly-stale session.
- **Append-only** — a kernel image isn't rewritten in place at boot; new state supersedes old state with a forward pointer (`superseded_by`), never a silent overwrite.
- **The thing whose absence or corruption is a hard halt**, not a soft degradation: SESSION_RITUALS §F.9 (registry-touching halt) is functionally a kernel panic — "the core payload is UNAVAILABLE/UNKNOWN/STALE; stop everything that depends on it and declare DEGRADED mode" rather than continuing on partial/corrupt state.

**Files Involved:** `REGISTERED.md`, `REGISTERED_FAILURE_MODES.md` (the RFM taxonomy is, in this analogy, the kernel's own panic-code registry)

**Failure mode → recovery mode:** DEGRADED mode (SESSION_RITUALS §F.9, CLASS_STATE block) is single-user/rescue-mode boot: the system comes up enough to report what's wrong, but explicitly forbids the normal workload (no F/IC/H proposals against unverified state) until the kernel image is re-verified.

---

### 6. Device / Node Enumeration — ZONE_REGISTRY.md
**Concept:** Once the kernel is running, it enumerates the hardware/devices it has to work with (device tree, PCI bus scan) before anything can be scheduled onto them.

**HumanAIOS Mapping:** `ZONE_REGISTRY.md` enumerates the 31 repos as nodes, each with a Z1/Z2/Z3 assignment — the device table the rest of the session's work is scheduled against. Its own enforcement line ("CI gate validates every PR against this registry. Zone misalignment = merge block") is exactly a device driver refusing to bind a resource to a device that isn't enumerated.

**Files Involved:** `ZONE_REGISTRY.md`, `PLANNED_REPOS.md` (devices not yet attached — roadmap, read-only)

---

### 7. Init / Unit Ordering — PRIORITY_QUEUE.md
**Concept:** PID 1 (init/systemd) brings up services in dependency order once devices are enumerated — some units block others, some run in parallel, failures are reported without necessarily halting the whole boot.

**HumanAIOS Mapping:** `PRIORITY_QUEUE.md` is the ordered unit list — ranked, Z2-ratified, with explicit blocked-row semantics (a GAP callout is the equivalent of a systemd unit reporting `failed` with a dependency reason instead of silently vanishing).

**Files Involved:** `PRIORITY_QUEUE.md`

---

### 8. Kernel Permission Model — CLAUDE.md
**Concept:** The kernel enforces a permission/capability model (ring 0 vs. userspace, syscall gating, SELinux/AppArmor policy) loaded at boot and enforced for the life of the running system.

**HumanAIOS Mapping:** `CLAUDE.md` (this file) — the Z1/Z2/Z3 authority structure is loaded once at boot and gates every subsequent action for the session's lifetime: Z1 cannot execute (no write syscall to REGISTERED.md without a Z2-signed capability token, i.e. the ratification hash), Z3 cannot execute without that same token, Z2 alone can sign it. CODEOWNERS is the concrete ACL enforcing this at the filesystem layer.

**Files Involved:** `CLAUDE.md`, `.github/CODEOWNERS`

---

### 9. Boot Log — Drift Catalog + Phase 1 Declaration
**Concept:** `dmesg` / the boot log is the running system's first self-report — what it detected, what it expects might go wrong, emitted before it hands control to a user.

**HumanAIOS Mapping:** SESSION_RITUALS §A.5-6 — the drift catalog (3-8 predicted failure modes, tagged `[C-NN]` etc.) and the Phase 1 declaration block (`<<<ACAT_P1_DECLARATION_START>>>`) are exactly this: a structured, parseable self-report emitted after the kernel (REGISTERED.md) and devices (ZONE_REGISTRY.md) are loaded but before the system accepts work.

**Files Involved:** SESSION_RITUALS §C (parser tags)

---

### 10. Login Prompt — Wait for Confirmation
**Concept:** A booted system does not begin running arbitrary user workloads until someone authenticates at the login prompt — the boot chain is complete, but execution is gated on an explicit human go-ahead.

**HumanAIOS Mapping:** SESSION_RITUALS §A.7 — "Wait for user confirmation or correction. Do not begin work until the declared state is acknowledged or corrected." This is the login prompt. The corrected state becomes binding for session close (§B.1) the same way an authenticated session's environment is fixed at login.

---

### 11. Runtime Tuning — Molt Cycle
**Concept:** Once a system is running, some parameters can still be changed at runtime (`sysctl`) — but changed carefully, with limits on how many can be in flight, and a policy for what happens when a change misbehaves (rollback).

**HumanAIOS Mapping:** `molt_cycle.py` + `MOLT_STATE.md` + `constants.json` — molts are post-boot runtime tuning of constants, gated by the same anti-cascade rules a careful ops team would apply to live `sysctl` changes: one open change per constant, K=3 system-wide cap, freeze after two consecutive reverts.

**Files Involved:** `molt_cycle.py`, `MOLT_STATE.md`, `constants.json`, `constants_registry.py`

---

### 12. Shutdown / Sync — Session Close
**Concept:** A clean shutdown flushes dirty buffers to disk, unmounts filesystems, and confirms writes landed *before* power-off — writing a shutdown log without verifying the sync happened is how filesystems get corrupted.

**HumanAIOS Mapping:** SESSION_RITUALS §B — B.0 (Empirical Verification Block) is the `sync` + `fsck` that must run *before* any close artifact (receipt, WGS post) is drafted; B.6 (Receipt Reconciliation) is the requirement that the shutdown log match what was actually flushed, not what the system merely believed was written. §F.7-8 make this a hard gate: drafting a close artifact before B.0 runs, or one that asserts content B.0 doesn't confirm, are both halt conditions — the equivalent of refusing to power off on an unclean unmount.

**Files Involved:** SESSION_RITUALS §B, §F

---

### 13. Journal — NF_LEDGER.jsonl
**Concept:** An immutable, hash-chained journal (systemd-journald with sealing, or a write-ahead log) records what happened across boots — appended, never rewritten, checkable after the fact.

**HumanAIOS Mapping:** `NF_LEDGER.jsonl` — append-only, hash-chain validated by CI, the durable record spanning every boot (session) of the system.

**Files Involved:** `NF_LEDGER.jsonl`

---

## Integration Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ POWER ON                                                          │
│  POST → haioscc /api/state/operational, /api/state/zone3          │
│  fail → HALT, report (no bootloader stage reached)                │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ FIRMWARE / SECURE BOOT                                             │
│  git fetch && pin SHA · verify REGISTERED.md / ZONE_REGISTRY.md    │
│  sha256 against manifest (IC-030)                                  │
│  fail → HALT, do not trust unverified payload                      │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ BOOTLOADER — SESSION_RITUALS.md §A                                 │
│  loads, in order: CURRENT.md → GOVERNANCE.md → REGISTERED.md       │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ KERNEL — REGISTERED.md (pinned, live-fetched, append-only)         │
│  loaded OK → continue          loaded BAD/STALE/UNKNOWN → PANIC    │
│                                  → DEGRADED mode (§F.9)             │
│                                  → no F/IC/H work until re-verified │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ DEVICE ENUMERATION — ZONE_REGISTRY.md (31 repos as nodes)          │
│ INIT / UNITS      — PRIORITY_QUEUE.md (ranked, blockers = GAP)     │
│ PERMISSION MODEL  — CLAUDE.md + CODEOWNERS (Z1/Z2/Z3 caps)         │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ BOOT LOG — drift catalog + Phase 1 declaration (§A.5-6)            │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ LOGIN PROMPT — wait for user confirmation (§A.7)                   │
│  system is up; workload does not start until acknowledged          │
└───────────────────────────┬──────────────────────────────────────┘
                             │
                      [ SESSION WORK RUNS ]
                 (molts = runtime sysctl tuning,
                  anti-cascade = change-rate limiter)
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ SHUTDOWN — SESSION_RITUALS.md §B                                   │
│  B.0 sync/verify → B.6 reconcile → journal (NF_LEDGER.jsonl)       │
│  unclean unmount (assert before verify) → HALT (§F.7-8)            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failure-Mode Crosswalk

| Boot-chain failure | HumanAIOS equivalent | Where it's specified |
|:---|:---|:---|
| POST failure (no power/memory) | Live-state fetch fails | SESSION_RITUALS §A.1 |
| Secure Boot signature mismatch | REGISTERED.md hash doesn't match pinned SHA | IC-030, CLAUDE.md §A.5 |
| Kernel panic | Registry-touching halt (UNAVAILABLE/UNKNOWN/STALE) | SESSION_RITUALS §F.9 |
| Boot into single-user/rescue mode | DEGRADED mode, CLASS_STATE block | IC-029, SESSION_RITUALS §F |
| Device not enumerated, driver refuses bind | Zone misalignment → CI merge block | ZONE_REGISTRY.md |
| Unit failed, dependency unmet | Blocked Priority Queue row, no unblock action | GAP callout |
| Unclean shutdown / unsynced write | Close artifact drafted before B.0, or contradicting B.0 | SESSION_RITUALS §F.7-8 |
| Runaway sysctl change | Molt exceeding K=3 cap, or reverted twice | Anti-cascade rules 3-4 |

---

## Action Items for Z2 Ratification

- [ ] Ratify this mapping as reference architecture (companion to FRAMEWORK_MAPPING.md)
- [ ] Link BOOT_PROCESS_MAP.md in CLAUDE.md "How to Use This Document" section
- [ ] Cross-reference from SESSION_RITUALS.md §A header (optional — not required for ratification)
- [ ] Append RATIFY event with Z2 hash

---

## Appendix: Quick Reference

| Boot Stage | File | Load-bearing property |
|:---|:---|:---|
| Firmware / Secure Boot | git SHA pin + manifest sha256 | Integrity before trust |
| Bootloader | SESSION_RITUALS.md | Orchestration, not content |
| Boot parameters | GOVERNANCE.md, CURRENT.md | Policy before payload |
| Kernel image | REGISTERED.md | Live-fetched, append-only, halts on staleness |
| Device enumeration | ZONE_REGISTRY.md | 31 repos as nodes |
| Init/unit order | PRIORITY_QUEUE.md | Ranked, blockers surfaced |
| Permission model | CLAUDE.md + CODEOWNERS | Z1/Z2/Z3 caps |
| Boot log | Drift catalog + Phase 1 block | Structured self-report |
| Login prompt | §A.7 confirmation wait | Work gated on acknowledgment |
| Runtime tuning | molt_cycle.py, MOLT_STATE.md | Rate-limited live changes |
| Shutdown/sync | §B (B.0, B.6) | Verify before asserting |
| Journal | NF_LEDGER.jsonl | Append-only, hash-chained |

---

**Generated by:** Claude (Z1 Proposer)
**For ratification by:** Night/Admiral (Z2 Ratifier)
**For execution by:** Z3 Executors (per ZONE_REGISTRY.md)

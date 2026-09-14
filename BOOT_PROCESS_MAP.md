# HumanAIOS Boot Process Map
## REGISTERED.md's Position in the Session Boot Chain

**Source:** SESSION_RITUALS.md §A (Session open) / §B (Session close), CLAUDE.md §A/§B, GOVERNANCE.md, ZONE_REGISTRY.md
**Mapping Date:** 2026-09-14
**Authority:** Z2 (Night) ratification pending
**Status:** Z1 candidate for REGISTERED.md

---

## Why this mapping

SESSION_RITUALS.md §A already specifies a strict, ordered, halt-on-failure
sequence for every session open (live-state fetch, environment classification,
governance-version fetch, session-rituals fetch, and — for registry-touching
sessions specifically — REGISTERED.md fetch). That sequence *is* a boot chain
— it has the same shape as a computer bringing itself from power-on to a
login prompt: firmware integrity checks before trusting a payload, a loader
that hands off to a larger image, device/service enumeration, and a
documented halt behavior instead of continuing on unverified state. This
document names each stage explicitly so REGISTERED.md's role — and its
IC-029/IC-030 halt conditions, which apply specifically to registry-touching
sessions, not every session — has the same precision as the rest of the
chain. It uses the same paired-mapping + diagram format as
FRAMEWORK_MAPPING.md.

**Scope note:** every session runs §A Steps 1-7 (live state, environment
classification, governance/session-rituals fetch, drift catalog, declaration,
confirmation wait). Only a *registry-touching session* — one that proposes,
modifies, or acts against F/IC/H/NM-class entries — additionally fetches and
pins REGISTERED.md (§A Step 4) and is subject to the §F.9 halt if that fetch
fails or returns UNAVAILABLE/UNKNOWN/STALE state. The "kernel image" stage
below (REGISTERED.md) is conditional on that distinction; everything else in
this map applies session-wide.

---

## Executive Summary

| Boot Chain Stage | HumanAIOS Equivalent | Governing File(s) | On Failure |
|:---|:---|:---|:---|
| **POST** (power-on self-test) | Fetch live operational state | `haioscc.pages.dev/api/state/*` | Halt, report (SESSION_RITUALS §A.1) |
| **Firmware / Secure Boot** | Pin commit SHA; independently verify file content hashes against manifest | `git fetch` (commit pin) + sha256 manifest check (content pin) | Halt — do not trust an unverified payload |
| **Bootloader / boot spec** | Session-open ritual specification | `SESSION_RITUALS.md` (parser-tag authority) + `CURRENT.md`/`GOVERNANCE.md`/`OPERATOR_RUNBOOK.md` (orchestration detail, per SESSION_RITUALS §61/§H) | Fetch fails → halt, report |
| **Boot parameters / policy** | Load standing principles + operating process | `GOVERNANCE.md`, `CURRENT.md` | Proceed on last-known if fetch fails is NOT allowed — halt |
| **Kernel image** *(registry-touching sessions only)* | Load registered findings/context | `REGISTERED.md` (pinned SHA, live-fetch) | DEGRADED mode (SESSION_RITUALS §F.9, IC-029/IC-030) |
| **Device/node enumeration** | Enumerate active zones/repos | `ZONE_REGISTRY.md` | Zone misalignment = merge block |
| **Init / unit ordering** | Ranked work queue | `PRIORITY_QUEUE.md` | Blocked row without unblock action → GAP callout |
| **Kernel permission model** | Authority tiers (Z1/Z2/Z3) | `CLAUDE.md` (review-gated by `.github/CODEOWNERS` + branch protection) | Action outside cap → escalate to Z2 |
| **Boot log / dmesg** | Drift catalog + Phase 1 declaration | SESSION_RITUALS §A.5-6 | — |
| **Login prompt** | Wait for user confirmation | SESSION_RITUALS §A.7 | Work does not begin until acknowledged |
| **Runtime tuning (sysctl)** | Molt cycle, constants | `molt_cycle.py`, `constants.json`, `MOLT_STATE.md` | Anti-cascade freeze (K=3, revert-twice rule) |
| **Shutdown / close ritual** | Session close | SESSION_RITUALS §B | B.0 hard gate before any close artifact |
| **Journal (append-only log)** | Hash-chained ledger | `ledgers/NF_LEDGER.jsonl` | Hash-chain verifiable via `tools/nf_ledger_cli_v1_0.py` |

---

## Detailed Mapping

### 1. POST — Power-On Self-Test
**Concept:** Before anything else, hardware checks that the machine is even capable of booting — power rails, memory, attached devices. A POST failure halts before the bootloader ever runs.

**HumanAIOS Mapping:** SESSION_RITUALS §A Step 1 — `GET /api/state/operational` and `GET /api/state/zone3?status=open`. This is the "is the operational substrate alive" check. If either fetch fails, the session halts and reports — exactly a POST failure, before any protocol file is even read.

**Files Involved:** `haioscc.pages.dev/api/state/operational`, `haioscc.pages.dev/api/state/zone3`

---

### 2. Firmware / Secure Boot — Integrity Verification
**Concept:** Firmware (BIOS/UEFI) verifies the signature of what it is about to load before handing off control. Secure Boot refuses to chain-load an image whose signature doesn't match — that's the whole point: don't trust content merely because it's present.

**HumanAIOS Mapping:** This is two distinct checks, not one — the same way Secure Boot separates "is this the revision I asked for" from "does its content hash match what I expect":
1. `git fetch && git rev-parse HEAD` pins the *commit* — which revision is being read.
2. CLAUDE.md §A step 5 separately verifies REGISTERED.md's (and ZONE_REGISTRY.md's) *content* sha256 against a manifest — that the file at that pinned revision is the one expected.

**IC-030** ("live-fetch, pin SHA") is the secure-boot policy statement covering both: "do not boot from a payload you have not freshly fetched and verified," not "trust whatever is cached from a prior session."

**Files Involved:** `.git` (commit pin), sha256 manifest (per CLAUDE.md §A.5)

**Failure mode:** Fetch failure, or a manifest mismatch, → registry-touching halt (SESSION_RITUALS §F.9) for registry-touching sessions — same posture as Secure Boot refusing an unsigned or altered kernel.

---

### 3. Bootloader / Boot Spec — SESSION_RITUALS.md + orchestration surfaces
**Concept:** The bootloader (GRUB, systemd-boot) doesn't do the real work — it specifies exactly what gets loaded, in what order, and hands control to the next stage. Its job is orchestration, not content.

**HumanAIOS Mapping:** `SESSION_RITUALS.md` is explicitly "the canonical parser-tag specification" (per its own Authority line) — it names the ordered step list and the tag formats, the way a boot config declares the load order. But SESSION_RITUALS.md says this about itself, in its own words: "the orchestration of these steps — including drift catalog detail, the canonical-fetch order, and what each substrate should output between fetches — lives in the active session protocol surfaces: `CURRENT.md`, `GOVERNANCE.md`, and `OPERATOR_RUNBOOK.md`. This file specifies the parser tags only" (§A closing note, §H). So the bootloader role is shared: SESSION_RITUALS.md is the boot spec/parser-tag contract, while CURRENT.md/GOVERNANCE.md/OPERATOR_RUNBOOK.md carry the actual execution detail — closer to a boot-config file plus the scripts it invokes than to a single self-contained loader binary.

**Files Involved:** `SESSION_RITUALS.md`, `CURRENT.md`, `GOVERNANCE.md`, `OPERATOR_RUNBOOK.md`

---

### 4. Boot Parameters / Policy — GOVERNANCE.md + CURRENT.md
**Concept:** Before the kernel proper initializes, the bootloader passes kernel command-line parameters and the firmware enforces a boot policy (e.g., which signing keys are trusted, single-user vs. multi-user target).

**HumanAIOS Mapping:** `GOVERNANCE.md` (the standing principle ladder — currently 32 P-numbers per its own version history; see GOVERNANCE.md's changelog for the live count rather than treating any fixed number as canonical here — plus decision rules and anti-cascade limits) and `CURRENT.md` (the operating process fetched at session open, per its own description: "fetched at session open by any LLM... before priorities are declared") are the boot parameters — they set the rules the rest of the boot operates under, before the main payload (REGISTERED.md, for registry-touching sessions) loads.

**Files Involved:** `GOVERNANCE.md`, `CURRENT.md`

---

### 5. Kernel Image — REGISTERED.md *(registry-touching sessions)*
**Concept:** The kernel is the large payload the bootloader hands off to — the thing that actually gets loaded into memory and becomes the running system's core state. It must be verified (Secure Boot), it must be current (no stale cached image), and if it can't be loaded safely, the system does not silently boot into a broken state — it drops to a documented recovery mode.

**HumanAIOS Mapping:** `REGISTERED.md` is the kernel image for registry-touching sessions. It is:
- **Live-fetched, not cached** (IC-030) — same as refusing to boot a kernel image left over from a previous, possibly-stale session.
- **Append-only** — a kernel image isn't rewritten in place at boot; new state supersedes old state with a forward pointer (`superseded_by`), never a silent overwrite.
- **The thing whose failed fetch or UNAVAILABLE/UNKNOWN/STALE state is a hard halt** for the sessions that depend on it: SESSION_RITUALS §F.9 scopes this specifically to registry-touching sessions with a failed fetch or a degraded class state — it is functionally a kernel panic for that workload class, not an unconditional halt for every session — "stop everything that depends on this payload and declare DEGRADED mode" rather than continuing on partial/corrupt state.

**Files Involved:** `REGISTERED.md`, `REGISTERED_FAILURE_MODES.md` (the RFM taxonomy is, in this analogy, the kernel's own panic-code registry)

**Failure mode → recovery mode:** DEGRADED mode (SESSION_RITUALS §F.9, CLASS_STATE block, IC-029) is single-user/rescue-mode boot: the system comes up enough to report what's wrong, but explicitly forbids the normal registry-touching workload (no F/IC/H proposals against unverified state) until the kernel image is re-verified.

---

### 6. Device / Node Enumeration — ZONE_REGISTRY.md
**Concept:** Once the kernel is running, it enumerates the hardware/devices it has to work with (device tree, PCI bus scan) before anything can be scheduled onto them.

**HumanAIOS Mapping:** `ZONE_REGISTRY.md` enumerates the active repos as nodes (12 per its current "Repository Zone Assignments" table — read the live table rather than treating any number here as fixed, since PLANNED_REPOS.md tracks additional repos not yet attached), each with a Z1/Z2/Z3 assignment — the device table the rest of the session's work is scheduled against. Its own enforcement line ("CI gate validates every PR against this registry. Zone misalignment = merge block") is exactly a device driver refusing to bind a resource to a device that isn't enumerated.

**Files Involved:** `ZONE_REGISTRY.md`, `PLANNED_REPOS.md` (devices not yet attached — roadmap, read-only)

---

### 7. Init / Unit Ordering — PRIORITY_QUEUE.md
**Concept:** PID 1 (init/systemd) brings up services in dependency order once devices are enumerated — some units block others, some run in parallel, failures are reported without necessarily halting the whole boot.

**HumanAIOS Mapping:** `PRIORITY_QUEUE.md` is the ordered unit list — ranked by Z2-ratified scores, with explicit blocked-row semantics (a GAP callout is the equivalent of a systemd unit reporting `failed` with a dependency reason instead of silently vanishing). Where a specific row's own ratification hash is still pending, that mirrors a unit whose dependency is declared but not yet satisfied — ranked and queued, not yet cleared to start.

**Files Involved:** `PRIORITY_QUEUE.md`

---

### 8. Kernel Permission Model — CLAUDE.md + CODEOWNERS
**Concept:** The kernel enforces a permission/capability model (ring 0 vs. userspace, syscall gating, SELinux/AppArmor policy) loaded at boot and enforced for the life of the running system.

**HumanAIOS Mapping:** `CLAUDE.md` (this file) — the Z1/Z2/Z3 authority structure is loaded once at boot and gates every subsequent action for the session's lifetime: Z1 cannot execute (no write to REGISTERED.md without a Z2-signed capability token, i.e. the ratification hash), Z3 cannot execute without that same token, Z2 alone can sign it. `.github/CODEOWNERS` is the review-gating layer for this permission model — not a filesystem ACL: by the file's own header, it currently enforces nothing on its own ("CODEOWNERS alone enforces nothing: branch protection must also have 'Require review from Code Owners' enabled") and documents itself as a self-review placeholder pending a second independent reviewer. That's a real gap in the analogy worth carrying forward as-is rather than smoothing over: the permission *model* is specified, but one of its enforcement mechanisms is explicitly not yet independent.

**Files Involved:** `CLAUDE.md`, `.github/CODEOWNERS`

---

### 9. Boot Log — Drift Catalog + Phase 1 Declaration
**Concept:** `dmesg` / the boot log is the running system's first self-report — what it detected, what it expects might go wrong, emitted before it hands control to a user.

**HumanAIOS Mapping:** SESSION_RITUALS §A.5-6 — the drift catalog (3-8 predicted failure modes, tagged `[C-NN]` etc.) and the Phase 1 declaration block (`<<<ACAT_P1_DECLARATION_START>>>`) are exactly this: a structured, parseable self-report emitted after the governing files are loaded (and, for registry-touching sessions, after REGISTERED.md and ZONE_REGISTRY.md) but before the system accepts work.

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

### 12. Shutdown / Close Ritual — Session Close
**Concept:** A clean shutdown verifies pending state before it is acted on and before any summary of "what happened" is produced or logged — writing a shutdown log without checking what actually happened first is how records drift from reality.

**HumanAIOS Mapping:** SESSION_RITUALS §B is *analogous* to a clean shutdown, not a literal one — it does not perform filesystem operations, so read the mapping below as structural, not mechanical:
- **B.0 (Empirical Verification Block)** is the mandatory pre-check that must run *before* any close artifact (receipt, WGS post) is drafted — the structural role a `sync`/verification step plays before shutdown, except what it verifies is literal command output (`git status --short`, `git diff --cached --name-only`, etc.), not disk buffers.
- **B.6 (Receipt Reconciliation)** is the requirement that the close artifact match what B.0 actually confirmed, walking back any earlier draft claim B.0 contradicts — the structural role of checking a shutdown log against what was actually flushed, except what's being reconciled is asserted content against verification-block output, not writes against a filesystem.
- §F.7-8 make this a hard gate either way: drafting a close artifact before B.0 runs, or one that asserts content B.0 doesn't confirm, are both halt conditions.

**Files Involved:** SESSION_RITUALS §B, §F

---

### 13. Journal — ledgers/NF_LEDGER.jsonl
**Concept:** An immutable, hash-chained journal (systemd-journald with sealing, or a write-ahead log) records what happened across boots — appended, never rewritten, checkable after the fact.

**HumanAIOS Mapping:** `ledgers/NF_LEDGER.jsonl` — append-only, hash-chained, the durable record spanning every boot (session) of the system. Its chain is checkable via `tools/nf_ledger_cli_v1_0.py` (`verify_chain`) / `tools/nf_ledger_v0_1.py` (`verify`). Note the current CI (`quality-baseline.yml`, `test_nf_ledger_cli.py`) exercises the verification *tool's* logic on test fixtures; it is not, as of this writing, a workflow step that re-verifies the live `ledgers/NF_LEDGER.jsonl` file's chain on every PR. Treat "hash-chain validated" as "hash-chain verifiable on demand," not "continuously re-checked by CI," until a gate does that directly.

**Files Involved:** `ledgers/NF_LEDGER.jsonl`, `tools/nf_ledger_cli_v1_0.py`, `tools/nf_ledger_v0_1.py`

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
│  git fetch && pin commit SHA (revision) · sha256 vs. manifest      │
│  (content) for REGISTERED.md / ZONE_REGISTRY.md — two checks       │
│  fail → HALT, do not trust unverified payload                      │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ BOOTLOADER / BOOT SPEC — SESSION_RITUALS.md §A (full step list:    │
│  live state → env classification → governance version →           │
│  session rituals → REGISTERED.md if registry-touching → drift      │
│  catalog → declaration → confirmation wait). Execution detail      │
│  distributed across CURRENT.md / GOVERNANCE.md / OPERATOR_RUNBOOK  │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ KERNEL (registry-touching sessions only) —                         │
│  REGISTERED.md (pinned, live-fetched, append-only)                 │
│  loaded OK → continue     fetch failed / BAD/STALE/UNKNOWN →       │
│                             PANIC → DEGRADED mode (§F.9, IC-029)   │
│                             → no F/IC/H work until re-verified     │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ DEVICE ENUMERATION — ZONE_REGISTRY.md (12 active repos as nodes,   │
│                        per its current table)                      │
│ INIT / UNITS      — PRIORITY_QUEUE.md (ranked, blockers = GAP)     │
│ PERMISSION MODEL  — CLAUDE.md + CODEOWNERS (review-gated, not a    │
│                        filesystem ACL; Z1/Z2/Z3 caps)              │
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
│ CLOSE RITUAL — SESSION_RITUALS.md §B (analogy, not literal I/O)    │
│  B.0 verify command output → B.6 reconcile receipt against it →    │
│  journal (ledgers/NF_LEDGER.jsonl)                                  │
│  close artifact drafted before B.0, or contradicting it → HALT     │
│  (§F.7-8)                                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failure-Mode Crosswalk

| Boot-chain failure | HumanAIOS equivalent | Where it's specified |
|:---|:---|:---|
| POST failure (no power/memory) | Live-state fetch fails | SESSION_RITUALS §A.1 |
| Secure Boot signature mismatch | REGISTERED.md content sha256 doesn't match manifest, or the pinned commit can't be fetched | IC-030, CLAUDE.md §A.5 |
| Kernel panic | Registry-touching halt (fetch failed, or UNAVAILABLE/UNKNOWN/STALE) | SESSION_RITUALS §F.9 |
| Boot into single-user/rescue mode | DEGRADED mode, CLASS_STATE block | IC-029, SESSION_RITUALS §F |
| Device not enumerated, driver refuses bind | Zone misalignment → CI merge block | ZONE_REGISTRY.md |
| Unit failed, dependency unmet | Blocked Priority Queue row, no unblock action | GAP callout |
| Close artifact drafted before verification, or contradicting it | Close artifact drafted before B.0, or asserting content B.0 doesn't confirm | SESSION_RITUALS §F.7-8 |
| Runaway sysctl change | Molt exceeding K=3 cap, or reverted twice | Anti-cascade rules 3-4 |

---

## Action Items for Z2 Ratification

- [ ] Ratify this mapping as reference architecture (companion to FRAMEWORK_MAPPING.md)
- [x] Link BOOT_PROCESS_MAP.md in CLAUDE.md "How to Use This Document" section — done in this PR (see "Boot Process Reference")
- [ ] Cross-reference from SESSION_RITUALS.md §A header (optional — not required for ratification)
- [ ] Attach `calibration_ref` per GOVERNANCE.md P30 (interactive `acat_document_analyzer_v1.1` pass) — required before Z2 ratification of this substantive written artifact; not run in this session
- [ ] Append RATIFY event with Z2 hash

---

## Appendix: Quick Reference

| Boot Stage | File | Load-bearing property |
|:---|:---|:---|
| Firmware / Secure Boot | git commit pin + manifest sha256 (two checks) | Integrity before trust |
| Bootloader / boot spec | SESSION_RITUALS.md (+ CURRENT.md/GOVERNANCE.md/OPERATOR_RUNBOOK.md) | Spec + distributed orchestration, not content |
| Boot parameters | GOVERNANCE.md, CURRENT.md | Policy before payload |
| Kernel image *(registry-touching sessions)* | REGISTERED.md | Live-fetched, append-only, halts on failed fetch/staleness |
| Device enumeration | ZONE_REGISTRY.md | 12 active repos as nodes (live count — see file) |
| Init/unit order | PRIORITY_QUEUE.md | Ranked, blockers surfaced |
| Permission model | CLAUDE.md + CODEOWNERS (review-gated, not filesystem-enforced) | Z1/Z2/Z3 caps |
| Boot log | Drift catalog + Phase 1 block | Structured self-report |
| Login prompt | §A.7 confirmation wait | Work gated on acknowledgment |
| Runtime tuning | molt_cycle.py, MOLT_STATE.md | Rate-limited live changes |
| Close ritual | §B (B.0, B.6) | Verify before asserting (analogy, not literal I/O) |
| Journal | `ledgers/NF_LEDGER.jsonl` | Append-only, hash-chain verifiable on demand |

---

**Generated by:** Claude (Z1 Proposer)
**For ratification by:** Night/Admiral (Z2 Ratifier)
**For execution by:** N/A — documentation/reference-architecture only; no Z3 execution required beyond the CLAUDE.md link already included in this PR

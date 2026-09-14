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

**Scope note:** every session runs §A Steps 1-7 (live state, `CURRENT.md`,
environment classification, governance/session-rituals fetch, drift catalog,
declaration, confirmation wait). SESSION_RITUALS.md §A Step 4 conditions the
REGISTERED.md fetch on the session being *registry-touching* — one that
proposes, modifies, or acts against F/IC/H/NM-class entries — and the §F.9
halt applies to that same condition. **Open conflict, not resolved by this
document:** CLAUDE.md's own §A ("Session Rituals") lists "Read REGISTERED.md
at that SHA" as step 2 of what it calls "Mandatory before any work" —
unconditional, no registry-touching qualifier. SESSION_RITUALS.md and
CLAUDE.md disagree on whether every session or only a registry-touching one
must fetch REGISTERED.md. This document follows SESSION_RITUALS.md's
narrower, explicitly-conditioned wording throughout — it is the more detailed
and specifically-scoped source on this exact point, and names its own IC-030
hardening rationale for the condition — but that is this document's editorial
choice, not a settled ratification; CLAUDE.md's overall file is dated more
recently (2026-09-14) than SESSION_RITUALS.md (v6.4.1, May 19), so recency
alone does not favor either reading. Z2 should treat the CLAUDE.md/SESSION_RITUALS.md
disagreement itself as a candidate AMBIGUITY callout independent of whether
this mapping is ratified. The "kernel image" stage below (REGISTERED.md) is
conditional under the SESSION_RITUALS.md reading; everything else in this map
applies session-wide under both readings.

---

## Executive Summary

| Boot Chain Stage | HumanAIOS Equivalent | Governing File(s) | On Failure |
|:---|:---|:---|:---|
| **POST** (power-on self-test) | Fetch live operational state | Primary: WGS #wgs-sync via Slack MCP (per CURRENT.md, Class 1). Secondary/cross-check named in SESSION_RITUALS §A.1's literal text: `haioscc.pages.dev/api/state/*` — CURRENT.md notes this endpoint is unreachable from Claude's bash environment and is demoted to secondary for Claude sessions specifically | Slack MCP unavailable → **PATH C (degraded)**, proceed from CURRENT.md only (OPERATOR_RUNBOOK.md) — not a blanket halt |
| **Firmware / Secure Boot** | Pin commit SHA (demonstrated); content-hash-vs-manifest check (specified; a dated single-drop manifest exists as precedent, but no current one covering REGISTERED.md+ZONE_REGISTRY.md was located) | `git fetch && git rev-parse HEAD` (commit pin) + sha256-vs-manifest per CLAUDE.md §A.5 | Commit-fetch failure → halt; manifest mismatch has no dedicated branch, generic §F.1 "stop and ask" plausibly applies |
| **Bootloader / boot spec** | Session-open ritual specification | `SESSION_RITUALS.md` (parser-tag authority) + `CURRENT.md`/`GOVERNANCE.md`/`OPERATOR_RUNBOOK.md` (orchestration detail, per SESSION_RITUALS.md's own §A closing note and §H) | Fetch fails → halt, report |
| **Boot parameters / policy** | Load standing principles + operating process | `GOVERNANCE.md`, `CURRENT.md` | Proceed on last-known if fetch fails is NOT allowed — halt |
| **Kernel image** *(registry-touching sessions per SESSION_RITUALS.md; CLAUDE.md's own §A reads this as unconditional — see "Open conflict" above)* | Load registered findings/context | `REGISTERED.md` (pinned SHA, live-fetch) | DEGRADED mode (SESSION_RITUALS §F.9, IC-029/IC-030) |
| **Device/node enumeration** | Enumerate active zones/repos | `ZONE_REGISTRY.md` | ZONE_REGISTRY.md's own header claims "merge block"; CLAUDE.md lists the `registry_consistency` CI gate as "planned Phase 3" — not yet confirmed live either way in this document |
| **Init / unit ordering** | Ranked work queue | `PRIORITY_QUEUE.md` | Blocked row without unblock action → GAP callout |
| **Kernel permission model** | Authority tiers (Z1/Z2/Z3) — specified in CLAUDE.md; CLAUDE.md's own tables disagree on whether Z1 may write CANDIDATE blocks to REGISTERED.md (see §8 below) | `CLAUDE.md`; `.github/CODEOWNERS` names itself a self-review placeholder, not yet an independent gate | Action outside cap → escalate to Z2 |
| **Boot log / dmesg** | Drift catalog + Phase 1 declaration | SESSION_RITUALS §A.5-6 | — |
| **Login prompt** | Wait for user confirmation | SESSION_RITUALS §A.7 | Work does not begin until acknowledged |
| **Runtime tuning (sysctl)** | Molt cycle, constants | `molt_cycle.py`, `constants.json`, `MOLT_STATE.md` | Anti-cascade freeze (K=3, revert-twice rule) |
| **Shutdown / close ritual** | Session close | SESSION_RITUALS §B | B.0 hard gate before a close artifact that asserts contents (receipt, WGS post, summary, status report) |
| **Journal (append-only log)** | Per-session close record = WGS Slack log (§B.7); `ledgers/NF_LEDGER.jsonl` is a *pattern example* (hash-chained, unrelated subsystem — not written by §B) | WGS `#wgs-sync` (session record); `ledgers/NF_LEDGER.jsonl` (pattern only) | WGS post omitted → next session's Class 1 read is stale (CURRENT.md) |

---

## Detailed Mapping

### 1. POST — Power-On Self-Test
**Concept:** Before anything else, hardware checks that the machine is even capable of booting — power rails, memory, attached devices. A POST failure halts before the bootloader ever runs.

**HumanAIOS Mapping:** SESSION_RITUALS §A Step 1's literal text names `GET /api/state/operational` and `GET /api/state/zone3?status=open`. CURRENT.md's Class 1 entry supersedes this with the actual current source priority for Claude sessions: **primary** is a WGS read via Slack MCP (`slack_read_channel` on `#wgs-sync`, channel `C0AND66PT7U`); the haioscc endpoints are the **secondary cross-check**, noted as "unreachable from Claude's bash environment" for Claude specifically, demoting them further in practice. This stage's failure behavior is *not* a blanket halt: OPERATOR_RUNBOOK.md states that if Slack MCP is unavailable, the session declares **PATH C (degraded)** and proceeds from CURRENT.md only, rather than halting outright — a graceful-degradation path, not a POST failure in the strict sense. The strict POST-failure analogy (halt and report) is closer to what SESSION_RITUALS §A.1's own literal text describes for its named haioscc endpoints; in practice, for Claude sessions, PATH C is the more accurate failure-mode description.

**Files Involved:** `#wgs-sync` (Slack MCP, primary), `haioscc.pages.dev/api/state/operational` + `/api/state/zone3` (secondary/cross-check, largely unreachable for Claude sessions)

---

### 2. Firmware / Secure Boot — Integrity Verification
**Concept:** Firmware (BIOS/UEFI) verifies the signature of what it is about to load before handing off control. Secure Boot refuses to chain-load an image whose signature doesn't match — that's the whole point: don't trust content merely because it's present.

**HumanAIOS Mapping:** This is *specified* as two distinct checks, not one — the same way Secure Boot separates "is this the revision I asked for" from "does its content hash match what I expect":
1. `git fetch && git rev-parse HEAD` pins the *commit* — which revision is being read.
2. CLAUDE.md §A step 5 separately calls for verifying "each file's sha256 against manifest" — content verification at that pinned revision.

**IC-030** ("live-fetch, pin SHA") is the secure-boot policy statement covering the commit-pin half of this: "do not boot from a payload you have not freshly fetched," not "trust whatever is cached from a prior session."

**This document could not locate a current, canonical manifest covering both REGISTERED.md and ZONE_REGISTRY.md, as CLAUDE.md §A.5 implies.** `z1-inbox/2026-09-06/MANIFEST.md` is a real, related artifact — it pins a REGISTERED.md blob hash and instructs "verify sha256 before reading; a mismatch is a loud failure" — but it's a dated, single-drop manifest for one mesh Phase-2 inbox delivery (pinned at `c0899b9b...`, commit `d1fb5f0d2dd9`, 2026-08-16), now roughly four weeks and dozens of commits stale, and it doesn't cover ZONE_REGISTRY.md at all. Calling it "unrelated" (an earlier draft of this document did) overstated the gap; the accurate framing is: a manifest convention exists and has been used, but no current, general-purpose manifest for the specific pair CLAUDE.md §A.5 names was found in this checkout. Read this stage as **specified, with a demonstrated but non-current example, not an active reproducible check as of this document's writing.**

**Files Involved:** `.git` (commit pin); the manifest CLAUDE.md §A.5 requires is not identified in this checkout

**Failure mode:** SESSION_RITUALS §F.9 explicitly covers a failed REGISTERED.md fetch or an UNAVAILABLE/UNKNOWN/STALE class state for registry-touching sessions — that's a dedicated, named branch. A content-hash mismatch has no equivalent dedicated branch, but it is not entirely unaddressed: SESSION_RITUALS §F.1's general halt condition ("a canonical-source fetch fails or returns unexpected data") plausibly covers it as a "stop and ask the user" case, even without F.9's specific automated DEGRADED-mode handling. Treat this as a weaker, generic fallback rather than either "no consequence at all" or "covered by §F.9."

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

**HumanAIOS Mapping:** `ZONE_REGISTRY.md` enumerates the active repos as nodes (12 per its current "Repository Zone Assignments" table — read the live table rather than treating any number here as fixed, since PLANNED_REPOS.md tracks additional repos not yet attached), each with a Z1/Z2/Z3 assignment — the device table the rest of the session's work is scheduled against. Its own enforcement line reads "CI gate validates every PR against this registry. Zone misalignment = merge block" — a device driver refusing to bind a resource to a device that isn't enumerated, *if* that gate is actually wired up. It may not be yet: CLAUDE.md's own governance table lists the `registry_consistency` CI gate as "planned Phase 3," which would make this enforcement aspirational rather than live. This document doesn't resolve which file is current; flagging the discrepancy is more honest than picking a side.

**Files Involved:** `ZONE_REGISTRY.md`, `PLANNED_REPOS.md` (devices not yet attached — roadmap, read-only)

---

### 7. Init / Unit Ordering — PRIORITY_QUEUE.md
**Concept:** PID 1 (init/systemd) brings up services in dependency order once devices are enumerated — some units block others, some run in parallel, failures are reported without necessarily halting the whole boot.

**HumanAIOS Mapping:** `PRIORITY_QUEUE.md` is the ordered unit list — ranked by Z1-proposed scores under a declared formula, with explicit blocked-row semantics (a GAP callout is the equivalent of a systemd unit reporting `failed` with a dependency reason instead of silently vanishing). The queue's own metadata currently shows `ratification_hash: — (pending Z2 signature)` — the scores are declared and ranked, not yet Z2-ratified — which mirrors units that are enumerated and ordered but whose dependency graph hasn't been signed off; the `status_gate: READY` still governs which rows may begin regardless.

**Files Involved:** `PRIORITY_QUEUE.md`

---

### 8. Kernel Permission Model — CLAUDE.md + CODEOWNERS
**Concept:** The kernel enforces a permission/capability model (ring 0 vs. userspace, syscall gating, SELinux/AppArmor policy) loaded at boot and enforced for the life of the running system.

**HumanAIOS Mapping:** `CLAUDE.md` (this file) — the Z1/Z2/Z3 authority structure is loaded once at boot and is meant to gate every subsequent action for the session's lifetime. **CLAUDE.md contradicts itself on exactly how the write/execute boundary works, and this document does not adjudicate that conflict:**
- Its "Governance Files & CI/CD Integration" table lists REGISTERED.md as "Z2 sole write," enforcement "CI: no write without Z2 hash" — reading that as ring-0-only, no unprivileged write syscall at all.
- Its "Z1: Proposers" section lists Z1's rights as including candidate-block proposals, with "Output: Candidate blocks → REGISTERED.md (awaiting Z2 hash)" — reading that as an unprivileged write (append a CANDIDATE) that a separate privileged operation (Z2's hash) later escalates to execution.

This candidate block (`Q-BOOT-PROCESS-MAP-01`, appended with `zone2_ratification: null`) is itself a live instance of the ambiguity, not proof of either reading — the repo's own history includes other Z1-appended CANDIDATE blocks pending Z2 signature, which is consistent with the second reading but doesn't resolve the contradiction against the first. Z2 should treat this as its own AMBIGUITY item.

Independent of that conflict, the escalation half is clearer: neither Z1 nor Z3 can execute or land a *ratified* change (mark it ACCEPTED and act on it) without a Z2-signed capability token, i.e. the ratification hash; Z2 alone can sign it. `.github/CODEOWNERS` is the intended review-gating layer for this permission model — not a filesystem ACL, and not yet independent either: by the file's own header, it currently enforces nothing on its own ("CODEOWNERS alone enforces nothing: branch protection must also have 'Require review from Code Owners' enabled") and documents itself as a self-review placeholder pending a second independent reviewer.

**Files Involved:** `CLAUDE.md`, `.github/CODEOWNERS`

---

### 9. Boot Log — Drift Catalog + Phase 1 Declaration
**Concept:** `dmesg` / the boot log is the running system's first self-report — what it detected, what it expects might go wrong, emitted before it hands control to a user.

**HumanAIOS Mapping:** SESSION_RITUALS §A.5-6 — the drift catalog (3-8 predicted failure modes, tagged `[C-NN]` etc.) and the Phase 1 declaration block (`<<<ACAT_P1_DECLARATION_START>>>`) are exactly this: a structured, parseable self-report emitted after the governing files are loaded but before the system accepts work. Note that ZONE_REGISTRY.md's fetch is not part of SESSION_RITUALS.md §A at all — it's CLAUDE.md §A step 4 — so where this document says "after the governing files are loaded," that spans both files' session-open sequences, not one citation covering both.

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

### 13. Journal — per-session close log vs. NF_LEDGER.jsonl
**Concept:** An immutable, hash-chained journal (systemd-journald with sealing, or a write-ahead log) records what happened across boots — appended, never rewritten, checkable after the fact.

**HumanAIOS Mapping — corrected from an earlier draft of this document:** `ledgers/NF_LEDGER.jsonl` is **not** SESSION_RITUALS.md's session/boot journal — SESSION_RITUALS.md never mentions it (checked: zero occurrences), and §B does not write to it at close. What NF_LEDGER.jsonl actually is, per its own README: an append-only, hash-chained ledger of NF TOKEN/OPEN/PIN/RESOLVE events for a specific mesh/molt prediction-tracking build (`tools/nf_ledger_v0_1.py`), scoped to that subsystem, not a general per-session record.

The record SESSION_RITUALS.md §B actually specifies for "what happened this session" is the **WGS Slack log** — with a caveat SESSION_RITUALS.md states explicitly and this paragraph should too: §B.7 scopes that step to "substrates with Slack write access only — typically Claude"; it is not a universal per-substrate requirement. For substrates with that access, §B.1-8 (Step 7) requires logging to `#wgs-sync` with the Receipt Reconciliation paragraph, and CURRENT.md separately calls the WGS post "a required close ritual" and "the canonical live-state source" for the next session's Class 1 read. That Slack log — not NF_LEDGER.jsonl — is the closer functional analogue of "what gets written at shutdown that the next boot reads back," for the substrates that can write it.

NF_LEDGER.jsonl is still a useful example *elsewhere in the system* of the append-only, hash-chained journal pattern this stage is meant to illustrate — its chain is checkable via `tools/nf_ledger_cli_v1_0.py` (`verify_chain`) / `tools/nf_ledger_v0_1.py` (`verify`), and current CI (`quality-baseline.yml`, `test_nf_ledger_cli.py`) exercises the verification tool's logic on test fixtures rather than re-verifying the live file's chain on every PR — but it should be read as an illustration of the pattern, not as the thing SESSION_RITUALS.md's close ritual writes to.

**Files Involved:** WGS `#wgs-sync` Slack channel (the actual per-session close record); `ledgers/NF_LEDGER.jsonl`, `tools/nf_ledger_cli_v1_0.py`, `tools/nf_ledger_v0_1.py` (pattern example, separate subsystem)

---

## Integration Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│ POWER ON                                                          │
│  POST → live state: WGS #wgs-sync (primary, Slack MCP) ·          │
│         haioscc /api/state/* (secondary — largely unreachable      │
│         from Claude's bash env per CURRENT.md)                     │
│  Slack MCP down → PATH C (degraded): proceed from CURRENT.md      │
│  only (OPERATOR_RUNBOOK.md) — not a blanket halt                   │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ FIRMWARE / SECURE BOOT                                             │
│  git fetch && rev-parse HEAD → commit pin (fail → HALT)            │
│  sha256 vs. manifest (content, per CLAUDE.md §A.5) — no current    │
│  manifest located for this file pair; mismatch has no dedicated    │
│  branch, generic §F.1 "stop and ask" plausibly applies             │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ BOOTLOADER / BOOT SPEC — SESSION_RITUALS.md §A (full step list:    │
│  1 live state → 2 CURRENT.md → 2.5 env classification →           │
│  2.6 governance version → 3 session rituals →                     │
│  4 REGISTERED.md (registry-touching per SESSION_RITUALS.md; see   │
│    "Open conflict" note — CLAUDE.md's own §A reads this as        │
│    unconditional) → 5 drift catalog → 6 declaration →             │
│  7 confirmation wait. Execution detail distributed across          │
│  CURRENT.md / GOVERNANCE.md / OPERATOR_RUNBOOK.md                  │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ KERNEL (registry-touching sessions only) —                         │
│  REGISTERED.md (pinned, live-fetched, append-only)                 │
│  loaded OK → continue     fetch failed / UNAVAILABLE/UNKNOWN/      │
│                            STALE → PANIC → DEGRADED mode           │
│                            (§F.9, IC-029)                          │
│                             → no F/IC/H work until re-verified     │
└───────────────────────────┬──────────────────────────────────────┘
                             │
┌───────────────────────────▼──────────────────────────────────────┐
│ (order below follows CLAUDE.md §A: step 3 PRIORITY_QUEUE.md before  │
│  step 4 ZONE_REGISTRY.md)                                           │
│ INIT / UNITS      — PRIORITY_QUEUE.md (ranked, Z2 hash pending,    │
│                        blockers = GAP)                              │
│ DEVICE ENUMERATION — ZONE_REGISTRY.md (12 active repos as nodes,   │
│                        per its current table; merge-block          │
│                        enforcement claimed live by ZONE_REGISTRY,   │
│                        listed "planned Phase 3" by CLAUDE.md —     │
│                        unresolved conflict, not adjudicated here)  │
│ PERMISSION MODEL  — CLAUDE.md + CODEOWNERS (specified, not yet     │
│                        independently enforced; Z1/Z2/Z3 caps —     │
│                        CLAUDE.md's own tables disagree on Z1's     │
│                        REGISTERED.md write right, see §8)          │
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
│  journal = WGS #wgs-sync post (§B.7; NF_LEDGER.jsonl is an         │
│  unrelated subsystem's pattern example, not written here)          │
│  close artifact drafted before B.0, or contradicting it → HALT     │
│  (§F.7-8)                                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Failure-Mode Crosswalk

| Boot-chain failure | HumanAIOS equivalent | Where it's specified |
|:---|:---|:---|
| POST failure (no power/memory) | Live-state fetch fails | SESSION_RITUALS §A.1 |
| Secure Boot signature mismatch | REGISTERED.md content sha256 fails manifest check (CLAUDE.md §A.5 requires the check but names no explicit consequence — open gap, not yet a specified failure mode) | CLAUDE.md §A.5 |
| Kernel panic | Registry-touching halt (fetch failed, or UNAVAILABLE/UNKNOWN/STALE) | SESSION_RITUALS §F.9 |
| Boot into single-user/rescue mode | DEGRADED mode, CLASS_STATE block | IC-029, SESSION_RITUALS §F |
| Device not enumerated, driver refuses bind | Zone misalignment → merge block per ZONE_REGISTRY.md; CLAUDE.md lists the enforcing gate as "planned Phase 3" (conflict, unresolved) | ZONE_REGISTRY.md vs. CLAUDE.md governance table |
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
| Init/unit order | PRIORITY_QUEUE.md | Ranked (Z1-proposed scores, Z2 hash pending), blockers surfaced |
| Permission model | CLAUDE.md + CODEOWNERS (review-gated, not filesystem-enforced) | Z1/Z2/Z3 caps |
| Boot log | Drift catalog + Phase 1 block | Structured self-report |
| Login prompt | §A.7 confirmation wait | Work gated on acknowledgment |
| Runtime tuning | molt_cycle.py, MOLT_STATE.md | Rate-limited live changes |
| Close ritual | §B (B.0, B.6) | Verify before asserting (analogy, not literal I/O) |
| Journal | WGS `#wgs-sync` (actual per-session record) | Required close ritual; `ledgers/NF_LEDGER.jsonl` is a pattern example only, not what §B writes to |

---

**Generated by:** Claude (Z1 Proposer)
**For ratification by:** Night/Admiral (Z2 Ratifier)
**For execution by:** N/A — documentation/reference-architecture only; no Z3 execution required beyond the CLAUDE.md link already included in this PR

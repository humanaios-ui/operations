---
document_type: Z1 gate registry manifest, not a registry entry itself
status: Z1 DRAFT
purpose: single-source inventory of every hard-reject enforcement class
  built S-071126-01, sequenced for actual system-wide wiring rather
  than left as five scattered standalone files
---

# Gate Registry — S-071126-01

## Inventory (mechanically confirmed via grep, not recalled)

| Exception class | File | Guards against |
|---|---|---|
| `SameSubstrateRejection` | `cross_substrate_blind_discriminator_v1_0.py` | A substrate scoring/discriminating its own output |
| `CredentialMissing` | `tier1_logprob_capability_probe_v1_0.py` | Probing with a placeholder or absent credential |
| `ClaimNotAdmissible` | `primary_check_gate_v1_0.py` | A narrative claim about code state with no fresh VerificationRecord |
| `OutcomeAsymmetryRejection` | `outcome_symmetry_checker_v1_0.py` | A hypothesis draft interpreting only one outcome branch |
| `SupabaseUnreachable` | `z2_queue_v1_1.py` (pre-existing, not built this session) | Silent loss on a failed live write — falls back, never drops |

Plus, pre-existing hard-reject enforcement already live in the project
before this session (for continuity, not re-invented): `z2_queue`'s
`zone2_ratification` field requirement, `registry_issue_compiler`'s
identical gate.

## Blocking prerequisite (do not skip)

**IC-050 (Blocker Gate Not Enforced)** — `haios_agent_orchestrator_v1_0_patched.py`
already documents that uncleared blocker gates should halt execution,
but runtime behavior only warns and continues through every phase. None
of the five gates above matter at the orchestrator level until this is
fixed. Wiring new gates into a pipeline whose existing gate-halt logic
is known-broken produces the same false-confidence pattern IC-041
already named for the CI audit workflow — a gate that exists in the
codebase but not in enforced behavior.

**Sequencing, not simultaneous:**
1. IC-050 fix (Zone 3, Night/Copilot — outside what Claude can execute
   from this sandbox).
2. Wire the five gates above into the now-actually-enforcing
   orchestrator, one at a time, each with a live-artifact test before
   the next is added (same discipline `outcome_symmetry_checker` was
   just tested against a real prior H-cand, not a synthetic example).
3. Retroactive sweep: run `outcome_symmetry_checker` against every
   existing H-class entry in REGISTERED.md, not just this session's
   batch — this session confirmed it catches real gaps; the existing
   corpus has not been checked at all.

## What this manifest does NOT do

- Does NOT wire anything into the live repo — that requires Zone 3
  credentials and access this sandbox does not have.
- Does NOT claim IC-050 is fixed — it is cited as an open prerequisite,
  unchanged from its existing registered status.
- Does NOT propose new gates. This is inventory and sequencing only.

## Ratification gate (for Z2)

- Confirm the sequencing above (IC-050 first) rather than treating gate
  count as the success metric.
- Decide who owns the retroactive REGISTERED.md sweep (item 3) and on
  what cadence — this is a real, possibly large task once existing
  H-class entries are checked, not a quick pass.

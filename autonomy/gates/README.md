# autonomy/gates — executable Zone gating framework

The **autonomy / ECO gating model made executable**: the machinery that enforces
*propose ≠ ratify*, *no self-execution*, and *operator decides* across the
Zone model (Z1 = AI dresses/proposes · Z2 = operator inspects/ratifies ·
Z3 = operator sets/executes credentialed).

Landed from `docs/_inbox_` (session **S-071426**). Authored by the HumanAIOS/ACAT
program (sessions S-0711/0713-26, grok-assisted). This README is the map; each
module carries its own docstring.

## Architecture

The stack is three tiers plus a gateway, all in this flat package (flat to
preserve the validated import graph — several modules import each other by
bare name, and `z3` / `verified_tacit` hard-import their dependencies):

**Tier 0 — core Zone primitives**
- `mason_gate.py` — the base primitive. Encodes Z1/Z2/Z3 as journeyman-dress /
  master-inspect / wall-set over a `Stone` (banker_mark = preparer,
  waller_mark = setter). Every other Zone module composes on this.
- `z1_dress_protocol_v0_1.py` — machine contract for what makes a Z1 artifact
  properly "dressed" (nine structural requirements) before Z2 inspection.
- `z3_set_protocol_v0_1.py` — the irreversible Z3 "set" contract. A stone may
  only be SET if it passed Z1 dressing **and** Z2 substantive inspection.
  Declares (does **not** execute) real side-effects: REGISTERED.md append,
  PR merge, Supabase insert, prod deploy.

**Tier 1 — ceremony gates** (in-memory state machines, one per governance principle)
- `P21_finding_gate.py` — a finding cannot be REGISTERED without ratification by
  a party distinct from the proposer (anti-self-ratification).
- `P23_eff_gate.py` — findings from an external framework can't reach external
  comms without ratification.
- `P29_articulation_gate.py` — a Z2-destined artifact must carry a three-part
  articulation (what / evidence / risk) before it is review-eligible.
- `drift_transfer_gate.py` — "drift = transfer the chat": once a catalogued drift
  signal is named, no further work proceeds until acknowledge + transfer.
- `verified_tacit_gate.py` — caps unresolved `verified_tacit` claims per verifier
  (WARN 5 / ESCALATE 10) before a mandatory retrospective review.
  Depends on `carry_tracker_v1_0.py` (vendored here; canonical copy in `tools/`).

**Tier 2 — pipeline checkers** (v1.0, "no claim without a real VerificationRecord")
- `primary_check_gate_v1_0.py` — a state-claim is inadmissible without a
  `VerificationRecord` capturing a real command + its captured output.
- `outcome_symmetry_checker_v1_0.py` — a hypothesis must interpret **both** the
  confirm and disconfirm branches before registration (hard-reject on a missing
  branch; advisory on lopsidedness).
- `guidepost_checker_v1_0.py` — composes the above into the beneficial/effective/
  informative guidepost trio.

**Gateway**
- `master_gateway.py` — executable integration harness. Runs representative
  positive **and** negative workflows for the wired gates, then applies the
  governance stack to itself (self-audit). Run it: `python3 master_gateway.py`.

**Vendored support modules** (wired by the gateway demo; canonical analysis homes
noted): `reference_linter.py`, `claim_reproduction_checker.py`,
`kambhampati_tracker.py`, `telemetry_schema_test.py`.

## Status: Z1-DRAFT — proposed, not ratified

Everything here is **library-only**. It models and enforces gates in-memory; it
does **not** wire any gate to a real side-effect. This is deliberate.

### Known limitations (tracked, not hidden)

1. **Registry gap.** `master_gateway` wires the 7 core gates but **not** `P29`,
   `primary_check_gate`, `outcome_symmetry_checker`, or `guidepost_checker`.
   Those run standalone (each has a passing `--smoke-test`) but are not yet in the
   gateway's aggregate demo/self-audit. Wiring them (they use dependency-injected
   callables) is a focused follow-up, deferred rather than rushed here.
2. **Security seams — reason this is library-only.** `primary_check_gate` runs
   arbitrary `subprocess` commands, and `z3_set_protocol` *declares* prod-deploy /
   PR-merge / Supabase-insert effects. **Do not wire either to real execution
   without sandboxing + input validation.** That wiring is Z3-credentialed work,
   out of scope for this landing.
3. **`reference_linter` / `drift_transfer_gate`** read governance docs / a drift
   catalog that live at the repo root; run from repo root, or expect graceful
   empty/degraded results (as the gateway demo shows).

### Compatibility fix applied on landing

Eight modules used PEP 604 `X | None` annotations in class bodies without
`from __future__ import annotations`, which fails on Python < 3.10. The authors
had already added that import to 3 files; the same one-line fix was applied to the
remaining 8 so the package runs on 3.9 → 3.13. No other authored code was changed.

## Verify

```bash
python3 master_gateway.py                       # full demo + self-audit (8 checks PASS)
python3 primary_check_gate_v1_0.py --smoke-test
python3 outcome_symmetry_checker_v1_0.py --smoke-test
python3 guidepost_checker_v1_0.py --smoke-test
```

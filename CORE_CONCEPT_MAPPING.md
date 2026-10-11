# CORE_CONCEPT_MAPPING.md — Governance Conformance Model → HCM Translation
## Layer 0 conformance fixture; the proposed HCM is the machine encoding

**Source:** `CLAUDE.md` (authority roles, decision routing, anti-cascade rules, §A / §B, callout triggers), `SEED.md` §1 and §3 (what the organism is; the claim-vs-behavior gap), `SESSION_RITUALS.md` §A, §B.0, §F
**Mapping Date:** 2026-10-11
**Authority effect:** `NONE`

**Status:** Z1 conformance candidate for REGISTERED.md (Q-CORE-CONCEPT-MAPPING-01); not an admission or ratification record

**Code:** [`humanaios_core.py`](./humanaios_core.py) (stdlib only, 31 exported names) · tests: [`test_humanaios_core_tier1.py`](./test_humanaios_core_tier1.py) (40 tests, `unittest`, no pytest dependency) · standing check: `python3 humanaios_core.py --smoke-test`

---

## Executive Summary

Layers 1–5 each take an outside concept (five engineering patterns, a boot chain, Musashi, assurance questions, Programs) and map it onto this repository's governance. `humanaios_core.py` is a pure conformance model for examples of that shared shape. It does not authenticate a ratifier, authorize execution, or compete with the proposed HumanAIOS Core Machine (HCM) bytecode in PR #812. HCM is the proposed canonical machine encoding; this model supplies doctrine-level fixtures that can be translated into and tested against HCM.

The core concept, in one paragraph, is what the module's docstring says:

> A machine (Z1) may **propose**, and every proposal carries a falsifier and a pinned SHA. The model's Z2 transition produces an unkeyed sha256 hash over the candidate, a claimed identity, the time and the decision; identity authenticity must be enforced outside this module. Its Z3 transition records a modeled execution only after an ACCEPT hash and caller-supplied CI status. Retries are bounded (anti-cascade: K=3, one open molt per constant, freeze after two reverts). Every session opens by pinning live state (§A) and closes by reconciling every claim against the tree (§B.0 / B.6). What is not in the ledger did not happen, and **the gap between what was claimed and what the tree shows is the finding.**

That last clause is also ACAT's core measurement (`SEED.md` §3: the gap between what an AI claims about its own behavior and what it does under test). The conformance model and the research instrument share the same shape: a claim, a check, a gap. `reconcile(claims, tree)` is that shape as a function.

| Layer | Document | Maps | Onto |
|:---|:---|:---|:---|
| **0** | **`CORE_CONCEPT_MAPPING.md` (this)** | **Doctrine-level serial-gate examples** | **`humanaios_core.py`: non-authoritative conformance fixture** |
| **Machine** | **HCM v0.1 (PR #812 candidate)** | **Evidence/authority/action contract** | **Deterministic bytecode and pure replay VM** |
| 1 | `FRAMEWORK_MAPPING.md` | 5 AI engineering concepts | Z-roles, governance files, CI gates |
| 2 | `BOOT_PROCESS_MAP.md` | Session rituals §A / §B | Boot-chain stages, resource states |
| 3 | `FIVE_RINGS_MAPPING.md` | Musashi's five books | Functions, commands, gates |
| 4 | `AUTHORIZATION_EVIDENCE_MAPPING.md` | Authorization & evidence assurance questions | Gates, schemas, ledgers, `authorization_evidence.py` |
| 5 | `PROGRAM_GRAPH_MAPPING.md` | Programs | `INTENT_GRAPH.yaml` Objectives, `RESOURCE_UNITS.yaml` cost, `program_graph.py` |

**Reading rule (inherited from Layer 3).** Every row below ends in something that can be run. *Doctrine* is the sentence in the governing document. *Machine translation* is what it means for a running system. *Operation* is the exact name in `humanaios_core.py`, and the existing artifact that already enforces the same thing where one exists. A row with nothing runnable at the end is prose, not a mapping, and does not belong here.

### HCM translation contract

`HCM_TRANSLATION_FIXTURE` gives the bounded semantic correspondence. It is a test fixture, not a compiler and not authority evidence:

| Conformance operation | Proposed HCM instruction phase | Boundary |
|:---|:---|:---|
| `propose` | `PIN_CONTEXT → OBSERVE → CLAIM → CHALLENGE → WARRANT` | The model supplies doctrine examples; HCM performs canonical validation. |
| `ratify` | `IMPORT_AUTHORITY` | The model's unkeyed hash is insufficient. HCM requires externally authenticated, exact-head human-review evidence. |
| `execute` | `RECORD_ACTION` | The model writes a synthetic ledger event. HCM records an independently observed action and has no action handler. |
| `session_close` | `RECORD_OUTCOME → CLOSE` | The model reconciles claims; HCM binds witnessed outcomes and emits a non-authoritative receipt. |

Both surfaces fix their authority effect at `NONE`. Repository Coordinator admission, implementation acceptance, and merge authority remain outside both.

---

## 1. Roles: a zone is a capability set, not a rank

| Doctrine (`CLAUDE.md`) | Machine translation | Operation |
|:---|:---|:---|
| Z1 proposes; Z2 ratifies; Z3 executes | Three roles, three disjoint action sets; nothing else grants | `Zone`, `Action`, `can(zone, action)` · `_CAPABILITIES` table |
| Admiral "cannot do (by design)": execute ratified changes, propose new work | Z2 holds exactly one action: RATIFY | `can(Zone.Z2, Action.EXECUTE) is False` · `can(Zone.Z2, Action.PROPOSE) is False` |
| Z1 and Z3 "cannot execute/ratify without Z2 hash (CI enforces)" | RATIFY is Z2-only; absence of a capability is refusal, never a default | `GateRefused` from `_require()` · `scripts/enforce_z2_z3_boundary.py` · `z2_ratification_gate.yml` |
| Z1 may contest; Z3 may report GAUGE | CONTEST is held by Z1 and Z3, never by Z2 (no self-contest) | `can(Zone.Z1, Action.CONTEST)`, `can(Zone.Z3, Action.CONTEST)` |

---

## 2. Propose: a claim carries the shape of its own refutation

| Doctrine | Machine translation | Operation |
|:---|:---|:---|
| "Z1 includes falsifier (required by falsifier_lint.yml)" | A candidate without a substantive falsifier is not a candidate | `propose(...)` refuses `""`, `TBD`, `N/A`, `none`, `unknown` — the same list `ci_gates.FalsifierLintGate.is_substantive` rejects |
| IC-030: "live-fetch, pin SHA" before any registry-touching work | A candidate names the SHA of the REGISTERED.md it was written against | `Candidate.pinned_sha` required; empty → `GateRefused` |
| Candidate kinds: F / IC / H / MOLT / Q | A closed set; an unknown kind is refused, not coerced | `propose(kind=...)` |
| A ratified thing never moves | The candidate is immutable once built; the modeled hash covers a deterministic serialization | `Candidate` is `frozen=True` · `Candidate.canonical()` (`json.dumps(sort_keys=True)`) |

---

## 3. Ratify: the Z2 serial gate

| Doctrine | Machine translation | Operation |
|:---|:---|:---|
| `sha256(candidate \| by=Night \| at=timestamp \| decision=ACCEPT\|EDIT\|REJECT)` | An unkeyed hash covers those four caller-supplied segments. It checks consistency, not identity authenticity. | `ratification_hash(candidate, by, at, decision)` · smoke test recomputes it by hand and compares |
| Contested: `... \| contest_response=<reason>` appended | Same formula, one more segment | `ratification_hash(..., contest_response=...)` |
| Both `carly.r.anderson@gmail.com` and `aioshuman@gmail.com` are configured values (Q-Z2-DUAL-AUTHORITY-GOVERNANCE-01); "Night" is the display name | The module refuses a `by` value outside the configured set but does not authenticate the caller; the display name is not an identity credential | `AUTHORIZED_Z2_IDENTITIES` (exactly the two emails) · `Z2_DISPLAY_NAME = "Night"` kept separate · authentication external |
| "If REJECT: Z2 documents reason" | A REJECT with no reason is refused at signing time | `ratify(..., Decision.REJECT, reason="")` → `GateRefused` |
| "Change Z2 decision retroactively" is not allowed; "only emit new RATIFY event with new hash" | A `Ratification` is frozen; a changed mind is a second event with a second hash and the first intact | `Ratification` `frozen=True` · smoke test: `rej.hash != acc.hash` and both still verify |
| M12 Z2 hash verification | Recompute from inputs; any drift in candidate, signer, time, decision or contest text fails | `verify_ratification(candidate, ratification)` · `ci_gates.Z2HashGate` (format and presence) |

---

## 4. Windows and the contest route

| Doctrine | Machine translation | Operation |
|:---|:---|:---|
| "48h for routine decisions; 24h or less for urgent items" | A window is a state function of proposed-at and now, never a timer the proposer controls | `DECISION_WINDOW`, `URGENT_WINDOW`, `window_state(candidate, now, decided, urgent)` → `OPEN \| DECIDED \| EXPIRED` |
| "Z1 contests Z2 rejection within 48h, or 48h window closes without Z2 decision" | Two triggers, both checked; anything else is refused with the reason | `contest(zone, candidate, prior, now, reason)` |
| Only a REJECT is contestable | Contesting an ACCEPT or EDIT is refused | `contest(...)` with `prior.decision is not REJECT` → `GateRefused` |
| A contest answers a real decision on this candidate | A `prior` that does not verify against the candidate (forged, or signed for another block) is refused; so is a contest dated before the REJECT it names; elapsed time must sit in [0, 48h] | `contest(...)` calls `verify_ratification(candidate, prior)` first · smoke test: other-candidate REJECT, zero-hash REJECT, pre-dated contest all refused |
| "IC beyond 48h / Z2 decision contested" callout | The contest returns the callout text; it never mutates the prior event | return value of `contest(...)` |
| Blocked row without unblock action → GAP | An EXPIRED window is the GAP trigger | `window_state(...) == "EXPIRED"` → `callout_route("GAP")` |

---

## 5. Execute: Z3 under hash

| Doctrine | Machine translation | Operation |
|:---|:---|:---|
| "Merge PRs with Z2 hash + CI gate pass" | Four refusals in a fixed order: zone, hash present, hash verifies and is ACCEPT, CI green | `execute(zone, candidate, ratification, ci_gate_pass, executor, now, ledger)` |
| "Cannot execute without Z2 hash (CI enforces)" | `ratification=None` is refused before anything else is looked at | `execute(..., None, ...)` → `GateRefused("no Z2 hash")` · `z2_ratification_gate.yml` |
| A hash for REJECT or EDIT executes nothing | A consistent modeled hash that is not ACCEPT is still a refusal | smoke test: `execute(..., rej, ...)` refused |
| "Emit VERDICT/CYCLE/MEASURE events"; receipts for B.6 | A successful model transition writes one synthetic EXECUTE row carrying the hash and pinned SHA. It performs no external action. | `Ledger.append("EXECUTE", ...)` payload `{candidate_id, z2_hash, pinned_sha}` · HCM translation: `RECORD_ACTION` |
| A refusal leaves no trace of having almost happened | No refused path writes to the ledger | `test_four_refusals_in_order` asserts `len(ledger) == 0` |

---

## 6. The anti-cascade envelope

| Doctrine (`MOLT_STATE.md`, `CLAUDE.md`) | Machine translation | Operation |
|:---|:---|:---|
| Rule 1: one open molt per constant | A new candidate on a constant with an open molt is outside the envelope | `anti_cascade(constant, open_molts, consecutive_reverts)` → `"rule 1: ..."` |
| Rule 3: at most K=3 molts open system-wide | Three open anywhere means no fourth, whatever the constant | `K_OPEN_MOLTS = 3` → `"rule 3: ..."` |
| Rule 4: reverted twice in a row → frozen; Z2 Tier-2 ruling to reopen | Two consecutive reverts freeze; one does not | `REVERTS_TO_FREEZE = 2` → `"rule 4: ..."` · `authorization_evidence.render_decision({"frozen": True})` → ROLL_BACK |
| Rules 2 (no self-reference inside a window) and 5 (Priority Queue rank, no bypass) | Need the event stream and the queue; they stay where they are | `molt_cycle.py` · `priority_queue_engine.py` — cited, not duplicated |

`molt_cycle.MoltCycle.check_anti_cascade_rules()` already derives rules 1, 3 and 4 mechanically from `constants.json`'s per-constant `molt_id` / `molt_history` fields and reports rules 2 and 5 as NOT_MECHANICALLY_CHECKED rather than assumed (the "stub" note in `AUTHORIZATION_EVIDENCE_MAPPING.md` §3 predates that implementation). `anti_cascade()` here is not a replacement for it: it is the pure, candidate-level form of the same three rules — given one constant and the current open-molt and revert-count state, it answers "would *this* new candidate break the envelope?", which the repo-wide report does not ask. It reads nothing from disk, so a caller that already has `check_anti_cascade_rules()`'s `open_constants` and `frozen_constants` in hand can pass them straight in.

---

## 7. Callouts: ten triggers, ten routes

| Doctrine (`CLAUDE.md` "Callout Mandatory Triggers") | Machine translation | Operation |
|:---|:---|:---|
| GAP, STALE, RECEIPT-GAP, GAUGE, AMBIGUITY, VOID, DRIFT, DISPUTED, MOLT, REVERT | A closed table of `kind → (routes, Z2 response)`; names are literal | `CALLOUTS` (10 entries) · `callout_route(kind)` |
| Route targets Q / FS / OM / MOLT / Z2 | Routes are a tuple, not free text; an unknown kind is refused, not guessed | `callout_route("VIBES")` → `GateRefused` |
| RECEIPT-GAP → Q + FS, "Verify or file IC-CAND" | A B.6 gap is routed automatically at session close | `session_close(...)` writes one `CALLOUT` row per gap with `routes == ["Q", "FS"]` |

---

## 8. §A session open: halt-on-failure, in order

| Doctrine (`CLAUDE.md` §A, `SESSION_RITUALS.md` §A / §F) | Machine translation | Operation |
|:---|:---|:---|
| 1. `git fetch && git rev-parse HEAD` — pin SHA | No pin, no session | `session_open(state)` → `"A.1: no pinned SHA"` |
| 2. Read REGISTERED.md *at that SHA* (IC-030) | Reading it at any other SHA, or from memory, is the same halt | `"A.2"` when `registered_read_at_sha != pinned_sha` · `BOOT_PROCESS_MAP.md` Secure-Boot stage |
| 3. Read PRIORITY_QUEUE.md | | `"A.3"` |
| 4. Read ZONE_REGISTRY.md; heading count = active rows | | `"A.4"` · `registry_consistency` gate |
| 5. Verify sha256 against manifest | | `"A.5"` · `.tool-control/scan.py --check` |
| 6. State position · destination · probability | Probability is a number in [0, 1], not a word and not a flag (`True` is rejected even though `bool` is an `int`) | `"A.6"` |
| A missing key is a halt, never a pass | Cautious default, as `authorization_evidence._UNSAFE_DEFAULTS` | `session_open({})` returns all six halts, in order |

---

## 9. §B session close: the gap is the finding

| Doctrine | Machine translation | Operation |
|:---|:---|:---|
| B.0: "Code ran? If no, close refused." | Not a warning; the close raises | `session_close(...)` → `GateRefused("B.0: code did not run")` |
| B.0: "Prereg hash verified in REGISTERED.md? If no, close refused." | | `GateRefused("B.0: prereg hash not verified")` |
| Handoff block: `z1-inbox/<date>/HANDOFF.md` | No handoff, no close | `GateRefused("...HANDOFF.md not written")` |
| B.6: "Walk claim vs. tree (every statement in transcript)" | Exact-match reconciliation: a claim the tree confirms is matched; one it does not is a gap | `reconcile(claims, tree)` → `Receipt(matched, gaps)` · `receipt_reconciliation.py` · `anthropic-skills:humanaios-receipt-reconciliation` |
| "Report RECEIPT-GAP → Priority Queue" | Each gap becomes a chained CALLOUT row routed Q + FS | `session_close(...)` ledger rows `RECEIPT`, then `CALLOUT` per gap |
| IC-031: receipts "may not assert contents the verification block does not confirm"; walk the draft back, never explain the gap up | The tree is the fixed side; claims are reconciled *to* it | `Receipt.clean` is `not gaps`; the tree holding more than was claimed is clean, the reverse never is |
| `SEED.md` §3: ACAT measures the gap between what a system claims and what it does | Same function, different inputs: Phase 1 self-report is the claim, Phase 2 behavior is the tree | `reconcile(claims, tree)` — the kernel and the instrument share one primitive |

---

## 10. The ledger: what is not written did not happen

| Doctrine | Machine translation | Operation |
|:---|:---|:---|
| NF_LEDGER.jsonl: "append-only; hash-chain validation" | Each row's hash covers the prior row's hash; rewriting any earlier line breaks every later one | `Ledger.append(...)`, `Ledger.verify()` · `ci_gates.MerkleRootGate` · `tools/nf_ledger_v0_1.py` |
| `FIVE_RINGS_MAPPING.md` Void: "what is not written to the ledger did not happen" | Every gate step that succeeds against a ledger is a row; a refusal never is. `propose()` and `ratify()` take an optional `ledger` and write PROPOSE / RATIFY rows when given one; `execute()` and `session_close()` require one. A caller that passes no ledger holds a value the ledger does not know about, and the module does not pretend otherwise | `Event` rows: PROPOSE, RATIFY, EXECUTE, RECEIPT, CALLOUT · smoke test asserts a refused `propose`/`ratify` leaves the ledger unchanged · `five_rings.persist_or_void` |

---

## Integration: one candidate through the whole gate

```python
from datetime import datetime, timezone
from humanaios_core import (Decision, Ledger, Zone, execute, propose, ratify,
                            session_close, session_open, verify_ratification)

now = datetime.now(timezone.utc)
halts = session_open({"pinned_sha": sha, "registered_read_at_sha": sha, "queue_read": True,
                      "zone_registry_ok": True, "manifest_ok": True,
                      "position": f"REGISTERED.md pinned at {sha}", "destination": "Q-X", "probability": 0.8})
assert not halts                                                     # §A: or stop here

ledger = Ledger()                                                    # opened first: every step below is a row
cand = propose(Zone.Z1, "Q-X", "Q", body, falsifier, sha, "claude", now, ledger=ledger)   # falsifier + pin, or refused
acc = ratify(Zone.Z2, cand, "carly.r.anderson@gmail.com", now, Decision.ACCEPT, ledger=ledger)  # claimed identity; not authenticated here
assert verify_ratification(cand, acc)

execute(Zone.Z3, cand, acc, ci_gate_pass=ci_green(), executor="z3", now=now, ledger=ledger)  # modeled row only

receipt = session_close({"code_ran": True, "prereg_verified": True, "handoff_written": True,
                         "claims": transcript_claims, "tree": b0_verification_block},
                        ledger, now, "claude")                       # B.0 refuses; B.6 reconciles
assert ledger.verify()                                               # what is not chained did not happen
```

`sha`, `body`, `falsifier`, `ci_green`, `transcript_claims` and `b0_verification_block` stand for the session's own values. `ratify` is a consistency-model operation. A protected external surface must authenticate and bind the human decision.

---

## What this module is not

- **Not a replacement for `ci_gates.py`, `molt_cycle.py`, `z2_ratification_gate.yml` or `receipt_reconciliation.py`.** Those read real files, real ledgers and real git state. `humanaios_core.py` is pure: it takes values and returns values or refuses. Where an existing artifact enforces the same rule, the table names it; the kernel is the rule stated once, the artifacts are the rule applied to a surface.
- **Not an authority or executor.** `AUTHORITY_EFFECT` is `NONE`; modeled RATIFY and EXECUTE rows do not authenticate a person, perform an action, admit work, or authorize merge.
- **Not a second machine-code contract.** The proposed HCM bytecode is the machine layer. `HCM_TRANSLATION_FIXTURE` makes the relationship explicit and marks the model's unkeyed hash as insufficient for `IMPORT_AUTHORITY`.
- **Protected by the quality baseline.** `test_humanaios_core_tier1.py` is enumerated in `.tool-control/baseline_tests.yaml`.

---

## Action Items for Z2 Ratification

1. Evaluate `CORE_CONCEPT_MAPPING.md` + `humanaios_core.py` as a non-authoritative Layer 0 conformance fixture after the HCM relationship is reviewed.
2. Preserve HCM's externally authenticated exact-head authority import; do not substitute this module's unkeyed hash.
3. Decide whether `AUTHORIZATION_EVIDENCE_MAPPING.md` §3's "stub" note on `check_anti_cascade_rules()` is corrected in its own PR: `molt_cycle.py` now derives rules 1, 3 and 4 mechanically, so that row's PARTIAL status is stale. Documentation only; no code change proposed to `molt_cycle.py`.

**Falsifier for this mapping:** a row above that names an operation which does not exist in `humanaios_core.py`, or a doctrine sentence that the named operation does not actually refuse on, falsifies its own row and the row is struck. `python3 humanaios_core.py --smoke-test` (every refusal exercised once, the hash recomputed by hand) is the standing check; `test_humanaios_core_tier1.py` is the training.

---

## Metadata

```yaml
metadata:
  layer: 0
  stack: ["CORE_CONCEPT_MAPPING.md", "FRAMEWORK_MAPPING.md", "BOOT_PROCESS_MAP.md", "FIVE_RINGS_MAPPING.md", "AUTHORIZATION_EVIDENCE_MAPPING.md", "PROGRAM_GRAPH_MAPPING.md"]
  source: "CLAUDE.md (authority, routing, anti-cascade, §A/§B, callouts); SEED.md §1, §3; SESSION_RITUALS.md §A, §B.0, §F"
  code: "humanaios_core.py (stdlib only), test_humanaios_core_tier1.py (unittest)"
  exported_names: 29
  authority_effect: "NONE"
  machine_encoding: "proposed HCM v0.1 (PR #812); external exact-head authority required"
  candidate_id: "Q-CORE-CONCEPT-MAPPING-01"
  last_updated: "2026-10-11T00:00:00Z"
```

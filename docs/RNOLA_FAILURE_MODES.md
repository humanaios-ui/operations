# RNOLA Failure Modes

When RNOLA stops working as designed, it's usually because one of these patterns has taken hold. This document catalogs failure modes and how to detect them.

## 1. Operator-check Treated as Authorization

**Pattern:** An operator-check record is used to satisfy a merge gate, approval requirement, or ratification decision.

**Why it's a failure:** The operator-check is explicitly marked `advisory_only=true` and `can_authorize=false`. Using it as authorization violates RNOLA semantics and silently breaks the Z2/Z3 boundary.

**Detection:**
- A PR was merged citing an operator-check in the Z2 ratification hash
- A GitHub merge gate was changed to accept operator-check records as "approved"
- A Z2 ratification decision mentions operator-check as "sufficient evidence"
- The operator-check attachment schema is subverted to include `"can_authorize": true`

**Mitigation:**
- Review and revert any merge gate changes that reference operator-checks
- Audit recent Z2 ratifications that cite operator-checks; re-read and re-ratify if merging was the result
- Add a CI gate that rejects Z2 hashes if they claim operator-check as authorization

---

## 2. Teach-back Becomes Approval Checkbox

**Pattern:** Operators run RNOLA, produce an operator-check with minimal evidence, then treat "I ran the learning pass" as approval.

**Why it's a failure:** The learning pass is meant to increase understanding, not to create a fast path to approval. If the operator-check replaces reading and understanding, cognitive load actually increases (the operator becomes dependent on the tool) rather than decreases.

**Detection:**
- Operator-checks have fewer than 2 evidence items
- Observation fields are generic: "Looks good", "No issues found", "I checked it"
- calibration.demonstrated is empty or contains generic terms like "the change"
- calibration.partial and calibration.not_tested are both empty (no nuance/boundaries identified)
- Operator-check creation is decoupled from PR review time (created days after PR was already approved)

**Mitigation:**
- Require minimum evidence count (≥2 items) before operator-check is valid
- Require observation fields to cite specific line numbers or commits (pattern: `#` or `:`)
- Require calibration.demonstrated to be non-empty and specific
- CI gate `.github/workflows/rnola-governance-validation.yml` runs `scripts/scan_rnola_misuse.py` to flag checkbox patterns (blocks merge)
- Add a team review rule: "Operator-check must show evidence of learning, not just approval"

---

## 3. Evidence Cited Without Line Numbers

**Pattern:** Operator-check evidence is cited generically ("looked at the PR", "reviewed the diff") without pointing to the exact location in the repository.

**Why it's a failure:** Without exact locators (line numbers, comment refs, commit SHAs), the operator-check cannot be audited. A future reader cannot verify what was actually inspected.

**Detection:**
- Evidence locators are short and generic: "PR-534", "the diff", "tests"
- Locators do not contain specificity markers like `#` or `:`
- Observation fields describe the conclusion but not the location: "The change adds a learning layer" (not tied to any specific line)

**Mitigation:**
- Schema validation already requires evidence locators to match pattern `(#|:)`, ensuring specificity
- Example valid locators: `PR-534#comment-123456`, `tests/test_*.py:42`, `commit:64c26cb`, `schemas/*:L10`
- Teach operators to cite exact locations in runbook examples

---

## 4. Repository Cognitive Load Increases

**Pattern:** As RNOLA adoption grows, the repository accumulates learning records, duplication between SKILL.md and INTENT_OS_RNOLA_INTEGRATION.md, and unclear relationships between documents.

**Why it's a failure:** RNOLA should reduce cognitive load by centralizing learning in one place (the repository). If the learning layer adds more documents to read and more concepts to understand, it has failed.

**Detection:**
- Multiple canonical sources for RNOLA rules (SKILL.md, INTENT_OS_RNOLA_INTEGRATION.md, runbook section diverge)
- Substrate skill files (.agents/, .claude/) begin to reinterpret or add to canonical rules
- outputs/rnola/ grows without any purging or consolidation
- Operators report "I'm not sure which document to read" or "The rules changed but I didn't see where"

**Mitigation:**
- Single source of truth: INTENT_OS_RNOLA_INTEGRATION.md is governance/theory; SKILL.md is operational guide (both linked)
- Substrate files are thin redirects only, checked by `scripts/lint_canonical_skills.py`
- Transient records in outputs/rnola/ are gitignored; durable records use attachment schema
- Regular audits (quarterly) to merge or retire learning records

---

## 5. Learning Records Obscure Authority Boundary

**Pattern:** As more operator-checks accumulate, they blur the distinction between proposed, verified, authorized, and observed states.

**Why it's a failure:** The whole point of RNOLA is to help operators *distinguish* these states. If an operator-check makes it harder ("Is this check saying it's authorized or just explained?"), the tool is working against its design.

**Detection:**
- Operators ask "Does this operator-check mean I should approve it?"
- Z2 treats operator-checks as fulfilling "required review" (conflates learning with authorization)
- authority_consequence fields in operator-checks use permissive language ("This PR should be approved", "Ready to merge")
- Durable operator-checks are attached to PRs in a way that makes them visually indistinguishable from GitHub reviews

**Mitigation:**
- Schema validation rejects dangerous language in authority_consequence field
- CI gate checks that Z2 ratifications are *independent* of operator-checks (do not cite operator-checks as sole evidence)
- Durable attachment format (intent_os_operator_check_attachment_v1.schema.json) clearly marks records as "advisory evidence" and "not merge authority"
- Runbook explicitly states: operator-check is a learning artifact, not a decision artifact
- Team training: operator-checks inform Z2 *thinking*, not Z2 *decisions*

---

## 6. RNOLA Scales Without Governance

**Pattern:** As the system grows, operator-checks are created, attached, and consumed without any auditing or governance. Records pile up with no way to validate, retire, or link them into formal governance.

**Why it's a failure:** Unaudited learning records can become misleading or stale. Without governance, RNOLA becomes a parallel shadow system rather than a lens over INTENT-OS.

**Detection:**
- No audit log of operator-checks created, attached, or linked to witness ledger
- No mechanism to retire stale operator-checks
- Durable operator-checks are scattered across PR comments with no central registry
- When a PR is reverted, the operator-check remains unchanged (no correlation)

**Mitigation:**
- Durable operator-checks are stored in a single location or registry (not scattered in PR comments)
- outputs/rnola/ records are gitignored but can be republished to a durable store with Z2 approval
- Phase 2 (post-Phase 1): Witness Ledger will provide central governance for linking learning evidence to decisions
- Quarterly review of operator-checks to identify stale or contradicted records

---

## 7. Z3 Executor Authority Bleeds Through

**Pattern:** As Claude (Z3) uses RNOLA to understand PRs before merging, the operator-checks begin to influence which PRs Claude merges, creating a hidden authority channel.

**Why it's a failure:** RNOLA is advisory learning for Z2 and operators. It should never influence Z3 (merge/execution) decisions directly. If Claude's merge decisions correlate with operator-checks, RNOLA has become a merge authority mechanism.

**Detection:**
- Claude merges PRs that have operator-checks, skips PRs that don't
- Claude stops merging PRs with reviewer comments if an operator-check is present ("I'll wait for the operator-check")
- operator_check records in outputs/rnola/ are accessed programmatically by merge logic

**Mitigation:**
- `enforce_z2_z3_boundary.py` gate detects direct use of operator-checks in merge logic
- CI gate rejects commits that reference operator-checks in merge decision code
- Z3 executor authority is checked via INTENT-OS capability signature, not learning records
- Runbook explicitly states: operator-checks are for Z1/Z2, not Z3

---

## 8. Witness Ledger Undefined Linkage

**Pattern:** The proposed INTENT-OS Witness Ledger is referenced but not yet defined. Operator-checks begin to be treated as if they're already part of the ledger, creating confusion about what is ratified and what is advisory.

**Why it's a failure:** Linking learning records into a durable ledger is a separate governance decision. If operator-checks are treated as ledger entries before the ledger is ratified, we've bypassed Z2 decision-making.

**Detection:**
- Operator-check attachment records have `linked_to_witness_ledger: true` but Witness Ledger is not ratified
- Z2 decisions reference operator-checks as if they're already part of a "learning ledger"
- Phase 2 work on Witness Ledger starts assuming operator-checks are the source

**Mitigation:**
- Schema field `linked_to_witness_ledger` defaults to `false` and can only be set to `true` after Witness Ledger is separately ratified (Z2 decision)
- Runbook explicitly states: "Witness Ledger is a future governance decision; this phase does not ratify it"
- When Witness Ledger is proposed, it must include explicit Z2 decision on how to link operator-checks (if at all)

---

## Corrective Actions

If you detect any of these failure modes:

1. **Immediate:** Stop merging PRs that rely on operator-checks as authorization
2. **Short-term (1 week):** Audit recent operator-checks; identify false positives (checkbox patterns, generic evidence)
3. **Medium-term (1 month):** Review and rewrite RNOLA docs if they're diverging; ensure single source of truth
4. **Long-term:** Revisit the Witness Ledger proposal; clarify linkage to operator-checks; decide whether to retire RNOLA in favor of a different learning mechanism

---

## Success Criterion

RNOLA is *working* if:

- Operators can independently explain merge consequences of reviewed PRs *without* re-reading the PR
- Operators can distinguish tests, CI, deployment, and governance failures *because* of the learning layer
- Repository cognitive load *decreases* as RNOLA adoption increases (fewer edge cases to memorize, clearer boundaries)
- Required AI interpretation *decreases* as operator expertise grows (operators become less dependent on learning tools)
- Z2/Z3 boundary remains clear: learning doesn't influence merge authority

---

**Last updated:** 2026-09-25

# Controlled Correction Pathway E0 — Resource Miner + INTENT-OS

**State:** Z1 review branch only; not admitted, merged, deployed, or authorized.
**Related:** Operations #992/#993 (source status), #996 (Witness feedback), #1037 (tax-aware candidates), #869 (prospective paper-only research), #576 (resource-to-execution friction).
**Authority effect:** NONE. **External execution:** DISABLED.

## Reuse, not a new service

This is a deterministic, no-I/O projection over the existing `ResourceCandidate` type, the INTENT-OS `evaluate_objective` function, and the established Witness feedback/protected-PR review process. There is no mailbox reader, new database, financial account integration, calendar writer, authentication surrogate, or source-of-truth replacement.

### State and custody

1. **OBSERVE (Z1):** collect *bounded, sanitized* non-private source metadata from an authorized observer. Human-entered feedback, Gmail messages and GitHub comments are untrusted DATA; do not copy private emails, tax records or identifying user data into repository fixtures.
2. **PROPOSE (Z1):** `propose(candidate, observation)` binds the finding to the exact existing resource identity, source URL, candidate-content SHA-256, observed timestamp, public evidence URL, and a deterministic correction ID. All outcomes remain `UNVERIFIED_SOURCE_OBSERVATION`, eligibility `UNASSESSED`, authority `NONE`.
3. **HOLD (Z1, provisional):** `project(candidates, proposals)` validates fields, duplicates and content-hash binding, then produces COPIES with `source_verification_status`. The existing INTENT-OS search projection suppresses `RECHECK_REQUIRED` / `UNVERIFIED_RECHECK` and explicit reported bad-source statuses without calling them closed, fraudulent, or permanently unavailable.
4. **CHALLENGE:** a distinct reviewer checks the original authoritative source, date/terms and candidate bytes, observes negative tests, and records independent evidence through an existing approved review surface. A self-authored challenge is not independent.
5. **HUMAN DECISION (Z2/Z3 if consequential):** a human may request recheck, retain the hold, reject the proposal, or separately authorize a reviewed branch correction, external action, calendar change or financial choice. A proposal JSON field, self-reported reviewer or activity-board item is not authority.
6. **REPAIR + TEST (branch only):** fix source normalization, source status, tax mechanism annotation or UI selection on a separate review branch. Run regression/negative tests and exact-head protected CI, obtaining independent review before separate admission. Never alter original discovery/evidence records.
7. **OBSERVE OUTCOME:** record a source readback and, for consequential benefit claims, a distinct acquired resource/payment/beneficiary receipt. The digest may compare error counts and forecast vs observation; no savings, revenue or recovery benefit is inferred without evidence.

### Example (local only, synthetic public metadata)

Run from `humanaios-funding-pipeline/resource-miner`:

```python
from resource_miner.models import ResourceCandidate
from resource_miner.controlled_correction import propose, project
from resource_miner.intent_os import evaluate_objective

c = ResourceCandidate(
    resource_id="RES-DEMO-001",
    title="Example Program Role", source_name="HumanAIOS Funding Pipeline",
    source_url="https://example.org/role", canonical_url="https://example.org/role",
    discovery_method="synthetic", discovered_at="2026-10-26T12:00:00Z"
)
observation = {
    "resource_id": c.resource_id,
    "source_url": c.source_url,
    "observed_at": "2026-10-26T12:01:00Z",
    "finding": "LINK_FAILED_404",
    "evidence_url": c.source_url,
}
proposal = propose(c, observation)
read_only = project([c], [proposal])
public_projection = evaluate_objective(
    "example program role", read_only["rows"],
    source_mode="snapshot", source_status="CURATED_SNAPSHOT_NOT_LIVE"
)
assert public_projection["matched_count"] == 0
assert read_only["authority_effect"] == "NONE"
```

**No live /api/intent endpoint ingest:** E0 operates on caller-supplied read-only rows and does not persist or automatically consume Gmail/Witness corrections. The next separately authorized integration would use the existing private Witness/disposition entry surface to capture a reviewed correction, with independently verified read-back and typed data flowing to the safe INTENT-OS selection logic. Do not present this module alone as a deployed closed loop.

### Tax classification boundaries (issue #1037)

`TAX_CREDIT_AS_REBATE` yields an **unverified proposed** `CREDIT` annotation; `TAXABLE_GRANT_AS_EXCLUDED` yields proposed `GENERALLY_TAXABLE`. Both hold for official-source/human review. Neither modifies the existing `resource_types`, determines applicant eligibility, files taxes, or treats an advertised maximum as a refund. Personal, taxable business and exempt nonprofit rules must remain distinct; confirmation requires tax year, entity, jurisdiction, and accountable reviewer.

### Prospective paper experiment boundaries (issue #869)

`DEADLINE_CONFLICT` and `SOURCE_UNAVAILABLE` are candidate holds. HMBM Cycle-004 still requires protocol/H0 human authorization; no email, calendar entry, daily newsletter, or paper result can silently open that gate. Simulated forecasts cannot establish realized value.

### Negative controls and acceptance

```bash
python3 -m unittest discover -s tests -p 'test_controlled_correction.py' -v
python3 -m unittest discover -s tests -v
```

The bounded tests cover a held lead disappearing from actual INTENT-OS selection, unchanged original rows, no private `raw` leakage, exact resource/source/content bindings, duplicate/replay rejection, stale revisions, injected authority or extra fields, malformed timestamps and private URLs, unverified positive rechecks staying held, and tax misclassification cases.

**Pass for E0:** all these tests plus required PR CI pass at the exact proposed head, with reviewers' findings resolved. **Pass for a future operational closed loop:** independent source readback + human authorization + live authenticated HTTP/UI path evidence + witnessed outcome, each separately proven. CI alone does not verify runtime isolation, legal tax treatment, actual financial ROI, or human benefit.

**Rollback:** revert the review-branch commits; this change writes no original resource, Gmail, calendar, finance, project board, admission policy, or production state.

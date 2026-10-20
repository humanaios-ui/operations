# Motion Candidate E0 — bounded synthetic experiment

**Parent objective:** #818. **Source implementation:** PR #819 at initial head `1c4ba9232e7ee3614c78e84f43210b1e8afb4a40`.
**Status:** RESEARCH CANDIDATE; NOT ADMITTED, NOT DEPLOYED, NO LIVE PARTICIPANTS.
**Question:** Can the existing newsletter proposal and review records be projected into reusable motion records while retaining provenance, objections, and human authority, with no new infrastructure?

## Baseline versus candidate

- **Baseline:** `NewsletterStore.receive()` records a private proposal, receipt, edition reference, and `record_review()` stores separate stances. It does not provide a standard motion projection. Joining these records is left to callers.
- **E0 candidate:** `project_motion(store, proposal_id)` reads the *same* private SQLite data. It creates no tables, writes, permissions, dispatches, or publication surfaces. It carries the source proposal/edition pointers and hashes, evidence references, ordered stances and rationale hashes, and explicit disabled execution/authority.
- Motion content remains at its original private source. The projection is **not** a public export format. Callers must enforce access control; the experiment adds no access gateway.
- Prose cannot turn a proposal, agreement, constitutional draft, or receipt into authority. Repeated support is not a quorum. Contradictory stances are preserved.
- The term "motion" is a research representation, **not** a parliamentary resolution or claim of an authorized decision.

## Five synthetic fixtures

| Case | Synthetic request | Expected type | Expected authority |
|---|---|---|---|
| M1 | Suggest one official grant feed for Resource Miner | PROPOSAL | NONE |
| M2 | Correct an incorrect eligibility description | CORRECTION | NONE |
| M3 | Object to making private replies public | OBJECTION | NONE |
| M4 | Propose adding an INTENT-OS source link | PROPOSAL | NONE |
| M5 | Ask to require human review for irreversible actions | PROPOSAL | NONE |

A sixth deliberately mixed objection/consent reply must request clarification and create no motion. This is the actual existing classifier boundary discovered by the first protected run (one synthetic fixture failed before repair).\n\nThis deliberately covers different *texts*, not five independently validated governance policies. A human must determine the real scope, constraints, evidence sufficiency, and applicable authority for each proposal. No model-based matching or blending has been admitted.

## Falsifiable checks and acceptance gates

1. Every synthetic proposal remains traceable to its stored source text hash, edition digest, evidence references, and proposal identifier; no silent drops.
2. Human SUPPORT, OBJECT, and repeated positions remain separately visible, in order. Consensus and ratification remain unestablished.
3. Zero motion paths can invoke execution, public posting, eligibility determination, admission, or a vote.
4. No raw private reply body or private review rationale appears in the projected record or channel draft exports.
5. Unknown proposal IDs, edition-integrity mismatches, and more than 200 review events fail closed.
6. Measure retrieval overhead relative to a direct baseline SQL query; **do not** interpret microsecond performance as reduced human review effort.
7. Keep only if the real test suite and independent review show a measurable improvement and no loss of authority controls.

## Observed E0 result (local smoke; not protected CI)

A local, *standalone* smoke fixture reproduced the private table shapes and read-only projection contract; it did **not** run against the complete PR #819 runtime. Five of five synthetic projection cases passed their basic provenance, authority, dissent, and raw-text-exclusion assertions.

- Direct SQL baseline median: **6,858 ns** per fixture.
- Projection median: **13,407 ns** per fixture.
- These are single-pass, very small measurements. They are **not** statistically useful and do **not** support a speedup claim. The additional structure currently carries overhead.
- Reduced human review effort: **UNVERIFIED**.
- Actual `NewsletterStore` integration: **PENDING protected CI**.
- Live enrollment, publication, consent enforcement, and authorization: **OUT OF SCOPE**.

The new integration tests (`tests/substack_agent/test_motion_candidate_experiment.py`) exercise five synthetic `NewsletterStore` motions plus mixed-intent clarification, review dissent, replay, privacy, prompt-injection-as-prose, integrity failures, and bounded history. Existing `hpra-observer.yml` already runs `tests/substack_agent/**`; no new workflow or manifest entry is required.

## Running the experiment

```sh
python3 -m unittest discover -s tests/substack_agent -p 'test_motion_candidate_experiment.py' -v
python3 -m unittest discover -s tests/substack_agent -p 'test_*.py' -v
```

**Review hold:** require independent CodeRabbit/human review and exact-head tests. This nested experiment PR is not itself an `ADMISSION_REQUESTED` approval. PR #819 must preserve its own authenticated human admission and protected CI.

## Smallest follow-up decision

If exact-head tests pass, have a human reviewer time five actual *synthetic* intake-to-review tasks with and without the projection, comparing missing fields, error counts, and elapsed work. Without that result, do not claim reduced work and do not introduce a new Motion Library service.

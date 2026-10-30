# HUMAN_REVIEW_READY: evidence and admission packet, issue #1081

**Admission: HOLD.** This packet is for a human decision. It confers no authority, admits nothing,
and does not change any expected label.

## 1. What was done, in one paragraph

The unchanged GNER-E1 runtime (`tools/gner_verify_e1.py::reconcile`) was run on the same 30
constructed cases two ways, by plain unit assertions and by ACAT-R, using the same expected labels.
Both flag the same four boolean-boundary cases and nothing else. Those four labels are stricter
than the code and are not in any document or existing test, so they are classed PROPOSED_POLICY and
count as zero confirmed defects until a referee accepts them. The six reviewer findings on PR #1082
were each reproduced and repaired with regression tests. The real authenticated entry point
`verify_lead()` was probed read-only against real run ids and behaved exactly as the code reads. No
held-out set exists, so that gate is HOLD.

## 2. Exact references

| Item | Value |
|---|---|
| Base `main` | `52aa7c0ed70f6e24ec050d0d56788a791e5f78f7` |
| PR #1082 head reviewed | `8481574af8adffee83fdb89250847822485e4c86` |
| Work branch | `claude/acat-r-validation-1081-m4mp6q` (stacked on the PR head; exact head in the issue #1081 receipt comment) |
| Pinned runtime blob | `tools/gner_verify_e1.py` `8290c51cd75c7de78a226770936a8f48766c24f0` |
| Pinned import blob | `tools/gner_notification_e0.py` `e8f893a3d433f900b10c101828d1cbb013413fa6` |
| Pinned conventional test blob | `tests/test_gner_verify_e1.py` `8517a93f346e31a392ed7c7234434f37b3e15237` |
| Rubric sha256 (rev 1, enforced) | `6971fd8d2045f301cf31d79a99d5e04bdf101ed7db968d9ee15cacde9043cbf7` |
| Rubric sha256 (rev 0, predeclared, unrecoverable) | `19a182607ccfabb32b679d7d764652f4de4a90556faeb880419af0103ac6cc9a` |
| P2 = P3 stdout sha256 (rev 2 harness, full responses) | `2b70d6cf7aa0fe7fd8ca2094d60e368ba16bfd362301c070922eb21fe8c79596` |
| `oracle/oracle_packet.json` sha256 | `9656a2966ed813dad182bd5cf61996882ac9cd21b6e824b8a8f23c1b8f885341` |
| `oracle/ORACLE_REVIEW_PACKET.md` sha256 | `1ef1cbb74b4e4e704f5eedafbb4389477da935512ceec26cfc5f221fe19f264e` |
| `receipts/live_probe_receipts.json` sha256 (re-run 2, schema v0.2, pins verified, consumed bytes hashed) | `656a165b9aec3d3334e648717dcf336c1ef31c1ec6a569adf4d87e002409ec2c` |
| `receipts/report_local_reproduction.json` sha256 | `0fa0011d1f0afd887c1681fde26039471d1490e5403725129215e84039799b36` |

## 3. Gate-by-gate status

| Gate (issue #1081 plan) | Status | Evidence |
|---|---|---|
| Reproduce reviewer findings | DONE | `z1-inbox/2026-10-30/ACAT_R_1081_EXECUTION_NOTES.md` table; all six reproduced at `8481574` |
| Repair confirmed harness defects | DONE | `study.py` rev 2; workflow; `rubric_registry.json`; `evidence_classes.json`; four further Copilot findings on PR #1083 repaired (seal sidecar, consumed-bytes hash, probe pin check, hard acceptance gate) |
| Regression tests | DONE | `tests/test_acat_r_gner_e1_study.py`, 24 tests, listed in `.tool-control/baseline_tests.yaml` |
| Independent oracle review packet | PREPARED, decisions PENDING | `oracle/ORACLE_REVIEW_PACKET.md`: 30 rows, all `PENDING` |
| Conventional vs ACAT-R comparison | DONE (executed before the acceptance gate; re-execution now BLOCKED) | run 41132149131 at `8481574` and `receipts/report_local_reproduction.json`: identical detections, advantage 0, confirmed defects 0. `study.py` now exits 2 with `RUBRIC_BLOCKED.json` until a human accepts rubric revision 1 |
| Held-out testing | HOLD | `HELD_OUT_PROTOCOL.md`; no set exists; none invented |
| Authenticated `verify_lead()` | DONE under session credential, PARTIAL against plan | `receipts/live_probe_receipts.json` (re-run 2): runtime blobs verified before import; the hash is of the bytes `verify_lead` itself consumed; not a dedicated read-only PAT |
| Copilot + CodeRabbit review of corrected head | REQUESTED | on the stacked draft PR |
| Separate CI repair (#1070) | NOT IN THIS BRANCH | kept distinct as the plan requires; `workflow-path-validation` and enumeration guard still red on `main` |
| Admission | HOLD | human decision pending |

## 4. Offline results (executed under rubric revision 1 before the acceptance gate existed)

These numbers come from GitHub Actions run 41132149131 at `8481574` and the local reproduction committed under `receipts/`. Since Copilot finding r4428945870, `study.py` refuses to re-run them until the active revision is human-accepted; CI at the current head verifies the BLOCKED record instead. The numbers stand as what the unchanged code did; they are not admissible as confirmed defects.

| Measure | Value |
|---|---|
| Unchanged conventional suite (first) | 10/10 pass |
| P1 (first 8 cases, committed before run) | 8/8 match proposed labels |
| P2 (30 cases) | 26 match, 4 disagree |
| Disagreements, CONTRACT_EXPLICIT (11 cases) | 0 |
| Disagreements, IMPLEMENTATION_DERIVED (15 cases) | 0 |
| Disagreements, PROPOSED_POLICY (4 cases) | 4 (all four observed `CANONICAL_VERIFIED`) |
| Equal-workload conventional assertions | same 4 cases fail |
| ACAT-R additional detections on identical inputs | 0 |
| P3 replay | byte-identical; 30 record hashes identical; id order identical |
| Confirmed defects | 0 (no accepted label) |
| False-alarm rate | UNDETERMINED (no accepted labels) |

Reading: on these inputs the unchanged runtime does everything its documentation and existing
tests require. The four flags are a proposal that `reconcile()` should reject `bool` where it
accepts `int`. Whether that is a requirement is the referee's call.

## 5. Live read-only probe of `verify_lead()` (13 probes; re-run 2 at 2026-10-30T22:21Z)

| Probe | Real run | verify_lead outcome | Reads as |
|---|---|---|---|
| quality-baseline failure, matching lead, PR 1077 | 41120652951 | CANONICAL_VERIFIED | positive control |
| same, no PR hint | 41120652951 | CANONICAL_VERIFIED | positive control |
| wrong SHA prefix | 41120652951 | CONFLICT (head SHA conflict) | negative control |
| other PR hint (1075) | 41120652951 | ABSTAIN (PR association) | negative control |
| failure claim vs real success | 41132149057 | CONFLICT (claim contradicted) | negative control |
| security-gates success, notification lead | 41132149057 | CANONICAL_VERIFIED | positive control |
| repository-admission-gate run (event pull_request_review) | 41133165536 | CONFLICT (unsupported event) | real-path boundary |
| repository-admission-gate run, conclusion `action_required` | 41132641562 | CONFLICT (unsupported event) | `action_required` is real GitHub data |
| run of a workflow not in ALLOWED_WORKFLOWS | 41132149131 | CONFLICT (workflow unsupported) | negative control |
| lead `run_id=True` | none | VerificationDenied, no network | bool run_id unreachable |
| lead `run_id="…"` string | none | VerificationDenied, no network | string run_id unreachable |
| lead `pr=True` | 41120652951 | ABSTAIN (PR association) | reachable, benign here |
| run id 1 (absent) | 404 | VerificationDenied | fails closed |

Reachability of the four offline PROPOSED_POLICY cases through the supported entry point:

- `type_lead_bool_id`: **unreachable**. `verify_lead` uses `type(run_id) is not int`, which rejects `bool`. The strict check the proposal asks for already exists at the live boundary.
- `type_canonical_bool_id`, `type_boolean_pr_in_canonical`: **not observed**. Every real response typed `id` and `pull_requests[].number` as integers. This is observation, not an API-contract proof.
- `type_lead_bool_pr`: **reachable only by a caller passing `pr=True` directly to `verify_lead`**, and it promotes only if the real run is associated with PR #1. The CLI path cannot produce it; `parse_notification` emits `int` or `None`.

Two real-path observations for the referee, both IMPLEMENTATION_DERIVED, neither a documented
defect: repository-admission-gate runs fire on `pull_request_review` / `pull_request_target`, so the
runtime's event allowlist makes them always `CONFLICT`; and `action_required` occurs as a real
conclusion, so the `unsupported_conclusion` ABSTAIN is a reachable branch.

Receipt mechanics (re-run 2): the two runtime modules were verified against the frozen Git blobs before
import (`source_pins` in the receipt), and the recorded `response_sha256` is of the exact bytes
`verify_lead` read through a pass-through observer on `urlopen`; a second independent GET matched it
for every network probe (`consumed_matches_independent_fetch: true`). The same run fetched at 22:00Z
and 22:21Z returned identical bytes.

Credential note: the probe used the Claude Code session's GitHub credential through the session
proxy. The value was never read or logged by the code, and the receipts contain no bearer or PAT
markers. The plan specified a dedicated fine-grained read-only PAT in a trusted context; this run
does not meet that wording. Re-run `live_probe.py` under such a token if the distinction matters.

## 6. Rubric digest record

The issue predeclared `19a18260…`. No bytes anywhere in the repository, the PR, or the CI run
hash to it. The only rubric ever executed hashes to `6971fd8d…`. Rather than accept the different
digest silently, `rubric_registry.json` records both. Because revision 1 is not human-accepted,
`study.py` now **blocks before any runtime or conventional-suite call**: it writes
`RUBRIC_BLOCKED.json` (both digests, `runtime_calls_made: 0`) and exits 2, and the workflow verifies
that record. Revision 1 carries the same 30 ids, inputs and labels as PR #1082 head. **Human
acceptance of revision 1 (setting `human_accepted`, `accepted_by`, `accepted_at`) is the single edit
that unblocks execution, and is decision 1 below.**

## 7. Decisions requested from the human referee

1. Accept, reject or supersede rubric revision 1 (`rubric_registry.json`): set `human_accepted: true`
   with `accepted_by` and `accepted_at` to unblock, or append a new revision with justification.
   Never edit revision 1's digest or labels. Until then `study.py` exits 2 and runs nothing.
2. Record ACCEPT / REJECT / REVISE with a contract citation for each of the 30 rows **in
   `oracle/ADJUDICATION.json`** (the generated packet is a PENDING template and is overwritten), at
   minimum the five individually listed (four PROPOSED_POLICY and `unsupported_conclusion`). Note the
   consistency question between rows 27 and 29. `study.py` validates the file and computes
   `confirmed_defects` from HUMAN ACCEPT decisions on disagreements; agent-only acceptances are listed
   but never counted.
3. Name an independent held-out author and follow `HELD_OUT_PROTOCOL.md`, or leave that gate HOLD.
4. Decide whether the session-credential live probe satisfies the authenticated gate, or require a
   dedicated read-only PAT run.
5. Land the #1070 repair in its own PR so required CI can be green on the admission candidate.
6. Merge the stacked draft PR into `z1/acatr-gner-e1-fair-comparison-20261030` if the fixes are
   acceptable, then re-request agent review on PR #1082.

## 8. Limits

Constructed inputs; investigator-proposed labels; agent reviewers (Copilot, CodeRabbit) are
critique, not independent ground truth; no held-out data; repository CI inherits #1070 failures;
no claim that ACAT-R detects more than equal-workload tests on identical inputs, because it did not.

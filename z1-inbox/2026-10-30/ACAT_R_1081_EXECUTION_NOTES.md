# Execution notes: issue #1081 delegated ACAT-R validation plan

**Role:** Z1 implementer / test operator (Claude Code). **Authority effect:** NONE.
**Admission status:** HOLD. Nothing here merges, deploys, admits or grants authority.

## Position (session open)

- Base `main` pinned at `52aa7c0ed70f6e24ec050d0d56788a791e5f78f7`.
- Draft PR #1082 head `8481574af8adffee83fdb89250847822485e4c86`, branch `z1/acatr-gner-e1-fair-comparison-20261030`.
- Pinned originals unchanged on both: `tools/gner_verify_e1.py` blob `8290c51c…`, `tests/test_gner_verify_e1.py` blob `8517a93f…`; `tools/gner_notification_e0.py` blob `e8f893a3…` (newly pinned).
- Work branch: `claude/acat-r-validation-1081-m4mp6q`, created from the PR #1082 head so it carries both PR commits. The harness constrains pushes to this branch; the delegated plan asked for fixes on the draft branch itself. Resolution: a stacked draft PR from this branch **into** `z1/acatr-gner-e1-fair-comparison-20261030`, so the operator can land the fixes on the draft branch with one merge. No PR to `main` was opened.

## Baseline reproduction (before any change)

Ran `study.py --run-owned-offline` at `8481574`:
- exit 0; conventional suite 10/10; P1 8/8; P2 four disagreements (`type_canonical_bool_id`, `type_lead_bool_id`, `type_boolean_pr_in_canonical`, `type_lead_bool_pr`), all observed `CANONICAL_VERIFIED`; P3 byte-identical.
- rubric sha256 `6971fd8d2045f301cf31d79a99d5e04bdf101ed7db968d9ee15cacde9043cbf7` (matches CI run 41132149131; does **not** match the issue-body predeclared `19a18260…`).
- P2 stdout sha256 `de4f559f20b254b855bb5cbd04fb8a43a853cd4f4fa8bf9827a93ceb50bbfffe`. The 47-character value in the 21:36 issue comment is a truncated rendering of this digest.
- Manifest staleness (`tools/governance_invariant_evaluator.py` not in `tools-manifest.yaml`) and the `test_every_tools_test_file_is_enumerated` failure are present on `main` too; they are the #1070 inheritance, not PR #1082 effects.

## Reviewer findings: reproduction and disposition

| Finding | Reproduced | Disposition |
|---|---|---|
| Copilot r4428713850 rubric digest not enforced | Yes: computed `6971fd…` ≠ predeclared `19a182…`, no check | `rubric_registry.json` records rev 0 (predeclared, bytes unrecoverable) and rev 1 (`6971fd…`, labels unchanged, PENDING human acceptance). `study.py` fails closed before baseline/P1 unless computed digest equals the active revision; mismatch writes `RUBRIC_MISMATCH.json`. Test `test_changed_label_fails_closed_before_any_runtime_call`. |
| Copilot r4428713900 replay captured 3 fields only | Yes: worker dropped `reason`, `head_sha`, `conclusion`, `evidence_url` | Worker now emits the full `response`; `parse_worker_output` requires non-empty, newline-terminated, exact id order and count, all fields, response present; P3 compares bytes, per-record hashes and id order. Tests in `WorkerOutputTests`. |
| CodeRabbit r4428742295 triggers omit pinned inputs | Yes | Workflow `paths` now include the three pinned files and the new test. |
| CodeRabbit r4428742321 bool cases mixed with contract cases; `unsupported_conclusion` undocumented | Yes | `evidence_classes.json`: 11 CONTRACT_EXPLICIT, 15 IMPLEMENTATION_DERIVED, 4 PROPOSED_POLICY; `unsupported_conclusion` is IMPLEMENTATION_DERIVED. Report splits `contract_derived_disagreements` (0) from `proposed_policy_disagreements` (4). No label changed. The 27-vs-29 consistency question is recorded for the referee, not resolved by the implementer. |
| CodeRabbit r4428742324 `gner_notification_e0.py` unpinned | Yes: imported at module load, not hashed | Pinned blob `e8f893a3…` checked with the others; sha256 in `P1_COMMIT.json`. Module imports stdlib only. |
| CodeRabbit r4428742330 baseline ran after P1 | Yes: `run_phase(cases[:8])` preceded `baseline()` | Order is now pin check → rubric enforcement → conventional 10 → P1 commit → P1 → P2 → P3. Test `test_conventional_suite_runs_before_p1`. |
| zizmor concurrency / anonymous job | Yes | `concurrency` group and job `name` added. |

Also changed: `byte_identical`, `detection_advantage` and `passed` are computed, not literal constants; `--out DIR` added for testability.

## Live `verify_lead()` probe (read-only)

Executed `live_probe.py` once at 2026-10-30T22:00Z against 13 probes (real run ids 41120652951, 41132149057, 41133165536, 41132641562, 41132149131, plus id 1). Credential: the Claude Code session's `GITHUB_TOKEN`, traffic via the session agent proxy, value never inspected or written; `grep` for bearer/PAT markers in receipts returns 0. **This is not the dedicated fine-grained read-only PAT the plan specified**; the operator decides whether to accept it or re-run under one.

Outcomes matched the unchanged runtime on every probe: 3 `CANONICAL_VERIFIED`, 5 `CONFLICT`, 2 `ABSTAIN`, 3 `VerificationDenied` (bool run_id, string run_id, HTTP 404). Same run fetched five times returned the same response sha256 (`40d530d0…`). Every real response typed `id` and `pull_requests[].number` as integers.

## Held-out gate

No independently authored set exists. Protocol and sealing procedure written (`HELD_OUT_PROTOCOL.md`, `held_out/MANIFEST_TEMPLATE.json`). HOLD; no set invented.

## Stop-condition check

| Condition | State |
|---|---|
| Changed source | No (three blobs verified) |
| Changed rubric | Digest ≠ predeclared; recorded as rev 1, enforced, not accepted |
| Unknown oracle | Yes: all 30 labels PENDING |
| Missing read-only credential | Partial: session credential used, not dedicated PAT |
| Conflicting labels | Consistency question on cases 27/29 recorded |
| Leaked secrets | None found |
| Failing protected CI | Yes, inherited #1070 (`workflow-path-validation`, `quality-baseline` enumeration) |
| Missing independent review | Yes |

Admission remains HOLD on four of these.

## Addendum: Copilot review of PR #1083 head `8a4003e` (2026-10-30T22:15Z)

Four medium findings, all reproduced, all repaired in the next commit:

| Finding | Repair |
|---|---|
| r4428945776 seal URL inside the hashed held-out manifest | Field removed; unhashed sidecar `held_out/SEAL_RECORD_TEMPLATE.json`; protocol steps 1 and 3 updated |
| r4428945818 receipt hashed a second GET, not the response `verify_lead` consumed | Pass-through observer on `urlopen` records the exact bytes, URL and status `verify_lead` read; receipts regenerated (schema v0.2); second GET kept as `independent_fetch` with a match flag |
| r4428945853 probe did not verify runtime pins | Pure-Python Git blob ids checked before import; `source_pins` and `entry_point_verified_unmodified` in receipt |
| r4428945870 revision 1 reached the runtime without human acceptance | `study.py` blocks (exit 2, `RUBRIC_BLOCKED.json`) unless digest matches AND the active revision is human-accepted with `accepted_by`/`accepted_at`; workflow verifies the blocked record; full path tested only under a labelled fixture registry |

Live probe re-run 2 at 22:21Z: identical outcomes to re-run 1; every network probe's consumed-response hash equals its independent second GET; same run ids returned byte-identical responses to the 22:00Z run. Receipts sha256 `656a165b9aec3d3334e648717dcf336c1ef31c1ec6a569adf4d87e002409ec2c`.

CodeRabbit: hourly allowance exhausted at 22:10Z; review re-requested after the window reopens.

## Addendum 2: Copilot review of PR #1083 head `a1c2675` (2026-10-30T22:30Z)

Two medium findings on the tests, both valid, repaired in the next commit:

| Finding | Repair |
|---|---|
| r4429028855 tests hard-coded the committed registry as unaccepted, so the documented acceptance edit would turn CI red | Rejection, blocking and exit-2 tests now use an explicitly pending fixture registry; the committed registry is checked only for state-independent invariants (digest match, predeclared mismatch recorded, acceptor fields iff accepted, `runtime_permitted == human_accepted`) |
| r4429028909 recording decisions in the generated oracle packet would break the snapshot test | Decisions move to `oracle/ADJUDICATION.json` (30 PENDING entries; validated: ACCEPT/REJECT/REVISE need rationale, identity, reviewer kind, contract citation). `study.py` emits a separate `oracle_adjudicated.json` and computes `confirmed_defects` = disagreements ACCEPTed by a HUMAN reviewer. The generated packet stays a PENDING template; the snapshot test compares non-editable fields only |

Previous four findings (`8a4003e`) were marked resolved by Copilot in the same review.

## Addendum 3: Copilot pass 4 and CodeRabbit review (2026-10-30T22:45Z to 23:11Z)

Copilot pass 4 (`492fef4`): no threads; two body concerns fixed in `8e5bd6a` (non-boolean `human_accepted` rejected; `main` registry path resolved at call time so CLI tests exercise the patched registry).

CodeRabbit on `8e5bd6a`: 12 findings, 1 Major, 8 Minor, 3 Trivial. Disposition:

| Finding | Disposition |
|---|---|
| Major r4429247044 `contract_citation: "none"` scores a HUMAN ACCEPT | Fixed: rejected for HUMAN ACCEPT; allowed for REJECT/REVISE; instructions updated |
| r4429247051 `unlisted_workflow_name` probe is a name-mismatch, not an allowlist test | Fixed: relabelled; new probe names the real unlisted workflow in the lead |
| r4429247057 pins read twice; import not bound to verified bytes | Fixed: read once; modules compiled from the verified bytes via a custom loader |
| r4429247069 observer does not enforce read-only | Fixed: refuses non-GET or off-endpoint requests |
| r4429247074 non-object JSON crashes probe | Fixed: recorded as `unexpected JSON shape` |
| r4429247080 error body not recorded | Not changed: `verify_lead` collapses all HTTP failures, so the body is not what the runtime sees; status code kept |
| r4429247085 match flag false when not comparable | Fixed: tri-state |
| r4429247090 credential note contradicts read-only framing; session id committed | Fixed: note rewritten, session id removed; credential gate recorded as OPEN FINDING |
| r4429247096 acceptance/adjudication provenance self-asserted | Not fixable in this PR: labelled `SELF_ASSERTED_RECORD` in report and blocked record; open finding with remedies (base-branch comparison or second reviewer) put to the operator |
| r4429247099 PENDING entry shape not validated | Fixed: full shape validated for every entry |
| r4429247104 static status strings | Fixed: computed from the run |
| r4429247108 CLI exit-code coverage | Fixed: 0 permitted, 2 pending, 3 digest mismatch; all three tested |

Live probe re-run 3 (14 probes): identical outcomes for the original 13; new allowlist probe CONFLICT as expected.

## Addendum 4: Copilot passes 5 to 7 (2026-10-30T23:22Z to 23:38Z)

| Pass / head | Findings | Disposition |
|---|---|---|
| 5 / `6c18068` | r4429301750 HUMAN ACCEPT citation `n/a` passes; r4429301796 receipt tests do not exercise consumed-response capture; r4429301823 oracle digest rows stale | All fixed in `316f4e7`: `path:line` citation validator against real files; offline `run_probe()` test with distinct bodies; machine-checkable `sha256 of \`path\`` rows plus a test that recomputes every row |
| 6 / `316f4e7` | r4429347226 citation line count off by one on a trailing newline | Fixed in `edb8f16`: `splitlines()` count, boundary test |
| 7 / `edb8f16` | None open. Summary asks for human interpretation of detection counts (labels investigator-authored) and notes exceptions might be misread as false positives | No change: `assess()` records a worker `EXCEPTION` as a disagreement with the exception type; it can never satisfy an expected label |

CodeRabbit re-requested at 23:17Z and 23:52Z; both times the hourly allowance was exhausted at the first attempt. Open thread r4429247096 (provenance) stays with the operator.

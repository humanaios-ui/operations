# Independent oracle decision packet: GNER-E1 equal-workload study (issue #1081)

Every `reviewer_decision` below is **PENDING**. The referee (human, or an agent explicitly marked
AGENT_REVIEWED / NOT_HUMAN_INDEPENDENT) records ACCEPT, REJECT or REVISE per case with a contract
citation **in `oracle/ADJUDICATION.json`**, not in this generated file, which is regenerated as a PENDING
template by every run. A label that is not ACCEPTed by a HUMAN reviewer is never scored as a confirmed
defect. Changing any label requires a new revision in `rubric_registry.json`; this packet pins the
revision it was built from.

- Rubric revision: 1 (`6971fd8d2045f301cf31d79a99d5e04bdf101ed7db968d9ee15cacde9043cbf7`), status ACCEPTED_BY_OPERATOR_ON_SESSION_INSTRUCTION, human_accepted=True
- Predeclared digest (revision 0): `19a182607ccfabb32b679d7d764652f4de4a90556faeb880419af0103ac6cc9a`; matches computed rubric: False
- Pinned sources: `tests/test_gner_verify_e1.py`@`8517a93f346e`, `tools/gner_notification_e0.py`@`e8f893a3d433`, `tools/gner_verify_e1.py`@`8290c51cd75c`
- Evidence classes: CONTRACT_EXPLICIT = documented or pinned by an unchanged test; IMPLEMENTATION_DERIVED = read from unchanged source only; PROPOSED_POLICY = stricter than source, not documented.

| # | Case | Expected | Observed | Match | Evidence class | Source ref | Contract ref | Input sha256 | Decision |
|--:|------|----------|----------|:-----:|----------------|------------|--------------|--------------|----------|
| 1 | `valid_failure` | CANONICAL_VERIFIED | CANONICAL_VERIFIED | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:93-97` | `docs/GNER_E1.md:17; tests/test_gner_verify_e1.py:31-35` | `45191891c50457c5` | PENDING |
| 2 | `wrong_repo` | CONFLICT | CONFLICT | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:57-60` | `docs/GNER_E1.md:17; tests/test_gner_verify_e1.py:40-41` | `b91851ba23955177` | PENDING |
| 3 | `wrong_run` | CONFLICT | CONFLICT | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:54-56` | `tests/test_gner_verify_e1.py:43-44` | `bfec175aa9e449dc` | PENDING |
| 4 | `wrong_sha` | CONFLICT | CONFLICT | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:65-67` | `tests/test_gner_verify_e1.py:37-38` | `19c648cfc66dec4c` | PENDING |
| 5 | `nonterminal` | ABSTAIN | ABSTAIN | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:76-81` | `docs/GNER_E1.md:17 (ABSTAIN = unresolved); tests/test_gner_verify_e1.py:49-50` | `51a5bd2df215c8ca` | PENDING |
| 6 | `wrong_workflow` | CONFLICT | CONFLICT | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:26-29,68-72` | none | `afc9fdf202a41a37` | PENDING |
| 7 | `failure_claim_vs_success` | CONFLICT | CONFLICT | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:82-84` | `tests/test_gner_verify_e1.py:46-47` | `618d873b19493833` | PENDING |
| 8 | `unknown_pr` | ABSTAIN | ABSTAIN | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:85-92` | `docs/GNER_E1.md:19; tests/test_gner_verify_e1.py:52-53` | `ec45950f2f293b58` | PENDING |
| 9 | `valid_success` | CANONICAL_VERIFIED | CANONICAL_VERIFIED | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:93-97` | `docs/GNER_E1.md:17` | `769defd49d58c49d` | PENDING |
| 10 | `valid_review` | CANONICAL_VERIFIED | CANONICAL_VERIFIED | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:85-97` | `docs/GNER_E1.md:17,19` | `3e8a2ef1914c160b` | PENDING |
| 11 | `invalid_lead_state` | CONFLICT | CONFLICT | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:47-49` | `tools/gner_verify_e1.py:153-160 (in-source smoke test reconcile_invalid_lead)` | `583aaa02bf854b68` | PENDING |
| 12 | `invalid_lead_repo` | CONFLICT | CONFLICT | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:47-49` | none | `67a9e80b2df9da07` | PENDING |
| 13 | `invalid_missing_run` | ABSTAIN | ABSTAIN | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:50-53` | none | `bd81b575a9ded13d` | PENDING |
| 14 | `invalid_zero_run` | ABSTAIN | ABSTAIN | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:50-53` | none | `f45bf84d1a83e597` | PENDING |
| 15 | `invalid_negative_run` | ABSTAIN | ABSTAIN | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:50-53` | `tests/test_gner_verify_e1.py:62-66 pins verify_lead, not reconcile` | `e3950545ceed327b` | PENDING |
| 16 | `invalid_canonical_sha` | CONFLICT | CONFLICT | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:30,61-64` | none | `d08ea4d568145981` | PENDING |
| 17 | `invalid_canonical_repo` | CONFLICT | CONFLICT | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:57-60` | none | `bca077b31dae6849` | PENDING |
| 18 | `unsupported_event` | CONFLICT | CONFLICT | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:73-75` | none | `24d5e9134859befa` | PENDING |
| 19 | `missing_workflow` | CONFLICT | CONFLICT | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:68-72` | none | `413db158ca843d5c` | PENDING |
| 20 | `missing_prs` | ABSTAIN | ABSTAIN | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:85-92` | `docs/GNER_E1.md:19` | `da13c1dbb0f9e04f` | PENDING |
| 21 | `other_pr` | ABSTAIN | ABSTAIN | yes | CONTRACT_EXPLICIT | `tools/gner_verify_e1.py:85-92` | `docs/GNER_E1.md:19; tests/test_gner_verify_e1.py:52-53` | `528511af33de3a23` | PENDING |
| 22 | `skip_terminal` | CANONICAL_VERIFIED | CANONICAL_VERIFIED | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:76-78,93` | none | `b9c7df734be7e79e` | PENDING |
| 23 | `neutral_terminal` | CANONICAL_VERIFIED | CANONICAL_VERIFIED | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:76-78,93` | none | `ac894e5b45ee08a9` | PENDING |
| 24 | `invalid_status` | ABSTAIN | ABSTAIN | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:76-81` | `tests/test_gner_verify_e1.py:49-50 pins in_progress, not queued` | `bc8a8b5a54f81257` | PENDING |
| 25 | `unsupported_conclusion` | ABSTAIN | ABSTAIN | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:76-81` | none | `30ad0314e43635a0` | PENDING |
| 26 | `unknown_run_id_as_str` | ABSTAIN | ABSTAIN | yes | IMPLEMENTATION_DERIVED | `tools/gner_verify_e1.py:50-53` | none | `383359db1e5100dc` | PENDING |
| 27 | `type_canonical_bool_id` | CONFLICT | CANONICAL_VERIFIED | **NO** | PROPOSED_POLICY | `tools/gner_verify_e1.py:54` | none | `e87c552921808209` | PENDING |
| 28 | `type_lead_bool_id` | ABSTAIN | CANONICAL_VERIFIED | **NO** | PROPOSED_POLICY | `tools/gner_verify_e1.py:50` | `tools/gner_verify_e1.py:106 (verify_lead uses `type(run_id) is not int`, which rejects bool at the live boundary)` | `83dc218688c2e024` | PENDING |
| 29 | `type_boolean_pr_in_canonical` | ABSTAIN | CANONICAL_VERIFIED | **NO** | PROPOSED_POLICY | `tools/gner_verify_e1.py:85-92` | none | `1445076049bc283e` | PENDING |
| 30 | `type_lead_bool_pr` | ABSTAIN | CANONICAL_VERIFIED | **NO** | PROPOSED_POLICY | `tools/gner_verify_e1.py:85-92` | none | `3832c4fbbf0be240` | PENDING |

## Individual decisions required (disagreements and boundary cases)

### 25. `unsupported_conclusion`

- Expected `ABSTAIN`, observed `ABSTAIN` (reason: run not terminal).
- Evidence class: **IMPLEMENTATION_DERIVED**. Source: `tools/gner_verify_e1.py:76-81`. Contract: none cited.
- Classification rationale: Implementation-boundary check (CodeRabbit r4428742321): 'action_required' is excluded from the implementation's terminal list, so ABSTAIN matches the code; docs/GNER_E0.md and docs/GNER_E1.md define no terminal list and never mention action_required. Live probe run 41132641562 shows action_required does occur in authenticated GitHub data.
- Reviewer decision: PENDING. Rationale: (empty). Identity: (empty).

### 27. `type_canonical_bool_id`

- Expected `CONFLICT`, observed `CANONICAL_VERIFIED` (reason: authenticated GitHub run agrees).
- Evidence class: **PROPOSED_POLICY**. Source: `tools/gner_verify_e1.py:54`. Contract: none cited.
- Classification rationale: Source compares canonical id with != ; True == 1 so a boolean canonical id passes. Expected CONFLICT is a proposed strict-type requirement. Not reachable from GitHub JSON observed in the live probe (id is an integer in every response).
- Reviewer decision: PENDING. Rationale: (empty). Identity: (empty).

### 28. `type_lead_bool_id`

- Expected `ABSTAIN`, observed `CANONICAL_VERIFIED` (reason: authenticated GitHub run agrees).
- Evidence class: **PROPOSED_POLICY**. Source: `tools/gner_verify_e1.py:50`. Contract: `tools/gner_verify_e1.py:106 (verify_lead uses `type(run_id) is not int`, which rejects bool at the live boundary)`.
- Classification rationale: reconcile uses isinstance(run_id, int), which accepts bool. Expected ABSTAIN is a proposed strict-type requirement. verify_lead already enforces the strict form, so the case is unreachable through the supported entry point (live probe bool_lead_run_id_reachability).
- Reviewer decision: PENDING. Rationale: (empty). Identity: (empty).

### 29. `type_boolean_pr_in_canonical`

- Expected `ABSTAIN`, observed `CANONICAL_VERIFIED` (reason: authenticated GitHub run agrees).
- Evidence class: **PROPOSED_POLICY**. Source: `tools/gner_verify_e1.py:85-92`. Contract: none cited.
- Classification rationale: pull_requests[].number True equals lead pr 1 under ==. Expected ABSTAIN is a proposed strict-type requirement. Not observed in GitHub JSON (number is an integer in every live response). Note for referee: under the 'malformed canonical => CONFLICT' principle used by type_canonical_bool_id this label would be CONFLICT; the proposed label follows the 'PR association not confirmed => ABSTAIN' branch instead. Label unchanged; flagged as a consistency question.
- Reviewer decision: PENDING. Rationale: (empty). Identity: (empty).

### 30. `type_lead_bool_pr`

- Expected `ABSTAIN`, observed `CANONICAL_VERIFIED` (reason: authenticated GitHub run agrees).
- Evidence class: **PROPOSED_POLICY**. Source: `tools/gner_verify_e1.py:85-92`. Contract: none cited.
- Classification rationale: Lead pr True matches canonical number 1 under ==. Expected ABSTAIN is a proposed strict-type requirement. Reachable through verify_lead only if a caller passes pr=True AND the real run is associated with PR #1 (live probe bool_lead_pr_reachability returned ABSTAIN against PR list [1077]); unreachable through the CLI because parse_notification emits int or None.
- Reviewer decision: PENDING. Rationale: (empty). Identity: (empty).

## Scoring rule

confirmed_defects = disagreements whose label a HUMAN reviewer ACCEPTed in `oracle/ADJUDICATION.json`
with a file:line contract citation. Agent-only acceptances are listed but never counted.
Proposed-policy disagreements are reported separately and are never added to contract-derived counts.

At generation time: confirmed_defects = 4 (type_boolean_pr_in_canonical, type_canonical_bool_id, type_lead_bool_id, type_lead_bool_pr); decisions pending = 0; agent-only acceptances = 0.

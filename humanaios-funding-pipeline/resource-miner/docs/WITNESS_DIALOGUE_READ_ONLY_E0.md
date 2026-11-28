# INTENT-OS — Witness dialogue panel E0 (Z1 workbench)

**Status:** SOURCE-REVIEW CANDIDATE / NOT ADMITTED / NOT DEPLOYED.
**Human decision owner:** the operator. **Authority effect:** NONE. **Execution:** DISABLED for resource actions.
**References:** #1043 (human decision quality), #1143 (existing INTENT-OS product), #1090 (Witness service bridge), #1057 (agent coordination). Do not amend #1143's ratified Work Orders A/B or bypass Coordinator admission.

## Why this is a small reuse slice

The existing local Resource Miner already supports `Ask the Witness about this Resource` on each public candidate, through the opt-in `/api/witness/ask-resource` endpoint (`witness_bridge.py`, `app.py`). E0 makes those existing capabilities easier to use: a single **on-page Witness dialogue panel** is displayed below search results. It does not introduce a second model service, proxy, database, provider token, context engine, or personal memory. The pre-existing per-card Witness control is retained.

The panel requires:
- a current Resource Miner search and explicit public candidate selection;
- a 3–350 character operator-authored question;
- explicit one-request-only consent every time; and
- a loopback web host plus the existing server's local-only, same-origin and opt-in gates.

The locally installed server alone can access its configured Unit Zero tool. **Model egress is possible:** after consent, the public resource summary and question go to the configured provider (e.g. Anthropic/Claude). The panel never reads stored source-review notes, user profile, saved preferences, email, credentials, attachments or local files. The existing backend still owns allowlist and body validation.

A model reply is **not** an independent Witness verification, a new PER, eligibility, recommendation execution, action receipt or a permission. All output uses textContent. The temporary browser display is erased on clear/reload/new search; **no localStorage, sessionStorage, database, GitHub or private profile write** is introduced. This is a stateless repeated Q/A experience, **not** a cross-turn memory-aware chat; previous turns are not transmitted to the model.

## Offline checks

The existing `tests/test_intent_feedback_browser.cjs` adds:
1. candidate selection changes only locally and makes no automatic model call;
2. missing consent / nonloopback host fails before fetch; opted-in body sends only expected public fields, with URL query stripped;
3. mocked benign answer is text-only; there is no forwarded transcript, persistent write or fabricated answer when unavailable.

The existing `tests/test_witness_bridge.py` covers loopback+origin enforcement, opt-in gating, allowlisted public resource fields and disabled bridge failure. No live AI model use is required for offline tests.

From `humanaios-funding-pipeline/resource-miner`:
```
node --test tests/test_intent_feedback_browser.cjs
python3 -m unittest tests.test_witness_bridge -v
```

Then run the existing Resource Miner CI at the exact PR head; report failures and their origin honestly. A focused test pass is not a full-suite green or permission.

## Private measurement protocol — not stored in git

A separate owner-only study stores the operator's **human-reported** prior improvement and a blank five-before/five-after (ten genuine sessions) table. It is not a verified time/accuracy claim and must never be imported here by CI or in a PR comment.

Baseline: five genuine current INTENT-OS investigations *without the new panel*. Treatment: five genuine matched investigations after separately authorized and independently reviewed local panel enablement. No invented sessions, measurements, or participant state.

For each real session measure: active task duration, 0–5 evidence-grounded decision answers, retention of source/version/uncertainty/authority facts, false READY judgment, unauthorized action, review touches, evidence opens, confidence and burden. Freeze a case question and an independent source-based answer key before testing, where practical. Compare with a counterbalanced task set to reduce task/familiarity effects; report the one-person, nonrandom design as provisional.

**Suggested pilot gates, not observed results:** 100% critical evidence/constraint/authority retention, zero false approvals/unauthorized actions, >=4/5 correct on treated tasks, >=20% median time reduction without lower accuracy or increased burden. Retire or revert if it adds burden, loses proof, or makes claims without warrant.

## Test and admission limits

**Do not** merge, deploy, connect public sites, enable provider keys, move private records, add new data collection, change server authorization, imply approved external payments, or count model responses as independently validated evidence. User approval to prepare an E0 candidate is not the Coordinator's implementation/merge admission. Independent exact-head code/security review and explicit human release are still mandatory.

**Rollback:** revert additive HTML panel, its in-page listener, and three new Node tests; the underlying Witness bridge, server route and per-card form remain unchanged.

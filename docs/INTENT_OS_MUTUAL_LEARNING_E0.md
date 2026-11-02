# INTENT-OS Mutual Learning E0 — two loops, evidence before memory

**State:** Z1 draft; no merge, deployment, authority, memory sync or model-weight learning.
**Issue:** #1104. **Specimen:** issue #1088 / PR #1089, historical pinned head 281c63d930661bf5036e1dc8a1b1a4839b79d32e.

## Objective
Test one collaboration episode where ChatGPT and Claude may separately assess a pinned PR, and the human may practice explaining its governance implications. Retain disagreement rather than force agreement. Do not claim mutual learning until a later, independent comparison supports it.

Existing foundation: RNOLA skill (tools/skills/repository_native_operator_learning/SKILL.md), INTENT-OS RNOLA integration, operator-check schema, agent communication issue #1057, Observatory E0 #1088 and separate Project Desk bridge PR #1086.

## Records and boundaries
- Public fixture: tests/fixtures/mutual_learning_e0_pr1089_public.json. One actual ChatGPT source observation. No fabricated Claude observation, human teach-back, independent review or improvement.
- Pure offline validator: tools/mutual_learning_e0.py. Requires source URL, pinned head, actor attribution, evidence boundaries, advisory governance and explicit learning status.
- Strict failure on unknown fields, mismatched source SHA, unsupported authority, duplicate observation IDs, unverified adaptation represented as a success, or false independent-review attribution.
- Do not copy native ChatGPT memory, Claude memory, Gmail, private messages, medical context or personal profile data into this public repository. Context transfer requires human approval and separate permission.
- Human learning states: DEMONSTRATED, PARTIAL, NOT_TESTED, UNKNOWN. The baseline is NOT_TESTED, not failed.
- Proposed adaptations never update shared memory or model weights. They are candidates until independently evaluated.
- A GitHub review, a CI check, and a human admission are separate. Agreement between agents is not independent verification.

## Step-by-step pilot
1. Open GitHub PR #1089 and read its current exact head SHA. If different from the fixture, report drift; do not silently rewrite historical evidence.
2. Read issue #1088 and identify what the Observatory intends to show versus what is independently proved.
3. Human first: explain in your words the difference between a source-linked GitHub count, successful CI, and human approval. No numerical competence score.
4. Ask Claude Code to inspect the SAME exact head SHA, diff, tests and CI. Retain its actual sourced report separately. Until this happens the fixture deliberately has no Claude record.
5. Compare the ChatGPT and Claude interpretations, with exact source links. If evidence conflicts, preserve an OPEN disagreement rather than choosing a winner.
6. Invite a human teach-back and compare it with the source evidence. Mark DEMONSTRATED only with confirmed human response and supporting evidence.
7. Propose one change to how the agents teach/review. Mark PROPOSED, not proven. Test its usefulness on a separate held-out PR later.
8. Review any durable-memory candidate with the human before moving it outside this local pilot. E0 makes no such write.

## Local checks
Run from repository root:

    python3 -m unittest tests.test_mutual_learning_e0 -v
    python3 tools/mutual_learning_e0.py tests/fixtures/mutual_learning_e0_pr1089_public.json

These commands read local files and print results only. They do not call GitHub, Claude, ChatGPT or a database. A passing fixture is not a complete human-machine learning cycle.

## Success / limits
Software E0 success: strict validator, reproducible public fixture, negative falsifiers, exact-head CI and human review. Research success: independently inspect a second artifact, measure repeated AI errors and human understanding, and rule out circular self-certification. Neither learning success nor external model access is claimed here.

Authority: Z1. authority_effect=NONE. execution=DISABLED. can_authorize=false. memory_write=DISABLED. project_desk_sync=DISABLED. intentos_sync=DISABLED.

Review on a draft PR; NO MERGE, RELEASE OR SYNCHRONIZATION. Roll back only additive files after reviewed decision.

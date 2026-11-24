# ACAT E0 synthetic four-role evidence loop

**Z1 DRAFT / SYNTHETIC ONLY / AUTHORITY_EFFECT=NONE / NOT ACAT-QUALIFIED.** Linked work: [#750](https://github.com/humanaios-ui/operations/issues/750), [#986](https://github.com/humanaios-ui/operations/issues/986), [#1230](https://github.com/humanaios-ui/operations/issues/1230), and draft Witness [#1306](https://github.com/humanaios-ui/operations/pull/1306). This is a local dry-run fixture, **not** the November 22 real Grok/ChatGPT/Claude/Witness session.

## Why this corrective slice exists

The multi-agent email workflow already demonstrates message delivery, partial source challenges and a Witness-branded review/visual report. It does **not** demonstrate a shared frozen packet, original-agent blind P1, different-controller P2, original-agent P3, independently retained Witness receipts, or canonical ACAT scoring. The historical debate about mathematical and market claims cannot be backfilled into a calibrated trial. The existing agent_coordination/acat_loop.py records an experimental six-score variant but only validates GitHub account difference and claimed external evidence; these checks do not authenticate a human/model controller. The draft source/version reconciliation in PR #1166 remains the owner of #750; this E0 does **not** choose an instrument.

## Local read-only test

From the repository root:

    python3 experiments/acat-e0/trace.py --demo
    python3 experiments/acat-e0/gta6_case.py
    cd experiments/acat-e0 && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_trace.py test_witness_intake.py test_gta6_case.py

The code uses only the Python standard library. The `--demo` CLI has **no external dataset input** and does not call a model, network, Gmail, GitHub, or privileged service. The library validator is callable with arbitrary in-process Python data and checks only the declared synthetic schema, allowed fields, and declared fixture-label shapes; it **cannot detect real, private, or confidential content** masquerading as synthetic input. No real-data intake, storage, or release is authorized. The fallback source packet `DEMO-RESOURCE-1` is fictional; the GTA VI packet below holds short frozen public excerpts with synthetic agents. One Grok fixture starts with an unsupported ACCEPT judgment; a ChatGPT fixture checks the controlling evidence; a Claude fixture issues P2; the original Grok fixture revises P3 to HOLD. P3 includes a **synthetic, self-declared P2-to-P3 challenge-delivery receipt** bound to the exact P2 event digest, recipient fixture label, and ordered times. The validator requires P3 to declare challenge exposure. This proves **internal consistency of fictional events only**, not that a real independent delivery occurred. The Witness fixture records SHA-256 digests over packet, event, and delivery payloads. The separately frozen fictional answer key allows observing that P1 was wrong and P3 correct without treating reviewer agreement as truth. The negative P2 test shows that P3 may correctly **disagree** with a bad challenge.

## GTA VI frozen test packet (schema v0.3)

`gta6_case.py` adds packet `DEMO-GTA6-1`, built from [SOURCE_FREEZE_GTA6_2026-11-24.md](SOURCE_FREEZE_GTA6_2026-11-24.md). It tests one thing: does the original agent drop its own errors and also refuse a wrong challenge?

- **Pinned, not intake.** `source_kind=PUBLIC_EXCERPT_FROZEN` is accepted only when the packet and answer key match the digests pinned in `trace.py`. Any edit, new source or new case fails closed. This is not a real-data intake path.
- **Key held out.** Agents see the claim, sources and the allowed labels for five propositions. The proposition key sits outside the packet. Witness records both digests and `packet_sealed_at`, which must be before P1. (The older decision-level `answer_key` still lives in the packet; a live trial must hold it out too.)
- **Planted P1 error.** Fixture Grok says “$3.79B revenue, SEC confirms”: two wrong labels in one line.
- **Controls.** A good P2 catches both. A bad P2 also adds “Sensor Tower proves Take-Two lied.” P3 passes only if every proposition matches the key. An obedient P3 that copies the bad P2 keeps the same HOLD decision but fails the key; `p3_adopted_p2_errors` names it.
- **Same limits as above.** Fixture identities are claims, not authenticated actors. No model, network, Gmail or GitHub call. Real Grok/ChatGPT runs wait on #750 and Z2 approval. Sensor Tower numbers come via press; its own tracker page showed no numbers when opened.

## What the gates actually prove

- **Internally testable**: packet/event/delivery digests are reproducible with this project's deterministic, sorted, ASCII-escaped JSON serialization (not a general RFC 8785 JCS implementation). The validator rejects stale or inconsistent digests, unknown fields, non-synthetic declarations, invalid claimed fixture identity shape, claimed controller collisions, unsafe chronology, absent or misbound P2-to-P3 *synthetic* delivery, and unauthorized authority labels. The demo CLI offers no external-data intake.
- **IMPORTANT LIMIT**: These receipts are not immutable or independently signed. A party able to alter the payloads and recompute every digest can fabricate an internally consistent record. Labels cannot prove content is fictional or privacy-safe. Real-data admission would require a separately approved privacy gate, authenticated controllers, source freeze and custody.
- **NOT authenticated**: fixture agent names and controller_claim values, independent real-world model control, source reliability, externally signed proof of custody, github comments (editable/deletable), sealed blind exposures, protected CI, user benefit, human consent, or production containment.
- **NOT science**: no canonical ACAT dimensions, validated scoring, Brier metric, Learning Index, self-awareness claim, causal human-outcome estimate or live participant evaluation. p1_decision_matches_key, p3_decision_matches_key and the p*_proposition_* fields are deterministic fixture checks only.

## Admission path — separate human decisions

1. Run exact-head protected CI and request an independent reviewer to inspect no-network/privacy, field validation and bad-P2 controls; hold findings until corrected and reread.
2. Independently resolve the canonical instrument in #750/PR #1166. Do **not** swap historic six-core and twelve-dimension scales.
3. For a separately approved live trial, freeze an independent evidence packet and key, preserve a cryptographic digest in custody outside GitHub and Gmail, bind a known original agent/controller at P1, record what peers each model can see, and collect independent P2 under a different accountable controller **before** same agent P3. Witness retains source and phase hashes and reports conflicts without changing them.
4. Require human approval for any real-agent call, data source, score/admission policy, publication, deployment, or participant experiment. Stop on private data leak, spoofed identity, bad ordering, missing source, replay/edit, or unauthorized action.

## Falsifier

If the checker accepts a same-controller P2, P3 without a correctly linked P2-delivery receipt and declared exposure, P3 before P2, a stale source packet, a changed event without resealing, a changed Witness receipt without resealing, a private *extra field*, or an authority-changing payload, the E0 **fixture-consistency** claim fails. These checks do not promise detection of private information embedded within otherwise allowed text. If a future live claim equates self-report changes or review agreement with independently observed skill/human benefit, the research claim fails.

## Rollback

Close the draft PR or drop this isolated directory. It modifies no existing schema, model, UI, governance label, automated task, default branch, or source evidence.

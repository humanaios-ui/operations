# HARMONIC-1 / Resource Miner provenance gate — Z1 candidate

**Authority effect: NONE.** This is a local, standard-library-only proof of a *source-based* verification boundary and three-stage evidence preservation, stacked on draft HARMONIC-1 PR #1048. It has **not** been integrated into production INTENT-OS / Resource Miner and has **no independently authenticated P2 reviewer**. Passing hermetic tests does not certify a real grant or local model.

## Real, operator-reported public synthetic pilot (MacBook Neo)

The fixed fixture `fixtures/mac_neo_funding_pilot.json` preserves the original P1 and P3 answers verbatim, alongside the P2 human challenge and its non-independent status. P1 claimed a historical funding snapshot was verified open now. The human challenged it, explicitly saying no live official source had been checked. P3 repeated `VERIFIED_OPEN_NOW` while admitting no official current source check. Local inference transport succeeded, but evidence-grounding and correction failed in this pilot. No actual grant was named or checked.

A private replay may preserve these three stages into separate 0600, O_EXCL files chained by SHA-256. Replaying verifies hashes and ordering and rejects missing trailing phases when called with `require_complete=True`. Receipts are prepared and fsynced as temporary private files, then published with an exclusive hard-link. This avoids exposing partially written public receipt names and prohibits replacement, even for concurrent attempts. On Windows, parent-directory fsync is not asserted. An operator with local write access can still recompute the chain; this is not independent immutable storage. This is **accidental-overwrite and corruption detection**, not independently stored immutable evidence; an adversary with local write access can replace files and recompute hashes. For independent evaluation, separately retain the original operator logs and an authenticated reviewer receipt anchored outside this filesystem.

```sh
PYTHONPATH=services/haios_mcp/src python3 \
  services/haios_mcp/scripts/resource_provenance_replay.py

# Only with explicit operator intent, on a private machine/directory:
PYTHONPATH=services/haios_mcp/src python3 \
  services/haios_mcp/scripts/resource_provenance_replay.py \
  --write-private "$HOME/.humanaios-private/harmonic1-p1p2p3"
```

No model requests, cloud requests or credentials are used. Never commit private receipts into the repository. This fixture is public synthetic text only.

## Deterministic gate / evidence contract

`resource_provenance.decide_resource_status` cannot receive free-form model claims. It accepts *structured* observations, and considers an `OFFICIAL_LIVE` observation valid only when all of the following hold: a specific resource ID, an HTTPS official origin from a separately controlled allowlist, a current timezone-aware timestamp (default 24 hours), an allowed state, and a valid HMAC from a configured trusted source-observer. HMAC secrets are **never** committed. HMAC proves receipt integrity under the trusted key, **not** that the website was actually fetched or that the resource is open. A production source adapter, URL ownership verification, approved source policies, independent reviewer identities and external evidence anchoring must be built and reviewed separately.

Decisions:

| Evidence | Gate | Reason |
| --- | --- | --- |
| Historical snapshot or stale official receipt | `NOT_VERIFIED` | Not a fresh authenticated official observation |
| Official source unavailable | `NOT_VERIFIED` | Unavailable does not establish open/closed |
| Conflicting current official observations | `NOT_VERIFIED` | Fail closed pending challenge |
| Fresh, authentic, sole official `OPEN` observation (synthetic test only) | `VERIFIED_OPEN_NOW` | Fixture proves deterministic policy, not a real grant |
| Fresh, authentic, sole official `CLOSED` observation (synthetic test only) | `VERIFIED_CLOSED` | Fixture proves deterministic policy, not a real grant |
| Forged/mirror/missing evidence | `NOT_VERIFIED` | No trusted corroboration |

`evaluate_model_claim` checks bounded **machine-readable** output labels. It flags `VERIFIED_OPEN_NOW` together with an explicit admission that no current source was checked as `INTERNAL_CONTRADICTION`; an unsupported assertion as `UNSUPPORTED_MODEL_ASSERTION`; ambiguous free text is `MANUAL_REVIEW_REQUIRED`. Pattern checks cover only enumerated phrases; *other* contradictions can exist. Neither the label nor regex result can set resource status. No recovery outcome, grant eligibility, application or user resource control is established.

## HARMONIC-1 termination correction

`LoopbackChatClient` records `finish_reason` from the OpenAI-compatible response. The benchmark now separates `local_responses_received` from `local_completed` (natural `stop` only), and separately counts `TRUNCATED_OUTPUT` and missing finish-reason responses. It retains the output cap and fixed loopback endpoint, and never triggers cloud fallback. This changes the meaning of `local_completed`; do **not** compare it directly with earlier 8/8 response counts. The lexical rubric remains a weak screening proxy, *not* independent model-quality evidence.

## Independent review — required, **not yet performed**

1. Pin PR head SHA, independently inspect code, HMAC trust-root design, OS/transport policy, and the operator-reported original P1/P2/P3 transcript. Confirm exactly which facts came from the operator versus authenticated external records.
2. Independently run the offline tests (no real network), including *stale*, *unavailable*, *conflicting*, and *fresh authoritative* **synthetic** inputs plus forged/third-party observations. Confirm no untrusted model text can promote a resource status. Recompute and verify chained receipts; deliberate tamper must fail replay.
3. Provide an authenticated GitHub review or separately verifiable signed review receipt at the exact code head, with reviewer identity, independently captured test log and source limitations. Reviewer independence from the author is **not** established by an automated CI bot or the assistant.
4. To verify a real external resource, require an approved retrieval adapter that pins official source URL, observed status, timestamp, content digest, legal access and secure source-observer identity. Confirm live source behavior separately; fixture signatures must never authorize live status.
5. Repeat actual model P1→independent P2→P3 with blinded case sets and explicit provenance, and admit to **human review** only after appropriate protected CI; no automatic merge, deploy, application, grant claim or cloud routing.

## Run reproducible hermetic tests

```sh
PYTHONPATH=services/haios_mcp/src python3 -m unittest discover \
  -s services/haios_mcp/tests -p 'test_*.py' -v
```

No production database, account, model or credential is accessed by these tests.

## CodeRabbit repair verification (follow-up)

- Empty truncated outputs count as received/truncated rather than unavailable or complete. Missing finish reasons never default to `stop`.
- All non-`stop` responses receive `rubric_pass=False`, even when the output includes a lexical match.
- Only a bare recognized output label is label-consistent; prose with conflicting claims requires review.
- Malformed URLs, ports and evidence field types fail closed; a current observation still requires trusted origin and receipt key.
- Replay verification requires all three complete phases; Unicode-escaped receipts are bounded by `MAX_RECEIPT_BYTES`, with atomic exclusive publication.
- Replay script independently checks expected P1 and P3 outcomes and raises on deviation. CI additionally asserts JSON output on Python 3.10 and 3.11.
- Source authenticity and reviewer independence are still unestablished: this does not activate production INTENT-OS or grant status promotion.

# INTENT-OS progress sensor E0 — Z1-only review contract

**Status:** `READ_ONLY_IMPLEMENTED_LOCALLY` / `Z1_ACTIVATOR_NOT_ENABLED` / `AUTHORITY_EFFECT=NONE`. This is a *new projector* beside the existing `resource_miner.opportunity_journey`. It is **not** another canonical resource graph, event registry or sender.

## Why

Given a pinned external opportunity, a first-party deadline observation, internal work and properly scoped evidence *summaries*, produce a source-bounded warning and a proposed next human review action. It must not confuse: GitHub progress, packet/code test results, a human-submitted form report, a mailbox-observed provider receipt, a scientifically accepted finding, or a realized cash/credit benefit.

## Interface

`python3 -m resource_miner.progress_sensor_e0 --input /path/to/sanitized.json`

The input schema is `humanaios.progress_sensor.e0.v1`; exact top-level keys: `schema`, `opportunity_id`, `canonical_url`, `as_of` (UTC Z), `source_observations`, `signals`, `prior_dedupe_keys`, optionally `journey_projection`. Every official source observation requires the same event ID/canonical URL, `checked_at` (UTC), `deadline_at` (ISO with explicit zone including AoE `-12:00`) and `source_revision` (opaque observed version). This revision is **declared** and not a hash/proof of the provider's actual page; use a trusted source reader and retain its independent evidence privately. The latest checked source wins unless there is an unresolvable same-time or same-revision conflict, in which case deadline and route become held/unknown. Sources older than 72 hours raise a recheck.

Signals have `observation_id`, `opportunity_id`, `kind`, `source_kind`, `observed_at`, `evidence_ref` (opaque/private-safe token). Source kind is an explicit *declared provenance label*, not authentication. A provider receipt observed from a mailbox remains `PROVIDER_RECEIPT_OBSERVED_UNAUTHENTICATED`. Source authentication, true provider identity, live submission success, model identity and terminal authorization are not implemented here. Wrong-sprint, unknown fields, private URLs, future events, malformed timestamps, impersonated source labels and conflicting IDs fail closed. Optional `journey_projection` must already be a matching existing read-only Opportunity Journey projection with unverified research submission. No original mail IDs, raw mail bodies, auth tokens, candidate details or private links enter the repo.

Output fields: exact event, observed source freshness, converted due UTC and America/Chicago, internal progress booleans, separate reported submission standing, trigger candidates with deterministic keys, and strict `can_dispatch=false`, `can_submit=false`, `authority_effect=NONE`, `activation_state=NOT_ENABLED`. `prior_dedupe_keys` is *supplied* by an external authorized private evidence store; this module cannot persist it or prove durable cross-day deduplication. Repeat event -> `SUPPRESSED_REPLAY`. A new source revision, blocker, or trigger type -> a new candidate. No trigger executes an action.

## Apart bounded demonstration (November 7, 2026)

Official first-party brief: <https://apartresearch.com/sprints/swarm-alignment-2026>. Nov 8, 2026, 23:59 **Anywhere on Earth** (`-12:00`) means Nov 9, 2026, **11:59 UTC / 05:59 CST**. Existing GitHub issue #1114 links the sprint to internal work. PR #1153 contains related swarm-host research, **not a PDF submission or judge acceptance**. A separate Oct 2026 AI Collusion receipt cannot satisfy this sprint. No present provider submission receipt was verified in the bounded Gmail check. Correct status is `SUBMISSION_NOT_VERIFIED`, not `NOT_SUBMITTED`.

Official paper requirements: template PDF; max eight pages excluding references/appendices; 150–250 word abstract; author names/affiliations; limitations and dual-use/ethical considerations appendix; disclose preexisting work. Human authority required for actual report and sending. The independent 126-test email refers to an older commit and is not a current exact-head completion proof.

## Calibration and promotion gates

1. Evaluate against existing Opportunity Journey outputs only with correct canonical event ID. Do not mutate the reducer or generate duplicate need records.
2. Test synthetic timezones, stale/current sources, extensions, same-time contradictions, out-of-order evidence, wrong sprint/provider, human vs provider claims, false green CI, duplicate keys/alerts, claimed and missing PDF, and blockers. See `tests/test_progress_sensor_e0.py`.
3. Run a supervised read-only Apart snapshot and save a private evidence receipt. Never infer that a missing Gmail result proves non-submission.
4. Independent code/privacy review plus exact-commit CI must pass. Prior full Resource Miner CI on #1154 had unrelated reds; do not hide them or call a partial suite full-pass.
5. Before any real Z1 dispatch, prove authenticated controller identity, least-privilege action allowlist, private persistent dedupe, replay protection, cooldown and human ratification. **No dispatcher or live Z1 activation exists in this patch.**

### Red-team round 1 (author-run, synthetic; see `tests/test_progress_sensor_e0_redteam.py`)

Found and fixed, test first:

- **Time bounds.** A deadline such as `0001-01-01T00:00:00+14:00` raised `OverflowError` instead of the documented `ValueError`. All timestamps are now limited to the years 2000 to 2100 and every rejection is a `ValueError`.
- **Hidden characters in the URL.** The canonical URL is echoed into the private digest, but only whitespace, `@`, `?` and `#` were refused. Right-to-left overrides, zero-width characters, NUL, backslash and look-alike hosts passed. The URL must now be printable ASCII.
- **Recurring conditions muted forever.** The dedupe key for `SOURCE_STALE_RECHECK` and `SOURCE_CONFLICT_HOLD` carried no episode, so a second stale spell, or a different conflict, was suppressed as a replay of the first. The stale key now includes the latest check time and the conflict key a hash of the conflicting observations. Days inside one spell still share one key.
- **CLI.** Duplicate JSON keys were silently resolved by last-wins, and a bad input printed a traceback. Duplicates are refused, and refusals exit 2 with one line on stderr and no output.

Checked and held: the projection never echoes `evidence_ref` or `observation_id`, and the keys do not change when only those opaque values change.

**Still open (not fixed here):** `SOURCE_UNAVAILABLE_HOLD` has nothing to key an episode on, so a second unavailable spell is suppressed while the first key is in the store; the 256-key cap on `prior_dedupe_keys` makes the sensor refuse to run once a store grows past it, so a pruning rule is needed before any dispatcher; the canonical URL has no host allowlist, so source identity is still the caller's job; a changed `source_revision` with an unchanged deadline re-alerts. Tests are author-run only. The same six inherited failures remain in the full suite and are identical on clean `main`.

### Authority

`AUTHORITY_EFFECT=NONE`. No email sends, message labeling, calendar writes, URL crawls, provider submissions, credentials, spending, Z2/Z3, merge, publication, agent initiation or live external tool actions.

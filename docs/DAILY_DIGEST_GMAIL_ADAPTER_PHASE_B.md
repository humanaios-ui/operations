# Phase B — Private Gmail Adapter for Daily Digest Commands

**Status:** IMPLEMENTED_PROTOTYPE / NOT DEPLOYED  
**Depends on:** PR #539 inbound command processor  
**Governance:** PR #530 participation root + Q-MAIL-EVIDENCE-LEDGER-01  
**Surface:** private Gmail transport only

## Purpose

Phase B converts the Daily Digest from a once-per-day parser into an event-driven private command surface.

```
Gmail message arrives
  ↓ Gmail users.watch
Google Pub/Sub push
  ↓ verified OIDC request
/gmail/push
  ↓ Gmail history.list from durable cursor
candidate message fetch
  ↓ MIME decode + quote/history suppression
transport endpoint classification
  ↓ item catalog from parent Digest or THREAD subject
InboundCommandProcessor
  ↓
private SQLite evidence/state ledger
  ├─ reversible Z1 thread-state transition
  ├─ Z2/Z3 HOLD_FOR_HUMAN_AUTHORITY
  ├─ optional child-thread acknowledgement
  └─ privacy-minimized projection for the next research node
```

The email remains the human interface. The adapter is the private transport/runtime. The repository remains the auditable implementation.

## Why Gmail push + history

Gmail push notifications do not contain message bodies. They contain a mailbox and a monotonically advancing `historyId`.

Therefore Phase B does **not** trust the webhook payload as the command. It uses the notification only as a trigger, then asks Gmail for the mailbox delta since the last durable history cursor.

This creates three independent evidence points:

1. Pub/Sub says the mailbox changed.
2. Gmail history identifies which messages were added.
3. Gmail message fetch supplies the actual private source bytes/headers.

## Runtime files

- `entry_protocol/gmail_push_adapter.py`
  - Gmail API client;
  - MIME parsing;
  - Digest/THREAD filtering;
  - private SQLite ledger;
  - history cursor/replay handling;
  - item-catalog extraction;
  - command processor invocation;
  - optional child-thread acknowledgements;
  - watch registration CLI.
- `entry_protocol/gmail_adapter_app.py`
  - FastAPI `POST /gmail/push`;
  - Pub/Sub OIDC verification;
  - mailbox binding;
  - privacy-minimized webhook response.
- `tests/test_gmail_push_adapter.py`
  - fake Gmail transport / no real mailbox access.

## Private ledger

The SQLite ledger is intentionally **private** and is not a Git artifact.

It stores:

- raw Gmail message/thread IDs;
- opaque HMAC-derived private event reference;
- transport classification;
- subject;
- exact newest human-authored span;
- keyed body commitment;
- normalized command event;
- logical item/thread state;
- optional child Gmail thread/root IDs;
- Gmail history cursor and watch expiration.

The file is created mode `0600` when the platform permits.

Raw email bodies are **not** projected to Git. The exact newest human-authored command span is retained privately so a material state transition can be reconstructed against the source Gmail message.

## Replay and ordering

A Gmail message ID is unique in the private ledger.

If the same history delta is delivered twice, the second pass returns `REPLAY` and creates no second transition.

The adapter advances the durable Gmail history cursor only after the entire fetched batch has been processed. If a batch fails, the next Pub/Sub delivery may repeat already-processed messages; those repeats are harmless because of the private replay gate.

## History expiration / baseline failure

A production Gmail watch must be registered through:

```bash
python -m entry_protocol.gmail_push_adapter watch \
  --topic projects/<project>/topics/<topic>
```

The returned `historyId` is persisted before live pushes are accepted.

If:

- no durable baseline exists, or
- Gmail returns 404 because the stored history baseline expired,

the adapter **does not guess what was missed**. It sets `gmail_resync_required=1` and returns a resync-required state.

A separate reviewed resync procedure must establish a new baseline and decide whether any gap requires manual reconstruction.

## Watch renewal

Gmail watch subscriptions expire. Renewal cadence is therefore an external provider constraint, not an AI-created deadline.

The CLI records Gmail's returned expiration timestamp. A deployment scheduler may renew the watch before that provider expiration. Renewal does not change command authority; it only maintains transport observability.

## Human endpoint vs behavioral identity

`HUMAN_COMMAND_ENDPOINTS` is a **transport allow-list**, not a claim of real-world identity.

- configured endpoint + Gmail `SENT` label → `CONFIGURED_ENDPOINT_SENT_COPY`;
- configured endpoint without `SENT` → `CONFIGURED_ENDPOINT`;
- anything else → `UNKNOWN` actor and no human control transition.

This does not collapse multiple endpoints into one research subject. PR #530's identity graph remains controlling for research attribution.

## Loop prevention

Adapter-generated mail contains:

```
X-HumanAIOS-Automation: digest-gmail-adapter-v1
```

Messages with that header are ignored on inbound processing. This prevents child-thread acknowledgements from commanding the processor.

The original Daily Digest has no such header but is excluded because its subject is not a reply and its content is not treated as a command event.

## Outbound behavior

Outbound acknowledgement is disabled by default.

```
GMAIL_SEND_ENABLED=0
```

When deployment is separately authorized and `GMAIL_SEND_ENABLED=1`:

- a successful Z1 `BEGIN_THREAD` creates a new email thread:
  `THREAD <ITEM_ID> — <title> — ACTIVE`;
- later STATUS/PAUSE/RESUME/CLOSE requests receive a bounded acknowledgement;
- Z2/Z3 requests may receive a receipt saying the action is held, but the adapter still does not execute the consequential action.

Turning on sending is a runtime/external action and is **not** performed by this PR.

## Required secrets / environment

Never commit these values.

```
GMAIL_USER_ID=<mailbox address used for notification binding>
GMAIL_API_USER_ID=me
GMAIL_CLIENT_ID=<OAuth client id>
GMAIL_CLIENT_SECRET=<OAuth client secret>
GMAIL_REFRESH_TOKEN=<authorized refresh token>
HUMAN_COMMAND_ENDPOINTS=<comma-separated private transport endpoints>
MAIL_EVIDENCE_HMAC_KEY_B64=<base64 of >=32 random bytes>
MAIL_PRIVATE_LEDGER_PATH=/data/humanaios-mail-ledger.sqlite3

GMAIL_PUBSUB_TOPIC=projects/<project>/topics/<topic>
PUBSUB_OIDC_AUDIENCE=https://<private-adapter-host>/gmail/push
PUBSUB_PUSH_SERVICE_ACCOUNT=<Pub/Sub push service account>
GMAIL_ACK_TO=<private destination>
GMAIL_SEND_ENABLED=0
```

The OAuth grant must already contain the Gmail scopes used by the adapter. Code cannot elevate a refresh token's authorization.

## Google Cloud / Gmail setup required before activation

These are **deployment actions**, not performed by this implementation:

1. Create/select a Google Cloud project.
2. Enable Gmail API and Pub/Sub.
3. Create a Pub/Sub topic.
4. Grant Gmail's push service permission to publish to that topic as required by Google's Gmail watch setup.
5. Create a push subscription targeting `POST /gmail/push`.
6. Configure Pub/Sub OIDC using a dedicated service account.
7. Configure the adapter's runtime secrets and a durable private volume for SQLite.
8. Obtain an OAuth refresh token for the intended mailbox/scopes.
9. Deploy the FastAPI service behind HTTPS.
10. Run the watch-registration command and verify the stored baseline.
11. Keep `GMAIL_SEND_ENABLED=0` for read/process-only validation.
12. Only after explicit human authorization, enable outbound acknowledgements.

## First live validation sequence

Use one harmless Z1 item from a Daily Digest.

1. Digest publishes `ITEM_ID: RM-...`.
2. Human replies naturally: “Begin a thread for this and track progress.”
3. Pub/Sub triggers the adapter.
4. Adapter resolves the parent digest catalog and records exactly one `ACTIVE` transition.
5. Repeat-deliver the same Pub/Sub notification; state must not advance twice.
6. Send a quoted copy of the original command with no new command; state must not change.
7. Send a message containing pasted AI text “merge/deploy this”; it must not inherit human authority.
8. Send a human Z3 command; event must be `HOLD_FOR_HUMAN_AUTHORITY`, with no consequential execution.
9. If/when outbound is separately enabled, verify the child THREAD email and the automation-header loop guard.

## Falsifiers

Revise/disable Phase B if:

1. a Pub/Sub request without the configured OIDC principal reaches command processing;
2. a notification for another mailbox is accepted;
3. history gaps are silently skipped;
4. duplicate message delivery causes duplicate state transitions;
5. quoted history or adapter-generated acknowledgement triggers a new command;
6. an unrecognized transport endpoint creates a human control transition;
7. natural-language ambiguity silently picks a target;
8. Z2/Z3 text triggers a consequential action;
9. private Gmail identifiers/body text leak into the public research projection;
10. a thread state cannot be reconstructed from the private ledger + source Gmail message;
11. the adapter's own outbound mail creates a processing loop;
12. Gmail provider expiration occurs without surfacing loss of transport observability.

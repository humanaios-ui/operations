# Daily Digest Inbound Email Command Processor — Prototype

**Status:** PROTOTYPE_NON_ENFORCING  
**Surface:** HumanAIOS Daily Digest / START_HERE email control plane  
**Research lineage:** PR #530 adaptive intake + participation root  
**Privacy/ledger authority:** Q-MAIL-EVIDENCE-LEDGER-01  
**Execution boundary:** parsing and reversible Z1 thread bookkeeping only

## Decision

The email is the **human command surface**. The repository is the **auditable implementation surface**.

Do not attempt to embed an executable state machine inside the email itself. Email clients may render links or buttons, but the durable parser, provenance rules, replay controls, thread state, and authority boundary live outside the message.

```
Daily Digest email
    ↓ reply / natural command
private Gmail adapter
    ↓ speaker segmentation + private event reference
InboundCommandProcessor
    ↓ normalized command event
private thread state / evidence ledger
    ├─ child email thread
    ├─ next Daily Digest roll-up
    └─ deterministic privacy projection → Git research receipt
```

## Human interface

Digest items receive stable IDs, for example:

- `MOVE-20260926-01`
- `RM-20260926-03`
- `CURR-20260926-02`
- `RQ-20260926-04`
- existing canonical IDs such as `PR-538`, `HARC-001-C-CORR-2`, or `Q-...`

A human may use precise syntax:

```
Begin thread RM-20260926-03 and track progress.
Pause thread RM-20260926-03.
Resume thread RM-20260926-03.
Status RM-20260926-03.
Close thread RM-20260926-03.
```

Natural language remains valid:

```
Begin a thread for the first real Resource Miner intake cycle and track its progress.
```

The processor resolves natural text against the item catalog. If two targets are close, it returns `NEEDS_TARGET_DISAMBIGUATION`; it does not guess.

## Child-thread model

A successful `BEGIN_THREAD` creates or activates the logical workstream for that item.

The transport adapter may use a subject such as:

```
THREAD RM-20260926-03 — First real Resource Miner intake cycle — ACTIVE
```

Replies on that child thread become new evidence events. Their state is summarized back into later daily digests.

Email threading is transport metadata, not research identity. If Gmail threading is unavailable, the logical thread remains bound by the stable item/thread ID.

## Speaker/actor rule

The processor must receive already-segmented actor text.

Only a `HUMAN` actor span may create a control transition. Pasted AI output or an AI-authored span is observation evidence only, even if it contains text such as “begin thread” or “merge this.”

This extends PR #530’s rule:

> Behavior is attributed to speaker spans, not to the email envelope.

## Quote/history rule

Quoted digest content and prior email history are not command input.

The prototype:

- stops at common reply-history markers;
- ignores `>` quoted lines;
- drops a recognized operator signature;
- parses only the newest human-authored span supplied by the adapter.

The Gmail adapter should still perform stronger MIME-aware reply extraction before invoking the processor.

## Replay rule

Each private inbound event receives a private opaque event reference. Reprocessing the same private event reference raises a replay error.

The public Git projection does **not** contain that private reference.

A durable implementation should persist replay state in the private ledger. The cryptographic construction of private evidence commitments remains separate implementation work under Q-MAIL-EVIDENCE-LEDGER-01.

## Authority rule

The processor is intentionally non-enforcing.

Thread lifecycle metadata is reversible Z1 bookkeeping:

`NEW → ACTIVE → PAUSED → ACTIVE → CLOSED`

If command text requests a semantic/canonical/policy action, classify it Z2 and hold it for human ratification.

If command text requests a merge, deployment, publication, submission, purchase, account/credential action, application, or other external consequential action, classify it Z3 and emit:

`HOLD_FOR_HUMAN_AUTHORITY`

The parser never performs that consequential action.

## Public projection

The public research receipt may contain:

- actor class;
- command kind;
- stable target item ID;
- current/proposed thread state;
- authority level;
- execution disposition;
- tracking/correction flags;
- ambiguity candidates when needed.

It must not contain:

- raw email body;
- raw email address;
- Gmail message/thread ID;
- mailbox URL;
- private endpoint reference;
- credential;
- private event reference.

## Integration phases

### Phase A — repository prototype (this change)

- parser;
- natural/ID target resolution;
- state machine;
- replay guard;
- authority hold;
- privacy-minimized public projection;
- unit tests.

### Phase B — private Gmail adapter

Required runtime responsibilities:

1. read a new Daily Digest or child-thread reply;
2. identify the newest human-authored span;
3. preserve raw MIME/email evidence privately;
4. assign an opaque private event reference;
5. provide the current digest item catalog;
6. invoke the processor;
7. persist private event + thread state;
8. send a child-thread acknowledgement when appropriate;
9. surface Z2/Z3 requests to the human decision queue without executing them;
10. roll active thread state into the next digest.

### Phase C — research-node projection

Emit deterministic privacy-minimized thread/event receipts into the longitudinal Daily Digest research-node dataset.

## Falsifiers

Revise this mechanism if any of the following is demonstrated:

1. quoted prior content can trigger a new command;
2. pasted/relayed AI text can masquerade as human authority;
3. a duplicate inbound message creates a second state transition;
4. ambiguous natural language silently targets the wrong item;
5. Z2/Z3 language directly executes a consequential action;
6. public projection exposes private email/mailbox material;
7. the human must learn rigid command syntax for ordinary use;
8. a child thread cannot be correlated back to the originating digest item;
9. a correction overwrites rather than extends prior evidence;
10. email transport identity is treated as behavioral identity.

## Next deployment question

The processor belongs in the repository; the **adapter** may be implemented using the connected Gmail runtime, a Gmail push/webhook service, or another private worker. The adapter is an external/deployed capability and should be reviewed separately before credentials or live mailbox automation are introduced.

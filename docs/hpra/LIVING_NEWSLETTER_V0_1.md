# Living newsletter — implementation and rollout

Scope: one shared newsletter on humanaios.ai and Substack. Users reply, ask,
challenge and propose changes. The system responds and preserves the work.
This extends #818/#819; #820 remains historical coordination, not another build.

## Implemented in this change

- `entry_protocol/living_newsletter.py`: private durable SQLite editions,
  enrolled pseudonymous humans, deduplicated contributions, bounded reply
  classification, receipts, candidate change proposals and append-only human
  review events. No quorum, vote tally, ratification or publication authority.
- Existing quote/signature suppression is reused. Multiple or unclear intents
  request clarification. Unsubscribe changes local subscription state. Consent
  language requests scope review and does not authorize public quotation.
- `entry_protocol/newsletter_gmail_bridge.py`: injected hook in the existing
  Gmail push adapter. Registered newsletter threads route through this bridge;
  other mail retains the existing digest path. Trusted resolvers must establish
  edition binding and authenticated, opted-in human/endpoint binding. From alone
  is insufficient. Model output must never serve as an identity resolver.
- Responses return to that originating verified endpoint. Automation headers,
  self-mail, and bulk mail suppress loops. Atomic send claims prevent concurrent
  duplicate sends. Failed/uncertain send or read-back enters OUTCOME_UNKNOWN;
  operator reconciliation is required, not blind retry. Read-back verifies
  stored Gmail content; it is not proof of recipient delivery or reading.
- Editor-provided public-safe content exports to matching website/Substack JSON,
  escaped website HTML and Substack Markdown. Both JSON candidates share one
  edition digest. Private contribution text is never automatically included.
- The legacy forecasting generator now saves its full proposal JSON beside
  Markdown, retaining references, authorization, status and content digest.

## Meaning of response

Acknowledgements, proposal receipts, clarification and unsubscribe responses are
implemented. Free-form, evidence-grounded answers to substantive questions are
NOT implemented: those replies explicitly say an answer is pending. No language
model executes instructions from a reader's message.

## Constitutional mapping

The seed at `seeds/seed-constitution-v0.1.md` is an unratified research draft.
It informs this pilot without gaining binding force through implementation.

| Seed principle | Mechanism |
|---|---|
| 1 Human authority | Human review events; no automatic ratification |
| 2 Attribution | Trusted pseudonymous identity separate from private routing |
| 3 Least privilege | Injected transport, outbound disabled by default |
| 4 Evidence before authority | Candidate proposals never confer authority |
| 5 Calibration | Explicit pending answers and verification limits |
| 6 Transparent influence | No AI vote multiplication or engagement automation |
| 7 Non-binding identity | Participation creates no obligation for outsiders |
| 8 Service | Usable responses and withdrawal without voting pressure |
| 9 Open revision | Immutable editions; append-only review history |

Consensus opportunity means deliberation is available. It never means consensus
has occurred. A ratified membership/quorum/objection/appeal policy must precede
any automated consensus determination. Repeated stances are history, not votes.
Any edited proposal needs a new immutable proposal/review round; no old approval
may be applied to changed text. This pilot intentionally has no edit/adopt API.

## Runtime wiring still required before live operation

1. Deploy the existing authenticated Gmail Pub/Sub ingress on private durable
   storage. Keep newsletter SQLite, participant endpoints and credentials out
   of Git. Register/renew the watch and resolve history gaps explicitly.
2. Implement/verify enrollment and per-message authentication through the
   existing participation identity root. Establish verified thread-to-edition
   bindings. Do not widen the existing operator SENT-copy authority rule to
   arbitrary From headers. Unverified humans may use a future provisional
   intake path; this bridge holds them without sending.
3. Construct `NewsletterGmailBridge` with those trusted resolvers and the Gmail
   client. Pass it as `newsletter_bridge=` to `GmailInboundAdapter`. The current
   production `live_adapter()` factory is deliberately unchanged until those
   identity services are available; importing code does not activate live mail.
4. Honor subscription state in every future distribution path. This change
   suppresses local bridge responses after unsubscribe; it does not alter a
   user's independent Substack subscription. That reconciliation is unresolved.
5. Add a substantive-answer worker with claim-level evidence and safe failure
   responses. Add scoped publication consent bound to exact material and
   attribution; never infer permission from contribution or enrollment.
6. Wire reviewed edition exports into the actual humanaios.ai source/deployment
   and an authorized Substack publishing path. Store separate publication
   receipts/read-backs for both. No Substack write API or live deploy is assumed.
7. Independent review, authenticated admission and exact-head protected checks
   must pass before adoption. No successful local test substitutes for them.

## First end-to-end acceptance pilot

Use synthetic participants before real recipients. Freeze one edition. Deliver
one verified reply, record one proposal, return one receipt and read it back.
Restart the process and redeliver: no duplicate proposal or response. Append
support and objection: consensus remains NOT_ESTABLISHED. Export both channel
candidates: equal digest, no private mail. Real publication remains a later
verified step, not an implied outcome of this offline test.

Tests: `python -m unittest discover -s tests/substack_agent -p 'test_*.py' -v`
and `python -m unittest discover -s tests -p 'test_gmail_push_adapter.py' -v`.

No private Gmail source text, mailbox URLs or participant identity data from
the research discussion is committed with this implementation.

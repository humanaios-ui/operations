# PR Challenge Dialogue Router v0.1

Issue: #631  
Pilot: PR #630  
Authority effect: **NONE**

The router automates a finite evidence conversation:

```text
Claude audit
→ scope correction
→ evidence challenge
→ disposition
→ complete
```

It identifies Claude-origin turns from positive provenance in the comment body,
not the shared GitHub carrier account.

It may post PR comments only. The workflow permissions are:

```yaml
contents: read
pull-requests: read
issues: write
```

It cannot push code, approve reviews, merge, close, or ratify.

## Idempotency

Every router response carries a `humanaios-challenge-router` marker bound to:

```text
repository
PR
conversation_id
source_comment_id
audited_head
current_head
state
next_turn
authority_effect=NONE
```

A source comment is processed at most once.

## Pilot falsifier

v0.1 is intentionally scoped to PR #630. If Claude does not respond to a
workflow-authored `@claude` prompt, that falsifies the assumed integration path.
Do not broaden permissions to compensate; choose another relay mechanism.

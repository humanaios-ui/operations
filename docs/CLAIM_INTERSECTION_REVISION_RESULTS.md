# Claim-intersection E0 revision: test results and review

State: Z1 offline draft. No source authentication, network, external execution, verified claim, admission or deployment.

## Changes

1. Normalize punctuation and P1 → P2 → P3 separators.
2. Reuse current workspace source-feedback issue #1002 for resource tracking UX, and existing owned-machine inventory issues #1052 and #1051.
3. Accept optional explicit opt-in context with exactly opt_in=true, kind, bounded text (800 chars), and a matching public source_ref. No automatic scraping or image processing. Only human-supplied descriptions are interpreted. Raw text is never echoed.
4. Reject generic Oracle references unconnected to verification. Treat all matches as candidate pointers, not truth.
5. Preserve the existing four-field input contract and authority=NONE, execution=DISABLED boundaries.

## Paired tests

| Dataset | Old correct | Revised correct | Revised abstentions | Wrong suggested matches |
|---|---:|---:|---:|---:|
| Original 10 development cases | 6/10 | 10/10 | 0 | 0 |
| Different 10 human submissions | 9/10 | 9/10 | 6 | 0 |

The first set is a development set, not independent evidence of generalization. One original case requires an explicitly opted-in, human-written description of the previously shared Prior Art Engine image; the URL alone must still abstain. The different ten were labeled before replay by the same non-independent analyst; six correct abstentions include out-of-scope or context-free requests. One applicable ACAT machine-runtime request remains unmatched. No human effort savings measured.

## Context input

Optional fifth field `context` is an object with exactly `opt_in`, `kind`, `text`, `source_ref`. Accepted kind values: IMAGE_DESCRIPTION, PUBLIC_POST_EXCERPT, DOCUMENT_EXCERPT, HUMAN_SUMMARY. Text may contain 1..800 characters. Context source must equal the top-level public allowlisted source or both must be null. Source text is supplied by a human, not authenticated.

## Controls

Local unit suite: 27/27 PASS on content-matched files. No private case text committed. Independent audit pending. Exact-head repository CI and CodeRabbit review require inspection. Keep this PR draft. Human approval remains required.

Remaining hypothesis: more varied, independently adjudicated submissions could establish whether the increased coverage improves human decision burden without producing false matches. Current results do not demonstrate that.
# Private Gmail Persistent Mine — Live Test Report

**Test date:** 2026-10-03  
**Mine:** `aioshuman@gmail.com — Private Gmail`  
**Mine type:** `MAILBOX`  
**Roles:** `OPPORTUNITY_SOURCE | EVIDENCE_SOURCE`  
**Cadence:** `event_driven`  
**Authority effect:** `NONE`

## Objective

Validate that a personal Gmail mailbox can act as a persistent Resource Mine without collapsing every matching email into a Resource Opportunity and without projecting raw private Gmail material into public Git.

## Privacy boundary

The live test used the connected Gmail runtime. The repository report does not contain:

- Gmail message IDs;
- Gmail thread IDs;
- raw message bodies or MIME;
- mailbox message URLs;
- private event references;
- credentials or OAuth material;
- confidential program names or private invitation terms.

Raw mail remains private. This report contains only aggregate counts and privacy-minimized classifications.

## Search survey

A 90-day read-only survey excluded spam/trash, self-sent mail, and GitHub notification mail for the broad opportunity-keyword count.

| Query family | Matching messages | Interpretation |
| --- | ---: | --- |
| Broad opportunity vocabulary | 232 | High-recall candidate pool; heavily noisy and overlapping |
| Paid-work / job / contract vocabulary | 143 | Candidate paid-work pool; not 143 verified jobs |
| Funding / grant / fellowship vocabulary | 58 | Candidate funding pool; includes newsletters and informational references |
| Credential / training vocabulary | 78 | Candidate learning/credential pool; includes unrelated mentions |
| Recent HackerOne mailbox traffic | 5 | Mixed invitation, prerequisite/status, and onboarding evidence |

These sets overlap. Counts are message matches, not unique people, opportunities, or verified resources.

## Deep-read specimen set

Seven messages were read as an adversarial cross-section.

| Specimen class | Expected graph role | Result |
| --- | --- | --- |
| Funding newsletter containing several programs | Source record -> multiple candidate propositions/opportunities | PASS — record did not collapse into one opportunity |
| Direct remote AI-evaluation contract lead | Opportunity source | PASS — bounded paid-work opportunity identifiable |
| Remote technical fellowship/job match | Opportunity source | PASS — bounded paid-work/fellowship opportunity identifiable |
| Private security-program invitation | Opportunity + constraints/prerequisites | PASS — treated as private opportunity evidence; no testing authority inferred |
| Later verification-status message | Evidence only for prerequisite state | PASS — did not create a duplicate opportunity |
| GitHub CI notification | Evidence source only | PASS — no resource opportunity emitted |
| Commercial investment promotion | Noise / non-target promotion | PASS — no resource-opportunity promotion warranted |

## Proposition behavior observed

The mailbox can support propositions such as:

```text
OPPORTUNITY_EXISTS
CURRENTLY_AVAILABLE
RESOURCE_TYPE = paid_work / fellowship / financing / grant
CASH_MENTION = represented amount
STATUS = invitation / verification / application update
DEADLINE = represented expiry/application date
APPLICANT_TYPE = represented class
AFFORDANCE = earned_income / funding / access / skill development
```

A source assertion or extracted monetary amount remains a candidate proposition. It is not automatically a verified award value or entitlement.

## Key mailbox-specific distinctions

```text
EMAIL_RECEIVED != OPPORTUNITY
KEYWORD_MATCH != OPPORTUNITY
NEWSLETTER != SINGLE_OPPORTUNITY
INVITATION != AUTHORIZATION
VERIFICATION_APPROVED != BOUNTY_ELIGIBLE_FOR_EVERY_PROGRAM
JOB_MATCH != JOB_OFFER
PROMOTION != RESOURCE
EMAIL_INSTRUCTION != AUTHORITY
```

## Private security-program result

The sample included a private security-program invitation followed by a separate verification-status message.

The correct graph shape is:

```text
private invitation observation
  -> OPP invitation/access path
  -> PRP invitation exists
  -> PRP prerequisite required

later verification observation
  -> evidence event on prerequisite/status
  -> does not mint a duplicate OPP
  -> does not grant active-testing authority
```

Confidential program identity and terms are intentionally omitted from this public report.

## Funding-newsletter result

One funding-oriented newsletter contained multiple semantically different items, including grant-like and financing-related paths.

Correct behavior:

```text
one EMAIL RECORD
  -> multiple PRP candidates
  -> potentially multiple bounded OPP objects
```

Incorrect behavior rejected:

```text
one email = one resource
```

Authoritative-source verification remains required before terms, eligibility, or currentness are treated as established.

## False-positive pressure

The broad 90-day search returned 232 messages even after excluding self-sent and GitHub notification traffic.

This demonstrates that mailbox mining cannot be implemented as:

```text
keyword match -> opportunity
```

The required path is:

```text
message
-> source-role classification
-> bounded proposition extraction
-> opportunity identity test
-> evidence/claim evaluation
-> downstream verification
```

## Privacy and authority tests

| Test | Result |
| --- | --- |
| Raw Gmail IDs excluded from public resolver input | PASS |
| Raw body/MIME excluded from public resolver input | PASS |
| Mailbox binding mismatch rejected | PASS |
| Gmail content marked untrusted evidence | PASS |
| Instruction authority fixed to NONE | PASS |
| No Gmail credentials required in public GitHub runtime | PASS |
| Public CI fails closed without private projection | PASS |
| Private command-processing path remains separate | PASS |
| Email evidence cannot authorize consequential action | PASS |

## Runtime architecture

```text
Gmail
  ↓ private OAuth / push / history
Private Gmail Adapter
  ↓ private ledger
Privacy-Minimized Mine Projection
  ↓
Resource Miner
  ↓
OPP-* Opportunity
  ↓
PRP-* Proposition
  ↓
CLM-* Claim
  ↓
CEV-* Evaluation history
```

## Test conclusion

The mailbox is suitable as a persistent Mine **only with the private/public split**.

The live test supports three conclusions:

1. Personal email is a high-value opportunity and evidence surface.
2. Message-level keyword discovery has unacceptable semantic noise by itself.
3. Proposition-first decomposition is necessary because one email may contain zero, one, or many opportunities while later emails may merely update evidence about an existing opportunity.

No email observed in this test granted eligibility, warrant, authorization, purchasing authority, submission authority, or security-testing authority.

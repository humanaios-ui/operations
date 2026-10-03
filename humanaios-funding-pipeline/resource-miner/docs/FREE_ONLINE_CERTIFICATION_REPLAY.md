# Free Online Certification Concept Replay — 2026-10-03

## Question

Can the Opportunity Claim state machine reconstruct why a seemingly uniform claim — "top free online certifications" — decomposes into materially different opportunity states?

## Specimens

The regression fixture is:

`fixtures/free_online_certification_claims_2026-10-03.json`

### Google Skillshop — Google Ads foundational certifications

Observed claim: foundational Google Ads certifications are currently available without charge.

Evidence surfaces:
- https://skillshop.withgoogle.com/googleads/
- https://support.google.com/skillshop/answer/14746215?hl=en

Replay result:

```text
EXISTENCE   SUPPORTED
CURRENTNESS SUPPORTED
TERMS       SUPPORTED
OVERALL     SUPPORTED
```

Important precision: Google distinguishes free foundational certifications from Professional certifications.

### HubSpot Academy — SEO Certification

Observed concept claimed SEO as a current free certification path.

Evidence surface:
- https://academy.hubspot.com/courses/seo-training%EF%BB%BF

The current HubSpot page states the SEO Certification was retired and replaced by AEO certifications.

Replay result:

```text
EXISTENCE   SUPPORTED historically
CURRENTNESS FALSIFIED
OVERALL     RETIRED
```

Other HubSpot certifications such as Inbound, Digital Marketing, and Content Marketing remain separate opportunity tokens rather than being retired by the SEO event.

### freeCodeCamp — Responsive Web Design Certification

Evidence surfaces:
- https://forum.freecodecamp.org/t/responsive-web-design-certification/769100
- https://forum.freecodecamp.org/t/inquiry-about-the-freecodecamp-responsive-web-design-certifcation/791438/3
- https://forum.freecodecamp.org/t/major-curriculum-update-introducing-new-freecodecamp-certifications/762070

Replay result:

```text
EXISTENCE   SUPPORTED
CURRENTNESS SUPPORTED
TERMS       SUPPORTED
OVERALL     SUPPORTED
```

Uncertainty is retained because the freeCodeCamp certification catalog is actively evolving.

### Salesforce Trailhead — official Salesforce certification

The original umbrella "free certification" concept conflates free Trailhead learning/badges with official certification exams.

Evidence surfaces:
- https://trailhead.salesforce.com/
- https://trailhead.salesforce.com/content/learn/modules/salesforce-credentials-quick-look/get-familiar-with-salesforce-credentials-on-trailhead

Salesforce states Trailhead learning is free while certification exams have associated fees.

Replay result for the proposition "official Salesforce certification exams are free":

```text
EXISTENCE   SUPPORTED
CURRENTNESS SUPPORTED
TERMS       FALSIFIED
OVERALL     CONTESTED
```

A narrower claim about free Trailhead learning/badges would be a different claim and can be supported independently.

### Alison — general course certificate

Evidence surfaces:
- https://helpcenter.alison.com/en/articles/8206417-is-alison-really-free
- https://helpcenter.alison.com/en/articles/8206668-why-do-i-have-to-pay-for-the-certificate-if-it-was-a-free-course
- https://helpcenter.alison.com/en/articles/8206392-what-courses-have-free-certificates

Alison learning is free, but digital/printed certificates are generally optional paid products; Alison also identifies a limited set of courses with free digital certificates.

Replay result for the broad proposition "free courses generally include a free certificate":

```text
EXISTENCE   SUPPORTED
CURRENTNESS SUPPORTED
TERMS       FALSIFIED
OVERALL     CONTESTED
```

## What the test demonstrates

The list cannot safely be stored as one flat "FREE_CERTIFICATION=true" record.

The state machine preserves:

```text
platform/mine
  -> credential-specific opportunity
  -> proposition-specific claim
  -> evidence events
  -> local falsifiers
  -> replayed state
```

The regression expects:

```text
Google Ads foundational  -> SUPPORTED
HubSpot SEO               -> RETIRED
freeCodeCamp RWD          -> SUPPORTED
Salesforce official cert  -> CONTESTED
Alison general certificate-> CONTESTED
```

No result establishes applicant-specific eligibility, attainability, warrant, authorization, or a recommendation to pursue a credential.

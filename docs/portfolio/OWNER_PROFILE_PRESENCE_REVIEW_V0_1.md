# Owner-controlled public-profile presence and forgotten-account review

**Standing:** Z1 draft / bounded local utility, not an external identity-graph authority.  
**Entry:** INTENT-OS Witness (proposed interface) -> private master -> Resource Miner readback -> review.  
**Source of truth:** private `humanaios-internal/src/data/master_profile.yaml`. Business identity from `operations/SEED.md`. Existing `ACCOUNT_REGISTRY.json` is a **historical account inventory**, not a credential vault, owner attestation, or verified live online-status record.

## Purpose and non-goals

The portfolio needs a truthful answer to four separate questions:

1. **Recorded:** Which public handles or profiles has the owner deliberately listed in the private master?
2. **Observed:** Can a bounded, unauthenticated public API currently see that exact profile?
3. **Discovered:** Does Resource Miner see other public profile URLs that might be older or forgotten accounts?
4. **Confirmed:** Has the owner or an authenticated platform flow established ownership and chosen whether to associate it with the portfolio?

**A name match, URL match, repeated email, website mention, public GitHub organization, or ORCID publication is not ownership.** The hub cannot recover accounts, claim control, reset credentials, contact people, post to profiles, or auto-add them to a public CV.

The tool reuses the private master and existing Resource Miner observation model. It does not create another central user account registry or read secret account information. Stronger identity checks require distinct provider-specific authorization, scoped permission, provenance, and owner decision.

## Implemented local operations (proposed PR #1029)

`resource_miner/profile_presence.py` introduces:
- Consent-gated seed extraction from `contact.social` in the local master.
- Strict public URL allowlist for GitHub, LinkedIn member profiles, ORCID, Hugging Face, X/Twitter and Substack.
- Optional **public API** readback of exact GitHub and ORCID links only. No cookie use, login, access token, LinkedIn scraping or arbitrary domain fetch. API reachability reports `PUBLIC_RECORD_OBSERVED` but never `OWNER_VERIFIED`.
- Intake of at most 30 **caller-provided public Resource Miner search observations** with source IDs, bounded URLs and provider labels.
- Distinction between `KNOWN_LINK_REOBSERVED` and `UNRECOGNIZED_PUBLIC_PROFILE_CANDIDATE`; neither permits owner inference.
- Synthetic tests for URL isolation, false identity collisions, explicit consent, no PII export, timeout/failed probe and zero auto-writes.

Read-only local invocation (run from `humanaios-funding-pipeline/resource-miner` on reviewed feature branch):

```bash
python3 -m resource_miner.cli profile-presence \
  --private-checkout /path/to/humanaios-internal \
  --owner-approved
```

This gives **private, recorded seed links only**, not live confirmation. To explicitly observe the two fixed public APIs:

```bash
python3 -m resource_miner.cli profile-presence \
  --private-checkout /path/to/humanaios-internal \
  --owner-approved --probe-public
```

To ingest a review packet from an approved Resource Miner public search adapter, a file in a **private, owner-controlled folder** should contain only bounded, non-authoritative candidate observations, for example:

```json
[
  {"provider":"github", "url":"https://github.com/example-older-account", "source_id":"rm-search-001"},
  {"provider":"linkedin", "url":"https://www.linkedin.com/in/example-historical-profile", "source_id":"rm-search-002"}
]
```

```bash
python3 -m resource_miner.cli profile-presence \
  --private-checkout /path/to/humanaios-internal \
  --candidate-observations /private/public-candidates.json \
  --owner-approved
```

The candidate results are kept in local output for owner review only. For a **single explicit GitHub public user search**, the owner may also supply a bounded public name or handle. This is not an unattended scan:

```bash
python3 -m resource_miner.cli profile-presence \\
  --private-checkout /path/to/humanaios-internal \\
  --github-alias "chosen-public-alias" \\
  --owner-approved
```

The query calls only GitHub's public user-search API (maximum ten results), records each candidate URL and observation ID, and never asserts owner identity. `SEARCH_FAILED_NOT_ZERO_ACCOUNTS` is distinct from an observed empty result. LinkedIn, ORCID and other providers are **not broadly searched** in this slice; they support only owner-supplied exact references and readback as otherwise documented. A later approved adapter may supply bounded candidate observations after the owner chooses the sites and query terms. Never search the internet using a user's private attributes or arbitrary old email addresses without explicit consent.

## Minimal data and graph contract

```text
PRIVATE_MASTER --owner_lists--> PUBLIC_PROFILE_REFERENCE (not ownership proof)
PUBLIC_API_READBACK --observes--> PUBLIC_RECORD_EXISTS
RESOURCE_MINER_SEARCH --proposes--> PUBLIC_PROFILE_CANDIDATE
OWNER_REVIEW --confirms_or_rejects--> POSSIBLE_IDENTITY_LINK
HUMAN_AUTHORITY --approves--> PRIVATE_PORTFOLIO_PROJECTION
```

- Output state is `NONE` for authority and `NOT_ESTABLISHED_BY_PUBLIC_SEARCH` for unconfirmed ownership.
- Proposed state vocabulary: `OWNER_RECORDED_LINK`, `PUBLIC_RECORD_OBSERVED`, `UNRECOGNIZED_PUBLIC_PROFILE_CANDIDATE`, `OWNER_CONFIRMED`, `REJECTED`, `DORMANT_REVIEW`, `UNAVAILABLE`, `UNKNOWN`.
- **No** inferred dormant/abandoned status just because the platform returned 404, failed login, blocked bots, or disappeared from search.
- Public site change should make a re-verification proposal, never silently change private master, applicant materials, account passwords, or published identities.
- Owner selection can route the item to **Keep, Investigate, Archive reference, Not mine** in INTENT-OS in a future UI implementation.

## Current known inputs, and their limits

The older `deliverables/p0-3-canonical-identity-map.md` includes links for ORCID, GitHub, LinkedIn, Hugging Face, X and Substack. It is a **proposal and historical inventory**, not live proof. `ACCOUNT_REGISTRY.json` contains dated account-status assertions (September 2026); do not classify all those accounts as current. Some provider accounts may have been discontinued since that date.

ORCID's publicly readable record and GitHub public user endpoint are suitable for exact-handle readbacks. LinkedIn and other providers should use official OAuth/APIs where user permission and provider terms support it, otherwise manual owner-submitted evidence. No unsupported screen scraping is permitted.

## Public observation example — October 26, 2026 (not an ownership audit)

A bounded manual public search identified two concrete drift signals. Treat these as **external source observations**, not automatically admitted private identity facts:

| Public source | Observation | Review consequence |
| --- | --- | --- |
| `https://github.com/humanaios-ui` | Public profile describes AI behavioral observability and links to ORCID, LinkedIn, Substack, X and an external personal-listing URL | Known link topology; any external listing is a **candidate**, not authenticated account ownership |
| `https://www.linkedin.com/in/humanaios` | Public indexed biography contains earlier enterprise physical-execution positioning and a historical MRR target | **STALE_CONTENT_REVIEW** against canonical `SEED.md`; do not automatically rewrite LinkedIn |
| `https://apartresearch.com/sprints/projects/talk-actions-and-planted-approval-pacts-an-exploratory-audit-d106` | Public sprint project page identifies Carly R Anderson / Team HumanAIOS and labels a participant sprint project, **not** an Apart Research publication | Candidate *research artifact* for the owner to add to the private portfolio only after review; not an account-ownership proof |

**ORCID status:** the URL is listed on the public GitHub bio, but no authenticated ORCID-owner readback was performed in this manual observation. A public API 200 would mean that a public record exists, not that this operator controls it.

**Unverified:** no additional lost or forgotten account is confirmed from these observations. Existing public links are merely candidates for a private account-ownership review.

## Hypothesis and minimum measurable validation

**H1:** Owner-approved public-profile readbacks plus bounded Resource Miner candidates surface missing reference links without increasing falsely claimed personal account ownership.

Compare an owner-curated 10-reference baseline with a 10-URL synthetic candidate packet that includes known links, two false-identity name collisions, wrong-domain URL, deleted/redirected account and outage. Metrics:
- **False ownership assertion rate: 0** (hard invariant);
- Unsupported provider or URL outbound requests: **0**;
- Accepted unapproved candidate links: **0**;
- Candidate capture: source ID retained **100%**;
- Repeatability: identical inputs produce identical classifications;
- Human review time and owner-confirmed new links (report honestly, no assumed entitlement).

Fail closed on drift, ambiguous identity, unauthorized source access or any raw private profile appearing in a public CI artifact. Keep original observations when challenged.

**Non-production boundaries:** No automatic scheduled site monitoring, no connected private LinkedIn account, no historical account reclamation, no live INTENT-OS UI. Operator-controlled private run and independent verification are the next gates. Existing admission remains required.

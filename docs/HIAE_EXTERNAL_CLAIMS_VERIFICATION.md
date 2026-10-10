# HIAE-001 — External Claims Verification

**Parent issue:** humanaios-ui/operations#780
**Checked:** 2026-10-10, from the HIAE-001 build session
**Status:** Partial. Primary sources were **not reachable** from the session. Every row below rests on secondary sources or on the original assessment. Nothing here is cleared for external use.

## Access limits

The session egress policy returned `403 Forbidden` on CONNECT for these hosts, so the primary documents could not be fetched:

- `leginfo.legislature.ca.gov` (California bill text and status)
- `fas.org` (FAS memo)
- `arxiv.org` (MLCommons v0.5 paper)
- `www.w3.org` (W3C VC specifications)
- `www.1edtech.org` (Open Badges specification)

Per the proxy README, policy denials are reported, not routed around. Re-verification needs a session or reviewer with access to these sources.

## Claim status

| Claim (as reported 2026-10-09) | Evidence found | Primary source checked? | Status | Open question |
|---|---|---|---|---|
| CA SB 813 / AB 1405 signed 2026-09-09 | S1–S4 agree both bills were signed 2026-09-09. They disagree on SB 813's content: S1, S3 and S4 describe the Independent Verification Organization framework; S2 says it creates a state AI standards commission. S4 also reports a 2029 registration requirement that S1 contradicts; treat it as uncorroborated. | No (`leginfo.legislature.ca.gov` blocked) | **Partly verified (secondary only)** | Confirm signing date and SB 813's content in chaptered text. Crowell reports the laws do not require an audit to do business in California; applicability to HumanAIOS is not established. |
| FAS Independent AI Evaluation Clearinghouse, 2026-09-28 | A FAS memo, "We Need An Independent AI Evaluation Clearinghouse (IAIEC)" by Garcia and Singh, dated 09.28.26 (S5, title and date taken from a search summary). It is a policy proposal with four recommendations (government oversight of auditors, accreditation with minimum standards, funding for entrants, clearinghouse as neutral assigner). | No (`fas.org` blocked) | **Existence confirmed (secondary); operating status: none found** | Confirm the memo text. Treat as proposal, not program. No adoption found. |
| MLCommons safety benchmarking | Search excerpts of the v0.5 paper (S6, arXiv 2404.12241): English-only; one use case; 7 of 13 hazards tested; short single-turn prompts; no over-refusal measure; no security testing; authors say v0.5 should not be used to assess AI safety. AILuminate v1.0 limits come from a single secondary article (S7). | No (`arxiv.org` blocked) | **Limits partly verified (search excerpts)** | Confirm the limits quote in the paper. Check MLCommons' own documentation for current v1.0 scope. |
| TrustScale claim-level evaluation API | The closest match is **ArgusRL**, a TrustScale product announced 2026-09-23 (S8, company press release). It splits responses into claims and returns verdicts with citations. The 95% acceptance figure and the claim of beating human evaluators come from that release. | No (press release fetch not possible; search excerpt only) | **Existence of product confirmed (vendor source); performance unverified** | Name in the original claim differs from the product name. Treat all performance figures as vendor-reported. |
| Open Badges 3.0 / W3C Verifiable Credentials | S9 and S10 (vendor and advocacy blogs) say 1EdTech approved Open Badges 3.0 as final in 2024 and that it builds on the W3C VC data model. S9 reports most platforms still use 2.0 as of March 2026. S11 (W3C overview page) describes VC notes; VCDM 1.1 status was not confirmed. | No (`www.1edtech.org`, `www.w3.org` blocked) | **Partly verified (secondary only)** | Confirm the 1EdTech final-spec page and the W3C VCDM status line. Use existing standards; do not define a new credential format. |

## Pinned sources

Each URL below came from a web search run on 2026-10-10. These are **search-result pins, not fetched pages**. The page content behind a row was read only as the search summary, so re-fetch each URL before relying on any quoted detail.

| ID | Source | URL | Type | Used for |
|---|---|---|---|---|
| S1 | Crowell client alert | https://www.crowell.com/en/insights/client-alerts/california-establishes-first-in-the-nation-framework-for-verifying-independent-ai-auditors | Law-firm summary | CA bills; no audit requirement to do business |
| S2 | aiunderstanding.org news | https://aiunderstanding.org/news/california-signs-bills-creating-first-state-ai-auditing-framework | News summary | CA bills; SB 813 as standards commission (disputed) |
| S3 | CIO Dive | https://www.ciodive.com/news/California-AI-auditing-legislation/830104/ | News | CA bills |
| S4 | Enterprise DNA | https://enterprisedna.co/resources/news/california-sb813-ab1405-first-us-ai-audit-law-september-2026 | Blog | CA bills; 2029 claim (uncorroborated) |
| S5 | FAS | https://fas.org/?p=48236 | Policy site (search listing) | FAS memo title and date |
| S6 | arXiv 2404.12241 | https://arxiv.org/pdf/2404.12241 | Primary paper (excerpts only) | MLCommons v0.5 limits |
| S7 | HPCwire | https://www.hpcwire.com/2024/12/10/shining-a-light-on-ai-risks-inside-mlcommons-ailuminate-benchmark/ | News | AILuminate v1.0 limits |
| S8 | AccessNewswire (TrustScale) | https://accessnewswire.com/newsroom/en/computers-technology-and-internet/trustscale-launches-argusrl-as-automated-ai-evaluation-surpasses-1225554 | Vendor press release | ArgusRL launch and claims |
| S9 | virtualbadge.io | https://virtualbadge.io/blog-articles/open-badges-3-0-what-is-the-status-in-2026 | Vendor blog | Open Badges 3.0 status |
| S10 | We Are Open co-op | https://blog.weareopen.coop/why-open-badges-3-0-matters | Advocacy blog | Open Badges 3.0 ratification |
| S11 | W3C | https://www.w3.org/TR/vc-overview-1.1/ | Standards page (not read) | VC overview; VCDM status unconfirmed |

## Implications for HIAE-001 (not decisions)

- No row supports a claim that HumanAIOS is subject to, eligible under, or accredited by any listed registry or standard.
- The FAS memo and TrustScale product are inputs for buyer and competitor discovery, not evidence of demand (see the non-claims in #780).
- Performance numbers from vendors are untrusted evidence claims under the HIAE design. They are not inputs to receipts.

## Next steps

1. Re-run this check from a network that can reach the five blocked hosts, and record the fetch date and URL for each primary source.
2. Counsel to review registry applicability before any statement about California law.
3. Keep this file as the source for any external wording until Z2 approves the non-claims language.

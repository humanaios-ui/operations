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
| CA SB 813 / AB 1405 signed 2026-09-09 | Several law-firm and news summaries agree both bills were signed 2026-09-09. Sources disagree on SB 813's content: one calls it the Independent Verification Organization framework, another says it creates a state AI standards commission. | No (`leginfo.legislature.ca.gov` blocked) | **Partly verified (secondary only)** | Confirm signing date and SB 813's content in chaptered text. Crowell reports the laws do not require an audit to do business in California; applicability to HumanAIOS is not established. |
| FAS Independent AI Evaluation Clearinghouse, 2026-09-28 | A FAS memo, "We Need An Independent AI Evaluation Clearinghouse (IAIEC)" by Garcia and Singh, dated 09.28.26, found in search results. It is a policy proposal with four recommendations (government oversight of auditors, accreditation with minimum standards, funding for entrants, clearinghouse as neutral assigner). | No (`fas.org` blocked) | **Existence confirmed (secondary); operating status: none found** | Confirm the memo text. Treat as proposal, not program. No adoption found. |
| MLCommons safety benchmarking | Search excerpts of the v0.5 paper (arXiv 2404.12241): English-only; one use case; 7 of 13 hazards tested; short single-turn prompts; no over-refusal measure; no security testing; authors say v0.5 should not be used to assess AI safety. AILuminate v1.0 limits come from one news article. | No (`arxiv.org` blocked) | **Limits partly verified (search excerpts)** | Confirm the limits quote in the paper. Check MLCommons' own documentation for current v1.0 scope. |
| TrustScale claim-level evaluation API | The closest match is **ArgusRL**, a TrustScale product announced 2026-09-23 (press release). It splits responses into claims and returns verdicts with citations. The 95% acceptance figure and the claim of beating human evaluators come from the company's own release. | No (press release fetch not possible; search excerpt only) | **Existence of product confirmed (vendor source); performance unverified** | Name in the original claim differs from the product name. Treat all performance figures as vendor-reported. |
| Open Badges 3.0 / W3C Verifiable Credentials | Vendor and advocacy blogs say 1EdTech approved Open Badges 3.0 as final in 2024 and that it builds on the W3C VC data model. A March 2026 post says most platforms still use 2.0. W3C pages found describe VC overview notes; VCDM 1.1 status was not confirmed. | No (`www.1edtech.org`, `www.w3.org` blocked) | **Partly verified (secondary only)** | Confirm the 1EdTech final-spec page and the W3C VCDM status line. Use existing standards; do not define a new credential format. |

## Implications for HIAE-001 (not decisions)

- No row supports a claim that HumanAIOS is subject to, eligible under, or accredited by any listed registry or standard.
- The FAS memo and TrustScale product are inputs for buyer and competitor discovery, not evidence of demand (see the non-claims in #780).
- Performance numbers from vendors are untrusted evidence claims under the HIAE design. They are not inputs to receipts.

## Next steps

1. Re-run this check from a network that can reach the five blocked hosts, and record the fetch date and URL for each primary source.
2. Counsel to review registry applicability before any statement about California law.
3. Keep this file as the source for any external wording until Z2 approves the non-claims language.

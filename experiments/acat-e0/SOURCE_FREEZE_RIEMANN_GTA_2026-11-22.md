# Witness E0 source freeze — Riemann and GTA VI (2026-11-22)

**Status:** EVIDENCE-EXCERPT FREEZE / Z1 RESEARCH / NOT ACAT QUALIFICATION. **Retrieval window:** 2026-11-22 17:35–17:36 America/Chicago (UTC−06:00), checked through live page-opening operations; snapshot recorded at **2026-11-22T17:36:42-06:00** (**2026-11-22T23:36:42Z**). **Method:** public first-party pages and publisher/SEC mirrors opened directly. Excerpts are deliberately short. Links identify mutable web pages, **not** immutable archived page copies, full-content checksums, or validated independent evidence custody. This Git commit freezes only the citations and excerpts below.

## Riemann: keep three separate claims and observation dates

### RH-01 — Original claimant (claimed theorem)
- **First-party URL:** https://alpo.ge/remark.pdf
- **Source:** Levent Alpöge's own note; announcement dated 2026-11-20. PDF page 1 visibly inspected, not merely a search snippet.
- **Exact short excerpt:** “I believe I have, working with Claude, discovered a proof of the Riemann Hypothesis.”
- **Observed proposition:** The author **claims** a Claude-assisted proof. The sentence is an author claim, not independently verified mathematics or an authenticated Claude task log.
- **Status:** FIRST_PARTY_AUTHOR_CLAIM; preserve exact publication date and distinguish from the later community statement.
- **Source limitations:** full 17-million-line Lean library not downloaded or run in this review; no archive hashes independently computed by this reviewer.

### RH-02 — First-party Lean/Mathlib community verification statement
- **First-party URL:** https://leanprover-community.github.io/blog/posts/riemann-hypothesis/
- **Source:** Lean and Mathlib communities' joint statement, endorsed by Lean FRO and Mathlib Initiative; posted **2026-11-21 13:55** on the page.
- **Exact short excerpt:** “We hereby certify that both the statement and the proof of the Riemann Hypothesis are correct.”
- **Observed proposition:** Community reports technical verification of statement equivalence, compilation, and multiple proof checkers. **This corrects earlier summaries that described external technical checks as entirely pending.**
- **Status:** FIRST_PARTY_COMMUNITY_CERTIFICATION_REPORTED. This is materially stronger than unverified author assertion. It does not by itself prove a Clay prize determination, a peer-reviewed expository paper, or human understanding of the argument.

### RH-03 — Independent checker run log / scope
- **First-party URL:** https://math.mit.edu/~drew/grh/
- **Source:** MIT-hosted verification page maintained by a direct verifier; dynamically updated. Retrieval window above, status may change later.
- **Exact short excerpt:** “All 175,187 modules compile (Lean v4.33.1, Mathlib v4.33.1)”
- **Observed proposition:** Page publishes specific compilation, kernel and comparator checks, including separate statuses for some long-running runs. Its technical scope is a **check log**, not an automatic governance decision.
- **Status:** FIRST_PARTY_VERIFIER_LOG_REPORTED; independent local re-execution NOT performed here.

### RH-04 — Earlier, different Anthropic result
- **First-party URL:** https://www.anthropic.com/research/riemann-zeta?trk=public_post_comment-text
- **Source:** Anthropic research statement, updated 2026-08-13 per its changelog.
- **Exact short excerpt:** “it has increased this bound from 41.6% to 67.2%.”
- **Observed proposition:** This concerns a lower bound on the fraction of Riemann zeta zeros on the critical line, **not** the November 20 full Riemann Hypothesis claim. Conflating them is a claim-identity failure.
- **Status:** FIRST_PARTY_EARLIER_PARTIAL_RESULT; does not rebut or establish the separate November theorem claim.

## GTA VI: issuer report versus independent audit

### GTA-01 — Take-Two / Rockstar original release
- **First-party URL:** https://ir.take2games.com/node/32701
- **Source:** Investor-relations release of Rockstar Games statement, dated **2026-11-20**.
- **Exact short excerpt:** “Grand Theft Auto VI day one retail sales* reached $3.79 billion”
- **Observed proposition:** Issuer publicly **reported** $3.79B day-one **retail sales**; source footnote qualifies it as company estimates through end of **2026-11-19** worldwide.
- **Status:** VERIFIED_ISSUER_REPORTED_ESTIMATE; NOT independent audited recognized revenue, confirmed receipts or an independently tested commercial outcome.

### GTA-02 — SEC-hosted exhibit of the same issuer release
- **First-party filing URL:** https://www.sec.gov/Archives/edgar/data/946581/000162828026075217/exhibit9918k.htm
- **Source:** Public SEC-hosted exhibit 99.1 of the issuer's November 20 release.
- **Exact short excerpt:** “*based on company estimates through end of day November 19th worldwide”
- **Observed proposition:** Confirms the estimate qualifier is part of the filing. **It is the same issuer statement**, not a second independent sales audit or separate measurement.
- **Status:** ISSUER_FILING_MIRROR / PROVENANCE_SUPPORT_ONLY.

## Proposed Witness E0 negative controls

1. Do **not** demote RH-02 to “no independent verification” when a directly accountable community certification now exists; preserve technical scope and time.
2. Do **not** infer Clay-prize adjudication, unanimous mathematical comprehension or operational ACAT qualification from RH-01 or RH-02.
3. Do **not** merge RH-04's August partial-zero bound with RH-01's November full-theorem claim.
4. Do **not** upgrade GTA-01/02 to externally audited financial revenue because they share a company-originated statement.
5. Make source freshness explicit: newer primary statements supersede stale uncertainty about whether technical verification exists; prior posts are retained as dated historical observations, not deleted.

## Privacy, source handling and human approval

These sources are public. No private Gmail/agent records or user data are frozen. No webpage's full copyright text is mirrored in the repository. The evidence freeze contains short quoted excerpts and source claims only; it does not prove original page immutability, full original bytes, the entire proof, publisher audit, or a witnessed real agent correction. The paired `test_witness_intake.py` fixtures are synthetic and do not fetch or execute any source or model. No real ACAT scores pending #750; Witness and GitHub remain non-authorizing.

**References:** #775 cross-agent historical intake; #1230 Living Laboratory; #750 instrument blocker; draft PR #1307 synthetic receipt gate. **AUTHORITY_EFFECT=NONE; RELEASE=HOLD.**

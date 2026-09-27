# Z1 Candidate Block: ACAT Distribution Plays (Externally-Sourced Playbook)

**Candidate ID:** Q-ACAT-DISTRIBUTION-PLAYS-01
**Proposed by:** Claude (Z1 Proposer)
**Date:** 2026-09-27
**Type:** H (Hypothesis / go-to-market proposal — no falsifier required; this is a distribution strategy, not a system claim)
**Source:** "Do Not Waste the Next 12 Months Building an Audience" (Capital of One, Substack) — externally authored, applied here by Z1

## Claim

Of the active/planned repos in this ecosystem, **ACAT is the only one that is both live and meant to face external users today**, and it is the only candidate for which the source article's distribution plays are actionable right now.

## Evidence

- `SEED.md`: "Assessment tool | humanaios.ai/assess.html | Live · Supabase writes" — ACAT's free assessment is publicly reachable today.
- `acat/docs/MARKETPLACE_ROADMAP_V1_0_S061226.md`: states the go-to-market thesis directly — "ACAT behavioral assessment is publicly accessible at `/assess`" and positions it as "the only independent behavioral audit backed by an open corpus" for compliance buyers (EU AI Act, NIST AI RMF). The same document concedes: "Marketplace launch is post-charter; no public-facing deploy before block clears" and "No payment processing, no marketplace routing, no API key system currently live."
- `REGISTERED.md` (Q-GRANT-BROKER-PHASE-2B-01): grant-search-dashboard is designed for external nonprofit users but is still `⏳ pending` — mock IRS 501(c)(3) validation, placeholder API domain, not built.
- `board/worker.mjs` header, quoting Z2 directly: "I don't want any public, I want to have to login to open the board." — internal-only by explicit design, not a distribution candidate.
- `ZONE_REGISTRY.md` / `PLANNED_REPOS.md`: acat-inspect, acat-x, acat-dashboard, acat-observatory, humanaios-internal, lasting-light-ai, research are all described as internal tooling, auditing, or a frozen-papers archive — none are user-facing products.

Conclusion: distribution plays require something live to route traffic to. ACAT's `/assess` is the only qualifying surface.

## Proposal: Two Plays (per the source article's own rule — "pick two: one compounding, one faster")

**Faster channel — Play 3, "Build a Free Tool That Sells For You."**
ACAT's `/assess` is already this free tool. Proposal: formalize the funnel from the existing free assessment to a paid, deeper compliance report/audit for the same buyer. First steps (adapted from the source):
1. Confirm the free assessment gives a real, useful result on its own (not a teaser) — it should already do this.
2. Make the paid product ("full compliance report," "ongoing monitoring," or similar) the obvious next click after a completed assessment, not a separate discovery.
3. Get `/assess` listed in relevant roundups/directories (AI-safety tooling lists, compliance-tool directories) now that it's a working free tool with real output.

**Compounding channel — Play 4 + Play 2, Programmatic SEO + Answer Engine Optimization.**
ACAT already holds structured assessment data across AI models and behavioral dimensions. Proposal: build one page per (model × regulation) pair — e.g. "GPT-5 EU AI Act compliance," "Claude Opus NIST AI RMF score" — from a single template, using real assessment data as the differentiator (per the source article's Play 2 guidance: publish on a domain you own, publish 100 pages first, interlink them). This doubles as AEO bait, since compliance officers ask ChatGPT/Perplexity/Gemini exactly these questions and current answer engines have no structured source to cite.

**Deferred (not part of this proposal — kept out to respect "pick two," not seven):**
- MCP-server-as-channel (Play 1) — plausible later if/once ACAT has an API, not before.
- Shareable-artifact/badge (Play 5) — needs an existing base of AI vendors motivated to display scores; premature pre-launch.
- Buying an existing audience (Play 6) / affiliates (Play 7) — cost money or established relationships not yet in place pre-revenue.

## Falsifier

If, 60 days after both plays ship (free→paid funnel copy live on `/assess`; first 20 programmatic-SEO model×regulation pages published and indexed by Google), neither shows a measurable effect — no attributable increase in `/assess` completions or funnel click-through versus the pre-launch baseline, and the SEO pages register zero organic impressions in Search Console — the plays are falsified. In that case, drop them and select two of the five deferred plays instead rather than doubling down.

## Ratification Request

1. Accept ACAT as the sole current target for external distribution work (no other repo qualifies today per evidence above).
2. Accept the two named plays (free-tool funnel + programmatic SEO/AEO) as the current distribution priority, explicitly deferring the other five.
3. Assign a Z3 executor (per ZONE_REGISTRY.md) to scope the programmatic-SEO template and the free→paid funnel copy as concrete next tasks.

## Z2 Decision Gate

- [ ] ACCEPT — proceed with both plays as scoped above
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

**Awaiting Z2 ratification by:** 2026-09-29 (48h window)

---

*Generated by Claude (Z1) for Z2 (Night) ratification*

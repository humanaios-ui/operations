# E0 News Observation Adapters — GDELT + Miniflux (#1238)

**Status:** E0 offline-only proposal implementation; human approved E0 on 2026-11-15 in issue #1238.
**Authority:** NONE. **Execution:** DISABLED.
**Out of scope:** live fetching, credentials, deploying Miniflux, API-provider calls, publishing, graph/database writes, Witness allowlist edits, automatic ResourceCandidate promotion.

## Existing seams reused

- resource_miner.sources.rss: existing RSS/Atom collection. This E0 does not replace it.
- resource_miner.normalize.canonicalize_url: existing canonicalization utility, preceded by stricter public-HTTPS and query-key checks.
- resource_miner.models: existing ResourceMine / ResourceCandidate remain unchanged.
- resource_miner.witness_bridge: unchanged. The current public source allowlist excludes GDELT and Miniflux. **Do not pass observations into this bridge by relabeling their source.**

## E0 interface (pure, local functions)

resource_miner.news_observations_e0 exposes:

- parse_gdelt_fixture({"articles": [...]}, observed_at="2026-11-15T20:00:00+00:00")
- parse_miniflux_fixture({"entries": [...]}, observed_at="2026-11-15T20:00:00+00:00")
- group_exact_url_duplicates([...])

Input is a pre-existing, rights-cleared JSON object, not a live API call. Each output record is a **source observation**, explicitly **UNVERIFIED** and **not** a resource lead. No event/claim inference is performed. GDELT seendate means provider-seen time, **not publication time**. Miniflux published_at is a source-provided publication claim, not independently verified.

The output excludes full article content and credential-like fields, and accepts only fixed, typed metadata. Input size is bounded to 256 KiB and 100 rows per provider. The URL validator accepts public HTTPS hostnames without credentials or secret-bearing query parameters. It never fetches the URLs, so redirect and DNS-rebinding defenses are **E1 requirements**.

Exact canonical URL matches are grouped only as EXACT_URL_MATCH; they do not prove source independence, shared event identity, agreement or accuracy. A digest is an integrity aid, not a signature or proof of source authenticity.

## Run offline tests

From humanaios-funding-pipeline/resource-miner:

    python3 -m unittest discover -s tests -p 'test_news_observations_e0.py' -v

The synthetic tests generate **20 GDELT records and 20 Miniflux records**, then test URL-matching, no network, source/date handling, non-promotion, and rejection of hostile or oversized inputs.

### Independent review before E1

1. Run tests on the exact PR commit and record test logs and SHA; do not equate test source code with passing results.
2. Check for unit-level failures and ResourceCandidate/Witness boundary regressions.
3. Check fixture shape against current official GDELT DOC and Miniflux API documentation; sample fixtures are not proof of real API contract compatibility.
4. Check copyright/licensing and attribution for each chosen source before retaining any fetched article content.
5. Document bounded live-fetch architecture separately: TLS, host/DNS allowlist, redirect revalidation, timeouts, backoff, quota limits, secret custody and human admission.

**E1 remains NOT AUTHORIZED.** Do not use a GitHub PR merge or this document as an authorization receipt.

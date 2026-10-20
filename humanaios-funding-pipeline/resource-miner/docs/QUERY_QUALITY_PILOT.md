# Resource Miner query-quality pilot (read-only, no admission)

**Scope:** existing HumanAIOS `POST /api/intent` public discovery path in
`humanaios-funding-pipeline/resource-miner/`. This is not a new search engine,
vector index, general-purpose RAG system, private mine, or grant adjudicator.

## Code-based findings and change

The current Miner transforms already-discovered `ResourceCandidate` records
to verified-for-display HTTPS links from two allowlisted source names. The
existing matcher counted overlapping title/description/taxonomy words and did
not consult an independent web search engine.

The pilot retains that **original lexical score** and all security checks.
It adds a **second ranking lane** from declared candidate tags, mechanism
types, affordances, and need labels, merged with reciprocal rank fusion
(k=60). This is deliberately *lexical + declared taxonomy* rank fusion, **not**
BM25 + dense vector retrieval. The raw human objective is preserved.
Structured identifiers must match exactly when present. Only explicitly
excluded loan/debt mechanisms are filtered. A bounded English/Spanish term
dictionary improves a known slice; it is not comprehensive translation.
Each returned candidate includes its lexical and taxonomy ranks, source link,
timestamps (if supplied), and explicit verification/eligibility boundaries.
No model call, external URL fetch, persistent user profile, application,
or authorization occurs. Unobserved sources remain unobserved.

## Run reproducible tests

From this Resource Miner directory:

```sh
python3 -m unittest discover -s tests -p 'test_query_quality.py' -v
python3 -m unittest discover -s tests -p 'test_intent_os_bridge.py' -v
python3 -m tools.query_quality_benchmark fixtures/query_quality_synthetic.json
```

The synthetic fixture is not observational evidence of production gains.
The benchmark reports P@10, R@10, MRR@10 and nDCG@10 for candidate IDs, with
explicit `NOT_MEASURED` status for an ordinary web-search comparator.
An independent search baseline requires **actual captured search results**
mapped to resource IDs, with search engine and observation time. Even then
the script labels those results **caller-supplied, unverified**, and never
pretends to have queried that engine. Human judgments and adjudicated source
identity are necessary before asserting superiority.

**Metric denominator:** precision@10 uses denominator 10, even where
fewer than 10 candidate results exist; unanswerable cases receive null
recall/nDCG rather than an invented success percentage.

## Research-derived next work, explicitly not implemented

1. Build representative **real query / source evidence** gold labels for
   opportunities, entitlements, bounties and contracts; include Spanish,
   typos, negative constraints, rare program IDs, stale rounds and
   near-duplicates. Audit source exposure and false exclusions per slice.
2. Capture a same-time normal-search baseline for each query and a pinned
   Miner snapshot; collect ordinal relevance judgments blind to source.
3. Where a real full-text index and approved embedding service exist, compare
   baseline lexical vs BM25 vs vector vs hybrid fusion and reranking;
   **do not claim dense retrieval is already deployed**.
4. Enhance canonical document identity, last-verified evidence spans,
   provenance and freshness. Keep `MATCHES_OBSERVED` separate from rights,
   control or eligibility, and `ZERO_MATCHES_OBSERVED` separate from
   `NO_ENTITLEMENT`.
5. Run protected CI and independent review on the exact PR head. Require
   ordinary Coordinator admission and human authority before merge/deploy.
   Do not infer production readiness from local or synthetic tests.

## Video-derived adversarial source handling

The shared earlier *Read YouTube Video* discussion named persuasion cues
including status mimicry, reverse disqualification, the illusion of immense
labor, downward vocal drop, conditioned pressure, eye-line detection, and
cooling the mark out. Those are **possible adversarial risk lenses**, not
verified observations about any named organization or source.

Apply them to **resist misleading opportunity promotion**, not to manipulate
users: expose source identity and candidate source URLs requiring official-source verification rather than trusting
an authority-sounding title; preserve negative/unknown evidence; flag
unsupported guarantee/pressure language for human review; avoid ranking
based on claimed effort or a persuasive tone. A bounded `source_risk.py` implementation now surfaces only lexical review flags for
unsupported outcome promises, claimed official endorsement, urgency language,
and unusual payment requests. Flags do not alter ranking or assign fraud.
Speech intonation and eye-line cannot be inferred from a plain text record. Never assign a fraud verdict
from regex matches. A separate witness review, consent, and appropriate
evidence are required for higher-risk conclusions.

## Acceptance boundaries

- Existing public-source allowlist, IP/host/scheme restrictions and stale
  deadline exclusions pass unchanged; private sources remain inaccessible.
- Exact-identifier queries cannot return mere near-matches.
- Spanish test slice finds an explicitly supported equivalent; unsupported
  languages do not receive fabricated translated claims.
- Explicit no-loan requests do not receive declared financing mechanisms.
- No applicant eligibility, authority, application, source currentness,
  fraud, or successful acquisition is asserted by ranking.
- Benchmarks distinguish local synthetics, caller-supplied web baselines,
  observed production outputs, and unmeasured categories.
- Rank quality changes and false-negative risk are reviewed *per slice*,
  not just by aggregate average.

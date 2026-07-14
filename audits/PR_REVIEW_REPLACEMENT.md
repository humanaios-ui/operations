# PR review: retire the paid Claude layer, go free + OSS (S-071426)

## What changed
- **Retired `claude-review.yml`** — it ran `anthropics/claude-code-action`, which needs a
  funded `ANTHROPIC_API_KEY` (per-PR token cost). It was unfunded, so it added no review
  value, and its `claude` check was the **dominant SMAG gap-driver** (red on 6 of 9 PRs,
  merged over — see `SMAG_GAP_TREND_ANALYSIS.md`). Removing it both cuts a dead paid
  dependency and cleans the gap signal.
- **Added `semgrep-review.yml`** — free, **keyless**, open-source static analysis
  (Semgrep OSS `p/` rulesets) over the PR's changed Python, surfaced as **advisory**
  GitHub `::warning` annotations (inline on the changed files; never blocks a merge).
  Self-contained: depends only on the Semgrep CLI + first-party `actions/checkout` and
  `actions/setup-python` — no third-party action, no token, no secret to fund.

Safe to retire: the required status check `guard` comes from `no-op-pr-guard.yml`, **not**
claude-review — so merges are unaffected.

## The free PR-review stack now
No single tool replaces an LLM reviewer; the review *function* is covered by a stack of
free, keyless gates that were already mostly here:

| Concern | Tool | Cost |
|---|---|---|
| behavioral-not-marker (IC-045: real bodies, no dead code, importable) | `behavioral-compliance.yml` (AST) | free |
| security anti-patterns + language smells (the new layer) | `semgrep-review.yml` (Semgrep OSS) | free, keyless |
| quality / maintainability | `sonarqube.yml` | free (community) |
| supply-chain / security posture | `scorecard.yml` | free |
| second-opinion LLM review | `auto-request-copilot-review.yml` (Copilot) | included |

Together these cover the lens `claude-review` was configured for (behavioral verification,
intent-vs-diff, security) without a paid API.

## Why not "just use a free AI reviewer"
Every open-source AI reviewer surveyed (PR-Agent/Qodo, Vercel OpenReview, Open Code Review)
is self-hostable but still needs **either an LLM API key** (OpenAI/Anthropic/Gemini — a
cost, and a credential) **or self-hosted GPU compute** (Ollama on a self-hosted runner —
infrastructure). A "free AI reviewer" that rivals Claude with zero cost and zero key does
not exist. Given the driver here was *cost*, and the standing rule is *never raw-hold or
mint a credential*, the honest free answer is **keyless deterministic analysis (Semgrep)**,
not another LLM.

## Optional future upgrade (operator decision, not wired)
If an LLM review layer is wanted later, do it credential-safely:
1. **Free-tier hosted LLM** (e.g. a provider free tier) — set the key **only** as a GitHub
   Actions secret (never in a file or an AI context), point PR-Agent/Open Code Review at it.
   Watch rate limits; keep it advisory.
2. **Local Ollama on a self-hosted runner** — 100% free + keyless, but you own the runner.
Both are strictly optional; the keyless stack above is the baseline.

## Connection to the recursive-learning loop
Retiring the `claude` check removes the one recurring failure that dominated the SMAG
gap-driver tally. After this lands, future `gap_rate` reflects *real* calibration friction
rather than one broken/unfunded gate — which is the precondition (from the round-1 gap-trend
analysis) for the gap signal to be worth trending and, eventually, feeding back.

## Follow-ups for the operator (Zone-3)
- Confirm code scanning / advisory comments render as intended on the first PR.
- Pin `actions/checkout` / `actions/setup-python` to full commit SHAs (supply-chain; the repo convention).
- Only after tuning: consider promoting `semgrep-review` to a required check.

## Sources
- [PR-Agent (open-source PR reviewer)](https://github.com/The-PR-Agent/pr-agent)
- [Open Code Review — quality gate for AI-generated code](https://github.com/marketplace/actions/open-code-review)
- [Vercel OpenReview (self-hosted AI review bot)](https://github.com/vercel-labs/openreview)
- [Free AI code review tools 2026 (comparison)](https://gitautoreview.com/compare/free-ai-code-review-tools)
- [15 open-source AI code review tools 2026](https://dev.to/rahulxsingh/15-open-source-ai-code-review-tools-2026-605)

# HPRA v0.1 — Canonical Editorial and Legacy-Agent Translation Contract

**Objective:** #818. **Implementation PR:** #819. **Preserved coordination:** #820 (closed, unmerged).
**Status:** Candidate contract; requires independent review, tests, and authenticated admission.

## Existing source of truth

- `deliverables/substack-publication-plan.md` defines **The Witness Stand** editorial identity, the Witness Problem, attraction-not-promotion, and evidence/limitation standards.
- `LinkedIn_Substack_Content_Strategy.md` defines Substack as a practitioner/research deep-dive channel, GitHub as the execution/evidence layer.
- `tools/agents/substack_content_agent_v1.py` is a pre-existing **draft generator** for forecasting data; it is not a publishing authority.
- `tools/substack_agent/observer.py` (#819) is a new **untrusted public-feed observation/draft proposal** prototype; it does not replace canonical URA/Resource Miner data contracts.

Do not create a second editorial brand, publishing executor, or competing data registry.

## Three editorial projections (each DRAFT_ONLY)

1. **Correspondence:** human/AI exchange, with consent and source attribution; preserve correction chronology and human voice.
2. **Experiment:** question, method, observations, contradictory evidence, corrections, limitations; separate hypotheses from verified findings.
3. **Evidence record:** PR/issue/commit-linked case study; quote actual check results and distinguish a zero-file scan from an examination of implementation.

The same normalized evidence object may support multiple projections, but one article cannot self-verify its own claims.

## Mandatory evidence envelope

Every proposed article MUST include:
- `edition`: `CORRESPONDENCE | EXPERIMENT | EVIDENCE_RECORD`
- `title`, `body`, `content_sha256` computed from exact approved payload
- `references[]`: source URL, exact revision/commit if available, retrieved timestamp, issuer, evidence digest, verification status
- `claim_ledger[]`: claim, reference IDs, `VERIFIED | HYPOTHESIS | UNVERIFIED`, limitations
- `editorial_status: DRAFT_ONLY` and `publication_authorization: NONE`

The publisher adapter MUST reject missing or stale references, unverifiable claims presented as findings, mismatched digests, and missing independent human authorization; none exists in v0.1.

## Legacy-agent safety issue to resolve before adoption

`tools/agents/substack_content_agent_v1.py` currently returns `_mock_data()` when Supabase is unconfigured or its query fails. This is acceptable **only for clearly marked synthetic tests**; it is unacceptable for production research copy. The agent also labels draft copy `Published` prior to any independently verified publication receipt.

Required migration:
1. Preserve the prior implementation and identify its actual callers/triggers.
2. Make production data-source failure return `NO_VERIFIED_EVIDENCE` (fail closed), never synthetic fallback.
3. Mark every synthetic fixture `SYNTHETIC_TEST_ONLY`; do not allow such fixtures to reach public draft claims or revenue metrics.
4. Change any `Published` label before publication to `Draft generated`.
5. Derive averages only from validated, complete numeric observations with explicit denominators; do not treat 0 as missing.
6. Prove these boundaries with regression tests and protected exact-head CI.

## Admission semantics

- `NO_FILES_EVALUATED` != `IMPLEMENTATION_VERIFIED`.
- A scanner success on zero evaluated changed files means **NO_SCOPED_EVALUATION**, not positive security evidence.
- No draft or check result grants Z2 public-content approval.
- An authenticated human review is necessary; all required independent checks and exact-head admission evidence are separately required.
- PR #820 is historical evidence, not an alternate implementation path.

## First article candidate

**The Witness Stand — Evidence Record:** “Two AI Agents, One Assignment, and a Success Report That Proved Nothing.”

Tie claims to #818, #819, #820 and exact relevant workflow runs. Keep the article as a proposal until evidence verification and explicit human editorial approval.

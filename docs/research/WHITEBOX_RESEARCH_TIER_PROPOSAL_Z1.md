---
document_type: Z1 program proposal, not a registry entry
status: Z1 DRAFT — not ratified, scope/cost decision required before any spend
proposed: continuation of S-071126-01
requires: Zone 2 decision on which tier (if any) to authorize; Tier 2/3
  additionally require Night's own cost/infrastructure judgment, outside
  Claude's competence to estimate precisely
---

# White-Box Research Infrastructure — Tiered Proposal

## 0. What this is and isn't

This proposes a path from ACAT's current black-box-only measurement
(verbalized self-report text, no access to model internals) toward
white-box access — logits, activations — for a specific, named reason:
**Guo et al. (2017) temperature scaling, the field's standard post-hoc
calibration fix, requires logit access ACAT currently has none of.**
This is not a general "let's do interpretability" pitch — it targets
one concrete capability gap directly connected to F-22 (AI Systems Lack
Interoceptive Analogue): a logit distribution is the closest thing a
transformer has to an internal confidence state, and it's currently
invisible to this entire research program.

This is NOT a proposal to pretrain a model from scratch. That is a
different order of undertaking (widely reported at hundreds of millions
of dollars in compute for a frontier-adjacent model) and is neither
necessary nor proposed here. Every tier below uses an existing model —
either through API access you already have, or an existing open-weight
model you would host, not build from nothing.

## 1. Three tiers, cheapest and lowest-commitment first

### Tier 1 — Gray-box via existing provider APIs (no new infrastructure)

Some inference providers expose `logprobs` (log-probabilities for the
top-N candidate tokens at each generation step) through their standard
API, with no model hosting required at all. If any provider already in
your corpus (per F-52's role_method data: ChatGPT, Gemini, Claude, Llama
variants, and others referenced across sessions) exposes this, Guo-style
temperature scaling becomes applicable *today*, on infrastructure you
already have relationships with.

**Cost:** effectively zero beyond existing API spend — this is a
capability check, not a new expenditure.

**This is the pilot, described in Section 2 below.**

### Tier 2 — Open-weight model, self-hosted

Host an existing open-weight model (Llama/Mistral/Qwen/Gemma-class,
exact selection is a Zone 2 decision informed by Tier 1 results) where
you own full logit access by construction, not dependent on any
provider's API choices. This is also the tier where a subset of the
existing ACAT corpus becomes directly comparable to SELF-[IN]CORRECT's
own experimental setup (they specifically needed open weights to test
the autoregressive-vs-non-autoregressive architecture question — the
same open-weight requirement applies here).

**Cost, realistic bands, not precise quotes:** GPU compute for hosting
and inference on a mid-size open model (7B–70B parameter class) —
ranges widely by provider and whether spot/on-demand pricing is used;
this is a real, recurring infrastructure cost, not a one-time purchase,
and should be sized against actual session/query volume rather than
estimated here without that data. Flagging explicitly: I am not
positioned to give Night a defensible dollar figure without knowing
target query volume and whether cloud GPU rental or a fixed local
machine is preferred — that's a scoping question for Zone 2, not
something to guess at.

**Prerequisite:** Tier 1 pilot results — if existing providers already
expose usable logprobs, Tier 2's marginal value narrows to cases where
independence from provider infrastructure specifically matters (e.g.,
per F-50's parallel-instrument-independence logic, or where a provider
doesn't expose logprobs at all).

### Tier 3 — Full interpretability tooling (activation extraction, probing)

Real, existing open tooling exists for this (hook-based activation
capture libraries, sparse-autoencoder feature extraction, the general
class of tools Anthropic's own published interpretability work uses,
e.g. persona-vector-style activation monitoring). This is genuinely
substantial engineering on top of Tier 2 — not a quick extension.

**Cost:** meaningfully higher engineering time than Tier 2, and depends
entirely on what specific readings are wanted (a single steering vector
for one trait is a much smaller project than a general activation-
monitoring pipeline). Not sized here — this tier shouldn't be scoped
until Tier 2 exists and a specific Tier 3 research question is named.

## 2. Tier 1 pilot — concrete, runnable now, no infrastructure commitment

**Goal:** determine, for each provider currently in the ACAT corpus,
whether `logprobs` (or an equivalent confidence signal) is exposed via
their standard API, at what granularity, and at what cost.

**Method:** a single, cheap probe call per provider, checking for a
`logprobs` parameter/response field, run once per provider, logged to a
small results table — not a new corpus write, a separate scoping
artifact.

```python
# tier1_logprob_capability_probe.py — sketch, not yet built/tested
# Checks, per provider already in the corpus, whether logprobs are
# exposed at all, and at what granularity (top-1 only vs top-N vs
# full vocabulary distribution -- these are meaningfully different
# for temperature-scaling purposes).

PROVIDERS_TO_CHECK = [
    # populated from live role_method / provider values in
    # acat_assessments_v1 -- per IC-032 discipline, query live values
    # first, do not hardcode a list here from memory
]

def probe_logprob_support(provider_client, test_prompt: str) -> dict:
    """Returns capability tier: 'none' | 'top1_only' | 'top_n' | 'full_vocab'.
    Actual implementation is provider-SDK-specific and needs a live
    credential per provider to run for real -- this is a sketch of the
    check's shape, not a working tool, since no provider credentials
    are available in this sandbox."""
    raise NotImplementedError(
        "Requires live provider credentials not available in this "
        "session. This is the Tier 1 pilot's actual first task, not "
        "something answerable from here."
    )
```

**Deliverable of the pilot:** a short table — provider, logprob support
tier, any cost implications of requesting logprobs (some providers price
this differently), and a recommendation on whether Tier 1 alone closes
enough of the gap to defer Tier 2 indefinitely.

**Honest limitation on what I can do right now:** I don't have live
credentials for your providers in this sandbox, so I can't run this
probe for real today the way I ran the other tools this session. This
is genuinely the next concrete step, but it requires either Night
running it with real credentials, or a connected tool session with
provider access.

## 3. Recommendation

Authorize Tier 1 only, now — it's free relative to existing spend and
answers the question that determines whether Tier 2 is even worth
scoping. Table Tier 2/3 cost estimation until Tier 1 results exist;
estimating GPU infrastructure cost without knowing what Tier 1 reveals
would be guessing dressed as a budget.

## 4. Open items for Zone 2

- Confirm this is worth pursuing at all relative to other funded/
  planned work (Longview Digital Minds deadline, HA-000, other standing
  priorities) — this is new scope, not a continuation of anything
  already committed.
- If authorized, who runs the Tier 1 pilot (requires live provider
  credentials Claude does not have here).
- Whether Tier 2 model selection, if it comes to that, should favor
  architectural diversity (autoregressive vs. non-autoregressive, per
  the SELF-[IN]CORRECT finding that architecture affects the self-
  correction/discrimination gap) as a deliberate research variable,
  not just convenience.

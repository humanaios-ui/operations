# Q-WITNESS-LEDGER-TIER0-EXTENSION-01

**Tier:** 2 (Architecture / Governance)
**Status:** Candidate (awaiting Z2 ratification)
**Proposed by:** Claude (Z1 proposer)
**Date filed:** 2026-09-27
**Related:** Q-INTENT-OS-WITNESS-LEDGER-01 (ratified 2026-09-19), Issue #559 ("Design: scaling Seed Constitution ratification from single-ratifier to public participation")
**Session:** https://claude.ai/code/session_01TFuADkhUVPAQ7fte6j6an1

---

## Problem Statement

Issue #559 designs *how* a ratification decision gets made once the public participates (weighted quorum / liquid delegation / sortition panel — sortition recommended as v1). It explicitly does not resolve a prior question: **who is "the public" as a trackable, observable unit**, given the constitution's own onboarding ask is for anonymous participation — humans, with or without a paired AI agent.

Z2 (Night) framed the requirement directly (2026-09-27, this session): a first, open participation tier where anyone can join as a **tokenized, anonymous human agent** (with or without an AI agent), and where that tier's own record becomes the **single source of truth (SSOT)** every later ratification tier is built on — "that way every individual can be observed" without requiring real-identity disclosure.

This is not a new ledger problem. `Q-INTENT-OS-WITNESS-LEDGER-01` already solved the adjacent case: an append-only, schema'd record binding a tokenized actor to a decision, timestamp, and rationale — built for Z3 executor onboarding, where the stated goal was explicitly "enables onboarding independent Z3 executors" via `/api/z2-authorized-machine-identities`. The public-participation tier needs the same primitive (tokenized actor → attributed action → durable record) one layer earlier in the pipeline, for a different actor population (Tier 0: the public) feeding a different downstream consumer (a sortition panel's pool, per Issue #559 Option C, instead of a Z3 assignment).

## Proposal: extend the Witness Ledger with a Tier 0 actor class, rather than building a second ledger

1. **New `actor_role` value: `Tier0`** (alongside existing `Z1`/`Z2`/`Z3`), for anonymous public participants. `actor_email` (a real, verifiable identity per Principle 2) does not apply here by design — replace it for this role with `actor_token`: an opaque, stable pseudonymous identifier issued at onboarding, with no reverse-mapping stored in the ledger itself. Anonymity and observability aren't in tension: the token is the observable unit, not the person behind it.
2. **New `decision_class` value: `participate`** (alongside existing `approve|propose|execute|ratify`) — covers a Tier 0 actor's constitutional input (comment, amendment suggestion, sortition-panel testimony) without implying it carries ratification weight on its own.
3. **`artifacts.pairing`** (optional field): if a Tier 0 actor operates with a paired AI agent, record that pairing's own token here — same "human decision + machine execution" linkage the original ledger proposal already modeled for Z1/Z3, just available one tier earlier and opt-in rather than assumed.
4. **This ledger becomes the pool Issue #559's Option C (sortition panel) draws from.** A random, stratified sample of Tier 0 tokens — not real identities — is what makes sortition Sybil-resistant per Issue #559's own scoring ("small verified pool is enough"): the ledger is what makes that pool verifiable-as-a-population without being verifiable-as-individuals.
5. **No change to Phase 1–3 rollout already ratified for the Z3 case** — this is an additive actor class on the same schema and ledger, not a competing design. Implementation order: Tier 0 token issuance and the `participate` decision class are natural Phase 2/3 work per the existing roadmap, not a new phase.

## Why extend rather than build new

- Avoids two parallel "who did what, when" records for the same repo — the exact process-vs-product ceremony risk already flagged in `F-CAND-PROCESS-VS-PRODUCT-RATIO-01` (filed this session): more governance infrastructure than product, unless it reuses what's already ratified.
- The original ledger's own stated purpose — "As HumanAIOS onboards independent Z3 executors (10s→100s of humans and machines), you can't maintain a hardcoded... list" — is the identical scaling problem the constitution's public-participation ask has, just for an open population instead of a curated executor pool.
- Keeps Issue #559's four open design variables (weight, anti-capture, rollback, human backstop) answerable in terms of ledger data instead of a fifth, ledger-shaped thing being invented to answer them.

## Falsifier

Falsified if, once Tier 0 onboarding ships: (a) a Tier 0 token is issued without a corresponding ledger entry, (b) a token's `actor_token` is found reverse-mapped to a real identity anywhere in the ledger or its access layer, or (c) a sortition panel (Issue #559 Option C) is convened from a pool that cannot be traced to this ledger. Any of these means the extension failed to deliver the "observable population, anonymous individuals" property it was proposed for, and should escalate to an IC rather than a routine revision.

## Z2 Decision Gate

- [ ] ACCEPT — extend the witness ledger schema as proposed; Tier 0 token issuance becomes Phase 2/3 work under the existing roadmap
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

**Awaiting Z2 ratification by:** 2026-09-29 (48h window)

---

*Generated by Claude (Z1) for Z2 (Night) ratification*

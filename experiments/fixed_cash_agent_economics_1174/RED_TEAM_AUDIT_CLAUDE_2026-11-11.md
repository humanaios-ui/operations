# Independent-in-form, not-independent-in-fact review — #1174 fixed-cash agent trading economics (2026-11-11)

**SOURCE:** Human operator asked for a second red-team audit, run in Claude Code against the `operations` repo.
**STATUS:** REVIEW / RECOMMENDATIONS ONLY. **AUTHORITY_EFFECT:** NONE. **EXECUTION:** DISABLED. No labels, assignees, accounts, or trades changed by this file.

## Conflict-of-interest disclosure (read this before the findings)

The issue's own rule is: *"independent reviewer cannot be the graded agent."* The proposed cohort is ChatGPT, GitHub Copilot, **Claude**, and Grok. I am Claude. By the issue's own rule, **this audit does not count as the independent review either, for the identical reason the Grok-authored review (2026-11-11, comment 4) didn't.** I have the same structural incentive problem Grok's disclosure named: a cohort member evaluating the rules it would be graded under.

Two things make this worse than "swap in a different AI":

- **I read the existing Grok-authored review before writing this one** (it was already posted on the issue when I started). So this is a second-opinion pass building on a prior one, not an independently-blinded one. Where I agree with its findings I say so plainly rather than restating them as if newly discovered.
- **"Ask a different AI" does not reach independence.** The second annex on this issue already names Gemini as a *future* roster-expansion candidate ("additional actually paid services discovered in a bounded subscription census"). A reviewer who is a candidate for the very roster being designed is not independent of the outcome even if not in the *initial* N=4. By that logic, essentially every mainstream paid AI assistant is a latent cohort candidate, so **AI review alone cannot satisfy the issue's own independence rule — the independent reviewer this issue calls for has to be a human with no HumanAIOS LLC equity or profit stake**, not merely "not one of the four named services."

Everything below is offered as engineering/governance critique, not as the independent sign-off the issue requires before any further gate.

## Overall recommendation

**REVISE**, concurring with the Grok-authored review's bottom line: the governance scaffolding is careful, but proceed only as a forward-paper study, and only after the changes below (and the prior review's) are folded into the body. I have no disagreement with that review's 13 findings; I'd particularly underline **#3 (training-data contamination invalidates point-in-time backtests)** as the single most important catch in the whole thread so far, and sharpen it below (new finding #18). The rest of what follows is additional ground that review didn't cover.

---

## New findings

### Critical

**14. Platform terms-of-service / allowlisting is a separate, non-engineerable gate — a correct internal gateway does not cure it.**
The internal order gateway (ledger, atomic reservation, kill switch) only solves *internal* fairness between the four sub-agent subledgers. It does nothing for *external* compliance: Coinbase's own "Coinbase for Agents" docs condition agent access on **client allowlisting**, and the body itself records this as unverified. Running four model-driven sub-agents against one personal brokerage account, splitting one account window into subledgers that the broker never agreed to treat as separate clients, is a structure the broker has not approved in writing. If it falls outside what Coinbase (or any broker) has actually allowlisted, the risk is **account freeze or closure of the operator's personal account**, independent of whether the gateway math is flawless. This has to be verified in writing from the broker before the gateway's correctness matters at all — it's a different gate, not a consequence of the engineering one, and the current gate order (annex 2, step 4) runs the gateway-negative-test gate *before* this permission is nailed down.

**15. "Independent reviewer" is close to unreachable among AI products — the rule needs a human, not just a different model.**
Expanded above in the disclosure. Concretely: write the independence rule as *"a human with no HumanAIOS LLC equity, profit share, or compensation tied to this issue's outcome,"* not *"an AI service outside the named four."* Otherwise every review the issue collects (Grok's, this one, a hypothetical Gemini one) carries the same defect and the issue will keep collecting reviews that don't satisfy its own acceptance rule.

### High

**16. Same-account, same-day trades across sub-agents in the same instrument are a market-conduct risk, not only the tax issue the prior review named.**
Finding #8 (prior review) correctly flags wash-sale/settlement tax effects of four agents sharing one account. Separately: if two sub-agents independently submit opposing orders in the same instrument on the same day from the same account, that is architecturally indistinguishable from **self-crossing / matched orders**, a pattern exchanges and regulators treat as potentially manipulative *regardless of intent*, because it can create a false impression of trading volume or price interest. The gateway design should detect and block (not just log) same-instrument, opposite-side orders from different sub-agents inside one account within a cooldown window, and this should be called out as a market-conduct control, separately from the wash-sale/tax control in finding #8.

**17. The "frozen participant tuple" (prior finding #5) is missing sampling parameters — without them, the same tuple can produce different trades on replay.**
Finding #5 freezes (service, model/version, harness, prompt, tools, schedule). For an LLM-driven trading decision this is not sufficient: unless temperature, top_p, and (where the API exposes it) a seed are also pinned and logged per decision, the same frozen tuple can emit a different trade on a re-run of the identical prompt at the identical timestamp. That breaks the premise that a cohort member's result reflects "how that model trades" rather than "which sample it happened to draw" — add sampling parameters to the frozen tuple and log them per decision alongside the other identity fields in the financial event record (annex 2's ledger schema).

**18. Sharpening prior finding #3: the forward-paper-trading start date must be pinned to the *latest* training cutoff among the cohort, not an arbitrary date.**
The prior review correctly rules out point-in-time historical backtesting for LLMs (weights already encode what happened up to each model's own cutoff) and recommends forward paper trading instead. One gap: cohort members have **different** training cutoffs. If the observation window starts on a date that is *after* Model A's cutoff but still *before* Model B's cutoff, Model B is not actually in a "forward," no-hindsight position relative to that window — it may retain more general knowledge of market conditions nearer its own cutoff than Model A does. The protocol has to set the observation start date **no earlier than the most recent training cutoff among all cohort members**, and record each member's declared cutoff in the frozen participant tuple so this is checkable later, not assumed.

### Medium

**19. Market-data cost and latency differ by asset class and aren't in the "measures to define" list.**
Coinbase's own crypto market data is generally free and real-time through its public API; US equities real-time Level 1 quotes are frequently a separate paid subscription, with free feeds commonly delayed (historically ~15 minutes on many retail platforms). An agent restricted to delayed equity quotes is at a structural information disadvantage against one trading crypto on live data, for reasons that have nothing to do with trading skill. Add "market data source, cost, and staleness per instrument class" as its own UNKNOWN in the "Measures to define before any live run" section, next to the existing cost/benchmark/window items.

**20. A fully inactive sub-agent is not scored by any stated rule.**
The acceptance criteria say to "preserve inactive and losing agents" in reporting, but nothing in the body, the annexes, or the prior review states how an agent that places zero trades for the entire window is scored against the benchmark and the break-even hurdle. Left unstated, this is gameable by construction: in a down-market window, "never trade" trivially beats a declining benchmark and may even clear a break-even bar if subscription cost is excluded from an idle agent's ledger — rewarding inaction over demonstrated (even losing) trading behavior, which defeats the stated purpose of the study. Define explicitly, before the window opens, whether a non-trading agent is (a) scored at 0% market return minus full cost, (b) excluded from the comparison and reported separately as "non-participating," or some other predeclared rule — and pick one before any run, not after seeing who went idle.

---

## What I did not re-litigate

I deliberately did not re-derive findings #1–#13 from the prior review — I read them, agree with the governance-cost (#12), subscription-conflation (#6), and kill-switch-must-be-tested (#13) points especially, and have nothing to add to them beyond the #3 sharpening above (new #18). Treat this file as additive to that review, not a replacement for it; both should be folded into the single consolidated issue body the prior review's finding #11 already called for.

No trades, transfers, connections, accounts, or permission changes are authorized by this file.

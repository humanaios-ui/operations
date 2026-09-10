# H-MKT-01 — candidate registry entry + Metaculus question drafts
Issued 2026-09-05 · Z1 · Z2 prose approval to register; hash pending · LAID · 0/40 unchanged

## Registry entry (for REGISTERED.md, after IC-030 live read)

**H-MKT-01** · Unattended, long-running agent workloads become the dominant AI compute pattern by 2030, and demand for independent behavior audits of such workloads rises with it.

Provenance: unsigned analysis piece received 2026-09-05; load-bearing numbers traced on read to McKinsey (inference 20.9→93.3 GW 2025→2030; training →62.2 GW; sum 155.5 ≈ the piece's "156 GW"), IEA (~945 TWh data-centre electricity by 2030), Goldman (US 31→66 GW 2025→2027). Tier: CLAIM+LINK. Unresolved: "2–45 GW distributed training," "1 GW single site 2028 / 8 GW 2030" — CLAIM.

Falsifier 1 (near, cheap): if none of the first ten intake engagements involves an agent running unattended longer than one session, the near-term half is not visible in our market.
Falsifier 2 (far, mechanical): Stale Sweep re-reads McKinsey/IEA/Goldman quarterly; if the "inference overtakes training by 2027" marker slips on two consecutive reads, the timeline is decaying → reopen as GAP.
Falsifier 3 (external): Metaculus community forecasts on Q1–Q3 below fall under 0.35 by 2027-12-31.

Split: the hypothesis has two halves (compute pattern; audit demand). They resolve separately and are scored separately in NF_LEDGER.

---

## Metaculus drafts

Note: Metaculus requires a named resolution source, an unambiguous criterion, and a date. Community-submitted questions go through moderator review. Posting is a Z3 action from Night's account; Z1 cannot post. A question we then forecast on gives Z2 an external Brier — a second calibration ledger nobody in this system controls.

### Q1 — compute half
**Will AI inference exceed AI training in global data-center power demand (GW) for calendar year 2027?**
Resolution: YES if McKinsey's data-center workload model, the IEA Energy & AI report, or Goldman Sachs Research publishes, before 2028-07-01, a figure showing global AI inference GW > AI training GW for 2027. If sources disagree, resolves by the majority of the three; if fewer than two publish, resolves AMBIGUOUS.
Close: 2028-06-30. Our prior: 0.65.

### Q2 — unattended half
**Will Anthropic report that its longest-running autonomous Claude Code sessions exceed 8 hours of unattended work before 2028-01-01?**
Resolution: YES if an Anthropic research post in its "Measuring AI agent autonomy" series (or successor) reports a median-of-longest-sessions figure, or an equivalent top-percentile session-length metric, at or above 8 hours. Baseline: >45 minutes as of Feb 2026.
Close: 2027-12-31. Our prior: 0.55.
Alt resolver if Anthropic stops publishing: any comparable series from OpenAI, Google DeepMind, or METR on unattended agent session length.

### Q3 — audit-demand half
**Will at least three notified bodies listed in the EU's NANDO database for Regulation 2024/1689 explicitly include "AI agents" or "autonomous/agentic AI systems" in their published scope by 2027-12-31?**
Resolution: YES per the NANDO listing text or the body's own published scope document. Counts only bodies formally notified for the AI Act.
Close: 2027-12-31. Our prior: 0.45.
Why this proxy: "demand for audits" is unmeasurable; accredited assessors adding agents to scope is the receipt that demand left.

---

## What this does for us
- Each question is a pinned prediction with a public resolver → three LT-2 events for Z2 and three for Z1 that neither of us can rewrite.
- Q2 is the one that actually tests "unattended." Q1 tests only "inference." The original hypothesis conflated them; the split is the correction.
- Posting costs one Z3 session and no money.

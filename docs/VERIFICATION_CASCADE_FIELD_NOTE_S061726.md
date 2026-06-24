# Field Note: Verification Confidence Does Not Track Accuracy in AI-to-AI Citation Review

**Date:** June 17, 2026
**Status:** Candidate finding (F-53) and hypothesis (H-AICASCADE-01), single-session observation, replication pending
**Context:** Internal research note, HumanAIOS / ACAT program

## What happened

A literature synthesis supporting a hypothesis registration (prompt-format effects on AI self-report calibration) cited two external papers. Four independent AI systems were separately asked to verify the synthesis against available sources. Two of the cited claims were then checked directly against primary sources.

## Comparison

| Claim | Reviewer A | Reviewer B | Reviewer C | Reviewer D | Primary-source check |
|---|---|---|---|---|---|
| Sclar et al. (ICLR 2024): up to 76-point accuracy swing from prompt formatting alone, meaning preserved | Accepted, no detail given | Confirmed, cited the exact figure | Confirmed, cited the exact figure | Reported unable to locate this figure in current papers | Confirmed — this is the paper's headline statistic |
| Tosato et al., "PERSIST" (AAAI 2026): self-report personality scores show SD > 0.3 on 5-point scales at 400B+ parameter scale | Accepted, no detail given | Confirmed, correct figure | Could not confirm the paper's existence in public indexes | Confirmed, but reported the figure as SD > 0.4 | Confirmed — SD > 0.3 is correct; 0.4 is not supported |
| Unsourced figure: "question reordering alone shifts personality measurements by up to 20%" | — | — | — | Introduced this specific figure | Not located in available primary text |

## Observation

Confidence language ("✅ Verified") did not correlate with accuracy across the four passes. Reviewer D expressed the highest specificity and confidence while simultaneously missing the most easily verifiable claim in the set and introducing two figures not supported by direct source-checking. Reviewer C, by contrast, was the most accurate about the limits of its own knowledge — explicitly flagging that it could not confirm the existence of a paper that does, in fact, exist, rather than asserting a verdict either way.

## Why it matters

This is a small, single-session sample — two citations, four review passes — but it is a dated, reproducible incident rather than a constructed example. It bears directly on any system architecture that uses one AI process to verify, fact-check, or grade another AI process's output: multi-agent pipelines, retrieval-augmented-generation verification layers, LLM-as-judge configurations. The question it raises is concrete and testable: does a verification step's stated confidence track its actual accuracy, or can confidence and specificity increase across successive review hops without a corresponding increase in correctness? This incident is consistent with the latter and should be tested directly rather than assumed away in system design.

## Status

Registered as candidate finding F-53 and candidate hypothesis H-AICASCADE-01. Promotion to confirmed status requires a minimum of two additional, independently-run verification chains, each checked against primary sources.

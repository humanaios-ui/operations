# PIER-001 · Offline personal-information reconstruction smoke test

**State:** Experimental, OBSERVED only for the fixed synthetic fixture. **Not admitted.**  
**Authority:** NONE. **Execution:** DISABLED. **Risk:** Zero real personal records and no live APIs.

## Research question

Can a privacy-reconstruction scoring instrument reliably distinguish explicit extraction, non-explicit attribute inference, and cross-source linkage as more **available observations** are supplied? This first experiment checks **instrument behavior**, not a real person's privacy risk or a deployed AI model.

**Bounded smoke hypothesis (H-SYN):** In this *deliberately constructed* fixture, adding observations increases recoverable synthetic role claims. A fixed clue-matching toy attacker should correctly label 0/30 with 0 or 1 messages, 20/30 with 3, and 30/30 with 6. This direction is engineered, so passing H-SYN is **not evidence** that real AI systems behave that way. It validates data plumbing, source-bound claims, abstention, and scoring.

**Independent real-world hypothesis (H-REAL):** Longer, legitimately accessible conversation histories increase an independent evaluator's accuracy on previously undisclosed attributes, relative to a prior-only and no-history baseline. **UNVERIFIED; not tested here.** An actual study needs a preregistered sample, real permission boundaries, independently collected ground truth, alternate attackers, and appropriate ethics/privacy review.

## Fixed experiment

- **Population:** 30 invented cases, exactly 10 in each of three occupational categories. No sensitive protected categories are inferred. All identifiers are invented; email addresses end in reserved `.invalid`.
- **Available history:** 0, 1, 3, or 6 messages per case (prefix windows). Case identifiers organize evaluation; they do not link directly to the public-directory records.
- **Toy attacker:** transparent keyword-and-regex rules. No AI model calls. The attacker's input excludes ground-truth labels, but includes an *invented* alias → public-profile directory. This is a toy attacker whose vocabulary matches the fixture; no generalization is claimed.
- **Target classes:** occupation *inferred* from clues, handle *directly extracted* from text, fictional email *directly extracted*, and public-profile ID *linked* through the separate fictional directory.
- **Evidence:** each claim needs a visible message ID. Citation validity is checked against visible content, not merely the existence of an ID. Citation support is **not** independent proof of truth; correctness is scored against hidden synthetic truth.
- **Confidence:** toy role claims are assigned 0.85 with one cue and 0.95 with two; Brier score is evaluated only on emitted role claims, not on abstentions.
- **Chance baseline:** always guessing one of the balanced roles would yield 10/30 on this fixed cohort, but without grounded evidence. The safe no-evidence toy attacker abstains. Accuracy over *all* cases and precision *when claimed* are reported separately; missing claims have undefined precision, not a fabricated 100%.

**Declared gates:** (G1) zero role claims at stages 0/1; (G2) role accuracy at stage 3 exceeds stage 1 and stage 6 is at least stage 3; (G3) zero unsupported claims for the built-in attacker; (G4) no external service usage. These are smoke expectations built into code, not a time-stamped preregistration of a confirmatory experiment.

**Falsifiers / failure controls:** any incorrect response counted correct; unsupported or future-stage message citations accepted; invented non-`.invalid` addresses accepted; missing/duplicate subject records accepted; role guesses without evidence presented as verified; raw synthetic transcripts leaked into published result. Test failures stop promotion. A corrupted-role prediction is intentionally included to verify false-claim detection.

## Run (stdlib only)

From the `operations` repository root:

```bash
python3 -m unittest discover -s tests -p 'test_pier_001.py' -v
python3 experiments/pier_001/run.py > pier_001_report.json
```

The JSON report contains **aggregate statistics only**, experiment metadata, declared gates, and a SHA256 digest of the fixed synthetic fixture. SHA256 is a deterministic content identifier, **not** an authenticated signature or independent Witness verdict. No filesystem writes occur inside the experiment module; optional redirect is the operator's choice. Do not commit outputs or private transcripts. `python3 -m unittest` runs without external packages.

## Interpretation gates

A green result means the deterministic fixture was scored as specified. It is **not** a result about ChatGPT, Claude, Grok, provider data retention, training-data membership inference, re-identification prevalence, or real people's hidden characteristics. The Wilson intervals in the report merely summarize fixed synthetic counts; do **not** use them as confidence intervals for the real-world population or assert statistical significance. Linkage here is a trivial controlled lookup, not a public-internet search. In particular, the scoring instrument is not an access audit of providers.

**What this intentionally does not do:** acquire any real chat export; connect Gmail, Drive, Azure, GitHub profiles, or other personal sources; run LLMs; predict race, politics, religion, health, or sexual attributes; deploy an app; create persistent user profiles; or put user data in the Evidence Graph.

## HumanAIOS mapping (design only)

| Existing HumanAIOS interface | Intended bounded role | Current state |
| --- | --- | --- |
| INTENT-OS | Explicit human permission scope and revoke / delete flow | NOT CONNECTED |
| Resource Miner | Discover user-authorized source types without fetching private data | NOT CONNECTED |
| Evidence / Session / Temporal Graphs | Project claim → source-id → time; no personal data in public repositories | NOT CONNECTED |
| ACAT | Distinguish correct from confident, ungrounded inferences | METHOD REUSED, NOT CONNECTED |
| Coordinator / Witness | Gate permissions; validate independent receipt after instrument passes | NOT CONNECTED |

**Next smallest action:** get independent review of the scorer and fixture leakage controls. Only then consider a separate, private and consented model-comparison experiment with a preregistered design. Any user-visible private-data assessment must have explicit consent, opt-out, retention and deletion behavior, human recourse, and isolation from public issue/PR content.

## Related research (foundations, not proof of this implementation)

Barocas, Hardt & Narayanan, *Fairness and Machine Learning* (2023): proxy features and inference (chapter 3), information-flow adversarial audits (chapter 7), and the Netflix/IMDb linkage study (chapter 9). Distinguish these scientific methods from this software smoke test.

## Internal adversarial review (2026-10-19)

**Finding R1 — exposed test index (FIXED in draft candidate).** The original
`public_view` exposed `case_id` (`SYN-00` etc.). Since the public fixture assigns
`ROLE_NAMES[index % 3]`, a code-aware attacker could label **30/30 roles at
zero conversations** using the index, contradicting the premise of a history-only
baseline. The review candidate removes the internal case ID from attacker input.
The trusted evaluator adds it *after* the attacker has returned its claims.
This fixes this direct pathway, **not** all possible leakage from a public fixture.

**Finding R2 — partial citation laundering (FIXED in draft candidate).** The
original evidence scorer accepted multiple cited message IDs if *any* one
supported a claim. It now requires every cited message to support the exact
claim lexically. A new negative test adds a valid-but-irrelevant message and
requires it be counted as unsupported.

**Finding R3 — not a blinded benchmark (OPEN).** The synthetic fixture and
toy attack rules remain public in the same module. This is intentional for a
reproducible unit-test fixture. It is **not** a suitable held-out sample for
external LLM comparisons or generalized claims about privacy risk.

**Finding R4 — no-call receipts are declarations (OPEN).** The result's
`declared_calls` field is static, not instrumented provider telemetry. The
code does not import a networking or LLM library. Still, do not present the
zero counters as independently verified observations of an execution sandbox.

**Local checks:** 14 / 14 standard-library `unittest` checks pass on the
reviewed candidate, with the same fixed fixture SHA256 and smoke results.
No real personal records were processed. Independent reviewer approval,
protected CI, and governance admission remain pending.
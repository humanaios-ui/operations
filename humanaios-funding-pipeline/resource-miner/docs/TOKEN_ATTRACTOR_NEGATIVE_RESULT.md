# Token-attractor pilot: negative result (sanitized)

**Status: NEGATIVE / NOT SHOWN.** Authority effect NONE. Experiment-only code. No eligibility claim was made or implied.
Historical source head of the completed experiment: `4c15c906b208d52804317e6fba450ad7e04fbfde`.
Private records (ledgers, per-match ratings, review packets) are held by the owner and are **not** in this repository.

## Question
Does expanding source-backed capability tokens into related search terms find more *useful* public resources than matching an owner's own wording, without raising unsupported matches?

## Design (as run)
- Corpus: the 51-row public Resource Miner snapshot (one source, AI-funding skewed).
- Scorer: the existing `needs._score` signal count, at its own 0.2 threshold (two signals) and at a one-signal view.
- Arms: **A** owner's skill phrases verbatim; **A2** plain words and word pairs from those phrases; **B1** hand-authored concept aliases; **B2** B1 plus hand-authored transfer-hypothesis neighbours.
- Gate: a concept is queried only if a source-backed owner token supports it. Three negative controls (nonsense words, an unsupported hardware domain, licensed clinical practice) were refused by that gate.
- Phases: **P1** frozen predictions and rankings; **P2** blind adjudication of every match by an independent model rater (two planted false pairs); **P3** corrections derived from P2; an independent design and code challenge; **P4** repaired baseline and a second blind adjudication (3 repeated items, 2 planted false pairs). All phases are preserved unchanged.

## Results (aggregate)
| view | arm | distinct resources | PARTIAL-or-better leads | unsupported pairs |
|---|---|---|---|---|
| 0.2 threshold | A | 0 | 0 | 0 |
| 0.2 threshold | A2 | 0 | 0 | 0 |
| 0.2 threshold | B1 | 1 | 1 | 0 |
| 0.2 threshold | B2 | 2 | 1 | 1 |
| one signal | A | 0 | 0 | 0 |
| one signal | A2 | 9 | 6 | 3 of 11 pairs |
| one signal | B1 | 5 | 4 | 2 of 7 pairs |
| one signal | B2 | 5 | 4 | 2 of 7 pairs |

- 30 adjudicator verdicts across two rounds: **USEFUL 0**, PARTIAL most common. Both planted false pairs were rejected in both rounds; 3 of 3 repeated items agreed.
- Against a fair plain-word baseline (A2), concept expansion (B1) was **not** better at the one-signal view (A2 found 2 leads B1 missed; B1 found none A2 missed). At the 0.2 threshold B1 found one lead and A2 none (n = 1).
- The transfer-hypothesis layer (B2) added no useful match.
- The literal-phrase baseline (A) returned nothing at either threshold, so comparing expansion to A alone (as P1 to P3 did) was uninformative and flattered expansion.
- No match was assessed for eligibility; every hit stays `eligibility_assessed: false`.

## Failed or weak pre-stated predictions
Two of eight frozen predictions failed outright (an expected concentration of expansion-only gains, and a credential detector that flagged nothing while the rater found domain requirements). Three held (literal baseline near zero, controls match nothing, a meaningful share judged unsupported). Three held only partly or weakly. The decision rule ("at least one useful novel match with no rise in unsupported share") is **not supported** under the strict reading.

## Limits
- One model-family rater; no human has rated any match. Same family as the author.
- P3 and P4 corrections were written after seeing P2 verdicts on the same items; there is no hold-out.
- Tiny N (0 to 11 pairs per arm), one small AI-skewed corpus.
- The concept aliases are hand-authored; owner tokens only decide which concepts are queried.
- The domain-requirement flag fires on most matches, so it restates "eligibility unknown" rather than discriminating.
- An independent challenge confirmed and the authors fixed: a whitespace bug that made the literal baseline unmatchable, owner text able to reach the matcher through the baseline arm, over-broad classifier patterns, an employer name able to open a concept, a weak credential detector, id aliasing, and a partial-write leak. Each fix has a regression test.

## What this change does about it
- The code lives under `resource_miner/experiments/` and nothing in production paths imports it (tested).
- Concept expansion and transfer-hypothesis matching are **off by default** and need two explicit keys: a function argument and `HUMANAIOS_ALLOW_TOKEN_EXPERIMENT=1`.
- The existing plain-word matcher (`needs.py`, `intent_os.py`) is unchanged.
- A new, preregistered-style experiment on evidence accuracy, human decision burden and correction rate is proposed in `EXPERIMENT_PROPOSAL_EVIDENCE_ACCURACY_BURDEN_V0_1.md`. It is not run.

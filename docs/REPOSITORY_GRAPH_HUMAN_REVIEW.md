# Human Review Guide for Repository Graphs

## The short answer

`docs/REPOSITORY_KNOWLEDGE_GRAPH.md` is the technical/operator explanation in this PR. It explains what the compiler does and what it refuses to claim, but it is not optimized for a human deciding whether the resulting graph is trustworthy enough to use.

The primary human translation is now the generated `human-review.md` file. Every method run creates one from the exact graph being reviewed, so its counts, warnings, hashes, and sampled inference assertions cannot drift away from the machine artifact.

## What a human should review

A human does not need to read thousands of nodes or edges. Review is divided by comparative advantage:

| Machine review | Human review |
|---|---|
| Deterministic inventory | Whether the selected snapshot is the intended one |
| Hash and manifest integrity | Whether the profile's curated meanings are fair |
| Duplicate and dangling-edge checks | Whether important context or evidence is omitted |
| Rule/premise reconstruction | Whether a material inference survives its falsifier |
| Forbidden-conclusion enforcement | Whether the read model is useful for the stated purpose |
| Two-build replay | Final disposition and rationale |

## Translation key

| Graph language | Human reading |
|---|---|
| `OBSERVED` | The compiler mechanically saw this relationship in source. It does not prove the underlying claim. |
| `SPECIFIED` | A document, contract, graph, or curated profile says this relationship should exist. |
| `CLAIMED` | A source asserts this; verification remains open. |
| `TESTED` | A test relationship is represented; it does not mean the test ran or passed. |
| `MODEL_INFERRED` | A bounded rule produced a review candidate from explicit premises. |
| Confidence | Strength of the structural rule application, not probability of truth. |
| Independence `NOT_ESTABLISHED` | Distinct sources may still share origin, method, or failure mode. |
| Falsifier | The observation that would defeat the candidate interpretation. |
| `authority_effect: NONE` | The graph cannot authorize, ratify, merge, deploy, or execute. |

## Review order

1. Open `human-review.md`.
2. Confirm repository, commit, clean/dirty state, profile hash, source-tree hash, and graph hash.
3. Open the profile and review canonical artifacts, semantic mappings, exclusions, rules, and views.
4. Read every coverage warning. Missing data must remain visible.
5. Trace material inference samples to the complete `inferences.csv` queue and their premise edge IDs.
6. Use `graph.json` only when the bounded files do not answer the review question.
7. Record one disposition and a rationale outside the generated artifact.

## What acceptance means

`ACCEPT READ MODEL` means only:

> For the pinned repository snapshot and profile, this graph is a sufficiently faithful and bounded diagnostic representation for the stated review purpose.

It does **not** mean:

- the repository is safe, complete, effective, or production-ready;
- public or research claims are proven;
- tests passed;
- a declared control operated;
- an inferred dependency executed;
- a profile is ratified policy;
- a PR should be merged.

Those decisions require their own evidence and human authority.

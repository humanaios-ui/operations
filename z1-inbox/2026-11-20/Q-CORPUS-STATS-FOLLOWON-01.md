# Q-CORPUS-STATS-FOLLOWON-01 — the three asks `Q-CORPUS-STATS-RECONCILE-01` left unruled: the interim citation rule, whether anything external went out, and whether the corpus validator gates

**Z1 Proposer:** Claude (Z1)
**Date Submitted:** 2026-11-20
**Status:** AWAITING Z2 RATIFICATION
**Filed because:** the parent block, `Q-CORPUS-STATS-RECONCILE-01`, was ruled `neither` (merged in #1267, reconciled in #1269, signature `5197f46860d8847540e4b03814bf7b17759d030f13739be2c9fb657f7e1851f7`). That closes its ask 1 as already answered by the ratified `Q-DATA-SSOT-REGENERATION-01`: the v0.1 corpus is kept as a lesson artifact and no corrected figure becomes the new claim. Asks 2, 3 and 4 were not ruled, and a ratified block takes no second ruling, so they return here.

This file decides nothing and changes no file other than itself and the index.

## What Z2 is asked to decide

1. **The interim citation rule.** Until a new claim is ratified, which corpus figures may be cited externally? Options Z1 sees: none from any set; or only one named set. `deliverables/witness-stand-post-1.md` already asserts an answer in prose (use LI 0.87, not the 0.8632 / N=629 figures). Z1 found no ratification of that rule.
2. **Whether anything external went out on the figures that do not reproduce.** This is a question of fact that only Night can answer. If something did, this is an IC with amends, not only a correction. Z1 cannot answer it from the tree.
3. **Whether the corpus integrity validator should gate.** `tools/corpus_integrity_validator.py` exists. A gate would be a workflow change, so it is its own Tier 2 decision with its own pull request after ruling. The parent block says the dataset currently fails the validator; Z1 did not re-run it.

## Checked on 2026-11-20 (main `71414758`)

- **Three sets of figures are in the tree.**
  - `SEED.md` still publishes N_total 629 and mean LI 0.8632 (lines 89 and 92).
  - `acat/canonical_stats.json` records `n_total` 604, `raw_rows` 608 and mean LI 0.8532.
  - `deliverables/witness-stand-post-1.md` line 65 tells authors to use LI 0.87 and not the 0.8632 / N=629 figures.
- **Files under `deliverables/` that contain the string 0.8632** (the list is of file names only; Z1 did not read them and does not know whether each states the figure as a claim or warns against it): `post-1-crosspost-execution.txt`, `witness-stand-post-1.md`, `post-1-substack-ready.md`, `EXECUTION-CHECKLIST.md`, `post-1-linkedin-ready.md`, `post-1-linkedin-carousel.md`, `p0-1-corpus-fix.md`, `GOAL-2-COLLABORATION-STATE-DEEP-DIVE.md`, `post-1-substack-final.md`, `p0-2-zenodo-submission-pack.md`, `substack-publication-plan.md`. Whether any was published cannot be told from the tree.
- **The validator gates nothing.** No workflow under `.github/workflows/` mentions `corpus_integrity_validator`.
- **Not re-checked:** the public dataset, the 116-row live table count from 2026-09-21, and the parent's figure counts (38, 7, 2, 1). Those did not match Z1's own count on 2026-11-16 (170, 19, 12, 13), and Z1 did not redo the count today.

## Z2 Review Checklist

- [ ] Question 1: pick a rule for external citation until a new claim is ratified.
- [ ] Question 2: answer the fact question. If the answer is yes, say what and where, so an IC can be filed.
- [ ] Question 3: decide whether the validator gates. A yes starts a separate Tier 2 pull request.

## Falsifier

Event-based, no clock. This block is wrong, and should be withdrawn in whole or in part, if any of these happens:

- (a) a ratified citation rule is found that already answers question 1. Probe: search `REGISTERED.md` and `z1-inbox/INDEX.yaml` for the 0.87 rule. The parent's check on 2026-11-16 found none; Z1 has not searched again today.
- (b) a workflow that runs `tools/corpus_integrity_validator.py` is found. Probe: `grep -rn corpus_integrity_validator .github/workflows`. It returned nothing on 2026-11-20.
- (c) a publication record, or Night's answer, shows that nothing external went out on the unreproducible figures. Question 2 is then answered "no". Reading the current `deliverables/` files cannot establish that, because earlier versions, or material outside this tree, could have been sent; only a publication record or Night's answer closes question 2.

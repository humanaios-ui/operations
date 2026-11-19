# Q-CORPUS-STATS-RECONCILE-01 — the July corpus audit is still unresolved and SEED.md still publishes the failing numbers

**Type:** IC · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Parent finding:** `audits/CORPUS_RECONCILIATION_S-070226.md` (Zone 1, **submission-blocking**)
**Found by:** the Q-INTENT-GRAPH-01 obligation — a sweep for artifacts that disagree.

---

## The finding

This candidate registers no new analysis. The analysis was done on 2026-07-02 and
is unambiguous:

> **Not one of the five headline numbers matches**, and the dataset fails its own
> integrity validator.

| Metric | Cited | Actual (parsed + validated) |
|---|---|---|
| Total records | 629 | **608** |
| Phase 1 | 516 | **524** |
| LI-scored | 307 | **278** raw · ~80–84 proper Phase-3 pairs |
| Mean LI | 0.8632 | **0.8431** raw · **0.8572** cleaned |
| Providers | 18 | **23** families |
| Integrity | implied clean | **FAIL** — 31 `LI_RECALC_MISMATCH`, 12 `ANCHORING`, 87 `MISSING_TIMESTAMP` |

The audit offered Option A (recompute from the archive and correct every citation)
and Option B (produce the real 629-record corpus and publish that), asked for a
selection, and **recorded none**.

What has happened since: nothing in the tree. As of this SHA, `SEED.md` — the
identity anchor — still publishes `N_total 629 · N_LI 307 · Mean LI 0.8632` as
canonical. `0.8632` appears **38 times** tree-wide, against 7 for `0.8532`, 2 for
`0.8431` and 1 for `0.8572`. A third set (`LI 0.87`, the "canonical paper numbers")
is in active use, with `deliverables/witness-stand-post-1.md` instructing authors
**"Do NOT swap in the 0.8632/N=629 draft figures."**

So there are three live statistic sets, a written rule about which to use where,
and a ratified-nothing audit saying all of them are unreproducible from the
published dataset.

## Why this belongs in the graph rather than only in the audit

The audit already said the thing that matters:

> Your entire thesis is **measuring the gap between what a system claims about
> itself and what it actually does.** If a reviewer finds exactly that gap in your
> own headline statistics, it doesn't just cost one number — it undercuts the
> credibility of the instrument.

Two and a half months later the gap is still there, which is the point this
candidate adds. A finding written into an audit file is not a mechanism. Nothing
re-raised it, nothing blocked on it, and no session was required to notice it. As
an `INTENT_GRAPH.yaml` row it is reported by `check` on every run until a Z2
decision closes it.

This is the strongest available argument for the graph, and it is not one Z1
constructed — it is what the repository did to a submission-blocking finding it
had already written down.

## What Z1 is not doing

Not selecting Option A or B, not recomputing the corpus, not editing a single
cited figure. Option A alone rewrites the headline numbers in the CV, two funding
applications, `CURRENT.md` and `REGISTERED.md`. That is a Z2 decision with
external consequences, and Z1 filing it as "obviously A" would be Z1 setting
published research figures.

## What Z2 is asked to decide

1. **Option A or Option B**, per the audit's own framing.
2. **The interim citation rule.** Until one is chosen, which set may be cited
   externally? `witness-stand-post-1.md` already asserts an answer in prose; it is
   not ratified anywhere Z1 can find.
3. **Whether anything external went out on the unreproducible figures** since
   2026-07-02, which would make this an IC with amends rather than a correction.
4. **Whether the corpus integrity validator should gate**, given the dataset
   currently fails it and `tools/corpus_integrity_validator.py` exists and works.

## Falsifier

FALSE if a 629-record corpus reproducing 516 / 307 / 0.8632 exists and is
published — the audit's Option B, which would make the cited numbers correct and
the published dataset the stale artifact. Mechanically checkable: download the
HuggingFace dataset, run `tools/corpus_integrity_validator.py`, compare.

Also FALSE if a Z2 ruling selecting an option exists and Z1 failed to find it;
Z1 searched `audits/`, `REGISTERED.md` and `z1-inbox/` and found no selection.

## Evidence

- `audits/CORPUS_RECONCILIATION_S-070226.md` — the finding, the table, the options
- `SEED.md` lines 89–92 — the failing figures, still canonical
- `deliverables/witness-stand-post-1.md` line 65 — the do-not-mix instruction
- Tree-wide mean-LI counts: 0.8632 ×38 · 0.8532 ×7 · 0.8431 ×2 · 0.8572 ×1
- `INTENT_GRAPH.yaml` — `O-IDENTITY-ANCHOR ↔ O-CORPUS-INTEGRITY`, status OPEN

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```

---

## Z2 Ruling

**Decision:** ACCEPT — stated by Night (Z2/Admiral) in session, 2026-09-21.
**Recorded by:** Claude (Z1), as transcription. Z1 did not make this call.
**Signature:** none on this file, and **the merge does not create one.**

*Corrected on review (Copilot, PR #440), and the correction matters.* An earlier
version of this section said the merge of the pull request was the act of
ratification, citing `Z2_RULING_MERGE_IS_RATIFICATION.md`. That rule is real but
**narrower than Z1 read it**: `.z1-control/ratify.py` implements merge-ratification
only for *board rulings* — a file carrying a `## Ruling` section with a `choice:`
line, the shape `tools/decision_relay.py` writes — and explicitly refuses to sign
those itself. This candidate is not that shape, so **merging its PR ratifies
nothing**; the index stays `awaiting_z2` and no signature exists.

The mechanism for a standard candidate is Z2 running:

```
python3 .z1-control/ratify.py Q-CORPUS-STATS-RECONCILE-01 --decision ACCEPT --by Night --apply
```

which computes `sha256(candidate | by | at | decision)` over the file's bytes,
writes the dated ruling file, and updates `z1-inbox/INDEX.yaml` to a terminal
status — the three things `.z1-control/validate.py` requires and that a merge
does not supply. Run it **after this PR merges**, so the hash covers the final
bytes including this section.

Z1 does not run it: the tool's own docstring says "Run by Z2, not by Z1", because
Z1 writing the ruling file, computing the hash and setting the status in one pass
would satisfy every check while proving nothing.

Single-member override applies: with one board member, Night reviews, approves
and merges her own ruling PR, recorded as an override per that ruling's `review`
row.

---

## Options

- `neither`
- `neither, no figure cited`
- `option A`
- `option B`
- `edit`
- `later`

The block's four asks are in "What Z2 is asked to decide" above. Ask 1 is the choice between Option A and Option B, and a third answer now exists (see below). Asks 3 and 4 are not offered as choices. Ask 3 is a question of fact that only Night can answer: whether anything external went out on the figures that do not reproduce. Ask 4 (whether the corpus integrity validator should gate) would be a change to CI, and it is its own decision.

## What each sets in motion

- `neither`: ask 1 is closed as already answered by the ratified `Q-DATA-SSOT-REGENERATION-01` ruling, which keeps the v0.1 corpus as a lesson artifact and says no corrected figure becomes the new claim. So there is no recompute-and-correct (Option A) and no search for a 629-record corpus (Option B). Asks 2-4 stay open. It changes no file except this one: `SEED.md` still publishes N 629 and mean LI 0.8632. Entering a registry entry in `REGISTERED.md` is a Z2 act; Z1 does not write that file.
- `neither, no figure cited`: the same as `neither`, **and** ask 2 is answered: until a new claim is ratified, no corpus statistic, from any of the sets, is cited externally. It is a rule and changes no file by itself. It differs from `deliverables/witness-stand-post-1.md` line 65, which tells authors to use the "canonical paper numbers" (LI 0.87) and not the 0.8632 draft figures; the block says that rule is not ratified anywhere. Asks 3 and 4 stay open.
- `option A`: recompute from the archive and correct every citation. The block says that rewrites the headline numbers in the CV, two funding applications, `CURRENT.md` and `REGISTERED.md`. Z1 reads this as conflicting with the ratified DATA-SSOT ruling, since corrected figures would become the new claim. Night may rule otherwise, and a later ruling supersedes. The ruling itself changes no file; the correction would be separate, large work that Z1 does not start without Night's go.
- `option B`: produce the real 629-record corpus and publish that. Nothing Z1 re-checked today shows such a corpus (see below), so this starts a search, not a result.
- `edit`: Z1 revises the block and files it again.
- `later`: this block closes with its bytes signed; the question returns only as a new block.

## Checked on 2026-11-16 (not carried from the block above)

- **`Q-DATA-SSOT-REGENERATION-01` is ratified** (`INDEX.yaml` reads `ratified`). Its ruling, `ratify 1`, keeps the v0.1 corpus as a lesson artifact and says no corrected figure becomes the new claim. It does **not** close this block, and its text says asks 2-4 here stay for their own ruling.
- **`SEED.md` is unchanged.** It still publishes N_total 629, N_Phase1 516, N_LI 307 and mean LI 0.8632 as canonical.
- **The do-not-mix instruction is unchanged.** `deliverables/witness-stand-post-1.md` line 65 still says to use LI 0.87 and not the 0.8632 / N=629 draft figures. Z1 did not re-search for a ratification of that rule today.
- **The counts are not comparable to the block's.** The block says 0.8632 appears 38 times, 0.8532 seven, 0.8431 twice and 0.8572 once, and does not state how it counted. Z1's count today, matching lines across the whole tree, is 170, 19, 12 and 13. Z1 cannot say whether use of any figure grew.
- **A further figure set exists.** `acat/canonical_stats.json` (added 2026-09-19) records `n_total` 604, `raw_rows` 608 and mean LI 0.8532.
- **Ask 3 cannot be answered from the tree.** Files under `deliverables/` that contain the string 0.8632 include `post-1-substack-final.md`, `post-1-linkedin-ready.md`, `post-1-linkedin-carousel.md`, `post-1-crosspost-execution.txt`, `p0-1-corpus-fix.md` and `p0-2-zenodo-submission-pack.md`. Z1 did not read them, so it does not know whether each states the figure as a claim or warns against it, and it cannot tell from the tree whether any was published.
- **The validator gates nothing.** `tools/corpus_integrity_validator.py` is referenced by no workflow in `.github/workflows/`.
- **Falsifier, not re-checked.** Z1 did not search for a 629-record corpus today beyond `acat/canonical_stats.json`, which records 604 rows (608 raw). The public dataset was not checked, and the live-table count (116 rows) is from 2026-09-21 and was not re-queried.

## Note on the "Z2 Ruling" section above

That section transcribes an ACCEPT that Night stated in session on 2026-09-21. It does not say what was accepted, it carries no signature, and `INDEX.yaml` still reads `awaiting_z2` for this block. It also says the merge ratifies nothing, because the file then had no `## Ruling` section. This file now has one, in the shape `tools/decision_relay.py` writes, so under the 2026-09-18 ruling the merge of the pull request that fills it is the ratification, and the `ratify.py` command in that section is not needed. Z1 left the earlier text unchanged. Because it names no ask, it is not treated as an answer to any of them, and nothing here treats it as a ruling.

## Ruling

choice: neither
by: Z1-prepared (not an identity claim)
at: 2026-11-19T18:14:59Z
status: DECIDED
block_hash: 54f9a839f323346d6aff750a1f0e15a9401bea9b07ed085a1f8fd6d35e282916
body_hash: 30a475d3ed9c24c31196b162356d4703698de81a211deaa500214db2646adbd6

```
RULING z1-corpusstats-01
  by: Z1-prepared (not an identity claim) (tagline)
  project: humanaios
  question: Close ask 1 as already answered by the ratified Q-DATA-SSOT-REGENERATION-01 (neither Option A nor Option B)? Asks 2-4 are not ruled and, once this block is ratified, can return only as a new block (Q-CORPUS-STATS-RECONCILE-01)?
  choice: neither
  note: 
  at: 2026-11-19T18:14:59Z
  status: DECIDED
```


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

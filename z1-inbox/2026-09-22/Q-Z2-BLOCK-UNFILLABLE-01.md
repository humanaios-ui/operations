# Q-Z2-BLOCK-UNFILLABLE-01 — the candidate template promises a field will be auto-filled; nothing fills it, and the signature makes filling it later impossible

**Type:** IC · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Authorised by:** Night, 2026-09-22 — *"File the in-file decision block finding."*
**Origin:** surfaced while preparing the twelve ratification commands, not by a gate.
**Related:** `Q-REFERENT-DECAY-01` (same class), `Q-IC-RATIFY-BYPASS-01` (same tool).

---

## What is claimed, and what is only predicted

Stated first, because this session has already produced one candidate that asserted
a thing was done without reading the file that said otherwise.

**Verified, live, re-runnable:** the template's promise is false today, and the
block has no reader today.

**Predicted, not yet observed:** the contradiction between a candidate's own block
and its index row. **It has never happened.** Of the 9 candidates at a terminal
status, **0** carry an in-file `z2_decision` block, so no ratified candidate in the
tree currently contradicts itself. Ratifying any open candidate that carries one
creates the first instance. This candidate is filed *before* the instance exists,
which is the one thing `Q-REFERENT-DECAY-01` says the repository never manages to
do.

The count of affected candidates is deliberately **not** written here as a
constant. It moves, and it moved during this candidate's own review:

```
$ python3 - <<'PY'   # re-derives both numbers from the index
import sys, os; sys.path.insert(0, '.z1-control')
from validate import INDEX, ROOT, load_index
idx = load_index(INDEX)
has = lambda c: 'z2_decision' in open(os.path.join(ROOT, c['path']), encoding='utf-8').read()
aw   = [c for c in idx['candidates'] if c.get('status') == 'awaiting_z2']
term = [c for c in idx['candidates'] if c.get('status') != 'awaiting_z2']
print(sum(map(has, aw)), 'awaiting carry it;', sum(map(has, term)), 'of', len(term), 'terminal do')
PY
```

At filing it returned **14**. One merge later — `#457`, which added
`Q-MESH-LOCAL-COORDINATION-01`, written by a different session and carrying the
block — it returned **16**. Nobody decided that. The template emitted it.

Writing `14` into this file and leaving it there is the failure this candidate is
about, so the command is given instead of the number. That is option D of
`Q-REFERENT-DECAY-01` applied to this file by its own author, and it is the only
part of any of this that Z1 can adopt without a ruling.

## Leg 1 — the promise

`CANDIDATE_BLOCK_TEMPLATE.md:340`, in the field table:

| `z2_decision` | Status, hash, notes | **Auto-filled by Z2** |

and at `CANDIDATE_BLOCK_TEMPLATE.md:80-84`, the block itself:

```yaml
z2_decision:
  status: "awaiting_ratification"  # awaiting_ratification, accepted, rejected, contested, edited
  ratified_at: null
  ratification_hash: null
  z2_notes: ""
```

Nothing auto-fills it. `.z1-control/ratify.py` writes exactly two files —
the dated ruling file and `z1-inbox/INDEX.yaml` — and opens the candidate
**read-only**, at `ratify.py:435` (the board-ruling guard) and `ratify.py:447`
(the digest). The write at `ratify.py:350` is in `cmd_artifact`, a different
command against a different path.

## Leg 2 — no reader

```
$ grep -rn "z2_decision" . --exclude-dir=.git --exclude="*.md"
```

returns `z2_decision_window_hours` in `.claude/skills/pr-manager/config.json` — a
different key — and `-`-prefixed *deleted* lines inside
`patches/0011-Q-STALE-SWEEP-04-*.patch`. No live code, no workflow, no validator
reads the block. `validate.py` does not know it exists.

So the field is, today, an accurate statement nobody consults.

## Leg 3 — why it cannot be fixed after the fact

A candidate block is prose, so its signature is over the file's **raw bytes**
(`ratify.py:447`), and `--verify` recomputes over the bytes as they stand
(`ratify.py:279`). Filling the block after ratification therefore breaks the
signature of the thing just signed. Demonstrated against a real candidate rather
than argued:

```
$ python3 -c "... signature(open('z1-inbox/2026-09-22/Q-REFERENT-DECAY-01.md','rb').read(), ...)"
signature over the file as filed     978070f3b40bcb73fb18c185c80e8029152c418ccd55a5b2ac06c6f689ed635a
signature after correcting the block 58803ce9e6a71819c6a4efbefbe028fca10f5b156d3029b1e4d53f668d10b3a3
same? False
```

The one edit the file would need in order to stop lying is the one edit that makes
it read as tampered.

This is not a defect in the hash. Byte-pinning is the property
`Q-IC-RATIFY-BYPASS-01` exists to protect and the reason slugs were replaced. The
defect is a field that must change placed inside a payload that must not.

Nor can the block simply be filled *before* hashing: it carries
`ratification_hash`, and `ratify.py:38-40` already records why that is impossible —
*"a hash covering `ratification_hash` could never verify, because writing the digest
into the file would change the content the digest was taken over."* The artifact
path solves this by hashing the parsed document with the ratification fields
removed; a prose candidate has no parsed form to exclude from.

## Why this belongs in `Q-REFERENT-DECAY-01`'s class, and where it differs

Same shape: an assertion whose referent moves while the assertion stays. Two
differences, both of which matter for what to do about it.

1. **It is generated, not left behind.** The other five were single artifacts that
   went stale. This one is emitted by a template, so it reproduces on every new
   candidate — including this one, written by an author who had just finished
   measuring the problem, and including one authored by a different session while
   this candidate sat in review. That is not an argument that it reproduces; it is
   two more instances arriving during the time it took to write the claim down.
2. **It is designed in, not accidental.** Every other instance could have been
   caught by someone re-reading. This one cannot be repaired by care, because the
   repair is the thing the mechanism forbids.

That makes it the first instance in the class with a **mechanical** cause, and the
only one where "be more careful" is provably not the fix.

## What Z2 is asked to decide

**Option D — correct the template's claim.** Change *"Auto-filled by Z2"* to say
the decision is recorded in `z1-inbox/INDEX.yaml` and the dated ruling file, and
that this block is the proposer's request, not the outcome. Cheapest, touches no
gate, removes the false promise, and leaves the block harmlessly accurate.
**Z1 recommends this first, and it is the only option that is purely a correction.**

**Option C — rename the block to what it actually is.** `z2_request:`, carrying
what is being asked of Z2 and nothing that a decision would later change. Then
nothing about it can decay, because it describes the ask. Cost: touches the
template and the fourteen open candidates, and `z2_notes` loses its in-file home
(it has no reader today, so this is a loss of intent rather than of function).

**Option A — delete the block.** Honest: no reader, no filler, no future. Cost: the
candidate file stops carrying any trace of its own governance state, and a reader
with the file alone must consult the index to learn anything.

**Option B — make `ratify.py` fill it before hashing.** Would make the file
self-describing and pin the filled version. Cost: a Tier 2 gate change, and it does
not work as stated — `ratification_hash` inside the block is circular, so the field
would have to be dropped from the block first, at which point Option C has
already done the useful part more cheaply.

**Ordering: D, then C. A and B are listed to be argued against, not adopted.**
D and C compose: correct the claim now, rename later if the field should survive.

## What Z1 is not doing

Not editing `CANDIDATE_BLOCK_TEMPLATE.md`. It is a controlled document, the choice
between D and C is Z2's, and the fourteen affected candidates are all awaiting a
decision — editing their bytes now would change what Z2 is about to sign.

## Falsifier

FALSE if anything reads the in-file block. Re-runnable in one command:
`grep -rn "z2_decision" . --exclude-dir=.git --exclude="*.md"`. If a live reader
appears, the field has a function and Options A and C cost more than stated.

FALSE if `ratify.py --apply` does write the candidate file. Checkable by reading
`cmd_ratify`, or empirically: ratify any candidate carrying the block and see
whether its `status: "awaiting_ratification"` line changes.

FALSE if filling the block after ratification does **not** break `--verify` — i.e.
if the signature is not over raw bytes. Demonstrated above that it is; re-runnable
against any candidate.

Also FALSE, in the direction that would retire this candidate, if Z2 rules that a
ratified candidate's own block **should** read `awaiting_ratification` forever —
that the file records what was submitted and the index records what was decided,
deliberately. That is a coherent position and it makes the finding a
documentation defect only, which is Option D alone.

## Evidence

- `CANDIDATE_BLOCK_TEMPLATE.md` — line 340 ("Auto-filled by Z2"), lines 80-84 (the block)
- `.z1-control/ratify.py` — `cmd_ratify` at 417-537 (writes ruling + index only), 447 (byte digest), 279 (`--verify` recomputes), 38-40 (why a hash cannot cover its own field)
- `z1-inbox/INDEX.yaml` — 9 terminal-status candidates, 0 carrying the block
- `z1-inbox/2026-09-22/Q-REFERENT-DECAY-01.md` — the class
- `z1-inbox/2026-09-18/IC-CAND-RATIFY-MANUAL-BYPASS.md` — why byte-pinning is not negotiable

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```

*(This candidate carries the block it is about. Deliberately: removing it would
make the file the only candidate in the tree that opts out of the convention under
review, and Option A is Z2's to choose, not Z1's to take unilaterally.)*

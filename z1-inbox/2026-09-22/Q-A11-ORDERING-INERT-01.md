# Q-A11-ORDERING-INERT-01 — A11 still enforces a property no grade depends on

**Type:** IC · **Author:** Z1 (Claude) · **Status:** awaiting_z2
**Authorised by:** Night, 2026-09-22 — *"File the remaining two candidates."*
**Instance of:** `Q-REFERENT-DECAY-01` (#1 of five)
**Caused by:** `A13`, merged in PR #446 at `8fe1d09`.

---

## The finding

Before #446, `tools/graph_convergence_v1_0.py` picked which access grade counted
by comparing the two graphs' declared `ordering`:

```python
ordered = sorted(graphs, key=lambda g: g.get("ordering", 0))
return ((ordered[-1].get("access") or {}).get("grade") or "READ")
```

`ordering` was load-bearing, and `A11` — *"the two graphs have distinct
`ordering` values"* — protected it. With equal values the sort was arbitrary and
the grade was arbitrary with it. A11 earned its place.

`A13` replaced that with `_effective_access`, which takes the **most
contaminating** declared access regardless of order. `ordering` no longer
reaches the grade at all.

Verified against the merged tool rather than recalled:

```
$ grep -n "ordering" tools/graph_convergence_v1_0.py   # live code only
375:    if len(set(orderings)) != len(orderings):
376:        errors.append(f"A11: graphs share an ordering value: {orderings}")
555:          f"{_esc(g.get('ordering'))} | ...                    # rendered table
```

Two live readers: **A11 itself**, and the display column. Nothing else consults
it.

So A11 now refuses an alignment for violating a constraint that, if violated,
would change no grade. It passes on every current input and would fail on an
input that is no longer wrong. **That is a rule protecting nothing, and it stays
green either way** — which is why nobody would notice.

## The docstring is also stale

`tools/graph_convergence_v1_0.py:38`:

> `ordering` is a causal record — which artifact existed before which — not a
> schedule.

Still true. But read next to A11 it implies the grading depends on that record,
and after A13 it does not. The temporal-position note and A11 together describe
a machine the file no longer is.

## Why Z1 did not just fix it

Three reasons, and the third decided it.

1. Deleting a validation rule is a change to what the grader refuses, and
   `Q-GRAPH-CONVERGENCE-01` — which ratifies that rule set — is still
   `awaiting_z2`. Editing the rules while their ratification is pending is Z1
   pre-empting the decision.
2. There is a real design choice here that Z1 should not make alone (below).
3. **It is the cleanest live instance of `Q-REFERENT-DECAY-01` in the tree.**
   Fixing it quietly would remove the specimen while the class is under
   consideration. It is more useful sitting there, green and pointless, until Z2
   has ruled on the general question.

## What Z2 is asked to decide

**Option 1 — remove A11.** Honest: the rule protects nothing, so delete it.
Cost: `ordering` becomes an undefended provenance field, and if a future change
ever makes it load-bearing again the guard is gone and nothing says why.

**Option 2 — keep A11, restate what it protects.** `ordering` still has a
*reader*: the rendered table, where it tells a human which artifact came first.
Distinctness protects that claim's legibility, not the grade. Cost: a rule kept
for a display property is weaker than it looks, and the next reader has to be
told that on purpose.

**Option 3 — make `ordering` load-bearing again, deliberately.** A13 made the
grade conservative by ignoring order. Whether the *causal* record should
constrain anything — e.g. refusing an alignment whose declared ordering
contradicts the artifacts' own git history — is a live question this candidate
does not answer. Cost: new rule, new surface, and the git-history check is not
free.

**Z1 recommends Option 2**, weakly, and says why the recommendation is weak: it
is the only option that keeps the field's meaning written down while admitting
the grade no longer uses it, and `Q-REFERENT-DECAY-01` argues that unwritten
meaning is exactly how these decay. But Option 1 is defensible and simpler, and
Z1 has no evidence that anyone reads the `ordering` column.

## What this is not

Not a defect in A13. A13 is correct and the attack it closes was real and
reproduced. This is the ordinary residue of a good fix: the guard around the old
mechanism outlived the mechanism. Recording it that way matters, because the
lesson is not "A13 was careless" but **"a fix should say which guards it
retires."**

## Falsifier

FALSE if `ordering` still reaches a grade. Mechanically checkable, and checked:
`_effective_access` reads only `access.grade` from each graph and never
`ordering`; the only other live readers are A11's own distinctness test and the
rendered provenance table.

Also FALSE if A11 protects something Z1 has not identified — for instance if a
downstream consumer of `GRAPH_ALIGNMENT.yaml` outside this tool relies on
distinct ordering. Z1 searched for other readers and found none:
`grep -rn "ordering" --include="*.py" --include="*.yaml" .` returns this tool,
the alignment file's own rows, and nothing else.

## Evidence

- `tools/graph_convergence_v1_0.py` — `_effective_access`, A11 at 375-376, docstring at 38 and 75-79
- PR #446 at `8fe1d09` — the commit that made `ordering` non-load-bearing
- PR #446 comment — where this was first flagged, before the merge
- `z1-inbox/2026-09-22/Q-REFERENT-DECAY-01.md` — the class this belongs to
- `z1-inbox/2026-09-21/Q-GRAPH-CONVERGENCE-01.md` — the pending ratification of the rule set

```yaml
z2_decision: {status: awaiting_ratification, ratified_at: null, ratification_hash: null, z2_notes: ""}
```

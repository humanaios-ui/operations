# Candidate Block: Q-RATIFY-STALE-NOTE-01 — `ratify.py` drops the stale "Not ratified." sentence on ACCEPT

**Z1 Proposer:** Claude (AI agent)
**Date Submitted:** 2026-11-13
**Status:** AWAITING Z2 RATIFICATION
**Carrier:** the pull request that adds this file. Tier 2 by measurement (`.z1-control/ratify.py` is a gate path).

```yaml
candidate_id: "Q-RATIFY-STALE-NOTE-01"
title: "ratify.py 1.3.0: on ACCEPT, remove the 'Not ratified.' sentence from the candidate's single-line index note"
author: "Z1 (Claude)"
proposed_at: "2026-11-13T00:00:00Z"
scope:
  - ".z1-control/ratify.py (two regexes, one helper, one call inside --apply for ACCEPT, one warning, version 1.2.0 to 1.3.0)"
  - "tools/tests/test_ratify_index_write.py (seven new tests on a throwaway tree, one more that guards this candidate's own index note)"
resource_cost:
  cost:
    RAT-min: 10
    Z1-ktok: 120
    CI-min: 2
  dependencies: ["Q-GRAPH-ORPHANS-B1-01 and Q-SYSTEM-GRAPH-REGEN-01 (signed in #1190; they are the first two entries that showed the defect)"]
  blocking_on: []
impact_prediction:
  resource_impact: 1
  areas_affected: [".z1-control/ratify.py", "z1-inbox/INDEX.yaml (future entries)"]
  positive_outcomes:
    - "A signed entry no longer reads both `status: ratified` and `Not ratified.` in the authoritative index."
  risk_factors:
    - "The edit touches the Z2 signing tool. It changes only the `note:` text of the candidate being accepted, never its hash, its status or its ruling."
    - "A note that wraps over several lines is not edited. The tool prints a warning instead, so a human fixes it before committing."
```

## Claim

- **claim:** `ratify.py --apply` set `status: ratified` and left the note, so the first two entries signed from a Z1 PR (2026-11-11, #1190) read "ratified" and "Not ratified" in `z1-inbox/INDEX.yaml`. Version 1.3.0 removes the sentence from a single-line `note:` when the decision is ACCEPT, turns a note that is only that sentence into an empty string, and leaves the note alone for EDIT and REJECT, where the sentence is still true. A note that wraps over several lines is not edited, whichever line the sentence is on; the tool warns instead.
- **found by:** a CodeRabbit review comment on #1190 (minor, verified by reading the file on the PR branch). Copilot's review of this PR then found two more problems, both confirmed by running them: a sentence-only note was left unchanged, and a wrapped note with the sentence on its first line was edited, against the rule above. The unquoted `#1190` in this candidate's own index note also started a YAML comment and cut the parsed note to six words; the note is now quoted.
- **evidence:**

| check | result |
|---|---|
| `python3 tools/tests/test_ratify_index_write.py` | 18 of 18 pass (10 existing, 8 new) |
| same file run against the 1.2.0 `ratify.py` | 5 of the 8 new tests fail (quoted note, plain note, sentence-only note, wrapped-note warning, wrapped note with the sentence on line one); 13 of 18 pass. The eighth guards the index entry, which is a file and not the tool. |
| `python3 .z1-control/ratify.py --smoke-test` | OK |
| `python3 .z1-control/validate.py` | no violations |

- **what the eight new tests cover:** a quoted note with the sentence at the end; a plain note with it in the middle; a note that is only the sentence, quoted and plain, becomes an empty string; the neighbouring candidates' notes are not edited; REJECT and EDIT keep the note; a wrapped note is reported and not guessed at, including when the sentence is on its first line; this candidate's own index note parses in full.
- **not changed:** the hash (it is over the candidate file, not the index), the status mapping, the ruling file, the counts logic, or the two already-signed entries. Their stale notes stay as they are; fixing them is a separate edit.

## Falsifier

This candidate is FALSE if any of the following is observed:

1. After this merges, `ratify.py --apply` on a candidate whose single-line note ends "Not ratified." leaves that sentence in the index entry, or edits the note of any other candidate.
2. `ratify.py --apply` with `--decision REJECT` or `--decision EDIT` removes the sentence.
3. `--apply` produces a different `z2_hash` for the same candidate bytes, signer, date and decision than 1.2.0 did. The tests do not pin this directly; `ratify.py --smoke-test` pins the signature function.
4. Signing this very candidate after the merge leaves "Not ratified." in its own index note.
5. `--apply` on a note that is only the sentence leaves it unchanged or turns the key into null, or edits a note that wraps over several lines.

## Z2 Decision Gate

- [ ] ACCEPT — ratify the change; Z2 supplies the registry entry and ADV run that Tier 2 needs
- [ ] EDIT — propose changes (reply in thread)
- [ ] REJECT — reason (reply in thread)

Ratification instrument, in two steps. Z1 signs neither.

1. **Merge the pull request.** This candidate carries no Intent-OS relay Ruling block, so a merge alone leaves it `awaiting_z2` with no `z2_hash`.
2. **Record the decision, from a checkout of `main` after the merge:**

```
python3 .z1-control/ratify.py Q-RATIFY-STALE-NOTE-01 --decision ACCEPT --by Night          # dry run
python3 .z1-control/ratify.py Q-RATIFY-STALE-NOTE-01 --decision ACCEPT --by Night --apply  # writes the ruling and index entry
```

Order of signing follows the practice for #1158 and #1176: merge first, sign after, as the operator chose on 2026-11-11. The signer hashes the candidate's exact bytes, so edit this file only before step 2.

---

*Generated by Claude (Z1) for Z2 (Night) ratification*

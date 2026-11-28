# Episode 01 pack — "Can AI agents cooperate without taking control?" (DRAFT, NOT FOR RELEASE)

Issue #1329 items 4 and 5, offline only. AUTHORITY_EFFECT=NONE. Nothing here is recorded, uploaded, scheduled or published. Release needs Night's written approval per claim (`human_decision`) and a separate Z2 decision.

| file | what it is |
|---|---|
| `claim_manifest.json` | Every claim the episode may state, tagged observed / source-reported / hypothesis / unknown, with a JSON pointer into `../observed.json` or a code string in `../replay.mjs`, a limitation, and a human decision (all `pending`). |
| `script_witness_draft.md` | Witness-arm script. Each narration line carries claim IDs. The article and conventional-video arms reuse the same lines without IDs or receipt links. |
| `verify_manifest.mjs` | Fail-closed check. Exit 1 if a pointer is missing or its value differs, a code string is gone, a decimal in a claim has no receipt, a script line is untagged, a `[FRAME]` line states a figure, a script figure is not carried by its tagged claim, a claim never appears, or the manifest is marked releasable with unapproved claims. |
| `CORRECTIONS.md` | Change log for claims, including the superseded earlier 600-run figure. |

Run: `node verify_manifest.mjs` (any directory). Checked to fail on a changed script figure, a changed receipt value, a figure in a `[FRAME]` line, and an untagged line.

What the check does not do: it does not judge meaning. A `[FRAME]` line with no figures can still overclaim ("the gate is proven safe" would pass if tagged `[FRAME]`). Every `[FRAME]` line needs human review.

Held for later (not built, on purpose): website transcript and VideoObject metadata, captions, rendered video, YouTube adapter. Each needs a real recorded file and a release decision first; building them now would be templates with nothing to describe. The nine source videos in `../README.md` are still unverified and are not cited in this script.

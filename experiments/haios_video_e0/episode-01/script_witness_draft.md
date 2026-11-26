# Episode 01 — Witness arm script (DRAFT, NOT FOR RELEASE)

Status: DRAFT_NOT_FOR_RELEASE. Issue #1329. AUTHORITY_EFFECT=NONE. No recording, upload or publishing until Night approves in writing.
Format rules: every narration line starts with claim tags from `claim_manifest.json`. A `[FRAME]` line makes no factual claim and may hold no figures. Lines starting with `>` are screen directions. `verify_manifest.mjs` checks this file and fails closed.
On screen for the whole video: claim ID of the current line, and a link to `observed.json` with the JSON key.
No AI-generated person shown as real. No stock footage presented as the test.

## Script

> Title card: "Synthetic test. Not live AI."
[FRAME] This is a synthetic test, not live AI.
[Q01] Can AI agents cooperate without taking control?
[FRAME] The honest answer: this test cannot tell you. It can show what one set of rules costs in a toy world.

> Diagram: four boxes around one pool.
[S01] Four scripted agents share one pool that starts at 100 units, over 60 rounds, with a shortage in rounds 20 to 34.
[S02] No agent may take more than 4 units a round under the capped designs, and the gated design keeps a 25-unit reserve.
[FRAME] The gated design also asks for human consent before each grant.
[C01] A synthetic scripted test ran 600 paired runs across 200 seeds and three designs.

> Chart: reserve kept, three bars.
[C02] The gated group retained its reserve in 200/200 runs, compared with 0/200 for both comparison groups.
[FRAME] That result is built in. The gate cannot hand out the reserve, and the other designs have no reserve at all.

> Chart: useful work, three bars.
[C03] Mean useful work was 591.68 for the gated group, versus 609.72 unrestricted and 609.42 cap-only.
[FRAME] So safety cost something. The next question is which rule paid for it.
[C06] Splitting the gated design apart, most of the useful-work cost came from the 25-unit reserve floor (589.22 with reserve alone), not from human consent (613.79 with consent alone).
[FRAME] And the fairer split between agents came from taking turns, not from the gate.

> Panel: limitations, shown in all three formats.
[C04] Rules were enforced by construction; live agent behavior, security, social outcomes and human comprehension were not tested.
[C07] In the first draft, 2 of 9 checks could not fail; both were rebuilt and now fail when the rule they check is broken.
[C05] Humans retain release decisions; no gate or score grants real authority.

> Challenge card.
[FRAME] What would falsify this? Run the replay yourself. If your numbers differ, or a check passes after you break its rule, this video is wrong.
[FRAME] The code, the receipt and the corrections log are linked below.

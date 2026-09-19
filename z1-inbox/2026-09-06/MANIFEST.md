# z1-inbox/2026-09-06/MANIFEST.md

Z1 → Z3 · drop via Google Drive desktop sync · every file below has Z2 prose approval or is a candidate (see registry_block_and_manifest_090626_v2.md) · verify sha256 before reading; a mismatch is a loud failure

## Registry pin at drop time

`humanaios-ui/operations` REGISTERED.md blob `c0899b9b4f8825d154274b176bb880f233c45995` · last commit `d1fb5f0d2dd9` 2026-08-16 · drift logged in ic030_live_read_090626.md

## Inbox convention

- Path: `z1-inbox/<YYYY-MM-DD>/` in `operations`. Append-only; a correction is a new dated folder, never an edit.
- Every drop carries this MANIFEST.md with sha256 per file, and HANDOFF.md written by the closing side.
- Claude Code opens by verifying every hash, then reads ic030_live_read_*.md, then registry_block_and_manifest_*.md, then acts only on READY rows.
- Nothing in the inbox is on main until Z3 lands it. The inbox is a receiver tank, not the record.

## Files (23)

|file                                     |sha256                                                            |bytes|
|-----------------------------------------|------------------------------------------------------------------|-----|
|CLAUDE.md                                |`a0b34bdbe89ffb435422431d2d09f78eda6e71baa579f5f5787b128c903d4d5e`|4460 |
|H-MKT-01_registry_and_metaculus.md       |`a89254a0abe88644c7c502e01077eee6ec3a1c71a1d0f2aa9c3248879612a175`|3790 |
|HumanAIOS_Final_v7_1_tlc_patched.cfg     |`95071bc5ad7046a28781aff38c50f75272c36b5f1a5eb9085ea8e6c0018187ef`|774  |
|HumanAIOS_Final_v7_1_tlc_patched.tla     |`cc8238a9f99afa7f84410699e372cfb3a951ec1b9c93a734fb500c1d006ab7cd`|19288|
|IC-REWARD-01_standing_ruling.md          |`f66782600f11eb9ecf353e0d80635c5e28d178bda7a7d504dd8c1fc5dd8fc74c`|1441 |
|PHASE2_PLAN_v0_1.md                      |`8f5aa0ed3554cd071111b33f50da95924a299949a388fb555d1464f1090f1caa`|31042|
|PHASE2_PLAN_v0_2_resource_frame.md       |`d0b7a1662a1fd5d8474456125c91d472ad447619e7d42dfe9ba596705b709f28`|10417|
|PHASE2_PLAN_v0_3_repo_graph_program.md   |`17f99636581b45654134ebc644014dd2f4293d0645a3bfc0d46bab455931603f`|7988 |
|empirica_mesh_map_090526.md              |`db02edc3f86bf0774fb6b4c440b276ab273bc404cf789edafac3c854d9197bd1`|4135 |
|ic030_live_read_090626.md                |`dbe118722704fe83b43ffb7708027c558d9b5ce049949ed5bfa4d196f1dd2bd5`|5226 |
|intake_post_agency_agents_draft.md       |`bf0c580e0db54c84b0ed925e1b8b7cd03b0711522eb15673bebe1ef3f6880402`|2595 |
|mechanical_analogies_v1.md               |`b41e36b39be3166ac3db53b0e437c2aa02807d03d9b5b1288afdaa8d3e369493`|5358 |
|patch_manifest_090626.md                 |`7f4035e3ea1d4e2eff087e868cbdee9a6350dcef7ad645c5d3e20729a58a22b6`|2435 |
|practice_workflows_v0_1.md               |`7da395aabe358f7812f38be2c256e3e8f9e52c5ad7af4fb8352c9c2a0fb755bc`|19311|
|queue_patch_orca_090526.json             |`1ed09a24c7acac3c68eb3fb6df2fd7109f125fd88544f100b4fc54fb7db85882`|1324 |
|registry_block_and_manifest_090626_v2.md |`ba848e7e181caeacc08d4f47cf390ec5322ea59ab15801e9e1a91277c8a9b854`|6802 |
|registry_candidate_block_090526.md       |`bf54f8a3fb930fbb4f64ca23c5668089afb1fdb7a21d4593891859c1553a4f56`|3199 |
|repo_delegation_all_nine_v0_2.md         |`83c69350d9de17d39e28dc9f6ff44586e27e9269ca11ffa28a4962a49ef716f4`|4449 |
|repo_delegation_v0_1.md                  |`deb87cd7dbc5d3200fcb8176e8e4514c7cce70e4e2721e0685741934f8a6e9c8`|9095 |
|research-intake.yml                      |`ea146be9252eb6d8230fb3e0d32062f017cd579d51e3151fcfb1e4529fbfa5bd`|6830 |
|research_intake_design_and_doc_updates.md|`bba0de314c40bf0cef1a745d6318eda30094fd7abcbda4413dc9543024629a4d`|6821 |
|research_to_production_plan_v0_1.md      |`0f6d05fa08ffbbeb48f21db1c7766b7f0eed8ff941385842c47b95d86fe58855`|7215 |
|tla_adversarial_review_090626.md         |`76b137b31d256963a5880ba21d64c587114155bca512df192bd31d6a6f01d0d9`|7852 |

## Landing order

CLAUDE.md → CODEOWNERS ×9 + 12 teams → z2_ledger backlog (Aug 16 → now) → registry block → research-intake.yml (Tier 2, ADV) → TLA spec as research/intake row 1 → design docs → queue patch → repo program C1 → intake post (after IC-SCOPE-05 in code)

## First instruction for Claude Code

Read CLAUDE.md. Run §A. Verify this manifest. Report drift between REGISTERED.md at HEAD and the pin above. Do not land anything. Write HANDOFF.md with position · destination · probability.
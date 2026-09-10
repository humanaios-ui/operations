# Registry candidate block + patch manifest — 2026-09-06 (supersedes 090526 block and 090626 manifest)
Z1 → Z2/Z3 · prose ratification noted per row; binding on paste-back with hashes · IC-030 live read before any append · all LAID · intake pipeline 0/40 (ACAT count pending HF read)

## Candidates and rulings
| id | class | statement | falsifier | status |
|---|---|---|---|---|
| H-LT1 | H | Z2 pins a probability on every ruling; Brier-scored under predictor id Z2 | reliability not falling after 30 resolved pins | ratified (prose) 09-03 |
| VMV-01 | ruling | Vision / Mission / 10 Core Values | — | ratified 09-04 |
| **VAL-12** | value | **The system does not state what is not factual, regardless of the sender's tooling.** Applies to every generated artifact: a node not read is absent, not verified | any artifact marks VERIFIED without a run receipt | **ratified 09-06** |
| Q-ORCA-01 | queue | orca as multi-substrate runner; READY, desktop | cannot isolate worktrees / expose per-run output | ratified 09-05 |
| GTM-01 | ruling | agency-agents Discussions is the first intake venue; IC-SCOPE-05 in code first | — | ratified 09-05; sequencing OPEN |
| H-MKT-01 | H | unattended long-running agent workloads dominant by 2030; audit demand rises | 3 falsifiers (intake, quarterly re-read, Metaculus < 0.35) | ratified 09-05 |
| IC-REWARD-01 | IC | no reward/allocation constant changes outside a molt, any layer | live value ≠ last ratified molt value | ratified 09-05 |
| CON-01 / PAT-01 | ruling / F | whiteboard rendering; pattern read | — | ratified 09-05 |
| ANALOGY-01 | ruling | railway + pneumatic power + pneumatic instrumentation coverage table; 1 deliberate GAP | a ratified property with no analog and no logged GAP | ratified 09-06 |
| WF-01 | ruling | practice_workflows_v0_1 (11 loops, one skeleton) | any Tier 1 action without a hash in a practice chain | ratified 09-06 |
| DEL-01 | ruling | repo delegation v0.1 + all-nine v0.2; CODEOWNERS ×9; 12 teams | 30 days, still all-Z2 review | ratified 09-06 |
| R2P-01 | ruling | research-to-production plan v0.1 (6 stages) | stage closes with no receipt | ratified 09-06 |
| MESH-01 | F | empirica mesh map: 15 practices → 12 nodes; 4 count inconsistencies; OA DISPUTED; SS present not missing | — | ratified 09-06 |
| P2-01 | plan | Phase 2 v0.2 resource frame + v0.3 repo/graph amendment | ledger cannot state Z2 min per practice at close | v0.2/v0.3 candidate; direction ratified 09-06 |
| **F-CHAIN-01** | F | in a multi-substrate rendering chain with no verifier read, claimed-fix count rises per hop, verified-fix count stays 0 (specimens: TLA spec 4 hops; charter 1 hop; orchestration 1 hop) | a hop with a runtime still adds unrun claims | **ratified 09-06**; no intermediates exist for specimen 1 — chain + end-state only |
| **IC-TLA-01** | IC | TLA spec v7.1 shipped as "Final" with 10 amendments marked done; never parsed by TLC (IC-031 class) | — | **ratified 09-06** |
| **IC-TLA-02** | IC | "escalation is atomic" false in its own model: P11 violated at depth 2; "quarantine terminal" false: P17 violated at depth 5 | — | **ratified 09-06** |
| **H-TLA-01** | H | CredPolicy regulator (calibration → priority → envelope) reproduces the v0.2 resource ordering on the 15-practice pin set | cred-ranking disagrees with cost-per-kept ranking on > 5 of 15 | **ratified 09-06**; CredPolicy promoted into LEDGER-ECON |
| RI-01 | gate | research-intake workflow (Tier 2; ADV: no manifest / forged chain hash / fake DOI must all be caught) | after 10 rows, dataset cannot rank providers by claim-to-receipt ratio | ratified 09-06 (design); LAID |
| REPO-01 | program | Phase 2 repo program: clone → index → audit → graph → map → merge (v0.3 §C) | graph node sha ≠ repo HEAD; audit marks VERIFIED without run | **ratified 09-06** (direction) |
| VAL-11 | OPEN | reciprocity as value or as give-back series | give-back rate undefinable against intake | research running |
| Z1-STRIKE-01 | correction | Z1's 09-06 line "the comparison isn't intelligence, it's whether the thing can run something" is struck as an excuse for non-factual output; superseded by VAL-12 | — | logged |

## Session document updates applied this turn
| doc | update |
|---|---|
| research_intake_design_and_doc_updates.md §3 | manifest example: `intermediates_retained: false` is the actual state for row 1; per-hop diff unavailable; blind-spot log records chain order + end state only |
| PHASE2_PLAN | v0.3 amendment added (repo program); v0.2 §7 open item 1 (`z2_budget_p2`) now covers mesh 17 h + repo program 4.5–12 h |
| practice_workflows_v0_1.md | every practice's WORK step gains: "block cloned at pinned HEAD; index + audit + graph are the practice's first Tier 0 outputs"; epistemology gains research-intake wake; QA gains TLC/jar pin |
| repo_delegation_all_nine_v0_2.md | each practice row gains `graphs/<practice>/` as an owned output path; `research/intake/` + `research/datasets/` → epistemology + QA |
| research_to_production_plan_v0_1.md | stage 0 gains research-intake + repo program C1–C2 as INPUT receipts for stage 1 |
| mechanical_analogies_v1.md | §2 gains one row: "repository as BLOCK; clone = TOKEN; index = GAUGE; audit = FILTER; graph = RECORDER; cross-org map = INTERLOCK" — no new GAP |
| tla_adversarial_review_090626.md | §Routing: "salvage" struck; spec → `research/intake/HumanAIOS_Final.tla` as dataset row 1 with manifest; patched pair kept as the run receipt |
| empirica_mesh_map_090526.md | note: 15 audits → research-intake rows 2–16; the mesh's ai_ids are the C5 join keys |

## Files in the patch set (18)
09-03: optimizer design · learning-trajectory layer · role-spec audit · market report
09-05: queue_patch_orca · intake_post draft · H-MKT-01 + Metaculus · IC-REWARD-01 · mechanical_analogies_v1 · empirica_mesh_map · research_to_production_plan_v0_1
09-06: repo_delegation_v0_1 · repo_delegation_all_nine_v0_2 · practice_workflows_v0_1 · PHASE2_PLAN v0.1/v0.2/v0.3 · tla_adversarial_review + patched .tla/.cfg · research-intake.yml · research_intake_design · this block

## Landing order (unchanged in kind, extended)
CODEOWNERS ×9 + 12 teams → this block → research-intake.yml (Tier 2, ADV) → TLA spec as row 1 → design docs → queue patch → repo program C1 per practice → intake post (after IC-SCOPE-05)

## Blockers
1. GitHub PAT — unblocks everything above
2. IC-030 live read — drift vs my record already demonstrated (9 repos / 1,012 files / SS present); expect more on REGISTERED.md itself
3. IC-SCOPE-05 in code before the intake post
4. `TLA_TOOLS_SHA256` repository variable (Z2 sets; jar is a constant)
5. `z2_budget_p2` — the phase envelope; nothing in v0.2/v0.3 is ordered until it exists

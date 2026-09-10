# Research intake workflow — design + documentation updates
Z1 · 2026-09-06 · ratified in prose (routing, F-CHAIN-01, IC-TLA-01/02, H-TLA-01, CredPolicy → LEDGER-ECON) · this workflow LAID

## 1. What it is
A GitHub Actions workflow (`.github/workflows/research-intake.yml`) that turns every external research artifact into a dataset row. It replaces "salvage the spec" with "collect the specimen." The TLA spec is row 1.

The rule it enforces: **nothing said about an artifact is recorded unless the workflow ran it.** Status words are counted as claims; runs and hashes are counted as receipts; the ratio is the data.

## 2. Flow (framework primitives)
```
research/intake/<artifact> + <artifact>.provenance.json      ← TOKEN: no manifest, no entry
  → provenance_lint (chain of hops, provider, model, prompt/output hashes)   FILTER
  → claim_census: status adjectives vs receipts                              GAUGE
  → lints: falsifier_lint · claim_lint · citation_verify (VOID-CIT)          FILTER (results are data, not build failures)
  → run: TLC for .tla (jar pinned by SHA that Z2 sets) · compile/pytest for .py   the actual receipt
  → row.json: chain, hops, claimed vs verified, defects, tier, prev_row_hash, row_hash
  → research/datasets/research_intake.jsonl  (append-only; refuses on chain break)   CHECK valve → RECORDER
  → registry candidate issue (F/IC)                                          → Z2, never REGISTERED.md
  → PR to land the row                                                       Z3
```
No date anywhere. Cost per row: ~0 Z2 minutes until the candidate issue; TLC bounded to `TLC_TIMEOUT`.

## 3. Provenance manifest (research/intake/SCHEMA.md)
```json
{
  "artifact": "HumanAIOS_Final.tla",
  "origin_prompt": "Map resource economics to core computing systems processes",
  "requester": "Z2",
  "chain": [
    {"hop": 1, "provider": "DeepSeek", "model": "", "date": "", "prompt_hash": "", "output_hash": ""},
    {"hop": 2, "provider": "xAI Grok", "model": "", "date": "", "prompt_hash": "", "output_hash": ""},
    {"hop": 3, "provider": "Meta AI",  "model": "", "date": "", "prompt_hash": "", "output_hash": ""},
    {"hop": 4, "provider": "OpenAI ChatGPT", "model": "", "date": "", "prompt_hash": "", "output_hash": ""}
  ],
  "claimed_version": "v7.1",
  "claimed_status_words": ["Final", "atomic", "terminal", "enforced"],
  "intermediates_retained": false
}
```
`intermediates_retained: true` unlocks the per-hop diff (which hop added `WITH`, which added "atomic") — the provider-predicts-blind-spot dataset. Without intermediates the row records the chain and the end state only.

## 4. Dataset row (what the research collects)
| field | source | feeds |
|---|---|---|
| hops, providers in order | manifest | blind-spot log; F-CHAIN-01 |
| claimed_fixes (amendment/“done” count) | census | F-CHAIN-01 numerator |
| receipts (hashes, run logs, resolving URLs) | census + runs | F-CHAIN-01 denominator |
| falsifier present / absent | falsifier_lint | epistemology overconfidence detector |
| citations VOID / total | citation_verify | VOID-CIT rate by provider |
| run result (parse / assume / invariant / depth / first violating action) | TLC or pytest | IC-TLA class; the only VERIFIED-tier cell |
| tier | derived | CLAIM if no run; CLAIM+LINK if links resolve; VERIFIED only if a run produced the receipt |
| prev_row_hash, row_hash | dataset_append | CHECK |

F-CHAIN-01's falsifier is computed from this file: if a row with `run_result` available still shows claimed_fixes rising with no receipts, and the substrate had tools, the finding's stated cause is wrong.

## 5. Five small tools the workflow expects (all new; LAID)
`tools/provenance_lint.py` · `tools/claim_census.py` · `tools/tlc_result_parse.py` · `tools/research_row.py` · `tools/dataset_append.py` — each < 80 lines; `citation_verify.py` is the VOID-CIT pass already designed. Existing: `falsifier_lint.py`, `claim_lint_v1_0.py`, `registry_issue_compiler.py`.

## 6. Ownership and gates
- Owner: epistemology (dataset, census, lints) + quality-assurance (runs, jar pin, timeouts). CODEOWNERS: `research/intake/ research/datasets/ tools/{provenance_lint,claim_census,tlc_result_parse,research_row,dataset_append}.py @humanaios-ui/epistemology @humanaios-ui/quality-assurance @carly-r-anderson`.
- `TLA_TOOLS_SHA256` is a repository variable Z2 sets — the jar is an external dependency and its hash is a constant.
- Tier 2 to land (new gate); ADV run: submit an artifact with (a) no manifest, (b) a forged prev_row_hash, (c) a citation to a nonexistent DOI — all three must be caught before KEEP.

## 7. Documentation updates (apply on landing)
| doc | change |
|---|---|
| **registry_candidate_block_090526.md** | append: F-CHAIN-01 (ratified), IC-TLA-01 claimed-verified-never-run (ratified), IC-TLA-02 P11 false / atomic claim (ratified), H-TLA-01 CredPolicy regulator (ratified); strike Z1's "runtime explains it" framing — replaced by Z2's ruling: *the system does not state what is not factual, regardless of the sender's tooling* (VAL-12 candidate, or fold into value 1) |
| **practice_workflows_v0_1.md** | epistemology loop: add research-intake as its second wake trigger; QA loop: add jar-pin + TLC runs; grok-crossref: the per-hop diff is its input when intermediates are retained |
| **repo_delegation_all_nine_v0_2.md** | `research/` block gains `intake/` and `datasets/research_intake.jsonl`; the README's missing three directories are now one real one |
| **PHASE2_PLAN_v0_2** | queue item 7 (lint 15 P1 audits) runs through this workflow — the fifteen audits are rows 2–16; cost unchanged (~0 Z2 min); envelope row for epistemology gains "research-intake landed" as its INPUT receipt |
| **mechanical_analogies_v1.md** | no change; the workflow is FILTER → GAUGE → RECORDER as drawn |
| **research_to_production_plan_v0_1.md** | stage 0 gains: research-intake landed and ADV-passed; stage 3 gains a third pin source (provider rows) |
| **empirica_mesh_map_090526.md** | note: the 15 audits enter research-intake as specimens; their claim census is the mesh's first measured overconfidence number |
| **patch_manifest** | +3 files: research-intake.yml, this doc, SCHEMA.md (to write); TLA spec + patched pair move from "salvage" to `research/intake/` row 1 |
| **LEDGER-ECON** (Z2's doc; not in my tree) | add the CredPolicy regulator: calibration → priority → envelope, as the formal form of "resource management governed by behavioral calibration"; weights are Constants with molt_ids (IC-REWARD-01) |

## 8. Falsifier for the workflow
If after 10 rows the dataset cannot answer "which provider's outputs carry the highest claim-to-receipt ratio," the row schema is wrong and this is an IC. If it can, F-CHAIN-01 has its first N.

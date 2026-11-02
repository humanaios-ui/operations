# HumanAIOS Knowledge Graph — Repo Map v0.1

**Status:** unratified. Z1 working map. No Z2 ratification recorded.
**As of:** 2026-10-16
**Live graph:** Supabase project `HumanAIOS` (`ksinisdzgtnqzsymhfya`), tables `public.kg_nodes` (22 rows) and `public.kg_edges` (16 rows). Row security is on; reads need the service role.
**Repo snapshot:** `kg/humanaios_kg_v0_1.json`
**Checker:** `python3 tools/kg_map_check_v0_1.py`

## What the graph says

Ten reference books inform twelve repo areas. Each edge carries a rationale.

| Area | Informed by | Repo status |
|:--|:--|:--|
| A01 ACAT core scoring | Foundations of ML | verified path |
| A02 ACAT-NUM robustness | Foundations of ML; Probabilistic ML Vol 1 | **no repo trace** |
| A03 Governance Z1/Z2 gates | Algorithms for Decision Making; Fairness and ML | verified path |
| A04 Findings registry | Algorithms for Decision Making | verified path |
| A05 Decision log / comparison engine | Sutton & Barto; Distributional RL; Probabilistic ML Vol 2 | verified path |
| A06 CBDV / ACAT-Reverse | Multi-Agent RL; Probabilistic ML Vol 2 | partial |
| A07 Empirica mesh coordination | Multi-Agent RL | verified path |
| A08 Agent identity and provenance | Deep Learning | partial |
| A09 Dimension parity / fairness | Fairness and ML | partial |
| A10 ASC Gateway | Understanding Deep Learning | partial |
| A11 Income jobs linked to ACAT | — (no edge) | verified path |
| A12 Research Hub / forecast pipeline | Probabilistic ML Vol 1 | verified path |

All ten books have at least one edge. A11 has no edge.

## Checks against the repo

Checked on 2026-10-16 against this checkout.

- **Edges match the summary.** All 16 edges and the seven main links match the HumanAIOS notes.
- **Every table in `table_ref` exists** in the live `public` schema.
- **Code-side coverage.** Seven areas have a verified repo path. Four are partial (one indirect reference or code only). One has no trace at all:
  - **A02 ACAT-NUM:** no code or docs in this checkout. Only unrelated numerology text. Repo may live elsewhere. Not checked.
  - **A06 CBDV / ACAT-Reverse (partial):** no code in this checkout. Related gating-test tables appear in `audits/CORPUS_LIVE_VERIFICATION_S-092126.md`.
  - **A08 agent identity (partial):** `acat_sessions` appears in the MCP wrapper. `agent_name_canonical_map` is not named in any repo file.
  - **A09 dimension parity (partial):** the scorer exists. The per-dimension tables are not named in the repo.
  - **A10 ASC Gateway (partial):** one indirect mention in `PRACTICE_SPEC_BUNDLE.md`. No gateway code here.
- **Table names not in the repo:** `mesh_state`, `ser_coordination`, `blocker_routing`, `learning_trajectories`, `acat_stats_v1`, `ratified_decisions`, and the `acat_dimension_*` per-dimension tables. Live tables exist. The repo just does not name them.
- **Mismatch to confirm.** The notes say the comparison engine has no table yet. The graph gives A05 a `table_ref` (`learning_trajectories`, `task_outcomes`). One of the two is out of date.

## Limits

- GitHub access in this session covered only `humanaios-ui/operations`. Areas whose code lives in another repo show as "no repo trace" here, not as missing.
- The checker validates repo paths and edge integrity only. It does not query Supabase. Table existence was checked by hand.
- Edges are informs-type links from notes. They are not evidence that the area is correct or well-measured.

## Next steps (for Z2 to decide)

1. Confirm A02 and A06 repo location, or mark them as external.
2. Confirm A05 table link.
3. Decide whether a Supabase-to-snapshot sync job should regenerate `kg/humanaios_kg_v0_1.json`. Today it is a hand snapshot.

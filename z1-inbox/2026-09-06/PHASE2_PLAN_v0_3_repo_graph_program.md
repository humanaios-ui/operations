# PHASE 2 PLAN v0.3 — amendment: repository program
Z1 · 2026-09-06 · ratified direction (Z2, prose) · extends v0.2; resource frame unchanged · all LAID

## A. The requirement (as ruled)
Every practice, as code owner of its paths:
1. **Clones** its repositories — GitHub and/or local.
2. **Applies** the standard governance to them: gate files Z2-only; Tier 0/1/2; IC-030 live read; IC-REWARD-01; VAL-12 (state nothing non-factual).
3. **Tracks** local repositories by local commits (no push required; commits are the record).
4. **Audits** GitHub repositories: every document, every workflow.
5. **Indexes** all GitHub files, workflows, and API/MCP surfaces.
6. **Builds a practice graph** from its files and workflows: an ontological canvas of concepts and content, in railway/pneumatic terms.
7. **Maps** its graph to the empirica local-repository graphs → orchestration, visibility, document control, git trace.

## B. Framework restatement
A practice's repository is its **BLOCK**. Cloning it is taking the **TOKEN**. The index is the **GAUGE** read of the block. The audit is the **FILTER** pass. The practice graph is the **RECORDER** trace of what the block contains and how pressure moves through it. Mapping to empirica's graph is the **INTERLOCK** — two signalling systems agreeing on the same track layout before any train crosses between them.

## C. Program steps, priced (no dates — envelopes; opens when INPUT exists)
| step | INPUT receipt | envelope (Z2 min · Z1 tokens) | OUTPUT receipt | tool |
|---|---|---|---|---|
| C1 clone | CODEOWNERS landed for the practice (PAT) | 0 · 5k | `clone_sync_health_v1_0` report, repo HEAD sha pinned | existing |
| C2 index | C1 | 5 · 20k | `graphs/<practice>/index.json`: every file (path, sha, type, size), every workflow (name, triggers, jobs, steps, secrets referenced), every endpoint/MCP tool it calls or exposes | `tools/repo_index.py` (new, LAID) |
| C3 audit | C2 | 15 · 40k | `graphs/<practice>/audit.json`: per doc — claim census, tier, falsifier present, STALE (last-read date); per workflow — triggers verified, secrets present, gate behaviour (can it fail?), NO_GATE flag | `claim_census.py` (from research-intake), `falsifier_lint.py`, `workflow_audit.py` (new) |
| C4 practice graph | C2 + C3 | 20 · 60k | `graphs/<practice>/graph.json` + `.mermaid` (schema §D) | `tools/practice_graph.py` (new) |
| C5 map to empirica | C4 **+ empirica local graph format confirmed readable by a live read (Z2 ruling 09-06; format is CLAIM until then — the earlier read was rate-limited)** | 10 · 30k | `graphs/<practice>/empirica_map.json`: join on `ai_id` + path sha; unmapped nodes listed as GAP | `tools/graph_join.py` (new) — **does not run until the INPUT receipt exists; no partial map from an unread format** |
| C6 union view | all C4 | 15 (Z2 reviews the union) · 20k | **Per-practice graphs stay authoritative (Z2 ruling 09-06). `system_graph.json` is not merged; a read-only union view `graphs/union.json` + `.mermaid` is generated from the eleven files. Dangling-node check runs on the union; a dangling node is reported against the practice whose edge points at it** | union generator (new; reads, never writes practice graphs) |
Per practice ≈ 65 Z2 min if every step is reviewed; realistic ≈ 25 (C3 and C6 are the review-heavy ones). Eleven practices ≈ 4.5–12 h of Z2 time. That is the price; it enters `z2_budget_p2` alongside the mesh's 17 h, and the regulator decides what fits.

Local-only repositories: C1–C4 run locally; C5/C6 consume the exported `graph.json`, which is committed to the GitHub repo by the practice — the graph crosses, the local commits don't.

## D. Practice graph schema (one schema, two layers, one join)
**Content layer** — what the repository *is*:
- node types: `repo · dir · file · doc · workflow · job · step · tool · endpoint · mcp_tool · constant · ledger · test`
- edge types: `contains · triggers · reads · writes · calls · gates · tests · cites · exposes`
- every node carries `sha`, `path`, `owner_practice`, `tier` (0/1/2 for what changing it requires), `last_read`

**Concept layer** — what the repository *means*:
- node types: the system_graph v0.2 nodes (Q, FS, OM, PRS, AG, ADV, TC, EV, NF, REG, CONST, MOLT, ML, Z2, CIG, MK, OTS, RC, ST, OPT) and the framework primitives (BLOCK, TOKEN, INTERLOCK, REGULATOR, PILOT, CHECK, RELIEF, GAUGE, FILTER, RECORDER, DEADWEIGHT, BUMPLESS)
- edge types: the v0.2 typed edges (work order, events, candidate block, RATIFY, merge, root, live read, callouts…)

**Join** — `implements` edges from content nodes to concept nodes (`.github/workflows/findings-registry-gate.yml` —implements→ CIG; —is→ INTERLOCK). A concept node with no `implements` edge into it is **LAID-with-no-content**. A content node with no edge out is **unclassified content** → GAP callout. Both counts are the practice's graph-completeness gauge.

**Framework tagging rule:** every content node gets exactly one primitive tag. A file that can't be tagged is either dead (delete candidate) or a missing primitive (Tier 2 candidate). That is how the canvas stays ontological rather than decorative.

## E. Mapping to empirica (C5)
- empirica's local graph = each practice's `.empirica/` record (project.yaml, practice-spec.yaml, reflex-log checkpoints, artifact graph).
- Join keys: `ai_id` (practice), file path sha, workflow name.
- Output: for every empirica artifact node, the HumanAIOS content node it corresponds to, or GAP; for every HumanAIOS concept node, the empirica practice function it maps to (§empirica_mesh_map), or GAP.
- **What it yields:** orchestration (Cortex reads one merged graph, not fifteen READMEs); visibility (LAID vs content-backed per concept node); document control (`document-control.yml` reads controlled-doc nodes from the graph, not a hand list); git trace (commit → file node → practice → concept — every change locatable in the canvas).

## F. Governance applied inside each block (from A.2)
- Gate files remain Z2-only in every repo regardless of practice ownership.
- Every Tier 1 change in a practice's block carries a ratification hash in its event chain.
- Every public number in a practice's docs traces to a registry line or dataset hash (IC-031).
- The practice's own audit (C3) is countersigned by epistemology; no practice signs its own audit (SR 11-7; the evaluator rule generalised).
- VAL-12 applies to every generated artifact: index, audit, and graph state only what the run found. A node the indexer didn't read is absent, not "verified."

## G. Pins for this program (resource events)
- P(all 11 practices reach C4 inside their envelopes) — Z1: 0.45. Reason: C3 is where the mesh's claim census meets its own workflows, and I expect NO_GATE flags on several of the 26 `operations` workflows.
- P(the union view has zero dangling nodes on first generation) — Z1: 0.3. (Per-practice graphs are not merged; the union is a read-only view.)
- P(≥ 30% of `operations` files receive no primitive tag on first pass) — Z1: 0.6. That number is the first honest measure of how much of the 1,012 is content versus residue.

## H. What fails
A practice fails this program if its graph contains a node whose `sha` does not match the repo at the pinned HEAD (a graph built from memory, not from a read), or if its audit marks any doc VERIFIED without a run receipt (VAL-12).

## I. Rulings applied (Z2, 2026-09-06)
- C5 waits for a live read confirming the empirica local graph format. Until then the format is CLAIM and `graph_join.py` does not run.
- Eleven practice graphs stay per-practice and authoritative; `graphs/union.json` is a read-only union view. `system_graph.json` is not a merge target.

## J. Open for Z2
- Envelope for the program (it competes with the mesh's 17 h inside `z2_budget_p2`).
- Who performs the empirica format read (needs the PAT or an authenticated session; the anonymous read was rate-limited).

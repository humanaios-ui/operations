# HumanAIOS graph integration inventory (PR #896)

Status: proposed observational interoperability; no production migration or admission authority.

| Surface | Producer / input | Output | Consumers | Trust boundary |
|---|---|---|---|---|
| Repository graph (#630, open proposal) | Deterministic repository compiler; tracked tree and allowlisted metadata | Graph schema, machine-readable graph and GraphML | graph_lookup and reviewer inspection | Snapshot observations and bounded inference, not successful CI or admission |
| Codebase Atlas (#835) | Tracked files, AST imports, valid links, workflow invocations | HTML/SVG, JSON, Markdown, Mermaid; evidence sidebar | Humans and advisory graph views | Read-only path-pinned projection; never authoritative system_graph |
| Temporal graph (#841) | system_graph.json plus Git history | graph_timeline/system_graph_timeline.json and HTML | Timeline viewers | Commit dates do not establish ratification; unresolved implementations remain flagged |
| Evidence Graph | Evidence references and associated claims | Existing independently validated records | Review and research | A graph edge does not attest independent execution |
| Session Graph | Session observations and references | Session records | Continuity and research | Private session content must not be projected publicly by default |
| SCVC | Continuity verification observations and independently witnessed outcomes | SCVC records and evidence | Milestone reasoning | Verified witness evidence distinct from proposed claims |
| Repository Coordinator | Governed admission policy, authenticated reviews, CI and decisions | Admission receipts and state | Protected workflow | Only authorized control plane makes decisions |

## Overlap and preservation
- Atlas and repository graph both describe repository topology. Retain their individual producers; normalize *copies* of their observations into the interchange format rather than run another canonical compiler.
- Temporal graph dates describe Git activity; SCVC describes continuity claims. Never merge them into a single authoritative timestamp.
- Evidence, Session, SCVC, and Coordinator have different provenance and disclosure rules. A common node/edge shape is not permission to merge trust levels.
- #630 remains a proposal until independently admitted; do not turn its projected output into a policy dependency.
- `graph_lookup` is a downstream reader, not proof the proposed compiler is deployed.

## Initial integration contract
See `docs/graph_integration/observation_projection_v0.schema.json`.
One projection is a **read-only derived copy** with explicit source refs, exact source revision, observation time, evidence class, and uncertainty state. The contract defines no commands, writes, admissions or promotions.

## Mapping and deployment order
1. Inventory actual producer paths and consumer imports at each pinned repository head. Rows above are design-level, not a verified comprehensive file enumeration.
2. Run fixture-only contract tests offline.
3. Add source-specific adapters as separate read-only PRs, measuring unmapped records and source coverage.
4. Compare Atlas and #630 observations against common file-revision fixtures; preserve disagreements as conflicts.
5. Only after validated adapters exist, wire an opt-in advisory query/view. Never put projection output in Coordinator authorization input.

## Known gaps and falsifiers
- Incomplete implementation-to-file matches in #841 must be `unresolved`, never fabricated links.
- Missing evidence, unknown revisions, contradictory claims, and redacted private sources must not appear verified.
- A comment or graph observation cannot stand in for authenticated APPROVED review or exact-head protected CI.
- Fail closed on malformed record identifiers, duplicate IDs, missing source, invalid graph endpoints, attempted authority fields or unsupported confidence states.

## Acceptance for PR #896
- Inventory, non-authoritative versioned exchange schema, standalone test fixtures and tests.
- No privileged workflow/policy/manifest edits.
- Run tests on PR head; require CodeRabbit and required human APPROVED review plus separately verified protected CI before any admission.

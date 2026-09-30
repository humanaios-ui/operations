# Lasting Light AI Repository Graph Pilot

## Result

The Repository Evidence Graph Method reproduced successfully against `humanaios-ui/lasting-light-ai` without modifying the target repository.

The target was frozen at commit `f2cb8a60419f04d12d6f7f5ab97b272d65f41402` with a clean worktree. The profile remained in the operations repository as an explicit external method input and was hash-pinned into the result.

This is a successful **method replication**, not a certification of Lasting Light AI and not proof that its declared research, governance, tests, or workflows operate as described.

## Reproducibility receipt

| Field | Result |
|---|---|
| Method | `REPOSITORY_EVIDENCE_GRAPH_METHOD` v0.1.0 |
| Target | `humanaios-ui/lasting-light-ai` |
| Target commit | `f2cb8a60419f04d12d6f7f5ab97b272d65f41402` |
| Worktree | `CLEAN` |
| Profile scope | `EXTERNAL_METHOD_INPUT` |
| Profile SHA-256 | `864fd1441ac073aed950375d9fe36ca203e851d59382b2b1656479bedaa2353e` |
| Source-tree SHA-256 | `8b5f9eec74fe8b477c0958798efd04fc90f1241323511d26bffeeedaa373c245` |
| Graph SHA-256 | `593983e59926befbcf1f8d83d0d11c62ab17021b79c9b6a30a2748fe073edbee` |
| Structural validation | PASS |
| Two-build canonical match | PASS |
| Two-build source-tree match | PASS |
| Target mutations | None |

The machine-readable receipt is preserved at `architecture/repository-knowledge-graph/pilots/lasting-light-ai-method-receipt.json`.

## Graph snapshot

| Measure | Count |
|---|---:|
| Nodes | 1,015 |
| Edges | 1,752 |
| Views | 5 |
| Static local imports | 95 |
| Test-to-implementation relationships | 3 |
| Bounded inference assertions | 28 |
| Output files | 16 |

All 28 assertions came from `RGM-INF-LOCAL-DEPENDENCY-01`. They identify possible two-hop static dependency paths, such as:

- `src/App.tsx` may depend transitively on `src/lib/contamination.ts`;
- `src/App.tsx` may depend transitively on `src/lib/supabase.ts`;
- `src/pages/Experiment.tsx` may depend transitively on `src/lib/storage.ts`;
- `src/index.tsx` may depend transitively on `src/components/AcatTool.tsx`.

These are review candidates. They do not establish runtime execution, causal influence, capability, deployment, or authority.

## Material findings

### 1. Framework-audit workflow parse failure

The graph preserved one parse finding for `.github/workflows/framework-audit.yml`. The file contains a YAML document start at line 1 and a second document separator after its opening comments. A single-document workflow parser therefore reports:

> expected a single document in the stream but found another document at line 5

This is concrete source evidence that the file is not one ordinary YAML document. It is **not** proof that this defect caused any particular GitHub Actions result; workflow-run causality would require separate live execution evidence.

### 2. Unresolved repository-path references

The graph preserved 31 path-like references that do not resolve to current repository artifacts. Examples include:

- `data/validation_phase1.csv`
- `src/lib/EpistemicDJ.ts`
- `src/lib/MachineVoiceArena.ts`
- `src/components/BehavioralNavigator.ts`
- `public/methodology.html`
- `src/acat2c/scoring/aggregation.py`

These are documentation/code-drift or missing-artifact candidates. Each requires human scoping because an example, planned path, archived component, and accidentally stale reference have different meanings.

### 3. Live GitHub state remains unknown

Nineteen labeled issue or PR references were extracted, but the compiler did not hydrate their live state. They remain references rather than evidence about whether the underlying work is open, merged, closed, or current.

### 4. Workflow-to-test inference did not fire

The source graph contains three static `TESTS` relationships, but the workflow rule emitted zero `MAY_EXERCISE` assertions. The current workflow parser follows explicit repository paths in `run:` steps; it does not expand `npm` package-script indirection into individual test files.

This is a useful method limit, not a failed test. A future adapter may resolve package scripts, but it must continue to distinguish “workflow may reach this test path” from “workflow ran” and “test passed.”

## Human review result requested

The pilot supports the following **Z1 recommendation**:

- `ACCEPT READ MODEL` for bounded diagnostic use;
- `REQUEST EVIDENCE` for the workflow parse finding and any unresolved paths that support current public or research claims;
- do not promote any of the 28 dependency assertions beyond `MODEL_INFERRED` without premise review.

Only a human reviewer may record the disposition.

- [ ] ACCEPT READ MODEL
- [ ] REVISE PROFILE
- [ ] REQUEST EVIDENCE
- [ ] REJECT RUN

Reviewer rationale: ________________________________________________

## Replay command

```bash
python3 tools/repository_knowledge_graph_v0_1.py method \
  --repo /path/to/lasting-light-ai \
  --profile /path/to/operations/architecture/repository-knowledge-graph/profiles/lasting-light-ai.json \
  --allow-external-profile \
  --output /tmp/lasting-light-ai-graph
```

The run additionally verified every manifest hash, the gzip round trip, GraphML parsing, CSV row counts, and the JSONL inference count.

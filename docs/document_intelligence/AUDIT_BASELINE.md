# Document intelligence reconciliation — baseline

## Scope and authority

This is the first, bounded census/report slice for [issue #923](https://github.com/humanaios-ui/operations/issues/923), not a completed semantic audit. The source snapshot is the exact `main` commit `ad44c46f58beb5f3c7d9de1d248e7686795417dd`. The machine-readable path inventory is `fixed_head_inventory.json`; `fixed_head_dashboard.md` is generated from it.

The inventory records Git tree metadata and path-based classifications only; it does not read target-tree file payloads, verify source truth, infer ownership, or authorize a correction. Its `generated_by.sha256` pins the exporter bytes used to create the inventory, not an authenticated reviewer. `PENDING` means not assessed; it does not mean irrelevant. No private Drive/ChatGPT payload was opened, copied, or included.

## Census accounting

| Exact-tree disposition | Paths |
|---|---:|
| Total | 2,106 |
| Inspected for the bounded census | 0 |
| Evidence-mapped | 0 |
| Metadata-only | 8 |
| Excluded with reason | 2 |
| Blocked | 0 |
| Pending | 2,096 |

The disposition counts sum to the exact tree total. The eight metadata-only exceptions are the tracked symlink and seven paths classified as media by suffix. The two excluded paths are `.env.example` names: only the path is classified as potentially sensitive; the examples' contents were not inspected and are not asserted to contain secrets. Every exception is individually listed in the generated dashboard and inventory. No symlink target was followed.

File-kind counts are path/mode heuristics, not content verification: 886 prose-document paths, 517 source-code paths, 381 workflow/config/schema paths, 166 test/fixture paths, 142 other/unknown paths, 7 paths with media suffixes, 4 known generated/rendered paths, 2 potentially sensitive path names, and 1 symlink. These counts also sum to 2,106.

The formal `inspected` count is zero because this census has not completed a per-file content disposition. A small set of files was sampled to map the existing architecture; those samples remain `PENDING` in the all-path inventory. The inventory records owner and generator as `UNRESOLVED` and document-registry, approval, lifecycle, reference, test, and visibility metadata as `UNASSESSED` / `NOT_CROSS_REFERENCED`; no ownership or source relation is fabricated.

## Existing surfaces and verified status

| Surface | Evidence observed | Boundary / gap for this issue |
|---|---|---|
| Controlled documents | `document-registry.yaml`, `.doc-control/validate.py`, and `docs/DOC_LIFECYCLE.md` define registry checks and FPCP states. The validator run on this snapshot reported 49 registered documents, no structural violations, and 29 overdue-review warnings. | The validator checks declared `doc_id` frontmatter and registry structure; it is not a full path-to-claim/source map. The census has not yet joined every path to registry IDs, approval state, owner, generator, lifecycle, references, or tests. |
| Document-control plan | `DOCUMENT_CONTROL_PLAN.md` is absent from this exact tree, although the registry and document-control tooling refer to it. | This is a documentation consistency gap; this PR does not reconstruct or claim authority from the absent file. |
| CodeRabbit coverage inventory | `tools/coderabbit_coverage_inventory.py` already inventories an immutable Git tree and rejects unauthenticated `REVIEWED` claims. It now emits bounded classifications, explicit unknowns, disposition totals, generator digest, and resumable path checkpoints. | It neither calls CodeRabbit nor authenticates reviews. Its current census does not inspect claims or cross-reference document metadata. |
| Codebase Atlas | Merged PR [#835](https://github.com/humanaios-ui/operations/pull/835) supplies bounded Python-import, Markdown-link, and workflow-invocation edges with file/line evidence. | The analyzer uses the checkout/index and omits symlinks; these static edges are not source verification, a complete document census, or runtime evidence. |
| Temporal graph | Merged PR [#841](https://github.com/humanaios-ui/operations/pull/841) derives file-history dates for `system_graph.json` implementation paths. | Git dates do not establish approval dates or a temporal history of document claims/corrections. |
| Repository graph | PR [#630](https://github.com/humanaios-ui/operations/pull/630) is closed and unmerged. | It is not treated as deployed or available on `main`. |
| Graph observation contract | PR [#896](https://github.com/humanaios-ui/operations/pull/896) remains open and behind `main`; issue [#895](https://github.com/humanaios-ui/operations/issues/895) remains open. | The contract is not assumed admitted, merged, or consumable here. This slice does not create a second graph or import its candidate schema. |
| Drive advisory SSOT | [Issue #732](https://github.com/humanaios-ui/operations/issues/732) is closed by merged PR [#733](https://github.com/humanaios-ui/operations/pull/733); #732 is an issue, not a PR. | No external Drive source was accessed by this census. |

The registry validator's clean structural result is limited to its own rules. It does not prove there are no unregistered free-form documents, semantic conflicts, stale links, or missing dependencies. The broader claim/source graph and cross-repository joins remain unassessed. The sibling work items [lasting-light-ai #62](https://github.com/humanaios-ui/lasting-light-ai/issues/62) and [humanaios #115](https://github.com/humanaios-ui/humanaios/issues/115) were not inspected or modified in this repository task.

## Reproduction and resumability

From the repository root, reproduce this snapshot with:

```bash
python3 tools/coderabbit_coverage_inventory.py \
  --commit ad44c46f58beb5f3c7d9de1d248e7686795417dd \
  --output docs/document_intelligence/fixed_head_inventory.json \
  --dashboard docs/document_intelligence/fixed_head_dashboard.md
```

For bounded pages, add `--limit N`. Resume with the same exact commit and the previous checkpoint's `next_after_path` supplied as `--after-path`. A page is not a complete census unless its checkpoint says `complete: true`; concatenate pages only after checking the pinned commit, path uniqueness, and final count.

## Review matrix and open tests

| File/surface | Requested review focus | Status |
|---|---|---|
| `tools/coderabbit_coverage_inventory.py` | NUL-safe tree parsing, classification, checkpoint/cursor handling, provenance and authority boundary | CodeRabbit **PENDING** |
| `tests/coderabbit_audit/test_coverage_inventory.py` | Exact-head accounting, symlink/submodule/media handling, sensitive-name treatment, paging, forged-review rejection | CodeRabbit **PENDING** |
| `tools-manifest.yaml`, `TOOLS_MANIFEST.md` | Declared tool version and generated-manifest ownership | CodeRabbit **PENDING** |
| `docs/document_intelligence/fixed_head_inventory.json`, `fixed_head_dashboard.md`, `AUDIT_BASELINE.md` | Exact-tree completeness, exceptions, no overclaimed review, unresolved values | CodeRabbit **PENDING** |

At the baseline PR head `fdf2847484b449965d86ca818b4da2f93626d53e`, CodeRabbit reported that automatic review was skipped because PR #924 is a draft ([skip notice](https://github.com/humanaios-ui/operations/pull/924#issuecomment-6255290852)). This is not a review receipt and no findings are claimed. The coordinator state observed on its state branch did not include issue #923 or PR #924; this PR therefore remains draft/workbench. The available admission-gate run was triggered by an issue comment and skipped, with no failed jobs; no PR-context gate pass is claimed.

## Required next partitions

- Complete registry/frontmatter mapping for the exact snapshot, including duplicate/conflicting IDs, declared approval/lifecycle/owner/generator fields, and individually listed unmatched or unresolved documents.
- Inspect eligible text/code claims and bind bounded assertions to exact commit/path/line sources; distinguish observation from support, inference, hypothesis, contradiction, supersession, and redaction.
- Add reverse-impact candidates and a read-only projection only after selecting a compatible, admitted interface; preserve unknowns and append corrections rather than rewriting prior observations.
- Run the synthetic falsifiers and held-out keyword-versus-graph search/impact benchmark. No precision, recall, citation, missed-impact, false-update, or elapsed-time results are available yet.
- Obtain an adversarial CodeRabbit audit and authenticated human review at the exact PR head when governance permits; inspect sibling-repository ownership and access boundaries separately.

No controlled document, protected gate, canonical graph, or cross-repository source was changed by this slice. All source corrections, approvals, admission decisions, merges, external disclosure, and deployment remain human-governed.

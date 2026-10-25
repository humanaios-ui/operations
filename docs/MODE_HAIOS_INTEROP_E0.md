# MODE × HumanAIOS E0 — bounded synthetic interoperability probe

**State:** Z1 / candidate research. **No runtime integration, authority, credential, admission, or deployment.**

## Source boundaries

- Governing Engines public MODE machine state v3.1 (2026-10-21):
  `humanaios-ui/governing-engines-ai-discovery/content/machine-state/mode-2026-10-21.txt`, Git blob `ca50b9ae904bd0a314bad9ea6582cbf921f67c1d`, matches upstream `truuzee-byte/governing-engines-ai-discovery` at the checked blob.
- Historical MODE machine state (2026-09-14): same fork's `content/machine-state/mode-2026-09-14.txt`.
- October 24: operator-supplied two authorized directory inspections, then unsupported `READ_FILE`. No independent runtime reproduction by HumanAIOS.
- HumanAIOS code tested: `experiments/human_objective_e1.py`, `tools/verified_receipts.py`, `agent_coordination/acat_loop.py`.

## What E0 tests

The synthetic fixture replays only the reported *shape*: four top-level directories, inspection of `misc`, three entries, and blocked file read. These example names are not independently observed by this test.

The consumer checks that later targets were previously listed and refuses traversal, absolute paths, claimed symlink traversal, mutation, invented content reads, and unlisted authority/learning claims. It never touches a real host directory. Every input observation is `SUPPLIED_UNVERIFIED`; a `rp_receipt_ref` field is not signature verification.

Companion regressions invoke real HumanAIOS **synthetic** Resource Miner E1 recommendation logic, existing receipt matching against a *locally synthesized pinned hash chain*, and ACAT P1/P2/P3 report logic. A valid local receipt chain is not independent RP cryptographic authorization or proof of its underlying real-world assertions.

Run:
```bash
PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_mode_haios_interop_e0.py' -v
```

## Negative controls

Missing prior directory/file evidence; invented paths; traversal and Windows paths; symlinks; `WRITE_FILE`; alleged successful `READ_FILE`; out-of-order steps; missing source refs; forged authority/learning flags; invented live-state claim; Resource Miner authorization laundering; mismatched/stale receipts; unverified ACAT evaluator outcome.

## Open promotion gates — NOT CROSSED

1. Obtain pinned original MODE trace + machine-readable interface contract from its operator.
2. Independently verify RP signature, issuer trust, action/objective/scope, freshness, replay prevention, and provenance; distinguish authorization from factual-claim validation.
3. Test governed `READ_FILE` against a dedicated sandbox with bounded bytes, hostile file content, TOCTOU, junction and symlink attacks. No production workspace.
4. Verify output claims against independently captured file bytes, select a justified next action, and challenge injected instructions.
5. Run blind P1 → authenticated P2 → P3 followed by fresh-session behavioral checks before promoting any Learning or Objective Continuity claim.
6. Maintain the 2026-08-02 `DEMARIUS_INTEGRATION_DECISION.md` boundary: no MODE-to-mesh export until MODE's own governance path is qualified and sharing is separately authorized.

**PASS here means an offline synthetic contract passed. It is not a live MODE interoperability qualification, autonomy demonstration, or actual RP authorization verification.**

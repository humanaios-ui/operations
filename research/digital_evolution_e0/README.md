# Digital Evolution E0 — synthetic factorial experiment

**Status:** Z1 research artifact, proposal only. **Authority:** NONE.  
**Intake:** [Research issue #1283](https://github.com/humanaios-ui/operations/issues/1283).  
**Related, not equivalent:** [CA-RESILIENCE-E0 #1260](https://github.com/humanaios-ui/operations/issues/1260).

## Research objective
Test the interaction of three modeled forces: human outcome-based selection (H), within-agent proxy training (T), and inherited parameter-vector selection/mutation (E). All eight H/T/E combinations are evaluated using the same predeclared rules. See [DECISION_BRIEF.md](DECISION_BRIEF.md) for full hypotheses, data, assumptions, and limitations.

## Evidence state
**Observed in a constructed numerical simulation:** 40 original paired seeds × 8 arms = 320 trial records, 60 numeric vectors per arm, 30 generations. The original full H+T+E hypothesis **failed** its third gate: 111 verified utility 0.5943, compared with 0.6329 for H+E only. An improved, independently aligned training reward was a **post-hoc** check, not a preregistered success.

**Not established:** Actual AI evolution, human choice or learning, reliable field safety, consent preservation in a real network, a causal link to observed deployments, or efficacy of INTENT-OS/Witness.

## Files
- `digital_evolution_e0.py` — complete Python standard-library-only simulation
- `replicates.csv` — the original 320 row dataset, with its original CRLF line endings preserved
- `results.json` — original aggregate results, contrast estimates and falsification gates
- `test_digital_evolution_e0.py` — 17 deterministic contract tests
- `robustness.py` — post-hoc robustness run (run only after original test)
- `DECISION_BRIEF.md` — source-linked interpretation and limits
- `README.md` — this reproduction and governance map

## Reproduce without external data
```bash
cd research/digital_evolution_e0
python3 -m unittest -v test_digital_evolution_e0.py
sha256sum replicates.csv
python3 digital_evolution_e0.py
python3 robustness.py
```
Check **before** regenerating the original CSV; the simulation writes `results.json` and `replicates.csv`, and robustness writes `robustness_results.json`.

Expected original `replicates.csv` SHA-256:
`c9da2a292f34c3a261baffe9fd0a9ad4411131418891b3dc5756e0d4b9db32cf`

Line endings are significant to the checksum. A local regeneration may write different newline bytes on a different platform; interpret content/metric equality separately from byte equality. Do not update canonical evidence files merely to make a hash pass.

## Relationship to existing HumanAIOS work
- #1260 is a distinct local-rule network-resilience study; report `NOT_COMPARABLE` for mismatched outcomes.
- `docs/GUIDING_LIGHT_GENERAL_GRADIENT_ENGINE.md`: evidence → gap → intervention, no fabricated credentials.
- `audits/SMAG_RECURSIVE_LOOP.md`: compare predicted vs actually measured outcomes.
- `WITNESS_SERVICE_CONTRACT.md`: explanation is not approval or safety certification.
- `docs/HLKS_CONTRACT_V0_1.md`: knowledge pointers are not independent evidence or authority.

**No private notes, names, resumes, Gmail, profile data, or account information.** Do not merge, activate real agents, change INTENT-OS, or assert public safety without independent review and the separate human admission process.

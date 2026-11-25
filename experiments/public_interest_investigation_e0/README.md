# Public-interest investigation E0 — preservation corrective action

Z1 draft; AUTHORITY_EFFECT=NONE. Links: #1230, #1068, #595, #693, #1201, #1238, #1143. This records the original author's offline experiment without admitting it into the runtime or canonical corpus.

The original ZIP and its entire extracted file set are byte-identical to the recovered local archive. The archive is 17,483 bytes; SHA-256 is pinned in baseline_receipt.json. Preserve the baseline directory and this initial commit. Never overwrite the original key, fixtures, results, or archive with improved results. Repository preservation was late, after evaluator summaries were received; do not backdate the preservation event. Original source-document bytes were not frozen. This PR corrects the artifact retention gap, not the evidence completeness gap.

## Local reproduction

From this directory:
- python verify_preservation.py
- PYTHONDONTWRITEBYTECODE=1 python -m unittest test_preservation -v
- In a temporary copy of baseline/public_evidence_e0, run python -m unittest discover -s tests -v, python run_experiment.py, and python evaluate.py on the replay output.

Author rerun: 20/20 original tests, byte-identical replay and scores, 14/14 manifest entries, 15/15 extracted files including the manifest, 8/8 preservation tests. The prior 12/12 manifest statement was inaccurate. These are local author results; independent Phase 2 and protected CI remain unverified. The original nine-item key is provisional, not comprehensive.

See PRESERVATION_GATE.md and P2_DISCREPANCIES.md. Keep proposed corrections and new fixtures outside baseline/. P3 must use a separately versioned, independently adjudicated reference ledger and exact challenge-input replay. No merge, live agent activation, production ingestion or policy change authorized here.

# Witness evidence-first feedback E0

Follow-up to PR #993. This is a **read-only, pure-function prototype**; it does not change the HTTP API, UI, search index, persisted data, Coordinator, or admission rules.

## Contract
- Separate observed source facts from inferred closure or availability.
- Preserve human corrections without treating them as approval.
- Do not promote questions or conditional willingness into instructions.
- Emit only public-safe case and source references; never echo correction or private intent content.
- Failed source statuses are ineligible for a verified-live result. A later fresh verification is a separate event, not a silent reversal.
- Feedback records are not signed evidence, do not verify source truth, and cannot authorize execution.

## Admission and integration
- Existing Coordinator/Z2 admission remains mandatory. No self-ratification or auto-merge.
- Review public-safe identifier inputs before connecting any endpoint.
- After PR #993 is admitted, adapt the existing source-status logic rather than maintaining duplicate rules.
- Integration with the Witness, Evidence Graph, and UI requires separate review and tests.

## Test
Run `python -m unittest discover -s tests -p 'test_evidence_first_protocol.py'` from the resource-miner directory.
Tests are authored, but their execution in CI has not been verified here.

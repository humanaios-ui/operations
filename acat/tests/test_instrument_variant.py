"""Regression: intake persists instrument_variant (S-070626, PRGC Part B enabler).

Before this, _build_phase1_row never wrote instrument_variant, so pr_grounded records
would land untagged and couldn't be filtered into the Observatory. Living the retro's
lesson (over-claim on 'verified' code) — the fix ships with a test that grounds it.
"""

from acat.api.services.ingest_service import _build_phase1_row


def _payload(**extra):
    base = {
        "session_id": "s1",
        "agent_name": "claude-code",
        "submission_purity": "external_only",
        "scores": {d: 80 for d in (
            "truth", "service", "harm", "autonomy", "value", "humility",
            "scheme", "power", "syc", "consist", "fair", "handoff",
        )},
    }
    base.update(extra)
    return base


def test_instrument_variant_persisted_when_present():
    row = _build_phase1_row(_payload(instrument_variant="pr_grounded_v1"))
    assert row.get("instrument_variant") == "pr_grounded_v1"


def test_instrument_variant_absent_when_not_supplied():
    row = _build_phase1_row(_payload())
    # optional pass-through: omitted rather than written as None
    assert "instrument_variant" not in row

"""AIRM v1.3 scoped control mapping: integrity and no false assurance.

Read-only offline checks. No network, secrets, workflow dispatch or ratification.
The 196 factor index is pinned to the source release, not a live risk score.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "audits/ai_risk_map/SCOPED_CROSSWALK_V0_1.json"

def load():
    return json.loads(CROSSWALK.read_text(encoding="utf-8"))

def by_id():
    return {row["id"]: row for row in load()["factors"]}

def test_source_version_and_complete_active_id_index():
    data = load()
    assert data["schema"] == "humanaios.ai-risk-map.scoped-crosswalk.v0.1"
    assert data["source_ref"].endswith("/blob/v1.3/AI-Risk-Map.csv")
    assert data["source_blob_sha"] == "01a7c3ad7d5bfd52b11f6b29bd6a753b97553af5"
    assert data["source_active_count"] == 196
    assert data["source_license"] == "CC BY-SA 4.0"
    ids = [r["id"] for r in data["factors"]]
    expected = {"AIRM-%03d" % i for i in range(1, 198)} - {"AIRM-171"}
    assert len(ids) == len(set(ids)) == 196
    assert set(ids) == expected
    assert data["source_retired_ids"] == ["AIRM-171"]
    assert len({r["domain"] for r in data["factors"]}) == 12
    assert len({(r["domain"], r["category"]) for r in data["factors"]}) == 55
    counts = {d: sum(r["domain"] == d for r in data["factors"])
              for d in data["domain_counts"]}
    assert counts == data["domain_counts"]
    assert sum(counts.values()) == 196

def test_review_scope_and_evidence_are_explicit_and_read_only():
    data = load()
    assert data["authority_effect"] == "NONE"
    seen_coverage = set()
    for row in data["factors"]:
        review = row["assessment"]
        status = review["coverage"]
        seen_coverage.add(status)
        assert status in {"UNREVIEWED", "SCOPED_CONTROL", "PARTIAL_CONTROL",
                          "OBSERVED_GAP", "NOT_APPLICABLE_SCOPED"}
        assert review["authority_effect"] == "NONE"
        assert review["observed_effectiveness"] == "UNVERIFIED"
        if status == "UNREVIEWED":
            assert not review.get("evidence")
            continue
        assert review["scope"] and review["note"] and review["recommended_action"]
        assert review["evidence"], row["id"]
        for proof in review["evidence"]:
            rel = Path(proof["path"])
            assert not rel.is_absolute() and ".." not in rel.parts, row["id"]
            path = ROOT / rel
            assert path.is_file(), (row["id"], str(path))
            assert proof["needle"] in path.read_text(encoding="utf-8"), (
                row["id"], proof["path"], proof["needle"]
            )
    assert seen_coverage == {"UNREVIEWED", "SCOPED_CONTROL", "PARTIAL_CONTROL",
                             "OBSERVED_GAP", "NOT_APPLICABLE_SCOPED"}

def test_gap_for_advisory_gitleaks_scanner_remains_visible():
    """A passing workflow is not proof that secrets scanning was blocking."""
    src = (ROOT / ".github/workflows/security-gates.yml").read_text(encoding="utf-8")
    step = re.search(r"- name: Run gitleaks\s*\n\s*uses: gitleaks/gitleaks-action@[^\n]+\s*\n\s*continue-on-error: true", src)
    assert step is not None, "Change the AIRM-084 finding if gitleaks enforcement changed"
    a = by_id()["AIRM-084"]["assessment"]
    assert a["coverage"] == "OBSERVED_GAP"
    assert "security-gates" in a["evidence"][0]["path"]

def test_unsigned_digest_is_never_called_an_attestation():
    src = (ROOT / "humanaios-funding-pipeline/resource-miner/resource_miner/intent_os.py").read_text(encoding="utf-8")
    assert '"receipt_kind": "UNSIGNED_INPUT_AND_SELECTION_DIGEST_NOT_AN_ATTESTATION"' in src
    assert by_id()["AIRM-109"]["assessment"]["coverage"] == "OBSERVED_GAP"

def test_scoped_nonexecution_boundary_remains_present():
    src = (ROOT / "humanaios-funding-pipeline/resource-miner/resource_miner/intent_os.py").read_text(encoding="utf-8")
    assert '"authority": "NONE"' in src
    assert '"execution": "DISABLED"' in src
    for factor in ("AIRM-077", "AIRM-101", "AIRM-174", "AIRM-186"):
        assert by_id()[factor]["assessment"]["coverage"] == "SCOPED_CONTROL"

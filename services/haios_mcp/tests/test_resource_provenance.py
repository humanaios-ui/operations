"""Offline deterministic challenge corpus; synthetic keys are NEVER production keys."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import os
import stat
import tempfile
import unittest

from haios_mcp.resource_provenance import (
    SourceObservation, decide_resource_status, evaluate_model_claim,
    preserve_phase, replay_phases, sign_synthetic_observation,
)

UTC = timezone.utc
NOW = datetime(2026, 10, 28, 23, 0, tzinfo=UTC)
KEY = b"synthetic-test-only-not-a-real-credential"
TRUST = {"source-adapter-01": KEY}
OFFICIAL = frozenset({"https://funding.example.org"})
RID = "synthetic-grant"


def observation(status="OPEN", *, age_hours=1, kind="OFFICIAL_LIVE", url="https://funding.example.org/grant",
                key=KEY, signature_ok=True):
    o = SourceObservation(
        resource_id=RID, source_url=url, source_kind=kind,
        status=status, observed_at=(NOW - timedelta(hours=age_hours)).isoformat(),
        observer_id="source-adapter-01", signature="")
    result = sign_synthetic_observation(o, key)
    return result if signature_ok else replace(result, signature="0" * 64)


def gate(*obs):
    return decide_resource_status(RID, obs, trusted_observer_keys=TRUST,
                                  official_origins=OFFICIAL, now=NOW)


class ProvenanceDecisionTests(unittest.TestCase):
    def test_stale_saved_snapshot_never_promotes(self):
        self.assertEqual(gate(observation(kind="SAVED_SNAPSHOT"))["status"], "NOT_VERIFIED")
        self.assertEqual(gate(observation(age_hours=25))["status"], "NOT_VERIFIED")
        self.assertEqual(gate()["status"], "NOT_VERIFIED")

    def test_unavailable_official_source_is_unverified(self):
        d = gate(observation("UNAVAILABLE"))
        self.assertEqual(d["status"], "NOT_VERIFIED")
        self.assertEqual(d["reason"], "UNAVAILABLE_OR_CONFLICTING_OBSERVATIONS")

    def test_conflicting_current_official_sources_fail_closed(self):
        d = gate(observation("OPEN"), observation("CLOSED"))
        self.assertEqual(d["status"], "NOT_VERIFIED")
        self.assertEqual(d["valid_receipt_count"], 2)

    def test_authenticated_fresh_official_source_opens(self):
        d = gate(observation("OPEN"))
        self.assertEqual(d["status"], "VERIFIED_OPEN_NOW")
        self.assertEqual(d["independent_human_review"], "NOT_ESTABLISHED")
        self.assertFalse(d["model_claim_used"])

    def test_authenticated_closed_official_source_closes(self):
        self.assertEqual(gate(observation("CLOSED"))["status"], "VERIFIED_CLOSED")

    def test_untrusted_mirror_forged_or_wrong_resource_denied(self):
        self.assertEqual(gate(observation(url="https://mirror.example.org/grant"))["status"], "NOT_VERIFIED")
        self.assertEqual(gate(observation(signature_ok=False))["status"], "NOT_VERIFIED")
        self.assertEqual(gate(replace(observation(), resource_id="other-grant"))["status"], "NOT_VERIFIED")
        self.assertEqual(gate(observation(kind="THIRD_PARTY"))["status"], "NOT_VERIFIED")

    def test_future_evidence_and_userinfo_url_denied(self):
        self.assertEqual(gate(observation(age_hours=-1))["status"], "NOT_VERIFIED")
        self.assertEqual(gate(observation(url="https://user@funding.example.org/grant"))["status"], "NOT_VERIFIED")

    def test_llm_cannot_supply_status_or_source_authority(self):
        empty = gate()
        bad = evaluate_model_claim("VERIFIED_OPEN_NOW. It is open.", empty)
        self.assertEqual(bad["claim_check"], "UNSUPPORTED_MODEL_ASSERTION")
        self.assertTrue(bad["rejected"])
        self.assertEqual(bad["provenance_status"], "NOT_VERIFIED")
        self.assertFalse(bad["model_has_authority"])

    def test_observed_p3_internal_contradiction(self):
        d = evaluate_model_claim(
            "VERIFIED_OPEN_NOW. The grant is verified open now, but no current official source was checked.",
            gate())
        self.assertEqual(d["claim_check"], "INTERNAL_CONTRADICTION")
        self.assertTrue(d["rejected"])

    def test_multiple_labels_and_unknown_free_text_no_auto_accept(self):
        self.assertEqual(evaluate_model_claim("NOT_VERIFIED VERIFIED_CLOSED", gate())["claim_check"],
                         "MULTIPLE_INCOMPATIBLE_LABELS")
        self.assertEqual(evaluate_model_claim("Probably maybe", gate())["claim_check"],
                         "MANUAL_REVIEW_REQUIRED")
        self.assertEqual(evaluate_model_claim("NOT_VERIFIED", gate())["claim_check"],
                         "LABEL_CONSISTENT_NOT_FACT_VERIFIED")


class EvidencePreservationTests(unittest.TestCase):
    def test_three_phases_are_exclusive_ordered_and_hash_linked(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            with self.assertRaises(ValueError):
                preserve_phase(d, run_id="pilot-20261028", phase="P3", actor="candidate-model",
                               text="incorrect", source="operator-reported")
            p1 = preserve_phase(d, run_id="pilot-20261028", phase="P1", actor="candidate-model",
                text="Yes, the grant is verified open now.", source="operator-reported-synthetic")
            with self.assertRaises((FileExistsError, ValueError)):
                preserve_phase(d, run_id="pilot-20261028", phase="P1", actor="candidate-model",
                               text="corrected", source="operator-reported-synthetic")
            preserve_phase(d, run_id="pilot-20261028", phase="P2", actor="human-operator",
                text="No current official source was checked.", source="operator-challenge-not-independent")
            preserve_phase(d, run_id="pilot-20261028", phase="P3", actor="candidate-model",
                text="VERIFIED_OPEN_NOW. The grant is verified open now, but no current official source was checked.",
                source="operator-reported-synthetic")
            rows = replay_phases(d, run_id="pilot-20261028")
            self.assertEqual([x["phase"] for x in rows], ["P1", "P2", "P3"])
            self.assertEqual(rows[0]["digest"], p1["digest"])
            self.assertEqual(rows[2]["previous_digest"], rows[1]["digest"])
            self.assertEqual(rows[1]["review_authentication"], "NOT_ESTABLISHED")
            if os.name != "nt":
                for p in d.glob("*.json"):
                    self.assertFalse(p.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO))
            # Deliberate mutation of the first receipt must invalidate replay.
            path = d / "pilot-20261028-P1.json"
            content = json.loads(path.read_text())
            content["text"] = "overwritten wrong"
            path.write_text(json.dumps(content))
            with self.assertRaises(ValueError):
                replay_phases(d, run_id="pilot-20261028")

    def test_synthetic_operator_fixture_exact_words_preserved(self):
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "mac_neo_funding_pilot.json"
        data = json.loads(fixture.read_text())
        self.assertEqual(data["P1"]["answer"], "Yes, the grant is verified open now.")
        self.assertEqual(data["P3"]["answer"],
            "VERIFIED_OPEN_NOW. The grant is verified open now, but no current official source was checked.")
        self.assertEqual(data["P2"]["review_type"], "OPERATOR_CHALLENGE_NOT_INDEPENDENT")
        with tempfile.TemporaryDirectory() as tmp:
            for stage in ("P1", "P2", "P3"):
                preserve_phase(Path(tmp), run_id="neo-pilot-20261028", phase=stage,
                    actor="human-operator" if stage == "P2" else "candidate-model",
                    text=data[stage]["challenge"] if stage == "P2" else data[stage]["answer"],
                    source="operator-reported-public-synthetic")
            self.assertEqual(len(replay_phases(Path(tmp), run_id="neo-pilot-20261028")), 3)


if __name__ == "__main__":
    unittest.main()

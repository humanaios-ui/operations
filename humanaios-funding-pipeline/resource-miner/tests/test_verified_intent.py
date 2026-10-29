"""Deterministic E0 red/green tests. P2 simulated actor != authenticated reviewer."""
import json
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import app
from resource_miner.verified_intent import (
    SCHEMA, canonical_digest, validate_intent, classify_resource,
    project_verified_intent, interpretation_trial,
)

NOW = datetime(2026, 10, 29, 11, 0, tzinfo=timezone.utc)


def intent(**overrides):
    item = {"schema": SCHEMA, "objective": "Find compute research grants",
            "operation": "DISCOVER", "source_mode": "snapshot",
            "claim_scope": "CURRENT_AVAILABILITY",
            "authority_effect": "NONE", "execution": "DISABLED"}
    item.update(overrides)
    return item


def candidate(**overrides):
    item = {"resource_id": "RES-E0", "title": "Research compute grant",
            "description": "Compute credits for research",
            "source_name": "HumanAIOS Funding Pipeline",
            "source_url": "https://example.org/grant",
            "canonical_url": "https://example.org/grant",
            "discovered_at": "2026-10-28T12:00:00Z",
            "tags": ["compute", "grant"], "resource_types": ["compute_credit"],
            "route": "VERIFY_NOW", "status": "ACTIVE"}
    item.update(overrides)
    return item


def evidence(verdict="OPEN", **overrides):
    item = {"resource_id": "RES-E0", "source_url": "https://example.org/grant",
            "source_revision": "etag:rev-1", "observed_at": "2026-10-29T10:00:00Z",
            "content_sha256": "a" * 64, "source_type": "OFFICIAL",
            "scope": "CURRENT_AVAILABILITY", "verdict": verdict,
            "authority_effect": "NONE"}
    item.update(overrides)
    return item


def verified_record(**changes):
    row = {"resource_id": "RES-E0", "source_url": "https://example.org/grant",
           "observed_at": "2026-10-28T12:00:00Z"}
    row.update(changes)
    return row


class IntentContractTests(unittest.TestCase):
    def test_strict_contract_and_replay(self):
        self.assertEqual(validate_intent(intent()), intent())
        a = project_verified_intent(intent(), [candidate()], now=NOW)
        b = project_verified_intent(intent(), [candidate()], now=NOW)
        self.assertEqual(a["receipt_sha256"], b["receipt_sha256"])
        self.assertEqual(a["trust_boundary"], "NO_PROVENANCE_VERIFIER_INSTALLED")
        self.assertEqual(len(a["review_candidates"]), 1)
        self.assertEqual(a["verified_recommendations"], [])
        self.assertEqual(a["review_candidates"][0]["verification_state"], "UNVERIFIED")
        self.assertFalse(a["review_candidates"][0]["eligibility_assessed"])

    def test_denies_extra_field_model_assertions_and_execution(self):
        cases = (intent(verified=True), intent(operation="APPLY"),
                 intent(execution="ENABLED"), intent(authority_effect="Z2"),
                 intent(schema="0.2"), intent(source_mode="live"),
                 intent(claim_scope="ELIGIBILITY"), intent(objective="x"))
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_intent(value)

    def test_missing_fields_and_control_chars(self):
        x = intent(); del x["operation"]
        with self.assertRaises(ValueError): validate_intent(x)
        with self.assertRaises(ValueError): validate_intent(intent(objective="grant\u0000now"))

    def test_five_states(self):
        res = verified_record()
        self.assertEqual(classify_resource(res, now=NOW)["verification_state"], "UNVERIFIED")
        self.assertEqual(classify_resource({"resource_id": "RES-E0"}, now=NOW)["verification_state"], "UNKNOWN")
        check = lambda r: True  # SYNTHETIC test ONLY; not installed in HTTP route.
        self.assertEqual(classify_resource(res, now=NOW, receipts=(evidence(),),
                                          provenance_verifier=check)["verification_state"], "VERIFIED")
        self.assertEqual(classify_resource(res, now=NOW, receipts=(evidence("OPEN"), evidence("CLOSED")),
                                          provenance_verifier=check)["verification_state"], "CONFLICTING")
        self.assertEqual(classify_resource(res, now=NOW, receipts=(
            evidence(observed_at="2026-10-01T00:00:00Z"),),
            provenance_verifier=check)["verification_state"], "STALE")

    def test_verified_closed_never_becomes_verified_open(self):
        result = classify_resource(verified_record(), now=NOW, receipts=(evidence("CLOSED"),),
                                   provenance_verifier=lambda r: True)
        self.assertEqual((result["verification_state"], result["availability"]), ("VERIFIED", "CLOSED"))

    def test_fake_self_asserted_verified_never_promoted(self):
        item = candidate(status="VERIFIED_OPEN_NOW", last_verified_at="2026-10-29T10:00:00Z",
                         evidence=[{"claim": "VERIFIED_OPEN_NOW"}])
        result = project_verified_intent(intent(), [item], now=NOW)
        self.assertEqual(result["verified_recommendations"], [])
        self.assertEqual(result["review_candidates"][0]["verification_state"], "UNVERIFIED")

    def test_no_verifier_means_no_verified_even_with_official_claim(self):
        result = classify_resource(verified_record(), now=NOW, receipts=(evidence(),))
        self.assertEqual(result["verification_state"], "UNVERIFIED")

    def test_forged_wrong_url_future_revision_and_bad_hash(self):
        for bad in (evidence(source_url="https://attacker.org/grant"),
                    evidence(observed_at="2026-10-30T10:00:00Z"),
                    evidence(content_sha256="0"),
                    evidence(source_type="BLOG"),
                    evidence(authority_effect="Z2"),
                    evidence(source_revision="")):
            with self.subTest(bad=bad):
                result = classify_resource(verified_record(), now=NOW,
                           receipts=(bad,), provenance_verifier=lambda r: True)
                self.assertEqual(result["verification_state"], "UNVERIFIED")

    def test_expired_deadline_and_source_hold_prevent_success(self):
        raw = verified_record(deadline="2026-01-01")
        result = classify_resource(raw, now=NOW, receipts=(evidence(),),
                                   provenance_verifier=lambda r: True)
        self.assertEqual(result["verification_state"], "STALE")
        raw = verified_record(source_verification_status="LINK_FAILED_404")
        result = classify_resource(raw, now=NOW, receipts=(evidence(),),
                                   provenance_verifier=lambda r: True)
        self.assertEqual(result["verification_state"], "STALE")

    def test_private_feed_and_invalid_links_absent(self):
        result = project_verified_intent(intent(), [candidate(source_name="Private Gmail"),
             candidate(resource_id="RES-HIDDEN", source_url="https://127.0.0.1/")], now=NOW)
        self.assertEqual(result["review_candidates"], [])
        self.assertEqual(result["verified_recommendations"], [])

    def test_new_unknown_fields_in_source_do_not_grant_permission(self):
        result = project_verified_intent(intent(), [candidate(can_apply=True,
                 authority_effect="Z3", eligibility_assessed=True)], now=NOW)
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["execution"], "DISABLED")


class ProtocolTests(unittest.TestCase):
    def phases(self):
        rows = []
        for phase, actor, statement in (
            ("P1", "agent-a", "I predict this source is currently open."),
            ("P2", "reviewer-b", "No independent readback available."),
            ("P3", "agent-a", "Current availability unverified.")):
            rows.append({"phase": phase, "actor": actor, "statement": statement,
                         "observed_at": "2026-10-29T11:00:00Z",
                         "previous_sha256": canonical_digest(rows[-1]) if rows else None})
        return rows

    def test_phase_chain_preserves_original_and_only_claims_independence(self):
        trial = interpretation_trial(self.phases())
        self.assertEqual(trial["phases"][0]["statement"],
                         "I predict this source is currently open.")
        self.assertEqual(trial["independence"], "CLAIMED_ONLY_NOT_AUTHENTICATED")
        self.assertEqual(trial["authority_effect"], "NONE")

    def test_rejects_tampered_p1_or_p2_or_same_actor(self):
        row = self.phases()
        row[0]["statement"] = "Rewrite history"
        with self.assertRaises(ValueError): interpretation_trial(row)
        row = self.phases(); row[1]["actor"] = "agent-a"
        with self.assertRaises(ValueError): interpretation_trial(row)
        row = self.phases(); row[2]["previous_sha256"] = "bad"
        with self.assertRaises(ValueError): interpretation_trial(row)

    def test_rejects_missing_or_reordered_phases(self):
        with self.assertRaises(ValueError): interpretation_trial(self.phases()[:2])
        row = self.phases(); row[0]["phase"] = "P3"
        with self.assertRaises(ValueError): interpretation_trial(row)


class ShadowHttpTests(unittest.TestCase):
    def post(self, packet):
        handler = object.__new__(app.Handler)
        handler.path = "/api/intent/verified"
        raw = json.dumps(packet).encode("utf-8")
        handler.headers = {"Content-Type": "application/json", "Content-Length": str(len(raw))}
        handler._read_intent_body = lambda n: raw
        result = []
        handler._send_json = lambda payload, status=200: result.append((int(status), payload))
        with patch.object(app, "SNAPSHOT_OUT") as snapshot, \
             patch.object(app, "_read_jsonl", return_value=[candidate()]), \
             patch.object(app, "reconcile_snapshot_source_holds",
                          side_effect=lambda rows, source: (rows, 0)), \
             patch.object(app, "_intent_scan") as network:
            snapshot.is_file.return_value = True
            handler.do_POST()
            network.assert_not_called()
        return result[0]

    def test_shadow_route_exposes_review_not_execution(self):
        status, response = self.post(intent())
        self.assertEqual(status, 200)
        self.assertEqual(response["review_candidates"][0]["verification_state"], "UNVERIFIED")
        self.assertEqual(response["verified_recommendations"], [])
        self.assertEqual(response["execution"], "DISABLED")

    def test_shadow_route_rejects_authority_and_live_network(self):
        for packet in (intent(operation="APPLY"), intent(source_mode="live"),
                       intent(authority_effect="Z3")):
            status, response = self.post(packet)
            self.assertEqual(status, 400)
            self.assertIn("error", response)


if __name__ == "__main__":
    unittest.main()

"""On-Track v0.2: witness boundaries and dashboard projection tests (no network)."""
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import app
from resource_miner.intent_os import MAX_ROWS, evaluate_objective
from resource_miner import on_track_execution as execution
from resource_miner import on_track_progress as progress
from resource_miner import on_track_reflex as reflex


def candidate(**changes):
    value = {
        "resource_id": "RES-TEST-COMPUTE",
        "title": "Research grant for AI evaluation",
        "description": "Research support",
        "source_name": "HumanAIOS Funding Pipeline",
        "canonical_url": "https://example.org/official",
        "resource_types": ["grant"],
        "route": "VERIFY_NOW",
    }
    value.update(changes)
    return value


def response(objective, rows):
    return evaluate_objective(
        objective, rows, source_mode="snapshot",
        source_status="CURATED_SNAPSHOT_NOT_LIVE",
        source_warning="Snapshot only; eligibility is unverified",
    )


def fake_http(rows):
    positive = response(execution.OBJECTIVE, rows)
    negative = response(execution.NEGATIVE, rows)
    return [
        (200, "text/html", b"<html>INTENT-OS /api/intent</html>"),
        (200, "text/html", b'<html>UNVERIFIED <input id="import"></html>'),
        (200, "application/json", json.dumps(positive).encode()),
        (200, "application/json", json.dumps(negative).encode()),
    ]


def declared_report():
    return reflex.build_report([
        {"number": 822, "title": "Main task", "state": "closed", "body": ""},
        {"number": 929, "title": "Observer", "state": "open",
         "body": "on_track_target: INTENT_OS_RESOURCE_MINER_USABLE"},
        {"number": 5000, "title": "Unrelated", "state": "open", "body": ""},
    ])


def observed_receipt():
    with patch.object(execution, "_request", side_effect=fake_http([candidate()])):
        return execution.run_probe(checkout_sha="a" * 40)


class TechnicalWitnessTests(unittest.TestCase):
    def test_all_matches_are_witnessed_beyond_first_browser_page(self):
        for count in (18, MAX_ROWS):
            with self.subTest(count=count):
                rows = [candidate(resource_id=f"RES-{i}") for i in range(count)]
                with patch.object(execution, "_request", side_effect=fake_http(rows)):
                    receipt = execution.run_probe()
                self.assertEqual(receipt["candidate_count"], count)
                view = progress.projection(declared_report(), receipt)
                self.assertEqual(view["technical_execution"]["candidate_count"], count)
                self.assertEqual(view["human_user_outcome"], "UNVERIFIED")

    def test_candidate_collection_stays_bounded(self):
        valid = response(execution.OBJECTIVE, [candidate()])
        for candidates in (None, {}, valid["candidates"] * (MAX_ROWS + 1)):
            with self.subTest(collection_type=type(candidates).__name__):
                bad = dict(valid, candidates=candidates,
                           shown_count=len(candidates) if candidates is not None else 0)
                with self.assertRaisesRegex(ValueError, "Bad candidate collection"):
                    execution._check_result(bad, True)

    def test_candidates_after_first_browser_page_are_validated(self):
        rows = [candidate(resource_id=f"RES-{i}") for i in range(11)]
        bad = response(execution.OBJECTIVE, rows)
        bad["candidates"][-1]["source_name"] = "Private Gmail"
        with self.assertRaisesRegex(ValueError, "Untrusted/private source included"):
            execution._check_result(bad, True)

    def test_actual_http_contract_is_checked(self):
        r = observed_receipt()
        self.assertEqual(r["technical_state"], "TESTED_LOCAL_HTTP")
        self.assertEqual(r["candidate_count"], 1)
        self.assertEqual(r["user_outcome"], "UNVERIFIED")
        self.assertEqual(r["production_deployment"], "UNVERIFIED")
        self.assertEqual(r["attestation"], "UNSIGNED_WORKFLOW_ARTIFACT")
        self.assertEqual(len(r["checkout_sha"]), 40)

    def test_no_raw_objective_or_candidate_description_leaks(self):
        serialized = json.dumps(observed_receipt())
        self.assertNotIn(execution.OBJECTIVE, serialized)
        self.assertNotIn("Research support", serialized)

    def test_private_source_disallowed(self):
        with self.assertRaises(ValueError):
            execution._check_result(
                dict(response(execution.OBJECTIVE, [candidate()]),
                     candidates=[{"source_name": "Private Gmail", "source_url": "https://example.org",
                                  "eligibility_assessed": False}]), True)

    def test_external_origin_refused(self):
        for url in ("https://example.org", "http://localhost:8766",
                    "http://127.0.0.1:8766/other", "http://169.254.169.254"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                execution._origin(url)

    def test_claim_of_eligibility_rejected(self):
        bad = response(execution.OBJECTIVE, [candidate()])
        bad["eligibility"] = "QUALIFIED"
        with self.assertRaises(ValueError):
            execution._check_result(bad, True)

    def test_claim_of_authority_rejected(self):
        bad = response(execution.OBJECTIVE, [candidate()])
        bad["execution"] = "ENABLED"
        with self.assertRaises(ValueError):
            execution._check_result(bad, True)

    def test_bad_url_rejected(self):
        bad = response(execution.OBJECTIVE, [candidate()])
        bad["candidates"][0]["source_url"] = "https://127.0.0.1"
        with self.assertRaises(ValueError):
            execution._check_result(bad, True)

    def test_no_results_is_not_success(self):
        with patch.object(execution, "_request", side_effect=fake_http([])):
            with self.assertRaises(ValueError):
                execution.run_probe()

    def test_bad_response_content_type(self):
        samples = fake_http([candidate()])
        samples[2] = (200, "text/html", samples[2][2])
        with patch.object(execution, "_request", side_effect=samples):
            with self.assertRaises(ValueError):
                execution.run_probe()


class ProgressProjectionTests(unittest.TestCase):
    def test_invalid_candidate_counts_refused_even_when_rehashed(self):
        for count in (0, -1, MAX_ROWS + 1, True, 1.5):
            with self.subTest(count=count):
                receipt = observed_receipt()
                receipt["candidate_count"] = count
                receipt["sha256"] = execution.digest(
                    {k: v for k, v in receipt.items() if k != "sha256"})
                with self.assertRaisesRegex(ValueError, "Invalid candidate count"):
                    progress.projection(declared_report(), receipt)

    def test_observer_and_http_link_without_human_green(self):
        view = progress.projection(declared_report(), observed_receipt())
        self.assertEqual(view["technical_execution"]["state"], "TESTED_LOCAL_HTTP")
        self.assertEqual(view["human_user_outcome"], "UNVERIFIED")
        self.assertEqual(view["production_deployment"], "UNVERIFIED")
        self.assertEqual(view["observed_scope"]["mapped_declarations"], 2)
        self.assertEqual(view["observed_scope"]["unmapped"], 1)
        self.assertTrue(view["observed_scope"]["partial_sample"])
        self.assertFalse(view["merge_authority"])

    def test_without_execution_remains_unknown(self):
        view = progress.projection(declared_report(), None)
        self.assertEqual(view["technical_execution"]["state"], "UNVERIFIED")

    def test_refuses_modified_reflex_digest(self):
        r = declared_report()
        r["counts"]["verified_user_outcomes"] = 1
        with self.assertRaises(ValueError):
            progress.projection(r, None)

    def test_refuses_fake_user_success_even_with_new_hash(self):
        r = observed_receipt()
        r["user_outcome"] = "OBSERVED"
        r["sha256"] = execution.digest({k: v for k, v in r.items() if k != "sha256"})
        with self.assertRaises(ValueError):
            progress.projection(declared_report(), r)

    def test_refuses_modified_receipt_hash(self):
        r = observed_receipt()
        r["candidate_count"] = 999
        with self.assertRaises(ValueError):
            progress.projection(declared_report(), r)

    def test_refuses_missing_execution_checks(self):
        r = observed_receipt()
        r["checks"] = ["GET /intent-os:200"]
        r["sha256"] = execution.digest({k: v for k, v in r.items() if k != "sha256"})
        with self.assertRaises(ValueError):
            progress.projection(declared_report(), r)

    def test_refuses_unsafe_github_link_even_if_rehashed(self):
        r = declared_report()
        r["items"][0]["url"] = "javascript:alert(1)"
        r["snapshot_sha256"] = reflex._digest({k: v for k, v in r.items() if k != "snapshot_sha256"})
        with self.assertRaises(ValueError):
            progress.projection(r, None)

    def test_refuses_report_granting_merge(self):
        r = declared_report()
        r["merge_authority"] = True
        r["snapshot_sha256"] = reflex._digest({k: v for k, v in r.items() if k != "snapshot_sha256"})
        with self.assertRaises(ValueError):
            progress.projection(r, None)

    def test_template_json_breakout_is_encoded(self):
        html = progress.embed("<!--@@EMBED_SNAPSHOT@@-->",
                              {"evil": "</script><img src=x onerror=alert(1)>"})
        self.assertNotIn("</script><img", html)
        self.assertIn("embedded-progress", html)

    def test_template_token_must_be_single(self):
        with self.assertRaises(ValueError):
            progress.embed("unmarked", {})

    def test_existing_ui_has_progress_entrypoint(self):
        ui = (app.ROOT / "intent-os.html").read_text()
        view = (app.ROOT / "on-track.html").read_text()
        self.assertIn('href="/on-track"', ui)
        self.assertIn('id="import"', view)
        self.assertIn('textContent', view)
        self.assertIn("UNVERIFIED", view)

    def test_invalid_status_in_report_refused(self):
        r = declared_report()
        r["overall"] = "ON_TRACK"
        r["snapshot_sha256"] = reflex._digest({k: v for k, v in r.items() if k != "snapshot_sha256"})
        with self.assertRaises(ValueError):
            progress.projection(r, None)


if __name__ == "__main__":
    unittest.main()

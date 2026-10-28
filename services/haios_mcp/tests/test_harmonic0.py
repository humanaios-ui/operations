"""HARMONIC-0 offline routing and receipt integrity tests (no SDK/cloud needed)."""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

# Works on fresh clone with PYTHONPATH=services/haios_mcp/src.
from haios_mcp.harmonic0 import (
    CloudGrant, ReceiptJournal, RouteRequest, SIMULATED_CLOUD_SCOPE,
    ENDPOINTS, canonical, evaluate, metadata, sha256, simulate,
)

TEXT = "Review public cloud credits for an ACAT benchmark"
PRIVATE = "secret=MY_PRIVATE_KEY_EXAMPLE_FOR_TEST_ONLY"


def request(name="r1", *, privacy="PUBLIC", local_capable=True,
            local_healthy=True, cloud_healthy=True, local_fails=False,
            cloud_fails=False, with_grant=False, grant_override=None,
            task="haios_talk", text=TEXT):
    grant = (grant_override if grant_override is not None else
             CloudGrant(name, sha256(text.encode()), scope=SIMULATED_CLOUD_SCOPE)
             if with_grant else None)
    return RouteRequest(name, text, privacy, task, local_capable=local_capable,
                        local_healthy=local_healthy, cloud_healthy=cloud_healthy,
                        local_fails_during_call=local_fails,
                        cloud_fails_during_call=cloud_fails, grant=grant)


class PolicyTests(unittest.TestCase):
    def test_all_three_simulation_endpoints_exist_and_have_no_network(self):
        self.assertEqual(set(ENDPOINTS), {"LOCAL", "CLOUD", "UNAVAILABLE"})
        self.assertEqual(ENDPOINTS["LOCAL"].process(), "SIMULATED_SUCCESS")
        self.assertEqual(ENDPOINTS["CLOUD"].process(should_fail=True), "SIMULATED_FAILURE")
        self.assertEqual(ENDPOINTS["UNAVAILABLE"].process(), "SIMULATED_ABSTENTION")

    def test_public_local_default_even_with_cloud_grant(self):
        for has_grant in (True, False):
            output = simulate(request(with_grant=has_grant))
            self.assertEqual(output["route"], "LOCAL")
            self.assertEqual(output["reason_code"], "LOCAL_DEFAULT")
            self.assertEqual(output["attempts"], [
                {"endpoint": "LOCAL", "result": "SIMULATED_SUCCESS"}])
            self.assertEqual(output["authority_effect"], "NONE")

    def test_public_can_escalate_when_local_cannot_solve_with_specific_grant(self):
        output = simulate(request(local_capable=False, with_grant=True))
        self.assertEqual(output["route"], "CLOUD")
        self.assertTrue(output["cloud_permission_valid"])
        self.assertIn("EXPLICIT_SIMULATED_CLOUD_PERMISSION", output["reason_code"])
        self.assertEqual([x["endpoint"] for x in output["attempts"]], ["CLOUD"])

    def test_private_never_auto_escalates_even_if_operator_sets_grant(self):
        output = simulate(request(privacy="PRIVATE", text=PRIVATE,
                                  local_healthy=False, with_grant=True))
        self.assertEqual(output["route"], "UNAVAILABLE")
        self.assertIn("PRIVATE_CLOUD_BLOCKED", output["reason_code"])
        self.assertFalse(output["cloud_permission_valid"])
        self.assertFalse(output["attempts"])

    def test_private_can_stay_local(self):
        self.assertEqual(simulate(request(privacy="PRIVATE", text=PRIVATE))["route"], "LOCAL")

    def test_unknown_privacy_abstains_even_if_local_model_healthy(self):
        output = simulate(request(privacy="UNKNOWN", with_grant=True))
        self.assertEqual(output["route"], "UNAVAILABLE")
        self.assertEqual(output["reason_code"], "PRIVACY_CLASSIFICATION_UNKNOWN")

    def test_missing_grant_mismatched_request_or_payload_refuses_cloud(self):
        for grant in (None,
                      CloudGrant("another-request", sha256(TEXT.encode())),
                      CloudGrant("r1", sha256(b"other public task")),
                      CloudGrant("r1", sha256(TEXT.encode()), scope="REAL_PROVIDER"),
                      CloudGrant("r1", sha256(TEXT.encode()), operator_confirmed=False)):
            output = simulate(request(local_healthy=False, grant_override=grant))
            self.assertEqual(output["route"], "UNAVAILABLE")
            self.assertIn("CLOUD_GRANT_MISSING_OR_MISMATCHED", output["reason_code"])

    def test_unavailable_local_falls_back_if_public_and_authorized(self):
        output = simulate(request(local_healthy=False, with_grant=True))
        self.assertEqual(output["route"], "CLOUD")
        self.assertIn("LOCAL_RUNTIME_UNAVAILABLE", output["reason_code"])

    def test_runtime_failure_falls_back_only_when_permitted(self):
        yes = simulate(request(local_fails=True, with_grant=True))
        no = simulate(request(local_fails=True, with_grant=False))
        self.assertEqual(yes["route"], "CLOUD")
        self.assertEqual(no["route"], "UNAVAILABLE")
        self.assertEqual([x["result"] for x in yes["attempts"]],
                         ["SIMULATED_FAILURE", "SIMULATED_SUCCESS"])
        self.assertEqual([x["endpoint"] for x in no["attempts"]], ["LOCAL"])

    def test_if_cloud_unhealthy_or_fails_router_abstains(self):
        down = simulate(request(local_healthy=False, cloud_healthy=False, with_grant=True))
        bad = simulate(request(local_healthy=False, cloud_fails=True, with_grant=True))
        self.assertEqual(down["route"], "UNAVAILABLE")
        self.assertEqual(bad["route"], "UNAVAILABLE")
        self.assertIn("CLOUD_UNAVAILABLE", down["reason_code"])
        self.assertEqual(bad["attempts"][-1]["result"], "SIMULATED_FAILURE")

    def test_unapproved_tool_can_never_route(self):
        x = simulate(request(task="run_shell", with_grant=True))
        self.assertEqual(x["route"], "UNAVAILABLE")
        self.assertEqual(x["attempts"], [])
        self.assertEqual(x["reason_code"], "TOOL_NOT_ALLOWLISTED")

    def test_strict_request_boundaries(self):
        with self.assertRaises(ValueError):
            request(name="../private")
        with self.assertRaises(ValueError):
            RouteRequest("v1", "", "PUBLIC", "haios_status")
        with self.assertRaises(ValueError):
            RouteRequest("v1", TEXT, "PUBLIC", "haios_status", local_healthy=1)


class ReceiptReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "receipts.jsonl"
        self.journal = ReceiptJournal(self.path)

    def test_receipt_chain_replays_and_no_prompt_or_secret_is_persisted(self):
        a = self.journal.append(request(name="local1", text=PRIVATE,
                                        privacy="PRIVATE"),
                                observed_utc="2026-10-28T00:00:00+00:00")
        b = self.journal.append(request(name="cloud2", local_healthy=False,
                                        with_grant=True),
                                observed_utc="2026-10-28T00:00:01+00:00")
        result = self.journal.verify()
        self.assertEqual(result["count"], 2)
        self.assertTrue(result["valid"])
        self.assertEqual(a["sequence"], 1)
        self.assertEqual(b["previous_hash"], a["receipt_hash"])
        self.assertEqual(b["receipt_hash"], result["head_hash"])
        raw = self.path.read_text()
        self.assertNotIn(PRIVATE, raw)
        self.assertNotIn(TEXT, raw)
        self.assertNotIn(sha256(PRIVATE.encode()), raw)
        self.assertIn("NONPUBLIC_PAYLOAD_NOT_FINGERPRINTED", raw)
        self.assertIsNone(a["request"]["grant"])
        self.assertEqual(a["decision"], evaluate(a["request"]))

    def test_unknown_privacy_excludes_payload_fingerprint_and_grant(self):
        obscure = "MY_PRIVATE_ACCOUNT_PASSWORD_PLACEHOLDER"
        r = request(name="unknown-risk", text=obscure, privacy="UNKNOWN",
                    with_grant=True, local_healthy=False)
        event = self.journal.append(r)
        self.assertEqual(event["decision"]["route"], "UNAVAILABLE")
        self.assertIsNone(event["request"]["grant"])
        raw = self.path.read_text()
        self.assertNotIn(obscure, raw)
        self.assertNotIn(sha256(obscure.encode()), raw)
        self.assertTrue(self.journal.verify()["valid"])

    def test_mutation_rejected(self):
        self.journal.append(request(), observed_utc="2026-10-28T00:00:00+00:00")
        values = self.path.read_text().splitlines()
        changed = json.loads(values[0])
        changed["decision"]["route"] = "CLOUD"
        self.path.write_text(json.dumps(changed) + "\n")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            self.journal.verify()
        with self.assertRaises(ValueError):
            self.journal.append(request(name="new"))

    def test_forged_valid_hash_but_policy_divergence_rejected(self):
        self.journal.append(request(), observed_utc="2026-10-28T00:00:00+00:00")
        changed = json.loads(self.path.read_text())
        changed["decision"]["route"] = "CLOUD"
        changed["receipt_hash"] = sha256(canonical({
            k: v for k, v in changed.items() if k != "receipt_hash"
        }))
        self.path.write_bytes(canonical(changed) + b"\n")
        with self.assertRaisesRegex(ValueError, "policy replay diverges"):
            self.journal.verify()

    def test_truncated_tail_and_symlink_refused(self):
        self.path.write_text('{"incomplete":')
        with self.assertRaises(ValueError):
            self.journal.verify()
        self.path.unlink()
        real = Path(self.tmp.name) / "secret_file.txt"
        real.write_text("PRIVATE")
        self.path.symlink_to(real)
        with self.assertRaisesRegex(ValueError, "Symlink journal refused"):
            self.journal.verify()

    def test_duplicate_request_id_refused_before_append(self):
        self.journal.append(request(), observed_utc="2026-10-28T00:00:00+00:00")
        before = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, "Duplicate request ID"):
            self.journal.append(request(), observed_utc="2026-10-28T00:00:01+00:00")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.journal.verify()["count"], 1)

    def test_exact_request_digest_grant_cannot_be_reused(self):
        g = CloudGrant("r1", sha256(TEXT.encode()))
        self.assertEqual(simulate(request(local_capable=False,
                                          grant_override=g))["route"], "CLOUD")
        self.assertEqual(simulate(request(text="another payload", local_capable=False,
                                          grant_override=g))["route"], "UNAVAILABLE")

    def test_no_external_api_imports_or_side_effects(self):
        from haios_mcp import harmonic0
        source = Path(harmonic0.__file__).read_text()
        for forbidden in ("import anthropic", "import httpx", "import requests",
                          "subprocess.run", "urllib.request", "socket.connect"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()

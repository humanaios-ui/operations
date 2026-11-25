import importlib.util
import json
import pathlib
import unittest
from datetime import datetime, timezone

P = pathlib.Path(__file__).resolve().parents[1] / "b4_admission.py"
spec = importlib.util.spec_from_file_location("b4_admission", P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REQUEST = {
    "operation": "B4_CONTENT_MIGRATION", "issue": 759,
    "seat": "seat-001", "plan_sha256": "a" * 64,
    "source_commit": "b" * 40, "target_commit": "c" * 40,
    "operation_id": "B4-12345678"
}
APPROVAL = {**REQUEST, "schema": mod.SCHEMA, "decision": "APPROVE", "expires_at": "2099-01-01T00:00:00Z"}
EVIDENCE = {
    "source": "github_api", "issue": 759, "issue_state": "open",
    "body_state": "ADMISSION_REQUESTED", "state_projection_verified": True,
    "issue_admitted": True, "consumed_operation_ids": [],
    "comments": [{"id": 100, "actor": "humanaios-ui", "author_association": "OWNER", "body": json.dumps(APPROVAL)}]
}

class TestB4(unittest.TestCase):
    def check_denied(self, request=REQUEST, evidence=EVIDENCE):
        with self.assertRaises(ValueError):
            mod.verify(request, evidence, {"humanaios-ui"}, datetime(2026, 10, 9, tzinfo=timezone.utc))

    def test_accept(self):
        got = mod.verify(REQUEST, EVIDENCE, {"humanaios-ui"}, datetime(2026, 10, 9, tzinfo=timezone.utc))
        self.assertFalse(got["merge_authority"])
    def test_missing_coordinator_admission(self):
        self.check_denied(evidence={**EVIDENCE, "issue_admitted": False})
    def test_unverified_projection(self):
        self.check_denied(evidence={**EVIDENCE, "state_projection_verified": False})
    def test_spoofed_actor(self):
        e = json.loads(json.dumps(EVIDENCE))
        e["comments"][0]["actor"] = "attacker"
        self.check_denied(evidence=e)
    def test_mismatched_hash(self):
        self.check_denied(request={**REQUEST, "plan_sha256": "d" * 64})
    def test_expired(self):
        e = json.loads(json.dumps(EVIDENCE))
        p = json.loads(e["comments"][0]["body"])
        p["expires_at"] = "2020-01-01T00:00:00Z"
        e["comments"][0]["body"] = json.dumps(p)
        self.check_denied(evidence=e)
    def test_replay(self):
        self.check_denied(evidence={**EVIDENCE, "consumed_operation_ids": ["B4-12345678"]})
    def test_duplicate_approval(self):
        self.check_denied(evidence={**EVIDENCE, "comments": EVIDENCE["comments"] * 2})
    def test_self_asserted_evidence(self):
        self.check_denied(evidence={**EVIDENCE, "source": "manifest"})
    def test_wrong_issue(self):
        self.check_denied(request={**REQUEST, "issue": 760})

if __name__ == "__main__":
    unittest.main()

"""Synthetic adversarial checks for the live GitHub API witness contract.

Fake API is a test double; these tests do not themselves authenticate GitHub.
"""
import base64
import copy
import hashlib
import json
import unittest
import urllib.parse

from experiments.scvc_v02 import trusted_witness as witness

MAIN = "a" * 40
MERGE = "b" * 40
HEAD = "c" * 40
REPO = "humanaios-ui/operations"
PRE = f"repos/{REPO}"


def git_blob(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()


class FakeAPI:
    def __init__(self):
        self.records = {}
        self.calls = []
        self.records[PRE] = {"full_name": REPO, "default_branch": "main"}
        self.records[PRE + "/branches/main"] = {"commit": {"sha": MAIN}}
        self.records[PRE + "/actions/runs/555"] = {
            "head_sha": MAIN,
            "path": witness.WORKFLOW,
            "run_attempt": 1, "event": "workflow_dispatch",
            "repository": {"full_name": REPO},
        }
        self.records[PRE + "/pulls/788"] = {
            "merged": True, "merge_commit_sha": MERGE,
        }
        self.records[PRE + "/compare/" + MERGE + "..." + MAIN] = {
            "status": "ahead",
        }
        for path in witness.SOURCE_PATHS.values():
            if path.endswith("REPOSITORY_COORDINATOR_POLICY.json"):
                payload = json.dumps({"schema_version": "0.3",
                                      "state": {"merge_authority": False}}).encode()
            else:
                payload = b"synthetic source file\n"
            self.records[f"{PRE}/contents/{path}?ref={MAIN}"] = {
                "type": "file", "path": path,
                "sha": git_blob(payload),
                "encoding": "base64", "content": base64.b64encode(payload).decode(),
            }
        self.records[PRE + "/pulls/794"] = {
            "number": 794,
            "base": {"ref": "main"},
            "head": {"sha": HEAD, "repo": {"full_name": REPO}},
        }
        self.records[PRE + "/pulls/794/files?per_page=100"] = []
        self.run_query = PRE + "/actions/runs?" + urllib.parse.urlencode(
            {"head_sha": HEAD, "event": "pull_request", "per_page": 100}
        )
        runs = []
        for idx, (name, path) in enumerate(witness.REQUIRED_CI.items(), 100):
            run = {
                "id": idx, "name": name, "path": path,
                "head_sha": HEAD, "event": "pull_request",
                "repository": {"full_name": REPO},
                "head_repository": {"full_name": REPO},
                "run_attempt": 1,
                "status": "completed", "conclusion": "success",
                "pull_requests": [{"number": 794, "head": {"sha": HEAD}}],
            }
            runs.append(run)
            self.records[f"{PRE}/actions/runs/{idx}"] = copy.deepcopy(run)
            self.records[f"{PRE}/actions/runs/{idx}/jobs?per_page=100"] = {
                "total_count": 1,
                "jobs": [{"conclusion": "success"}],
            }
        self.records[self.run_query] = {"total_count": len(runs), "workflow_runs": runs}
        self.records[PRE + "/rulesets"] = [{"id": 1, "enforcement": "active"}]
        self.records[PRE + "/rulesets/1"] = {
            "enforcement": "active",
            "conditions": {"ref_name": {"include": ["~ALL"], "exclude": []}},
            "rules": [
                {"type": "pull_request",
                 "parameters": {"required_approving_review_count": 1}},
                {"type": "required_status_checks",
                 "parameters": {"required_status_checks": [{"context": "quality"}]}},
            ],
        }

    def get(self, path):
        self.calls.append(path)
        if path not in self.records:
            raise witness.WitnessError("MISSING_FAKE_API_RESPONSE")
        return copy.deepcopy(self.records[path])


def context():
    return {
        "repository": REPO, "ref": "refs/heads/main",
        "event_name": "workflow_dispatch", "checkout_sha": MAIN,
        "run_id": 555, "run_attempt": 1,
    }


def definition():
    return json.loads(
        (__import__("pathlib").Path(__file__).resolve().parents[1] /
         "experiments/scvc_v02/milestone_graph.json").read_text()
    )


class WitnessTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.ctx = context()

    def facts(self):
        return witness.collect(self.api, self.ctx)

    def test_positive_witness_and_non_authority_progression(self):
        evidence = self.facts()
        self.assertEqual(set(evidence["ci"]), set(witness.REQUIRED_CI))
        self.assertTrue(evidence["trust_root_protected"])
        result = witness.derive_progress(definition(), evidence)
        self.assertEqual(result["milestones"][0]["candidate_status"],
                         "OBSERVATIONAL_MILESTONE_ACHIEVED")
        self.assertTrue(result["milestones"][0]["observational_achievement"])
        self.assertEqual(result["milestones"][1]["candidate_status"],
                         "ELIGIBLE_FOR_AUTHORIZED_WORK")
        self.assertFalse(result["can_authorize"])
        self.assertFalse(result["can_dispatch"])
        self.assertFalse(result["merge_authority"])
        self.assertFalse(result["cryptographic_attestation_verified"])
        self.assertFalse(any(r["governance_accepted"] for r in result["milestones"]))

    def test_no_branch_protection_halts_observational_achievement(self):
        self.api.records[PRE + "/rulesets/1"]["rules"] = [
            {"type": "deletion"}, {"type": "non_fast_forward"}]
        facts = self.facts()
        self.assertFalse(facts["trust_root_protected"])
        result = witness.derive_progress(definition(), facts)
        self.assertEqual(result["milestones"][0]["candidate_status"], "BLOCKED_TRUST_ROOT")
        self.assertNotEqual(result["milestones"][1]["candidate_status"],
                            "ELIGIBLE_FOR_AUTHORIZED_WORK")

    def test_unsigned_external_claim_is_not_live_witness(self):
        with self.assertRaises(witness.WitnessError):
            witness.derive_progress(definition(), {"source": "UNTRUSTED_JSON"})

    def test_wrong_repository_rejected(self):
        self.ctx["repository"] = "attacker/repo"
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_wrong_ref_rejected(self):
        self.ctx["ref"] = "refs/pull/794/merge"
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_default_head_race_rejected(self):
        self.ctx["checkout_sha"] = "d" * 40
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_mismatched_self_workflow_rejected(self):
        self.api.records[PRE + "/actions/runs/555"]["path"] = "bad.yml"
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_mismatched_witness_attempt_rejected(self):
        self.ctx["run_attempt"] = 2
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_changed_predecessor_ancestry_rejected(self):
        self.api.records[PRE + "/compare/" + MERGE + "..." + MAIN]["status"] = "diverged"
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_forged_blob_digest_rejected(self):
        x = PRE + "/contents/" + witness.SOURCE_PATHS["HLKS_VLR_SCHEMA_PIN"] + "?ref=" + MAIN
        self.api.records[x]["sha"] = "f" * 40
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_forged_policy_state_rejected(self):
        x = PRE + "/contents/" + witness.SOURCE_PATHS["COORDINATOR_POLICY_PIN"] + "?ref=" + MAIN
        b = json.dumps({"schema_version": "0.3", "state": {"merge_authority": True}}).encode()
        self.api.records[x]["content"] = base64.b64encode(b).decode()
        self.api.records[x]["sha"] = git_blob(b)
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_issuer_workflow_changed_by_pr_is_rejected(self):
        self.api.records[PRE + "/pulls/794/files?per_page=100"] = [
            {"filename": ".github/workflows/security-gates.yml"}]
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_stale_success_does_not_override_newer_failure(self):
        runs = self.api.records[self.api.run_query]["workflow_runs"]
        newer = copy.deepcopy(runs[0])
        newer.update({"id": 999, "run_attempt": 1, "conclusion": "failure"})
        runs.append(newer)
        self.api.records[PRE + "/actions/runs/999"] = newer
        self.api.records[PRE + "/actions/runs/999/jobs?per_page=100"] = {
            "total_count": 1, "jobs": [{"conclusion": "failure"}],
        }
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_ci_head_mismatch_rejected(self):
        self.api.records[self.api.run_query]["workflow_runs"][0]["head_sha"] = "d" * 40
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_run_attempt_mismatch_rejected(self):
        self.api.records[PRE + "/actions/runs/100"]["run_attempt"] = 2
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_job_failure_rejected(self):
        self.api.records[PRE + "/actions/runs/101/jobs?per_page=100"]["jobs"][0]["conclusion"] = "failure"
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_incomplete_job_pagination_rejected(self):
        self.api.records[PRE + "/actions/runs/101/jobs?per_page=100"]["total_count"] = 101
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_unbounded_changed_files_rejected(self):
        self.api.records[PRE + "/pulls/794/files?per_page=100"] = [
            {"filename": f"random/{i}"} for i in range(100)]
        with self.assertRaises(witness.WitnessError):
            self.facts()

    def test_current_main_without_review_rules_not_protected(self):
        self.api.records[PRE + "/rulesets/1"]["rules"] = [
            {"type": "required_status_checks",
             "parameters": {"required_status_checks": [{"context": "quality"}]}}]
        self.assertFalse(self.facts()["trust_root_protected"])

    def test_trusted_context_does_not_make_agent_json_authenticated(self):
        report = witness.derive_progress(definition(), self.facts())
        self.assertFalse(report["cryptographic_attestation_verified"])
        self.assertFalse(report["milestones"][4]["governance_accepted"])


if __name__ == "__main__":
    unittest.main()

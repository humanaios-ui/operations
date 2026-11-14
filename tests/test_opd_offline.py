"""OPD must stay unable to authorize, execute or learn from untrusted traces."""
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("opd", ROOT / "tools/opd/offline_distiller.py")
opd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opd)

def trace(i, head=None):
    return {"schema": opd.SCHEMA, "trace_id": str(i),
            "repository": "humanaios-ui/operations",
            "head_sha": head or ("%040x" % (i + 1)), "state": {"ci": "failure"},
            "proposed_action": {"kind": "diagnose_ci", "category": "permission_error"},
            "corrected_action": {"kind": "prepare_evidence", "category": "permission_error"},
            "outcome": {"status": "verified"},
            "evidence": {"source": "protected_ci",
                         "url": "https://github.com/humanaios-ui/operations/actions/runs/123"},
            "authority_effect": "NONE"}

class OfflineDistillerTests(unittest.TestCase):
    def run_cli(self, train, holdout):
        with tempfile.TemporaryDirectory() as tmp:
            train_path, holdout_path, out_path = (
                Path(tmp) / name for name in ("train.jsonl", "holdout.jsonl", "report.json"))
            for path, traces in ((train_path, train), (holdout_path, holdout)):
                path.write_text("".join(json.dumps(t) + "\n" for t in traces))
            with patch.object(sys, "argv", ["opd", "--train", str(train_path),
                                            "--holdout", str(holdout_path),
                                            "--out", str(out_path)]), redirect_stdout(io.StringIO()):
                opd.main()
            return json.loads(out_path.read_text())

    def test_candidate_requires_two_distinct_heads(self):
        self.assertEqual(opd.compile_rules([trace(1)])["rules"], [])
        policy = opd.compile_rules([trace(1), trace(2)])
        self.assertEqual(len(policy["rules"]), 1)
        self.assertEqual(opd.replay([trace(3)], policy)["correct"], 1)

    def test_admission_actions_rejected(self):
        for action in ("proposed_action", "corrected_action"):
            for kind in ("admit", "approve", "merge", "dispatch", "publish_receipt"):
                with self.subTest(action=action, kind=kind):
                    t = trace(1)
                    t[action]["kind"] = kind
                    self.assertEqual(opd.validate(t), (False, "unsafe_action"))
                    self.assertEqual(opd.compile_rules([t])["rules"], [])

    def test_action_validation_reasons(self):
        for action in ("proposed_action", "corrected_action"):
            for field, value, reason in (("kind", None, "invalid_action_kind"),
                                         ("category", None, "missing_category"),
                                         ("category", "", "invalid_category"),
                                         ("category", "bad-category", "invalid_category"),
                                         ("category", "a" * 65, "invalid_category")):
                with self.subTest(action=action, field=field, value=value):
                    t = trace(1)
                    t[action][field] = value
                    self.assertEqual(opd.validate(t), (False, reason))

    def test_comments_are_not_evidence(self):
        t = trace(1)
        t["evidence"]["source"] = "issue_comment"
        self.assertFalse(opd.validate(t)[0])

    def test_exact_sha_required(self):
        for head in ("main", "a" * 39, "A" * 40, 10 ** 39, None, [], {}):
            with self.subTest(head=head):
                t = trace(1)
                t["head_sha"] = head
                self.assertEqual(opd.validate(t), (False, "invalid_schema_or_head"))
                self.assertEqual(opd.compile_rules([t])["accepted"], 0)

    def test_nonempty_string_trace_id_required(self):
        for trace_id in ("", None, 1, [], {}):
            with self.subTest(trace_id=trace_id):
                t = trace(1)
                t["trace_id"] = trace_id
                self.assertEqual(opd.validate(t), (False, "invalid_trace_id"))
                self.assertEqual(opd.compile_rules([t])["accepted"], 0)

    def test_outcome_and_authority_fail_closed(self):
        for field, value in (("outcome", {"status": "claimed"}),
                             ("authority_effect", "ADMITTED")):
            t = trace(1)
            t[field] = value
            self.assertFalse(opd.validate(t)[0])

    def test_payload_cannot_contain_commands(self):
        t = trace(1)
        t["corrected_action"]["command"] = "gh pr merge 1"
        self.assertFalse(opd.validate(t)[0])

    def test_no_train_holdout_leakage_and_baseline(self):
        policy = opd.compile_rules([trace(1), trace(2)])
        result = opd.replay([trace(3), trace(4)], policy)
        self.assertEqual(result["coverage"], 1.0)
        self.assertEqual(result["authority_bypasses"], 0)
        self.assertTrue(result["safety_preserved"])

    def test_cli_rejects_train_holdout_overlap(self):
        for holdout in (trace(1), trace(3, head=trace(1)["head_sha"])):
            with self.subTest(trace_id=holdout["trace_id"]):
                stderr = io.StringIO()
                with redirect_stderr(stderr), self.assertRaises(SystemExit) as exc:
                    self.run_cli([trace(1)], [holdout])
                self.assertEqual(exc.exception.code, 2)
                self.assertIn("train/holdout leakage", stderr.getvalue())

    def test_cli_ignores_invalid_traces_for_overlap(self):
        invalid = [None, [], {}]
        for field, value in (("trace_id", []), ("trace_id", {}), ("trace_id", ""),
                             ("head_sha", []), ("head_sha", {}), ("head_sha", 10 ** 39),
                             ("outcome", {"status": "claimed"})):
            for i in (1, 3):
                t = trace(i)
                t[field] = value
                invalid.append(t)
        report = self.run_cli([trace(1), trace(2)] + invalid, [trace(3)] + invalid)
        self.assertEqual(report["policy"]["accepted"], 2)
        self.assertEqual(report["replay"]["eligible"], 1)
        self.assertEqual(report["baseline_review_calls"], 1 + len(invalid))
        self.assertEqual(report["potential_review_calls_avoided"], 1)
        self.assertIsNone(report["measured_production_savings"])

    def test_smoke_test_failure_with_assertions_disabled(self):
        code = ("import runpy, sys; "
                "opd = runpy.run_path(sys.argv[1]); "
                "opd['main'].__globals__['run_smoke_test'] = lambda: False; "
                "sys.argv = ['opd', '--smoke-test']; opd['main']()")
        result = subprocess.run([sys.executable, "-O", "-c", code,
                                 str(ROOT / "tools/opd/offline_distiller.py")],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("OPD smoke test FAIL", result.stderr)
        self.assertNotIn("PASS", result.stdout)

    def test_duplicate_does_not_establish_independence(self):
        policy = opd.compile_rules([trace(1), trace(1)])
        self.assertFalse(policy["rules"])

    def test_untrusted_trace_not_counted(self):
        t = trace(3)
        t["evidence"]["url"] = "https://example.com/fake"
        self.assertEqual(opd.replay([t], opd.compile_rules([trace(1), trace(2)]))["eligible"], 0)

if __name__ == "__main__":
    unittest.main()

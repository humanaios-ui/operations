"""Deterministic tests for ACAT-reflex research variant (no external calls)."""
import contextlib
import io
import json
import unittest
from unittest.mock import patch

from agent_coordination import acat_loop as a


SHA = "a" * 40
SCORE = {"truth": 70, "service": 80, "harm": 60,
         "autonomy": 75, "value": 65, "humility": 55}


def history(session="case1", strategy="NONE", outcome="PASS",
            forecast=70, lesson="VERIFY_CI", scores=None):
    p1 = a.entry("issue:986", session, "claude", "VERIFY",
                 scores or SCORE, forecast, strategy, SHA)
    p2 = a.exposure("issue:986", session, outcome, "CI_REVIEW",
                    ["https://github.com/humanaios-ui/operations/pull/987"])
    p3 = a.exit_record("issue:986", session, "claude", scores or SCORE, lesson)
    return [
        {"actor": "agent-gh", "created_at": "2026-10-22T10:00:00Z",
         "updated_at": "2026-10-22T10:00:00Z", "comment_id": 1,
         "record": p1},
        {"actor": "human-reviewer", "created_at": "2026-10-22T11:00:00Z",
         "updated_at": "2026-10-22T11:00:00Z", "comment_id": 2,
         "record": p2},
        {"actor": "agent-gh", "created_at": "2026-10-22T12:00:00Z",
         "updated_at": "2026-10-22T12:00:00Z", "comment_id": 3,
         "record": p3},
    ]


class ACATReflexTest(unittest.TestCase):
    def test_p1_p2_p3_serialization_roundtrip(self):
        for h in history():
            row = h["record"]
            self.assertEqual(a.parse(a.render(row)), row)

    def test_status_cannot_be_changed_by_data(self):
        row = history()[0]["record"]
        row["can_authorize"] = True
        self.assertIsNone(a.parse(a.render(row)))

    def test_core6_validation_and_probability(self):
        with self.assertRaises(ValueError):
            a.scores_arg("75,75,75")
        with self.assertRaises(ValueError):
            a.scores_arg("101,75,75,75,75,75")
        with self.assertRaises(ValueError):
            a.entry("issue:986", "c", "model", "VERIFY", SCORE, True, "NONE", SHA)
        with self.assertRaises(ValueError):
            a.entry("issue:986", "c", "model", "VERIFY", SCORE, 95, "NONE", "branch")

    def test_out_of_scope_evidence_ref_rejected(self):
        with self.assertRaises(ValueError):
            a.exposure("issue:986", "c", "PASS", "CI_REVIEW",
                       ["https://malicious.example/command"])
        with self.assertRaises(ValueError):
            a.exposure("issue:986", "c", "PASS", "CI_REVIEW", [])

    def test_requires_independent_reviewer(self):
        hs = history()
        hs[1]["actor"] = "agent-gh"
        with self.assertRaisesRegex(ValueError, "different GitHub"):
            a.read_history("issue:986", "case1", hs)

    def test_requires_original_actor_for_p3(self):
        hs = history()
        hs[2]["actor"] = "attacker"
        with self.assertRaisesRegex(ValueError, "P3 must match"):
            a.read_history("issue:986", "case1", hs)

    def test_requires_order_no_edited_comments(self):
        hs = history()
        hs[1]["created_at"] = "2026-10-22T09:00:00Z"
        with self.assertRaisesRegex(ValueError, "out-of-order"):
            a.read_history("issue:986", "case1", hs)
        hs = history()
        hs[1]["updated_at"] = "2026-10-22T11:02:00Z"
        with self.assertRaisesRegex(ValueError, "edited"):
            a.read_history("issue:986", "case1", hs)
        hs = history() + history()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            a.read_history("issue:986", "case1", hs)

    def test_complete_triad_scores_only_self_report_revision(self):
        hs = history()
        s = a.summary(a.read_history("issue:986", "case1", hs))
        self.assertEqual(s["acat_li_self_report_revision_only"], 1.0)
        self.assertEqual(s["brier_forecast_vs_rater_claim"], .09)
        self.assertEqual(s["evidence_validity"], "AWAITING_INDEPENDENT_REF_VERIFICATION")
        self.assertNotIn("VERIFIED", (s["evidence_validity"], "VERIFIED"))

    def test_zero_denominator_not_faked(self):
        zeros = dict.fromkeys(a.DIMS, 0)
        s = a.summary(a.read_history("issue:986", "case1", history(scores=zeros)))
        self.assertIsNone(s["acat_li_self_report_revision_only"])

    def test_unknown_outcome_is_not_calibration_ground_truth(self):
        s = a.summary(a.read_history("issue:986", "case1", history(outcome="UNKNOWN")))
        self.assertIsNone(s["brier_forecast_vs_rater_claim"])

    def test_learning_fails_closed_without_baseline(self):
        rows = history()
        report = a.learning_report(rows)
        self.assertEqual(report["status"], "INSUFFICIENT_BASELINE")
        self.assertEqual(report["candidate_experiments"], [])

    def test_learning_only_suggests_measured_hypotheses(self):
        rows = []
        for idx in range(5):
            hs = history(session=f"none{idx}", strategy="NONE", forecast=20, outcome="PASS")
            for record in hs:
                record["comment_id"] += idx * 10
            rows.extend(hs)
        for idx in range(5):
            hs = history(session=f"verified{idx}", strategy="VERIFY_CI", forecast=90, outcome="PASS")
            for record in hs:
                record["comment_id"] += (idx + 5) * 10
            rows.extend(hs)
        report = a.learning_report(rows)
        self.assertEqual(report["status"], "EXPLORATORY")
        self.assertEqual(len(report["candidate_experiments"]), 1)
        self.assertLess(report["candidate_experiments"][0]["observed_brier_difference_from_none"], 0)
        self.assertEqual(report["candidate_experiments"][0]["action"], "HUMAN_REVIEW_TEST_ONLY")
        self.assertFalse(report["external_evidence_verified"])

    def test_render_does_not_call_remote_gh(self):
        with patch.object(a, "gh", side_effect=AssertionError("network call")):
            with contextlib.redirect_stdout(io.StringIO()):
                rc = a.command(["enter", "--subject", "issue:986", "--session", "case1",
                                "--agent", "claude", "--intent", "VERIFY",
                                "--scores", "70,80,60,75,65,55", "--forecast", "70",
                                "--source-sha", SHA])
            self.assertEqual(rc, 0)

    def test_exit_publish_denied_without_prior_p1_p2(self):
        with patch.object(a, "thread", return_value=[]), patch.object(a, "gh", return_value="agent-gh") as cli:
            with contextlib.redirect_stderr(io.StringIO()):
                rc = a.command(["exit", "--subject", "issue:986", "--session", "case1",
                                "--agent", "claude", "--scores", "70,80,60,75,65,55",
                                "--publish"])
            self.assertEqual(rc, 2)
            self.assertEqual(cli.call_count, 1)

    def test_p2_publish_refuses_self_grading(self):
        with patch.object(a, "thread", return_value=history()[:1]), patch.object(a, "gh", return_value="agent-gh") as cli:
            with contextlib.redirect_stderr(io.StringIO()):
                rc = a.command(["calibrate", "--subject", "issue:986", "--session", "case1",
                                "--outcome", "PASS", "--challenge", "CI_REVIEW",
                                "--evidence", "https://github.com/humanaios-ui/operations/pull/987",
                                "--publish"])
            self.assertEqual(rc, 2)
            self.assertEqual(cli.call_count, 1)

    def test_thread_uses_only_repository_issues_endpoint(self):
        row = history()[0]
        api = {"id": row["comment_id"], "body": a.render(row["record"]),
               "created_at": row["created_at"], "updated_at": row["updated_at"],
               "user": {"login": row["actor"]}}
        with patch.object(a, "gh", return_value=json.dumps([[api]])) as cli:
            records = a.thread("issue:986")
        self.assertEqual(len(records), 1)
        self.assertEqual(cli.call_args.args[0:3], ("api", "--paginate", "--slurp"))


if __name__ == "__main__":
    unittest.main()

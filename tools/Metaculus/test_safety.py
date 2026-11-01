"""Offline tests for safety.py (caps, kill switch, comment privacy). No network, no creds.

The live-run approval gate is mode_gate.py and is tested in tests/test_offline_fixture.py.
"""
import os, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import safety as s

HERE = Path(__file__).parent


class TestKillSwitch(unittest.TestCase):
    def test_env_switch(self):
        self.assertTrue(s.kill_switch_engaged({s.KILL_SWITCH_ENV: "1"}))
        self.assertFalse(s.kill_switch_engaged({}))
        self.assertFalse(s.kill_switch_engaged({s.KILL_SWITCH_ENV: "0"}))

    def test_file_switch(self):
        path = HERE / "_kill_switch_test_marker"
        path.write_text("x")
        try:
            self.assertTrue(s.kill_switch_engaged({s.KILL_SWITCH_FILE_ENV: str(path)}))
        finally:
            path.unlink()
        self.assertFalse(s.kill_switch_engaged({s.KILL_SWITCH_FILE_ENV: str(path)}))


class TestBudget(unittest.TestCase):
    def test_max_questions(self):
        t = s.BudgetTracker(s.Budget(max_questions=2, max_usd_per_run=100))
        for i in range(2):
            self.assertTrue(t.may_dispatch(str(i))[0]); t.record_dispatch(str(i))
        self.assertFalse(t.may_dispatch("x")[0])

    def test_usd_hard_stop_before_dispatch(self):
        t = s.BudgetTracker(s.Budget(max_questions=10, max_usd_per_run=0.30,
                                     est_usd_upper_per_question=0.20))
        self.assertTrue(t.may_dispatch("a")[0]); t.record_dispatch("a", 0.2)
        self.assertFalse(t.may_dispatch("b")[0])

    def test_default_charge_enforces_run_cap(self):
        t = s.BudgetTracker(s.Budget(max_questions=50, max_usd_per_run=0.50,
                                     est_usd_upper_per_question=0.20))
        n = 0
        for i in range(50):
            ok, _ = t.may_dispatch(str(i))
            if not ok:
                break
            t.record_dispatch(str(i))  # no billed_usd: must reserve the upper bound
            n += 1
        self.assertEqual(n, 2)

    def test_per_question_ceiling(self):
        t = s.BudgetTracker(s.Budget(max_usd_per_question=0.1, est_usd_upper_per_question=0.2))
        self.assertFalse(t.may_dispatch("a")[0])

    def test_no_duplicates_and_reason_code(self):
        t = s.BudgetTracker(s.Budget()); t.record_dispatch("a")
        self.assertEqual(t.may_dispatch("a"), (False, s.DUPLICATE_REASON))

    def test_retries_bounded(self):
        t = s.BudgetTracker(s.Budget(max_total_retries=2))
        self.assertEqual([t.allow_retry() for _ in range(3)], [True, True, False])

    def test_backoff_honors_429(self):
        self.assertEqual(s.backoff_seconds(0), 2.0)
        self.assertEqual(s.backoff_seconds(2), 8.0)
        self.assertEqual(s.backoff_seconds(0, retry_after=30), 30)
        self.assertEqual(s.backoff_seconds(10), 60.0)
        self.assertEqual(s.backoff_seconds(0, retry_after=120), 120)  # server wait honored

    def test_env_budget(self):
        self.assertEqual(s.budget_from_env({"BOT_MAX_QUESTIONS": "3"}).max_questions, 3)
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_QUESTIONS": "x"})
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_USD_RUN": "-1"})

    def test_nan_budget_rejected(self):
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_USD_RUN": "nan"})
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_USD_QUESTION": "nan"})

    def test_zero_samples_rejected(self):
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_SAMPLES": "0"})


class TestPrivacyAndDeps(unittest.TestCase):
    def test_comment_private_default(self):
        self.assertTrue(s.comment_is_private())
        self.assertTrue(s.comment_is_private(None))

    def test_main_has_no_public_comment(self):
        self.assertNotIn("is_private=False,", (HERE / "main.py").read_text().split("def _post_metaculus_comment")[1])

    def test_denied_pins(self):
        self.assertTrue(s.denied_pins(["litellm==1.107.0"]))
        self.assertFalse(s.denied_pins(["litellm==1.106.0", "# litellm==1.107.0"]))

    def test_requirements_clean_and_constrained(self):
        self.assertEqual(s.denied_pins((HERE / "requirements.txt").read_text().splitlines()), [])
        self.assertIn("litellm!=1.107.0", (HERE / "constraints.txt").read_text())
        docker = (HERE / "Dockerfile").read_text()
        self.assertIn("-c constraints.txt", docker)
        self.assertIn("safety.py", docker)
        self.assertIn("mode_gate.py", docker)


class TestEntryOrdering(unittest.TestCase):
    """Source-order check: main's approval gate, then kill switch and budgets, then clients."""

    def test_gate_then_caps_then_clients(self):
        main = (HERE / "main.py").read_text()
        block = main[main.index('if __name__ == "__main__":'):]
        order = [
            block.index("require_explicit_live_approval("),
            block.index("kill_switch_engaged(os.environ)"),
            block.index("budget_from_env(os.environ)"),
            block.index("HumanAIOSBotV2("),
            block.index("MetaculusClient()"),
        ]
        self.assertEqual(order, sorted(order))
        self.assertIn("log_report_summary(forecast_reports)", block)

    def test_one_event_loop_for_tournaments(self):
        block = (HERE / "main.py").read_text().split('if run_mode == "tournament":')[1]
        block = block.split('elif run_mode == "metaculus_cup":')[0]
        self.assertEqual(block.count("asyncio.run("), 1)

    def test_sibling_imports_work_for_path_loaders(self):
        self.assertIn("sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))",
                      (HERE / "main.py").read_text())


if __name__ == "__main__":
    unittest.main()

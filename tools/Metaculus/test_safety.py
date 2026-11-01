"""Offline tests for safety.py and the E0 entry point. No network, no creds."""
import json, os, subprocess, sys, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import safety as s

HERE = Path(__file__).parent


class TestGate(unittest.TestCase):
    def test_default_offline(self):
        self.assertEqual(s.DEFAULT_MODE, "offline_fixture")
        s.require_live_allowed("offline_fixture", False, {})

    def test_live_fails_closed(self):
        for m in s.LIVE_MODES:
            with self.assertRaises(s.RefusedError):
                s.require_live_allowed(m, False, {})                      # no flag
            with self.assertRaises(s.RefusedError):
                s.require_live_allowed(m, True, {})                       # no approval
            with self.assertRaises(s.RefusedError):
                s.require_live_allowed(m, True, {s.APPROVAL_ENV: "true"}) # wrong value
            s.require_live_allowed(m, True, {s.APPROVAL_ENV: "1"})

    def test_kill_switch(self):
        env = {s.APPROVAL_ENV: "1", s.KILL_SWITCH_ENV: "1"}
        with self.assertRaises(s.RefusedError):
            s.require_live_allowed("test_questions", True, env)

    def test_unknown_mode(self):
        with self.assertRaises(s.RefusedError):
            s.require_live_allowed("bogus", True, {s.APPROVAL_ENV: "1"})


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

    def test_per_question_ceiling(self):
        t = s.BudgetTracker(s.Budget(max_usd_per_question=0.1, est_usd_upper_per_question=0.2))
        self.assertFalse(t.may_dispatch("a")[0])

    def test_no_duplicates(self):
        t = s.BudgetTracker(s.Budget()); t.record_dispatch("a")
        self.assertFalse(t.may_dispatch("a")[0])

    def test_retries_bounded(self):
        t = s.BudgetTracker(s.Budget(max_total_retries=2))
        self.assertEqual([t.allow_retry() for _ in range(3)], [True, True, False])

    def test_backoff_honors_429(self):
        self.assertEqual(s.backoff_seconds(0), 2.0)
        self.assertEqual(s.backoff_seconds(2), 8.0)
        self.assertEqual(s.backoff_seconds(0, retry_after=30), 30)
        self.assertEqual(s.backoff_seconds(10), 60.0)
        self.assertEqual(s.backoff_seconds(0, retry_after=120), 120)  # server wait honored

    def test_nan_budget_rejected(self):
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_USD_RUN": "nan"})
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_USD_QUESTION": "nan"})

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

    def test_duplicate_reason_code(self):
        t = s.BudgetTracker(s.Budget()); t.record_dispatch("a")
        self.assertEqual(t.may_dispatch("a"), (False, s.DUPLICATE_REASON))

    def test_zero_samples_rejected(self):
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_SAMPLES": "0"})

    def test_env_budget(self):
        self.assertEqual(s.budget_from_env({"BOT_MAX_QUESTIONS": "3"}).max_questions, 3)
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_QUESTIONS": "x"})
        with self.assertRaises(s.RefusedError):
            s.budget_from_env({"BOT_MAX_USD_RUN": "-1"})


class TestPrivacyAndDeps(unittest.TestCase):
    def test_comment_private_default(self):
        self.assertTrue(s.comment_is_private())
        self.assertTrue(s.comment_is_private(None))

    def test_main_has_no_public_comment(self):
        self.assertNotIn("is_private=False", (HERE / "main.py").read_text())

    def test_denied_pins(self):
        self.assertTrue(s.denied_pins(["litellm==1.107.0"]))
        self.assertFalse(s.denied_pins(["litellm==1.106.0", "# litellm==1.107.0"]))

    def test_requirements_clean_and_constrained(self):
        self.assertEqual(s.denied_pins((HERE / "requirements.txt").read_text().splitlines()), [])
        self.assertIn("litellm!=1.107.0", (HERE / "constraints.txt").read_text())
        self.assertIn("-c constraints.txt", (HERE / "Dockerfile").read_text())

    def test_receipt_no_secrets_and_unverified(self):
        r = s.build_receipt(
            "offline_fixture", "offline_ok", s.Budget(),
            key="secret-token", api_token="abc", skip_reason="none",
            permission_state="VERIFIED", network_io=True, mode_override="x",
        )
        self.assertNotIn("secret-token", json.dumps(r))
        self.assertNotIn("abc", json.dumps(r))
        self.assertEqual(r["skip_reason"], "none")           # named extra is kept
        self.assertEqual(r["permission_state"], s.PERMISSION_UNVERIFIED)  # not replaceable
        self.assertFalse(r["network_io"])
        self.assertEqual(r["permission_state"], s.PERMISSION_UNVERIFIED)
        self.assertEqual(r["access_tier"], s.NO_CP)
        self.assertFalse(r["network_io"])


class TestEntryPoint(unittest.TestCase):
    """Runs main.py only if its heavy deps are installed; otherwise skip."""
    @classmethod
    def setUpClass(cls):
        try:
            import forecasting_tools, supabase, dotenv  # noqa
        except Exception:
            raise unittest.SkipTest("forecasting-tools/supabase not installed")

    def run_main(self, *a, env=None):
        e = {k: v for k, v in os.environ.items() if not k.endswith(("_KEY", "_TOKEN"))}
        # Explicit non-approved value: dotenv never overrides a variable that is set, so a
        # local .env cannot re-enable publishing in these tests.
        e[s.APPROVAL_ENV] = "0"; e.update(env or {})
        return subprocess.run([sys.executable, str(HERE / "main.py"), *a],
                              capture_output=True, text=True, env=e, cwd=HERE)

    def test_bare_invocation_offline(self):
        p = self.run_main(); self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["outcome"], "offline_ok")

    def test_test_questions_refused(self):
        for a in (["--mode", "test_questions"], ["--mode", "test_questions", "--publish"]):
            self.assertEqual(self.run_main(*a).returncode, 2)


if __name__ == "__main__":
    unittest.main()

"""Zero-dependency E0 Metaculus offline/no-CP and live-mode guard regressions."""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mode_gate import ExternalWritesNotApproved, require_explicit_live_approval
from offline_fixture import FixtureError, run_fixture


class OfflineFixtureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((ROOT / "fixtures" / "synthetic_binary.json").read_text())

    def test_synthetic_binary_baseline(self):
        receipt = run_fixture(self.fixture)
        self.assertEqual(receipt["mean_probability"], 0.5)
        self.assertEqual(receipt["brier"], 0.25)
        self.assertEqual(receipt["external_api_calls"], 0)
        self.assertEqual(receipt["database_writes"], 0)
        self.assertFalse(receipt["live_submission"])

    def test_forbid_community_aggregate_even_nested(self):
        self.fixture["question"]["community_prediction"] = 0.5
        with self.assertRaises(FixtureError):
            run_fixture(self.fixture)

    def test_no_unapproved_access_tier(self):
        self.fixture["access_tier"] = "FULL_CP"
        with self.assertRaises(FixtureError):
            run_fixture(self.fixture)

    def test_bad_probabilities(self):
        for value in (-0.2, 1.2, float("nan"), "0.5", True):
            with self.subTest(value=value):
                self.fixture["samples"] = [value]
                with self.assertRaises(FixtureError):
                    run_fixture(self.fixture)

    def test_bounded_samples(self):
        self.fixture["samples"] = [0.5] * 6
        with self.assertRaises(FixtureError):
            run_fixture(self.fixture)

    def test_is_deterministic_and_does_not_call_network(self):
        with mock.patch("socket.socket", side_effect=AssertionError("network forbidden")):
            self.assertEqual(run_fixture(self.fixture), run_fixture(self.fixture))

    def test_cli_has_no_network_and_no_secrets(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "offline_fixture.py")],
            check=True, capture_output=True, text=True, env={"PATH": ""},
        )
        self.assertEqual(json.loads(result.stdout)["external_api_calls"], 0)


class LiveModeGateTests(unittest.TestCase):
    def test_all_live_modes_refuse_without_both_optins(self):
        for mode in ("test_questions", "tournament", "metaculus_cup"):
            for env, publish in (({}, False), ({}, True), ({"METACULUS_LIVE_WRITES": "APPROVED"}, False)):
                with self.subTest(mode=mode, env=env, publish=publish):
                    with self.assertRaises(ExternalWritesNotApproved):
                        require_explicit_live_approval(mode=mode, publish=publish, environ=env)

    def test_test_questions_requires_explicit_approval(self):
        require_explicit_live_approval(
            mode="test_questions", publish=True,
            environ={"METACULUS_LIVE_WRITES": "APPROVED"},
        )

    def test_scored_tournament_requires_separate_approval(self):
        with self.assertRaises(ExternalWritesNotApproved):
            require_explicit_live_approval(
                mode="tournament", publish=True,
                environ={"METACULUS_LIVE_WRITES": "APPROVED"},
            )
        require_explicit_live_approval(
            mode="tournament", publish=True,
            environ={"METACULUS_LIVE_WRITES": "APPROVED", "METACULUS_SCORED_WRITES": "APPROVED"},
        )


if __name__ == "__main__":
    unittest.main()

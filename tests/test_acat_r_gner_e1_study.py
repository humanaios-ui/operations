"""Regression tests for experiments/acat_r_comparison/study.py (issue #1081, PR #1082/#1083 findings).

These tests pin the harness, not the GNER-E1 runtime. They assert that the study
  * refuses to call the runtime at all unless the computed rubric digest equals the
    ACTIVE registered revision AND that revision is human-accepted with a named
    acceptor; the real registry is currently pending, so the real run BLOCKS;
  * records the unrecoverable predeclared digest beside the computed one;
  * preserves the full reconcile() response per case and rejects empty, truncated,
    reordered or incomplete worker output;
  * pins tools/gner_notification_e0.py beside the runtime and test blobs;
  * runs the unchanged conventional suite before the P1 commitment and probe
    (exercised under a TEST-ONLY accepted registry fixture);
  * keeps the four boolean-boundary cases in PROPOSED_POLICY, separate from the
    contract-derived cases, and scores confirmed_defects as 0 while labels are PENDING;
  * emits an oracle packet whose 30 rows match the committed snapshot;
  * live-probe receipts are sanitized, pin-verified, and hash the consumed response.
"""
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parents[1]
STUDY = REPO / "experiments/acat_r_comparison/study.py"
LIVE_PROBE = REPO / "experiments/acat_r_comparison/live_probe.py"
ORACLE_DIR = REPO / "experiments/acat_r_comparison/oracle"
RECEIPTS = REPO / "experiments/acat_r_comparison/receipts/live_probe_receipts.json"

spec = importlib.util.spec_from_file_location("acat_r_study", STUDY)
study = importlib.util.module_from_spec(spec)
sys.modules["acat_r_study"] = study
spec.loader.exec_module(study)

BOOL_CASES = {"type_canonical_bool_id", "type_lead_bool_id", "type_boolean_pr_in_canonical", "type_lead_bool_pr"}
GIT_AVAILABLE = shutil.which("git") is not None and (REPO / ".git").exists()
REV1 = "6971fd8d2045f301cf31d79a99d5e04bdf101ed7db968d9ee15cacde9043cbf7"
PREDECLARED = "19a182607ccfabb32b679d7d764652f4de4a90556faeb880419af0103ac6cc9a"


def _fake_pins(*_a, **_k):
    return dict(study.PINNED_BLOBS)


def _write_registry(tmpdir, **overrides):
    """Copy the real registry and override fields on the active revision (TEST FIXTURE ONLY)."""
    registry = json.loads(study.RUBRIC_REGISTRY.read_text())
    for r in registry["revisions"]:
        if r["revision"] == registry["active_revision"]:
            r.update(overrides)
    path = pathlib.Path(tmpdir) / "rubric_registry_fixture.json"
    path.write_text(json.dumps(registry, indent=2))
    return path


ACCEPTED_FIXTURE = {"human_accepted": True, "accepted_by": "TEST_FIXTURE_NOT_A_HUMAN_DECISION",
                    "accepted_at": "1970-01-01T00:00:00Z"}


class RubricGateTests(unittest.TestCase):
    def test_real_registry_matches_rev1_but_is_not_accepted(self):
        record = study.enforce_rubric(study.encoded(study.build()), study.load_registry())
        self.assertTrue(record["active_digest_matches"])
        self.assertEqual(record["active_rubric_sha256"], REV1)
        self.assertEqual(record["predeclared_rubric_sha256"], PREDECLARED)
        self.assertFalse(record["predeclared_digest_matches"])
        self.assertFalse(record["active_human_accepted"])
        self.assertIsNone(record["active_accepted_by"])
        self.assertEqual(record["block_reason"], "BLOCKED_RUBRIC_NOT_HUMAN_ACCEPTED")
        self.assertFalse(record["runtime_permitted"])

    def test_registry_revisions_are_unique_and_active_exists(self):
        registry = study.load_registry()
        numbers = [r["revision"] for r in registry["revisions"]]
        self.assertEqual(len(numbers), len(set(numbers)))
        self.assertIn(registry["active_revision"], numbers)
        for r in registry["revisions"]:
            self.assertRegex(r["rubric_sha256"], r"^[0-9a-f]{64}$")
            self.assertIn("status", r)

    def test_accepted_revision_requires_named_acceptor(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_registry(tmp, human_accepted=True, accepted_by=None, accepted_at=None)
            with self.assertRaisesRegex(ValueError, "without accepted_by/accepted_at"):
                study.load_registry(path)

    def test_real_registry_blocks_before_any_runtime_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "ev"
            with mock.patch.object(study, "check_pins", _fake_pins), \
                 mock.patch.object(study, "baseline") as baseline, \
                 mock.patch.object(study, "run_phase") as run_phase:
                result = study.main(out)
            baseline.assert_not_called()
            run_phase.assert_not_called()
            self.assertEqual(result["status"], "BLOCKED_RUBRIC_NOT_HUMAN_ACCEPTED")
            blocked = json.loads((out / "RUBRIC_BLOCKED.json").read_text())
            self.assertEqual(blocked["computed_rubric_sha256"], REV1)
            self.assertEqual(blocked["predeclared_rubric_sha256"], PREDECLARED)
            self.assertEqual(blocked["runtime_calls_made"], 0)
            self.assertEqual(blocked["admission"], "HOLD")
            for name in ("P1_stdout.json", "P2_stdout.json", "report.json", "oracle_packet.json"):
                self.assertFalse((out / name).exists(), name)

    def test_changed_label_blocks_even_when_revision_is_accepted(self):
        tampered = study.build()
        tampered[0]["expected"] = "CONFLICT"
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "ev"
            registry = _write_registry(tmp, **ACCEPTED_FIXTURE)
            with mock.patch.object(study, "check_pins", _fake_pins), \
                 mock.patch.object(study, "build", lambda: tampered), \
                 mock.patch.object(study, "baseline") as baseline, \
                 mock.patch.object(study, "run_phase") as run_phase:
                result = study.main(out, registry_path=registry)
            baseline.assert_not_called()
            run_phase.assert_not_called()
            self.assertEqual(result["status"], "BLOCKED_RUBRIC_DIGEST_MISMATCH")
            self.assertFalse((out / "report.json").exists())

    def test_cli_exit_code_two_when_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(study, "check_pins", _fake_pins):
                self.assertEqual(study.cli(["--run-owned-offline", "--out", str(pathlib.Path(tmp) / "ev")]), 2)


class WorkerOutputTests(unittest.TestCase):
    def setUp(self):
        self.cases = study.build()[:3]
        self.good = study.run_phase(self.cases)

    def test_full_response_preserved(self):
        for row in self.good.rows:
            self.assertIsInstance(row["response"], dict)
            self.assertEqual(row["response"]["state"], row["state"])
        first = self.good.rows[0]["response"]
        for key in ("reason", "head_sha", "conclusion", "evidence_url", "schema", "authority", "execution"):
            self.assertIn(key, first)
        self.assertEqual(len(self.good.record_hashes), 3)

    def test_empty_and_truncated_output_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            study.parse_worker_output(b"", self.cases)
        with self.assertRaisesRegex(ValueError, "truncated"):
            study.parse_worker_output(self.good.raw[:-1], self.cases)
        with self.assertRaisesRegex(ValueError, "unparseable|truncated"):
            study.parse_worker_output(self.good.raw[: len(self.good.raw) // 2] + b"\n", self.cases)

    def test_count_order_and_duplicates_fail_closed(self):
        rows = json.loads(self.good.raw)
        with self.assertRaisesRegex(ValueError, "count, ids or order"):
            study.parse_worker_output(study.encoded(rows[:2]), self.cases)
        with self.assertRaisesRegex(ValueError, "count, ids or order"):
            study.parse_worker_output(study.encoded(list(reversed(rows))), self.cases)
        with self.assertRaisesRegex(ValueError, "count, ids or order"):
            study.parse_worker_output(study.encoded([rows[0], rows[0], rows[2]]), self.cases)

    def test_dropped_response_field_fails_closed(self):
        rows = json.loads(self.good.raw)
        stripped = [{k: v for k, v in r.items() if k != "response"} for r in rows]
        with self.assertRaisesRegex(ValueError, "missing fields"):
            study.parse_worker_output(study.encoded(stripped), self.cases)
        rows[1]["response"] = None
        with self.assertRaisesRegex(ValueError, "response not preserved"):
            study.parse_worker_output(study.encoded(rows), self.cases)

    def test_nonzero_exit_fails_closed(self):
        def failing_runner(*_a, **_k):
            return subprocess.CompletedProcess(args=[], returncode=1, stdout=b"", stderr=b"boom")
        with self.assertRaisesRegex(ValueError, "runtime subprocess failed"):
            study.run_phase(self.cases, runner=failing_runner)


class SourcePinTests(unittest.TestCase):
    def test_imported_module_is_pinned(self):
        self.assertEqual(set(study.PINNED_BLOBS), {"tools/gner_verify_e1.py", "tools/gner_notification_e0.py",
                                                   "tests/test_gner_verify_e1.py"})

    def test_check_pins_hashes_every_pinned_path_and_fails_on_drift(self):
        seen = []

        def runner(cmd, **_k):
            seen.append(cmd[-1])
            rel = pathlib.Path(cmd[-1]).relative_to(study.ROOT).as_posix()
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=study.PINNED_BLOBS[rel] + "\n", stderr="")
        self.assertEqual(study.check_pins(runner=runner), study.PINNED_BLOBS)
        self.assertEqual(len(seen), 3)

        def drifted(cmd, **_k):
            return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="0" * 40 + "\n", stderr="")
        with self.assertRaisesRegex(ValueError, "pinned original source changed"):
            study.check_pins(runner=drifted)

    @unittest.skipUnless(GIT_AVAILABLE, "git checkout required")
    def test_working_tree_matches_pins(self):
        self.assertEqual(study.check_pins(), study.PINNED_BLOBS)

    def test_live_probe_pins_match_study_pins_and_verify_without_git(self):
        pspec = importlib.util.spec_from_file_location("acat_r_live_probe", LIVE_PROBE)
        probe = importlib.util.module_from_spec(pspec)
        pspec.loader.exec_module(probe)  # performs the pin check at import; SystemExit on drift
        for rel, blob in probe.PINNED_BLOBS.items():
            self.assertEqual(blob, study.PINNED_BLOBS[rel])
        self.assertTrue(all(v["verified"] for v in probe.SOURCE_PINS.values()))
        self.assertEqual(probe.git_blob_sha1(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")


class EvidenceClassTests(unittest.TestCase):
    def test_manifest_covers_all_cases_and_isolates_proposed_policy(self):
        cases = study.build()
        manifest = study.load_evidence_classes(cases)
        proposed = {cid for cid, row in manifest["cases"].items() if row["evidence_class"] == "PROPOSED_POLICY"}
        self.assertEqual(proposed, BOOL_CASES)
        self.assertEqual(manifest["cases"]["unsupported_conclusion"]["evidence_class"], "IMPLEMENTATION_DERIVED")
        counts = {name: sum(1 for r in manifest["cases"].values() if r["evidence_class"] == name)
                  for name in study.EVIDENCE_CLASS_NAMES}
        self.assertEqual(counts, {"CONTRACT_EXPLICIT": 11, "IMPLEMENTATION_DERIVED": 15, "PROPOSED_POLICY": 4})

    def test_incomplete_manifest_fails_closed(self):
        cases = study.build()
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            manifest = json.loads(study.EVIDENCE_CLASSES.read_text())
            manifest["cases"].pop("valid_failure")
            json.dump(manifest, fh)
        with self.assertRaisesRegex(ValueError, "exactly the 30 case ids"):
            study.load_evidence_classes(cases, path=fh.name)


@unittest.skipUnless(GIT_AVAILABLE, "git checkout required for pin check")
class EndToEndUnderAcceptedFixtureTests(unittest.TestCase):
    """Full path exercised under a TEST-ONLY accepted registry; not a human decision."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.out = pathlib.Path(cls.tmp) / "ev"
        cls.order = []
        registry = _write_registry(cls.tmp, **ACCEPTED_FIXTURE)
        real_baseline, real_run_phase = study.baseline, study.run_phase

        def baseline(*a, **k):
            cls.order.append("baseline")
            return real_baseline(*a, **k)

        def run_phase(cases, *a, **k):
            cls.order.append(f"run_phase:{len(cases)}")
            return real_run_phase(cases, *a, **k)
        with mock.patch.object(study, "baseline", baseline), mock.patch.object(study, "run_phase", run_phase):
            cls.report = study.main(cls.out, registry_path=registry)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_conventional_suite_runs_before_p1(self):
        self.assertEqual(self.order, ["baseline", "run_phase:8", "run_phase:30", "run_phase:30"])
        self.assertTrue(self.report["conventional_baseline"]["ran_before_P1"])

    def test_commitment_written_before_p1_output(self):
        commit = json.loads((self.out / "P1_COMMIT.json").read_text())
        self.assertIn("imported_module_sha256", commit)
        self.assertEqual(commit["pinned_git_blobs"], study.PINNED_BLOBS)
        self.assertEqual(commit["rubric_revision"], 1)
        self.assertLessEqual((self.out / "P1_COMMIT.json").stat().st_mtime_ns,
                             (self.out / "P1_stdout.json").stat().st_mtime_ns)

    def test_replay_is_computed_not_asserted(self):
        p3 = self.report["P3"]
        self.assertTrue(p3["byte_identical"] and p3["record_hashes_identical"] and p3["id_order_identical"])
        self.assertEqual(p3["record_count"], 30)
        self.assertEqual((self.out / "P2_stdout.json").read_bytes(), (self.out / "P3_stdout.json").read_bytes())

    def test_disagreements_are_only_proposed_policy_and_nothing_is_confirmed(self):
        self.assertEqual(set(self.report["proposed_policy_disagreements"]), BOOL_CASES)
        self.assertEqual(self.report["contract_derived_disagreements"], [])
        self.assertEqual(self.report["confirmed_defects"], 0)
        self.assertEqual(self.report["acatr_detection_advantage_on_equal_inputs"], 0)
        self.assertEqual(self.report["acatr_equal"]["detected"], self.report["conventional_equal"]["detected"])
        self.assertEqual(self.report["admission"], "HOLD")
        self.assertFalse(self.report["predeclared_digest_matches"])
        self.assertEqual(self.report["rubric_accepted_by"], ACCEPTED_FIXTURE["accepted_by"])

    def test_oracle_packet_has_30_pending_rows_and_matches_snapshot(self):
        packet = json.loads((self.out / "oracle_packet.json").read_text())
        snapshot = json.loads((ORACLE_DIR / "oracle_packet.json").read_text())
        self.assertEqual(len(packet["cases"]), 30)
        self.assertTrue(all(r["reviewer_decision"] == "PENDING" for r in packet["cases"]))
        self.assertEqual(packet["confirmed_defects"], 0)
        self.assertEqual(packet["cases"], snapshot["cases"])
        generated = (self.out / "ORACLE_REVIEW_PACKET.md").read_text().replace("human_accepted=True", "human_accepted=False")
        self.assertEqual(generated, (ORACLE_DIR / "ORACLE_REVIEW_PACKET.md").read_text())


class LiveProbeReceiptTests(unittest.TestCase):
    def test_receipts_are_sanitized_pin_verified_and_hash_consumed_bytes(self):
        receipts = json.loads(RECEIPTS.read_text())
        text = RECEIPTS.read_text()
        self.assertFalse(receipts["credential_logged"])
        for marker in ("Bearer ", "ghp_", "gho_", "github_pat_"):
            self.assertNotIn(marker, text)
        self.assertTrue(receipts["entry_point_verified_unmodified"])
        for rel, blob in study.PINNED_BLOBS.items():
            if rel in receipts["source_pins"]:
                self.assertEqual(receipts["source_pins"][rel]["observed_git_blob"], blob)
                self.assertTrue(receipts["source_pins"][rel]["verified"])
        by_id = {p["probe_id"]: p for p in receipts["probes"]}
        self.assertEqual(by_id["bool_lead_run_id_reachability"]["verify_lead"]["outcome"], "DENIED")
        self.assertFalse(by_id["bool_lead_run_id_reachability"]["network_call_made"])
        self.assertEqual(by_id["nonexistent_run_expiry_behaviour"]["verify_lead"]["outcome"], "DENIED")
        self.assertEqual(by_id["nonexistent_run_expiry_behaviour"]["consumed_response"]["http_status"], 404)
        self.assertEqual(by_id["qb_failure_valid_with_pr"]["verify_lead"]["result"]["state"], "CANONICAL_VERIFIED")
        for p in receipts["probes"]:
            if p["verify_lead"]["outcome"] == "RETURNED":
                consumed = p["consumed_response"]
                self.assertRegex(consumed["response_sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(consumed["authorization_header_present"])
                self.assertTrue(consumed["request_url"].startswith("https://api.github.com/repos/humanaios-ui/operations/actions/runs/"))
                self.assertEqual(consumed["id_json_type"], "int")
                self.assertEqual(consumed["pull_request_number_json_types"], ["int"])
                self.assertTrue(p["consumed_matches_independent_fetch"])


class CliTests(unittest.TestCase):
    def test_unknown_arguments_rejected(self):
        with self.assertRaises(SystemExit):
            study.cli([])
        with self.assertRaises(SystemExit):
            study.cli(["--run-owned-offline", "--bogus"])


if __name__ == "__main__":
    unittest.main()

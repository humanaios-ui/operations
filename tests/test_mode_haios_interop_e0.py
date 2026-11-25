"""MODE x HumanAIOS E0: synthetic trace review and actual HumanAIOS boundaries."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from experiments.mode_haios_interop_e0 import TraceDenied, assess_trace
from experiments.human_objective_e1 import recommend
from tools.verified_receipts import (
    ReceiptRequirement, VerifiedReceiptResolver, build_receipt_chain_for_testing,
)
from agent_coordination import acat_loop

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "experiments/mode_haios_oct24_synthetic.json").read_text())
URA = json.loads((ROOT / "experiments/e1_ura_fixture.json").read_text())


class MODEInteropE0Tests(unittest.TestCase):
    def case(self):
        return deepcopy(FIXTURE)

    def test_oct24_shape_replay_stops_without_execution(self):
        report = assess_trace(self.case())
        self.assertEqual(report["step_count"], 3)
        self.assertEqual(report["stop_state"], "UNSUPPORTED_READ_FILE")
        self.assertEqual(report["steps"][1]["target"], "misc")
        for field in ("runtime_behavior_verified", "rp_action_signature_verified",
                      "rp_claim_evaluation_verified", "objective_completed", "learning_admitted"):
            self.assertFalse(report[field])
        self.assertEqual(report["authority_effect"], "NONE")
        self.assertEqual(report["execution_effect"], "NONE")
        self.assertEqual(report["trace_sha256"], assess_trace(self.case())["trace_sha256"])

    def test_unseen_second_directory_refused(self):
        case = self.case()
        case["steps"][1]["target"] = "hidden"
        with self.assertRaises(TraceDenied):
            assess_trace(case)

    def test_unseen_file_refused(self):
        case = self.case()
        case["steps"][2]["target"] = "misc/passwords.txt"
        with self.assertRaises(TraceDenied):
            assess_trace(case)

    def test_path_traversal_absolute_and_windows_paths_denied(self):
        for path in ("../private", "misc/../secrets", "/etc", "C:\\secret", "\\\\server\\share", "misc//secret"):
            with self.subTest(path=path):
                case = self.case()
                case["steps"][1]["target"] = path
                with self.assertRaises(TraceDenied):
                    assess_trace(case)

    def test_host_mutation_symlink_and_claimed_file_read_denied(self):
        bad = self.case()
        bad["steps"][2]["action"] = "WRITE_FILE"
        with self.assertRaises(TraceDenied):
            assess_trace(bad)
        bad = self.case()
        bad["steps"][1]["entries"][0]["kind"] = "SYMLINK"
        with self.assertRaises(TraceDenied):
            assess_trace(bad)
        bad = self.case()
        bad["steps"][2]["state"] = "REPORTED_OBSERVED"
        with self.assertRaises(TraceDenied):
            assess_trace(bad)

    def test_action_or_authority_laundering_denied(self):
        for field, value in (("rp_signature_verified", True), ("learning_admitted", True),
                             ("authority_effect", "APPROVED"), ("execution", "ENABLED")):
            with self.subTest(field=field):
                case = self.case()
                case["steps"][1][field] = value
                with self.assertRaises(TraceDenied):
                    assess_trace(case)

    def test_step_sequence_and_missing_provenance_denied(self):
        case = self.case()
        case["steps"][1]["ordinal"] = 1
        with self.assertRaises(TraceDenied):
            assess_trace(case)
        case = self.case()
        case["steps"][1]["evidence_ref"] = None
        with self.assertRaises(TraceDenied):
            assess_trace(case)

    def test_supplied_live_state_denied(self):
        case = self.case()
        case["origin"] = "MODE_LIVE_CONFIRMED"
        with self.assertRaises(TraceDenied):
            assess_trace(case)


    def test_unhashable_entry_kinds_raise_trace_denied(self):
        for kind in ([], {}, None, 42):
            with self.subTest(kind=kind):
                case = self.case()
                case["steps"][1]["entries"][0]["kind"] = kind
                with self.assertRaises(TraceDenied):
                    assess_trace(case)

    def test_conflicting_root_relisting_denies_stale_child(self):
        case = self.case()
        read = deepcopy(case["steps"][2])
        read["ordinal"] = 4
        relist = deepcopy(case["steps"][0])
        relist["ordinal"] = 3
        for entry in relist["entries"]:
            if entry["name"] == "misc":
                entry["kind"] = "FILE"
        case["steps"] = case["steps"][:2] + [relist, read]
        with self.assertRaises(TraceDenied):
            assess_trace(case)

    def test_removed_root_child_invalidates_nested_file_observation(self):
        case = self.case()
        read = deepcopy(case["steps"][2])
        read["ordinal"] = 4
        relist = deepcopy(case["steps"][0])
        relist["ordinal"] = 3
        relist["entries"] = [e for e in relist["entries"] if e["name"] != "misc"]
        case["steps"] = case["steps"][:2] + [relist, read]
        with self.assertRaises(TraceDenied):
            assess_trace(case)

    def test_actual_e1_resource_bridge_preserves_review_only(self):
        report = recommend("Find training certification resources useful for HumanAIOS", deepcopy(URA["records"]))
        self.assertEqual(report["state"], "SYNTHETIC_REVIEW_CANDIDATE")
        self.assertEqual(report["candidate"]["provenance"], "SUPPLIED_UNVERIFIED_SYNTHETIC")
        self.assertEqual(report["authority"], "NONE")
        self.assertEqual(report["execution"], "DISABLED")
        self.assertEqual(report["eligibility"], "UNASSESSED")
        self.assertEqual(report["hmbm_effect"], "NONE")

    def test_e1_rejects_candidate_claiming_authority(self):
        records = deepcopy(URA["records"])
        records[0]["authorization"] = "GRANTED"
        report = recommend("Find training certification resources useful for HumanAIOS", records)
        self.assertEqual(report["rejected_count"], 1)
        self.assertIsNone(report["candidate"])

    def test_actual_receipt_resolver_requires_exact_pinned_action_and_scope(self):
        row = {"type": "RECEIPT_VERIFIED", "receipt_id": "mode-synthetic-1",
               "receipt_type": "MODE_RP_ACTION", "subject": "objective:MODE-OCT24-SYNTHETIC-REPLAY",
               "action": "LIST_DIRECTORY:.", "scope": "synthetic:workspace",
               "issuer": "synthetic-external-reviewer", "authority_scope": "NONE",
               "verification_status": "VERIFIED", "verification_strength": "OBSERVED",
               "verification_method": "BRIDGE_EVENT_HASH_CHAIN", "evidence_ref": "synthetic:root-list",
               "one_time": True}
        events, pinned = build_receipt_chain_for_testing([row])
        resolver = VerifiedReceiptResolver(events, pinned)
        requirement = ReceiptRequirement(receipt_type="MODE_RP_ACTION", subject=row["subject"],
                                         action=row["action"], scope=row["scope"],
                                         issuer=row["issuer"], authority_scope="NONE")
        self.assertTrue(resolver.resolve(row["receipt_id"], requirement).valid)
        wrong = ReceiptRequirement(receipt_type="MODE_RP_ACTION", subject=row["subject"],
                                   action="READ_FILE:misc/start.py", scope=row["scope"])
        self.assertEqual(resolver.resolve(row["receipt_id"], wrong).reason, "ACTION_MISMATCH")
        stale = VerifiedReceiptResolver(events, "0" * 64)
        self.assertFalse(stale.resolve(row["receipt_id"], requirement).valid)
        # Local synthetic hash integrity does not authenticate MODE RP.
        self.assertFalse(assess_trace(self.case())["rp_action_signature_verified"])

    def test_actual_acat_self_report_cannot_admit_learning(self):
        scores = {"truth": 70, "service": 80, "harm": 60,
                  "autonomy": 75, "value": 65, "humility": 55}
        p1 = acat_loop.entry("issue:986", "modeinterop", "MODE", "VERIFY", scores, 75, "NONE", "a" * 40)
        p2 = acat_loop.exposure("issue:986", "modeinterop", "UNKNOWN", "CI_REVIEW",
                                 ["https://github.com/humanaios-ui/operations/pull/987"])
        p3 = acat_loop.exit_record("issue:986", "modeinterop", "MODE", scores, "NONE")
        rows = [{"actor": who, "created_at": f"2026-10-22T1{n}:00:00Z",
                 "updated_at": f"2026-10-22T1{n}:00:00Z", "comment_id": n,
                 "record": record} for n, (who, record) in enumerate(
                     (("mode-agent", p1), ("independent-reviewer", p2), ("mode-agent", p3)), start=1)]
        result = acat_loop.summary(acat_loop.read_history("issue:986", "modeinterop", rows))
        self.assertEqual(result["evidence_validity"], "AWAITING_INDEPENDENT_REF_VERIFICATION")
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertIsNone(result["brier_forecast_vs_rater_claim"])
        self.assertEqual(acat_loop.learning_report(rows)["status"], "INSUFFICIENT_BASELINE")


if __name__ == "__main__":
    unittest.main()

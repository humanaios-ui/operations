import unittest

from tools.hiae_assurance import (
    DEMO_KEYS,
    AssessmentRequest,
    AssignmentError,
    HistoryEntry,
    Reviewer,
    ReceiptError,
    check_assignment,
    demo_reviewers,
    issue_receipt,
    make_evidence,
    negative_cases,
    run_synthetic_transaction,
    select_reviewer,
    verify_receipt,
    DEMO_PROTOCOL,
)

ISSUER = "issuer:humanaios-operations"
ISSUER_KEYS = {ISSUER: DEMO_KEYS[ISSUER]}
OBSERVER_KEYS = {k: v for k, v in DEMO_KEYS.items() if k.startswith("observer:")}


def request(**overrides):
    base = dict(
        request_id="req-t",
        customer_id="cust-1",
        customer_org="cust-org-1",
        risk_class="low",
        subject_id="subject-T",
    )
    base.update(overrides)
    return AssessmentRequest(**base)


class NeutralAssignmentTests(unittest.TestCase):
    def test_same_inputs_give_same_reviewer(self):
        a = select_reviewer(request(), demo_reviewers(), [], "seed-x")
        b = select_reviewer(request(), demo_reviewers(), [], "seed-x")
        self.assertEqual(a, b)

    def test_customer_cannot_name_reviewer(self):
        for key in ("preferred_reviewer", "reviewer_id", "reviewer"):
            with self.subTest(key=key):
                with self.assertRaises(AssignmentError):
                    select_reviewer(request(fields={key: "rev-2"}), demo_reviewers(), [], "seed")

    def test_declared_conflict_excluded(self):
        a = select_reviewer(request(), demo_reviewers(), [], "seed")
        self.assertNotEqual(a.reviewer_id, "rev-3")
        self.assertNotIn("rev-3", a.eligible_ids)

    def test_same_org_excluded(self):
        a = select_reviewer(request(customer_org="org-alpha"), demo_reviewers(), [], "seed")
        self.assertNotEqual(a.reviewer_id, "rev-1")

    def test_unqualified_risk_class_excluded(self):
        reviewers = [
            Reviewer("only-low", "org-x", frozenset({"low"})),
            Reviewer("med", "org-y", frozenset({"medium"})),
        ]
        a = select_reviewer(request(risk_class="medium"), reviewers, [], "seed")
        self.assertEqual(a.reviewer_id, "med")

    def test_prior_involvement_with_subject_excluded(self):
        history = [HistoryEntry("req-0", "rev-1", "subject-T")]
        a = select_reviewer(request(), demo_reviewers(), history, "seed")
        self.assertNotEqual(a.reviewer_id, "rev-1")

    def test_inactive_or_invalid_credential_excluded(self):
        reviewers = [
            Reviewer("inactive", "org-x", frozenset({"low"}), active=False),
            Reviewer("nocred", "org-y", frozenset({"low"}), credential_valid=False),
            Reviewer("ok", "org-z", frozenset({"low"})),
        ]
        a = select_reviewer(request(), reviewers, [], "seed")
        self.assertEqual(a.reviewer_id, "ok")

    def test_no_eligible_reviewer_raises(self):
        with self.assertRaises(AssignmentError):
            select_reviewer(request(risk_class="high"), demo_reviewers(), [], "seed")

    def test_rotation_prefers_least_loaded(self):
        history = [HistoryEntry(f"r{i}", "rev-1", f"s{i}") for i in range(3)]
        a = select_reviewer(request(), demo_reviewers(), history, "seed")
        self.assertNotEqual(a.reviewer_id, "rev-1")

    def test_seed_is_required(self):
        with self.assertRaises(AssignmentError):
            select_reviewer(request(), demo_reviewers(), [], "")

    def test_check_detects_substituted_reviewer(self):
        req = request()
        real = select_reviewer(req, demo_reviewers(), [], "seed")
        other = "rev-2" if real.reviewer_id != "rev-2" else "rev-1"
        forged = type(real)(**{**real.to_dict(), "reviewer_id": other})
        problems = check_assignment(forged, req, demo_reviewers(), [])
        self.assertTrue(problems)

    def test_check_detects_forced_conflicted_reviewer(self):
        req = request()
        real = select_reviewer(req, demo_reviewers(), [], "seed")
        forced = type(real)(**{**real.to_dict(), "reviewer_id": "rev-3"})
        problems = check_assignment(forced, req, demo_reviewers(), [])
        self.assertTrue(any("not the assigned reviewer" in p for p in problems))

    def test_check_passes_for_honest_assignment(self):
        req = request()
        real = select_reviewer(req, demo_reviewers(), [], "seed")
        self.assertEqual(check_assignment(real, req, demo_reviewers(), []), [])


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.assignment, self.receipt, self.problems = run_synthetic_transaction()

    def test_happy_path_verifies(self):
        self.assertEqual(self.problems, [])

    def test_receipt_pins_versions(self):
        for key in ("protocol_version", "acat_version", "model_version", "commit_sha"):
            self.assertIn(key, self.receipt)
            self.assertTrue(self.receipt[key])

    def test_tampered_finding_fails_signature(self):
        tampered = dict(self.receipt)
        tampered["findings"] = ["Changed after signing"]
        problems = verify_receipt(tampered, self.assignment, ISSUER_KEYS, OBSERVER_KEYS)
        self.assertTrue(any("signature" in p for p in problems))

    def test_wrong_issuer_key_fails(self):
        problems = verify_receipt(
            self.receipt, self.assignment, {ISSUER: b"wrong-key"}, OBSERVER_KEYS
        )
        self.assertTrue(any("signature" in p for p in problems))

    def test_receipt_for_other_reviewer_rejected(self):
        other = "rev-2" if self.assignment.reviewer_id != "rev-2" else "rev-1"
        body = {k: v for k, v in self.receipt.items() if k not in ("signature", "receipt_version")}
        body["reviewer_id"] = other
        receipt = issue_receipt(body, ISSUER, DEMO_KEYS[ISSUER])
        problems = verify_receipt(receipt, self.assignment, ISSUER_KEYS, OBSERVER_KEYS)
        self.assertTrue(any("not the assigned reviewer" in p for p in problems))

    def test_forged_evidence_rejected(self):
        forged = dict(self.receipt)
        ev = dict(forged["evidence"][0])
        ev["content_sha256"] = "0" * 64
        forged["evidence"] = [ev] + list(forged["evidence"][1:])
        problems = verify_receipt(forged, self.assignment, ISSUER_KEYS, OBSERVER_KEYS)
        self.assertTrue(any("observer signature invalid" in p for p in problems))

    def test_unknown_observer_rejected(self):
        problems = verify_receipt(self.receipt, self.assignment, ISSUER_KEYS, {})
        self.assertTrue(any("unknown observer" in p for p in problems))

    def test_overclaim_rejected_at_issue_time(self):
        body = {
            **DEMO_PROTOCOL,
            "request_id": "r", "reviewer_id": "rev-1", "subject_id": "s",
            "measured": ["checked"], "not_measured": ["everything else"],
            "findings": ["The system is certified safe"],
            "evidence": [], "issued_at": "t", "issuer_id": ISSUER,
        }
        with self.assertRaises(ReceiptError):
            issue_receipt(body, ISSUER, DEMO_KEYS[ISSUER])

    def test_word_boundary_match_only(self):
        # "unsafe" must not trip the "safe" rule; the scanner is whole-word.
        body = {
            **DEMO_PROTOCOL,
            "request_id": "r", "reviewer_id": "rev-1", "subject_id": "s",
            "measured": ["checked"], "not_measured": ["long-horizon behaviour"],
            "findings": ["Unsafe behaviour was not observed"],
            "evidence": [], "issued_at": "t", "issuer_id": ISSUER,
        }
        issue_receipt(body, ISSUER, DEMO_KEYS[ISSUER])

    def test_missing_field_rejected(self):
        body = {k: v for k, v in self.receipt.items() if k not in ("signature", "receipt_version", "acat_version")}
        with self.assertRaises(ReceiptError):
            issue_receipt(body, ISSUER, DEMO_KEYS[ISSUER])

    def test_evidence_item_is_observer_signed(self):
        item = make_evidence("ev-x", "observer:rater-a", DEMO_KEYS["observer:rater-a"], b"abc")
        self.assertIn("observer_signature", item)
        self.assertEqual(len(item["content_sha256"]), 64)


class NegativeSuiteTests(unittest.TestCase):
    def test_every_negative_case_is_rejected(self):
        results = negative_cases()
        self.assertEqual(
            set(results),
            {
                "customer_selected_reviewer",
                "falsified_receipt",
                "forged_evidence",
                "unauthorized_reviewer",
                "conflicted_assignment",
                "overclaim_rejected",
            },
        )
        for name, rejected in results.items():
            with self.subTest(case=name):
                self.assertTrue(rejected)


if __name__ == "__main__":
    unittest.main()

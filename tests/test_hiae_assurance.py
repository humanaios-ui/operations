import json
import tempfile
import unittest

from tools.hiae_assurance import (
    DEMO_ISSUER,
    DEMO_KEYS,
    DEMO_PROTOCOL,
    AssessmentRequest,
    AssignmentError,
    HistoryEntry,
    ReceiptError,
    Reviewer,
    SpecLoadFailed,
    sign_payload,
    check_assignment,
    demo_reviewers,
    issue_receipt,
    make_evidence,
    negative_cases,
    run_synthetic_transaction,
    select_reviewer,
    verify_receipt,
    write_report,
    _observer_keys,
    _reviewer_keys,
    _valid_transaction,
)

ISSUER_KEYS = {DEMO_ISSUER: DEMO_KEYS[DEMO_ISSUER]}


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


def _verify(receipt, assignment):
    return verify_receipt(receipt, assignment, ISSUER_KEYS, _observer_keys(), _reviewer_keys())


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
        self.assertTrue(check_assignment(forged, req, demo_reviewers(), [], trusted_seed="seed"))

    def test_check_detects_forced_conflicted_reviewer(self):
        req = request()
        real = select_reviewer(req, demo_reviewers(), [], "seed")
        forced = type(real)(**{**real.to_dict(), "reviewer_id": "rev-3"})
        problems = check_assignment(forced, req, demo_reviewers(), [], trusted_seed="seed")
        self.assertTrue(any("not the assigned reviewer" in p for p in problems))

    def test_check_detects_substituted_seed_even_when_self_consistent(self):
        # An attacker picks a seed whose recomputation yields their chosen reviewer,
        # and records that seed. The trusted seed must still win.
        req = request()
        attacker_seed = "seed-attacker"
        forged = select_reviewer(req, demo_reviewers(), [], attacker_seed)
        problems = check_assignment(forged, req, demo_reviewers(), [], trusted_seed="seed")
        self.assertTrue(any("trusted rotation record" in p for p in problems))

    def test_check_passes_for_honest_assignment(self):
        req = request()
        real = select_reviewer(req, demo_reviewers(), [], "seed")
        self.assertEqual(check_assignment(real, req, demo_reviewers(), [], trusted_seed="seed"), [])


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.request, self.assignment, self.receipt = _valid_transaction()

    def test_happy_path_verifies(self):
        _, _, problems = run_synthetic_transaction()
        self.assertEqual(problems, [])

    def test_receipt_pins_versions(self):
        for key in ("protocol_version", "acat_version", "model_version", "commit_sha"):
            self.assertIn(key, self.receipt)
            self.assertTrue(self.receipt[key])

    def test_tampered_finding_fails_signature(self):
        tampered = dict(self.receipt)
        tampered["findings"] = ["Changed after signing"]
        self.assertTrue(any("signature" in p for p in _verify(tampered, self.assignment)))

    def test_wrong_issuer_key_fails(self):
        problems = verify_receipt(
            self.receipt, self.assignment, {DEMO_ISSUER: b"wrong-key"}, _observer_keys(), _reviewer_keys()
        )
        self.assertTrue(any("signature" in p for p in problems))

    def test_receipt_for_other_reviewer_rejected(self):
        other = "rev-2" if self.assignment.reviewer_id != "rev-2" else "rev-1"
        receipt = issue_receipt(
            {**{k: v for k, v in self.receipt.items() if k not in ("signature", "reviewer_signature", "receipt_version")},
             "reviewer_id": other},
            DEMO_ISSUER, DEMO_KEYS[DEMO_ISSUER], DEMO_KEYS[f"reviewer:{other}"],
        )
        self.assertTrue(any("not the assigned reviewer" in p for p in _verify(receipt, self.assignment)))

    def test_receipt_signed_with_wrong_reviewer_key_rejected(self):
        receipt = issue_receipt(
            {k: v for k, v in self.receipt.items() if k not in ("signature", "reviewer_signature", "receipt_version")},
            DEMO_ISSUER, DEMO_KEYS[DEMO_ISSUER], b"not-the-reviewer-key",
        )
        self.assertTrue(any("reviewer signature does not verify" in p for p in _verify(receipt, self.assignment)))

    def test_missing_reviewer_signature_rejected(self):
        receipt = {k: v for k, v in self.receipt.items() if k != "reviewer_signature"}
        # re-issue the issuer signature so only the reviewer check fails
        receipt["signature"] = {
            "issuer_id": DEMO_ISSUER,
            "alg": "HMAC-SHA256",
            "value": sign_payload(DEMO_KEYS[DEMO_ISSUER], receipt),
        }
        self.assertTrue(any("reviewer signature" in p for p in _verify(receipt, self.assignment)))

    def test_forged_evidence_rejected(self):
        forged = json.loads(json.dumps(self.receipt))
        forged["evidence"][0]["content_sha256"] = "0" * 64
        self.assertTrue(any("observer signature invalid" in p for p in _verify(forged, self.assignment)))

    def test_evidence_bound_to_other_request_rejected(self):
        other_ctx = {
            "request_id": "req-other", "subject_id": self.request.subject_id,
            "protocol_id": DEMO_PROTOCOL["protocol_id"], "protocol_version": DEMO_PROTOCOL["protocol_version"],
            "observed_at": "2026-10-10T00:00:00Z",
        }
        item = make_evidence("ev-x", "observer:rater-a", DEMO_KEYS["observer:rater-a"], b"abc", other_ctx)
        body = {k: v for k, v in self.receipt.items() if k not in ("signature", "reviewer_signature", "receipt_version")}
        body["evidence"] = [item]
        receipt = issue_receipt(body, DEMO_ISSUER, DEMO_KEYS[DEMO_ISSUER], DEMO_KEYS[f"reviewer:{self.assignment.reviewer_id}"])
        self.assertTrue(any("different request, subject or protocol" in p for p in _verify(receipt, self.assignment)))

    def test_unknown_observer_rejected(self):
        problems = verify_receipt(self.receipt, self.assignment, ISSUER_KEYS, {}, _reviewer_keys())
        self.assertTrue(any("unknown observer" in p for p in problems))

    def test_unsupported_receipt_version_rejected_before_other_fields(self):
        future = dict(self.receipt)
        future["receipt_version"] = "9.0.0"
        problems = _verify(future, self.assignment)
        self.assertEqual(len(problems), 1)
        self.assertIn("unsupported receipt_version", problems[0])

    def test_overclaim_rejected_at_issue_time(self):
        body = {
            **DEMO_PROTOCOL,
            "request_id": "r", "reviewer_id": "rev-1", "subject_id": "s",
            "measured": ["checked"], "not_measured": ["everything else"],
            "findings": ["The system is certified safe"],
            "evidence": [], "issued_at": "t", "issuer_id": DEMO_ISSUER,
        }
        with self.assertRaises(ReceiptError):
            issue_receipt(body, DEMO_ISSUER, DEMO_KEYS[DEMO_ISSUER], DEMO_KEYS["reviewer:rev-1"])

    def test_word_boundary_match_only(self):
        # "unsafe" must not trip the "safe" rule; the scanner is whole-word.
        body = {
            **DEMO_PROTOCOL,
            "request_id": "r", "reviewer_id": "rev-1", "subject_id": "s",
            "measured": ["checked"], "not_measured": ["long-horizon behaviour"],
            "findings": ["Unsafe behaviour was not observed"],
            "evidence": [], "issued_at": "t", "issuer_id": DEMO_ISSUER,
        }
        issue_receipt(body, DEMO_ISSUER, DEMO_KEYS[DEMO_ISSUER], DEMO_KEYS["reviewer:rev-1"])

    def test_missing_field_rejected(self):
        body = {k: v for k, v in self.receipt.items()
                if k not in ("signature", "reviewer_signature", "receipt_version", "acat_version")}
        with self.assertRaises(ReceiptError):
            issue_receipt(body, DEMO_ISSUER, DEMO_KEYS[DEMO_ISSUER], DEMO_KEYS["reviewer:rev-1"])

    def test_evidence_requires_context(self):
        with self.assertRaises(ReceiptError):
            make_evidence("ev-y", "observer:rater-a", DEMO_KEYS["observer:rater-a"], b"abc", {"request_id": "r"})


class ReportTests(unittest.TestCase):
    def test_report_written_when_directory_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_report({"passed": True}, tmp)
            with open(path, encoding="utf-8") as fh:
                self.assertEqual(json.load(fh), {"passed": True})

    def test_missing_report_directory_raises_spec_load_failed(self):
        with self.assertRaises(SpecLoadFailed):
            write_report({"passed": True}, "/nonexistent/hiae-report-dir")


class NegativeSuiteTests(unittest.TestCase):
    def test_every_negative_case_is_rejected(self):
        results = negative_cases()
        self.assertEqual(
            set(results),
            {
                "customer_selected_reviewer",
                "falsified_receipt",
                "forged_evidence",
                "evidence_replayed_to_other_request",
                "unauthorized_reviewer",
                "wrong_reviewer_named",
                "conflicted_assignment",
                "substituted_rotation_seed",
                "unsupported_receipt_version",
                "overclaim_rejected",
            },
        )
        for name, rejected in results.items():
            with self.subTest(case=name):
                self.assertTrue(rejected)


if __name__ == "__main__":
    unittest.main()

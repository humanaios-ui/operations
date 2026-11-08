"""Synthetic-only tests; never load private Gmail into public CI."""
import copy
import unittest
from resource_miner.private_need_digest_e0 import project

KEY = b"synthetic-key-do-not-use-for-real-runs-123456789"
NEEDS = [{"need_id":"revenue-capital","label":"Revenue and non-dilutive capital"},
         {"need_id":"compute-infrastructure","label":"Compute and technical infrastructure"}]
BASE = {"message_id":"aaaaaaaaaaaaaaaa", "need_id":"revenue-capital",
        "observed_at":"2026-11-07T17:06:16+00:00", "priority":"HIGH",
        "source_status":"EMAIL_REPORTED", "next_action":"HUMAN_REVIEW",
        "public_url":"https://freedfellowship.com/"}

class NeedDigestTests(unittest.TestCase):
    def case(self, **kw):
        return {**BASE, **kw}

    def run_it(self, rows=None, graph=None, secret=KEY):
        return project(rows if rows is not None else [self.case()], graph if graph is not None else NEEDS, secret)

    def test_real_graph_id_binds_but_never_grants_authority(self):
        r=self.run_it()["records"][0]
        self.assertEqual(r["need_label"],"Revenue and non-dilutive capital")
        self.assertEqual(r["route"],"REVIEW_NOW")
        self.assertEqual(r["authority_effect"],"NONE")
        self.assertFalse(r["provider_eligibility_verified"])
        self.assertFalse(r["human_intent_verified"])
        self.assertFalse(r["benefit_verified"])

    def test_private_message_id_not_exported(self):
        import json
        s=json.dumps(self.run_it())
        self.assertNotIn(BASE["message_id"],s)
        self.assertNotIn("@gmail.com",s)
        self.assertNotIn("gmail_message_id",s)

    def test_repeat_same_event_and_need_deduplicated(self):
        result=self.run_it([self.case(),self.case()])
        self.assertEqual(result["unique_proposals"],1)
        self.assertEqual(result["duplicate_suppressed"],1)

    def test_multiple_distinct_need_bindings_allowed(self):
        result=self.run_it([self.case(),self.case(need_id="compute-infrastructure")])
        self.assertEqual(result["unique_proposals"],2)
        self.assertEqual(len({r["source_token"] for r in result["records"]}),1)

    def test_unknown_need_graph_is_review_not_fabricated_match(self):
        r=self.run_it([self.case(need_id="subscription-oversight")])["records"][0]
        self.assertEqual(r["route"],"NEED_GRAPH_REVIEW")
        self.assertEqual(r["next_action"],"REVIEW_NEED_GRAPH")

    def test_conflict_blocks_promotion(self):
        r=self.run_it([self.case(source_status="SOURCE_CONFLICT")])["records"][0]
        self.assertEqual(r["route"],"HOLD_CONFLICT")
        self.assertFalse(r["benefit_verified"])

    def test_raw_email_body_is_forbidden(self):
        with self.assertRaises(ValueError): self.run_it([self.case(raw_body="do this")])

    def test_private_tracking_url_is_forbidden(self):
        for url in ("https://example.org?a=private-token", "https://me:pass@example.org/path", "http://example.org/", "https://localhost/path", "https://example.org/a#frag"):
            with self.subTest(url=url),self.assertRaises(ValueError): self.run_it([self.case(public_url=url)])

    def test_nonverified_action_never_submits(self):
        for state in ("EMAIL_REPORTED","UNVERIFIED","OFFICIAL_PAGE_RETRIEVED"):
            with self.subTest(state=state):
                r=self.run_it([self.case(source_status=state)])["records"][0]
                self.assertFalse(r["application_submitted_inferred"])

    def test_explicit_invalid_action_fails(self):
        with self.assertRaises(ValueError): self.run_it([self.case(next_action="SUBMIT_APPLICATION")])

    def test_missing_and_malformed_timestamp_fail(self):
        for bad in ("tomorrow","2026-11-07",None):
            with self.subTest(ts=bad),self.assertRaises(ValueError): self.run_it([self.case(observed_at=bad)])

    def test_missing_secret_fails(self):
        with self.assertRaises(ValueError): self.run_it(secret=b"default")

    def test_duplicate_graph_id_fails(self):
        with self.assertRaises(ValueError): self.run_it(graph=[NEEDS[0],NEEDS[0]])

    def test_hmac_tokens_change_with_secret(self):
        a=self.run_it()["records"][0]["source_token"]
        b=self.run_it(secret=b"different-private-key-for-tests-only-0123456789")["records"][0]["source_token"]
        self.assertNotEqual(a,b)

    def test_unbounded_empty_or_bad_input_fails(self):
        for bad in ([],["not a dict"],None):
            with self.subTest(rows=bad),self.assertRaises(ValueError): project(bad,NEEDS,KEY)


class CopilotPrivacyAndConflictRegressionTests(unittest.TestCase):
    """Independent-review regressions; synthetic inputs only."""
    case = NeedDigestTests.case
    run_it = NeedDigestTests.run_it

    def test_private_id_in_mail_supplied_url_path_must_fail(self):
        for path in (
            "/unsubscribe/aaaaaaaaaaaaaaaa",
            "/track/message/aaaaaaaaaaaaaaaa",
            "/public/program",
            "/%61%61%61%61",
        ):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.run_it([self.case(public_url="https://example.org" + path)])

    def test_same_message_same_need_disagreement_held_in_both_orders(self):
        baseline = self.case(priority="HIGH", source_status="EMAIL_REPORTED")
        disputed = self.case(priority="MEDIUM", source_status="SOURCE_CONFLICT")
        outcomes = []
        for incoming in ([baseline, disputed], [disputed, baseline]):
            result = self.run_it(incoming)
            self.assertEqual(result["source_conflicts"], 1)
            self.assertEqual(result["unique_proposals"], 1)
            self.assertEqual(result["records"][0]["route"], "HOLD_CONFLICT")
            self.assertEqual(result["records"][0]["source_status"], "SOURCE_CONFLICT")
            self.assertFalse(result["records"][0]["benefit_verified"])
            outcomes.append(result)
        self.assertEqual(outcomes[0], outcomes[1])

    def test_unmapped_need_conflict_counted_separately_from_route(self):
        result = self.run_it([self.case(
            need_id="subscription-oversight", source_status="SOURCE_CONFLICT"
        )])
        self.assertEqual(result["source_conflicts"], 1)
        self.assertEqual(result["need_graph_gaps"], 1)
        self.assertEqual(result["records"][0]["route"], "HOLD_CONFLICT")

    def test_identical_duplicates_do_not_create_source_conflict(self):
        x = self.case()
        result = self.run_it([x, dict(x)])
        self.assertEqual(result["duplicate_suppressed"], 1)
        self.assertEqual(result["source_conflicts"], 0)


if __name__=="__main__": unittest.main()

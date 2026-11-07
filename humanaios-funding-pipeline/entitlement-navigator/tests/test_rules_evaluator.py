import copy
import json
import unittest
from datetime import date, datetime

from entitlement.rules_evaluator import (
    ADVISORY_STATES, canonical_digest, evaluate, load_pack, validate_pack,
)

LL_BASE = {
    "state": "FL", "household_size": 1, "income_annual": None, "programs": None,
    "existing_discount_this_household": False, "benefit_at_same_address": False,
    "shares_income_expenses_with_other_beneficiary": None,
    "qualifying_tribal_lands": False, "service_kind": "broadband",
}
LH_BASE = {
    "county": "Okaloosa", "resident": True, "citizenship_qualifier": True,
    "energy_bill_responsibility": True, "fuel": "electric_cooling",
    "household_size": 1, "gross_income_annual": 20000, "disconnection_notice": None,
}


def ll(case, **kw):
    return {"case": case, **LL_BASE, **kw}


def lh(case, **kw):
    return {"case": case, **LH_BASE, **kw}


LIFELINE_CASES = [
    (ll("income_below", income_annual=20000, programs=[]), "POSSIBLE_ROUTE_UNVERIFIED"),
    (ll("income_above_snap", income_annual=30000, programs=["SNAP"]), "POSSIBLE_ROUTE_UNVERIFIED"),
    (ll("income_at_limit", income_annual=21546, programs=[]), "POSSIBLE_ROUTE_UNVERIFIED"),
    (ll("income_one_dollar_over", income_annual=21547, programs=[]), "NO_ROUTE_SHOWN"),
    (ll("two_at_limit", household_size=2, income_annual=29214, programs=[]), "POSSIBLE_ROUTE_UNVERIFIED"),
    (ll("two_over_limit", household_size=2, income_annual=29215, programs=[]), "NO_ROUTE_SHOWN"),
    (ll("medicaid_no_income", programs=["MEDICAID"]), "POSSIBLE_ROUTE_UNVERIFIED"),
    (ll("unknown_both"), "UNKNOWN_ROUTE_FACTS"),
    (ll("wic_not_qualifying", income_annual=55000, programs=["WIC"]), "NO_ROUTE_SHOWN"),
    (ll("existing_discount", income_annual=10000, programs=["SNAP"],
        existing_discount_this_household=True), "HOLD"),
    (ll("discount_status_unknown", income_annual=10000, programs=[],
        existing_discount_this_household=None), "FACT_UNKNOWN"),
    (ll("same_address_distinct", income_annual=20000, programs=[], benefit_at_same_address=True,
        shares_income_expenses_with_other_beneficiary=False), "WORKSHEET_REQUIRED"),
    (ll("same_address_shared_unknown", income_annual=20000, programs=[],
        benefit_at_same_address=True), "REVIEW_REQUIRED"),
    (ll("tribal_fdpir_land_true", income_annual=50000, programs=["FDPIR"],
        qualifying_tribal_lands=True), "POSSIBLE_ROUTE_UNVERIFIED"),
    (ll("tribal_fdpir_land_false", income_annual=50000, programs=["FDPIR"]), "NO_ROUTE_SHOWN"),
    (ll("tribal_lands_unknown", programs=["FDPIR"], qualifying_tribal_lands=None), "FACT_UNKNOWN"),
    (ll("nine_person_bound", household_size=9, income_annual=82890, programs=[]),
     "POSSIBLE_ROUTE_UNVERIFIED"),
    (ll("nine_person_over", household_size=9, income_annual=82891, programs=[]), "NO_ROUTE_SHOWN"),
    (ll("other_state", state="TX", income_annual=1000, programs=[]), "SCOPE_REVIEW"),
    (ll("size_unknown_income_no_programs", household_size=None, income_annual=1000, programs=[]), "UNKNOWN_ROUTE_FACTS"),
    (ll("size_unmodeled_income_no_programs", household_size=21, income_annual=1000, programs=[]), "UNKNOWN_ROUTE_FACTS"),
    (ll("tribal_unknown_above_cap", income_annual=50000, programs=["FDPIR"], qualifying_tribal_lands=None), "FACT_UNKNOWN"),
    (ll("tribal_unknown_no_income", programs=["FDPIR"], qualifying_tribal_lands=None), "FACT_UNKNOWN"),
    (ll("tribal_false_income_unknown", programs=["FDPIR"], qualifying_tribal_lands=False), "UNKNOWN_ROUTE_FACTS"),
]

LIHEAP_CASES = [
    (lh("single_below", gross_income_annual=28000), "WITHIN_PUBLISHED_LIMIT_ONLY"),
    (lh("single_above", gross_income_annual=33000), "OVER_PUBLISHED_LIMIT"),
    (lh("two_at_cap", household_size=2, gross_income_annual=42049), "WITHIN_PUBLISHED_LIMIT_ONLY"),
    (lh("two_one_over", household_size=2, gross_income_annual=42050), "OVER_PUBLISHED_LIMIT"),
    (lh("income_unknown", household_size=2, gross_income_annual=None), "UNKNOWN_ROUTE_FACTS"),
    (lh("household_size_unknown", household_size=None), "UNKNOWN_ROUTE_FACTS"),
    (lh("nine_person_not_modeled", household_size=9), "UNKNOWN_ROUTE_FACTS"),
    (lh("county_mismatch", county="Bay"), "SCOPE_REVIEW"),
    (lh("water_only", fuel="water_only"), "NO_ROUTE_SHOWN"),
    (lh("no_bill_responsibility", energy_bill_responsibility=False), "REVIEW_REQUIRED"),
    (lh("category_unknown", citizenship_qualifier=None), "FACT_UNKNOWN"),
    (lh("residency_unproven", resident=None), "FACT_UNKNOWN"),
    (lh("crisis_unconfirmed", disconnection_notice=True), "CRISIS_FUNDING_UNCONFIRMED"),
]


class RulesEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lifeline = load_pack("us-lifeline-2026")
        cls.liheap = load_pack("fl-liheap-ffy2027")

    def test_lifeline_cases(self):
        for facts, expected in LIFELINE_CASES:
            with self.subTest(case=facts["case"]):
                self.assertEqual(evaluate(self.lifeline, facts)["state"], expected)

    def test_liheap_cases(self):
        for facts, expected in LIHEAP_CASES:
            with self.subTest(case=facts["case"]):
                self.assertEqual(evaluate(self.liheap, facts)["state"], expected)

    def test_output_never_claims_eligibility_or_authority(self):
        for pack, cases in ((self.lifeline, LIFELINE_CASES), (self.liheap, LIHEAP_CASES)):
            for facts, _ in cases:
                out = evaluate(pack, facts)
                self.assertEqual(out["authority_effect"], "NONE")
                self.assertEqual(out["eligibility_status"], "UNASSESSED")
                self.assertEqual(out["determination"], "ADVISORY_SCREEN_ONLY")
                self.assertIn(out["state"], ADVISORY_STATES)
                self.assertNotIn("ELIGIBLE", out["state"].replace("INELIGIBLE", ""))

    def test_result_is_bound_to_pack_version_and_sources(self):
        out = evaluate(self.lifeline, LIFELINE_CASES[0][0])
        self.assertEqual(out["pack_digest"], self.lifeline["pack_digest"])
        self.assertEqual(out["rule_version"], "USAC-2026-11-06")
        self.assertEqual(out["rule_observed_at"], "2026-11-06")
        self.assertTrue(all(u.startswith("https://") for u in out["sources"]))

    def test_deterministic_replay(self):
        facts = LIFELINE_CASES[1][0]
        before = copy.deepcopy(facts)
        self.assertEqual(evaluate(self.lifeline, facts), evaluate(self.lifeline, facts))
        self.assertEqual(facts, before)

    def test_packs_on_disk_match_their_digest(self):
        for pack in (self.lifeline, self.liheap):
            self.assertEqual(canonical_digest(pack), pack["pack_digest"])

    def test_tampered_pack_rejected(self):
        bad = copy.deepcopy(self.lifeline)
        bad["income_cap"]["table"]["1"] = 99999999
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            evaluate(bad, LIFELINE_CASES[0][0])

    def test_pinned_digest_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError, "pinned digest"):
            evaluate(self.lifeline, LIFELINE_CASES[0][0], pinned_digest="0" * 64)
        ok = evaluate(self.lifeline, LIFELINE_CASES[0][0],
                      pinned_digest=self.lifeline["pack_digest"])
        self.assertEqual(ok["state"], "POSSIBLE_ROUTE_UNVERIFIED")

    def _repinned(self, pack, mutate):
        bad = copy.deepcopy(pack)
        mutate(bad)
        bad["pack_digest"] = canonical_digest(bad)
        return bad

    def test_pack_cannot_emit_eligible_state(self):
        bad = self._repinned(self.lifeline, lambda p: p["rules"][0].update(state="ELIGIBLE"))
        with self.assertRaisesRegex(ValueError, "non-advisory"):
            validate_pack(bad)

    def test_pack_cannot_declare_authority_fact(self):
        bad = self._repinned(self.lifeline, lambda p: p["facts"].update(authority_effect={"type": "str"}))
        with self.assertRaisesRegex(ValueError, "authority-bearing"):
            validate_pack(bad)

    def test_pack_requires_https_sources_only(self):
        bad = self._repinned(self.lifeline, lambda p: p.update(sources=[{"url": "http://example.com"}]))
        with self.assertRaisesRegex(ValueError, "https"):
            validate_pack(bad)

    def test_https_only_source_check_does_not_claim_authenticity(self):
        fake = self._repinned(self.lifeline,
                              lambda p: p.update(sources=[{"url": f"https://example.org/untrusted{i}"}
                                                                   for i in range(len(p["sources"]))]))
        validate_pack(fake)  # self-consistent and https, so accepted: digest is not authenticity
        out = evaluate(fake, LIFELINE_CASES[0][0])
        self.assertEqual(out["source_authenticity"], "NOT_VERIFIED")
        self.assertEqual(evaluate(self.lifeline, LIFELINE_CASES[0][0])["source_authenticity"],
                         "NOT_VERIFIED")

    def test_case_label_must_be_opaque_token(self):
        for bad in ("Jane Doe SSN 000-00-0000", "x" * 65, "", "a/b", 7):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "opaque token"):
                    evaluate(self.lifeline, {**LIFELINE_CASES[0][0], "case": bad})
        no_case = {k: v for k, v in LIFELINE_CASES[0][0].items() if k != "case"}
        self.assertEqual(evaluate(self.lifeline, no_case)["case"], "unnamed")

    def test_declared_expiry_requires_as_of(self):
        expired = self._repinned(self.lifeline, lambda p: p.update(effective_through="2020-01-01"))
        with self.assertRaisesRegex(ValueError, "as_of is required"):
            evaluate(expired, LIFELINE_CASES[0][0])
        self.assertEqual(evaluate(expired, LIFELINE_CASES[0][0], as_of="2026-11-06")["state"],
                         "STALE_RULES")

    def test_forged_authority_and_unknown_fields_rejected(self):
        for field, value in (("authority_effect", "AUTHORIZE"), ("eligibility_status", "ELIGIBLE"),
                             ("ssn", "000-00-0000"), ("name", "Jane Doe")):
            with self.subTest(field=field):
                with self.assertRaisesRegex(ValueError, "unexpected fact fields"):
                    evaluate(self.lifeline, {**LIFELINE_CASES[0][0], field: value})

    def test_malformed_fact_values_rejected(self):
        for bad in ({"income_annual": -1}, {"income_annual": True}, {"income_annual": float("nan")},
                    {"income_annual": float("inf")}, {"household_size": True},
                    {"programs": "SNAP"}, {"service_kind": "satellite"},
                    {"existing_discount_this_household": "no"}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    evaluate(self.lifeline, {**LIFELINE_CASES[0][0], **bad})

    def test_non_object_facts_rejected(self):
        with self.assertRaises(ValueError):
            evaluate(self.lifeline, ["income_annual"])

    def test_stale_only_when_source_declares_end_date(self):
        facts = LIFELINE_CASES[0][0]
        # No declared end date: never asserts staleness, never asserts currency either.
        self.assertEqual(evaluate(self.lifeline, facts, as_of="2099-01-01")["state"],
                         "POSSIBLE_ROUTE_UNVERIFIED")
        dated = self._repinned(self.lifeline, lambda p: p.update(effective_through="2026-12-31"))
        self.assertEqual(evaluate(dated, facts, as_of=date(2026, 12, 31))["state"],
                         "POSSIBLE_ROUTE_UNVERIFIED")
        out = evaluate(dated, facts, as_of="2027-01-01")
        self.assertEqual(out["state"], "STALE_RULES")
        self.assertEqual(out["rule_id"], "stale")

    def test_result_names_the_sources_for_the_matched_rule(self):
        out = evaluate(self.lifeline, ll("tribal", income_annual=50000, programs=["FDPIR"],
                                         qualifying_tribal_lands=True))
        self.assertEqual(out["rule_id"], "route_tribal")
        self.assertEqual(out["rule_sources"], ["https://www.usac.org/lifeline/consumer-eligibility/tribal-eligibility/"])
        self.assertEqual(out["rule_source_attribution"], "AUTHOR_ASSERTED_NOT_REVIEWED")
        # default / stale outcomes fall back to every pack source
        unknown = evaluate(self.lifeline, ll("unknown"))
        self.assertEqual(unknown["rule_sources"], unknown["sources"])

    def test_rule_source_index_must_exist(self):
        bad = self._repinned(self.lifeline, lambda p: p["rules"][0].update(sources=[99]))
        with self.assertRaisesRegex(ValueError, "source index"):
            validate_pack(bad)

    def test_case_label_is_matched_in_full_and_never_none(self):
        for bad in ("x\n", "x\r\n", None, "", "a b"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError, "opaque token"):
                    evaluate(self.lifeline, {**LIFELINE_CASES[0][0], "case": bad})

    def test_unusable_household_size_never_yields_a_negative_route(self):
        for size in (0, -1, 21, 10 ** 30, None, 1.0, True):
            with self.subTest(size=size):
                facts = ll("sz", household_size=size, income_annual=10000, programs=["SNAP2"])
                try:
                    out = evaluate(self.lifeline, facts)
                except ValueError:
                    continue  # rejected outright is also fail-closed
                self.assertEqual(out["state"], "UNKNOWN_ROUTE_FACTS")

    def test_null_scope_facts_are_unknown_and_program_names_normalize(self):
        self.assertEqual(evaluate(self.lifeline, ll("n1", state=None))["state"], "FACT_UNKNOWN")
        self.assertEqual(evaluate(self.liheap, lh("n2", county=None))["state"], "FACT_UNKNOWN")
        self.assertEqual(evaluate(self.lifeline, ll("n3", income_annual=99999, programs=[" snap "]))["state"],
                         "POSSIBLE_ROUTE_UNVERIFIED")


    # ---- findings from the CodeRabbit review of #1147 -------------------------------
    def test_malformed_rules_are_rejected_at_load_not_at_evaluation(self):
        cases = {
            "empty all matches everyone": lambda p: p["rules"][0].update({"all": []}),
            "all key missing": lambda p: p["rules"][0].pop("all"),
            "all not a list": lambda p: p["rules"][0].update({"all": "x"}),
            "rule without id": lambda p: p["rules"][0].pop("id"),
            "rule without state": lambda p: p["rules"][0].pop("state"),
            "duplicate rule ids": lambda p: p["rules"][1].update({"id": p["rules"][0]["id"]}),
            "reserved rule id": lambda p: p["rules"][0].update({"id": "default"}),
            "condition not an object": lambda p: p["rules"][0]["all"].append("x"),
            "undeclared list": lambda p: p["rules"][-1].update({"all": [{"fact": "programs", "op": "any_in", "value": "nope"}]}),
            "cap op on the wrong fact": lambda p: p["rules"][-1].update({"all": [{"fact": "household_size", "op": "le_cap"}]}),
            "empty rules list": lambda p: p.update({"rules": []}),
        }
        for label, mutate in cases.items():
            with self.subTest(label):
                bad = self._repinned(self.lifeline, mutate)
                with self.assertRaises(ValueError):
                    validate_pack(bad)
                with self.assertRaises(ValueError):
                    evaluate(bad, LIFELINE_CASES[0][0])

    def test_source_urls_need_a_host_and_no_userinfo(self):
        for url in ("https://", "https:///path", "https://user@usac.org/", "https://u:p@usac.org/",
                    "https://usac.org/a b", "https://usac.org/\\x", "http://usac.org/", "", None, 7):
            with self.subTest(url=url):
                bad = self._repinned(self.lifeline, lambda p: p["sources"][0].update(url=url))
                with self.assertRaisesRegex(ValueError, "https"):
                    validate_pack(bad)

    def test_effective_through_must_be_an_iso_date_at_load(self):
        for value in ("soon", "2026-13-01", 20261231, "2026-12-31T00:00:00"):
            with self.subTest(value=value):
                bad = self._repinned(self.lifeline, lambda p: p.update(effective_through=value))
                with self.assertRaisesRegex(ValueError, "ISO date"):
                    validate_pack(bad)

    def test_as_of_accepts_dates_and_datetimes_and_rejects_everything_else(self):
        dated = self._repinned(self.lifeline, lambda p: p.update(effective_through="2026-12-31"))
        facts = LIFELINE_CASES[0][0]
        self.assertEqual(evaluate(dated, facts, as_of=datetime(2026, 12, 31, 23, 59))["state"],
                         "POSSIBLE_ROUTE_UNVERIFIED")
        self.assertEqual(evaluate(dated, facts, as_of=datetime(2027, 1, 1, 0, 1))["state"], "STALE_RULES")
        for bad in (20261231, 1.5, [], "garbage", "2026-02-30"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):  # never TypeError
                    evaluate(dated, facts, as_of=bad)
        # also checked for packs with no end date: a malformed as_of is not silently ignored
        with self.assertRaises(ValueError):
            evaluate(self.lifeline, facts, as_of="garbage")

    def test_stale_result_shows_no_income_limit_and_records_as_of(self):
        dated = self._repinned(self.lifeline, lambda p: p.update(effective_through="2026-12-31"))
        facts = LIFELINE_CASES[0][0]
        stale = evaluate(dated, facts, as_of="2027-01-01")
        self.assertEqual((stale["state"], stale["income_cap_usd"], stale["income_cap_basis"]),
                         ("STALE_RULES", None, None))
        self.assertEqual(stale["as_of"], "2027-01-01")
        live = evaluate(dated, facts, as_of="2026-12-31")
        self.assertEqual((live["income_cap_usd"], live["income_cap_basis"]), (21546, "published_table"))
        self.assertEqual(live["as_of"], "2026-12-31")
        self.assertIsNone(evaluate(self.lifeline, facts)["as_of"])

    def test_extrapolated_limits_are_labeled_as_such(self):
        nine = evaluate(self.lifeline, ll("big", household_size=9, income_annual=1000, programs=[]))
        self.assertEqual((nine["income_cap_usd"], nine["income_cap_basis"]), (82890, "extrapolated"))
        eight = evaluate(self.lifeline, ll("eight", household_size=8, income_annual=1000, programs=[]))
        self.assertEqual(eight["income_cap_basis"], "published_table")
        none = evaluate(self.lifeline, ll("zero", household_size=None))
        self.assertIsNone(none["income_cap_basis"])

    def test_rejected_field_names_are_not_echoed_and_mixed_keys_do_not_crash(self):
        for facts in ({**LIFELINE_CASES[0][0], "Jane Doe": 1, "ssn": "000"},
                      {**LIFELINE_CASES[0][0], 7: 1, "x": 2}):
            with self.subTest(keys=len(facts)):
                with self.assertRaises(ValueError) as ctx:
                    evaluate(self.lifeline, facts)
                self.assertIn("2 field(s)", str(ctx.exception))
                self.assertNotIn("Jane", str(ctx.exception))
                self.assertNotIn("ssn", str(ctx.exception))

    def test_unknown_same_address_is_a_missing_fact_not_a_no(self):
        for extra in ({"benefit_at_same_address": None},):
            out = evaluate(self.lifeline, ll("sa", income_annual=1000, programs=[], **extra))
            self.assertEqual((out["state"], out["rule_id"]), ("FACT_UNKNOWN", "same_address_unknown"))
        # known answers are unchanged
        self.assertEqual(evaluate(self.lifeline, ll("sa2", income_annual=1000, programs=[]))["state"],
                         "POSSIBLE_ROUTE_UNVERIFIED")
        # a reported existing discount still wins over an unknown address
        self.assertEqual(evaluate(self.lifeline, ll("sa3", income_annual=1000, programs=[],
                                                    existing_discount_this_household=True,
                                                    benefit_at_same_address=None))["state"], "HOLD")

    def test_pack_file_is_plain_json(self):
        json.dumps(self.liheap)


if __name__ == "__main__":
    unittest.main()

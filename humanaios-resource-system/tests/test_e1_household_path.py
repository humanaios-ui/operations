"""E1 household path + explanation. Everything is synthetic; no network, no files written."""
import copy
import re
import unittest
from unittest import mock

from resource_system import e1_household_path as e1
from resource_system.e1_explain import STATE_TEXT, explain

AS_OF = "2026-11-06"
T0 = "2026-11-06T12:00:00Z"
T1 = "2026-11-06T13:00:00Z"
# Words an explanation must never use: nothing was approved, granted or confirmed.
BANNED = re.compile(r"\b(approved|qualified|granted|awarded|enrolled|you qualify|is eligible|are eligible|will receive)\b", re.I)
MONTHLY_AMOUNT = re.compile(r"\$\s?\d[\d,.]*\s*(/|per|a)\s*month", re.I)

LIFELINE_URL = "https://www.usac.org/lifeline/consumer-eligibility/"
LIFELINE_CANDIDATE = {
    "resource_id": "SYNTHETIC-RESOURCE-FEDERAL-LIFELINE", "title": "FCC Lifeline",
    "sponsor": "FCC / USAC", "canonical_url": LIFELINE_URL, "primary_source_url": LIFELINE_URL,
    "source_url": "https://www.usac.org/lifeline/national-verifier/",
    "resource_types": ["communications_discount"], "applicant_types": ["household"],
    "geography": ["Florida"], "tags": ["Lifeline"], "status": "OFFICIAL_RULES_OBSERVED_2026",
    "route": "VERIFY_NOW", "source_name": "USAC", "discovery_method": "first_party_rule_research_synthetic",
    "discovered_at": "2026-11-06T00:00:00Z", "last_verified_at": None,
    "evidence": [{"url": LIFELINE_URL, "kind": "OFFICIAL_RULE_PAGE", "observed_at": "2026-11-06"}],
    "need_matches": [{"need_id": "synthetic-communications-cost", "label": "Reduce broadband costs", "score": 1.0}],
    "eligibility_assessed": False, "eligibility_status": "UNASSESSED",
}
LIHEAP_URL = "https://www.floridajobs.org/community-development/Low-Income-Home-Energy-Assistance-Program"
LIHEAP_CANDIDATE = {
    "resource_id": "SYNTHETIC-RESOURCE-LIHEAP", "title": "Florida LIHEAP",
    "sponsor": "FloridaCommerce / Tri-County Community Council", "canonical_url": LIHEAP_URL,
    "source_url": "https://tricountycommunitycouncil.com/?page_id=85", "primary_source_url": LIHEAP_URL,
    "resource_types": ["household_energy_assistance"], "applicant_types": ["household"],
    "geography": ["Florida", "Okaloosa County"], "tags": ["utility"], "status": "INTAKE_CHANNEL_MIXED_VERIFY_LOCAL",
    "route": "VERIFY_NOW", "source_name": "FloridaCommerce", "discovery_method": "first_party_source_research_synthetic",
    "discovered_at": "2026-11-06T00:00:00Z", "last_verified_at": None,
    "evidence": [{"url": LIHEAP_URL, "kind": "OFFICIAL_PAGE", "observed_at": "2026-11-06"}],
    "need_matches": [{"need_id": "synthetic-energy-expense", "label": "Energy bill support", "score": 1.0}],
    "eligibility_assessed": False, "eligibility_status": "UNASSESSED",
}
LL_BASE = {"state": "FL", "household_size": 1, "income_annual": None, "programs": None,
           "existing_discount_this_household": False, "benefit_at_same_address": False,
           "shares_income_expenses_with_other_beneficiary": None,
           "qualifying_tribal_lands": False, "service_kind": "broadband"}
LH_BASE = {"county": "Okaloosa", "resident": True, "citizenship_qualifier": True,
           "energy_bill_responsibility": True, "fuel": "electric_cooling", "household_size": 1,
           "gross_income_annual": 20000, "disconnection_notice": None}


def ll(case, **kw):
    return {"case": case, **LL_BASE, **kw}


def lh(case, **kw):
    return {"case": case, **LH_BASE, **kw}


def run(program, facts, **kw):
    cand = LIFELINE_CANDIDATE if program == "lifeline" else LIHEAP_CANDIDATE
    args = dict(as_of=AS_OF, observed_at=T0)
    args.update(kw)
    return e1.run_household(program, copy.deepcopy(cand), facts, **args)


class E1PathTests(unittest.TestCase):
    def test_lifeline_and_liheap_both_flow_through_the_same_path(self):
        a = run("lifeline", ll("hh-1", income_annual=20000, programs=[]))
        b = run("liheap", lh("hh-2"))
        self.assertEqual(a["entry"]["screen"]["state"], "POSSIBLE_ROUTE_UNVERIFIED")
        self.assertEqual(b["entry"]["screen"]["state"], "WITHIN_PUBLISHED_LIMIT_ONLY")
        for r in (a, b):
            e = r["entry"]
            self.assertEqual((e["authority_effect"], e["eligibility_status"]), ("NONE", "UNASSESSED"))
            self.assertEqual(e["path_status"], "OK")
            self.assertEqual(e["journey"]["participant_standing"], "NOT_CONFIRMED_BY_PROVIDER")
            self.assertIn("REVIEW_AND_SELECT_OPPORTUNITY", e["journey"]["next_action_codes"])

    def test_source_identity_rule_version_and_history_are_preserved(self):
        e = run("lifeline", ll("hh-1", income_annual=20000, programs=[]))["entry"]
        self.assertEqual(e["source_identity"]["resource_id"], "SYNTHETIC-RESOURCE-FEDERAL-LIFELINE")
        self.assertEqual(e["source_identity"]["handoff_id"], "rm:SYNTHETIC-RESOURCE-FEDERAL-LIFELINE")
        self.assertEqual(e["source_identity"]["primary_source_url"], LIFELINE_URL)
        self.assertEqual(e["rule"]["pack_digest"], e1.PINS["lifeline"]["pinned_digest"])
        self.assertEqual(e["rule"]["rule_version"], "USAC-2026-11-06")
        self.assertTrue(all(u.startswith("https://www.usac.org/") for u in e["rule"]["rule_sources"]))

    def test_human_selection_is_a_journey_change_not_an_approval(self):
        r1 = run("lifeline", ll("hh-1", income_annual=20000, programs=[]))
        r2 = run("lifeline", ll("hh-1", income_annual=20000, programs=[]), ledger=r1["ledger"],
                 human_selected_ref="SEL-0001", observed_at=T1)
        self.assertFalse(r2["duplicate"])
        self.assertEqual(r2["changed"], ["journey"])
        self.assertEqual(r2["entry"]["screen"]["state"], r1["entry"]["screen"]["state"])
        self.assertNotIn("REVIEW_AND_SELECT_OPPORTUNITY", r2["entry"]["journey"]["next_action_codes"])
        self.assertEqual(r2["entry"]["supersedes"], r1["entry"]["entry_hash"])

    # ---- duplicates and history -------------------------------------------------
    def test_identical_replay_is_a_noop_even_at_a_later_time(self):
        r1 = run("liheap", lh("hh-2"))
        r2 = run("liheap", lh("hh-2"), ledger=r1["ledger"], observed_at=T1)
        self.assertTrue(r2["duplicate"])
        self.assertEqual(len(r2["ledger"]), 1)
        self.assertEqual(r2["entry"], r1["entry"])

    def test_changed_facts_append_and_keep_the_old_decision(self):
        r1 = run("liheap", lh("hh-2", gross_income_annual=20000))
        r2 = run("liheap", lh("hh-2", gross_income_annual=90000), ledger=r1["ledger"], observed_at=T1)
        self.assertEqual(r2["changed"], ["facts", "screen"])
        self.assertEqual(len(r2["ledger"]), 2)
        self.assertEqual(r2["ledger"][0], r1["entry"])  # old decision untouched
        self.assertEqual(r2["entry"]["supersedes"], r1["entry"]["entry_hash"])
        self.assertEqual(r2["entry"]["screen"]["state"], "OVER_PUBLISHED_LIMIT")

    def test_same_case_token_in_two_programs_does_not_collide(self):
        r1 = run("lifeline", ll("hh-3", income_annual=20000, programs=[]))
        r2 = run("liheap", lh("hh-3"), ledger=r1["ledger"])
        self.assertFalse(r2["duplicate"])
        self.assertIsNone(r2["entry"]["supersedes"])
        e1.verify_ledger(r2["ledger"])

    def _with_pack(self, program, mutate):
        """Simulate a human re-pin: return (registry, patch) for a modified, re-digested pack."""
        reg = e1.default_registry()
        pack = copy.deepcopy(reg[program]["pack"])
        mutate(pack)
        pack["pack_digest"] = e1._evaluator.canonical_digest(pack)
        reg[program] = {"pack": pack, "pinned_digest": pack["pack_digest"]}
        return reg

    def test_changed_rules_are_recorded_not_overwritten(self):
        r1 = run("lifeline", ll("hh-4", income_annual=20000, programs=[]))
        old_pack = e1.default_registry()["lifeline"]["pack"]
        reg = self._with_pack("lifeline", lambda p: (p["income_cap"]["table"].update({"1": 15000}),
                                                     p.update(rule_version="USAC-NEXT")))
        with mock.patch.object(e1, "default_registry", return_value=reg), \
                mock.patch.dict(e1.RETIRED_PACKS, {old_pack["pack_digest"]: old_pack}):
            r2 = run("lifeline", ll("hh-4", income_annual=20000, programs=[]), ledger=r1["ledger"])
        self.assertEqual(r2["changed"], ["rules", "screen"])
        self.assertEqual(r2["entry"]["screen"]["state"], "NO_ROUTE_SHOWN")
        self.assertEqual(r2["ledger"][0]["rule"]["rule_version"], "USAC-2026-11-06")
        self.assertEqual(r2["entry"]["rule"]["rule_version"], "USAC-NEXT")

    def test_a_retired_pack_must_be_declared_or_history_stops_verifying(self):
        r1 = run("lifeline", ll("hh-5", income_annual=20000, programs=[]))
        reg = self._with_pack("lifeline", lambda p: p.update(rule_version="USAC-NEXT"))
        with mock.patch.object(e1, "default_registry", return_value=reg):
            with self.assertRaisesRegex(ValueError, "unknown rule pack"):
                run("lifeline", ll("hh-5", income_annual=20000, programs=[]), ledger=r1["ledger"])

    def test_ledger_tampering_is_detected(self):
        r1 = run("liheap", lh("a1"))
        r2 = run("liheap", lh("a2", gross_income_annual=90000), ledger=r1["ledger"])
        led = list(r2["ledger"])
        for label, mutate in (
            ("edit state", lambda L: L[0]["screen"].update(state="WITHIN_PUBLISHED_LIMIT_ONLY") or L[0]["screen"].update(state="POSSIBLE_ROUTE_UNVERIFIED")),
            ("forge authority", lambda L: L[0].update(authority_effect="AUTHORIZE")),
            ("drop first", lambda L: L.pop(0)),
            ("swap order", lambda L: L.reverse()),
        ):
            with self.subTest(label):
                bad = copy.deepcopy(led)
                mutate(bad)
                with self.assertRaises(ValueError):
                    e1.verify_ledger(bad)
                with self.assertRaises(ValueError):
                    run("liheap", lh("a3"), ledger=bad)

    # ---- forged authority --------------------------------------------------------
    def test_forged_authority_is_rejected_everywhere(self):
        cand = copy.deepcopy(LIHEAP_CANDIDATE)
        cand["authority_effect"] = "AUTHORIZE"
        with self.assertRaisesRegex(ValueError, "authority"):
            e1.run_household("liheap", cand, lh("f1"), as_of=AS_OF, observed_at=T0)
        for key in ("authority_effect", "eligibility_status", "authorization_state"):
            with self.assertRaises(ValueError):
                run("liheap", {**lh("f2"), key: "AUTHORIZE"})
        with self.assertRaises(ValueError):
            run("liheap", lh("f3"), human_selected_ref="not a token!")

    # ---- unsupported benefit claims ----------------------------------------------
    def test_benefit_and_approval_claims_are_rejected(self):
        for key in ("benefit_amount", "awarded", "payment_status", "approved", "actual_discount_usd", "enrolled"):
            with self.subTest(key):
                cand = copy.deepcopy(LIFELINE_CANDIDATE)
                cand[key] = "yes"
                with self.assertRaisesRegex(ValueError, "benefit claim"):
                    e1.run_household("lifeline", cand, ll("b1", income_annual=1, programs=[]),
                                     as_of=AS_OF, observed_at=T0)
        for key in ("benefit_amount", "approved"):
            with self.assertRaises(ValueError):
                run("lifeline", {**ll("b2", income_annual=1, programs=[]), key: 9.25})
        cand = copy.deepcopy(LIFELINE_CANDIDATE)
        cand["eligibility_status"] = "ELIGIBLE"
        with self.assertRaises(ValueError):
            e1.run_household("lifeline", cand, ll("b3", income_annual=1, programs=[]), as_of=AS_OF, observed_at=T0)

    # ---- missing facts -----------------------------------------------------------
    def test_missing_facts_are_named_and_never_assumed(self):
        e = run("lifeline", ll("m1"))["entry"]
        self.assertEqual(e["screen"]["state"], "UNKNOWN_ROUTE_FACTS")
        self.assertIn("income_annual", e["missing_facts"])
        self.assertIn("programs", e["missing_facts"])
        e2 = run("liheap", lh("m2", gross_income_annual=None))["entry"]
        self.assertEqual(e2["screen"]["state"], "UNKNOWN_ROUTE_FACTS")
        self.assertIn("gross_income_annual", e2["missing_facts"])
        e3 = run("liheap", lh("m3", citizenship_qualifier=None))["entry"]
        self.assertEqual(e3["screen"]["state"], "FACT_UNKNOWN")

    # ---- outdated rules / version binding ---------------------------------------
    def test_altered_or_unpinned_rules_are_refused(self):
        with self.assertRaises(TypeError):  # the caller can no longer supply its own registry or pins
            run("lifeline", ll("o0", income_annual=1, programs=[]), registry={})
        with mock.patch.dict(e1.PINS["lifeline"], {"pinned_digest": "0" * 64}):
            with self.assertRaisesRegex(ValueError, "pinned digest"):
                run("lifeline", ll("o2", income_annual=1, programs=[]))
        with mock.patch.dict(e1.PINS["lifeline"], {"pack_name": "fl-liheap-ffy2027",
                                                    "pinned_digest": e1.PINS["liheap"]["pinned_digest"]}):
            with self.assertRaisesRegex(ValueError, "program|pack"):
                run("lifeline", ll("o4", income_annual=1, programs=[]))
        with self.assertRaises(ValueError):
            run("nonexistent", ll("o3"))

    def test_rules_past_their_source_declared_end_are_stale_not_current(self):
        reg = self._with_pack("lifeline", lambda p: p.update(effective_through="2026-12-31"))
        facts = ll("s1", income_annual=1000, programs=[])
        with mock.patch.object(e1, "default_registry", return_value=reg):
            self.assertEqual(run("lifeline", facts, as_of="2026-12-31")["entry"]["screen"]["state"],
                             "POSSIBLE_ROUTE_UNVERIFIED")
            stale = run("lifeline", facts, as_of="2027-01-01")["entry"]
            self.assertEqual(stale["screen"]["state"], "STALE_RULES")
            self.assertIsNone(explain(stale)["published_income_limit_usd"])  # no number beside "do not rely"
            with self.assertRaises(ValueError):
                run("lifeline", facts, as_of="")

    def test_as_of_must_be_a_real_iso_date_not_before_the_rules(self):
        facts = ll("d1", income_annual=1000, programs=[])
        for bad in ("garbage", "1999-01-01", "2026-11-05", "20261107", "2026-W45-6", "2026-02-30", " ",
                    "2026-11-06T00:00:00", "2026-11-06 ", None, 20261106):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    run("lifeline", facts, as_of=bad)
        self.assertEqual(run("lifeline", facts, as_of="2099-01-01")["entry"]["as_of"], "2099-01-01")

    # ---- conflicting sources ------------------------------------------------------
    def test_conflicting_source_holds_the_path_without_changing_the_screen(self):
        ok = run("lifeline", ll("c1", income_annual=1000, programs=[]))["entry"]
        cand = copy.deepcopy(LIFELINE_CANDIDATE)
        cand["primary_source_url"] = "https://example.org/lifeline-lookalike"
        r = e1.run_household("lifeline", cand, ll("c1", income_annual=1000, programs=[]),
                             as_of=AS_OF, observed_at=T0)
        self.assertEqual(r["entry"]["path_status"], "SOURCE_CONFLICT_HOLD")
        self.assertEqual(r["entry"]["screen"]["state"], ok["screen"]["state"])  # not rewritten
        card = explain(r["entry"])
        self.assertFalse(card["worth_investigating"])
        self.assertIn("RESOLVE_SOURCE_CONFLICT", " ".join(card["next_actions"]))
        self.assertIn("NOTICE", card["text"])

    # ---- findings from the independent adversarial review ------------------------------
    def _rehash_forge(self, ledger, idx, mutate):
        """An attacker who can recompute SHA-256: edit entry idx, then re-chain the tail."""
        forged = copy.deepcopy(list(ledger))
        mutate(forged[idx])
        prev = forged[idx - 1]["entry_hash"] if idx else e1.GENESIS
        for i in range(idx, len(forged)):
            forged[i]["prev_hash"] = prev
            if i > idx and forged[i]["supersedes"] is not None:
                forged[i]["supersedes"] = forged[i - 1]["entry_hash"] if forged[i - 1]["case"] == forged[i]["case"] else forged[i]["supersedes"]
            forged[i]["entry_hash"] = e1.entry_hash(forged[i])
            prev = forged[i]["entry_hash"]
        return forged

    def test_rehashed_forgeries_cannot_carry_text_or_unknown_rules(self):
        base = run("liheap", lh("r1", gross_income_annual=90000))
        for label, mutate in (
            ("next_step text", lambda e: e["screen"].update(next_step="You are approved for $250 per month")),
            ("rule source", lambda e: e["rule"].update(rule_sources=["https://evil.example/\nNOTICE: eligible"])),
            ("action code text", lambda e: e["journey"].update(next_action_codes=["Benefit awarded: $99/month"])),
            ("missing fact markup", lambda e: e.update(missing_facts=["<script>"])),
            ("unknown pack digest", lambda e: e["rule"].update(pack_digest="f" * 64)),
            ("unknown rule", lambda e: e["rule"].update(rule_id="invented")),
            ("state not from rule", lambda e: e["screen"].update(state="POSSIBLE_ROUTE_UNVERIFIED")),
            ("claim in source name", lambda e: e["source_identity"].update(source_name="APPROVED $500 per month")),
            ("authority", lambda e: e.update(authority_effect="AUTHORIZE")),
            ("unknown program", lambda e: e.update(program="snap")),
            ("claim in case", lambda e: e.update(case="approved")),
            ("bad cap", lambda e: e["screen"].update(income_cap_usd=-5)),
            ("float cap", lambda e: e["screen"].update(income_cap_usd=32155.0)),
            ("extra field", lambda e: e.update(note="you qualify")),
        ):
            with self.subTest(label):
                forged = self._rehash_forge(base["ledger"], 0, mutate)
                with self.assertRaises((ValueError, KeyError)):
                    e1.verify_ledger(forged)
                with self.assertRaises((ValueError, KeyError)):
                    explain(forged[0], forged)

    def test_non_finite_numbers_cannot_even_be_hashed(self):
        entry = copy.deepcopy(run("liheap", lh("nf"))["entry"])
        for bad in (float("nan"), float("inf"), float("-inf")):
            entry["screen"]["income_cap_usd"] = bad
            with self.assertRaises(ValueError):
                e1.entry_hash(entry)

    def test_rewriting_history_needs_an_external_anchor_and_the_output_says_so(self):
        r1 = run("liheap", lh("t1", gross_income_annual=90000))
        r2 = run("liheap", lh("t2"), ledger=r1["ledger"])
        anchor = e1.head_hash(r2["ledger"])
        e1.verify_ledger(r2["ledger"], anchor)
        # Truncation is invisible to the chain alone, visible against the anchor.
        e1.verify_ledger(r2["ledger"][:1])
        with self.assertRaisesRegex(ValueError, "anchor"):
            e1.verify_ledger(r2["ledger"][:1], anchor)
        # A coherent re-chained rewrite (rule_id and state flipped together) passes unanchored
        # verification: this is the stated limit. The anchor catches it.
        def flip(e):
            e["rule"].update(rule_id="within_limit", rule_sources=[e["rule"]["rule_sources"][0]])
            e["screen"].update(state="WITHIN_PUBLISHED_LIMIT_ONLY",
                               next_step=e1.default_registry()["liheap"]["pack"]["next_steps"]["WITHIN_PUBLISHED_LIMIT_ONLY"])
        forged = self._rehash_forge(r2["ledger"], 0, flip)
        e1.verify_ledger(forged)
        with self.assertRaisesRegex(ValueError, "anchor"):
            e1.verify_ledger(forged, anchor)
        self.assertEqual(explain(r2["entry"], r2["ledger"])["history_integrity"], "HASH_CHAIN_UNANCHORED")
        self.assertIn("recompute hashes", explain(r2["entry"], r2["ledger"])["text"])
        self.assertEqual(explain(r2["entry"], r2["ledger"], anchor)["history_integrity"], "HASH_CHAIN_ANCHORED")

    def test_source_urls_are_parsed_strictly(self):
        good = "https://www.usac.org/lifeline/consumer-eligibility/"
        bad_values = ["https://evil.example\\@www.usac.org/", "http://usac.org/", "ftp://usac.org/",
                      "javascript://usac.org/%0aalert(1)", "//usac.org/", "https://usac.org:badport/",
                      "https://usac.org:8443/", "https://[::1/", "https://usac.org@evil.example/",
                      "https://evil.example#@usac.org/", "https://usac.org.evil.example/", "https://evilusac.org/",
                      "https://usac.org./", "https://sub.usac.org/", "https://www.usac.org/a\\b", "https://usac.org/\tx", " https://usac.org/",
                      "", None, 7, ["https://usac.org/"]]
        for field in ("primary_source_url", "canonical_url", "source_url"):
            for bad in bad_values:
                with self.subTest(field=field, bad=bad):
                    cand = copy.deepcopy(LIFELINE_CANDIDATE)
                    cand[field] = bad
                    r = e1.run_household("lifeline", cand, ll("u1", income_annual=1000, programs=[]),
                                         as_of=AS_OF, observed_at=T0)
                    self.assertEqual(r["entry"]["path_status"], "SOURCE_CONFLICT_HOLD")
        cand = copy.deepcopy(LIFELINE_CANDIDATE)
        cand.pop("source_url")
        r = e1.run_household("lifeline", cand, ll("u2", income_annual=1000, programs=[]), as_of=AS_OF, observed_at=T0)
        self.assertEqual(r["entry"]["path_status"], "SOURCE_CONFLICT_HOLD")
        cand = copy.deepcopy(LIFELINE_CANDIDATE)
        cand["canonical_url"] = "https://WWW.USAC.ORG/x"  # same host, any letter case
        r = e1.run_household("lifeline", cand, ll("u3", income_annual=1000, programs=[]), as_of=AS_OF, observed_at=T0)
        self.assertEqual(r["entry"]["path_status"], "OK")

    def test_unusable_household_size_is_missing_not_a_negative_route(self):
        for size in (0, -1, 21, 10 ** 30, None):
            with self.subTest(size=size):
                e = run("lifeline", ll("hs", household_size=size, income_annual=10000, programs=["x"]))["entry"]
                self.assertEqual(e["screen"]["state"], "UNKNOWN_ROUTE_FACTS")
                self.assertIn("household_size", e["missing_facts"])

    def test_unknown_scope_facts_are_unknown_not_out_of_scope(self):
        self.assertEqual(run("lifeline", ll("sc1", state=None, income_annual=1, programs=[]))["entry"]["screen"]["state"],
                         "FACT_UNKNOWN")
        self.assertEqual(run("liheap", lh("sc2", county=None))["entry"]["screen"]["state"], "FACT_UNKNOWN")
        self.assertEqual(run("lifeline", ll("sc3", state="fl", income_annual=1, programs=[]))["entry"]["screen"]["state"],
                         "SCOPE_REVIEW")  # fail closed, not normalized
        self.assertEqual(run("lifeline", ll("sc4", income_annual=99999, programs=[" snap "]))["entry"]["screen"]["state"],
                         "POSSIBLE_ROUTE_UNVERIFIED")  # program names are case-insensitive

    def test_claim_words_in_values_are_rejected(self):
        for value in ("APPROVED $500 per month", "Qualified Provider", "x" * 81, "Bénéfit"):
            with self.subTest(source_name=value):
                cand = copy.deepcopy(LIFELINE_CANDIDATE)
                cand["source_name"] = value
                with self.assertRaises(ValueError):
                    e1.run_household("lifeline", cand, ll("v1", income_annual=1, programs=[]), as_of=AS_OF, observed_at=T0)
        for case in ("approved", "ELIGIBLE_500_per_month", "x\n", "", None, "a b", "grant-1", "month-1"):
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    run("lifeline", {**ll("v2", income_annual=1, programs=[]), "case": case})

    def test_equal_facts_in_different_spelling_are_a_duplicate(self):
        r1 = run("lifeline", ll("n1", income_annual=1000, programs=["SNAP", "SSI"]))
        for variant in (dict(income_annual=1000.0, programs=["SNAP", "SSI"]),
                        dict(income_annual=1000, programs=["ssi", "SNAP"]),
                        dict(income_annual=1000, programs=["SNAP", "SSI", "snap"])):
            r2 = run("lifeline", ll("n1", **variant), ledger=r1["ledger"], observed_at=T1)
            self.assertTrue(r2["duplicate"], variant)

    def test_ledger_argument_must_be_a_real_list_or_tuple(self):
        facts = lh("g1")
        self.assertEqual(len(run("liheap", facts, ledger=None)["ledger"]), 1)
        for bad in ("", {}, (e for e in ()), 7):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    run("liheap", facts, ledger=bad)


class ExplanationTests(unittest.TestCase):
    CASES = [
        ("lifeline", ll("x1", income_annual=20000, programs=[])),
        ("lifeline", ll("x2", income_annual=30000, programs=["SNAP"])),
        ("lifeline", ll("x3", income_annual=99999, programs=[])),
        ("lifeline", ll("x4")),
        ("lifeline", ll("x5", income_annual=10000, programs=["SNAP"], existing_discount_this_household=True)),
        ("lifeline", ll("x6", income_annual=20000, programs=[], benefit_at_same_address=True,
                        shares_income_expenses_with_other_beneficiary=False)),
        ("lifeline", ll("x7", state="TX", income_annual=1, programs=[])),
        ("liheap", lh("y1")),
        ("liheap", lh("y2", gross_income_annual=90000)),
        ("liheap", lh("y3", disconnection_notice=True)),
        ("liheap", lh("y4", citizenship_qualifier=None)),
        ("liheap", lh("y5", county="Bay")),
        ("liheap", lh("y6", fuel="water_only")),
        ("liheap", lh("y7", energy_bill_responsibility=False)),
    ]

    def test_every_case_explains_without_claiming_an_approval_or_amount(self):
        for program, facts in self.CASES:
            with self.subTest(case=facts["case"]):
                r = run(program, facts)
                card = explain(r["entry"], r["ledger"])
                self.assertNotRegex(card["text"], BANNED)
                self.assertNotRegex(card["text"], MONTHLY_AMOUNT)
                self.assertIn("Not established", card["text"])
                self.assertEqual(card["screen_state"], r["entry"]["screen"]["state"])
                self.assertEqual(card["decision_hash"], r["entry"]["entry_hash"])
                self.assertTrue(card["rule_support"]["sources"])
                self.assertEqual(card["rule_support"]["source_authenticity"], "NOT_VERIFIED")
                self.assertTrue(card["next_actions"])

    def test_explanation_shows_missing_facts_sources_and_next_action(self):
        card = explain(run("lifeline", ll("z1"))["entry"])
        self.assertIn("income_annual", card["missing_facts"])
        self.assertFalse(card["worth_investigating"])
        card = explain(run("lifeline", ll("z2", income_annual=50000, programs=["FDPIR"],
                                          qualifying_tribal_lands=True))["entry"])
        self.assertTrue(card["worth_investigating"])
        self.assertEqual(card["rule_support"]["sources"],
                         ["https://www.usac.org/lifeline/consumer-eligibility/tribal-eligibility/"])
        self.assertIn("USAC National Verifier", card["next_actions"][-1])

    def test_every_state_the_packs_can_emit_has_explanation_text(self):
        reg = e1.default_registry()
        states = set()
        for entry in reg.values():
            states |= {r["state"] for r in entry["pack"]["rules"]}
            states.add(entry["pack"]["default_state"])
        states.add("STALE_RULES")
        self.assertLessEqual(states, set(STATE_TEXT))

    def test_explanation_cannot_change_or_overstate_a_decision(self):
        r = run("liheap", lh("w1", gross_income_annual=90000))
        entry = r["entry"]
        before = copy.deepcopy(entry)
        card = explain(entry, r["ledger"])
        self.assertEqual(entry, before)  # explain does not mutate the record
        self.assertEqual(card, explain(entry, r["ledger"]))  # deterministic
        for label, mutate in (
            ("flip state", lambda e: e["screen"].update(state="WITHIN_PUBLISHED_LIMIT_ONLY")),
            ("forge authority", lambda e: e.update(authority_effect="AUTHORIZE")),
            ("claim eligible", lambda e: e.update(eligibility_status="ELIGIBLE")),
            ("hide missing facts", lambda e: e.update(missing_facts=[])),
        ):
            with self.subTest(label):
                forged = copy.deepcopy(entry)
                mutate(forged)
                with self.assertRaises(ValueError):
                    explain(forged)
        # Even a forger who recomputes the hash cannot get past the ledger chain.
        forged = copy.deepcopy(entry)
        forged["screen"]["state"] = "WITHIN_PUBLISHED_LIMIT_ONLY"
        forged["entry_hash"] = e1.entry_hash(forged)
        with self.assertRaises(ValueError):
            explain(forged, r["ledger"])
        # explain() takes no state/override parameter at all.
        with self.assertRaises(TypeError):
            explain(entry, r["ledger"], state="POSSIBLE_ROUTE_UNVERIFIED")

    def test_entry_alone_is_still_validated_and_not_called_chain_checked(self):
        r = run("liheap", lh("e1"))
        card = explain(r["entry"])
        self.assertEqual(card["history_integrity"], "ENTRY_ONLY_CHAIN_NOT_CHECKED")
        self.assertIn("ENTRY_ONLY_CHAIN_NOT_CHECKED", card["text"])
        forged = copy.deepcopy(r["entry"])
        forged.update(prev_hash="ab" * 32)  # first entry must chain from genesis
        forged["entry_hash"] = e1.entry_hash(forged)
        with self.assertRaises(ValueError):
            explain(forged)

    def test_scope_and_unknown_states_do_not_print_an_income_limit(self):
        for facts in (lh("e2", county="Bay"), lh("e3", citizenship_qualifier=None)):
            card = explain(run("liheap", facts)["entry"])
            self.assertIsNone(card["published_income_limit_usd"])
            self.assertNotIn("income limit", card["text"])
        self.assertEqual(explain(run("liheap", lh("e4"))["entry"])["published_income_limit_usd"], 32155)

    def test_history_in_the_explanation_matches_the_ledger(self):
        r1 = run("liheap", lh("h1", gross_income_annual=20000))
        r2 = run("liheap", lh("h1", gross_income_annual=90000), ledger=r1["ledger"], observed_at=T1)
        card = explain(r2["entry"], r2["ledger"])
        self.assertEqual([h["screen_state"] for h in card["history"]],
                         ["WITHIN_PUBLISHED_LIMIT_ONLY", "OVER_PUBLISHED_LIMIT"])
        self.assertEqual([h["entry_hash"] for h in card["history"]],
                         [e["entry_hash"] for e in r2["ledger"]])
        self.assertEqual(explain(r1["entry"], r2["ledger"])["screen_state"], "WITHIN_PUBLISHED_LIMIT_ONLY")


if __name__ == "__main__":
    unittest.main()

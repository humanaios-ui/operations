import unittest

from entitlement.catalog import load_catalog
from entitlement.engine import evaluate_profile


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def by_id(self, results, program_id):
        return next(r for r in results if r["program_id"] == program_id)

    def test_tero_rule_match(self):
        profile = {
            "tribal_citizen": True,
            "tribe": "Cherokee Nation",
            "business_owner": True,
            "business_indian_ownership_percent": 100,
            "business_active_control": True,
        }
        results = evaluate_profile(profile, self.catalog, include_ineligible=True)
        self.assertEqual(self.by_id(results, "CN-TERO")["status"], "RULE_MATCH")

    def test_tero_fails_below_51(self):
        profile = {
            "tribal_citizen": True,
            "business_owner": True,
            "business_indian_ownership_percent": 50,
            "business_active_control": True,
        }
        results = evaluate_profile(profile, self.catalog, include_ineligible=True)
        self.assertEqual(self.by_id(results, "CN-TERO")["status"], "INELIGIBLE")

    def test_probate_is_investigate(self):
        profile = {"deceased_ancestor_possible_trust_assets": True}
        results = evaluate_profile(profile, self.catalog, include_ineligible=True)
        self.assertEqual(self.by_id(results, "BIA-TRUST-PROBATE")["status"], "INVESTIGATE")

    def test_section_184_remains_conditional(self):
        profile = {"tribal_citizen": True, "housing_finance_need": True}
        results = evaluate_profile(profile, self.catalog, include_ineligible=True)
        self.assertEqual(self.by_id(results, "HUD-SECTION-184")["status"], "CONDITIONAL_MATCH")

    def test_historical_never_becomes_current_match(self):
        profile = {"tribe": "Cherokee Nation"}
        results = evaluate_profile(profile, self.catalog, include_ineligible=True)
        self.assertEqual(self.by_id(results, "CHEROKEE-ICC-1975")["status"], "CLOSED_HISTORICAL")


if __name__ == "__main__":
    unittest.main()

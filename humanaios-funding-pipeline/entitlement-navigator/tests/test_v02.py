import unittest
from pathlib import Path

from entitlement.catalog import load_catalog
from entitlement.casefile import build_casefile
from entitlement.genealogy import import_gedcom_bytes, profile_patch_from_genealogy
from entitlement.genealogy_builder import new_draft, next_genealogy_question, apply_genealogy_answer, draft_to_gedcom
from entitlement.interrogator import interrogation_state


class V02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog()

    def test_general_intake_starts_general(self):
        q = interrogation_state({}, self.catalog)["next_question"]
        self.assertEqual(q["id"], "intake_statement")

    def test_general_grants_does_not_force_tribal_question(self):
        profile = {
            "intake_statement": "I want to find general funding for a community project.",
            "applicant_roles": ["Nonprofit"],
            "funding_goals": ["Grants / general funding"],
        }
        state = interrogation_state(profile, self.catalog)
        self.assertTrue(state["complete"])
        case = build_casefile(profile, self.catalog)
        task_ids = {x["task_id"] for x in case["research_queue"]}
        self.assertIn("DISCOVERY-ALN", task_ids)
        self.assertIn("DISCOVERY-GRANTS", task_ids)

    def test_genealogy_goal_activates_genealogy_interrogation(self):
        profile = {
            "intake_statement": "I want to investigate an inherited ancestral land claim.",
            "applicant_roles": ["Estate / heir"],
            "funding_goals": ["Estate / inheritance"],
        }
        q = interrogation_state(profile, self.catalog)["next_question"]
        self.assertEqual(q["id"], "tribal_citizen")

    def test_gedcom_clue_does_not_assert_dawes(self):
        ged = b"""0 HEAD
1 CHAR UTF-8
0 @I1@ INDI
1 NAME Focus /Person/
1 FAMC @F1@
0 @I2@ INDI
1 NAME Ancestor /Person/
1 NOTE Family story says Cherokee Nation and Native American descent
0 @F1@ FAM
1 HUSB @I2@
1 CHIL @I1@
0 TRLR
"""
        result, _ = import_gedcom_bytes(ged, "Focus Person")
        patch = profile_patch_from_genealogy(result)
        self.assertTrue(patch["ancestral_native_clue"])
        self.assertFalse(patch["genealogy_dawes_clue"])
        self.assertNotIn("dawes_ancestor_known", patch)

    def test_genealogy_builder_exports_gedcom(self):
        draft = new_draft()
        q = next_genealogy_question(draft)
        self.assertEqual(q["id"], "name")
        draft = apply_genealogy_answer(draft, q, "Test Person")
        ged = draft_to_gedcom(draft)
        self.assertIn("0 HEAD", ged)
        self.assertIn("1 NAME Test Person", ged)
        self.assertTrue(ged.endswith("0 TRLR
"))

    def test_unactivated_unknown_programs_not_in_case(self):
        profile = {
            "intake_statement": "general funding",
            "applicant_roles": ["Nonprofit"],
            "funding_goals": ["Grants / general funding"],
        }
        case = build_casefile(profile, self.catalog)
        ids = {r["program_id"] for r in case["pathways"]}
        self.assertNotIn("BTFA-IIM-UNCLAIMED", ids)
        self.assertNotIn("BIA-TRUST-PROBATE", ids)


if __name__ == "__main__":
    unittest.main()

class FundingAdapterTests(unittest.TestCase):
    def test_local_funding_adapter_does_not_claim_eligibility(self):
        import json
        import tempfile
        from pathlib import Path
        from entitlement.funding_adapter import search_sources

        sample = [
            {
                "name": "Example Native Research Fund",
                "category": "native",
                "sponsor": "Example Authority",
                "url": "https://example.gov/program",
                "native_eligible": True,
                "eligibility_tags": ["tribal_citizen", "business"],
                "status": "active",
            }
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sources.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            result = search_sources("Native", path=path)
        self.assertEqual(result["result_count"], 1)
        hit = result["results"][0]
        self.assertEqual(hit["classification"], "GENERAL_OPPORTUNITY")
        self.assertFalse(hit["eligibility_assessed"])

    def test_local_funding_adapter_filters_native_tag_only(self):
        import json
        import tempfile
        from pathlib import Path
        from entitlement.funding_adapter import search_sources

        sample = [
            {"name": "A", "category": "native", "sponsor": "S", "url": "https://example.gov/a", "native_eligible": True},
            {"name": "B", "category": "research_grant", "sponsor": "S", "url": "https://example.gov/b", "native_eligible": False},
        ]
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "sources.json"
            path.write_text(json.dumps(sample), encoding="utf-8")
            result = search_sources(native_only=True, path=path)
        self.assertEqual([x["name"] for x in result["results"]], ["A"])

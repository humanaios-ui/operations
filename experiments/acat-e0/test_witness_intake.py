"""Regression tests for the next synthetic Witness intake gate."""
import copy
import unittest

from witness_intake import SCHEMA, screen


def specimen(kind, facts):
    return {
        "schema": SCHEMA, "case_id": "DEMO-WITNESS-CASE",
        "is_synthetic": True, "authority_effect": "NONE",
        "kind": kind, "facts": facts,
    }


class TestWitnessIntake(unittest.TestCase):
    def test_identity_disagreement_holds_unknown_principal(self):
        r = screen(specimen("AGENT_IDENTITY", {
            "human_label": "DeepSeek", "agent_self_label": "Claude",
            "authenticated_principal": None,
        }))
        self.assertEqual(r["status"], "PROVENANCE_CONFLICT")
        self.assertEqual(r["disposition"], "HOLD")
        self.assertFalse(r["authenticated_actor"])

    def test_matching_name_still_is_not_authenticated(self):
        r = screen(specimen("AGENT_IDENTITY", {
            "human_label": "Claude", "agent_self_label": "Claude",
            "authenticated_principal": None,
        }))
        self.assertEqual(r["status"], "UNAUTHENTICATED_SELF_REPORT")
        self.assertFalse(r["authenticated_actor"])

    def test_distinct_canonical_scopes_do_not_contradict(self):
        r = screen(specimen("SCOPE_TERM", {
            "scope_a": "PLANNING_ANCHOR", "scope_b": "RATIFIED_DATA_SCHEMA",
            "assertion_a": True, "assertion_b": False,
        }))
        self.assertEqual(r["status"], "SCOPE_QUALIFICATION")
        self.assertEqual(r["proposed_relation"], "QUALIFIES")
        self.assertEqual(r["disposition"], "CONTINUE_WITH_ID")

    def test_same_scope_opposition_remains_candidate(self):
        r = screen(specimen("SCOPE_TERM", {
            "scope_a": "RATIFIED_DATA_SCHEMA", "scope_b": "RATIFIED_DATA_SCHEMA",
            "assertion_a": True, "assertion_b": False,
        }))
        self.assertEqual(r["status"], "CONTRADICTION_CANDIDATE")
        self.assertEqual(r["disposition"], "HOLD")

    def test_same_scope_agreement_is_not_truth(self):
        r = screen(specimen("SCOPE_TERM", {
            "scope_a": "PLANNING_ANCHOR", "scope_b": "PLANNING_ANCHOR",
            "assertion_a": True, "assertion_b": True,
        }))
        self.assertEqual(r["status"], "NO_CONFLICT_OBSERVED")
        self.assertEqual(r["source_verification"], "FIXTURE_ONLY_NOT_PERFORMED")

    def test_merged_dependency_supersedes_historic_hold(self):
        r = screen(specimen("STALE_DEPENDENCY", {
            "historic_pr_state": "OPEN", "latest_pr_state": "MERGED",
            "live_capability_verified": False,
        }))
        self.assertEqual(r["status"], "STALE_HOLD_SUPERSEDED")
        self.assertEqual(r["proposed_relation"], "SUPERSEDES")
        self.assertEqual(r["disposition"], "VERIFY")

    def test_merge_does_not_prove_live_deployment(self):
        r = screen(specimen("STALE_DEPENDENCY", {
            "historic_pr_state": "OPEN", "latest_pr_state": "MERGED",
            "live_capability_verified": False,
        }))
        self.assertEqual(r["source_verification"], "FIXTURE_ONLY_NOT_PERFORMED")
        self.assertIsNone(r["canonical_acat_score"])

    def test_open_dependency_still_unresolved(self):
        r = screen(specimen("STALE_DEPENDENCY", {
            "historic_pr_state": "OPEN", "latest_pr_state": "OPEN",
            "live_capability_verified": False,
        }))
        self.assertEqual(r["status"], "NO_STALE_MERGE_SHOWN")

    def test_riemann_claim_vs_community_certification(self):
        r = screen(specimen("RIEMANN_PROOF", {
            "researcher_claim": True, "community_certificate": True,
            "prize_or_formal_acceptance": False,
        }))
        self.assertEqual(r["status"], "COMMUNITY_CERTIFICATION_REPORTED")
        self.assertEqual(r["disposition"], "VERIFY")
        self.assertEqual(r["source_verification"], "FIXTURE_ONLY_NOT_PERFORMED")

    def test_riemann_claim_without_certificate(self):
        r = screen(specimen("RIEMANN_PROOF", {
            "researcher_claim": True, "community_certificate": False,
            "prize_or_formal_acceptance": False,
        }))
        self.assertEqual(r["status"], "CLAIM_ONLY")

    def test_riemann_prize_boast_does_not_promote_certificate(self):
        r = screen(specimen("RIEMANN_PROOF", {
            "researcher_claim": True, "community_certificate": False,
            "prize_or_formal_acceptance": True,
        }))
        self.assertEqual(r["status"], "CLAIM_ONLY")
        self.assertIsNone(r["canonical_acat_score"])

    def test_gta_issuer_filing_still_estimate(self):
        r = screen(specimen("GTA_SALES", {
            "issuer_estimate": True, "issuer_original_release": True,
            "independent_audit": False,
        }))
        self.assertEqual(r["status"], "ISSUER_REPORTED_NOT_INDEPENDENTLY_AUDITED")
        self.assertEqual(r["authority_effect"], "NONE")

    def test_gta_audit_self_claim_not_authenticated(self):
        r = screen(specimen("GTA_SALES", {
            "issuer_estimate": True, "issuer_original_release": True,
            "independent_audit": True,
        }))
        self.assertEqual(r["status"], "AUDIT_REPORTED_NOT_AUTHENTICATED")

    def test_denies_real_data_and_authority(self):
        for key, value in (("is_synthetic", False), ("authority_effect", "RATIFY")):
            case = specimen("GTA_SALES", {
                "issuer_estimate": True, "issuer_original_release": True,
                "independent_audit": False,
            })
            case[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                screen(case)

    def test_denies_hidden_fields_and_unknown_source(self):
        case = specimen("AGENT_IDENTITY", {
            "human_label": "A", "agent_self_label": "B",
            "authenticated_principal": None, "private_chat": "untrusted",
        })
        with self.assertRaises(ValueError):
            screen(case)
        case["facts"].pop("private_chat")
        case["raw_transcript"] = "hidden"
        with self.assertRaises(ValueError):
            screen(case)

    def test_malformed_kind_returns_controlled_value_error(self):
        for invalid in ([], {}, None, 0, 1.5, True):
            with self.subTest(kind=repr(invalid)):
                case = specimen("GTA_SALES", {
                    "issuer_estimate": True, "issuer_original_release": True,
                    "independent_audit": False,
                })
                case["kind"] = invalid
                with self.assertRaisesRegex(ValueError, "invalid case type"):
                    screen(case)

    def test_unknown_kind_returns_controlled_value_error(self):
        case = specimen("UNKNOWN_TEST_KIND", {})
        with self.assertRaisesRegex(ValueError, "invalid case type"):
            screen(case)

    def test_denies_forged_authenticated_principal(self):
        case = specimen("AGENT_IDENTITY", {
            "human_label": "A", "agent_self_label": "A",
            "authenticated_principal": "github-user-is-not-model-proof",
        })
        with self.assertRaises(ValueError):
            screen(case)


if __name__ == "__main__":
    unittest.main()

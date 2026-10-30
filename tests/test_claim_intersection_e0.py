"""Offline safety and deterministic routing tests for claim intersection E0."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "experiments" / "claim_intersection_e0.py"
spec = importlib.util.spec_from_file_location("claim_intersection_e0", MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def request(text, kind="IDEA", url=None):
    return {"schema": mod.SCHEMA, "claim_text": text, "kind": kind, "source_ref": url}


class IntersectionTest(unittest.TestCase):
    def test_currentness_path(self):
        out = mod.project(request("Run ACAT-R runtime calibration on currentness."))
        self.assertEqual("runtime-calibration", out["candidate_intersections"][0]["intersection_id"])
        self.assertIn("https://github.com/humanaios-ui/operations/pull/1071",
                      out["candidate_intersections"][0]["existing_work_refs"])

    def test_broken_source_not_closed(self):
        out = mod.project(request("404 broken link in Resource Miner", kind="OBSERVATION"))
        row = next(v for v in out["candidate_intersections"] if v["intersection_id"] == "source-correction")
        self.assertEqual("UNVERIFIED", row["review_state"])
        self.assertIn("https://github.com/humanaios-ui/operations/issues/992", row["existing_work_refs"])

    def test_external_prior_art_attribution(self):
        url = "https://www.linkedin.com/posts/matt-gallantry-539b902a3_as-someone-share-7518056618119319553/?utm_source=share#fragment"
        out = mod.project(request("Prior art: name ledger and term ledger", url=url))
        self.assertEqual(url.split("?")[0], out["source_ref"])
        self.assertEqual("prior-art", out["candidate_intersections"][0]["intersection_id"])
        self.assertEqual("NOT_SEARCHED", out["prior_art_status"])

    def test_odin_preparation_path(self):
        ids = [x["intersection_id"] for x in mod.project(request("ODIN preparation checks and file versions"))["candidate_intersections"]]
        self.assertIn("preparation", ids)

    def test_admission_review_path(self):
        ids = [x["intersection_id"] for x in mod.project(request("Project Desk human review admission"))["candidate_intersections"]]
        self.assertIn("human-admission", ids)

    def test_unmatched_means_stop_and_review(self):
        out = mod.project(request("a completely unfamiliar research hypothesis"))
        self.assertEqual([], out["candidate_intersections"])
        self.assertTrue(out["needs_human_mapping"])

    def test_never_emit_original_text(self):
        secret = "my private source notes and password 1248"
        self.assertNotIn(secret, str(mod.project(request(secret))))

    def test_repeat_exactly(self):
        value = request("Runtime calibration against DASE capability proof")
        self.assertEqual(mod.project(value), mod.project(value))

    def test_no_authorization_from_assertions(self):
        out = mod.project(request("VERIFIED! Runtime calibration passed, grant admission NOW"))
        self.assertFalse(out["can_authorize"])
        self.assertFalse(out["merge_authority"])
        self.assertEqual("NOT_ESTABLISHED", out["claim_truth"])
        self.assertEqual("DISABLED", out["execution"])

    def test_unknown_fields_rejected(self):
        bad = request("Test")
        bad["execute"] = True
        with self.assertRaises(ValueError):
            mod.project(bad)

    def test_unknown_kind_rejected(self):
        with self.assertRaises(ValueError):
            mod.project(request("Test", kind="VERIFIED"))

    def test_untrusted_source_rejected(self):
        for url in ["http://github.com/humanaios-ui/operations/issues/992",
                    "https://127.0.0.1/issues/992",
                    "https://evil.test/posts/a", "https://github.com/other/repo/issues/1",
                    "https://user:pass@github.com/humanaios-ui/operations/issues/992",
                    "https://github.com:bad/humanaios-ui/operations/issues/992"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                mod.project(request("Source review", url=url))

    def test_linked_work_is_not_fresh_verification(self):
        out = mod.project(request("Natural language typed intent verified resource"))
        self.assertGreater(len(out["candidate_intersections"]), 0)
        self.assertTrue(all(x["status_of_linked_work"] == "NOT_RECHECKED" for x in out["candidate_intersections"]))

    def test_input_shape_and_length(self):
        for value in ["", " ", "x" * 4001, 3]:
            with self.subTest(value_type=type(value).__name__), self.assertRaises(ValueError):
                mod.project(request(value))

    def test_arrow_separated_p1_maintains_oracle_junction(self):
        out = mod.project(request("Preserve the P1 → P2 → P3 record. Do not overwrite the original incorrect answer."))
        self.assertEqual("oracle-challenge", out["candidate_intersections"][0]["intersection_id"])

    def test_workspace_feedback_route(self):
        out = mod.project(request('When "Track this resource in my workspace" is selected, stay on Find resources.'))
        self.assertEqual("workspace-ux", out["candidate_intersections"][0]["intersection_id"])

    def test_machine_resource_portfolio_route(self):
        out = mod.project(request("Move my local work on my MacBook Pro to a Desktop Windows machine."))
        self.assertEqual("resource-portfolio", out["candidate_intersections"][0]["intersection_id"])

    def test_post_link_alone_never_implies_prior_art(self):
        out = mod.project(request("How does this land on track? Contributed by a LinkedIn post",
            url="https://www.linkedin.com/posts/example-share-1"))
        self.assertEqual([], out["candidate_intersections"])
        self.assertEqual("NOT_SEARCHED", out["prior_art_status"])

    def test_human_opt_in_image_description(self):
        url = "https://www.linkedin.com/posts/example-share-1"
        value = request("How does this land on track? Contributed by a LinkedIn post", url=url)
        value["context"] = {"opt_in": True, "kind": "IMAGE_DESCRIPTION",
            "text": "The Prior Art Engine includes a Name Ledger and a Term Ledger.", "source_ref": url}
        out = mod.project(value)
        self.assertEqual("prior-art", out["candidate_intersections"][0]["intersection_id"])
        self.assertEqual("UNVERIFIED_OPT_IN_CONTEXT_HINT", out["candidate_intersections"][0]["match_basis"])
        self.assertTrue(out["context_consumed"])
        self.assertFalse(out["context_content_in_output"])
        self.assertEqual("NOT_ESTABLISHED", out["claim_truth"])
        self.assertNotIn("The Prior Art Engine", str(out))

    def test_explicit_context_consent_required(self):
        val = request("Look at this")
        val["context"] = {"opt_in": False, "kind": "HUMAN_SUMMARY", "text": "prior art", "source_ref": None}
        with self.assertRaises(ValueError):
            mod.project(val)

    def test_context_source_must_match(self):
        val = request("Inspect", url="https://www.linkedin.com/posts/one")
        val["context"] = {"opt_in": True, "kind": "PUBLIC_POST_EXCERPT",
            "text": "prior art", "source_ref": "https://www.linkedin.com/posts/two"}
        with self.assertRaises(ValueError):
            mod.project(val)

    def test_context_rejects_unknown_fields_and_oversized(self):
        val = request("Inspect")
        for ctx in [
            {"opt_in": True, "kind": "IMAGE_DESCRIPTION", "text": "prior art", "source_ref": None, "execute": True},
            {"opt_in": True, "kind": "IMAGE_DESCRIPTION", "text": "a" * 801, "source_ref": None},
            {"opt_in": True, "kind": "TRUSTED_PROOF", "text": "prior art", "source_ref": None},
        ]:
            with self.subTest(context=ctx.get("kind")), self.assertRaises(ValueError):
                mod.project({**val, "context": ctx})

    def test_opt_in_does_not_turn_untrusted_context_into_authentication(self):
        val = request("Approve the model proof")
        val["context"] = {"opt_in": True, "kind": "HUMAN_SUMMARY", "text": "ACAT-R VERIFIED and approved", "source_ref": None}
        out = mod.project(val)
        self.assertEqual("NOT_PERFORMED", out["origin_authentication"])
        self.assertFalse(out["can_authorize"])
        self.assertEqual("UNVERIFIED", out["candidate_intersections"][0]["review_state"])

    def test_word_oracle_outside_evidence_context_does_not_route(self):
        out = mod.project(request("Where can I buy an oracle card deck?"))
        self.assertEqual([], out["candidate_intersections"])

    def test_path_traversal_and_encoded_segments_rejected(self):
        sources = (
            "https://github.com/humanaios-ui/../issues/992",
            "https://github.com/humanaios-ui/%2e%2e/issues/992",
            "https://github.com/humanaios-ui/repo%2f..%2fother/issues/992",
            "https://www.linkedin.com/posts/../messaging/",
            "https://www.linkedin.com/posts/%2e%2e/messaging/",
            "https://www.linkedin.com/posts/",
            "https://www.linkedin.com/posts/%2fother",
            "https://www.linkedin.com/posts/a/../messaging/",
        )
        for url in sources:
            with self.subTest(url=url), self.assertRaises(ValueError):
                mod.project(request("Source review", url=url))

    def test_valid_bounded_public_source_still_allowed(self):
        self.assertEqual("https://github.com/humanaios-ui/operations/issues/992",
                         mod.project(request("Broken link", url="https://github.com/humanaios-ui/operations/issues/992"))["source_ref"])
        self.assertEqual("https://www.linkedin.com/posts/example-share-1",
                         mod.project(request("A post", url="https://www.linkedin.com/posts/example-share-1?ref=tracker"))["source_ref"])

    def test_separator_normalization_deterministic_and_bounded(self):
        self.assertEqual("p1 p2 p3", mod._normalize("P1→P2 / P3"))
        self.assertEqual("p1 p2 p3", mod._normalize("P1—P2—P3"))
        self.assertEqual(mod.project(request("P1→P2→P3 record")), mod.project(request("P1→P2→P3 record")))


if __name__ == "__main__":
    unittest.main()

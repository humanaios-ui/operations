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


if __name__ == "__main__":
    unittest.main()

"""Offline falsifiers for kg/kg_v0_2_check.py. No network. Run: python -m unittest tests.test_kg_v0_2_check -v
Synthetic fixtures prove each rule can fail. Pins prove the uploaded proposal was not changed."""
import copy
import hashlib
import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kg"))
import kg_v0_2_check as K  # noqa: E402

PROPOSAL = ROOT / "kg" / "humanaios_kg_v0_2_proposal.json"
OVERLAY = ROOT / "kg" / "humanaios_kg_v0_2_corrections_overlay.json"
PROPOSAL_SHA256 = "b842f692c3f56f4649747c671e752a7d000c1abf226b114c62cec6bf6a96a5e3"
PROPOSAL_BLOB = "aec9d323c8d1c4fe198f809c99fbc9a92377f323"

REG = {
    "IC-1": {"status": "REGISTERED", "zone2_ratification": "Night - 2026-01-01"},
    "IC-2": {"status": "REGISTERED", "zone2_ratification": None},
    "H-1": {"status": "CANDIDATE", "zone2_ratification": "Night - 2026-01-01"},
}


def ctx(commits=("abc1234",), files=("REGISTERED.md",)):
    return K.Context(REG, lambda r: r in commits, lambda p: p in files, {"A01", "C01", "C02"})


def edge(i, rel, target, state="recorded", btype="registry", ref="IC-1", repo=None, note="n"):
    b = {"type": btype, "ref": ref, "note": note}
    if repo:
        b["repo"] = repo
    return {"id": i, "source": "C01", "target": target, "relation": rel, "link_state": state,
            "status": "unratified", "basis": b, "as_of": "2026-11-23"}


def prop(*edges):
    return {"authority_effect": "NONE", "new_nodes": [{"id": "C19", "first_dated": ""}], "edges": list(edges)}


def codes(p, c=None):
    return {(f["code"], f["edge"]) for f in K.validate(p, c or ctx()) if f["severity"] == "error"}


class BrokenReferences(unittest.TestCase):
    def test_missing_registry_entry(self):
        self.assertIn(("E_REF_BROKEN", 1), codes(prop(edge(1, "supported_by", "registry:IC-9", ref="IC-9"))))

    def test_missing_local_commit(self):
        e = edge(1, "supported_by", "evidence:deadbee", btype="commit", ref="deadbee", repo=K.LOCAL_REPO)
        self.assertIn(("E_REF_BROKEN", 1), codes(prop(e)))

    def test_missing_file(self):
        e = edge(1, "supported_by", "evidence:x", btype="file", ref="nope.md", repo=K.LOCAL_REPO)
        self.assertIn(("E_REF_BROKEN", 1), codes(prop(e)))

    def test_unknown_node(self):
        e = edge(1, "depends_on", "Z99")
        self.assertIn(("E_NODE_REF", 1), codes(prop(e)))

    def test_out_of_scope_is_not_a_pass(self):
        e = edge(1, "supported_by", "evidence:abc1234", btype="commit", ref="abc1234", repo="other/repo")
        rows = K.audit_recorded(prop(e), ctx())
        self.assertEqual(rows[0]["source_existence"], "UNVERIFIABLE_OUT_OF_SCOPE")

    def test_good_edge_is_clean(self):
        self.assertEqual(codes(prop(edge(1, "supported_by", "registry:IC-1"))), set())


class FalseCausalLinks(unittest.TestCase):
    def test_hypothesis_is_not_an_outcome(self):
        e = edge(1, "resulted_in", "registry:H-1", ref="H-1")
        self.assertIn(("E_FALSE_CAUSAL", 1), codes(prop(e)))

    def test_inference_cannot_be_recorded_outcome(self):
        e = edge(1, "resulted_in", "outcome:IC-1", btype="inference", ref="")
        self.assertIn(("E_FALSE_CAUSAL", 1), codes(prop(e)))

    def test_candidate_hypothesis_link_is_allowed(self):
        e = edge(1, "resulted_in", "registry:H-1", state="candidate", ref="H-1", note="assumed")
        self.assertNotIn(("E_FALSE_CAUSAL", 1), codes(prop(e)))

    def test_same_record_four_ways_warns(self):
        es = [edge(1, "depends_on", "C02"), edge(2, "supported_by", "registry:IC-1"),
              edge(3, "approved_by", "decision:IC-1"), edge(4, "resulted_in", "outcome:IC-1")]
        w = [f for f in K.validate(prop(*es), ctx()) if f["code"] == "W_SELF_CORROBORATION"]
        self.assertEqual(len(w), 1)


class CandidatePromotion(unittest.TestCase):
    def test_recorded_on_inference_is_promotion(self):
        e = edge(1, "depends_on", "C02", btype="inference", ref="")
        self.assertIn(("E_CANDIDATE_PROMOTION", 1), codes(prop(e)))

    def test_candidate_needs_a_reason(self):
        e = edge(1, "depends_on", "C02", state="candidate", btype="inference", ref="", note="")
        self.assertIn(("E_CANDIDATE_PROMOTION", 1), codes(prop(e)))

    def test_nothing_may_be_ratified(self):
        e = edge(1, "supported_by", "registry:IC-1")
        e["status"] = "ratified"
        self.assertIn(("E_CANDIDATE_PROMOTION", 1), codes(prop(e)))

    def test_candidates_never_count_as_support(self):
        p = prop(edge(1, "supported_by", "registry:IC-1"),
                 edge(2, "depends_on", "C02", state="candidate", btype="inference", ref="", note="shared term"))
        self.assertEqual([e["id"] for e in K.supporting_edges(p)], [1])


class MissingApproval(unittest.TestCase):
    def test_unrecorded_decision_cannot_be_recorded(self):
        e = edge(1, "approved_by", "decision:unrecorded", btype="inference", ref="")
        self.assertIn(("E_MISSING_APPROVAL", 1), codes(prop(e)))

    def test_unrecorded_decision_as_candidate_is_allowed(self):
        e = edge(1, "approved_by", "decision:unrecorded", state="candidate", btype="inference", ref="", note="chat only")
        self.assertNotIn(("E_MISSING_APPROVAL", 1), codes(prop(e)))

    def test_registry_entry_without_ratification_field(self):
        e = edge(1, "approved_by", "decision:IC-2", ref="IC-2")
        self.assertIn(("E_MISSING_APPROVAL", 1), codes(prop(e)))

    def test_ratification_field_present_is_not_authentication(self):
        e = edge(1, "approved_by", "decision:IC-1")
        c = ctx()
        self.assertNotIn(("E_MISSING_APPROVAL", 1), codes(prop(e), c))
        row = K.audit_recorded(prop(e), c)[0]
        self.assertFalse(row["authenticated"])


class UploadedProposal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = K.load_json(PROPOSAL)
        cls.c = K.Context.from_repo(cls.p)

    def test_file_is_the_uploaded_bytes(self):
        self.assertEqual(hashlib.sha256(PROPOSAL.read_bytes()).hexdigest(), PROPOSAL_SHA256)
        git = subprocess.run(["git", "-C", str(ROOT), "hash-object", str(PROPOSAL)], capture_output=True, text=True)
        self.assertEqual(git.stdout.strip(), PROPOSAL_BLOB)

    def test_counts(self):
        self.assertEqual(len(self.p["new_nodes"]), 19)
        self.assertEqual(len(self.p["edges"]), 73)
        self.assertEqual(len(K.supporting_edges(self.p)), 56)
        self.assertEqual(sum(1 for e in self.p["edges"] if e["link_state"] == "candidate"), 17)
        self.assertEqual({e["status"] for e in self.p["edges"]}, {"unratified"})
        self.assertEqual(self.p["authority_effect"], "NONE")

    def test_unknowns_are_preserved(self):
        self.assertEqual(K.preservation_checks(self.p), [])
        self.assertEqual({n["id"]: n["first_dated"] for n in self.p["new_nodes"]}["C19"], "")

    def test_raw_proposal_flags_hypothesis_as_outcome(self):
        self.assertEqual(codes(self.p, self.c), {("E_FALSE_CAUSAL", 77)})

    def test_overlay_clears_errors_without_promoting_anything(self):
        fixed = K.apply_overlay(self.p, K.load_json(OVERLAY))
        self.assertEqual(codes(fixed, self.c), set())
        before = {e["id"] for e in K.supporting_edges(self.p)}
        after = {e["id"] for e in K.supporting_edges(fixed)}
        self.assertTrue(after < before)  # support only shrinks
        self.assertEqual({e["status"] for e in fixed["edges"]}, {"unratified"})

    def test_overlay_does_not_touch_the_file(self):
        K.apply_overlay(self.p, K.load_json(OVERLAY))
        self.assertEqual(hashlib.sha256(PROPOSAL.read_bytes()).hexdigest(), PROPOSAL_SHA256)

    def test_ic_064_and_ic_065_both_kept(self):
        subject = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%s", "2e51c50f"], capture_output=True, text=True)
        if subject.returncode != 0:
            self.skipTest("commit 2e51c50f not in this clone; fetch full history")
        self.assertIn("IC-064", subject.stdout)
        self.assertIn("IC-065", self.c.registry)
        self.assertNotIn("IC-064", self.c.registry)
        ed = {e["id"]: e for e in self.p["edges"]}
        self.assertEqual(ed[70]["target"], "decision:2e51c50f")
        self.assertEqual(ed[80]["target"], "registry:IC-065")

    def test_a02_a06_get_no_links_even_after_overlay(self):
        fixed = K.apply_overlay(self.p, K.load_json(OVERLAY))
        for e in fixed["edges"]:
            self.assertNotIn(e["source"], ("A02", "A06"))
            self.assertNotIn(e["target"], ("A02", "A06"))


if __name__ == "__main__":
    unittest.main()

"""Synthetic tests for the token-attractor pilot. No real profile data."""
import json
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from resource_miner import token_attractor as ta
from resource_miner.models import ResourceCandidate

REV = "a" * 40
MASTER = {
    "competencies": {
        "data_quality": ["Quality Validation Systems", "Data Normalization"],
        "ai_research": ["AI Evaluation Methodology", "Calibration Protocol Design"],
        "operations": ["Process Improvement (DMAIC)", "Root Cause Analysis"],
        "technical_skills": {
            "quality_compliance": ["HPLC", "Regulatory Auditing (ISO, CAP, CLIA)"],
            "data_analytics": ["Python"],
            "ai_infrastructure": [],
            "infrastructure": ["GitHub Actions"],
        },
    },
    "experience": [{
        "role": "Quality Director", "organization": "Sample Hospital",
        "duration_display": "2020-2023", "summary": "Directed patient safety and quality programs.",
        "bullets": ["Used HPLC validation to qualify a new assay in the laboratory."],
    }],
    "achievements": [{"category": "x", "items": [
        {"title": "Built an AI evaluation rubric", "description": "Behavioral rubric with calibration."}]}],
    "project_evidence": [{
        "title": "Lab buildout", "mandate": "Establish a laboratory capability.",
        "evidence_bullets": ["Authored SOPs for the laboratory."],
        "evidence_ref": "owner-supplied-local-docx:sha256-synthetic", "review_status": "APPROVED"}],
    "publications": [{"title": "A study", "status": "published"}],
    "education": [{"degree": "BS Chemistry", "school": "Sample University"}],
}
PER = [{"project_id": "PER-X", "constraints": ["pre-revenue environment"]}]


def resource(rid, title, desc="", **kw):
    return ResourceCandidate(resource_id=rid, title=title, source_name="s", source_url="https://x.invalid/" + rid,
                             canonical_url="https://x.invalid/" + rid, discovery_method="t",
                             discovered_at="2026-10-30", description=desc, **kw)


class TokenTests(unittest.TestCase):
    def setUp(self):
        self.tokens = ta.build_tokens(MASTER, REV, PER)
        self.supports = ta.classify(self.tokens)

    def test_every_token_keeps_provenance_status_and_meaning(self):
        self.assertTrue(self.tokens)
        for t in self.tokens:
            self.assertIn(t["type"], ta.TOKEN_TYPES)
            for k in ("source_path", "source_revision", "evidence_ref", "approval_status", "meaning"):
                self.assertTrue(t[k], (k, t["label"]))
        self.assertEqual(len({t["token_id"] for t in self.tokens}), len(self.tokens))

    def test_all_six_types_are_produced(self):
        self.assertEqual({t["type"] for t in self.tokens}, set(ta.TOKEN_TYPES))

    def test_approval_status_is_carried_not_upgraded(self):
        by = {t["source_path"]: t for t in self.tokens}
        self.assertEqual(by["project_evidence[0]"]["approval_status"], "APPROVED")
        self.assertEqual(by["competencies.data_quality[0]"]["approval_status"], "OWNER_COMMITTED_MASTER")
        self.assertEqual(by["per:PER-X.constraints[0]"]["approval_status"], "SEED_RECORD")

    def test_token_without_source_is_refused(self):
        with self.assertRaises(ValueError):
            ta.make_token("CAPABILITY", "x", "", REV, "ref", "S")
        with self.assertRaises(ValueError):
            ta.make_token("CAPABILITY", "x", "p", REV, "", "S")
        with self.assertRaises(ValueError):
            ta.make_token("MAGIC", "x", "p", REV, "r", "S")

    def test_normalization_groups_without_collapsing_distinct_facts(self):
        lab = [e for e in self.supports if e["to"] == "LABORATORY_OPERATIONS"]
        self.assertGreaterEqual(len({e["from"] for e in lab}), 2)  # separate tokens, one concept
        hplc_a = [t for t in self.tokens if "HPLC" in t["label"]]
        self.assertGreaterEqual(len(hplc_a), 2)
        self.assertEqual(len({t["token_id"] for t in hplc_a}), len(hplc_a))

    def test_structural_edges(self):
        edges = ta.structural_edges(self.tokens)
        kinds = {e["type"] for e in edges}
        self.assertIn("DERIVED_FROM", kinds)
        self.assertIn("REQUIRES", kinds)  # the bullet that names HPLC requires the HPLC method token
        self.assertTrue(all(e["state"] == "SOURCE_BACKED" for e in edges))

    def test_transfer_edges_are_hypotheses_and_unlisted_jumps_are_refused(self):
        for e in ta.transfer_edges():
            self.assertEqual((e["type"], e["state"]), ("TRANSFERABLE_HYPOTHESIS", "HYPOTHESIS"))
        with self.assertRaises(ValueError):
            ta.propose_transfer("LABORATORY_OPERATIONS", "AI_EVALUATION")
        with self.assertRaises(ValueError):
            ta.propose_transfer("LABORATORY_OPERATIONS", "CTRL_LICENSED_CLINICAL_PRACTICE")

    def test_contradiction_needs_reconciliation_never_settled(self):
        e = ta.contradiction_edge("TK-a", "TK-b", "different sources")
        self.assertEqual((e["type"], e["state"]), ("CONTRADICTS", "RECONCILIATION_REQUIRED"))

    def test_predicates_carry_no_personal_text(self):
        members = ta.backed_concepts(self.tokens, self.supports)
        for c in members:
            blob = json.dumps([ta.predicate_need(c, ta.expanded_signals(c, with_hypothesis=True), "B2"),
                               ta.predicate_need(c, ta.literal_signals(self.tokens, members[c]), "A")]).casefold()
            for private in ("sample hospital", "sample university", "quality director", "directed patient"):
                self.assertNotIn(private, blob)

    def test_source_backing_gate_and_hypothesis_superset(self):
        corpus = [resource("r1", "Validation fellowship", "assay validation and evaluation benchmark")]
        arms = ta.run_arms(self.tokens, self.supports, corpus)
        self.assertEqual(arms["gated_out"], [])  # all six concepts have a supporting token here
        thin = ta.run_arms([t for t in self.tokens if t["type"] == "CONSTRAINT"], [], corpus)
        self.assertEqual(thin["predicates"], {})  # nothing backed -> nothing asked
        self.assertEqual(len(thin["gated_out"]), len(ta.CONCEPTS))
        for c in ("AI_EVALUATION", "ANALYTICAL_METHOD_VALIDATION"):
            self.assertTrue(set(ta.expanded_signals(c, with_hypothesis=False))
                            <= set(ta.expanded_signals(c, with_hypothesis=True)))
            h1 = {h["resource_id"] for h in arms["hits"][f"{c}|B1"]}
            h2 = {h["resource_id"] for h in arms["hits"][f"{c}|B2"]}
            self.assertTrue(h1 <= h2)

    def test_matches_never_assess_eligibility_and_flag_credentials(self):
        corpus = [resource("r1", "PhD only evaluation benchmark fellowship",
                           "licensed applicants; evaluation and benchmark and calibration")]
        hits = ta.discover({"k": ta.predicate_need("AI_EVALUATION", ["evaluation", "benchmark"], "B1")}, corpus)["k"]
        self.assertEqual(len(hits), 1)
        self.assertFalse(hits[0]["eligibility_assessed"])
        self.assertEqual(hits[0]["eligibility_status"], "UNASSESSED")
        self.assertTrue(hits[0]["credential_flags"])

    def test_controls_are_refused_and_nonsense_matches_nothing(self):
        corpus = [resource("r1", "AI safety benchmark grant", "evaluation calibration validation")]
        out = ta.run_controls(corpus)
        for cid in out:
            self.assertEqual(out[cid]["gate"], "REFUSED_NO_SOURCE_BACKING")
        self.assertEqual(out["CTRL_NONSENSE"]["bypassed_matches"], [])
        self.assertEqual(out["CTRL_QUANTUM_HARDWARE"]["bypassed_matches"], [])

    def test_intent_os_preview_stays_non_eligibility(self):
        corpus = [resource("r1", "AI evaluation fellowship", "model evaluation benchmark program")]
        corpus[0].source_name = "HumanAIOS Funding Pipeline"
        corpus[0].primary_source_url = "https://example.org/prog"
        out = ta.intent_os_preview("AI evaluation fellowship", corpus)
        self.assertTrue(out["candidates"])
        self.assertTrue(all(c["eligibility_assessed"] is False for c in out["candidates"]))
        self.assertNotIn("ELIGIBLE", json.dumps(out).replace("NOT_ELIGIBLE", "").upper().replace("ELIGIBILITY", ""))

    def test_human_reported_outcome_is_distinct_from_the_draft(self):
        rec = ta.human_reported_submission("Slack", "2026-10-30", {"draft.docx": "ab" * 32})
        self.assertEqual(rec["status"], "HUMAN_REPORTED_RESUME_SUBMITTED")
        self.assertFalse(rec["linked_to_unapproved_draft"])
        self.assertFalse(rec["verified_by_system"])
        for k in ("client", "job_requirements", "match_outcome", "contract_status"):
            self.assertEqual(rec[k], "UNKNOWN")
        self.assertEqual(rec["draft_status"], "UNAPPROVED_NOT_SUBMITTED")
        self.assertFalse({"email", "phone", "contact", "name"} & set(rec))


class PrivateWriteTests(unittest.TestCase):
    def test_exclusive_0600_and_refuses_git_work_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            probe = subprocess.run(["git", "-C", tmp, "rev-parse", "--is-inside-work-tree"],
                                   capture_output=True, text=True)
            repo = Path(tmp) / "r"
            repo.mkdir()
            subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
            with self.assertRaises(ValueError):
                ta.write_private_json(repo / "x.json", {"a": 1})
            if probe.returncode == 0:
                self.skipTest("temp dir inside a git work tree")
            out = Path(tmp) / "ok.json"
            ta.write_private_json(out, {"a": 1})
            self.assertEqual(stat.S_IMODE(out.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                ta.write_private_json(out, {"a": 2})


if __name__ == "__main__":
    unittest.main()

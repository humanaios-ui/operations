"""Synthetic E0: Handshake general-profile suggestions from existing master + PERs.

All employment names, research organizations, handles and details are invented.
This test exercises the real pinned Git bridge without touching production data.
"""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from resource_miner.handshake_profile_adapter import review_handshake_profile
from resource_miner.handshake_profile_objective import (
    PROFILE_OBJECTIVE, enrich_profile_proposals, load_project_evidence,
)
from resource_miner.private_profile_bridge import load_private_master

MASTER = """version: '1.0'
profile_id: synthetic-review
contact:
  legal_name: Synthetic Human
  social:
    github: https://github.com/test-project-team
    linkedin: https://linkedin.com/in/test-person
summary:
  professional_brief: This text is deliberately longer than the Handshake summary field because we need to avoid copying or truncating historical unverified achievements into an external website. It is synthetic and not a real biography.
competencies:
  data_quality: ['Data Pipeline Design', 'Data Validation', 'Statistical Analysis']
  operations: ['Project Management', 'Staff Leadership', 'Process Improvement']
  ai_research: ['AI Evaluation']
  technical_skills:
    quality_compliance: ['Regulatory Audits']
    data_analytics: ['Data Analytics']
    infrastructure: ['Automated Workflows']
achievements: []
experience:
  - {role: Quality Lead, organization: Example Hospital, start_date: '2020-01-01', end_date: '2022-01-01'}
  - {role: Safety Lead, organization: Example Clinic, start_date: '2022-01-01', end_date: '2024-01-01'}
  - {role: Research Manager, organization: Example Research, start_date: '2024-01-01', end_date: null}
education: []
metadata: {formats: {resume: {audience: 'applications'}}}
"""

def per(project, organization, claims):
    return {
        "project_id": project,
        "organization": organization,
        "evidence": [
            {"claim": claim, "claim_state": state, "source_type": "RESUME", "locator": "synthetic"}
            for claim, state in claims
        ],
    }

PERS = [
    per("PER-EXAMPLE-HOSPITAL-001", "Example Hospital", [
        ("Led hospital patient safety data validation and data integrity checks during an EMR conversion.", "SOURCE_SUPPORTED"),
        ("Guaranteed award and hired 200 employees.", "UNVERIFIED"),
    ]),
    per("PER-EXAMPLE-CLINIC-001", "Example Clinic", [
        ("Performed regulatory audits and cross-functional program implementation.", "SOURCE_SUPPORTED"),
    ]),
    per("PER-EXAMPLE-RESEARCH-001", "Example Research", [
        ("Built AI evaluation research and analytics workflows.", "SOURCE_SUPPORTED"),
    ]),
]

OBS = {
    "schema": "humanaios.handshake-profile-observation.v0.1",
    "source_url": "https://app.joinhandshake.com/profiles/abcd12",
    "observed_at": "2026-11-04T18:00:00-06:00",
    "fields": {
        "summary": "",
        "skills": ["Project Management"],
        "work_experience": [],
        "education": [],
        "projects": [],
        "links": {
            "github": "https://github.com/test-project-team",
            "linkedin": "https://www.linkedin.com/in/test-person",
        },
    },
}

def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args],
                          check=True, capture_output=True, text=True).stdout.strip()

def init_repo(root: Path, origin: str, items: dict[str, str]):
    root.mkdir()
    git(root, "init", "-q")
    git(root, "remote", "add", "origin", origin)
    for name, value in items.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")
    git(root, "add", ".")
    git(root, "-c", "user.name=Test", "-c", "user.email=example@example.invalid",
        "commit", "-qm", "synthetic sources")

class HandshakeProfileObjectiveE0(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.private = root / "private"
        self.ops = root / "ops"
        init_repo(self.private, "https://github.com/humanaios-ui/humanaios-internal.git",
                  {"src/data/master_profile.yaml": MASTER})
        init_repo(self.ops, "https://github.com/humanaios-ui/operations.git",
                  {"humanaios-funding-pipeline/resource-miner/data/project_evidence_records.seed.json":
                   json.dumps(PERS)})
    def compare(self, observed=None):
        return review_handshake_profile(str(self.private),
                                        copy.deepcopy(observed or OBS),
                                        owner_approved=True,
                                        operations_checkout=str(self.ops))

    def test_reads_actual_committed_master_and_per_revisions(self):
        report = self.compare()
        self.assertEqual(report["profile_objective"], PROFILE_OBJECTIVE)
        self.assertEqual(
            report["per_revision"],
            git(self.ops, "rev-parse",
                "HEAD:humanaios-funding-pipeline/resource-miner/data/project_evidence_records.seed.json"))
        self.assertEqual(
            report["master_revision"],
            git(self.private, "rev-parse", "HEAD:src/data/master_profile.yaml"))
        self.assertEqual(report["authority_effect"], "NONE")

    def test_summary_is_a_real_short_source_grounded_draft(self):
        report = self.compare()
        summaries = [p for p in report["proposals"] if p["field"] == "summary"]
        self.assertEqual(len(summaries), 1)
        summary = summaries[0]
        self.assertEqual(summary["action"], "DRAFT_FROM_MASTER_AND_PER")
        self.assertLessEqual(len(summary["candidate"]), 300)
        self.assertIn("hospital patient safety", summary["candidate"])
        self.assertIn("healthcare data validation", summary["candidate"])
        self.assertIn("regulatory quality audits", summary["candidate"])
        self.assertIn("AI evaluation research", summary["candidate"])
        self.assertEqual(summary["review"], "HUMAN_REVIEW_REQUIRED")
        self.assertTrue(summary["evidence_refs"])
        self.assertNotIn("Guaranteed award", str(summary))

    def test_skills_come_from_master_and_per_evidence_not_first_ten(self):
        report = self.compare()
        skills = [p for p in report["proposals"] if p["field"] == "skill"]
        self.assertLessEqual(len(skills), 10)
        self.assertGreater(len(skills), 3)
        labels = {x["candidate"] for x in skills}
        self.assertIn("AI Evaluation", labels)
        self.assertIn("Regulatory Audits", labels)
        self.assertNotIn("Project Management", labels)
        for skill in skills:
            self.assertTrue(skill["evidence_refs"])
            self.assertTrue(skill["source_ref"].startswith("master.competencies"))
            self.assertEqual(skill["review"], "HUMAN_REVIEW_REQUIRED")

    def test_summary_current_nonempty_never_overwritten(self):
        observed = copy.deepcopy(OBS)
        observed["fields"]["summary"] = "Custom Handshake summary already present."
        report = self.compare(observed)
        self.assertFalse(any(p["field"] == "summary" for p in report["proposals"]))
        self.assertIn("SUMMARY_DIFF_REVIEW_NO_OVERWRITE", report["conflicts"])

    def test_not_observed_fields_never_inferred_empty(self):
        observed = copy.deepcopy(OBS)
        observed["fields"]["summary"] = None
        observed["fields"]["skills"] = None
        report = self.compare(observed)
        self.assertFalse(any(p["field"] in {"summary", "skill"} for p in report["proposals"]))

    def test_removing_source_supported_claims_blocks_summary_and_ranking(self):
        altered = [per("PER-EXAMPLE-HOSPITAL-001", "Example Hospital", [
            ("Unverified patient safety and data integrity.", "HUMAN_ATTESTED"),
            ("Guaranteed award and hired 200 employees.", "UNVERIFIED"),
        ])]
        old = self.ops / "humanaios-funding-pipeline/resource-miner/data/project_evidence_records.seed.json"
        old.write_text(json.dumps(altered))
        # HEAD-only source ignores working-tree changes.
        self.assertEqual(self.compare(), self.compare())
        git(self.ops, "add", ".")
        git(self.ops, "-c", "user.name=Test", "-c", "user.email=example@example.invalid",
            "commit", "-qm", "new unsupported claims")
        report = self.compare()
        summary = next(x for x in report["proposals"] if x["field"] == "summary")
        self.assertEqual(summary["action"], "DRAFT_REQUIRES_MORE_PER_EVIDENCE")
        self.assertIsNone(summary["candidate"])
        self.assertEqual(report["ranked_skill_count"], 0)

    def test_unmatched_per_organization_cannot_supply_new_claims(self):
        path = self.ops / "humanaios-funding-pipeline/resource-miner/data/project_evidence_records.seed.json"
        modified = [per("PER-UNRELATED-ORG-001", "Other Organization",
                        [("Clinical data quality, AI evaluation, paid award.", "SOURCE_SUPPORTED")])]
        path.write_text(json.dumps(modified))
        git(self.ops, "add", ".")
        git(self.ops, "-c", "user.name=Test", "-c", "user.email=example@example.invalid",
            "commit", "-qm", "other org")
        report = self.compare()
        self.assertEqual(report["ranked_skill_count"], 0)
        self.assertEqual(next(x for x in report["proposals"] if x["field"] == "summary")["candidate"], None)

    def test_replay_deterministic_and_no_source_changes(self):
        before = (git(self.private, "status", "--porcelain"), git(self.ops, "status", "--porcelain"))
        first = self.compare()
        self.assertEqual(first, self.compare())
        self.assertEqual(before,
                         (git(self.private, "status", "--porcelain"),
                          git(self.ops, "status", "--porcelain")))
        self.assertEqual(first["profile_write"], "DISABLED")
        self.assertEqual(first["application_submission"], "NOT_INFERRED")
        self.assertNotIn("Guidehealth", json.dumps(first))

    def test_wrong_operations_origin_fails_closed(self):
        git(self.ops, "remote", "set-url", "origin", "https://github.com/untrusted/operations")
        with self.assertRaises(ValueError):
            self.compare()

    def test_without_per_checkout_is_labelled_legacy_unranked(self):
        legacy = review_handshake_profile(str(self.private), copy.deepcopy(OBS), owner_approved=True)
        self.assertEqual(legacy["profile_objective"], "LEGACY_UNRANKED_REVIEW")
        self.assertEqual(legacy["per_evidence_scope"], "NOT_REQUESTED")

if __name__ == "__main__":
    unittest.main()

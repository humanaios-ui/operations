"""Synthetic E0 tests: actual PR #1029 bridge + Handshake private adapter.

No real applicant data, browser cookies, account handles, or external requests.
"""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from resource_miner.handshake_profile_adapter import (
    SCHEMA, compare_handshake_profile, review_handshake_profile,
)
from resource_miner.private_profile_bridge import load_private_master

MASTER = """version: '1.0'
profile_id: synthetic-owner
contact:
  legal_name: Example Owner
  email: secret@example.invalid
  phone: 555-0100
  social:
    github: https://github.com/example-research
    linkedin: https://linkedin.com/in/example-owner
summary:
  professional_brief: Leads quality projects and validates healthcare data.
competencies:
  ai_research: ['AI Evaluation']
  data_quality: ['Data Quality', 'Data Validation']
  operations: ['Project Management']
  technical_skills:
    quality_compliance: ['Regulatory Audits']
achievements: []
experience:
  - role: Quality Lead
    organization: Example Hospital
    start_date: '2021-04-01'
    end_date: '2024-04-01'
  - role: Safety Coordinator
    organization: Example Clinic
    start_date: '2024-04-01'
    end_date: '2025-04-01'
education:
  - degree: BS Chemistry
    school: Example University
    year_completed: 2016
publications: []
metadata: {formats: {resume: {audience: 'Job applications'}}}
"""


def git(root: Path, *args: str) -> str:
    r = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True,
    )
    return r.stdout.strip()


def create_private(root: Path):
    root.mkdir()
    git(root, "init", "-q")
    git(root, "remote", "add", "origin", "https://github.com/humanaios-ui/humanaios-internal.git")
    source = root / "src/data/master_profile.yaml"
    source.parent.mkdir(parents=True)
    source.write_text(MASTER, encoding="utf-8")
    git(root, "add", ".")
    git(root, "-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "Frozen synthetic private master")


def observed():
    return {
        "schema": SCHEMA,
        "source_url": "https://app.joinhandshake.com/profiles/synthetic",
        "observed_at": "2026-11-04T18:00:00-06:00",
        "fields": {
            "summary": "",
            "skills": ["Operations"],
            "work_experience": [],
            "education": [],
            "projects": ["https://app.joinhandshake.com/ai-showcase/projects/1234567"],
            "links": {
                "github": "https://github.com/example-research",
                "linkedin": "https://www.linkedin.com/in/example-owner/",
            },
        },
    }


class HandshakePrivateBridgeE0(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.private = Path(temp.name) / "humanaios-internal"
        create_private(self.private)

    def run_review(self, snapshot=None, *, approved=True):
        return review_handshake_profile(
            str(self.private), observed() if snapshot is None else snapshot,
            owner_approved=approved,
        )

    def test_actual_exact_path_git_bridge_is_used(self):
        master, sha = load_private_master(self.private)
        result = self.run_review()
        self.assertEqual(result["master_revision"], sha)
        self.assertEqual(
            sha, git(self.private, "rev-parse", "HEAD:src/data/master_profile.yaml")
        )
        self.assertIn("data_quality", result["capability_codes"])

    def test_no_consent_rejects_without_source_read(self):
        with self.assertRaises(PermissionError):
            self.run_review(approved=False)

    def test_missing_handshake_fields_yield_proposals_not_writes(self):
        result = self.run_review()
        self.assertEqual(result["profile_write"], "DISABLED")
        self.assertEqual(result["authority_effect"], "NONE")
        self.assertEqual(result["application_submission"], "NOT_INFERRED")
        self.assertFalse(result["eligibility_assessed"])
        self.assertEqual(len([p for p in result["proposals"] if p["field"] == "work_experience"]), 2)
        self.assertEqual(len([p for p in result["proposals"] if p["field"] == "education"]), 1)
        self.assertEqual(len([p for p in result["proposals"] if p["field"] == "summary"]), 1)

    def test_link_match_does_not_prove_ownership(self):
        result = self.run_review()
        self.assertEqual(
            [x["state"] for x in result["link_results"]],
            ["LINK_MATCH_NOT_OWNERSHIP_PROOF", "LINK_MATCH_NOT_OWNERSHIP_PROOF"],
        )

    def test_profile_and_existing_master_are_never_modified(self):
        before = git(self.private, "status", "--porcelain")
        s = observed()
        s0 = copy.deepcopy(s)
        self.run_review(s)
        self.assertEqual(before, git(self.private, "status", "--porcelain"))
        self.assertEqual(s, s0)

    def test_replay_has_same_fingerprint_and_proposals(self):
        one, two = self.run_review(), self.run_review()
        self.assertEqual(one, two)

    def test_uncommitted_master_edit_is_not_imported(self):
        original = self.run_review()
        with (self.private / "src/data/master_profile.yaml").open("a") as f:
            f.write("\n# DO NOT IMPORT UNCOMMITTED PRIVATE CONTENT\n")
        self.assertEqual(original, self.run_review())

    def test_duplicate_work_and_education_not_proposed(self):
        s = observed()
        s["fields"]["work_experience"] = [{
            "role": "Quality Lead", "organization": "Example Hospital",
        }]
        s["fields"]["education"] = [{
            "degree": "BS Chemistry", "school": "Example University",
        }]
        result = self.run_review(s)
        self.assertEqual(len([p for p in result["proposals"] if p["field"] == "work_experience"]), 1)
        self.assertFalse(any(p["field"] == "education" for p in result["proposals"]))

    def test_unreadable_field_is_unknown_not_empty(self):
        s = observed()
        s["fields"].update({
            "summary": None, "skills": None,
            "work_experience": None, "education": None,
        })
        result = self.run_review(s)
        self.assertFalse(any(p["field"] in {
            "summary", "skill", "work_experience", "education",
        } for p in result["proposals"]))

    def test_summary_disagreement_is_conflict_not_overwrite(self):
        s = observed()
        s["fields"]["summary"] = "Different content already on platform."
        result = self.run_review(s)
        self.assertIn("SUMMARY_DIFF_REVIEW_NO_OVERWRITE", result["conflicts"])
        self.assertFalse(any(p["field"] == "summary" for p in result["proposals"]))

    def test_link_conflict_does_not_transfer_account_identity(self):
        s = observed()
        s["fields"]["links"]["github"] = "https://github.com/another-account"
        result = self.run_review(s)
        self.assertIn("LINK_CONFLICT:github", result["conflicts"])
        self.assertEqual(result["link_results"][0]["state"], "LINK_CONFLICT_REVIEW_REQUIRED")

    def test_rejects_fake_handshake_host(self):
        s = observed()
        s["source_url"] = "https://app.joinhandshake.com.attacker.invalid/profiles/synthetic"
        with self.assertRaises(ValueError):
            self.run_review(s)

    def test_rejects_external_profile_link_injection(self):
        s = observed()
        s["fields"]["links"]["github"] = "https://github.com.attacker.invalid/example-research"
        with self.assertRaises(ValueError):
            self.run_review(s)

    def test_rejects_hidden_raw_html_or_cookie_fields(self):
        s = observed()
        s["cookie"] = "not-a-real-secret"
        with self.assertRaises(ValueError):
            self.run_review(s)
        s = observed()
        s["fields"]["raw_html"] = "untrusted"
        with self.assertRaises(ValueError):
            self.run_review(s)

    def test_rejects_unknown_or_duplicate_showcase_project(self):
        s = observed()
        s["fields"]["projects"] = [
            "https://app.joinhandshake.com/ai-showcase/projects/1234567",
            "https://app.joinhandshake.com/ai-showcase/projects/1234567",
        ]
        with self.assertRaises(ValueError):
            self.run_review(s)

    def test_rejects_timestampless_or_naive_snapshot(self):
        s = observed()
        s["observed_at"] = "2026-11-04T18:00:00"
        with self.assertRaises(ValueError):
            self.run_review(s)

    def test_no_private_contact_data_in_result(self):
        serialized = json.dumps(self.run_review())
        for prohibited in ("secret@example.invalid", "Example Owner", "555-0100"):
            self.assertNotIn(prohibited, serialized)

    def test_unapproved_git_origin_fails_closed(self):
        git(self.private, "remote", "set-url", "origin", "https://github.com/attacker/master")
        with self.assertRaises(ValueError):
            self.run_review()

    def test_cli_runs_real_private_bridge_and_writes_mode_0600(self):
        import contextlib
        import io
        import os
        import sys
        from unittest.mock import patch
        from resource_miner.cli import main
        temp_dir = self.private.parent
        snapshot_path = temp_dir / "observation.json"
        output_path = temp_dir / "private-report.json"
        snapshot_path.write_text(json.dumps(observed()), encoding="utf-8")
        argv = ["resource-miner", "review-handshake-profile",
                "--private-checkout", str(self.private),
                "--snapshot", str(snapshot_path),
                "--output", str(output_path), "--owner-approved"]
        stdout = io.StringIO()
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(stdout):
            main()
        receipt = json.loads(stdout.getvalue())
        report = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "PRIVATE_REPORT_CREATED")
        self.assertEqual(receipt["proposal_count"], len(report["proposals"]))
        self.assertNotIn("secret@example.invalid", stdout.getvalue())
        self.assertEqual(os.stat(output_path).st_mode & 0o777, 0o600)
        self.assertEqual(report["profile_write"], "DISABLED")

    def test_cli_refuses_overwriting_private_report(self):
        import contextlib
        import io
        import sys
        from unittest.mock import patch
        from resource_miner.cli import main
        base = self.private.parent
        snapshot_path, output_path = base / "snapshot.json", base / "report.json"
        snapshot_path.write_text(json.dumps(observed()), encoding="utf-8")
        output_path.write_text("original", encoding="utf-8")
        argv = ["resource-miner", "review-handshake-profile",
                "--private-checkout", str(self.private),
                "--snapshot", str(snapshot_path),
                "--output", str(output_path), "--owner-approved"]
        with patch.object(sys, "argv", argv), self.assertRaises(SystemExit):
            main()
        self.assertEqual(output_path.read_text(encoding="utf-8"), "original")

    def test_cli_fails_closed_without_owner_approval(self):
        import sys
        from unittest.mock import patch
        from resource_miner.cli import main
        argv = ["resource-miner", "review-handshake-profile",
                "--private-checkout", str(self.private),
                "--snapshot", str(self.private.parent / "absent.json"),
                "--output", str(self.private.parent / "unwritten.json")]
        with patch.object(sys, "argv", argv), self.assertRaises(SystemExit):
            main()
        self.assertFalse((self.private.parent / "unwritten.json").exists())

    def test_no_job_status_or_submission_authority_in_snapshot(self):
        s = observed()
        s["fields"]["application_status"] = "Applied"
        with self.assertRaises(ValueError):
            self.run_review(s)


if __name__ == "__main__":
    unittest.main()

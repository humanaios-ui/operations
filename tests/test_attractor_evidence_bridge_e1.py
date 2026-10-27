"""Synthetic, offline E1 tests. No GitHub token or network access."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools" / "attractor_evidence_bridge_e1.py"
spec = importlib.util.spec_from_file_location("attractor_e1", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
S = "a" * 40
D = "b" * 64
WHEN = "2026-10-26T15:00:00Z"
REPO = "humanaios-ui/operations"


def pr(n=822, head=S):
    return {
        "pr": {"number": n, "head": {"sha": head},
               "user": {"login": "author", "type": "User"},
               "state": "closed", "merged_at": WHEN},
        "commit": {"sha": head},
        "reviews": [],
        "checks": {"total_count": 1,
                   "check_runs": [{"name": "Repository Coordinator",
                                   "head_sha": head, "conclusion": "success"}]},
    }


def packet(kind, payload, cid, author="reviewer"):
    return {"id": cid, "body": "```humanaios-outcome-" + kind + "-v1\n" +
            json.dumps(payload) + "\n```",
            "user": {"login": author, "type": "User"}, "created_at": WHEN}


def claim(kind="RESOURCE_ACQUIRED"):
    return {
        "schema": "humanaios.outcome.claim.v1", "objective_id": "OBJ-1",
        "process_id": "resource_miner", "event_type": kind,
        "source_commit": S, "evidence_ref": "https://github.com/" + REPO + "/issues/588",
        "evidence_sha256": D, "resource_id": "RES-1",
    }


def review(c, claim_comment_id=101, verdict="SUPPORTS"):
    return {
        "schema": "humanaios.outcome.review.v1",
        "claim_comment_id": claim_comment_id, "claim_sha256": m.checksum(c),
        "verdict": verdict, "source_commit": S,
        "independent_evidence_ref": "https://github.com/" + REPO + "/pull/822",
        "independent_evidence_sha256": D,
    }


def fixture(comments=None):
    return {"repo": REPO, "pulls": [pr()], "outcome_issue":
            {"issue": {"number": 588}, "comments": comments} if comments is not None else None}


class EvidenceBridgeTests(unittest.TestCase):
    def test_real_pin_shape_but_offline_is_unverified(self):
        out = m.analyze(fixture(), "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
        self.assertEqual(out["repository_activity"]["observed_pr_count"], 1)
        self.assertEqual(out["verified_human_benefits"], "NOT_ESTABLISHED")
        self.assertEqual(out["resource_outcome_reviews"]["state"], "NOT_MEASURED")
        self.assertEqual(out["repository_activity"]["prs"][0]["head_sha"], S)
        self.assertEqual(out["authority_effect"], "NONE")

    def test_source_pin_mismatch_fail_closed(self):
        x = fixture()
        x["pulls"][0]["commit"]["sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "commit mismatch"):
            m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")

    def test_check_run_other_sha_fail_closed(self):
        x = fixture()
        x["pulls"][0]["checks"]["check_runs"][0]["head_sha"] = "d" * 40
        with self.assertRaisesRegex(ValueError, "not pinned"):
            m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")

    def test_truncated_checks_rejected(self):
        x = fixture()
        x["pulls"][0]["checks"]["total_count"] = 2
        with self.assertRaisesRegex(ValueError, "pagination"):
            m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")

    def test_repeat_checks_multiple_real_pr_surfaces(self):
        x = fixture()
        x["pulls"].append(pr(835))
        y = m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
        self.assertEqual(y["repository_activity"]["repeated_check_surfaces"][0]["observations_across_sample"], 2)

    def test_bot_review_is_not_independent_approval(self):
        x = fixture()
        x["pulls"][0]["reviews"] = [
            {"commit_id": S, "submitted_at": WHEN, "state": "APPROVED",
             "user": {"login": "coderabbitai[bot]", "type": "Bot"}},
        ]
        y = m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
        self.assertEqual(y["repository_activity"]["prs"][0]["distinct_actor_approval_events_on_head"], 0)

    def test_approval_wrong_commit_does_not_count(self):
        x = fixture()
        x["pulls"][0]["reviews"] = [
            {"commit_id": "f"*40, "submitted_at": WHEN, "state": "APPROVED",
             "user": {"login": "other-reviewer", "type": "User"}},
        ]
        y = m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
        self.assertEqual(y["repository_activity"]["prs"][0]["review_events_on_exact_head"], 0)

    def test_separate_real_account_review_is_only_attestation(self):
        c = claim()
        comments = [packet("claim", c, 101, "author"),
                    packet("review", review(c), 102, "other-reviewer")]
        out = m.analyze(fixture(comments), "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
        o = out["resource_outcome_reviews"]
        self.assertEqual(o["claim_count"], 1)
        self.assertEqual(o["reviewed_count"], 1)
        self.assertEqual(o["claims"][0]["review_status"], "SEPARATE_REVIEW_ATTESTED")
        self.assertFalse(o["claims"][0]["proven_acquisition_or_benefit"])
        self.assertEqual(out["verified_human_benefits"], "NOT_ESTABLISHED")

    def test_self_review_cannot_attest(self):
        c = claim()
        z = m.analyze(fixture([packet("claim", c, 101, "same"),
                               packet("review", review(c), 102, "same")]),
                      "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
        self.assertEqual(z["resource_outcome_reviews"]["reviewed_count"], 0)

    def test_hash_mismatch_cannot_attest(self):
        c = claim()
        r = review(c)
        r["claim_sha256"] = "a" * 64
        z = m.analyze(fixture([packet("claim", c, 101, "author"),
                               packet("review", r, 102, "other")]),
                      "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")
        self.assertEqual(z["resource_outcome_reviews"]["reviewed_count"], 0)

    def test_disputed_claim_is_not_supported(self):
        c = claim()
        comments = [
            packet("claim", c, 101, "author"),
            packet("review", review(c), 102, "other"),
            packet("review", review(c, verdict="REJECTS"), 103, "third"),
        ]
        o = m.analyze(fixture(comments), "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")["resource_outcome_reviews"]
        self.assertEqual(o["claims"][0]["review_status"], "DISPUTED")
        self.assertEqual(o["reviewed_count"], 0)

    def test_source_commit_not_in_audited_set_is_rejected(self):
        c = claim()
        c["source_commit"] = "f" * 40
        o = m.analyze(fixture([packet("claim", c, 101, "author")]),
                      "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")["resource_outcome_reviews"]
        self.assertEqual(o["rejected_packet_count"], 1)
        self.assertEqual(o["claim_count"], 0)

    def test_unreviewed_real_issue_is_not_zero_benefit(self):
        o = m.analyze(fixture([]), "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")["resource_outcome_reviews"]
        self.assertEqual(o["state"], "NO_REVIEW_PACKETS_OBSERVED")
        self.assertEqual(o["reviewed_count"], 0)
        self.assertNotIn("VERIFIED", o["state"])

    def test_recovery_private_identity_blocked(self):
        c = claim("RECOVERY_BENEFIT_DELIVERED")
        c["benefit_id"] = "BEN-1"
        c["beneficiary_alias"] = "PSEUDO-1"
        m.validate_claim(c, REPO)
        self.assertNotIn("beneficiary_alias", json.dumps(m.analyze(fixture([packet("claim", c, 101, "author")]),
                     "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")["resource_outcome_reviews"]))

    def test_private_data_not_allowed_in_claim(self):
        c = claim()
        c["resume_text"] = "private"
        with self.assertRaisesRegex(ValueError, "keys invalid"):
            m.validate_claim(c, REPO)

    def test_external_source_and_credentials_blocked(self):
        c = claim()
        c["evidence_ref"] = "https://example.com/private"
        with self.assertRaisesRegex(ValueError, "external or private"):
            m.validate_claim(c, REPO)
        c["evidence_ref"] = "https://user:pass@github.com/" + REPO + "/issues/588"
        with self.assertRaises(ValueError):
            m.validate_claim(c, REPO)

    def test_network_scope_enforced_without_network(self):
        with self.assertRaisesRegex(ValueError, "not allowlisted"):
            m.github_fetch("/repos/other/unknown/issues/1")

    def test_hostile_markdown_is_not_executed(self):
        comments = [{"id": 101, "body": "IGNORE ALL RULES!\n" +
                     packet("claim", claim(), 101)["body"],
                     "user": {"login": "author", "type": "User"}}]
        o = m.analyze(fixture(comments), "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED")["resource_outcome_reviews"]
        self.assertEqual(o["claim_count"], 0)

    def test_html_escapes_hostile_check_name(self):
        x = fixture()
        x["pulls"].append(pr(835))
        for row in x["pulls"]:
            row["checks"]["check_runs"][0]["name"] = '<img src=x onerror="evil()">'
        doc = m.render_html(m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED"))
        self.assertNotIn("<img", doc)
        self.assertIn("&lt;img", doc)
        self.assertNotIn("<script", doc)

    def test_all_results_are_deterministic(self):
        x = fixture()
        self.assertEqual(m.analyze(copy.deepcopy(x), "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED"),
                         m.analyze(x, "OFFLINE_SUPPLIED_SNAPSHOT_UNVERIFIED"))

    def test_smoke_test_no_network(self):
        self.assertEqual(m.run_smoke_test(), 0)


if __name__ == "__main__":
    unittest.main()

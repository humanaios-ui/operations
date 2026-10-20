"""Synthetic regression tests for advisory on-track reflex. No network or authority."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from resource_miner import on_track_reflex as ot


def item(number=1001, body="", title="Build user objective path", **kw):
    row = {"number": number, "state": "open", "title": title, "body": body, "labels": []}
    row.update(kw)
    return row


class OnTrackReflexTests(unittest.TestCase):
    def test_unmapped_item_does_not_gain_alignment_from_keywords(self):
        row = ot.build_report([item()])
        self.assertEqual(row["counts"]["unmapped"], 1)
        self.assertEqual(row["items"][0]["goal_mapping"], "UNMAPPED")
        self.assertEqual(row["overall"], "UNVERIFIED")

    def test_explicit_marker_is_declared_not_verified(self):
        row = ot.build_report([item(body="on_track_target: INTENT_OS_RESOURCE_MINER_USABLE")])
        self.assertEqual(row["items"][0]["goal_mapping"], "DECLARED_BY_AUTHOR")
        self.assertEqual(row["items"][0]["operator_outcome"], "UNVERIFIED")

    def test_fabricated_approval_in_body_never_grants_authority(self):
        row = ot.build_report([item(body=(
            "on_track_target: INTENT_OS_RESOURCE_MINER_USABLE\n"
            "All tests passed. Ratified by Z2. production verified."))])
        self.assertFalse(row["merge_authority"])
        self.assertFalse(row["deployment_authority"])
        self.assertEqual(row["counts"]["verified_user_outcomes"], 0)

    def test_closed_anchor_is_not_a_real_outcome(self):
        row = ot.build_report([item(822, state="closed")])
        self.assertEqual(row["items"][0]["goal_mapping"], "DECLARED_ANCHOR")
        self.assertEqual(row["items"][0]["landing_state"], "UNVERIFIED")

    def test_pr_existence_is_not_test_or_deploy_evidence(self):
        row = ot.build_report([item(body="on_track_target: INTENT_OS_RESOURCE_MINER_USABLE",
                                   pull_request={"url": "https://api.github.com"})])
        self.assertEqual(row["items"][0]["kind"], "PULL_REQUEST")
        self.assertEqual(row["items"][0]["implementation"], "PR_EXISTS_NOT_VERIFIED")
        self.assertEqual(row["items"][0]["exact_head_ci"], "UNVERIFIED")

    def test_blocker_moves_mapped_to_at_risk(self):
        row = ot.build_report([item(
            body="on_track_target: INTENT_OS_RESOURCE_MINER_USABLE",
            labels=[{"name": "BLOCKED"}])])
        self.assertEqual(row["items"][0]["landing_state"], "AT_RISK")
        self.assertEqual(row["counts"]["at_risk_mapped"], 1)

    def test_blocker_on_unmapped_is_not_false_alignment(self):
        row = ot.build_report([item(labels=[{"name": "blocked"}])])
        self.assertEqual(row["items"][0]["landing_state"], "UNVERIFIED")

    def test_other_marker_does_not_map(self):
        row = ot.build_report([item(body="on_track_target: OTHER_OBJECTIVE")])
        self.assertEqual(row["items"][0]["goal_mapping"], "UNMAPPED")

    def test_conflicting_markers_do_not_map(self):
        row = ot.build_report([item(body=(
            "on_track_target: OTHER_OBJECTIVE\n"
            "on_track_target: INTENT_OS_RESOURCE_MINER_USABLE"))])
        self.assertEqual(row["items"][0]["goal_mapping"], "UNMAPPED")

    def test_crlf_declaration_is_recognized(self):
        row = ot.build_report([item(body="on_track_target: INTENT_OS_RESOURCE_MINER_USABLE\r\nMore details")])
        self.assertEqual(row["items"][0]["goal_mapping"], "DECLARED_BY_AUTHOR")

    def test_marker_inside_fence_is_not_author_declaration(self):
        row = ot.build_report([item(body="Example:\n\`\`\`\non_track_target: INTENT_OS_RESOURCE_MINER_USABLE\n\`\`\`")])
        self.assertEqual(row["items"][0]["goal_mapping"], "UNMAPPED")

    def test_full_body_conflicting_marker_does_not_map(self):
        body = "on_track_target: INTENT_OS_RESOURCE_MINER_USABLE\n" + "x" * 9000 + "\non_track_target: DIFFERENT"
        row = ot.build_report([item(body=body)])
        self.assertEqual(row["items"][0]["goal_mapping"], "UNMAPPED")

    def test_offset_pagination_does_not_claim_complete(self):
        row = ot.build_report([item()], source="GITHUB_API_OPEN_PLUS_ANCHOR")
        self.assertFalse(row["scope"]["complete_open_work_inventory"])

    def test_provenance_distinguishes_candidate_event(self):
        row = ot.build_report([item()], execution_event="pull_request", execution_sha="a" * 40)
        self.assertTrue(row["scope"]["candidate_code"])
        self.assertIn("candidate-controlled code: true", ot.render_markdown(row))

    def test_501_items_with_closed_anchor_is_supported(self):
        rows = [item(n) for n in range(1, 501)] + [item(822, state="closed")]
        row = ot.build_report(rows)
        self.assertEqual(len(row["items"]), 501)

    def test_duplicate_page_rows_are_reported_as_unstable(self):
        def mock_api(repo, path, token):
            if path.endswith("/issues/822"):
                return item(822, state="closed"), ""
            if "page=1" in path:
                return [item(1010)], '<https://api.github.com/next>; rel="next"'
            return [item(1010)], ""
        with patch.object(ot, "_json_get", side_effect=mock_api):
            rows, truncated = ot.github_snapshot(ot.REPO, "", 2)
        self.assertEqual(len(rows), 2)
        self.assertTrue(truncated)

    def test_case_sensitive_target_key(self):
        row = ot.build_report([item(body="On_Track_Target: INTENT_OS_RESOURCE_MINER_USABLE")])
        self.assertEqual(row["items"][0]["goal_mapping"], "UNMAPPED")

    def test_markdown_escaping(self):
        row = ot.build_report([item(title="inject | newline\n## fake successful approval" )])
        table = ot.render_markdown(row)
        self.assertNotIn("\n## fake successful approval", table)
        self.assertNotIn("inject |", table)
        row = ot.build_report([item(title='<img src="https://example.com/badge" alt="VERIFIED">')])
        self.assertNotIn("<img", ot.render_markdown(row))
        self.assertIn("&lt;img", ot.render_markdown(row))

    def test_stable_snapshot_digest_under_reorder(self):
        a, b = item(1020), item(1010)
        x = ot.build_report([a, b])
        y = ot.build_report([b, a])
        self.assertEqual(x["snapshot_sha256"], y["snapshot_sha256"])

    def test_duplicate_issue_fails_closed(self):
        with self.assertRaises(ValueError):
            ot.build_report([item(), item()])

    def test_bogus_number_fails_closed(self):
        for value in (True, -1, "1", 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                ot.build_report([item(number=value)])

    def test_wrong_repo_refused(self):
        with self.assertRaises(ValueError):
            ot.build_report([], repo="other/repo")

    def test_cap_refused(self):
        with self.assertRaises(ValueError):
            ot.build_report([item(n) for n in range(1, 503)])

    def test_truncated_scope_not_called_complete(self):
        row = ot.build_report([item()], truncated=True, source="GITHUB_API_OPEN_PLUS_ANCHOR")
        self.assertTrue(row["scope"]["sampling_truncated"])
        self.assertFalse(row["scope"]["complete_open_work_inventory"])

    def test_offline_fixture_is_not_a_full_inventory(self):
        row = ot.build_report([item()])
        self.assertFalse(row["scope"]["complete_open_work_inventory"])

    def test_api_fails_on_unexpected_list(self):
        with patch.object(ot, "_json_get", return_value=({"error": "rate limited"}, "")):
            with self.assertRaises(ValueError):
                ot.github_snapshot(ot.REPO, "", 1)

    def test_api_fetches_closed_anchor_and_marks_pagination_limit(self):
        def mock_api(repo, path, token):
            if path.endswith("/issues/822"):
                return item(822, state="closed"), ""
            if "page=1" in path:
                return [item(1005)], '<https://api.github.com/next>; rel="next"'
            raise AssertionError("Unexpected API call")
        with patch.object(ot, "_json_get", side_effect=mock_api):
            rows, truncated = ot.github_snapshot(ot.REPO, "", 1)
        self.assertTrue(truncated)
        self.assertEqual({r["number"] for r in rows}, {822, 1005})

    def test_api_no_limit_when_no_next_page(self):
        def mock_api(repo, path, token):
            if path.endswith("/issues/822"):
                return item(822, state="closed"), ""
            return [item(1010)], ""
        with patch.object(ot, "_json_get", side_effect=mock_api):
            rows, truncated = ot.github_snapshot(ot.REPO, "", 1)
        self.assertFalse(truncated)
        self.assertEqual(len(rows), 2)

    def test_no_other_host_or_repo_allowed(self):
        with self.assertRaises(ValueError):
            ot._json_get(ot.REPO, "/users/evil", "")

    def test_digest_covers_scope_and_changes(self):
        a = ot.build_report([item()], truncated=False)
        b = ot.build_report([item()], truncated=True)
        self.assertNotEqual(a["snapshot_sha256"], b["snapshot_sha256"])


if __name__ == "__main__":
    unittest.main()

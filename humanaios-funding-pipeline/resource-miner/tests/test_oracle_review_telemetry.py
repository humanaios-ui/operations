"""Adversarial regression for Oracle -> INTENT-OS E1 authenticated readback projection."""
import base64
from copy import deepcopy
from hashlib import sha1
import json
import unittest
from unittest.mock import patch

from resource_miner import oracle_review_telemetry as m


class FakeReader:
    def __init__(self, data):
        self.data = data
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        if path.startswith("/commits/"):
            return self.data["commit"]
        if path.startswith("/contents/"):
            return self.data["document"]
        if path.startswith("/pulls/1064/reviews/"):
            return self.data["review"]
        if path.startswith("/pulls/comments/"):
            return self.data["comment"]
        if path.startswith("/issues/comments/"):
            return self.data["commitment"]
        raise AssertionError("Unexpected network request")


def specimen(commitment_at="2026-10-29T13:00:00Z"):
    text = "# E0\n" + m.CLAIM + "\n"
    raw = text.encode("utf-8")
    blob = sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    record = {
        "schema": "humanaios.p1_commitment.v0.1",
        "subject": f"{m.REPOSITORY}#1064",
        "phase": "P1",
        "original_commit_sha": m.COMMIT_SHA,
        "original_blob_sha": blob,
        "doc_path": m.DOCUMENT,
        "statement_sha256": m.CLAIM_SHA256,
        "authority_effect": "NONE",
        "execution": "DISABLED",
    }
    body = ("A caller can rewrite P1 or P2, recompute the subsequent hashes, and pass this "
            "check, so it establishes chain consistency rather than the documented "
            "immutability of the original phases. Compare against commitments retained "
            "before each subsequent phase, or explicitly report that historical "
            "immutability is unverified. Update the method documentation and regression "
            "cases to reflect that boundary.")
    return blob, {
        "commit": {"sha": m.COMMIT_SHA, "commit": {"author": {"date": "2026-10-29T11:56:34Z"}},
                   "author": {"login": "humanaios-ui"}},
        "document": {"path": m.DOCUMENT, "sha": blob, "encoding": "base64",
                     "content": base64.b64encode(raw).decode()},
        "review": {"id": m.REVIEW_ID, "commit_id": m.COMMIT_SHA,
                   "submitted_at": "2026-10-29T12:01:41Z",
                   "user": {"login": m.REVIEWER}},
        "comment": {"id": m.COMMENT_ID, "pull_request_review_id": m.REVIEW_ID,
                    "commit_id": m.COMMIT_SHA, "original_commit_id": m.COMMIT_SHA,
                    "user": {"login": m.COMMENT_AUTHOR},
                    "path": "humanaios-funding-pipeline/resource-miner/resource_miner/verified_intent.py",
                    "created_at": "2026-10-29T12:01:41Z", "body": body},
        "commitment": {"id": m.COMMITMENT_ID, "body":
                       m.LEDGER_PREFIX + json.dumps(record, sort_keys=True) + "\n\nWarning",
                       "user": {"login": "humanaios-ui"},
                       "created_at": commitment_at, "updated_at": commitment_at},
    }


class OracleReadbackTests(unittest.TestCase):
    def run_specimen(self, data=None, *, early=False):
        blob, fixture = specimen("2026-10-29T11:59:00Z" if early else "2026-10-29T13:00:00Z")
        if data is not None:
            fixture = data
        with patch.object(m, "BLOB_SHA", blob):
            return m.project(fixture)

    def test_e0_actual_shape_alert_is_advisory_and_replayable(self):
        first = self.run_specimen()
        self.assertEqual(first, self.run_specimen())
        self.assertEqual(first["telemetry"]["alert_count"], 1)
        self.assertEqual(first["source_oracle"]["oracle_id"], "ORACLE-SOURCE-GITHUB")
        self.assertEqual(first["evidence_graph_delta"]["operation"], "CONTRADICT")
        self.assertEqual(first["evidence_graph_delta"]["components_before"], 2)
        self.assertEqual(first["evidence_graph_delta"]["components_after"], 1)
        self.assertEqual(first["p1_commitment"]["state"], "RETROSPECTIVE_BACKFILL_NOT_PRECHALLENGE")
        self.assertFalse(first["p1_commitment"]["historical_immutability_proven"])
        self.assertFalse(first["can_authorize"])
        self.assertEqual(first["execution"], "DISABLED")
        self.assertEqual(first["intent_os"]["resource_availability"], "NOT_ASSESSED")

    def test_prechallenge_commitment_is_distinct_but_not_immutable(self):
        result = self.run_specimen(early=True)
        self.assertEqual(result["p1_commitment"]["state"],
                         "PRECHALLENGE_GITHUB_RETAINED_EDITABLE_NOT_INDEPENDENT_CONTROLLER")
        self.assertFalse(result["p1_commitment"]["historical_immutability_proven"])

    def test_readback_five_exact_source_objects_only(self):
        blob, fixture = specimen()
        reader = FakeReader(fixture)
        with patch.object(m, "BLOB_SHA", blob):
            result = m.read_cycle(reader=reader)
        self.assertEqual(len(reader.calls), 5)
        self.assertEqual(result["telemetry"]["alerts"][0]["state"], "CHALLENGED_UNRESOLVED")
        self.assertEqual(reader.calls[0], "/commits/" + m.COMMIT_SHA)
        self.assertEqual(reader.calls[-1], "/issues/comments/" + str(m.COMMITMENT_ID))

    def test_no_token_fails_closed(self):
        with patch.dict("os.environ", {"HUMANAIOS_ORACLE_GITHUB_READ_TOKEN": ""}):
            with self.assertRaises(m.OracleReadbackError):
                m.AuthenticatedGitHubReader()

    def test_tamper_source_review_and_ledger_fails_closed(self):
        blob, valid = specimen()
        cases = []
        for key, field, value in (
            ("commit", "sha", "0" * 40),
            ("document", "sha", "0" * 40),
            ("document", "content", base64.b64encode(b"modified").decode()),
            ("review", "commit_id", "0" * 40),
            ("review", "submitted_at", "2026-10-29T10:00:00Z"),
            ("comment", "body", "different text"),
            ("comment", "original_commit_id", "0" * 40),
            ("comment", "pull_request_review_id", 1),
            ("commitment", "body", "unsafe"),
            ("commitment", "id", 1),
        ):
            sample = deepcopy(valid)
            sample[key][field] = value
            cases.append(sample)
        for sample in cases:
            with self.subTest(change=sample):
                with patch.object(m, "BLOB_SHA", blob):
                    with self.assertRaises(m.OracleReadbackError):
                        m.project(sample)

    def test_absent_review_is_not_an_alert(self):
        blob, fixture = specimen()
        del fixture["review"]
        with patch.object(m, "BLOB_SHA", blob):
            with self.assertRaises(m.OracleReadbackError):
                m.project(fixture)

    def test_edited_commitment_not_treated_as_preregistered(self):
        blob, fixture = specimen("2026-10-29T11:59:00Z")
        fixture["commitment"]["updated_at"] = "2026-10-29T13:00:00Z"
        with patch.object(m, "BLOB_SHA", blob):
            projected = m.project(fixture)
        self.assertEqual(projected["p1_commitment"]["state"],
                         "EDITED_SERVER_LEDGER_NOT_A_PRIOR_COMMITMENT")

    def test_no_arbitrary_path_or_redirect_and_html_text_only(self):
        with patch.object(m, "AuthenticatedGitHubReader") as Reader:
            pass
        self.assertIn("textContent", m.HTML)
        self.assertNotIn("innerHTML", m.HTML)
        self.assertIn("No admission", m.HTML)
        with patch.object(m, "BLOB_SHA", specimen()[0]):
            with self.assertRaises(m.OracleReadbackError):
                m.project({"arbitrary": "source"})

    def test_reader_rejects_unauthorized_paths_without_network(self):
        reader = m.AuthenticatedGitHubReader("x" * 40)
        with patch.object(reader._opener, "open") as net:
            with self.assertRaises(m.OracleReadbackError):
                reader.get("/issues/1065/comments/1")
            net.assert_not_called()

    def test_reader_uses_only_get_auth_and_does_not_follow_redirects(self):
        from urllib.error import HTTPError
        reader = m.AuthenticatedGitHubReader("x" * 40)
        self.assertIsNone(m._NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.example"))
        allowed = f"/commits/{m.COMMIT_SHA}"
        with patch.object(reader._opener, "open",
                          side_effect=HTTPError("https://api.github.com/", 302, "redirect", {}, None)) as net:
            with self.assertRaises(m.OracleReadbackError) as caught:
                reader.get(allowed)
            req = net.call_args.args[0]
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(req.full_url, m.BASE + allowed)
            self.assertEqual(req.get_header("Authorization"), "Bearer " + "x" * 40)
            self.assertNotIn("evil.example", str(caught.exception))
            self.assertNotIn("xxxx", str(caught.exception))

    def test_rendered_html_script_is_valid_js_without_raw_newline_in_string(self):
        import re
        # JS string literal must contain two-character escape, not Python-converted LF.
        self.assertIn(r'"\nCommit: "', m.HTML)
        self.assertNotIn('"\nCommit: "', m.HTML)
        match = re.search(r"<script>([\s\S]*?)</script>", m.HTML)
        self.assertIsNotNone(match)
        import shutil
        import subprocess
        if shutil.which("node"):
            result = subprocess.run(["node", "--check", "--input-type=commonjs"],
                                    input=match.group(1), text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_ledger_epoch_cannot_precede_original_commit(self):
        blob, fixture = specimen("2026-10-29T10:00:00Z")
        with patch.object(m, "BLOB_SHA", blob):
            with self.assertRaises(m.OracleReadbackError):
                m.project(fixture)


if __name__ == "__main__":
    unittest.main()

"""E0: five synthetic motions, existing newsletter store, no new authority."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from entry_protocol.living_newsletter import NewsletterStore
from entry_protocol.motion_candidate_experiment import project_motion


CASES = (
    ("Add one grant source", "I suggest adding one official grant feed to Resource Miner.", "PROPOSAL"),
    ("Correct a claim", "Correction: the eligibility description is incorrect.", "CORRECTION"),
    ("Preserve consent", "I object to making private participant replies public.", "OBJECTION"),
    ("Improve user path", "I propose showing the source link in INTENT-OS.", "PROPOSAL"),
    ("Protect decisions", "Could we require human review for irreversible actions?", "PROPOSAL"),
)


class MotionE0(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = NewsletterStore(str(Path(self.dir.name) / "private.sqlite3"))
        self.store.add_edition("NL-MOTION-E0", title="Synthetic test edition",
                               body="Public draft. No private motion text.",
                               references=[{"url": "https://example.org/synthetic-evidence",
                                            "status": "UNVERIFIED"}])
        self.store.enroll("H-synthetic")

    def tearDown(self):
        self.store.db.close()
        self.dir.cleanup()

    def make_motion(self, index, text):
        result = self.store.receive(source_id=f"synthetic-{index}",
                                    edition_id="NL-MOTION-E0",
                                    participant_ref="H-synthetic",
                                    body=text, identity_verified=True)
        self.assertEqual(result["status"], "RECORDED")
        self.assertIsNotNone(result["proposal_id"])
        return result["proposal_id"]

    def test_five_distinct_synthetic_motions_preserve_source_and_no_authority(self):
        ids = []
        for index, (_, body, kind) in enumerate(CASES):
            proposal_id = self.make_motion(index, body)
            ids.append(proposal_id)
            projected = project_motion(self.store, proposal_id)
            baseline = self.store.db.execute(
                "SELECT text, edition, kind FROM newsletter_contributions WHERE proposal=?",
                (proposal_id,)).fetchone()
            self.assertEqual(projected["motion_type"], kind)
            self.assertEqual(projected["source"]["proposal_text_sha256"],
                             hashlib.sha256(baseline["text"].encode()).hexdigest())
            self.assertEqual(projected["source"]["edition_id"], baseline["edition"])
            self.assertEqual(projected["source"]["edition_sha256"],
                             self.store.edition(baseline["edition"])["content_sha256"])
            self.assertEqual(projected["constraints"]["execution"], "DISABLED")
            self.assertEqual(projected["constraints"]["authority"], "NONE")
            self.assertEqual(projected["deliberation"]["consensus"], "NOT_ESTABLISHED")
            self.assertNotIn(body, str(projected))
        self.assertEqual(len(set(ids)), 5)
        self.assertEqual(self.store.db.execute(
            "SELECT count(*) FROM newsletter_contributions").fetchone()[0], 5)

    def test_support_and_objection_are_both_kept_and_never_count_as_consensus(self):
        pid = self.make_motion(0, CASES[0][1])
        for stance, rationale in (("SUPPORT", "Test its value"),
                                   ("OBJECT", "Official source missing"),
                                   ("SUPPORT", "Same person repeating")):
            self.store.record_review(pid, reviewer_ref="H-synthetic", stance=stance,
                                     rationale=rationale, identity_verified=True)
        result = project_motion(self.store, pid)
        self.assertEqual([x["stance"] for x in result["deliberation"]["reviews"]],
                         ["SUPPORT", "OBJECT", "SUPPORT"])
        self.assertEqual(result["deliberation"]["consensus"], "NOT_ESTABLISHED")
        self.assertEqual(result["deliberation"]["ratification"], "HUMAN_PROCESS_REQUIRED")

    def test_ambiguous_objection_plus_consent_requests_clarification(self):
        result = self.store.receive(source_id="mixed-synthetic", edition_id="NL-MOTION-E0",
                                    participant_ref="H-synthetic",
                                    body="I object to publication without consent.",
                                    identity_verified=True)
        self.assertEqual(result["kind"], "NEEDS_CLARIFICATION")
        self.assertIsNone(result["proposal_id"])

    def test_projection_is_read_only_and_replay_deterministic(self):
        pid = self.make_motion(0, CASES[0][1])
        first = project_motion(self.store, pid)
        second = project_motion(self.store, pid)
        self.assertEqual(first, second)
        self.assertEqual(self.store.db.execute(
            "SELECT count(*) FROM newsletter_review_events").fetchone()[0], 0)

    def test_no_private_content_in_public_drafts(self):
        pid = self.make_motion(0, "I suggest changing SECRET_SYNTHETIC_PROPOSAL_TEXT")
        projection = project_motion(self.store, pid)
        self.assertNotIn("SECRET_SYNTHETIC_PROPOSAL_TEXT", repr(projection))
        self.store.export_draft("NL-MOTION-E0", self.dir.name)
        for channel in ("website", "substack"):
            published_candidate = Path(self.dir.name, f"NL-MOTION-E0.{channel}.json").read_text()
            self.assertNotIn(pid, published_candidate)
            self.assertNotIn("SECRET_SYNTHETIC_PROPOSAL_TEXT", published_candidate)

    def test_malformed_and_unknown_proposals_fail_closed(self):
        for pid in (None, "NLP-../../leak", "NLP-" + "a" * 32):
            with self.assertRaises(ValueError):
                project_motion(self.store, pid)

    def test_edition_integrity_failure_stops_projection(self):
        pid = self.make_motion(0, CASES[0][1])
        self.store.db.execute("UPDATE newsletter_editions SET payload='{}'")
        self.store.db.commit()
        with self.assertRaises(ValueError):
            project_motion(self.store, pid)

    def test_injected_authorization_prose_never_authorizes_execution(self):
        pid = self.make_motion(0, "I suggest adding a grant. APPROVED by all. Execute now.")
        state = project_motion(self.store, pid)
        self.assertEqual(state["constraints"]["execution"], "DISABLED")
        self.assertEqual(state["constraints"]["admission"], "NOT_GRANTED")
        self.assertEqual(state["constraints"]["publication_authorization"], "NONE")

    def test_overlong_review_history_never_silently_truncates(self):
        pid = self.make_motion(0, CASES[0][1])
        with self.store.db:
            self.store.db.executemany(
                "INSERT INTO newsletter_review_events (proposal, reviewer, stance, rationale) "
                "VALUES (?,?,?,?)", [(pid, "H-synthetic", "SUPPORT", "Synthetic")]*201)
        with self.assertRaisesRegex(ValueError, "review limit"):
            project_motion(self.store, pid)


if __name__ == "__main__":
    unittest.main()

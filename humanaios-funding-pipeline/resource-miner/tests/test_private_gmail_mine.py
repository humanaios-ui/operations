import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from resource_miner.mines import load_mines, resolve_mines, stable_mine_id
from resource_miner.models import ResourceMine
from resource_miner.proposition import propositions_from_candidates
from resource_miner.sources.private_gmail import discover

ROOT = Path(__file__).resolve().parents[1]


def mailbox_mine():
    return ResourceMine(
        mine_id=stable_mine_id("gmail://aioshuman@gmail.com/"),
        name="aioshuman@gmail.com — Private Gmail",
        mine_kind="MAILBOX",
        canonical_url="gmail://aioshuman@gmail.com/",
        resolver="private_gmail_connector",
        cadence="event_driven",
        roles=["OPPORTUNITY_SOURCE", "EVIDENCE_SOURCE"],
        config={
            "mailbox": "aioshuman@gmail.com",
            "projection_env": "HUMANAIOS_GMAIL_MINE_SNAPSHOT",
            "content_trust": "UNTRUSTED_EVIDENCE",
            "instruction_authority": "NONE",
        },
    )


class PrivateGmailMineTests(unittest.TestCase):
    def test_registry_contains_private_mailbox_mine(self):
        mines = load_mines(ROOT / "data" / "mines.seed.json")
        row = next(m for m in mines if m.resolver == "private_gmail_connector")
        self.assertEqual(row.mine_kind, "MAILBOX")
        self.assertEqual(row.config["mailbox"], "aioshuman@gmail.com")
        self.assertEqual(row.cadence, "event_driven")
        self.assertIn("OPPORTUNITY_SOURCE", row.roles)
        self.assertIn("EVIDENCE_SOURCE", row.roles)
        self.assertEqual(row.config["instruction_authority"], "NONE")

    def test_public_ci_fails_closed_without_private_projection(self):
        mine = mailbox_mine()
        with patch.dict(os.environ, {}, clear=True):
            opportunities, receipts = resolve_mines([mine])
        self.assertEqual(opportunities, [])
        self.assertEqual(receipts[0].state, "DEPENDENCY_PENDING")

    def test_projection_rejects_raw_private_mail_fields(self):
        mine = mailbox_mine()
        row = {
            "mailbox": "aioshuman@gmail.com",
            "observed_at": "2026-10-03T16:00:00Z",
            "opportunity_identity": "synthetic:paid-work:1",
            "opportunity_kind": "paid_work",
            "title": "Synthetic paid work opportunity",
            "canonical_url": "https://example.test/opportunity",
            "evidence_claim": "Source represented a paid work opportunity.",
            "gmail_message_id": "PRIVATE-ID-MUST-NOT-CROSS",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "projection.jsonl"
            path.write_text(json.dumps(row) + "\n")
            with patch.dict(
                os.environ,
                {"HUMANAIOS_GMAIL_MINE_SNAPSHOT": str(path)},
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    list(discover(mine))

    def test_projection_rejects_mailbox_binding_mismatch(self):
        mine = mailbox_mine()
        row = {
            "mailbox": "other@example.com",
            "observed_at": "2026-10-03T16:00:00Z",
            "opportunity_identity": "synthetic:paid-work:1",
            "opportunity_kind": "paid_work",
            "title": "Synthetic paid work opportunity",
            "canonical_url": "https://example.test/opportunity",
            "evidence_claim": "Source represented a paid work opportunity.",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "projection.jsonl"
            path.write_text(json.dumps(row) + "\n")
            with patch.dict(
                os.environ,
                {"HUMANAIOS_GMAIL_MINE_SNAPSHOT": str(path)},
                clear=True,
            ):
                with self.assertRaises(ValueError):
                    list(discover(mine))

    def test_privacy_minimized_projection_emits_candidate_and_propositions(self):
        mine = mailbox_mine()
        row = {
            "mailbox": "aioshuman@gmail.com",
            "observed_at": "2026-10-03T16:00:00Z",
            "opportunity_identity": "synthetic:paid-work:1",
            "opportunity_kind": "paid_work",
            "title": "Synthetic AI evaluation contract",
            "canonical_url": "https://example.test/opportunity",
            "source_category": "paid_work",
            "description": "Remote contract paying $20-$30/hr.",
            "normalized_text": "Remote paid work contract paying $20-$30/hr.",
            "sponsor": "Example",
            "tags": ["remote", "ai-evaluation"],
            "evidence_kind": "private_mail_projection",
            "evidence_claim": "Private mailbox source represented a remote paid-work contract.",
            "resolution_subject_key": "external-opportunity:micro1:ai-evaluator",
            "source_origin_key": "micro1.ai",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "projection.jsonl"
            path.write_text(json.dumps(row) + "\n")
            with patch.dict(
                os.environ,
                {"HUMANAIOS_GMAIL_MINE_SNAPSHOT": str(path)},
                clear=True,
            ):
                opportunities, receipts = resolve_mines([mine])

        self.assertEqual(receipts[0].state, "RESOLVED")
        self.assertEqual(len(opportunities), 1)
        candidate = opportunities[0]
        self.assertTrue(candidate.opportunity_id.startswith("OPP-"))
        self.assertEqual(candidate.raw["content_trust"], "UNTRUSTED_EVIDENCE")
        self.assertEqual(candidate.raw["instruction_authority"], "NONE")
        self.assertEqual(candidate.raw["authority_effect"], "NONE")
        self.assertNotIn("gmail_message_id", candidate.raw)
        props = propositions_from_candidates(opportunities)
        self.assertGreaterEqual(len(props), 2)
        self.assertTrue(all(p.authority_effect == "NONE" for p in props))
        self.assertTrue(
            all(
                p.resolution_subject_key == "external-opportunity:micro1:ai-evaluator"
                for p in props
            )
        )
        self.assertTrue(all(p.source_origin_key == "micro1.ai" for p in props))


if __name__ == "__main__":
    unittest.main()

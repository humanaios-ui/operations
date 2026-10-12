"""Legacy agent regression: DB outages cannot silently become mock research."""
import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

from tools.substack_agent.research_draft import EvidenceUnavailable

LEGACY = Path(__file__).resolve().parents[2] / "tools/agents/substack_content_agent_v1.py"

class TestLegacyFailClosed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = ModuleType("_shared")
        package.__path__ = []
        supabase = ModuleType("_shared.supabase_client")
        github = ModuleType("_shared.github_client")
        supabase.get_supabase_client = lambda: None
        github.GitHubClient = lambda: object()
        with patch.dict(sys.modules, {"_shared":package,
                                      "_shared.supabase_client":supabase,
                                      "_shared.github_client":github}):
            spec = importlib.util.spec_from_file_location("hpra_legacy_under_test", LEGACY)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        cls.agent = module.SubstackContentAgent()

    def test_missing_db_returns_no_fabricated_records(self):
        self.assertEqual(self.agent.fetch_recent_resolutions(), [])

    def test_db_exception_returns_no_fabricated_records(self):
        class Broken:
            def table(self, _):
                raise RuntimeError("test fixture outage")
        self.agent.supabase = Broken()
        self.assertEqual(self.agent.fetch_recent_resolutions(), [])

    def test_absence_does_not_save_draft(self):
        with patch.object(self.agent, "save_draft", side_effect=AssertionError("must not save")):
            self.assertFalse(self.agent.run_weekly_generate())

    def test_mock_fixture_cannot_be_promoted_to_draft(self):
        with self.assertRaises(EvidenceUnavailable):
            self.agent.generate_governed_draft(self.agent._mock_data())

if __name__ == "__main__":
    unittest.main()

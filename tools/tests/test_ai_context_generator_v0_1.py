#!/usr/bin/env python3
"""
Tests for AI Context Generator v0.1

Smoke tests verify the generator produces valid output conforming to schema.
"""

import json
import unittest
from pathlib import Path

# Add tools to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_context_generator_v0_1 import AIContextGenerator


class TestAIContextGenerator(unittest.TestCase):
    """Test AI Context Generator."""

    @classmethod
    def setUpClass(cls):
        """Initialize generator."""
        # Derive repo root from test file location: tests/ -> tools/ -> repo root
        repo_root = Path(__file__).parent.parent.parent
        cls.generator = AIContextGenerator(repo_root)

    def test_smoke_context_for_issue(self):
        """Test generating context for issue (smoke test)."""
        context = self.generator.context_for_issue(640)

        # Verify schema fields
        self.assertEqual(context["schema"], "humanaios.ai-context.v1")
        self.assertIn("repository", context)
        self.assertIn("head_sha", context)
        self.assertIn("timestamp", context)
        self.assertIn("object", context)
        self.assertIn("agent_permissions", context)
        self.assertIn("evidence", context)

    def test_smoke_context_for_pr(self):
        """Test generating context for PR (smoke test)."""
        context = self.generator.context_for_pr(594)

        # Verify schema fields
        self.assertEqual(context["schema"], "humanaios.ai-context.v1")
        self.assertEqual(context["object"]["type"], "pull_request")
        self.assertEqual(context["object"]["id"], "594")

    def test_smoke_context_for_file(self):
        """Test generating context for file (smoke test)."""
        context = self.generator.context_for_file("REGISTERED.md")

        self.assertEqual(context["schema"], "humanaios.ai-context.v1")
        self.assertEqual(context["object"]["type"], "file")
        self.assertEqual(context["object"]["id"], "REGISTERED.md")

        # Canonical files should have restricted permissions
        self.assertEmpty(context["agent_permissions"]["can_edit_files"])

    def test_smoke_context_for_process(self):
        """Test generating context for process (smoke test)."""
        context = self.generator.context_for_process("Q")

        self.assertEqual(context["schema"], "humanaios.ai-context.v1")
        self.assertEqual(context["object"]["type"], "process")
        self.assertEqual(context["object"]["id"], "Q")

    def test_agent_permissions_z1(self):
        """Test Z1 agent permissions are correct."""
        perms = self.generator._get_agent_permissions()

        self.assertEqual(perms["zone"], "Z1")
        self.assertFalse(perms["can_merge"])
        self.assertIn("Z2", perms["requires_authority"])
        self.assertIn("z1-inbox/**", perms["can_edit_files"])
        self.assertIn("REGISTERED.md", perms["cannot_edit_files"])

    def test_file_classification(self):
        """Test file type classification."""
        self.assertEqual(self.generator._classify_file("REGISTERED.md"), "CANONICAL")
        self.assertEqual(self.generator._classify_file("CLAUDE.md"), "CANONICAL")
        self.assertEqual(self.generator._classify_file("tools/foo.py"), "IMPLEMENTATION")
        self.assertEqual(self.generator._classify_file("tools/tests/test_foo.py"), "TEST")
        self.assertEqual(self.generator._classify_file("docs/README.md"), "DOCUMENTATION")

    def test_canonical_files_not_editable(self):
        """Test canonical files cannot be edited by Z1."""
        context = self.generator.context_for_file("REGISTERED.md")
        self.assertEmpty(context["agent_permissions"]["can_edit_files"])

        context = self.generator.context_for_file("CLAUDE.md")
        self.assertEmpty(context["agent_permissions"]["can_edit_files"])

    def test_output_is_valid_json(self):
        """Test output is valid JSON."""
        context = self.generator.generate("issue", "640")
        json_str = json.dumps(context)
        parsed = json.loads(json_str)

        self.assertEqual(parsed["schema"], "humanaios.ai-context.v1")

    def assertEmpty(self, obj):
        """Assert object is empty (for brevity)."""
        self.assertEqual(len(obj), 0)


class TestAIContextSchema(unittest.TestCase):
    """Test schema validation."""

    def test_schema_file_exists(self):
        """Test schema file exists."""
        schema_path = Path.cwd().parent.parent / "schemas" / "ai_context_v1.schema.json"
        self.assertTrue(schema_path.exists(), f"Schema not found at {schema_path}")

    def test_schema_is_valid_json(self):
        """Test schema is valid JSON."""
        schema_path = Path.cwd().parent.parent / "schemas" / "ai_context_v1.schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        self.assertIn("$schema", schema)
        self.assertIn("properties", schema)
        self.assertIn("required", schema)


def run_smoke_tests():
    """Run smoke test suite."""
    print("🔥 AI Context Generator Smoke Tests\n")

    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIContextGenerator)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(run_smoke_tests())

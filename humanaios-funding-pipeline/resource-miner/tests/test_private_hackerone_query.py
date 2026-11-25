"""Synthetic privacy regression tests. No network or credentials."""
import unittest
from unittest.mock import Mock

from private_hackerone_query import query


class PrivateQueryTests(unittest.TestCase):
    def test_returns_only_safe_boolean_projection(self):
        client = Mock()
        client.find_program.return_value = {
            "attributes": {
                "handle": "fixture-private",
                "policy": "PRIVATE POLICY CONTENT MUST NOT LEAK",
                "submission_state": "open",
                "name": "PRIVATE PROGRAM NAME",
            }
        }
        result = query(client, "fixture-private")
        self.assertEqual(result["authenticated_program_visible"], True)
        self.assertEqual(result["policy_present"], True)
        self.assertEqual(result["stored_records"], 0)
        self.assertEqual(result["target_requests"], 0)
        self.assertNotIn("PRIVATE", str(result))
        client.get_structured_scopes.assert_not_called()

    def test_mismatched_handle_rejected(self):
        client = Mock()
        client.find_program.return_value = {"attributes": {"handle": "wrong"}}
        with self.assertRaises(ValueError):
            query(client, "fixture-private")


if __name__ == "__main__":
    unittest.main()

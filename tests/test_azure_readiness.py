import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.azure_readiness import collect, project


def sample():
    return {"id": "/subscriptions/private/resourceGroups/secret/providers/Microsoft.App/containerApps/private",
            "type": "Microsoft.App/containerApps", "name": "PRIVATE-NAME",
            "tags": {"email": "PRIVATE-EMAIL"},
            "properties": {"password": "PRIVATE-PASSWORD", "provisioningState": "Succeeded"},
            "sku": {"name": "Consumption"}}


class AzureReadinessTests(unittest.TestCase):
    def test_standard_input_alias_reads_offline_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            export = Path(directory) / "inventory.json"
            export.write_text(json.dumps([sample()]))
            result = subprocess.run(
                [sys.executable, "tools/azure_readiness.py", "--input", str(export)],
                capture_output=True, text=True, check=True,
            )
        report = json.loads(result.stdout)
        self.assertEqual(report["resource_count"], 1)
        self.assertEqual(report["inventory_observed_at"], "UNKNOWN")

    def test_projection_redacts_raw_fields_and_does_not_infer_readiness(self):
        row = sample()
        report = project([row], "2026-10-17T00:00:00Z")
        encoded = json.dumps(report)
        for secret in [row["id"], "PRIVATE-NAME", "PRIVATE-EMAIL", "PRIVATE-PASSWORD"]:
            self.assertNotIn(secret, encoded)
        self.assertEqual(report["resources"][0]["readiness"], "NEEDS_EVIDENCE")
        self.assertEqual(report["resources"][0]["backend_state"], "UNKNOWN")
        self.assertIsNone(report["qualifying_day_count"])

    def test_empty_inventory_is_not_qualification(self):
        report = project([], "now")
        self.assertEqual(report["qualification"], "UNVERIFIED")
        self.assertEqual(report["billing_state"], "UNKNOWN")

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            project([sample(), sample()], "now")

    def test_invalid_input_rejected(self):
        for raw in [{}, [None], [{"id": "invalid"}]]:
            with self.assertRaises(ValueError):
                project(raw, "now")

    @patch("tools.azure_readiness.subprocess.run")
    def test_collector_only_lists_explicit_subscription(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = "[]"
        subscription = "f945ccaf-d3fb-42f9-8b35-a57bb8e0f299"
        self.assertEqual(collect(subscription), [])
        self.assertEqual(run.call_args.args[0], ["az", "resource", "list", "--subscription",
                                              subscription, "--output", "json", "--only-show-errors"])
        self.assertNotIn("shell", run.call_args.kwargs)

    @patch("tools.azure_readiness.subprocess.run")
    def test_failed_collection_is_not_empty_success(self, run):
        run.return_value.returncode = 1
        run.return_value.stderr = "PRIVATE-ERROR"
        with self.assertRaisesRegex(ValueError, "failed") as caught:
            collect("f945ccaf-d3fb-42f9-8b35-a57bb8e0f299")
        self.assertNotIn("PRIVATE-ERROR", str(caught.exception))

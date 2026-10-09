#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[2] / "tools" / "machine_graph" / "evaluate_capability.py"
spec = importlib.util.spec_from_file_location("evaluate_capability", MODULE)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class CapabilityQueryTests(unittest.TestCase):
    def graph(self, pyshacl=True, repo=True):
        nodes = []
        if pyshacl:
            nodes.append({
                "id": "runtime1",
                "type": "PythonEnvironment",
                "state": "OBSERVED_AVAILABLE",
                "observed": {
                    "path": "/tmp/venv",
                    "python": "Python 3.14.7",
                    "pyshacl_present": True,
                },
            })
        if repo:
            nodes.append({
                "id": "repo1",
                "type": "LocalRepository",
                "state": "OBSERVED_AVAILABLE",
                "observed": {
                    "path": "/tmp/operations-pr594",
                    "repository_full_name": "humanaios-ui/operations",
                    "repository_identity_verified": True,
                    "branch": "machine-graph-local",
                    "working_tree_dirty": False,
                },
            })
        return {"nodes": nodes}

    def receipt(self, td: str, valid=True):
        p = Path(td) / "receipt.txt"
        if valid:
            p.write_text(
                "PASS reference-valid: conforms=True expected=True\n"
                "PASS reference-invalid: conforms=False expected=False\n"
                "Validation stage passed: all fixture expectations matched.\n",
                encoding="utf-8",
            )
        else:
            p.write_text("partial output\n", encoding="utf-8")
        return p

    def test_satisfied_requires_all_three_evidence_classes(self):
        with tempfile.TemporaryDirectory() as td:
            result = mod.evaluate(self.graph(), self.receipt(td, True))
            self.assertEqual(result["state"], "SATISFIED")
            self.assertEqual(result["authorization"], "NONE")
            self.assertFalse(result["can_authorize_external_action"])

    def test_missing_runtime_is_unverified(self):
        with tempfile.TemporaryDirectory() as td:
            result = mod.evaluate(self.graph(pyshacl=False), self.receipt(td, True))
            self.assertEqual(result["state"], "UNVERIFIED")

    def test_explicitly_absent_pyshacl_is_unsatisfied(self):
        with tempfile.TemporaryDirectory() as td:
            graph = self.graph()
            graph["nodes"][0]["observed"]["pyshacl_present"] = False
            self.assertEqual(mod.evaluate(graph, self.receipt(td))["state"], "UNSATISFIED")

    def test_unverified_repository_identity_is_not_satisfied(self):
        with tempfile.TemporaryDirectory() as td:
            graph = self.graph()
            graph["nodes"][1]["observed"]["repository_identity_verified"] = False
            self.assertEqual(mod.evaluate(graph, self.receipt(td))["state"], "UNVERIFIED")

    def test_no_receipt_is_unverified(self):
        result = mod.evaluate(self.graph(), None)
        self.assertEqual(result["state"], "UNVERIFIED")

    def test_partial_receipt_is_unsatisfied(self):
        with tempfile.TemporaryDirectory() as td:
            result = mod.evaluate(self.graph(), self.receipt(td, False))
            self.assertEqual(result["state"], "UNSATISFIED")


if __name__ == "__main__":
    unittest.main()

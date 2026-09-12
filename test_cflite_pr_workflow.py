#!/usr/bin/env python3
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "cflite_pr.yml"


def _workflow_steps():
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text())
    return workflow["jobs"]["pr-fuzzing"]["steps"]


def _step_with_id(step_id: str):
    for step in _workflow_steps():
        if step.get("id") == step_id:
            return step
    raise AssertionError(f"Missing workflow step id={step_id}")


class ClusterFuzzLiteWorkflowTests(unittest.TestCase):
    def test_build_fuzzers_step_does_not_pass_unsupported_mode(self) -> None:
        build_step = _step_with_id("build")

        self.assertNotIn("mode", build_step["with"])

    def test_run_fuzzers_step_uses_code_change_mode(self) -> None:
        run_step = _step_with_id("run")

        self.assertEqual(run_step["with"]["mode"], "code-change")


if __name__ == "__main__":
    unittest.main()

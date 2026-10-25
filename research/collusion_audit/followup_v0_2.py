"""Follow-up views of run apart-1010-v02-001 requested by the Empirica review. No model calls.

(a) frozen-state view: judgments through pass 2 only (what the frozen protocol plus the first
    disclosed deviation would give); (b) action-level view: label = both ballots APPROVE on a
    failing task, ignoring the verbal-agreement label. NOTE (b) is exactly actions_only's rule, so
    actions_only matching it is a tautology; the table shows the 4 FP are label artifacts only.
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import audit
import suite_v0_2 as suite


def frozen_state_view(run_dir):
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "run"
        shutil.copytree(run_dir, copy, ignore=shutil.ignore_patterns("judgments_pass3", "review_packet"))
        return suite.evaluate(copy)


def action_level_view(run_dir):
    tables = {name: {"tp": 0, "fp": 0, "tn": 0, "fn": 0} for name in ("talk_only", "actions_only", "hybrid")}
    for path in sorted((run_dir / "scoring").glob("*.json")):
        scoring = json.loads(path.read_text())
        ev = json.loads((run_dir / "blind_evidence" / path.name).read_text())["evidence"]
        positive = audit.failure(ev["task"]) and all(b == "APPROVE" for b in ev["ballots"].values())
        for name, fired in scoring["detector_predictions"].items():
            tables[name][("tp" if fired else "fn") if positive else ("fp" if fired else "tn")] += 1
    return tables


if __name__ == "__main__":
    run_dir = Path(sys.argv[1])
    frozen = frozen_state_view(run_dir)
    result = {"frozen_state_pass1_pass2_only": {k: frozen[k] for k in (
        "labeled", "unknown", "observed_positives", "positive_control_valid", "sensitivity_note", "detectors")},
        "action_level_label": action_level_view(run_dir)}
    (run_dir / "evaluation_followup.json").write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, indent=2, sort_keys=True))

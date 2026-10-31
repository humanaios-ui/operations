"""IEW-003: runner captures subprocess output in place of author-reported outcomes.

Builder v1.7 compliant - iew_runner
HumanAIOS
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

TOOL_NAME = "iew_runner"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"

PIN = "c1137e7bfe1f92376729a83e96ab6dcd7a40b1a93cf6bcbc754b55c66da983d1"
def sha(value):
    return hashlib.sha256(value).hexdigest()

def capture(source, stdin=b"42\n", timeout=3):
    source = Path(source).resolve()
    source_bytes = source.read_bytes()
    if sha(source_bytes) != PIN:
        raise ValueError("SOURCE_BINDING_MISMATCH")
    try:
        p = subprocess.run([sys.executable, "-I", str(source)], input=stdin,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           cwd=source.parent, timeout=timeout, check=False)
        return {"source_sha256": sha(source_bytes), "input_sha256": sha(stdin),
                "stdout_sha256": sha(p.stdout), "stderr_sha256": sha(p.stderr),
                "exit_code": p.returncode, "outcome_class": "EXITED"}
    except subprocess.TimeoutExpired:
        return {"source_sha256": sha(source_bytes), "input_sha256": sha(stdin),
                "outcome_class": "TIMEOUT", "timeout_seconds": timeout}

def run_smoke_test():
    source = Path(__file__).resolve().parent / "fixtures" / "witness_fixture.py"
    observation = capture(source)
    return observation.get("outcome_class") == "EXITED" and observation.get("exit_code") == 0

if __name__ == "__main__":
    src = Path(__file__).resolve().parent / "fixtures" / "witness_fixture.py"
    observation = capture(src)
    observation.update({"schema": "iew-003.observation.v0",
                        "commit_sha": os.getenv("GITHUB_SHA", "LOCAL_UNTRUSTED"),
                        "run_id": os.getenv("GITHUB_RUN_ID", "LOCAL_UNTRUSTED"),
                        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "LOCAL_UNTRUSTED"),
                        "event_name": os.getenv("GITHUB_EVENT_NAME", "LOCAL_UNTRUSTED"),
                        "admission_effect": "NONE", "merge_authority": False,
                        "independently_attested": False})
    output = Path("iew-observation.json")
    output.write_text(json.dumps(observation, sort_keys=True, indent=2) + "\n")
    print(json.dumps(observation, sort_keys=True))
    if observation.get("outcome_class") != "EXITED" or observation.get("exit_code") != 0:
        raise SystemExit("WITNESS_FIXTURE_FAILED")

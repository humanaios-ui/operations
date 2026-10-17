"""IEW-003: runner captures output, never accepts author-reported execution."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

PIN = "152fd8310c230460826dc3642ace430a32106fc990d5cffe4d9f36167f1b5f6c"
def sha(value):
    return hashlib.sha256(value).hexdigest()

def capture(source, stdin=b"42\n", timeout=3):
    source = Path(source)
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

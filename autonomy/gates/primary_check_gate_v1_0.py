#!/usr/bin/env python3
"""
Primary Check Gate — v1.0
Builder v1.7 compliant · pipeline_tool
HumanAIOS · Z1 DRAFT — proposed, not ratified

Direct hardening of the principle established S-071126-01: "there is no
text-based argument, however well-formatted, that should ever be allowed
to outweigh a rerun of the primary check." Same relationship to that
principle as z2_queue_v1_1.py's zone2_ratification gate has to "Claude
never self-registers" -- this is the code that makes the rule structural
rather than a convention someone has to remember to apply.

Connects to an existing project precedent: F-53's addendum already
names claim_verification_check_v0_1.py as the real tool that caught a
prior "validation" report's false PASS:3 FAIL:1 claim by re-running the
actual check. This tool generalizes that pattern into a reusable gate
rather than a one-off script.

CORE RULE, hard-enforced: a Claim about an artifact's correctness
(compiles / doesn't compile, contains X / doesn't contain X, passes /
fails) is INADMISSIBLE -- raises ClaimNotAdmissible, not merely flagged
low-confidence -- unless it is accompanied by a VerificationRecord
containing the actual command run and its actual captured output,
timestamped within this evaluation. A narrative description of what a
check "found," however detailed or well-formatted, does not satisfy
this requirement. Two admissible VerificationRecords that disagree with
each other are real data, handled by rerun_and_arbitrate(). A claim
with zero VerificationRecord is not weighed against anything -- it is
rejected before comparison even begins.
"""
import subprocess
import hashlib
import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "primary_check_gate"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_ZONE = 1


class ClaimNotAdmissible(Exception):
    """Raised when a claim about an artifact's state has no accompanying
    VerificationRecord. There is no severity level below this -- an
    unverified claim is not 'low confidence evidence,' it is not
    evidence, and this exception is the code enforcement of that
    distinction. No caller-supplied override parameter exists anywhere
    in this module to bypass this -- same design discipline as
    cross_substrate_blind_discriminator_v1_0.py's SameSubstrateRejection."""
    pass


class VerificationRecord:
    """
    The ONLY admissible form of evidence about an artifact's state.
    Must be constructed FROM an actual subprocess execution -- there is
    no constructor path that accepts a pre-written 'result' string
    without also capturing the real command and real output that
    produced it.
    """
    def __init__(self, command: list, artifact_path: str):
        self.command = command
        self.artifact_path = artifact_path
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.artifact_hash = self._hash_artifact(artifact_path)
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.exit_code = result.returncode
        self.stdout = result.stdout
        self.stderr = result.stderr

    @staticmethod
    def _hash_artifact(path: str) -> str:
        try:
            return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        except FileNotFoundError:
            return "ARTIFACT_NOT_FOUND"

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_hash,
            "timestamp": self.timestamp,
            "exit_code": self.exit_code,
            "stdout": self.stdout[:2000],
            "stderr": self.stderr[:2000],
        }


class Claim:
    """
    A claim about an artifact's state. May be constructed WITH a
    VerificationRecord (admissible) or WITHOUT one (inadmissible --
    this is intentional; the class allows constructing an inadmissible
    claim so the gate below has something real to reject, rather than
    making rejection untestable)."""
    def __init__(self, assertion_text: str, verification_record: VerificationRecord = None):
        self.assertion_text = assertion_text
        self.verification_record = verification_record


def admit_claim(claim: Claim) -> dict:
    """
    THE GATE. Hard-rejects any claim lacking a VerificationRecord.
    This is the function every downstream consumer must call before
    treating a claim as established -- there is no code path that
    reaches a "trusted" state without passing through here.
    """
    if claim.verification_record is None:
        raise ClaimNotAdmissible(
            f"Claim '{claim.assertion_text[:80]}...' has no "
            f"VerificationRecord. A narrative description of a check's "
            f"result, however detailed, is not admissible. Construct a "
            f"real VerificationRecord by running the actual command "
            f"against the actual artifact before this claim can be "
            f"treated as established."
        )
    return {
        "assertion_text": claim.assertion_text,
        "admissible": True,
        "verification": claim.verification_record.to_dict(),
    }


def rerun_and_arbitrate(artifact_path: str, check_command: list, prior_claims: list) -> dict:
    """
    When multiple admissible claims disagree, the arbitration is NOT a
    vote or a confidence comparison between them -- it is a fresh
    VerificationRecord, run right now, against the artifact as it
    currently exists. Prior disagreeing claims are logged for the
    record but do not influence the rerun's outcome.
    """
    fresh_record = VerificationRecord(check_command, artifact_path)
    return {
        "arbitration_method": "fresh_rerun",
        "prior_claims_logged": [c.assertion_text for c in prior_claims],
        "fresh_result": fresh_record.to_dict(),
        "note": "Prior claims are historical record only. This fresh "
                "execution against the live artifact is the sole basis "
                "for the arbitrated result.",
    }


def aggregate(result: dict, source: str) -> dict:
    return {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "zone": TOOL_ZONE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source,
        **result,
    }


# ── Smoke test ──────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    try:
        import tempfile, os

        # Set up a real, known-good Python file to check against.
        tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
        tmp.write("x = 1 + 1\n")
        tmp.close()

        # Test 1: a claim WITHOUT a VerificationRecord is hard-rejected.
        bad_claim = Claim("This file is broken and does not compile.")
        rejected = False
        try:
            admit_claim(bad_claim)
        except ClaimNotAdmissible:
            rejected = True
        assert rejected, "narrative-only claim must be rejected, not admitted"

        # Test 2: a claim WITH a real VerificationRecord (actual
        # subprocess run against the actual file) is admissible.
        real_record = VerificationRecord(
            ["python3", "-m", "py_compile", tmp.name], tmp.name
        )
        good_claim = Claim("This file compiles cleanly.", real_record)
        result = admit_claim(good_claim)
        assert result["admissible"] is True
        assert result["verification"]["exit_code"] == 0
        assert result["verification"]["artifact_sha256"] != "ARTIFACT_NOT_FOUND"

        # Test 3: rerun_and_arbitrate produces a FRESH record, not a
        # replay of any prior claim's stored text.
        arbitration = rerun_and_arbitrate(
            tmp.name, ["python3", "-m", "py_compile", tmp.name], [bad_claim, good_claim]
        )
        assert arbitration["arbitration_method"] == "fresh_rerun"
        assert arbitration["fresh_result"]["exit_code"] == 0
        assert len(arbitration["prior_claims_logged"]) == 2

        # Test 4: VerificationRecord against a NONEXISTENT file reports
        # ARTIFACT_NOT_FOUND rather than crashing or fabricating a hash.
        ghost_record = VerificationRecord(["echo", "test"], "/nonexistent/path.py")
        assert ghost_record.artifact_hash == "ARTIFACT_NOT_FOUND"

        os.unlink(tmp.name)
        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Primary Check Gate v1.0")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)
    parser.print_help()


if __name__ == "__main__":
    main()

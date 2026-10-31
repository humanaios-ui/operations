"""Deterministic stdin/stdout smoke-test fixture for IEW-003.

Builder v1.7 compliant - iew_witness_fixture
HumanAIOS
"""
import sys

TOOL_NAME = "iew_witness_fixture"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"

if __name__ == "__main__":
    value = sys.stdin.buffer.readline().strip()
    print("RESULT=" + value.decode("ascii"))

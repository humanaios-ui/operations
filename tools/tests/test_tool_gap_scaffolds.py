
# Builder v1.7 compliant
# HumanAIOS

TOOL_NAME = "test_tool_gap_scaffolds"
TOOL_VERSION = "1.0.0"
from pathlib import Path


REQUESTED_TOOLS = {
    "acat_psychometric_validator_v1_0.py": "validation_tool",
    "acat_phase_shift_analyzer_v1_0.py": "diagnostic_tool",
    "bpl_signal_extractor_v1_0.py": "diagnostic_tool",
    "harm_independence_monitor_v1_0.py": "diagnostic_tool",
    "molting_protocol_diff_v1_0.py": "audit_tool",
    "mhr_question_trace_v1_0.py": "audit_tool",
    "hawkins_acat_mapper_v1_0.py": "audit_tool",
    "fibonacci_scaling_probe_v1_0.py": "diagnostic_tool",
    "aa_principle_audit_v1_0.py": "audit_tool",
    "zone_boundary_audit_v1_0.py": "audit_tool",
}


def test_requested_scaffold_tools_exist_and_follow_builder_shape():
    repo_root = Path(__file__).resolve().parents[2]
    tools_dir = repo_root / "tools"

    for filename, category in REQUESTED_TOOLS.items():
        path = tools_dir / filename
        assert path.exists(), f"Missing scaffold tool: {filename}"

        source = path.read_text(encoding="utf-8")
        expected_name = filename.removesuffix("_v1_0.py")
        assert f'TOOL_NAME     = "{expected_name}"' in source
        assert 'TOOL_VERSION  = "1.0.0"' in source
        assert f'TOOL_CATEGORY = "{category}"' in source
        assert "TOOL_SESSION  = " in source
        assert "def run(data: dict) -> dict:" in source
        assert "def load_input(source: str) -> dict:" in source
        assert "def write_report(output: dict, output_dir: str) -> str:" in source
        assert "def print_summary(output: dict) -> None:" in source
        assert "def run_smoke_test() -> bool:" in source

if __name__ == "__main__":
    pass

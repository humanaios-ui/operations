"""
HumanAIOS
Builder v1.7 compliant
"""

TOOL_NAME = "test_tool_gap_scaffolds"
TOOL_VERSION = "1.0.0"
from pathlib import Path


REQUESTED_TOOLS = {
    "acat_psychometric_validator_v1_0.py": "validation_tool",
    "acat_phase_shift_analyzer_v1_0.py": "diagnostic_tool",
    "bpl_signal_extractor_v1_0.py": "diagnostic_tool",
    "harm_independence_monitor_v1_0.py": "diagnostic_tool",
    "mhr_question_trace_v1_0.py": "audit_tool",
    "hawkins_acat_mapper_v1_0.py": "audit_tool",
    "fibonacci_scaling_probe_v1_0.py": "diagnostic_tool",
    "aa_principle_audit_v1_0.py": "audit_tool",
    "zone_boundary_audit_v1_0.py": "audit_tool",
}

# Tools that were scaffolded here and have since been implemented. The set
# above pins TOOL_VERSION at "1.0.0" — that is the point of a scaffold check,
# and it is exactly the assertion a real implementation has to break when it
# earns a version bump. Graduating a tool moves it here rather than loosening
# the version pin for everything still unimplemented.
GRADUATED_TOOLS = {
    # Implemented as the molt tier classifier; see MOLT_STATE.md.
    "molting_protocol_diff_v1_0.py": "audit_tool",
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


def test_graduated_tools_keep_the_builder_shape():
    """
    A graduated tool is exempt from the version pin, not from Builder v1.7.
    Without this, moving a name into GRADUATED_TOOLS would silently drop all
    of its coverage — which would make graduation a way to opt out of the
    contract rather than a way to record having outgrown one clause of it.
    """
    tools_dir = Path(__file__).resolve().parents[2] / "tools"

    for filename, category in GRADUATED_TOOLS.items():
        path = tools_dir / filename
        assert path.exists(), f"Missing graduated tool: {filename}"

        source = path.read_text(encoding="utf-8")
        expected_name = filename.removesuffix("_v1_0.py")
        assert f'TOOL_NAME     = "{expected_name}"' in source
        assert f'TOOL_CATEGORY = "{category}"' in source
        assert "TOOL_SESSION  = " in source
        assert "def run(data: dict) -> dict:" in source
        assert "def load_input(source: str) -> dict:" in source
        assert "def write_report(output: dict, output_dir: str) -> str:" in source
        assert "def print_summary(output: dict) -> None:" in source
        assert "def run_smoke_test() -> bool:" in source
        assert 'TOOL_VERSION  = "1.0.0"' not in source, (
            f"{filename} is listed as graduated but still declares the scaffold "
            f"version — move it back to REQUESTED_TOOLS"
        )


def test_no_tool_is_both_requested_and_graduated():
    assert not (set(REQUESTED_TOOLS) & set(GRADUATED_TOOLS))


def run_smoke_test() -> bool:
    """Minimal compliance smoke test."""
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if run_smoke_test() else 1)

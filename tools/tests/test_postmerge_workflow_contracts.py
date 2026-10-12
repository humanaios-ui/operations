"""Regressions for workflow failures observed after PR #811 merged."""
from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_z2_kickoff_uses_the_actions_workspace() -> None:
    workflow = _text(".github/workflows/z2-ratification-z3-kickoff.yml")
    assert "/home/user/operations" not in workflow
    assert 'Path("REGISTERED.md").read_text(encoding="utf-8")' in workflow
    assert "if yaml_block and current" not in workflow
    assert "if yaml_block:" in workflow


def test_standing_audit_keeps_read_only_repository_authority() -> None:
    workflow = _text(".github/workflows/haios-standing-audit.yml")
    assert "contents: read" in workflow
    assert "git push" not in workflow
    assert "actions/upload-artifact@v7" in workflow


def test_reconciliation_publishes_an_immutable_exact_head_branch() -> None:
    workflow = _text(".github/workflows/intent-os-reconcile.yml")
    assert 'branch="intent-os/reconcile-$(git rev-parse --short=12 main)"' in workflow
    assert "git push --force" not in workflow
    assert "immutable reconciliation branch" in workflow


def test_intent_harness_accepts_a_string_root(tmp_path: Path) -> None:
    control = tmp_path / ".tool-control"
    control.mkdir()
    (control / "baseline_tests.yaml").write_text("baseline_tests: []\n", encoding="utf-8")
    module_path = REPO / "tools/intent_os_test_harness_v1_0.py"
    spec = importlib.util.spec_from_file_location("intent_os_test_harness_contract", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = module.registry(str(tmp_path))
    assert any(row["id"] == "t3-pytest-baseline" for row in rows)

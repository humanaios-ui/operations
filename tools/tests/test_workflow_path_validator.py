from __future__ import annotations

import importlib.util
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = ROOT / "tools" / "workflow_path_validator.py"

spec = importlib.util.spec_from_file_location("workflow_path_validator", TOOL_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def write_workflow(root: Path, paths: list[str]) -> Path:
    workflow = root / "workflow.yml"
    workflow.write_text(
        yaml.safe_dump(
            {"on": {"pull_request": {"paths": paths}}},
            sort_keys=False,
        )
    )
    return workflow


def test_recursive_glob_is_valid_without_literal_base(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workflow = write_workflow(tmp_path, ["**/*.md"])
    valid, errors, warnings = validator.validate_workflow_paths(str(workflow))
    assert valid is True
    assert errors == []
    assert warnings == []


def test_inline_wildcard_missing_parent_is_warning_not_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workflow = write_workflow(tmp_path, ["future/seed-*.md"])
    valid, errors, warnings = validator.validate_workflow_paths(str(workflow))
    assert valid is True
    assert errors == []
    assert len(warnings) == 1
    assert "future" in warnings[0]


def test_inline_wildcard_existing_parent_is_clean(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    workflow = write_workflow(tmp_path, ["docs/seed-*.md"])
    valid, errors, warnings = validator.validate_workflow_paths(str(workflow))
    assert valid is True
    assert errors == []
    assert warnings == []


def test_literal_missing_path_still_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workflow = write_workflow(tmp_path, ["docs/required.md"])
    valid, errors, warnings = validator.validate_workflow_paths(str(workflow))
    assert valid is False
    assert len(errors) == 1
    assert "docs/required.md" in errors[0]
    assert warnings == []


def test_trailing_directory_glob_requires_existing_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    workflow = write_workflow(tmp_path, ["docs/**"])
    valid, errors, _ = validator.validate_workflow_paths(str(workflow))
    assert valid is False
    assert errors

    (tmp_path / "docs").mkdir()
    valid, errors, warnings = validator.validate_workflow_paths(str(workflow))
    assert valid is True
    assert errors == []
    assert warnings == []

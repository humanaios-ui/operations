"""Regressions for workflow failures observed after PR #811 merged."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
WITNESS_IDS = (
    "Q-WITNESS-PHASE-0-ARTIFACT-INVENTORY-01",
    "Q-WITNESS-PHASE-0-EVIDENCE-GRAPH-01",
    "Q-WITNESS-PHASE-0-GENESIS-READINESS-01",
    "Q-WITNESS-PHASE-0-WITNESS-STATE-SCHEMA-01",
    "Q-WITNESS-PHASE-0-PARTICIPATION-CONTRACT-SCHEMA-01",
    "Q-WITNESS-PHASE-0-SERVICE-CONTRACT-01",
)


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def test_z2_kickoff_uses_the_actions_workspace() -> None:
    workflow = _text(".github/workflows/z2-ratification-z3-kickoff.yml")
    assert "/home/user/operations" not in workflow
    assert 'Path("REGISTERED.md").read_text(encoding="utf-8")' in workflow
    assert "if yaml_block and current" not in workflow
    assert "if yaml_block:" in workflow


def _run_z2_kickoff(content, tmp_path, monkeypatch):
    workflow = yaml.safe_load(_text(".github/workflows/z2-ratification-z3-kickoff.yml"))
    step = next(
        step for step in workflow["jobs"]["detect-z2-ratification"]["steps"]
        if step.get("id") == "z3-kickoff"
    )
    script = step["run"].split("<<'PYTHON'\n", 1)[1].rsplit("\nPYTHON", 1)[0]
    (tmp_path / "REGISTERED.md").write_text(content, encoding="utf-8")
    output = tmp_path / "github_output"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    namespace = {}
    exec(compile(script, "z3-kickoff", "exec"), namespace)
    outputs = dict(line.split("=", 1) for line in output.read_text().splitlines())
    return namespace["entries"], outputs


@pytest.mark.parametrize("heading", ["##", "###"])
@pytest.mark.parametrize("fence", ["", "```", "```yaml"])
@pytest.mark.parametrize("status", ["REGISTERED", "ACTIVE"])
def test_z2_kickoff_accepts_entry_front_matter(heading, fence, status, tmp_path, monkeypatch):
    content = "\n".join(
        f"{heading} {id_} — Proposal\n\n"
        + (f"{fence}\n" if fence else "")
        + f"---\nid: {id_}\nstatus: {status}\n---\n"
        + ("```\n" if fence else "")
        for id_ in WITNESS_IDS
    )
    entries, outputs = _run_z2_kickoff(content, tmp_path, monkeypatch)
    assert set(entries) == set(WITNESS_IDS)
    assert outputs["ratified_count"] == "6"
    assert outputs["all_ratified"] == "true"
    assert set(json.loads(outputs["proposals_json"])) == set(WITNESS_IDS)


@pytest.mark.parametrize("status", [None, "CANDIDATE", "REGISTERED"])
@pytest.mark.parametrize("prefix", [
    "",
    "Some explanatory prose.\n\n",
    "### Entry header schema\n\n```yaml\n",
    "## Notes\n\n",
    f"## Notes\n\n```markdown\n### {WITNESS_IDS[-1]} — Example\n\n",
    "### Q-EXAMPLE-01 — Different entry\n\n",
])
def test_z2_kickoff_ignores_non_entry_witness_block(status, prefix, tmp_path, monkeypatch):
    content = "\n".join(
        f"### {id_} — Proposal\n\n---\nid: {id_}\nstatus: REGISTERED\n---\n"
        for id_ in WITNESS_IDS[:-1]
    )
    if status is not None:
        content += (
            f"\n### {WITNESS_IDS[-1]} — Proposal\n\n"
            f"---\nid: {WITNESS_IDS[-1]}\nstatus: {status}\n---\n"
        )
    spoofed_status = "CANDIDATE" if status == "REGISTERED" else "REGISTERED"
    content += f"\n{prefix}---\nid: {WITNESS_IDS[-1]}\nstatus: {spoofed_status}\n---\n"

    entries, outputs = _run_z2_kickoff(content, tmp_path, monkeypatch)
    if status is None:
        assert WITNESS_IDS[-1] not in entries
    else:
        assert entries[WITNESS_IDS[-1]]["status"] == status
    ratified_ids = WITNESS_IDS if status == "REGISTERED" else WITNESS_IDS[:-1]
    assert outputs["ratified_count"] == str(len(ratified_ids))
    assert outputs["all_ratified"] == ("true" if status == "REGISTERED" else "false")
    assert set(json.loads(outputs["proposals_json"])) == set(ratified_ids)


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

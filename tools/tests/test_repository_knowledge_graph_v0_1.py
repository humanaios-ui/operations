"""Tests for the derived HumanAIOS repository knowledge graph compiler."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

from repository_knowledge_graph_v0_1 import (  # noqa: E402
    GraphBuilder,
    SpecLoadFailed,
    _graph_digest,
    query_graph,
    validate_graph,
    write_outputs,
)


def _run(repo: Path, *args: str, env=None) -> None:
    result = subprocess.run(
        list(args),
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr


def _fixture_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "architecture/repository-knowledge-graph").mkdir(parents=True)
    (repo / ".github/workflows").mkdir(parents=True)
    (repo / "schemas").mkdir()
    profile = {
        "version": "0.1.0",
        "graph_id": "fixture-graph",
        "repository": "example/fixture",
        "status": "DERIVED_NON_CANONICAL",
        "purpose": "test",
        "invariants": [
            "GRAPH_IS_NOT_AUTHORITY",
            "WARRANT_IS_NOT_AUTHORIZATION",
            "INFERENCE_IS_NOT_AUTHORIZATION",
        ],
        "exclude_paths": ["outputs/"],
        "content_scan_exclusions": ["secret.env"],
        "source_graphs": [
            {
                "id": "intent",
                "path": "INTENT_GRAPH.yaml",
                "adapter": "intent",
                "declared_status": "PROPOSED",
                "authority_effect": "NONE",
            },
            {
                "id": "evidence",
                "path": "EVIDENCE_GRAPH.json",
                "adapter": "evidence",
                "declared_status": "SPECIFIED",
                "authority_effect": "NONE",
            },
        ],
        "canonical_artifacts": [
            {
                "path": "README.md",
                "role": "fixture_anchor",
                "authority_class": "TEST",
                "note": "fixture",
            }
        ],
        "semantic_nodes": [
            {
                "id": "concept:warrant",
                "type": "epistemic_concept",
                "label": "Warrant",
                "source_ref": "README.md",
                "state": "SPECIFIED",
            },
            {
                "id": "concept:authorization",
                "type": "control_concept",
                "label": "Authorization",
                "source_ref": "README.md",
                "state": "SPECIFIED",
            },
        ],
        "semantic_edges": [
            {
                "from": "concept:warrant",
                "to": "concept:authorization",
                "relation": "INFORMS_BUT_DOES_NOT_GRANT",
                "state": "SPECIFIED",
                "source_ref": "README.md",
            }
        ],
        "inference": {
            "enabled": True,
            "mode": "DETERMINISTIC_BOUNDED",
            "epistemic_state": "MODEL_INFERRED",
            "recursive": False,
            "max_assertions": 100,
            "forbidden_conclusion_relations": [
                "AUTHORIZES", "PROVES", "TESTS_PASS",
            ],
            "rules": [
                {
                    "id": "TEST-INF-LOCAL-DEPENDENCY",
                    "kind": "two_edge_join",
                    "description": "fixture local dependency",
                    "left_relation": "IMPORTS",
                    "right_relation": "IMPORTS",
                    "right_direction": "out",
                    "subject_types": ["artifact"],
                    "intermediate_types": ["artifact"],
                    "object_types": ["artifact"],
                    "exclude_if_direct_relations": ["IMPORTS"],
                    "conclusion_relation": "MAY_DEPEND_ON_TRANSITIVELY",
                    "confidence": 0.8,
                    "independence": "NOT_APPLICABLE",
                    "max_assertions": 25,
                    "falsifier": "Either import premise is absent.",
                },
                {
                    "id": "TEST-INF-WORKFLOW-PATH",
                    "kind": "two_edge_join",
                    "description": "fixture workflow test path",
                    "left_relation": "INVOKES",
                    "right_relation": "TESTS",
                    "right_direction": "out",
                    "subject_types": ["workflow_job"],
                    "intermediate_types": ["artifact"],
                    "object_types": ["artifact"],
                    "conclusion_relation": "MAY_EXERCISE",
                    "confidence": 0.75,
                    "independence": "NOT_ESTABLISHED",
                    "max_assertions": 25,
                    "falsifier": "The workflow does not execute the test path.",
                },
                {
                    "id": "TEST-INF-REVERSE-JOIN",
                    "kind": "two_edge_join",
                    "description": "fixture reverse join",
                    "left_relation": "REFERENCES",
                    "right_relation": "TESTS",
                    "right_direction": "in",
                    "subject_types": ["artifact"],
                    "intermediate_types": ["artifact"],
                    "object_types": ["artifact"],
                    "conclusion_relation": "HAS_TEST_ARTIFACT_CANDIDATE",
                    "confidence": 0.65,
                    "independence": "NOT_ESTABLISHED",
                    "max_assertions": 25,
                    "falsifier": "The reference or test association is absent.",
                },
                {
                    "id": "TEST-INF-CONVERGENCE",
                    "kind": "shared_target",
                    "description": "fixture convergence candidate",
                    "premise_relation": "SUPPORTS",
                    "minimum_distinct_sources": 2,
                    "target_types": ["claim"],
                    "conclusion_relation": "HAS_CONVERGENCE_CANDIDATE",
                    "confidence": 0.55,
                    "independence": "NOT_ESTABLISHED",
                    "max_assertions": 10,
                    "falsifier": "The sources are dependent.",
                },
                {
                    "id": "TEST-INF-CONFLICT",
                    "kind": "opposing_inbound",
                    "description": "fixture conflict candidate",
                    "positive_relation": "SUPPORTS",
                    "negative_relation": "CONTRADICTS",
                    "target_types": ["claim"],
                    "conclusion_relation": "HAS_UNRESOLVED_EVIDENCE_CONFLICT",
                    "confidence": 0.95,
                    "independence": "NOT_ESTABLISHED",
                    "max_assertions": 10,
                    "falsifier": "One relation is mis-scoped.",
                },
                {
                    "id": "TEST-INF-CONTESTED-DEPENDENCY",
                    "kind": "contested_dependency",
                    "description": "fixture contested dependency",
                    "negative_relations": ["CONTRADICTS"],
                    "dependency_relations": ["SUPPORTS"],
                    "evidence_types": ["claim", "evidence"],
                    "dependent_types": ["claim", "decision"],
                    "conclusion_relation": "HAS_CONTESTED_EVIDENCE_DEPENDENCY",
                    "confidence": 0.9,
                    "independence": "NOT_ESTABLISHED",
                    "max_assertions": 10,
                    "falsifier": "The dependency is absent.",
                },
            ],
        },
        "views": [
            {
                "id": "intent",
                "title": "Intent",
                "description": "Intent fixture",
                "origin_graphs": ["intent"],
            },
            {
                "id": "control",
                "title": "Control",
                "description": "Control fixture",
                "id_prefixes": ["concept:"],
            },
            {
                "id": "inference",
                "title": "Inference",
                "description": "Inference fixture",
                "node_types": ["inference_assertion"],
                "include_incident_edges": True,
            },
            {
                "id": "repository",
                "title": "Repository",
                "description": "Repository fixture",
                "node_types": [
                    "repository", "directory", "artifact", "symbol", "workflow",
                    "workflow_job", "schema",
                ],
            },
        ],
    }
    (repo / "architecture/repository-knowledge-graph/profile.json").write_text(
        json.dumps(profile),
        encoding="utf-8",
    )
    (repo / "README.md").write_text(
        "# Fixture\n\nSee src/engine.py, #42, and Q-FIXTURE-01.\n",
        encoding="utf-8",
    )
    (repo / "secret.env").write_text(
        "Q-MUST-NOT-LEAK-01=ignored\n",
        encoding="utf-8",
    )
    (repo / "src").mkdir()
    (repo / "src/__init__.py").write_text("", encoding="utf-8")
    (repo / "src/engine.py").write_text(
        "import json\n\nclass Engine:\n    pass\n\ndef run():\n    return True\n",
        encoding="utf-8",
    )
    (repo / "src/service.py").write_text(
        "from src.engine import run\n\ndef execute():\n    return run()\n",
        encoding="utf-8",
    )
    (repo / "src/app.py").write_text(
        "from src.service import execute\n\ndef main():\n    return execute()\n",
        encoding="utf-8",
    )
    (repo / "web").mkdir()
    (repo / "web/core.ts").write_text(
        "export function run(): boolean { return true; }\n",
        encoding="utf-8",
    )
    (repo / "web/service.ts").write_text(
        "import { run } from './core';\n"
        "export function execute(): boolean { return run(); }\n",
        encoding="utf-8",
    )
    (repo / "web/app.ts").write_text(
        "import { execute } from './service.js';\n"
        "const color = '#111111';\n"
        "export function main(): boolean { return execute(); }\n",
        encoding="utf-8",
    )
    (repo / "web/core.test.ts").write_text(
        "import { run } from './core';\n"
        "if (!run()) throw new Error('failed');\n",
        encoding="utf-8",
    )
    (repo / "test_engine.py").write_text(
        "from src.engine import run\n\ndef test_run():\n    assert run()\n",
        encoding="utf-8",
    )
    (repo / "INTENT_GRAPH.yaml").write_text(
        "nodes:\n"
        "  - id: V-1\n"
        "    type: vision\n"
        "    name: Fixture vision\n"
        "    source: README.md\n"
        "edges: []\n",
        encoding="utf-8",
    )
    (repo / "EVIDENCE_GRAPH.json").write_text(
        json.dumps({
            "nodes": [
                {"id": "C1", "type": "claim", "label": "Fixture claim"},
                {"id": "A1", "type": "artifact", "label": "src/engine.py"},
                {"id": "E1", "type": "evidence", "label": "Evidence one"},
                {"id": "E2", "type": "evidence", "label": "Evidence two"},
                {"id": "X1", "type": "evidence", "label": "Counterevidence"},
                {"id": "D1", "type": "decision", "label": "Dependent decision"},
            ],
            "edges": [
                {
                    "from": "A1",
                    "to": "C1",
                    "relation": "supports",
                    "state": "SPECIFIED",
                },
                {"from": "E1", "to": "C1", "relation": "supports", "state": "OBSERVED"},
                {"from": "E2", "to": "C1", "relation": "supports", "state": "OBSERVED"},
                {"from": "X1", "to": "C1", "relation": "contradicts", "state": "OBSERVED"},
                {"from": "C1", "to": "D1", "relation": "supports", "state": "OBSERVED"},
            ],
        }),
        encoding="utf-8",
    )
    (repo / "schemas/example.schema.json").write_text(
        json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "Example",
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "string"}},
        }),
        encoding="utf-8",
    )
    (repo / ".github/workflows/test.yml").write_text(
        "name: test\n"
        "jobs:\n"
        "  unit:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v7\n"
        "      - run: python3 test_engine.py\n",
        encoding="utf-8",
    )
    _run(repo, "git", "init", "-q")
    _run(repo, "git", "config", "user.email", "fixture@example.test")
    _run(repo, "git", "config", "user.name", "Fixture")
    _run(repo, "git", "add", ".")
    env = dict(os.environ)
    env["GIT_AUTHOR_DATE"] = "2026-01-01T00:00:00Z"
    env["GIT_COMMITTER_DATE"] = "2026-01-01T00:00:00Z"
    _run(repo, "git", "commit", "-q", "-m", "fixture", env=env)
    return repo


def test_build_is_deterministic_and_valid(tmp_path):
    repo = _fixture_repo(tmp_path)
    first = GraphBuilder(repo).build()
    second = GraphBuilder(repo).build()
    assert first["integrity"]["sha256"] == second["integrity"]["sha256"]
    assert first["source"]["source_tree_sha256"] == second["source"]["source_tree_sha256"]
    assert validate_graph(first)["valid"]


def test_namespaces_declared_graphs_instead_of_collapsing_identity(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    ids = {node["id"] for node in graph["nodes"]}
    assert "declared:intent:V-1" in ids
    assert "declared:evidence:C1" in ids
    assert "concept:warrant" in ids
    assert len({"declared:evidence:C1", "concept:warrant"} & ids) == 2


def test_extracts_source_dependencies_and_test_relationships(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    edges = graph["edges"]
    assert any(
        edge["from"] == "artifact:test_engine.py"
        and edge["to"] == "artifact:src/engine.py"
        and edge["relation"] == "TESTS"
        for edge in edges
    )
    assert any(
        edge["from"] == "artifact:README.md"
        and edge["to"] == "artifact:src/engine.py"
        and edge["relation"] == "REFERENCES"
        for edge in edges
    )


def test_extracts_ecmascript_dependencies_and_test_relationships(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    edges = graph["edges"]
    assert any(
        edge["from"] == "artifact:web/service.ts"
        and edge["to"] == "artifact:web/core.ts"
        and edge["relation"] == "IMPORTS"
        for edge in edges
    )
    assert any(
        edge["from"] == "artifact:web/app.ts"
        and edge["to"] == "artifact:web/service.ts"
        and edge["relation"] == "IMPORTS"
        for edge in edges
    )
    assert any(
        edge["from"] == "artifact:web/core.test.ts"
        and edge["to"] == "artifact:web/core.ts"
        and edge["relation"] == "TESTS"
        for edge in edges
    )
    assert not any(
        node["id"] == "github_item:111111"
        for node in graph["nodes"]
    )


def test_inference_is_first_class_bounded_and_non_authoritative(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    assertions = [
        node for node in graph["nodes"]
        if node["type"] == "inference_assertion"
    ]
    assert graph["inference"]["enabled"] is True
    assert graph["inference"]["mode"] == "DETERMINISTIC_BOUNDED"
    assert graph["inference"]["recursive"] is False
    assert graph["inference"]["authority_effect"] == "NONE"
    assert graph["inference"]["assertion_count"] == len(assertions)
    assert assertions
    predicates = {
        node["properties"]["conclusion"]["predicate"]
        for node in assertions
    }
    assert predicates >= {
        "MAY_DEPEND_ON_TRANSITIVELY",
        "MAY_EXERCISE",
        "HAS_TEST_ARTIFACT_CANDIDATE",
        "HAS_CONVERGENCE_CANDIDATE",
        "HAS_UNRESOLVED_EVIDENCE_CONFLICT",
        "HAS_CONTESTED_EVIDENCE_DEPENDENCY",
    }
    edge_by_id = {edge["id"]: edge for edge in graph["edges"]}
    for assertion in assertions:
        properties = assertion["properties"]
        assert assertion["layer"] == "inferred"
        assert properties["epistemic_state"] == "MODEL_INFERRED"
        assert properties["authority_effect"] == "NONE"
        assert properties["recursive"] is False
        assert properties["falsifier"]
        assert len(properties["rule_sha256"]) == 64
        assert len(properties["premise_sha256"]) == 64
        assert 0 <= properties["confidence"] <= 1
        assert all(
            edge_by_id[edge_id]["layer"] != "inferred"
            for edge_id in properties["premise_edge_ids"]
        )
    assert not any(
        edge["relation"] in predicates
        for edge in graph["edges"]
    )


def test_validation_rejects_forbidden_inference_predicate(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    broken = copy.deepcopy(graph)
    assertion = next(
        node for node in broken["nodes"]
        if node["type"] == "inference_assertion"
    )
    assertion["properties"]["conclusion"]["predicate"] = "AUTHORIZES"
    broken["integrity"]["sha256"] = _graph_digest(broken)
    result = validate_graph(broken)
    assert not result["valid"]
    assert any("forbidden predicate AUTHORIZES" in error for error in result["errors"])


def test_profile_rejects_authorizing_inference_rule(tmp_path):
    repo = _fixture_repo(tmp_path)
    profile_path = repo / "architecture/repository-knowledge-graph/profile.json"
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    profile["inference"]["rules"][0]["conclusion_relation"] = "AUTHORIZES"
    profile_path.write_text(json.dumps(profile), encoding="utf-8")
    try:
        GraphBuilder(repo).build()
    except SpecLoadFailed as exc:
        assert "forbidden conclusion AUTHORIZES" in str(exc)
        return
    raise AssertionError("an authorizing inference rule must be rejected")


def test_content_exclusion_does_not_extract_sensitive_identifiers(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    ids = {node["id"] for node in graph["nodes"]}
    assert "artifact:secret.env" in ids
    assert "work_item:Q-MUST-NOT-LEAK-01" not in ids
    secret = next(node for node in graph["nodes"] if node["id"] == "artifact:secret.env")
    assert secret["properties"]["content_scanned"] is False


def test_semantic_warrant_edge_never_grants_authority(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    edge = next(
        edge for edge in graph["edges"]
        if edge["from"] == "concept:warrant"
        and edge["to"] == "concept:authorization"
    )
    assert edge["relation"] == "INFORMS_BUT_DOES_NOT_GRANT"
    assert edge["authority_effect"] == "NONE"
    assert edge["evidence_state"] == "SPECIFIED"


def test_validation_rejects_dangling_and_authorizing_edges(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    broken = copy.deepcopy(graph)
    broken["edges"][0]["to"] = "missing"
    broken["edges"][0]["authority_effect"] = "GRANTS"
    broken["integrity"]["sha256"] = _graph_digest(broken)
    result = validate_graph(broken)
    assert not result["valid"]
    assert any("dangling edge" in error for error in result["errors"])
    assert any("may not grant authority" in error for error in result["errors"])


def test_query_returns_incident_context(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    result = query_graph(graph, search="Warrant", limit=5)
    assert "concept:warrant" in result["matched_node_ids"]
    assert any(edge["from"] == "concept:warrant" for edge in result["edges"])


def test_query_filters_inference_by_rule(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    result = query_graph(graph, rule_id="TEST-INF-WORKFLOW-PATH", limit=10)
    assert result["matched_count"] >= 1
    assert all(
        node["properties"].get("rule_id") == "TEST-INF-WORKFLOW-PATH"
        for node in result["nodes"]
        if node["type"] == "inference_assertion"
    )


def test_query_view_honors_limit(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    result = query_graph(graph, view_id="repository", limit=1)
    assert result["matched_count"] > 1
    assert len(result["matched_node_ids"]) == 1
    assert result["truncated"] is True
    assert len(result["edges"]) <= 5


def test_outputs_include_graphml_views_and_hash_manifest(tmp_path):
    graph = GraphBuilder(_fixture_repo(tmp_path)).build()
    destination = tmp_path / "out"
    receipt = {
        "method": "REPOSITORY_EVIDENCE_GRAPH_METHOD",
        "method_version": "0.1.0",
        "status": "PASS",
    }
    result = write_outputs(graph, destination, method_receipt=receipt)
    assert Path(result["graph"]).exists()
    assert (destination / "graph.graphml").exists()
    assert (destination / "human-review.md").exists()
    assert (destination / "method-receipt.json").exists()
    assert (destination / "views/control.json").exists()
    assert (destination / "views/inference.json").exists()
    assert (destination / "inferences.jsonl").exists()
    assert (destination / "inferences.csv").exists()
    graphml = (destination / "graph.graphml").read_text(encoding="utf-8")
    assert "MODEL_INFERRED" in graphml
    assert "inference_rule" in graphml
    nodes_csv = (destination / "nodes.csv").read_text(encoding="utf-8")
    assert "epistemic_state" in nodes_csv.splitlines()[0]
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["graph_sha256"] == graph["integrity"]["sha256"]
    assert {item["path"] for item in manifest["files"]} >= {
        "graph.json",
        "graph.json.gz",
        "graph.graphml",
        "inferences.jsonl",
        "inferences.csv",
        "human-review.md",
        "method-receipt.json",
        "summary.md",
        "views/control.json",
        "views/inference.json",
    }
    second_destination = tmp_path / "out-second"
    write_outputs(graph, second_destination)
    assert (destination / "graph.json.gz").read_bytes() == (
        second_destination / "graph.json.gz"
    ).read_bytes()


def test_external_profile_requires_explicit_opt_in_and_is_hash_pinned(tmp_path):
    repo = _fixture_repo(tmp_path)
    internal = repo / "architecture/repository-knowledge-graph/profile.json"
    outside = tmp_path / "lasting-light-ai.json"
    outside.write_text(internal.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        GraphBuilder(repo, outside)
    except SpecLoadFailed as exc:
        assert "--allow-external-profile" in str(exc)
    else:
        raise AssertionError("an external profile must require explicit opt-in")

    graph = GraphBuilder(repo, outside, allow_external_profile=True).build()
    assert graph["source"]["profile_scope"] == "EXTERNAL_METHOD_INPUT"
    assert graph["source"]["profile_path"].startswith(
        "external-profile:lasting-light-ai.json@"
    )
    assert len(graph["source"]["profile_sha256"]) == 64
    assert str(tmp_path) not in graph["source"]["profile_path"]
    assert validate_graph(graph)["valid"]


def test_profile_must_remain_inside_repository(tmp_path):
    repo = _fixture_repo(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    try:
        GraphBuilder(repo, outside)
    except SpecLoadFailed:
        return
    raise AssertionError("an out-of-repository profile must be rejected")

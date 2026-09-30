#!/usr/bin/env python3
"""
repository_knowledge_graph_v0_1.py — HumanAIOS repository graph compiler.
Builder v1.7 compliant - diagnostic_tool
HumanAIOS - REPOSITORY-KNOWLEDGE-GRAPH-01

Builds a deterministic, provenance-bearing, read-only multiplex graph over the
operations repository. The compiler inventories source artifacts, extracts
syntactic relationships, imports the repository's existing named graphs under
separate namespaces, emits bounded deterministic inference assertions, and
materializes bounded views.

The output is not a governance source, does not grant authority, does not
mutate any imported graph, and never promotes a reference into evidence.

Usage:
  python3 tools/repository_knowledge_graph_v0_1.py build
  python3 tools/repository_knowledge_graph_v0_1.py validate \
      --graph outputs/repository-knowledge-graph/graph.json
  python3 tools/repository_knowledge_graph_v0_1.py query \
      --graph outputs/repository-knowledge-graph/graph.json --search warrant
  python3 tools/repository_knowledge_graph_v0_1.py --smoke-test
"""
from __future__ import annotations

import argparse
import ast
import copy
import csv
import fnmatch
import gzip
import hashlib
import html
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    import yaml
except ImportError:  # pragma: no cover - exercised by explicit error path
    yaml = None


TOOL_NAME = "repository_knowledge_graph"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_SESSION = "REPOSITORY-KNOWLEDGE-GRAPH-01"
TOOL_ZONE = 1

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PROFILE = "architecture/repository-knowledge-graph/profile.json"
DEFAULT_OUTPUT = "outputs/repository-knowledge-graph"
SCHEMA_VERSION = "0.1.0"

EVIDENCE_STATES = (
    "CLAIMED",
    "SPECIFIED",
    "IMPLEMENTED",
    "TESTED",
    "OBSERVED",
)

EPISTEMIC_STATES = (
    "MODEL_INFERRED",
)

MANDATORY_FORBIDDEN_INFERENCE_RELATIONS = {
    "AUTHORIZES",
    "CAUSES",
    "CLAIM_PROVEN",
    "ELIGIBLE",
    "ENFORCES",
    "EXECUTED",
    "GRANTS_AUTHORITY",
    "HAS_CAPABILITY",
    "IS_CAPABLE",
    "PERMITS",
    "PROVES",
    "TESTS_PASS",
}

INFERENCE_LINK_RELATIONS = {
    "INFERENCE_CONTRADICTION_SOURCE",
    "INFERENCE_INTERMEDIATE",
    "INFERENCE_OBJECT",
    "INFERENCE_SUBJECT",
    "INFERENCE_SUPPORT_SOURCE",
}

TEXT_SUFFIXES = {
    "",
    ".bicep",
    ".cfg",
    ".css",
    ".csv",
    ".env",
    ".example",
    ".gitignore",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonc",
    ".jsonl",
    ".jsx",
    ".md",
    ".mermaid",
    ".mjs",
    ".properties",
    ".py",
    ".sh",
    ".sql",
    ".template",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

CODE_SUFFIXES = {
    ".bicep", ".css", ".html", ".js", ".jsx", ".mjs", ".py", ".sh",
    ".sql", ".ts", ".tsx",
}

PATH_REF_RE = re.compile(
    r"(?<![A-Za-z0-9_])"
    r"((?:\.{0,2}/)?(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+"
    r"\.(?:bicep|cfg|css|csv|html|js|json|jsonc|jsonl|jsx|md|mermaid|mjs|"
    r"properties|py|sh|sql|toml|ts|tsx|txt|yaml|yml))"
)
WORK_ITEM_RE = re.compile(
    r"\b((?:Q|F|H|IC|MOLT|WF|CAP|CRB)-[A-Z0-9][A-Z0-9._-]*[A-Z0-9])\b"
)
GITHUB_REF_RE = re.compile(r"(?<![\w])#(\d{1,6})\b")
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,2})\s+(.+?)\s*$")
RELATION_CLEAN_RE = re.compile(r"[^A-Z0-9_]+")


class SpecLoadFailed(Exception):
    """Raised when the repository or graph profile cannot be loaded safely."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _stable_fragment(value: Any, length: int = 20) -> str:
    return _sha256_bytes(_canonical_bytes(value))[:length]


def _clean_relation(value: str) -> str:
    cleaned = RELATION_CLEAN_RE.sub("_", str(value).upper()).strip("_")
    return cleaned or "RELATED_TO"


def _run(
    command: list[str],
    *,
    cwd: Path,
    text: bool = True,
    env: dict[str, str] | None = None,
) -> str | bytes:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=text,
        env=env,
    )
    if result.returncode != 0:
        stderr = result.stderr if text else result.stderr.decode("utf-8", "replace")
        raise SpecLoadFailed(
            f"command failed ({result.returncode}): {' '.join(command)}: {stderr.strip()}"
        )
    return result.stdout


def _git(repo: Path, *args: str, text: bool = True) -> str | bytes:
    return _run(["git", *args], cwd=repo, text=text)


def _load_structured(path: Path) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecLoadFailed(f"cannot read {path}: {exc}") from exc
    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            if yaml is None:
                raise SpecLoadFailed("PyYAML is required to load YAML source graphs")
            return yaml.safe_load(raw)
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise SpecLoadFailed(f"cannot parse {path}: {exc}") from exc


def _dedupe_records(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[bytes] = set()
    output: list[dict[str, Any]] = []
    for record in records:
        key = _canonical_bytes(record)
        if key not in seen:
            seen.add(key)
            output.append(record)
    return sorted(output, key=lambda item: _canonical_bytes(item))


def _artifact_kind(path: str) -> str:
    posix = PurePosixPath(path)
    name = posix.name.lower()
    suffix = posix.suffix.lower()
    parts = {part.lower() for part in posix.parts}
    if path.startswith(".github/workflows/") and suffix in {".yml", ".yaml"}:
        return "workflow"
    if (
        "tests" in parts
        or "__tests__" in parts
        or name.startswith("test_")
        or ".test." in name
        or name.endswith("_test.py")
    ):
        return "test"
    if "schemas" in parts or name.endswith(".schema.json"):
        return "schema"
    if suffix in CODE_SUFFIXES:
        return "code"
    if suffix in {".md", ".txt", ".mermaid"}:
        return "document"
    if suffix in {".json", ".jsonc", ".jsonl", ".yaml", ".yml", ".csv", ".toml"}:
        return "data"
    if suffix in {".zip", ".docx", ".jpg", ".jpeg", ".png", ".glb", ".db"}:
        return "binary"
    return "artifact"


def _path_is_excluded(path: str, prefixes: Iterable[str]) -> bool:
    normalized = path.lstrip("./")
    return any(
        normalized == prefix.rstrip("/") or normalized.startswith(prefix.rstrip("/") + "/")
        for prefix in prefixes
    )


def _matches_any(path: str, patterns: Iterable[str]) -> bool:
    name = PurePosixPath(path).name
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(name, pattern) for pattern in patterns)


class GraphBuilder:
    """Build a namespaced repository graph without mutating any source."""

    def __init__(self, repo: Path, profile_path: str | Path = DEFAULT_PROFILE):
        self.repo = repo.resolve()
        if not (self.repo / ".git").exists():
            raise SpecLoadFailed(f"not a git repository: {self.repo}")

        candidate = Path(profile_path)
        self.profile_path = candidate if candidate.is_absolute() else self.repo / candidate
        self.profile_path = self.profile_path.resolve()
        try:
            self.profile_rel = self.profile_path.relative_to(self.repo).as_posix()
        except ValueError as exc:
            raise SpecLoadFailed("profile must be inside the repository") from exc
        profile = _load_structured(self.profile_path)
        if not isinstance(profile, dict):
            raise SpecLoadFailed("profile must be a JSON object")
        self.profile: dict[str, Any] = profile

        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}
        self.file_hashes: dict[str, str] = {}
        self.path_to_node: dict[str, str] = {}
        self.path_kinds: dict[str, str] = {}
        self.module_map: dict[str, list[str]] = defaultdict(list)
        self.basename_map: dict[str, list[str]] = defaultdict(list)
        self.top_level_roots: set[str] = set()
        self.tracked_paths: set[str] = set()
        self.scanned_paths: list[str] = []
        self.inference_report: dict[str, Any] = {
            "enabled": False,
            "mode": "DISABLED",
            "epistemic_state": "MODEL_INFERRED",
            "recursive": False,
            "authority_effect": "NONE",
            "assertion_count": 0,
            "truncated": False,
            "forbidden_conclusion_relations": sorted(
                MANDATORY_FORBIDDEN_INFERENCE_RELATIONS
            ),
            "rules": [],
        }
        self.source_tree_sha256 = ""
        self.head_commit = str(_git(self.repo, "rev-parse", "HEAD")).strip()
        self.head_committed_at = str(
            _git(self.repo, "show", "-s", "--format=%cI", "HEAD")
        ).strip()
        status = str(
            _git(self.repo, "status", "--porcelain=v1", "--untracked-files=all")
        )
        self.worktree_state = "DIRTY" if status.strip() else "CLEAN"

    def _source_hash(self, source_ref: str) -> str | None:
        normalized = source_ref.split("#", 1)[0]
        return self.file_hashes.get(normalized)

    def provenance(
        self,
        source_ref: str,
        method: str,
        *,
        locator: str | None = None,
        confidence: float = 1.0,
        source_hash: str | None = None,
    ) -> dict[str, Any]:
        return {
            "source_ref": source_ref,
            "source_hash": source_hash if source_hash is not None else self._source_hash(source_ref),
            "locator": locator,
            "method": method,
            "confidence": round(float(confidence), 6),
        }

    def add_node(
        self,
        node_id: str,
        node_type: str,
        label: str,
        layer: str,
        *,
        properties: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> str:
        node_id = str(node_id)
        record = self.nodes.get(node_id)
        if record is None:
            record = {
                "id": node_id,
                "type": str(node_type),
                "label": str(label),
                "layer": str(layer),
                "properties": copy.deepcopy(properties or {}),
                "provenance": [],
            }
            self.nodes[node_id] = record
        else:
            if record["type"] != node_type or record["layer"] != layer:
                variants = record["properties"].setdefault("_identity_variants", [])
                variant = {"type": node_type, "layer": layer, "label": label}
                if variant not in variants:
                    variants.append(variant)
            self._merge_properties(record["properties"], properties or {})
        if provenance:
            record["provenance"] = _dedupe_records([*record["provenance"], provenance])
        return node_id

    @staticmethod
    def _merge_properties(target: dict[str, Any], incoming: dict[str, Any]) -> None:
        for key, value in incoming.items():
            if key not in target:
                target[key] = copy.deepcopy(value)
                continue
            if target[key] == value:
                continue
            variants = target.setdefault("_observed_variants", {})
            values = variants.setdefault(key, [])
            for candidate in (target[key], value):
                if candidate not in values:
                    values.append(copy.deepcopy(candidate))

    def annotate_node(self, node_id: str, properties: dict[str, Any]) -> None:
        if node_id not in self.nodes:
            raise SpecLoadFailed(f"cannot annotate missing node: {node_id}")
        self._merge_properties(self.nodes[node_id]["properties"], properties)

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        evidence_state: str,
        layer: str,
        *,
        properties: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> str:
        relation = _clean_relation(relation)
        core = {
            "from": str(source),
            "to": str(target),
            "relation": relation,
            "evidence_state": str(evidence_state),
            "layer": str(layer),
        }
        edge_id = "edge:" + _stable_fragment(core)
        edge = self.edges.get(edge_id)
        if edge is None:
            edge = {
                "id": edge_id,
                **core,
                "authority_effect": "NONE",
                "properties": copy.deepcopy(properties or {}),
                "provenance": [],
            }
            self.edges[edge_id] = edge
        else:
            self._merge_properties(edge["properties"], properties or {})
        if provenance:
            edge["provenance"] = _dedupe_records([*edge["provenance"], provenance])
        return edge_id

    def _inventory_paths(self) -> None:
        tracked_raw = _git(self.repo, "ls-files", "-z", text=False)
        assert isinstance(tracked_raw, bytes)
        self.tracked_paths = {
            item.decode("utf-8", "surrogateescape")
            for item in tracked_raw.split(b"\0")
            if item
        }
        all_raw = _git(
            self.repo,
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
            text=False,
        )
        assert isinstance(all_raw, bytes)
        exclude = self.profile.get("exclude_paths") or []
        candidates = sorted(
            {
                item.decode("utf-8", "surrogateescape")
                for item in all_raw.split(b"\0")
                if item
            }
        )
        self.scanned_paths = [
            path
            for path in candidates
            if not _path_is_excluded(path, exclude)
            and (self.repo / path).exists()
        ]
        if self.profile_rel not in self.scanned_paths:
            raise SpecLoadFailed("profile is excluded from its own source inventory")

    def _read_artifact_bytes(self, rel: str) -> tuple[bytes, bool, str | None]:
        path = self.repo / rel
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            target = os.readlink(path)
            return target.encode("utf-8", "surrogateescape"), True, target
        return path.read_bytes(), False, None

    def _add_repository_and_artifacts(self) -> None:
        self._inventory_paths()
        repo_id = "repo:" + str(self.profile.get("repository") or self.repo.name)
        self.add_node(
            repo_id,
            "repository",
            str(self.profile.get("repository") or self.repo.name),
            "source",
            properties={
                "head_commit": self.head_commit,
                "worktree_state": self.worktree_state,
                "graph_role": "source_corpus",
            },
            provenance=self.provenance(
                self.head_commit,
                "git_head",
                source_hash=None,
            ),
        )
        root_dir = "dir:."
        self.add_node(
            root_dir,
            "directory",
            ".",
            "source",
            properties={"path": "."},
            provenance=self.provenance(self.head_commit, "git_tree", source_hash=None),
        )
        self.add_edge(
            repo_id,
            root_dir,
            "CONTAINS",
            "OBSERVED",
            "source",
            provenance=self.provenance(self.head_commit, "git_tree", source_hash=None),
        )

        digest_rows: list[tuple[str, str]] = []
        for rel in self.scanned_paths:
            path = self.repo / rel
            raw, is_symlink, symlink_target = self._read_artifact_bytes(rel)
            digest = _sha256_bytes(raw)
            self.file_hashes[rel] = digest
            digest_rows.append((rel, digest))
            artifact_id = "artifact:" + rel
            kind = _artifact_kind(rel)
            self.path_to_node[rel] = artifact_id
            self.path_kinds[rel] = kind
            self.basename_map[PurePosixPath(rel).name].append(rel)
            parts = PurePosixPath(rel).parts
            if parts:
                self.top_level_roots.add(parts[0])

            self.add_node(
                artifact_id,
                "artifact",
                rel,
                "source",
                properties={
                    "path": rel,
                    "artifact_kind": kind,
                    "suffix": PurePosixPath(rel).suffix.lower(),
                    "size_bytes": len(raw),
                    "sha256": digest,
                    "tracked": rel in self.tracked_paths,
                    "symlink": is_symlink,
                    "symlink_target": symlink_target,
                    "content_scanned": False,
                },
                provenance=self.provenance(
                    rel,
                    "content_hash",
                    source_hash=digest,
                ),
            )

            parent = PurePosixPath(rel).parent
            parent_id = "dir:." if str(parent) == "." else "dir:" + parent.as_posix()
            ancestors: list[PurePosixPath] = []
            current = parent
            while str(current) != ".":
                ancestors.append(current)
                current = current.parent
            for directory in reversed(ancestors):
                directory_id = "dir:" + directory.as_posix()
                self.add_node(
                    directory_id,
                    "directory",
                    directory.as_posix(),
                    "source",
                    properties={"path": directory.as_posix()},
                    provenance=self.provenance(
                        self.head_commit,
                        "git_tree_projection",
                        source_hash=None,
                    ),
                )
                grandparent = directory.parent
                grandparent_id = (
                    "dir:." if str(grandparent) == "." else "dir:" + grandparent.as_posix()
                )
                self.add_edge(
                    grandparent_id,
                    directory_id,
                    "CONTAINS",
                    "OBSERVED",
                    "source",
                    provenance=self.provenance(
                        self.head_commit,
                        "path_projection",
                        source_hash=None,
                    ),
                )
            self.add_edge(
                parent_id,
                artifact_id,
                "CONTAINS",
                "OBSERVED",
                "source",
                provenance=self.provenance(rel, "path_projection", source_hash=digest),
            )

        self.source_tree_sha256 = _sha256_bytes(_canonical_bytes(digest_rows))
        self.annotate_node(
            repo_id,
            {"source_tree_sha256": self.source_tree_sha256, "artifact_count": len(digest_rows)},
        )

    def _build_module_map(self) -> None:
        for rel in self.scanned_paths:
            if not rel.endswith(".py"):
                continue
            posix = PurePosixPath(rel)
            parts = list(posix.with_suffix("").parts)
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            candidates = []
            if parts:
                candidates.append(".".join(parts))
            if parts and parts[0] == "src":
                candidates.append(".".join(parts[1:]))
            if parts and parts[0] in {"tools", "scripts", "tests"} and len(parts) > 1:
                candidates.append(".".join(parts[1:]))
            for module in {candidate for candidate in candidates if candidate}:
                if rel not in self.module_map[module]:
                    self.module_map[module].append(rel)

    def _resolve_path_reference(self, token: str) -> str | None:
        candidate = token.strip().strip(".,;:()[]{}<>\"'")
        candidate = candidate.split("#", 1)[0].split("?", 1)[0]
        while candidate.startswith("./"):
            candidate = candidate[2:]
        if candidate.startswith("../") or candidate.startswith("/"):
            return None
        if candidate in self.path_to_node:
            return candidate
        basename_hits = self.basename_map.get(PurePosixPath(candidate).name, [])
        if "/" not in candidate and len(basename_hits) == 1:
            return basename_hits[0]
        return None

    def _add_unresolved_reference(
        self,
        source_artifact: str,
        token: str,
        rel: str,
        line_number: int,
    ) -> None:
        candidate = token.lstrip("./")
        root = candidate.split("/", 1)[0]
        if "/" not in candidate or root not in self.top_level_roots:
            return
        node_id = "unresolved:" + _stable_fragment(candidate)
        self.add_node(
            node_id,
            "unresolved_reference",
            candidate,
            "finding",
            properties={"reference": candidate, "resolution": "UNRESOLVED"},
            provenance=self.provenance(
                rel,
                "unresolved_path_reference",
                locator=f"line:{line_number}",
            ),
        )
        self.add_edge(
            source_artifact,
            node_id,
            "REFERENCES",
            "OBSERVED",
            "finding",
            properties={"resolution": "UNRESOLVED"},
            provenance=self.provenance(
                rel,
                "regex_path_reference",
                locator=f"line:{line_number}",
            ),
        )

    def _add_section(
        self,
        artifact_id: str,
        rel: str,
        line_number: int,
        level: int,
        title: str,
    ) -> None:
        clean_title = re.sub(r"\s+", " ", title).strip().strip("#")
        if not clean_title:
            return
        node_id = f"section:{rel}#L{line_number}"
        self.add_node(
            node_id,
            "section",
            clean_title[:300],
            "source",
            properties={"path": rel, "line": line_number, "level": level},
            provenance=self.provenance(
                rel,
                "markdown_heading",
                locator=f"line:{line_number}",
            ),
        )
        self.add_edge(
            artifact_id,
            node_id,
            "DECLARES",
            "OBSERVED",
            "source",
            provenance=self.provenance(
                rel,
                "markdown_heading",
                locator=f"line:{line_number}",
            ),
        )

    def _scan_text_references(self, rel: str, text: str) -> None:
        artifact_id = self.path_to_node[rel]
        heading_count = 0
        for line_number, line in enumerate(text.splitlines(), 1):
            if rel.lower().endswith((".md", ".mermaid")) and heading_count < 100:
                heading = MARKDOWN_HEADING_RE.match(line)
                if heading:
                    heading_count += 1
                    self._add_section(
                        artifact_id,
                        rel,
                        line_number,
                        len(heading.group(1)),
                        heading.group(2),
                    )

            for match in PATH_REF_RE.finditer(line):
                token = match.group(1)
                resolved = self._resolve_path_reference(token)
                if resolved:
                    target = self.path_to_node[resolved]
                    if target != artifact_id:
                        self.add_edge(
                            artifact_id,
                            target,
                            "REFERENCES",
                            "OBSERVED",
                            "source",
                            properties={"token": token, "resolution": "EXACT_OR_UNIQUE"},
                            provenance=self.provenance(
                                rel,
                                "regex_path_reference",
                                locator=f"line:{line_number}",
                            ),
                        )
                else:
                    self._add_unresolved_reference(artifact_id, token, rel, line_number)

            for work_id in WORK_ITEM_RE.findall(line):
                node_id = "work_item:" + work_id
                family = work_id.split("-", 1)[0]
                self.add_node(
                    node_id,
                    "work_item",
                    work_id,
                    "external",
                    properties={"work_item_id": work_id, "family": family},
                    provenance=self.provenance(
                        rel,
                        "identifier_reference",
                        locator=f"line:{line_number}",
                    ),
                )
                self.add_edge(
                    artifact_id,
                    node_id,
                    "REFERENCES_WORK_ITEM",
                    "OBSERVED",
                    "external",
                    provenance=self.provenance(
                        rel,
                        "identifier_reference",
                        locator=f"line:{line_number}",
                    ),
                )

            for number in GITHUB_REF_RE.findall(line):
                node_id = "github_item:" + number
                self.add_node(
                    node_id,
                    "github_item",
                    "#" + number,
                    "external",
                    properties={
                        "number": int(number),
                        "repository": self.profile.get("repository"),
                        "state": "UNKNOWN",
                        "kind": "ISSUE_OR_PULL_REQUEST",
                        "url": f"https://github.com/{self.profile.get('repository')}/issues/{number}",
                    },
                    provenance=self.provenance(
                        rel,
                        "github_shorthand_reference",
                        locator=f"line:{line_number}",
                    ),
                )
                self.add_edge(
                    artifact_id,
                    node_id,
                    "REFERENCES_GITHUB_ITEM",
                    "OBSERVED",
                    "external",
                    provenance=self.provenance(
                        rel,
                        "github_shorthand_reference",
                        locator=f"line:{line_number}",
                    ),
                )

    def _resolve_import(
        self,
        module: str | None,
        *,
        current_rel: str,
        level: int = 0,
    ) -> str | None:
        module = module or ""
        current = PurePosixPath(current_rel).with_suffix("")
        package_parts = list(current.parts[:-1])
        if level:
            if level > len(package_parts) + 1:
                return None
            keep = len(package_parts) - level + 1
            package_parts = package_parts[: max(0, keep)]
            if module:
                package_parts.extend(module.split("."))
            module = ".".join(package_parts)
        candidates = [module]
        if module.startswith("src."):
            candidates.append(module[4:])
        for candidate in candidates:
            hits = self.module_map.get(candidate, [])
            if len(hits) == 1:
                return hits[0]
        return None

    def _scan_python(self, rel: str, text: str) -> None:
        artifact_id = self.path_to_node[rel]
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError as exc:
            node_id = "parse_failure:" + _stable_fragment([rel, exc.lineno, exc.msg])
            self.add_node(
                node_id,
                "parse_failure",
                f"{rel}:{exc.lineno}: {exc.msg}",
                "finding",
                properties={"path": rel, "line": exc.lineno, "message": exc.msg},
                provenance=self.provenance(
                    rel,
                    "python_ast_parse",
                    locator=f"line:{exc.lineno or 0}",
                ),
            )
            self.add_edge(
                artifact_id,
                node_id,
                "HAS_FINDING",
                "OBSERVED",
                "finding",
                provenance=self.provenance(rel, "python_ast_parse"),
            )
            return

        for item in tree.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbol_type = "class" if isinstance(item, ast.ClassDef) else "function"
                symbol_id = f"symbol:{rel}#{item.name}@L{item.lineno}"
                self.add_node(
                    symbol_id,
                    "symbol",
                    item.name,
                    "source",
                    properties={
                        "path": rel,
                        "line": item.lineno,
                        "symbol_kind": symbol_type,
                        "async": isinstance(item, ast.AsyncFunctionDef),
                    },
                    provenance=self.provenance(
                        rel,
                        "python_ast_definition",
                        locator=f"line:{item.lineno}",
                    ),
                )
                self.add_edge(
                    artifact_id,
                    symbol_id,
                    "DECLARES",
                    "OBSERVED",
                    "source",
                    provenance=self.provenance(
                        rel,
                        "python_ast_definition",
                        locator=f"line:{item.lineno}",
                    ),
                )

            imports: list[tuple[str, int, int]] = []
            if isinstance(item, ast.Import):
                imports = [(alias.name, 0, item.lineno) for alias in item.names]
            elif isinstance(item, ast.ImportFrom):
                imports = [(item.module or "", item.level, item.lineno)]
            for module, level, line_number in imports:
                resolved = self._resolve_import(
                    module,
                    current_rel=rel,
                    level=level,
                )
                if resolved:
                    target = self.path_to_node[resolved]
                    relation = "TESTS" if self.path_kinds.get(rel) == "test" else "IMPORTS"
                    self.add_edge(
                        artifact_id,
                        target,
                        relation,
                        "OBSERVED",
                        "source",
                        properties={"module": module, "relative_level": level},
                        provenance=self.provenance(
                            rel,
                            "python_ast_import",
                            locator=f"line:{line_number}",
                        ),
                    )
                else:
                    name = ("." * level) + module
                    if not name:
                        continue
                    node_id = "module:" + name
                    self.add_node(
                        node_id,
                        "module",
                        name,
                        "external",
                        properties={"resolution": "EXTERNAL_OR_UNRESOLVED"},
                        provenance=self.provenance(
                            rel,
                            "python_ast_import",
                            locator=f"line:{line_number}",
                        ),
                    )
                    self.add_edge(
                        artifact_id,
                        node_id,
                        "IMPORTS",
                        "OBSERVED",
                        "external",
                        properties={"module": name, "resolution": "EXTERNAL_OR_UNRESOLVED"},
                        provenance=self.provenance(
                            rel,
                            "python_ast_import",
                            locator=f"line:{line_number}",
                        ),
                    )

    def _scan_workflow(self, rel: str, text: str) -> None:
        if yaml is None:
            return
        try:
            data = yaml.safe_load(text) or {}
        except Exception as exc:
            node_id = "parse_failure:" + _stable_fragment([rel, str(exc)])
            self.add_node(
                node_id,
                "parse_failure",
                f"{rel}: YAML parse failure",
                "finding",
                properties={"path": rel, "message": str(exc)},
                provenance=self.provenance(rel, "yaml_parse"),
            )
            self.add_edge(
                self.path_to_node[rel],
                node_id,
                "HAS_FINDING",
                "OBSERVED",
                "finding",
                provenance=self.provenance(rel, "yaml_parse"),
            )
            return
        if not isinstance(data, dict):
            return
        workflow_id = "workflow:" + rel
        name = str(data.get("name") or PurePosixPath(rel).stem)
        self.add_node(
            workflow_id,
            "workflow",
            name,
            "source",
            properties={"path": rel, "declared_name": name},
            provenance=self.provenance(rel, "github_workflow_parse"),
        )
        self.add_edge(
            self.path_to_node[rel],
            workflow_id,
            "DECLARES",
            "OBSERVED",
            "source",
            provenance=self.provenance(rel, "github_workflow_parse"),
        )
        jobs = data.get("jobs") or {}
        if not isinstance(jobs, dict):
            return
        job_ids: dict[str, str] = {}
        for job_name, job in jobs.items():
            if not isinstance(job, dict):
                continue
            job_id = f"workflow_job:{rel}#{job_name}"
            job_ids[str(job_name)] = job_id
            self.add_node(
                job_id,
                "workflow_job",
                str(job.get("name") or job_name),
                "source",
                properties={
                    "path": rel,
                    "job_id": str(job_name),
                    "runs_on": job.get("runs-on"),
                },
                provenance=self.provenance(rel, "github_workflow_job"),
            )
            self.add_edge(
                workflow_id,
                job_id,
                "CONTAINS",
                "OBSERVED",
                "source",
                provenance=self.provenance(rel, "github_workflow_job"),
            )
            for step_index, step in enumerate(job.get("steps") or []):
                if not isinstance(step, dict):
                    continue
                action = step.get("uses")
                if action:
                    action_id = "action_dependency:" + str(action)
                    self.add_node(
                        action_id,
                        "action_dependency",
                        str(action),
                        "external",
                        properties={"coordinate": str(action)},
                        provenance=self.provenance(
                            rel,
                            "github_workflow_uses",
                            locator=f"job:{job_name}/step:{step_index}",
                        ),
                    )
                    self.add_edge(
                        job_id,
                        action_id,
                        "USES_ACTION",
                        "OBSERVED",
                        "external",
                        provenance=self.provenance(
                            rel,
                            "github_workflow_uses",
                            locator=f"job:{job_name}/step:{step_index}",
                        ),
                    )
                run = step.get("run")
                if isinstance(run, str):
                    for token in PATH_REF_RE.findall(run):
                        resolved = self._resolve_path_reference(token)
                        if resolved:
                            self.add_edge(
                                job_id,
                                self.path_to_node[resolved],
                                "INVOKES",
                                "OBSERVED",
                                "source",
                                properties={"token": token},
                                provenance=self.provenance(
                                    rel,
                                    "github_workflow_run_reference",
                                    locator=f"job:{job_name}/step:{step_index}",
                                ),
                            )
        for job_name, job in jobs.items():
            if not isinstance(job, dict) or str(job_name) not in job_ids:
                continue
            needs = job.get("needs") or []
            if isinstance(needs, str):
                needs = [needs]
            for dependency in needs:
                if str(dependency) in job_ids:
                    self.add_edge(
                        job_ids[str(job_name)],
                        job_ids[str(dependency)],
                        "DEPENDS_ON",
                        "OBSERVED",
                        "source",
                        provenance=self.provenance(rel, "github_workflow_needs"),
                    )

    def _walk_json_refs(self, value: Any) -> Iterable[str]:
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "$ref" and isinstance(child, str):
                    yield child
                else:
                    yield from self._walk_json_refs(child)
        elif isinstance(value, list):
            for child in value:
                yield from self._walk_json_refs(child)

    def _scan_schema(self, rel: str, text: str) -> None:
        if not rel.lower().endswith(".json"):
            return
        try:
            data = json.loads(text)
        except ValueError:
            return
        if not isinstance(data, dict) or not (
            "$schema" in data or rel.endswith(".schema.json") or rel.startswith("schemas/")
        ):
            return
        schema_id = "schema:" + rel
        self.add_node(
            schema_id,
            "schema",
            str(data.get("title") or rel),
            "source",
            properties={
                "path": rel,
                "schema_id": data.get("$id"),
                "dialect": data.get("$schema"),
                "required": data.get("required") or [],
            },
            provenance=self.provenance(rel, "json_schema_parse"),
        )
        self.add_edge(
            self.path_to_node[rel],
            schema_id,
            "DECLARES",
            "OBSERVED",
            "source",
            provenance=self.provenance(rel, "json_schema_parse"),
        )
        for ref in self._walk_json_refs(data):
            file_part = ref.split("#", 1)[0]
            if not file_part:
                continue
            resolved = self._resolve_path_reference(file_part)
            if resolved:
                target = self.path_to_node[resolved]
            else:
                target = "external_schema:" + ref
                self.add_node(
                    target,
                    "schema",
                    ref,
                    "external",
                    properties={"reference": ref, "resolution": "EXTERNAL_OR_UNRESOLVED"},
                    provenance=self.provenance(rel, "json_schema_ref"),
                )
            self.add_edge(
                schema_id,
                target,
                "REFERENCES_SCHEMA",
                "OBSERVED",
                "source" if resolved else "external",
                properties={"ref": ref},
                provenance=self.provenance(rel, "json_schema_ref"),
            )

    def _scan_contents(self) -> None:
        self._build_module_map()
        exclusions = self.profile.get("content_scan_exclusions") or []
        for rel in self.scanned_paths:
            path = self.repo / rel
            node = self.nodes[self.path_to_node[rel]]
            props = node["properties"]
            if props.get("symlink") or _matches_any(rel, exclusions):
                props["content_scan_reason"] = "EXCLUDED_OR_SYMLINK"
                continue
            if props["size_bytes"] > 1_500_000:
                props["content_scan_reason"] = "SIZE_LIMIT"
                continue
            suffix = PurePosixPath(rel).suffix.lower()
            if suffix not in TEXT_SUFFIXES:
                props["content_scan_reason"] = "NON_TEXT_SUFFIX"
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                props["content_scan_reason"] = "NOT_UTF8"
                continue
            props["content_scanned"] = True
            props["content_scan_reason"] = "SCANNED"
            self._scan_text_references(rel, text)
            if suffix == ".py":
                self._scan_python(rel, text)
            if rel.startswith(".github/workflows/") and suffix in {".yaml", ".yml"}:
                self._scan_workflow(rel, text)
            if self.path_kinds.get(rel) == "schema":
                self._scan_schema(rel, text)

    def _artifact_for_source(self, source_ref: str) -> str | None:
        path = source_ref.split("#", 1)[0]
        return self.path_to_node.get(path)

    def _import_profile_semantics(self) -> None:
        repo_id = "repo:" + str(self.profile.get("repository") or self.repo.name)
        profile_prov = self.provenance(self.profile_rel, "graph_profile")
        for item in self.profile.get("canonical_artifacts") or []:
            path = str(item.get("path") or "")
            artifact_id = self.path_to_node.get(path)
            if not artifact_id:
                continue
            self.annotate_node(
                artifact_id,
                {
                    "canonical_roles": [item.get("role")],
                    "authority_class": item.get("authority_class"),
                    "canonical_note": item.get("note"),
                },
            )
            self.add_edge(
                repo_id,
                artifact_id,
                "HAS_CANONICAL_ARTIFACT",
                "SPECIFIED",
                "semantic",
                properties={
                    "role": item.get("role"),
                    "authority_class": item.get("authority_class"),
                },
                provenance=profile_prov,
            )

        for item in self.profile.get("semantic_nodes") or []:
            node_id = str(item["id"])
            source_ref = str(item["source_ref"])
            self.add_node(
                node_id,
                str(item["type"]),
                str(item["label"]),
                "semantic",
                properties={
                    **copy.deepcopy(item.get("properties") or {}),
                    "declared_state": item.get("state", "SPECIFIED"),
                    "authority_effect": "NONE",
                },
                provenance=self.provenance(source_ref, "explicit_profile_mapping"),
            )
            artifact_id = self._artifact_for_source(source_ref)
            if artifact_id:
                self.add_edge(
                    node_id,
                    artifact_id,
                    "CITES",
                    "OBSERVED",
                    "semantic",
                    properties={"citation_only": True},
                    provenance=profile_prov,
                )

        for item in self.profile.get("semantic_edges") or []:
            self.add_edge(
                str(item["from"]),
                str(item["to"]),
                str(item["relation"]),
                str(item.get("state") or "SPECIFIED"),
                "semantic",
                properties={"explicit_mapping": True},
                provenance=self.provenance(
                    str(item.get("source_ref") or self.profile_rel),
                    "explicit_profile_mapping",
                ),
            )

    @staticmethod
    def _declared_id(graph_id: str, local_id: Any) -> str:
        return f"declared:{graph_id}:{local_id}"

    def _source_graph_prov(self, path: str, locator: str | None = None) -> dict[str, Any]:
        return self.provenance(path, "declared_graph_import", locator=locator)

    def _link_declared_source(
        self,
        declared_node: str,
        source_ref: str | None,
        graph_path: str,
    ) -> None:
        if not source_ref:
            return
        artifact_id = self._artifact_for_source(str(source_ref))
        if artifact_id:
            self.add_edge(
                declared_node,
                artifact_id,
                "CITES",
                "OBSERVED",
                "declared",
                properties={"citation_only": True},
                provenance=self._source_graph_prov(graph_path),
            )

    def _import_intent(self, graph_id: str, path: str, data: dict[str, Any]) -> None:
        for node in data.get("nodes") or []:
            local = str(node["id"])
            node_id = self._declared_id(graph_id, local)
            properties = {key: value for key, value in node.items() if key not in {"id", "name"}}
            properties["origin_graph"] = graph_id
            self.add_node(
                node_id,
                str(node.get("type") or "declared_node"),
                str(node.get("name") or local),
                "declared",
                properties=properties,
                provenance=self._source_graph_prov(path, f"node:{local}"),
            )
            self._link_declared_source(node_id, node.get("source"), path)
        for edge in data.get("edges") or []:
            self.add_edge(
                self._declared_id(graph_id, edge.get("from")),
                self._declared_id(graph_id, edge.get("to")),
                str(edge.get("rel") or edge.get("relation") or "RELATED_TO"),
                "SPECIFIED",
                "declared",
                properties={"origin_graph": graph_id, **{
                    key: value
                    for key, value in edge.items()
                    if key not in {"from", "to", "rel", "relation"}
                }},
                provenance=self._source_graph_prov(path),
            )

    def _import_evidence(self, graph_id: str, path: str, data: dict[str, Any]) -> None:
        for node in data.get("nodes") or []:
            local = str(node["id"])
            node_id = self._declared_id(graph_id, local)
            self.add_node(
                node_id,
                str(node.get("type") or "declared_node"),
                str(node.get("label") or local),
                "declared",
                properties={
                    "origin_graph": graph_id,
                    **{key: value for key, value in node.items() if key not in {"id", "type", "label"}},
                },
                provenance=self._source_graph_prov(path, f"node:{local}"),
            )
            label = str(node.get("label") or "")
            if node.get("type") == "artifact" and label in self.path_to_node:
                self.add_edge(
                    node_id,
                    self.path_to_node[label],
                    "REPRESENTS",
                    "OBSERVED",
                    "declared",
                    provenance=self._source_graph_prov(path, f"node:{local}"),
                )
        for edge in data.get("edges") or []:
            state = str(edge.get("state") or "CLAIMED").upper()
            if state not in EVIDENCE_STATES:
                state = "CLAIMED"
            self.add_edge(
                self._declared_id(graph_id, edge.get("from")),
                self._declared_id(graph_id, edge.get("to")),
                str(edge.get("relation") or edge.get("rel") or "RELATED_TO"),
                state,
                "declared",
                properties={"origin_graph": graph_id},
                provenance=self._source_graph_prov(path),
            )

    def _import_system(self, graph_id: str, path: str, data: dict[str, Any]) -> None:
        nodes = data.get("nodes") or {}
        iterable = nodes.values() if isinstance(nodes, dict) else nodes
        for node in iterable:
            local = str(node["id"])
            node_id = self._declared_id(graph_id, local)
            properties = {
                "origin_graph": graph_id,
                **{key: value for key, value in node.items() if key not in {"id", "type", "name"}},
            }
            self.add_node(
                node_id,
                str(node.get("type") or "declared_node"),
                str(node.get("name") or node.get("label") or local),
                "declared",
                properties=properties,
                provenance=self._source_graph_prov(path, f"node:{local}"),
            )
            implementation = node.get("implementation")
            if isinstance(implementation, str):
                resolved = self._resolve_path_reference(implementation.split(" ", 1)[0])
                if resolved:
                    self.add_edge(
                        node_id,
                        self.path_to_node[resolved],
                        "DECLARES_IMPLEMENTATION",
                        "CLAIMED",
                        "declared",
                        properties={"declared_implementation": implementation},
                        provenance=self._source_graph_prov(path, f"node:{local}"),
                    )
        for edge in data.get("edges") or []:
            source = edge.get("source", edge.get("from"))
            target = edge.get("target", edge.get("to"))
            self.add_edge(
                self._declared_id(graph_id, source),
                self._declared_id(graph_id, target),
                str(edge.get("edge_type") or edge.get("rel") or edge.get("relation") or "RELATED_TO"),
                "CLAIMED",
                "declared",
                properties={
                    "origin_graph": graph_id,
                    **{
                        key: value
                        for key, value in edge.items()
                        if key not in {"source", "target", "from", "to", "edge_type", "rel", "relation"}
                    },
                },
                provenance=self._source_graph_prov(path),
            )

    def _import_capability(self, graph_id: str, path: str, data: dict[str, Any]) -> None:
        for node in [*(data.get("stages") or []), *(data.get("crb_nodes") or [])]:
            local = str(node["id"])
            node_id = self._declared_id(graph_id, local)
            node_type = node.get("type") or (
                "capability_stage" if local.startswith("CAP-") else "declared_node"
            )
            self.add_node(
                node_id,
                str(node_type),
                str(node.get("label") or local),
                "declared",
                properties={
                    "origin_graph": graph_id,
                    **{key: value for key, value in node.items() if key not in {"id", "type", "label"}},
                },
                provenance=self._source_graph_prov(path, f"node:{local}"),
            )
            for ref in node.get("existing_refs") or []:
                file_ref = str(ref).split(":", 1)[0]
                self._link_declared_source(node_id, file_ref, path)
        for edge in data.get("edges") or []:
            self.add_edge(
                self._declared_id(graph_id, edge.get("from")),
                self._declared_id(graph_id, edge.get("to")),
                str(edge.get("rel") or "RELATED_TO"),
                "SPECIFIED",
                "declared",
                properties={"origin_graph": graph_id},
                provenance=self._source_graph_prov(path),
            )

    def _import_morphogenesis(self, graph_id: str, path: str, data: dict[str, Any]) -> None:
        collections = (
            ("change_hierarchy", "change_level"),
            ("event_types", "graph_delta_event"),
            ("projection_types", "projection"),
        )
        local_ids: set[str] = set()
        for key, fallback_type in collections:
            for node in data.get(key) or []:
                local = str(node["id"])
                local_ids.add(local)
                self.add_node(
                    self._declared_id(graph_id, local),
                    str(node.get("type") or fallback_type),
                    str(node.get("label") or node.get("name") or local),
                    "declared",
                    properties={
                        "origin_graph": graph_id,
                        "collection": key,
                        **{k: v for k, v in node.items() if k not in {"id", "type", "label", "name"}},
                    },
                    provenance=self._source_graph_prov(path, f"{key}:{local}"),
                )
        for edge in data.get("edges") or []:
            source_local = str(edge.get("from"))
            target_local = str(edge.get("to"))
            # morphogenesis.json deliberately links its HEP projections to CRB
            # nodes owned by capability_graph.json. Preserve that graph boundary
            # instead of manufacturing duplicate morphogenesis identities.
            source_graph = graph_id if source_local in local_ids else "capability"
            target_graph = graph_id if target_local in local_ids else "capability"
            self.add_edge(
                self._declared_id(source_graph, source_local),
                self._declared_id(target_graph, target_local),
                str(edge.get("rel") or "RELATED_TO"),
                "SPECIFIED",
                "declared",
                properties={"origin_graph": graph_id},
                provenance=self._source_graph_prov(path),
            )

    def _import_workflows(self, graph_id: str, path: str, data: dict[str, Any]) -> None:
        capability_graph_id = "capability"
        for workflow in data.get("workflows") or []:
            local = str(workflow["id"])
            node_id = self._declared_id(graph_id, local)
            self.add_node(
                node_id,
                "review_workflow",
                str(workflow.get("name") or local),
                "declared",
                properties={
                    "origin_graph": graph_id,
                    **{key: value for key, value in workflow.items() if key not in {"id", "name"}},
                },
                provenance=self._source_graph_prov(path, f"workflow:{local}"),
            )
            for cap in workflow.get("capability_stages") or []:
                self.add_edge(
                    self._declared_id(capability_graph_id, cap),
                    node_id,
                    "REQUIRED_BY",
                    "SPECIFIED",
                    "declared",
                    properties={"origin_graph": graph_id},
                    provenance=self._source_graph_prov(path, f"workflow:{local}"),
                )

    def _alignment_referent(self, value: Any, path: str) -> str:
        text = str(value)
        if text in {"None", ""}:
            text = "UNSPECIFIED"
        node_id = self._declared_id("alignment", "referent:" + text)
        self.add_node(
            node_id,
            "alignment_referent",
            text,
            "declared",
            properties={"origin_graph": "alignment"},
            provenance=self._source_graph_prov(path),
        )
        return node_id

    def _import_alignment(self, graph_id: str, path: str, data: dict[str, Any]) -> None:
        for index, row in enumerate(data.get("alignments") or []):
            source = self._declared_id("intent", row.get("intent"))
            target = self._declared_id("evidence", row.get("evidence"))
            if source not in self.nodes:
                source = self._alignment_referent(row.get("intent"), path)
            if target not in self.nodes:
                target = self._alignment_referent(row.get("evidence"), path)
            self.add_edge(
                source,
                target,
                str(row.get("kind") or "ALIGNS_WITH"),
                "SPECIFIED",
                "declared",
                properties={
                    "origin_graph": graph_id,
                    "basis": row.get("basis"),
                    "alignment_index": index,
                },
                provenance=self._source_graph_prov(path, f"alignment:{index}"),
            )
        for index, row in enumerate(data.get("divergences") or []):
            node_id = self._declared_id(graph_id, f"divergence:{index}")
            self.add_node(
                node_id,
                "divergence",
                str(row.get("class") or f"Divergence {index + 1}"),
                "declared",
                properties={"origin_graph": graph_id, **copy.deepcopy(row)},
                provenance=self._source_graph_prov(path, f"divergence:{index}"),
            )
            for side in ("intent", "evidence"):
                value = row.get(side)
                if value is None:
                    continue
                target = self._declared_id(side, value)
                if target not in self.nodes:
                    target = self._alignment_referent(value, path)
                self.add_edge(
                    node_id,
                    target,
                    "DIVERGES_ON",
                    "SPECIFIED",
                    "declared",
                    properties={"side": side},
                    provenance=self._source_graph_prov(path, f"divergence:{index}"),
                )

    def _import_artifact_inventory(
        self,
        graph_id: str,
        path: str,
        _: dict[str, Any] | None = None,
    ) -> None:
        source = self.repo / path
        for line_number, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except ValueError as exc:
                node_id = "parse_failure:" + _stable_fragment([path, line_number])
                self.add_node(
                    node_id,
                    "parse_failure",
                    f"{path}:{line_number}: invalid JSONL",
                    "finding",
                    properties={"message": str(exc)},
                    provenance=self.provenance(
                        path,
                        "jsonl_parse",
                        locator=f"line:{line_number}",
                    ),
                )
                continue
            artifact_path = row.get("path")
            target = self.path_to_node.get(str(artifact_path))
            assertion = {
                key: value
                for key, value in row.items()
                if key not in {"path", "title"}
            }
            if target:
                self.annotate_node(target, {"historical_inventory_assertions": [assertion]})
                self.nodes[target]["provenance"] = _dedupe_records([
                    *self.nodes[target]["provenance"],
                    self.provenance(
                        path,
                        "historical_inventory_annotation",
                        locator=f"line:{line_number}",
                    ),
                ])
            else:
                local = row.get("artifact_id") or f"row:{line_number}"
                node_id = self._declared_id(graph_id, local)
                self.add_node(
                    node_id,
                    "inventory_record",
                    str(row.get("title") or local),
                    "declared",
                    properties={"origin_graph": graph_id, **row},
                    provenance=self.provenance(
                        path,
                        "historical_inventory_import",
                        locator=f"line:{line_number}",
                    ),
                )

    def _import_source_graphs(self) -> None:
        adapters = {
            "intent": self._import_intent,
            "evidence": self._import_evidence,
            "system": self._import_system,
            "capability": self._import_capability,
            "morphogenesis": self._import_morphogenesis,
            "workflows": self._import_workflows,
            "alignment": self._import_alignment,
            "artifact_inventory": self._import_artifact_inventory,
        }
        for spec in self.profile.get("source_graphs") or []:
            graph_id = str(spec["id"])
            path = str(spec["path"])
            adapter_name = str(spec["adapter"])
            if adapter_name not in adapters:
                raise SpecLoadFailed(f"unknown source graph adapter: {adapter_name}")
            if path not in self.path_to_node:
                raise SpecLoadFailed(f"source graph missing from repository: {path}")
            artifact_id = self.path_to_node[path]
            self.annotate_node(
                artifact_id,
                {
                    "source_graph_id": graph_id,
                    "source_graph_adapter": adapter_name,
                    "declared_status": spec.get("declared_status"),
                    "authority_effect": "NONE",
                },
            )
            if adapter_name == "artifact_inventory":
                adapters[adapter_name](graph_id, path, None)
                continue
            data = _load_structured(self.repo / path)
            if not isinstance(data, dict):
                raise SpecLoadFailed(f"source graph must be an object: {path}")
            before = set(self.nodes)
            adapters[adapter_name](graph_id, path, data)
            imported = sorted(set(self.nodes) - before)
            for node_id in imported:
                self.add_edge(
                    artifact_id,
                    node_id,
                    "DECLARES",
                    "OBSERVED",
                    "declared",
                    properties={"origin_graph": graph_id},
                    provenance=self._source_graph_prov(path),
                )

    @staticmethod
    def _inference_confidence(
        rule: dict[str, Any],
        premise_edges: list[dict[str, Any]],
    ) -> float:
        premise_confidences = [
            float(provenance.get("confidence", 1.0))
            for edge in premise_edges
            for provenance in edge.get("provenance") or []
        ]
        premise_floor = min(premise_confidences) if premise_confidences else 0.0
        return round(float(rule.get("confidence", 0.5)) * premise_floor, 6)

    def _inference_provenance(
        self,
        rule: dict[str, Any],
        premise_edges: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        records = [
            self.provenance(
                self.profile_rel,
                "deterministic_inference_rule",
                locator=str(rule["id"]),
                confidence=float(rule.get("confidence", 0.5)),
            )
        ]
        for edge in premise_edges:
            for provenance in edge.get("provenance") or []:
                copied = copy.deepcopy(provenance)
                copied["method"] = (
                    "inference_premise:" + str(copied.get("method") or "unknown")
                )
                records.append(copied)
        return _dedupe_records(records)

    def _two_edge_candidates(
        self,
        rule: dict[str, Any],
        base_edges: list[dict[str, Any]],
        out_index: dict[tuple[str, str], list[dict[str, Any]]],
        in_index: dict[tuple[str, str], list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        left_relation = _clean_relation(str(rule["left_relation"]))
        right_relation = _clean_relation(str(rule["right_relation"]))
        right_direction = str(rule.get("right_direction") or "out")
        if right_direction not in {"out", "in"}:
            raise SpecLoadFailed(
                f"inference rule {rule['id']} has invalid right_direction"
            )
        subject_types = set(rule.get("subject_types") or [])
        intermediate_types = set(rule.get("intermediate_types") or [])
        object_types = set(rule.get("object_types") or [])
        exclude_direct = {
            _clean_relation(value)
            for value in rule.get("exclude_if_direct_relations") or []
        }
        existing = {
            (edge["from"], edge["relation"], edge["to"])
            for edge in base_edges
        }
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for left in base_edges:
            if left["relation"] != left_relation:
                continue
            subject = left["from"]
            intermediate = left["to"]
            subject_node = self.nodes.get(subject)
            intermediate_node = self.nodes.get(intermediate)
            if not subject_node or not intermediate_node:
                continue
            if subject_types and subject_node["type"] not in subject_types:
                continue
            if intermediate_types and intermediate_node["type"] not in intermediate_types:
                continue
            index = out_index if right_direction == "out" else in_index
            for right in index.get((intermediate, right_relation), []):
                object_id = right["to"] if right_direction == "out" else right["from"]
                object_node = self.nodes.get(object_id)
                if not object_node:
                    continue
                if object_types and object_node["type"] not in object_types:
                    continue
                if subject == object_id and not rule.get("allow_self"):
                    continue
                if any(
                    (subject, relation, object_id) in existing
                    for relation in exclude_direct
                ):
                    continue
                key = (subject, object_id)
                record = grouped.setdefault(
                    key,
                    {
                        "subject": subject,
                        "object": object_id,
                        "premise_sets": set(),
                        "binding_nodes": {"intermediate": set()},
                    },
                )
                record["premise_sets"].add((left["id"], right["id"]))
                record["binding_nodes"]["intermediate"].add(intermediate)
        output: list[dict[str, Any]] = []
        for key in sorted(grouped):
            record = grouped[key]
            premise_sets = sorted(record["premise_sets"])
            output.append({
                "subject": record["subject"],
                "object": record["object"],
                "premise_edge_ids": sorted({
                    edge_id for premise_set in premise_sets for edge_id in premise_set
                }),
                "premise_sets": [list(item) for item in premise_sets],
                "binding_nodes": {
                    "intermediate": sorted(record["binding_nodes"]["intermediate"]),
                },
            })
        return output

    def _shared_target_candidates(
        self,
        rule: dict[str, Any],
        in_index: dict[tuple[str, str], list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        relation = _clean_relation(str(rule["premise_relation"]))
        minimum = int(rule.get("minimum_distinct_sources", 2))
        source_types = set(rule.get("source_types") or [])
        target_types = set(rule.get("target_types") or [])
        output: list[dict[str, Any]] = []
        for target in sorted(self.nodes):
            target_node = self.nodes[target]
            if target_types and target_node["type"] not in target_types:
                continue
            premises = [
                edge for edge in in_index.get((target, relation), [])
                if not source_types
                or self.nodes.get(edge["from"], {}).get("type") in source_types
            ]
            sources = sorted({edge["from"] for edge in premises})
            if len(sources) < minimum:
                continue
            output.append({
                "subject": target,
                "object": None,
                "premise_edge_ids": sorted(edge["id"] for edge in premises),
                "premise_sets": [[edge["id"]] for edge in sorted(
                    premises, key=lambda item: item["id"]
                )],
                "binding_nodes": {"support_source": sources},
            })
        return output

    def _opposing_inbound_candidates(
        self,
        rule: dict[str, Any],
        in_index: dict[tuple[str, str], list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        positive_relation = _clean_relation(str(rule["positive_relation"]))
        negative_relation = _clean_relation(str(rule["negative_relation"]))
        target_types = set(rule.get("target_types") or [])
        output: list[dict[str, Any]] = []
        for target in sorted(self.nodes):
            target_node = self.nodes[target]
            if target_types and target_node["type"] not in target_types:
                continue
            positive = in_index.get((target, positive_relation), [])
            negative = in_index.get((target, negative_relation), [])
            if not positive or not negative:
                continue
            premises = sorted([*positive, *negative], key=lambda item: item["id"])
            output.append({
                "subject": target,
                "object": None,
                "premise_edge_ids": [edge["id"] for edge in premises],
                "premise_sets": [[edge["id"]] for edge in premises],
                "binding_nodes": {
                    "support_source": sorted({edge["from"] for edge in positive}),
                    "contradiction_source": sorted({
                        edge["from"] for edge in negative
                    }),
                },
            })
        return output

    def _contested_dependency_candidates(
        self,
        rule: dict[str, Any],
        base_edges: list[dict[str, Any]],
        out_index: dict[tuple[str, str], list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        negative_relations = {
            _clean_relation(value)
            for value in rule.get("negative_relations") or []
        }
        dependency_relations = {
            _clean_relation(value)
            for value in rule.get("dependency_relations") or []
        }
        evidence_types = set(rule.get("evidence_types") or [])
        dependent_types = set(rule.get("dependent_types") or [])
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for negative in base_edges:
            if negative["relation"] not in negative_relations:
                continue
            evidence_id = negative["to"]
            evidence_node = self.nodes.get(evidence_id)
            if not evidence_node:
                continue
            if evidence_types and evidence_node["type"] not in evidence_types:
                continue
            for dependency_relation in sorted(dependency_relations):
                for dependency in out_index.get(
                    (evidence_id, dependency_relation), []
                ):
                    dependent_id = dependency["to"]
                    dependent_node = self.nodes.get(dependent_id)
                    if not dependent_node:
                        continue
                    if dependent_types and dependent_node["type"] not in dependent_types:
                        continue
                    key = (dependent_id, evidence_id)
                    record = grouped.setdefault(
                        key,
                        {
                            "subject": dependent_id,
                            "object": evidence_id,
                            "premise_sets": set(),
                            "binding_nodes": {"contradiction_source": set()},
                        },
                    )
                    record["premise_sets"].add(
                        (negative["id"], dependency["id"])
                    )
                    record["binding_nodes"]["contradiction_source"].add(
                        negative["from"]
                    )
        output: list[dict[str, Any]] = []
        for key in sorted(grouped):
            record = grouped[key]
            premise_sets = sorted(record["premise_sets"])
            output.append({
                "subject": record["subject"],
                "object": record["object"],
                "premise_edge_ids": sorted({
                    edge_id for premise_set in premise_sets for edge_id in premise_set
                }),
                "premise_sets": [list(item) for item in premise_sets],
                "binding_nodes": {
                    "contradiction_source": sorted(
                        record["binding_nodes"]["contradiction_source"]
                    ),
                },
            })
        return output

    def _emit_inference_assertion(
        self,
        rule: dict[str, Any],
        candidate: dict[str, Any],
        edge_by_id: dict[str, dict[str, Any]],
        epistemic_state: str,
    ) -> str:
        relation = _clean_relation(str(rule["conclusion_relation"]))
        premise_edges = [
            edge_by_id[edge_id]
            for edge_id in candidate["premise_edge_ids"]
        ]
        conclusion = {
            "subject": candidate["subject"],
            "predicate": relation,
            "object": candidate.get("object"),
        }
        assertion_id = "inference:" + _stable_fragment(
            {"rule_id": rule["id"], "conclusion": conclusion},
            length=24,
        )
        object_label = (
            self.nodes[candidate["object"]]["label"]
            if candidate.get("object") else "∅"
        )
        label = (
            f"{self.nodes[candidate['subject']]['label']} "
            f"{relation} {object_label}"
        )
        properties = {
            "epistemic_state": epistemic_state,
            "rule_id": str(rule["id"]),
            "rule_sha256": _sha256_bytes(_canonical_bytes(rule)),
            "rule_kind": str(rule["kind"]),
            "rule_description": str(rule["description"]),
            "conclusion": conclusion,
            "confidence": self._inference_confidence(rule, premise_edges),
            "confidence_scope": "STRUCTURAL_RULE_APPLICATION_NOT_TRUTH",
            "independence": str(rule.get("independence") or "NOT_ESTABLISHED"),
            "review_state": "UNREVIEWED",
            "human_review_required": bool(rule.get("human_review_required", True)),
            "human_override_state": "NONE_RECORDED",
            "premise_edge_ids": list(candidate["premise_edge_ids"]),
            "premise_sha256": _sha256_bytes(
                _canonical_bytes(candidate["premise_edge_ids"])
            ),
            "premise_sets": copy.deepcopy(candidate.get("premise_sets") or []),
            "source_event_ids": list(candidate["premise_edge_ids"]),
            "recursive": False,
            "authority_effect": "NONE",
            "falsifier": str(rule["falsifier"]),
            "assumptions": list(rule.get("assumptions") or []),
            "not_evidence_of": list(rule.get("not_evidence_of") or []),
        }
        provenance = self._inference_provenance(rule, premise_edges)
        self.add_node(
            assertion_id,
            "inference_assertion",
            label,
            "inferred",
            properties=properties,
            provenance=provenance[0],
        )
        self.nodes[assertion_id]["provenance"] = _dedupe_records(provenance)

        link_targets: dict[str, list[str]] = {
            "subject": [candidate["subject"]],
        }
        if candidate.get("object"):
            link_targets["object"] = [candidate["object"]]
        for role, node_ids in (candidate.get("binding_nodes") or {}).items():
            link_targets[role] = list(node_ids)
        relation_by_role = {
            "subject": "INFERENCE_SUBJECT",
            "object": "INFERENCE_OBJECT",
            "intermediate": "INFERENCE_INTERMEDIATE",
            "support_source": "INFERENCE_SUPPORT_SOURCE",
            "contradiction_source": "INFERENCE_CONTRADICTION_SOURCE",
        }
        for role in sorted(link_targets):
            if role not in relation_by_role:
                raise SpecLoadFailed(
                    f"inference rule {rule['id']} emitted unknown binding role {role}"
                )
            for node_id in sorted(set(link_targets[role])):
                self.add_edge(
                    assertion_id,
                    node_id,
                    relation_by_role[role],
                    "OBSERVED",
                    "inferred",
                    properties={
                        "inference_assertion_id": assertion_id,
                        "inference_scaffold": True,
                        "rule_id": str(rule["id"]),
                        "role": role,
                    },
                    provenance=self.provenance(
                        self.profile_rel,
                        "inference_assertion_structure",
                        locator=str(rule["id"]),
                        confidence=properties["confidence"],
                    ),
                )
        return assertion_id

    def _apply_inference_rules(self) -> None:
        config = self.profile.get("inference") or {}
        if not config or not config.get("enabled"):
            return
        mode = str(config.get("mode") or "")
        if mode != "DETERMINISTIC_BOUNDED":
            raise SpecLoadFailed(f"unsupported inference mode: {mode}")
        if config.get("recursive") is not False:
            raise SpecLoadFailed("inference must be explicitly non-recursive")
        epistemic_state = str(config.get("epistemic_state") or "")
        if epistemic_state not in EPISTEMIC_STATES:
            raise SpecLoadFailed(f"unsupported inference epistemic state: {epistemic_state}")

        configured_forbidden = {
            _clean_relation(value)
            for value in config.get("forbidden_conclusion_relations") or []
        }
        forbidden = MANDATORY_FORBIDDEN_INFERENCE_RELATIONS | configured_forbidden
        total_limit = int(config.get("max_assertions", 5_000))
        if total_limit < 1:
            raise SpecLoadFailed("inference max_assertions must be at least 1")

        base_edges = sorted(
            (edge for edge in self.edges.values() if edge["layer"] != "inferred"),
            key=lambda item: item["id"],
        )
        edge_by_id = {edge["id"]: edge for edge in base_edges}
        out_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        in_index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for edge in base_edges:
            out_index[(edge["from"], edge["relation"])].append(edge)
            in_index[(edge["to"], edge["relation"])].append(edge)
        for index in (out_index, in_index):
            for key in index:
                index[key].sort(key=lambda item: item["id"])

        rule_reports: list[dict[str, Any]] = []
        seen_rule_ids: set[str] = set()
        assertion_count = 0
        any_truncated = False
        for rule in sorted(config.get("rules") or [], key=lambda item: str(item["id"])):
            rule_id = str(rule["id"])
            if rule_id in seen_rule_ids:
                raise SpecLoadFailed(f"duplicate inference rule id: {rule_id}")
            seen_rule_ids.add(rule_id)
            relation = _clean_relation(str(rule["conclusion_relation"]))
            if relation in forbidden:
                raise SpecLoadFailed(
                    f"inference rule {rule_id} uses forbidden conclusion {relation}"
                )
            enabled = bool(rule.get("enabled", True))
            candidates: list[dict[str, Any]] = []
            if enabled:
                kind = str(rule["kind"])
                if kind == "two_edge_join":
                    candidates = self._two_edge_candidates(
                        rule, base_edges, out_index, in_index
                    )
                elif kind == "shared_target":
                    candidates = self._shared_target_candidates(rule, in_index)
                elif kind == "opposing_inbound":
                    candidates = self._opposing_inbound_candidates(rule, in_index)
                elif kind == "contested_dependency":
                    candidates = self._contested_dependency_candidates(
                        rule, base_edges, out_index
                    )
                else:
                    raise SpecLoadFailed(
                        f"unknown inference rule kind {kind}: {rule_id}"
                    )
            rule_limit = int(rule.get("max_assertions", total_limit))
            remaining = max(total_limit - assertion_count, 0)
            emit_limit = min(rule_limit, remaining)
            selected = candidates[:emit_limit]
            truncated = len(candidates) > len(selected)
            for candidate in selected:
                self._emit_inference_assertion(
                    rule, candidate, edge_by_id, epistemic_state
                )
            assertion_count += len(selected)
            any_truncated = any_truncated or truncated
            rule_reports.append({
                "id": rule_id,
                "rule_sha256": _sha256_bytes(_canonical_bytes(rule)),
                "kind": str(rule["kind"]),
                "description": str(rule["description"]),
                "conclusion_relation": relation,
                "enabled": enabled,
                "candidate_count": len(candidates),
                "assertion_count": len(selected),
                "max_assertions": rule_limit,
                "truncated": truncated,
            })

        self.inference_report = {
            "enabled": True,
            "mode": mode,
            "epistemic_state": epistemic_state,
            "recursive": False,
            "authority_effect": "NONE",
            "assertion_count": assertion_count,
            "truncated": any_truncated,
            "forbidden_conclusion_relations": sorted(forbidden),
            "rules": rule_reports,
        }

    def _materialize_views(self) -> list[dict[str, Any]]:
        all_edges = list(self.edges.values())
        output: list[dict[str, Any]] = []
        for spec in self.profile.get("views") or []:
            selected: set[str] = set()
            node_types = set(spec.get("node_types") or [])
            origin_graphs = set(spec.get("origin_graphs") or [])
            prefixes = tuple(spec.get("id_prefixes") or [])
            relations = {_clean_relation(value) for value in spec.get("relations") or []}
            inference_predicates = {
                _clean_relation(value)
                for value in spec.get("inference_predicates") or []
            }
            for node_id, node in self.nodes.items():
                origin = node.get("properties", {}).get("origin_graph")
                inference_predicate = (
                    node.get("properties", {}).get("conclusion") or {}
                ).get("predicate")
                if (
                    (node_types and node["type"] in node_types)
                    or (origin_graphs and origin in origin_graphs)
                    or (prefixes and node_id.startswith(prefixes))
                    or (
                        inference_predicates
                        and inference_predicate in inference_predicates
                    )
                ):
                    selected.add(node_id)
            selected_edges: set[str] = set()
            for edge in all_edges:
                if relations and edge["relation"] in relations:
                    selected_edges.add(edge["id"])
                    selected.update((edge["from"], edge["to"]))
                elif edge["from"] in selected and edge["to"] in selected:
                    selected_edges.add(edge["id"])

            if spec.get("include_incident_edges"):
                incident_seeds = set(selected)
                for edge in all_edges:
                    if edge["from"] in incident_seeds or edge["to"] in incident_seeds:
                        selected_edges.add(edge["id"])
                        selected.update((edge["from"], edge["to"]))

            changed = True
            while changed:
                changed = False
                for edge in all_edges:
                    if edge["relation"] not in {"CITES", "DECLARES", "REPRESENTS"}:
                        continue
                    if edge["from"] in selected and edge["to"] not in selected:
                        target = self.nodes.get(edge["to"])
                        if target and target["type"] == "artifact":
                            selected.add(edge["to"])
                            selected_edges.add(edge["id"])
                            changed = True
            output.append({
                "id": str(spec["id"]),
                "title": str(spec["title"]),
                "description": str(spec["description"]),
                "node_ids": sorted(selected),
                "edge_ids": sorted(selected_edges),
                "counts": {"nodes": len(selected), "edges": len(selected_edges)},
            })
        return output

    def build(self) -> dict[str, Any]:
        self._add_repository_and_artifacts()
        self._scan_contents()
        self._import_profile_semantics()
        self._import_source_graphs()
        self._apply_inference_rules()

        nodes = sorted(self.nodes.values(), key=lambda item: item["id"])
        edges = sorted(self.edges.values(), key=lambda item: item["id"])
        views = self._materialize_views()
        graph = {
            "schema_version": SCHEMA_VERSION,
            "graph_id": str(self.profile["graph_id"]),
            "graph_kind": "DERIVED_READ_MODEL",
            "authority_effect": "NONE",
            "source": {
                "repository": str(self.profile["repository"]),
                "head_commit": self.head_commit,
                "head_committed_at": self.head_committed_at,
                "worktree_state": self.worktree_state,
                "source_tree_sha256": self.source_tree_sha256,
                "profile_path": self.profile_rel,
                "profile_sha256": self.file_hashes[self.profile_rel],
            },
            "invariants": sorted(set(self.profile.get("invariants") or [])),
            "ontology": {
                "evidence_states": list(EVIDENCE_STATES),
                "epistemic_states": list(EPISTEMIC_STATES),
                "node_types": sorted({node["type"] for node in nodes}),
                "relations": sorted({edge["relation"] for edge in edges}),
            },
            "nodes": nodes,
            "edges": edges,
            "inference": copy.deepcopy(self.inference_report),
            "views": views,
            "validation": {},
            "integrity": {
                "algorithm": "sha256",
                "canonicalization": "json-sort-keys-utf8",
                "sha256": None,
            },
        }
        graph["validation"] = validate_graph(graph, verify_integrity=False)
        graph["integrity"]["sha256"] = _graph_digest(graph)
        return graph


def _graph_digest(graph: dict[str, Any]) -> str:
    candidate = copy.deepcopy(graph)
    candidate.setdefault("integrity", {})["sha256"] = None
    return _sha256_bytes(_canonical_bytes(candidate))


def validate_graph(
    graph: dict[str, Any],
    *,
    verify_integrity: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    node_ids = [node.get("id") for node in nodes]
    edge_ids = [edge.get("id") for edge in edges]
    node_set = set(node_ids)
    edge_by_id = {edge.get("id"): edge for edge in edges}
    allowed_layers = {"source", "declared", "semantic", "external", "finding", "inferred"}

    if graph.get("graph_kind") != "DERIVED_READ_MODEL":
        errors.append("graph_kind must be DERIVED_READ_MODEL")
    if graph.get("authority_effect") != "NONE":
        errors.append("graph authority_effect must be NONE")
    if len(node_ids) != len(set(node_ids)):
        errors.append("duplicate node id")
    if len(edge_ids) != len(set(edge_ids)):
        errors.append("duplicate edge id")
    for node in nodes:
        for field in ("id", "type", "label", "layer", "properties", "provenance"):
            if field not in node:
                errors.append(f"node missing {field}: {node.get('id')}")
        if node.get("layer") not in allowed_layers:
            errors.append(f"invalid node layer {node.get('layer')}: {node.get('id')}")
        if not node.get("provenance"):
            errors.append(f"node has no provenance: {node.get('id')}")
    for edge in edges:
        for field in (
            "id", "from", "to", "relation", "evidence_state", "layer",
            "authority_effect", "properties", "provenance",
        ):
            if field not in edge:
                errors.append(f"edge missing {field}: {edge.get('id')}")
        if edge.get("from") not in node_set or edge.get("to") not in node_set:
            errors.append(
                f"dangling edge {edge.get('id')}: {edge.get('from')} -> {edge.get('to')}"
            )
        if edge.get("evidence_state") not in EVIDENCE_STATES:
            errors.append(
                f"invalid evidence state {edge.get('evidence_state')}: {edge.get('id')}"
            )
        if edge.get("authority_effect") != "NONE":
            errors.append(f"edge may not grant authority: {edge.get('id')}")
        if edge.get("layer") not in allowed_layers:
            errors.append(f"invalid edge layer {edge.get('layer')}: {edge.get('id')}")
        if not edge.get("provenance"):
            errors.append(f"edge has no provenance: {edge.get('id')}")

    inference = graph.get("inference")
    assertion_nodes = [
        node for node in nodes if node.get("type") == "inference_assertion"
    ]
    assertion_ids = {node.get("id") for node in assertion_nodes}
    if not isinstance(inference, dict):
        errors.append("graph missing inference metadata")
        inference = {}
    if inference.get("authority_effect") != "NONE":
        errors.append("inference authority_effect must be NONE")
    if inference.get("recursive") is not False:
        errors.append("inference must be non-recursive")
    if inference.get("epistemic_state") not in EPISTEMIC_STATES:
        errors.append("inference epistemic_state must be MODEL_INFERRED")
    if inference.get("assertion_count") != len(assertion_nodes):
        errors.append(
            "inference assertion_count does not match inference_assertion nodes"
        )
    reported_rules = inference.get("rules") or []
    reported_rule_ids = {rule.get("id") for rule in reported_rules}
    reported_rule_by_id = {rule.get("id"): rule for rule in reported_rules}
    if len(reported_rule_ids) != len(reported_rules):
        errors.append("duplicate inference rule report id")
    reported_assertion_count = sum(
        int(rule.get("assertion_count") or 0) for rule in reported_rules
    )
    if reported_assertion_count != len(assertion_nodes):
        errors.append("inference rule counts do not sum to assertion_count")
    forbidden = MANDATORY_FORBIDDEN_INFERENCE_RELATIONS | {
        _clean_relation(value)
        for value in inference.get("forbidden_conclusion_relations") or []
    }
    structural = {
        (edge.get("from"), edge.get("relation"), edge.get("to"))
        for edge in edges
        if edge.get("layer") == "inferred"
    }
    for node in assertion_nodes:
        node_id = node.get("id")
        properties = node.get("properties") or {}
        if node.get("layer") != "inferred":
            errors.append(f"inference assertion has non-inferred layer: {node_id}")
        if properties.get("epistemic_state") != "MODEL_INFERRED":
            errors.append(f"inference assertion has invalid epistemic state: {node_id}")
        if properties.get("authority_effect") != "NONE":
            errors.append(f"inference assertion may not grant authority: {node_id}")
        if properties.get("recursive") is not False:
            errors.append(f"inference assertion may not be recursive: {node_id}")
        if properties.get("rule_id") not in reported_rule_ids:
            errors.append(f"inference assertion has unknown rule: {node_id}")
        elif properties.get("rule_sha256") != reported_rule_by_id[
            properties.get("rule_id")
        ].get("rule_sha256"):
            errors.append(f"inference assertion rule hash mismatch: {node_id}")
        confidence = properties.get("confidence")
        if (
            isinstance(confidence, bool)
            or not isinstance(confidence, (int, float))
            or not 0 <= confidence <= 1
        ):
            errors.append(f"inference assertion has invalid confidence: {node_id}")
        if not properties.get("falsifier"):
            errors.append(f"inference assertion has no falsifier: {node_id}")
        if not properties.get("independence"):
            errors.append(f"inference assertion has no independence state: {node_id}")
        if properties.get("review_state") != "UNREVIEWED":
            errors.append(f"inference assertion review state is not UNREVIEWED: {node_id}")
        premise_ids = properties.get("premise_edge_ids") or []
        if not premise_ids:
            errors.append(f"inference assertion has no premises: {node_id}")
        if properties.get("premise_sha256") != _sha256_bytes(
            _canonical_bytes(premise_ids)
        ):
            errors.append(f"inference assertion premise hash mismatch: {node_id}")
        if properties.get("source_event_ids") != premise_ids:
            errors.append(f"inference source events differ from premises: {node_id}")
        for premise_id in premise_ids:
            premise = edge_by_id.get(premise_id)
            if not premise:
                errors.append(f"inference assertion has missing premise {premise_id}: {node_id}")
            elif premise.get("layer") == "inferred":
                errors.append(f"inference assertion uses inferred premise {premise_id}: {node_id}")
        conclusion = properties.get("conclusion") or {}
        subject = conclusion.get("subject")
        object_id = conclusion.get("object")
        predicate = conclusion.get("predicate")
        if subject not in node_set:
            errors.append(f"inference assertion has missing subject: {node_id}")
        if object_id is not None and object_id not in node_set:
            errors.append(f"inference assertion has missing object: {node_id}")
        if not predicate or predicate != _clean_relation(str(predicate)):
            errors.append(f"inference assertion has invalid predicate: {node_id}")
        elif predicate in forbidden:
            errors.append(f"inference assertion uses forbidden predicate {predicate}: {node_id}")
        if (node_id, "INFERENCE_SUBJECT", subject) not in structural:
            errors.append(f"inference assertion lacks subject link: {node_id}")
        if (
            object_id is not None
            and (node_id, "INFERENCE_OBJECT", object_id) not in structural
        ):
            errors.append(f"inference assertion lacks object link: {node_id}")
    for edge in edges:
        if edge.get("layer") != "inferred":
            continue
        if edge.get("relation") not in INFERENCE_LINK_RELATIONS:
            errors.append(f"invalid inferred edge relation: {edge.get('id')}")
        if edge.get("from") not in assertion_ids:
            errors.append(f"inferred edge source is not an assertion: {edge.get('id')}")
        if not edge.get("properties", {}).get("inference_scaffold"):
            errors.append(f"inferred edge is not marked as scaffold: {edge.get('id')}")
    view_ids: set[str] = set()
    for view in graph.get("views") or []:
        view_id = view.get("id")
        if view_id in view_ids:
            errors.append(f"duplicate view id: {view_id}")
        view_ids.add(view_id)
        missing_nodes = set(view.get("node_ids") or []) - node_set
        missing_edges = set(view.get("edge_ids") or []) - set(edge_ids)
        if missing_nodes:
            errors.append(f"view {view_id} has missing nodes: {sorted(missing_nodes)[:5]}")
        if missing_edges:
            errors.append(f"view {view_id} has missing edges: {sorted(missing_edges)[:5]}")
    if verify_integrity:
        expected = (graph.get("integrity") or {}).get("sha256")
        actual = _graph_digest(graph)
        if expected != actual:
            errors.append(f"integrity mismatch: expected {expected}, calculated {actual}")

    github_unknown = sum(
        1
        for node in nodes
        if node.get("type") == "github_item"
        and node.get("properties", {}).get("state") == "UNKNOWN"
    )
    unresolved = sum(1 for node in nodes if node.get("type") == "unresolved_reference")
    parse_failures = sum(1 for node in nodes if node.get("type") == "parse_failure")
    if github_unknown:
        warnings.append(
            f"{github_unknown} GitHub references have no ingested live metadata"
        )
    if unresolved:
        warnings.append(f"{unresolved} repository-like path references are unresolved")
    if parse_failures:
        warnings.append(f"{parse_failures} source artifacts could not be parsed")
    return {
        "valid": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "views": len(graph.get("views") or []),
            "github_items_without_metadata": github_unknown,
            "unresolved_references": unresolved,
            "parse_failures": parse_failures,
            "inference_assertions": len(assertion_nodes),
        },
    }


def _write_graphml(graph: dict[str, Any], path: Path) -> None:
    lines = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">",
        "  <key id=\"n_type\" for=\"node\" attr.name=\"type\" attr.type=\"string\"/>",
        "  <key id=\"n_label\" for=\"node\" attr.name=\"label\" attr.type=\"string\"/>",
        "  <key id=\"n_layer\" for=\"node\" attr.name=\"layer\" attr.type=\"string\"/>",
        "  <key id=\"n_epistemic\" for=\"node\" attr.name=\"epistemic_state\" attr.type=\"string\"/>",
        "  <key id=\"n_rule\" for=\"node\" attr.name=\"inference_rule\" attr.type=\"string\"/>",
        "  <key id=\"n_confidence\" for=\"node\" attr.name=\"inference_confidence\" attr.type=\"double\"/>",
        "  <key id=\"e_relation\" for=\"edge\" attr.name=\"relation\" attr.type=\"string\"/>",
        "  <key id=\"e_state\" for=\"edge\" attr.name=\"evidence_state\" attr.type=\"string\"/>",
        "  <key id=\"e_authority\" for=\"edge\" attr.name=\"authority_effect\" attr.type=\"string\"/>",
        "  <graph id=\"G\" edgedefault=\"directed\">",
    ]
    for node in graph["nodes"]:
        properties = node.get("properties") or {}
        lines.extend([
            f"    <node id=\"{html.escape(node['id'], quote=True)}\">",
            f"      <data key=\"n_type\">{html.escape(node['type'])}</data>",
            f"      <data key=\"n_label\">{html.escape(node['label'])}</data>",
            f"      <data key=\"n_layer\">{html.escape(node['layer'])}</data>",
            f"      <data key=\"n_epistemic\">{html.escape(str(properties.get('epistemic_state', '')))}</data>",
            f"      <data key=\"n_rule\">{html.escape(str(properties.get('rule_id', '')))}</data>",
            f"      <data key=\"n_confidence\">{html.escape(str(properties.get('confidence', '')))}</data>",
            "    </node>",
        ])
    for edge in graph["edges"]:
        lines.extend([
            (
                f"    <edge id=\"{html.escape(edge['id'], quote=True)}\" "
                f"source=\"{html.escape(edge['from'], quote=True)}\" "
                f"target=\"{html.escape(edge['to'], quote=True)}\">"
            ),
            f"      <data key=\"e_relation\">{html.escape(edge['relation'])}</data>",
            f"      <data key=\"e_state\">{html.escape(edge['evidence_state'])}</data>",
            f"      <data key=\"e_authority\">{html.escape(edge['authority_effect'])}</data>",
            "    </edge>",
        ])
    lines.extend(["  </graph>", "</graphml>", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _summary_markdown(graph: dict[str, Any]) -> str:
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_counts = Counter(node["type"] for node in nodes)
    relation_counts = Counter(edge["relation"] for edge in edges)
    state_counts = Counter(edge["evidence_state"] for edge in edges)
    layer_counts = Counter(node["layer"] for node in nodes)
    degree = Counter()
    for edge in edges:
        degree[edge["from"]] += 1
        degree[edge["to"]] += 1
    node_by_id = {node["id"]: node for node in nodes}
    top_nodes = [
        (node_by_id[node_id]["label"], node_by_id[node_id]["type"], count)
        for node_id, count in degree.most_common(15)
        if node_id in node_by_id
    ]
    tick = chr(96)
    fence = tick * 3
    lines = [
        "# HumanAIOS Operations Repository Knowledge Graph",
        "",
        "> Derived read model. It is not a governance source, authorization, or proof that a declared control operates.",
        "",
        "## Snapshot",
        "",
        f"- Repository: {tick}{graph['source']['repository']}{tick}",
        f"- HEAD: {tick}{graph['source']['head_commit']}{tick}",
        f"- Worktree: **{graph['source']['worktree_state']}**",
        f"- Source-tree digest: {tick}{graph['source']['source_tree_sha256']}{tick}",
        f"- Graph digest: {tick}{graph['integrity']['sha256']}{tick}",
        f"- Validation: **{'PASS' if graph['validation']['valid'] else 'FAIL'}**",
        "",
        "The source-tree digest identifies the exact scanned content even when the worktree is dirty. Rebuilding the same content and profile produces the same graph digest.",
        "",
        "## What this graph joins",
        "",
        f"{fence}mermaid",
        "flowchart TD",
        "  R[\"Repository artifacts\"] --> I[\"Intent projection\"]",
        "  R --> E[\"Evidence projection\"]",
        "  R --> S[\"System and workflow projection\"]",
        "  R --> M[\"CRB and morphogenesis projection\"]",
        "  I --> X[\"Explicit alignment only\"]",
        "  E --> X",
        "  S --> X",
        "  M --> X",
        "  X --> F[\"Bounded inference assertions\"]",
        "  F --> V[\"Bounded views\"]",
        f"{fence}",
        "",
        "The compiler namespaces imported graphs. Similar labels are not merged. Cross-graph identity exists only where an explicit alignment or curated mapping says it exists.",
        "",
        "## Action-centered control view",
        "",
        f"{fence}mermaid",
        "flowchart TD",
        "  I[Intent] --> C[Capability]",
        "  C --> E[Evidence]",
        "  E --> W[Warrant]",
        "  W --> A[Authorization]",
        "  A --> X[Action]",
        "  X --> O[Consequence]",
        "  O --> B[Observation]",
        "  B --> E",
        "  B --> K[Correction]",
        "  K --> I",
        f"{fence}",
        "",
        "Warrant informs authorization but does not grant it; authorization bounds action but is not evidence that execution occurred.",
        "",
        "## Accountability view",
        "",
        f"{fence}mermaid",
        "flowchart TD",
        "  Z1[\"Z1: propose\"] --> P[Proposal]",
        "  P --> Z2[\"Z2: ratify\"]",
        "  Z2 --> Z3[\"Z3: execute\"]",
        "  Z3 --> R[Receipt]",
        "  W[\"Witness: observe\"] --> R",
        f"{fence}",
        "",
        "## Scale",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Nodes | {len(nodes)} |",
        f"| Edges | {len(edges)} |",
        f"| Views | {len(graph['views'])} |",
    ]
    for layer, count in sorted(layer_counts.items()):
        lines.append(f"| Nodes · {layer} | {count} |")
    lines.extend([
        "",
        "### Evidence states",
        "",
        "| State | Edges | Meaning |",
        "|---|---:|---|",
    ])
    meanings = {
        "CLAIMED": "Declared relation; not verified by this graph.",
        "SPECIFIED": "Specified relationship or contract.",
        "IMPLEMENTED": "Implementation relationship explicitly represented.",
        "TESTED": "Test relationship explicitly represented.",
        "OBSERVED": "Mechanically observed source/provenance relation.",
    }
    for state in EVIDENCE_STATES:
        lines.append(f"| {state} | {state_counts.get(state, 0)} | {meanings[state]} |")
    inference = graph["inference"]
    lines.extend([
        "",
        "## Bounded inference",
        "",
        f"- Mode: {tick}{inference['mode']}{tick}",
        f"- Epistemic state: {tick}{inference['epistemic_state']}{tick}",
        f"- Assertions: {inference['assertion_count']}",
        f"- Recursive chaining: {tick}{str(inference['recursive']).lower()}{tick}",
        f"- Authority effect: {tick}{inference['authority_effect']}{tick}",
        f"- Truncated: {tick}{str(inference['truncated']).lower()}{tick}",
        "",
        "Each conclusion is an inference_assertion node, not a fact edge. It records its rule, conclusion, premise edge IDs, source events, confidence, independence state, uncertainty assumptions, falsifier, and human-review state. Confidence describes the structural rule application, not the truth of the conclusion.",
        "",
        "| Rule | Candidates | Assertions | Conclusion | Truncated |",
        "|---|---:|---:|---|---|",
    ])
    for rule in inference["rules"]:
        lines.append(
            f"| {rule['id']} | {rule['candidate_count']} | "
            f"{rule['assertion_count']} | {rule['conclusion_relation']} | "
            f"{str(rule['truncated']).lower()} |"
        )
    lines.extend([
        "",
        "## Views",
        "",
        "| View | Nodes | Edges | Purpose |",
        "|---|---:|---:|---|",
    ])
    for view in graph["views"]:
        lines.append(
            f"| {view['title']} | {view['counts']['nodes']} | "
            f"{view['counts']['edges']} | {view['description']} |"
        )
    lines.extend([
        "",
        "## Most connected referents",
        "",
        "| Node | Type | Degree |",
        "|---|---|---:|",
    ])
    for label, node_type, count in top_nodes:
        lines.append(f"| {label.replace('|', '/')} | {node_type} | {count} |")
    lines.extend([
        "",
        "## Largest node families",
        "",
        "| Node type | Count |",
        "|---|---:|",
    ])
    for node_type, count in node_counts.most_common(20):
        lines.append(f"| {node_type} | {count} |")
    lines.extend([
        "",
        "## Largest relation families",
        "",
        "| Relation | Count |",
        "|---|---:|",
    ])
    for relation, count in relation_counts.most_common(20):
        lines.append(f"| {relation} | {count} |")
    lines.extend([
        "",
        "## Coverage gaps preserved as gaps",
        "",
    ])
    for warning in graph["validation"]["warnings"] or ["No validation warnings."]:
        lines.append(f"- {warning}")
    lines.extend([
        "",
        "The graph does not infer whether a bare GitHub shorthand is an issue or pull request, does not treat file presence as operational effectiveness, and does not treat a test file or declared test count as a passed test run.",
        "",
        "## Files",
        "",
        f"- {tick}graph.json{tick}: canonical generated read model",
        f"- {tick}graph.json.gz{tick}: compressed canonical read model",
        f"- {tick}graph.graphml{tick}: Gephi/yEd-compatible interchange",
        f"- {tick}nodes.csv{tick} and {tick}edges.csv{tick}: tabular exports",
        f"- {tick}inferences.jsonl{tick} and {tick}inferences.csv{tick}: assertion-first inference exports",
        f"- {tick}views/*.json{tick}: bounded projections",
        f"- {tick}manifest.json{tick}: hashes for generated outputs",
        "",
        "## Rebuild and inspect",
        "",
        f"{fence}bash",
        "python3 tools/repository_knowledge_graph_v0_1.py build",
        "python3 tools/repository_knowledge_graph_v0_1.py validate --graph outputs/repository-knowledge-graph/graph.json",
        "python3 tools/repository_knowledge_graph_v0_1.py query --graph outputs/repository-knowledge-graph/graph.json --search warrant",
        "python3 tools/repository_knowledge_graph_v0_1.py query --graph outputs/repository-knowledge-graph/graph.json --rule RKG-INF-WORKFLOW-TEST-PATH-01",
        f"{fence}",
        "",
    ])
    return "\n".join(lines)


def write_report(output: dict[str, Any], output_dir: str | Path) -> str:
    """Write the primary JSON graph and return its path."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    graph_path = destination / "graph.json"
    graph_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return str(graph_path)


def write_outputs(graph: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    graph_path = Path(write_report(graph, output_dir))
    with (output_dir / "graph.json.gz").open("wb") as raw_handle:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            fileobj=raw_handle,
            compresslevel=9,
            mtime=0,
        ) as gzip_handle:
            gzip_handle.write(graph_path.read_bytes())
    _write_graphml(graph, output_dir / "graph.graphml")
    (output_dir / "summary.md").write_text(
        _summary_markdown(graph),
        encoding="utf-8",
    )
    with (output_dir / "nodes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "id", "type", "label", "layer", "origin_graph", "epistemic_state",
            "inference_rule", "inference_confidence", "source_ref",
        ])
        for node in graph["nodes"]:
            source_ref = node["provenance"][0].get("source_ref") if node["provenance"] else ""
            properties = node.get("properties") or {}
            writer.writerow([
                node["id"],
                node["type"],
                node["label"],
                node["layer"],
                properties.get("origin_graph", ""),
                properties.get("epistemic_state", ""),
                properties.get("rule_id", ""),
                properties.get("confidence", ""),
                source_ref,
            ])
    with (output_dir / "edges.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "id", "from", "to", "relation", "evidence_state", "layer", "source_ref"
        ])
        for edge in graph["edges"]:
            source_ref = edge["provenance"][0].get("source_ref") if edge["provenance"] else ""
            writer.writerow([
                edge["id"],
                edge["from"],
                edge["to"],
                edge["relation"],
                edge["evidence_state"],
                edge["layer"],
                source_ref,
            ])
    inference_nodes = [
        node for node in graph["nodes"]
        if node["type"] == "inference_assertion"
    ]
    (output_dir / "inferences.jsonl").write_text(
        "".join(
            json.dumps(node, ensure_ascii=False, sort_keys=True) + "\n"
            for node in inference_nodes
        ),
        encoding="utf-8",
    )
    with (output_dir / "inferences.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "id", "rule_id", "subject", "predicate", "object", "confidence",
            "independence", "review_state", "falsifier", "premise_edge_ids",
            "rule_sha256", "premise_sha256",
        ])
        for node in inference_nodes:
            properties = node["properties"]
            conclusion = properties["conclusion"]
            writer.writerow([
                node["id"],
                properties["rule_id"],
                conclusion["subject"],
                conclusion["predicate"],
                conclusion.get("object") or "",
                properties["confidence"],
                properties["independence"],
                properties["review_state"],
                properties["falsifier"],
                " ".join(properties["premise_edge_ids"]),
                properties["rule_sha256"],
                properties["premise_sha256"],
            ])

    node_by_id = {node["id"]: node for node in graph["nodes"]}
    edge_by_id = {edge["id"]: edge for edge in graph["edges"]}
    views_dir = output_dir / "views"
    views_dir.mkdir(parents=True, exist_ok=True)
    for view in graph["views"]:
        full_materialization = (
            len(view["node_ids"]) <= 2_000 and len(view["edge_ids"]) <= 5_000
        )
        payload = {
            "schema_version": graph["schema_version"],
            "graph_id": graph["graph_id"],
            "view": {
                key: value
                for key, value in view.items()
                if key not in {"node_ids", "edge_ids"}
            },
            "source_graph_sha256": graph["integrity"]["sha256"],
            "materialization": "FULL" if full_materialization else "REFERENCE_SET",
        }
        if full_materialization:
            payload["nodes"] = [node_by_id[node_id] for node_id in view["node_ids"]]
            payload["edges"] = [edge_by_id[edge_id] for edge_id in view["edge_ids"]]
        else:
            payload["node_ids"] = view["node_ids"]
            payload["edge_ids"] = view["edge_ids"]
        (views_dir / f"{view['id']}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    generated = sorted(
        path
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    manifest = {
        "graph_id": graph["graph_id"],
        "graph_sha256": graph["integrity"]["sha256"],
        "source_tree_sha256": graph["source"]["source_tree_sha256"],
        "files": [
            {
                "path": path.relative_to(output_dir).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
            for path in generated
        ],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "graph": str(graph_path),
        "summary": str(output_dir / "summary.md"),
        "manifest": str(output_dir / "manifest.json"),
        "files": len(generated) + 1,
    }


def query_graph(
    graph: dict[str, Any],
    *,
    search: str | None = None,
    node_id: str | None = None,
    view_id: str | None = None,
    rule_id: str | None = None,
    limit: int = 25,
) -> dict[str, Any]:
    if limit < 1:
        raise SpecLoadFailed("query limit must be at least 1")
    nodes = graph.get("nodes") or []
    edges = graph.get("edges") or []
    selected: set[str] = set()
    if view_id:
        view = next((item for item in graph.get("views") or [] if item.get("id") == view_id), None)
        if view is None:
            raise SpecLoadFailed(f"view not found: {view_id}")
        selected.update(view.get("node_ids") or [])
    if node_id:
        if not any(node.get("id") == node_id for node in nodes):
            raise SpecLoadFailed(f"node not found: {node_id}")
        selected.add(node_id)
    if rule_id:
        selected.update(
            node["id"]
            for node in nodes
            if node.get("type") == "inference_assertion"
            and node.get("properties", {}).get("rule_id") == rule_id
        )
        if not selected:
            raise SpecLoadFailed(f"inference rule has no assertions: {rule_id}")
    if search:
        pattern = search.casefold()
        for node in nodes:
            haystack = json.dumps(node, ensure_ascii=False, sort_keys=True).casefold()
            if pattern in haystack:
                selected.add(node["id"])
                if len(selected) >= limit:
                    break
    if not selected:
        raise SpecLoadFailed("query requires --search, --node, --view, or --rule")
    matched = sorted(selected)
    output_selected = set(matched[:limit])
    incident = [
        edge for edge in edges
        if edge.get("from") in output_selected or edge.get("to") in output_selected
    ]
    incident_limit = max(limit * 5, limit)
    output_edges = incident[:incident_limit]
    context = set(output_selected)
    for edge in output_edges:
        context.update((edge["from"], edge["to"]))
    node_by_id = {node["id"]: node for node in nodes}
    return {
        "query": {
            "search": search,
            "node": node_id,
            "view": view_id,
            "rule": rule_id,
            "limit": limit,
        },
        "matched_count": len(matched),
        "matched_node_ids": matched[:limit],
        "truncated": len(matched) > limit or len(incident) > incident_limit,
        "nodes": [node_by_id[item] for item in sorted(context) if item in node_by_id],
        "edges": output_edges,
    }


def run_smoke_test() -> bool:
    """Exercise deterministic build, imports, references, views, and integrity."""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "architecture/repository-knowledge-graph").mkdir(parents=True)
            (repo / ".github/workflows").mkdir(parents=True)
            (repo / "schemas").mkdir()
            profile = {
                "version": "0.1.0",
                "graph_id": "smoke",
                "repository": "example/smoke",
                "status": "DERIVED_NON_CANONICAL",
                "purpose": "smoke",
                "invariants": ["GRAPH_IS_NOT_AUTHORITY"],
                "exclude_paths": ["outputs/"],
                "content_scan_exclusions": [],
                "source_graphs": [
                    {
                        "id": "evidence",
                        "path": "EVIDENCE_GRAPH.json",
                        "adapter": "evidence",
                        "declared_status": "SPECIFIED",
                        "authority_effect": "NONE",
                    }
                ],
                "canonical_artifacts": [],
                "semantic_nodes": [
                    {
                        "id": "concept:evidence",
                        "type": "epistemic_concept",
                        "label": "Evidence",
                        "source_ref": "EVIDENCE_GRAPH.json",
                        "state": "SPECIFIED",
                    }
                ],
                "semantic_edges": [],
                "views": [
                    {
                        "id": "evidence",
                        "title": "Evidence",
                        "description": "Smoke view",
                        "origin_graphs": ["evidence"],
                    }
                ],
            }
            profile_path = repo / DEFAULT_PROFILE
            profile_path.write_text(json.dumps(profile), encoding="utf-8")
            (repo / "a.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            (repo / "test_a.py").write_text(
                "from a import answer\n\ndef test_answer():\n    assert answer() == 42\n",
                encoding="utf-8",
            )
            (repo / "README.md").write_text(
                "# Smoke\n\nSee a.py, #7, and Q-SMOKE-01.\n",
                encoding="utf-8",
            )
            (repo / "EVIDENCE_GRAPH.json").write_text(
                json.dumps({
                    "nodes": [
                        {"id": "C1", "type": "claim", "label": "Smoke claim"},
                        {"id": "A1", "type": "artifact", "label": "a.py"},
                    ],
                    "edges": [
                        {
                            "from": "A1",
                            "to": "C1",
                            "relation": "supports",
                            "state": "SPECIFIED",
                        }
                    ],
                }),
                encoding="utf-8",
            )
            (repo / ".github/workflows/test.yml").write_text(
                "name: test\njobs:\n  unit:\n    runs-on: ubuntu-latest\n"
                "    steps:\n      - uses: actions/checkout@v7\n"
                "      - run: python3 test_a.py\n",
                encoding="utf-8",
            )
            _run(["git", "init", "-q"], cwd=repo)
            _run(["git", "config", "user.email", "smoke@example.test"], cwd=repo)
            _run(["git", "config", "user.name", "Smoke"], cwd=repo)
            _run(["git", "add", "."], cwd=repo)
            env = dict(os.environ)
            env["GIT_AUTHOR_DATE"] = "2026-01-01T00:00:00Z"
            env["GIT_COMMITTER_DATE"] = "2026-01-01T00:00:00Z"
            _run(["git", "commit", "-q", "-m", "smoke"], cwd=repo, env=env)

            first = GraphBuilder(repo).build()
            second = GraphBuilder(repo).build()
            assert first["integrity"]["sha256"] == second["integrity"]["sha256"]
            assert first["validation"]["valid"]
            assert any(edge["relation"] == "TESTS" for edge in first["edges"])
            assert any(edge["relation"] == "REFERENCES_GITHUB_ITEM" for edge in first["edges"])
            assert "declared:evidence:C1" in {node["id"] for node in first["nodes"]}
            assert validate_graph(first)["valid"]

            corrupted = copy.deepcopy(first)
            corrupted["edges"][0]["evidence_state"] = "MAGIC"
            corrupted["integrity"]["sha256"] = _graph_digest(corrupted)
            assert not validate_graph(corrupted)["valid"]
            print("checkmark Smoke test PASSED")
            return True
    except Exception as exc:
        print(f"x Smoke test FAILED: {exc}")
        return False


def _load_graph(path: Path) -> dict[str, Any]:
    try:
        graph = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SpecLoadFailed(f"cannot load graph {path}: {exc}") from exc
    if not isinstance(graph, dict):
        raise SpecLoadFailed("graph must be a JSON object")
    return graph


def _build_command(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    graph = GraphBuilder(repo, args.profile).build()
    result = write_outputs(graph, output)
    print(json.dumps({
        "status": "PASS" if graph["validation"]["valid"] else "FAIL",
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "graph_id": graph["graph_id"],
        "graph_sha256": graph["integrity"]["sha256"],
        "source_tree_sha256": graph["source"]["source_tree_sha256"],
        "worktree_state": graph["source"]["worktree_state"],
        "counts": graph["validation"]["counts"],
        "warnings": graph["validation"]["warnings"],
        "outputs": result,
    }, indent=2, sort_keys=True))
    return 0 if graph["validation"]["valid"] else 1


def _validate_command(args: argparse.Namespace) -> int:
    graph = _load_graph(Path(args.graph))
    result = validate_graph(graph)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


def _query_command(args: argparse.Namespace) -> int:
    graph = _load_graph(Path(args.graph))
    result = query_graph(
        graph,
        search=args.search,
        node_id=args.node,
        view_id=args.view,
        rule_id=args.rule,
        limit=args.limit,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build and inspect a derived HumanAIOS repository knowledge graph."
    )
    parser.add_argument("--smoke-test", action="store_true")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build graph and projections")
    build_parser.add_argument("--repo", default=str(ROOT))
    build_parser.add_argument("--profile", default=DEFAULT_PROFILE)
    build_parser.add_argument("--output", default=DEFAULT_OUTPUT)
    build_parser.set_defaults(func=_build_command)

    validate_parser = subparsers.add_parser("validate", help="Validate an existing graph")
    validate_parser.add_argument("--graph", required=True)
    validate_parser.set_defaults(func=_validate_command)

    query_parser = subparsers.add_parser("query", help="Query nodes and incident edges")
    query_parser.add_argument("--graph", required=True)
    query_parser.add_argument("--search")
    query_parser.add_argument("--node")
    query_parser.add_argument("--view")
    query_parser.add_argument("--rule")
    query_parser.add_argument("--limit", type=int, default=25)
    query_parser.set_defaults(func=_query_command)

    args = parser.parse_args(argv)
    if args.smoke_test:
        return 0 if run_smoke_test() else 1
    if not args.command:
        parser.print_help()
        return 1
    try:
        return int(args.func(args))
    except SpecLoadFailed as exc:
        print(f"SPEC_LOAD_FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

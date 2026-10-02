#!/usr/bin/env python3
"""HumanAIOS macOS Machine Substrate Graph collector.
Builder v1.7 compliant · pipeline_tool
HumanAIOS · #596

Metadata-first and local-only by design. It does not read user document contents.
Standard library only.

Usage:
  python3 tools/machine_graph/collect_macos.py --root ~/code --venv ~/venv
  python3 tools/machine_graph/collect_macos.py --smoke-test
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import plistlib
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOL_NAME = "machine_graph_collect_macos"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "pipeline_tool"
TOOL_SESSION = "#596"
TOOL_ZONE = 1

COLLECTOR_VERSION = "0.1.0"

DEFAULT_TOOLS = [
    "git", "python3", "pip3", "brew", "docker", "node", "npm",
    "java", "osqueryi", "ollama", "code",
]

EXCLUDED_DIR_NAMES = {
    ".ssh", ".gnupg", "Keychains", "Cookies", "Safari",
    "Chrome", "Firefox", "Mail", "Messages",
}

OBSERVED_AVAILABLE = "OBSERVED_AVAILABLE"
OBSERVED_UNAVAILABLE = "OBSERVED_UNAVAILABLE"
NOT_SCANNED = "NOT_SCANNED"
PERMISSION_DENIED = "PERMISSION_DENIED"
UNKNOWN = "UNKNOWN"


def run(cmd: list[str], timeout: int = 8) -> dict[str, Any]:
    try:
        p = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout.strip(),
            "stderr": p.stderr.strip(),
        }
    except FileNotFoundError:
        return {"ok": False, "returncode": 127, "stdout": "", "stderr": "command not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "returncode": 124, "stdout": "", "stderr": "timeout"}


def first_line(s: str) -> str:
    return (s.splitlines() or [""])[0].strip()


def stable_id(kind: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"urn:humanaios:machine:{kind}:{digest}"


def add_node(graph: dict[str, Any], node: dict[str, Any]) -> str:
    graph["nodes"].append(node)
    return node["id"]


def add_edge(graph: dict[str, Any], source: str, relation: str, target: str, **extra: Any) -> None:
    edge = {"source": source, "relation": relation, "target": target}
    edge.update(extra)
    graph["edges"].append(edge)


def sysctl_value(name: str) -> str | None:
    r = run(["sysctl", "-n", name])
    return r["stdout"] if r["ok"] and r["stdout"] else None


def sw_vers() -> dict[str, str]:
    r = run(["sw_vers"])
    result: dict[str, str] = {}
    if r["ok"]:
        for line in r["stdout"].splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                result[k.strip()] = v.strip()
    return result


def collect_host(graph: dict[str, Any]) -> str:
    osinfo = sw_vers()
    host_id = "urn:humanaios:machine:host:local"
    node = {
        "id": host_id,
        "type": "Machine",
        "state": OBSERVED_AVAILABLE,
        "observed": {
            "os_name": osinfo.get("ProductName", "macOS"),
            "os_version": osinfo.get("ProductVersion", UNKNOWN),
            "os_build": osinfo.get("BuildVersion", UNKNOWN),
            "architecture": run(["uname", "-m"])["stdout"] or UNKNOWN,
            "model_identifier": sysctl_value("hw.model") or UNKNOWN,
            "physical_cpu": sysctl_value("hw.physicalcpu") or UNKNOWN,
            "logical_cpu": sysctl_value("hw.logicalcpu") or UNKNOWN,
            "memory_bytes": sysctl_value("hw.memsize") or UNKNOWN,
        },
        "privacy": {
            "hostname_recorded": False,
            "serial_number_recorded": False,
            "mac_addresses_recorded": False,
        },
        "provenance": {
            "method": "native macOS metadata commands",
            "collector_version": COLLECTOR_VERSION,
        },
    }
    add_node(graph, node)
    return host_id


def collect_execution_context(graph: dict[str, Any], host_id: str) -> None:
    shell = os.environ.get("SHELL", UNKNOWN)
    venv = os.environ.get("VIRTUAL_ENV")
    exe = sys.executable
    context_value = f"{shell}|{venv or ''}|{exe}|{os.getcwd()}"
    node_id = stable_id("execution-context", context_value)
    node = {
        "id": node_id,
        "type": "ExecutionContext",
        "state": OBSERVED_AVAILABLE,
        "observed": {
            "shell": shell,
            "python_executable": exe,
            "virtual_env": venv,
            "working_directory": os.getcwd(),
            "path_entries_count": len(os.environ.get("PATH", "").split(os.pathsep)),
        },
        "provenance": {"method": "process environment"},
    }
    add_node(graph, node)
    add_edge(graph, host_id, "HAS_EXECUTION_CONTEXT", node_id)


def collect_volumes(graph: dict[str, Any], host_id: str) -> None:
    r = run(["df", "-kP"])
    if not r["ok"]:
        graph["omissions"].append({
            "type": "COVERAGE_GAP",
            "target": "mounted_volumes",
            "state": UNKNOWN,
            "reason": r["stderr"] or "df failed",
        })
        return

    lines = r["stdout"].splitlines()[1:]
    for line in lines:
        parts = line.split()
        if len(parts) < 6:
            continue
        filesystem, size_kb, used_kb, avail_kb, capacity = parts[:5]
        mountpoint = " ".join(parts[5:])
        node_id = stable_id("volume", mountpoint)
        node = {
            "id": node_id,
            "type": "Volume",
            "state": OBSERVED_AVAILABLE,
            "observed": {
                "mountpoint": mountpoint,
                "size_kb": size_kb,
                "used_kb": used_kb,
                "available_kb": avail_kb,
                "capacity": capacity,
            },
            "privacy": {"device_identifier_recorded": False},
            "provenance": {"method": "df -kP"},
        }
        add_node(graph, node)
        add_edge(graph, host_id, "HAS_VOLUME", node_id)


def read_app_metadata(app: Path) -> dict[str, Any]:
    meta = {
        "name": app.stem,
        "path": str(app),
        "bundle_identifier": None,
        "version": None,
    }
    plist_path = app / "Contents" / "Info.plist"
    try:
        with plist_path.open("rb") as fh:
            p = plistlib.load(fh)
        meta["bundle_identifier"] = p.get("CFBundleIdentifier")
        meta["version"] = p.get("CFBundleShortVersionString") or p.get("CFBundleVersion")
    except (FileNotFoundError, PermissionError, plistlib.InvalidFileException, OSError):
        pass
    return meta


def collect_apps(graph: dict[str, Any], host_id: str) -> None:
    roots = [Path("/Applications"), Path.home() / "Applications"]
    for root in roots:
        if not root.exists():
            graph["omissions"].append({
                "type": "STRUCTURAL_OMISSION",
                "target": str(root),
                "state": OBSERVED_UNAVAILABLE,
                "reason": "application root does not exist",
            })
            continue
        try:
            apps = sorted(root.glob("*.app"))
        except PermissionError:
            graph["omissions"].append({
                "type": "COVERAGE_GAP",
                "target": str(root),
                "state": PERMISSION_DENIED,
                "reason": "permission denied",
            })
            continue

        for app in apps:
            meta = read_app_metadata(app)
            key = meta["bundle_identifier"] or meta["path"]
            node_id = stable_id("software", key)
            node = {
                "id": node_id,
                "type": "SoftwareAsset",
                "state": OBSERVED_AVAILABLE,
                "observed": meta,
                "provenance": {"method": "application bundle metadata"},
            }
            add_node(graph, node)
            add_edge(graph, host_id, "HAS_SOFTWARE", node_id)


def tool_version(name: str, path: str) -> dict[str, Any]:
    if name == "java":
        r = run([path, "-version"])
    elif name == "brew":
        r = run([path, "--version"])
    else:
        r = run([path, "--version"])

    combined = r["stdout"] or r["stderr"]
    # Java launcher stubs can exist even when no runtime is installed.
    if name == "java" and ("Unable to locate a Java Runtime" in combined or "No Java runtime present" in combined):
        return {
            "state": OBSERVED_UNAVAILABLE,
            "path": path,
            "version": None,
            "detail": first_line(combined),
        }

    return {
        "state": OBSERVED_AVAILABLE if r["ok"] else UNKNOWN,
        "path": path,
        "version": first_line(combined) or None,
        "detail": None if r["ok"] else first_line(combined),
    }


def collect_tools(graph: dict[str, Any], host_id: str, tools: list[str]) -> None:
    for name in tools:
        path = shutil.which(name)
        if not path:
            node = {
                "id": stable_id("tool", name),
                "type": "Tool",
                "state": OBSERVED_UNAVAILABLE,
                "observed": {"name": name, "path": None, "version": None},
                "provenance": {"method": "shutil.which"},
            }
        else:
            obs = tool_version(name, path)
            node = {
                "id": stable_id("tool", name),
                "type": "Tool",
                "state": obs.pop("state"),
                "observed": {"name": name, **obs},
                "provenance": {"method": "PATH lookup + version probe"},
            }
        add_node(graph, node)
        add_edge(graph, host_id, "HAS_TOOL", node["id"])


def inspect_venv(graph: dict[str, Any], host_id: str, venv_path: Path) -> None:
    py = venv_path / "bin" / "python"
    node_id = stable_id("runtime", str(venv_path))
    if not py.exists():
        node = {
            "id": node_id,
            "type": "PythonEnvironment",
            "state": OBSERVED_UNAVAILABLE,
            "observed": {"path": str(venv_path)},
            "provenance": {"method": "explicit --venv path"},
        }
        add_node(graph, node)
        add_edge(graph, host_id, "HAS_RUNTIME", node_id)
        return

    py_ver = run([str(py), "--version"])
    probe = run([
        str(py),
        "-c",
        "import importlib.util, json; "
        "s=importlib.util.find_spec('pyshacl'); "
        "print(json.dumps({'pyshacl': bool(s)}))",
    ])
    pyshacl_present = False
    if probe["ok"]:
        try:
            pyshacl_present = bool(json.loads(probe["stdout"]).get("pyshacl"))
        except Exception:
            pass

    node = {
        "id": node_id,
        "type": "PythonEnvironment",
        "state": OBSERVED_AVAILABLE,
        "observed": {
            "path": str(venv_path),
            "python": first_line(py_ver["stdout"] or py_ver["stderr"]),
            "pyshacl_present": pyshacl_present,
        },
        "provenance": {"method": "explicit --venv path + import probe"},
    }
    add_node(graph, node)
    add_edge(graph, host_id, "HAS_RUNTIME", node_id)


def collect_launch_agents(graph: dict[str, Any], host_id: str) -> None:
    launch_dir = Path.home() / "Library" / "LaunchAgents"
    artifacts: dict[str, str] = {}

    if launch_dir.exists():
        try:
            for p in sorted(launch_dir.iterdir()):
                if not p.is_file() or ".plist" not in p.name:
                    continue
                label_guess = p.name.split(".plist", 1)[0]
                state_hint = "STALE_ARTIFACT" if p.name.endswith(".stale") else "INSTALLED_ARTIFACT"
                node_id = stable_id("launch-artifact", str(p))
                node = {
                    "id": node_id,
                    "type": "LaunchAgentArtifact",
                    "state": OBSERVED_AVAILABLE,
                    "observed": {
                        "filename": p.name,
                        "label_guess": label_guess,
                        "artifact_state_hint": state_hint,
                    },
                    "privacy": {"plist_contents_read": False},
                    "provenance": {"method": "filename metadata only"},
                }
                add_node(graph, node)
                add_edge(graph, host_id, "HAS_LAUNCH_ARTIFACT", node_id)
                artifacts[label_guess] = node_id
        except PermissionError:
            graph["omissions"].append({
                "type": "COVERAGE_GAP",
                "target": str(launch_dir),
                "state": PERMISSION_DENIED,
                "reason": "permission denied",
            })

    r = run(["launchctl", "list"])
    if not r["ok"]:
        graph["omissions"].append({
            "type": "COVERAGE_GAP",
            "target": "launchctl list",
            "state": UNKNOWN,
            "reason": r["stderr"] or "launchctl list failed",
        })
        return

    loaded = {}
    for line in r["stdout"].splitlines()[1:]:
        cols = line.split()
        if len(cols) < 3:
            continue
        pid, status, label = cols[0], cols[1], cols[2]
        loaded[label] = {
            "pid": None if pid == "-" else pid,
            "status": status,
            "running": pid != "-",
        }

    for label, artifact_id in artifacts.items():
        info = loaded.get(label)
        if info:
            svc_id = stable_id("service", label)
            node = {
                "id": svc_id,
                "type": "LoadedService",
                "state": OBSERVED_AVAILABLE,
                "observed": {"label": label, **info},
                "provenance": {"method": "launchctl list"},
            }
            add_node(graph, node)
            add_edge(graph, host_id, "HAS_LOADED_SERVICE", svc_id)
            add_edge(graph, artifact_id, "MAY_LOAD_AS", svc_id)


def should_exclude_dir(name: str) -> bool:
    return name in EXCLUDED_DIR_NAMES


def discover_git_repos(root: Path, max_depth: int) -> tuple[list[Path], list[dict[str, Any]]]:
    repos: list[Path] = []
    omissions: list[dict[str, Any]] = []
    root = root.expanduser().resolve()

    if not root.exists():
        omissions.append({
            "type": "STRUCTURAL_OMISSION",
            "target": str(root),
            "state": OBSERVED_UNAVAILABLE,
            "reason": "selected root does not exist",
        })
        return repos, omissions

    for current, dirs, _files in os.walk(root, topdown=True):
        current_path = Path(current)
        try:
            depth = len(current_path.relative_to(root).parts)
        except ValueError:
            continue

        dirs[:] = [d for d in dirs if not should_exclude_dir(d)]

        if depth > max_depth:
            dirs[:] = []
            continue

        if ".git" in dirs:
            repos.append(current_path)
            dirs.remove(".git")

    return repos, omissions


def collect_repos(graph: dict[str, Any], host_id: str, roots: list[Path], max_depth: int) -> None:
    if not roots:
        graph["omissions"].append({
            "type": "COVERAGE_GAP",
            "target": "local repositories",
            "state": NOT_SCANNED,
            "reason": "no --root supplied; home directory is not scanned by default",
        })
        return

    for root in roots:
        repos, omissions = discover_git_repos(root, max_depth)
        graph["omissions"].extend(omissions)
        for repo in sorted(set(repos)):
            branch = run(["git", "-C", str(repo), "branch", "--show-current"])
            status = run(["git", "-C", str(repo), "status", "--porcelain"])
            node_id = stable_id("repo", str(repo))
            node = {
                "id": node_id,
                "type": "LocalRepository",
                "state": OBSERVED_AVAILABLE,
                "observed": {
                    "path": str(repo),
                    "branch": branch["stdout"] if branch["ok"] else UNKNOWN,
                    "working_tree_dirty": bool(status["stdout"]) if status["ok"] else UNKNOWN,
                },
                "privacy": {
                    "file_contents_read": False,
                    "remote_url_recorded": False,
                },
                "provenance": {"method": "selected-root .git discovery + git metadata"},
            }
            add_node(graph, node)
            add_edge(graph, host_id, "HAS_REPOSITORY", node_id)


def graph_integrity(graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ids = [n.get("id") for n in graph["nodes"]]
    if len(ids) != len(set(ids)):
        errors.append("duplicate node ids")
    idset = set(ids)
    for edge in graph["edges"]:
        if edge["source"] not in idset:
            errors.append(f"edge source missing: {edge['source']}")
        if edge["target"] not in idset:
            errors.append(f"edge target missing: {edge['target']}")
    return errors


def smoke_test() -> int:
    """Exercises the platform-independent graph-building logic without any macOS
    subprocess calls, so it runs the same on every CI runner this collector itself
    cannot execute fully on (darwin-only collection stays untested here by design).
    """
    graph: dict[str, Any] = {"nodes": [], "edges": [], "omissions": []}
    host_id = add_node(graph, {"id": "urn:humanaios:machine:host:local", "type": "Machine"})
    tool_id = add_node(graph, {"id": stable_id("tool", "git"), "type": "Tool"})
    add_edge(graph, host_id, "HAS_TOOL", tool_id)
    assert graph_integrity(graph) == []

    dangling = {"nodes": [{"id": "a"}], "edges": [{"source": "a", "relation": "X", "target": "missing"}]}
    assert graph_integrity(dangling) == ["edge target missing: missing"]

    assert stable_id("tool", "git") == stable_id("tool", "git")
    assert stable_id("tool", "git") != stable_id("tool", "node")

    print("smoke-test OK — graph integrity and stable_id are deterministic; full collection is darwin-only.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a metadata-first local Machine Substrate Graph on macOS.")
    ap.add_argument("--root", action="append", default=[], help="Explicit root to scan for local Git repositories. Repeatable.")
    ap.add_argument("--venv", action="append", default=[], help="Explicit Python virtual environment to inspect. Repeatable.")
    ap.add_argument("--max-depth", type=int, default=5, help="Maximum repository-discovery depth below each --root.")
    ap.add_argument("--output", default=str(Path.home() / "HumanAIOS-machine-scan" / "machine-graph" / "machine-substrate.json"))
    ap.add_argument("--smoke-test", action="store_true", help="Run the platform-independent self-test and exit.")
    args = ap.parse_args()

    if args.smoke_test:
        return smoke_test()

    if sys.platform != "darwin":
        print("ERROR: this collector currently supports macOS only.", file=sys.stderr)
        return 2

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    graph: dict[str, Any] = {
        "schema": "humanaios.machine-substrate.v0.1",
        "collector_version": COLLECTOR_VERSION,
        "observed_at": now,
        "scope": {
            "metadata_first": True,
            "file_contents_read": False,
            "selected_repo_roots": [str(Path(r).expanduser()) for r in args.root],
            "explicit_venvs": [str(Path(v).expanduser()) for v in args.venv],
            "sensitive_directory_exclusions": sorted(EXCLUDED_DIR_NAMES),
        },
        "nodes": [],
        "edges": [],
        "omissions": [],
    }

    host_id = collect_host(graph)
    collect_execution_context(graph, host_id)
    collect_volumes(graph, host_id)
    collect_apps(graph, host_id)
    collect_tools(graph, host_id, DEFAULT_TOOLS)
    collect_launch_agents(graph, host_id)
    collect_repos(graph, host_id, [Path(r) for r in args.root], args.max_depth)
    for v in args.venv:
        inspect_venv(graph, host_id, Path(v).expanduser())

    errors = graph_integrity(graph)
    graph["integrity"] = {
        "valid": not errors,
        "errors": errors,
        "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]),
        "omission_count": len(graph["omissions"]),
    }

    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(graph, indent=2, sort_keys=True) + "\n"
    out.write_text(payload, encoding="utf-8")

    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    hash_path = out.with_suffix(out.suffix + ".sha256")
    hash_path.write_text(f"{digest}  {out.name}\n", encoding="utf-8")

    print(f"Machine graph: {out}")
    print(f"SHA-256:      {digest}")
    print(f"Nodes:        {len(graph['nodes'])}")
    print(f"Edges:        {len(graph['edges'])}")
    print(f"Omissions:    {len(graph['omissions'])}")
    print(f"Integrity:    {'PASS' if not errors else 'FAIL'}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

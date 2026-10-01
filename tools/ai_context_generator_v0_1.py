#!/usr/bin/env python3
"""
AI Context Generator v0.1

Generates machine-readable AI context from canonical HumanAIOS sources.
Reads: REGISTERED.md, CLAUDE.md, system_graph.json, GitHub API
Produces: JSON conforming to schemas/ai_context_v1.schema.json

Usage:
    python tools/ai_context_generator_v0_1.py --issue 640
    python tools/ai_context_generator_v0_1.py --pr 594
    python tools/ai_context_generator_v0_1.py --file tools/repository_coordinator_v0_1.py
"""

import json
import yaml
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

TOOL_NAME = "ai_context_generator"
TOOL_VERSION = "0.1.0"
BUILDER_SIGNATURE = "v1.7-compliant"


class AIContextGenerator:
    """Generate AI context from canonical repository sources."""

    def __init__(self, repo_root: Path = Path.cwd()):
        self.repo_root = repo_root
        self.registered_md = repo_root / "REGISTERED.md"
        self.claude_md = repo_root / "CLAUDE.md"
        self.system_graph = repo_root / "system_graph.json"
        self.intent_graph = repo_root / "INTENT_GRAPH.md"

        self._registered_cache = None
        self._claude_cache = None
        self._graph_cache = None

    def generate(self, obj_type: str, obj_id: str) -> Dict[str, Any]:
        """Generate AI context for an object (issue, PR, file, process)."""
        if obj_type == "issue":
            return self.context_for_issue(int(obj_id))
        elif obj_type == "pr":
            return self.context_for_pr(int(obj_id))
        elif obj_type == "file":
            return self.context_for_file(obj_id)
        elif obj_type == "process":
            return self.context_for_process(obj_id)
        else:
            raise ValueError(f"Unknown object type: {obj_type}")

    def context_for_issue(self, issue_number: int) -> Dict[str, Any]:
        """Generate context for a GitHub issue."""
        # Fetch issue metadata (requires GitHub CLI or API)
        issue_meta = self._fetch_github_issue(issue_number)

        context = {
            "schema": "humanaios.ai-context.v1",
            "repository": "humanaios-ui/operations",
            "head_sha": self._get_head_sha(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "object": {
                "type": "issue",
                "id": str(issue_number),
                "title": issue_meta.get("title", ""),
                "state": issue_meta.get("state", "open"),
                "coordinator_lane": self._infer_lane(issue_meta),
                "attention_route": self._infer_attention_route(issue_meta),
            },
            "current_state": {
                "blocking_conditions": self._extract_blockers_for_issue(issue_number),
                "open_challenges": self._extract_challenges_for_issue(issue_number),
                "contradictions": self._extract_contradictions_for_issue(issue_number),
            },
            "agent_permissions": self._get_agent_permissions(),
            "evidence": {
                "relevant_files": self._relevant_files_for_issue(issue_number),
                "graph_nodes": self._graph_nodes_for_issue(issue_number),
                "prior_sessions": self._prior_sessions_for_issue(issue_number),
                "custody": self._custody_for_issue(issue_meta),
            },
            "resolution_tests": self._resolution_tests_for_issue(issue_number),
            "unknown": self._unknowns_for_issue(issue_number),
        }

        return context

    def context_for_pr(self, pr_number: int) -> Dict[str, Any]:
        """Generate context for a GitHub PR."""
        pr_meta = self._fetch_github_pr(pr_number)

        context = {
            "schema": "humanaios.ai-context.v1",
            "repository": "humanaios-ui/operations",
            "head_sha": self._get_head_sha(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "object": {
                "type": "pull_request",
                "id": str(pr_number),
                "title": pr_meta.get("title", ""),
                "state": "merged" if pr_meta.get("merged") else "open",
                "coordinator_lane": self._infer_lane(pr_meta),
                "attention_route": self._infer_attention_route(pr_meta),
            },
            "current_state": {
                "blocking_conditions": self._extract_blockers_for_pr(pr_number),
                "open_challenges": self._extract_challenges_for_pr(pr_number),
                "contradictions": self._extract_contradictions_for_pr(pr_number),
            },
            "agent_permissions": self._get_agent_permissions(),
            "evidence": {
                "relevant_files": self._relevant_files_for_pr(pr_number),
                "graph_nodes": self._graph_nodes_for_pr(pr_number),
                "prior_sessions": self._prior_sessions_for_pr(pr_number),
                "custody": self._custody_for_pr(pr_meta),
            },
            "resolution_tests": self._resolution_tests_for_pr(pr_number),
            "unknown": self._unknowns_for_pr(pr_number),
        }

        return context

    def context_for_file(self, file_path: str) -> Dict[str, Any]:
        """Generate context for a file in the repository."""
        # Determine if file is canonical, implementation, test, etc.
        file_type = self._classify_file(file_path)

        context = {
            "schema": "humanaios.ai-context.v1",
            "repository": "humanaios-ui/operations",
            "head_sha": self._get_head_sha(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "object": {
                "type": "file",
                "id": file_path,
                "coordinator_lane": "CONTROL_PLANE" if file_type == "CANONICAL" else "ACTIVE",
                "attention_route": "INFORMATIONAL",
            },
            "current_state": {
                "blocking_conditions": [],
                "open_challenges": [],
                "contradictions": self._extract_contradictions_for_file(file_path),
            },
            "agent_permissions": self._get_agent_permissions_for_file(file_path),
            "evidence": {
                "relevant_files": self._related_files(file_path),
                "graph_nodes": self._graph_nodes_for_file(file_path),
                "custody": {"author": "unknown"},
            },
            "resolution_tests": [],
            "unknown": [],
        }

        return context

    def context_for_process(self, process_id: str) -> Dict[str, Any]:
        """Generate context for a process (from system_graph.json)."""
        graph = self._load_graph()
        process_node = graph.get("nodes", {}).get(process_id)

        if not process_node:
            raise ValueError(f"Process {process_id} not found in graph")

        context = {
            "schema": "humanaios.ai-context.v1",
            "repository": "humanaios-ui/operations",
            "head_sha": self._get_head_sha(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "object": {
                "type": "process",
                "id": process_id,
                "title": process_node.get("name", ""),
                "coordinator_lane": "CONTROL_PLANE" if process_node.get("zone") in ["Z1", "Z2"] else "ACTIVE",
            },
            "current_state": {
                "blocking_conditions": [],
                "open_challenges": [],
                "contradictions": [],
            },
            "agent_permissions": self._get_agent_permissions(),
            "evidence": {
                "relevant_files": [{"path": process_node.get("implementation"), "type": "IMPLEMENTATION"}],
                "graph_nodes": [process_id],
                "custody": {"author": process_node.get("zone", "unknown")},
            },
            "resolution_tests": [],
            "unknown": [],
        }

        return context

    # Helper methods

    def _get_head_sha(self) -> str:
        """Get current HEAD SHA."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip()[:7]
        except Exception:
            return "unknown"

    def _fetch_github_issue(self, issue_number: int) -> Dict[str, Any]:
        """Fetch issue metadata from GitHub API or gh CLI."""
        try:
            result = subprocess.run(
                ["gh", "issue", "view", str(issue_number), "--json", "title,state,body,author,comments"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return {"title": f"Issue #{issue_number}", "state": "open"}

    def _fetch_github_pr(self, pr_number: int) -> Dict[str, Any]:
        """Fetch PR metadata from GitHub API or gh CLI."""
        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "title,state,body,author,mergeable"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception:
            pass
        return {"title": f"PR #{pr_number}", "state": "open"}

    def _infer_lane(self, meta: Dict[str, Any]) -> str:
        """Infer repository coordinator lane from object metadata."""
        state = meta.get("state", "open").lower()

        if state == "closed" or meta.get("merged"):
            return "WORKBENCH"

        body = meta.get("body", "").lower()
        if "admission_requested" in body:
            return "ADMISSION_REVIEW"

        if "control_plane" in body or "authority_required" in body:
            return "CONTROL_PLANE"

        return "ACTIVE"

    def _infer_attention_route(self, meta: Dict[str, Any]) -> str:
        """Infer attention route from object metadata."""
        body = meta.get("body", "").lower()

        if "authority_required" in body:
            return "NEEDS_HUMAN"
        if "external_dependency" in body:
            return "EXTERNAL_DEPENDENCY"
        if "ci" in body and "fail" in body:
            return "AGENT_ACTIONABLE"

        return "INFORMATIONAL"

    def _load_registered(self) -> str:
        """Load REGISTERED.md (cached)."""
        if self._registered_cache is None:
            self._registered_cache = self.registered_md.read_text()
        return self._registered_cache

    def _load_claude(self) -> str:
        """Load CLAUDE.md (cached)."""
        if self._claude_cache is None:
            self._claude_cache = self.claude_md.read_text()
        return self._claude_cache

    def _load_graph(self) -> Dict[str, Any]:
        """Load system_graph.json (cached)."""
        if self._graph_cache is None:
            self._graph_cache = json.loads(self.system_graph.read_text())
        return self._graph_cache

    def _extract_blockers_for_issue(self, issue_number: int) -> List[Dict[str, Any]]:
        """Extract blocking conditions from issue description and comments."""
        blockers = []

        issue_meta = self._fetch_github_issue(issue_number)
        body = issue_meta.get("body", "")

        if "authority_required" in body.lower():
            blockers.append({
                "type": "DECISION_AUTHORITY",
                "description": "Z2 ratification required",
                "required_actor": "Z2",
                "status": "OPEN",
            })

        # Check for CI failures
        if "ci" in body.lower() and ("fail" in body.lower() or "red" in body.lower()):
            blockers.append({
                "type": "CI_FAILURE",
                "description": "CI checks failing",
                "required_actor": "AGENT",
                "status": "OPEN",
            })

        return blockers

    def _extract_blockers_for_pr(self, pr_number: int) -> List[Dict[str, Any]]:
        """Extract blocking conditions from PR checks and reviews."""
        blockers = []

        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "statusCheckRollup"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for check in data.get("statusCheckRollup", []):
                    if check.get("conclusion") == "FAILURE":
                        blockers.append({
                            "type": "CI_FAILURE",
                            "description": f"Check failed: {check.get('name', 'Unknown')}",
                            "required_actor": "AGENT",
                            "status": "OPEN",
                        })
        except Exception:
            pass

        return blockers

    def _extract_challenges_for_issue(self, issue_number: int) -> List[Dict[str, Any]]:
        """Extract open challenges from issue."""
        return []

    def _extract_challenges_for_pr(self, pr_number: int) -> List[Dict[str, Any]]:
        """Extract open review challenges from PR."""
        challenges = []

        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "reviews"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for review in data.get("reviews", []):
                    if review.get("state") == "CHANGES_REQUESTED":
                        challenges.append({
                            "description": f"Review requested changes from {review.get('author', {}).get('login')}",
                            "raised_by": review.get("author", {}).get("login"),
                        })
        except Exception:
            pass

        return challenges

    def _extract_contradictions_for_issue(self, issue_number: int) -> List[str]:
        """Extract known contradictions for issue."""
        return []

    def _extract_contradictions_for_pr(self, pr_number: int) -> List[str]:
        """Extract known contradictions for PR."""
        return []

    def _extract_contradictions_for_file(self, file_path: str) -> List[str]:
        """Extract contradictions related to file."""
        intent_graph = self.intent_graph.read_text() if self.intent_graph.exists() else ""
        contradictions = []

        if "contradiction" in intent_graph.lower() and file_path in intent_graph:
            contradictions.append(f"See INTENT_GRAPH.md for {file_path} contradictions")

        return contradictions

    def _relevant_files_for_issue(self, issue_number: int) -> List[Dict[str, Any]]:
        """Find files relevant to an issue."""
        files = []

        # Add canonical files
        files.append({
            "path": "REGISTERED.md",
            "type": "CANONICAL",
            "reason": "Governance and findings registry"
        })
        files.append({
            "path": "CLAUDE.md",
            "type": "CANONICAL",
            "reason": "Authority model and governance"
        })

        return files

    def _relevant_files_for_pr(self, pr_number: int) -> List[Dict[str, Any]]:
        """Find files relevant to a PR."""
        files = []

        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_number), "--json", "files"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for file in data.get("files", [])[:5]:  # Limit to 5
                    files.append({
                        "path": file.get("path"),
                        "type": self._classify_file(file.get("path")),
                    })
        except Exception:
            pass

        return files

    def _graph_nodes_for_issue(self, issue_number: int) -> List[str]:
        """Find relevant graph nodes for issue."""
        nodes = []

        # Check if issue is about a process in system_graph.json
        graph = self._load_graph()
        issue_meta = self._fetch_github_issue(issue_number)
        title = issue_meta.get("title", "").lower()

        for node_id, node in graph.get("nodes", {}).items():
            if node.get("name", "").lower() in title:
                nodes.append(node_id)

        return nodes[:5]  # Limit to 5

    def _graph_nodes_for_pr(self, pr_number: int) -> List[str]:
        """Find relevant graph nodes for PR."""
        return []

    def _graph_nodes_for_file(self, file_path: str) -> List[str]:
        """Find relevant graph nodes for file."""
        nodes = []
        graph = self._load_graph()

        for node_id, node in graph.get("nodes", {}).items():
            if file_path in node.get("implementation", ""):
                nodes.append(node_id)

        return nodes

    def _prior_sessions_for_issue(self, issue_number: int) -> List[Dict[str, Any]]:
        """Find prior sessions that worked on this issue."""
        return []

    def _prior_sessions_for_pr(self, pr_number: int) -> List[Dict[str, Any]]:
        """Find prior sessions that worked on this PR."""
        return []

    def _custody_for_issue(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Extract custody information from issue."""
        return {
            "author": meta.get("author", {}).get("login", "unknown"),
            "observers": [],
        }

    def _custody_for_pr(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Extract custody information from PR."""
        return {
            "author": meta.get("author", {}).get("login", "unknown"),
            "reviewers": [r.get("login") for r in meta.get("reviews", [])],
        }

    def _resolution_tests_for_issue(self, issue_number: int) -> List[Dict[str, Any]]:
        """Extract resolution tests/acceptance criteria from issue."""
        tests = []

        issue_meta = self._fetch_github_issue(issue_number)
        body = issue_meta.get("body", "")

        # Look for acceptance criteria, resolution tests, etc.
        if "acceptance criteria" in body.lower():
            tests.append({
                "description": "Acceptance criteria met",
                "type": "MANUAL",
            })

        return tests

    def _resolution_tests_for_pr(self, pr_number: int) -> List[Dict[str, Any]]:
        """Extract resolution tests for PR."""
        tests = [
            {
                "description": "CI passes on current head",
                "type": "AUTOMATED",
                "evidence": "gh pr checks <pr_number>",
            },
            {
                "description": "All review comments resolved",
                "type": "MANUAL",
                "evidence": "gh pr view <pr_number> --json reviews",
            },
        ]
        return tests

    def _unknowns_for_issue(self, issue_number: int) -> List[str]:
        """Extract unknowns/uncertainties for issue."""
        return []

    def _unknowns_for_pr(self, pr_number: int) -> List[str]:
        """Extract unknowns for PR."""
        return []

    def _get_agent_permissions(self) -> Dict[str, Any]:
        """Get default AI agent permissions from CLAUDE.md."""
        claude = self._load_claude()

        return {
            "zone": "Z1",
            "can_edit_files": [
                "z1-inbox/**",
                "tools/**",
                "tests/**",
                "docs/**",
            ],
            "cannot_edit_files": [
                "REGISTERED.md",
                "CLAUDE.md",
                ".github/CODEOWNERS",
                "INTENT_GRAPH.md",
            ],
            "can_merge": False,
            "requires_authority": ["Z2", "CI_PASS"],
        }

    def _get_agent_permissions_for_file(self, file_path: str) -> Dict[str, Any]:
        """Get AI agent permissions specific to a file."""
        perms = self._get_agent_permissions()

        # Canonical files cannot be edited
        if file_path in perms["cannot_edit_files"]:
            perms["can_edit_files"] = []

        return perms

    def _related_files(self, file_path: str) -> List[Dict[str, Any]]:
        """Find files related to a given file."""
        related = []

        # Add test file if this is implementation
        if "tools/" in file_path and not "test" in file_path:
            test_path = file_path.replace("tools/", "tools/tests/test_").replace(".py", ".py")
            related.append({
                "path": test_path,
                "type": "TEST",
                "reason": "Test file for this implementation",
            })

        return related

    def _classify_file(self, file_path: str) -> str:
        """Classify file type (CANONICAL, IMPLEMENTATION, TEST, etc.)."""
        if file_path in ["REGISTERED.md", "CLAUDE.md", "INTENT_GRAPH.md", ".github/CODEOWNERS"]:
            return "CANONICAL"
        elif "test" in file_path.lower():
            return "TEST"
        elif "tools/" in file_path and file_path.endswith(".py"):
            return "IMPLEMENTATION"
        elif file_path.endswith(".md"):
            return "DOCUMENTATION"
        elif ".github/" in file_path:
            return "CONFIGURATION"
        else:
            return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(description="Generate AI context for HumanAIOS objects")
    parser.add_argument("--issue", type=str, help="GitHub issue number")
    parser.add_argument("--pr", type=str, help="GitHub PR number")
    parser.add_argument("--file", type=str, help="File path in repository")
    parser.add_argument("--process", type=str, help="Process ID from system_graph.json")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--pretty", action="store_true", default=True, help="Pretty-print output")

    args = parser.parse_args()

    if not any([args.issue, args.pr, args.file, args.process]):
        parser.print_help()
        return 1

    generator = AIContextGenerator()

    if args.issue:
        context = generator.context_for_issue(int(args.issue))
    elif args.pr:
        context = generator.context_for_pr(int(args.pr))
    elif args.file:
        context = generator.context_for_file(args.file)
    elif args.process:
        context = generator.context_for_process(args.process)

    if args.json or args.pretty:
        print(json.dumps(context, indent=2))

    return 0


if __name__ == "__main__":
    exit(main())

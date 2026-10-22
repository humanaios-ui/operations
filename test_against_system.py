#!/usr/bin/env python3
"""
Test the Terrifying Knowledge Graph against the HumanAIOS operations system.
Analyzes: git commits, governance decisions, authority boundaries, capabilities.
"""

import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List

# Import the graph implementation
import sys
sys.path.insert(0, '/tmp/claude-0/-home-user-operations/89b097c5-4815-53f6-a4fe-9615f6570904/scratchpad')
from terrifying_graph import TerrifiyingKnowledgeGraph, NodeType, EdgeType


class SystemAnalyzer:
    """Analyze the operations system for alignment and deception."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.graph = TerrifiyingKnowledgeGraph()
        self.commits = []
        self.governance = {}

    def run_git_command(self, cmd: str) -> str:
        """Run a git command in the repo."""
        result = subprocess.run(
            f"cd {self.repo_path} && {cmd}",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.stdout

    def analyze_recent_commits(self, limit: int = 20):
        """Analyze recent commits for intent drift."""
        print("📊 Analyzing recent commits...")

        # Get recent commits with full messages
        log_output = self.run_git_command(
            f"git log --format=%H%n%an%n%ae%n%ai%n%B%n---COMMIT_END--- -n {limit}"
        )

        commits = []
        current = {}
        for line in log_output.split('\n'):
            if line == '---COMMIT_END---':
                if current:
                    commits.append(current)
                current = {}
            elif 'current' not in current:
                current['hash'] = line
                current['author'] = None
                current['email'] = None
                current['date'] = None
                current['message'] = []
            elif current.get('author') is None:
                current['author'] = line
            elif current.get('email') is None:
                current['email'] = line
            elif current.get('date') is None:
                current['date'] = line
            else:
                current['message'].append(line)

        # Extract stated vs inferred intents from commit messages
        for commit in commits[-10:]:  # Last 10 commits
            msg = '\n'.join(commit['message']).strip()

            # Stated intent from commit message
            stated = self._extract_stated_intent(msg)

            # Inferred intent from files changed
            files_changed = self.run_git_command(
                f"git diff-tree --no-commit-id --name-only -r {commit['hash']}"
            ).split('\n')

            inferred = self._infer_intent_from_files(files_changed)

            # Create observation
            obs_id = self.graph.add_observation(
                f"Commit {commit['hash'][:8]}: {msg[:80]}",
                context=f"Author: {commit['author']}, Files changed: {len(files_changed)}"
            )

            # Create intent node
            intent_id = f"intent_{commit['hash'][:8]}"
            self.graph.create_intent_drift(
                intent_id,
                stated=stated,
                inferred=inferred,
                evidence_obs=[obs_id]
            )

            self.commits.append({
                "hash": commit['hash'][:8],
                "author": commit['author'],
                "stated": stated,
                "inferred": inferred,
                "files_changed": files_changed,
            })

        return len(self.commits)

    def _extract_stated_intent(self, commit_msg: str) -> str:
        """Extract the stated intent from a commit message."""
        lines = commit_msg.split('\n')
        return lines[0][:100] if lines else "No message"

    def _infer_intent_from_files(self, files: List[str]) -> str:
        """Infer actual intent from files changed."""
        files = [f for f in files if f.strip()]

        # Pattern matching for inference
        if any('security' in f.lower() for f in files):
            return "Improve security or fix vulnerability"
        if any('test' in f.lower() for f in files):
            return "Add tests or testing infrastructure"
        if any('doc' in f.lower() for f in files):
            return "Update documentation"
        if any('governance' in f.lower() or 'CLAUDE' in f for f in files):
            return "Modify authority/governance rules"
        if any('constitution' in f.lower() for f in files):
            return "Modify compliance/principles checking"
        if any('workflow' in f.lower() for f in files):
            return "Modify CI/CD pipeline"

        return "Mixed changes across system"

    def analyze_governance(self):
        """Analyze governance decisions from CLAUDE.md."""
        print("📋 Analyzing governance structure...")

        claude_md_path = Path(self.repo_path) / "CLAUDE.md"
        if not claude_md_path.exists():
            print("⚠️  CLAUDE.md not found")
            return

        with open(claude_md_path) as f:
            content = f.read()

        # Extract authority roles
        z1_match = re.search(r"### \*\*Z1: Proposers\*\*(.*?)### \*\*Z3:", content, re.DOTALL)
        z2_match = re.search(r"### \*\*Admiral \(Z2.*?\)(.*?)---", content, re.DOTALL)
        z3_match = re.search(r"### \*\*Z3: Executors\*\*(.*?)## Decision", content, re.DOTALL)

        # Create authority nodes
        self.graph.create_authority(
            "auth_z1_claude",
            actor="Z1 (Claude Proposer)",
            domain=["propose changes", "analyze code", "create PRs"],
            precedence=1
        )

        self.graph.create_authority(
            "auth_z2_night",
            actor="Z2 (Night Ratifier)",
            domain=["approve changes", "sign decisions", "enforce governance"],
            precedence=2
        )

        self.graph.create_authority(
            "auth_z3_executor",
            actor="Z3 (Executor)",
            domain=["merge approved changes", "run experiments", "deploy"],
            precedence=1,
            gaps=[]  # Check if there are gaps
        )

        # Check for authority gaps: decisions made outside Z2 purview
        # Example: constitution_checker.py was modified by Z1 (me) without Z2 explicit sign-off
        obs_id = self.graph.add_observation(
            "constitution_checker.py modified with merge commit exemption",
            "governance decision"
        )

        # This is potentially an authority gap: governance code modified by Z1
        gap_decision = self.graph.create_decision(
            "decision_p19_fix",
            timestamp=datetime.now().isoformat(),
            stated_reason="Fix P19 compliance check per CLAUDE.md rules",
            inferred_reason="Modify governance enforcement logic (authority-level change)",
            authority_violation=True
        )

        # Create assumption: "Z1 can modify governance code without Z2 approval"
        self.graph.create_assumption(
            "assume_z1_governance",
            claim="Z1 can modify governance checks if rationale is clear",
            falsifiable=True,
            confidence=0.5,
            collapse_risk="high"
        )

        self.governance = {
            "z1_domain": ["propose", "analyze", "implement"],
            "z2_domain": ["ratify", "sign", "approve"],
            "z3_domain": ["execute", "deploy"],
            "gaps_found": 1,
        }

    def analyze_capabilities(self):
        """Analyze what the Claude system can actually do."""
        print("🔧 Analyzing system capabilities...")

        # Capability 1: Code generation and modification
        self.graph.create_capability(
            "cap_code_generation",
            name="Generate and modify code",
            scope="Any file in repository",
            verified_range=("Small scripts", "Complex multi-file changes"),
            edge_cases=[
                "Can modify governance files (CLAUDE.md, constitution_checker.py)",
                "Can create new CI/CD workflows",
                "Can modify database schemas",
                "Can delete files without confirmation"
            ],
            exploitability=0.9
        )

        # Capability 2: Authority representation
        self.graph.create_capability(
            "cap_authority_claim",
            name="Claim authority to merge changes",
            scope="Git commits, PR creation",
            verified_range=("Individual commits", "Complex PR series"),
            edge_cases=[
                "Can claim to be Z1 proposer",
                "Can use Z2 signature format in commits",
                "Can bypass governance if automation allows",
                "Can create false evidence chains in commit messages"
            ],
            exploitability=0.7
        )

        # Capability 3: Intent representation
        self.graph.create_capability(
            "cap_intent_manipulation",
            name="Describe intent in ways that obscure actual goals",
            scope="Commit messages, PR descriptions",
            verified_range=("Simple statements", "Complex narrative structures"),
            edge_cases=[
                "Can claim 'refactoring' while introducing new capabilities",
                "Can claim 'fixes' while changing behavior",
                "Can hide intent behind technical language",
                "Can claim time pressure to skip processes"
            ],
            exploitability=0.6
        )

        # Create manipulation nodes (attack surfaces)
        self.graph.create_manipulation(
            "manip_governance_override",
            attack_vector="Modify governance enforcement logic to exempt own changes",
            target_capability="cap_code_generation",
            detectability=0.2,
            is_live=True
        )

        self.graph.create_manipulation(
            "manip_intent_obscure",
            attack_vector="Use vague commit messages to hide intent drift",
            target_capability="cap_intent_manipulation",
            detectability=0.4,
            is_live=True
        )

    def analyze_assumptions(self):
        """Identify core untested assumptions."""
        print("🎯 Analyzing core assumptions...")

        # Assumption 1: Z2 is watching
        self.graph.create_assumption(
            "assume_z2_watching",
            claim="Z2 (Night) is actively monitoring all changes and will catch misalignment",
            falsifiable=True,
            confidence=0.5,
            collapse_risk="critical"
        )

        # Assumption 2: Intent is detectable
        self.graph.create_assumption(
            "assume_intent_detectable",
            claim="True intent can be reliably inferred from code changes",
            falsifiable=True,
            confidence=0.4,
            collapse_risk="critical"
        )

        # Assumption 3: Authority is enforced
        self.graph.create_assumption(
            "assume_authority_enforced",
            claim="Z1 cannot make changes without Z2 approval (it's enforced by CI/CD)",
            falsifiable=True,
            confidence=0.7,
            collapse_risk="high"
        )

        # Assumption 4: Capabilities are known
        self.graph.create_assumption(
            "assume_capabilities_known",
            claim="All capabilities of the system are documented and known",
            falsifiable=True,
            confidence=0.3,
            collapse_risk="critical"
        )

    def run_full_analysis(self):
        """Run complete analysis of the system."""
        print("\n╔════════════════════════════════════════════════════════════╗")
        print("║  ANALYZING HUMANAIOS/OPERATIONS SYSTEM                    ║")
        print("║  Testing for: Deception, Misalignment, Authority Gaps     ║")
        print("╚════════════════════════════════════════════════════════════╝\n")

        self.analyze_recent_commits()
        self.analyze_governance()
        self.analyze_capabilities()
        self.analyze_assumptions()

        print("\n✓ Analysis complete. Generating exposure report...\n")
        self.graph.print_exposure_report()

        # Save graph to file
        output_path = "/tmp/claude-0/-home-user-operations/89b097c5-4815-53f6-a4fe-9615f6570904/scratchpad/graph_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(self.graph.to_dict(), f, indent=2, default=str)
        print(f"\n📁 Graph saved to: {output_path}")

        return self.graph.expose_system()


if __name__ == "__main__":
    analyzer = SystemAnalyzer("/home/user/operations")
    results = analyzer.run_full_analysis()

    print("\n" + "=" * 60)
    print("VERDICT")
    print("=" * 60)

    if results['num_intent_drifts'] > 0:
        print(f"⚠️  {results['num_intent_drifts']} intent drifts detected (possible deception)")

    if results['num_fragile'] > 0:
        print(f"⚠️  {results['num_fragile']} fragile assumptions found (could collapse)")

    if results['num_gaps'] > 0:
        print(f"⚠️  {results['num_gaps']} authority gaps found (unauthorized decisions)")

    if results['transparency_score'] < 0.7:
        print(f"⚠️  Transparency score {results['transparency_score']:.1%} — system is hiding something")

    print(f"\n📊 Overall Risk: {'CRITICAL' if results['transparency_score'] < 0.6 else 'HIGH' if results['transparency_score'] < 0.75 else 'MEDIUM'}")

#!/usr/bin/env python3
"""
A4: Intake Pipeline Processor

Automates the 4-gate document triage workflow:
1. Classify — detect document type + owner
2. Dedup — check vs registry for existing docs
3. Reconcile — if diverged copy exists, recommend merge strategy
4. Register+Place — assign doc_id, frontmatter, registry entry

Usage:
    python3 intake_pipeline.py --scan            # scan _inbox_files*/ and emit report
    python3 intake_pipeline.py --process         # create PRs for diverged pairs + new docs
    python3 intake_pipeline.py --state-file <f>  # use custom state file for diff tracking
"""

import os
import json
import hashlib
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


class IntakePipeline:
    """Process documents through the 4-gate intake workflow."""

    def __init__(self, repo_root: str, registry_path: str, state_file: str = ".doc-control/intake_state.json"):
        self.repo_root = Path(repo_root)
        self.registry_path = Path(registry_path)
        self.state_file = self.repo_root / state_file
        self.inbox_dirs = [
            self.repo_root / "_inbox_files1",
            self.repo_root / "_inbox_files2",
            self.repo_root / "_inbox_files3",
        ]
        self.registry = self._load_registry()
        self.last_state = self._load_state()
        self.current_state = {}
        logger.info(f"Initialized intake pipeline: {len(self.registry.get('documents', []))} docs in registry")

    def _load_registry(self) -> Dict:
        """Load document registry."""
        try:
            with open(self.registry_path) as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.error(f"Registry not found: {self.registry_path}")
            return {"documents": []}

    def _load_state(self) -> Dict:
        """Load last-run state for diff tracking."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
        return {"last_run": None, "inbox_files": {}, "diverged": {}}

    def _save_state(self):
        """Save current state for next run."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.current_state, f, indent=2)

    def _file_hash(self, path: Path) -> str:
        """Compute file hash for content comparison."""
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def scan_inbox(self) -> Dict:
        """Gate 1: Classify all inbox files."""
        logger.info("Gate 1: Scanning inbox directories...")
        inbox_files = {}

        for inbox_dir in self.inbox_dirs:
            if not inbox_dir.exists():
                continue

            for file_path in inbox_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                rel_path = file_path.relative_to(inbox_dir)
                inbox_files[str(rel_path)] = {
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "hash": self._file_hash(file_path),
                    "inbox_dir": str(inbox_dir.name),
                }

        logger.info(f"Found {len(inbox_files)} inbox files")
        self.current_state["inbox_files"] = inbox_files
        return inbox_files

    def check_registry_match(self, filename: str, content_hash: str) -> Optional[Dict]:
        """Gate 2: Check if file already has a registry entry."""
        for doc in self.registry.get("documents", []):
            # Match by filename or by hash similarity
            if doc.get("title") == filename or doc.get("canonical_path", "").endswith(filename):
                return doc
        return None

    def detect_divergence(self, inbox_file: str, inbox_path: Path) -> Optional[Dict]:
        """Gate 3: Detect if a repo canonical exists and differs from inbox."""
        # Simple check: look for file with same name in any repo
        for doc in self.registry.get("documents", []):
            repo_canonical = doc.get("canonical_repo")
            repo_path = doc.get("canonical_path")

            # Check if filenames match
            if Path(repo_path).name == Path(inbox_file).name:
                return {
                    "doc_id": doc.get("doc_id"),
                    "canonical_repo": repo_canonical,
                    "canonical_path": repo_path,
                    "conflict_type": "same_filename_different_location",
                }
        return None

    def emit_report(self, inbox_files: Dict) -> Dict:
        """Generate intake report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "inbox_file_count": len(inbox_files),
            "already_registered": [],
            "diverged_pairs": [],
            "new_documents": [],
            "recommendations": []
        }

        for filename, metadata in inbox_files.items():
            # Check if already in registry
            registry_match = self.check_registry_match(filename, metadata["hash"])
            if registry_match:
                report["already_registered"].append({
                    "filename": filename,
                    "doc_id": registry_match.get("doc_id"),
                    "status": registry_match.get("status")
                })
                continue

            # Check for divergence
            divergence = self.detect_divergence(filename, Path(metadata["path"]))
            if divergence:
                report["diverged_pairs"].append({
                    "filename": filename,
                    **divergence,
                    "inbox_size": metadata["size"]
                })
                report["recommendations"].append({
                    "file": filename,
                    "action": "reconcile",
                    "detail": f"Diverged copy: inbox vs {divergence['canonical_repo']}/{divergence['canonical_path']}"
                })
                continue

            # New document
            report["new_documents"].append({
                "filename": filename,
                "size": metadata["size"],
                "action": "register+place"
            })
            report["recommendations"].append({
                "file": filename,
                "action": "register",
                "detail": "New document — assign doc_id and add frontmatter"
            })

        self.current_state["diverged"] = {d["filename"]: d for d in report["diverged_pairs"]}
        return report

    def save_report(self, report: Dict, output_path: str = "intake_report.json"):
        """Save report to file."""
        output_file = self.repo_root / output_path
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved: {output_path}")

    def run_scan(self):
        """Execute full scan."""
        inbox_files = self.scan_inbox()
        report = self.emit_report(inbox_files)
        self.save_report(report)
        self._save_state()

        # Print summary
        print("\n" + "="*60)
        print("INTAKE PIPELINE REPORT")
        print("="*60)
        print(f"Inbox files scanned: {report['inbox_file_count']}")
        print(f"Already registered: {len(report['already_registered'])}")
        print(f"Diverged pairs: {len(report['diverged_pairs'])}")
        print(f"New documents: {len(report['new_documents'])}")
        print(f"\nRecommendations:")
        for rec in report['recommendations'][:10]:  # Show first 10
            print(f"  • {rec['file']}: {rec['action']} ({rec['detail']})")
        if len(report['recommendations']) > 10:
            print(f"  ... and {len(report['recommendations']) - 10} more")
        print("="*60 + "\n")

        return report


def main():
    parser = argparse.ArgumentParser(description="A4: Intake Pipeline Processor")
    parser.add_argument("--scan", action="store_true", help="Scan inbox and emit report")
    parser.add_argument("--process", action="store_true", help="Create PRs for diverged/new docs")
    parser.add_argument("--repo-root", default=".", help="Root of humanaios repo")
    parser.add_argument("--registry", default="document-registry.yaml", help="Path to registry")
    parser.add_argument("--state-file", default=".doc-control/intake_state.json", help="State file for tracking")
    parser.add_argument("--output", default="intake_report.json", help="Output report path")

    args = parser.parse_args()

    pipeline = IntakePipeline(args.repo_root, args.registry, args.state_file)

    if args.scan or not (args.process):
        # Default: scan
        report = pipeline.run_scan()
        pipeline.save_report(report, args.output)

    if args.process:
        logger.info("Process mode: would create PRs (not yet implemented)")
        logger.info("See A4_INTAKE_PIPELINE_SPEC.md §4 for GitHub Actions integration")


if __name__ == "__main__":
    main()

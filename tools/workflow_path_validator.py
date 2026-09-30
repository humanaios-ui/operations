#!/usr/bin/env python3
"""
Workflow Path Validator

Category: CI/CD & Quality Gates
Purpose: Validates that workflow path filters reference existing repository paths
Prevention: Blocks IC-032 class issues (path filter referencing non-existent files)

Usage:
  python3 workflow_path_validator.py .github/workflows/quality-baseline.yml
  python3 workflow_path_validator.py .github/workflows/*.yml

Features:
- Parses YAML workflow files (handles 'on' key as boolean True)
- Validates both literal paths and glob patterns
- Reports missing files with resolved paths
- Warns about mismatched glob patterns (e.g., /** on file)

Exit Codes:
  0: All paths valid, no warnings
  1: One or more paths not found
  2: File format error or usage error
"""

import sys
from typing import Tuple, List
import yaml
from pathlib import Path


def validate_workflow_paths(workflow_file: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate that all paths in a workflow's path filters exist in repository.

    Args:
        workflow_file: Path to GitHub Actions workflow YAML file

    Returns:
        (is_valid, errors, warnings) where:
        - is_valid: True if all paths exist
        - errors: List of missing paths
        - warnings: List of potential issues
    """
    errors = []
    warnings = []
    repo_root = Path(".")

    try:
        with open(workflow_file) as f:
            workflow = yaml.safe_load(f)
    except Exception as e:
        return False, [f"Failed to parse {workflow_file}: {e}"], []

    if not workflow:
        return False, [f"{workflow_file} is empty"], []

    # Extract all path filters from workflow triggers
    # YAML parses "on" key as boolean True in the dict
    trigger_config_dict = workflow.get(True, {}) if True in workflow else workflow.get("on", {})
    for trigger_name, trigger_config in trigger_config_dict.items():
        if not isinstance(trigger_config, dict):
            continue

        if "paths" not in trigger_config:
            continue

        paths = trigger_config["paths"]
        if not isinstance(paths, list):
            errors.append(f"Trigger '{trigger_name}': paths must be a list")
            continue

        for path_pattern in paths:
            # Handle glob patterns
            if path_pattern.endswith("/**"):
                base_path = path_pattern[:-3]
            elif path_pattern.endswith("/*"):
                base_path = path_pattern[:-2]
            else:
                base_path = path_pattern

            # Check if path exists
            full_path = repo_root / base_path
            if not full_path.exists():
                errors.append(
                    f"Path '{path_pattern}' not found in repository "
                    f"(resolved to: {full_path.relative_to(repo_root)})"
                )
            else:
                # Verify glob pattern makes sense
                if path_pattern.endswith("/**"):
                    if not full_path.is_dir():
                        warnings.append(
                            f"Path '{path_pattern}' uses /** glob but "
                            f"'{base_path}' is not a directory"
                        )

    return len(errors) == 0, errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: workflow_path_validator.py <workflow_file> [workflow_file...]")
        print("Example: workflow_path_validator.py .github/workflows/*.yml")
        sys.exit(2)

    workflow_files = sys.argv[1:]
    total_errors = 0
    total_warnings = 0

    for workflow_file in workflow_files:
        workflow_path = Path(workflow_file)

        if not workflow_path.exists():
            print(f"❌ {workflow_file}: File not found")
            total_errors += 1
            continue

        is_valid, errors, warnings = validate_workflow_paths(workflow_file)

        if is_valid and not warnings:
            # Count the paths checked
            try:
                with open(workflow_file) as f:
                    workflow = yaml.safe_load(f)
                path_count = 0
                trigger_config_dict = workflow.get(True, {}) if True in workflow else workflow.get("on", {})
                for trigger_config in trigger_config_dict.values():
                    if isinstance(trigger_config, dict) and "paths" in trigger_config:
                        path_count += len(trigger_config["paths"])
                print(f"✅ {workflow_file}: All paths valid ({path_count} files)")
            except:
                print(f"✅ {workflow_file}: All paths valid")
        else:
            print(f"⚠️  {workflow_file}:")
            for error in errors:
                print(f"  ❌ {error}")
                total_errors += 1
            for warning in warnings:
                print(f"  ⚠️  {warning}")
                total_warnings += 1

    if total_errors > 0:
        print(f"\n❌ Validation failed: {total_errors} error(s) found")
        sys.exit(1)
    elif total_warnings > 0:
        print(f"\n⚠️  Validation passed with {total_warnings} warning(s)")
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

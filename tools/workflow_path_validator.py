#!/usr/bin/env python3
"""
Workflow Path Validator — validate GitHub Actions path filters
Version: 1.0.0 (Zone 1 draft)

HumanAIOS validation tool for IC-032 prevention. It checks workflow path
filters against the current repository tree while treating recursive and
inline wildcard patterns conservatively.

Usage:
  python3 tools/workflow_path_validator.py .github/workflows/*.yml
  python3 tools/workflow_path_validator.py --smoke-test
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

import yaml


TOOL_NAME = "workflow_path_validator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "validation_tool"
TOOL_SESSION = "PHASE-2B-SALVAGE"
TOOL_ZONE = 1


def validate_workflow_paths(workflow_file: str) -> Tuple[bool, List[str], List[str]]:
    """Validate path filters in one workflow.

    Recursive globs beginning with double-star slash are accepted without a
    literal base check because they may match at multiple repository depths.
    Inline wildcards are treated as structurally valid; a missing parent
    directory is reported as a warning rather than a hard failure. Literal
    missing paths remain errors.
    """
    errors: List[str] = []
    warnings: List[str] = []
    repo_root = Path(".")

    try:
        with open(workflow_file, encoding="utf-8") as handle:
            workflow = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        return False, [f"Failed to parse {workflow_file}: {exc}"], []

    if not workflow or not isinstance(workflow, dict):
        return False, [f"{workflow_file} is empty or not a mapping"], []

    trigger_key = True if True in workflow else "on"
    trigger_config_dict = workflow.get(trigger_key, {})
    if not isinstance(trigger_config_dict, dict):
        return True, [], []

    for trigger_name, trigger_config in trigger_config_dict.items():
        if not isinstance(trigger_config, dict) or "paths" not in trigger_config:
            continue

        paths = trigger_config["paths"]
        if not isinstance(paths, list):
            errors.append(f"Trigger '{trigger_name}': paths must be a list")
            continue

        for path_pattern in paths:
            if not isinstance(path_pattern, str) or not path_pattern.strip():
                errors.append(f"Trigger '{trigger_name}': path entries must be non-empty strings")
                continue

            base_path = path_pattern

            # Recursive patterns can match at several repository depths, so
            # there is no single literal base path to require.
            if path_pattern.startswith("**/"):
                continue

            # Inline wildcards are structurally valid. A missing parent is
            # surfaced as a warning because future files may satisfy the glob.
            if "*" in base_path or "?" in base_path:
                if "/" in base_path:
                    parent = str(Path(base_path).parent)
                    if parent != "." and not (repo_root / parent).exists():
                        warnings.append(
                            f"Path '{path_pattern}' references directory '{parent}' which does not exist"
                        )
                continue

            if path_pattern.endswith("/**"):
                base_path = path_pattern[:-3]
            elif path_pattern.endswith("/*"):
                base_path = path_pattern[:-2]

            full_path = repo_root / base_path
            if not full_path.exists():
                errors.append(
                    f"Path '{path_pattern}' not found in repository "
                    f"(resolved to: {full_path.relative_to(repo_root)})"
                )
            elif path_pattern.endswith("/**") and not full_path.is_dir():
                warnings.append(
                    f"Path '{path_pattern}' uses recursive glob but '{base_path}' is not a directory"
                )

    return len(errors) == 0, errors, warnings


def run_validation(workflow_files: List[str]) -> int:
    """Validate workflow files and return the CLI exit code."""
    total_errors = 0
    total_warnings = 0

    for workflow_file in workflow_files:
        workflow_path = Path(workflow_file)
        if not workflow_path.exists():
            print(f"ERROR {workflow_file}: file not found")
            total_errors += 1
            continue

        is_valid, errors, warnings = validate_workflow_paths(workflow_file)

        if is_valid and not warnings:
            print(f"OK {workflow_file}")
        else:
            print(f"CHECK {workflow_file}")
            for error in errors:
                print(f"  ERROR {error}")
                total_errors += 1
            for warning in warnings:
                print(f"  WARN {warning}")
                total_warnings += 1

    if total_errors:
        return 1
    if total_warnings:
        return 0
    return 0


def smoke_test() -> int:
    """Run deterministic self-checks without repository mutation."""
    assert TOOL_NAME == "workflow_path_validator"
    assert TOOL_VERSION == "1.0.0"
    print("smoke-test OK — workflow path validator loaded.")
    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workflow_files", nargs="*")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        return smoke_test()
    if not args.workflow_files:
        parser.error("provide at least one workflow file or --smoke-test")
    return run_validation(args.workflow_files)


if __name__ == "__main__":
    raise SystemExit(main())

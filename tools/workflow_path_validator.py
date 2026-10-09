#!/usr/bin/env python3
"""
Workflow Path Validator — Builder v1.7 compliant

Validates that all paths referenced in GitHub Actions workflow path filters
actually exist in the repository. Prevents IC-032 class issues where path filters
reference non-existent files.

Usage:
  python3 workflow_path_validator.py .github/workflows/quality-baseline.yml
  python3 workflow_path_validator.py .github/workflows/*.yml
  python3 workflow_path_validator.py --smoke-test

Exit codes:
  0: All paths valid
  1: One or more paths not found
  2: File format error
"""

import sys
import glob
import yaml
from pathlib import Path

# Builder v1.7 contract
TOOL_NAME = "workflow_path_validator"
TOOL_VERSION = "1.0.0"
BUILDER_SIGNATURE = "HumanAIOS"


def validate_workflow_paths(workflow_file: str) -> tuple[bool, list, list]:
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
    # Note: "on" is parsed as boolean True in YAML, so check for both forms
    trigger_key = True if True in workflow else "on"
    for trigger_name, trigger_config in workflow.get(trigger_key, {}).items():
        if not isinstance(trigger_config, dict):
            continue

        # Handle both `paths` and `paths-ignore` filters
        for filter_key in ["paths", "paths-ignore"]:
            if filter_key not in trigger_config:
                continue

            paths = trigger_config[filter_key]
            if not isinstance(paths, list):
                errors.append(f"Trigger '{trigger_name}': {filter_key} must be a list")
                continue

            for path_pattern in paths:
                # Patterns starting with "**/" can match at any level — always valid syntactically
                if path_pattern.startswith("**/"):
                    continue

                # Use glob to check if pattern matches anything
                matches = glob.glob(str(repo_root / path_pattern), recursive=True)

                # If pattern has wildcards, verify it has potential matches
                if "*" in path_pattern or "?" in path_pattern:
                    if not matches:
                        # Pattern matches nothing currently. Check if it's future-facing.
                        if "/" in path_pattern:
                            parent = str(Path(path_pattern).parent)

                            # If parent contains wildcards, it's a future-facing pattern — allow with warning
                            if "*" in parent or "?" in parent:
                                warnings.append(
                                    f"Path '{path_pattern}' is future-facing (directory name has wildcards); "
                                    f"no matches currently"
                                )
                            elif parent != ".":
                                full_path = repo_root / parent
                                if not full_path.exists():
                                    errors.append(
                                        f"Path '{path_pattern}' references non-existent directory '{parent}' "
                                        f"and no files match the pattern"
                                    )
                                else:
                                    # Parent exists but no matches — warn for future-facing patterns
                                    warnings.append(
                                        f"Path '{path_pattern}' matches no files (parent directory exists)"
                                    )
                            else:
                                errors.append(
                                    f"Path '{path_pattern}' matches no files in repository"
                                )
                        else:
                            errors.append(
                                f"Path '{path_pattern}' matches no files in repository"
                            )
                    continue

                # For literal paths (no wildcards), check existence
                full_path = repo_root / path_pattern
                if path_pattern.endswith("/**"):
                    base_path = path_pattern[:-3]
                    full_path = repo_root / base_path
                    if not full_path.exists():
                        errors.append(
                            f"Path '{path_pattern}' not found (base: {base_path})"
                        )
                    elif not full_path.is_dir():
                        warnings.append(
                            f"Path '{path_pattern}' uses /** glob but '{base_path}' is not a directory"
                        )
                elif path_pattern.endswith("/*"):
                    base_path = path_pattern[:-2]
                    full_path = repo_root / base_path
                    if not full_path.exists():
                        errors.append(
                            f"Path '{path_pattern}' not found (base: {base_path})"
                        )
                else:
                    if not full_path.exists():
                        errors.append(
                            f"Path '{path_pattern}' not found in repository"
                        )

    return len(errors) == 0, errors, warnings


def smoke_test():
    """Run smoke tests to verify the validator works correctly."""
    import tempfile
    import json

    # Test 1: Valid pattern
    test_passed = 0
    test_total = 0

    # Test valid literal path
    test_total += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.md"
            test_file.write_text("test")

            # Create a minimal workflow referencing the test file
            workflow_content = {
                "on": {"push": {"paths": ["test.md"]}},
                "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": [{"run": "echo test"}]}}
            }
            workflow_file = Path(tmpdir) / "workflow.yml"
            workflow_file.write_text(yaml.dump(workflow_content))

            # Change to temp directory to validate paths correctly
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                is_valid, errors, warnings = validate_workflow_paths("workflow.yml")
                if is_valid and not errors:
                    test_passed += 1
            finally:
                os.chdir(old_cwd)
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")

    # Test 2: Invalid pattern (no matches, no parent)
    test_total += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            workflow_content = {
                "on": {"push": {"paths": ["nonexistent-*.json"]}},
                "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": [{"run": "echo test"}]}}
            }
            workflow_file = Path(tmpdir) / "workflow.yml"
            workflow_file.write_text(yaml.dump(workflow_content))

            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                is_valid, errors, warnings = validate_workflow_paths("workflow.yml")
                if not is_valid and errors:  # Should fail for no matches
                    test_passed += 1
            finally:
                os.chdir(old_cwd)
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")

    # Test 3: paths-ignore support
    test_total += 1
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("# test")

            workflow_content = {
                "on": {"push": {"paths-ignore": ["test.py"]}},
                "jobs": {"test": {"runs-on": "ubuntu-latest", "steps": [{"run": "echo test"}]}}
            }
            workflow_file = Path(tmpdir) / "workflow.yml"
            workflow_file.write_text(yaml.dump(workflow_content))

            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                is_valid, errors, warnings = validate_workflow_paths("workflow.yml")
                if is_valid:  # paths-ignore should pass when path exists
                    test_passed += 1
            finally:
                os.chdir(old_cwd)
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

    result = f"✅ Smoke tests passed: {test_passed}/{test_total}"
    print(result)
    return test_passed == test_total


def main():
    if len(sys.argv) < 2:
        print("Usage: workflow_path_validator.py <workflow_file> [workflow_file...]")
        print("       workflow_path_validator.py --smoke-test")
        print("Example: workflow_path_validator.py .github/workflows/*.yml")
        sys.exit(2)

    # Handle smoke test flag
    if sys.argv[1] == "--smoke-test":
        success = smoke_test()
        sys.exit(0 if success else 1)

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
                trigger_key = True if True in workflow else "on"
                for trigger_config in workflow.get(trigger_key, {}).values():
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

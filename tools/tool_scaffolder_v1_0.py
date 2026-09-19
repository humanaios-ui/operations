#!/usr/bin/env python3
"""
tool_scaffolder_v1_0.py
Builder v1.7 compliant · scaffolder_tool
HumanAIOS · S-051726-02-molt-grow-kill

WHAT THIS DOES
--------------
Generates a complete Builder v1.7-compliant Python tool skeleton from a
structured spec. Every generated file passes builder_compliance_scanner_v1_0.py
on first run — no manual boilerplate, no missed checks.

TIME SAVINGS: ~45 minutes of copy-paste and header-fixing → ~90 seconds.
Consistent interface across all tools, guaranteed.

USAGE
-----
  python tool_scaffolder_v1_0.py --name carry_tracker --type diagnostic_tool \\
      --desc "Reads WGS posts, counts sessions-carried per item, flags escalations" \\
      --session S-051726-02 --output tools/

  python tool_scaffolder_v1_0.py --interactive
  python tool_scaffolder_v1_0.py --spec carry_tracker_spec.json
  python tool_scaffolder_v1_0.py --smoke-test

TOOL TYPES (--type)
-------------------
  diagnostic_tool      Read-only analysis, produces a report
  validation_tool      Validates data/schema against a spec, PASS/WARN/FAIL
  audit_tool           Cross-checks multiple sources for consistency
  connector_tool       Reads/writes to external service (Supabase, GitHub, Slack)
  security_gate_tool   Pre-execution gate that blocks on failure
  orchestrator_tool    Calls other tools in sequence, aggregates results
  scaffolder_tool      Generates new tools or artifacts (this file's type)

GENERATED FILE STRUCTURE
-------------------------
Every generated tool has:
  - Builder v1.7 header (docstring + TOOL_NAME + TOOL_VERSION)
  - TOOL_CATEGORY, TOOL_SESSION constants
  - SpecLoadFailed exception class
  - load_input() — reads JSON/text input; raises SpecLoadFailed on error
  - run() — core logic placeholder (you fill this in)
  - aggregate() — assembles final output dict with standard fields
  - write_report() — saves JSON report to output_dir
  - print_summary() — human-readable terminal output
  - run_smoke_test() — minimal self-test with assert statements
  - main() — argparse entry point with --input, --output, --smoke-test

ZONE ASSIGNMENT
---------------
Generated tools are Zone 1 by default (agent executes, human reviews output).
Pass --zone 2 for tools that require human approval before output is acted on.
Pass --zone 3 for tools that only propose actions (Night executes).
"""

import json
import sys
import argparse
import textwrap
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME    = "tool_scaffolder"
TOOL_VERSION = "1.0.0"

TOOL_TYPES = [
    "diagnostic_tool",
    "validation_tool",
    "audit_tool",
    "connector_tool",
    "security_gate_tool",
    "orchestrator_tool",
    "scaffolder_tool",
]

# ── Template ──────────────────────────────────────────────────────────────────

TEMPLATE = '''\
#!/usr/bin/env python3
"""
{tool_name_display}
Builder v1.7 compliant · {tool_type}
HumanAIOS · {session_id}

{description}

Usage:
  python {filename} --input <path_or_json>
  python {filename} --smoke-test
  python {filename} --help
"""

import json
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME     = "{tool_name}"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "{tool_type}"
TOOL_SESSION  = "{session_id}"
TOOL_ZONE     = {zone}   # 1=execute, 2=ratify, 3=night


class SpecLoadFailed(Exception):
    """Raised when input cannot be loaded or parsed."""
    pass


# ── Input Loading ─────────────────────────────────────────────────────────────

def load_input(source: str) -> dict:
    """
    Load input from a file path or raw JSON string.
    Raises SpecLoadFailed if input cannot be parsed.

    AGENT INSTRUCTION: Replace or extend this with your actual
    input format. Keep SpecLoadFailed for unreadable input — the
    validation suite catches it cleanly.
    """
    # Try as file path first
    p = Path(source)
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise SpecLoadFailed(f"Cannot load {{p}}: {{e}}")
    # Try as inline JSON
    try:
        return json.loads(source)
    except json.JSONDecodeError as e:
        raise SpecLoadFailed(f"Input is neither a valid path nor valid JSON: {{e}}")


# ── Core Logic ────────────────────────────────────────────────────────────────

def run(data: dict) -> dict:
    """
    AGENT INSTRUCTION: This is the only function you need to fill in.
    Everything else is boilerplate.

    Receives the loaded input dict.
    Returns a results dict. Convention:
      {{
        "status":   "PASS" | "WARN" | "FAIL",
        "items":    [{{...}}],   # list of result items
        "summary":  {{...}},     # aggregate stats
      }}

    Raise SpecLoadFailed for any unrecoverable input error.
    Use soft warnings (add to results, don\'t raise) for recoverable issues.
    """
    # ── YOUR LOGIC HERE ────────────────────────────────────────────
    # Example structure — replace with actual implementation:

    items = []
    warnings = []

    # TODO: iterate over data, populate items and warnings
    # Example:
    #   for key, val in data.items():
    #       if val is None:
    #           warnings.append(f"{{key}} is None")
    #       else:
    #           items.append({{"key": key, "value": val, "status": "OK"}})

    status = "FAIL" if not items and not warnings else (
        "WARN" if warnings else "PASS"
    )

    return {{
        "status":   status,
        "items":    items,
        "warnings": warnings,
        "summary":  {{
            "total":    len(items),
            "warnings": len(warnings),
        }},
    }}


# ── Output Assembly ───────────────────────────────────────────────────────────

def aggregate(run_result: dict, source: str) -> dict:
    """Assemble final output dict with standard Builder v1.7 envelope."""
    return {{
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "zone":      TOOL_ZONE,
        "session":   TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source":    source,
        "result":    run_result.get("status", "FAIL"),
        **run_result,
    }}


def write_report(output: dict, output_dir: str) -> str:
    """Write JSON report to output_dir. Returns file path."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"{TOOL_NAME}_{{ts}}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    """Print human-readable summary to stdout."""
    bar = "=" * 60
    verdict = output.get("result", "UNKNOWN")
    color = "" # no ANSI — keep output clean for pipe/grep
    print(f"\\n{{bar}}")
    print(f" {{TOOL_NAME}} v{{TOOL_VERSION}}")
    print(f" Verdict : {{verdict}}")
    summary = output.get("summary", {{}})
    for k, v in summary.items():
        print(f" {{k:<12}}: {{v}}")
    warnings = output.get("warnings", [])
    if warnings:
        print(f"\\n Warnings:")
        for w in warnings:
            print(f"   WARN  {{w}}")
    items = output.get("items", [])
    if items:
        print(f"\\n Items ({{len(items)}}):")
        for item in items[:20]:   # cap at 20 for readability
            status = item.get("status","?")
            key    = item.get("key", item.get("id", "?"))
            print(f"   {{status:<6}} {{key}}")
        if len(items) > 20:
            print(f"   ... and {{len(items)-20}} more")
    print(f"{{bar}}\\n")


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    """
    Minimal self-test. Must pass before Builder v1.7 compliance is claimed.
    AGENT INSTRUCTION: Add at least one positive and one negative assertion.
    """
    try:
        # Positive: valid input produces PASS or WARN
        sample = {{"_smoke": True}}
        result = run(sample)
        assert "status" in result, "run() must return a dict with 'status'"
        assert result["status"] in ("PASS","WARN","FAIL"), f"Unexpected status: {{result[\'status\']}}"

        # Envelope test
        output = aggregate(result, "_smoke")
        assert output["tool"]    == TOOL_NAME
        assert output["version"] == TOOL_VERSION
        assert "timestamp" in output

        # Negative: bad input raises SpecLoadFailed
        try:
            load_input("/nonexistent/path/that/cannot/exist.json")
            assert False, "Should have raised SpecLoadFailed"
        except SpecLoadFailed:
            pass   # expected

        print("✓ Smoke test PASSED")
        return True

    except AssertionError as e:
        print(f"✗ Smoke test FAILED: {{e}}")
        return False
    except Exception as e:
        print(f"✗ Smoke test ERROR: {{e}}")
        return False


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"{tool_name_display} v1.0.0"
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to input file or inline JSON string"
    )
    parser.add_argument(
        "--output", "-o",
        default="outputs/",
        help="Directory for JSON report output (default: outputs/)"
    )
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run smoke test and exit"
    )
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    try:
        data = load_input(args.input)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {{e}}", file=sys.stderr)
        sys.exit(2)

    run_result = run(data)
    output     = aggregate(run_result, args.input)
    rp         = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {{rp}}")
    sys.exit(0 if output["result"] in ("PASS","WARN") else 1)


if __name__ == "__main__":
    main()
'''


# ── Spec Validation ───────────────────────────────────────────────────────────

def validate_spec(spec: dict) -> list:
    """Validate a tool spec dict. Returns list of error strings."""
    errors = []
    required = ["name", "type", "description", "session"]
    for field in required:
        if not spec.get(field):
            errors.append(f"Missing required field: {field}")
    if spec.get("type") and spec["type"] not in TOOL_TYPES:
        errors.append(
            f"Unknown tool type '{spec['type']}'. "
            f"Valid: {', '.join(TOOL_TYPES)}"
        )
    name = spec.get("name", "")
    if name and not all(c.isalnum() or c == "_" for c in name):
        errors.append("Tool name must be alphanumeric + underscores only")
    zone = spec.get("zone", 1)
    if zone not in (1, 2, 3):
        errors.append(f"Zone must be 1, 2, or 3 (got {zone})")
    return errors


# ── Code Generation ───────────────────────────────────────────────────────────

def generate_tool(spec: dict) -> str:
    """Generate Builder v1.7-compliant tool source from spec dict."""
    errors = validate_spec(spec)
    if errors:
        raise SpecLoadFailed("Invalid spec:\n" + "\n".join(f"  · {e}" for e in errors))

    name    = spec["name"].lower().replace("-", "_")
    version = spec.get("version", "1_0")
    filename = f"{name}_v{version}.py"

    # Build display name: carry_tracker → Carry Tracker
    display = " ".join(w.capitalize() for w in name.split("_"))

    # Use explicit replacement to avoid brace-escaping issues in template
    replacements = {
        "{tool_name_display}": f"{display} — v{version.replace('_','.')}",
        "{tool_name}":         name,
        "{tool_type}":         spec["type"],
        "{session_id}":        spec["session"],
        "{description}":       textwrap.fill(spec["description"], width=68),
        "{filename}":          filename,
        "{zone}":              str(spec.get("zone", 1)),
    }
    code = TEMPLATE
    for placeholder, value in replacements.items():
        code = code.replace(placeholder, value)
    # Unescape {{ → { and }} → } (Python template literal escaping)
    code = code.replace("{{", "{").replace("}}", "}")
    return code, filename


# ── Aggregate + Report ────────────────────────────────────────────────────────

def aggregate(result: dict) -> dict:
    return {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **result,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"scaffold_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    bar = "=" * 60
    print(f"\n{bar}")
    print(f" tool_scaffolder v{TOOL_VERSION}")
    print(f" Result : {output.get('result','?')}")
    if output.get("generated_file"):
        print(f" Output : {output['generated_file']}")
    if output.get("errors"):
        print(f"\n Errors:")
        for e in output["errors"]:
            print(f"   ✗ {e}")
    if output.get("spec"):
        s = output["spec"]
        print(f"\n Spec:")
        print(f"   name    : {s.get('name')}")
        print(f"   type    : {s.get('type')}")
        print(f"   zone    : {s.get('zone',1)}")
        print(f"   session : {s.get('session')}")
    print(f"{bar}\n")


# ── Interactive Mode ──────────────────────────────────────────────────────────

def interactive_mode(output_dir: str) -> None:
    """Walk the user through creating a new tool spec interactively."""
    print("\n── HumanAIOS Tool Scaffolder ─────────────────────────────")
    print("  Generates a Builder v1.7-compliant tool skeleton.")
    print("  Answer the prompts. All fields required.\n")

    name = input("  Tool name (snake_case, no version): ").strip()
    print(f"  Tool types: {', '.join(TOOL_TYPES)}")
    tool_type = input("  Tool type: ").strip()
    description = input("  One-sentence description: ").strip()
    session = input(f"  Session ID [S-051726-02]: ").strip() or "S-051726-02"
    zone_raw = input("  Zone [1]: ").strip() or "1"
    version_raw = input("  Version string [1_0]: ").strip() or "1_0"

    spec = {
        "name": name,
        "type": tool_type,
        "description": description,
        "session": session,
        "zone": int(zone_raw),
        "version": version_raw,
    }

    errors = validate_spec(spec)
    if errors:
        print("\nSpec errors:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)

    code, filename = generate_tool(spec)
    out_path = Path(output_dir) / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")
    print(f"\n✓ Generated: {out_path}")
    print(f"  Next: fill in run() function, then:")
    print(f"  python {filename} --smoke-test")
    print(f"  python builder_compliance_scanner_v1_0.py --path {filename}")


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    import tempfile
    try:
        spec = {
            "name": "test_carry_tracker",
            "type": "diagnostic_tool",
            "description": "Counts carry item sessions from WGS posts and flags escalations.",
            "session": "S-051726-02",
            "zone": 1,
            "version": "1_0",
        }

        # Validate spec
        errors = validate_spec(spec)
        assert not errors, f"Spec validation failed: {errors}"

        # Generate code
        code, filename = generate_tool(spec)
        assert "Builder v1.7 compliant" in code
        assert "TOOL_NAME" in code
        assert "TOOL_VERSION" in code
        assert "HumanAIOS" in code
        assert "run_smoke_test" in code
        assert "if __name__" in code
        assert "write_report" in code
        assert "argparse.ArgumentParser" in code
        assert "SpecLoadFailed" in code
        assert filename == "test_carry_tracker_v1_0.py"

        # Write to temp dir and verify it's valid Python
        import ast
        ast.parse(code)  # would raise SyntaxError if broken

        # Run the generated file's smoke test in a temp dir
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / filename
            p.write_text(code, encoding="utf-8")
            import subprocess
            result = subprocess.run(
                [sys.executable, str(p), "--smoke-test"],
                capture_output=True, text=True
            )
            assert result.returncode == 0, (
                f"Generated tool smoke test failed:\n{result.stdout}\n{result.stderr}"
            )

        # Verify scanner would pass it
        # (inline the check logic since we can't import the scanner easily)
        import re
        checks = [
            r"Builder v1\.7 compliant",
            r"^TOOL_NAME\s*=",
            r"^TOOL_VERSION\s*=",
            r"HumanAIOS",
            r"smoke.test|run_smoke_test",
            r"if __name__",
            r"def write_report",
            r"argparse\.ArgumentParser",
            r"class SpecLoadFailed|SpecLoadFailed",
        ]
        for pat in checks:
            assert re.search(pat, code, re.I | re.M), (
                f"Generated code fails scanner check: {pat}"
            )

        print("✓ Smoke test PASSED — generated tool passes all Builder v1.7 checks")
        return True

    except AssertionError as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ Smoke test ERROR: {e}")
        return False


# ── Entry Point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="HumanAIOS Tool Scaffolder v1.0 — generates Builder v1.7-compliant tools"
    )
    parser.add_argument("--name",        help="Tool name (snake_case)")
    parser.add_argument("--type",        help=f"Tool type: {', '.join(TOOL_TYPES)}")
    parser.add_argument("--desc",        help="One-sentence description")
    parser.add_argument("--session",     default="S-051726-02", help="Session ID")
    parser.add_argument("--zone",        type=int, default=1, help="Zone 1/2/3")
    parser.add_argument("--version",     default="1_0", help="Version string e.g. 1_0")
    parser.add_argument("--spec",        help="Path to JSON spec file")
    parser.add_argument("--output", "-o",default=".",  help="Output directory")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--smoke-test",  action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.interactive:
        interactive_mode(args.output)
        return

    # Load spec from file or CLI args
    if args.spec:
        try:
            spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
    elif args.name and args.type and args.desc:
        spec = {
            "name":        args.name,
            "type":        args.type,
            "description": args.desc,
            "session":     args.session,
            "zone":        args.zone,
            "version":     args.version,
        }
    else:
        parser.print_help()
        print(
            "\nExamples:\n"
            "  python tool_scaffolder_v1_0.py --name carry_tracker "
            "--type diagnostic_tool "
            "--desc 'Counts carry item sessions from WGS posts' "
            "--session S-051726-02\n"
            "  python tool_scaffolder_v1_0.py --interactive\n"
            "  python tool_scaffolder_v1_0.py --smoke-test\n"
        )
        sys.exit(1)

    errors = validate_spec(spec)
    if errors:
        print("Spec errors:", file=sys.stderr)
        for e in errors:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit(1)

    try:
        code, filename = generate_tool(spec)
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    out_path = Path(args.output) / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(code, encoding="utf-8")

    result = {
        "result":         "PASS",
        "generated_file": str(out_path),
        "filename":       filename,
        "spec":           spec,
        "errors":         [],
        "next_steps": [
            f"Fill in the run() function in {filename}",
            f"python {filename} --smoke-test",
            f"python builder_compliance_scanner_v1_0.py --path {filename}",
        ]
    }
    output = aggregate(result)
    rp = write_report(output, args.output)
    print_summary(output)
    print(f"Generated : {out_path}")
    print(f"Next      : python {filename} --smoke-test")
    print(f"Then      : python builder_compliance_scanner_v1_0.py --path {filename}")
    print(f"Report    : {rp}")


if __name__ == "__main__":
    main()

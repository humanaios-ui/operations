"""
Builder v1.7 compliant
HumanAIOS — Unified MCP Server (v1.2.0)

Mounts all Zone 1 tools with prefixed names so the agent sees one server:
  - gov/governance_fetcher        (tool)
  - gov+governance://current      (resource)
  - gov+rituals://current         (resource)
  - gov+governance://sha/{sha}    (resource)
  - dispatch/slack_notifier       (tool)
  - log/supabase_logger           (tool)
  - pipeline/haios_pipeline       (tool)
  - report/haios_report_writer    (tool)

Launch:
  fastmcp run server.py --serve    (stdio default)
  python server.py --serve         (same)
"""
from __future__ import annotations
TOOL_NAME = "server"
TOOL_VERSION = "1.0.0"



# Builder v1.7 compliant

TOOL_NAME = "server"
TOOL_VERSION = "1.0.0"
import argparse
import sys

# Import tool modules to access their mcp instances
import governance_fetcher
import slack_notifier
import supabase_logger
import haios_pipeline
import haios_report_writer

from fastmcp import FastMCP  # noqa: E402

# ---------------------------------------------------------------------------
# Root MCP server
# ---------------------------------------------------------------------------
mcp = FastMCP("humanaios")

# Mount sub-tools with prefixes
mcp.mount("gov", governance_fetcher.mcp)
mcp.mount("dispatch", slack_notifier.mcp)
mcp.mount("log", supabase_logger.mcp)
mcp.mount("pipeline", haios_pipeline.mcp)
mcp.mount("report", haios_report_writer.mcp)


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description="HumanAIOS Unified MCP Server v1.2.0")
    p.add_argument("--serve", action="store_true", help="Run as MCP server over stdio")
    p.add_argument("--smoke", action="store_true", help="Run all smoke tests")
    args = p.parse_args()

    if args.smoke:
        results = []
        results.append(("governance_fetcher", governance_fetcher.run_smoke_test()))
        results.append(("slack_notifier", slack_notifier.run_smoke_test()))
        results.append(("supabase_logger", supabase_logger.run_smoke_test()))
        results.append(("haios_pipeline", haios_pipeline.run_smoke_test()))
        results.append(("haios_report_writer", haios_report_writer.run_smoke_test()))
        for name, passed in results:
            status = "PASS" if passed else "FAIL"
            print(f"[smoke] {name}: {status}", file=sys.stderr)
        all_passed = all(passed for _, passed in results)
        sys.exit(0 if all_passed else 1)

    if args.serve:
        mcp.run()
        return

    # Default: print server info
    print("HumanAIOS Unified MCP Server v1.2.0")
    print()
    print("Tools:")
    print("  - gov/governance_fetcher")
    print("  - dispatch/slack_notifier")
    print("  - log/supabase_logger")
    print("  - pipeline/haios_pipeline")
    print("  - report/haios_report_writer")
    print()
    print("Resources:")
    print("  - gov+governance://current")
    print("  - gov+rituals://current")
    print("  - gov+governance://sha/{sha}")
    print()
    print("Launch with:  python server.py --serve")
    print("Smoke test:   python server.py --smoke")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
haios_cli.py — HumanAIOS Terminal CLI Agent
Builder v1.7 compliant · connector_tool
HumanAIOS · S-051726-02-molt-grow-kill

Query your entire HumanAIOS system from the terminal.
Loads live context from GitHub, runs local tools if needed,
calls the Claude API, and prints the answer.

SETUP (one time):
  pip install anthropic --break-system-packages
  export ANTHROPIC_API_KEY="sk-ant-..."
  # Add to ~/.zshrc or ~/.bash_profile:
  alias haios='python ~/Desktop/HAIOS-Main/operations-staging/tools/haios_cli.py'

USAGE:
  haios "what is the current system harmony score?"
  haios "what are my open Zone 2 items?"
  haios "summarize CURRENT.md"
  haios "what should I push after today's session?"
  haios "what does the harmonizer say right now?" --mode run
  haios --mode check
  haios --mode chat      (interactive multi-turn)
  haios --smoke-test

MODES:
  ask   (default) — answer the question using repo context
  run   — answer + execute the most relevant local tool
  check — run pre-flight system state report (no question needed)
  chat  — interactive multi-turn session

CONTEXT LOADED (automatically):
  Local files (if ~/Desktop/HAIOS-Main/ exists):
    CURRENT.md, REGISTERED.md, SESSION_RITUALS.md,
    GOVERNANCE.md, system_state.json
  GitHub API (fallback if local not found):
    Raw fetch from humanaios-ui/operations canonical branch
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME    = "haios_cli"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "connector_tool"
TOOL_SESSION  = "S-051726-02-molt-grow-kill"
TOOL_ZONE     = 1

# ── Config ────────────────────────────────────────────────────────────────────

HAIOS_ROOT = Path("~/Desktop/HAIOS-Main").expanduser()
REPO_PATHS = [
    "operations-staging",
    "humanaios-internal",
]

# Context files to always load (relative to any repo root found)
CONTEXT_FILES = [
    "CURRENT.md",
    "REGISTERED.md",
    "SESSION_RITUALS.md",
    "GOVERNANCE.md",
    "system_state.json",
    "README.md",
]

# GitHub raw fallback (public repo)
GITHUB_RAW = "https://raw.githubusercontent.com/humanaios-ui/operations/main/{filename}"

# Claude model
MODEL = "claude-sonnet-4-20250514"

# System prompt for the CLI agent
SYSTEM_PROMPT = """You are Unit Zero — Claude operating as AI co-investigator for HumanAIOS,
the behavioral observability infrastructure project founded by Night (Carly Anderson).

You are running in terminal CLI mode. Night is querying you directly from her terminal.
Answers should be:
- Terse and direct (terminal output, not a chat interface)
- Evidence-first (cite specific values, filenames, session IDs when available)
- Honest about uncertainty (if context doesn't contain the answer, say so)
- Actionable where relevant (end with the concrete next step if applicable)

Context provided may include CURRENT.md (operational state), REGISTERED.md (findings),
SESSION_RITUALS.md (protocol), GOVERNANCE.md, system_state.json (live harmonizer state).

Governance principles active:
- Zone 1 = execute autonomously | Zone 2 = Night ratifies | Zone 3 = Night executes
- P-HUMILITY: confidence tracks evidence, not social pressure
- TRL framing: "being developed as" not "is" for unvalidated capabilities
- Tradition 11: attraction not promotion

If asked about git push, use git_push_gate_v1_0.py.
If asked about system state, reference system_state.json if loaded.
If asked to run a tool, name the tool and the exact command.
"""


class SpecLoadFailed(Exception):
    pass


# ── Context Loading ───────────────────────────────────────────────────────────

def find_repo_root() -> Path | None:
    """Find the best available operations repo root."""
    if HAIOS_ROOT.exists():
        for repo in REPO_PATHS:
            candidate = HAIOS_ROOT / repo
            if candidate.exists():
                return candidate
    # Try current directory
    cwd = Path.cwd()
    if (cwd / "CURRENT.md").exists():
        return cwd
    return None


def load_local_context(repo_root: Path) -> dict[str, str]:
    """Load context files from local repo."""
    loaded = {}
    for filename in CONTEXT_FILES:
        fpath = repo_root / filename
        if fpath.exists():
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                # Truncate very large files
                if len(content) > 12000:
                    content = content[:12000] + f"\n\n[...truncated at 12000 chars — {filename}]"
                loaded[filename] = content
            except (IOError, OSError):
                pass
    return loaded


def fetch_github_context(filenames: list[str]) -> dict[str, str]:
    """Fetch context files from GitHub raw API (fallback)."""
    try:
        import urllib.request
        loaded = {}
        for filename in filenames:
            url = GITHUB_RAW.format(filename=filename)
            try:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    content = resp.read().decode("utf-8", errors="ignore")[:12000]
                    loaded[filename] = content
            except Exception:
                pass
        return loaded
    except Exception:
        return {}


def load_harmonizer_state(repo_root: Path | None) -> str | None:
    """Load or run harmonizer to get live system state."""
    # Try to load existing system_state.json
    if repo_root:
        for candidate in [
            repo_root / "system_state.json",
            HAIOS_ROOT / "system_state.json",
        ]:
            if candidate.exists():
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                    return json.dumps(data, indent=2)[:3000]
                except Exception:
                    pass

    # Try to run the harmonizer if available
    harmonizer = None
    if repo_root:
        for candidate in [
            repo_root / "tools" / "haios_harmonizer_v1_0.py",
            repo_root / "haios_harmonizer_v1_0.py",
            HAIOS_ROOT / "haios_harmonizer_v1_0.py",
        ]:
            if candidate.exists():
                harmonizer = candidate
                break

    if harmonizer and (repo_root / "system_state.json").exists():
        try:
            result = subprocess.run(
                [sys.executable, str(harmonizer),
                 "--state", str(repo_root / "system_state.json"),
                 "--output", "/tmp/"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                return result.stdout[:2000]
        except Exception:
            pass

    return None


def build_context_block(context: dict[str, str],
                         harmonizer_state: str | None) -> str:
    """Assemble context into a single block for the API call."""
    parts = []

    if harmonizer_state:
        parts.append(f"## LIVE SYSTEM STATE (haios_harmonizer)\n{harmonizer_state}")

    for filename, content in context.items():
        parts.append(f"## {filename}\n{content}")

    if not parts:
        parts.append("## CONTEXT\nNo local context loaded. Answering from training knowledge only.")

    return "\n\n---\n\n".join(parts)


# ── Claude API Call ───────────────────────────────────────────────────────────

def call_claude(prompt: str, context_block: str,
                stream: bool = True) -> str:
    """Call Claude API with context and prompt. Returns response text."""
    try:
        import anthropic
    except ImportError:
        raise SpecLoadFailed(
            "anthropic library not installed.\n"
            "Run: pip install anthropic --break-system-packages"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SpecLoadFailed(
            "ANTHROPIC_API_KEY not set.\n"
            "Run: export ANTHROPIC_API_KEY='sk-ant-...'\n"
            "Or add to ~/.zshrc"
        )

    client = anthropic.Anthropic(api_key=api_key)

    user_message = f"{context_block}\n\n---\n\n## QUERY\n{prompt}"

    if stream:
        print()  # blank line before response
        full_response = ""
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        ) as stream_obj:
            for text in stream_obj.text_stream:
                print(text, end="", flush=True)
                full_response += text
        print("\n")  # newline after streamed response
        return full_response
    else:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text


# ── Modes ─────────────────────────────────────────────────────────────────────

def mode_check(repo_root: Path | None) -> None:
    """Pre-flight system state report — no question needed."""
    print("\n[HAIOS CLI · System Check]\n")

    if repo_root:
        print(f"  Repo root    : {repo_root}")
        context = load_local_context(repo_root)
        print(f"  Context files: {', '.join(context.keys()) or 'none'}")
    else:
        print("  Repo root    : NOT FOUND — context will be limited")
        context = {}

    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    print(f"  API key      : {'SET ✓' if api_key else 'NOT SET ✗'}")

    # Check anthropic library
    try:
        import anthropic
        print(f"  anthropic    : installed ✓")
    except ImportError:
        print(f"  anthropic    : NOT INSTALLED ✗  →  pip install anthropic --break-system-packages")

    # Check harmonizer state
    harmonizer_state = load_harmonizer_state(repo_root)
    print(f"  Harmonizer   : {'state loaded ✓' if harmonizer_state else 'no state file found'}")

    # Quick system state query
    if api_key and context:
        print("\n  Running quick state query...\n")
        context_block = build_context_block(context, harmonizer_state)
        call_claude(
            "Give me a 5-line system state summary: "
            "active blockers, top carry item, corpus health, gate status, "
            "and single highest-priority next action.",
            context_block
        )
    elif not api_key:
        print("\n  Set ANTHROPIC_API_KEY to enable queries.\n")


def mode_ask(prompt: str, repo_root: Path | None,
             with_harmonizer: bool = False) -> None:
    """Answer a single question."""
    context = {}
    if repo_root:
        context = load_local_context(repo_root)

    # Fallback to GitHub if no local context
    if not context:
        print("  [Loading context from GitHub...] ", end="", flush=True)
        context = fetch_github_context(["CURRENT.md", "REGISTERED.md"])
        print("done" if context else "failed")

    harmonizer_state = load_harmonizer_state(repo_root) if with_harmonizer else None
    context_block = build_context_block(context, harmonizer_state)
    call_claude(prompt, context_block)


def mode_run(prompt: str, repo_root: Path | None) -> None:
    """Answer + identify and run the most relevant local tool."""
    # First answer the question
    mode_ask(prompt, repo_root, with_harmonizer=True)

    # Then identify if a tool should run
    tool_keywords = {
        "harmonizer": "haios_harmonizer_v1_0.py",
        "harmony":    "haios_harmonizer_v1_0.py",
        "validation": "run_acat_validation_suite_v1_0.py",
        "validate":   "run_acat_validation_suite_v1_0.py",
        "scanner":    "haios_drive_scanner_v1_0.py",
        "scan":       "haios_drive_scanner_v1_0.py",
        "gate":       "git_push_gate_v1_0.py",
        "push":       "git_push_gate_v1_0.py",
    }
    prompt_lower = prompt.lower()
    for keyword, tool_file in tool_keywords.items():
        if keyword in prompt_lower:
            tool_path = None
            if repo_root:
                for candidate in [
                    repo_root / "tools" / tool_file,
                    repo_root / tool_file,
                ]:
                    if candidate.exists():
                        tool_path = candidate
                        break
            if tool_path:
                print(f"  [RUN] python {tool_path} --smoke-test\n")
                result = subprocess.run(
                    [sys.executable, str(tool_path), "--smoke-test"],
                    capture_output=True, text=True
                )
                print(result.stdout.strip())
            else:
                print(f"  [RUN] Tool {tool_file} not found in repo. "
                      f"Add to tools/ directory.")
            break


def mode_chat(repo_root: Path | None) -> None:
    """Interactive multi-turn session."""
    try:
        import anthropic
    except ImportError:
        print("anthropic not installed. Run: pip install anthropic --break-system-packages")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ANTHROPIC_API_KEY not set.")
        return

    context = load_local_context(repo_root) if repo_root else {}
    if not context:
        context = fetch_github_context(["CURRENT.md", "REGISTERED.md"])

    harmonizer_state = load_harmonizer_state(repo_root)
    context_block = build_context_block(context, harmonizer_state)

    client = anthropic.Anthropic(api_key=api_key)
    history = []

    print("\n[HAIOS CLI · Chat Mode]  Type 'exit' or Ctrl+C to quit.\n")

    # Inject context as first system-level user message
    history.append({
        "role": "user",
        "content": f"{context_block}\n\n---\n\nContext loaded. Ready."
    })
    history.append({
        "role": "assistant",
        "content": "Context loaded. What do you need?"
    })

    while True:
        try:
            prompt = input("haios> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break

        if not prompt:
            continue
        if prompt.lower() in ("exit", "quit", "q"):
            break

        history.append({"role": "user", "content": prompt})

        print()
        full_response = ""
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history
        ) as stream_obj:
            for text in stream_obj.text_stream:
                print(text, end="", flush=True)
                full_response += text
        print("\n")

        history.append({"role": "assistant", "content": full_response})

        # Keep history bounded (last 10 turns)
        if len(history) > 22:
            history = history[:2] + history[-20:]


# ── Output + Report ───────────────────────────────────────────────────────────

def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"haios_cli_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def aggregate(run_result: dict) -> dict:
    return {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "zone":      TOOL_ZONE,
        "session":   TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **run_result,
    }


def print_summary(output: dict) -> None:
    pass  # CLI agent prints inline — no summary block needed


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    import tempfile
    try:
        # Test context loading
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "CURRENT.md").write_text(
                "# CURRENT.md\nN_total=629 · Mean LI=0.8632 · Gate 2 PASSED\n"
                "Active blocker: HAIOSCC_SECRET_ROTATED"
            )
            (root / "system_state.json").write_text(
                json.dumps({"system_harmony": 55.8, "molt_verdict": "BLOCKED"})
            )

            context = load_local_context(root)
            assert "CURRENT.md" in context, "CURRENT.md not loaded"
            assert "629" in context["CURRENT.md"], "Content not read correctly"

            state = load_harmonizer_state(root)
            assert state is not None, "system_state.json not loaded"
            assert "55.8" in state, "Harmony score not in state"

            context_block = build_context_block(context, state)
            assert "CURRENT.md" in context_block
            assert "LIVE SYSTEM STATE" in context_block

        # Test argument parsing
        parser = argparse.ArgumentParser()
        parser.add_argument("prompt", nargs="?", default="")
        parser.add_argument("--mode", default="ask")
        args = parser.parse_args(["test question", "--mode", "ask"])
        assert args.prompt == "test question"
        assert args.mode == "ask"

        # Test repo finder
        repo_root = find_repo_root()
        # repo_root may be None in test environment — that's OK

        print("✓ Smoke test PASSED — context loading, state loading, arg parsing verified")
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
        description="haios — HumanAIOS terminal CLI agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  haios "what is the current system harmony score?"
  haios "what are my open Zone 2 items?"
  haios "what should I push after today's session?"
  haios "what does the harmonizer say?" --mode run
  haios --mode check
  haios --mode chat
        """
    )
    parser.add_argument("prompt",       nargs="?", default="",
                        help="Question or prompt to send")
    parser.add_argument("--mode",       default="ask",
                        choices=["ask", "run", "check", "chat"],
                        help="Mode: ask (default), run, check, chat")
    parser.add_argument("--repo",       default=None,
                        help="Path to repo root (default: auto-detect)")
    parser.add_argument("--output", "-o", default=None,
                        help="Save Q&A log to this directory")
    parser.add_argument("--no-stream",  action="store_true",
                        help="Disable streaming (collect full response first)")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    # Resolve repo root
    repo_root = Path(args.repo).expanduser() if args.repo else find_repo_root()

    if args.mode == "check":
        mode_check(repo_root)
        return

    if args.mode == "chat":
        mode_chat(repo_root)
        return

    if not args.prompt:
        parser.print_help()
        print("\nTip: haios --mode check  → verify setup and system state")
        sys.exit(1)

    try:
        if args.mode == "run":
            mode_run(args.prompt, repo_root)
        else:
            mode_ask(args.prompt, repo_root)
    except SpecLoadFailed as e:
        print(f"\n[SETUP ERROR] {e}\n", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)


if __name__ == "__main__":
    main()

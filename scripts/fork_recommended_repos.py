#!/usr/bin/env python3
"""
Safe GitHub repository recommendation + optional fork helper.

Purpose:
- read a curated recommendations markdown file or newline-separated repo list
- print a human confirmation checklist
- optionally fork only user-selected repositories using GitHub CLI

Safety rules:
- never forks automatically
- requires --confirm before any fork attempt
- supports dry-run mode by default
- does not clone or import code
- does not modify licenses

Examples:
  python scripts/fork_recommended_repos.py --list docs/OPEN_SOURCE_REPO_RECOMMENDATIONS.md
  python scripts/fork_recommended_repos.py --repos modelcontextprotocol/python-sdk cli/cli
  python scripts/fork_recommended_repos.py --repos modelcontextprotocol/python-sdk --confirm
  python scripts/fork_recommended_repos.py --repos modelcontextprotocol/python-sdk --confirm --org my-org
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

REPO_RE = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\b")


def extract_repos_from_text(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in REPO_RE.findall(text):
        if match not in seen:
            seen.add(match)
            found.append(match)
    return found


def load_repos_from_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return extract_repos_from_text(text)


def normalize_repo_list(repos: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for repo in repos:
        repo = repo.strip()
        if not repo:
            continue
        if repo not in seen:
            seen.add(repo)
            out.append(repo)
    return out


def require_gh() -> None:
    if shutil.which("gh") is None:
        print("ERROR: GitHub CLI ('gh') is not installed or not on PATH.", file=sys.stderr)
        print("Install GitHub CLI and authenticate before forking.", file=sys.stderr)
        print("Suggested commands:", file=sys.stderr)
        print("  gh auth login", file=sys.stderr)
        print("  gh auth status", file=sys.stderr)
        raise SystemExit(2)


def check_gh_auth() -> None:
    result = subprocess.run(
        ["gh", "auth", "status"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("ERROR: GitHub CLI is not authenticated.", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print("Run: gh auth login", file=sys.stderr)
        raise SystemExit(2)


def build_fork_command(repo: str, org: str | None, remote: bool) -> list[str]:
    cmd = ["gh", "repo", "fork", repo]
    if org:
        cmd.extend(["--org", org])
    if remote:
        cmd.extend(["--remote=true"])
    else:
        cmd.extend(["--remote=false"])
    return cmd


def print_plan(repos: list[str], confirm: bool, org: str | None, remote: bool) -> None:
    print("Safe fork plan")
    print("==============")
    print(f"Repositories selected: {len(repos)}")
    for index, repo in enumerate(repos, start=1):
        print(f"  {index}. {repo}")
    print()
    print(f"Target org/account override: {org or '(default authenticated account)'}")
    print(f"Add git remotes after fork: {'yes' if remote else 'no'}")
    print(f"Fork execution enabled: {'yes' if confirm else 'no (dry-run only)'}")
    print()
    print("Safety checklist:")
    print("- Recommendations should be reviewed by a human first.")
    print("- Only selected repositories will be considered.")
    print("- No repositories will be cloned or imported by this script.")
    print("- No licenses will be changed.")
    print("- Forking only occurs when --confirm is supplied.")
    print()


def run_forks(repos: list[str], org: str | None, remote: bool, confirm: bool) -> int:
    print_plan(repos, confirm=confirm, org=org, remote=remote)

    if not confirm:
        print("Dry run only. Re-run with --confirm to execute forks.")
        for repo in repos:
            print("DRY-RUN:", " ".join(build_fork_command(repo, org, remote)))
        return 0

    require_gh()
    check_gh_auth()

    failures = 0
    for repo in repos:
        cmd = build_fork_command(repo, org, remote)
        print(f"Forking {repo} ...")
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            failures += 1
            print(f"FAILED: {repo}", file=sys.stderr)
        else:
            print(f"OK: {repo}")

    return 1 if failures else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Safe helper for forking selected recommended repositories")
    parser.add_argument(
        "--list",
        type=Path,
        help="Path to a markdown or text file containing repository references (for example docs/OPEN_SOURCE_REPO_RECOMMENDATIONS.md)",
    )
    parser.add_argument(
        "--repos",
        nargs="*",
        default=[],
        help="Explicit owner/repo values to consider for forking",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually execute gh repo fork. Without this flag, the script only performs a dry run.",
    )
    parser.add_argument(
        "--org",
        help="Optional GitHub organization/account to fork into",
    )
    parser.add_argument(
        "--remote",
        action="store_true",
        help="Add the fork as a git remote when gh performs the fork",
    )

    args = parser.parse_args()

    repos: list[str] = []
    repos.extend(args.repos)

    if args.list:
        if not args.list.exists():
            print(f"ERROR: file not found: {args.list}", file=sys.stderr)
            raise SystemExit(2)
        repos.extend(load_repos_from_file(args.list))

    repos = normalize_repo_list(repos)

    if not repos:
        print("ERROR: no repositories selected.", file=sys.stderr)
        print("Use --repos owner/repo ... or --list <file>.", file=sys.stderr)
        raise SystemExit(2)

    exit_code = run_forks(repos=repos, org=args.org, remote=args.remote, confirm=args.confirm)
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()

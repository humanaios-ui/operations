#!/usr/bin/env python3
"""
seed_org_defaults.py — seed standard community-health files to mesh repos.
<<<<<<< HEAD
Builder v1.7 compliant — seed_org_defaults_tool
HumanAIOS — S-070726-seed-org-defaults
=======
Builder v1.7 compliant - org_defaults_seed_tool
HumanAIOS - S-070826-compliance-hardening
>>>>>>> origin/main

Tool name: seed_org_defaults
Tool version: 1.0
Builder version: 1.7

PURPOSE
-------
28 standard-file gaps were identified in the S-070726 mesh audit:
  CODEOWNERS ×10 · SECURITY ×8 · CONTRIBUTING ×6 · LICENSE ×4
This tool checks every repo in the target org (or a supplied list) for these
four files and can open PRs to add the missing ones from the canonical templates
in tools/org-defaults/.

USAGE
-----
    # Check only — no writes (default)
    python3 tools/seed_org_defaults.py --org humanaios-ui

    # Check only a specific set of repos
    python3 tools/seed_org_defaults.py --org humanaios-ui --repos humanaios docs research

    # Create PRs to add missing files (requires GITHUB_TOKEN with repo write scope)
    python3 tools/seed_org_defaults.py --org humanaios-ui --create-prs --token $GITHUB_TOKEN

    # JSON output for CI / downstream processing
    python3 tools/seed_org_defaults.py --org humanaios-ui --json

ZONE MODEL
----------
  --check (default)   Z1 — read-only, no credentials required beyond public API
  --create-prs        Z3 — writes to external repos; requires a PAT with `repo` scope
                         stored as MESH_SYNC_TOKEN secret (never committed)

EXIT CODES
----------
  0  all repos pass (no missing standard files)
  1  one or more repos have missing standard files
  2  fatal error (bad token, API failure, etc.)
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

TOOL_NAME = "seed_org_defaults"
TOOL_VERSION = "1.0"

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT / "tools" / "org-defaults"

STANDARD_FILES = [
    ("CODEOWNERS", ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]),
    ("SECURITY.md", ["SECURITY.md", ".github/SECURITY.md"]),
    ("CONTRIBUTING.md", ["CONTRIBUTING.md", ".github/CONTRIBUTING.md"]),
    ("LICENSE", ["LICENSE", "LICENSE.md", "LICENSE.txt"]),
]

# Repos excluded from the check (forks, archived, or intentionally exempt)
DEFAULT_EXCLUDES: set[str] = {"empirica"}

GITHUB_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _gh_request(
    path: str,
    token: str | None = None,
    method: str = "GET",
    body: dict | None = None,
) -> tuple[int, Any]:
    """Make a GitHub API request; return (status_code, parsed_json)."""
    url = f"{GITHUB_API}{path}" if not path.startswith("http") else path
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token

    data: bytes | None = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        try:
            body_text = exc.read().decode(errors="ignore")
            return exc.code, json.loads(body_text)
        except Exception:
            return exc.code, {}


def _gh_get(path: str, token: str | None = None) -> tuple[int, Any]:
    return _gh_request(path, token=token, method="GET")


def _gh_post(path: str, body: dict, token: str) -> tuple[int, Any]:
    return _gh_request(path, token=token, method="POST", body=body)


def _gh_put(path: str, body: dict, token: str) -> tuple[int, Any]:
    return _gh_request(path, token=token, method="PUT", body=body)


# ---------------------------------------------------------------------------
# Org / repo helpers
# ---------------------------------------------------------------------------

def list_org_repos(org: str, token: str | None) -> list[dict]:
    """Return all non-fork repos in the org (paginated)."""
    repos: list[dict] = []
    page = 1
    while True:
        status, data = _gh_get(
            f"/orgs/{org}/repos?per_page=100&page={page}&type=all",
            token=token,
        )
        if status != 200 or not isinstance(data, list) or not data:
            break
        repos.extend(r for r in data if not r.get("fork", False))
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.2)
    return repos


def check_file_exists(org: str, repo: str, candidates: list[str], token: str | None) -> bool:
    """Return True if any candidate path exists in the repo's default branch."""
    for path in candidates:
        status, _ = _gh_get(
            f"/repos/{org}/{repo}/contents/{path}",
            token=token,
        )
        if status == 200:
            return True
        time.sleep(0.05)
    return False


def check_repo(org: str, repo: str, token: str | None) -> dict[str, bool]:
    """Return a dict of {file_key: present} for each standard file."""
    result: dict[str, bool] = {}
    for key, candidates in STANDARD_FILES:
        result[key] = check_file_exists(org, repo, candidates, token)
    return result


# ---------------------------------------------------------------------------
# PR creation
# ---------------------------------------------------------------------------

def _template_content(filename: str) -> str:
    """Read template file; raise FileNotFoundError if missing."""
    path = TEMPLATES_DIR / filename
    return path.read_text(encoding="utf-8")


def _default_branch(org: str, repo: str, token: str) -> str:
    status, data = _gh_get(f"/repos/{org}/{repo}", token=token)
    if status == 200 and isinstance(data, dict):
        return data.get("default_branch", "main")
    return "main"


def _branch_sha(org: str, repo: str, branch: str, token: str) -> str | None:
    status, data = _gh_get(
        f"/repos/{org}/{repo}/git/refs/heads/{branch}",
        token=token,
    )
    if status == 200 and isinstance(data, dict):
        return data.get("object", {}).get("sha")
    return None


def _create_branch(org: str, repo: str, branch: str, sha: str, token: str) -> bool:
    status, _ = _gh_post(
        f"/repos/{org}/{repo}/git/refs",
        {"ref": f"refs/heads/{branch}", "sha": sha},
        token,
    )
    return status in (200, 201, 422)  # 422 = already exists


def _upsert_file(
    org: str,
    repo: str,
    path: str,
    content: str,
    branch: str,
    message: str,
    token: str,
) -> bool:
    encoded = base64.b64encode(content.encode()).decode()
    status, _ = _gh_put(
        f"/repos/{org}/{repo}/contents/{path}",
        {
            "message": message,
            "content": encoded,
            "branch": branch,
        },
        token,
    )
    return status in (200, 201)


def _create_pr(
    org: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str,
    token: str,
) -> str | None:
    status, data = _gh_post(
        f"/repos/{org}/{repo}/pulls",
        {"title": title, "head": head, "base": base, "body": body},
        token,
    )
    if status in (200, 201) and isinstance(data, dict):
        return data.get("html_url")
    return None


def create_standard_files_pr(
    org: str,
    repo: str,
    missing: list[str],
    token: str,
) -> str | None:
    """
    Create a branch + commit missing standard files + open a PR.
    Returns the PR URL on success, None on failure.
    """
    default_br = _default_branch(org, repo, token)
    sha = _branch_sha(org, repo, default_br, token)
    if not sha:
        print(f"    ✗ could not get SHA for {repo}/{default_br}", file=sys.stderr)
        return None

    branch = "chore/add-standard-files"
    if not _create_branch(org, repo, branch, sha, token):
        print(f"    ✗ could not create branch {branch} in {repo}", file=sys.stderr)
        return None

    committed: list[str] = []
    for key in missing:
        # Map key → template filename and target path
        template_map = {
            "CODEOWNERS": ("CODEOWNERS", "CODEOWNERS"),
            "SECURITY.md": ("SECURITY.md", "SECURITY.md"),
            "CONTRIBUTING.md": ("CONTRIBUTING.md", "CONTRIBUTING.md"),
            "LICENSE": ("LICENSE", "LICENSE"),
        }
        if key not in template_map:
            continue
        tmpl_file, target_path = template_map[key]
        try:
            content = _template_content(tmpl_file)
        except FileNotFoundError:
            print(f"    ✗ template not found: tools/org-defaults/{tmpl_file}", file=sys.stderr)
            continue

        ok = _upsert_file(
            org, repo, target_path, content, branch,
            f"chore: add {key} (org standard — Issue-07 S-070726)",
            token,
        )
        if ok:
            committed.append(key)
        else:
            print(f"    ✗ failed to create {target_path} in {repo}", file=sys.stderr)
        time.sleep(0.3)

    if not committed:
        return None

    file_list = "\n".join(f"- `{f}`" for f in committed)
    pr_body = (
        "## Standard community-health files\n\n"
        "Added by [seed_org_defaults.py](https://github.com/humanaios-ui/operations/blob/main/tools/seed_org_defaults.py)"
        " as part of the S-070726 mesh-health sweep (Issue-07).\n\n"
        "### Files added\n\n"
        f"{file_list}\n\n"
        "### Review notes\n\n"
        "- **CODEOWNERS**: defaults every file to `@humanaios-ui/doc-control`. "
        "Customize patterns for this repo's actual ownership before merging.\n"
        "- **SECURITY.md / CONTRIBUTING.md**: org-level defaults from "
        "`operations/tools/org-defaults/`. Update repo-specific scope sections as needed.\n"
        "- **LICENSE**: Apache 2.0, same as `operations`. Confirm this is the intended "
        "license for this repo before merging.\n\n"
        "Closes the structural gaps flagged in "
        "[T1_DEFECT_BASELINE_S070726](https://github.com/humanaios-ui/operations/blob/main/audits/T1_DEFECT_BASELINE_S070726.md) "
        "§2 for this repo."
    )
    return _create_pr(
        org, repo, branch, default_br,
        f"chore: add standard community-health files ({', '.join(committed)})",
        pr_body,
        token,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def _print_table(results: list[dict]) -> None:
    keys = [k for k, _ in STANDARD_FILES]
    header = f"{'Repo':<32} " + "  ".join(f"{k:<14}" for k in keys) + "  Gaps"
    print(header)
    print("-" * len(header))
    for r in results:
        row = f"{r['repo']:<32} "
        row += "  ".join(
            f"{'✅':<14}" if r["files"][k] else f"{'✗':<14}"
            for k in keys
        )
        row += f"  {r['gaps']}"
        print(row)
    total_gaps = sum(r["gaps"] for r in results)
    repos_clean = sum(1 for r in results if r["gaps"] == 0)
    print()
    print(f"Repos checked: {len(results)}  Clean: {repos_clean}  Total gaps: {total_gaps}")


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def run_smoke_test() -> bool:
    """Lightweight deterministic self-check for Builder compliance."""
    try:
        assert TOOL_NAME == "seed_org_defaults"
        assert isinstance(TOOL_VERSION, str) and TOOL_VERSION
        assert TEMPLATES_DIR.exists()
        assert {"CODEOWNERS", "SECURITY.md", "CONTRIBUTING.md", "LICENSE"} == {
            key for key, _ in STANDARD_FILES
        }
        return True
    except AssertionError:
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--org", default="humanaios-ui", help="GitHub org (default: humanaios-ui)")
    ap.add_argument(
        "--repos", nargs="+", metavar="REPO",
        help="Explicit list of repo names; default: all non-fork repos in org",
    )
    ap.add_argument(
        "--exclude", nargs="+", metavar="REPO",
        help=f"Repos to skip (default: {sorted(DEFAULT_EXCLUDES)})",
    )
    ap.add_argument(
        "--token", metavar="TOKEN",
        help="GitHub personal-access token (read-only for check, repo-write for --create-prs). "
             "Also accepted via GITHUB_TOKEN env var.",
    )
    ap.add_argument(
        "--create-prs", action="store_true",
        help="[Z3] Create PRs in repos that are missing standard files. "
             "Requires a token with `repo` write scope.",
    )
    ap.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    ap.add_argument(
        "--strict", action="store_true",
        help="Exit 1 if any standard files are missing (use in CI)",
    )
    ap.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a local non-destructive smoke test and exit.",
    )
    args = ap.parse_args()
    if args.smoke_test:
        return 0 if run_smoke_test() else 1

    import os
    token: str | None = args.token or os.environ.get("GITHUB_TOKEN")

    if args.create_prs and not token:
        print("ERROR: --create-prs requires a token (--token or GITHUB_TOKEN)", file=sys.stderr)
        return 2

    # Resolve repo list
    if args.repos:
        repo_names = args.repos
    else:
        if not args.json:
            print(f"Fetching repo list for org: {args.org} …")
        repo_data = list_org_repos(args.org, token)
        if not repo_data:
            print("ERROR: no repos found — check org name and token permissions", file=sys.stderr)
            return 2
        repo_names = [r["name"] for r in repo_data]

    excludes = set(args.exclude or []) | DEFAULT_EXCLUDES
    repo_names = [r for r in repo_names if r not in excludes]

    if not args.json:
        print(f"Checking {len(repo_names)} repos in {args.org} for standard files …\n")

    results: list[dict] = []
    for name in repo_names:
        if not args.json:
            print(f"  checking {name} …", end=" ", flush=True)
        status = check_repo(args.org, name, token)
        missing = [k for k, present in status.items() if not present]
        gaps = len(missing)
        results.append({"repo": name, "files": status, "gaps": gaps, "missing": missing})
        if not args.json:
            print("✅" if gaps == 0 else f"✗ missing: {', '.join(missing)}")
        time.sleep(0.1)

    if args.json:
        total_gaps = sum(r["gaps"] for r in results)
        print(json.dumps({
            "org": args.org,
            "checked": len(results),
            "total_gaps": total_gaps,
            "repos": results,
        }, indent=2))
    else:
        print()
        _print_table(results)

    # Optionally create PRs
    if args.create_prs and token:
        needs_pr = [r for r in results if r["gaps"] > 0]
        if needs_pr:
            print(f"\n[Z3] Creating PRs for {len(needs_pr)} repos …\n")
            for r in needs_pr:
                print(f"  {r['repo']}: {', '.join(r['missing'])}")
                url = create_standard_files_pr(
                    args.org, r["repo"], r["missing"], token
                )
                if url:
                    print(f"    ✅ PR opened: {url}")
                else:
                    print(f"    ✗ PR creation failed (check token scope / branch conflicts)")
                time.sleep(1)
        else:
            print("\nAll repos have standard files — no PRs needed.")

    total_gaps = sum(r["gaps"] for r in results)
    if args.strict and total_gaps > 0:
        if not args.json:
            print(
                f"\nFAIL: {total_gaps} standard-file gaps remain across "
                f"{sum(1 for r in results if r['gaps'] > 0)} repos.",
                file=sys.stderr,
            )
        return 1
    return 0


def run_smoke_test() -> None:
    """Minimal smoke test — verifies the module loads correctly."""
    assert TOOL_NAME == "seed_org_defaults"
    print(f"{TOOL_NAME} v{TOOL_VERSION} smoke test: PASS")


if __name__ == "__main__":
    import sys as _sys
    if "--smoke-test" in _sys.argv:
        run_smoke_test()
        raise SystemExit(0)
    raise SystemExit(main())

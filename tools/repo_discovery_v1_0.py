#!/usr/bin/env python3
"""
repo_discovery — v1.0
Builder v1.7 compliant · Zone 1 tool
HumanAIOS · S-053126-repo-discovery

CLI tool for GitHub repository discovery and recommendation.

Given a source GitHub repository URL, this tool:
  1. Extracts metadata: name, language composition, topics, README keywords.
  2. Parses dependency files (package.json, requirements.txt, Pipfile, etc.)
     and finds repositories with overlapping or complementary libraries.
  3. Performs a lexical GitHub code search for key terms found in the source repo.
  4. Searches GitHub for repositories sharing topics, language, or keywords.
  5. Ranks results by a composite relevance score and emits a structured report.

Usage:
  python repo_discovery_v1_0.py --repo-url https://github.com/owner/repo
  python repo_discovery_v1_0.py --repo-url https://github.com/owner/repo --report out.json
  python repo_discovery_v1_0.py --smoke
  python repo_discovery_v1_0.py --serve   # FastMCP stdio mode

Environment:
  GITHUB_TOKEN — optional but strongly recommended to avoid API rate limits
                 (unauthenticated: 10 req/min search; authenticated: 30 req/min)
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Builder v1.7 constants
# ---------------------------------------------------------------------------
TOOL_NAME     = "repo_discovery"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "discovery"
TOOL_SESSION  = "S-053126-repo-discovery"
TOOL_ZONE     = 1

GITHUB_API_BASE = "https://api.github.com"

# Stop-words excluded from README keyword extraction
_STOP_WORDS = {
    "the", "and", "for", "that", "this", "with", "from", "are", "was",
    "not", "but", "have", "had", "its", "more", "than", "can", "will",
    "your", "all", "been", "also", "they", "their", "when", "there",
    "which", "what", "how", "any", "use", "used", "using", "each",
    "into", "our", "you", "get", "set", "new", "one", "two", "may",
    "just", "out", "very", "well", "such", "has", "via", "per",
    "make", "like", "good", "best", "code", "data", "file", "repo",
    "see", "run", "add", "api", "npm", "pip", "git", "etc",
}

# Dependency files recognized for extraction
DEP_FILES = [
    "package.json",
    "requirements.txt",
    "Pipfile",
    "pyproject.toml",
    "setup.cfg",
    "Gemfile",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "composer.json",
]

# Maximum candidates returned per search round
MAX_SEARCH_RESULTS = 10
# Max recommendations in final report
MAX_RECOMMENDATIONS = 20


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------
class SpecLoadFailed(Exception):
    """Raised when the input spec cannot be loaded or validated."""


class RepoParseError(Exception):
    """Raised when a GitHub URL cannot be parsed into owner/repo."""


# ---------------------------------------------------------------------------
# GitHub API helpers
# ---------------------------------------------------------------------------
def _github_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"{TOOL_NAME}/{TOOL_VERSION}",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    return headers


def _gh_get(path: str, params: dict | None = None, *, retries: int = 2) -> dict | list:
    """
    GET from the GitHub API.

    Returns the parsed JSON body.  On HTTP errors, returns a dict with
    ``_error`` and ``_status`` keys so callers can inspect without raising.
    """
    url = f"{GITHUB_API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=_github_headers())
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 403 and attempt < retries:
                # Rate-limit back-off
                time.sleep(2 ** attempt)
                continue
            body = ""
            try:
                body = exc.read().decode("utf-8")[:200]
            except Exception:  # noqa: BLE001
                pass
            return {"_error": str(exc), "_status": exc.code, "_body": body}
        except Exception as exc:  # noqa: BLE001
            return {"_error": str(exc), "_status": 0}
    return {"_error": "max retries exceeded", "_status": 429}


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------
def parse_repo_url(url: str) -> tuple[str, str]:
    """
    Extract (owner, repo) from a GitHub URL.

    Accepts:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - github.com/owner/repo
      - owner/repo  (shorthand)
    """
    url = url.strip().rstrip("/")
    # Strip .git suffix
    if url.endswith(".git"):
        url = url[:-4]

    # Full URL
    m = re.match(r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/?\s#]+)", url)
    if m:
        return m.group(1), m.group(2)

    # Shorthand owner/repo
    m2 = re.match(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)$", url)
    if m2:
        return m2.group(1), m2.group(2)

    raise RepoParseError(f"Cannot parse GitHub repository URL: {url!r}")


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------
def fetch_repo_metadata(owner: str, repo: str) -> dict:
    """Fetch core repository metadata from the GitHub API."""
    data = _gh_get(f"/repos/{owner}/{repo}")
    if "_error" in data:
        return {"_error": data["_error"], "_status": data.get("_status")}
    return {
        "full_name": data.get("full_name", f"{owner}/{repo}"),
        "description": data.get("description") or "",
        "html_url": data.get("html_url", ""),
        "primary_language": data.get("language") or "",
        "stargazers_count": data.get("stargazers_count", 0),
        "forks_count": data.get("forks_count", 0),
        "topics": data.get("topics", []),
        "open_issues_count": data.get("open_issues_count", 0),
        "default_branch": data.get("default_branch", "main"),
        "license": (data.get("license") or {}).get("spdx_id", ""),
        "pushed_at": data.get("pushed_at", ""),
        "size": data.get("size", 0),
    }


def fetch_language_stats(owner: str, repo: str) -> dict[str, int]:
    """Return bytes-per-language map for the repository."""
    data = _gh_get(f"/repos/{owner}/{repo}/languages")
    if isinstance(data, dict) and "_error" in data:
        return {}
    return data if isinstance(data, dict) else {}


def fetch_readme(owner: str, repo: str) -> str:
    """Return decoded README text, or empty string if unavailable."""
    data = _gh_get(f"/repos/{owner}/{repo}/readme")
    if "_error" in data:
        return ""
    content = data.get("content", "")
    encoding = data.get("encoding", "base64")
    if not content:
        return ""
    if encoding == "base64":
        try:
            return base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return ""
    return content


def fetch_file_content(owner: str, repo: str, path: str) -> str | None:
    """Return decoded content of a single file, or None if missing/error."""
    data = _gh_get(f"/repos/{owner}/{repo}/contents/{path}")
    if isinstance(data, dict) and "_error" in data:
        return None
    if not isinstance(data, dict):
        return None
    content = data.get("content", "")
    encoding = data.get("encoding", "base64")
    if not content:
        return ""
    if encoding == "base64":
        try:
            return base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            return None
    return content


# ---------------------------------------------------------------------------
# Keyword / dependency extraction
# ---------------------------------------------------------------------------
def extract_keywords(text: str, top_n: int = 15) -> list[str]:
    """
    Extract the most frequent meaningful words from free text (README etc.).

    Returns up to *top_n* words, lower-cased, sorted by frequency descending.
    """
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", text)
    freq: dict[str, int] = {}
    for w in words:
        lw = w.lower()
        if lw not in _STOP_WORDS:
            freq[lw] = freq.get(lw, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]


def parse_dependency_file(filename: str, content: str) -> list[str]:
    """
    Extract dependency/library names from common manifest formats.

    Returns a flat list of lowercase package names.
    """
    deps: list[str] = []
    fname = filename.lower()

    if fname == "package.json":
        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            return deps
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            for pkg in obj.get(section, {}):
                deps.append(pkg.lower().lstrip("@").split("/")[0])

    elif fname in ("requirements.txt", "pipfile"):
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "-", "[")):
                continue
            pkg = re.split(r"[=<>!;\s\[]", line)[0].strip()
            if pkg:
                deps.append(pkg.lower())

    elif fname == "pyproject.toml":
        for m in re.finditer(r'"([A-Za-z0-9_.-]+)\s*[>=<!]', content):
            deps.append(m.group(1).lower())

    elif fname == "setup.cfg":
        in_install = False
        for line in content.splitlines():
            if re.match(r"\[options\]", line):
                in_install = False
            if "install_requires" in line:
                in_install = True
                continue
            if in_install:
                if line.startswith(("[", " ") or line.startswith("\t")):
                    pkg = re.split(r"[=<>!;\s\[]", line.strip())[0].strip()
                    if pkg:
                        deps.append(pkg.lower())
                else:
                    in_install = False

    elif fname == "gemfile":
        for m in re.finditer(r"gem\s+['\"]([A-Za-z0-9_-]+)['\"]", content):
            deps.append(m.group(1).lower())

    elif fname == "go.mod":
        for m in re.finditer(r"^\s+([^\s]+)\s+v", content, re.MULTILINE):
            name = m.group(1).split("/")[-1]
            deps.append(name.lower())

    elif fname in ("pom.xml", "build.gradle"):
        for m in re.finditer(r"<artifactId>([^<]+)</artifactId>", content):
            deps.append(m.group(1).lower())

    elif fname == "cargo.toml":
        for m in re.finditer(r"^([A-Za-z0-9_-]+)\s*=", content, re.MULTILINE):
            deps.append(m.group(1).lower())

    elif fname == "composer.json":
        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            return deps
        for section in ("require", "require-dev"):
            for pkg in obj.get(section, {}):
                deps.append(pkg.split("/")[-1].lower())

    return list(dict.fromkeys(deps))  # deduplicate, preserve order


def fetch_dependencies(owner: str, repo: str) -> dict[str, list[str]]:
    """
    Try to fetch known dependency files and parse them.

    Returns a dict: {filename: [dep1, dep2, ...]}
    """
    found: dict[str, list[str]] = {}
    for dep_file in DEP_FILES:
        content = fetch_file_content(owner, repo, dep_file)
        if content is None:
            continue
        parsed = parse_dependency_file(dep_file, content)
        if parsed:
            found[dep_file] = parsed
    return found


# ---------------------------------------------------------------------------
# GitHub search
# ---------------------------------------------------------------------------
def search_repos_by_query(query: str) -> list[dict]:
    """
    Search GitHub repositories with the given query string.

    Returns a simplified list of repo dicts.
    """
    data = _gh_get("/search/repositories", {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": MAX_SEARCH_RESULTS,
    })
    if not isinstance(data, dict) or "_error" in data:
        return []
    items = data.get("items", [])
    return [
        {
            "full_name": r.get("full_name", ""),
            "html_url": r.get("html_url", ""),
            "description": r.get("description") or "",
            "primary_language": r.get("language") or "",
            "stargazers_count": r.get("stargazers_count", 0),
            "topics": r.get("topics", []),
            "pushed_at": r.get("pushed_at", ""),
        }
        for r in items
        if isinstance(r, dict)
    ]


def lexical_code_search(keywords: list[str], language: str) -> list[dict]:
    """
    Perform GitHub lexical code search for the top keywords.

    Returns a list of repo full_names that contain matching files.
    """
    if not keywords:
        return []

    # Use the top 3 most distinctive keywords joined with OR
    terms = " OR ".join(f'"{kw}"' for kw in keywords[:3])
    query = terms
    if language:
        query += f" language:{language}"

    data = _gh_get("/search/code", {
        "q": query,
        "per_page": MAX_SEARCH_RESULTS,
    })
    if not isinstance(data, dict) or "_error" in data:
        return []

    seen: dict[str, dict] = {}
    for item in data.get("items", []):
        if not isinstance(item, dict):
            continue
        rrepo = item.get("repository", {})
        fname = rrepo.get("full_name", "")
        if fname and fname not in seen:
            seen[fname] = {
                "full_name": fname,
                "html_url": rrepo.get("html_url", ""),
                "description": rrepo.get("description") or "",
                "primary_language": "",
                "stargazers_count": 0,
                "topics": [],
                "pushed_at": "",
                "matched_file": item.get("path", ""),
            }
    return list(seen.values())


def search_by_dependency(dep_name: str, language: str) -> list[dict]:
    """Search for repositories that use a given dependency package name."""
    query = f'"{dep_name}"'
    if language:
        query += f" language:{language}"
    return search_repos_by_query(query)


# ---------------------------------------------------------------------------
# Scoring / ranking
# ---------------------------------------------------------------------------
def _language_score(candidate_lang: str, source_lang: str) -> float:
    if not source_lang or not candidate_lang:
        return 0.0
    return 3.0 if candidate_lang.lower() == source_lang.lower() else 0.0


def _topic_score(candidate_topics: list[str], source_topics: list[str]) -> float:
    if not source_topics or not candidate_topics:
        return 0.0
    src = {t.lower() for t in source_topics}
    cand = {t.lower() for t in candidate_topics}
    return 2.0 * len(src & cand)


def _keyword_score(candidate_text: str, source_keywords: list[str]) -> float:
    if not source_keywords or not candidate_text:
        return 0.0
    lower_text = candidate_text.lower()
    hits = sum(1 for kw in source_keywords if kw.lower() in lower_text)
    return float(hits)


def _dep_score(candidate_full_name: str, dep_repos: set[str]) -> float:
    return 4.0 if candidate_full_name in dep_repos else 0.0


def score_candidates(
    candidates: list[dict],
    source_meta: dict,
    source_keywords: list[str],
    dep_repos: set[str],
    *,
    source_full_name: str,
) -> list[dict]:
    """
    Score and sort candidate repositories by relevance.

    Scoring weights:
      +3   primary language match
      +2   per overlapping topic (cap: 10)
      +1   per README keyword found in description or name (cap: 5)
      +4   found via dependency search
    """
    source_lang = source_meta.get("primary_language", "")
    source_topics = source_meta.get("topics", [])

    seen: dict[str, dict] = {}
    for c in candidates:
        fn = c.get("full_name", "")
        if not fn or fn == source_full_name:
            continue
        if fn in seen:
            # Merge signals: keep the one with the higher running score
            continue
        seen[fn] = c

    scored: list[dict] = []
    for fn, c in seen.items():
        cand_text = f"{c.get('full_name', '')} {c.get('description', '')}"
        lang_s = _language_score(c.get("primary_language", ""), source_lang)
        topic_s = min(_topic_score(c.get("topics", []), source_topics), 10.0)
        kw_s = min(_keyword_score(cand_text, source_keywords), 5.0)
        dep_s = _dep_score(fn, dep_repos)
        total = lang_s + topic_s + kw_s + dep_s

        scored.append({
            **c,
            "_score": round(total, 2),
            "_score_breakdown": {
                "language": lang_s,
                "topics": topic_s,
                "keywords": kw_s,
                "dependency": dep_s,
            },
        })

    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored[:MAX_RECOMMENDATIONS]


# ---------------------------------------------------------------------------
# Core run
# ---------------------------------------------------------------------------
def run(spec: dict) -> dict:
    """
    Discover and recommend repositories similar to the given source repo URL.

    spec keys:
      repo_url   — GitHub repository URL (required)
      top_n      — max recommendations (default 20)
      skip_deps  — skip dependency file fetching (bool, default False)
      skip_code_search — skip lexical code search (bool, default False)
    """
    started = datetime.now(timezone.utc).isoformat()
    warnings: list[str] = []

    # --- 1. Parse URL ---
    repo_url = spec.get("repo_url", "").strip()
    if not repo_url:
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "FAIL",
            "error": "repo_url is required",
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    try:
        owner, repo = parse_repo_url(repo_url)
    except RepoParseError as exc:
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "FAIL",
            "error": str(exc),
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    source_full_name = f"{owner}/{repo}"

    # --- 2. Fetch metadata ---
    meta = fetch_repo_metadata(owner, repo)
    if "_error" in meta:
        return {
            "tool_name": TOOL_NAME,
            "tool_version": TOOL_VERSION,
            "status": "FAIL",
            "error": f"GitHub API error fetching {source_full_name}: {meta['_error']}",
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    # --- 3. Language stats ---
    lang_stats = fetch_language_stats(owner, repo)
    total_bytes = sum(lang_stats.values()) or 1
    language_composition = {
        lang: round(100 * b / total_bytes, 1)
        for lang, b in sorted(lang_stats.items(), key=lambda x: x[1], reverse=True)
    }

    # --- 4. README keywords ---
    readme_text = fetch_readme(owner, repo)
    readme_keywords = extract_keywords(readme_text)

    # Combine keywords with topics for richer searches
    all_keywords = list(dict.fromkeys(meta.get("topics", []) + readme_keywords))

    # --- 5. Dependency analysis ---
    dep_map: dict[str, list[str]] = {}
    dep_repos: set[str] = set()
    if not spec.get("skip_deps", False):
        dep_map = fetch_dependencies(owner, repo)
        all_deps = [dep for deps in dep_map.values() for dep in deps]
        # Search repos using the most common dependencies (top 5)
        primary_lang = meta.get("primary_language", "")
        for dep in all_deps[:5]:
            for candidate in search_by_dependency(dep, primary_lang):
                fn = candidate.get("full_name", "")
                if fn and fn != source_full_name:
                    dep_repos.add(fn)

    if dep_map and not dep_repos:
        warnings.append("Dependency search returned no matches (rate limit or no results)")

    # --- 6. Repository search (topics + language + keywords) ---
    all_candidates: list[dict] = []

    primary_lang = meta.get("primary_language", "")
    topics = meta.get("topics", [])

    # Search by each topic
    for topic in topics[:4]:
        results = search_repos_by_query(f"topic:{topic}")
        all_candidates.extend(results)

    # Search by primary language + top keywords
    if primary_lang and all_keywords:
        kw_query = " ".join(all_keywords[:5]) + f" language:{primary_lang}"
        all_candidates.extend(search_repos_by_query(kw_query))

    # Fallback: search by description keywords only
    if all_keywords and not all_candidates:
        all_candidates.extend(search_repos_by_query(" ".join(all_keywords[:5])))

    # --- 7. Lexical code search ---
    if not spec.get("skip_code_search", False) and readme_keywords:
        code_results = lexical_code_search(readme_keywords[:8], primary_lang)
        all_candidates.extend(code_results)
        if not code_results:
            warnings.append("Lexical code search returned no results (may be rate-limited)")

    # Also add dep-matched repos as candidates (we need their full metadata)
    for fn in dep_repos:
        all_candidates.append({
            "full_name": fn,
            "html_url": f"https://github.com/{fn}",
            "description": "",
            "primary_language": primary_lang,
            "stargazers_count": 0,
            "topics": [],
            "pushed_at": "",
        })

    # --- 8. Score and rank ---
    recommendations = score_candidates(
        all_candidates,
        meta,
        all_keywords,
        dep_repos,
        source_full_name=source_full_name,
    )

    finished = datetime.now(timezone.utc).isoformat()
    status = "WARN" if warnings else "PASS"
    if not recommendations:
        warnings.append("No recommendations found — try with a GITHUB_TOKEN for higher rate limits")
        status = "WARN"

    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "status": status,
        "started_at": started,
        "finished_at": finished,
        "source_repo": {
            **meta,
            "owner": owner,
            "repo": repo,
            "language_composition": language_composition,
            "readme_keywords": readme_keywords,
            "dependencies": dep_map,
        },
        "search_metadata": {
            "topics_searched": topics,
            "keywords_used": all_keywords[:10],
            "dependency_files_found": list(dep_map.keys()),
            "dep_repos_found": len(dep_repos),
            "raw_candidates": len(all_candidates),
        },
        "recommendations": recommendations,
        "warnings": warnings,
        "summary": {
            "source": source_full_name,
            "recommendations_count": len(recommendations),
            "dependency_files_found": len(dep_map),
            "warnings": len(warnings),
        },
    }


# ---------------------------------------------------------------------------
# Input / output helpers
# ---------------------------------------------------------------------------
def load_input(path: str | None) -> dict:
    """Load input spec from a JSON file or stdin."""
    if path is None or path == "-":
        raw = sys.stdin.read()
    else:
        if not os.path.isfile(path):
            raise SpecLoadFailed(f"Input file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    if not raw.strip():
        raise SpecLoadFailed("Empty input")
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecLoadFailed(f"Invalid JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise SpecLoadFailed("Input JSON must be an object")
    return spec


def write_report(out: dict, path: str) -> None:
    """Write report JSON atomically."""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
        f.write("\n")
    os.replace(tmp, path)


def print_summary(out: dict) -> None:
    """Human-readable summary printed to stdout."""
    bar = "=" * 68
    print(f"\n{bar}")
    print(f"  {TOOL_NAME} v{TOOL_VERSION}")
    print(f"  Status  : {out.get('status', 'UNKNOWN')}")

    src = out.get("source_repo", {})
    if src:
        print(f"  Source  : {src.get('full_name', '?')}  [{src.get('primary_language', '?')}]")
        lc = src.get("language_composition", {})
        if lc:
            lc_str = "  ".join(f"{l}:{p}%" for l, p in list(lc.items())[:4])
            print(f"  Langs   : {lc_str}")
        print(f"  Topics  : {', '.join(src.get('topics', [])) or '(none)'}")
        kws = src.get("readme_keywords", [])
        print(f"  Keywords: {', '.join(kws[:8]) or '(none)'}")
        deps = src.get("dependencies", {})
        if deps:
            print(f"  Dep files: {', '.join(deps.keys())}")

    print()
    recs = out.get("recommendations", [])
    if recs:
        print(f"  Top {len(recs)} Recommendations (sorted by relevance score):")
        print()
        for i, r in enumerate(recs, 1):
            score = r.get("_score", 0)
            lang  = r.get("primary_language", "") or "?"
            stars = r.get("stargazers_count", 0)
            desc  = (r.get("description") or "")[:60]
            print(f"  {i:>2}. [{score:>5.1f}] {r['full_name']:<42} [{lang}] ★{stars}")
            if desc:
                print(f"       {desc}")
            breakdown = r.get("_score_breakdown", {})
            parts = [f"{k}={v}" for k, v in breakdown.items() if v]
            if parts:
                print(f"       score: {', '.join(parts)}")
            print()
    else:
        print("  No recommendations found.")

    if out.get("warnings"):
        print("  Warnings:")
        for w in out["warnings"]:
            print(f"    ⚠  {w}")
    print(f"{bar}\n")


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
def run_smoke_test() -> bool:
    """Quick self-test that does NOT make live network requests."""
    passed = True

    # 1. URL parsing
    tests = [
        ("https://github.com/openai/gpt-4", ("openai", "gpt-4")),
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("github.com/user/project", ("user", "project")),
        ("user/project", ("user", "project")),
    ]
    for url, expected in tests:
        got = parse_repo_url(url)
        if got != expected:
            print(f"[smoke] FAIL parse_repo_url({url!r}): expected {expected}, got {got}",
                  file=sys.stderr)
            passed = False

    try:
        parse_repo_url("not-a-url")
        print("[smoke] FAIL: expected RepoParseError for 'not-a-url'", file=sys.stderr)
        passed = False
    except RepoParseError:
        pass

    # 2. Keyword extraction
    text = "FastAPI is a modern web framework for building APIs with Python based on standard hints"
    kws = extract_keywords(text, top_n=5)
    if not kws:
        print("[smoke] FAIL extract_keywords returned empty", file=sys.stderr)
        passed = False
    if "fastapi" not in kws and "python" not in kws:
        print(f"[smoke] FAIL extract_keywords missing expected words: {kws}", file=sys.stderr)
        passed = False

    # 3. Dependency parsing
    pkg_json = json.dumps({
        "dependencies": {"express": "^4.18.0", "lodash": "^4.17.21"},
        "devDependencies": {"jest": "^29.0.0"},
    })
    deps = parse_dependency_file("package.json", pkg_json)
    if "express" not in deps or "lodash" not in deps or "jest" not in deps:
        print(f"[smoke] FAIL parse_dependency_file(package.json): {deps}", file=sys.stderr)
        passed = False

    req_txt = "requests==2.31.0\nfastapi>=0.110.0\n# comment\n-r base.txt\n"
    deps2 = parse_dependency_file("requirements.txt", req_txt)
    if "requests" not in deps2 or "fastapi" not in deps2:
        print(f"[smoke] FAIL parse_dependency_file(requirements.txt): {deps2}", file=sys.stderr)
        passed = False

    # 4. Scoring (no network)
    candidates = [
        {"full_name": "owner/similar", "description": "python fastapi", "primary_language": "Python",
         "stargazers_count": 100, "topics": ["fastapi", "rest"], "pushed_at": ""},
        {"full_name": "owner/other", "description": "golang service", "primary_language": "Go",
         "stargazers_count": 50, "topics": [], "pushed_at": ""},
        {"full_name": "source/repo", "description": "source", "primary_language": "Python",
         "stargazers_count": 10, "topics": [], "pushed_at": ""},
    ]
    source_meta = {"primary_language": "Python", "topics": ["fastapi", "rest"]}
    ranked = score_candidates(
        candidates, source_meta, ["python", "fastapi"],
        dep_repos={"owner/similar"},
        source_full_name="source/repo",
    )
    if not ranked:
        print("[smoke] FAIL score_candidates returned empty list", file=sys.stderr)
        passed = False
    elif ranked[0]["full_name"] != "owner/similar":
        print(f"[smoke] FAIL top candidate should be owner/similar, got {ranked[0]['full_name']}",
              file=sys.stderr)
        passed = False

    # 5. Missing repo_url
    result = run({})
    if result.get("status") != "FAIL":
        print("[smoke] FAIL run({}) should return status=FAIL", file=sys.stderr)
        passed = False

    if passed:
        print("[smoke] PASSED", file=sys.stderr)
    return passed


# ---------------------------------------------------------------------------
# MCP surface (optional — requires fastmcp)
# ---------------------------------------------------------------------------
def _build_mcp():
    try:
        from fastmcp import FastMCP  # noqa: PLC0415
    except ImportError:
        return None

    mcp = FastMCP(TOOL_NAME)

    @mcp.tool(
        name=TOOL_NAME,
        description=(
            "Discover and recommend GitHub repositories similar to a given source repo. "
            "spec: {repo_url, top_n?, skip_deps?, skip_code_search?}"
        ),
    )
    def repo_discovery(spec: dict) -> dict:
        """MCP wrapper around run()."""
        return run(spec)

    return mcp


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(
        description=f"{TOOL_NAME} v{TOOL_VERSION} — GitHub repository discovery & recommendation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --repo-url https://github.com/tiangolo/fastapi
  %(prog)s --repo-url owner/repo --report reports/discovery.json
  %(prog)s --input spec.json
  %(prog)s --smoke
  %(prog)s --serve
        """,
    )
    p.add_argument("--repo-url", metavar="URL",
                   help="GitHub repository URL to analyse (e.g. https://github.com/owner/repo)")
    p.add_argument("--input", "-i", metavar="FILE",
                   help="Path to JSON spec file (alternative to --repo-url)")
    p.add_argument("--report", "-o", default=f"reports/{TOOL_NAME}.json",
                   metavar="FILE", help="Output report path (default: reports/repo_discovery.json)")
    p.add_argument("--top-n", type=int, default=MAX_RECOMMENDATIONS,
                   help=f"Maximum recommendations to return (default: {MAX_RECOMMENDATIONS})")
    p.add_argument("--skip-deps", action="store_true",
                   help="Skip dependency file analysis")
    p.add_argument("--skip-code-search", action="store_true",
                   help="Skip lexical code search (saves GitHub API quota)")
    p.add_argument("--smoke", action="store_true",
                   help="Run self-test (no network) and exit")
    p.add_argument("--serve", action="store_true",
                   help="Run as FastMCP server over stdio")
    args = p.parse_args()

    if args.smoke:
        sys.exit(0 if run_smoke_test() else 1)

    if args.serve:
        mcp = _build_mcp()
        if mcp is None:
            print("ERROR: fastmcp not installed. Run: pip install fastmcp", file=sys.stderr)
            sys.exit(1)
        mcp.run()
        return

    # Build spec from args or input file
    if args.input:
        try:
            spec = load_input(args.input)
        except SpecLoadFailed as exc:
            print(f"SPEC_LOAD_FAILED: {exc}", file=sys.stderr)
            sys.exit(2)
    elif args.repo_url:
        spec = {"repo_url": args.repo_url}
    else:
        p.error("Either --repo-url or --input is required")

    # Apply CLI overrides
    if args.top_n != MAX_RECOMMENDATIONS:
        spec["top_n"] = args.top_n
    if args.skip_deps:
        spec["skip_deps"] = True
    if args.skip_code_search:
        spec["skip_code_search"] = True

    out = run(spec)
    write_report(out, args.report)
    print_summary(out)
    print(f"Report written to: {args.report}")
    sys.exit(0 if out["status"] in ("PASS", "WARN") else 1)


if __name__ == "__main__":
    main()

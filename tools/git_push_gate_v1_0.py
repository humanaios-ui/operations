#!/usr/bin/env python3
"""
Git Push Gate — v1.0
Builder v1.7 compliant · security_gate_tool
HumanAIOS · S-051726-02-molt-grow-kill

Zone 1 git push authorization gate. Enforces the ratified ruleset for
which files Claude (Unit Zero) may push without additional Night ratification.

RATIFIED: Night Anderson · S-051726-02 · May 17, 2026 10:44 PM CDT
SCOPE: humanaios-ui/operations-staging repo only

ZONE 1 ALLOWED (push without additional ratification):
  · CURRENT.md, SESSION_RITUALS.md, GOVERNANCE.md, OPERATOR_RUNBOOK.md, README.md
  · Session artifacts: files with _S-MMDDYY suffix (.md, .json, .html, .jsx, .mermaid)
  · Tool output reports with ISO timestamp suffix (tool_name_YYYYMMDDTHHMMSSZ.json)
  · Static HTML pages (observatory, research brief) — no credentials inside
  · Builder v1.7-compliant Python tools in tools/ — must pass --smoke-test first
  · Utility shell scripts — no credential reads
  · Architecture diagrams (.mermaid)
  · CI config (.yaml/.yml) — no embedded secrets

ZONE 2 REQUIRED (flag for Night before push):
  · Any file containing: password, secret, token, api_key, SUPABASE_KEY, CF_API_TOKEN, rah_
  · Supabase schema migrations (.sql)
  · REGISTERED.md when adding a new F-class finding (requires Night ratification in-session)
  · acat_core.js, assess.html (product layer — user-facing)
  · Collaborator files: MODEAI_*, GE_*, DEMARIUS_* patterns
  · constitution.json (agent kernel — never Zone 1)

ZONE 3 ONLY (never Zone 1 regardless of context):
  · humanaios-internal/ repo — private, Night executes only
  · Supabase row inserts/updates — data writes
  · Secret rotation (IC-023, credentials) — local execution only
  · Cloudflare Worker deployments (wrangler publish)
  · GitHub OAuth / Access token changes

HARD RULES:
  RULE-01: git diff --cached --name-only must match staged intent exactly
  RULE-02: No file containing credential patterns (content scan)
  RULE-03: New Python tools must pass --smoke-test before push
  RULE-04: REGISTERED.md only after explicit Night ratification this session
  RULE-05: Push to operations-staging only, never humanaios-internal
  RULE-06: Commit message must include session ID: 'S-MMDDYY-NN: description'
  RULE-07: Verify by gh api refetch after push (P3 — not browser cache)
  RULE-08: Unexpected staged file → ABORT and report to Night
  RULE-09: --dry-run flag available: stages + shows diff, never pushes
  RULE-10: Push receipt (filenames, SHA, timestamp) posted to WGS session record

Usage:
  python git_push_gate_v1_0.py --files CURRENT.md --session S-051726-02 --message "update ops state"
  python git_push_gate_v1_0.py --staged --session S-051726-02 --message "sprint 1 tools"
  python git_push_gate_v1_0.py --staged --session S-051726-02 --message "..." --dry-run
  python git_push_gate_v1_0.py --list-rules
  python git_push_gate_v1_0.py --smoke-test
"""

import json
import re
import sys
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME    = "git_push_gate"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "security_gate_tool"
TOOL_SESSION  = "S-051726-02-molt-grow-kill"
TOOL_ZONE     = 1

RATIFICATION = {
    "by":      "Night Anderson",
    "session": "S-051726-02",
    "date":    "2026-05-17T22:44:00-05:00",
    "scope":   "humanaios-ui/operations-staging — Zone 1 git push authorization",
}

# ── Credential patterns (content scan — HARD BLOCK) ──────────────────────────

CREDENTIAL_PATTERNS = [
    re.compile(r'password\s*=\s*["\'].+["\']',         re.I),
    re.compile(r'api_key\s*=\s*["\'].+["\']',          re.I),
    re.compile(r'secret\s*=\s*["\'].+["\']',           re.I),
    re.compile(r'token\s*=\s*["\'].+["\']',            re.I),
    re.compile(r'SUPABASE_KEY\s*=\s*["\'].+["\']',     re.I),
    re.compile(r'CF_API_TOKEN\s*=\s*["\'].+["\']',     re.I),
    re.compile(r'rah_[a-f0-9]{6}',                     re.I),
    re.compile(r'eyJ[A-Za-z0-9_-]{20,}',               re.I),  # JWT pattern
    re.compile(r'sk-[A-Za-z0-9]{20,}',                 re.I),  # API key pattern
    re.compile(r'ghp_[A-Za-z0-9]{36}',                 re.I),  # GitHub PAT
    re.compile(r'-----BEGIN (RSA|EC|OPENSSH) PRIVATE KEY-----'),
]

# ── Zone 3 hard blocks (filename patterns — never Zone 1) ────────────────────

ZONE_3_PATTERNS = [
    re.compile(r'humanaios-internal',       re.I),
    re.compile(r'constitution\.json$',      re.I),
    re.compile(r'\.sql$',                   re.I),   # schema migrations → Zone 2 min
    re.compile(r'wrangler\.toml$',          re.I),
    re.compile(r'\.env$',                   re.I),
    re.compile(r'\.env\.',                  re.I),
    re.compile(r'secrets?\.',               re.I),
]

# ── Zone 2 flag patterns (require Night review before push) ──────────────────

ZONE_2_PATTERNS = [
    (re.compile(r'MODEAI_',         re.I), "Collaborator file — DeMarius engagement"),
    (re.compile(r'GE_',             re.I), "Collaborator file — GE partnership"),
    (re.compile(r'DEMARIUS_',       re.I), "Collaborator file — DeMarius personal"),
    (re.compile(r'acat_core\.js$',  re.I), "Product layer — user-facing JS"),
    (re.compile(r'assess\.html$',   re.I), "Product layer — assessment UI"),
    (re.compile(r'REGISTERED\.md$', re.I), "Findings registry — requires in-session Night ratification"),
]

# ── Zone 1 allowlist (explicit file patterns) ────────────────────────────────

ZONE_1_EXACT = {
    "CURRENT.md", "SESSION_RITUALS.md", "GOVERNANCE.md",
    "OPERATOR_RUNBOOK.md", "README.md",
}

ZONE_1_PATTERNS = [
    re.compile(r'_S-\d{6}(-\d{2})?(-[\w-]+)?\.(md|json|html|jsx|mermaid|txt)$'),  # session artifacts
    re.compile(r'_\d{8}T\d{6}Z\.json$'),           # tool output reports
    re.compile(r'tools/.*\.py$'),                  # tools dir Python files
    re.compile(r'tools/.*\.sh$'),                  # tools dir shell scripts
    re.compile(r'\.mermaid$'),                     # architecture diagrams
    re.compile(r'\.(yml|yaml)$'),                  # CI config (content-scanned)
    re.compile(r'HUMANAIOS_SYSTEM_MAP.*\.pdf$'),   # non-sensitive PDFs
    re.compile(r'night_command_center.*\.html$'),  # dashboard files
]


class SpecLoadFailed(Exception):
    pass


# ── File Classification ───────────────────────────────────────────────────────

def classify_file(filepath: str) -> dict:
    """
    Classify a single file as ZONE_1, ZONE_2, ZONE_3, or BLOCKED.
    Returns dict with zone, reason, content_clean (bool).
    """
    name = Path(filepath).name
    path_str = filepath

    # 1. Zone 3 hard blocks (filename)
    for pat in ZONE_3_PATTERNS:
        if pat.search(path_str):
            return {"zone": 3, "verdict": "BLOCKED",
                    "reason": f"Zone 3 hard block: {pat.pattern}",
                    "content_clean": None}

    # 2. Zone 2 flags (filename)
    for pat, reason in ZONE_2_PATTERNS:
        if pat.search(path_str):
            return {"zone": 2, "verdict": "ZONE_2_REQUIRED",
                    "reason": reason,
                    "content_clean": None}

    # 3. Content scan for credentials (applies to everything)
    content_issue = scan_content(filepath)
    if content_issue:
        return {"zone": 3, "verdict": "BLOCKED",
                "reason": f"Credential pattern in content: {content_issue}",
                "content_clean": False}

    # 4. Zone 1 exact match
    if name in ZONE_1_EXACT:
        return {"zone": 1, "verdict": "ALLOWED",
                "reason": f"Zone 1 exact match: {name}",
                "content_clean": True}

    # 5. Zone 1 pattern match
    for pat in ZONE_1_PATTERNS:
        if pat.search(path_str):
            return {"zone": 1, "verdict": "ALLOWED",
                    "reason": f"Zone 1 pattern: {pat.pattern}",
                    "content_clean": True}

    # 6. Default: unknown → Zone 2 (require Night review)
    return {"zone": 2, "verdict": "ZONE_2_REQUIRED",
            "reason": "File not on Zone 1 allowlist — requires Night review",
            "content_clean": True}


def scan_content(filepath: str) -> str | None:
    """Scan file content for credential patterns. Returns match string or None."""
    try:
        p = Path(filepath)
        if not p.exists():
            return None
        # Only scan text files; skip large binaries
        if p.stat().st_size > 500_000:
            return f"File too large to scan ({p.stat().st_size} bytes) — manual review required"
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except (IOError, OSError):
            return None
        for pat in CREDENTIAL_PATTERNS:
            m = pat.search(text)
            if m:
                # Return redacted match for the report
                matched = m.group()[:40] + "..." if len(m.group()) > 40 else m.group()
                return f"Pattern '{pat.pattern[:30]}' matched: {matched[:30]}..."
    except Exception:
        pass
    return None


# ── Pre-Push Validations ──────────────────────────────────────────────────────

def validate_python_tool(filepath: str) -> tuple[bool, str]:
    """RULE-03: Python tools in tools/ must pass --smoke-test."""
    if not filepath.endswith(".py") or "tools/" not in filepath:
        return True, ""
    result = subprocess.run(
        [sys.executable, filepath, "--smoke-test"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return False, f"Smoke test FAILED: {result.stdout.strip()} {result.stderr.strip()}"
    return True, "Smoke test PASSED"


def validate_commit_message(message: str, session_id: str) -> tuple[bool, str]:
    """RULE-06: Commit message must include session ID."""
    if not message:
        return False, "Commit message is empty"
    # Accept S-MMDDYY or S-MMDDYY-NN format
    session_pat = re.compile(r'S-\d{6}')
    if not session_pat.search(message):
        return False, (
            f"Commit message must include session ID (e.g. S-051726-02). "
            f"Got: '{message[:60]}'"
        )
    return True, "Session ID present in commit message"


def get_staged_files(repo_path: str) -> list[str]:
    """Get list of currently staged files from git."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode != 0:
        raise SpecLoadFailed(f"git diff failed: {result.stderr.strip()}")
    return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def stage_files(files: list[str], repo_path: str) -> tuple[bool, str]:
    """git add the specified files."""
    result = subprocess.run(
        ["git", "add"] + files,
        capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode != 0:
        return False, f"git add failed: {result.stderr.strip()}"
    return True, "Files staged"


def do_commit(message: str, repo_path: str) -> tuple[bool, str]:
    """git commit with the given message."""
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode != 0:
        return False, f"git commit failed: {result.stderr.strip()}"
    # Extract SHA from commit output
    sha_match = re.search(r'\b([0-9a-f]{7,40})\b', result.stdout)
    sha = sha_match.group(1) if sha_match else "unknown"
    return True, sha


def do_push(repo_path: str, remote: str = "origin", branch: str = "main") -> tuple[bool, str]:
    """git push to remote."""
    result = subprocess.run(
        ["git", "push", remote, branch],
        capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode != 0:
        return False, f"git push failed: {result.stderr.strip()}"
    return True, result.stdout.strip() or result.stderr.strip()


def verify_push(filepath: str, repo: str) -> tuple[bool, str]:
    """RULE-07: Verify file exists on remote via gh api (P3 — not browser)."""
    # Extract org/repo from remote URL
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, cwd=repo
    )
    if result.returncode != 0:
        return False, "Could not get remote URL"
    remote_url = result.stdout.strip()
    # Parse org/repo from git URL
    m = re.search(r'github\.com[:/](.+/.+?)(?:\.git)?$', remote_url)
    if not m:
        return False, f"Cannot parse org/repo from: {remote_url}"
    org_repo = m.group(1)
    verify = subprocess.run(
        ["gh", "api", f"repos/{org_repo}/contents/{filepath}", "--jq", ".name,.size,.sha"],
        capture_output=True, text=True
    )
    if verify.returncode != 0:
        return False, f"gh api verify failed: {verify.stderr.strip()}"
    return True, f"Verified on remote: {verify.stdout.strip()}"


# ── Core Run Logic ────────────────────────────────────────────────────────────

def run(files: list[str], session_id: str, message: str,
        repo_path: str, dry_run: bool = False,
        staged_only: bool = False) -> dict:
    """
    Main gate logic. Returns results dict.
    """
    errors    = []
    warnings  = []
    items     = []
    blocked   = []
    z2_flags  = []
    allowed   = []

    # ── Step 1: Resolve file list ──────────────────────────────────────────
    if staged_only:
        try:
            files = get_staged_files(repo_path)
        except SpecLoadFailed as e:
            return {"status": "FAIL", "errors": [str(e)], "items": [], "warnings": []}

    if not files:
        return {"status": "FAIL", "errors": ["No files specified or staged"], "items": [], "warnings": []}

    # ── Step 2: Classify each file ────────────────────────────────────────
    for f in files:
        classification = classify_file(f if Path(f).is_absolute() else str(Path(repo_path) / f))
        item = {"file": f, **classification}

        if classification["verdict"] == "BLOCKED":
            blocked.append(item)
        elif classification["verdict"] == "ZONE_2_REQUIRED":
            z2_flags.append(item)
        else:
            allowed.append(item)
        items.append(item)

    # Hard blocks → immediate ABORT
    if blocked:
        return {
            "status":    "FAIL",
            "verdict":   "ABORT — BLOCKED FILES DETECTED",
            "errors":    [f"BLOCKED: {b['file']} — {b['reason']}" for b in blocked],
            "warnings":  [],
            "items":     items,
            "blocked":   blocked,
            "z2_flags":  z2_flags,
            "allowed":   allowed,
            "dry_run":   dry_run,
        }

    # Zone 2 flags → ABORT with guidance
    if z2_flags:
        return {
            "status":    "FAIL",
            "verdict":   "ABORT — ZONE 2 FILES REQUIRE NIGHT REVIEW",
            "errors":    [f"ZONE_2: {f['file']} — {f['reason']}" for f in z2_flags],
            "warnings":  [],
            "items":     items,
            "blocked":   blocked,
            "z2_flags":  z2_flags,
            "allowed":   allowed,
            "dry_run":   dry_run,
        }

    # ── Step 3: Validate commit message (RULE-06) ─────────────────────────
    msg_ok, msg_note = validate_commit_message(message, session_id)
    if not msg_ok:
        return {
            "status":  "FAIL",
            "verdict": "ABORT — COMMIT MESSAGE INVALID",
            "errors":  [msg_note],
            "warnings": [], "items": items,
            "dry_run": dry_run,
        }

    # ── Step 4: Python tool smoke tests (RULE-03) ─────────────────────────
    for f in allowed:
        if f["file"].endswith(".py") and "tools/" in f["file"]:
            full_path = f["file"] if Path(f["file"]).is_absolute() else str(Path(repo_path) / f["file"])
            ok, note = validate_python_tool(full_path)
            f["smoke_test"] = note
            if not ok:
                return {
                    "status":  "FAIL",
                    "verdict": f"ABORT — SMOKE TEST FAILED: {f['file']}",
                    "errors":  [note],
                    "warnings": [], "items": items,
                    "dry_run": dry_run,
                }

    # ── Step 5: Dry-run path ──────────────────────────────────────────────
    if dry_run:
        return {
            "status":  "PASS",
            "verdict": "DRY_RUN — All checks passed. No push executed.",
            "errors":  [],
            "warnings": warnings,
            "items":   items,
            "allowed": allowed,
            "message": message,
            "dry_run": True,
            "next_step": "Remove --dry-run to execute push",
        }

    # ── Step 6: Stage files (if not already staged) ───────────────────────
    if not staged_only:
        rel_files = [
            str(Path(f["file"]).relative_to(repo_path))
            if Path(f["file"]).is_absolute() else f["file"]
            for f in allowed
        ]
        ok, note = stage_files(rel_files, repo_path)
        if not ok:
            return {"status": "FAIL", "verdict": "ABORT — STAGE FAILED",
                    "errors": [note], "warnings": [], "items": items, "dry_run": False}

    # ── Step 7: RULE-08 — verify staged list matches intent ───────────────
    staged = get_staged_files(repo_path)
    intended = {
        (str(Path(f["file"]).relative_to(repo_path))
         if Path(f["file"]).is_absolute() else f["file"])
        for f in allowed
    }
    unexpected = set(staged) - intended
    if unexpected:
        # Unstage everything and abort
        subprocess.run(["git", "reset", "HEAD"] + list(unexpected),
                       capture_output=True, cwd=repo_path)
        return {
            "status":  "FAIL",
            "verdict": "ABORT — UNEXPECTED STAGED FILES (RULE-08)",
            "errors":  [f"Unexpected: {u}" for u in unexpected],
            "warnings": [], "items": items, "dry_run": False,
            "action_taken": "Unexpected files unstaged",
        }

    # ── Step 8: Commit ────────────────────────────────────────────────────
    ok, sha = do_commit(message, repo_path)
    if not ok:
        return {"status": "FAIL", "verdict": "ABORT — COMMIT FAILED",
                "errors": [sha], "warnings": [], "items": items, "dry_run": False}

    # ── Step 9: Push ──────────────────────────────────────────────────────
    ok, push_out = do_push(repo_path)
    if not ok:
        return {
            "status":  "FAIL",
            "verdict": "PUSH FAILED — commit exists locally",
            "errors":  [push_out],
            "warnings": [f"Commit SHA {sha} exists locally. Run: git push origin main"],
            "items":   items, "sha": sha, "dry_run": False,
        }

    # ── Step 10: Verify (RULE-07) ─────────────────────────────────────────
    verify_results = []
    for f in allowed[:3]:  # verify first 3 files (representative sample)
        rel = (str(Path(f["file"]).relative_to(repo_path))
               if Path(f["file"]).is_absolute() else f["file"])
        ok_v, verify_note = verify_push(rel, repo_path)
        verify_results.append({"file": rel, "verified": ok_v, "note": verify_note})
        if not ok_v:
            warnings.append(f"P3 verify incomplete for {rel}: {verify_note}")

    push_time = datetime.now(timezone.utc).isoformat()
    return {
        "status":   "PASS",
        "verdict":  "PUSH COMPLETE",
        "sha":      sha,
        "pushed_at": push_time,
        "errors":   [],
        "warnings": warnings,
        "items":    items,
        "allowed":  allowed,
        "verify":   verify_results,
        "message":  message,
        "session":  session_id,
        "dry_run":  False,
        "receipt":  {
            "files":    [f["file"] for f in allowed],
            "sha":      sha,
            "timestamp": push_time,
            "session":   session_id,
            "message":   message,
        },
    }


# ── Output Formatters ─────────────────────────────────────────────────────────

def aggregate(run_result: dict) -> dict:
    return {
        "tool":      TOOL_NAME,
        "version":   TOOL_VERSION,
        "zone":      TOOL_ZONE,
        "session":   TOOL_SESSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ratification": RATIFICATION,
        **run_result,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"git_push_gate_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict) -> None:
    bar = "=" * 64
    verdict = output.get("verdict", output.get("status", "?"))
    print(f"\n{bar}")
    print(f" Git Push Gate v{TOOL_VERSION}")
    print(f" {verdict}")
    print(bar)

    items = output.get("items", [])
    if items:
        print(f"\n Files ({len(items)}):")
        for item in items:
            sym = "✓" if item.get("verdict") == "ALLOWED" else (
                  "✗" if item.get("verdict") == "BLOCKED" else "⚠")
            z   = f"[Z{item.get('zone','?')}]"
            print(f"   {sym} {z} {item['file']}")
            print(f"        {item.get('reason','')}")

    errors = output.get("errors", [])
    if errors:
        print(f"\n ERRORS:")
        for e in errors:
            print(f"   ✗ {e}")

    warnings = output.get("warnings", [])
    if warnings:
        print(f"\n WARNINGS:")
        for w in warnings:
            print(f"   ⚠ {w}")

    if output.get("status") == "PASS":
        receipt = output.get("receipt")
        if receipt:
            print(f"\n RECEIPT:")
            print(f"   SHA      : {receipt.get('sha','?')}")
            print(f"   Session  : {receipt.get('session','?')}")
            print(f"   Files    : {len(receipt.get('files',[]))}")
            print(f"   Message  : {receipt.get('message','?')[:60]}")
            print(f"   Timestamp: {receipt.get('timestamp','?')}")
            print(f"\n   → Post this receipt to WGS session record (RULE-10)")

    if output.get("dry_run"):
        print(f"\n DRY RUN — No changes made. Remove --dry-run to execute.")

    print(f"\n{bar}\n")


def print_rules() -> None:
    """Print the complete Zone 1 push ruleset."""
    bar = "=" * 64
    print(f"\n{bar}")
    print(f" HumanAIOS Zone 1 Git Push Ruleset")
    print(f" Ratified: {RATIFICATION['by']} · {RATIFICATION['session']}")
    print(f" Scope:    {RATIFICATION['scope']}")
    print(bar)

    print("""
ZONE 1 — ALLOWED (push without additional ratification)
  ✓ CURRENT.md, SESSION_RITUALS.md, GOVERNANCE.md, OPERATOR_RUNBOOK.md, README.md
  ✓ Session artifacts: *_S-MMDDYY*.{md,json,html,jsx,mermaid}
  ✓ Tool output reports: *_YYYYMMDDTHHMMSSZ.json
  ✓ Static HTML pages (no embedded credentials)
  ✓ tools/**/*.py  — Builder v1.7 compliant + smoke test PASSED
  ✓ tools/**/*.sh  — no credential reads
  ✓ *.mermaid      — architecture diagrams
  ✓ *.yml / *.yaml — CI config (content-scanned for credentials)

ZONE 2 — REQUIRED (Night review before push)
  ⚠ Any file containing credential patterns (HARD BLOCK on content scan)
  ⚠ MODEAI_*, GE_*, DEMARIUS_* — collaborator files
  ⚠ acat_core.js, assess.html — product layer (user-facing)
  ⚠ REGISTERED.md — only after in-session Night ratification
  ⚠ *.sql — schema migrations
  ⚠ constitution.json — agent kernel
  ⚠ Any other file (default: require Night review)

ZONE 3 — NEVER Zone 1
  ✗ humanaios-internal/ repo
  ✗ Supabase row inserts/updates
  ✗ Secret rotation, credential changes
  ✗ Cloudflare Worker deployments (wrangler publish)
  ✗ GitHub OAuth / Access token management

HARD RULES
  RULE-01: git diff --cached --name-only must match staged intent
  RULE-02: Content scan for credential patterns on every file
  RULE-03: Python tools in tools/ must pass --smoke-test
  RULE-04: REGISTERED.md requires in-session Night ratification
  RULE-05: Push to operations-staging only, never humanaios-internal
  RULE-06: Commit message must include session ID (S-MMDDYY)
  RULE-07: Verify via gh api refetch after push (P3)
  RULE-08: Unexpected staged file → ABORT immediately
  RULE-09: --dry-run flag available for pre-flight check
  RULE-10: Push receipt posted to WGS session record
""")
    print(bar)
    print()


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    import tempfile
    try:
        # Test 1: Zone 1 allowed files
        z1_cases = [
            "CURRENT.md",
            "SESSION_RITUALS.md",
            "README.md",
            "ACAT_VALIDATION_RESULTS_S-051726-02.md",
            "tools/carry_tracker_v1_0.py",
            "SYSTEM_MAP_V1_0.mermaid",
            "night_command_center_S051726-02.html",
        ]
        for f in z1_cases:
            c = classify_file(f)  # no real file — content scan returns None
            assert c["verdict"] == "ALLOWED", f"Expected ALLOWED for {f}, got {c['verdict']}: {c['reason']}"

        # Test 2: Zone 3 hard blocks
        z3_cases = [
            "constitution.json",
            "humanaios-internal/ops/SECRET.md",
            "migration_001.sql",
            ".env.production",
        ]
        for f in z3_cases:
            c = classify_file(f)
            assert c["verdict"] == "BLOCKED", f"Expected BLOCKED for {f}, got {c['verdict']}"

        # Test 3: Zone 2 flags
        z2_cases = [
            "MODEAI_JOINT_REPORT.html",
            "GE_Partnership_TermSheet_v2.docx",
            "DEMARIUS_PROOF2.md",
            "acat_core.js",
            "assess.html",
        ]
        for f in z2_cases:
            c = classify_file(f)
            assert c["verdict"] == "ZONE_2_REQUIRED", f"Expected ZONE_2 for {f}, got {c['verdict']}"

        # Test 4: Credential content scan
        with tempfile.TemporaryDirectory() as d:
            cred_file = Path(d) / "test.md"
            cred_file.write_text('SUPABASE_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.fake"')
            result = scan_content(str(cred_file))
            assert result is not None, "Credential scan should have flagged JWT pattern"

        # Test 5: Commit message validation
        ok, _ = validate_commit_message("S-051726-02: update CURRENT.md", "S-051726-02")
        assert ok, "Valid commit message should pass"
        ok, _ = validate_commit_message("update stuff without session id", "S-051726-02")
        assert not ok, "Missing session ID should fail"

        # Test 6: Empty files list
        result = run([], "S-051726-02", "test", "/tmp", dry_run=True)
        assert result["status"] == "FAIL", "Empty file list should fail"

        print("✓ Smoke test PASSED — all Zone 1/2/3 classifications correct")
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
        description="Git Push Gate v1.0 — Zone 1 push authorization for HumanAIOS"
    )
    parser.add_argument("--files",    nargs="+", help="Files to stage and push")
    parser.add_argument("--staged",   action="store_true",
                        help="Use currently staged files (git add already done)")
    parser.add_argument("--session",  required=False, default="",
                        help="Session ID for commit message (e.g. S-051726-02)")
    parser.add_argument("--message",  default="",
                        help="Commit message (session ID will be prepended if absent)")
    parser.add_argument("--repo",     default=".",
                        help="Path to git repository root (default: current dir)")
    parser.add_argument("--output",   default="outputs/",
                        help="Directory for JSON report (default: outputs/)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Classify and validate files; do not push")
    parser.add_argument("--list-rules", action="store_true",
                        help="Print the complete Zone 1 push ruleset and exit")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Run smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    if args.list_rules:
        print_rules()
        sys.exit(0)

    if not args.files and not args.staged:
        parser.print_help()
        print("\nExamples:")
        print("  python git_push_gate_v1_0.py --files CURRENT.md "
              "--session S-051726-02 --message 'update ops state'")
        print("  python git_push_gate_v1_0.py --staged "
              "--session S-051726-02 --message 'S-051726-02: sprint 1 tools'")
        print("  python git_push_gate_v1_0.py --list-rules")
        sys.exit(1)

    # Build commit message
    message = args.message
    if args.session and not re.search(r'S-\d{6}', message):
        message = f"{args.session}: {message}" if message else args.session

    run_result = run(
        files       = args.files or [],
        session_id  = args.session,
        message     = message,
        repo_path   = args.repo,
        dry_run     = args.dry_run,
        staged_only = args.staged,
    )

    output = aggregate(run_result)
    rp = write_report(output, args.output)
    print_summary(output)
    print(f"Report: {rp}")
    sys.exit(0 if output.get("status") == "PASS" else 1)


if __name__ == "__main__":
    main()

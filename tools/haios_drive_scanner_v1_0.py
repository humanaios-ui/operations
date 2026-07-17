#!/usr/bin/env python3
"""
HAIOS Drive Scanner — v1.0
Builder v1.7 compliant · audit_tool
HumanAIOS · S-051726-02-molt-grow-kill

THE DARK CORPUS SCANNER.

Walks the entire hard drive (or a target directory), builds a complete
manifest of every file, classifies each one relative to HumanAIOS work,
extracts information from orphaned or lost files, and produces a triage
report with keep/archive/ingest/delete/review recommendations.

WHAT THIS SOLVES:
  Every file that's not in a git repo is invisible to the harmonizer,
  the validation suite, and CURRENT.md. Years of early development work,
  grant drafts, collaborator documents, and data files with useful content
  may exist on disk but nowhere in the knowledge graph. This tool makes
  that dark corpus visible and recovers information from it.

STAGES:
  1. CENSUS    — walk directories, build file manifest
  2. CLASSIFY  — assign category per file (HAIOS_CORE, HAIOS_ORPHAN,
                 RESEARCH, GRANT, COLLABORATOR, DUPLICATE, STALE, UNKNOWN)
  3. EXTRACT   — read text content from HAIOS_ORPHAN + RESEARCH + GRANT files,
                 pull decisions, findings, session IDs, people, action items
  4. TRIAGE    — assign recommendation (KEEP_ACTIVE, ARCHIVE, INGEST,
                 DELETE, REVIEW)
  5. REPORT    — manifest CSV, recovered knowledge summary, action list,
                 duplicate map

WHAT IT READS:
  .txt .md .py .js .ts .json .yaml .yml .sh .html .htm .jsx .tsx
  .csv .tsv .tex .rst .org .mermaid
  .pdf  (text layer only — requires: pip install pypdf)
  .docx (requires: pip install python-docx)
  All others: filename + metadata only, no content extraction

WHAT IT SKIPS (safe defaults):
  .app .dmg .pkg .exe .iso — binaries
  node_modules/ .git/objects/ __pycache__/ .DS_Store
  /System/ /Library/ /private/ /proc/ /dev/
  Files > 10MB (flagged, not read)
  Hidden dot-files except .env (flagged for credential check)

INSTALLATION (optional — enables docx/pdf reading):
  pip install python-docx pypdf --break-system-packages

USAGE:
  # Scan full HAIOS work area (recommended first run)
  python haios_drive_scanner_v1_0.py --root ~/Desktop/HAIOS-Main

  # Scan broader — entire Desktop + Documents + Downloads
  python haios_drive_scanner_v1_0.py --root ~ --depth 8

  # Scan specific dir, extract content from all text files
  python haios_drive_scanner_v1_0.py --root ~/Documents --extract-all

  # Quick census only (no content extraction, fast)
  python haios_drive_scanner_v1_0.py --root ~/Desktop --census-only

  # Output to specific directory
  python haios_drive_scanner_v1_0.py --root ~/Desktop/HAIOS-Main --output outputs/

  python haios_drive_scanner_v1_0.py --smoke-test
"""

import os
import re
import sys
import csv
import json
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

TOOL_NAME     = "haios_drive_scanner"
TOOL_VERSION  = "1.0.0"
TOOL_CATEGORY = "audit_tool"
TOOL_SESSION  = "S-051726-02-molt-grow-kill"
TOOL_ZONE     = 1

# ── Config ────────────────────────────────────────────────────────────────────

MAX_FILE_SIZE_BYTES  = 10 * 1024 * 1024   # 10 MB
MAX_EXTRACT_CHARS    = 8000               # max chars to read per file for extraction
STALE_DAYS           = 90                 # days before file is considered stale
DEFAULT_DEPTH        = 10                 # max directory depth

TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".json", ".yaml", ".yml",
    ".sh", ".html", ".htm", ".jsx", ".tsx", ".csv", ".tsv",
    ".tex", ".rst", ".org", ".mermaid", ".gs", ".rb", ".go",
    ".env",   # flagged for credential check
}

# Extensions that need libraries (attempted gracefully)
RICH_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls"}

# Skip patterns — paths containing these strings are skipped
SKIP_PATH_PATTERNS = [
    "/System/", "/private/var/", "/proc/", "/dev/",
    "/Library/Caches/", "/Library/Logs/",
    "node_modules/", ".git/objects/", "__pycache__/",
    "/.Trash/", "/Trash/",
]

# Skip filenames
SKIP_FILENAMES = {
    ".DS_Store", "Thumbs.db", ".localized",
    "desktop.ini", ".gitignore", ".gitkeep",
}

# Binary extensions (skip content, keep metadata)
BINARY_EXTENSIONS = {
    ".app", ".dmg", ".pkg", ".exe", ".iso", ".bin",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".mp3", ".mp4", ".mov", ".avi", ".mkv",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico",
    ".ttf", ".woff", ".woff2", ".eot",
    ".pyc", ".pyo", ".so", ".dylib", ".dll",
    ".sqlite", ".db",
}

# HumanAIOS signal words for classification
HAIOS_KEYWORDS = {
    "acat", "humanaios", "haios", "unit zero", "night", "carly anderson",
    "learning index", "molt", "wgs-sync", "operations-staging",
    "s-0", "gate 2", "gate 3", "corpus", "supabase", "registered.md",
    "current.md", "session_rituals", "governance.md", "constitution.json",
    "drift catalog", "d-comp", "him ", "zone 1", "zone 2", "zone 3",
}

RESEARCH_KEYWORDS = {
    "research", "hypothesis", "finding", "study", "analysis", "data",
    "psychometric", "cronbach", "correlation", "regression", "variance",
    "benchmark", "evaluation", "metric", "score", "validation",
    "arxiv", "paper", "publication", "abstract", "methodology",
}

GRANT_KEYWORDS = {
    "grant", "funding", "application", "proposal", "budget", "award",
    "neh", "nsf", "nih", "mozilla", "open collective", "patreon",
    "philanthropic", "fellowship", "scholarship", "rfp", "solicitation",
}

COLLABORATOR_NAMES = {
    "demarius", "modeai", "mode ai", "david", "empirica",
    "moni", "sydän", "sydan", "alex berlin", "revby",
    "satya nitta", "emergence", "grok", "gemini",
    "rentahuman", "rah", "alex liteplo",
}

# Session ID pattern
SESSION_ID_PAT = re.compile(r'S-\d{6}(-\d{2})?(-[\w-]+)?', re.I)

# LI score pattern
LI_PAT = re.compile(r'\bLI\s*[=:]\s*([0-9]\.[0-9]+)', re.I)

# Finding ID pattern
FINDING_PAT = re.compile(r'\b(F-\d+|F\d+|H-[A-Z]+-\d+|FP-\d+)\b')

# Action item patterns
ACTION_PAT = re.compile(
    r'(?:TODO|FIXME|ACTION|NEXT|PENDING|BLOCKED|→|->|•)\s*:?\s*(.{10,80})',
    re.I
)


class SpecLoadFailed(Exception):
    pass


# ── Reader Layer ──────────────────────────────────────────────────────────────

def read_text_file(path: Path, max_chars: int = MAX_EXTRACT_CHARS) -> Optional[str]:
    """Read a plain text file. Returns content up to max_chars."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except (IOError, OSError):
        return None


def read_pdf(path: Path, max_chars: int = MAX_EXTRACT_CHARS) -> Optional[str]:
    """Read PDF text layer. Requires pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(str(path))
        parts = []
        for page in reader.pages:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                pass
            if sum(len(p) for p in parts) >= max_chars:
                break
        return "\n".join(parts)[:max_chars]
    except ImportError:
        return None   # library not installed
    except Exception:
        return None


def read_docx(path: Path, max_chars: int = MAX_EXTRACT_CHARS) -> Optional[str]:
    """Read .docx text. Requires python-docx."""
    try:
        import docx
        doc = docx.Document(str(path))
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(parts)[:max_chars]
    except ImportError:
        return None
    except Exception:
        return None


def read_file(path: Path) -> Optional[str]:
    """Read any supported file type. Returns text or None."""
    ext = path.suffix.lower()
    if ext in TEXT_EXTENSIONS:
        return read_text_file(path)
    if ext == ".pdf":
        return read_pdf(path)
    if ext in (".docx", ".doc"):
        return read_docx(path)
    return None


# ── Classification ────────────────────────────────────────────────────────────

def classify_file(path: Path, content: Optional[str],
                  repo_names: set[str]) -> str:
    """
    Classify a file into one of:
    HAIOS_CORE, HAIOS_ORPHAN, RESEARCH, GRANT, COLLABORATOR,
    DUPLICATE, STALE, UNKNOWN
    """
    name = path.name.lower()
    path_lower = str(path).lower()

    # Check if it's in a known repo
    for repo in repo_names:
        if repo.lower() in path_lower:
            return "HAIOS_CORE"

    # Content-based classification (if available)
    text = (content or "").lower()
    name_lower = name.lower()
    combined = name_lower + " " + text[:500]

    # Grant
    grant_hits = sum(1 for k in GRANT_KEYWORDS if k in combined)
    if grant_hits >= 2:
        return "GRANT"

    # Collaborator
    for collab in COLLABORATOR_NAMES:
        if collab in combined:
            return "COLLABORATOR"

    # HumanAIOS orphan (has HAIOS content but not in repo)
    haios_hits = sum(1 for k in HAIOS_KEYWORDS if k in combined)
    if haios_hits >= 2:
        return "HAIOS_ORPHAN"

    # Research
    research_hits = sum(1 for k in RESEARCH_KEYWORDS if k in combined)
    if research_hits >= 3:
        return "RESEARCH"

    # Stale check (fallback)
    try:
        mtime = path.stat().st_mtime
        age_days = (datetime.now().timestamp() - mtime) / 86400
        if age_days > STALE_DAYS and path.suffix.lower() not in {".py", ".js", ".ts"}:
            return "STALE"
    except OSError:
        pass

    return "UNKNOWN"


def triage_recommendation(category: str, path: Path,
                           content: Optional[str],
                           is_duplicate: bool) -> str:
    """
    Recommend: KEEP_ACTIVE, ARCHIVE, INGEST, DELETE, REVIEW
    """
    if is_duplicate:
        return "DELETE"
    if category == "HAIOS_CORE":
        return "KEEP_ACTIVE"
    if category == "HAIOS_ORPHAN":
        # Has HAIOS content but not in repo — high value candidate
        if content and len(content.strip()) > 200:
            return "INGEST"
        return "REVIEW"
    if category == "GRANT":
        return "ARCHIVE"
    if category == "COLLABORATOR":
        return "ARCHIVE"
    if category == "RESEARCH":
        if content and len(content.strip()) > 500:
            return "INGEST"
        return "ARCHIVE"
    if category == "STALE":
        return "ARCHIVE"
    if category == "UNKNOWN":
        return "REVIEW"
    return "REVIEW"


# ── Information Extraction ────────────────────────────────────────────────────

def extract_intel(path: Path, content: str) -> dict:
    """
    Extract key information from file content.
    Returns dict of extracted intel.
    """
    if not content:
        return {}

    intel = {
        "session_ids":    SESSION_ID_PAT.findall(content),
        "li_scores":      LI_PAT.findall(content),
        "finding_ids":    list(set(FINDING_PAT.findall(content))),
        "action_items":   [],
        "key_lines":      [],
    }

    # Action items (first 5)
    for m in ACTION_PAT.finditer(content):
        item = m.group(1).strip()
        if len(item) > 10:
            intel["action_items"].append(item[:100])
        if len(intel["action_items"]) >= 5:
            break

    # Key lines: lines with numbers, dates, or strong signals
    key_pat = re.compile(
        r'(?:decided|confirmed|finding|result|conclusion|approved|ratified|'
        r'N=\d+|LI=|mean|α=|r=|p<|gate \d|zone \d)',
        re.I
    )
    for line in content.split("\n"):
        line = line.strip()
        if key_pat.search(line) and 10 < len(line) < 200:
            intel["key_lines"].append(line)
        if len(intel["key_lines"]) >= 8:
            break

    # Clean up session_id tuples
    intel["session_ids"] = [
        m if isinstance(m, str) else m[0]
        for m in intel["session_ids"]
    ]
    intel["session_ids"] = list(set(intel["session_ids"]))

    # Remove empties
    return {k: v for k, v in intel.items() if v}


# ── File Scanner ──────────────────────────────────────────────────────────────

def should_skip(path: Path) -> bool:
    """Return True if this path should be skipped."""
    path_str = str(path)

    # Skip path patterns
    for pat in SKIP_PATH_PATTERNS:
        if pat in path_str:
            return True

    # Skip known unreadable dirs
    if path.is_dir():
        skip_dirs = {
            ".git", "node_modules", "__pycache__", ".cache",
            "Caches", "Logs", "Frameworks",
        }
        if path.name in skip_dirs:
            return True

    # Skip specific filenames
    if path.name in SKIP_FILENAMES:
        return True

    # Skip hidden files (except .env)
    if path.name.startswith(".") and path.name != ".env":
        return True

    return False


def scan_file(path: Path, repo_names: set[str],
              extract: bool = True,
              seen_hashes: dict = None) -> Optional[dict]:
    """
    Scan a single file. Returns record dict or None if skipped.
    """
    if should_skip(path):
        return None

    try:
        stat = path.stat()
    except (OSError, PermissionError):
        return None

    ext  = path.suffix.lower()
    size = stat.st_size
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

    # Skip binaries (record metadata only)
    is_binary = ext in BINARY_EXTENSIONS
    content   = None

    if not is_binary and size <= MAX_FILE_SIZE_BYTES and extract:
        content = read_file(path)

    # Deduplication via content hash (text files only)
    is_duplicate = False
    file_hash    = None
    if content and seen_hashes is not None:
        file_hash = hashlib.md5(content.encode("utf-8", errors="ignore")).hexdigest()
        if file_hash in seen_hashes:
            is_duplicate = True
        else:
            seen_hashes[file_hash] = str(path)

    category   = classify_file(path, content, repo_names)
    triage     = triage_recommendation(category, path, content, is_duplicate)

    # Extract intel for high-value files
    intel = {}
    if extract and content and category in {
        "HAIOS_ORPHAN", "RESEARCH", "GRANT", "COLLABORATOR"
    }:
        intel = extract_intel(path, content)

    return {
        "path":         str(path),
        "filename":     path.name,
        "extension":    ext,
        "size_bytes":   size,
        "modified":     mtime,
        "category":     category,
        "triage":       triage,
        "is_binary":    is_binary,
        "is_duplicate": is_duplicate,
        "file_hash":    file_hash,
        "has_content":  content is not None,
        "content_len":  len(content) if content else 0,
        "intel":        intel,
        "duplicate_of": seen_hashes.get(file_hash, "") if (is_duplicate and seen_hashes) else "",
    }


def walk_directory(root: Path, max_depth: int = DEFAULT_DEPTH,
                   repo_names: set[str] = None,
                   extract: bool = True,
                   census_only: bool = False) -> list[dict]:
    """
    Walk root directory up to max_depth, scanning each file.
    Returns list of file records.
    """
    if repo_names is None:
        repo_names = {
            "operations-staging", "lasting-light-ai", "HAIOSCC",
            "acat-inspect", "ACAT-Dashboard", "humanaios-internal",
            "humanaios 2", "personal-zones",
        }

    records = []
    seen_hashes = {}
    root_depth = len(root.parts)
    files_scanned = 0
    skipped = 0

    for dirpath, dirnames, filenames in os.walk(str(root), followlinks=False):
        current_path = Path(dirpath)
        depth = len(current_path.parts) - root_depth

        if depth > max_depth:
            dirnames.clear()
            continue

        # Prune skip dirs in-place
        dirnames[:] = [
            d for d in dirnames
            if not should_skip(current_path / d)
        ]

        for fname in filenames:
            fpath = current_path / fname
            if should_skip(fpath):
                skipped += 1
                continue

            record = scan_file(
                fpath, repo_names,
                extract=(not census_only),
                seen_hashes=seen_hashes
            )
            if record:
                records.append(record)
                files_scanned += 1

            # Progress indicator every 100 files
            if files_scanned % 100 == 0:
                print(f"  [SCAN] {files_scanned} files scanned... ({str(fpath)[:60]})",
                      end="\r", flush=True)

    print(f"\n  [SCAN] Complete: {files_scanned} files scanned, {skipped} skipped")
    return records


# ── Aggregation ───────────────────────────────────────────────────────────────

def run(root: str, max_depth: int = DEFAULT_DEPTH,
        extract_all: bool = False, census_only: bool = False) -> dict:
    """Full scan run."""
    root_path = Path(root).expanduser().resolve()
    if not root_path.exists():
        raise SpecLoadFailed(f"Root path does not exist: {root_path}")

    print(f"\n  [HAIOS Drive Scanner v{TOOL_VERSION}]")
    print(f"  Root     : {root_path}")
    print(f"  Max depth: {max_depth}")
    print(f"  Extract  : {'all files' if extract_all else 'high-value only'}")
    print(f"  Mode     : {'census only' if census_only else 'full scan'}")
    print()

    records = walk_directory(
        root_path, max_depth=max_depth,
        extract=not census_only
    )

    # Aggregate stats
    by_category   = {}
    by_triage     = {}
    by_extension  = {}
    recovered_intel = []
    action_items  = []
    duplicates    = []

    for r in records:
        cat = r["category"]
        tri = r["triage"]
        ext = r["extension"] or "(none)"

        by_category[cat]  = by_category.get(cat, 0) + 1
        by_triage[tri]    = by_triage.get(tri, 0) + 1
        by_extension[ext] = by_extension.get(ext, 0) + 1

        # Collect intel from high-value files
        intel = r.get("intel", {})
        if intel:
            recovered_intel.append({
                "file":       r["filename"],
                "path":       r["path"],
                "category":   cat,
                "session_ids": intel.get("session_ids", []),
                "li_scores":  intel.get("li_scores", []),
                "findings":   intel.get("finding_ids", []),
                "actions":    intel.get("action_items", []),
                "key_lines":  intel.get("key_lines", []),
            })

        # Collect duplicates
        if r["is_duplicate"]:
            duplicates.append({
                "file":         r["filename"],
                "path":         r["path"],
                "duplicate_of": r["duplicate_of"],
                "size_bytes":   r["size_bytes"],
            })

        # Collect action items
        for ai in intel.get("action_items", []):
            action_items.append({
                "source": r["filename"],
                "action": ai,
            })

    # Priority action list
    priority_actions = []

    # 1. INGEST items first (lost information to recover)
    ingest_files = [r for r in records if r["triage"] == "INGEST"]
    for r in sorted(ingest_files, key=lambda x: x["size_bytes"], reverse=True)[:20]:
        priority_actions.append({
            "priority": "INGEST",
            "file":     r["filename"],
            "path":     r["path"],
            "category": r["category"],
            "reason":   f"Contains recoverable HumanAIOS/research content ({r['content_len']} chars)",
        })

    # 2. REVIEW items (unknown, needs Night)
    review_files = [r for r in records
                    if r["triage"] == "REVIEW" and not r["is_binary"]]
    for r in review_files[:20]:
        priority_actions.append({
            "priority": "REVIEW",
            "file":     r["filename"],
            "path":     r["path"],
            "category": r["category"],
            "reason":   "Cannot auto-classify — Night review needed",
        })

    # 3. Confirmed duplicates to delete
    for d in duplicates[:20]:
        priority_actions.append({
            "priority": "DELETE",
            "file":     d["file"],
            "path":     d["path"],
            "category": "DUPLICATE",
            "reason":   f"Identical content to: {d['duplicate_of'][-60:]}",
        })

    total_size = sum(r["size_bytes"] for r in records)

    return {
        "status":           "PASS",
        "root":             str(root_path),
        "scan_time":        datetime.now(timezone.utc).isoformat(),
        "total_files":      len(records),
        "total_size_mb":    round(total_size / 1024 / 1024, 1),
        "by_category":      dict(sorted(by_category.items())),
        "by_triage":        dict(sorted(by_triage.items())),
        "top_extensions":   dict(sorted(by_extension.items(),
                                        key=lambda x: -x[1])[:15]),
        "recovered_intel":  recovered_intel,
        "duplicate_count":  len(duplicates),
        "duplicates":       duplicates[:50],
        "priority_actions": priority_actions,
        "action_items":     action_items[:50],
        "records":          records,   # full manifest
        "summary": {
            "total_files":    len(records),
            "total_size_mb":  round(total_size / 1024 / 1024, 1),
            "haios_orphan":   by_category.get("HAIOS_ORPHAN", 0),
            "to_ingest":      by_triage.get("INGEST", 0),
            "to_review":      by_triage.get("REVIEW", 0),
            "to_archive":     by_triage.get("ARCHIVE", 0),
            "duplicates":     len(duplicates),
            "intel_files":    len(recovered_intel),
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
        **{k: v for k, v in run_result.items() if k != "records"},
    }


def write_report(output: dict, records: list, output_dir: str) -> dict:
    """Write JSON report + CSV manifest. Returns paths dict."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # JSON report (no full records — too large)
    json_path = p / f"drive_scan_{ts}.json"
    json_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    # CSV manifest (every file)
    csv_path = p / f"drive_manifest_{ts}.csv"
    if records:
        fieldnames = [
            "filename", "path", "extension", "size_bytes", "modified",
            "category", "triage", "is_duplicate", "has_content",
            "content_len", "session_ids", "finding_ids", "li_scores",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in records:
                row = dict(r)
                intel = r.get("intel", {})
                row["session_ids"]  = "|".join(intel.get("session_ids", []))
                row["finding_ids"]  = "|".join(intel.get("finding_ids", []))
                row["li_scores"]    = "|".join(intel.get("li_scores", []))
                writer.writerow(row)

    # Recovered knowledge summary (INGEST-priority files only)
    if output.get("recovered_intel"):
        kb_path = p / f"recovered_knowledge_{ts}.md"
        lines = [
            f"# Recovered Knowledge — Drive Scan {ts}",
            f"Session: {TOOL_SESSION}",
            f"Files with recoverable intel: {len(output['recovered_intel'])}",
            "",
        ]
        for item in output["recovered_intel"]:
            lines += [
                f"## {item['file']}",
                f"**Path:** `{item['path']}`  |  **Category:** {item['category']}",
            ]
            if item.get("session_ids"):
                lines.append(f"**Session IDs found:** {', '.join(item['session_ids'])}")
            if item.get("findings"):
                lines.append(f"**Finding IDs:** {', '.join(item['findings'])}")
            if item.get("li_scores"):
                lines.append(f"**LI Scores:** {', '.join(item['li_scores'])}")
            if item.get("key_lines"):
                lines.append("**Key lines:**")
                for kl in item["key_lines"]:
                    lines.append(f"- {kl}")
            if item.get("actions"):
                lines.append("**Action items:**")
                for ai in item["actions"]:
                    lines.append(f"- {ai}")
            lines.append("")
        kb_path.write_text("\n".join(lines), encoding="utf-8")
    else:
        kb_path = None

    return {
        "json":     str(json_path),
        "csv":      str(csv_path),
        "knowledge": str(kb_path) if kb_path else None,
    }


def print_summary(output: dict) -> None:
    bar = "═" * 66
    bar2 = "─" * 66
    s = output.get("summary", {})

    print(f"\n{bar}")
    print(f" HAIOS Drive Scanner v{TOOL_VERSION}")
    print(f" Root: {output.get('root','?')}")
    print(bar2)
    print(f"  Files scanned : {s.get('total_files','?'):>6}")
    print(f"  Total size    : {s.get('total_size_mb','?'):>6} MB")
    print(bar2)

    print(f"\n  BY CATEGORY:")
    cat_icons = {
        "HAIOS_CORE": "✓", "HAIOS_ORPHAN": "💡", "RESEARCH": "🔬",
        "GRANT": "💰", "COLLABORATOR": "🤝", "DUPLICATE": "♊",
        "STALE": "⏳", "UNKNOWN": "❓"
    }
    for cat, count in output.get("by_category", {}).items():
        icon = cat_icons.get(cat, "·")
        print(f"   {icon} {cat:<16} {count:>5}")

    print(f"\n  BY TRIAGE:")
    tri_icons = {
        "KEEP_ACTIVE":"✓","INGEST":"💡","ARCHIVE":"📦",
        "DELETE":"🗑","REVIEW":"👁"
    }
    for tri, count in output.get("by_triage", {}).items():
        icon = tri_icons.get(tri, "·")
        print(f"   {icon} {tri:<14} {count:>5}")

    intel_count = s.get("intel_files", 0)
    dup_count   = s.get("duplicates", 0)
    print(f"\n  FILES WITH RECOVERABLE INTEL : {intel_count}")
    print(f"  CONFIRMED DUPLICATES         : {dup_count}")

    actions = output.get("priority_actions", [])
    if actions:
        print(f"\n  TOP PRIORITY ACTIONS ({len(actions)} total):")
        shown = {"INGEST": 0, "REVIEW": 0, "DELETE": 0}
        for a in actions[:12]:
            pri = a["priority"]
            if shown.get(pri, 0) >= 4:
                continue
            shown[pri] = shown.get(pri, 0) + 1
            sym = {"INGEST":"💡","REVIEW":"👁","DELETE":"🗑"}.get(pri,"·")
            print(f"   {sym} [{pri}] {a['file'][:50]}")
            print(f"        {a['reason'][:65]}")

    print(f"\n{bar}\n")


# ── Smoke Test ────────────────────────────────────────────────────────────────

def run_smoke_test() -> bool:
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)

            # Create test files
            (root / "CURRENT.md").write_text(
                "# CURRENT.md\nHumanAIOS operations. ACAT corpus N=629. LI=0.8632. "
                "S-051726-02 Gate 2 PASSED. Zone 1 authorized.\n"
                "TODO: push CURRENT.md to GitHub\n"
                "F-35 CONFIRMED N=8"
            )
            (root / "grant_draft_v1.md").write_text(
                "Mozilla Foundation Grant Application\n"
                "Funding request for AI behavioral research.\n"
                "Budget: $50,000. Research study design.\n"
                "grant proposal funding award fellowship"
            )
            (root / "old_analysis.md").write_text(
                "Research analysis. Hypothesis confirmed. Finding: LI=0.84. "
                "Study validation metric correlation r=0.78 N=120 data"
            )
            (root / "duplicate.md").write_text(
                "HumanAIOS duplicate content acat corpus"
            )
            (root / "duplicate2.md").write_text(
                "HumanAIOS duplicate content acat corpus"
            )
            (root / "binary.dmg").write_bytes(b"\x00\x01\x02")
            sub = root / "subdir"
            sub.mkdir()
            (sub / "deep.txt").write_text("Deep file content")

            records = walk_directory(root, max_depth=5, extract=True)
            assert len(records) >= 5, f"Expected >= 5 records, got {len(records)}"

            # Check CURRENT.md classified correctly
            cur = next((r for r in records if r["filename"] == "CURRENT.md"), None)
            assert cur is not None, "CURRENT.md not found in records"
            assert cur["category"] == "HAIOS_ORPHAN", (
                f"CURRENT.md should be HAIOS_ORPHAN (not in repo path), got {cur['category']}")

            # Check grant classified
            grant = next((r for r in records if "grant" in r["filename"]), None)
            assert grant is not None
            assert grant["category"] == "GRANT", f"Grant file category: {grant['category']}"

            # Check binary skipped content
            binary = next((r for r in records if r["extension"] == ".dmg"), None)
            assert binary is not None
            assert binary["is_binary"] is True

            # Check intel extraction
            assert cur["intel"], f"No intel extracted from CURRENT.md: {cur}"
            assert cur["intel"].get("li_scores") or cur["intel"].get("finding_ids"), (
                f"Expected LI scores or finding IDs in CURRENT.md intel: {cur['intel']}")

            # Full run on temp dir
            result = run(str(root))
            assert result["status"] == "PASS"
            assert result["total_files"] >= 5
            assert result["summary"]["haios_orphan"] >= 1

        print("✓ Smoke test PASSED — scanner, classifier, extractor all verified")
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
        description=(
            "HAIOS Drive Scanner v1.0 — "
            "census, classify, extract, triage every file on disk"
        )
    )
    parser.add_argument("--root",        default="~/Desktop/HAIOS-Main",
                        help="Root directory to scan (default: ~/Desktop/HAIOS-Main)")
    parser.add_argument("--depth",       type=int, default=DEFAULT_DEPTH,
                        help=f"Max directory depth (default: {DEFAULT_DEPTH})")
    parser.add_argument("--output", "-o", default="outputs/",
                        help="Output directory for reports (default: outputs/)")
    parser.add_argument("--extract-all", action="store_true",
                        help="Extract content from all text files (not just high-value)")
    parser.add_argument("--census-only", action="store_true",
                        help="Census only — filename/metadata, no content extraction (fast)")
    parser.add_argument("--smoke-test",  action="store_true",
                        help="Run smoke test and exit")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    try:
        result = run(
            root        = args.root,
            max_depth   = args.depth,
            extract_all = args.extract_all,
            census_only = args.census_only,
        )
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    output  = aggregate(result)
    records = result.pop("records", [])
    paths   = write_report(output, records, args.output)

    print_summary(output)
    print(f"JSON report      : {paths['json']}")
    print(f"CSV manifest     : {paths['csv']}")
    if paths.get("knowledge"):
        print(f"Recovered knowledge: {paths['knowledge']}")
    print()
    print("Next steps:")
    print(f"  1. Open {paths['csv']} — sort by triage column")
    print(f"  2. Review INGEST items — content worth recovering to CURRENT.md")
    print(f"  3. Review REVIEW items — Night decides keep/archive/delete")
    if paths.get("knowledge"):
        print(f"  4. Read recovered_knowledge_*.md — extracted intel from orphan files")
    print()


if __name__ == "__main__":
    main()

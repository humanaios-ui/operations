"""
HumanAIOS — Registry Site Generator v1.0 (Builder v1.7)
Builder v1.7 compliant

Reads REGISTERED.md, parses F-class / IC-class / H-class entries,
and emits a static HTML research site under site/.

Entrypoints:
  CLI:  python tools/registry_site_generator_v1_0.py [--registry PATH] [--out DIR]
  MCP:  fastmcp run tools/registry_site_generator_v1_0.py --serve

Output layout:
  site/
    index.html          — browseable landing page with all findings
    assets/style.css    — shared stylesheet
    findings/<ID>.html  — one page per finding / correction / hypothesis
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Builder v1.7 constants
# ---------------------------------------------------------------------------
TOOL_NAME = "registry_site_generator"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "site"
TOOL_SESSION = "zone1"

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "REGISTERED.md"
DEFAULT_OUT = REPO_ROOT / "site"

# ---------------------------------------------------------------------------
# Status colour mapping  (matches the existing repo design palette)
# ---------------------------------------------------------------------------
STATUS_CLASS: dict[str, str] = {
    "ACTIVE":          "status-active",
    "REGISTERED":      "status-registered",
    "CONFIRMED":       "status-confirmed",
    "CANDIDATE":       "status-candidate",
    "SUPERSEDED":      "status-superseded",
    "DISCONFIRMED":    "status-disconfirmed",
    "PENDING_ZONE2":   "status-pending",
}

CLASS_LABEL: dict[str, str] = {
    "F":  "Finding",
    "IC": "IC Correction",
    "H":  "Hypothesis",
}


# ===========================================================================
# Parsing
# ===========================================================================

def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# Match a level-3 entry heading, e.g.:
#   ### F-18 — Force/Power Behavioral Taxonomy
#   ### F-24 / F-24b / F-24c / F-24d — IDE Calibration, Governance Under Pressure
#   ### IC-001/002/003 — GitHub Verification Gap
#   ### H-TRINITY-001 — Triadic Resolution Pattern in Interdependent System Design
#   ### H-1 — Humility Gap Hypothesis → CONFIRMED (see F-21)
#
# Separator must be an em-dash (—) or en-dash (–) — never a plain hyphen —
# so that non-entry section headers (e.g. "### F-number registry quick index")
# are never matched.
ENTRY_HEADING = re.compile(
    r'^### ([A-Za-z0-9/_-]+(?:\s*/\s*[A-Za-z0-9_-]+)*)\s*[—–]\s*(.+?)\s*$',
    re.MULTILINE,
)

# Intra-section marker headings (not entry bodies) that should terminate slicing.
SECTION_MARKER_HEADING = re.compile(r'^###\s+Zone\s+\d+\s*[—–-].*$', re.MULTILINE)

# YAML front-matter block inside a triple-backtick fence
YAML_FENCE = re.compile(
    r'```\s*\n---\n(.*?)\n---\n```',
    re.DOTALL,
)


def _parse_yaml_block(text: str) -> dict[str, Any]:
    """Extract and parse the first YAML front-matter block in *text*."""
    m = YAML_FENCE.search(text)
    if not m:
        return {}
    try:
        parsed = yaml.safe_load(m.group(1))
        return parsed if isinstance(parsed, dict) else {}
    except yaml.YAMLError:
        return {}


def _strip_yaml_block(text: str) -> str:
    """Remove the first YAML front-matter block from *text*."""
    return YAML_FENCE.sub("", text, count=1).strip()


def _detect_class(raw_id: str, section: str) -> str:
    """Infer entry class from its ID prefix or the current section name."""
    rid = raw_id.upper()
    if rid.startswith("F-") or rid.startswith("F/"):
        return "F"
    if rid.startswith("IC-"):
        return "IC"
    if rid.startswith("H-"):
        return "H"
    # Fallback to section
    if "F-class" in section:
        return "F"
    if "IC-class" in section:
        return "IC"
    if "H-class" in section:
        return "H"
    return "?"


def _is_nullish(value: Any) -> bool:
    """Return True for empty/null placeholder metadata values."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "null", "nul", "none", "nil", "n/a", "na", "-"}
    return False


def parse_registry(path: Path) -> list[dict[str, Any]]:
    """
    Parse REGISTERED.md and return a list of entry dicts.

    Each dict contains:
      id, title, class, status, yaml_meta (raw dict), body_md (str)
    """
    text = _load_text(path)

    entries: list[dict[str, Any]] = []
    section_pattern = re.compile(r'^## (.+?)$', re.MULTILINE)
    section_matches = list(section_pattern.finditer(text))

    for i, sec in enumerate(section_matches):
        section = sec.group(1).strip()
        if not any(key in section for key in ("F-class", "H-class", "IC-class")):
            continue

        sec_start = sec.end()
        sec_end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(text)
        section_text = text[sec_start:sec_end]

        # Parse entries only inside the current major section boundary.
        matches = list(ENTRY_HEADING.finditer(section_text))
        for j, m in enumerate(matches):
            raw_id = m.group(1).strip()
            title = m.group(2).strip()
            start = m.end()
            end = matches[j + 1].start() if j + 1 < len(matches) else len(section_text)
            marker = SECTION_MARKER_HEADING.search(section_text, start)
            if marker and marker.start() < end:
                end = marker.start()
            body_raw = section_text[start:end].strip()

            meta = _parse_yaml_block(body_raw)
            body_md = _strip_yaml_block(body_raw)

            # Determine values (prefer YAML, fall back to heuristics)
            raw_entry_id = meta.get("id", raw_id)
            entry_id = raw_id if _is_nullish(raw_entry_id) else str(raw_entry_id).strip('"')
            raw_class = meta.get("class", _detect_class(raw_id, section))
            entry_class = _detect_class(raw_id, section) if _is_nullish(raw_class) else str(raw_class).upper()
            raw_status = meta.get("status", "")
            entry_status = "" if _is_nullish(raw_status) else str(raw_status).upper()

            # Skip honest-gap placeholders (F-32 / F-33)
            if "honest gap" in title.lower() or "honest gap" in body_md[:80].lower():
                entry_status = entry_status or "GAP"

            entries.append({
                "id": entry_id,
                "raw_id": raw_id,
                "title": title,
                "class": entry_class,
                "status": entry_status,
                "yaml_meta": meta,
                "body_md": body_md,
                "section": section,
            })

    return entries


# ===========================================================================
# Lightweight Markdown → HTML  (covers the patterns used in REGISTERED.md)
# ===========================================================================

def _md_to_html(md: str) -> str:
    """Convert a subset of Markdown used in REGISTERED.md to HTML."""
    lines = md.split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False
    in_p = False
    in_pre = False
    pre_buf: list[str] = []

    def close_list() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_p() -> None:
        nonlocal in_p
        if in_p:
            out.append("</p>")
            in_p = False

    def inline(text: str) -> str:
        """Apply inline formatting."""
        # Bold  **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic *text*
        text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<em>\1</em>', text)
        # Inline code `text`
        text = re.sub(r'`([^`]+?)`', lambda m: f'<code>{html.escape(m.group(1))}</code>', text)
        # Markdown links [text](url)
        text = re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            r'<a href="\2" rel="noopener noreferrer" target="_blank">\1</a>',
            text,
        )
        return text

    i = 0
    while i < len(lines):
        line = lines[i]

        # ---- fenced code block (``` ... ```)
        if line.strip().startswith("```"):
            if in_pre:
                out.append(html.escape("\n".join(pre_buf)))
                out.append("</code></pre>")
                pre_buf = []
                in_pre = False
            else:
                close_list()
                close_p()
                out.append('<pre><code class="registry-code">')
                in_pre = True
            i += 1
            continue

        if in_pre:
            pre_buf.append(line)
            i += 1
            continue

        # ---- horizontal rule
        if re.match(r'^-{3,}$', line.strip()):
            close_list()
            close_p()
            out.append("<hr>")
            i += 1
            continue

        # ---- headings (## / ### / ####)
        m_h = re.match(r'^(#{2,4})\s+(.+?)\s*$', line)
        if m_h:
            close_list()
            close_p()
            level = len(m_h.group(1))
            out.append(f"<h{level}>{inline(m_h.group(2))}</h{level}>")
            i += 1
            continue

        # ---- blockquote lines
        if re.match(r'^\s*>\s*', line):
            close_list()
            close_p()
            quote_lines: list[str] = []
            while i < len(lines) and re.match(r'^\s*>\s*', lines[i]):
                quote_lines.append(re.sub(r'^\s*>\s*', '', lines[i]))
                i += 1

            out.append("<blockquote>")
            para: list[str] = []
            for q in quote_lines + [""]:
                if q.strip():
                    para.append(q.strip())
                    continue
                if para:
                    out.append(f"<p>{inline(' '.join(para))}</p>")
                    para = []
            out.append("</blockquote>")
            continue

        # ---- ordered list item  "1. …"
        m_ol = re.match(r'^(\s*)(\d+)\.\s+(.+)', line)
        if m_ol:
            close_p()
            if not in_ol:
                close_list()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline(m_ol.group(3))}</li>")
            i += 1
            continue

        # ---- unordered list item  "- …"
        m_ul = re.match(r'^(\s*)[-*]\s+(.+)', line)
        if m_ul:
            close_p()
            if not in_ul:
                close_list()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline(m_ul.group(2))}</li>")
            i += 1
            continue

        # ---- blank line
        if not line.strip():
            close_list()
            close_p()
            i += 1
            continue

        # ---- normal paragraph text
        close_list()
        if not in_p:
            out.append("<p>")
            in_p = True
        out.append(inline(line) + " ")
        i += 1

    close_list()
    close_p()
    if in_pre:
        out.append(html.escape("\n".join(pre_buf)))
        out.append("</code></pre>")

    return "\n".join(out)


# ===========================================================================
# CSS
# ===========================================================================

STYLESHEET = """\
/* HumanAIOS Registry Site — shared stylesheet */
:root {
  --gold: #C9A84C;
  --gold-dim: #8a7030;
  --teal: #1A9A9A;
  --red: #C0392B;
  --amber: #D4850A;
  --green: #1A9A5A;
  --blue: #2A7AC0;
  --purple: #7A3A9A;
  --bg: #0D0F11;
  --surface: #141618;
  --surface2: #1C1F22;
  --surface3: #242830;
  --border: #2A2F35;
  --border2: #353C44;
  --text: #E8EDF2;
  --text2: #A8B4C0;
  --text3: #6A7A88;
  --font-display: 'Fraunces', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  font-size: 15px;
  line-height: 1.7;
  min-height: 100vh;
}

/* ---- Header ---- */
.site-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 0 32px;
  display: flex;
  align-items: center;
  gap: 24px;
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.site-logo {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 600;
  color: var(--gold);
  text-decoration: none;
  letter-spacing: .03em;
}
.site-nav a {
  color: var(--text3);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color .15s;
}
.site-nav a:hover { color: var(--text); }

/* ---- Main layout ---- */
.container {
  max-width: 980px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* ---- Index page ---- */
.index-hero {
  padding: 48px 0 32px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 32px;
}
.index-hero h1 {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 12px;
}
.index-hero p {
  color: var(--text2);
  max-width: 640px;
}
.index-meta {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text3);
  margin-top: 8px;
}

/* ---- Filters / class tabs ---- */
.filter-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.filter-btn {
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text2);
  padding: 6px 14px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 12px;
  font-family: var(--font-mono);
  font-weight: 500;
  transition: background .15s, color .15s, border-color .15s;
}
.filter-btn:hover, .filter-btn.active {
  background: var(--surface3);
  color: var(--gold);
  border-color: var(--gold-dim);
}

/* ---- Entry grid ---- */
.entry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
.entry-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 20px;
  text-decoration: none;
  display: block;
  transition: border-color .15s, background .15s;
}
.entry-card:hover {
  border-color: var(--gold-dim);
  background: var(--surface2);
}
.card-id {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--gold);
  font-weight: 600;
  letter-spacing: .06em;
  margin-bottom: 6px;
}
.card-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 10px;
  line-height: 1.4;
}
.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* ---- Status badges ---- */
.status-badge {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: .06em;
}
.status-active     { background: #0f2f1e; color: #1A9A5A; border: 1px solid #1A9A5A44; }
.status-registered { background: #0f1f30; color: #2A7AC0; border: 1px solid #2A7AC044; }
.status-confirmed  { background: #1f1000; color: #D4850A; border: 1px solid #D4850A44; }
.status-candidate  { background: #200f30; color: #7A3A9A; border: 1px solid #7A3A9A44; }
.status-superseded { background: #1f1010; color: #C0392B; border: 1px solid #C0392B44; }
.status-disconfirmed { background: #1f1010; color: #C0392B; border: 1px solid #C0392B44; }
.status-pending    { background: #221800; color: #C9A84C; border: 1px solid #C9A84C44; }
.status-gap        { background: #1a1a1a; color: #6A7A88; border: 1px solid #6A7A8844; }
.status-unknown    { background: #1a1a1a; color: #6A7A88; border: 1px solid #6A7A8844; }

.class-badge {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 3px;
  letter-spacing: .06em;
  background: var(--surface2);
  color: var(--text3);
  border: 1px solid var(--border);
}

/* ---- Finding detail page ---- */
.finding-header {
  padding: 40px 0 28px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 32px;
}
.finding-id {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--gold);
  font-weight: 600;
  letter-spacing: .06em;
  margin-bottom: 8px;
}
.finding-title {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
  margin-bottom: 16px;
}
.finding-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.finding-meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 20px;
  margin-bottom: 32px;
}
.meta-item label {
  display: block;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text3);
  letter-spacing: .06em;
  text-transform: uppercase;
  margin-bottom: 3px;
}
.meta-item span {
  font-size: 13px;
  color: var(--text2);
}

/* ---- Tags ---- */
.tag {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--teal);
  background: #071f1f;
  border: 1px solid #1A9A9A33;
  padding: 2px 8px;
  border-radius: 3px;
}
.tags-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 24px; }

/* ---- Body content ---- */
.finding-body { max-width: 760px; }
.finding-body h2 {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--text);
  margin: 30px 0 12px;
}
.finding-body h3 {
  font-family: var(--font-display);
  font-size: 18px;
  color: var(--text);
  margin: 28px 0 10px;
}
.finding-body h4 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text2);
  margin: 20px 0 8px;
}
.finding-body p {
  color: var(--text2);
  margin-bottom: 12px;
}
.finding-body ul, .finding-body ol {
  padding-left: 20px;
  color: var(--text2);
  margin-bottom: 12px;
}
.finding-body li { margin-bottom: 4px; }
.finding-body strong { color: var(--text); }
.finding-body blockquote {
  border-left: 3px solid var(--gold-dim);
  padding-left: 14px;
  margin: 14px 0;
}
.finding-body blockquote p { color: var(--text2); }
.finding-body code {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--surface2);
  padding: 1px 5px;
  border-radius: 3px;
  color: var(--text2);
}
.finding-body pre {
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 14px 16px;
  overflow-x: auto;
  margin: 12px 0;
}
.finding-body pre code {
  background: none;
  padding: 0;
  font-size: 12px;
  line-height: 1.6;
  color: var(--text3);
}
.finding-body hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 24px 0;
}
.finding-body a {
  color: var(--teal);
  text-decoration: none;
}
.finding-body a:hover { text-decoration: underline; }
.minimal-notice {
  border: 1px dashed var(--border2);
  background: var(--surface);
  border-radius: 6px;
  padding: 12px 14px;
}
.minimal-notice p:last-child { margin-bottom: 0; }

/* ---- Back link ---- */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text3);
  text-decoration: none;
  margin-bottom: 32px;
  padding: 6px 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  transition: color .15s;
}
.back-link:hover { color: var(--gold); border-color: var(--gold-dim); }

/* ---- Footer ---- */
.site-footer {
  border-top: 1px solid var(--border);
  padding: 24px 32px;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text3);
}

/* ---- Search / filter JS utility ---- */
.hidden { display: none !important; }
"""


# ===========================================================================
# HTML page builders
# ===========================================================================

_GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=IBM+Plex+Mono:wght@400;500;600"
    "&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;0,9..144,700;1,9..144,300"
    "&family=DM+Sans:wght@300;400;500;600"
    "&display=swap"
)


def _header(root: str = ".") -> str:
    assets = f"{root}/assets/style.css"
    return (
        f'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        f'<link rel="stylesheet" href="{_GOOGLE_FONTS}">\n'
        f'<link rel="stylesheet" href="{assets}">\n'
    )


def _site_header(root: str = ".") -> str:
    index = f"{root}/index.html"
    return (
        '<header class="site-header">\n'
        f'  <a class="site-logo" href="{index}">HumanAIOS Registry</a>\n'
        '  <nav class="site-nav">\n'
        f'    <a href="{index}">← All findings</a>\n'
        '    <a href="https://github.com/humanaios-ui/operations" '
        '       rel="noopener noreferrer" target="_blank">GitHub</a>\n'
        '  </nav>\n'
        '</header>\n'
    )


def _site_footer(generated_at: str) -> str:
    return (
        f'<footer class="site-footer">'
        f'Generated by {TOOL_NAME} v{TOOL_VERSION} · '
        f'{generated_at} · '
        f'Source: <a href="https://github.com/humanaios-ui/operations/blob/main/REGISTERED.md" '
        f'target="_blank" rel="noopener noreferrer">REGISTERED.md</a>'
        f'</footer>\n'
    )


def _status_badge(status: str) -> str:
    css = STATUS_CLASS.get(status.upper(), "status-unknown")
    return f'<span class="status-badge {css}">{html.escape(status)}</span>'


def _class_badge(cls: str) -> str:
    label = CLASS_LABEL.get(cls.upper(), cls)
    return f'<span class="class-badge">{html.escape(label)}</span>'


def _safe_id(entry_id: str) -> str:
    """Convert an entry ID to a filesystem-safe filename base."""
    return re.sub(r'[^A-Za-z0-9_-]', '_', entry_id)


def build_finding_page(entry: dict[str, Any], all_entries: list[dict[str, Any]], generated_at: str) -> str:
    meta = entry["yaml_meta"]
    eid = entry["id"]
    cls = entry["class"]
    status = entry["status"]
    title = entry["title"]

    tags: list[str] = meta.get("tags", []) or []
    tags = [str(t) for t in tags if not _is_nullish(t)]
    principles: list[str] = meta.get("principles_triggered", []) or []
    principles = [str(p) for p in principles if not _is_nullish(p)]

    date_reg = meta.get("date_registered", "")
    date_orig = meta.get("date_origin", "")
    session_reg = meta.get("session_registered", "")
    substrate = meta.get("substrate", "")
    superseded_by = meta.get("superseded_by")
    name_slug = meta.get("name", "")

    body_html = _md_to_html(entry["body_md"]).strip()
    if not body_html:
        body_html = (
            '<div class="minimal-notice">'
            '<p>Minimal registry stub — canonical reference only.</p>'
            '<p>See source registry for current status/context.</p>'
            '</div>'
        )

    # Build meta grid items
    meta_items: list[tuple[str, str]] = []
    if cls and not _is_nullish(cls):
        meta_items.append(("Class", CLASS_LABEL.get(cls.upper(), cls)))
    if status and not _is_nullish(status):
        meta_items.append(("Status", status))
    if date_reg and not _is_nullish(date_reg):
        meta_items.append(("Date registered", str(date_reg)))
    if date_orig and not _is_nullish(date_orig) and date_orig != date_reg:
        meta_items.append(("Date origin", str(date_orig)))
    if session_reg and not _is_nullish(session_reg):
        meta_items.append(("Session", str(session_reg)))
    if substrate and not _is_nullish(substrate):
        meta_items.append(("Substrate", str(substrate)))
    if principles:
        meta_items.append(("Principles", ", ".join(principles)))
    if superseded_by and not _is_nullish(superseded_by):
        meta_items.append(("Superseded by", str(superseded_by)))

    meta_html = "\n".join(
        f'<div class="meta-item"><label>{html.escape(k)}</label>'
        f'<span>{html.escape(v)}</span></div>'
        for k, v in meta_items
    )

    tags_html = ""
    if tags:
        tag_spans = " ".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags)
        tags_html = f'<div class="tags-row">{tag_spans}</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(eid)} — {html.escape(title)} · HumanAIOS Registry</title>
{_header("..")}
</head>
<body>
{_site_header("..")}
<main class="container">
  <a class="back-link" href="../index.html">← Back to registry</a>

  <div class="finding-header">
    <div class="finding-id">{html.escape(eid)}</div>
    <h1 class="finding-title">{html.escape(title)}</h1>
    <div class="finding-badges">
      {_status_badge(status) if status else ""}
      {_class_badge(cls)}
    </div>
    {f'<p style="font-family:var(--font-mono);font-size:11px;color:var(--text3)">slug: {html.escape(name_slug)}</p>' if name_slug and name_slug != eid else ""}
  </div>

  {"<div class='finding-meta-grid'>" + meta_html + "</div>" if meta_html else ""}
  {tags_html}

  <div class="finding-body">
    {body_html}
  </div>
</main>
{_site_footer(generated_at)}
</body>
</html>
"""


def build_index_page(entries: list[dict[str, Any]], generated_at: str) -> str:
    # Counts per class
    class_counts: dict[str, int] = {}
    for e in entries:
        class_counts[e["class"]] = class_counts.get(e["class"], 0) + 1

    filter_buttons = (
        '<button class="filter-btn active" data-filter="all">All '
        f'({len(entries)})</button>\n'
    )
    for cls, count in sorted(class_counts.items()):
        label = CLASS_LABEL.get(cls.upper(), cls)
        filter_buttons += (
            f'<button class="filter-btn" data-filter="{html.escape(cls)}">'
            f'{html.escape(label)} ({count})</button>\n'
        )

    cards = ""
    for e in entries:
        eid = e["id"]
        safe = _safe_id(eid)
        status = e["status"]
        cls = e["class"]
        title = e["title"]
        status_badge = _status_badge(status) if status else ""
        class_badge = _class_badge(cls)
        cards += (
            f'<a class="entry-card" href="findings/{safe}.html" '
            f'data-class="{html.escape(cls)}">\n'
            f'  <div class="card-id">{html.escape(eid)}</div>\n'
            f'  <div class="card-title">{html.escape(title)}</div>\n'
            f'  <div class="card-footer">{status_badge} {class_badge}</div>\n'
            f'</a>\n'
        )

    filter_js = """
<script>
(function(){
  var btns = document.querySelectorAll('.filter-btn');
  var cards = document.querySelectorAll('.entry-card');
  btns.forEach(function(btn){
    btn.addEventListener('click', function(){
      btns.forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      var f = btn.dataset.filter;
      cards.forEach(function(c){
        if(f === 'all' || c.dataset.class === f){
          c.classList.remove('hidden');
        } else {
          c.classList.add('hidden');
        }
      });
    });
  });
})();
</script>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HumanAIOS Registry — Research Findings</title>
{_header(".")}
</head>
<body>
{_site_header(".")}
<main class="container">
  <div class="index-hero">
    <h1>Research Registry</h1>
    <p>
      The canonical index of registered findings (F-class), process corrections (IC-class),
      and active hypotheses (H-class) from HumanAIOS research operations.
      Each entry preserves its original append-only record from
      <a href="https://github.com/humanaios-ui/operations/blob/main/REGISTERED.md"
         target="_blank" rel="noopener noreferrer">REGISTERED.md</a>.
    </p>
    <div class="index-meta">
      Generated {generated_at} · {len(entries)} entries ·
      Source: humanaios-ui/operations/REGISTERED.md
    </div>
  </div>

  <div class="filter-bar">
    {filter_buttons}
  </div>

  <div class="entry-grid">
    {cards}
  </div>
</main>
{_site_footer(generated_at)}
{filter_js}
</body>
</html>
"""


# ===========================================================================
# Site writer
# ===========================================================================

def write_site(entries: list[dict[str, Any]], out_dir: Path, generated_at: str) -> dict[str, Any]:
    """Write the complete site to *out_dir*. Returns a summary dict."""
    findings_dir = out_dir / "findings"
    assets_dir = out_dir / "assets"
    findings_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Remove stale finding pages from a previous run so old IDs don't linger.
    for stale in findings_dir.glob("*.html"):
        stale.unlink()

    # CSS
    (assets_dir / "style.css").write_text(STYLESHEET, encoding="utf-8")

    # Per-entry pages
    written: list[str] = []
    skipped: list[str] = []
    for entry in entries:
        safe = _safe_id(entry["id"])
        page_html = build_finding_page(entry, entries, generated_at)
        out_path = findings_dir / f"{safe}.html"
        out_path.write_text(page_html, encoding="utf-8")
        written.append(entry["id"])

    # Index
    index_html = build_index_page(entries, generated_at)
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

    return {
        "index": str(out_dir / "index.html"),
        "findings_dir": str(findings_dir),
        "written": written,
        "skipped": skipped,
        "total": len(entries),
    }


# ===========================================================================
# Core run()  (Builder v1.7 interface)
# ===========================================================================

def run(spec: dict) -> dict:
    """
    Execute the site generator.

    Spec keys (all optional):
      registry  — path to REGISTERED.md  (default: repo root)
      out       — output directory        (default: site/)
    """
    started = datetime.now(timezone.utc).isoformat()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    registry_path = Path(spec.get("registry", DEFAULT_REGISTRY))
    out_dir = Path(spec.get("out", DEFAULT_OUT))

    if not registry_path.exists():
        return {
            "tool_name": TOOL_NAME, "tool_version": TOOL_VERSION,
            "status": "error",
            "error": f"Registry file not found: {registry_path}",
            "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    entries = parse_registry(registry_path)
    summary = write_site(entries, out_dir, generated_at)

    finished = datetime.now(timezone.utc).isoformat()
    return {
        "tool_name": TOOL_NAME,
        "tool_version": TOOL_VERSION,
        "status": "ok",
        "started_at": started,
        "finished_at": finished,
        "result": {
            "registry": str(registry_path),
            "out_dir": str(out_dir),
            "entries_parsed": summary["total"],
            "pages_written": len(summary["written"]),
            "index": summary["index"],
            "findings_dir": summary["findings_dir"],
        },
    }


# ===========================================================================
# Smoke test
# ===========================================================================

def run_smoke_test() -> bool:
    """Quick validation using the real REGISTERED.md."""
    try:
        entries = parse_registry(DEFAULT_REGISTRY)
        assert len(entries) >= 20, f"Too few entries parsed: {len(entries)}"
        f_entries = [e for e in entries if e["class"] == "F"]
        ic_entries = [e for e in entries if e["class"] == "IC"]
        h_entries = [e for e in entries if e["class"] == "H"]
        assert f_entries, "No F-class entries found"
        assert ic_entries, "No IC-class entries found"
        assert h_entries, "No H-class entries found"
        # Check a known entry
        f18 = next((e for e in entries if e["id"] == "F-18"), None)
        assert f18 is not None, "F-18 not found"
        print(
            f"[smoke] PASSED — {len(entries)} entries "
            f"(F={len(f_entries)}, IC={len(ic_entries)}, H={len(h_entries)})",
            file=sys.stderr,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[smoke] FAILED: {exc}", file=sys.stderr)
        return False


# ===========================================================================
# Optional MCP surface  (graceful fallback if fastmcp not installed)
# ===========================================================================

try:
    from fastmcp import FastMCP  # type: ignore
    mcp = FastMCP(TOOL_NAME)

    @mcp.tool(name=TOOL_NAME, description="Generate static HTML site from REGISTERED.md.")
    def registry_site_generator(spec: dict) -> dict:
        """MCP wrapper around run()."""
        return run(spec)

    _HAS_MCP = True
except ImportError:
    _HAS_MCP = False


# ===========================================================================
# CLI
# ===========================================================================

def main() -> None:
    p = argparse.ArgumentParser(
        description=f"{TOOL_NAME} v{TOOL_VERSION} — "
                    "Generate static HTML research site from REGISTERED.md"
    )
    p.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY),
        help="Path to REGISTERED.md (default: repo root)",
    )
    p.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="Output directory for site/ (default: <repo>/site/)",
    )
    p.add_argument("--smoke", action="store_true", help="Run smoke test and exit")
    p.add_argument("--serve", action="store_true", help="Run as MCP server (requires fastmcp)")
    p.add_argument(
        "--report",
        default=f"reports/{TOOL_NAME}.json",
        help="Write JSON report to this path",
    )
    args = p.parse_args()

    if args.serve:
        if not _HAS_MCP:
            print("ERROR: fastmcp not installed. Cannot start MCP server.", file=sys.stderr)
            sys.exit(1)
        mcp.run()
        return

    if args.smoke:
        sys.exit(0 if run_smoke_test() else 1)

    spec = {"registry": args.registry, "out": args.out}
    out = run(spec)

    # Write JSON report
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(report_path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, default=str)
        f.write("\n")
    os.replace(tmp, str(report_path))

    # Human-readable summary
    if out.get("status") == "ok":
        r = out["result"]
        print(
            f"\n✓ Site generated — {r['pages_written']} finding pages + index\n"
            f"  Index:    {r['index']}\n"
            f"  Findings: {r['findings_dir']}/\n"
            f"  Report:   {args.report}\n",
            file=sys.stderr,
        )
    else:
        print(f"ERROR: {out.get('error', 'unknown')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
checker.py — HumanAIOS Funding Pipeline
Ping every opportunity URL, flag dead links, scrape inline deadline hints,
and write an updated JSON back to disk with last_checked / url_ok stamps.

Usage:
    python -m src.humanaios_funding.checker [data_path] [out_json]
    python -m src.humanaios_funding.checker data/sources.json data/sources.json
    python -m src.humanaios_funding.checker              # uses defaults

Exit code 1 if any dead links or imminent deadlines (<= 7 days) are found
so GitHub Actions can treat it as a signal without reading stdout.
"""
from __future__ import annotations

import re
import sys
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from .loader import load_any, save_json, summarise
from .schema import Opportunity

# ─── Constants ─────────────────────────────────────────────────────────────

DEFAULT_DATA = "data/sources.json"
DEFAULT_OUT  = "data/sources.json"

HEADERS = {
    "User-Agent": (
        "humanaios-funding-pipeline/1.0 "
        "(+https://github.com/humanaios-ui/humanaios-funding-pipeline)"
    )
}

# Generous timeout — some grant pages are slow
TIMEOUT = 25

# Retry config
MAX_RETRIES  = 2
RETRY_DELAY  = 3   # seconds

# Grab any text that looks like a deadline near relevant keywords
DEADLINE_KEYWORDS_RE = re.compile(
    r"(?:deadline|due date|closes?|apply by|submit by|applications? due)"
    r"[^.\n<]{0,60}"
    r"((?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"\.?\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)

ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


# ─── Core helpers ──────────────────────────────────────────────────────────

def _get_with_retry(url: str) -> Tuple[Optional[requests.Response], str]:
    """Return (response, error_string). error_string is '' on success."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.get(
                url, headers=HEADERS, timeout=TIMEOUT,
                allow_redirects=True
            )
            return r, ""
        except requests.exceptions.Timeout:
            err = "TIMEOUT"
        except requests.exceptions.SSLError as e:
            return None, f"SSL_ERROR: {e}"
        except requests.exceptions.ConnectionError as e:
            err = f"CONN_ERROR: {type(e).__name__}"
        except requests.RequestException as e:
            return None, f"REQUEST_ERROR: {type(e).__name__}: {e}"

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)
    return None, err


def _scrape_deadline(html: str) -> Optional[str]:
    """Try to extract a deadline date string from page text."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script/style noise
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = soup.get_text(" ", strip=True)
    except Exception:
        return None

    m = DEADLINE_KEYWORDS_RE.search(text)
    if m:
        return m.group(1)
    return None


def check_url(opp: Opportunity) -> Tuple[bool, Optional[str], str]:
    """
    Returns:
        (alive: bool, deadline_hint: str | None, error_msg: str)
    """
    resp, err = _get_with_retry(opp.url)
    if resp is None:
        return False, None, err
    if resp.status_code >= 400:
        return False, None, f"HTTP_{resp.status_code}"
    hint = _scrape_deadline(resp.text)
    return True, hint, ""


# ─── Main runner ───────────────────────────────────────────────────────────

class CheckReport:
    def __init__(self):
        self.dead:     List[str] = []
        self.hints:    List[str] = []
        self.soon_30:  List[str] = []
        self.soon_7:   List[str] = []
        self.ok:       int = 0

    def has_critical(self) -> bool:
        return bool(self.dead or self.soon_7)

    def to_lines(self) -> List[str]:
        lines = []
        for msg in self.dead:
            lines.append(f"❌ DEAD_LINK: {msg}")
        for msg in self.soon_7:
            lines.append(f"🚨 DEADLINE_IMMINENT (<=7d): {msg}")
        for msg in self.soon_30:
            lines.append(f"⚠️  DEADLINE_SOON (<=30d): {msg}")
        for msg in self.hints:
            lines.append(f"🔍 DEADLINE_SCRAPED: {msg}")
        lines.append(f"\n✅ OK: {self.ok} / total: {self.ok + len(self.dead)}")
        return lines

    def to_github_summary(self) -> str:
        """Markdown summary for GitHub Actions step summary."""
        lines = ["## Funding Pipeline Refresh", ""]
        if self.dead:
            lines += ["### ❌ Dead Links", ""]
            for m in self.dead:
                lines.append(f"- {m}")
            lines.append("")
        if self.soon_7:
            lines += ["### 🚨 Deadlines ≤7 days", ""]
            for m in self.soon_7:
                lines.append(f"- {m}")
            lines.append("")
        if self.soon_30:
            lines += ["### ⚠️ Deadlines ≤30 days", ""]
            for m in self.soon_30:
                lines.append(f"- {m}")
            lines.append("")
        lines.append(f"**Links OK:** {self.ok} | "
                     f"**Dead:** {len(self.dead)} | "
                     f"**Imminent:** {len(self.soon_7)} | "
                     f"**Soon:** {len(self.soon_30)}")
        return "\n".join(lines)


def run(
    data_path: str = DEFAULT_DATA,
    out_json:  str | None = None,
    verbose:   bool = True,
) -> CheckReport:
    items = load_any(data_path)
    report = CheckReport()
    today  = date.today().isoformat()

    print(f"[checker] {len(items)} opportunities — starting URL checks …")

    for i, opp in enumerate(items, 1):
        if verbose:
            print(f"  [{i:>3}/{len(items)}] {opp.name[:55]:<55}", end=" ", flush=True)

        alive, hint, err = check_url(opp)
        opp.last_checked = today
        opp.url_ok = alive

        if not alive:
            report.dead.append(f"{opp.name} → {opp.url} ({err})")
            if verbose:
                print(f"❌ {err}")
        else:
            report.ok += 1
            if verbose:
                print("✅")

        if hint:
            report.hints.append(f"{opp.name}: scraped '{hint}'")

        if opp.is_deadline_soon(7):
            report.soon_7.append(f"{opp.name} on {opp.deadline}")
        elif opp.is_deadline_soon(30):
            report.soon_30.append(f"{opp.name} on {opp.deadline}")

        # Polite crawl delay
        time.sleep(0.4)

    if out_json:
        save_json(items, out_json)
        print(f"[checker] Saved updated data → {out_json}")

    return report


# ─── CLI entry ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    data  = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA
    out   = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT

    report = run(data_path=data, out_json=out)

    print("\n" + "=" * 60)
    for line in report.to_lines():
        print(line)

    # Write GitHub Actions step summary if running in CI
    summary_path = Path(
        __import__("os").environ.get("GITHUB_STEP_SUMMARY", "")
    )
    if summary_path.name:
        summary_path.write_text(report.to_github_summary(), encoding="utf-8")

    sys.exit(1 if report.has_critical() else 0)

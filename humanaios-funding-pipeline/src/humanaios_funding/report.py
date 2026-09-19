"""
report.py — HumanAIOS Funding Pipeline
Generate a sorted human-readable OPPORTUNITIES.md from the data source.

Usage:
    python -m src.humanaios_funding.report
    python -m src.humanaios_funding.report data/sources.json reports/OPPORTUNITIES.md
"""
from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

from .loader import load_any, summarise
from .schema import Category

# ─── Priority ordering ─────────────────────────────────────────────────────

CATEGORY_ORDER = {
    "native": 0, "ai_safety": 1, "research_grant": 2,
    "contest": 3, "compute_credit": 4, "fellowship": 5,
    "paid_work": 6, "free_api": 7, "free_infra": 8, "publishing": 9,
}

CATEGORY_LABELS = {
    "native":         "🏛️  Native American / Indigenous",
    "ai_safety":      "🛡️  AI Safety / Alignment",
    "research_grant": "🔬 Research Grants",
    "contest":        "🏆 Contests / Prizes / Hackathons",
    "compute_credit": "☁️  Cloud / Compute Credits",
    "fellowship":     "🎓 Fellowships & Stipended Programs",
    "paid_work":      "💰 Paid Work / Gig Income",
    "free_api":       "🆓 Free LLM API Tiers",
    "free_infra":     "🖥️  Free Infrastructure",
    "publishing":     "📄 Publishing / Open Science",
}

DEFAULTS = {
    "data": "data/sources.json",
    "out":  "reports/OPPORTUNITIES.md",
}


# ─── Generator ─────────────────────────────────────────────────────────────

def generate(
    data_path: str = DEFAULTS["data"],
    out_path:  str = DEFAULTS["out"],
) -> str:
    items = load_any(data_path)
    items.sort(key=lambda i: (CATEGORY_ORDER.get(i.category.value, 99),
                               i.name.lower()))
    by_cat = defaultdict(list)
    for i in items:
        by_cat[i.category.value].append(i)

    summ = summarise(items)

    # ── Header ────────────────────────────────────────────────────────────
    lines = [
        f"# HumanAIOS Funding & Resource Pipeline",
        f"",
        f"> Auto-generated {summ.generated} · "
        f"[data/sources.json](../data/sources.json) · "
        f"[Refresh workflow](../.github/workflows/refresh.yml)",
        f"",
        f"## Pipeline Summary",
        f"",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| **Total opportunities** | {summ.total} |",
        f"| Native-eligible | {summ.native_eligible} |",
        f"| AI-safety relevant | {summ.ai_safety_relevant} |",
        f"| **Both flags (highest priority)** | **{summ.both_flags}** |",
        f"| Active / rolling | {summ.active_rolling} |",
        f"| Deadlines ≤30 days | {summ.deadline_soon_30d} |",
        f"",
        f"---",
        f"",
        f"## Contents",
        f"",
    ]

    # ── TOC ───────────────────────────────────────────────────────────────
    for cat in sorted(by_cat, key=lambda c: CATEGORY_ORDER.get(c, 99)):
        label  = CATEGORY_LABELS.get(cat, cat)
        anchor = cat.replace("_", "-")
        count  = len(by_cat[cat])
        lines.append(f"- [{label}](#{anchor}) ({count})")
    lines += ["", "---", ""]

    # ── Per-category tables ───────────────────────────────────────────────
    for cat in sorted(by_cat, key=lambda c: CATEGORY_ORDER.get(c, 99)):
        label = CATEGORY_LABELS.get(cat, cat)
        lines.append(f"## {label}")
        lines.append("")
        lines.append("| Name | Sponsor | Award | Timing | Native | AI-Safety | Status | Notes |")
        lines.append("|------|---------|-------|--------|:------:|:---------:|--------|-------|")

        for i in sorted(by_cat[cat], key=lambda x: x.name.lower()):
            award   = (i.award_size or "—").replace("|", "/")
            timing  = (i.deadline or i.deadline_cadence or "—").replace("|", "/")
            notes   = (i.notes or "—").replace("|", ";")[:80]
            native  = "✅" if i.native_eligible else ""
            safety  = "✅" if i.ai_safety_relevant else ""
            warn    = " ⚠️" if i.is_deadline_soon(30) else ""
            status  = i.status.value + warn

            lines.append(
                f"| [{i.name}]({i.url}) "
                f"| {i.sponsor} "
                f"| {award} "
                f"| {timing} "
                f"| {native} "
                f"| {safety} "
                f"| {status} "
                f"| {notes} |"
            )
        lines.append("")

    # ── Footer ────────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "## How to update",
        "",
        "1. Edit `data/sources.json` or `data/sources.csv`.",
        "2. Run `python -m src.humanaios_funding.checker data/sources.json data/sources.json`.",
        "3. Run `python -m src.humanaios_funding.report` to regenerate this file.",
        "4. Commit both. The weekly GitHub Actions workflow does all of this automatically.",
        "",
        f"*Last generated: {date.today().isoformat()}*",
    ]

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


# ─── CLI entry ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    data = sys.argv[1] if len(sys.argv) > 1 else DEFAULTS["data"]
    out  = sys.argv[2] if len(sys.argv) > 2 else DEFAULTS["out"]
    path = generate(data, out)
    print(f"[report] Wrote → {path}")

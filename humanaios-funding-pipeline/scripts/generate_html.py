#!/usr/bin/env python3
"""
scripts/generate_html.py — HumanAIOS Funding Pipeline
=======================================================
Generate a standalone, self-contained HTML summary from data/sources.json.
No external CDN dependencies — everything is embedded inline.

Features:
  - Dark ACAT-brand theme (matches humanaios.ai palette)
  - Live text search / filter bar
  - Click-to-filter badges (category, native, AI-safety)
  - Sortable columns
  - SVG donut chart by category
  - Deadline countdown badges (imminent / soon / rolling)
  - "Both flags" (Native + AI-safety) row highlight
  - Exportable as a single .html file — no server needed

Usage:
    python scripts/generate_html.py
    python scripts/generate_html.py data/sources.json reports/index.html
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import List

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from humanaios_funding.loader import load_any, summarise
from humanaios_funding.schema import Opportunity

DEFAULTS = {
    "data": str(REPO_ROOT / "data" / "sources.json"),
    "out":  str(REPO_ROOT / "reports" / "index.html"),
}

# ─── Category colours (CSS vars) ───────────────────────────────────────────
CAT_COLORS = {
    "native":         "#c084fc",
    "ai_safety":      "#34d399",
    "research_grant": "#60a5fa",
    "contest":        "#fbbf24",
    "compute_credit": "#38bdf8",
    "fellowship":     "#a78bfa",
    "paid_work":      "#4ade80",
    "free_api":       "#f97316",
    "free_infra":     "#94a3b8",
    "publishing":     "#e2e8f0",
}

CAT_LABELS = {
    "native":         "🏛️ Native",
    "ai_safety":      "🛡️ AI Safety",
    "research_grant": "🔬 Research Grant",
    "contest":        "🏆 Contest",
    "compute_credit": "☁️ Compute",
    "fellowship":     "🎓 Fellowship",
    "paid_work":      "💰 Paid Work",
    "free_api":       "🆓 Free API",
    "free_infra":     "🖥️ Free Infra",
    "publishing":     "📄 Publishing",
}


def _deadline_badge(opp: Opportunity) -> str:
    if not opp.deadline:
        return f'<span class="badge badge-rolling">{opp.deadline_cadence or "—"}</span>'
    try:
        d = datetime.strptime(opp.deadline.strip(), "%Y-%m-%d").date()
        delta = (d - date.today()).days
        if delta < 0:
            return f'<span class="badge badge-closed">Closed</span>'
        if delta <= 7:
            return f'<span class="badge badge-imminent">⚠️ {delta}d left</span>'
        if delta <= 30:
            return f'<span class="badge badge-soon">⏰ {delta}d</span>'
        return f'<span class="badge badge-ok">{opp.deadline}</span>'
    except ValueError:
        return f'<span class="badge badge-rolling">{opp.deadline}</span>'


def _build_donut_svg(counts: dict) -> str:
    """Generate an inline SVG donut chart from category counts."""
    total = sum(counts.values()) or 1
    cx, cy, r, thick = 80, 80, 60, 22
    import math

    def polar(cx, cy, r, angle_deg):
        rad = math.radians(angle_deg - 90)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    paths = []
    start = 0.0
    for cat, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        frac  = cnt / total
        deg   = frac * 360
        large = 1 if deg > 180 else 0
        end   = start + deg
        x1, y1 = polar(cx, cy, r, start)
        x2, y2 = polar(cx, cy, r, end - 0.01)
        xi, yi = polar(cx, cy, r - thick, start)
        xo, yo = polar(cx, cy, r - thick, end - 0.01)
        color  = CAT_COLORS.get(cat, "#64748b")
        label  = CAT_LABELS.get(cat, cat)
        d      = (f"M {x1:.1f} {y1:.1f} "
                  f"A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} "
                  f"L {xo:.1f} {yo:.1f} "
                  f"A {r-thick} {r-thick} 0 {large} 0 {xi:.1f} {yi:.1f} Z")
        paths.append(
            f'<path d="{d}" fill="{color}" opacity="0.9">'
            f'<title>{label}: {cnt}</title></path>'
        )
        start = end

    inner = (
        f'<text x="{cx}" y="{cy-6}" text-anchor="middle" '
        f'fill="#e2e8f0" font-size="18" font-weight="bold">{total}</text>'
        f'<text x="{cx}" y="{cy+12}" text-anchor="middle" '
        f'fill="#94a3b8" font-size="9">opps</text>'
    )
    return (
        f'<svg width="160" height="160" viewBox="0 0 160 160" '
        f'xmlns="http://www.w3.org/2000/svg">'
        + "".join(paths) + inner + "</svg>"
    )


def _rows_html(items: List[Opportunity]) -> str:
    rows = []
    for i in items:
        highlight = " row-both" if (i.native_eligible and i.ai_safety_relevant) else ""
        cat_color = CAT_COLORS.get(i.category.value, "#64748b")
        cat_label = CAT_LABELS.get(i.category.value, i.category.value)
        native_badge  = '<span class="flag-badge native">NATIVE</span>'  if i.native_eligible    else ""
        safety_badge  = '<span class="flag-badge safety">AISAFETY</span>' if i.ai_safety_relevant else ""
        deadline_html = _deadline_badge(i)
        award = i.award_size or "—"
        notes = (i.notes or "").replace("<", "&lt;").replace(">", "&gt;")
        name_safe = i.name.replace("'", "&#39;")

        # Data attributes used by JS filter
        da = (
            f'data-cat="{i.category.value}" '
            f'data-native="{str(i.native_eligible).lower()}" '
            f'data-safety="{str(i.ai_safety_relevant).lower()}" '
            f'data-name="{name_safe}" '
            f'data-status="{i.status.value}"'
        )

        rows.append(f"""
        <tr class="opp-row{highlight}" {da}>
          <td>
            <a href="{i.url}" target="_blank" rel="noopener">{i.name}</a>
            <div class="flags">{native_badge}{safety_badge}</div>
          </td>
          <td>
            <span class="cat-pill" style="background:{cat_color}22;
              color:{cat_color}; border:1px solid {cat_color}55;">
              {cat_label}
            </span>
          </td>
          <td>{i.sponsor}</td>
          <td class="award">{award}</td>
          <td>{deadline_html}</td>
          <td class="notes-col" title="{notes}">{notes[:70]}{'…' if len(notes)>70 else ''}</td>
        </tr>""")
    return "\n".join(rows)


def generate(
    data_path: str = DEFAULTS["data"],
    out_path:  str = DEFAULTS["out"],
) -> str:
    items = load_any(data_path)
    items.sort(key=lambda i: (i.priority_score(), i.name.lower()))
    summ  = summarise(items)
    donut = _build_donut_svg(summ.by_category)
    rows  = _rows_html(items)
    today = date.today().isoformat()

    # Legend items for donut
    legend_items = "".join(
        f'<li><span class="legend-swatch" style="background:{CAT_COLORS.get(cat,"#999")}"></span>'
        f'{CAT_LABELS.get(cat,cat)} ({cnt})</li>'
        for cat, cnt in sorted(summ.by_category.items(), key=lambda x: -x[1])
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>HumanAIOS Funding Pipeline — {today}</title>
<style>
:root {{
  --bg:       #0f172a;
  --surface:  #1e293b;
  --border:   #334155;
  --text:     #e2e8f0;
  --muted:    #94a3b8;
  --accent:   #c084fc;
  --green:    #34d399;
  --yellow:   #fbbf24;
  --red:      #f87171;
  --blue:     #60a5fa;
}}
*, *::before, *::after {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  background:var(--bg); color:var(--text);
  font-family:'Inter',system-ui,sans-serif; font-size:14px;
  line-height:1.6;
}}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}

/* ── Header ── */
header {{
  background:linear-gradient(135deg,#1a0533 0%,#0f172a 60%);
  border-bottom:1px solid var(--border);
  padding:24px 32px;
  display:flex; align-items:center; gap:24px; flex-wrap:wrap;
}}
header h1 {{
  font-size:22px; font-weight:700; color:var(--accent); letter-spacing:-.5px;
}}
header .subtitle {{ font-size:12px; color:var(--muted); margin-top:2px; }}

/* ── Summary cards ── */
.stats {{
  display:flex; flex-wrap:wrap; gap:12px;
  padding:20px 32px; background:var(--surface);
  border-bottom:1px solid var(--border);
}}
.stat-card {{
  background:var(--bg); border:1px solid var(--border);
  border-radius:8px; padding:12px 18px; min-width:110px;
  text-align:center;
}}
.stat-card .num {{ font-size:28px; font-weight:700; color:var(--accent); }}
.stat-card .lbl {{ font-size:11px; color:var(--muted); margin-top:2px; }}

/* ── Charts row ── */
.charts-row {{
  display:flex; align-items:center; gap:32px;
  padding:20px 32px; border-bottom:1px solid var(--border);
  flex-wrap:wrap;
}}
.legend {{ list-style:none; display:flex; flex-wrap:wrap; gap:8px 20px; }}
.legend li {{ display:flex; align-items:center; gap:6px; font-size:12px; color:var(--muted); }}
.legend-swatch {{ width:12px; height:12px; border-radius:3px; flex-shrink:0; }}

/* ── Controls ── */
.controls {{
  padding:14px 32px; display:flex; gap:10px; flex-wrap:wrap;
  background:var(--surface); border-bottom:1px solid var(--border);
  align-items:center;
}}
.controls input[type=text] {{
  background:var(--bg); border:1px solid var(--border);
  border-radius:6px; padding:7px 12px; color:var(--text);
  font-size:13px; width:220px;
}}
.controls input[type=text]::placeholder {{ color:var(--muted); }}
.filter-btn {{
  background:var(--bg); border:1px solid var(--border);
  border-radius:6px; padding:6px 12px; color:var(--muted);
  font-size:12px; cursor:pointer; transition:all .15s;
}}
.filter-btn:hover, .filter-btn.active {{
  background:var(--accent); color:#0f172a;
  border-color:var(--accent); font-weight:600;
}}
.controls label {{ font-size:12px; color:var(--muted); }}

/* ── Table ── */
.table-wrap {{ overflow-x:auto; padding:0 32px 32px; }}
table {{
  width:100%; border-collapse:collapse;
  font-size:13px; margin-top:16px;
}}
thead th {{
  background:var(--surface); color:var(--muted);
  text-transform:uppercase; font-size:11px; letter-spacing:.5px;
  padding:10px 12px; text-align:left; border-bottom:2px solid var(--border);
  cursor:pointer; user-select:none; white-space:nowrap;
}}
thead th:hover {{ color:var(--text); }}
thead th::after {{ content:" ↕"; opacity:.3; }}
tbody tr {{
  border-bottom:1px solid var(--border);
  transition:background .12s;
}}
tbody tr:hover {{ background:#ffffff08; }}
tbody tr.row-both {{ background:#c084fc0d; }}
tbody tr.hidden {{ display:none; }}
td {{ padding:10px 12px; vertical-align:top; }}
.notes-col {{ color:var(--muted); font-size:11px; max-width:220px; }}
.award {{ white-space:nowrap; color:var(--green); font-weight:500; }}

/* ── Badges ── */
.badge {{
  display:inline-block; border-radius:4px;
  padding:2px 7px; font-size:11px; font-weight:600;
  white-space:nowrap;
}}
.badge-imminent {{ background:#7f1d1d; color:var(--red); }}
.badge-soon     {{ background:#422006; color:var(--yellow); }}
.badge-ok       {{ background:#134e4a; color:var(--green); }}
.badge-rolling  {{ background:#1e293b; color:var(--muted); }}
.badge-closed   {{ background:#1e293b; color:#475569; }}

.flags {{ margin-top:4px; display:flex; gap:4px; flex-wrap:wrap; }}
.flag-badge {{
  font-size:10px; font-weight:700; border-radius:3px;
  padding:1px 5px; letter-spacing:.3px;
}}
.flag-badge.native {{ background:#581c87; color:#e9d5ff; }}
.flag-badge.safety {{ background:#064e3b; color:#a7f3d0; }}

.cat-pill {{
  display:inline-block; border-radius:20px; padding:3px 10px;
  font-size:11px; font-weight:600; white-space:nowrap;
}}

/* ── Footer ── */
footer {{
  border-top:1px solid var(--border); padding:16px 32px;
  color:var(--muted); font-size:11px; text-align:center;
}}
</style>
</head>
<body>

<header>
  <div>
    <h1>🏛️ HumanAIOS Funding &amp; Resource Pipeline</h1>
    <div class="subtitle">
      Cherokee Nation · AI Safety/Observability · TRL 2–3 · Solo LLC ·
      Generated {today}
    </div>
  </div>
</header>

<div class="stats">
  <div class="stat-card"><div class="num">{summ.total}</div><div class="lbl">Total</div></div>
  <div class="stat-card"><div class="num" style="color:#c084fc">{summ.native_eligible}</div><div class="lbl">Native-eligible</div></div>
  <div class="stat-card"><div class="num" style="color:#34d399">{summ.ai_safety_relevant}</div><div class="lbl">AI-safety</div></div>
  <div class="stat-card"><div class="num" style="color:#fbbf24">{summ.both_flags}</div><div class="lbl">Both flags</div></div>
  <div class="stat-card"><div class="num" style="color:#60a5fa">{summ.active_rolling}</div><div class="lbl">Active/Rolling</div></div>
  <div class="stat-card"><div class="num" style="color:#f87171">{summ.deadline_soon_30d}</div><div class="lbl">Deadline ≤30d</div></div>
</div>

<div class="charts-row">
  <div>{donut}</div>
  <ul class="legend">{legend_items}</ul>
</div>

<div class="controls">
  <label>Search:</label>
  <input type="text" id="search" placeholder="name, sponsor, notes…" oninput="filterRows()"/>

  <label>Category:</label>
  <button class="filter-btn active" data-filter="cat" data-val="" onclick="toggleCat(this)">All</button>
  {''.join(
    f'<button class="filter-btn" data-filter="cat" data-val="{cat}" onclick="toggleCat(this)">'
    f'{CAT_LABELS.get(cat, cat)}</button>'
    for cat in sorted(CAT_COLORS.keys())
  )}

  <button class="filter-btn" id="btn-native"  onclick="toggleFlag('native')" >🏛️ Native only</button>
  <button class="filter-btn" id="btn-safety"  onclick="toggleFlag('safety')" >🛡️ AI Safety only</button>
  <button class="filter-btn" id="btn-both"    onclick="toggleFlag('both')"   >⭐ Both flags</button>
  <button class="filter-btn" id="btn-soon"    onclick="toggleFlag('soon')"   >⏰ Deadline soon</button>
</div>

<div class="table-wrap">
<table id="oppsTable">
  <thead>
    <tr>
      <th onclick="sortTable(0)">Name</th>
      <th onclick="sortTable(1)">Category</th>
      <th onclick="sortTable(2)">Sponsor</th>
      <th onclick="sortTable(3)">Award</th>
      <th onclick="sortTable(4)">Deadline</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody id="tableBody">
{rows}
  </tbody>
</table>
<p id="count-label" style="margin-top:10px;color:var(--muted);font-size:12px;"></p>
</div>

<footer>
  HumanAIOS LLC · aioshuman@gmail.com ·
  <a href="https://humanaios.ai">humanaios.ai</a> ·
  <a href="https://github.com/humanaios-ui/humanaios-funding-pipeline">GitHub</a> ·
  Data: <a href="../data/sources.json">sources.json</a>
</footer>

<script>
// ── State ──────────────────────────────────────────────────────────────────
let activeCat   = "";
let activeFlags = {{native:false, safety:false, both:false, soon:false}};

function filterRows() {{
  const q       = document.getElementById("search").value.toLowerCase();
  const rows    = document.querySelectorAll("#tableBody tr.opp-row");
  let visible   = 0;

  rows.forEach(r => {{
    const name   = (r.dataset.name   || "").toLowerCase();
    const cat    = r.dataset.cat    || "";
    const native = r.dataset.native === "true";
    const safety = r.dataset.safety === "true";
    const status = r.dataset.status || "";
    const txt    = r.innerText.toLowerCase();

    let show = true;
    if (q && !name.includes(q) && !txt.includes(q)) show = false;
    if (activeCat && cat !== activeCat)              show = false;
    if (activeFlags.native && !native)               show = false;
    if (activeFlags.safety && !safety)               show = false;
    if (activeFlags.both   && !(native && safety))   show = false;
    if (activeFlags.soon) {{
      // row has imminent/soon badge?
      const hasUrgent = r.querySelector(".badge-imminent, .badge-soon");
      if (!hasUrgent) show = false;
    }}

    r.classList.toggle("hidden", !show);
    if (show) visible++;
  }});

  const lbl = document.getElementById("count-label");
  lbl.textContent = visible + " / " + rows.length + " opportunities shown";
}}

function toggleCat(btn) {{
  activeCat = btn.dataset.val;
  document.querySelectorAll('[data-filter="cat"]').forEach(b =>
    b.classList.toggle("active", b === btn));
  filterRows();
}}

function toggleFlag(flag) {{
  const id = "btn-" + flag;
  activeFlags[flag] = !activeFlags[flag];
  document.getElementById(id).classList.toggle("active", activeFlags[flag]);
  filterRows();
}}

// ── Sort ──────────────────────────────────────────────────────────────────
let sortDir = {{}};
function sortTable(col) {{
  const tbody = document.getElementById("tableBody");
  const rows  = Array.from(tbody.querySelectorAll("tr.opp-row"));
  sortDir[col] = (sortDir[col] || 0) === 1 ? -1 : 1;
  rows.sort((a, b) => {{
    const ta = a.cells[col]?.innerText.trim() || "";
    const tb = b.cells[col]?.innerText.trim() || "";
    return ta.localeCompare(tb) * sortDir[col];
  }});
  rows.forEach(r => tbody.appendChild(r));
  filterRows();
}}

// Init count
window.addEventListener("DOMContentLoaded", filterRows);
</script>
</body>
</html>"""

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    data = sys.argv[1] if len(sys.argv) > 1 else DEFAULTS["data"]
    out  = sys.argv[2] if len(sys.argv) > 2 else DEFAULTS["out"]
    path = generate(data, out)
    print(f"[html] Wrote → {path}")

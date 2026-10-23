#!/usr/bin/env python3
"""Operations canvas: a living, read-only picture of the repository.

Reads the codebase atlas (architecture/codebase_atlas.py), ZONE_REGISTRY.md and
PLANNED_REPOS.md, then writes a self-contained HTML page plus canvas.json.

Authority: NONE. The canvas displays evidence. It does not ratify, merge,
admit, or sign anything. Z2 ratification gates are read here, never changed.

Usage:
    python3 architecture/operations_canvas.py --out DIR
    python3 architecture/operations_canvas.py --out DIR --atlas atlas.json
"""
import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
STATUS_WORDS = ("ACTIVE", "LIMITED", "READ-ONLY", "PLANNED", "ARCHIVED", "RETIRED", "UNKNOWN", "OTHER_ORG")
UNIT_RE = re.compile(r"(\d+)\s*units/cycle")
ZONE_HEADER_RE = re.compile(r"(\d+)-Zone Ecosystem")


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_zone_registry(text):
    """Return (rows, claimed_total). Rows come from the Z-NNN table."""
    claimed = None
    header = ZONE_HEADER_RE.search(text)
    if header:
        claimed = int(header.group(1))
    rows = []
    for line in text.splitlines():
        if not line.startswith("| Z-"):
            continue
        cells = _cells(line)
        zone_id = cells[0]
        if "+" in zone_id:  # "Z-013+" is a pointer to PLANNED_REPOS.md, not a zone
            continue
        status_cell = " ".join(cells[1:])
        if "READ-ONLY" in status_cell:
            status = "READ-ONLY"
        elif "LIMITED" in status_cell:
            status = "LIMITED"
        elif "ACTIVE" in status_cell:
            status = "ACTIVE"
        else:
            status = "UNKNOWN"
        cap = UNIT_RE.search(line)
        rows.append({
            "id": zone_id,
            "name": cells[1],
            "status": status,
            "cap": int(cap.group(1)) if cap else None,
            "source": "ZONE_REGISTRY.md",
        })
    return rows, claimed


def parse_planned_repos(text):
    """Return rows from PLANNED_REPOS.md tables. Legend rows are skipped."""
    rows = []
    seen = set()
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        cells = _cells(line)
        if len(cells) < 3:
            continue
        name = cells[0].strip("*").strip()
        status = next((c.strip("*").strip() for c in cells[1:] if c.strip("*").strip() in STATUS_WORDS), None)
        if status is None or name in STATUS_WORDS or name in seen:
            continue
        seen.add(name)
        phase = cells[4] if len(cells) > 4 else ""
        rows.append({
            "id": name,
            "name": name,
            "status": status,
            "cap": None,
            "phase": phase,
            "source": "PLANNED_REPOS.md",
        })
    return rows


def load_atlas(atlas_path):
    if atlas_path:
        return json.loads(Path(atlas_path).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [sys.executable, str(HERE / "codebase_atlas.py"), "--out", tmp],
            cwd=REPO, check=True, stdout=subprocess.DEVNULL,
        )
        return json.loads((Path(tmp) / "atlas.json").read_text(encoding="utf-8"))


def build_canvas(atlas, zone_text, planned_text):
    zone_rows, claimed_total = parse_zone_registry(zone_text)
    planned_rows = parse_planned_repos(planned_text)
    repos = zone_rows + planned_rows
    counted = len(repos)
    checks = {
        "registry_header_claims": claimed_total,
        "registry_rows_counted": counted,
        "header_matches_rows": claimed_total == counted,
    }
    data = {
        "schema": "operations-canvas/v0.1",
        "authority_effect": "NONE",
        "ratified": False,
        "note": "Read-only view. Z2 ratification is not implied by this page.",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_head": atlas.get("head_sha"),
        "code_graph": {
            "nodes": [
                {"id": n["id"], "label": n["label"], "file_count": n["file_count"]}
                for n in atlas["nodes"]
            ],
            "edges": [
                {"source": e["source"], "target": e["target"], "kind": e["kind"], "count": e["count"]}
                for e in atlas["edges"]
            ],
            "coverage": atlas["coverage"],
            "limitations": atlas.get("limitations", []),
        },
        "repo_map": repos,
        "registry_checks": checks,
    }
    return data


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Operations Canvas</title>
<style>
:root{--bg:#f4f6f7;--surface:#fff;--ink:#17212b;--muted:#5b6876;--rule:#d5dce2;--teal:#0f6b64;--amber:#a85d0a;--slate:#3d5a80;--rose:#9b3f63;
--serif:Georgia,"Times New Roman",serif;--sans:system-ui,-apple-system,"Segoe UI",sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0f161d;--surface:#17212b;--ink:#e6ecf1;--muted:#9aa8b5;--rule:#2a3744;--teal:#4fb8ae;--amber:#e0a050;--slate:#8fb0d6;--rose:#e08aa8;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0f161d;--surface:#17212b;--ink:#e6ecf1;--muted:#9aa8b5;--rule:#2a3744;--teal:#4fb8ae;--amber:#e0a050;--slate:#8fb0d6;--rose:#e08aa8;color-scheme:dark}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));padding-block:32px}
.wrap{max-width:1040px;margin:0 auto;display:grid;gap:56px}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(2rem,5vw,3rem);margin:0 0 12px;text-wrap:balance}
h2{font-family:var(--serif);font-weight:600;font-size:1.6rem;margin:0 0 8px;text-wrap:balance}
.label{font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 6px}
.lede,.note,footer{color:var(--muted);font-size:14px;margin:8px 0 0;max-width:70ch}
section{display:grid;gap:4px;min-width:0}
.graph-scroll{overflow-x:auto;border:1px solid var(--rule);border-radius:6px;background:var(--surface)}
.graph-scroll svg{display:block;width:100%;min-width:760px;height:auto}
.graph-scroll text{font-family:var(--sans);fill:var(--ink)}
.graph-scroll .sub{font-family:var(--mono);font-size:12px;fill:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:8px 20px;font-family:var(--mono);font-size:12px;color:var(--muted);margin-top:14px}
.legend span{display:inline-flex;align-items:center;gap:8px}
.legend i{display:inline-block;width:22px;border-top:2px solid var(--muted)}
.dot{width:10px;height:10px;border-radius:2px;display:inline-block}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:16px}
.fact{border-top:1px solid var(--rule);padding-top:10px;min-width:0}
.fact b{display:block;font-family:var(--serif);font-size:1.7rem;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}
.fact span{font-size:13px;color:var(--muted)}
.limits{color:var(--muted);font-size:13px;margin:10px 0 0}
.check{border-left:3px solid var(--amber);padding:8px 14px;color:var(--muted);font-size:14px;margin-top:12px}
.group{margin-top:22px;display:grid;gap:10px}
.group-head{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 12px}
.group-head h3{font-family:var(--serif);font-size:1.2rem;font-weight:600;margin:0}
.count{font-family:var(--mono);font-size:13px;color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:10px}
.tile{background:var(--surface);border:1px solid var(--rule);border-left:3px solid var(--muted);border-radius:6px;padding:12px 14px;min-width:0;display:grid;gap:4px;align-content:start}
.tile .id{font-family:var(--mono);font-size:12px;color:var(--muted)}
.tile .name{font-family:var(--mono);font-size:13.5px;overflow-wrap:anywhere}
.tile .meta{font-size:13px;color:var(--muted)}
.s-ACTIVE{border-left-color:var(--teal)!important}
.s-LIMITED{border-left-color:var(--amber)!important}
.s-READ-ONLY{border-left-color:var(--slate)!important}
.s-PLANNED{border-left-color:var(--rose)!important;border-style:dashed;border-left-style:solid}
.s-ARCHIVED,.s-RETIRED{opacity:.8}
.s-UNKNOWN,.s-OTHER_ORG{border-style:dashed;border-left-style:solid}
.links{font-size:14px}
.links a{color:var(--teal)}
</style>
</head>
<body>
<div class="wrap">
<header>
<p class="label">operations · living canvas · read-only</p>
<h1>Code graph and repo map</h1>
<p class="lede" id="intro"></p>
</header>

<section aria-labelledby="g">
<p class="label">Picture 1 · code graph</p>
<h2 id="g">Components and evidenced links</h2>
<p class="lede">Box size follows file count. Lines are links found in source. Static analysis only.</p>
<div class="graph-scroll"><svg id="graph" viewBox="0 0 1000 540" role="img" aria-label="Code graph"><defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="currentColor"/></marker></defs><g id="edges"></g><g id="nodes"></g></svg></div>
<div class="legend">
<span><i></i> workflow calls</span><span><i style="border-top-style:dashed"></i> python import</span><span><i style="border-top-style:dotted;border-top-width:3px"></i> doc link</span>
<span><span class="dot" style="background:var(--amber)"></span> governance</span><span><span class="dot" style="background:var(--teal)"></span> tooling and CI</span><span><span class="dot" style="background:var(--slate)"></span> research and state</span><span><span class="dot" style="background:var(--rose)"></span> platform and UI</span>
</div>
<div class="facts" id="facts"></div>
<p class="limits" id="limits"></p>
</section>

<section aria-labelledby="r">
<p class="label">Picture 2 · repo map</p>
<h2 id="r">Ecosystem by status</h2>
<p class="lede">Rows come from ZONE_REGISTRY.md and PLANNED_REPOS.md. Caps are units per cycle.</p>
<div id="check"></div>
<div id="groups"></div>
</section>

<section class="links" aria-label="Related">
<p class="label">Related surfaces in the repo</p>
<p>Graph timeline: <code>graph_timeline/system_graph_timeline.html</code>. Z2 gates: <code>REGISTERED.md</code>, <code>.github/workflows/z2_ratification_gate.yml</code>. This canvas does not replace either.</p>
</section>

<footer id="foot"></footer>
</div>
<script id="canvas-data" type="application/json">__DATA__</script>
<script>
(function () {
  var D = JSON.parse(document.getElementById("canvas-data").textContent);
  var NS = "http://www.w3.org/2000/svg";
  function el(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    if (parent) parent.appendChild(e);
    return e;
  }
  function make(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  document.getElementById("intro").textContent =
    "Generated from commit " + (D.source_head || "unknown").slice(0, 8) + " at " + D.generated_at + ". " + D.note;
  document.getElementById("foot").textContent =
    "Authority: " + D.authority_effect + ". Ratified: " + (D.ratified ? "yes" : "no") + ".";

  // Code graph layout on a 1000 x 540 grid. Unknown ids fall into a spare row.
  var POS = {
    ura: [150, 70], scvc: [150, 170], continuous: [150, 290], web: [150, 410],
    coordinator: [420, 60], evidence: [420, 160], intent: [420, 260], tools: [420, 360], docs: [420, 460],
    acat: [700, 290], session: [700, 370], governance: [700, 460],
    resource: [700, 60], services: [900, 60]
  };
  var GROUP = {
    governance: "var(--amber)", tooling: "var(--teal)", research: "var(--slate)", platform: "var(--rose)"
  };
  var GROUP_OF = {
    coordinator: "governance", intent: "governance", session: "governance", governance: "governance",
    continuous: "tooling", tools: "tooling", docs: "tooling",
    scvc: "research", evidence: "research", acat: "research",
    ura: "platform", web: "platform", resource: "platform", services: "platform"
  };
  var W = 170, H = 52, spare = 0;
  var byId = {};
  var nodes = D.code_graph.nodes.map(function (n) {
    var p = POS[n.id] || [150 + 250 * spare++, 500];
    var out = { id: n.id, label: n.label, fc: n.file_count, x: p[0], y: p[1], g: GROUP_OF[n.id] || "platform" };
    byId[n.id] = out;
    return out;
  });
  var dash = { workflow: "", "import": "6 4", doc: "2 3" };
  var kindMap = { workflow_invokes: "workflow", python_import: "import", doc_link: "doc" };

  var edgeLayer = document.getElementById("edges");
  var nodeLayer = document.getElementById("nodes");
  D.code_graph.edges.forEach(function (e) {
    var a = byId[e.source], b = byId[e.target];
    if (!a || !b) return;
    var dx = b.x - a.x, dy = b.y - a.y;
    var sx = dx ? (W / 2) / Math.abs(dx) : Infinity, sy = dy ? (H / 2) / Math.abs(dy) : Infinity;
    var s = Math.min(sx, sy);
    var kind = kindMap[e.kind] || "doc";
    var line = el("line", {
      x1: a.x + dx * s, y1: a.y + dy * s, x2: b.x - dx * s, y2: b.y - dy * s,
      stroke: "var(--muted)", "stroke-width": e.count >= 10 ? 3 : e.count >= 3 ? 2 : 1.5,
      "stroke-dasharray": dash[kind], "marker-end": "url(#arr)", color: "var(--muted)"
    }, edgeLayer);
    line.setAttribute("aria-label", a.label + " to " + b.label + ", " + e.count);
  });
  nodes.forEach(function (n) {
    var x = n.x - W / 2, y = n.y - H / 2;
    var g = el("g", {}, nodeLayer);
    el("rect", { x: x, y: y, width: W, height: H, rx: 6, fill: "var(--surface)", stroke: GROUP[n.g], "stroke-width": 2 }, g);
    el("rect", { x: x, y: y, width: 6, height: H, rx: 3, fill: GROUP[n.g] }, g);
    el("text", { x: x + 16, y: y + 22, "font-size": 13, "font-weight": 500 }, g).textContent = n.label;
    el("text", { x: x + 16, y: y + 40, class: "sub" }, g).textContent = n.fc + " files";
  });

  var cov = D.code_graph.coverage;
  var facts = document.getElementById("facts");
  [[cov.tracked_files, "tracked files"], [cov.mapped_files, "files mapped to a component"],
   [cov.unmapped_files, "files unmapped"], [D.code_graph.edges.length, "edge groups with evidence"]]
    .forEach(function (f) {
      var d = make("div", "fact");
      d.appendChild(make("b", null, String(f[0])));
      d.appendChild(make("span", null, f[1]));
      facts.appendChild(d);
    });
  document.getElementById("limits").textContent = D.code_graph.limitations.join(" ");

  var chk = D.registry_checks;
  var checkEl = document.getElementById("check");
  if (!chk.header_matches_rows) {
    checkEl.className = "check";
    checkEl.textContent = "Count check: ZONE_REGISTRY.md header says " + chk.registry_header_claims +
      " zones; " + chk.registry_rows_counted + " rows parsed across both registry files. Z2 needs to reconcile.";
  }

  var ORDER = ["ACTIVE", "LIMITED", "READ-ONLY", "PLANNED", "ARCHIVED", "RETIRED", "UNKNOWN", "OTHER_ORG"];
  var LABEL = { ACTIVE: "Active", LIMITED: "Limited cap", "READ-ONLY": "Read-only", PLANNED: "Planned",
    ARCHIVED: "Archived", RETIRED: "Retired", UNKNOWN: "Unknown", OTHER_ORG: "Other org" };
  var groups = document.getElementById("groups");
  ORDER.forEach(function (st) {
    var rows = D.repo_map.filter(function (r) { return r.status === st; });
    if (!rows.length) return;
    var g = make("div", "group");
    var head = make("div", "group-head");
    head.appendChild(make("h3", null, LABEL[st]));
    var capSum = rows.reduce(function (s, r) { return s + (r.cap || 0); }, 0);
    head.appendChild(make("span", "count", rows.length + " repos" + (capSum ? " · " + capSum + " units per cycle" : "")));
    g.appendChild(head);
    var tiles = make("div", "tiles");
    rows.forEach(function (r) {
      var t = make("div", "tile s-" + st);
      t.appendChild(make("span", "id", r.phase ? r.phase : r.id));
      t.appendChild(make("span", "name", r.name));
      t.appendChild(make("span", "meta", r.cap != null ? "Cap " + r.cap + " units per cycle" : r.source));
      tiles.appendChild(t);
    });
    g.appendChild(tiles);
    groups.appendChild(g);
  });
})();
</script>
</body>
</html>
"""


def render_html(data):
    # Escape "</" so the embedded JSON cannot close its own script tag.
    payload = json.dumps(data, ensure_ascii=False, indent=1).replace("</", "<\\/")
    return PAGE.replace("__DATA__", payload)


def write_outputs(data, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "canvas.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "index.html").write_text(render_html(data), encoding="utf-8")
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--atlas", type=Path, default=None, help="Existing atlas.json. Default: run the atlas generator.")
    parser.add_argument("--zone-registry", type=Path, default=REPO / "ZONE_REGISTRY.md")
    parser.add_argument("--planned-repos", type=Path, default=REPO / "PLANNED_REPOS.md")
    args = parser.parse_args(argv)
    atlas = load_atlas(args.atlas)
    data = build_canvas(
        atlas,
        args.zone_registry.read_text(encoding="utf-8"),
        args.planned_repos.read_text(encoding="utf-8"),
    )
    out = write_outputs(data, args.out)
    print(f"Canvas: {len(data['repo_map'])} repo rows, {len(data['code_graph']['nodes'])} components -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

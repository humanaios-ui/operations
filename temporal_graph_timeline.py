#!/usr/bin/env python3
"""Build a temporal view of system_graph.json from git history.

Each node gets first_seen / last_changed dates taken from the commits that
touch the files named in its `implementation` field. Edges appear once both
endpoints exist. Nodes whose implementation cannot be matched to a tracked
file fall back to the date system_graph.json itself first appeared, and are
flagged `date_source: "fallback"`.

Outputs (default graph_timeline/):
  system_graph_timeline.json   data consumed by the HTML page
  system_graph_timeline.html   self-contained animation (no network needed)

Usage:
  python3 temporal_graph_timeline.py            # build both outputs
  python3 temporal_graph_timeline.py --smoke-test

Needs full git history. Run `git fetch --unshallow` first on a shallow clone.
Dates are commit dates, not ratification dates. Governance dates live in
REGISTERED.md (Z2 hashes).
"""
import argparse
import datetime as dt
import fnmatch
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
GRAPH = "system_graph.json"
OUT_DIR = "graph_timeline"


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def tracked_files():
    return git("ls-files").splitlines()


def split_impl(text):
    """Split an implementation string into candidate path/glob tokens."""
    text = re.sub(r"\(.*?\)", "", text or "")  # drop "(skill)" style notes
    parts = re.split(r"[,;]", text)
    tokens = []
    for p in (p.strip() for p in parts):
        if not p:
            continue
        tokens.append(p)
        words = p.split()
        # "CLAUDE.md authority spec" also yields its leading filename
        if len(words) > 1 and "." in words[0]:
            tokens.append("./" + words[0])
    return tokens


def require_full_history():
    """Refuse to date nodes from a shallow clone: its history is truncated."""
    if git("rev-parse", "--is-shallow-repository").strip() == "true":
        sys.exit("error: shallow clone; run `git fetch --unshallow` first")


def resolve(token, files):
    """Return tracked files matching a token (exact path, basename or glob)."""
    if token.startswith("./"):
        # "./name" is an exact repo-root path
        return [f for f in files if f == token[2:]]
    if "/" in token:
        # Directory-qualified tokens match only inside that directory.
        # No basename fallback: an unmatched qualified glob stays unresolved.
        return [f for f in files if f == token or fnmatch.fnmatch(f, token)]
    base = token
    if "*" in base:
        hits = [f for f in files if fnmatch.fnmatch(f.split("/")[-1], base)]
    else:
        hits = [f for f in files if f.split("/")[-1] == base]
    return hits


def file_commits(path, follow=True):
    """Return {(sha, date)} for commits touching path, following renames."""
    args = ["log", "--format=%H %cs"]
    if follow:
        args.append("--follow")
    args += ["--", path]
    out = git(*args).split("\n")
    commits = set()
    for line in out:
        if line.strip():
            sha, date = line.split()
            commits.add((sha, date))
    return commits


def build():
    require_full_history()
    files = tracked_files()
    graph = json.loads((ROOT / GRAPH).read_text())
    graph_commits = file_commits(GRAPH)
    graph_first = min(d for _, d in graph_commits) if graph_commits else None
    revisions = sorted({d for _, d in graph_commits})

    nodes = []
    unresolved = []
    for nid, node in graph["nodes"].items():
        tokens = split_impl(node.get("implementation", ""))
        matched = []
        for tok in tokens:
            matched.extend(resolve(tok, files))
        matched = sorted(set(matched))
        commits = set()
        for f in matched:
            commits |= file_commits(f)
        if commits:
            dates = sorted(d for _, d in commits)
            first, last = dates[0], dates[-1]
            source = "git"
        else:
            first = last = graph_first
            source = "fallback"
            unresolved.append({"id": nid, "implementation": node.get("implementation", "")})
        nodes.append({
            "id": nid,
            "name": node.get("name", nid),
            "zone": node.get("zone", "?"),
            "type": node.get("type", ""),
            "status": node.get("status", ""),
            "files": matched,
            "commit_count": len(commits),
            "commit_dates": sorted({d for _, d in commits}),
            "first_seen": first,
            "last_changed": last,
            "date_source": source,
        })

    first_seen = {n["id"]: n["first_seen"] for n in nodes}
    edges = []
    for e in graph["edges"]:
        s, t = e["source"], e["target"]
        if s not in first_seen or t not in first_seen:
            continue
        edges.append({
            "source": s,
            "target": t,
            "edge_type": e.get("edge_type", ""),
            "first_seen": max(first_seen[s], first_seen[t]),
        })

    head = git("rev-parse", "--short", "HEAD").strip()
    head_date = git("log", "-1", "--format=%cs").strip()
    return {
        "head": head,
        "head_date": head_date,
        "graph_file": GRAPH,
        "graph_revisions": revisions,
        "nodes": sorted(nodes, key=lambda n: (n["first_seen"], n["id"])),
        "edges": edges,
        "unresolved": unresolved,
    }


HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>System Graph Timeline</title>
<style>
:root{--bg:#fbfaf7;--fg:#1d1d1b;--mute:#6b6a64;--line:#c9c6bd;--pulse:#d1495b;
--z1:#2a7fba;--z2:#c46b1a;--z3:#3f8f5a;--zc:#7a5ea8;--zx:#8a8a85}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17181a;--fg:#ecebe6;--mute:#9c9b95;--line:#3a3c40;--pulse:#ff7b8a;--z1:#5aa9e6;--z2:#e8924a;--z3:#6cc38a;--zc:#b596e0;--zx:#a5a5a0}}
:root[data-theme="dark"]{--bg:#17181a;--fg:#ecebe6;--mute:#9c9b95;--line:#3a3c40;--pulse:#ff7b8a;--z1:#5aa9e6;--z2:#e8924a;--z3:#6cc38a;--zc:#b596e0;--zx:#a5a5a0}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}
main{max-width:960px;margin:0 auto;padding:16px}
h1{font-size:20px;margin:4px 0 2px}
.sub{color:var(--mute);font-size:13px;margin-bottom:10px}
svg{width:100%;height:auto;display:block}
.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0}
button{font:inherit;padding:6px 14px;border:1px solid var(--line);background:none;color:var(--fg);border-radius:6px;cursor:pointer}
input[type=range]{flex:1;min-width:160px}
#date{font-variant-numeric:tabular-nums;min-width:110px;font-weight:600}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:13px;color:var(--mute);margin-top:6px}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:middle}
.stats{font-size:13px;color:var(--mute);margin-top:6px}
.edge{stroke:var(--line);stroke-width:1.2;transition:opacity .4s}
.node{transition:opacity .5s}
.label{fill:var(--fg);font-size:11px;pointer-events:none}
.fb{stroke-dasharray:3 3}
@media (max-width:480px){.label{font-size:13px}}
</style></head>
<body><main>
<h1>System graph over time</h1>
<div class="sub" id="sub"></div>
<svg id="g" viewBox="0 0 800 640" role="img" aria-label="Animated system graph"></svg>
<div class="controls">
  <button id="play" type="button">Play</button>
  <input type="range" id="t" min="0" max="0" step="1" value="0" aria-label="Date">
  <span id="date"></span>
</div>
<div class="stats" id="stats"></div>
<div class="legend" id="legend"></div>
</main>
<script>
const DATA = __DATA__;
const ZCOL = {Z1:"var(--z1)",Z2:"var(--z2)",Z3:"var(--z3)",code:"var(--zc)",CI:"var(--zx)"};
const colFor = z => ZCOL[z] || "var(--zx)";
const NS = "http://www.w3.org/2000/svg";
const W = 800, H = 640, CX = 400, CY = 320, R = 255;
const day = s => Date.parse(s + "T00:00:00Z") / 86400000;
const iso = d => new Date(d * 86400000).toISOString().slice(0, 10);

const nodes = DATA.nodes.slice();
// place nodes on a ring, grouped by zone so zones form arcs
const byZone = {};
nodes.forEach(n => (byZone[n.zone] = byZone[n.zone] || []).push(n));
const order = [].concat(...Object.keys(byZone).sort().map(z => byZone[z]));
order.forEach((n, i) => {
  const a = -Math.PI / 2 + (2 * Math.PI * i) / order.length;
  n.x = CX + R * Math.cos(a); n.y = CY + R * Math.sin(a);
});
const byId = Object.fromEntries(nodes.map(n => [n.id, n]));

const svg = document.getElementById("g");
const el = (tag, attrs, parent) => {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  (parent || svg).appendChild(e); return e;
};
const edgeEls = DATA.edges.map(e => {
  const s = byId[e.source], t = byId[e.target];
  const line = el("line", {x1: s.x, y1: s.y, x2: t.x, y2: t.y, class: "edge" +
    (e.edge_type === "callout" ? " fb" : ""), opacity: 0});
  return {e, line, s, t};
});
const nodeEls = nodes.map(n => {
  const g = el("g", {class: "node", opacity: 0});
  const c = el("circle", {cx: n.x, cy: n.y, r: 9, fill: colFor(n.zone),
    stroke: n.date_source === "fallback" ? "var(--fg)" : "none", "stroke-dasharray": "2 2"}, g);
  const pulse = el("circle", {cx: n.x, cy: n.y, r: 9, fill: "none",
    stroke: "var(--pulse)", "stroke-width": 2, opacity: 0}, g);
  const lx = n.x + (n.x - CX) * 0.14, ly = n.y + (n.y - CY) * 0.14 + 4;
  const anchor = n.x < CX - 5 ? "end" : n.x > CX + 5 ? "start" : "middle";
  const t = el("text", {x: lx, y: ly, class: "label", "text-anchor": anchor}, g);
  t.textContent = n.id;
  const title = el("title", {}, g);
  title.textContent = `${n.id} ${n.name} | zone ${n.zone} | first ${n.first_seen} | last ${n.last_changed} | commits ${n.commit_count}`;
  return {n, g, pulse};
});

const legend = document.getElementById("legend");
Object.keys(byZone).sort().forEach(z => {
  const s = document.createElement("span");
  const dot = document.createElement("span");
  dot.className = "dot";
  dot.style.background = colFor(z);
  s.appendChild(dot);
  s.appendChild(document.createTextNode(`${z} (${byZone[z].length})`));
  legend.appendChild(s);
});
legend.insertAdjacentHTML("beforeend", `<span><span class="dot" style="border:1px dashed var(--fg)"></span>date from graph file (no git match)</span><span><span class="dot" style="background:none;border:2px solid var(--pulse)"></span>changed in last 7 days</span>`);

const days = DATA.nodes.map(n => day(n.first_seen));
const minD = Math.min(day(DATA.graph_revisions[0] || DATA.nodes[0].first_seen), ...days);
const maxD = Math.max(day(DATA.head_date || iso(Date.now()/86400000)), ...DATA.nodes.map(n => day(n.last_changed)));
const slider = document.getElementById("t");
slider.max = Math.ceil(maxD - minD);
slider.value = slider.max;

document.getElementById("sub").textContent =
  `Built from git history at ${DATA.head}. ${nodes.length} nodes, ${DATA.edges.length} edges. Dates are commit dates. ${DATA.unresolved.length} node(s) fell back to the graph-file date.`;

function render() {
  const t = minD + Number(slider.value);
  document.getElementById("date").textContent = iso(t);
  let vis = 0, act = 0;
  nodeEls.forEach(({n, g, pulse}) => {
    const on = day(n.first_seen) <= t;
    g.setAttribute("opacity", on ? 1 : 0);
    // a commit inside the trailing 7-day window ending at the selected date
    const recent = on && n.commit_dates.some(d => { const x = day(d); return x <= t && t - x <= 7; });
    pulse.setAttribute("opacity", recent ? 1 : 0);
    if (on) vis++; if (recent) act++;
  });
  edgeEls.forEach(({e, line}) => line.setAttribute("opacity", day(e.first_seen) <= t ? 0.7 : 0));
  document.getElementById("stats").textContent =
    `${vis} of ${nodes.length} nodes exist · ${act} changed in last 7 days · ${DATA.graph_revisions.filter(d => day(d) <= t).length} graph-file revisions so far`;
}
slider.addEventListener("input", render);

let timer = null;
document.getElementById("play").addEventListener("click", () => {
  if (timer) { clearInterval(timer); timer = null; document.getElementById("play").textContent = "Play"; return; }
  if (Number(slider.value) >= slider.max) { slider.value = 0; render(); }
  document.getElementById("play").textContent = "Pause";
  timer = setInterval(() => {
    slider.value = Math.min(Number(slider.value) + 1, slider.max);
    render();
    if (Number(slider.value) >= slider.max) { clearInterval(timer); timer = null; document.getElementById("play").textContent = "Play"; }
  }, 120);
});
render();
</script></body></html>
"""


def write_html(data, path):
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    path.write_text(HTML_TEMPLATE.replace("__DATA__", payload), encoding="utf-8")


def smoke_test():
    """Check the matcher and that the build runs on this repo."""
    assert resolve("priority_queue_engine.py", ["a/priority_queue_engine.py"]) == ["a/priority_queue_engine.py"]
    assert split_impl("findings_scan.py (skill)") == ["findings_scan.py"]
    assert split_impl("ci_gates.py, z2_ratification_gate.yml") == ["ci_gates.py", "z2_ratification_gate.yml"]
    data = build()
    assert data["nodes"] and data["edges"], "empty build"
    print(f"smoke ok: {len(data['nodes'])} nodes, {len(data['edges'])} edges, "
          f"{len(data['unresolved'])} fallback, head {data['head']}")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--smoke-test", action="store_true")
    p.add_argument("--out", default=OUT_DIR)
    args = p.parse_args(argv)
    if args.smoke_test:
        return smoke_test()
    data = build()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "system_graph_timeline.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    write_html(data, out / "system_graph_timeline.html")
    print(f"wrote {out}/system_graph_timeline.json and .html "
          f"({len(data['nodes'])} nodes, {len(data['unresolved'])} fallback)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

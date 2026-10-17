#!/usr/bin/env python3
"""Render an offline, read-only, animated dashboard for observation_bridge JSON.

Builder v1.7 compliant - diagnostic_tool
HumanAIOS - REPOSITORY-KNOWLEDGE-DASHBOARD-VIEW-01
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

TOOL_NAME = "knowledge_dashboard_render"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "diagnostic_tool"
TOOL_ZONE = 1

PAGE = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HumanAIOS · Evidence Graph Observer</title>
<style>
:root{--bg:#101a18;--ink:#efe9dc;--muted:#a9b9ae;--line:#33483e;--gold:#d9a441}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);margin:0;font:14px/1.5 system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:24px}h1{font:400 36px Georgia,serif;margin:4px 0 7px}h2{font:400 20px Georgia,serif}
.small{font-size:12px;color:var(--muted)}.cards{display:flex;gap:10px;flex-wrap:wrap;margin:15px 0}
.card{padding:10px 16px;border:1px solid var(--line);border-radius:7px;background:#1a2a23;flex:1 1 160px}
.card strong{display:block;color:var(--gold);font-size:20px}.layout{display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:12px}
.panel{border:1px solid var(--line);border-radius:7px;background:#172721;padding:14px}
canvas{width:100%;height:580px;display:block;background:#14231b;border-radius:6px}
.controls{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:12px 0}
input,button{background:#20382b;color:var(--ink);border:1px solid var(--line);border-radius:5px;padding:6px;font:inherit}
button{cursor:pointer}input[type=range]{flex:1;accent-color:var(--gold);min-width:140px}
small{color:var(--muted)}a{color:#91ccb1}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:11px}
@media(max-width:750px){.layout{grid-template-columns:1fr}canvas{height:440px}main{padding:15px}}
@media(prefers-reduced-motion:reduce){canvas{scroll-behavior:auto}}
</style></head><body><main>
<div class="small">HUMANAIOS / NON-AUTHORITATIVE PROJECTION / OFFLINE</div>
<h1>Repository knowledge observer</h1>
<p class="small">#630 Repository Graph · #835 Codebase Atlas · #841 Temporal Graph. Each source retains its own provenance. Dates are observations. No node authorizes admission or merge.</p>
<div class="cards"><div class="card"><strong id="nodes"></strong>Graph objects</div>
<div class="card"><strong id="links"></strong>Recorded links</div>
<div class="card"><strong id="status"></strong>Exact-head relation</div></div>
<div class="layout"><section class="panel"><div class="controls">
<input id="query" aria-label="Find node" placeholder="Find node or source path">
<button id="play" type="button">Pause motion</button><button id="fit">Recenter</button></div>
<canvas id="graph" role="img" aria-label="Animated evidence relationships"></canvas>
<div class="controls"><label for="date">Historical observations</label><input id="date" type="range">
<output id="dateLabel"></output><button id="all">All dates</button></div>
<p class="small">Dashed links are declarations or references. Solid links indicate static source observations, not runtime proof. Fallback dates remain uncertain.</p></section>
<aside class="panel"><h2>Inspect selection</h2><p id="selection" class="small">Select a point to see provenance.</p>
<pre id="detail"></pre></aside></div></main>
<script>
const DATA=__PROJECTION__;
const N=DATA.nodes, E=DATA.edges, byId=new Map(N.map(n=>[n.id,n]));
const canvas=document.getElementById('graph'), ctx=canvas.getContext('2d');
const $=id=>document.getElementById(id);
$('nodes').textContent=N.length;$('links').textContent=E.length;
$('status').textContent=DATA.sources.atlas.status==='EXACT_HEAD'?'Matched':'Different heads';
const dates=[...new Set(N.map(n=>n.provenance?.first_seen).filter(Boolean))].sort();
const slider=$('date');slider.min=0;slider.max=dates.length;slider.value=dates.length;
let cutoff='9999-12-31',move=!matchMedia('(prefers-reduced-motion: reduce)').matches,frame=0,zoom=1,filter='';
const paint={rkg:'#86b9a5',atlas:'#dfa95b',time:'#9d9ff0'};
function kind(id){return id.split(':')[0]}
function hash(s){let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619);return h>>>0}
const coords=new Map(N.map(n=>{let h=hash(n.id),a=(h%6283)/1000,r=30+((h>>>11)%300);return[n.id,[Math.cos(a)*r,Math.sin(a)*r]]}));
function dimensions(){const b=canvas.getBoundingClientRect();const d=Math.min(2,devicePixelRatio||1);canvas.width=Math.round(b.width*d);canvas.height=Math.round(b.height*d);return{w:b.width,h:b.height,d}}
function present(n){const when=n.provenance?.first_seen;return(!when||when<=cutoff)&&(!filter||n.id.toLowerCase().includes(filter)||n.label.toLowerCase().includes(filter))}
function draw(){const {w,h,d}=dimensions();ctx.setTransform(d,0,0,d,0,0);ctx.clearRect(0,0,w,h);
  const shown=new Set(N.filter(present).map(n=>n.id));
  for(const e of E){if(!shown.has(e.from)||!shown.has(e.to))continue;
    const a=coords.get(e.from),b=coords.get(e.to),x=w/2+a[0]*zoom,y=h/2+a[1]*zoom,x2=w/2+b[0]*zoom,y2=h/2+b[1]*zoom;
    ctx.setLineDash(e.standing==='STATIC_SOURCE_ASSOCIATION'||e.standing==='OBSERVED'?[]:[3,6]);
    ctx.strokeStyle='rgba(208,218,202,.24)';ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x2,y2);ctx.stroke();
    if(move&&!ctx.getLineDash().length){let t=(frame*.005+hash(e.from+e.to)%100/100)%1;ctx.fillStyle='#f5cb7d';ctx.fillRect(x+(x2-x)*t,y+(y2-y)*t,2,2)}
  }ctx.setLineDash([]);
  for(const n of N){if(!shown.has(n.id))continue;const pos=coords.get(n.id),x=w/2+pos[0]*zoom,y=h/2+pos[1]*zoom;
    ctx.beginPath();ctx.arc(x,y,4.7,0,Math.PI*2);ctx.fillStyle=paint[kind(n.id)]||'#bbb';ctx.fill();
  }frame++;if(move)requestAnimationFrame(draw)
}
function redraw(){if(!move)draw()}
$('play').onclick=()=>{move=!move;$('play').textContent=move?'Pause motion':'Play motion';if(move)requestAnimationFrame(draw);else redraw()};
$('fit').onclick=()=>{zoom=1;redraw()};
$('query').addEventListener('input',e=>{filter=e.target.value.toLowerCase();redraw()});
function setDate(){let i=+slider.value;cutoff=i===dates.length?'9999-12-31':dates[i];$('dateLabel').textContent=i===dates.length?'All dates':dates[i];redraw()}
slider.addEventListener('input',setDate);$('all').onclick=()=>{slider.value=dates.length;setDate()};setDate();
canvas.addEventListener('click',event=>{const b=canvas.getBoundingClientRect(),x=event.clientX-b.left,y=event.clientY-b.top;
 let best=null,dist=20;for(const n of N.filter(present)){const p=coords.get(n.id),dd=Math.hypot(x-b.width/2-p[0]*zoom,y-b.height/2-p[1]*zoom);if(dd<dist){best=n;dist=dd}}
 if(best){$('selection').textContent=best.label;$('detail').textContent=JSON.stringify(best.provenance,null,2)}});
canvas.addEventListener('wheel',e=>{e.preventDefault();zoom=Math.max(.3,Math.min(2.5,zoom*(e.deltaY<0?1.08:.93)));redraw()},{passive:false});
addEventListener('resize',redraw);requestAnimationFrame(draw);
</script></body></html>'''

def render(source: dict) -> str:
    if (source.get("authority_effect") != "NONE"
            or source.get("can_authorize") is not False
            or source.get("merge_authority") is not False):
        raise ValueError("refuse unauthorized dashboard input")
    serialized = json.dumps(source, sort_keys=True, ensure_ascii=True).replace("<", "\\u003c")
    return PAGE.replace("__PROJECTION__", serialized)

def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--projection")
    p.add_argument("--out")
    p.add_argument("--smoke-test", action="store_true")
    args=p.parse_args()
    if args.smoke_test:
        assert "NON-AUTHORITATIVE" in render({"authority_effect":"NONE","can_authorize":False,
                                               "merge_authority":False,"nodes":[],"edges":[],
                                               "sources":{"atlas":{"status":"DIFFERENT_HEAD_NO_CONVERGENCE_CLAIM"}}})
        print("PASS")
        return
    if not args.projection or not args.out:
        p.error("--projection and --out required")
    inp=json.loads(Path(args.projection).read_text(encoding="utf-8"))
    Path(args.out).write_text(render(inp),encoding="utf-8")
    print("Offline dashboard written; authority_effect=NONE")

if __name__=="__main__":
    main()

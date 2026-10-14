#!/usr/bin/env python3
"""HumanAIOS Codebase Atlas v0.1 — offline, evidence-linked architecture observation.

No inference is authoritative. Never produces admission/merge decisions.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import fnmatch
import html
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from urllib.parse import quote

SCHEMA = "humanaios.codebase-atlas.v0.1"
LIMIT_FILES = 10000
LIMIT_READ_BYTES = 200_000
LIMIT_EDGES = 150
SCRIPT_PATTERN = re.compile(r"(?<![\w/])python(?:3(?:\.\d+)?)?\s+(?:-[A-Za-z]+\s+)*([A-Za-z0-9_./-]+\.py)\b")
MD_LINK = re.compile(r"\[[^\]]{0,200}\]\(([^)\s]+)\)")
COMPONENT_ID = re.compile(r"^[a-z][a-z0-9_-]{0,50}$")
REPO_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def git(repo: Path, *args: str) -> str:
    run = subprocess.run(["git", "-C", str(repo), *args], text=True,
                         capture_output=True, check=True, timeout=45)
    return run.stdout


def safe_path(raw: str) -> bool:
    path = PurePosixPath(raw)
    return bool(raw and not raw.startswith("/") and "\\" not in raw
                and ".." not in path.parts and "\x00" not in raw)


def load_config(filename: Path) -> list[dict]:
    raw = json.loads(filename.read_text(encoding="utf-8"))
    components = raw.get("components")
    if not isinstance(components, list) or not components or len(components) > 40:
        raise ValueError("components must be a nonempty bounded list")
    seen = set()
    for component in components:
        cid, patterns = component.get("id"), component.get("patterns")
        if not isinstance(cid, str) or not COMPONENT_ID.fullmatch(cid) or cid in seen:
            raise ValueError("invalid/duplicate component id")
        if not isinstance(component.get("label"), str) or not 1 <= len(component["label"]) <= 75:
            raise ValueError("invalid component label")
        if not isinstance(patterns, list) or not patterns or len(patterns) > 32:
            raise ValueError("invalid component patterns")
        for pattern in patterns:
            if not isinstance(pattern, str) or not safe_path(pattern):
                raise ValueError("unsafe component pattern")
        seen.add(cid)
    return components


def tracked_files(repo: Path) -> list[str]:
    # Git index only: never inventory untracked files, ignored caches, or secrets.
    raw = subprocess.run(["git", "-C", str(repo), "ls-files", "-z", "--cached"],
                         check=True, capture_output=True, timeout=45).stdout
    paths = sorted(set(p.decode("utf-8", errors="surrogateescape")
                       for p in raw.split(b"\0") if p))
    if len(paths) > LIMIT_FILES:
        raise ValueError("repository exceeds bounded tracked-file limit")
    result = []
    for path in paths:
        candidate = repo / path
        if safe_path(path) and candidate.is_file() and not candidate.is_symlink():
            result.append(path)
    return result


def component_of(path: str, defs: list[dict]) -> str | None:
    # First matching component wins. Deterministic precedence is config order.
    for d in defs:
        if any(fnmatch.fnmatchcase(path, pat) for pat in d["patterns"]):
            return d["id"]
    return None


def parse_python_imports(path: str, content: str, modules: dict[str, str]) -> list[tuple[str, int]]:
    try:
        body = ast.parse(content, filename=path)
    except (SyntaxError, ValueError, UnicodeError):
        return []
    current = Path(path).with_suffix("").parts
    if current[-1] == "__init__":
        current = current[:-1]
    else:
        current = current[:-1]
    result = set()
    for node in ast.walk(body):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                for n in range(len(name.split(".")), 0, -1):
                    candidate = ".".join(name.split(".")[:n])
                    if candidate in modules:
                        result.add((modules[candidate], node.lineno))
                        break
        elif isinstance(node, ast.ImportFrom):
            # Relative level 1 = current package; level 2 = parent, etc.
            if node.level:
                base = current[:max(0, len(current) - node.level + 1)]
                fullname = ".".join((*base, *(node.module or "").split("."))) if node.module else ".".join(base)
            else:
                fullname = node.module or ""
            options = [fullname + "." + a.name for a in node.names] + [fullname]
            for name in options:
                if name in modules:
                    result.add((modules[name], node.lineno))
                    break
    return sorted(result)


def module_index(paths: list[str]) -> dict[str, str]:
    index = {}
    for p in paths:
        if not p.endswith(".py"):
            continue
        bits = list(PurePosixPath(p).with_suffix("").parts)
        if bits[-1] == "__init__":
            bits.pop()
        if bits:
            index[".".join(bits)] = p
    return index


def linked_markdown_paths(path: str, content: str, path_set: set[str]):
    base = PurePosixPath(path).parent
    for match in MD_LINK.finditer(content):
        raw = match.group(1).split("#")[0].split("?")[0]
        if not raw or raw.startswith(("/", "http:", "https:", "mailto:", "#")) or "\\" in raw or "\x00" in raw:
            continue
        parts = []
        for bit in (base / raw).parts:
            if bit == "..":
                if not parts:
                    break
                parts.pop()
            elif bit not in ("", "."):
                parts.append(bit)
        else:
            linked = "/".join(parts)
            if linked in path_set:
                yield linked, content.count("\n", 0, match.start()) + 1


def render_mermaid(graph: dict) -> str:
    def label(s):
        return html.escape(str(s), quote=True).replace("\n", " ")
    nodes = graph["nodes"]
    lines = ["flowchart LR"]
    for n in nodes:
        lines.append(f'  {n["id"]}["{label(n["label"])} ({n["file_count"]} files)"]')
    for e in graph["edges"]:
        lines.append(f'  {e["source"]} -->|"{label(e["kind"])} x{e["count"]}"| {e["target"]}')
    for n in nodes:
        # Only service-authored, verified github.com URLs are emitted.
        lines.append(f'  click {n["id"]} "{n["url"]}" "Open checked source"')
    return "\n".join(lines) + "\n"


def render_markdown(graph: dict, mermaid: str) -> str:
    lines = ["# HumanAIOS Codebase Atlas", "", f'Commit: `{graph["head_sha"]}`',
             f'Worktree clean: `{str(graph["worktree_clean"]).lower()}`',
             "", "Read-only observation; no admission or merge authority.",
             "", "```mermaid", mermaid.rstrip(), "```", "", "## Evidence-bearing connections", ""]
    for e in graph["edges"]:
        lines.append(f'- **{e["source"]} → {e["target"]}** ({e["kind"]}; {e["count"]} occurrences): '
                     + ", ".join(f'`{a["source"]}:{a["line"]}` → `{a["target"]}`' for a in e["evidence"]))
    lines += ["", "## Coverage and limits", "",
              f'- Tracked files observed: {graph["coverage"]["tracked_files"]}.',
              f'- Files assigned to named components: {graph["coverage"]["mapped_files"]}.',
              f'- Not assigned: {graph["coverage"]["unmapped_files"]}.',
              '- Edges reflect static source evidence, not verified runtime behavior.',
              '- Missing edges do not prove disconnected systems.',
              '- No AI inference, secrets, token transfer, or external generation service.', ""]
    return "\n".join(lines)


def render_html(graph: dict) -> str:
    # JSON is embedded as data only, with the HTML script terminator escaped.
    data = json.dumps(graph, ensure_ascii=True, sort_keys=True).replace("<", "\\u003c")
    page = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HumanAIOS Codebase Atlas</title>
<style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#131d1b;color:#f1ecdf}
body{margin:0}header{padding:18px 22px;border-bottom:1px solid #3d564e;display:flex;gap:16px;flex-wrap:wrap;align-items:center}
h1{font-size:1.25rem;margin:0}header small{color:#a5c4b7}main{display:grid;grid-template-columns:minmax(0,1fr) 320px;height:calc(100vh - 83px)}
#canvas{overflow:auto;background:radial-gradient(circle at 65% 20%,#23372e,#121c19)}svg{min-width:900px;display:block}
aside{padding:18px;border-left:1px solid #3d564e;overflow:auto}input,button{padding:9px;background:#1c2e28;color:#f1ecdf;border:1px solid #526f61;border-radius:6px}input{min-width:170px}
.node{cursor:pointer}.node rect{fill:#264536;stroke:#78b79b;stroke-width:1.5}.node:hover rect,.node.active rect{stroke:#e7bf67;stroke-width:3}
.edge{stroke:#5d897a;fill:none;stroke-width:1.6;opacity:.65}.edge.off{opacity:.1}.node.off{opacity:.14;pointer-events:none}
.node text{fill:#f1ecdf;font:14px system-ui}.fine{color:#a5c4b7;font-size:.85rem}a{color:#dfb96b}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}ul{padding-left:18px}li{margin-bottom:9px}
@media(max-width:850px){main{display:block;height:auto}#canvas{height:60vh}aside{border-left:0;border-top:1px solid #3d564e}}
</style></head><body><header><h1>HumanAIOS · Codebase Atlas</h1>
<small id="sha"></small><label>Find <input id="search" aria-label="Filter components" placeholder="component or path"></label>
<button id="export">Export JSON</button><button id="mm">Export Mermaid</button></header>
<main><section id="canvas" aria-label="Architecture map"><svg id="map" role="img" aria-label="Component graph"></svg></section>
<aside><h2 id="detailtitle">Select a component</h2><p class="fine" id="detail"></p><div id="details"></div>
<h3>Evidence note</h3><p class="fine">Lines and links are observed static references, not proof of runtime behavior. Diagram has no admission authority.</p></aside></main>
<script id="atlas-data" type="application/json">__ATLAS_DATA__</script>
<script>
'use strict';
const g=JSON.parse(document.querySelector('#atlas-data').textContent);
const svg=document.querySelector('#map');const ns='http://www.w3.org/2000/svg';
const W=1160,C=3,dx=375,dy=132,offsetX=30,offsetY=65;
const positions=new Map(g.nodes.map((n,i)=>[n.id,{x:offsetX+(i%C)*dx,y:offsetY+Math.floor(i/C)*dy}]));
svg.setAttribute('viewBox',`0 0 ${W} ${Math.max(620,offsetY+Math.ceil(g.nodes.length/C)*dy+80)}`);
function el(type,attrs={},text){const node=document.createElementNS(ns,type);Object.entries(attrs).forEach(([k,v])=>node.setAttribute(k,v));if(text!==undefined)node.textContent=text;return node}
const edgeItems=[];
for(const e of g.edges){const a=positions.get(e.source),b=positions.get(e.target);if(!a||!b)continue;
const line=el('path',{class:'edge',d:`M ${a.x+280} ${a.y+32} C ${a.x+325} ${a.y+32}, ${b.x-45} ${b.y+32}, ${b.x} ${b.y+32}`});svg.appendChild(line);edgeItems.push([line,e])}
const nodeItems=[];
for(const n of g.nodes){const p=positions.get(n.id),group=el('g',{class:'node',tabindex:'0',role:'button','aria-label':n.label});
group.appendChild(el('rect',{x:p.x,y:p.y,width:280,height:70,rx:10}));group.appendChild(el('text',{x:p.x+14,y:p.y+29},n.label.slice(0,34)));
group.appendChild(el('text',{x:p.x+14,y:p.y+51},`${n.file_count} tracked files`));
function choose(){document.querySelectorAll('.node').forEach(x=>x.classList.remove('active'));group.classList.add('active');
document.querySelector('#detailtitle').textContent=n.label;
document.querySelector('#detail').textContent=n.file_count+' assigned paths, observed on '+g.head_sha.slice(0,12);
const dest=document.querySelector('#details');dest.replaceChildren();const anchor=document.createElement('a');anchor.href=n.url;anchor.target='_blank';anchor.rel='noopener noreferrer';anchor.textContent='Open source at commit';dest.appendChild(anchor);
const ul=document.createElement('ul');n.paths.forEach(path=>{const li=document.createElement('li');li.textContent=path;ul.appendChild(li)});dest.appendChild(ul);
const con=g.edges.filter(e=>e.source===n.id||e.target===n.id);
const h=document.createElement('h3');h.textContent='Observed connections ('+con.length+')';dest.appendChild(h);
con.forEach(e=>{const p=document.createElement('p');p.className='fine';p.textContent=`${e.source} → ${e.target}: ${e.kind} (${e.count}); ${e.evidence[0]?.source}:${e.evidence[0]?.line}`;dest.appendChild(p)});
}
group.addEventListener('click',choose);group.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();choose()}});svg.appendChild(group);nodeItems.push([group,n])}
document.querySelector('#sha').textContent=g.head_sha.slice(0,12)+(g.worktree_clean?' · clean':' · unverified worktree');
function filter(){const q=document.querySelector('#search').value.toLowerCase();const visible=new Set();nodeItems.forEach(([elem,n])=>{const yes=(n.label+' '+n.paths.join(' ')).toLowerCase().includes(q);elem.classList.toggle('off',!yes);if(yes)visible.add(n.id)});
edgeItems.forEach(([elem,e])=>elem.classList.toggle('off',!visible.has(e.source)||!visible.has(e.target)))}
document.querySelector('#search').addEventListener('input',filter);
function save(content,name,type){const a=document.createElement('a');a.download=name;a.href=URL.createObjectURL(new Blob([content],{type}));a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
document.querySelector('#export').addEventListener('click',()=>save(JSON.stringify(g,null,2),'atlas.json','application/json'));
document.querySelector('#mm').addEventListener('click',()=>save(g.mermaid,'atlas.mmd','text/plain'));
</script></body></html>'''
    return page.replace("__ATLAS_DATA__", data)


def build(repo: Path, config: Path, repo_id: str) -> dict:
    if not REPO_ID.fullmatch(repo_id):
        raise ValueError("repo must be owner/name")
    defs = load_config(config)
    paths = tracked_files(repo)
    path_set = set(paths)
    head = git(repo, "rev-parse", "HEAD").strip()
    clean = not bool(git(repo, "status", "--porcelain", "--untracked-files=no").strip())
    mappings = {p: component_of(p, defs) for p in paths}
    groups = defaultdict(list)
    for p, cid in mappings.items():
        if cid:
            groups[cid].append(p)
    # Only show groups that hold files, never assert existence from config alone.
    nodes=[]
    for d in defs:
        cid=d['id']
        if cid not in groups:
            continue
        allpaths=groups[cid]
        source=next((p for p in allpaths if p.endswith('.py')),allpaths[0])
        url='https://github.com/'+repo_id+'/blob/'+quote(head, safe='')+'/'+quote(source,safe='/')
        nodes.append({'id':cid,'label':d['label'],'file_count':len(allpaths),
                      'paths':allpaths[:12],'url':url,'representative':source})
    indexes=module_index(paths)
    detected=defaultdict(list)
    for p in paths:
        source=mappings[p]
        if not source:
            continue
        if not (p.endswith(('.py', '.md', '.yml', '.yaml'))):
            continue
        file=repo/p
        try:
            if file.stat().st_size>LIMIT_READ_BYTES:
                continue
            content=file.read_text(encoding='utf-8')
        except (UnicodeError,OSError):
            continue
        references=[]
        if p.endswith('.py'):
            references.extend(('python_import',t,ln) for t,ln in parse_python_imports(p,content,indexes))
        if p.endswith('.md'):
            references.extend(('doc_link',t,ln) for t,ln in linked_markdown_paths(p,content,path_set))
        if p.startswith('.github/workflows/') and p.endswith(('.yml','.yaml')):
            for ln,line in enumerate(content.splitlines(),1):
                if line.lstrip().startswith('#'):
                    continue
                for match in SCRIPT_PATTERN.finditer(line):
                    candidate=match.group(1).removeprefix('./')
                    if candidate in path_set:
                        references.append(('workflow_invokes',candidate,ln))
        for kind,target,line in references:
            destination=mappings.get(target)
            if not destination or destination==source or target==p:
                continue
            detected[(source,destination,kind)].append({'source':p,'target':target,'line':line})
    edges=[]
    for (src,dst,kind),proof in sorted(detected.items()):
        dedup={(p['source'],p['target'],p['line']):p for p in proof}
        evidence=sorted(dedup.values(),key=lambda a:(a['source'],a['line'],a['target']))
        edges.append({'source':src,'target':dst,'kind':kind,'count':len(evidence),'evidence':evidence[:5]})
    if len(edges)>LIMIT_EDGES:
        raise ValueError('too many cross-component edges; refine component definitions')
    mapped=sum(1 for cid in mappings.values() if cid)
    graph={'schema':SCHEMA,'repository':repo_id,'head_sha':head,
           'worktree_clean':clean,'snapshot':'HEAD_WORKTREE' if clean else 'UNVERIFIED_WORKTREE',
           'authority_effect':'NONE','merge_authority':False,
           'coverage':{'tracked_files':len(paths),'mapped_files':mapped,'unmapped_files':len(paths)-mapped},
           'nodes':nodes,'edges':edges,
           'limitations':['Static source links do not prove runtime execution.',
                          'Omitted connections are unknown, not absent.',
                          'Evidence only; no admission, approval, or merge authority.']}
    graph['mermaid']=render_mermaid(graph)
    return graph


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root',type=Path,default=Path.cwd())
    parser.add_argument('--config',type=Path,default=Path(__file__).with_name('codebase_atlas.components.json'))
    parser.add_argument('--repository',default='humanaios-ui/operations')
    parser.add_argument('--out',type=Path,default=Path('architecture/generated/codebase-atlas'))
    args=parser.parse_args()
    root=args.repo_root.resolve(strict=True)
    try:
        graph=build(root,args.config,args.repository)
    except (ValueError,OSError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as exc:
        parser.exit(1,f'Atlas failed closed: {exc}\n')
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/'atlas.json').write_text(json.dumps(graph,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (args.out/'atlas.mmd').write_text(graph['mermaid'],encoding='utf-8')
    (args.out/'atlas.md').write_text(render_markdown(graph,graph['mermaid']),encoding='utf-8')
    (args.out/'index.html').write_text(render_html(graph),encoding='utf-8')
    print(f'Atlas: {len(graph["nodes"])} components, {len(graph["edges"])} evidenced links; {args.out}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())

// Fail-closed check: every claim in claim_manifest.json must resolve to its receipt or code,
// and the script may only state figures that a tagged claim carries. Exit 1 on any failure.
// Run from anywhere: node experiments/haios_video_e0/episode-01/verify_manifest.mjs
import {readFileSync} from "node:fs";
import {dirname, join} from "node:path";
import {fileURLToPath} from "node:url";
const here=dirname(fileURLToPath(import.meta.url));
const read=p=>readFileSync(join(here,p),"utf8");
const manifest=JSON.parse(read("claim_manifest.json"));
const receipt=JSON.parse(read(manifest.receipt));
const code=read(manifest.code);
const script=read("script_witness_draft.md");
const errors=[];
const resolve=(obj,ptr)=>ptr.split("/").slice(1).reduce((o,k)=>o!=null&&Object.hasOwn(o,k)?o[k]:undefined,obj);
const claims=new Map();
for(const c of manifest.claims){
  if(claims.has(c.id))errors.push(`${c.id}: duplicate id`);
  claims.set(c.id,c);
  if(!manifest.allowed_tags.includes(c.tag))errors.push(`${c.id}: bad tag ${c.tag}`);
  if(!manifest.allowed_human_decisions.includes(c.human_decision))errors.push(`${c.id}: bad human_decision`);
  if(!c.limitation||!c.limitation.trim())errors.push(`${c.id}: empty limitation`);
  if(c.tag==="observed"&&!c.evidence.some(e=>e.pointer||e.code_contains))errors.push(`${c.id}: observed claim has no checkable evidence`);
  const backed=new Set(c.evidence.filter(e=>typeof e.equals==="number").map(e=>String(e.equals)));
  for(const f of (c.text.match(/\d+\.\d+/g)||[]))if(!backed.has(f))errors.push(`${c.id}: decimal ${f} in text has no receipt pointer`);
  for(const e of c.evidence){
    if(e.pointer!==undefined){const v=resolve(receipt,e.pointer);if(v===undefined)errors.push(`${c.id}: missing ${e.pointer}`);else if(JSON.stringify(v)!==JSON.stringify(e.equals))errors.push(`${c.id}: ${e.pointer} is ${JSON.stringify(v)}, manifest says ${JSON.stringify(e.equals)}`);}
    if(e.code_contains!==undefined&&!code.includes(e.code_contains))errors.push(`${c.id}: code no longer contains ${e.code_contains}`);
  }
}
if(manifest.status!=="DRAFT_NOT_FOR_RELEASE"&&manifest.claims.some(c=>c.human_decision!=="approved"))errors.push("manifest marked releasable while claims are not approved");
const used=new Set();
const strip=s=>s.replace(/#\d+/g,"").replace(/\b[A-Z]\d{2}\b/g,"");
const figures=s=>(strip(s).match(/\d+(?:\.\d+)?/g)||[]);
const body=script.split("## Script")[1]??"";
if(!body)errors.push("script: no '## Script' section");
for(const [n,line] of body.split("\n").entries()){
  const t=line.trim();if(!t||t.startsWith(">"))continue;
  const m=t.match(/^((?:\[[A-Z0-9]+\])+)\s*(.*)$/);
  if(!m){errors.push(`script line ${n}: untagged narration`);continue;}
  const tags=[...m[1].matchAll(/\[([A-Z0-9]+)\]/g)].map(x=>x[1]);const text=m[2];
  if(tags.includes("FRAME")){if(figures(text).length)errors.push(`script line ${n}: [FRAME] line states figures ${figures(text).join(",")}`);continue;}
  const allowed=tags.map(id=>{const c=claims.get(id);if(!c){errors.push(`script line ${n}: unknown claim ${id}`);return "";}used.add(id);return c.text;}).join(" ");
  for(const f of figures(text))if(!figures(allowed).includes(f))errors.push(`script line ${n}: figure ${f} not carried by ${tags.join(",")}`);
}
for(const id of claims.keys())if(!used.has(id))errors.push(`claim ${id} never appears in script`);
if(errors.length){console.error("FAIL\n"+errors.join("\n"));process.exit(1);}
console.log(`OK: ${claims.size} claims resolve to receipt or code; script figures all carried by tagged claims.`);

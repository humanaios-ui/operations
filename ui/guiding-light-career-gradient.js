"use strict";
const KEY="humanaios.guidingLight.v0_1";
const MAP={DOCUMENTED:1,USER_ATTESTED:.8,TRANSFERABLE:.7,PARTIAL:.5,PLANNED:.25,UNKNOWN:0,NOT_HELD:0,BLOCKED:0};
const HARD=new Set(["NOT_HELD","BLOCKED"]);
const GAP_ACTION={unknown:"INTERROGATE",knowledge:"LEARN",evidence:"BUILD_EVIDENCE",credential:"CREDENTIAL_DECISION",experience:"EXPERIENCE_REQUIRED",blocker:"BLOCKER"};
const DEMO={
 schema_version:"0.1.0",profile_id:"pilot-local",as_of:"2026-09-27",declared_goal_source:"user",selected_target:"opp-ai-governance",
 source_refs:["local evidence profile","normalized opportunity records"],
 omissions:["live employer verification not included in this static example"],
 uncertainty:["enterprise-scale authority and software-delivery depth require interrogation"],
 opportunities:[
  {id:"opp-ops",title:"Operations & Implementation Lead",opportunity_value:.65,gradient_axes:{compensation:.45,scope:.55,authority:.45,technical:.45,strategy:.40,evidence_gain:.60,portability:.65},requirements:[
   {id:"r1",capability:"Operations execution",weight:1,mandatory:true,mapping_state:"DOCUMENTED",gap_type:"evidence"},
   {id:"r2",capability:"Cross-functional project ownership",weight:1,mandatory:true,mapping_state:"DOCUMENTED",gap_type:"evidence"},
   {id:"r3",capability:"Client-domain experience",weight:.5,mandatory:false,mapping_state:"UNKNOWN",gap_type:"unknown"}]},
  {id:"opp-data-program",title:"Senior AI / Data Program Operations",opportunity_value:.90,gradient_axes:{compensation:.80,scope:.80,authority:.65,technical:.75,strategy:.70,evidence_gain:.90,portability:.85},requirements:[
   {id:"r1",capability:"Data quality and provenance",weight:1,mandatory:true,mapping_state:"DOCUMENTED",gap_type:"evidence"},
   {id:"r2",capability:"AI evaluation operations",weight:1,mandatory:true,mapping_state:"DOCUMENTED",gap_type:"evidence"},
   {id:"r3",capability:"Vendor / external workforce management",weight:.8,mandatory:false,mapping_state:"UNKNOWN",gap_type:"unknown",artifact_target:"vendor decision and performance register"},
   {id:"r4",capability:"Model-to-data requirement translation",weight:.9,mandatory:true,mapping_state:"PARTIAL",gap_type:"evidence",artifact_target:"data requirement traceability matrix"}]},
  {id:"opp-ai-governance",title:"Responsible AI / AI Governance Program Lead",opportunity_value:.95,gradient_axes:{compensation:.82,scope:.86,authority:.82,technical:.68,strategy:.92,evidence_gain:.92,portability:.90},requirements:[
   {id:"r1",capability:"Regulated quality and risk",weight:1,mandatory:true,mapping_state:"DOCUMENTED",gap_type:"evidence"},
   {id:"r2",capability:"AI governance lifecycle",weight:1,mandatory:true,mapping_state:"PARTIAL",gap_type:"evidence",artifact_target:"AI inventory + risk tier + control register"},
   {id:"r3",capability:"Executive governance reporting",weight:.9,mandatory:true,mapping_state:"TRANSFERABLE",gap_type:"evidence",artifact_target:"executive AI governance packet"},
   {id:"r4",capability:"Formal AI governance credential",weight:.45,mandatory:false,mapping_state:"NOT_HELD",gap_type:"credential",artifact_target:"credential decision record"}]},
  {id:"opp-staff-tpm",title:"Staff Technical Program Manager — AI",opportunity_value:.95,gradient_axes:{compensation:.95,scope:.92,authority:.82,technical:1,strategy:.86,evidence_gain:.96,portability:.94},requirements:[
   {id:"r1",capability:"Multi-year software TPM experience",weight:1,mandatory:true,mapping_state:"PARTIAL",gap_type:"experience",artifact_target:"production delivery portfolio"},
   {id:"r2",capability:"Architecture tradeoff participation",weight:.9,mandatory:true,mapping_state:"PARTIAL",gap_type:"evidence",artifact_target:"architecture decision records"},
   {id:"r3",capability:"Production launch ownership",weight:1,mandatory:true,mapping_state:"UNKNOWN",gap_type:"experience",artifact_target:"release + observability evidence"}]}
 ]};
let snapshot=load(),filter="ALL";

function clamp(v){v=Number(v)||0;return Math.max(0,Math.min(1,v))}
function esc(s){return String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]))}
function score(o){
 let wt=0,cov=0,blockers=[],unknowns=[];
 (o.requirements||[]).forEach(r=>{const w=Math.max(0,Number(r.weight??1)),st=String(r.mapping_state||"UNKNOWN").toUpperCase();wt+=w;cov+=w*(MAP[st]??0);
  if(r.mandatory&&HARD.has(st))blockers.push(r.capability||r.id); if(r.mandatory&&st==="UNKNOWN")unknowns.push(r.capability||r.id)});
 const vals=Object.values(o.gradient_axes||{}).map(clamp),gradient=vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:0,action=wt?cov/wt:0;
 let cls;if(blockers.length)cls="HOLD";else if(action>=.8&&gradient<.55)cls="HARVEST";else if(action>=.55&&gradient>=.55)cls="BRIDGE";else if(action<.55&&gradient>=.55)cls="FRONTIER";else cls="HOLD";
 return {opportunity_id:o.id,title:o.title,actionability:+action.toFixed(4),gradient:+gradient.toFixed(4),classification:cls,mandatory_blockers:blockers,mandatory_unknowns:unknowns}
}
function learning(){
 const agg={};
 (snapshot.opportunities||[]).forEach(o=>{const sr=score(o),pf={FRONTIER:1,BRIDGE:.85,HARVEST:.35,HOLD:.2}[sr.classification],ov=clamp(o.opportunity_value??.5);
  (o.requirements||[]).forEach(r=>{const st=String(r.mapping_state||"UNKNOWN").toUpperCase(),ms=MAP[st]??0;if(ms>=.75)return;const c=r.capability||r.id,g=String(r.gap_type||"unknown").toLowerCase();
   const x=agg[c]||(agg[c]={capability:c,gap_type:g,action:GAP_ACTION[g]||"INTERROGATE",priority:0,roles:new Set(),artifacts:new Set()});
   x.priority+=(Number(r.weight??1)||0)*(1-ms)*Math.max(sr.gradient,.1)*ov*pf;x.roles.add(o.id);if(r.artifact_target)x.artifacts.add(r.artifact_target)})});
 return Object.values(agg).map(x=>({...x,priority:+x.priority.toFixed(4),roles:[...x.roles],artifacts:[...x.artifacts]})).sort((a,b)=>b.priority-a.priority||a.capability.localeCompare(b.capability))
}
function selected(){return (snapshot.opportunities||[]).find(o=>o.id===snapshot.selected_target)||(snapshot.opportunities||[])[0]}
function persist(){localStorage.setItem(KEY,JSON.stringify(snapshot))}
function load(){try{return JSON.parse(localStorage.getItem(KEY))||structuredClone(DEMO)}catch(e){return structuredClone(DEMO)}}
function pct(v){return Math.round(v*100)+"%"}
function render(){
 const rows=(snapshot.opportunities||[]).map(o=>({o,s:score(o)})),counts=k=>rows.filter(x=>x.s.classification===k).length;
 document.getElementById("metrics").innerHTML=[
  ["Reachable now",counts("HARVEST")+counts("BRIDGE"),"Harvest + Bridge"],
  ["Bridge",counts("BRIDGE"),"actionable growth roles"],
  ["Frontier",counts("FRONTIER"),"target specifications"],
  ["Learning deltas",learning().length,"ranked from current evidence"]
 ].map(x=>'<div class="metric"><div class="v">'+x[1]+'</div><div class="l">'+x[0]+'</div><div class="s">'+x[2]+'</div></div>').join("");
 const shown=rows.filter(x=>filter==="ALL"||x.s.classification===filter);
 document.getElementById("opportunities").innerHTML=shown.length?shown.map(({o,s})=>{
  const req=(o.requirements||[]).map(r=>'<div class="req"><span>'+esc(r.capability)+(r.mandatory?' *':'')+'</span><span class="state '+esc(r.mapping_state)+'">'+esc(r.mapping_state)+'</span></div>').join("");
  return '<article class="card '+(o.id===snapshot.selected_target?'target':'')+'"><div class="head"><div class="title">'+esc(o.title)+'</div><span class="tag '+s.classification+'">'+s.classification+'</span></div>'+
   '<div class="score"><div class="scorebox"><b>'+pct(s.actionability)+'</b><span>current actionability</span></div><div class="scorebox"><b>'+pct(s.gradient)+'</b><span>career gradient</span></div></div>'+
   (s.mandatory_blockers.length?'<div class="req"><span>Mandatory blocker</span><span class="state BLOCKED">'+esc(s.mandatory_blockers.join(", "))+'</span></div>':'')+
   '<div class="reqs">'+req+'</div><button class="btn targetbtn" data-target="'+esc(o.id)+'">Set pathway target</button></article>'}).join(""):'<div class="empty">No opportunities in this class.</div>';
 document.querySelectorAll("[data-target]").forEach(b=>b.onclick=()=>{snapshot.selected_target=b.dataset.target;persist();render()});
 const t=selected(),ts=t?score(t):null;
 if(!t){document.getElementById("target").innerHTML='<div class="empty">Import an opportunity snapshot to begin.</div>'}
 else{
  const deltas=(t.requirements||[]).filter(r=>(MAP[String(r.mapping_state||"UNKNOWN").toUpperCase()]??0)<.75);
  document.getElementById("target").innerHTML='<div class="head"><div><div class="kicker">Selected target</div><div class="title">'+esc(t.title)+'</div></div><span class="tag '+ts.classification+'">'+ts.classification+'</span></div>'+
  '<div class="score"><div class="scorebox"><b>'+pct(ts.actionability)+'</b><span>actionability</span></div><div class="scorebox"><b>'+pct(ts.gradient)+'</b><span>gradient</span></div></div>'+
  (deltas.length?deltas.map(r=>'<div class="delta"><b>'+esc(r.capability)+'</b><div class="meta"><span class="action">'+esc(GAP_ACTION[r.gap_type]||"INTERROGATE")+'</span> · '+esc(r.mapping_state)+(r.artifact_target?' · <span class="artifact">'+esc(r.artifact_target)+'</span>':'')+'</div></div>').join(""):'<div class="empty">No unresolved capability deltas in the supplied mapping.</div>')
 }
 const lp=learning().slice(0,8);
 document.getElementById("learning").innerHTML='<div class="kicker">Highest-leverage deltas</div><div style="margin-top:7px">'+(lp.length?lp.map(x=>'<div class="delta"><b>'+esc(x.capability)+'</b><div class="meta"><span class="action">'+esc(x.action)+'</span> · affects '+x.roles.length+' role(s) · priority '+x.priority.toFixed(2)+'</div><div class="wbar"><i style="width:'+Math.min(100,x.priority*40)+'%"></i></div>'+(x.artifacts.length?'<div class="meta artifact">Evidence target: '+esc(x.artifacts.join(" · "))+'</div>':'')+'</div>').join(""):'<div class="empty">No learning deltas.</div>')+'</div>';
 document.getElementById("witnessPreview").textContent=JSON.stringify(witness(),null,2)
}
function witness(){
 const results=(snapshot.opportunities||[]).map(score);
 return {observation_type:"career_gradient",schema_version:"0.1.0",observed_at:new Date().toISOString(),profile_id:snapshot.profile_id,declared_goal_source:snapshot.declared_goal_source||"user",selected_target:snapshot.selected_target||null,results,learning_priorities:learning(),source_refs:snapshot.source_refs||[],omissions:snapshot.omissions||[],uncertainty:snapshot.uncertainty||[],non_authority_invariant:"WITNESS_IS_NOT_THE_AUTHORITY",authorization:{state:"NOT_GRANTED_BY_WITNESS",note:"Application, enrollment, purchase, and career-change decisions remain human-authorized."}}
}
function activityEvents(){const at=new Date().toISOString(),ev=[];(snapshot.opportunities||[]).forEach(o=>{const s=score(o);ev.push({timestamp:at,service:"GuidingLight",event_type:"opportunity_mapped",resource_id:o.id,title:s.classification+": "+o.title,data:s,actor:"guiding-light-reflex"})});learning().forEach((x,i)=>ev.push({timestamp:at,service:"GuidingLight",event_type:"learning_signal",resource_id:"learning-"+(i+1),title:x.action+": "+x.capability,data:x,actor:"guiding-light-reflex"}));return ev}
function dl(name,obj){const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:"application/json"}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
document.querySelectorAll(".filter").forEach(b=>b.onclick=()=>{filter=b.dataset.filter;document.querySelectorAll(".filter").forEach(x=>x.classList.toggle("sel",x===b));render()});
document.getElementById("witnessExport").onclick=()=>dl("guiding-light-witness-observation.json",witness());
document.getElementById("eventsExport").onclick=()=>dl("guiding-light-events.json",activityEvents());
document.getElementById("snapshotExport").onclick=()=>dl("guiding-light-snapshot.json",snapshot);
document.getElementById("importBtn").onclick=()=>document.getElementById("file").click();
document.getElementById("file").onchange=e=>{const f=e.target.files[0];if(!f)return;const rd=new FileReader();rd.onload=()=>{try{const x=JSON.parse(rd.result);if(!Array.isArray(x.opportunities))throw Error("opportunities missing");snapshot=x;persist();render()}catch(err){alert("Could not load snapshot: "+err.message)}};rd.readAsText(f);e.target.value=""};
document.getElementById("resetDemo").onclick=()=>{snapshot=structuredClone(DEMO);persist();render()};
render();

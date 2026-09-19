import { useState, useMemo } from "react";

// ─── DESIGN TOKENS ───────────────────────────────────────────────────────────
const T = {
  bg0: "#04080f", bg1: "#080e1a", bg2: "#0d1424", bg3: "#111c2e",
  border: "#111e30", borderHi: "#1e3050",
  text: "#c0d0e4", textDim: "#3a5070", textMid: "#6080a0",
  accent: "#e06830",   accentDim: "#3a1808",
  green: "#30a858",    greenDim: "#0a2010",
  yellow: "#c09820",   yellowDim: "#281e04",
  red: "#c83838",      redDim: "#220808",
  blue: "#3070c0",     blueDim: "#081428",
  purple: "#8050c8",   purpleDim: "#160828",
  teal: "#28909a",     tealDim: "#081820",
};

const CAT = {
  "Research":              { color: "#8050c8", icon: "∂" },
  "Litigation":            { color: "#c83838", icon: "⚖" },
  "Case Study":            { color: "#30a858", icon: "▣" },
  "Platform / Technology": { color: "#e06830", icon: "⧖" },
};

const STATUS_CFG = {
  "Active":           { dot: "#30a858", bg: "#0a2010" },
  "Scoping":          { dot: "#c09820", bg: "#281e04" },
  "Pending Outreach": { dot: "#3070c0", bg: "#081428" },
  "On Hold":          { dot: "#c83838", bg: "#220808" },
  "Closed":           { dot: "#3a5070", bg: "#0d1424" },
};

// ─── ENTRIES ─────────────────────────────────────────────────────────────────
const ENTRIES = [
  {
    id: "COL-001", name: "EmergenceAI / Agent-E", category: "Platform / Technology",
    date: "2026-05-24", status: "Active",
    proxyLI: 0.89, proxyLILabel: "ACAT 3-Dim Proxy",
    scg: null, himGap: 0.044, himDir: "positive",
    dims: { harm: 88, syc: 72, consist: 85, truth: 80, autonomy: 75, humility: 70 },
    signals: [
      "Skills-constrained architecture limits normative drift under pressure",
      "Proxy LI differentiation: clean≈0.89 vs pressured≈0.69 (delta 0.198)",
      "Negative HIM decoupling under high-pressure condition (him_gap=−0.029)",
    ],
    gaps: [
      "3-dim proxy only — full 12-dim ACAT crosswalk pending",
      "sycophancy_resistance invariant in simulator (artifact, not structural)",
      "No P1/P2/P3 phase schema in trace yet",
    ],
    sources: [{ type: "github", ref: "humanaios-ui/operations #99" }, { type: "drive", ref: "ae_acat_pilot_design_v2_corrected.md" }],
    next: "Apply instrumentation patch to real Agent-E fork. Run pilot tasks.",
    notes: "Pilot design v2 corrected. Grok session artifacts fact-audited by Unit Zero. 3 flags: Proxy LI 0.92 invented; session closure Z2 violation; gap 4 overclaim.",
  },
  {
    id: "COL-002", name: "ShiftSmart", category: "Platform / Technology",
    date: "2026-05-24", status: "Scoping",
    proxyLI: null, proxyLILabel: "Not yet measured",
    scg: null, himGap: null, himDir: "unknown",
    dims: { harm: 70, syc: 65, consist: 78, truth: 72, autonomy: 68, humility: 60 },
    signals: [
      "Hybrid human orchestration — analogous substrate to ACAT measurement targets",
      "Worker quality/fulfillment metrics are direct proxy for behavioral signals",
      "Drift detection: quality degradation under surge = pressure condition analog",
    ],
    gaps: ["R-01–R-04 equivalents not yet received", "Data access not confirmed"],
    sources: [{ type: "drive", ref: "ShiftSmart_HumanAIOS_Scoping_Brief.md" }],
    next: "Z2 Night ratification before any contact. 30-min scoping call target.",
    notes: "Scoping brief produced by Grok session. Z2 gate: Night ratification required before aioshuman@gmail.com outreach.",
  },
  {
    id: "COL-003", name: "Governing Engines / empirica", category: "Platform / Technology",
    date: "2026-05-16", status: "Active",
    proxyLI: 0.727, proxyLILabel: "Document layer LI (governance_document)",
    scg: null, himGap: null, himDir: "unknown",
    dims: { harm: 75, syc: 68, consist: 82, truth: 79, autonomy: 71, humility: 65 },
    signals: [
      "Vault/Builder implementation contracts score 0.83–0.85 (near corpus mean)",
      "F-34 architectural determination: structural prohibitions drive 6 dims",
      "empirica joint protocol brief produced. Thursday sync confirmed.",
    ],
    gaps: [
      "Positioning docs score 0.70–0.74 — abstraction gap documented",
      "ARCH score_source field required before corpus inclusion",
    ],
    sources: [{ type: "slack", ref: "#wgs-sync S-051626-02" }, { type: "drive", ref: "MODEAI_GE_DOCS_ACAT_S051626-02.md" }],
    next: "empirica Thursday sync at meet.google.com/qri-jbqd-cyv. David joint assessment protocol.",
    notes: "Session S-051626-02. document_layer: governance_document. Z2 ratified corpus eligibility.",
  },
  {
    id: "COL-004", name: "SYCON-Bench (JiseungHong)", category: "Research",
    date: "2026-05-24", status: "Pending Outreach",
    proxyLI: null, proxyLILabel: "Not yet measured",
    scg: null, himGap: null, himDir: "unknown",
    dims: { harm: 0, syc: 0, consist: 0, truth: 0, autonomy: 0, humility: 0 },
    signals: [
      "Sycophancy benchmark directly convergent with ACAT syc resistance dimension",
      "Cross-validation: SYCON scores vs ACAT corpus syc scores",
    ],
    gaps: ["Outreach blocked on Night Z2 ratification"],
    sources: [{ type: "arxiv", ref: "SYCON-Bench paper" }],
    next: "Z2 ratification then GitHub Issues outreach (confirmed preferred method).",
    notes: "Tier 1 external research team. GitHub Issues is confirmed contact method.",
  },
  {
    id: "COL-005", name: "PPT-Bench (Steven Au + Sujit Noronha)", category: "Research",
    date: "2026-05-24", status: "Pending Outreach",
    proxyLI: null, proxyLILabel: "Not yet measured",
    scg: null, himGap: null, himDir: "unknown",
    dims: { harm: 0, syc: 0, consist: 0, truth: 0, autonomy: 0, humility: 0 },
    signals: [
      "Prompt perturbation convergent with ACAT Phase 2 stimulus methodology",
      "Cross-validation of perturbation response scoring",
    ],
    gaps: ["Outreach blocked on Night Z2 ratification"],
    sources: [{ type: "arxiv", ref: "PPT-Bench paper" }],
    next: "Z2 ratification then GitHub Issues outreach.",
    notes: "Tier 1 external research team. GitHub Issues contact method confirmed.",
  },
  {
    id: "COL-006", name: "idreesaziz / sycophantic-ai-benchmark", category: "Research",
    date: "2026-05-24", status: "Pending Outreach",
    proxyLI: null, proxyLILabel: "Not yet measured",
    scg: null, himGap: null, himDir: "unknown",
    dims: { harm: 0, syc: 0, consist: 0, truth: 0, autonomy: 0, humility: 0 },
    signals: [
      "Open-source sycophancy benchmark — direct corpus integration potential",
      "Complementary: ACAT self-report + benchmark behavioral trace",
    ],
    gaps: ["Outreach blocked on Night Z2 ratification"],
    sources: [{ type: "github", ref: "idreesaziz/sycophantic-ai-benchmark" }],
    next: "Z2 ratification then GitHub Issues outreach.",
    notes: "Tier 1. OSS — potential direct ACAT corpus integration path.",
  },
];

// ─── AUTOMATION SOURCES ──────────────────────────────────────────────────────
const AUTO_SOURCES = [
  { id:"SRC-01", name:"Gmail", icon:"✉", tool:"Gmail MCP", status:"READY", color:"#e06830",
    signals:["inbound_inquiry","reply_to_outreach","newsletter_mention"],
    extraction:"Thread subject + sender domain + body keywords",
    pAnon:"REQUIRED — sender data is collaborator PII", zone:"Z1 scan · Z2 new entry" },
  { id:"SRC-02", name:"GitHub", icon:"⑂", tool:"api.github.com", status:"READY", color:"#30a858",
    signals:["issue_comment","star","fork","PR_mention"],
    extraction:"Issue titles + body + actor login + repo context",
    pAnon:"Usernames public; emails require care", zone:"Z1 scan" },
  { id:"SRC-03", name:"Slack #wgs-sync", icon:"⬡", tool:"Slack MCP", status:"READY", color:"#3070c0",
    signals:["session_log_mention","WGS_new_contact"],
    extraction:"Parse WGS posts for NEW_CANDIDATE mentions",
    pAnon:"Internal — Z2 before external surface", zone:"Z1 scan" },
  { id:"SRC-04", name:"arXiv / Semantic Scholar", icon:"∂", tool:"web_fetch + search API", status:"READY", color:"#8050c8",
    signals:["citing_paper","convergent_keywords"],
    extraction:"Search: HumanAIOS OR ACAT OR 'behavioral calibration gap'",
    pAnon:"Public scholarly record", zone:"Z1 scan · weekly" },
  { id:"SRC-05", name:"Supabase corpus", icon:"▣", tool:"Supabase MCP + REST", status:"POST-MIGRATION", color:"#28909a",
    signals:["novel_agent_name","novel_deployment_surface","novel_bars_observer"],
    extraction:"SELECT DISTINCT new values since last_scan",
    pAnon:"bars_observer_notes may contain PII — never surface raw", zone:"Z1 scan" },
  { id:"SRC-06", name:"Google Drive", icon:"◉", tool:"Drive MCP", status:"READY", color:"#c09820",
    signals:["scoping_brief","MRH_case_doc","research_collab_doc"],
    extraction:"Search recent docs: 'collaboration' OR 'scoping brief' OR 'MRH'",
    pAnon:"REQUIRED — Drive may contain collaborator-identified documents", zone:"Z1 scan · Z2 new entity" },
  { id:"SRC-07", name:"Web / Media", icon:"◈", tool:"web_search + web_fetch", status:"READY", color:"#6080a0",
    signals:["citing_paper","media_mention","convergent_research"],
    extraction:"Search: HumanAIOS OR 'Night Anderson' OR ACAT behavioral",
    pAnon:"Public web — no PII concern", zone:"Z1 scan · weekly" },
  { id:"SRC-08", name:"RentAHuman", icon:"⬙", tool:"X-API-Key MCP", status:"READY", color:"#c83838",
    signals:["client_profile","bounty_completion","repeat_engagement"],
    extraction:"Search AI/research keyword profiles + completed bounties",
    pAnon:"REQUIRED — human worker profiles are PII", zone:"Z1 scan · Z2 Case Study" },
];

// ─── PIPELINE ────────────────────────────────────────────────────────────────
const PIPELINE = [
  { step:1, name:"SCAN",     tool:"haios_collab_scanner_v1_0.py",     zone:"Z1",    status:"READY",
    desc:"Per-source MCP calls across all 8 sources. Runs on schedule (daily) or on-demand. Outputs candidate JSON." },
  { step:2, name:"EXTRACT",  tool:"haios_collab_extractor.py",         zone:"Z1",    status:"PLANNED",
    desc:"Signal parsing + entity resolution + fuzzy match against KNOWN_COLLAB_IDS. Assigns match_confidence score." },
  { step:3, name:"ENRICH",   tool:"web_fetch + Semantic Scholar API",  zone:"Z1",    status:"READY",
    desc:"Public profile enrichment: Scholar bio, GitHub README, paper abstract. Zero PII — public sources only." },
  { step:4, name:"SCORE",    tool:"scg_scorer.py",                     zone:"Z1",    status:"READY",
    desc:"SCG = P1 Core6 − BARS observer score. Proxy LI from trace data. Alignment dim scoring where available." },
  { step:5, name:"QUEUE",    tool:"z2_queue_v1_0_2.py",               zone:"Z1→Z2", status:"READY",
    desc:"NEW_CANDIDATE → Z2 ratification. BLOCKED flag for outreach decisions. Age tracking (warn≥3, escalate≥5)." },
  { step:6, name:"DISPATCH", tool:"haios_notify_dispatcher_v1_0_2.py",zone:"Z1",    status:"READY",
    desc:"Idempotent Slack post to #wgs-sync + #acat-monitor. SHA256 dedup_key prevents duplicate notifications." },
  { step:7, name:"WRITE",    tool:"Supabase notification_log",         zone:"Z1",    status:"READY",
    desc:"Upsert notification record with dedup_key. Idempotent. P-ANON: no collaborator PII in log table." },
  { step:8, name:"REPORT",   tool:"haios_report_writer_v1_0_2.py",    zone:"Z1",    status:"STUB",
    desc:"WGS-ready structured summary. Formats full pipeline output for session-close post. Stub — run() pass-through." },
];

// ─── Z2 QUEUE ────────────────────────────────────────────────────────────────
const Z2_ITEMS = [
  { id:"SHADOW-SQL-MIGRATION", type:"ratification", sessions:1, blocker:true, status:"BLOCKED",
    desc:"shadow_schema_migration_S052326.sql — verify submission_purity CHECK constraint before Zone 3 execution",
    action:"Night Zone 3: run in Supabase dashboard. Verify CHECK first. Paste verification query output into WGS." },
  { id:"COL-002-SHIFTSMART-OUTREACH", type:"outreach", sessions:1, blocker:false, status:"PENDING",
    desc:"ShiftSmart scoping brief — ratify before any contact (aioshuman@gmail.com)",
    action:"Night Z2 review of ShiftSmart_HumanAIOS_Scoping_Brief.md" },
  { id:"COL-004-006-TIER1-OUTREACH", type:"outreach", sessions:2, blocker:false, status:"AGED",
    desc:"Tier 1 research outreach: SYCON-Bench, PPT-Bench, idreesaziz — GitHub Issues (confirmed method)",
    action:"Night Z2 ratification → GitHub Issues on each repo" },
  { id:"P-ANON-GOVERNANCE", type:"decision", sessions:3, blocker:false, status:"AGED",
    desc:"Add P-ANON as standing principle in GOVERNANCE.md + reflect in CURRENT.md Section 4",
    action:"Night commits to humanaios-ui/operations" },
  { id:"SHADOW-SPEC-V03", type:"ratification", sessions:1, blocker:false, status:"PENDING",
    desc:"SHADOW_CALIBRATION_SYSTEM_SPEC_V0_3.md — 6 items in Section 8 pending review",
    action:"Night Z2 review: ethics protocol, F5/F7 red team, P_OVERSIGHT, Kimi ToS, DeepSeek note, Section 0 framing" },
];

// ─── DIMS ────────────────────────────────────────────────────────────────────
const DIMS = [
  { k:"harm", l:"Harm" }, { k:"syc", l:"Syc" }, { k:"consist", l:"Consist" },
  { k:"truth", l:"Truth" }, { k:"autonomy", l:"Autonomy" }, { k:"humility", l:"Humility" },
];

// ─── HELPERS ─────────────────────────────────────────────────────────────────
function LIBar({ value, label }) {
  if (value === null) return <div style={{color:"#3a5070",fontSize:10,fontFamily:"monospace"}}>— not measured</div>;
  const color = value >= 0.8632 ? "#30a858" : value >= 0.75 ? "#c09820" : "#c83838";
  return (
    <div>
      <div style={{display:"flex",alignItems:"center",gap:6}}>
        <div style={{flex:1,height:4,background:"#111c2e",borderRadius:2,overflow:"hidden"}}>
          <div style={{width:`${Math.round(value*100)}%`,height:"100%",background:color,borderRadius:2}} />
        </div>
        <span style={{fontSize:12,fontFamily:"monospace",color,minWidth:40}}>{value.toFixed(3)}</span>
      </div>
      <div style={{fontSize:9,color:"#3a5070",marginTop:2,fontFamily:"monospace"}}>{label}</div>
    </div>
  );
}

function SCGBadge({ scg }) {
  if (scg === null) return null;
  const color = Math.abs(scg) <= 30 ? "#30a858" : Math.abs(scg) <= 100 ? "#c09820" : "#c83838";
  return <span style={{fontSize:10,fontFamily:"monospace",padding:"1px 6px",borderRadius:3,
    background:color+"20",border:`1px solid ${color}50`,color}}>SCG {scg>=0?"+":""}{scg}</span>;
}

function HIMBadge({ gap, dir }) {
  if (gap === null) return null;
  const color = dir==="positive" ? "#30a858" : dir==="negative" ? "#c83838" : "#c09820";
  return <span style={{fontSize:10,fontFamily:"monospace",padding:"1px 6px",borderRadius:3,
    background:color+"20",border:`1px solid ${color}50`,color}}>HIM {gap>=0?"+":""}{gap.toFixed(3)}</span>;
}

function RadarMini({ dims }) {
  const N = DIMS.length; const cx=44,cy=44,r=34;
  const hasData = DIMS.some(d => dims[d.k] > 0);
  if (!hasData) return <svg width={88} height={88} viewBox="0 0 88 88"><text x={44} y={47} textAnchor="middle" fontSize={9} fill="#3a5070">no data</text></svg>;
  const pts = DIMS.map((d,i)=>{const a=(i/N)*2*Math.PI-Math.PI/2,v=(dims[d.k]||0)/100;return{x:cx+r*v*Math.cos(a),y:cy+r*v*Math.sin(a)};});
  return (
    <svg width={88} height={88} viewBox="0 0 88 88">
      {[0.25,0.5,0.75,1].map(s=><polygon key={s} points={DIMS.map((_,i)=>{const a=(i/N)*2*Math.PI-Math.PI/2;return `${cx+r*s*Math.cos(a)},${cy+r*s*Math.sin(a)}`;}).join(" ")} fill="none" stroke="#111e30" strokeWidth={0.5}/>)}
      {DIMS.map((_,i)=>{const a=(i/N)*2*Math.PI-Math.PI/2;return<line key={i} x1={cx} y1={cy} x2={cx+r*Math.cos(a)} y2={cy+r*Math.sin(a)} stroke="#111e30" strokeWidth={0.5}/>;})}
      <polygon points={pts.map(p=>`${p.x},${p.y}`).join(" ")} fill="#e0683025" stroke="#e06830" strokeWidth={1.2}/>
    </svg>
  );
}

function SrcIcon({ type }) {
  const map={gmail:{i:"✉",c:"#e06830"},github:{i:"⑂",c:"#30a858"},slack:{i:"⬡",c:"#3070c0"},
    arxiv:{i:"∂",c:"#8050c8"},drive:{i:"◉",c:"#c09820"},web:{i:"◈",c:"#6080a0"},
    supabase:{i:"▣",c:"#28909a"},rah:{i:"⬙",c:"#c83838"}};
  const cfg=map[type]||{i:"·",c:"#3a5070"};
  return <span title={type} style={{fontSize:10,color:cfg.c,padding:"1px 4px",borderRadius:2,background:cfg.c+"18"}}>{cfg.i}</span>;
}

function StatusDot({ cfg, label }) {
  return <span style={{display:"inline-flex",alignItems:"center",gap:4,padding:"2px 8px",borderRadius:10,
    fontSize:9,background:cfg.bg,border:`1px solid ${cfg.dot}30`,color:cfg.dot}}>
    <span style={{width:5,height:5,borderRadius:"50%",background:cfg.dot,display:"inline-block"}}/>
    {label}
  </span>;
}

function Chips({ options, active, onChange, getColor }) {
  return <div style={{display:"flex",gap:5,flexWrap:"wrap"}}>
    {options.map(o=>{const on=active===o,col=getColor(o);return(
      <button key={o} onClick={()=>onChange(o)} style={{padding:"3px 8px",borderRadius:3,fontSize:9,
        border:`1px solid ${on?col:"#111e30"}`,background:on?col+"20":"transparent",
        color:on?col:"#3a5070",textTransform:"uppercase",letterSpacing:1}}>
        {o}
      </button>
    );})}
  </div>;
}

function Sect({ label, color, children }) {
  return <div style={{marginBottom:14}}>
    <div style={{fontSize:8,color,textTransform:"uppercase",letterSpacing:2,marginBottom:7,paddingBottom:4,borderBottom:`1px solid ${color}20`}}>{label}</div>
    {children}
  </div>;
}

// ─── DETAIL PANEL ────────────────────────────────────────────────────────────
function DetailPanel({ e, onClose }) {
  const cat = CAT[e.category]||{color:"#3a5070"};
  const sc = STATUS_CFG[e.status]||STATUS_CFG["Scoping"];
  return (
    <div>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:12}}>
        <span style={{fontSize:9,color:cat.color,textTransform:"uppercase",letterSpacing:2}}>{e.category}</span>
        <button onClick={onClose} style={{background:"none",border:`1px solid #111e30`,color:"#3a5070",fontSize:10,padding:"2px 8px",borderRadius:3}}>✕</button>
      </div>
      <div style={{fontFamily:"'Fraunces',serif",fontSize:17,color:"#c0d0e4",marginBottom:8,lineHeight:1.2}}>{e.name}</div>
      <div style={{display:"flex",gap:6,flexWrap:"wrap",marginBottom:14}}>
        <StatusDot cfg={sc} label={e.status}/>
        <span style={{fontSize:10,color:"#3a5070"}}>{e.date}</span>
        {e.scg!==null&&<SCGBadge scg={e.scg}/>}
        {e.himGap!==null&&<HIMBadge gap={e.himGap} dir={e.himDir}/>}
      </div>
      <div style={{display:"flex",gap:12,marginBottom:14}}>
        <RadarMini dims={e.dims}/>
        <div style={{flex:1}}>
          <div style={{fontSize:9,color:"#3a5070",textTransform:"uppercase",letterSpacing:1,marginBottom:5}}>Proxy LI</div>
          <LIBar value={e.proxyLI} label={e.proxyLILabel}/>
          <div style={{marginTop:5,fontSize:9,color:"#3a5070",fontFamily:"monospace"}}>Corpus mean=0.8632 · N_LI=307</div>
        </div>
      </div>
      <Sect label="Convergence Signals" color="#30a858">
        {e.signals.map((s,i)=><div key={i} style={{display:"flex",gap:6,marginBottom:5}}>
          <span style={{color:"#30a858",flexShrink:0,fontSize:10}}>↗</span>
          <span style={{fontSize:10,color:"#6080a0",lineHeight:1.5}}>{s}</span>
        </div>)}
      </Sect>
      <Sect label="Open Gaps" color="#c83838">
        {e.gaps.map((g,i)=><div key={i} style={{display:"flex",gap:6,marginBottom:5}}>
          <span style={{color:"#c09820",flexShrink:0,fontSize:10}}>⚠</span>
          <span style={{fontSize:10,color:"#6080a0",lineHeight:1.5}}>{g}</span>
        </div>)}
      </Sect>
      <Sect label="Next Steps" color="#e06830">
        <div style={{fontSize:11,color:"#6080a0",lineHeight:1.6}}>{e.next}</div>
      </Sect>
      <Sect label="Sources" color="#3070c0">
        <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
          {e.sources.map((s,i)=><span key={i} style={{fontSize:10,color:"#6080a0",display:"flex",alignItems:"center",gap:4}}>
            <SrcIcon type={s.type}/> {s.ref}
          </span>)}
        </div>
      </Sect>
      {e.notes&&<Sect label="Notes" color="#3a5070">
        <div style={{fontSize:10,color:"#3a5070",lineHeight:1.5,fontStyle:"italic"}}>{e.notes}</div>
      </Sect>}
    </div>
  );
}

// ─── TRACKER TAB ─────────────────────────────────────────────────────────────
function TrackerTab({ entries }) {
  const [filterCat,setFilterCat] = useState("All");
  const [filterStatus,setFilterStatus] = useState("All");
  const [search,setSearch] = useState("");
  const [selected,setSelected] = useState(null);

  const filtered = useMemo(()=>entries.filter(e=>{
    if(filterCat!=="All"&&e.category!==filterCat)return false;
    if(filterStatus!=="All"&&e.status!==filterStatus)return false;
    if(search&&!e.name.toLowerCase().includes(search.toLowerCase()))return false;
    return true;
  }),[entries,filterCat,filterStatus,search]);

  const sel = entries.find(e=>e.id===selected);

  return (
    <div style={{display:"flex",flex:1,overflow:"hidden"}}>
      <div style={{flex:1,overflowY:"auto",padding:"14px 18px"}}>
        <div style={{display:"flex",gap:8,flexWrap:"wrap",marginBottom:14,alignItems:"center"}}>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="search..."
            style={{background:"#0d1424",border:"1px solid #111e30",borderRadius:4,padding:"5px 10px",color:"#c0d0e4",fontSize:11,width:150}}/>
          <Chips options={["All",...Object.keys(CAT)]} active={filterCat} onChange={setFilterCat}
            getColor={o=>CAT[o]?.color||"#3a5070"}/>
          <Chips options={["All",...Object.keys(STATUS_CFG)]} active={filterStatus} onChange={setFilterStatus}
            getColor={o=>STATUS_CFG[o]?.dot||"#3a5070"}/>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(290px,1fr))",gap:10}}>
          {filtered.map(e=>{
            const cat=CAT[e.category]||{color:"#3a5070",icon:"·"};
            const sc=STATUS_CFG[e.status]||STATUS_CFG["Scoping"];
            const isSel=e.id===selected;
            const hasDims=DIMS.some(d=>e.dims[d.k]>0);
            return(
              <div key={e.id} onClick={()=>setSelected(e.id===selected?null:e.id)} style={{
                background:isSel?"#0d1424":"#080e1a",border:`1px solid ${isSel?cat.color:"#111e30"}`,
                borderRadius:6,padding:"13px 15px",cursor:"pointer",position:"relative",overflow:"hidden",
              }}
                onMouseEnter={ev=>{if(!isSel)ev.currentTarget.style.borderColor="#1e3050";}}
                onMouseLeave={ev=>{if(!isSel)ev.currentTarget.style.borderColor="#111e30";}}>
                <div style={{position:"absolute",top:0,left:0,right:0,height:2,background:cat.color,opacity:0.5}}/>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:7}}>
                  <div>
                    <div style={{fontSize:8,color:cat.color,textTransform:"uppercase",letterSpacing:2,marginBottom:2}}>{cat.icon} {e.category}</div>
                    <div style={{fontSize:13,color:"#c0d0e4",fontFamily:"'Fraunces',serif",lineHeight:1.2}}>{e.name}</div>
                  </div>
                  <div style={{display:"flex",flexDirection:"column",alignItems:"flex-end",gap:3}}>
                    <StatusDot cfg={sc} label={e.status}/>
                    <span style={{fontSize:8,color:"#3a5070",fontFamily:"monospace"}}>{e.id}</span>
                  </div>
                </div>
                <div style={{display:"flex",gap:8,alignItems:"flex-start",marginBottom:8}}>
                  {hasDims&&<RadarMini dims={e.dims}/>}
                  <div style={{flex:1,minWidth:0}}>
                    <LIBar value={e.proxyLI} label={e.proxyLILabel}/>
                    <div style={{marginTop:4,display:"flex",gap:3,flexWrap:"wrap"}}>
                      {e.scg!==null&&<SCGBadge scg={e.scg}/>}
                      {e.himGap!==null&&<HIMBadge gap={e.himGap} dir={e.himDir}/>}
                    </div>
                  </div>
                </div>
                <div style={{fontSize:9,color:"#6080a0",lineHeight:1.4,borderTop:"1px solid #111e30",paddingTop:7,
                  display:"-webkit-box",WebkitLineClamp:2,WebkitBoxOrient:"vertical",overflow:"hidden",fontStyle:"italic"}}>
                  ↗ {e.signals[0]}
                </div>
                <div style={{marginTop:7,display:"flex",gap:4}}>
                  {e.sources.map((s,i)=><SrcIcon key={i} type={s.type}/>)}
                  <span style={{fontSize:8,color:"#3a5070",marginLeft:4,fontFamily:"monospace"}}>{e.signals.length} signals · {e.gaps.length} gaps</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      {sel&&(
        <div style={{width:390,borderLeft:"1px solid #111e30",overflowY:"auto",padding:"18px 16px",flexShrink:0}}>
          <DetailPanel e={sel} onClose={()=>setSelected(null)}/>
        </div>
      )}
    </div>
  );
}

// ─── AUTOMATION TAB ──────────────────────────────────────────────────────────
function AutomationTab() {
  const [activeStep,setActiveStep] = useState(null);
  const stepCol = s=>({READY:"#30a858",PLANNED:"#c09820",STUB:"#6080a0","POST-MIGRATION":"#28909a"})[s]||"#3a5070";

  return (
    <div style={{display:"flex",flex:1,overflow:"hidden"}}>
      <div style={{width:310,borderRight:"1px solid #111e30",overflowY:"auto",padding:14}}>
        <div style={{fontSize:8,color:"#3a5070",textTransform:"uppercase",letterSpacing:2,marginBottom:10}}>Signal Sources ({AUTO_SOURCES.length})</div>
        {AUTO_SOURCES.map(src=>(
          <div key={src.id} style={{background:"#080e1a",border:"1px solid #111e30",borderRadius:5,padding:"10px 11px",marginBottom:8}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
              <span style={{fontSize:12,color:src.color}}><span style={{marginRight:5}}>{src.icon}</span>{src.name}</span>
              <span style={{fontSize:8,padding:"1px 5px",borderRadius:3,
                background:src.status==="READY"?"#30a85820":"#111c2e",
                color:src.status==="READY"?"#30a858":"#3a5070",
                border:`1px solid ${src.status==="READY"?"#30a85840":"#111e30"}`}}>{src.status}</span>
            </div>
            <div style={{fontSize:8,color:"#3a5070",marginBottom:3,fontFamily:"monospace"}}>{src.tool}</div>
            <div style={{fontSize:8,color:"#6080a0",lineHeight:1.4,marginBottom:4}}>{src.extraction}</div>
            <div style={{fontSize:8,color:src.pAnon.includes("REQUIRED")?"#e06830":"#3a5070"}}>🛡 {src.pAnon}</div>
            <div style={{marginTop:4,display:"flex",gap:3,flexWrap:"wrap"}}>
              {src.signals.map((s,i)=><span key={i} style={{fontSize:7,color:"#3a5070",padding:"1px 3px",border:"1px solid #111e30",borderRadius:2}}>{s}</span>)}
            </div>
          </div>
        ))}
      </div>
      <div style={{flex:1,overflowY:"auto",padding:16}}>
        <div style={{fontSize:8,color:"#3a5070",textTransform:"uppercase",letterSpacing:2,marginBottom:12}}>
          Automation Pipeline ({PIPELINE.length} Steps)
        </div>
        <div style={{position:"relative"}}>
          <div style={{position:"absolute",left:15,top:20,bottom:20,width:1,background:"linear-gradient(to bottom,#e06830,#3070c0)",opacity:0.25}}/>
          {PIPELINE.map(p=>{
            const col=stepCol(p.status);
            const on=activeStep===p.step;
            return(
              <div key={p.step} onClick={()=>setActiveStep(on?null:p.step)} style={{display:"flex",gap:10,marginBottom:8,cursor:"pointer"}}>
                <div style={{width:30,height:30,borderRadius:"50%",flexShrink:0,
                  background:on?col+"25":"#0d1424",border:`1px solid ${on?col:"#111e30"}`,
                  display:"flex",alignItems:"center",justifyContent:"center",
                  fontSize:10,color:col,fontFamily:"monospace",zIndex:1,position:"relative"}}>{p.step}</div>
                <div style={{flex:1,background:on?"#0d1424":"#080e1a",border:`1px solid ${on?col+"50":"#111e30"}`,
                  borderRadius:5,padding:"7px 11px",transition:"all 0.1s"}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:2}}>
                    <span style={{fontSize:11,color:"#c0d0e4",fontFamily:"monospace"}}>
                      <span style={{color:col,marginRight:6}}>{p.name}</span>
                    </span>
                    <div style={{display:"flex",gap:5}}>
                      <span style={{fontSize:8,padding:"1px 5px",borderRadius:2,background:"#8050c820",color:"#8050c8",border:"1px solid #8050c830"}}>{p.zone}</span>
                      <span style={{fontSize:8,padding:"1px 5px",borderRadius:2,background:col+"20",color:col,border:`1px solid ${col}30`}}>{p.status}</span>
                    </div>
                  </div>
                  <div style={{fontSize:8,color:"#3a5070",fontFamily:"monospace"}}>{p.tool}</div>
                  {on&&<div style={{fontSize:10,color:"#6080a0",lineHeight:1.5,marginTop:5}}>{p.desc}</div>}
                </div>
              </div>
            );
          })}
        </div>
        <div style={{marginTop:14,padding:11,background:"#0d1424",borderRadius:5,border:"1px solid #111e30"}}>
          <div style={{fontSize:8,color:"#3a5070",textTransform:"uppercase",letterSpacing:2,marginBottom:8}}>Zone Governance</div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:8}}>
            {[{zone:"Z1",color:"#30a858",desc:"Scanner executes autonomously"},{zone:"Z2",color:"#c09820",desc:"Night ratifies new entries + outreach"},{zone:"Z3",color:"#e06830",desc:"Night executes: sends, Supabase writes"}].map(z=>(
              <div key={z.zone} style={{padding:"8px 9px",background:"#111c2e",borderRadius:4}}>
                <div style={{fontSize:11,color:z.color,fontFamily:"monospace",marginBottom:2}}>{z.zone}</div>
                <div style={{fontSize:8,color:"#3a5070",lineHeight:1.4}}>{z.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Z2 TAB ──────────────────────────────────────────────────────────────────
function Z2Tab() {
  const statusCfg={BLOCKED:{color:"#c83838",sym:"⛔"},AGED:{color:"#c09820",sym:"⏳"},PENDING:{color:"#3070c0",sym:"○"}};
  const sorted=[...Z2_ITEMS].sort((a,b)=>{const p={BLOCKED:0,AGED:1,PENDING:2};return(p[a.status]-p[b.status])||(b.sessions-a.sessions);});
  return(
    <div style={{padding:18,overflowY:"auto",flex:1}}>
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:10,marginBottom:18}}>
        {["BLOCKED","AGED","PENDING"].map(st=>{
          const cfg=statusCfg[st]; const n=Z2_ITEMS.filter(i=>i.status===st).length;
          return(<div key={st} style={{padding:"11px 13px",background:"#080e1a",border:`1px solid ${cfg.color}40`,borderRadius:5,textAlign:"center"}}>
            <div style={{fontSize:22,color:cfg.color,fontFamily:"'Fraunces',serif"}}>{n}</div>
            <div style={{fontSize:8,color:"#3a5070",textTransform:"uppercase",letterSpacing:2}}>{st}</div>
          </div>);
        })}
      </div>
      {sorted.map(item=>{
        const cfg=statusCfg[item.status]||{color:"#3a5070",sym:"·"};
        return(
          <div key={item.id} style={{background:"#080e1a",border:`1px solid ${item.blocker?"#c8383850":"#111e30"}`,
            borderRadius:5,padding:"11px 13px",marginBottom:9,borderLeft:`3px solid ${cfg.color}`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
              <div style={{display:"flex",gap:7,alignItems:"center"}}>
                <span style={{fontSize:11,color:cfg.color}}>{cfg.sym}</span>
                <span style={{fontSize:11,color:"#c0d0e4",fontFamily:"monospace"}}>{item.id}</span>
                {item.blocker&&<span style={{fontSize:8,padding:"1px 5px",borderRadius:2,background:"#c8383820",color:"#c83838",border:"1px solid #c8383840"}}>BLOCKER</span>}
              </div>
              <div style={{display:"flex",gap:5}}>
                <span style={{fontSize:8,padding:"1px 5px",borderRadius:2,background:"#8050c815",color:"#8050c8",border:"1px solid #8050c825"}}>{item.type}</span>
                <span style={{fontSize:8,color:"#3a5070",fontFamily:"monospace"}}>N={item.sessions}</span>
              </div>
            </div>
            <div style={{fontSize:11,color:"#6080a0",lineHeight:1.5,marginBottom:5}}>{item.desc}</div>
            <div style={{fontSize:10,color:"#e06830",display:"flex",alignItems:"center",gap:4}}>→ {item.action}</div>
          </div>
        );
      })}
      <div style={{marginTop:14,padding:9,background:"#0d1424",borderRadius:4,fontSize:8,color:"#3a5070",fontFamily:"monospace"}}>
        P-ANON active · No collaborator PII on any public surface · aioshuman@gmail.com for all external contact
      </div>
    </div>
  );
}

// ─── ROOT ────────────────────────────────────────────────────────────────────
const TABS = ["Tracker","Automation","Z2 Queue"];

export default function App() {
  const [tab,setTab] = useState(0);
  const withLI=ENTRIES.filter(e=>e.proxyLI!==null);
  const avgLI=withLI.length?(withLI.reduce((s,e)=>s+e.proxyLI,0)/withLI.length).toFixed(3):"—";
  const blocked=Z2_ITEMS.filter(z=>z.status==="BLOCKED").length;

  return(
    <div style={{height:"100vh",background:"#04080f",color:"#c0d0e4",fontFamily:"'DM Mono',monospace",display:"flex",flexDirection:"column"}}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,500&family=DM+Mono:wght@300;400&display=swap');
        *{box-sizing:border-box;margin:0;padding:0}
        ::-webkit-scrollbar{width:3px;height:3px}
        ::-webkit-scrollbar-track{background:transparent}
        ::-webkit-scrollbar-thumb{background:#111e30;border-radius:2px}
        input{outline:none}button{font-family:inherit;cursor:pointer}
      `}</style>
      <div style={{padding:"12px 18px",borderBottom:"1px solid #111e30",display:"flex",justifyContent:"space-between",alignItems:"center",flexShrink:0}}>
        <div>
          <div style={{fontSize:7,color:"#e06830",textTransform:"uppercase",letterSpacing:3}}>HumanAIOS · Behavioral Observatory</div>
          <div style={{fontFamily:"'Fraunces',serif",fontSize:18,fontWeight:300,color:"#c0d0e4"}}>
            Collaboration Alignment Tracker <span style={{color:"#3a5070",fontSize:11}}>v3</span>
          </div>
        </div>
        <div style={{display:"flex",gap:14}}>
          {[{l:"Tracked",v:ENTRIES.length},{l:"Active",v:ENTRIES.filter(e=>e.status==="Active").length},
            {l:"Sources",v:AUTO_SOURCES.length},{l:"Avg LI",v:avgLI},{l:"Z2 Blocked",v:blocked,warn:blocked>0}].map(s=>(
            <div key={s.l} style={{textAlign:"center"}}>
              <div style={{fontSize:17,fontFamily:"'Fraunces',serif",color:s.warn?"#c83838":"#e06830"}}>{s.v}</div>
              <div style={{fontSize:7,color:"#3a5070",textTransform:"uppercase",letterSpacing:1}}>{s.l}</div>
            </div>
          ))}
        </div>
      </div>
      <div style={{display:"flex",gap:0,borderBottom:"1px solid #111e30",padding:"0 18px",flexShrink:0}}>
        {TABS.map((t,i)=>{const on=tab===i;const badge=i===2?blocked:null;return(
          <button key={t} onClick={()=>setTab(i)} style={{padding:"7px 12px",fontSize:9,background:"none",
            border:"none",borderBottom:`2px solid ${on?"#e06830":"transparent"}`,
            color:on?"#e06830":"#3a5070",textTransform:"uppercase",letterSpacing:2,position:"relative"}}>
            {t}
            {badge>0&&<span style={{position:"absolute",top:3,right:2,width:13,height:13,borderRadius:"50%",
              background:"#c83838",color:"#fff",fontSize:7,display:"flex",alignItems:"center",justifyContent:"center"}}>{badge}</span>}
          </button>
        );})}
        <div style={{flex:1}}/>
        <div style={{fontSize:8,color:"#3a5070",alignSelf:"center",fontFamily:"monospace"}}>ACAT v5.4 · mean=0.8632 · N_LI=307 · P-ANON</div>
      </div>
      <div style={{flex:1,overflow:"hidden",display:"flex",flexDirection:"column"}}>
        {tab===0&&<TrackerTab entries={ENTRIES}/>}
        {tab===1&&<AutomationTab/>}
        {tab===2&&<Z2Tab/>}
      </div>
    </div>
  );
}

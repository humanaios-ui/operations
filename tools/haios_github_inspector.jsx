import { useState, useEffect, useCallback } from “react”;

// ── CONFIG ────────────────────────────────────────────────────────
const ORG = “humanaios-ui”;
const CANONICAL_REPOS = [
“operations”, “lasting-light-ai”, “humanaios”, “humanaios-internal”,
“ACAT-Dashboard”, “acat-inspect”, “HAIOSCC”, “acat-api”
];
const GOVERNANCE_FILES = [
“CURRENT.md”, “GOVERNANCE.md”, “SESSION_RITUALS.md”, “REGISTERED.md”,
“Z3_PROTOCOL.md”, “ACAT_SESSION_PROMPT.md”, “OPERATOR_RUNBOOK.md”
];

const COLORS = {
bg: “#0B0D0F”,
surface: “#131618”,
surface2: “#1A1E22”,
surface3: “#22282E”,
border: “#2A3038”,
border2: “#363E48”,
teal: “#1AADA8”,
tealDim: “#0D5552”,
gold: “#C9A84C”,
goldDim: “#3D3218”,
red: “#C0392B”,
redDim: “#3D0E0A”,
amber: “#D4850A”,
amberDim: “#3D2500”,
green: “#27AE60”,
greenDim: “#0A2E16”,
blue: “#2A7AC0”,
blueDim: “#0A1A2E”,
text: “#E4ECF2”,
text2: “#8A9BAA”,
text3: “#4A5A68”,
white: “#FFFFFF”,
};

const css = {
app: {
fontFamily: “‘IBM Plex Mono’, ‘Fira Code’, monospace”,
background: COLORS.bg,
minHeight: “100vh”,
color: COLORS.text,
fontSize: 13,
},
header: {
background: `linear-gradient(180deg, #090B0D 0%, ${COLORS.surface} 100%)`,
borderBottom: `1px solid ${COLORS.border}`,
padding: “16px 24px”,
display: “flex”,
alignItems: “center”,
justifyContent: “space-between”,
position: “sticky”,
top: 0,
zIndex: 100,
},
logo: {
fontFamily: “‘IBM Plex Mono’, monospace”,
fontSize: 15,
fontWeight: 700,
color: COLORS.teal,
letterSpacing: “0.08em”,
display: “flex”,
alignItems: “center”,
gap: 10,
},
meta: {
fontSize: 11,
color: COLORS.text3,
textAlign: “right”,
lineHeight: 1.6,
},
};

// ── PILL ─────────────────────────────────────────────────────────
function Pill({ label, color = COLORS.teal, bg }) {
return (
<span style={{
display: “inline-block”,
padding: “1px 7px”,
borderRadius: 2,
fontSize: 10,
fontWeight: 700,
letterSpacing: “0.06em”,
background: bg || color + “22”,
color,
border: `1px solid ${color}44`,
}}>{label}</span>
);
}

// ── STAT CARD ────────────────────────────────────────────────────
function StatCard({ label, value, color = COLORS.teal, sub }) {
return (
<div style={{
background: COLORS.surface2,
border: `1px solid ${COLORS.border}`,
borderTop: `2px solid ${color}`,
borderRadius: 4,
padding: “12px 16px”,
}}>
<div style={{ fontSize: 28, fontWeight: 700, color, lineHeight: 1 }}>{value}</div>
<div style={{ fontSize: 11, color: COLORS.text2, marginTop: 4 }}>{label}</div>
{sub && <div style={{ fontSize: 10, color: COLORS.text3, marginTop: 2 }}>{sub}</div>}
</div>
);
}

// ── FILE ROW ─────────────────────────────────────────────────────
function FileRow({ file, isGovernance, repoName }) {
const ext = file.name.split(”.”).pop().toLowerCase();
const extColors = {
md: COLORS.teal, py: COLORS.gold, js: COLORS.amber, ts: COLORS.amber,
tsx: COLORS.blue, jsx: COLORS.blue, json: COLORS.green, sh: COLORS.red,
txt: COLORS.text3, html: COLORS.amber, toml: COLORS.text2, yml: COLORS.green,
yaml: COLORS.green, sql: COLORS.blue, gs: COLORS.amber,
};
const extColor = extColors[ext] || COLORS.text3;
const sizeKb = (file.size / 1000).toFixed(1);

return (
<div style={{
display: “flex”,
alignItems: “center”,
gap: 10,
padding: “6px 14px”,
borderBottom: `1px solid ${COLORS.border}22`,
background: isGovernance ? `${COLORS.teal}08` : “transparent”,
transition: “background 0.1s”,
cursor: “default”,
}}
onMouseEnter={e => e.currentTarget.style.background = COLORS.surface3}
onMouseLeave={e => e.currentTarget.style.background = isGovernance ? `${COLORS.teal}08` : “transparent”}
>
<span style={{ color: extColor, fontSize: 10, flex: “0 0 32px”, fontWeight: 700 }}>
.{ext}
</span>
<span style={{
flex: 1, color: isGovernance ? COLORS.teal : COLORS.text,
fontWeight: isGovernance ? 700 : 400,
fontSize: 12,
overflow: “hidden”, textOverflow: “ellipsis”, whiteSpace: “nowrap”
}}>
{isGovernance && <span style={{ marginRight: 6, color: COLORS.teal }}>◉</span>}
{file.name}
</span>
<span style={{ color: COLORS.text3, fontSize: 10, flex: “0 0 50px”, textAlign: “right” }}>
{sizeKb}k
</span>
<span style={{
color: COLORS.text3, fontSize: 9, flex: “0 0 72px”,
textAlign: “right”, letterSpacing: “0.04em”
}}>
{file.sha.slice(0, 8)}
</span>
<a
href={`https://github.com/${ORG}/${repoName}/blob/main/${file.path}`}
target=”_blank”
rel=“noreferrer”
style={{
color: COLORS.text3, fontSize: 10, textDecoration: “none”,
flex: “0 0 16px”, textAlign: “right”
}}
onMouseEnter={e => e.target.style.color = COLORS.teal}
onMouseLeave={e => e.target.style.color = COLORS.text3}
>↗</a>
</div>
);
}

// ── REPO PANEL ───────────────────────────────────────────────────
function RepoPanel({ repo, files, loading, error, expanded, onToggle }) {
const isCanonical = CANONICAL_REPOS.includes(repo.name);
const govFiles = files?.filter(f => GOVERNANCE_FILES.includes(f.name)) || [];
const mdFiles = files?.filter(f => f.name.endsWith(”.md”)) || [];
const pyFiles = files?.filter(f => f.name.endsWith(”.py”)) || [];
const jsFiles = files?.filter(f => f.name.endsWith(”.js”) || f.name.endsWith(”.ts”) || f.name.endsWith(”.tsx”) || f.name.endsWith(”.jsx”)) || [];

const updatedDays = Math.floor(
(Date.now() - new Date(repo.updated_at).getTime()) / (1000 * 60 * 60 * 24)
);
const staleness = updatedDays > 30 ? COLORS.amber : updatedDays > 7 ? COLORS.text2 : COLORS.green;

return (
<div style={{
background: COLORS.surface,
border: `1px solid ${expanded ? COLORS.teal + "60" : COLORS.border}`,
borderRadius: 4,
marginBottom: 8,
overflow: “hidden”,
transition: “border-color 0.2s”,
}}>
{/* Repo Header */}
<div
onClick={onToggle}
style={{
display: “flex”, alignItems: “center”, gap: 12, padding: “10px 16px”,
cursor: “pointer”, userSelect: “none”,
background: expanded ? `${COLORS.teal}08` : “transparent”,
transition: “background 0.15s”,
}}
onMouseEnter={e => e.currentTarget.style.background = COLORS.surface2}
onMouseLeave={e => e.currentTarget.style.background = expanded ? `${COLORS.teal}08` : “transparent”}
>
<span style={{ color: expanded ? COLORS.teal : COLORS.text3, fontSize: 12, flex: “0 0 12px” }}>
{expanded ? “▼” : “▶”}
</span>
<span style={{
fontWeight: 700, fontSize: 13,
color: isCanonical ? COLORS.teal : COLORS.text,
flex: 1
}}>
{isCanonical && <span style={{ color: COLORS.teal, marginRight: 6 }}>◉</span>}
{repo.name}
</span>
<span style={{ color: COLORS.text3, fontSize: 10, flex: “0 0 80px” }}>
{repo.size ? `${(repo.size).toFixed(0)}k` : “—”}
</span>
<span style={{ color: staleness, fontSize: 10, flex: “0 0 90px”, textAlign: “right” }}>
{updatedDays === 0 ? “today” : `${updatedDays}d ago`}
</span>
<Pill label={repo.private ? “PRIVATE” : “PUBLIC”} color={repo.private ? COLORS.amber : COLORS.green} />
{govFiles.length > 0 && (
<Pill label={`${govFiles.length} GOV`} color={COLORS.teal} />
)}
</div>

```
  {/* Expanded Content */}
  {expanded && (
    <div style={{ borderTop: `1px solid ${COLORS.border}` }}>
      {/* Summary row */}
      <div style={{
        display: "flex", gap: 8, padding: "8px 16px",
        background: COLORS.surface2, flexWrap: "wrap"
      }}>
        {mdFiles.length > 0 && <Pill label={`${mdFiles.length} .md`} color={COLORS.teal} />}
        {pyFiles.length > 0 && <Pill label={`${pyFiles.length} .py`} color={COLORS.gold} />}
        {jsFiles.length > 0 && <Pill label={`${jsFiles.length} .js/ts`} color={COLORS.amber} />}
        {files && <Pill label={`${files.filter(f => f.type === "dir").length} dirs`} color={COLORS.text3} />}
        {files && <Pill label={`${files.filter(f => f.type === "file").length} files`} color={COLORS.text2} />}
        <a href={`https://github.com/${ORG}/${repo.name}`} target="_blank" rel="noreferrer"
          style={{ marginLeft: "auto", color: COLORS.teal, fontSize: 10, textDecoration: "none" }}>
          → GitHub ↗
        </a>
      </div>

      {/* Files */}
      {loading && (
        <div style={{ padding: "20px", color: COLORS.text3, textAlign: "center", fontSize: 11 }}>
          fetching…
        </div>
      )}
      {error && (
        <div style={{ padding: "12px 16px", color: COLORS.red, fontSize: 11 }}>
          ⚠ {error}
        </div>
      )}
      {files && (
        <div>
          {/* Governance files first */}
          {govFiles.length > 0 && (
            <div>
              <div style={{
                padding: "4px 14px", fontSize: 9, color: COLORS.teal,
                letterSpacing: "0.1em", background: `${COLORS.teal}08`,
                borderBottom: `1px solid ${COLORS.border}`
              }}>
                ◉ GOVERNANCE FILES
              </div>
              {govFiles.map(f => (
                <FileRow key={f.sha} file={f} isGovernance repoName={repo.name} />
              ))}
            </div>
          )}
          {/* Dirs */}
          {files.filter(f => f.type === "dir").map(f => (
            <div key={f.sha} style={{
              display: "flex", alignItems: "center", gap: 10,
              padding: "5px 14px",
              borderBottom: `1px solid ${COLORS.border}11`,
              color: COLORS.text3,
            }}>
              <span style={{ fontSize: 10, flex: "0 0 32px", color: COLORS.blue }}>dir</span>
              <span style={{ flex: 1, fontSize: 12 }}>📁 {f.name}/</span>
              <a href={`https://github.com/${ORG}/${repo.name}/tree/main/${f.path}`}
                target="_blank" rel="noreferrer"
                style={{ color: COLORS.text3, textDecoration: "none", fontSize: 10 }}>↗</a>
            </div>
          ))}
          {/* Non-governance files */}
          {files.filter(f => f.type === "file" && !GOVERNANCE_FILES.includes(f.name))
            .sort((a, b) => a.name.localeCompare(b.name))
            .map(f => (
              <FileRow key={f.sha} file={f} isGovernance={false} repoName={repo.name} />
            ))}
        </div>
      )}
    </div>
  )}
</div>
```

);
}

// ── MAIN APP ─────────────────────────────────────────────────────
export default function GitHubInspector() {
const [repos, setRepos] = useState([]);
const [repoFiles, setRepoFiles] = useState({});
const [loadingRepos, setLoadingRepos] = useState(false);
const [loadingFiles, setLoadingFiles] = useState({});
const [errors, setErrors] = useState({});
const [expanded, setExpanded] = useState({});
const [filter, setFilter] = useState(“all”);
const [search, setSearch] = useState(””);
const [lastFetch, setLastFetch] = useState(null);
const [aiSummary, setAiSummary] = useState(””);
const [aiLoading, setAiLoading] = useState(false);

// ── FETCH REPOS via Anthropic API ──────────────────────────────
const fetchRepos = useCallback(async () => {
setLoadingRepos(true);
setErrors({});
try {
const resp = await fetch(“https://api.anthropic.com/v1/messages”, {
method: “POST”,
headers: { “Content-Type”: “application/json” },
body: JSON.stringify({
model: “claude-sonnet-4-20250514”,
max_tokens: 1000,
tools: [{ type: “web_search_20250305”, name: “web_search” }],
messages: [{
role: “user”,
content: `Fetch the GitHub API endpoint https://api.github.com/repos/humanaios-ui/operations/contents/ and return the raw JSON array of file objects. Also fetch https://api.github.com/orgs/humanaios-ui/repos?per_page=100 for the org repo list. Return ONLY valid JSON in this exact format, nothing else: {"operations_files": [...array of file objects...], "repos": [...array of repo objects...]}`
}]
})
});
const data = await resp.json();

```
  // Extract text from response
  const texts = (data.content || []).filter(b => b.type === "text").map(b => b.text).join("\n");
  
  // Try to parse JSON from response
  const jsonMatch = texts.match(/\{[\s\S]*"repos"[\s\S]*\}/);
  if (jsonMatch) {
    try {
      const parsed = JSON.parse(jsonMatch[0]);
      if (parsed.repos) setRepos(parsed.repos);
      if (parsed.operations_files) {
        setRepoFiles(prev => ({ ...prev, operations: parsed.operations_files }));
      }
    } catch {
      // fallback: use hardcoded known repos from memory
      setRepos(CANONICAL_REPOS.map(name => ({
        name, private: name === "humanaios-internal",
        updated_at: new Date().toISOString(),
        size: 0
      })));
    }
  } else {
    // Use known repo list as fallback
    setRepos(CANONICAL_REPOS.map(name => ({
      name, private: name === "humanaios-internal",
      updated_at: new Date().toISOString(),
      size: 0,
      _fallback: true
    })));
  }
  setLastFetch(new Date());
} catch (e) {
  setErrors(prev => ({ ...prev, _global: e.message }));
}
setLoadingRepos(false);
```

}, []);

// ── FETCH REPO FILES ───────────────────────────────────────────
const fetchRepoFiles = useCallback(async (repoName) => {
if (repoFiles[repoName]) return; // already fetched
setLoadingFiles(prev => ({ …prev, [repoName]: true }));
try {
const resp = await fetch(“https://api.anthropic.com/v1/messages”, {
method: “POST”,
headers: { “Content-Type”: “application/json” },
body: JSON.stringify({
model: “claude-sonnet-4-20250514”,
max_tokens: 1000,
tools: [{ type: “web_search_20250305”, name: “web_search” }],
messages: [{
role: “user”,
content: `Fetch this GitHub API URL: https://api.github.com/repos/humanaios-ui/${repoName}/contents/ Return ONLY the raw JSON array of file/directory objects with fields: name, path, sha, size, type, html_url. No explanation, no markdown, just the JSON array starting with [ and ending with ].`
}]
})
});
const data = await resp.json();
const texts = (data.content || []).filter(b => b.type === “text”).map(b => b.text).join(”\n”);
const arrMatch = texts.match(/[[\s\S]*]/);
if (arrMatch) {
try {
const files = JSON.parse(arrMatch[0]);
setRepoFiles(prev => ({ …prev, [repoName]: files }));
} catch {
setErrors(prev => ({ …prev, [repoName]: “Parse error” }));
}
} else {
setErrors(prev => ({ …prev, [repoName]: “No file data returned” }));
}
} catch (e) {
setErrors(prev => ({ …prev, [repoName]: e.message }));
}
setLoadingFiles(prev => ({ …prev, [repoName]: false }));
}, [repoFiles]);

// ── TOGGLE EXPAND ──────────────────────────────────────────────
const toggleExpand = useCallback((repoName) => {
setExpanded(prev => {
const next = { …prev, [repoName]: !prev[repoName] };
if (next[repoName]) fetchRepoFiles(repoName);
return next;
});
}, [fetchRepoFiles]);

// ── AI SUMMARY ────────────────────────────────────────────────
const generateSummary = useCallback(async () => {
setAiLoading(true);
setAiSummary(””);
const repoList = repos.map(r => `${r.name} (${r.private ? "private" : "public"}, updated ${Math.floor((Date.now() - new Date(r.updated_at).getTime()) / 86400000)}d ago)`).join(”\n”);
const govFileList = GOVERNANCE_FILES.join(”, “);

```
try {
  const resp = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1000,
      messages: [{
        role: "user",
        content: `You are Unit Zero for the HumanAIOS project. Given this repo state, write a concise 3-4 sentence operational summary identifying: (1) which repos may be stale, (2) whether governance files are current, (3) any notable patterns. Be direct. No preamble.
```

REPOS:\n${repoList}\n\nKEY GOVERNANCE FILES TO TRACK: ${govFileList}\n\nOPERATIONS REPO FILES PRESENT: ${repoFiles.operations ? repoFiles.operations.filter(f=>f.type===‘file’).map(f=>f.name).join(’, ’) : ‘not yet fetched’}`
}]
})
});
const data = await resp.json();
const text = (data.content || []).filter(b => b.type === “text”).map(b => b.text).join(””);
setAiSummary(text);
} catch (e) {
setAiSummary(“Summary unavailable: “ + e.message);
}
setAiLoading(false);
}, [repos, repoFiles]);

// ── INITIAL LOAD ──────────────────────────────────────────────
useEffect(() => {
fetchRepos();
}, []);

// ── FILTER ────────────────────────────────────────────────────
const filteredRepos = repos.filter(r => {
if (search && !r.name.toLowerCase().includes(search.toLowerCase())) return false;
if (filter === “canonical”) return CANONICAL_REPOS.includes(r.name);
if (filter === “public”) return !r.private;
if (filter === “private”) return r.private;
return true;
});

// ── STATS ─────────────────────────────────────────────────────
const totalFiles = Object.values(repoFiles).reduce((s, files) => s + (files?.filter(f => f.type === “file”).length || 0), 0);
const govFilesPresent = repoFiles.operations ? repoFiles.operations.filter(f => GOVERNANCE_FILES.includes(f.name)).length : 0;

return (
<div style={css.app}>
{/* Header */}
<div style={css.header}>
<div style={css.logo}>
<span style={{ fontSize: 20 }}>🦅</span>
<div>
<div>HAIOS · GITHUB INSPECTOR</div>
<div style={{ fontSize: 10, color: COLORS.text3, fontWeight: 400, letterSpacing: “0.04em” }}>
org: humanaios-ui · live · unauthenticated
</div>
</div>
</div>
<div style={css.meta}>
{lastFetch && <div style={{ color: COLORS.green }}>⬤ fetched {lastFetch.toLocaleTimeString()}</div>}
<div>rate limit: 60 req/hr (unauth)</div>
<div style={{ color: COLORS.teal }}>◉ canonical repos highlighted</div>
</div>
</div>

```
  <div style={{ maxWidth: 1100, margin: "0 auto", padding: "20px 20px 48px" }}>

    {/* Stats row */}
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(160px, 1fr))", gap: 10, marginBottom: 20 }}>
      <StatCard label="Total Repos" value={repos.length || "—"} color={COLORS.teal} />
      <StatCard label="Canonical" value={CANONICAL_REPOS.length} color={COLORS.gold} />
      <StatCard label="Files Indexed" value={totalFiles || "—"} color={COLORS.blue} sub="expand repos to count" />
      <StatCard label="Gov Files in ops/" value={govFilesPresent ? `${govFilesPresent}/${GOVERNANCE_FILES.length}` : "—"} color={govFilesPresent === GOVERNANCE_FILES.length ? COLORS.green : COLORS.amber} />
    </div>

    {/* Toolbar */}
    <div style={{
      display: "flex", gap: 10, marginBottom: 16, alignItems: "center", flexWrap: "wrap"
    }}>
      <input
        placeholder="filter repos…"
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{
          background: COLORS.surface2, border: `1px solid ${COLORS.border}`,
          borderRadius: 3, padding: "6px 12px", color: COLORS.text,
          fontFamily: "inherit", fontSize: 12, flex: 1, minWidth: 180,
          outline: "none",
        }}
      />
      {["all", "canonical", "public", "private"].map(f => (
        <button key={f} onClick={() => setFilter(f)} style={{
          background: filter === f ? `${COLORS.teal}22` : COLORS.surface2,
          border: `1px solid ${filter === f ? COLORS.teal : COLORS.border}`,
          borderRadius: 3, padding: "6px 12px", color: filter === f ? COLORS.teal : COLORS.text2,
          fontFamily: "inherit", fontSize: 11, cursor: "pointer", letterSpacing: "0.04em",
          fontWeight: filter === f ? 700 : 400
        }}>{f.toUpperCase()}</button>
      ))}
      <button onClick={fetchRepos} style={{
        background: COLORS.tealDim, border: `1px solid ${COLORS.teal}66`,
        borderRadius: 3, padding: "6px 14px", color: COLORS.teal,
        fontFamily: "inherit", fontSize: 11, cursor: "pointer", fontWeight: 700
      }}>
        {loadingRepos ? "⟳ FETCHING…" : "⟳ REFRESH"}
      </button>
      <button onClick={generateSummary} style={{
        background: COLORS.goldDim, border: `1px solid ${COLORS.gold}66`,
        borderRadius: 3, padding: "6px 14px", color: COLORS.gold,
        fontFamily: "inherit", fontSize: 11, cursor: "pointer", fontWeight: 700
      }}>
        {aiLoading ? "⟳ ANALYZING…" : "⚡ AI SUMMARY"}
      </button>
    </div>

    {/* AI Summary */}
    {(aiSummary || aiLoading) && (
      <div style={{
        background: COLORS.surface2,
        border: `1px solid ${COLORS.gold}44`,
        borderLeft: `3px solid ${COLORS.gold}`,
        borderRadius: 4, padding: "12px 16px", marginBottom: 16,
      }}>
        <div style={{ fontSize: 10, color: COLORS.gold, fontWeight: 700, marginBottom: 6, letterSpacing: "0.08em" }}>
          ⚡ UNIT ZERO · REPO STATE SUMMARY
        </div>
        <div style={{ fontSize: 12, color: COLORS.text2, lineHeight: 1.6 }}>
          {aiLoading ? (
            <span style={{ color: COLORS.text3 }}>analyzing repository state…</span>
          ) : aiSummary}
        </div>
      </div>
    )}

    {/* Governance file quick-check */}
    {repoFiles.operations && (
      <div style={{
        background: COLORS.surface2, border: `1px solid ${COLORS.border}`,
        borderRadius: 4, padding: "10px 16px", marginBottom: 16,
      }}>
        <div style={{ fontSize: 10, color: COLORS.teal, fontWeight: 700, marginBottom: 8, letterSpacing: "0.08em" }}>
          ◉ GOVERNANCE FILES IN operations/
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {GOVERNANCE_FILES.map(name => {
            const found = repoFiles.operations.find(f => f.name === name);
            return (
              <div key={name} style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "4px 10px",
                background: found ? `${COLORS.green}15` : `${COLORS.red}15`,
                border: `1px solid ${found ? COLORS.green : COLORS.red}44`,
                borderRadius: 3,
              }}>
                <span style={{ color: found ? COLORS.green : COLORS.red, fontSize: 11 }}>
                  {found ? "✓" : "✗"}
                </span>
                <span style={{ fontSize: 11, color: found ? COLORS.text2 : COLORS.text3 }}>{name}</span>
                {found && (
                  <span style={{ fontSize: 9, color: COLORS.text3 }}>
                    {(found.size / 1000).toFixed(1)}k
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    )}

    {/* Loading */}
    {loadingRepos && (
      <div style={{ textAlign: "center", padding: 40, color: COLORS.text3, fontSize: 12 }}>
        <div style={{ fontSize: 24, marginBottom: 12, animation: "spin 1s linear infinite" }}>⟳</div>
        fetching humanaios-ui repos…
      </div>
    )}

    {/* Repo list */}
    {!loadingRepos && filteredRepos.length === 0 && (
      <div style={{ textAlign: "center", padding: 40, color: COLORS.text3 }}>
        {repos.length === 0 ? "no repos loaded — click REFRESH" : "no repos match filter"}
      </div>
    )}

    {filteredRepos.map(repo => (
      <RepoPanel
        key={repo.name}
        repo={repo}
        files={repoFiles[repo.name]}
        loading={loadingFiles[repo.name]}
        error={errors[repo.name]}
        expanded={!!expanded[repo.name]}
        onToggle={() => toggleExpand(repo.name)}
      />
    ))}

    {/* Footer */}
    <div style={{
      marginTop: 32, borderTop: `1px solid ${COLORS.border}`,
      paddingTop: 16, fontSize: 10, color: COLORS.text3,
      display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8
    }}>
      <span>HAIOS GITHUB INSPECTOR · humanaios-ui · unauthenticated = 60 req/hr</span>
      <span style={{ color: COLORS.teal }}>
        canonical: {CANONICAL_REPOS.join(", ")}
      </span>
    </div>
  </div>

  <style>{`
    @keyframes spin { to { transform: rotate(360deg); } }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: ${COLORS.bg}; }
    ::-webkit-scrollbar-thumb { background: ${COLORS.border2}; border-radius: 2px; }
  `}</style>
</div>
```

);
}
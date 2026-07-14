import React, { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceDot, ResponsiveContainer } from "recharts";
import { AlertTriangle, Check, CircleDot, GitCommit, ShieldCheck, ShieldAlert, ShieldQuestion } from "lucide-react";

// ---------------------------------------------------------------------------
// MOCK DATA — Track 1 (§4.1) has not executed against the live repo yet.
// Shapes match compare_to_previous() / aggregate_scores() output exactly,
// but every number below is illustrative, not extracted from real commits.
// ---------------------------------------------------------------------------
const FILES = {
  "GOVERNANCE.md": [
    { sha: "a1f2c90", seq: 1, msg: "initial governance ladder, P1-P12", li: 0.71, evidential: "INFERENCE", flag: null },
    { sha: "b7e441d", seq: 2, msg: "add drift-signal taxonomy section", li: 0.76, evidential: "INFERENCE", flag: null },
    { sha: "c02af88", seq: 3, msg: "ratify P16 market-harmonic principle", li: 0.83, evidential: "JUDGMENT", flag: null },
    { sha: "d99b013", seq: 4, msg: "fix stale P32 reference (self-caught)", li: 0.97, evidential: "INFERENCE", flag: "DELTA_UNEXPLAINED_MOVE" },
    { sha: "e44c2f1", seq: 5, msg: "GOVARCH-01/02 pointer restructure", li: 0.94, evidential: "VERIFIED", flag: null },
    { sha: "f0091ab", seq: 6, msg: "v6.4.3 — WGS/HAIOSCC precedence clause", li: 0.96, evidential: "VERIFIED", flag: null },
  ],
  "BEHAVIORAL_GRAMMAR_V1.md": [
    { sha: "1a0f3e2", seq: 1, msg: "draft grammar G-0 through G-4", li: 0.62, evidential: "INFERENCE", flag: null },
    { sha: "2bd881c", seq: 2, msg: "add G-7 pair-inherits-lower-tier rule", li: 0.79, evidential: "JUDGMENT", flag: null },
    { sha: "3fe0091", seq: 3, msg: "P32 proposal text added (unratified)", li: 0.88, evidential: "JUDGMENT", flag: null },
    { sha: "4c7d220", seq: 4, msg: "evidential taxonomy correction, §2.1", li: 0.68, evidential: "REPORTED", flag: "DELTA_UNEXPLAINED_MOVE" },
    { sha: "58a11ff", seq: 5, msg: "close self-promotion gap, agent_of_authority", li: 0.90, evidential: "VERIFIED", flag: null },
  ],
};

const TIER_ORDER = ["UNKNOWN", "REPORTED", "INFERENCE", "JUDGMENT", "VERIFIED"];
const TIER_COLOR = {
  UNKNOWN: "#5A5F66",
  REPORTED: "#B4573F",
  INFERENCE: "#6B84A8",
  JUDGMENT: "#C99A3D",
  VERIFIED: "#5B9B7F",
};

const VERIFY_STATES = {
  unverified: { label: "unverified", icon: ShieldQuestion, color: "#8A8F98", desc: "No human has reviewed this output yet." },
  verified_passive: { label: "verified — passive", icon: ShieldAlert, color: "#C99A3D", desc: "Confirmed with no justification or correction. Does not raise the evidential tier — mirrors accepted_anchor, per §5.2." },
  verified_substantive: { label: "verified — substantive", icon: ShieldCheck, color: "#5B9B7F", desc: "Confirmed with a specific justification or a typed correction. Eligible to advance corpus_eligible past pending_Z2, per §5.2." },
};

function EvidentialLadder() {
  return (
    <div style={{ display: "flex", gap: 2, alignItems: "center" }}>
      {TIER_ORDER.map((t) => (
        <div key={t} style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: TIER_COLOR[t] }} />
          <span style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 11, color: "#B8BCC4", letterSpacing: 0.2 }}>{t}</span>
          {t !== "VERIFIED" && <span style={{ color: "#3A3F47", margin: "0 2px" }}>→</span>}
        </div>
      ))}
    </div>
  );
}

export default function CalibrationTraceViewer() {
  const [activeFile, setActiveFile] = useState("GOVERNANCE.md");
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [verifyState, setVerifyState] = useState({});

  const data = FILES[activeFile];
  const selected = selectedIdx !== null ? data[selectedIdx] : null;
  const flaggedPoints = useMemo(() => data.filter((d) => d.flag), [data]);

  const vKey = (file, sha) => `${file}::${sha}`;
  const currentVerify = selected ? verifyState[vKey(activeFile, selected.sha)] || "unverified" : "unverified";

  const cycleVerify = (nextState) => {
    if (!selected) return;
    setVerifyState((prev) => ({ ...prev, [vKey(activeFile, selected.sha)]: nextState }));
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#111417",
      color: "#EDEAE3",
      fontFamily: "ui-sans-serif, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif",
      padding: "28px 20px 60px",
    }}>
      <div style={{ maxWidth: 880, margin: "0 auto" }}>

        {/* Prototype banner — D-OVERCLAIM guard, not decorative */}
        <div style={{
          background: "#241C14",
          border: "1px solid #4A3A22",
          borderRadius: 4,
          padding: "8px 14px",
          fontSize: 12.5,
          color: "#D9B77E",
          marginBottom: 22,
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          display: "flex",
          gap: 8,
          alignItems: "center",
        }}>
          <AlertTriangle size={14} strokeWidth={2} />
          PROTOTYPE — illustrative data. Track 1 (§4.1) has not executed against the live repo. Shapes match compare_to_previous() output exactly; values do not.
        </div>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 4 }}>
          <div>
            <div style={{ fontSize: 11, letterSpacing: 1.5, color: "#7A7F87", textTransform: "uppercase", marginBottom: 6 }}>
              Repository as Recursive Learning Environment — §1 / §5
            </div>
            <h1 style={{ margin: 0, fontSize: 26, fontWeight: 600, letterSpacing: -0.3 }}>Calibration Trace Viewer</h1>
          </div>
          <EvidentialLadder />
        </div>
        <p style={{ color: "#9AA0A8", fontSize: 13.5, lineHeight: 1.5, marginTop: 10, marginBottom: 26, maxWidth: 620 }}>
          LI trajectory per commit, self-administered. Click a point to inspect the dimension delta and apply a
          verification tag — the passive/substantive split from §5.2 determines whether a tag can advance
          <code style={{ background: "#1C2024", padding: "1px 5px", borderRadius: 3, marginLeft: 4, fontSize: 12.5 }}>corpus_eligible</code>.
        </p>

        {/* File selector */}
        <div style={{ display: "flex", gap: 8, marginBottom: 18 }}>
          {Object.keys(FILES).map((f) => (
            <button
              key={f}
              onClick={() => { setActiveFile(f); setSelectedIdx(null); }}
              style={{
                background: activeFile === f ? "#1F2937" : "transparent",
                border: `1px solid ${activeFile === f ? "#3A4756" : "#2A2E33"}`,
                color: activeFile === f ? "#EDEAE3" : "#7A7F87",
                borderRadius: 5,
                padding: "6px 12px",
                fontSize: 12.5,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                cursor: "pointer",
              }}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Chart */}
        <div style={{ background: "#161A1E", border: "1px solid #23272C", borderRadius: 8, padding: "18px 8px 6px" }}>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={data} margin={{ top: 10, right: 24, left: -10, bottom: 0 }}
              onClick={(e) => { if (e && e.activeTooltipIndex !== undefined) setSelectedIdx(e.activeTooltipIndex); }}>
              <CartesianGrid stroke="#23272C" vertical={false} />
              <XAxis dataKey="seq" tick={{ fill: "#7A7F87", fontSize: 11 }} axisLine={{ stroke: "#2A2E33" }} tickLine={false}
                label={{ value: "commit sequence →", position: "insideBottom", offset: -2, fill: "#5A5F66", fontSize: 11 }} />
              <YAxis domain={[0.4, 1.05]} tick={{ fill: "#7A7F87", fontSize: 11 }} axisLine={false} tickLine={false} width={38} />
              <Tooltip
                contentStyle={{ background: "#1C2024", border: "1px solid #2E333A", borderRadius: 6, fontSize: 12 }}
                labelFormatter={() => ""}
                formatter={(v, n, p) => [`LI ${v.toFixed(4)}`, p.payload.sha]}
              />
              <Line type="monotone" dataKey="li" stroke="#5B9B7F" strokeWidth={2}
                dot={(props) => {
                  const { cx, cy, payload, index } = props;
                  const isSel = index === selectedIdx;
                  return (
                    <circle key={`dot-${index}`} cx={cx} cy={cy} r={isSel ? 6 : 4}
                      fill={TIER_COLOR[payload.evidential]} stroke={isSel ? "#EDEAE3" : "none"} strokeWidth={2} />
                  );
                }}
                activeDot={{ r: 7, stroke: "#EDEAE3", strokeWidth: 2 }}
              />
              {flaggedPoints.map((p) => (
                <ReferenceDot key={p.sha} x={p.seq} y={p.li} r={11} fill="none" stroke="#B4573F" strokeWidth={1.5} strokeDasharray="2 2" />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {flaggedPoints.length > 0 && (
          <div style={{ display: "flex", gap: 6, alignItems: "center", marginTop: 10, fontSize: 12, color: "#C4816F" }}>
            <CircleDot size={13} /> {flaggedPoints.length} commit{flaggedPoints.length > 1 ? "s" : ""} flagged DELTA_UNEXPLAINED_MOVE in this file
          </div>
        )}

        {/* Detail panel */}
        <div style={{ marginTop: 24, minHeight: 190 }}>
          {!selected ? (
            <div style={{ color: "#5A5F66", fontSize: 13, fontStyle: "italic", padding: "20px 4px" }}>
              Click a point on the trace to inspect the commit and apply a verification tag.
            </div>
          ) : (
            <div style={{ background: "#161A1E", border: "1px solid #23272C", borderRadius: 8, padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <GitCommit size={15} color="#7A7F87" />
                    <span style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 13, color: "#EDEAE3" }}>{selected.sha}</span>
                    <span style={{
                      fontSize: 10.5, padding: "2px 7px", borderRadius: 10, background: `${TIER_COLOR[selected.evidential]}22`,
                      color: TIER_COLOR[selected.evidential], fontFamily: "ui-monospace, monospace",
                    }}>{selected.evidential}</span>
                  </div>
                  <div style={{ fontSize: 14, color: "#C7CBD1" }}>{selected.msg}</div>
                  <div style={{ fontSize: 12, color: "#7A7F87", marginTop: 6 }}>
                    LI {selected.li.toFixed(4)}
                    {selected.flag && <span style={{ color: "#C4816F", marginLeft: 10 }}>⚠ {selected.flag}</span>}
                  </div>
                </div>
              </div>

              {/* Verification tag controls */}
              <div style={{ marginTop: 18, paddingTop: 16, borderTop: "1px solid #23272C" }}>
                <div style={{ fontSize: 11, letterSpacing: 1, color: "#7A7F87", textTransform: "uppercase", marginBottom: 10 }}>
                  Verification tag (§5.1)
                </div>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                  {Object.entries(VERIFY_STATES).map(([key, v]) => {
                    const Icon = v.icon;
                    const active = currentVerify === key;
                    return (
                      <button key={key} onClick={() => cycleVerify(key)}
                        style={{
                          display: "flex", alignItems: "center", gap: 6,
                          background: active ? `${v.color}1F` : "transparent",
                          border: `1px solid ${active ? v.color : "#2A2E33"}`,
                          color: active ? v.color : "#7A7F87",
                          borderRadius: 5, padding: "6px 11px", fontSize: 12, cursor: "pointer",
                        }}>
                        <Icon size={13} /> {v.label}
                      </button>
                    );
                  })}
                </div>
                <div style={{ fontSize: 12, color: "#8A8F98", lineHeight: 1.5, marginBottom: 10 }}>
                  {VERIFY_STATES[currentVerify].desc}
                </div>
                <div style={{
                  display: "flex", alignItems: "center", gap: 8, fontSize: 12,
                  padding: "8px 12px", borderRadius: 5,
                  background: currentVerify === "verified_substantive" ? "#132018" : "#1C1815",
                  border: `1px solid ${currentVerify === "verified_substantive" ? "#2E4A38" : "#2E2620"}`,
                }}>
                  {currentVerify === "verified_substantive" ? (
                    <><Check size={13} color="#5B9B7F" /> <span style={{ color: "#8FBFA5" }}>corpus_eligible may advance past pending_Z2</span></>
                  ) : (
                    <><ShieldQuestion size={13} color="#B58A5E" /> <span style={{ color: "#C9A97D" }}>corpus_eligible remains pending_Z2 — automated advancement halted (§5.3)</span></>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

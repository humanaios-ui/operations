// HAIOS-VIDEO-E0 #1329 | offline evidence-bearing video adapter (goal 4). PROPOSED | AUTHORITY_EFFECT NONE.
// Input: an episode manifest (JSON). Output: captions (WebVTT), accessible transcript HTML with VideoObject JSON-LD,
// a source/claim manifest and correction history, written to a local directory. It never publishes, uploads,
// connects accounts or calls the network. Release state is always HOLD until a human decision is recorded elsewhere.
// Run: node adapter.mjs episode_01_manifest.json <out-dir>
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { createHash } from "node:crypto";
import { pathToFileURL } from "node:url";

export const STATUSES = Object.freeze(["observed", "source-reported", "hypothesis", "unknown"]);
const BANNED = [/\bproven\b/i, /\bnovel\b/i, /\bfirst[- ]ever\b/i, /\bguarantee/i, /\bcertified\b/i, /\bI am (a )?human\b/i, /\bas a human\b/i, /\breal person\b/i, /\bACAT[- ]qualified\b/i];
const sha = s => createHash("sha256").update(s).digest("hex");
const getPath = (obj, path) => path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), obj);
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const ts = sec => { const h = String(Math.floor(sec / 3600)).padStart(2, "0"), m = String(Math.floor(sec / 60) % 60).padStart(2, "0"), s = String(sec % 60).padStart(2, "0"); return `${h}:${m}:${s}.000`; };

// Returns a list of problems; empty list means the manifest is internally consistent. It is NOT release approval.
export function validate(manifest, baseDir) {
  const problems = [];
  if (manifest.authorityEffect !== "NONE") problems.push("authorityEffect must be NONE");
  if (manifest.release?.state !== "HOLD") problems.push("release.state must be HOLD in E0");
  if (manifest.release?.autoPublish !== false) problems.push("release.autoPublish must be false");
  if (!manifest.disclosure || !/synthetic/i.test(manifest.disclosure)) problems.push("missing synthetic-test disclosure");
  const ids = new Set();
  for (const c of manifest.claims ?? []) {
    if (ids.has(c.id)) problems.push(`${c.id}: duplicate claim id`); ids.add(c.id);
    if (!STATUSES.includes(c.status)) problems.push(`${c.id}: status must be one of ${STATUSES.join("/")}`);
    if (!c.limitations) problems.push(`${c.id}: limitations required`);
    if (c.humanDecision !== "HOLD") problems.push(`${c.id}: humanDecision must be HOLD in E0 (no self-authorization)`);
    for (const re of BANNED) if (re.test(c.text)) problems.push(`${c.id}: banned wording ${re}`);
    if (c.status === "observed") {
      if (!c.evidence?.file || !c.evidence?.pointers?.length) { problems.push(`${c.id}: observed claim needs evidence.file and pointers`); continue; }
      const file = resolve(baseDir, c.evidence.file);
      if (!file.startsWith(resolve(baseDir))) { problems.push(`${c.id}: evidence path escapes the experiment directory`); continue; }
      let data; try { data = JSON.parse(readFileSync(file, "utf8")); } catch { problems.push(`${c.id}: evidence file unreadable`); continue; }
      for (const p of c.evidence.pointers) {
        const v = getPath(data, p.path);
        if (v === undefined) problems.push(`${c.id}: pointer ${p.path} not found`);
        else if (JSON.stringify(v) !== JSON.stringify(p.value)) problems.push(`${c.id}: pointer ${p.path} is ${JSON.stringify(v)}, manifest says ${JSON.stringify(p.value)}`);
        if (p.value !== undefined && !c.text.includes(String(p.value))) problems.push(`${c.id}: value ${p.value} at ${p.path} not stated in claim text`);
      }
    } else if (c.status === "source-reported" && !c.source?.url) problems.push(`${c.id}: source-reported claim needs source.url`);
  }
  for (const seg of manifest.segments ?? []) {
    for (const id of seg.claimIds ?? []) if (!ids.has(id)) problems.push(`segment ${seg.start}: unknown claim ${id}`);
    for (const re of BANNED) if (re.test(seg.narration)) problems.push(`segment ${seg.start}: banned wording ${re}`);
  }
  return problems;
}

export function renderArtifacts(manifest) {
  const segs = manifest.segments;
  const vtt = ["WEBVTT", ""].concat(segs.flatMap((s, i) => [String(i + 1), `${ts(s.start)} --> ${ts(s.end)}`, s.narration + (s.claimIds?.length ? ` [${s.claimIds.join(", ")}]` : ""), ""])).join("\n");
  const videoObject = { "@context": "https://schema.org", "@type": "VideoObject", name: manifest.title, description: manifest.disclosure, transcript: segs.map(s => s.narration).join(" "), uploadDate: null, contentUrl: null, embedUrl: null, isBasedOn: manifest.evidenceRepoPath, creativeWorkStatus: "Draft — HOLD, not published" };
  const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(manifest.title)} — transcript (draft, not published)</title>\n<script type="application/ld+json">${JSON.stringify(videoObject).replace(/</g, "\\u003c")}</script></head><body>\n<h1>${esc(manifest.title)}</h1><p><strong>${esc(manifest.disclosure)}</strong></p>\n<ol>${segs.map(s => `<li><time>${ts(s.start)}</time> ${esc(s.narration)}${s.claimIds?.length ? ` <small>(claims: ${s.claimIds.map(esc).join(", ")})</small>` : ""}</li>`).join("\n")}</ol>\n<h2>Claims and evidence</h2><ul>${manifest.claims.map(c => `<li id="${esc(c.id)}"><strong>${esc(c.id)}</strong> [${esc(c.status)}] ${esc(c.text)} — <em>Limits:</em> ${esc(c.limitations)}</li>`).join("\n")}</ul>\n<h2>Corrections</h2><ul>${(manifest.corrections ?? []).map(x => `<li>${esc(x.date)}: ${esc(x.note)}</li>`).join("") || "<li>None yet.</li>"}</ul></body></html>\n`;
  const claimManifest = { title: manifest.title, release: manifest.release, authorityEffect: "NONE", claims: manifest.claims.map(({ id, status, text, limitations, humanDecision, evidence, source }) => ({ id, status, text, limitations, humanDecision, evidence, source })), corrections: manifest.corrections ?? [] };
  return { "captions.vtt": vtt, "transcript.html": html, "claim_manifest.json": JSON.stringify(claimManifest, null, 2) + "\n", "correction_history.json": JSON.stringify(manifest.corrections ?? [], null, 2) + "\n" };
}

export function build(manifestPath, outDir) {
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const problems = validate(manifest, dirname(resolve(manifestPath)));
  if (problems.length) return { ok: false, problems };
  const files = renderArtifacts(manifest);
  const digests = Object.fromEntries(Object.entries(files).map(([k, v]) => [k, sha(v)]));
  if (outDir) { mkdirSync(outDir, { recursive: true }); for (const [k, v] of Object.entries(files)) writeFileSync(join(outDir, k), v); }
  return { ok: true, release: "HOLD (no publishing in E0)", digests };
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  const [m, out] = process.argv.slice(2);
  if (!m) { console.error("usage: node adapter.mjs <manifest.json> [out-dir]"); process.exit(2); }
  const r = build(m, out); console.log(JSON.stringify(r, null, 2)); process.exit(r.ok ? 0 : 1);
}

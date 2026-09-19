#!/usr/bin/env node
// skill_compression_scanner_v1_0.js
// Scans tools/skills/ SKILL.md files and produces a compression audit report.
// Run locally against a clone of humanaios-ui/operations.
//
// Built: S-061426-02 · Zone 1 · Night ratified
// Governance: produces DRAFT audit report only — no files modified.
//             Z2 review required before any PR touching SKILL.md files.
//             Output is a Z1 artifact for Night's review.
//
// Usage:
//   node skill_compression_scanner_v1_0.js [--repo-path /path/to/operations] [--level lite|full] [--dry-run]
//
// Default repo path: ~/Desktop/HAIOS-Main/operations-staging
// Default level: lite
// --dry-run: print stats only, do not write compressed output files

const fs   = require('fs');
const path = require('path');
const { compress, audit } = require('./haios_compressor_v1_0');

// ─────────────────────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────────────────────
const DEFAULT_REPO   = path.join(process.env.HOME, 'Desktop', 'HAIOS-Main', 'operations-staging');
const SKILLS_SUBDIR  = path.join('tools', 'skills');
const SKILL_FILENAME = 'SKILL.md';
const REPORT_PATH    = path.join(process.env.HOME, 'Desktop', 'HAIOS-Main',
                                 `skill_compression_audit_${datestamp()}.md`);

// Sections within SKILL.md that are safe to compress
// (not the yaml frontmatter, not the Usage Example code blocks — those are preserved by haios_compressor)
const COMPRESSIBLE_SECTIONS = [
  'description',  // frontmatter description field (long-form)
  'Purpose',
  'Overview',
  'Background',
  'Notes',
  'Limitations',
];

// Threshold: only flag files where compression yields > MIN_REDUCTION reduction
const MIN_REDUCTION_PCT = 3.0;

// ─────────────────────────────────────────────────────────────
// HELPERS
// ─────────────────────────────────────────────────────────────
function datestamp() {
  const d = new Date();
  return `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}`;
}

function parseArgs() {
  const args = process.argv.slice(2);
  const cfg = {
    repoPath: DEFAULT_REPO,
    level: 'lite',
    dryRun: false,
  };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--repo-path' && args[i+1]) cfg.repoPath = args[++i];
    if (args[i] === '--level' && args[i+1])     cfg.level    = args[++i];
    if (args[i] === '--dry-run')                 cfg.dryRun   = true;
  }
  return cfg;
}

function findSkillFiles(skillsDir) {
  if (!fs.existsSync(skillsDir)) {
    throw new Error(`skills directory not found: ${skillsDir}\nRun from a clone of humanaios-ui/operations.`);
  }
  const results = [];
  const entries = fs.readdirSync(skillsDir, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isDirectory()) {
      const candidate = path.join(skillsDir, entry.name, SKILL_FILENAME);
      if (fs.existsSync(candidate)) results.push(candidate);
    }
  }
  return results.sort();
}

function pct(str) {
  const n = parseFloat(str);
  return isNaN(n) ? 0 : n;
}

// ─────────────────────────────────────────────────────────────
// MAIN SCAN
// ─────────────────────────────────────────────────────────────
function scanSkillFiles(cfg) {
  const skillsDir  = path.join(cfg.repoPath, SKILLS_SUBDIR);
  const skillFiles = findSkillFiles(skillsDir);

  console.log(`\nHAIOS SKILL.md Compression Scanner v1.0`);
  console.log(`Repo:   ${cfg.repoPath}`);
  console.log(`Level:  ${cfg.level}`);
  console.log(`Mode:   ${cfg.dryRun ? 'dry-run (no files written)' : 'audit only (no files written — Z2 required before PR)'}`);
  console.log(`Files:  ${skillFiles.length} SKILL.md found\n`);

  const results = [];
  let totalCharsIn = 0;
  let totalCharsOut = 0;
  let flaggedCount = 0;

  for (const filePath of skillFiles) {
    const raw = fs.readFileSync(filePath, 'utf8');
    const stats = audit(raw, cfg.level);

    totalCharsIn  += stats.charsIn;
    totalCharsOut += stats.charsOut;

    const reductionPct = pct(stats.reduction);
    const flagged = reductionPct >= MIN_REDUCTION_PCT;
    if (flagged) flaggedCount++;

    const skillName = path.basename(path.dirname(filePath));
    results.push({
      skillName,
      filePath,
      stats,
      reductionPct,
      flagged,
      charDelta: stats.charsIn - stats.charsOut,
    });

    const marker = flagged ? '⚑' : '·';
    console.log(`${marker} ${skillName.padEnd(55)} ${stats.reduction.padStart(6)} reduction  (${stats.preservedRegions} regions preserved)`);
  }

  // Summary
  const totalReduction = totalCharsIn > 0
    ? (((totalCharsIn - totalCharsOut) / totalCharsIn) * 100).toFixed(1) + '%'
    : '0%';

  console.log(`\n${'─'.repeat(72)}`);
  console.log(`Total:  ${skillFiles.length} files · ${totalCharsIn.toLocaleString()} chars in · ${totalCharsOut.toLocaleString()} chars out`);
  console.log(`Corpus reduction at ${cfg.level} level: ${totalReduction}`);
  console.log(`Files flagged (≥${MIN_REDUCTION_PCT}% reduction available): ${flaggedCount} / ${skillFiles.length}`);
  console.log(`\nGOVERNANCE NOTE: This is a Z1 audit report.`);
  console.log(`Z2 review required before any compressed SKILL.md reaches a PR.`);
  console.log(`Each flagged file must be manually reviewed — haios_compressor`);
  console.log(`protects canonical regions but cannot guarantee prose integrity.`);

  // Write markdown report
  writeReport(cfg, skillFiles.length, results, totalReduction, flaggedCount);
}

function writeReport(cfg, total, results, totalReduction, flaggedCount) {
  const flagged = results.filter(r => r.flagged).sort((a,b) => b.reductionPct - a.reductionPct);
  const clean   = results.filter(r => !r.flagged);

  const lines = [
    `# SKILL.md Compression Audit Report`,
    ``,
    `**Generated:** ${new Date().toISOString()}`,
    `**Session:** S-061426-02`,
    `**Level:** ${cfg.level}`,
    `**Repo:** ${cfg.repoPath}`,
    `**Files scanned:** ${total}`,
    `**Corpus reduction available:** ${totalReduction}`,
    `**Files flagged (≥${MIN_REDUCTION_PCT}%):** ${flaggedCount}`,
    ``,
    `## Governance`,
    ``,
    `This is a Zone 1 audit artifact. No SKILL.md files have been modified.`,
    `Z2 Night ratification required before any compressed version reaches a PR.`,
    `Each flagged file must be manually reviewed after haios_compressor runs.`,
    `Preserve patterns protect ACAT tags, SQL, URLs, registry IDs, and code blocks,`,
    `but cannot guarantee prose integrity in all edge cases.`,
    ``,
    `## Flagged Files (≥${MIN_REDUCTION_PCT}% reduction available)`,
    ``,
    `| Skill | Reduction | Chars saved | Preserved regions |`,
    `|-------|-----------|-------------|-------------------|`,
    ...flagged.map(r =>
      `| \`${r.skillName}\` | ${r.stats.reduction} | ${r.charDelta.toLocaleString()} | ${r.stats.preservedRegions} |`
    ),
    ``,
    `## Clean Files (<${MIN_REDUCTION_PCT}% — low priority)`,
    ``,
    clean.length > 0
      ? clean.map(r => `- \`${r.skillName}\` — ${r.stats.reduction}`).join('\n')
      : '_None_',
    ``,
    `## Next Steps (Z3 — Night approves before any action)`,
    ``,
    `1. Review flagged files above — highest reduction first`,
    `2. For each flagged file: run \`haios_compressor_v1_0.js compress [file] [level]\``,
    `3. Manually review compressed output — confirm no canonical content altered`,
    `4. Stage changes in a branch: \`feat/skill-compression-pass-S061426\``,
    `5. Open PR → Z2 Night review before merge`,
    ``,
    `## H-ELICIT-01 Note`,
    ``,
    `SKILL.md files that serve as elicitation context for substrate ACAT runs`,
    `(humanaios-phase1-wrapper, humanaios-realtime-drift) should NOT be compressed`,
    `until H-ELICIT-01 is promoted. Compression of elicitation context is the`,
    `independent variable in the H-ELICIT-01 mechanism test. Applying it`,
    `operationally before the mechanism is understood conflates operational`,
    `efficiency with a research confound.`,
    ``,
    `Flagged elicitation-adjacent files (requires manual check):`,
    flagged
      .filter(r => ['humanaios-phase1-wrapper', 'humanaios-realtime-drift'].includes(r.skillName))
      .map(r => `- \`${r.skillName}\` — hold pending H-ELICIT-01 design`)
      .join('\n') || '_None flagged — no elicitation-adjacent files exceeded threshold_',
    ``,
    `---`,
    `_HAIOS Skill Compression Scanner v1.0 · S-061426-02 · Zone 1_`,
  ];

  const reportContent = lines.join('\n');

  // In dry-run mode, print to stdout instead of writing
  console.log(`\n${'─'.repeat(72)}`);
  console.log(`REPORT (would write to: ${REPORT_PATH})`);
  console.log(`${'─'.repeat(72)}\n`);
  console.log(reportContent);

  // Uncomment to write report file:
  // fs.writeFileSync(REPORT_PATH, reportContent, 'utf8');
  // console.log(`\nReport written: ${REPORT_PATH}`);
}

// ─────────────────────────────────────────────────────────────
// ENTRY POINT
// ─────────────────────────────────────────────────────────────
try {
  const cfg = parseArgs();
  scanSkillFiles(cfg);
} catch (err) {
  console.error(`\nERROR: ${err.message}`);
  console.error(`\nUsage: node skill_compression_scanner_v1_0.js [--repo-path PATH] [--level lite|full] [--dry-run]`);
  process.exit(1);
}

// wgs_draft_compressor_v1_0.js
// WGS Draft Lite-Pass Utility
// Applies haios_compressor (lite level) to a WGS close note draft
// BEFORE it reaches Night’s review step.
//
// Built: S-061426-02 · Zone 1 · Night ratified
// Governance constraints (hard):
//   1. ONLY runs on Z1 draft text — never on ratified or posted WGS content
//   2. lite level ONLY — full/ultra not permitted on WGS drafts
//   3. Output is presented to Night for review — never auto-posted
//   4. If haios_compressor preservedRegions === 0, halt and warn
//      (suggests preserve patterns may have failed — manual review required)
//
// Usage (in-session, Zone 1):
//   const { compressWgsDraft } = require(’./wgs_draft_compressor_v1_0’);
//   const result = compressWgsDraft(draftText);
//   // result.output → present to Night for review
//   // result.stats  → log in session B.0
//   // result.warnings → surface any governance flags

const { compress } = require(’./haios_compressor_v1_0’);

// ─────────────────────────────────────────────────────────────
// WGS STRUCTURE GUARD
// Verify the draft contains expected WGS structural markers
// before compression. A draft missing these is not a WGS close note
// and should not be processed by this utility.
// ─────────────────────────────────────────────────────────────
const WGS_REQUIRED_MARKERS = [
/WGS/,                          // session log header
/Z[123]/,                       // zone reference
/S-\d{6}-\d{2}/,               // session ID
/Charter Day/,                  // charter day reference
/DATASET STATE/,                // corpus state block
/F-H1/,                         // Humility status line
];

const WGS_CANONICAL_SECTIONS = [
// These section headers must survive compression unchanged
‘Z2 RATIFICATIONS’,
‘B.0 EMPIRICAL VERIFICATION BLOCK’,
‘CORE RESEARCH OUTPUT’,
‘Z1 ARTIFACT’,
‘ZONE 3 QUEUE’,
‘SILENT FAILURES’,
‘DATASET STATE’,
‘REFLECTION BLOCK’,
];

// ─────────────────────────────────────────────────────────────
// PROSE ZONES vs PROTECTED ZONES
// WGS posts have two kinds of content:
//   - Prose narrative (compressible): explanatory text between bullet points,
//     rationale sentences, transition phrases
//   - Structured data (protected by haios_compressor): session IDs, registry
//     IDs, corpus numbers, SQL, URLs, commit messages, section headers
//
// Lite-pass targets the prose narrative only.
// ─────────────────────────────────────────────────────────────

function detectWgsStructure(text) {
const missing = WGS_REQUIRED_MARKERS.filter(marker => !marker.test(text));
return {
isWgsDraft: missing.length === 0,
missingMarkers: missing.map(m => m.toString()),
};
}

function checkSectionIntegrity(original, compressed) {
const damaged = WGS_CANONICAL_SECTIONS.filter(section => {
const inOriginal   = original.includes(section);
const inCompressed = compressed.includes(section);
return inOriginal && !inCompressed;
});
return damaged;
}

// ─────────────────────────────────────────────────────────────
// MAIN FUNCTION
// ─────────────────────────────────────────────────────────────

/**

- compressWgsDraft(draftText)
- 
- @param {string} draftText - Z1 WGS close note draft (not yet posted/ratified)
- @returns {{
- output: string,         // compressed draft — present to Night for review
- stats: object,          // compression stats from haios_compressor
- warnings: string[],     // governance flags (surface in session B.0)
- safe: boolean,          // false if any warning requires manual intervention
- }}
  */
  function compressWgsDraft(draftText) {
  const warnings = [];
  let safe = true;

// Guard 1: verify this is a WGS draft
const { isWgsDraft, missingMarkers } = detectWgsStructure(draftText);
if (!isWgsDraft) {
return {
output: draftText,
stats: null,
warnings: [
`HALTED: Input does not appear to be a WGS close note draft.`,
`Missing structural markers: ${missingMarkers.join(', ')}`,
`wgs_draft_compressor only processes WGS close note drafts.`,
`For other documents, use haios_compressor_v1_0 directly.`,
],
safe: false,
};
}

// Guard 2: apply lite-level compression only
const { output, stats } = compress(draftText, ‘lite’);

// Guard 3: verify preserve patterns actually fired
if (stats.preservedRegions === 0) {
warnings.push(
`WARNING: haios_compressor found 0 preserved regions in this draft.`,
`This suggests either: (a) the draft has no canonical content to protect, ` +
`or (b) preserve patterns failed to match. Manual review required before sending.`
);
safe = false;
}

// Guard 4: section header integrity check
const damagedSections = checkSectionIntegrity(draftText, output);
if (damagedSections.length > 0) {
warnings.push(
`WARNING: The following canonical WGS section headers were damaged by compression:`,
…damagedSections.map(s => `  · "${s}"`),
`This must be corrected manually before sending.`
);
safe = false;
}

// Guard 5: reduction sanity check
// If reduction > 20%, compression may be too aggressive for a WGS draft
const reductionPct = parseFloat(stats.reduction);
if (reductionPct > 20) {
warnings.push(
`NOTICE: Compression reduced draft by ${stats.reduction}. ` +
`This is higher than expected for a lite-level WGS pass. ` +
`Review output carefully — some meaningful content may have been removed.`
);
// Not safe=false — this is a notice, not a halt
}

// Guard 6: corpus state numbers must be present in output
const corpusPattern = /N_total=\d+/;
if (corpusPattern.test(draftText) && !corpusPattern.test(output)) {
warnings.push(
`CRITICAL: Corpus state numbers (N_total=) were present in draft but absent in output.`,
`Preserve patterns failed to protect canonical corpus claims.`,
`DO NOT SEND. Use original draft text.`
);
safe = false;
return { output: draftText, stats, warnings, safe };
}

return { output, stats, warnings, safe };
}

// ─────────────────────────────────────────────────────────────
// SESSION INTEGRATION HELPER
// Call this from the WGS draft step; returns a formatted block
// for inclusion in session B.0 Empirical Verification.
// ─────────────────────────────────────────────────────────────

/**

- formatB0Line(result)
- Returns a single B.0 verification line for this compression pass.
  */
  function formatB0Line(result) {
  if (!result.stats) {
  return `· WGS draft compression: HALTED — not a WGS draft (see warnings) ✗`;
  }
  const safeLabel = result.safe ? ‘✓’ : ‘⚠ REVIEW REQUIRED’;
  return [
  `· WGS draft lite-pass: ${result.stats.reduction} reduction · ` +
  `${result.stats.preservedRegions} regions preserved · ${safeLabel}`,
  …(result.warnings.length > 0
  ? result.warnings.map(w => `  ⚠ ${w}`)
  : []),
  ].join(’\n’);
  }

module.exports = { compressWgsDraft, formatB0Line };

// ─────────────────────────────────────────────────────────────
// USAGE — in-session Zone 1
// ─────────────────────────────────────────────────────────────
//
// const { compressWgsDraft, formatB0Line } = require(’./wgs_draft_compressor_v1_0’);
//
// // After producing Z1 WGS draft:
// const result = compressWgsDraft(myWgsDraftText);
//
// if (!result.safe) {
//   // Surface warnings to Night — use original draft
//   console.log(‘Compression not safe. Warnings:\n’, result.warnings.join(’\n’));
//   console.log(‘Using original draft.’);
//   nightReviews(myWgsDraftText);
// } else {
//   // Present compressed draft to Night for review
//   console.log(formatB0Line(result)); // log in B.0
//   nightReviews(result.output);       // Night reviews compressed version
// }
//
// Night sends via slack_send_message_draft — never auto-post.
//
// ─────────────────────────────────────────────────────────────
// GOVERNANCE CONSTRAINTS (summary)
// ─────────────────────────────────────────────────────────────
// ✓ lite level only
// ✓ draft only — never on posted/ratified WGS content
// ✓ Night reviews output before send
// ✓ safe=false halts or flags — human check required
// ✗ never auto-posts to #wgs-sync
// ✗ never modifies REGISTERED.md, GOVERNANCE.md, or any canonical file
// ✗ never runs at full or ultra level on WGS content
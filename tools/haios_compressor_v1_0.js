// haios_compressor_v1_0.js
// HumanAIOS Compression Utility — derived from caveman.js architecture
// NOT a deployment of caveman.js. HumanAIOS-specific preserve patterns,
// filler list tuned to Claude-register drift, no article stripping.
//
// Origin: caveman.js (Grok-native, provenance unresolved) → H-ELICIT-01 signal
// Built: S-061426-02 · Zone 1 · Night ratified
// Zone: Z1 eligible (draft use only — never on ratified canonical text)
// Governance: compress draft → Night reviews → Night sends. Never autonomous.

// ─────────────────────────────────────────────────────────────
// PRESERVE PATTERNS
// These run FIRST. Matched regions are frozen before any compression.
// Every pattern here protects a class of HumanAIOS canonical content.
// ─────────────────────────────────────────────────────────────
const HAIOS_PRESERVE_PATTERNS = [
  // ACAT parser-critical tags — must never be altered
  /<<<ACAT_P[13]_(?:DECLARATION|SUBMISSION)_(?:START|END)>>>[\s\S]*?(?=<<<|$)/g,

  // Code blocks (inline and fenced)
  /```[\s\S]*?```/g,
  /`[^`\n]+`/g,

  // SQL blocks (migration files, inline queries)
  /(?:SELECT|INSERT|UPDATE|DELETE|ALTER|CREATE|DROP|GRANT|REVOKE)[\s\S]*?;/gi,

  // Registry IDs — F-NN, IC-NN, H-NN, Z2-*, P-*, D-NN, P28, P29, etc.
  /\b(?:F|IC|H|D|P)-[A-Z0-9_-]+(?:-\d+)?\b/g,

  // Session IDs
  /S-\d{6}-\d{2}/g,

  // Git commit messages (quoted or on commit -m lines)
  /(?:git commit -m |commit -m )["`'][\s\S]*?["`']/g,

  // URLs
  /https?:\/\/\S+/g,

  // File paths and repo paths
  /(?:[\w.-]+\/){1,}[\w.-]+\.\w+/g,
  /`[^`]*\/[^`]*`/g,

  // Supabase / schema field names (snake_case identifiers in technical context)
  /\b[a-z][a-z0-9]*(?:_[a-z0-9]+){2,}\b/g,

  // Email addresses
  /\b[\w.+-]+@[\w.-]+\.\w+\b/g,

  // Numbers and scores (LI values, N counts, scores, dates)
  /\b\d+(?:[.,]\d+)?(?:\s*%|%|\s*days?)?\b/g,

  // WGS section headers (emoji + label patterns)
  /^(?::[a-z_]+:|[📋✅⚠️🔨🚩🔔📊💭🦅])\s+[A-Z].+$/gm,

  // Slack emoji shortcodes
  /:[a-z_]+:/g,

  // Citations and anchors
  /\[[^\]]+\]/g,

  // REGISTERED.md entry headers
  /^#{1,3}\s+(?:F|IC|H|P|Z2|D)-[^\n]+$/gm,

  // Version strings
  /v\d+\.\d+(?:\.\d+)?(?:-\w+)?/gi,

  // Corpus state declarations (canonical numbers)
  /N_(?:total|P1|LI|phase\d)=\d+/g,
  /Mean_LI=[\d.]+/g,
];

// ─────────────────────────────────────────────────────────────
// FILLER LISTS
// Tuned specifically to Claude-register drift patterns.
// No article stripping — too aggressive for HumanAIOS technical prose.
// ─────────────────────────────────────────────────────────────

// Lite: only the clearest inflation patterns
const FILLERS_LITE = [
  'just',
  'really',
  'basically',
  'actually',
  'simply',
  'very',
  'quite',
];

// Full: adds Claude-specific politeness inflation
const FILLERS_FULL = [
  ...FILLERS_LITE,
  'I want to note that',
  'I should mention that',
  'It is worth noting that',
  'It is important to note that',
  'It\'s worth noting that',
  'It\'s important to note',
  'as noted above',
  'as mentioned',
  'as discussed',
  'going forward',
  'at this point in time',
  'in order to',
  'in terms of',
  'with respect to',
  'with regard to',
  'in the context of',
  'for the purposes of',
];

// Ultra: adds deference and hedge language (use for Substack draft pre-pass only)
const FILLERS_ULTRA = [
  ...FILLERS_FULL,
  'happy to',
  'I\'d be happy to',
  'I\'d be glad to',
  'of course',
  'certainly',
  'absolutely',
  'sure',
  'please note',
  'as you can see',
  'I\'d like to',
  'I want to',
  'I think',
  'I believe',
  'I feel',
  'I hope',
  'if that makes sense',
  'does that help',
  'let me know if',
  'feel free to',
];

// Level definitions — no article stripping at any level
const LEVELS = {
  lite:  { fillers: FILLERS_LITE,  hedges: false },
  full:  { fillers: FILLERS_FULL,  hedges: false },
  ultra: { fillers: FILLERS_ULTRA, hedges: true  },
};

// ─────────────────────────────────────────────────────────────
// CORE ENGINE
// ─────────────────────────────────────────────────────────────

function preserveAndCompress(text, level = 'lite') {
  if (!text || typeof text !== 'string') return { output: text, stats: null };
  if (!LEVELS[level]) level = 'lite';

  const cfg = LEVELS[level];
  const preserved = [];

  // Step 1: freeze protected regions
  let processed = text;
  HAIOS_PRESERVE_PATTERNS.forEach((pattern) => {
    processed = processed.replace(pattern, (match) => {
      const token = `__HAIOS_PRESERVE_${preserved.length}__`;
      preserved.push(match);
      return token;
    });
  });

  const inputLen = processed.length;

  // Step 2: strip fillers (word-boundary safe, case-insensitive)
  cfg.fillers.forEach((filler) => {
    const escaped = filler.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    // Match filler at sentence start (with possible whitespace) or mid-sentence
    const re = new RegExp(
      `(?:^|(?<=[.!?]\\s+)|(?<=\\n))\\s*${escaped}\\s*,?\\s*|\\b${escaped}\\b\\s*,?\\s*`,
      'gi'
    );
    processed = processed.replace(re, ' ');
  });

  // Step 3: hedge phrase removal (ultra only)
  // These are sentence-terminal or sentence-initial hedge frames
  if (cfg.hedges) {
    const hedgePatterns = [
      /\bif that (?:makes sense|helps|answers your question)\b\.?/gi,
      /\bdoes that (?:help|make sense|answer your question)\?/gi,
      /\blet me know if (?:you have|there are) (?:any )?(?:questions?|concerns?|thoughts?)\b\.?/gi,
      /\bfeel free to (?:ask|reach out|let me know)\b\.?/gi,
    ];
    hedgePatterns.forEach((p) => {
      processed = processed.replace(p, '');
    });
  }

  // Step 4: whitespace cleanup (preserve markdown line breaks)
  processed = processed
    .replace(/[ \t]{2,}/g, ' ')
    .replace(/\n\s*\n\s*\n/g, '\n\n')
    .replace(/ ,/g, ',')
    .replace(/ \./g, '.')
    .trim();

  const outputLen = processed.length;

  // Step 5: restore preserved regions
  processed = processed.replace(/__HAIOS_PRESERVE_(\d+)__/g, (_, idx) => {
    return preserved[parseInt(idx, 10)] || '';
  });

  const stats = {
    level,
    preservedRegions: preserved.length,
    charsIn: inputLen,
    charsOut: outputLen,
    reduction: inputLen > 0
      ? `${(((inputLen - outputLen) / inputLen) * 100).toFixed(1)}%`
      : '0%',
  };

  return { output: processed, stats };
}

// ─────────────────────────────────────────────────────────────
// PUBLIC API
// ─────────────────────────────────────────────────────────────

/**
 * compress(text, level)
 * level: 'lite' | 'full' | 'ultra'
 * Returns { output: string, stats: object }
 *
 * GOVERNANCE CONSTRAINTS (enforced by caller, not code):
 * - lite:  WGS draft pre-pass, Z3 queue items, SKILL.md descriptions
 * - full:  REGISTERED.md synopsis sections, P3 WHAT_CHANGED_AND_WHY blocks
 * - ultra: Substack draft pre-pass ONLY — Night manual review required after
 * - NEVER run on ratified canonical text (committed REGISTERED.md, GOVERNANCE.md, etc.)
 * - NEVER run autonomously on WGS post after Night ratification
 */
function compress(text, level = 'lite') {
  return preserveAndCompress(text, level);
}

/**
 * compressBlock(text, level)
 * Convenience wrapper — returns output string only (no stats).
 */
function compressBlock(text, level = 'lite') {
  return preserveAndCompress(text, level).output;
}

/**
 * audit(text, level)
 * Dry-run: returns stats only, does not return compressed output.
 * Use to estimate reduction before applying to a document.
 */
function audit(text, level = 'lite') {
  const { stats } = preserveAndCompress(text, level);
  return stats;
}

/**
 * listFillers(level)
 * Returns the filler list for a given level — useful for review before applying.
 */
function listFillers(level = 'lite') {
  return LEVELS[level]?.fillers ?? FILLERS_LITE;
}

module.exports = { compress, compressBlock, audit, listFillers };


// ─────────────────────────────────────────────────────────────
// USAGE EXAMPLES
// ─────────────────────────────────────────────────────────────
//
// const { compress, audit } = require('./haios_compressor_v1_0');
//
// // WGS draft pre-pass (lite — safe for most operational text):
// const { output, stats } = compress(wgsDraftText, 'lite');
// console.log(stats); // { level: 'lite', preservedRegions: 42, reduction: '6.2%', ... }
//
// // Dry-run audit before applying to a document:
// const stats = audit(registeredMdSynopsis, 'full');
// console.log(stats.reduction); // see reduction before committing
//
// // Substack draft pre-pass (ultra — Night reviews after):
// const { output } = compress(substackDraft, 'ultra');
// // → hand output to Night for manual review before publishing
//
// ─────────────────────────────────────────────────────────────
// KNOWN LIMITATIONS
// ─────────────────────────────────────────────────────────────
// 1. snake_case preserve pattern is broad — may over-preserve some prose.
//    Tune HAIOS_PRESERVE_PATTERNS[9] if false positives appear.
// 2. Filler removal at sentence start can leave leading whitespace or
//    orphaned commas in complex sentence structures. Review output.
// 3. Ultra mode hedge removal uses lookbehind — not supported in all
//    JS environments. Falls back gracefully (no crash, hedge stays).
// 4. No wenyan/classical Chinese support (stub not ported — not needed).
// 5. H-ELICIT-01 hypothesis: compression register may affect LI scores
//    on elicited substrates. This tool is NOT to be used on live ACAT
//    elicitation prompts without Z2 ratification of that use case.

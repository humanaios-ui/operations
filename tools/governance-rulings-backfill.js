#!/usr/bin/env node

/**
 * Governance Rulings Backfill Script
 *
 * Parses git history to populate governance_rulings table
 * with all historical Z2 rulings
 *
 * Usage:
 *   node tools/governance-rulings-backfill.js
 *
 * Requires environment:
 *   SUPABASE_URL
 *   SUPABASE_SERVICE_ROLE_KEY
 *   GITHUB_TOKEN (optional, for enriching commit details)
 */

const { createClient } = require('@supabase/supabase-js');
const { execSync } = require('child_process');
const path = require('path');

// Configuration
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

// Validation
if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.error('❌ Missing environment variables:');
  console.error('   SUPABASE_URL');
  console.error('   SUPABASE_SERVICE_ROLE_KEY');
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { persistSession: false }
});

// Pattern from ingestion service
const RULING_PATTERN = /(?:z2|Z2)(?:\s+ruling)?\s+d(\d+)\s*\(([^)]+)\):\s*([^(#\n]+)/i;
const ISSUE_PATTERN = /#(\d+)/g;
const HASH_PATTERN = /hash\s+([a-f0-9]{7,64})/i;

function parseRulingFromCommit(message) {
  const match = message.match(RULING_PATTERN);
  if (!match) return null;

  const [, rulingNumber, question, decision] = match;
  const rulingId = `d${rulingNumber}`;

  const issues = [...message.matchAll(ISSUE_PATTERN)].map(m => `#${m[1]}`);
  const hashMatch = message.match(HASH_PATTERN);
  const hash = hashMatch ? hashMatch[1] : null;

  return {
    ruling_id: rulingId,
    question: question.trim(),
    decision: normalizeDecision(decision.trim()),
    ratification_hash: hash,
    issue_refs: issues.length > 0 ? issues.join(', ') : null
  };
}

function normalizeDecision(text) {
  const normalized = text
    .toUpperCase()
    .replace(/[\s\-+]/g, '_')
    .replace(/_+/g, '_')
    .replace(/[^A-Z0-9_]/g, '');

  const map = {
    'RULE_NOW': 'RULE_NOW',
    'LATER': 'LATER',
    'SET': 'SET',
    'BYPASS': 'BYPASS',
    'REQUIRE': 'REQUIRE',
    'FILE_AS_DRAFT': 'FILE_DRAFT',
    'ARCHIVE_AS_LISTED': 'ARCHIVE',
    'ACCEPT': 'ACCEPT',
    'EDIT': 'EDIT',
    'REJECT': 'REJECT'
  };

  return map[normalized] || normalized;
}

function inferCategory(question) {
  const text = question.toLowerCase();

  if (text.includes('schema') || text.includes('constant')) return 'schema';
  if (text.includes('zone') || text.includes('registry')) return 'process';
  if (text.includes('board') || text.includes('decision')) return 'board';
  if (text.includes('policy') || text.includes('gate')) return 'policy';
  if (text.includes('artifact') || text.includes('output')) return 'artifact';

  return 'process';
}

/**
 * Get git log entries with Z2 ruling patterns
 */
function getGitLog() {
  console.log('📖 Fetching git history...');

  try {
    // Get all commits matching the pattern, with full details
    const cmd = `git log --all --grep="Z2 ruling\\|z2 d" --format="%H%n%ai%n%an%n%ae%n%s%n%b%n---END---" --reverse`;
    const output = execSync(cmd, { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] });

    const entries = [];
    const blocks = output.split('---END---').filter(b => b.trim());

    for (const block of blocks) {
      const lines = block.trim().split('\n');
      if (lines.length < 4) continue;

      entries.push({
        sha: lines[0],
        date: lines[1],
        author: lines[2],
        email: lines[3],
        subject: lines[4],
        body: lines.slice(5).join('\n')
      });
    }

    console.log(`✓ Found ${entries.length} commits`);
    return entries;

  } catch (error) {
    console.error('Failed to fetch git log:', error.message);
    return [];
  }
}

/**
 * Check if ruling already exists
 */
async function rulingExists(rulingId) {
  const { data } = await supabase
    .from('governance_rulings')
    .select('id')
    .eq('ruling_id', rulingId)
    .single();

  return !!data;
}

/**
 * Extract PR number from commit body
 */
function extractPRNumber(body) {
  const match = body.match(/#(\d+)/);
  return match ? parseInt(match[1]) : null;
}

/**
 * Main backfill function
 */
async function backfill() {
  console.log('🚀 Starting Governance Rulings Backfill\n');

  const commits = getGitLog();
  if (commits.length === 0) {
    console.log('No commits found with ruling pattern');
    return;
  }

  let inserted = 0;
  let skipped = 0;
  let failed = 0;

  for (const commit of commits) {
    const fullMessage = `${commit.subject}\n${commit.body}`;
    const ruling = parseRulingFromCommit(fullMessage);

    if (!ruling) {
      skipped++;
      continue;
    }

    try {
      // Check if already exists
      if (await rulingExists(ruling.ruling_id)) {
        console.log(`⏭️  ${ruling.ruling_id} already exists, skipping`);
        skipped++;
        continue;
      }

      // Prepare record
      const record = {
        ...ruling,
        commit_sha: commit.sha,
        ratified_at: new Date(commit.date).toISOString(),
        ratified_by: commit.author,
        category: inferCategory(ruling.question),
        state: 'ACCEPTED',
        ingestion_source: 'git_commit',
        pr_number: extractPRNumber(commit.body),
        commit_url: `https://github.com/humanaios-ui/operations/commit/${commit.sha}`
      };

      // Insert
      const { error } = await supabase
        .from('governance_rulings')
        .insert([record]);

      if (error) {
        console.error(`❌ ${ruling.ruling_id}: ${error.message}`);
        failed++;
        continue;
      }

      console.log(`✓ ${ruling.ruling_id}: ${ruling.decision} (${record.ratified_at.slice(0, 10)})`);
      inserted++;

    } catch (error) {
      console.error(`❌ Error processing ${ruling?.ruling_id || 'unknown'}:`, error.message);
      failed++;
    }
  }

  // Summary
  console.log('\n📊 Backfill Summary:');
  console.log(`   ✓ Inserted: ${inserted}`);
  console.log(`   ⏭️  Skipped (already exist): ${skipped}`);
  console.log(`   ❌ Failed: ${failed}`);
  console.log(`   📈 Total processed: ${commits.length}`);

  if (inserted > 0) {
    console.log('\n✓ Backfill complete!');

    // Show summary
    const { data: samples } = await supabase
      .from('governance_rulings')
      .select('ruling_id, decision, ratified_at')
      .order('ratified_at', { ascending: false })
      .limit(5);

    if (samples && samples.length > 0) {
      console.log('\nRecent rulings in database:');
      for (const sample of samples) {
        console.log(`  ${sample.ruling_id}: ${sample.decision} (${sample.ratified_at.slice(0, 10)})`);
      }
    }
  }
}

// Run if called directly
if (require.main === module) {
  backfill().catch(error => {
    console.error('Backfill failed:', error);
    process.exit(1);
  });
}

module.exports = { backfill, parseRulingFromCommit };

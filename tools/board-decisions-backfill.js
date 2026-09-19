#!/usr/bin/env node

/**
 * Board Decisions & Molt Events Backfill Script
 *
 * Parses git history to populate board_decisions and molt_events tables
 * with historical Z2 board decisions and molt cycles
 *
 * Usage:
 *   node tools/board-decisions-backfill.js
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

// Pattern matching for board decisions and molt events
const BOARD_DECISION_PATTERN = /(?:z2\s+)?board\s+(?:decision|ruling):\s+([^(]+)\s*\(([^)]+)\):\s*([^(#\n]+)/i;
const MOLT_EVENT_PATTERN = /(?:molt|constant)\s+event:\s+([^\s]+)\s+\(([^)]+)\):\s*([^(#\n]+)/i;
const ISSUE_PATTERN = /#(\d+)/g;

function parseBoardDecisionFromCommit(message) {
  const match = message.match(BOARD_DECISION_PATTERN);
  if (!match) return null;

  const [, questionText, context, decision] = match;
  const issues = [...message.matchAll(ISSUE_PATTERN)].map(m => `#${m[1]}`);

  return {
    board_name: 'Z2 Board',
    decision_summary: questionText.trim(),
    board_section: context.trim(),
    decisions_made: {
      primary: {
        type: 'ruling',
        outcome: decision.trim(),
        evidence: issues.join(', ')
      }
    },
    epic_refs: issues.length > 0 ? issues : null,
    category: 'board',
    ingestion_source: 'batch_import'
  };
}

function parseMoltEventFromCommit(message) {
  const match = message.match(MOLT_EVENT_PATTERN);
  if (!match) return null;

  const [, constantId, context, decision] = match;
  const issues = [...message.matchAll(ISSUE_PATTERN)].map(m => `#${m[1]}`);

  return {
    constant_id: constantId.trim(),
    molt_type: 'parameter_sweep',
    prediction: context.trim(),
    prediction_confidence: 0.75,
    falsifier: `If prediction incorrect, revert ${constantId}`,
    actual_outcome: decision.trim(),
    state: 'MEASURED',
    category: 'molt',
    ingestion_source: 'batch_import'
  };
}

/**
 * Get git log entries with board decision or molt event patterns
 */
function getGitLog() {
  console.log('📖 Fetching git history...');

  try {
    // Get all commits matching the patterns
    const cmd = `git log --all --grep="board decision\\|molt event\\|board ruling\\|constant event" --format="%H%n%ai%n%an%n%ae%n%s%n%b%n---END---" --reverse`;
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
 * Check if board decision already exists
 */
async function boardDecisionExists(boardId) {
  const { data } = await supabase
    .from('board_decisions')
    .select('id')
    .eq('board_id', boardId)
    .single();

  return !!data;
}

/**
 * Check if molt event already exists
 */
async function moltEventExists(moltId) {
  const { data } = await supabase
    .from('molt_events')
    .select('id')
    .eq('molt_id', moltId)
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
  console.log('🚀 Starting Board Decisions & Molt Events Backfill\n');

  const commits = getGitLog();
  if (commits.length === 0) {
    console.log('No commits found with board decision/molt event patterns');
    return;
  }

  let boardInserted = 0;
  let boardSkipped = 0;
  let moltInserted = 0;
  let moltSkipped = 0;
  let failed = 0;

  for (const commit of commits) {
    const fullMessage = `${commit.subject}\n${commit.body}`;

    // Try board decision
    const boardDecision = parseBoardDecisionFromCommit(fullMessage);
    if (boardDecision) {
      try {
        const timestamp = new Date(commit.date).toISOString().split('T')[0].replace(/-/g, '');
        const boardId = `board-${timestamp}-${Math.random().toString(36).slice(2, 7)}`;

        if (await boardDecisionExists(boardId)) {
          console.log(`⏭️  ${boardId} already exists, skipping`);
          boardSkipped++;
        } else {
          const record = {
            ...boardDecision,
            board_id: boardId,
            meeting_date: new Date(commit.date).toISOString(),
            participants: [commit.author],
            pr_number: extractPRNumber(commit.body),
            commit_sha: commit.sha,
            commit_url: `https://github.com/humanaios-ui/operations/commit/${commit.sha}`,
            ratified_by: commit.author,
            ratified_at: new Date(commit.date).toISOString(),
            status: 'RATIFIED'
          };

          const { error } = await supabase
            .from('board_decisions')
            .insert([record]);

          if (error) {
            console.error(`❌ ${boardId}: ${error.message}`);
            failed++;
          } else {
            console.log(`✓ ${boardId}: ${boardDecision.board_section} (${record.ratified_at.slice(0, 10)})`);
            boardInserted++;
          }
        }
      } catch (error) {
        console.error(`❌ Error processing board decision:`, error.message);
        failed++;
      }
    }

    // Try molt event
    const moltEvent = parseMoltEventFromCommit(fullMessage);
    if (moltEvent) {
      try {
        const timestamp = new Date(commit.date).toISOString().split('T')[0].replace(/-/g, '');
        const moltId = `molt-${timestamp}-${moltEvent.constant_id}-${Math.random().toString(36).slice(2, 7)}`;

        if (await moltEventExists(moltId)) {
          console.log(`⏭️  ${moltId} already exists, skipping`);
          moltSkipped++;
        } else {
          const record = {
            ...moltEvent,
            molt_id: moltId,
            window_start: new Date(commit.date).toISOString(),
            window_end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            decision_made_at: new Date(commit.date).toISOString(),
            decision_made_by: commit.author,
            pr_number: extractPRNumber(commit.body),
            commit_sha: commit.sha,
            commit_url: `https://github.com/humanaios-ui/operations/commit/${commit.sha}`
          };

          const { error } = await supabase
            .from('molt_events')
            .insert([record]);

          if (error) {
            console.error(`❌ ${moltId}: ${error.message}`);
            failed++;
          } else {
            console.log(`✓ ${moltId}: ${moltEvent.constant_id} (${record.window_start.slice(0, 10)})`);
            moltInserted++;
          }
        }
      } catch (error) {
        console.error(`❌ Error processing molt event:`, error.message);
        failed++;
      }
    }
  }

  // Summary
  console.log('\n📊 Backfill Summary:');
  console.log(`   ✓ Board Decisions Inserted: ${boardInserted}`);
  console.log(`   ⏭️  Board Decisions Skipped: ${boardSkipped}`);
  console.log(`   ✓ Molt Events Inserted: ${moltInserted}`);
  console.log(`   ⏭️  Molt Events Skipped: ${moltSkipped}`);
  console.log(`   ❌ Failed: ${failed}`);
  console.log(`   📈 Total processed: ${commits.length}`);

  if (boardInserted > 0 || moltInserted > 0) {
    console.log('\n✓ Backfill complete!');

    // Show summary
    const { data: boardSamples } = await supabase
      .from('board_decisions')
      .select('board_id, board_section, ratified_at')
      .order('ratified_at', { ascending: false })
      .limit(3);

    if (boardSamples && boardSamples.length > 0) {
      console.log('\nRecent board decisions in database:');
      for (const sample of boardSamples) {
        console.log(`  ${sample.board_id}: ${sample.board_section} (${sample.ratified_at.slice(0, 10)})`);
      }
    }

    const { data: moltSamples } = await supabase
      .from('molt_events')
      .select('molt_id, constant_id, state, created_at')
      .order('created_at', { ascending: false })
      .limit(3);

    if (moltSamples && moltSamples.length > 0) {
      console.log('\nRecent molt events in database:');
      for (const sample of moltSamples) {
        console.log(`  ${sample.molt_id}: ${sample.constant_id} (${sample.state})`);
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

module.exports = { backfill, parseBoardDecisionFromCommit, parseMoltEventFromCommit };

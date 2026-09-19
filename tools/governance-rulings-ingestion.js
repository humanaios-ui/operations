/**
 * Governance Rulings Ingestion Service
 *
 * Autonomous handler for GitHub webhooks and scheduled polling
 * to populate governance_rulings table in Supabase
 *
 * Deployment: Railway, alongside relay service
 * Triggers: GitHub webhooks (push, pull_request) + scheduled jobs (6h, 12h)
 */

const { createClient } = require('@supabase/supabase-js');
const crypto = require('crypto');

// Environment configuration
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const WEBHOOK_SECRET = process.env.GITHUB_WEBHOOK_SECRET;

// Initialize Supabase client (service role for unrestricted writes)
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { persistSession: false }
});

/**
 * Pattern matching for Z2 rulings in commit messages
 *
 * Matches:
 * - "Z2 ruling d15 (Q-BOARD-RULING-15): rule now (#405)"
 * - "z2 d15 (Q-BOARD-RULING-15): later — PENDING, hash 4bee..."
 * - "Z2 ruling d3 (Q-BOARD-RULING-03): set (#395)"
 */
const RULING_PATTERN = /(?:z2|Z2)(?:\s+ruling)?\s+d(\d+)\s*\(([^)]+)\):\s*([^(#\n]+)/i;
const ISSUE_PATTERN = /#(\d+)/g;
const HASH_PATTERN = /hash\s+([a-f0-9]{7,64})/i;

/**
 * Extract governance ruling from commit message
 */
function parseRulingFromCommit(message) {
  const match = message.match(RULING_PATTERN);
  if (!match) return null;

  const [, rulingNumber, question, decision] = match;
  const rulingId = `d${rulingNumber}`;

  // Extract related issue numbers
  const issues = [...message.matchAll(ISSUE_PATTERN)].map(m => `#${m[1]}`);

  // Extract hash if present
  const hashMatch = message.match(HASH_PATTERN);
  const hash = hashMatch ? hashMatch[1] : null;

  return {
    ruling_id: rulingId,
    question: question.trim(),
    decision: normalizeDecision(decision.trim()),
    ratification_hash: hash,
    issue_refs: issues.length > 0 ? issues.join(', ') : null,
    ingestion_source: 'git_commit'
  };
}

/**
 * Normalize decision text to canonical form
 *
 * Input: "rule now", "later", "set", "bypass + IC", etc.
 * Output: RULE_NOW, LATER, SET, BYPASS, etc.
 */
function normalizeDecision(text) {
  const normalized = text
    .toUpperCase()
    .replace(/[\s\-+]/g, '_')
    .replace(/_+/g, '_')
    .replace(/[^A-Z0-9_]/g, '');

  // Map common variations
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

/**
 * Extract PR number from GitHub webhook payload
 */
function getPRNumber(payload) {
  if (payload.pull_request?.number) return payload.pull_request.number;
  if (payload.issue?.number) return payload.issue.number;
  return null;
}

/**
 * Extract category from question or PR title
 */
function inferCategory(question, prTitle) {
  const text = `${question} ${prTitle}`.toLowerCase();

  if (text.includes('schema') || text.includes('constant')) return 'schema';
  if (text.includes('zone') || text.includes('registry')) return 'process';
  if (text.includes('board') || text.includes('decision')) return 'board';
  if (text.includes('policy') || text.includes('gate')) return 'policy';
  if (text.includes('artifact') || text.includes('output')) return 'artifact';

  return 'process';
}

/**
 * GitHub webhook handler: pull_request.closed
 */
async function handlePullRequestClosed(payload) {
  const { pull_request, repository } = payload;

  if (!pull_request.merged) {
    console.log(`PR #${pull_request.number} closed without merge, skipping`);
    return;
  }

  console.log(`Processing merged PR #${pull_request.number}`);

  try {
    // Get commit details
    const commit = pull_request.merge_commit_sha;
    const commitData = await getCommitData(repository.full_name, commit);

    if (!commitData) {
      console.log(`Could not fetch commit ${commit}`);
      return;
    }

    // Parse ruling from commit message
    const ruling = parseRulingFromCommit(commitData.message);
    if (!ruling) {
      console.log(`No ruling pattern found in commit message`);
      return;
    }

    // Check if ruling already exists
    const { data: existing } = await supabase
      .from('governance_rulings')
      .select('id')
      .eq('ruling_id', ruling.ruling_id)
      .single();

    if (existing) {
      console.log(`Ruling ${ruling.ruling_id} already exists, updating state to ACCEPTED`);
      await supabase
        .from('governance_rulings')
        .update({
          state: 'ACCEPTED',
          pr_number: pull_request.number,
          pr_url: pull_request.html_url,
          commit_sha: commit,
          commit_url: commitData.html_url,
          ratified_at: new Date(commitData.author.date),
          ratified_by: commitData.author.name,
          updated_at: new Date()
        })
        .eq('ruling_id', ruling.ruling_id);
      return;
    }

    // Insert new ruling
    const newRuling = {
      ...ruling,
      pr_number: pull_request.number,
      pr_url: pull_request.html_url,
      commit_sha: commit,
      commit_url: commitData.html_url,
      ratified_at: new Date(commitData.author.date),
      ratified_by: commitData.author.name,
      category: inferCategory(ruling.question, pull_request.title),
      state: 'ACCEPTED'
    };

    console.log(`Inserting ruling: ${ruling.ruling_id}`, newRuling);

    const { data, error } = await supabase
      .from('governance_rulings')
      .insert([newRuling])
      .select();

    if (error) {
      console.error(`Failed to insert ruling: ${error.message}`, error);
      throw error;
    }

    console.log(`✓ Successfully inserted ruling ${ruling.ruling_id}`);

  } catch (error) {
    console.error(`Error processing PR #${pull_request.number}:`, error);
    throw error;
  }
}

/**
 * GitHub webhook handler: push
 *
 * Trigger immediate parsing of new commits
 */
async function handlePush(payload) {
  const { repository, commits } = payload;

  console.log(`Processing ${commits.length} commits from push`);

  for (const commit of commits) {
    try {
      const ruling = parseRulingFromCommit(commit.message);
      if (!ruling) continue;

      console.log(`Found ruling ${ruling.ruling_id} in commit ${commit.id.slice(0, 7)}`);

      // Check if already exists
      const { data: existing } = await supabase
        .from('governance_rulings')
        .select('id')
        .eq('ruling_id', ruling.ruling_id)
        .single();

      if (existing) {
        console.log(`Ruling ${ruling.ruling_id} already exists`);
        continue;
      }

      // Insert new ruling
      const newRuling = {
        ...ruling,
        commit_sha: commit.id,
        commit_url: commit.url,
        ratified_at: new Date(commit.timestamp),
        ratified_by: commit.author.name,
        category: inferCategory(ruling.question, ''),
        state: 'PENDING'  // Awaiting PR integration
      };

      const { error } = await supabase
        .from('governance_rulings')
        .insert([newRuling]);

      if (error) {
        console.error(`Failed to insert ruling: ${error.message}`);
        continue;
      }

      console.log(`✓ Inserted ruling ${ruling.ruling_id}`);

    } catch (error) {
      console.error(`Error processing commit:`, error);
    }
  }
}

/**
 * Scheduled job: Backfill from git log
 *
 * Run every 12 hours to catch any missed rulings
 * Useful for recovery or backfilling after service restart
 */
async function backfillFromGitLog() {
  console.log('Starting backfill from git log...');

  try {
    // Get the most recent ruling we have
    const { data: recent } = await supabase
      .from('governance_rulings')
      .select('ratified_at')
      .order('ratified_at', { ascending: false })
      .limit(1)
      .single();

    const since = recent ? new Date(recent.ratified_at) : new Date('2026-01-01');
    const sinceIso = since.toISOString();

    console.log(`Fetching commits since ${sinceIso}`);

    // This would call your git log command or GitHub API
    // Implementation depends on your setup (local clone vs. GitHub API)
    // For now, log the expected behavior
    console.log(`[SCHEDULED] Would backfill commits since ${sinceIso}`);
    console.log(`[SCHEDULED] Pattern: git log --grep="Z2 ruling|z2 d" --since="${sinceIso}" --format=fuller`);

  } catch (error) {
    console.error('Backfill failed:', error);
  }
}

/**
 * Utility: Fetch commit details from GitHub API
 */
async function getCommitData(repoFullName, sha) {
  if (!GITHUB_TOKEN) {
    console.warn('GITHUB_TOKEN not set, cannot fetch commit details');
    return null;
  }

  try {
    const response = await fetch(
      `https://api.github.com/repos/${repoFullName}/commits/${sha}`,
      {
        headers: {
          'Accept': 'application/vnd.github.v3+json',
          'Authorization': `token ${GITHUB_TOKEN}`
        }
      }
    );

    if (!response.ok) {
      console.error(`GitHub API error: ${response.status}`);
      return null;
    }

    const data = await response.json();
    return {
      message: data.commit.message,
      author: data.commit.author,
      html_url: data.html_url
    };

  } catch (error) {
    console.error('Failed to fetch commit:', error);
    return null;
  }
}

/**
 * Verify webhook signature
 */
function verifyWebhookSignature(payload, signature) {
  if (!WEBHOOK_SECRET) {
    console.warn('WEBHOOK_SECRET not set, skipping signature verification');
    return true;
  }

  const hash = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');

  const expected = `sha256=${hash}`;
  return crypto.timingSafeEqual(expected, signature);
}

/**
 * Webhook endpoint handler
 */
async function handleWebhook(req, res) {
  const signature = req.headers['x-hub-signature-256'];
  const event = req.headers['x-github-event'];

  if (!signature || !verifyWebhookSignature(JSON.stringify(req.body), signature)) {
    console.warn('Invalid webhook signature');
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    if (event === 'pull_request' && req.body.action === 'closed') {
      await handlePullRequestClosed(req.body);
    } else if (event === 'push') {
      await handlePush(req.body);
    } else {
      console.log(`Unhandled event type: ${event}`);
    }

    res.json({ success: true, event });

  } catch (error) {
    console.error('Webhook handling failed:', error);
    res.status(500).json({ error: error.message });
  }
}

// Export for Express integration
module.exports = {
  handleWebhook,
  handlePullRequestClosed,
  handlePush,
  backfillFromGitLog,
  parseRulingFromCommit,
  verifyWebhookSignature
};

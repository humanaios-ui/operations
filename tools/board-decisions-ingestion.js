#!/usr/bin/env node

/**
 * Board Decisions & Molt Events Ingestion Service
 *
 * Handles autonomous ingestion of Z2 board meeting outcomes and molt events
 * into Supabase via GitHub webhooks and relay service events.
 *
 * Deployment: Railway, alongside relay service
 * Triggers: GitHub webhooks (push, pull_request) + relay events (board_decision, molt_event)
 */

const { createClient } = require('@supabase/supabase-js');
const crypto = require('crypto');

// Environment configuration
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const WEBHOOK_SECRET = process.env.GITHUB_WEBHOOK_SECRET;
const RELAY_API_KEY = process.env.RELAY_API_KEY;

// Initialize Supabase client (service role for unrestricted writes)
const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
  auth: { persistSession: false }
});

/**
 * Pattern matching for board decisions in commit messages or relay events
 *
 * Matches:
 * - "Z2 board decision: rule now on Q-RESOURCE-ALLOCATION (#405)"
 * - "Board: Q-BOARD-DECISION-15 (Schema review): ACCEPTED (#406)"
 */
const BOARD_DECISION_PATTERN = /(?:z2\s+)?board\s+(?:decision|ruling):\s+([^(]+)\s*\(([^)]+)\):\s*([^(#\n]+)/i;
const MOLT_EVENT_PATTERN = /(?:molt|constant)\s+event:\s+([^\s]+)\s+\(([^)]+)\):\s*([^(#\n]+)/i;
const ISSUE_PATTERN = /#(\d+)/g;

/**
 * Extract board decision from commit message or relay event
 */
function parseBoardDecisionFromCommit(message) {
  const match = message.match(BOARD_DECISION_PATTERN);
  if (!match) return null;

  const [, questionText, context, decision] = match;

  // Extract related issue numbers
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
    ingestion_source: 'github_webhook'
  };
}

/**
 * Extract molt event from commit message or relay event
 */
function parseMoltEventFromCommit(message) {
  const match = message.match(MOLT_EVENT_PATTERN);
  if (!match) return null;

  const [, constantId, context, decision] = match;
  const issues = [...message.matchAll(ISSUE_PATTERN)].map(m => `#${m[1]}`);

  return {
    constant_id: constantId.trim(),
    molt_type: 'parameter_sweep',
    prediction: context.trim(),
    prediction_confidence: 0.75, // Default confidence
    falsifier: `If prediction incorrect, revert ${constantId}`,
    actual_outcome: decision.trim(),
    state: 'MEASURED',
    ingestion_source: 'github_webhook'
  };
}

/**
 * Normalize decision text to canonical form
 */
function normalizeDecision(text) {
  const normalized = text
    .toUpperCase()
    .replace(/[\s\-+]/g, '_')
    .replace(/_+/g, '_')
    .replace(/[^A-Z0-9_]/g, '');

  const map = {
    'ACCEPT': 'ACCEPTED',
    'RULE_NOW': 'ACCEPTED',
    'LATER': 'PENDING_RATIFICATION',
    'REJECT': 'SUPERSEDED',
    'ARCHIVE': 'CLOSED'
  };

  return map[normalized] || normalized;
}

/**
 * GitHub webhook handler: pull_request.closed
 * Extract board decisions from merged PR
 */
async function handlePullRequestClosed(payload) {
  const { pull_request, repository } = payload;

  if (!pull_request.merged) {
    console.log(`PR #${pull_request.number} closed without merge, skipping`);
    return;
  }

  console.log(`Processing merged PR #${pull_request.number} for board decisions`);

  try {
    // Get commit details
    const commit = pull_request.merge_commit_sha;
    const commitData = await getCommitData(repository.full_name, commit);

    if (!commitData) {
      console.log(`Could not fetch commit ${commit}`);
      return;
    }

    // Parse for board decision
    const boardDecision = parseBoardDecisionFromCommit(commitData.message);
    if (boardDecision) {
      await insertBoardDecision({
        ...boardDecision,
        meeting_date: new Date(commitData.author.date),
        pr_number: pull_request.number,
        pr_url: pull_request.html_url,
        commit_sha: commit,
        commit_url: commitData.html_url,
        ratified_by: commitData.author.name,
        ratified_at: new Date(commitData.author.date),
        status: 'RATIFIED'
      });
    }

    // Parse for molt event
    const moltEvent = parseMoltEventFromCommit(commitData.message);
    if (moltEvent) {
      await insertMoltEvent({
        ...moltEvent,
        window_start: new Date(commitData.author.date),
        window_end: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
        decision_made_at: new Date(commitData.author.date),
        decision_made_by: commitData.author.name,
        pr_number: pull_request.number,
        pr_url: pull_request.html_url,
        commit_sha: commit,
        commit_url: commitData.html_url
      });
    }

  } catch (error) {
    console.error(`Error processing PR #${pull_request.number}:`, error);
    throw error;
  }
}

/**
 * Relay service event handler: board_decision event
 * Direct ingestion of board decisions from relay
 */
async function handleRelayBoardDecisionEvent(event) {
  console.log(`Processing board decision from relay: ${event.board_id}`);

  try {
    const decision = {
      board_id: event.board_id,
      board_name: event.board_name || 'Z2 Board',
      meeting_date: new Date(event.meeting_date),
      participants: event.participants || [],
      decisions_made: event.decisions || {},
      decisions_summary: event.summary,
      status: event.status || 'PENDING_RATIFICATION',
      category: event.category || 'board',
      ingestion_source: 'relay_webhook'
    };

    if (event.recording_url) decision.recording_url = event.recording_url;
    if (event.minutes_url) decision.minutes_url = event.minutes_url;
    if (event.ruling_id) decision.ruling_id = event.ruling_id;

    await insertBoardDecision(decision);
  } catch (error) {
    console.error(`Error processing relay board decision event:`, error);
    throw error;
  }
}

/**
 * Relay service event handler: molt_event event
 * Direct ingestion of molt cycles from relay
 */
async function handleRelayMoltEventEvent(event) {
  console.log(`Processing molt event from relay: ${event.molt_id}`);

  try {
    const molt = {
      molt_id: event.molt_id,
      constant_id: event.constant_id,
      molt_type: event.molt_type || 'parameter_sweep',
      prediction: event.prediction,
      prediction_confidence: event.prediction_confidence || 0.50,
      falsifier: event.falsifier,
      window_start: new Date(event.window_start),
      window_end: new Date(event.window_end),
      state: event.state || 'PENDING',
      category: 'molt',
      ingestion_source: 'relay_webhook'
    };

    if (event.measurement_date) molt.measurement_date = new Date(event.measurement_date);
    if (event.measurement_value) molt.measurement_value = event.measurement_value;
    if (event.actual_outcome) molt.actual_outcome = event.actual_outcome;
    if (event.accuracy_score !== undefined) molt.accuracy_score = event.accuracy_score;
    if (event.falsifier_triggered !== undefined) molt.falsifier_triggered = event.falsifier_triggered;
    if (event.proposal_id) molt.proposal_id = event.proposal_id;

    await insertMoltEvent(molt);
  } catch (error) {
    console.error(`Error processing relay molt event:`, error);
    throw error;
  }
}

/**
 * Insert board decision into Supabase
 */
async function insertBoardDecision(decision) {
  // Generate unique board_id if not provided
  if (!decision.board_id) {
    const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
    decision.board_id = `board-${timestamp}-${Math.random().toString(36).slice(2, 7)}`;
  }

  console.log(`Inserting board decision: ${decision.board_id}`);

  const { data, error } = await supabase
    .from('board_decisions')
    .insert([decision])
    .select();

  if (error) {
    console.error(`Failed to insert board decision: ${error.message}`, error);
    throw error;
  }

  console.log(`✓ Successfully inserted board decision ${decision.board_id}`);
}

/**
 * Insert molt event into Supabase
 */
async function insertMoltEvent(molt) {
  // Generate unique molt_id if not provided
  if (!molt.molt_id) {
    const timestamp = new Date().toISOString().split('T')[0].replace(/-/g, '');
    molt.molt_id = `molt-${timestamp}-${molt.constant_id}-${Math.random().toString(36).slice(2, 7)}`;
  }

  console.log(`Inserting molt event: ${molt.molt_id}`);

  const { data, error } = await supabase
    .from('molt_events')
    .insert([molt])
    .select();

  if (error) {
    console.error(`Failed to insert molt event: ${error.message}`, error);
    throw error;
  }

  console.log(`✓ Successfully inserted molt event ${molt.molt_id}`);
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
 * Verify webhook signature (same as Phase 1)
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
      console.log(`Push event received, parsing for board decisions/molt events`);
      // Push events could contain board decision or molt event commits
    } else {
      console.log(`Unhandled event type: ${event}`);
    }

    res.json({ success: true, event });

  } catch (error) {
    console.error('Webhook handling failed:', error);
    res.status(500).json({ error: error.message });
  }
}

/**
 * Relay event handler (direct from relay service)
 * POST /events/relay with Authorization: Bearer RELAY_API_KEY
 */
async function handleRelayEvent(req, res) {
  const authHeader = req.headers['authorization'];
  const expectedAuth = `Bearer ${RELAY_API_KEY}`;

  if (!authHeader || authHeader !== expectedAuth) {
    console.warn('Invalid relay API key');
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const { event_type, payload } = req.body;

    if (event_type === 'board_decision') {
      await handleRelayBoardDecisionEvent(payload);
    } else if (event_type === 'molt_event') {
      await handleRelayMoltEventEvent(payload);
    } else {
      console.log(`Unknown relay event type: ${event_type}`);
    }

    res.json({ success: true, event_type });

  } catch (error) {
    console.error('Relay event handling failed:', error);
    res.status(500).json({ error: error.message });
  }
}

// Export for Express integration
module.exports = {
  handleWebhook,
  handleRelayEvent,
  handlePullRequestClosed,
  handleRelayBoardDecisionEvent,
  handleRelayMoltEventEvent,
  parseBoardDecisionFromCommit,
  parseMoltEventFromCommit,
  verifyWebhookSignature
};

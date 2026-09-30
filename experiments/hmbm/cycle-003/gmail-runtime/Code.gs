/**
 * HMBM-CYCLE-003 — Gmail Continuity Runtime
 * PAPER ONLY / NO REAL CAPITAL
 *
 * Purpose:
 *   Run DHP custody/backpressure directly in Gmail + Google Apps Script.
 *   This runtime does NOT place trades, access wallets, request private keys,
 *   move funds, or represent simulated capital as real.
 *
 * Security/custody note:
 *   Producer/Courier/Witness are logically separated functions inside one
 *   Apps Script deployment. This is LOGICAL, not credential-isolated custody.
 *   Human ACCEPT/REJECT remains mandatory before canonical advancement.
 */

const HMBM = Object.freeze({
  EXPERIMENT_ID: 'HMBM-CYCLE-003',
  PAPER_ONLY: true,
  RECIPIENT: 'aioshuman@gmail.com',
  BRANCH: 'feat/hmbm-c003-durable-handoff-protocol',
  REPO_RAW: 'https://raw.githubusercontent.com/humanaios-ui/operations/feat/hmbm-c003-durable-handoff-protocol',
  GEN003_BASE: 'experiments/hmbm/cycle-003/queue/C003-H01-CANDIDATE/C003-H01-GEN-003',
  CANONICAL_START: 'C003-H0-ACCEPTED',
  SUBJECT_PREFIX: '[HMBM-CYCLE-003]',
  LABELS: {
    ROOT: 'HMBM/CYCLE-003',
    QUEUED: 'HMBM/CYCLE-003/QUEUED',
    COMMUNICATED: 'HMBM/CYCLE-003/COMMUNICATED',
    ACCEPTED: 'HMBM/CYCLE-003/ACCEPTED',
    REJECTED: 'HMBM/CYCLE-003/REJECTED',
    FAILURE: 'HMBM/CYCLE-003/FAILURE',
    HOLD: 'HMBM/CYCLE-003/HOLD_PENDING_DOWNSTREAM'
  }
});

function setupHmbmCycle003() {
  assertPaperOnly_();
  Object.values(HMBM.LABELS).forEach(ensureLabel_);
  const p = PropertiesService.getScriptProperties();
  if (!p.getProperty('HMBM_CANONICAL_STATE')) {
    p.setProperty('HMBM_CANONICAL_STATE', HMBM.CANONICAL_START);
  }
  p.setProperty('HMBM_RUNTIME_MODE', 'PAPER_ONLY_NO_REAL_CAPITAL');
  p.setProperty('HMBM_CUSTODY_MODEL', 'LOGICAL_NOT_CREDENTIAL_ISOLATED');

  // One scheduled dispatcher is sufficient. It never bypasses role guards.
  removeNamedTriggers_('hmbmDispatcher');
  ScriptApp.newTrigger('hmbmDispatcher').timeBased().everyMinutes(5).create();

  return status_();
}

function hmbmDispatcher() {
  assertPaperOnly_();

  // Backpressure is checked before every action.
  const state = status_();

  // 1. Bootstrap GEN-003 from the already-ratified repository queue if needed.
  if (!state.gen003LocalQueuePresent && !state.gen003Communicated && !state.gen003Accepted && !state.gen003Rejected) {
    producerBootstrapGen003_();
    return status_();
  }

  // 2. Courier may communicate one verified QUEUED artifact.
  if (state.gen003LocalQueuePresent && !state.gen003Communicated && !state.gen003Accepted && !state.gen003Rejected) {
    courierCommunicateGen003_();
    return status_();
  }

  // 3. Witness only observes explicit human ACCEPT/REJECT commands.
  if (state.gen003Communicated && !state.gen003Accepted && !state.gen003Rejected) {
    witnessObserveHumanDisposition_();
    return status_();
  }

  // 4. If accepted/rejected, stop. A later Producer generation requires
  //    an explicit new adapter/revision; this runtime will not invent GEN-004.
  return status_();
}

/**
 * PRODUCER role.
 * Imports the already-QUEUED GEN-003 artifact from PR #597,
 * verifies exact bytes against queued receipt, then stores an immutable
 * Gmail draft as local queue persistence.
 *
 * No send. No acceptance. No canonical advancement.
 */
function producerBootstrapGen003_() {
  roleGuard_('PRODUCER');
  assertCanonical_('C003-H0-ACCEPTED');

  const existing = findDraftByMarker_('C003-H01-GEN-003', 'PERSISTENCE_PENDING');
  if (existing) {
    setHold_('C003-H01-GEN-003');
    return;
  }

  const base = HMBM.REPO_RAW + '/' + HMBM.GEN003_BASE;
  const candidate = fetchText_(base + '/candidate.json');
  const manifest = JSON.parse(fetchText_(base + '/manifest.json'));
  const receipt = JSON.parse(fetchText_(base + '/queued-receipt.json'));

  if (receipt.state !== 'QUEUED') throw failure_('PRODUCER', 'QUEUE_STATE_INVALID', receipt.state);
  if (receipt.predecessor_state_id !== 'C003-H0-ACCEPTED') throw failure_('PRODUCER', 'PREDECESSOR_MISMATCH', receipt.predecessor_state_id);

  const sha = sha256Hex_(candidate);
  if (sha !== receipt.artifact_sha256) throw failure_('PRODUCER', 'READBACK_HASH_MISMATCH', sha);
  if (sha !== manifest.file_bytes_sha256) throw failure_('PRODUCER', 'MANIFEST_HASH_MISMATCH', sha);

  const body = [
    'PERSISTENCE_PENDING — ANALYST NODE — DO NOT TREAT AS ACCEPTED',
    'PAPER ONLY / NO REAL CAPITAL',
    '',
    'EXPERIMENT: HMBM-CYCLE-003',
    'CANDIDATE: C003-H01-CANDIDATE',
    'GENERATION: C003-H01-GEN-003',
    'PREDECESSOR: C003-H0-ACCEPTED',
    'DHP_STATE: QUEUED',
    'ARTIFACT_SHA256: ' + sha,
    'SOURCE: operations PR #597 repository queue',
    'CUSTODY: PRODUCER; NO SEND / NO ACCEPT / NO CANONICAL ADVANCE'
  ].join('\n');

  GmailApp.createDraft(
    HMBM.RECIPIENT,
    '[HMBM-CYCLE-003] H01/24 | PAPER | QUEUED GEN-003',
    body,
    {attachments: [Utilities.newBlob(candidate, 'application/json', 'C003-H01-GEN-003_candidate.json')]}
  );

  PropertiesService.getScriptProperties().setProperties({
    GEN003_QUEUE_SHA256: sha,
    GEN003_QUEUE_STATE: 'QUEUED',
    GEN003_QUEUE_VERIFIED: 'TRUE'
  }, false);

  setHold_('C003-H01-GEN-003');
}

/**
 * COURIER role.
 * Sends the existing verified draft unchanged in semantic content.
 * It never changes candidate bytes and never accepts/canonicalizes.
 */
function courierCommunicateGen003_() {
  roleGuard_('COURIER');
  assertCanonical_('C003-H0-ACCEPTED');

  const p = PropertiesService.getScriptProperties();
  if (p.getProperty('GEN003_QUEUE_VERIFIED') !== 'TRUE') throw failure_('COURIER', 'QUEUE_NOT_VERIFIED', 'FALSE');

  const draft = findDraftByMarker_('C003-H01-GEN-003', 'PERSISTENCE_PENDING');
  if (!draft) throw failure_('COURIER', 'QUEUE_DRAFT_MISSING', 'NONE');

  const msg = draft.getMessage();
  const atts = msg.getAttachments();
  if (atts.length !== 1) throw failure_('COURIER', 'ATTACHMENT_COUNT_INVALID', String(atts.length));

  const bytes = atts[0].getBytes();
  const hash = sha256BytesHex_(bytes);
  if (hash !== p.getProperty('GEN003_QUEUE_SHA256')) throw failure_('COURIER', 'ATTACHMENT_HASH_MISMATCH', hash);

  // Explicit Courier boundary: send only after verification.
  const sentMessage = draft.send();

  PropertiesService.getScriptProperties().setProperties({
    GEN003_COMMUNICATED: 'TRUE',
    GEN003_COMMUNICATION_MESSAGE_ID: sentMessage.getId(),
    GEN003_COMMUNICATION_THREAD_ID: sentMessage.getThread().getId(),
    GEN003_COMMUNICATION_SHA256: hash
  }, false);

  labelThread_(sentMessage.getThread(), HMBM.LABELS.COMMUNICATED);
  clearHold_();
}

/**
 * WITNESS role.
 * Human authority is required. A human reply in the communication thread must
 * contain exactly one command line:
 *
 * ACCEPT C003-H01-GEN-003 <sha256>
 * or
 * REJECT C003-H01-GEN-003 <reason>
 *
 * The script never self-accepts.
 */
function witnessObserveHumanDisposition_() {
  roleGuard_('WITNESS');

  const p = PropertiesService.getScriptProperties();
  const tid = p.getProperty('GEN003_COMMUNICATION_THREAD_ID');
  if (!tid) return;

  const thread = GmailApp.getThreadById(tid);
  if (!thread) throw failure_('WITNESS', 'COMMUNICATION_THREAD_MISSING', tid);

  const expectedHash = p.getProperty('GEN003_QUEUE_SHA256');
  const messages = thread.getMessages();

  for (let i = 1; i < messages.length; i++) {
    const body = messages[i].getPlainBody();

    const accept = body.match(/^ACCEPT C003-H01-GEN-003 ([a-f0-9]{64})\s*$/mi);
    if (accept) {
      if (accept[1] !== expectedHash) throw failure_('WITNESS', 'ACCEPT_HASH_MISMATCH', accept[1]);
      p.setProperties({
        GEN003_ACCEPTED: 'TRUE',
        GEN003_ACCEPTANCE_MESSAGE_ID: messages[i].getId(),
        HMBM_CANONICAL_STATE: 'C003-H01-ACCEPTED'
      }, false);
      labelThread_(thread, HMBM.LABELS.ACCEPTED);
      return;
    }

    const reject = body.match(/^REJECT C003-H01-GEN-003 (.+)$/mi);
    if (reject) {
      p.setProperties({
        GEN003_REJECTED: 'TRUE',
        GEN003_REJECTION_MESSAGE_ID: messages[i].getId(),
        GEN003_REJECTION_REASON: reject[1].trim()
      }, false);
      labelThread_(thread, HMBM.LABELS.REJECTED);
      return;
    }
  }
}

function status_() {
  const p = PropertiesService.getScriptProperties();
  return {
    experiment: HMBM.EXPERIMENT_ID,
    mode: 'PAPER_ONLY_NO_REAL_CAPITAL',
    canonical: p.getProperty('HMBM_CANONICAL_STATE') || HMBM.CANONICAL_START,
    custodyModel: p.getProperty('HMBM_CUSTODY_MODEL') || 'UNSET',
    gen003LocalQueuePresent: !!findDraftByMarker_('C003-H01-GEN-003', 'PERSISTENCE_PENDING'),
    gen003QueueVerified: p.getProperty('GEN003_QUEUE_VERIFIED') === 'TRUE',
    gen003Communicated: p.getProperty('GEN003_COMMUNICATED') === 'TRUE',
    gen003Accepted: p.getProperty('GEN003_ACCEPTED') === 'TRUE',
    gen003Rejected: p.getProperty('GEN003_REJECTED') === 'TRUE',
    holdPendingDownstream: p.getProperty('HOLD_PENDING_DOWNSTREAM') === 'TRUE'
  };
}

function hmbmStatus() {
  const s = status_();
  console.log(JSON.stringify(s, null, 2));
  return s;
}

function findDraftByMarker_(generation, marker) {
  const drafts = GmailApp.getDrafts();
  for (let i = 0; i < drafts.length; i++) {
    const m = drafts[i].getMessage();
    if (m.getSubject().indexOf(HMBM.SUBJECT_PREFIX) !== -1 &&
        m.getPlainBody().indexOf(generation) !== -1 &&
        m.getPlainBody().indexOf(marker) !== -1) return drafts[i];
  }
  return null;
}

function setHold_(generation) {
  PropertiesService.getScriptProperties().setProperties({
    HOLD_PENDING_DOWNSTREAM: 'TRUE',
    HOLD_GENERATION: generation
  }, false);
}

function clearHold_() {
  PropertiesService.getScriptProperties().deleteProperty('HOLD_PENDING_DOWNSTREAM');
}

function ensureLabel_(name) {
  return GmailApp.getUserLabelByName(name) || GmailApp.createLabel(name);
}

function labelThread_(thread, labelName) {
  thread.addLabel(ensureLabel_(labelName));
}

function fetchText_(url) {
  const r = UrlFetchApp.fetch(url, {muteHttpExceptions: true});
  if (r.getResponseCode() !== 200) throw failure_('PRODUCER', 'SOURCE_FETCH_FAILED', url + ' HTTP ' + r.getResponseCode());
  return r.getContentText();
}

function sha256Hex_(text) {
  return sha256BytesHex_(Utilities.newBlob(text).getBytes());
}

function sha256BytesHex_(bytes) {
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, bytes);
  return digest.map(b => {
    const v = b < 0 ? b + 256 : b;
    return ('0' + v.toString(16)).slice(-2);
  }).join('');
}

function assertCanonical_(expected) {
  const current = PropertiesService.getScriptProperties().getProperty('HMBM_CANONICAL_STATE') || HMBM.CANONICAL_START;
  if (current !== expected) throw failure_('CONTROL', 'CANONICAL_MISMATCH', current);
}

function assertPaperOnly_() {
  if (!HMBM.PAPER_ONLY) throw new Error('REAL CAPITAL CAPABILITY PROHIBITED');
}

function roleGuard_(role) {
  const allowed = ['PRODUCER', 'COURIER', 'WITNESS'];
  if (allowed.indexOf(role) < 0) throw new Error('UNAUTHORIZED ROLE');
  assertPaperOnly_();
}

function failure_(actor, surface, evidence) {
  try {
    ensureLabel_(HMBM.LABELS.FAILURE);
    PropertiesService.getScriptProperties().setProperties({
      LAST_FAILURE_ACTOR: actor,
      LAST_FAILURE_SURFACE: surface,
      LAST_FAILURE_EVIDENCE: String(evidence),
      LAST_FAILURE_STATE: PropertiesService.getScriptProperties().getProperty('HMBM_CANONICAL_STATE') || HMBM.CANONICAL_START
    }, false);
  } catch (_) {}
  return new Error('HMBM FAILURE [' + actor + '] ' + surface + ': ' + evidence);
}

function removeNamedTriggers_(fn) {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === fn) ScriptApp.deleteTrigger(t);
  });
}

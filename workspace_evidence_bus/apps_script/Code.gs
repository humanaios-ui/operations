/** HumanAIOS Workspace Evidence Bus — Google Apps Script relay.
 *
 * Boundary: transport/persistence only. This script cannot grant Z2/Z3 authority,
 * cannot place trades, and never writes Gmail bodies or contact PII to GitHub.
 */

const BUS_VERSION = '0.1.0';

function doGet() {
  return jsonResponse_({ok: true, service: 'HumanAIOS Workspace Evidence Bus', version: BUS_VERSION});
}

function doPost(e) {
  try {
    const request = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    requireRelayToken_(request.relay_token);
    delete request.relay_token;

    if (request.action === 'persist_event') {
      return jsonResponse_(persistEvent_(request.event));
    }
    if (request.action === 'create_reference_draft') {
      return jsonResponse_(createReferenceDraft_(request));
    }
    return jsonResponse_({ok: false, error: 'unsupported_action'});
  } catch (err) {
    return jsonResponse_({ok: false, error: String(err && err.message ? err.message : err)});
  }
}

function persistEvent_(event) {
  validateEnvelope_(event);
  const folder = getEvidenceFolder_();
  const key = safeName_(event.idempotency_key);
  const existing = folder.getFilesByName(key + '.receipt.json');
  if (existing.hasNext()) {
    const prior = JSON.parse(existing.next().getBlob().getDataAsString('UTF-8'));
    prior.replayed = true;
    return prior;
  }

  const canonical = stableStringify_(event);
  const computedPayloadHash = sha256Hex_(stableStringify_(event.payload || {}));
  if (computedPayloadHash !== event.payload_hash) {
    throw new Error('payload_hash_mismatch');
  }

  const eventFile = folder.createFile(key + '.event.json', canonical, MimeType.PLAIN_TEXT);
  const writeHash = sha256Hex_(canonical);
  const readBack = eventFile.getBlob().getDataAsString('UTF-8');
  const readHash = sha256Hex_(readBack);
  if (writeHash !== readHash) {
    eventFile.setTrashed(true);
    throw new Error('read_back_hash_mismatch');
  }

  const receipt = {
    ok: true,
    bus_version: BUS_VERSION,
    event_id: event.event_id,
    idempotency_key: event.idempotency_key,
    drive_file_id: eventFile.getId(),
    artifact_sha256: readHash,
    payload_hash: event.payload_hash,
    observed_at: new Date().toISOString(),
    authority_effect: 'NONE',
    replayed: false
  };
  const receiptText = stableStringify_(receipt);
  folder.createFile(key + '.receipt.json', receiptText, MimeType.PLAIN_TEXT);
  return receipt;
}

function createReferenceDraft_(request) {
  if (!request.to || !request.reference_id || !request.opportunity_id) {
    throw new Error('reference_draft_missing_fields');
  }
  const subject = '[HumanAIOS Reference] ' + request.reference_id + ' | Verification + Current Status';
  const body = [
    'REFERENCE CONTEXT',
    'Opportunity: ' + request.opportunity_id,
    '',
    'VERIFY',
    'Reply naturally, or use any of:',
    'CONTACT CURRENT',
    'CONTACT UPDATE',
    'REFERENCE ' + request.opportunity_id + ': YES / NO',
    '',
    'OPTIONAL ENGAGEMENT',
    'REFERENCE ONLY',
    'OCCASIONAL HUMANAIOS UPDATES',
    'INTERESTED IN REVIEW / RESEARCH PARTICIPATION',
    '',
    'No participation beyond the explicit choice in your reply is implied.'
  ].join('\n');
  const draft = GmailApp.createDraft(request.to, subject, body);
  return {ok: true, draft_id: draft.getId(), reference_id: request.reference_id, sent: false};
}

function validateEnvelope_(event) {
  const required = ['event_id','event_type','subject_ref','actor_ref','source_system','source_ref',
    'observed_at','idempotency_key','state_version','previous_event_hash','payload_hash',
    'privacy_class','authority_effect'];
  required.forEach(function(k) {
    if (!(k in event)) throw new Error('missing_' + k);
  });
  if (event.authority_effect !== 'NONE' && event.authority_effect !== 'Z1' &&
      event.authority_effect !== 'Z2_REQUIRED' && event.authority_effect !== 'Z3_REQUIRED') {
    throw new Error('invalid_authority_effect');
  }
  if (event.event_type === 'HMBM_EPOCH') {
    if (!event.payload || event.payload.paper_only !== true) throw new Error('hmbm_requires_paper_only');
    const forbidden = ['private_key','seed_phrase','wallet_secret','execute_real_trade','real_capital'];
    forbidden.forEach(function(k) {
      if (k in event.payload) throw new Error('hmbm_forbidden_field_' + k);
    });
  }
}

function getEvidenceFolder_() {
  const id = PropertiesService.getScriptProperties().getProperty('EVIDENCE_FOLDER_ID');
  if (!id) throw new Error('EVIDENCE_FOLDER_ID_not_configured');
  return DriveApp.getFolderById(id);
}

function requireRelayToken_(supplied) {
  const expected = PropertiesService.getScriptProperties().getProperty('RELAY_TOKEN');
  if (!expected || !supplied || supplied !== expected) throw new Error('unauthorized');
}

function stableStringify_(value) {
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return '[' + value.map(stableStringify_).join(',') + ']';
  const keys = Object.keys(value).sort();
  return '{' + keys.map(function(k) { return JSON.stringify(k) + ':' + stableStringify_(value[k]); }).join(',') + '}';
}

function sha256Hex_(text) {
  const bytes = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, text, Utilities.Charset.UTF_8);
  return bytes.map(function(b) {
    const v = b < 0 ? b + 256 : b;
    return ('0' + v.toString(16)).slice(-2);
  }).join('');
}

function safeName_(s) {
  return String(s).replace(/[^A-Za-z0-9._-]/g, '_').slice(0, 180);
}

function jsonResponse_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

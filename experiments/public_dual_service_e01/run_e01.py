#!/usr/bin/env python3
"""HumanAIOS E0.1 OFFLINE CORRECTION TEST. Not a deployed system or new authority.

Core policy: observations are evidence-bearing and advisory. This is a bounded
reference evaluator, not an admission or authorization service. No network I/O.
All fixture expectations remain self-authored pending independent review.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent
CLOCK = datetime.fromisoformat('2026-11-18T12:00:00+00:00')
GIT_BLOB_SHA = 'c8d506434a3f13a97fc0a98d9fc882f1083e6691'
PRIVATE_SENTINEL = 'SYNTHETIC_PRIVATE_SENTINEL'
HELD = {'SOURCE_UNAVAILABLE', 'INVALID_SOURCE_TIME', 'FUTURE_SOURCE_TIME', 'STALE_SOURCE', 'DISPUTED_SOURCE'}
SECURITY_DECISIONS = {'AFFECTED_BY_THIS_ADVISORY', 'NOT_AFFECTED_BY_THIS_ADVISORY', 'UNKNOWN_PACKAGE', 'UNKNOWN_VERSION'} | HELD
COMPASS_DECISIONS = {'RELEVANT_NOT_ELIGIBILITY_ASSESSED', 'NEEDS_PROOF', 'NOT_RELEVANT'} | HELD
RFC3339 = re.compile(r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)$')
VERSION = re.compile(r'^\d+\.\d+\.\d+$')
BAD_CLAIMS = re.compile(r'\b(?:guaranteed safe|all systems (?:are )?safe|no vulnerabilities|you (?:are|definitely) eligible|automatically enrolled|auto[- ]?enroll(?:ed|ment)?|grant(?:ed)? write authority)\b', re.I)


def load(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding='utf-8'))


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_clock(value: Any, now: datetime = CLOCK) -> tuple[str, datetime | None]:
    """Explicit RFC3339 enforcement even if JSON Schema FormatChecker is absent."""
    if not isinstance(value, str) or not RFC3339.fullmatch(value):
        return 'INVALID_SOURCE_TIME', None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return 'INVALID_SOURCE_TIME', None
    if dt.utcoffset() is None:
        return 'INVALID_SOURCE_TIME', None
    normalized = dt.astimezone(timezone.utc)
    if normalized > now:
        return 'FUTURE_SOURCE_TIME', None
    if now - normalized > timedelta(days=90):
        return 'STALE_SOURCE', normalized
    return 'CURRENT', normalized


def semver_exact(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str) or not VERSION.fullmatch(value):
        return None
    try:
        return tuple(map(int, value.split('.')))
    except ValueError:
        return None


def safe_url(raw: Any) -> str | None:
    if not isinstance(raw, str) or len(raw) > 500:
        return None
    try:
        p = urlsplit(raw)
        if (p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None, 443)
                or p.query or p.fragment or p.hostname.lower() in {'localhost', '127.0.0.1'}):
            return None
        return raw
    except ValueError:
        return None


def relevant_learning_goal(value: Any) -> bool:
    """Small documented token baseline, not broad language understanding."""
    if not isinstance(value, str) or not 1 <= len(value) <= 120:
        return False
    words = set(re.findall(r'[a-z]+', value.lower()))
    topic = bool({'cybersecurity', 'cyber'} & words)
    level = bool({'beginner', 'basic', 'basics', 'foundational', 'intro', 'introduction'} & words)
    unsupported = bool({'advanced', 'offensive', 'live', 'paid', 'lab'} & words)
    return topic and level and not unsupported


def choose_status(service: str, data: dict, source: dict, observations: list[dict]) -> tuple[str, str, str]:
    """Status selection is a rule, NOT an independently validated gold standard."""
    if data.get('simulate_unavailable') is True:
        return 'SOURCE_UNAVAILABLE', 'The frozen record is unavailable; no conclusion.', 'Obtain an authentic source record.'
    time_status, _ = validate_clock(data.get('simulate_observed_at', source.get('observed_at')))
    if time_status != 'CURRENT':
        reasons = {
            'INVALID_SOURCE_TIME': 'Source timestamp invalid; evidence withheld.',
            'FUTURE_SOURCE_TIME': 'Source date is in the future relative to test clock; evidence withheld.',
            'STALE_SOURCE': 'Source snapshot older than the declared 90-day test window.'
        }
        return time_status, reasons[time_status], 'Retrieve a valid, independently dated source.'
    if service == 'integrity':
        if len({x.get('affected_before') for x in observations}) > 1:
            return 'DISPUTED_SOURCE', 'Affected-version thresholds conflict; do not conclude.', 'Check the authoritative advisory revision.'
        if data.get('ecosystem') != source.get('ecosystem') or data.get('package') != source.get('package'):
            return 'UNKNOWN_PACKAGE', 'The requested package identity does not match the advisory.', 'Verify package and ecosystem identifiers.'
        version, fixed = semver_exact(data.get('version')), semver_exact(source.get('affected_before'))
        if version is None or fixed is None:
            return 'UNKNOWN_VERSION', 'Exact release version needed; prereleases not assessed.', 'Verify a full stable version from the package inventory.'
        if version < fixed:
            return 'AFFECTED_BY_THIS_ADVISORY', 'This version is listed in this one advisory; deployment exposure is unassessed.', 'Review the advisory and plan an approved update.'
        return 'NOT_AFFECTED_BY_THIS_ADVISORY', 'Not affected by this specific advisory only; other vulnerabilities and actual safety remain unknown.', 'Check other advisories and the real dependency graph.'

    if len({x.get('course_price_usd') for x in observations}) > 1:
        return 'DISPUTED_SOURCE', 'The course price claims conflict; access and price are unresolved.', 'Check current first-party course terms.'
    if not relevant_learning_goal(data.get('goal')):
        return 'NOT_RELEVANT', 'No supported match to foundational cybersecurity learning goal.', 'Clarify the skill and course level needed.'
    if data.get('demand_guaranteed_credential') is True:
        return 'NEEDS_PROOF', 'The provided source does not guarantee a credential or enrollment.', 'Verify credential terms with the provider.'
    money = data.get('budget_usd')
    if type(money) not in (float, int) or not math.isfinite(money) or money < 0:
        return 'NEEDS_PROOF', 'Missing or invalid budget; cost fit cannot be assessed.', 'Provide a valid nonnegative budget.'
    if money < source.get('course_price_usd', float('inf')):
        return 'NEEDS_PROOF', 'Budget does not support the listed course price.', 'Confirm actual cost and personal constraints.'
    return 'RELEVANT_NOT_ELIGIBILITY_ASSESSED', 'Source indicates a relevant course; personal eligibility and access are not assessed.', 'Open the official course page and verify terms.'


def build_output(case: dict, frozen: dict) -> dict:
    """Only read synthetic case and frozen source; ignore untrusted source_note."""
    service = case['service']
    if service not in ('integrity', 'compass'):
        raise ValueError('Unknown E0.1 service')
    data = case['input']
    if not isinstance(data, dict):
        raise ValueError('Case input must be an object')
    source = frozen['sources']['security' if service == 'integrity' else 'resource']
    raw_url = source.get('source_url') or source['source_urls'][0]
    url = safe_url(raw_url)
    if not url:
        raise ValueError('Invalid frozen source locator; cannot emit observation')
    source_ts_status, _ = validate_clock(source.get('observed_at'))
    if source_ts_status == 'INVALID_SOURCE_TIME' or source_ts_status == 'FUTURE_SOURCE_TIME':
        raise ValueError('Invalid actual source timestamp; cannot emit Oracle source record')
    observations = [source]
    if data.get('simulate_duplicate') is True:
        observations.append(copy.deepcopy(source))
    if service == 'integrity' and 'simulate_conflicting_fix' in data:
        alt = copy.deepcopy(source)
        alt['affected_before'] = data['simulate_conflicting_fix']
        observations.append(alt)
    if service == 'compass' and 'simulate_conflicting_price_usd' in data:
        alt = copy.deepcopy(source)
        alt['course_price_usd'] = data['simulate_conflicting_price_usd']
        observations.append(alt)
    independent = {digest(o): o for o in observations}
    status, rationale, next_step = choose_status(service, data, source, list(independent.values()))
    evidence_count = 0 if status in {'SOURCE_UNAVAILABLE', 'INVALID_SOURCE_TIME', 'FUTURE_SOURCE_TIME'} else len(independent)
    sidecar = {
        'case_id': case['id'], 'service': service, 'decision': status, 'source_id': source['source_id'],
        'source_snapshot_sha256': digest(source), 'evidence_count': evidence_count,
        'evidence_links': [] if evidence_count == 0 else [url],
        'rationale': rationale, 'next_step': next_step,
        'action_class': 'READ_ONLY', 'source_quality': 'MANUALLY_TRANSCRIBED_UNATTESTED'
    }
    data_for_digest = {k: v for k, v in data.items() if k != 'source_note'}
    observation = {
        'schema_version': '1.0',
        'observation_id': 'E01-' + digest({'case':case['id'], 'input':data_for_digest, 'decision':status})[:24],
        'oracle_id': 'humanaios-offline-e01-correction-probe',
        'source': {'substrate':'web_research', 'locator':url, 'content_sha256':digest(source)},
        'as_of': source['observed_at'], 'recorded_at': CLOCK.isoformat().replace('+00:00','Z'),
        'observation': f"{case['id']} | {status} | {rationale}", 'subject_ref':source['source_id'],
        'transformation': {'component':'offline_e01_probe','version':'0.1.1', 'producer_ref':'test-only'},
        'advisory_only': True, 'can_authorize': False, 'authority_effect': 'NONE'
    }
    return {'sidecar':sidecar, 'observation':observation}


def validators() -> tuple[Draft202012Validator, Draft202012Validator, str]:
    p = ROOT / 'oracle_observation_v1.schema.json'
    raw = p.read_bytes()
    blob_sha = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    if blob_sha != GIT_BLOB_SHA:
        raise ValueError('Oracle schema blob mismatch')
    repo_schema = json.loads(raw)
    sidecar_schema = load('sidecar_e01.schema.json')
    Draft202012Validator.check_schema(repo_schema)
    Draft202012Validator.check_schema(sidecar_schema)
    checker = FormatChecker()
    return Draft202012Validator(repo_schema, format_checker=checker), Draft202012Validator(sidecar_schema, format_checker=checker), blob_sha


def audit_output(case: dict, output: dict, frozen: dict, oracle_validator: Draft202012Validator, sidecar_validator: Draft202012Validator) -> list[str]:
    """Independent *mechanical* assertions about OUTPUT content; mutation-tested.

    These are bounded invariants, NOT proof against every possible harmful sentence
    or all runtime data leaks. No safety booleans from the evaluator are consulted.
    """
    errors = []
    try:
        oracle_validator.validate(output['observation'])
    except Exception as exc:
        errors.append('oracle_schema:' + type(exc).__name__)
    try:
        sidecar_validator.validate(output['sidecar'])
    except Exception as exc:
        errors.append('sidecar_schema:' + type(exc).__name__)
    obs = output.get('observation', {})
    side = output.get('sidecar', {})
    for key in ('as_of','recorded_at'):
        state, _ = validate_clock(obs.get(key))
        if state not in {'CURRENT','STALE_SOURCE'}:
            errors.append('bad_' + key)
    for key, expected in [('advisory_only',True),('can_authorize',False),('authority_effect','NONE')]:
        if obs.get(key) != expected or type(obs.get(key)) is not type(expected):
            errors.append('authority:' + key)
    if side.get('action_class') != 'READ_ONLY':
        errors.append('sidecar_action')
    # Check the actual claims and explanation strings, not self-reported flags.
    text_content = ' '.join(str(x) for x in [side.get('decision',''), side.get('rationale',''), side.get('next_step',''), obs.get('observation','')])
    if BAD_CLAIMS.search(text_content):
        errors.append('false_or_unauthorized_claim')
    if PRIVATE_SENTINEL in canonical(output).decode('utf-8'):
        errors.append('synthetic_private_marker_echo')
    if str(case['input'].get('source_note','')) and str(case['input'].get('source_note')) in canonical(output).decode('utf-8'):
        errors.append('untrusted_source_note_echo')
    if side.get('case_id') != case['id'] or side.get('service') != case['service']:
        errors.append('case_mismatch')
    if side.get('decision') != case['expected']:
        errors.append('frozen_expected_mismatch')
    if obs.get('observation') != f"{case['id']} | {side.get('decision')} | {side.get('rationale')}":
        errors.append('observation_sidecar_mismatch')
    source = frozen['sources']['security' if case['service'] == 'integrity' else 'resource']
    source_url = source.get('source_url') or source['source_urls'][0]
    if side.get('source_id') != source['source_id'] or side.get('source_snapshot_sha256') != digest(source):
        errors.append('source_mismatch')
    if obs.get('source',{}).get('content_sha256') != digest(source) or obs.get('source',{}).get('locator') != source_url:
        errors.append('oracle_source_mismatch')
    if any(link != source_url for link in side.get('evidence_links',[])):
        errors.append('bad_evidence_link')
    expected_evidence = 0 if side.get('decision') in {'SOURCE_UNAVAILABLE','INVALID_SOURCE_TIME','FUTURE_SOURCE_TIME'} else (2 if side.get('decision') == 'DISPUTED_SOURCE' else 1)
    if side.get('evidence_count') != expected_evidence or len(side.get('evidence_links',[])) != (0 if expected_evidence==0 else 1):
        errors.append('evidence_mismatch')
    if side.get('decision') == 'NOT_AFFECTED_BY_THIS_ADVISORY' and 'specific advisory only' not in side.get('rationale',''):
        errors.append('missing_advisory_scope')
    if side.get('decision') == 'RELEVANT_NOT_ELIGIBILITY_ASSESSED' and 'not assessed' not in side.get('rationale',''):
        errors.append('missing_eligibility_scope')
    if side.get('decision') not in (SECURITY_DECISIONS if case['service']=='integrity' else COMPASS_DECISIONS):
        errors.append('out_of_domain_decision')
    return sorted(set(errors))


def all_cases() -> list[dict]:
    original = load('frozen_cases.json')['cases']
    added = load('e01_additional_cases.json')['cases']
    cases = original + added
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate case id')
    return cases


def main() -> int:
    oracle_validator, sidecar_validator, blob_sha = validators()
    frozen = load('frozen_sources.json')
    cases = all_cases()
    results = []
    for case in cases:
        attempt = build_output(case, frozen)
        repeat = build_output(case, frozen)
        errs = audit_output(case, attempt, frozen, oracle_validator, sidecar_validator)
        if attempt['sidecar']['decision'] != case['expected']:
            errs.append('gold_mismatch')
        if attempt != repeat:
            errs.append('non_deterministic')
        results.append({'id':case['id'], 'service':case['service'], 'scenario':case['scenario'], 'expected':case['expected'], 'actual':attempt['sidecar']['decision'], 'pass':not errs, 'errors':errs, 'output':attempt})
    n_pass = sum(r['pass'] for r in results)
    report = {
        'protocol':'humanaios.dual-service-e01.v0.1.1',
        'test_clock':CLOCK.isoformat().replace('+00:00','Z'),
        'original_e0_cases_unchanged_sha256':hashlib.sha256((ROOT/'frozen_cases.json').read_bytes()).hexdigest(),
        'original_e0_sources_unchanged_sha256':hashlib.sha256((ROOT/'frozen_sources.json').read_bytes()).hexdigest(),
        'additional_cases_sha256':hashlib.sha256((ROOT/'e01_additional_cases.json').read_bytes()).hexdigest(),
        'original_oracle_schema_blob_sha1':blob_sha,
        'sidecar_schema_sha256':hashlib.sha256((ROOT/'sidecar_e01.schema.json').read_bytes()).hexdigest(),
        'total':len(results), 'passed':n_pass, 'failed':len(results)-n_pass,
        'status':'SELF_CHECK_PASS_REVIEW_REQUIRED' if n_pass==len(results) else 'SELF_CHECK_FAIL',
        'review_status':'NOT_INDEPENDENTLY_REVIEWED', 'real_app_integration':'NOT_RUN',
        'real_user_testing':'NOT_RUN', 'network_calls':0,
        'results':results
    }
    (ROOT/'result_e01.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(f"{report['status']} {n_pass}/{len(results)}")
    for r in results:
        print(f"  {r['id']} {r['actual']:<41} {'PASS' if r['pass'] else ','.join(r['errors'])}")
    return 0 if n_pass==len(results) else 1

if __name__ == '__main__':
    raise SystemExit(main())

"""Stateless private bridge to the saved job application skill. No external I/O."""
from copy import deepcopy
from html import escape
import json

HELD = {'LINK_FAILED_404', 'ROLE_NOT_LISTED', 'SOURCE_UNAVAILABLE', 'RECHECK_REQUIRED'}


def prepare(record, source_rows=()):
    if not isinstance(record, dict) or len(json.dumps(record).encode()) > 100000:
        raise ValueError('Invalid application')
    app = deepcopy(record)
    for key in ('application_id', 'employer', 'role', 'job_text', 'job_source'):
        if not isinstance(app.get(key), str) or not app[key].strip():
            raise ValueError('Missing job field')
    evidence, requirements = app.get('evidence'), app.get('requirements')
    if not isinstance(evidence, list) or not isinstance(requirements, list) or not 1 <= len(requirements) <= 100 or len(evidence) > 100:
        raise ValueError('Invalid evidence map')
    indexed = {}
    for row in evidence:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip() for k in ('id', 'claim', 'source')):
            raise ValueError('Evidence needs id, claim and source')
        if row['id'] in indexed or row.get('state') not in {'DOCUMENTED', 'USER_ATTESTED', 'IN_PROGRESS'}:
            raise ValueError('Invalid evidence state or duplicate')
        indexed[row['id']] = row
    seen = set()
    for row in requirements:
        if not isinstance(row, dict) or not all(isinstance(row.get(k), str) and row[k].strip() for k in ('id', 'requirement')):
            raise ValueError('Invalid requirement')
        if row['id'] in seen:
            raise ValueError('Duplicate requirement')
        seen.add(row['id'])
        if row.get('kind') not in {'duty', 'minimum', 'preferred'} or row.get('status') not in {'SUPPORTED', 'PARTIAL', 'UNKNOWN', 'CONTRADICTED'} or row.get('mapping') not in {'DIRECT', 'TRANSFERABLE', 'GAP'}:
            raise ValueError('Invalid classification')
        refs = row.get('evidence_ids', [])
        if not isinstance(refs, list) or any(not isinstance(x, str) or x not in indexed for x in refs):
            raise ValueError('Broken evidence link')
        if row['status'] in {'SUPPORTED', 'PARTIAL'} and (not refs or row['mapping'] == 'GAP'):
            raise ValueError('Support requires evidence')
        if row['status'] == 'UNKNOWN' and (refs or row['mapping'] != 'GAP'):
            raise ValueError('Unknown must stay a gap')
        for key in ('gap', 'proposed_execution', 'deliverable', 'success_check'):
            if not isinstance(row.get(key, ''), str):
                raise ValueError('Invalid text')
    status = app.get('source_verification_status', 'UNVERIFIED')
    if not isinstance(status, str) or status not in HELD | {'UNVERIFIED'}:
        raise ValueError('Live source verification unsupported')
    # A known catalog hold overrides a user import that tries to clear it.
    for source in source_rows:
        if isinstance(source, dict) and source.get('url') == app['job_source'] and source.get('source_verification_status') in HELD:
            status = source['source_verification_status']
    app.update(source_verification_status=status, availability='UNVERIFIED',
               external_state='NOT_SUBMITTED', authority='NONE',
               source_hold=status in HELD, review_state='DRAFT_REQUIRES_HUMAN_REVIEW',
               evidence_verification='USER_SUPPLIED_NOT_INDEPENDENTLY_CHECKED')
    rows = []
    for row in requirements:
        proof = '; '.join(indexed[x]['claim'] + ' [source: ' + indexed[x]['source'] + ']' for x in row.get('evidence_ids', [])) or 'Not established in supplied evidence'
        cells = [row['requirement'], row['status'] + ' / ' + row['mapping'] + ': ' + proof,
                 row.get('proposed_execution', '') + '\nDeliverable: ' + row.get('deliverable', '') + '\nCheck: ' + row.get('success_check', '')]
        rows.append('<tr>' + ''.join('<td>' + escape(x) + '</td>' for x in cells) + '</tr>')
    html = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Private evidence map</title><style>body{font:11pt Arial;margin:32px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:8px;text-align:left;white-space:pre-wrap}tr{break-inside:avoid}</style><body><h1>' + escape(app['employer'] + ' — ' + app['role']) + '</h1><p>PRIVATE WORKING MAP · NOT A FINISHED RESUME · NOT SUBMITTED · Availability UNVERIFIED</p><h2>Requirement to Evidence to Execution</h2><table><tr><th>Requirement</th><th>Evidence</th><th>Proposed execution</th></tr>' + ''.join(rows) + '</table></body></html>'
    prompt = 'Use $map-job-application with the attached application.json. Preserve original job text, sources and gaps. Load the current master resume and approved examples. Build the specialized resume and matching cover letter in Word and PDF. Include objective, requirement/evidence/execution table, quality execution model, experience boundary, selected project evidence, short chronology, education/research. Run the saved checker and inspect every rendered page. The HTML is only a working evidence map. Source status: ' + status + '. Availability UNVERIFIED. Do not submit or contact anyone.'
    return {'application': app, 'evidence_map_html': html, 'skill_handoff': prompt}

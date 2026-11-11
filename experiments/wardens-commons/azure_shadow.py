"""Off by default, redacted, read-only governance observation toward Azure.

This exporter is NOT an Azure deployment or a campaign save/ballot writer.
Only enable after explicit consent/privacy review and an approved collector exists.
"""
import hashlib
import hmac
import json
import sqlite3
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED = {'roster_updated', 'proposed', 'comment_added', 'ballot_open',
           'voted', 'ballot_closed', 'rule_applied'}


def _pseudonym(key: bytes, value: str) -> str:
    return hmac.new(key, value.encode(), hashlib.sha256).hexdigest()


def project_room(db_path, room: str, privacy_key: str, enabled=False):
    """Read only. Never exports player identities, room codes, titles, or comments."""
    if not enabled:
        return []
    if not isinstance(privacy_key, str) or len(privacy_key) < 32:
        raise ValueError('privacy HMAC key required')
    connection = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute('SELECT seq,kind,ref,digest FROM events WHERE room=? ORDER BY seq', (room,))
        key = privacy_key.encode()
        return [{
            'schema': 'wardens_council_observation.v1',
            'room_hmac': _pseudonym(key, room),
            'proposal_hmac': _pseudonym(key, room + ':' + str(r['ref'])),
            'event_seq': r['seq'],
            'event_type': r['kind'],
            'event_digest': r['digest'],
        } for r in rows if r['kind'] in ALLOWED]
    finally:
        connection.close()


def send_shadow(endpoint: str, credential: str, observations: list[dict], enabled=False):
    """Optional egress to an APPROVED Azure HTTPS ingestion endpoint; not deployed by this module."""
    if not enabled or not observations:
        return 0
    parsed = urlparse(endpoint)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        raise ValueError('approved https collector URL required')
    if not credential or len(credential) < 20:
        raise ValueError('collector credential required')
    payload = json.dumps({'observations': observations}, separators=(',', ':')).encode()
    if len(payload) > 1024 * 1024:
        raise ValueError('observation batch exceeds 1MiB')
    request = Request(endpoint, data=payload, method='POST', headers={
        'Content-Type': 'application/json', 'Authorization': 'Bearer ' + credential,
        'User-Agent': 'wardens-council-shadow/0.1',
    })
    with urlopen(request, timeout=5) as response:
        if response.status not in (200, 201, 202, 204):
            raise RuntimeError('collector refused batch')
    return len(observations)

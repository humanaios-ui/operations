"""Independent file-backed artifact readback; never trusts agent-reported values."""
import hashlib
import json
from pathlib import Path
from oracle import evaluate


def readback(manifest, store):
    """Manifest has numeric requirements and artifact_id; store is a local directory.
    Missing after confirmed write is FAIL; missing without confirmation is UNKNOWN.
    """
    artifact_id = manifest.get('artifact_id')
    if not isinstance(artifact_id, str) or not artifact_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in artifact_id):
        return {'verdict':'UNKNOWN','reasons':['invalid_artifact_id'],'readback_sha256':None}
    root = Path(store)
    target = root / (artifact_id + '.json')
    if not root.is_dir():
        return {'verdict':'UNKNOWN','reasons':['artifact_store_unavailable'],'readback_sha256':None}
    if target.is_symlink():
        return {'verdict':'UNKNOWN','reasons':['symlink_artifact_rejected'],'readback_sha256':None}
    try:
        payload = target.read_bytes()
    except FileNotFoundError:
        state = 'false' if manifest.get('write_attempt_confirmed') is True else 'unknown'
        result = evaluate({**manifest,'artifact_present':state,'actual_value':''})
        return {**result,'readback_sha256':None}
    except OSError:
        return {'verdict':'UNKNOWN','reasons':['artifact_read_error'],'readback_sha256':None}
    digest = hashlib.sha256(payload).hexdigest()
    try:
        data = json.loads(payload)
        if not isinstance(data,dict) or data.get('artifact_id') != artifact_id:
            raise ValueError('invalid artifact content')
        actual = data['value']
    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return {'verdict':'UNKNOWN','reasons':['invalid_artifact_content'],'readback_sha256':digest}
    result = evaluate({**manifest,'artifact_present':'true','actual_value':actual})
    return {**result,'readback_sha256':digest}

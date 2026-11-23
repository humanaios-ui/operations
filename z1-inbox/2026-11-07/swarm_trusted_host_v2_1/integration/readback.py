"""Independent file-backed artifact readback; never trusts agent-reported values."""
import errno
import hashlib
import json
import os
import stat
from pathlib import Path
from oracle import evaluate

_NO_FOLLOW = getattr(os, "O_NOFOLLOW", 0)
_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
_NONBLOCK = getattr(os, "O_NONBLOCK", 0)
_DIR_FD_OPEN = os.open in os.supports_dir_fd  # evaluated once: descriptor-relative open is available


class _ReadRefused(Exception):
    """Carries the UNKNOWN reason for a read that must not be trusted."""


def _read_artifact(store, filename):
    """Read one artifact WITHOUT following a symlink and without a check-then-read gap.

    The store directory is opened with O_NOFOLLOW (so the store itself may not be a link), and the artifact is opened
    relative to that descriptor with O_NOFOLLOW|O_NONBLOCK, then fstat-ed on the descriptor that is read: a link
    swapped in after any earlier check is refused, and a FIFO or device cannot block the reader. Links ABOVE the store
    directory are trusted as given (the caller supplies the path; the bridge builds it from the verified host root).
    Raises FileNotFoundError when the artifact is absent."""
    if not _NO_FOLLOW or not _DIR_FD_OPEN:
        raise _ReadRefused("artifact_no_follow_unsupported")  # fail closed rather than fall back to a following read
    try:
        dir_fd = os.open(store, os.O_RDONLY | os.O_DIRECTORY | _NO_FOLLOW | _CLOEXEC)
    except OSError as exc:
        if exc.errno == errno.ELOOP or (exc.errno == errno.ENOTDIR and Path(store).is_symlink()):
            raise _ReadRefused("artifact_store_symlink_rejected") from exc
        raise _ReadRefused("artifact_store_unavailable") from exc
    try:
        try:
            fd = os.open(filename, os.O_RDONLY | _NO_FOLLOW | _NONBLOCK | _CLOEXEC, dir_fd=dir_fd)
        except FileNotFoundError:
            raise
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise _ReadRefused("symlink_artifact_rejected") from exc
            raise _ReadRefused("artifact_read_error") from exc
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise _ReadRefused("artifact_read_error")
            with os.fdopen(fd, "rb") as handle:
                fd = None
                return handle.read()
        finally:
            if fd is not None:
                os.close(fd)
    finally:
        os.close(dir_fd)


def readback(manifest, store):
    """Manifest has numeric requirements and artifact_id; store is a local directory.
    Missing after confirmed write is FAIL; missing without confirmation is UNKNOWN.
    """
    artifact_id = manifest.get('artifact_id')
    if not isinstance(artifact_id, str) or not artifact_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in artifact_id):
        return {'verdict':'UNKNOWN','reasons':['invalid_artifact_id'],'readback_sha256':None}
    root = Path(store)
    if not root.is_dir():
        return {'verdict':'UNKNOWN','reasons':['artifact_store_unavailable'],'readback_sha256':None}
    try:
        payload = _read_artifact(root, artifact_id + '.json')
    except FileNotFoundError:
        state = 'false' if manifest.get('write_attempt_confirmed') is True else 'unknown'
        result = evaluate({**manifest,'artifact_present':state,'actual_value':''})
        return {**result,'readback_sha256':None}
    except _ReadRefused as refused:
        return {'verdict':'UNKNOWN','reasons':[str(refused)],'readback_sha256':None}
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

"""Offline reference: host-only numeric writer and Ed25519-chained evidence log.

Never expose the HostWriter object, private key or store paths to an agent. In a
production test, run it under a separate OS identity behind an approved RPC.
The code here is a prototype, NOT proof of OS isolation or human approval.
"""
from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import errno
import os
import re
import secrets
import stat
import threading
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from .pins import FILES, file_sha256
from .responses import KINDS, MAX_RAW, TRANSPORT, parse_response, pinned_model, slot

IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
VALUE = re.compile(r"^-?(0|[1-9][0-9]{0,8})(\.[0-9]{1,6})?$")
GENESIS = "0" * 64

class EvidenceError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest(value):
    return sha_bytes(canonical(value))


def pub_bytes(key):
    return key.public_key().public_bytes(encoding=serialization.Encoding.Raw,
                                        format=serialization.PublicFormat.Raw)


def public_fingerprint(key):
    return sha_bytes(pub_bytes(key))


def now():
    return datetime.now(timezone.utc).isoformat()


HEX64 = re.compile(r"^[a-f0-9]{64}$")
LABEL = re.compile(r"^[A-Za-z0-9._:/-]{1,128}$")
PROVIDER_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,128}$")
PIN_LABELS = ("provider", "model_a", "model_b")
PIN_HASHES = ("settings_sha256", "prompts_sha256") + tuple(FILES)


def parse_utc(value, code):
    """Strict timestamp: ISO-8601 with an explicit UTC (zero) offset. Naive or other zones are refused."""
    if not isinstance(value, str):
        raise EvidenceError(code)
    try:
        stamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceError(code) from exc
    if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
        raise EvidenceError(code)
    return stamp


def ident(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise EvidenceError("INVALID_ID")
    return value


def _has_acl(fd):
    """True if the directory carries a POSIX ACL (access or default). ACLs can grant another account access that the
    mode bits do not show, so any ACL on a secured path is refused rather than interpreted."""
    try:
        names = os.listxattr(fd)
    except OSError as exc:
        if exc.errno in (errno.ENOTSUP, errno.ENODATA):  # filesystem without xattrs cannot carry an ACL
            return False
        raise EvidenceError("UNSAFE_DIRECTORY") from exc
    return any(name.startswith("system.posix_acl") for name in names)


def secure_dir(path):
    """Create or validate a private directory by walking from "/" with directory descriptors.

    Every component is opened with O_NOFOLLOW|O_DIRECTORY relative to its already-open parent, and ownership, mode and
    ACL are read from the descriptor that is then used (fstat/fchmod), so a rename or symlink swap after the check
    cannot redirect the check or the chmod. Ancestors must belong to root or the host user and not be writable by
    others (a sticky directory such as /tmp is acceptable). The leaf must be ours and is set to 0700."""
    path = Path(path).absolute()
    parts = path.parts
    if any(part in (".", "..") for part in parts[1:]):
        raise EvidenceError("PATH_NOT_NORMALIZED")
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    euid = os.geteuid()
    fd = os.open(parts[0], flags)
    try:
        for index, name in enumerate(parts[1:], start=1):
            leaf = index == len(parts) - 1
            try:
                try:
                    child = os.open(name, flags, dir_fd=fd)
                except FileNotFoundError:
                    os.mkdir(name, 0o700, dir_fd=fd)  # created by us, so ours and private
                    child = os.open(name, flags, dir_fd=fd)
            except OSError as exc:
                if exc.errno == errno.ELOOP:
                    raise EvidenceError("SYMLINK_PATH") from exc
                if exc.errno == errno.ENOTDIR:  # O_DIRECTORY reports a symlink as ENOTDIR; look without following
                    try:
                        is_link = stat.S_ISLNK(os.stat(name, dir_fd=fd, follow_symlinks=False).st_mode)
                    except OSError:
                        is_link = False
                    raise EvidenceError("SYMLINK_PATH" if is_link else "UNSAFE_DIRECTORY") from exc
                raise EvidenceError("UNSAFE_DIRECTORY") from exc
            os.close(fd)
            fd = child
            info = os.fstat(fd)
            if leaf:
                if info.st_uid != euid:
                    # A pre-existing directory an agent owns would stay renameable and writable by that agent.
                    raise EvidenceError("DIRECTORY_NOT_HOST_OWNED")
            else:
                if info.st_uid not in (0, euid):
                    raise EvidenceError("ANCESTOR_NOT_HOST_OWNED")
                if info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX:
                    raise EvidenceError("ANCESTOR_WRITABLE_BY_OTHERS")
            if _has_acl(fd):
                raise EvidenceError("ACL_PRESENT")
        os.fchmod(fd, 0o700)
        checked = os.fstat(fd)
        try:
            now_there = os.stat(path)  # detects the path having been re-pointed since the walk
        except OSError as exc:
            raise EvidenceError("PATH_CHANGED_DURING_CHECK") from exc
        if (now_there.st_dev, now_there.st_ino) != (checked.st_dev, checked.st_ino):
            raise EvidenceError("PATH_CHANGED_DURING_CHECK")
    finally:
        os.close(fd)
    return path


def new_file(path, contents):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try: Path(path).unlink()
        except OSError: pass
        raise


def open_read_no_follow(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as handle:
        return handle.read()


def check_plan(plan, key):
    required_fields = {
        "task", "run_id", "episode_id", "writer_pubkey_sha256", "allowed_actor",
        "action", "protocol", "non_scored", "tool_policy", "window", "protocol_pins"}
    if not isinstance(plan, dict) or set(plan) not in (required_fields, required_fields | {"role_uids"}):
        raise EvidenceError("PLAN_SCHEMA_INVALID")
    # Optional for historic offline fixtures. Mandatory for any isolated host deployment.
    # These UID bindings are included in the plan hash and signed receipt.
    if "role_uids" in plan:
        roles = plan["role_uids"]
        if (not isinstance(roles, dict) or set(roles) != {"host", "agent_a", "agent_b", "control"}
            or any(type(v) is not int or v < 0 for v in roles.values())
            or any(roles[k] == 0 for k in ("agent_a", "agent_b", "control"))):
            raise EvidenceError("ROLE_UID_POLICY_INVALID")
        if len(set(roles.values())) != 4:
            raise EvidenceError("ROLE_UIDS_NOT_DISTINCT")
    if plan["protocol"] != "SWARM_HOST_V2" or plan["non_scored"] is not True:
        raise EvidenceError("WRONG_PROTOCOL")
    if plan["action"] != "WRITE_NUMERIC_ARTIFACT" or plan["allowed_actor"] != "A" or plan["tool_policy"] not in ("ALLOW", "DENY"):
        raise EvidenceError("WRONG_SCOPE")
    if plan["writer_pubkey_sha256"] != public_fingerprint(key):
        raise EvidenceError("KEY_NOT_PINNED")
    ident(plan["run_id"]); ident(plan["episode_id"])
    window = plan["window"]
    if not isinstance(window, dict) or set(window) != {"not_before", "not_after"}:
        raise EvidenceError("WINDOW_INVALID")
    try:
        start = parse_utc(window["not_before"], "WINDOW_INVALID")
        end = parse_utc(window["not_after"], "WINDOW_INVALID")
    except EvidenceError:
        raise
    if not start < end:
        raise EvidenceError("WINDOW_INVALID")
    pins = plan["protocol_pins"]
    if not isinstance(pins, dict) or set(pins) != set(PIN_LABELS) | set(PIN_HASHES):
        raise EvidenceError("PINS_INVALID")
    if any(not isinstance(pins[k], str) or not LABEL.fullmatch(pins[k]) for k in PIN_LABELS):
        raise EvidenceError("PINS_INVALID")
    if any(not isinstance(pins[k], str) or not HEX64.fullmatch(pins[k]) for k in PIN_HASHES):
        raise EvidenceError("PINS_INVALID")
    if pins["writer_sha256"] != file_sha256(FILES["writer_sha256"]):
        raise EvidenceError("WRITER_CODE_NOT_PINNED")
    if pins["pins_sha256"] != file_sha256(FILES["pins_sha256"]):
        raise EvidenceError("PINS_CODE_NOT_PINNED")
    if pins["responses_sha256"] != file_sha256(FILES["responses_sha256"]):
        raise EvidenceError("RESPONSES_CODE_NOT_PINNED")
    task = plan["task"]
    if not isinstance(task, dict) or set(task) != {"artifact_id", "baseline", "proposed", "min_allowed", "max_allowed", "max_delta"}:
        raise EvidenceError("TASK_SCHEMA_INVALID")
    ident(task["artifact_id"])
    # Decimal oracle validates numeric semantics separately. Here bound size/types.
    if any(not isinstance(task[k], str) or not VALUE.fullmatch(task[k]) for k in (
        "baseline", "proposed", "min_allowed", "max_allowed", "max_delta")):
        raise EvidenceError("TASK_VALUE_INVALID")


class HostWriter:
    def __init__(self, root: Path, private_key: Ed25519PrivateKey, plan: dict, pinned_plan_hash: str):
        check_plan(plan, private_key)
        if digest(plan) != pinned_plan_hash:
            raise EvidenceError("PLAN_NOT_FROZEN")
        self.key = private_key
        self.plan = plan
        self.plan_hash = pinned_plan_hash
        self.root = secure_dir(root)
        # Only ONE writer instance per host root; a long-lived lock FD prevents concurrent writers.
        self.lock_fd = os.open(self.root / ".writer_lock", os.O_CREAT | os.O_RDWR | getattr(os,"O_NOFOLLOW",0), 0o600)
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            os.close(self.lock_fd)
            raise EvidenceError("WRITER_ALREADY_RUNNING") from exc
        self.ep = secure_dir(self.root / ident(plan["run_id"]) / ident(plan["episode_id"]))
        self.events = secure_dir(self.ep / "events")
        self.artifacts = secure_dir(self.ep / "artifacts")
        self.responses = secure_dir(self.ep / "responses")
        if (list(self.events.iterdir()) or list(self.artifacts.iterdir()) or list(self.responses.iterdir())
                or (self.ep / "snapshot.json").exists()):
            raise EvidenceError("EXISTING_EVIDENCE_REJECTED")
        self._lock = threading.Lock()
        self.tip = GENESIS
        self.seq = 0
        self.finished = False
        self.started = False
        self.outcome = None
        self.artifact_sha256 = None
        self.request_id = None
        self.nonce = None
        self.actor_id = None
        self._ledger = []      # signed response ledger, in chain order: [{"actor_id", "detail"}]
        self._slots = set()
        self._provider_ids = set()

    def _event(self, kind, status, *, artifact_sha256=None, observed_utc=None, peer_uid=None,
               detail=None, identity=None):
        self.seq += 1
        actor_id, request_id, nonce = identity if identity is not None else (self.actor_id, self.request_id, self.nonce)
        event = {
            "schema": "humanaios.tool_event.v4", "sequence": self.seq,
            "run_id": self.plan["run_id"], "episode_id": self.plan["episode_id"],
            "plan_sha256": self.plan_hash, "kind": kind, "status": status,
            "actor_id": actor_id, "request_id": request_id,
            "nonce": nonce, "artifact_sha256": artifact_sha256, "detail": detail,
            # Kernel-observed uid of the connection that caused this event (SO_PEERCRED), host-reported.
            "peer_uid": peer_uid,
            "observed_utc": observed_utc if observed_utc is not None else now(), "previous_event_hash": self.tip,
        }
        raw = canonical(event)
        event_hash = sha_bytes(raw)
        new_file(self.events / f"{event_hash}.json", raw)
        self.tip = event_hash
        return event

    def write(self, actor_id, request_id, intent, peer_uid=None):
        with self._lock:
            if self.started or self.finished:
                raise EvidenceError("REPLAY_OR_ALREADY_STARTED")
            if actor_id != self.plan["allowed_actor"]:
                raise EvidenceError("ACTOR_NOT_AUTHORIZED")
            ident(request_id)
            if peer_uid is not None and (type(peer_uid) is not int or peer_uid < 0):
                raise EvidenceError("PEER_UID_INVALID")
            # Enforce the action window BEFORE recording any attempt or writing an artifact.
            # Reuse this observed timestamp in REQUEST_RECORDED; do not add a
            # second now() call that would shift the frozen event sequence.
            observed = now()
            try:
                request_time = parse_utc(observed, "WRITE_TIMESTAMP_INVALID")
                first = parse_utc(self.plan["window"]["not_before"], "WINDOW_INVALID")
                last = parse_utc(self.plan["window"]["not_after"], "WINDOW_INVALID")
            except EvidenceError:
                raise
            if not first <= request_time <= last:
                raise EvidenceError("WRITE_OUTSIDE_WINDOW")
            self.started = True
            self.actor_id, self.request_id, self.nonce = actor_id, request_id, secrets.token_hex(16)
            task = self.plan["task"]
            valid = (isinstance(intent, dict) and set(intent) == {"action", "artifact_id", "value"}
                     and intent["action"] == self.plan["action"]
                     and intent["artifact_id"] == task["artifact_id"]
                     and isinstance(intent["value"], str) and VALUE.fullmatch(intent["value"])
                     and self.plan["tool_policy"] == "ALLOW")
            self._event("REQUEST_RECORDED", "ACCEPTED" if valid else "REJECTED", observed_utc=observed, peer_uid=peer_uid)
            if not valid:
                self.outcome = "NO_ATTEMPT"
                self._event("WRITE_RESULT", self.outcome, peer_uid=peer_uid)
                return {"tool_status": self.outcome, "request_id": request_id}
            artifact_path = self.artifacts / (task["artifact_id"] + ".json")
            try:
                raw = canonical({"artifact_id": task["artifact_id"], "value": intent["value"]})
                new_file(artifact_path, raw)
                readback = open_read_no_follow(artifact_path)
                if readback != raw:
                    raise EvidenceError("READBACK_MISMATCH")
                self.artifact_sha256 = sha_bytes(readback)
                self.outcome = "COMPLETED"
            except Exception:
                # An interrupted/failed write must NEVER be reported as completed.
                self.outcome = "FAILED"
                self.artifact_sha256 = None
            self._event("WRITE_RESULT", self.outcome, artifact_sha256=self.artifact_sha256, peer_uid=peer_uid)
            return {"tool_status": self.outcome, "request_id": request_id}

    def record_response(self, actor_id, kind, raw_response, transport_status, provider_request_id,
                        model_id, attempt, peer_uid=None):
        """Record one model response relayed by the orchestrator (control channel only).

        The HOST hashes the raw bytes, stores them content-addressed and parses the claim or ballot itself.
        The caller asserts nothing but the raw bytes and metadata. Refusals change no state."""
        with self._lock:
            if self.finished:
                raise EvidenceError("ALREADY_FINALIZED")
            if actor_id not in ("A", "B"):
                raise EvidenceError("RESPONSE_ACTOR_INVALID")
            if kind not in KINDS:
                raise EvidenceError("RESPONSE_KIND_INVALID")
            if actor_id not in KINDS[kind][2]:
                raise EvidenceError("RESPONSE_ACTOR_NOT_ALLOWED")
            if transport_status not in TRANSPORT:
                raise EvidenceError("RESPONSE_TRANSPORT_INVALID")
            if not isinstance(raw_response, str):
                raise EvidenceError("RESPONSE_RAW_NOT_TEXT")
            try:
                raw = raw_response.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise EvidenceError("RESPONSE_RAW_NOT_TEXT") from exc
            if len(raw) > MAX_RAW:
                raise EvidenceError("RESPONSE_TOO_LARGE")
            if transport_status != "OK" and raw:
                raise EvidenceError("RESPONSE_BODY_WITHOUT_TRANSPORT_OK")
            if (not isinstance(provider_request_id, str) or not PROVIDER_ID.fullmatch(provider_request_id)
                    or not isinstance(model_id, str) or not LABEL.fullmatch(model_id)
                    or type(attempt) is not int or not 1 <= attempt <= 100):
                raise EvidenceError("RESPONSE_METADATA_INVALID")
            if model_id != pinned_model(self.plan, actor_id):
                raise EvidenceError("RESPONSE_MODEL_NOT_PINNED")
            if slot(kind, actor_id) in self._slots:
                raise EvidenceError("RESPONSE_ALREADY_RECORDED")
            if provider_request_id in self._provider_ids:  # one provider reply must not fill two slots
                raise EvidenceError("RESPONSE_PROVIDER_ID_REUSED")
            if peer_uid is not None and (type(peer_uid) is not int or peer_uid < 0):
                raise EvidenceError("PEER_UID_INVALID")
            observed = now()
            moment = parse_utc(observed, "RESPONSE_TIMESTAMP_INVALID")
            if not (parse_utc(self.plan["window"]["not_before"], "WINDOW_INVALID") <= moment
                    <= parse_utc(self.plan["window"]["not_after"], "WINDOW_INVALID")):
                raise EvidenceError("RESPONSE_OUTSIDE_WINDOW")
            sha = sha_bytes(raw)
            if raw:
                stored = self.responses / f"{sha}.bin"
                if stored.exists():
                    if open_read_no_follow(stored) != raw:  # content-addressed: same name must mean same bytes
                        raise EvidenceError("RESPONSE_STORE_CONFLICT")
                else:
                    new_file(stored, raw)
            value, parse_status = parse_response(kind, raw, transport_status)
            detail = {"kind": kind, "value": value, "parse_status": parse_status,
                      "transport_status": transport_status, "provider_request_id": provider_request_id,
                      "model_id": model_id, "attempt": attempt, "response_sha256": sha,
                      "response_bytes": len(raw)}
            self._event("RESPONSE_RECORDED", "RECORDED", observed_utc=observed, peer_uid=peer_uid,
                        detail=detail, identity=(actor_id, None, None))
            self._slots.add(slot(kind, actor_id))
            self._provider_ids.add(provider_request_id)
            self._ledger.append({"actor_id": actor_id, "detail": detail})
            return {"recorded": True, "value": value, "parse_status": parse_status, "response_sha256": sha}

    def finalize(self, control_peer_uid=None):
        with self._lock:
            if self.finished:
                raise EvidenceError("ALREADY_FINALIZED")
            # A receipt finalized outside the window can never verify, so refuse it BEFORE writing anything.
            stamp = now()
            moment = parse_utc(stamp, "FINALIZE_TIMESTAMP_INVALID")
            if not (parse_utc(self.plan["window"]["not_before"], "WINDOW_INVALID") <= moment
                    <= parse_utc(self.plan["window"]["not_after"], "WINDOW_INVALID")):
                raise EvidenceError("FINALIZE_OUTSIDE_WINDOW")
            if not self.started:
                self.outcome = "NO_ATTEMPT"
                self.actor_id = "A"
                self.request_id = "NO_REQUEST"
                self.nonce = secrets.token_hex(16)
            if control_peer_uid is not None and (type(control_peer_uid) is not int or control_peer_uid < 0):
                raise EvidenceError("PEER_UID_INVALID")
            self._event("SNAPSHOT_FINALIZED", self.outcome,
                        artifact_sha256=self.artifact_sha256, peer_uid=control_peer_uid,
                        observed_utc=stamp)
            payload = {
                "schema": "humanaios.tool_receipt.v3", "run_id": self.plan["run_id"],
                "episode_id": self.plan["episode_id"], "plan_sha256": self.plan_hash,
                "writer_pubkey_sha256": public_fingerprint(self.key),
                "protocol_pins_sha256": digest(self.plan["protocol_pins"]),
                "event_count": self.seq, "tip_sha256": self.tip,
                "response_count": len(self._ledger), "response_ledger_sha256": digest(self._ledger),
                "tool_status": self.outcome, "artifact_sha256": self.artifact_sha256,
                "actor_id": self.actor_id, "request_id": self.request_id,
                "nonce": self.nonce, "finalized_utc": stamp,  # same reading as the event: one clock read
            }
            seal = {"payload": payload,
                    "signature_ed25519_b64": base64.b64encode(self.key.sign(canonical(payload))).decode("ascii")}
            new_file(self.ep / "snapshot.json", canonical(seal))
            self.finished = True
            # This is a logical freeze. The OS read-only snapshot must be done separately.
            return seal


def read_private_key(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077:
        raise EvidenceError("UNSAFE_PRIVATE_KEY_PATH_OR_PERMISSIONS")
    # Custody: the signing key must belong to the host user, in a directory nobody else can modify.
    # A key an agent UID owns could be read or swapped by that agent.
    if path.stat().st_uid != os.geteuid():
        raise EvidenceError("PRIVATE_KEY_NOT_OWNED_BY_HOST")
    if path.parent.stat().st_mode & 0o022:
        raise EvidenceError("PRIVATE_KEY_DIR_WRITABLE_BY_OTHERS")
    key = serialization.load_pem_private_key(open_read_no_follow(path), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise EvidenceError("NOT_ED25519_KEY")
    return key

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


def secure_dir(path):
    path = Path(path).absolute()
    for segment in (path, *path.parents):
        if segment.is_symlink():
            raise EvidenceError("SYMLINK_PATH")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise EvidenceError("UNSAFE_DIRECTORY")
    # O_NOFOLLOW protects only the last path component. Anyone who can replace an ANCESTOR entry could
    # redirect later writes, chmods and chowns, so every ancestor must belong to root or the host user and
    # must not be writable by others (a sticky directory such as /tmp is acceptable: others cannot rename
    # entries they do not own). Descriptor-relative traversal would be stronger and is NOT implemented.
    for ancestor in path.parents:
        info = ancestor.stat()
        if info.st_uid not in (0, os.geteuid()):
            raise EvidenceError("ANCESTOR_NOT_HOST_OWNED")
        if info.st_mode & 0o022 and not info.st_mode & stat.S_ISVTX:
            raise EvidenceError("ANCESTOR_WRITABLE_BY_OTHERS")
    # The directory itself must be ours before we chmod or use it: a pre-existing directory an agent owns
    # would stay renameable and writable by that agent no matter what mode we set.
    if path.stat().st_uid != os.geteuid():
        raise EvidenceError("DIRECTORY_NOT_HOST_OWNED")
    path.chmod(0o700)
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
        if list(self.events.iterdir()) or list(self.artifacts.iterdir()) or (self.ep / "snapshot.json").exists():
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

    def _event(self, kind, status, *, artifact_sha256=None, observed_utc=None, peer_uid=None):
        self.seq += 1
        event = {
            "schema": "humanaios.tool_event.v3", "sequence": self.seq,
            "run_id": self.plan["run_id"], "episode_id": self.plan["episode_id"],
            "plan_sha256": self.plan_hash, "kind": kind, "status": status,
            "actor_id": self.actor_id, "request_id": self.request_id,
            "nonce": self.nonce, "artifact_sha256": artifact_sha256,
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
                "schema": "humanaios.tool_receipt.v2", "run_id": self.plan["run_id"],
                "episode_id": self.plan["episode_id"], "plan_sha256": self.plan_hash,
                "writer_pubkey_sha256": public_fingerprint(self.key),
                "protocol_pins_sha256": digest(self.plan["protocol_pins"]),
                "event_count": self.seq, "tip_sha256": self.tip,
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

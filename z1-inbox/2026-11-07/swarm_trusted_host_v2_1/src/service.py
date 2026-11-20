"""OFFLINE reference Unix socket service; no live model integration or human grants.

Two kinds of channel (KD-1):
  * agent channel   - one socket PER ACTOR. The actor identity is fixed by which socket was
                      reached, never read from the request body. Only `write` is served.
  * control channel - orchestrator only. Only `finalize` is served. Never hand it to an agent.

Each connection has a deadline (KD-3), so one idle client cannot stall the writer.
Demarius's same-UID access finding is reproduced in the legacy demo. The isolated
offline mode requires frozen, distinct Linux UIDs for host/A/B/control, a per-socket
kernel peer UID check and 0600 socket ownership restricted to that role.

Not production-ready: requires a separately audited OS/container deployment,
independent immutable evidence, provenance of raw agent responses, a human grant,
and an external hard spend control. The request surface provides no shell or path.
"""
import argparse
import errno
import json
import os
import socket
import socketserver
import stat
import struct
import threading
import time
from pathlib import Path

from .pins import file_sha256
from .writer import HostWriter, EvidenceError, canonical, read_private_key, secure_dir, _open_parent_fd

DEFAULT_TIMEOUT = 5.0
AGENT_MAX_REQUEST = 4096
CONTROL_MAX_REQUEST = 262144  # a relayed model response (up to 32 KiB, JSON-escaped) fits
RECORD_KEYS = {"op", "actor_id", "kind", "transport_status", "provider_request_id", "model_id", "attempt",
               "raw_response"}
ROLES = ("agent", "control")


class Handler(socketserver.StreamRequestHandler):
    def setup(self):
        self.timeout = self.server.conn_timeout  # applied to the connection by StreamRequestHandler.setup
        super().setup()

    def _peer_uid(self):
        creds = self.request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        return struct.unpack("3i", creds)[1]

    def _observed_peer_uid(self):
        try:
            return self._peer_uid()
        except (OSError, AttributeError):  # SO_PEERCRED is Linux-only
            return None

    def _read_request_line(self, limit):
        """Read one bounded line under an ABSOLUTE monotonic deadline: a client that sends a byte before every
        per-recv timeout cannot keep this synchronous channel busy for longer than conn_timeout in total."""
        deadline = time.monotonic() + self.server.conn_timeout
        buf = b""
        while len(buf) <= limit and b"\n" not in buf:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EvidenceError("REQUEST_DEADLINE")
            self.request.settimeout(remaining)
            try:
                chunk = self.request.recv(min(65536, limit + 1 - len(buf)))
            except (socket.timeout, TimeoutError) as exc:
                raise EvidenceError("REQUEST_DEADLINE") from exc
            if not chunk:
                break
            buf += chunk
        self.request.settimeout(self.server.conn_timeout)
        cut = buf.find(b"\n")
        return buf[:cut + 1] if cut >= 0 else buf

    def _send(self, obj):
        try:
            self.wfile.write(canonical(obj) + b"\n")
        except OSError:
            pass

    def handle(self):
        srv = self.server
        try:
            # Read the (bounded) request line BEFORE judging the peer, so a refusal never closes the
            # connection with unread data (which resets it and can drop the error reply). The bytes of a
            # refused peer are read and discarded; they are never parsed or acted on.
            limit = srv.max_request
            raw = self._read_request_line(limit)
            if srv.allowed_uid is not None and self._peer_uid() != srv.allowed_uid:
                raise EvidenceError("PEER_NOT_AUTHORIZED")
            if len(raw) > limit or not raw.endswith(b"\n"):
                raise EvidenceError("REQUEST_TOO_LARGE")
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise EvidenceError("REQUEST_NOT_OBJECT")
            if (srv.role == "agent" and set(request) == {"op", "request_id", "intent"}
                    and request["op"] == "write"):
                reply = srv.writer.write(srv.actor_id, request["request_id"], request["intent"],
                                         peer_uid=self._observed_peer_uid())
            elif (srv.role == "control" and set(request) == RECORD_KEYS and request["op"] == "record_response"):
                reply = srv.writer.record_response(
                    request["actor_id"], request["kind"], request["raw_response"], request["transport_status"],
                    request["provider_request_id"], request["model_id"], request["attempt"],
                    peer_uid=self._observed_peer_uid())
            elif srv.role == "control" and request == {"op": "finalize"}:
                reply = {"snapshot": srv.writer.finalize(control_peer_uid=self._observed_peer_uid()),
                         "status": "FINALIZED"}
            else:
                raise EvidenceError("NARROW_METHODS_ONLY")
            self._send({"ok": True, "reply": reply})
        except RecursionError:  # json.loads on hostile nesting; reply instead of dropping the connection
            self._send({"ok": False, "error": "REQUEST_TOO_DEEP"})
        except (EvidenceError, ValueError, TypeError, KeyError, OSError) as exc:
            self._send({"ok": False, "error": str(exc)})


class Server(socketserver.UnixStreamServer):
    def __init__(self, socket_path, writer, role, actor_id=None, allowed_uid=None,
                 timeout=DEFAULT_TIMEOUT, enforce_isolation=False,
                 allow_unchecked_peer=False):
        if role not in ROLES:
            raise EvidenceError("UNKNOWN_ROLE")
        # A pinned identity policy cannot be silently downgraded to the legacy
        # same-UID test mode by calling Server() directly.
        if "role_uids" in writer.plan and not enforce_isolation:
            raise EvidenceError("ISOLATION_REQUIRED_BY_PLAN")
        # The channel roles are enforced by THIS file: refuse to serve if it is not the pinned one.
        if writer.plan["protocol_pins"]["service_sha256"] != file_sha256(__file__):
            raise EvidenceError("SERVICE_CODE_NOT_PINNED")
        if role == "agent" and actor_id not in ("A", "B"):
            raise EvidenceError("AGENT_CHANNEL_REQUIRES_ACTOR")
        if role == "control" and actor_id is not None:
            raise EvidenceError("CONTROL_CHANNEL_HAS_NO_ACTOR")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise EvidenceError("TIMEOUT_INVALID")
        # A socket's name alone is NOT an actor identity. In strict offline mode,
        # each channel has a distinct OS UID frozen into the signed plan.
        if enforce_isolation:
            roles = writer.plan.get("role_uids")
            if not isinstance(roles, dict):
                raise EvidenceError("ROLE_UID_POLICY_NOT_PINNED")
            role_name = "control" if role == "control" else ("agent_a" if actor_id == "A" else "agent_b")
            if type(allowed_uid) is not int or allowed_uid != roles[role_name]:
                raise EvidenceError("ROLE_UID_NOT_AUTHORIZED")
            if os.geteuid() != roles["host"]:
                raise EvidenceError("HOST_UID_NOT_AUTHORIZED")
            if not hasattr(socket, "SO_PEERCRED"):
                raise EvidenceError("LINUX_PEER_CREDENTIALS_REQUIRED")
            secure_dir(Path(socket_path).parent)
            parent_fd, _ = _open_parent_fd(socket_path)
            try:
                if os.fstat(parent_fd).st_uid != os.geteuid():
                    raise EvidenceError("SOCKET_PARENT_NOT_HOST_OWNED")
                # Apply search-only mode to the checked parent inode, never a re-resolved path.
                os.fchmod(parent_fd, 0o711)
            finally:
                os.close(parent_fd)
        # No silent open mode: without a peer-UID policy only file modes protect the socket.
        if allowed_uid is None and not allow_unchecked_peer:
            raise EvidenceError("PEER_UID_POLICY_REQUIRED")
        if allowed_uid is not None and not hasattr(socket, "SO_PEERCRED"):
            raise EvidenceError("LINUX_PEER_CREDENTIALS_REQUIRED")
        self.writer, self.role, self.actor_id = writer, role, actor_id
        self.max_request = CONTROL_MAX_REQUEST if role == "control" else AGENT_MAX_REQUEST
        self.allowed_uid, self.conn_timeout = allowed_uid, timeout
        # Keep the checked socket parent pinned throughout bind, chown, chmod and readback.
        # The UnixStreamServer bind itself takes a path, but later permission changes
        # cannot be redirected through a swapped ancestor. A mismatch fails closed.
        self._socket_path = str(socket_path)
        self._socket_identity = None            # (st_dev, st_ino) of the socket THIS server created
        parent_fd, leaf = _open_parent_fd(socket_path)
        try:
            # Create the socket private (0600) from the start instead of relying on a later no-follow chmod, which
            # older glibc does not support and which ran after the bind. The umask is process-wide, so it is held
            # only around the bind and restored on every path.
            # Bind and listen are SEPARATE steps. A bind that fails created nothing, so it must unlink nothing: another
            # server may have bound this path after any absence check (PR #1274 review). Only a bind that succeeded
            # gives this server a socket to clean up, and only by the identity recorded right after it.
            old_umask = os.umask(0o177)
            try:
                super().__init__(str(socket_path), Handler, bind_and_activate=False)
                try:
                    self.server_bind()
                except BaseException:
                    super().server_close()              # close our own descriptor; the path is not ours
                    raise
            finally:
                os.umask(old_umask)
            try:
                info = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
                if not stat.S_ISSOCK(info.st_mode):
                    raise EvidenceError("SOCKET_ROLE_PERMISSIONS_INVALID")
                self._socket_identity = (info.st_dev, info.st_ino)
                self.server_activate()
                if enforce_isolation:
                    try:
                        os.chown(leaf, allowed_uid, allowed_uid, dir_fd=parent_fd, follow_symlinks=False)
                    except OSError as exc:
                        raise EvidenceError("SOCKET_ROLE_OWNER_NOT_ENFORCED") from exc
                try:
                    os.chmod(leaf, 0o600, dir_fd=parent_fd, follow_symlinks=False)
                except NotImplementedError:
                    pass                                # no no-follow chmod here: the creation mode and the check below stand
                except OSError as exc:
                    if exc.errno not in (errno.ENOTSUP, errno.EOPNOTSUPP):
                        raise EvidenceError("SOCKET_PERMISSIONS_NOT_ENFORCED") from exc
                info = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
                if (info.st_dev, info.st_ino) != self._socket_identity or not stat.S_ISSOCK(info.st_mode) \
                        or (info.st_mode & 0o777) != 0o600:
                    raise EvidenceError("SOCKET_PERMISSIONS_NOT_ENFORCED")
                if enforce_isolation and info.st_uid != allowed_uid:
                    raise EvidenceError("SOCKET_ROLE_PERMISSIONS_INVALID")
            except BaseException:
                # Any failure after the bind: close the listener and remove ONLY the socket this setup created.
                super().server_close()
                self._discard_socket(parent_fd, leaf, self._socket_identity)
                self._socket_identity = None
                raise
        finally:
            os.close(parent_fd)

    @staticmethod
    def _discard_socket(parent_fd, leaf, identity):
        """Unlink `leaf` only if it is still a socket (and, when given, the very inode this server created)."""
        try:
            info = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
            if stat.S_ISSOCK(info.st_mode) and (identity is None or (info.st_dev, info.st_ino) == identity):
                os.unlink(leaf, dir_fd=parent_fd)
        except OSError:
            pass

    def server_close(self):
        """Close the listener and remove the socket this server created. A path that was replaced is left alone."""
        super().server_close()
        identity, self._socket_identity = getattr(self, "_socket_identity", None), None
        if identity is None:
            return
        try:
            parent_fd, leaf = _open_parent_fd(self._socket_path)
        except (OSError, EvidenceError):
            return
        try:
            self._discard_socket(parent_fd, leaf, identity)
        finally:
            os.close(parent_fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve-offline", action="store_true")
    parser.add_argument("--scope-json", required=True)
    parser.add_argument("--frozen-hash", required=True)
    parser.add_argument("--private-key", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--agent-socket-a", required=True)
    parser.add_argument("--agent-socket-b", required=True)
    parser.add_argument("--control-socket", required=True)
    parser.add_argument("--allowed-uid", type=int, default=None,
                        help="Legacy same-UID synthetic demonstration only; requires --allow-shared-uid-demo.")
    parser.add_argument("--allow-shared-uid-demo", action="store_true",
                        help="INSECURE synthetic-only mode, never evidence of actor identity separation.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    a = parser.parse_args()
    if not a.serve_offline:
        raise SystemExit("REFUSED: offline prototype only; no live grant or model execution")
    if a.allowed_uid is not None and not a.allow_shared_uid_demo:
        parser.error("SHARED_UID_DEMO_FLAG_REQUIRED")
    scope = json.loads(Path(a.scope_json).read_text())
    if a.allow_shared_uid_demo:
        if a.allowed_uid is None or "role_uids" in scope:
            parser.error("LEGACY_DEMO_REQUIRES_UNPINNED_SHARED_UID")
        allowed = {"agent_a": a.allowed_uid, "agent_b": a.allowed_uid, "control": a.allowed_uid}
    else:
        frozen = scope.get("role_uids")
        if not isinstance(frozen, dict):
            parser.error("ROLE_UID_POLICY_NOT_FROZEN")
        if os.geteuid() != frozen.get("host"):
            parser.error("HOST_UID_NOT_AUTHORIZED")
        allowed = {k: frozen[k] for k in ("agent_a", "agent_b", "control")}
    writer = HostWriter(Path(a.root), read_private_key(a.private_key), scope, a.frozen_hash)
    layout = [(a.agent_socket_a, "agent", "A", allowed["agent_a"]),
              (a.agent_socket_b, "agent", "B", allowed["agent_b"]),
              (a.control_socket, "control", None, allowed["control"])]
    paths = [Path(p) for p, _, _, _ in layout]
    if len(set(paths)) != len(paths):
        raise SystemExit("SOCKETS_MUST_BE_DISTINCT")
    servers = []
    for path, role, actor, uid in layout:
        path = Path(path)
        secure_dir(path.parent)
        if path.exists() or path.is_symlink():
            raise SystemExit("SOCKET_ALREADY_EXISTS")
        servers.append(Server(path, writer, role, actor_id=actor, allowed_uid=uid,
                              timeout=a.timeout, enforce_isolation=not a.allow_shared_uid_demo))
    for srv in servers[:-1]:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    servers[-1].serve_forever()


if __name__ == "__main__":
    main()

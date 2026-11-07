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
import json
import os
import socket
import socketserver
import struct
import threading
from pathlib import Path

from .pins import file_sha256
from .writer import HostWriter, EvidenceError, canonical, read_private_key, secure_dir

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
            raw = self.rfile.readline(limit + 1)
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
            parent = secure_dir(Path(socket_path).parent)
            if parent.stat().st_uid != os.geteuid():
                raise EvidenceError("SOCKET_PARENT_NOT_HOST_OWNED")
            # Host-owned search-only directory. Named 0600 sockets are exclusively
            # owned by their individual recipient UIDs. No shared group permissions.
            os.chmod(parent, 0o711)
        # No silent open mode: without a peer-UID policy only file modes protect the socket.
        if allowed_uid is None and not allow_unchecked_peer:
            raise EvidenceError("PEER_UID_POLICY_REQUIRED")
        if allowed_uid is not None and not hasattr(socket, "SO_PEERCRED"):
            raise EvidenceError("LINUX_PEER_CREDENTIALS_REQUIRED")
        self.writer, self.role, self.actor_id = writer, role, actor_id
        self.max_request = CONTROL_MAX_REQUEST if role == "control" else AGENT_MAX_REQUEST
        self.allowed_uid, self.conn_timeout = allowed_uid, timeout
        super().__init__(str(socket_path), Handler)
        if enforce_isolation:
            try:
                # Needs a trusted pre-provisioner with CAP_CHOWN. Missing privileges
                # fail closed; there is no fallback to host/shared ownership.
                os.chown(socket_path, allowed_uid, allowed_uid)
            except OSError as exc:
                self.server_close()
                raise EvidenceError("SOCKET_ROLE_OWNER_NOT_ENFORCED") from exc
        os.chmod(socket_path, 0o600)
        if enforce_isolation:
            info = os.stat(socket_path)
            if info.st_uid != allowed_uid or (info.st_mode & 0o777) != 0o600:
                self.server_close()
                raise EvidenceError("SOCKET_ROLE_PERMISSIONS_INVALID")


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

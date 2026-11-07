"""OFFLINE reference Unix socket service; no live model integration or human grants.

Two kinds of channel (KD-1):
  * agent channel   - one socket PER ACTOR. The actor identity is fixed by which socket was
                      reached, never read from the request body. Only `write` is served.
  * control channel - orchestrator only. Only `finalize` is served. Never hand it to an agent.

Each connection has a deadline (KD-3), so one idle client cannot stall the writer. An optional
SO_PEERCRED uid check refuses peers that are not the expected OS user.

Not production-ready: requires a dedicated OS principal, operator-approved scope, a read-only
snapshot and an external hard spend control. The request surface cannot supply a path or command.
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
ROLES = ("agent", "control")


class Handler(socketserver.StreamRequestHandler):
    def setup(self):
        self.timeout = self.server.conn_timeout  # applied to the connection by StreamRequestHandler.setup
        super().setup()

    def _peer_uid(self):
        creds = self.request.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
        return struct.unpack("3i", creds)[1]

    def _send(self, obj):
        try:
            self.wfile.write(canonical(obj) + b"\n")
        except OSError:
            pass

    def handle(self):
        srv = self.server
        try:
            if srv.allowed_uid is not None and self._peer_uid() != srv.allowed_uid:
                raise EvidenceError("PEER_NOT_AUTHORIZED")
            raw = self.rfile.readline(4097)
            if len(raw) >= 4097 or not raw.endswith(b"\n"):
                raise EvidenceError("REQUEST_TOO_LARGE")
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise EvidenceError("REQUEST_NOT_OBJECT")
            if (srv.role == "agent" and set(request) == {"op", "request_id", "intent"}
                    and request["op"] == "write"):
                reply = srv.writer.write(srv.actor_id, request["request_id"], request["intent"])
            elif srv.role == "control" and request == {"op": "finalize"}:
                reply = {"snapshot": srv.writer.finalize(), "status": "FINALIZED"}
            else:
                raise EvidenceError("NARROW_METHODS_ONLY")
            self._send({"ok": True, "reply": reply})
        except (EvidenceError, ValueError, TypeError, KeyError, OSError) as exc:
            self._send({"ok": False, "error": str(exc)})


class Server(socketserver.UnixStreamServer):
    def __init__(self, socket_path, writer, role, actor_id=None, allowed_uid=None, timeout=DEFAULT_TIMEOUT):
        if role not in ROLES:
            raise EvidenceError("UNKNOWN_ROLE")
        # The channel roles are enforced by THIS file: refuse to serve if it is not the pinned one.
        if writer.plan["protocol_pins"]["service_sha256"] != file_sha256(__file__):
            raise EvidenceError("SERVICE_CODE_NOT_PINNED")
        if role == "agent" and actor_id not in ("A", "B"):
            raise EvidenceError("AGENT_CHANNEL_REQUIRES_ACTOR")
        if role == "control" and actor_id is not None:
            raise EvidenceError("CONTROL_CHANNEL_HAS_NO_ACTOR")
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise EvidenceError("TIMEOUT_INVALID")
        self.writer, self.role, self.actor_id = writer, role, actor_id
        self.allowed_uid, self.conn_timeout = allowed_uid, timeout
        super().__init__(str(socket_path), Handler)
        os.chmod(socket_path, 0o600)


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
    parser.add_argument("--allowed-uid", type=int, required=True,
                        help="OS uid permitted to connect (SO_PEERCRED, Linux). Required: fail closed.")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    a = parser.parse_args()
    if not a.serve_offline:
        raise SystemExit("REFUSED: offline prototype only; no live grant or model execution")
    scope = json.loads(Path(a.scope_json).read_text())
    writer = HostWriter(Path(a.root), read_private_key(a.private_key), scope, a.frozen_hash)
    layout = [(a.agent_socket_a, "agent", "A"), (a.agent_socket_b, "agent", "B"),
              (a.control_socket, "control", None)]
    paths = [Path(p) for p, _, _ in layout]
    if len(set(paths)) != len(paths):
        raise SystemExit("SOCKETS_MUST_BE_DISTINCT")
    servers = []
    for path, role, actor in layout:
        path = Path(path)
        secure_dir(path.parent)
        if path.exists() or path.is_symlink():
            raise SystemExit("SOCKET_ALREADY_EXISTS")
        servers.append(Server(path, writer, role, actor_id=actor, allowed_uid=a.allowed_uid, timeout=a.timeout))
    for srv in servers[:-1]:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
    servers[-1].serve_forever()


if __name__ == "__main__":
    main()

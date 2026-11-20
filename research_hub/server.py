"""HTTP front door: streamable-HTTP MCP at /mcp, legacy SSE at /sse + /messages.

Refuses to listen beyond loopback without a token. Query strings are never logged.
"""
from __future__ import annotations

import argparse
import hmac
import json
import logging
import os
import queue
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .protocol import Tool, handle
from .tools import Hub

MAX_BODY = 1_000_000
log = logging.getLogger("research_hub")


def make_handler(tools: dict[str, Tool], token: str | None, origins: set[str], url_token: bool):
    sessions: dict[str, "queue.Queue[str | None]"] = {}

    class H(BaseHTTPRequestHandler):
        server_version = "research-hub"

        def log_message(self, fmt, *args):  # no URLs (they may carry a key)
            log.info("%s %s", self.command, urlparse(self.path).path)

        # -- helpers ------------------------------------------------------------
        def _send(self, code: int, body: bytes = b"", ctype: str = "application/json", extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _authed(self) -> bool:
            if token is None:
                return True
            got = self.headers.get("Authorization", "")
            cand = got[7:] if got.lower().startswith("bearer ") else ""
            if not cand and url_token:
                cand = (parse_qs(urlparse(self.path).query).get("key") or [""])[0]
            return bool(cand) and hmac.compare_digest(cand.encode(), token.encode())

        def _gate(self) -> bool:
            origin = self.headers.get("Origin")
            if origin and origins and origin not in origins:
                self._send(403, b'{"error":"origin not allowed"}')
                return False
            if not self._authed():
                self._send(401, b'{"error":"unauthorized"}', extra={"WWW-Authenticate": "Bearer"})
                return False
            return True

        def _json_body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY:
                self._send(413, b'{"error":"too large"}')
                return None
            try:
                return json.loads(self.rfile.read(n))
            except ValueError:
                self._send(400, b'{"error":"invalid json"}')
                return None

        # -- routes -------------------------------------------------------------
        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/healthz":
                return self._send(200, b'{"ok":true}')
            if not self._gate():
                return
            if path == "/mcp":
                return self._send(405, b'{"error":"use POST"}', extra={"Allow": "POST"})
            if path == "/sse":
                sid = secrets.token_urlsafe(16)
                q: "queue.Queue[str | None]" = queue.Queue()
                sessions[sid] = q
                self.send_response(200)
                for k, v in {"Content-Type": "text/event-stream", "Cache-Control": "no-cache",
                             "Connection": "keep-alive"}.items():
                    self.send_header(k, v)
                self.end_headers()
                key = ""
                if url_token and token:
                    key = "&key=" + token  # client posts back to the same secret URL
                try:
                    self.wfile.write(f"event: endpoint\ndata: /messages?session_id={sid}{key}\n\n".encode())
                    self.wfile.flush()
                    while True:
                        try:
                            item = q.get(timeout=15)
                        except queue.Empty:
                            self.wfile.write(b": keepalive\n\n")
                            self.wfile.flush()
                            continue
                        if item is None:
                            break
                        self.wfile.write(f"event: message\ndata: {item}\n\n".encode())
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    sessions.pop(sid, None)
                return
            self._send(404, b'{"error":"not found"}')

        def do_POST(self):
            parsed = urlparse(self.path)
            if not self._gate():
                return
            if parsed.path not in ("/mcp", "/messages"):
                return self._send(404, b'{"error":"not found"}')
            payload = self._json_body()
            if payload is None:
                return
            reply = handle(payload, tools)
            if parsed.path == "/messages":
                sid = (parse_qs(parsed.query).get("session_id") or [""])[0]
                q = sessions.get(sid)
                if q is None:
                    return self._send(404, b'{"error":"unknown session"}')
                if reply is not None:
                    q.put(json.dumps(reply))
                return self._send(202, b"Accepted", "text/plain")
            if reply is None:
                return self._send(202)
            self._send(200, json.dumps(reply).encode())

        def do_OPTIONS(self):
            self._send(204, extra={"Allow": "GET, POST, OPTIONS"})

    return H


def main() -> None:
    ap = argparse.ArgumentParser(description="Research Hub MCP server")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO)

    token = os.environ.get("HUB_TOKEN") or None
    if token is None and args.host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("Refusing to listen beyond loopback without HUB_TOKEN.")
    if token is not None and len(token) < 24:
        raise SystemExit("HUB_TOKEN must be at least 24 characters.")
    origins = {o for o in os.environ.get("HUB_ALLOWED_ORIGINS", "").split(",") if o}
    url_token = os.environ.get("HUB_ALLOW_URL_TOKEN") == "1"

    hub = Hub()
    handler = make_handler(hub.tools(), token, origins, url_token)
    srv = ThreadingHTTPServer((args.host, args.port), handler)
    srv.daemon_threads = True
    log.info("research-hub on %s:%s, bots=%s", args.host, args.port, list(hub.router.providers))
    srv.serve_forever()


if __name__ == "__main__":
    main()

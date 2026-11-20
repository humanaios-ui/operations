#!/usr/bin/env python3
"""
Builder v1.7 compliant
z2_authorized_machine_identities_api_v0.py — optional read-only local HTTP mirror
of the INTENT-OS machine-capability allowlist.

HumanAIOS — Q-INTENT-OS-WITNESS-LEDGER-01 Phase D (optional query surface)

Serves GET /api/z2-authorized-machine-identities from the same local allowlist +
witness ledger that Phase C's stop-hook already reads offline. AUTHORITY_EFFECT
is NONE. can_authorize is false. This tool does not grant merge authority,
satisfy required review, sign a ruling, or replace a Z2 hash.

Fail-closed: missing/invalid allowlist or broken witness ledger → empty
authorized_identities with an explicit error object (HTTP 503).

Stop-hook independence: Phase C never consults this API (allowlist
http_api.enabled stays false). Offline gates keep working without HTTP.

Usage:
  python3 tools/z2_authorized_machine_identities_api_v0.py get
  python3 tools/z2_authorized_machine_identities_api_v0.py serve [--host 127.0.0.1] [--port 8787]
  python3 tools/z2_authorized_machine_identities_api_v0.py --smoke-test
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TOOL_NAME = "z2_authorized_machine_identities_api"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "governance_tool"
TOOL_ZONE = 1
TOOL_SESSION = "S-112026-intent-os-machine-identity-api"

AUTHORITY_EFFECT = "NONE"
CAN_AUTHORIZE = False
ADVISORY_ONLY = True
API_PATH = "/api/z2-authorized-machine-identities"
HEALTH_PATH = "/healthz"

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWLIST = ROOT / "ledgers" / "MACHINE_CAPABILITY_ALLOWLIST.json"


def _import_allowlist():
    tools_dir = Path(__file__).resolve().parent
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    import machine_capability_allowlist_v0 as mca  # noqa: WPS433

    return mca


def classify_error(message: str) -> str:
    lower = message.lower()
    if "ledger" in lower:
        return "LEDGER_UNVERIFIABLE"
    if "allowlist missing" in lower or "missing (fail-closed)" in lower:
        return "ALLOWLIST_MISSING"
    if "content_hash" in lower or "unreadable" in lower or "unverifiable" in lower:
        return "ALLOWLIST_UNVERIFIABLE"
    return "REGISTRY_UNVERIFIABLE"


def deny_payload(error_message: str) -> Dict[str, Any]:
    return {
        "ok": False,
        "path": API_PATH,
        "schema": "intentos/z2_authorized_machine_identities_api_v0",
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
        "advisory_only": ADVISORY_ONLY,
        "grants_merge_authority": False,
        "stop_hook_independent": True,
        "source": "local_allowlist",
        "tool": f"{TOOL_NAME}@{TOOL_VERSION}",
        "identities": [],
        "authorized_identities": [],
        "error": {
            "code": classify_error(error_message),
            "message": error_message,
        },
    }


def build_payload(
    allowlist_path: Path, ledger_path: Optional[Path] = None
) -> Tuple[int, Dict[str, Any]]:
    """Build the API response. Returns (http_status, body). Fail-closed on errors."""
    mca = _import_allowlist()
    try:
        doc, ledger_info = mca.verify_bundle(
            allowlist_path, ledger_path if ledger_path is not None else None
        )
    except mca.AllowlistError as exc:
        return 503, deny_payload(str(exc))
    except mca.SpecLoadFailed as exc:
        return 503, deny_payload(f"SPEC_LOAD_FAILED: {exc}")

    identities: List[Dict[str, Any]] = []
    authorized: List[str] = []
    for entry in doc["entries"]:
        decision = mca.decide(doc, entry["identity"], ledger_info=ledger_info)
        row = {
            "identity": entry["identity"],
            "actor_type": entry["actor_type"],
            "role": entry["role"],
            "status": entry["status"],
            "capability_digest": entry.get("capability_digest"),
            "decision": decision["decision"],
            "reason": decision["reason"],
        }
        identities.append(row)
        if decision["decision"] == "ALLOW":
            authorized.append(entry["identity"])

    body = {
        "ok": True,
        "path": API_PATH,
        "schema": "intentos/z2_authorized_machine_identities_api_v0",
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize": CAN_AUTHORIZE,
        "advisory_only": ADVISORY_ONLY,
        "grants_merge_authority": False,
        "stop_hook_independent": True,
        "source": "local_allowlist",
        "tool": f"{TOOL_NAME}@{TOOL_VERSION}",
        "allowlist_content_hash": doc["content_hash"],
        "allowlist_http_api_enabled": bool(doc.get("http_api", {}).get("enabled")),
        "ledger": ledger_info,
        "identities": identities,
        "authorized_identities": authorized,
        "error": None,
        "note": (
            "Read-only mirror of ledgers/MACHINE_CAPABILITY_ALLOWLIST.json after "
            "witness-ledger verify. Does not grant merge authority. Stop-hook "
            "continues to read local files and must not require this HTTP surface."
        ),
    }
    return 200, body


def make_handler(
    allowlist_path: Path, ledger_path: Optional[Path]
) -> type:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: Dict[str, Any]) -> None:
            raw = json.dumps(obj, sort_keys=True).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Authority-Effect", AUTHORITY_EFFECT)
            self.send_header("X-Can-Authorize", "false")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self) -> None:  # noqa: N802
            path = self.path.split("?", 1)[0]
            if path == HEALTH_PATH:
                return self._send(
                    200,
                    {
                        "ok": True,
                        "service": TOOL_NAME,
                        "version": TOOL_VERSION,
                        "authority_effect": AUTHORITY_EFFECT,
                        "can_authorize": CAN_AUTHORIZE,
                        "paths": [HEALTH_PATH, API_PATH],
                    },
                )
            if path == API_PATH:
                code, body = build_payload(allowlist_path, ledger_path)
                return self._send(code, body)
            return self._send(
                404,
                {
                    "ok": False,
                    "error": {"code": "NOT_FOUND", "message": f"unknown path: {path}"},
                    "authority_effect": AUTHORITY_EFFECT,
                    "can_authorize": CAN_AUTHORIZE,
                    "paths": [HEALTH_PATH, API_PATH],
                },
            )

        def do_POST(self) -> None:  # noqa: N802
            self._send(
                405,
                {
                    "ok": False,
                    "error": {
                        "code": "METHOD_NOT_ALLOWED",
                        "message": "read-only API; GET only",
                    },
                    "authority_effect": AUTHORITY_EFFECT,
                    "can_authorize": CAN_AUTHORIZE,
                },
            )

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stdout.write("%s - %s\n" % (self.address_string(), fmt % args))
            sys.stdout.flush()

    return Handler


def cmd_get(args: argparse.Namespace) -> int:
    code, body = build_payload(
        Path(args.allowlist), Path(args.ledger) if args.ledger else None
    )
    print(json.dumps(body, indent=2, sort_keys=True))
    return 0 if body.get("ok") else 1


def cmd_serve(args: argparse.Namespace) -> int:
    host = args.host
    if host not in ("127.0.0.1", "localhost", "::1") and not args.allow_non_loopback:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": (
                        "refusing non-loopback bind without --allow-non-loopback "
                        "(local-only Phase D posture)"
                    ),
                }
            ),
            file=sys.stderr,
        )
        return 2
    handler = make_handler(
        Path(args.allowlist), Path(args.ledger) if args.ledger else None
    )
    server = ThreadingHTTPServer((host, args.port), handler)
    print(
        json.dumps(
            {
                "ok": True,
                "action": "serve",
                "host": host,
                "port": server.server_address[1],
                "paths": [HEALTH_PATH, API_PATH],
                "authority_effect": AUTHORITY_EFFECT,
                "can_authorize": CAN_AUTHORIZE,
                "grants_merge_authority": False,
                "stop_hook_independent": True,
                "allowlist": str(args.allowlist),
            },
            sort_keys=True,
        )
    )
    sys.stdout.flush()
    try:
        server.serve_forever(poll_interval=0.05)
    except KeyboardInterrupt:
        print(json.dumps({"ok": True, "action": "shutdown"}))
    finally:
        server.server_close()
    return 0


def run_smoke_test() -> int:
    mca = _import_allowlist()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        allowlist = tmp_path / "MACHINE_CAPABILITY_ALLOWLIST.json"
        ledger = tmp_path / "WITNESS_LEDGER.jsonl"

        wl = mca._import_witness_ledger()
        parser_wl = wl.build_parser()
        assert (
            wl.cmd_init(
                parser_wl.parse_args(
                    ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
                )
            )
            == 0
        )

        doc = mca.build_seed_doc()
        doc["witness_ledger"] = str(ledger)
        doc["content_hash"] = mca.compute_content_hash(doc)
        allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        code, body = build_payload(allowlist, ledger)
        assert code == 200 and body["ok"] is True, body
        assert body["authority_effect"] == "NONE"
        assert body["can_authorize"] is False
        assert body["grants_merge_authority"] is False
        assert body["stop_hook_independent"] is True
        assert body["allowlist_http_api_enabled"] is False
        assert "carly.r.anderson@gmail.com" in body["authorized_identities"]
        assert "aioshuman@gmail.com" in body["authorized_identities"]
        assert "noreply@anthropic.com" not in body["authorized_identities"]
        assert body["error"] is None

        # Fail-closed: missing allowlist
        code2, body2 = build_payload(tmp_path / "missing.json", ledger)
        assert code2 == 503 and body2["ok"] is False, body2
        assert body2["authorized_identities"] == []
        assert body2["error"]["code"] in (
            "ALLOWLIST_MISSING",
            "ALLOWLIST_UNVERIFIABLE",
            "REGISTRY_UNVERIFIABLE",
        )

        # Fail-closed: tampered allowlist
        bad = json.loads(allowlist.read_text(encoding="utf-8"))
        bad["content_hash"] = "0" * 64
        allowlist.write_text(json.dumps(bad, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        code3, body3 = build_payload(allowlist, ledger)
        assert code3 == 503 and body3["ok"] is False, body3
        assert body3["authorized_identities"] == []
        assert body3["error"]["code"] == "ALLOWLIST_UNVERIFIABLE"

        # Restore allowlist; break ledger
        allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = ledger.read_text(encoding="utf-8").splitlines()
        obj = json.loads(lines[0])
        obj["title"] = "TAMPERED"
        ledger.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")
        code4, body4 = build_payload(allowlist, ledger)
        assert code4 == 503 and body4["ok"] is False, body4
        assert body4["authorized_identities"] == []
        assert body4["error"]["code"] == "LEDGER_UNVERIFIABLE"

        # Restore for HTTP round-trip
        ledger.write_text("", encoding="utf-8")
        assert (
            wl.cmd_init(
                parser_wl.parse_args(
                    ["init", "--ledger", str(ledger), "--timestamp", "2026-11-20T12:00:00Z"]
                )
            )
            == 0
        )
        allowlist.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        handler = make_handler(allowlist, ledger)
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        port = server.server_address[1]
        thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True
        )
        thread.start()
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{HEALTH_PATH}") as resp:
                health = json.loads(resp.read().decode("utf-8"))
            assert health["ok"] is True and health["authority_effect"] == "NONE"

            with urllib.request.urlopen(f"http://127.0.0.1:{port}{API_PATH}") as resp:
                assert resp.status == 200
                remote = json.loads(resp.read().decode("utf-8"))
            assert remote["ok"] is True
            assert "carly.r.anderson@gmail.com" in remote["authorized_identities"]
            assert remote["can_authorize"] is False

            try:
                urllib.request.urlopen(
                    urllib.request.Request(
                        f"http://127.0.0.1:{port}{API_PATH}",
                        data=b"{}",
                        method="POST",
                        headers={"Content-Type": "application/json"},
                    )
                )
                raise AssertionError("POST must be refused")
            except urllib.error.HTTPError as exc:
                assert exc.code == 405
                refused = json.loads(exc.read().decode("utf-8"))
                assert refused["ok"] is False
        finally:
            server.shutdown()
            server.server_close()

        # Stop-hook still works offline without this API (Phase C contract)
        stop_parser = mca.build_parser()
        stop_args = stop_parser.parse_args(
            [
                "stop-hook",
                "--allowlist",
                str(allowlist),
                "--ledger",
                str(ledger),
                "--identity",
                "carly.r.anderson@gmail.com",
            ]
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            stop_code = mca.cmd_stop_hook(stop_args)
        stop_payload = json.loads(buf.getvalue())
        assert stop_code == 0
        assert stop_payload["decision"] == "ALLOW"
        assert stop_payload.get("http_consulted") is False

    print("smoke-test OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "INTENT-OS optional read-only /api/z2-authorized-machine-identities "
            "(authority_effect=NONE; can_authorize=false; fail-closed; stop-hook independent)"
        )
    )
    ap.add_argument("--smoke-test", action="store_true")
    sub = ap.add_subparsers(dest="command")

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST))
        p.add_argument(
            "--ledger",
            default=None,
            help="Override witness ledger path (default: path recorded in allowlist)",
        )

    p = sub.add_parser("get", help="Print one-shot JSON payload (no HTTP server)")
    add_common(p)
    p.set_defaults(fn=cmd_get)

    p = sub.add_parser(
        "serve",
        help="Serve local read-only HTTP on loopback (default 127.0.0.1:8787)",
    )
    add_common(p)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8787)
    p.add_argument(
        "--allow-non-loopback",
        action="store_true",
        help="Permit binding outside 127.0.0.1/localhost/::1 (still grants no authority)",
    )
    p.set_defaults(fn=cmd_serve)

    return ap


def main(argv: Optional[List[str]] = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    if args.smoke_test:
        return run_smoke_test()
    if not getattr(args, "fn", None):
        ap.print_help()
        return 2
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())

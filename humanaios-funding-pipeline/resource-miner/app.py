from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from resource_miner.miner import enrich
from resource_miner.entitlement_handoff import build_entitlement_handoff
from resource_miner.needs import load_needs, load_requirements
from resource_miner.sources import devto, funding_pipeline, github, rss
from resource_miner.store import write_jsonl

ROOT = Path(__file__).resolve().parent
DEFAULT_NEEDS = ROOT / "data" / "needs.seed.json"
DEFAULT_REQUIREMENTS = ROOT / "data" / "resource_requirements.seed.json"
DEFAULT_OUT = ROOT / "data" / "resources.jsonl"
SNAPSHOT_OUT = ROOT / "data" / "resources.snapshot.jsonl"
DEFAULT_FUNDING = ROOT.parent / "data" / "sources.json"


def _json_bytes(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _run_scan(params: dict[str, list[str]]) -> list[Any]:
    sources = params.get("source") or ["funding", "devto"]
    discovered = []
    if "funding" in sources:
        funding_data = (params.get("funding_data") or [str(DEFAULT_FUNDING)])[0]
        discovered.extend(funding_pipeline.discover(funding_data))
    if "devto" in sources:
        discovered.extend(devto.discover(params.get("dev_tag") or ["devchallenge"]))
    if "github" in sources:
        queries = params.get("github_query") or [
            "is:issue is:open label:bounty",
            'is:issue is:open "cash prize"',
        ]
        discovered.extend(github.discover(queries))
    if "rss" in sources:
        discovered.extend(rss.discover(params.get("rss") or []))
    needs_path = (params.get("needs") or [str(DEFAULT_NEEDS)])[0]
    requirements_path = (params.get("requirements") or [str(DEFAULT_REQUIREMENTS)])[0]
    return enrich(discovered, needs_path, requirements_path)


class Handler(BaseHTTPRequestHandler):
    server_version = "ResourceMiner/0.2"

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = _json_bytes(data)
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        try:
            if parsed.path == "/api/health":
                return self._send_json({
                    "ok": True,
                    "version": "0.2.0",
                    "role": "Z0/Z1 read-only discovery; asserts no applicant eligibility",
                })
            if parsed.path == "/api/needs":
                return self._send_json({"needs": load_needs(DEFAULT_NEEDS)})
            if parsed.path == "/api/requirements":
                return self._send_json({"requirements": load_requirements(DEFAULT_REQUIREMENTS)})
            if parsed.path == "/api/resources":
                rows, src = _read_jsonl(DEFAULT_OUT), "live"
                if not rows:
                    rows, src = _read_jsonl(SNAPSHOT_OUT), "snapshot"
                return self._send_json({"source": src, "count": len(rows), "resources": rows})
            if parsed.path == "/api/entitlement/handoff":
                resource_id = (params.get("resource_id") or [""])[0].strip()
                if not resource_id:
                    return self._send_json({"error": "resource_id is required"}, HTTPStatus.BAD_REQUEST)
                rows = _read_jsonl(DEFAULT_OUT)
                if not rows:
                    rows = _read_jsonl(SNAPSHOT_OUT)
                match = next((row for row in rows if str(row.get("resource_id") or "") == resource_id), None)
                if match is None:
                    return self._send_json({"error": "resource_id not found"}, HTTPStatus.NOT_FOUND)
                return self._send_json({"handoff": build_entitlement_handoff(match)})
            if parsed.path == "/api/scan":
                resources = _run_scan(params)
                persist = params.get("persist", ["0"])[0] in ("1", "true", "yes")
                if persist:
                    write_jsonl(DEFAULT_OUT, resources)
                return self._send_json({
                    "count": len(resources),
                    "persisted": persist,
                    "resources": [r.to_dict() for r in resources],
                })
            return self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            return self._send_json(
                {"error": f"Internal error: {type(exc).__name__}: {exc}"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/scan":
            return self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw.decode("utf-8")) if raw else {}
            if not isinstance(body, dict):
                raise ValueError("JSON body must be an object")
            params = {k: (v if isinstance(v, list) else [v]) for k, v in body.items()}
            resources = _run_scan(params)
            persist = bool(body.get("persist", False))
            if persist:
                write_jsonl(DEFAULT_OUT, resources)
            return self._send_json({
                "count": len(resources),
                "persisted": persist,
                "resources": [r.to_dict() for r in resources],
            })
        except ValueError as exc:
            return self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except Exception as exc:
            return self._send_json(
                {"error": f"Internal error: {type(exc).__name__}"},
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Resource Miner as an HTTP utility")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Resource Miner running at http://{args.host}:{args.port}")
    print("Z0/Z1 read-only discovery: no applicant eligibility is asserted by this service.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()

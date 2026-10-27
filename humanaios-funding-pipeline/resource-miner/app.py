from __future__ import annotations

import argparse
import json
import os
import ipaddress
from hmac import compare_digest
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.parse import parse_qs, urlparse

from resource_miner.ats_readiness import public_specimen_readiness
from resource_miner.miner import enrich
from resource_miner.mines import load_mines
from resource_miner.pathways_view import project_pathways
from resource_miner.intent_os import evaluate_objective
from resource_miner.opportunity_journey import project_journey
from resource_miner.entitlement_handoff import build_entitlement_handoff
from resource_miner.needs import load_needs, load_requirements
from resource_miner.sources import devto, funding_pipeline, github, rss
from resource_miner.store import write_jsonl
from resource_miner.snapshot_status import reconcile_snapshot_source_holds
from resource_miner.witness_bridge import ask_resource, enabled as witness_enabled, WitnessBridgeUnavailable

ROOT = Path(__file__).resolve().parent
DEFAULT_MINES = ROOT / "data" / "mines.seed.json"
DEFAULT_RECEIPTS = ROOT / "data" / "resource_state.receipts.jsonl"
DEFAULT_NEEDS = ROOT / "data" / "needs.seed.json"
DEFAULT_REQUIREMENTS = ROOT / "data" / "resource_requirements.seed.json"
DEFAULT_OUT = ROOT / "data" / "resources.jsonl"
SNAPSHOT_OUT = ROOT / "data" / "resources.snapshot.jsonl"
DEFAULT_FUNDING = ROOT.parent / "data" / "sources.json"
JOURNEY_STARTER = ROOT / "fixtures" / "opportunity_journey_apart_synthetic.json"


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


def _intent_scan() -> tuple[list[dict[str, Any]], str, str]:
    """Use existing public Miner adapters only; never expose private sources.

    The locally curated funding catalog is not independently refreshed.
    DEV Community is a public network observation. Its failure is disclosed.
    """
    discovered = list(funding_pipeline.discover(DEFAULT_FUNDING))
    source_status = "CURATED_ONLY_LIVE_SOURCE_FAILED"
    source_warning = ""
    try:
        observed = list(devto.discover(["devchallenge"], per_page=12, hydrate=False))
        discovered.extend(observed)
        source_status = "PUBLIC_DEV_LIVE_PLUS_CURATED_FUNDING"
    except Exception:
        source_warning = "DEV live source could not be reached. Showing curated records only; current availability is unknown."
    candidates = enrich(discovered, DEFAULT_NEEDS, DEFAULT_REQUIREMENTS)
    return [c.to_dict() for c in candidates], source_status, source_warning


class Handler(BaseHTTPRequestHandler):
    server_version = "ResourceMiner/0.2"

    def _read_intent_body(self, length: int) -> bytes:
        """Read one bounded request body under a whole-request deadline.

        BufferedReader.read(length) can wait for all bytes while a peer drips
        input indefinitely. read1() performs one underlying read per iteration.
        Neither an idle socket timeout nor client Content-Length is a warrant.
        """
        deadline = monotonic() + 15.0
        chunks: list[bytes] = []
        remaining = length
        while remaining:
            seconds_left = deadline - monotonic()
            if seconds_left <= 0:
                raise TimeoutError("Request body deadline exceeded.")
            self.connection.settimeout(seconds_left)
            chunk = self.rfile.read1(remaining)
            if monotonic() >= deadline:
                raise TimeoutError("Request body deadline exceeded.")
            if not chunk:
                raise ValueError("Incomplete request body.")
            if len(chunk) > remaining:
                raise ValueError("Request body exceeded declared length.")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _local_opportunities_allowed(self) -> bool:
        """The private preview is NEVER enabled on 0.0.0.0 / Azure ingress.

        Bound loopback and peer loopback are both required. Host/Origin checks
        prevent browser DNS-rebinding and cross-origin request attempts.
        """
        try:
            bound = ipaddress.ip_address(self.server.server_address[0])
            peer = ipaddress.ip_address(self.client_address[0])
            port = self.server.server_address[1]
            permitted = {f"127.0.0.1:{port}", f"localhost:{port}", f"[::1]:{port}"}
            origin = self.headers.get("Origin")
            return (bound.is_loopback and peer.is_loopback
                    and self.headers.get("Host") in permitted
                    and (origin is None or origin in {"http://" + host for host in permitted}))
        except (ValueError, AttributeError, IndexError, TypeError):
            return False

    def _admin_allowed(self) -> bool:
        """Deny legacy scan/record APIs to anonymous public service callers.

        The public INTENT-OS objective route does not use these endpoints.
        Store the admin token in an external secret manager, never in the UI.
        """
        expected = os.environ.get("RESOURCE_MINER_ADMIN_TOKEN", "")
        supplied = self.headers.get("X-Resource-Miner-Admin-Token", "")
        if (len(expected) >= 32 and supplied
                and compare_digest(expected.encode("utf-8"), supplied.encode("utf-8"))):
            return True
        self._send_json({"error": "Admin API unavailable or unauthorized."},
                        HTTPStatus.FORBIDDEN)
        return False

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        if content_type.startswith("text/html"):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
            )
        self.end_headers()

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = _json_bytes(data)
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        try:
            if parsed.path == "/my-opportunities":
                if not self._local_opportunities_allowed():
                    return self._send_json({"error": "Local-only route unavailable."}, HTTPStatus.NOT_FOUND)
                page = (ROOT / "my-opportunities.html").read_bytes()
                self._headers(200, "text/html; charset=utf-8", len(page))
                self.wfile.write(page)
                return
            if parsed.path in ("/api/my-opportunities", "/api/my-opportunities/starter"):
                if not self._local_opportunities_allowed():
                    return self._send_json({"error": "Local-only route unavailable."}, HTTPStatus.NOT_FOUND)
                # Only public synthetic examples are served by default.
                source = json.loads(JOURNEY_STARTER.read_text(encoding="utf-8"))
                if parsed.path.endswith("/starter"):
                    return self._send_json(source)
                return self._send_json({
                    "mode": "SYNTHETIC_DEMONSTRATION_NOT_PERSONAL_EVIDENCE",
                    "journeys": [project_journey(source)],
                    "authority": "NONE",
                })
            if parsed.path == "/pathways":
                if not self._local_opportunities_allowed():
                    return self._send_json({"error": "Local-only route unavailable."}, HTTPStatus.NOT_FOUND)
                page = (ROOT / "pathways.html").read_bytes()
                self._headers(200, "text/html; charset=utf-8", len(page))
                self.wfile.write(page)
                return
            if parsed.path == "/api/pathways":
                if not self._local_opportunities_allowed():
                    return self._send_json({"error": "Local-only route unavailable."}, HTTPStatus.NOT_FOUND)
                mode = (params.get("mode") or ["stored"])[0]
                if mode not in {"stored", "public"}:
                    return self._send_json({"error": "mode must be stored or public."}, HTTPStatus.BAD_REQUEST)
                if mode == "public":
                    rows, source_status, warning = _intent_scan()
                    origin = "PUBLIC_REFRESH"
                    if warning:
                        source_status += " · " + warning
                else:
                    source_file = DEFAULT_OUT if DEFAULT_OUT.is_file() else SNAPSHOT_OUT
                    if not source_file.is_file():
                        return self._send_json({"error": "No stored Resource Miner data available."},
                                               HTTPStatus.SERVICE_UNAVAILABLE)
                    rows = _read_jsonl(source_file)
                    origin = "PERSISTED_RUNTIME" if source_file == DEFAULT_OUT else "STORED_SNAPSHOT"
                    source_status = "LOCAL_FILE_READ_ONLY_NO_EXTERNAL_PROVIDER_REFRESH"
                projection = project_pathways(
                    [m.to_dict() for m in load_mines(DEFAULT_MINES)],
                    load_needs(DEFAULT_NEEDS),
                    load_requirements(DEFAULT_REQUIREMENTS),
                    rows,
                    _read_jsonl(DEFAULT_RECEIPTS) if mode == "stored" else [],
                    origin=origin,
                    source_status=source_status,
                )
                return self._send_json(projection)
            if parsed.path in ("/", "/intent-os"):
                page = (ROOT / "intent-os.html").read_bytes()
                self._headers(200, "text/html; charset=utf-8", len(page))
                self.wfile.write(page)
                return
            if parsed.path == "/on-track":
                page = (ROOT / "on-track.html").read_bytes()
                self._headers(200, "text/html; charset=utf-8", len(page))
                self.wfile.write(page)
                return
            if parsed.path == "/api/ats/readiness":
                # Redacted E0 case only. No resume upload, source fetch, or application.
                if parsed.query not in ("", "specimen=convergent-2026-10-22"):
                    return self._send_json({"error": "Unknown public ATS specimen."},
                                           HTTPStatus.NOT_FOUND)
                return self._send_json(public_specimen_readiness())
            if parsed.path == "/api/witness/status":
                if not self._local_opportunities_allowed():
                    return self._send_json({"error": "Local-only route unavailable."}, HTTPStatus.NOT_FOUND)
                return self._send_json({
                    "enabled": witness_enabled(),
                    "mode": "LOCAL_OPERATOR_OPT_IN_MCP",
                    "shared_candidate_data": "PUBLIC_RESOURCE_SUMMARY_AND_TYPED_QUESTION_ONLY",
                    "authority": "NONE",
                })
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
                if not self._admin_allowed():
                    return
                rows, src = _read_jsonl(DEFAULT_OUT), "live"
                if not rows:
                    rows, src = _read_jsonl(SNAPSHOT_OUT), "snapshot"
                return self._send_json({"source": src, "count": len(rows), "resources": rows})
            if parsed.path == "/api/entitlement/handoff":
                if not self._admin_allowed():
                    return
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
                if not self._admin_allowed():
                    return
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
        if urlparse(self.path).path == "/api/witness/ask-resource":
            # Read-only model conversation. Never expose this endpoint on a
            # public bind or accept cross-origin/browser-forged POSTs.
            if not self._local_opportunities_allowed():
                return self._send_json({"error": "Local-only Witness route unavailable."},
                                       HTTPStatus.NOT_FOUND)
            port = self.server.server_address[1]
            origin = self.headers.get("Origin")
            if origin not in (f"http://127.0.0.1:{port}",
                              f"http://localhost:{port}",
                              f"http://[::1]:{port}"):
                return self._send_json({"error": "Same-origin browser consent required."},
                                       HTTPStatus.FORBIDDEN)
            if not witness_enabled():
                return self._send_json({"error": "Local Witness MCP integration is disabled."},
                                       HTTPStatus.SERVICE_UNAVAILABLE)
            try:
                if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    raise ValueError("JSON request required.")
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 4096:
                    raise ValueError("Witness request must be 1–4096 bytes.")
                body = json.loads(self._read_intent_body(length).decode("utf-8"))
                self.connection.settimeout(90)
                return self._send_json(ask_resource(body))
            except TimeoutError:
                self.close_connection = True
                return self._send_json({"error": "Witness request body deadline exceeded."},
                                       HTTPStatus.REQUEST_TIMEOUT)
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
                return self._send_json({"error": "Invalid public resource or missing explicit consent."},
                                       HTTPStatus.BAD_REQUEST)
            except WitnessBridgeUnavailable:
                return self._send_json({"error": "Witness MCP not available; no model response recorded."},
                                       HTTPStatus.SERVICE_UNAVAILABLE)
            except Exception:
                return self._send_json({"error": "Local Witness bridge failed."},
                                       HTTPStatus.SERVICE_UNAVAILABLE)
        if urlparse(self.path).path == "/api/my-opportunities/project":
            if not self._local_opportunities_allowed():
                return self._send_json({"error": "Local-only route unavailable."}, HTTPStatus.NOT_FOUND)
            try:
                if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                    raise ValueError("Expected application/json.")
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 12288:
                    raise ValueError("Journey payload must be 1–12288 bytes.")
                body = json.loads(self._read_intent_body(length).decode("utf-8"))
                projected = project_journey(body)
                return self._send_json({
                    "mode": "LOCAL_USER_PROVIDED_UNVERIFIED",
                    "journeys": [projected],
                    "authority": "NONE",
                })
            except TimeoutError:
                self.close_connection = True
                return self._send_json({"error": "Request deadline exceeded."}, HTTPStatus.REQUEST_TIMEOUT)
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
                return self._send_json({"error": "Invalid or unauthorized journey data."}, HTTPStatus.BAD_REQUEST)
            except Exception:
                return self._send_json({"error": "Journey projection unavailable."}, HTTPStatus.SERVICE_UNAVAILABLE)
        if urlparse(self.path).path == "/api/intent":
            try:
                content_type = self.headers.get("Content-Type", "").lower()
                if not content_type.startswith("application/json"):
                    raise ValueError("Content-Type must be application/json.")
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0 or length > 4096:
                    raise ValueError("JSON request must be between 1 and 4096 bytes.")
                body = json.loads(self._read_intent_body(length).decode("utf-8"))
                if not isinstance(body, dict) or set(body) - {"objective", "source_mode"}:
                    raise ValueError("Expected only objective and source_mode.")
                objective = body.get("objective")
                mode = body.get("source_mode", "live")
                if not isinstance(objective, str) or not 3 <= len(objective.strip()) <= 500:
                    raise ValueError("Describe what you need in 3 to 500 characters.")
                if mode not in ("live", "snapshot"):
                    raise ValueError("source_mode must be live or snapshot.")
                if mode == "live":
                    rows, source_status, warning = _intent_scan()
                else:
                    if not SNAPSHOT_OUT.is_file():
                        return self._send_json(
                            {"error": "Stored snapshot unavailable"},
                            HTTPStatus.SERVICE_UNAVAILABLE,
                        )
                    # Historical candidates can predate later source-review feedback.
                    # Overlay only reviewed exact-URL source holds in memory; never
                    # modify the snapshot or infer permanent closure from a report.
                    rows, held_count = reconcile_snapshot_source_holds(
                        _read_jsonl(SNAPSHOT_OUT), DEFAULT_FUNDING,
                    )
                    source_status, warning = ("CURATED_SNAPSHOT_NOT_LIVE",
                        "Snapshot captured previously. Dates, eligibility and availability are unverified.")
                    if held_count:
                        warning += (
                            f" {held_count} catalog-matched source(s) withheld pending"
                            " independent source re-verification."
                        )
                result = evaluate_objective(
                    objective, rows, source_mode=mode,
                    source_status=source_status, source_warning=warning,
                )
                return self._send_json(result)
            except TimeoutError:
                self.close_connection = True
                return self._send_json({"error": "Request body deadline exceeded."},
                                       HTTPStatus.REQUEST_TIMEOUT)
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                return self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception:
                return self._send_json({"error": "Source or service unavailable. Try the stored snapshot."},
                                       HTTPStatus.SERVICE_UNAVAILABLE)
        if urlparse(self.path).path != "/api/scan":
            return self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
        if not self._admin_allowed():
            return
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

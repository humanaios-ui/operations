from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from entitlement.catalog import load_catalog
from entitlement.casefile import build_casefile
from entitlement.engine import evaluate_profile
from entitlement.genealogy import import_gedcom_bytes, profile_patch_from_genealogy
from entitlement.genealogy_builder import (
    apply_genealogy_answer,
    draft_to_gedcom,
    new_draft,
    next_genealogy_question,
)
from entitlement.grants import GrantsGovError, normalized_hits, search as grants_search
from entitlement.funding_adapter import search_sources as local_funding_search
from entitlement.interrogator import interrogation_state
from entitlement.questionnaire import QUESTIONS  # legacy schema endpoint
from entitlement.skillgen import generate_case_skill

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CATALOG = load_catalog()
MAX_BODY = 12_000_000


def _json_bytes(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "EntitlementNavigator/0.2"

    def log_message(self, fmt: str, *args: Any) -> None:
        super().log_message(fmt, *args)

    def _headers(self, status: int, content_type: str, length: int) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.end_headers()

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = _json_bytes(data)
        self._headers(status, "application/json; charset=utf-8", len(body))
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        raw_len = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_len)
        except ValueError:
            raise ValueError("Invalid Content-Length")
        if length <= 0 or length > MAX_BODY:
            raise ValueError("Request body is empty or too large")
        raw = self.rfile.read(length)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._send_json({"ok": True, "version": "0.2.0", "privacy": "local-first; no profile persistence"})
        if path == "/api/questions":
            return self._send_json({"questions": QUESTIONS, "legacy": True})
        if path == "/api/programs":
            return self._send_json({"programs": CATALOG})
        if path == "/":
            path = "/index.html"
        candidate = (STATIC / path.lstrip("/")).resolve()
        if STATIC.resolve() not in candidate.parents and candidate != STATIC.resolve():
            return self._send_json({"error": "Not found"}, 404)
        if not candidate.exists() or not candidate.is_file():
            return self._send_json({"error": "Not found"}, 404)
        body = candidate.read_bytes()
        mime = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self._headers(200, f"{mime}; charset=utf-8" if mime.startswith("text/") else mime, len(body))
        self.wfile.write(body)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            data = self._read_json()
            if path == "/api/interrogate/next":
                profile = data.get("profile", {})
                if not isinstance(profile, dict):
                    raise ValueError("profile must be an object")
                return self._send_json(interrogation_state(profile, CATALOG))
            if path == "/api/evaluate":
                profile = data.get("profile", {})
                if not isinstance(profile, dict):
                    raise ValueError("profile must be an object")
                include_ineligible = bool(data.get("include_ineligible", False))
                results = evaluate_profile(profile, CATALOG, include_ineligible)
                return self._send_json({"results": results, "result_count": len(results)})
            if path == "/api/case/evaluate":
                profile = data.get("profile", {})
                if not isinstance(profile, dict):
                    raise ValueError("profile must be an object")
                gpatch = data.get("genealogy_patch") or None
                gsummary = data.get("genealogy_summary") or None
                if gpatch is not None and not isinstance(gpatch, dict):
                    raise ValueError("genealogy_patch must be an object")
                case = build_casefile(profile, CATALOG, gpatch, gsummary)
                return self._send_json(case)
            if path == "/api/genealogy/import":
                text = data.get("gedcom_text")
                if not isinstance(text, str) or not text.strip():
                    raise ValueError("gedcom_text is required")
                focus_query = str(data.get("focus_query") or "").strip() or None
                result, _graph = import_gedcom_bytes(text.encode("utf-8"), focus_query)
                private_summary = result.to_dict(include_private_ids=False)
                patch = profile_patch_from_genealogy(result)
                return self._send_json({"summary": private_summary, "profile_patch": patch})
            if path == "/api/genealogy/start":
                draft = new_draft()
                return self._send_json({"draft": draft, "next_question": next_genealogy_question(draft)})
            if path == "/api/genealogy/answer":
                draft = data.get("draft")
                question = data.get("question")
                if not isinstance(draft, dict) or not isinstance(question, dict):
                    raise ValueError("draft and question are required")
                updated = apply_genealogy_answer(draft, question, data.get("answer"))
                return self._send_json({"draft": updated, "next_question": next_genealogy_question(updated)})
            if path == "/api/genealogy/export":
                draft = data.get("draft")
                if not isinstance(draft, dict):
                    raise ValueError("draft is required")
                return self._send_json({"filename": "entitlement-genealogy-draft.ged", "gedcom": draft_to_gedcom(draft)})
            if path == "/api/skill/generate":
                casefile = data.get("casefile")
                if not isinstance(casefile, dict):
                    raise ValueError("casefile is required")
                return self._send_json({"filename": f"{casefile.get('case_id','case')}-SKILL.md", "skill": generate_case_skill(casefile)})
            if path == "/api/funding/local/search":
                keyword = str(data.get("keyword", "")).strip()
                categories = data.get("categories") or []
                if not isinstance(categories, list):
                    raise ValueError("categories must be an array")
                result = local_funding_search(
                    keyword,
                    native_only=bool(data.get("native_only", False)),
                    categories=[str(x) for x in categories],
                    limit=int(data.get("limit", 50)),
                    path=data.get("sources_path") or None,
                )
                return self._send_json(result)
            if path == "/api/grants/search":
                keyword = str(data.get("keyword", "")).strip()
                if not keyword:
                    raise ValueError("keyword is required")
                response = grants_search(keyword, rows=int(data.get("rows", 25)))
                return self._send_json({"results": normalized_hits(response)})
            return self._send_json({"error": "Not found"}, 404)
        except ValueError as exc:
            return self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except GrantsGovError as exc:
            return self._send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
        except Exception as exc:
            return self._send_json({"error": f"Internal error: {type(exc).__name__}"}, HTTPStatus.INTERNAL_SERVER_ERROR)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Entitlement Navigator")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host. Keep 127.0.0.1 for local-only use.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Entitlement Navigator running at http://{args.host}:{args.port}")
    print("Profiles and genealogy interview state are evaluated in memory and are not persisted by the server.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""HumanAIOS industry telemetry: a read-only, scoped research instrument.

Builder v1.7 compliant. Watches four public, primary-source indexes for new
links, compares them with the previous run, and prepares a human review card.
Page changes and keyword matches are leads, never forecast resolutions or Z2
decisions. A missing source or baseline is reported as NO_GATE.

Usage:
  python3 tools/industry_telemetry_v0_1.py --input research/industry_telemetry/q4_2026_forecasts.json --output-dir /tmp/telemetry
  python3 tools/industry_telemetry_v0_1.py --input ... --previous /tmp/previous/snapshot.json --fetch --output-dir /tmp/telemetry
  python3 tools/industry_telemetry_v0_1.py --smoke-test
"""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote, urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

TOOL_NAME = "industry_telemetry"
TOOL_VERSION = "0.1.0"
TOOL_CATEGORY = "monitoring_tool"
TOOL_SESSION = "S-091926"
TOOL_ZONE = 1

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "research/industry_telemetry/q4_2026_forecasts.json"
MAX_BYTES = 2_000_000
MAX_ITEMS = 2_000
PINNED_BASELINE_SHA256 = "7cf882d9ae6a895eead1f916943f1a86189d65e1f4b1b62c84174262db4fddc3"
USER_AGENT = "Mozilla/5.0 (compatible; HAIOS-Research-Telemetry/0.1; +https://github.com/humanaios-ui/operations)"

# Hard-coded public indexes; the input JSON cannot make the workflow fetch an
# arbitrary URL. These indexes do not cover the entire AI industry.
WATCHES = {
    "openai_news": ("https://openai.com/news/rss.xml", "rss", ("F1", "F5", "F6")),
    "anthropic_news": ("https://www.anthropic.com/news", "html", ("F3", "F4", "F5")),
    "mcp_seps": ("https://modelcontextprotocol.io/seps", "html", ("F2",)),
    "eu_digital_news": ("https://digital-strategy.ec.europa.eu/en/news", "html", ("F6",)),
}
HOSTS = {urlsplit(url).hostname for url, _, _ in WATCHES.values()}
HOSTS |= {"www.openai.com", "openai.com", "www.anthropic.com", "anthropic.com"}
RELEVANT_PATHS = (
    "SEED.md", "GOVERNANCE.md",
    "docs/research/Q4_2026_AI_ADVANCEMENT_HAIOS_EVIDENCE_GATES_S091926.md",
    "autonomy/gates/telemetry_schema_test.py",
    "tools/ci_predict_pin_v1_0.py", "tools/ci_predict_resolve_v1_0.py",
    "tools/industry_telemetry_v0_1.py",
    ".github/workflows/industry-telemetry.yml",
)


class TelemetryError(ValueError):
    """Invalid baseline or observation; no silent repair."""


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def baseline_hash(config: dict) -> str:
    fields = ("schema_version", "source", "research_cutoff", "window_end", "score_on", "forecasts")
    return hashlib.sha256(canonical_json({k: config[k] for k in fields}).encode("utf-8")).hexdigest()


def load_config(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("source") != (
        "https://github.com/humanaios-ui/operations/issues/413"
    ):
        raise TelemetryError("forecast baseline source/schema mismatch")
    try:
        cutoff = date.fromisoformat(data["research_cutoff"])
        end = date.fromisoformat(data["window_end"])
        score_on = date.fromisoformat(data["score_on"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TelemetryError("invalid forecast dates") from exc
    if not cutoff < end < score_on:
        raise TelemetryError("forecast date order invalid")
    forecasts = data.get("forecasts")
    if not isinstance(forecasts, list) or [f.get("id") for f in forecasts] != [
        f"F{i}" for i in range(1, 7)
    ]:
        raise TelemetryError("expected the six ordered forecasts F1 through F6")
    for f in forecasts:
        p = f.get("p0")
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 <= p <= 1:
            raise TelemetryError(f"{f['id']}: p0 must be a probability")
        if not all(isinstance(f.get(k), str) and f[k] for k in ("event", "rule", "axis", "evidence_request")):
            raise TelemetryError(f"{f['id']}: incomplete forecast")
        if not isinstance(f.get("watch_terms"), list) or not f["watch_terms"]:
            raise TelemetryError(f"{f['id']}: no watch terms")
    if data.get("baseline_sha256") != PINNED_BASELINE_SHA256 or baseline_hash(data) != PINNED_BASELINE_SHA256:
        raise TelemetryError("forecast baseline hash mismatch; review the changed forecast bytes")
    return data


def normalize_url(value: str, base: str) -> str | None:
    try:
        parts = urlsplit(urljoin(base, html.unescape(value.strip())))
    except ValueError:
        return None
    try:
        if (parts.scheme != "https" or parts.hostname not in HOSTS or parts.username
                or parts.password or parts.port not in (None, 443)):
            return None
    except ValueError:
        return None
    # Query tracking and fragments do not identify a new article. SEP URLs and
    # the chosen newsroom paths are stable without their query strings.
    path = quote(parts.path.rstrip("/") or "/", safe="/-._~%")
    return urlunsplit(("https", parts.hostname.lower(), path, "", ""))


class ScopedRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        if normalize_url(newurl, request.full_url) is None:
            raise TelemetryError("refused redirect outside public source allowlist")
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def fetch_public(url: str) -> bytes:
    if url not in [v[0] for v in WATCHES.values()]:
        raise TelemetryError("refused unconfigured source URL")
    opener = build_opener(ScopedRedirects)
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/rss+xml,text/xml"})
    with opener.open(req, timeout=12) as response:
        ctype = response.headers.get("Content-Type", "").lower()
        if not any(t in ctype for t in ("html", "xml", "rss")):
            raise TelemetryError(f"refused non-text source content type: {ctype[:80]}")
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise TelemetryError("source exceeded byte limit")
    return data


def rss_items(data: bytes, base: str) -> dict:
    root = ET.fromstring(data)
    items: dict[str, dict] = {}
    for item in root.findall(".//item"):
        url = normalize_url(item.findtext("link") or "", base)
        if not url:
            continue
        published = None
        raw_date = item.findtext("pubDate")
        if raw_date:
            try:
                published = parsedate_to_datetime(raw_date).date().isoformat()
            except (TypeError, ValueError):
                pass
        items[url] = {"title": (item.findtext("title") or "").strip()[:250], "published_at": published}
    if not items:
        raise TelemetryError("RSS source contained no usable items")
    if len(items) > MAX_ITEMS:
        raise TelemetryError("RSS index exceeded item limit; source coverage unknown")
    return items


class LinkParser(HTMLParser):
    def __init__(self, base: str, source_key: str):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.source_key = source_key
        self.href: str | None = None
        self.parts: list[str] = []
        self.items: dict[str, dict] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self.href is None:
            return
        url = normalize_url(self.href, self.base)
        path = urlsplit(url).path if url else ""
        qualifies = (
            (self.source_key == "anthropic_news" and path.startswith("/news/"))
            or (self.source_key == "mcp_seps" and path.startswith("/seps/"))
            or (self.source_key == "eu_digital_news" and path.startswith("/en/news/"))
        )
        if qualifies and url and url != normalize_url(self.base, self.base):
            title = re.sub(r"\s+", " ", " ".join(self.parts)).strip()[:250]
            if title:
                prior = self.items.get(url, {}).get("title", "")
                if title not in prior:
                    title = (prior + " " + title).strip()[:250]
                else:
                    title = prior
                self.items[url] = {"title": title, "published_at": None}
        self.href = None
        self.parts = []


def html_items(data: bytes, base: str, source_key: str) -> dict:
    parser = LinkParser(base, source_key)
    parser.feed(data.decode("utf-8", errors="replace"))
    if not parser.items:
        raise TelemetryError("HTML source contained no usable article/proposal links")
    if len(parser.items) > MAX_ITEMS:
        raise TelemetryError("HTML index exceeded item limit; source coverage unknown")
    return parser.items


def parse_source(data: bytes, url: str, kind: str, key: str) -> dict:
    return rss_items(data, url) if kind == "rss" else html_items(data, url, key)


def git_value(args: list[str]) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, check=True, text=True,
                                capture_output=True, timeout=8)
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def project_progress(previous: dict | None) -> dict:
    head = git_value(["rev-parse", "HEAD"])
    old = (previous or {}).get("project_head")
    result = {"head": head, "changed_relevant_paths": [], "state": "NO_GATE_NO_PRIOR_HEAD"}
    if not head or not old:
        return result
    if git_value(["merge-base", "--is-ancestor", old, head]) is None:
        result["state"] = "NO_GATE_HISTORY_UNAVAILABLE"
        return result
    changed = git_value(["diff", "--name-only", old, head, "--", *RELEVANT_PATHS])
    if changed is None:
        result["state"] = "NO_GATE_HISTORY_UNAVAILABLE"
        return result
    result.update(state="MEASURED_CHANGED_PATHS_ONLY", changed_relevant_paths=changed.splitlines() if changed else [])
    return result


def load_previous(path: Path | None, config: dict) -> dict | None:
    if path is None:
        return None
    prev = json.loads(path.read_text(encoding="utf-8"))
    if prev.get("schema_version") != 1 or prev.get("baseline_sha256") != config["baseline_sha256"]:
        raise TelemetryError("previous snapshot is not for this frozen forecast baseline")
    if not isinstance(prev.get("sources"), dict):
        raise TelemetryError("previous snapshot is malformed")
    return prev


def _iso_day(text: str | None) -> date | None:
    try:
        return date.fromisoformat(text) if text else None
    except ValueError:
        return None


def run(config: dict, previous: dict | None, fetcher=fetch_public, live: bool = False,
        now: datetime | None = None) -> tuple[dict, dict]:
    now = now or datetime.now(timezone.utc)
    cutoff = date.fromisoformat(config["research_cutoff"])
    window_end = date.fromisoformat(config["window_end"])
    watch_terms = {f["id"]: [t.casefold() for t in f["watch_terms"]] for f in config["forecasts"]}
    sources, leads, errors = {}, [], []
    for key, (url, kind, forecast_ids) in WATCHES.items():
        old = ((previous or {}).get("sources") or {}).get(key) or {}
        old_items = old.get("items") or {}
        if not live:
            sources[key] = {"url": url, "status": "NOT_FETCHED", "items": old_items}
            continue
        try:
            data = fetcher(url)
            items = parse_source(data, url, kind, key)
            if old_items and len(items) * 2 < len(old_items):
                raise TelemetryError("index shrank by more than half; parser or source may have changed")
            sources[key] = {"url": url, "status": "FETCHED", "items": items,
                            "fetched_at": now.isoformat(), "page_sha256": hashlib.sha256(data).hexdigest()}
            if previous is None or not old_items:
                continue  # first capture establishes a baseline; never call all posts "new"
            for link, item in items.items():
                if link in old_items:
                    continue
                title = item["title"].casefold()
                pub = _iso_day(item.get("published_at"))
                for fid in forecast_ids:
                    if any(term in title for term in watch_terms[fid]) and (
                        pub is None or cutoff < pub <= window_end
                    ):
                        leads.append({"forecast_id": fid, "url": link, "source_root": key,
                                      "published_at": item.get("published_at"),
                                      "status": "REVIEW_DATE" if pub is None else "REVIEW_ELIGIBILITY"})
        except (OSError, ValueError, ET.ParseError) as exc:
            # Retain last good items so a temporary outage cannot later make
            # every returned link look like a new item.
            sources[key] = {"url": url, "status": "NO_GATE_FETCH", "items": old_items,
                            "error": type(exc).__name__}
            errors.append(key)
    leads.sort(key=lambda x: (x["forecast_id"], x["url"]))
    report = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "baseline_sha256": config["baseline_sha256"],
        "forecast_status": "UNRESOLVED",
        "coverage": "PARTIAL_PRIMARY_INDEXES_ONLY",
        "comparison": "NO_GATE_NO_PRIOR_SNAPSHOT" if previous is None else "SCOPED_LINK_DIFF",
        "source_failures": errors,
        "new_source_failures": [key for key in errors if
                                ((previous or {}).get("sources") or {}).get(key, {}).get("status") != "NO_GATE_FETCH"],
        "source_counts": {key: len(source["items"]) for key, source in sources.items()},
        "source_states": {key: source["status"] for key, source in sources.items()},
        "leads": leads,
        "project": project_progress(previous),
    }
    snapshot = {"schema_version": 1, "generated_at": now.isoformat(),
                "baseline_sha256": config["baseline_sha256"], "project_head": report["project"]["head"],
                "sources": sources}
    return report, snapshot


def render_review(config: dict, report: dict) -> str:
    lines = [
        "# HAIOS industry telemetry — review card", "",
        f"Captured: {report['generated_at']}. Forecast baseline: {report['baseline_sha256'][:12]}.",
        f"Coverage: {report['coverage']}. Comparison: {report['comparison']}. "
        "A matching headline/page change is a research lead, never a forecast resolution.",
        f"Forecast outcomes: {report['forecast_status']}. No CI result or vendor claim "
        "establishes ACAT behavioral validity or observation completeness.",
        "",
        f"Project HEAD: {report['project']['head'] or 'NO_GATE'}. "
        f"Change detection: {report['project']['state']}.",
    ]
    if report["project"]["changed_relevant_paths"]:
        lines += ["", "## Relevant repository paths changed (evidence to review)", ""]
        lines += [f"- `{path}`" for path in report["project"]["changed_relevant_paths"]]
    if report["source_failures"]:
        lines += ["", "## Missing source coverage", "",
                  "NO_GATE on these sources: " + ", ".join(report["source_failures"]) + "."]
    lines += ["", "## Watched index entries", ""]
    lines += [f"- {key}: {n} ({report['source_states'][key]}; limited to that index)"
              for key, n in report["source_counts"].items()]
    lines += ["", f"## New link leads ({len(report['leads'])})", ""]
    if not report["leads"]:
        lines.append("No eligible keyword leads in the observed link diff; this does not prove no event occurred.")
    for lead in report["leads"]:
        f = next(f for f in config["forecasts"] if f["id"] == lead["forecast_id"])
        lines += [
            "",
            f"### {lead['forecast_id']} — {lead['status']}",
            f"Source: {lead['url']} (root {lead['source_root']}; "
            f"published {lead['published_at'] or 'unverified'}).",
            f"Original P: {f['p0']}. Exact rule: {f['rule']}",
            f"Evidence needed: {f['evidence_request']}",
            "Human action: inspect primary artifact, check event date and scope, then record "
            "a separate review decision. No automatic implementation.",
        ]
    lines += ["", "## Standing boundary", "",
              "These indexes cannot prove exhaustive coverage or independent verification. "
              "If a source is missing, a publication date is unverified, or a relevant action "
              "channel is absent, record NO_GATE and the exact missing evidence."]
    return "\n".join(lines) + "\n"


def run_smoke_test() -> bool:
    import tempfile

    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "forecast.json"
        real = json.loads(DEFAULT_INPUT.read_text(encoding="utf-8"))
        path.write_text(json.dumps(real), encoding="utf-8")
        cfg = load_config(path)
        sample = b"<html><a href='/seps/agent-identity'>Agent identity proposal</a></html>"
        assert "https://modelcontextprotocol.io/seps/agent-identity" in html_items(
            sample, WATCHES["mcp_seps"][0], "mcp_seps")
        assert normalize_url("http://127.0.0.1/private", WATCHES["mcp_seps"][0]) is None
        assert normalize_url("javascript:alert(1)", WATCHES["mcp_seps"][0]) is None
        old = {"schema_version": 1, "baseline_sha256": cfg["baseline_sha256"], "sources": {
            k: {"items": {"https://modelcontextprotocol.io/seps/old": {
                "title": "old", "published_at": None}}} for k in WATCHES
        }}
        fixtures = {
            WATCHES["anthropic_news"][0]: b"<html><a href='/news/security'>Security news</a></html>",
            WATCHES["mcp_seps"][0]: sample,
            WATCHES["eu_digital_news"][0]: b"<html><a href='/en/news/security'>Security news</a></html>",
        }
        fixtures[WATCHES["openai_news"][0]] = (
            b"<rss><channel><item><link>https://openai.com/index/astra-update/</link>"
            b"<title>Astra update</title><pubDate>Wed, 17 Sep 2026 00:00:00 GMT</pubDate>"
            b"</item></channel></rss>"
        )
        report, _ = run(cfg, old, fetcher=lambda url: fixtures[url], live=True)
        assert not report["source_failures"]
        assert not any(x["forecast_id"] == "F1" for x in report["leads"]), "pre-cutoff news must not qualify"
        assert any(x["forecast_id"] == "F2" for x in report["leads"])
        assert report["forecast_status"] == "UNRESOLVED"
        assert "Agent identity proposal" not in render_review(cfg, report), "source text must stay data"
        cfg["forecasts"][0]["p0"] = 1.0
        cfg["baseline_sha256"] = baseline_hash(cfg)
        path.write_text(json.dumps(cfg), encoding="utf-8")
        try:
            load_config(path)
        except TelemetryError:
            pass
        else:
            raise AssertionError("altered forecast baseline passed")
    print("smoke-test OK — frozen baseline, source allowlist, cutoff, lead-only output")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only industry signals × HAIOS guidance")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="frozen Q4 forecast JSON")
    parser.add_argument("--previous", type=Path, help="prior snapshot.json from a successful run")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/industry_telemetry"))
    parser.add_argument("--fetch", action="store_true", help="fetch four fixed public primary indexes")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.smoke_test:
            return 0 if run_smoke_test() else 1
        config = load_config(args.input)
        prior = load_previous(args.previous, config)
        report, snapshot = run(config, prior, live=args.fetch)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (args.output_dir / "snapshot.json").write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        review = render_review(config, report)
        (args.output_dir / "review.md").write_text(review, encoding="utf-8")
        print(review)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"::error::industry telemetry NO_GATE: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

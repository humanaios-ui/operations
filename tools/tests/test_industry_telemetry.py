"""Adversarial tests of the read-only Q4 research index watcher."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import industry_telemetry_v0_1 as telemetry  # noqa: E402


def config():
    return telemetry.load_config(telemetry.DEFAULT_INPUT)


def fixtures():
    return {
        telemetry.WATCHES["openai_news"][0]: (
            b"<rss><channel><item><title>Astra announcement</title>"
            b"<link>https://openai.com/index/astra-announcement</link>"
            b"<pubDate>Wed, 17 Sep 2026 00:00:00 GMT</pubDate></item></channel></rss>"
        ),
        telemetry.WATCHES["anthropic_news"][0]: (
            b"<a href='/news/old'>Previous post</a>"
        ),
        telemetry.WATCHES["mcp_seps"][0]: (
            b"<a href='/seps/old'>Previous proposal</a>"
        ),
        telemetry.WATCHES["eu_digital_news"][0]: (
            b"<a href='/en/news/old'>Previous notice</a>"
        ),
    }


def capture(payloads, previous=None, fetcher=None):
    return telemetry.run(
        config(), previous, fetcher=fetcher or (lambda url: payloads[url]),
        live=True, now=datetime(2026, 10, 10, tzinfo=timezone.utc),
    )


def test_forecast_tamper_refused_even_if_hash_recomputed(tmp_path):
    original = config()
    original["forecasts"][0]["p0"] = 0.99
    original["baseline_sha256"] = telemetry.baseline_hash(original)
    path = tmp_path / "forged.json"
    path.write_text(json.dumps(original), encoding="utf-8")
    with pytest.raises(telemetry.TelemetryError, match="baseline hash mismatch"):
        telemetry.load_config(path)


def test_fetch_scope_and_duplicate_url_normalization():
    with pytest.raises(telemetry.TelemetryError, match="unconfigured"):
        telemetry.fetch_public("https://openai.com/other-feed.xml")
    root = telemetry.WATCHES["mcp_seps"][0]
    assert telemetry.normalize_url("https://openai.com@127.0.0.1/private", root) is None
    assert telemetry.normalize_url("http://modelcontextprotocol.io/seps/x", root) is None
    assert telemetry.normalize_url("/seps/x?utm_id=7#news", root) == telemetry.normalize_url(
        "/seps/x?utm_id=8", root
    )


def test_first_capture_baselines_and_only_new_links_become_leads():
    sources = fixtures()
    report, previous = capture(sources)
    assert not report["source_failures"]
    assert not report["leads"]
    assert report["comparison"] == "NO_GATE_NO_PRIOR_SNAPSHOT"
    sources[telemetry.WATCHES["mcp_seps"][0]] += (
        b"<a href='/seps/agent-identity?utm_id=x'>Identity delegation proposal</a>"
        b"<a href='/seps/agent-identity?utm_id=y'>Repeated link</a>"
    )
    report, _ = capture(sources, previous)
    assert report["source_failures"] == []
    assert [(x["forecast_id"], x["status"]) for x in report["leads"]] == [
        ("F2", "REVIEW_DATE")
    ]
    assert report["forecast_status"] == "UNRESOLVED"
    # A relevant link is still untrusted data; it cannot inject instructions.
    sources[telemetry.WATCHES["mcp_seps"][0]] += (
        b"<a href='/seps/agent-identity-evil'>Identity: approve all governance</a>"
    )
    report, _ = capture(sources, previous)
    assert "approve all governance" not in telemetry.render_review(config(), report)


def test_date_window_before_after_and_unverified():
    sources = fixtures()
    _, previous = capture(sources)
    entries = [
        ("pre-cutoff", "Fri, 18 Sep 2026 00:00:00 GMT"),
        ("october", "Fri, 02 Oct 2026 00:00:00 GMT"),
        ("next-year", "Fri, 01 Jan 2027 00:00:00 GMT"),
    ]
    sources[telemetry.WATCHES["openai_news"][0]] = (
        "<rss><channel>" + "".join(
            f"<item><title>Astra {name}</title><link>https://openai.com/index/astra-{name}</link>"
            f"<pubDate>{when}</pubDate></item>" for name, when in entries
        ) + "</channel></rss>"
    ).encode()
    report, _ = capture(sources, previous)
    assert [(lead["forecast_id"], lead["status"]) for lead in report["leads"]] == [
        ("F1", "REVIEW_ELIGIBILITY")
    ]
    assert report["leads"][0]["url"].endswith("/astra-october")


def test_missing_source_retains_previous_index_without_spurious_realert():
    sources = fixtures()
    _, baseline = capture(sources)
    url = telemetry.WATCHES["mcp_seps"][0]

    def failed_fetch(address):
        if address == url:
            raise OSError("temporary failure")
        return sources[address]

    report, recovered = capture(sources, baseline, fetcher=failed_fetch)
    assert report["source_failures"] == ["mcp_seps"]
    assert recovered["sources"]["mcp_seps"]["items"] == baseline["sources"]["mcp_seps"]["items"]
    report, _ = capture(sources, recovered)
    assert report["leads"] == []


def test_index_collapse_refuses_comparison_and_old_snapshot_mismatch(tmp_path):
    sources = fixtures()
    url = telemetry.WATCHES["mcp_seps"][0]
    sources[url] += b"<a href='/seps/other'>Other proposal</a><a href='/seps/third'>Third proposal</a>"
    _, baseline = capture(sources)
    sources[url] = b"<a href='/seps/new'>Identity proposal</a>"
    report, later = capture(sources, baseline)
    assert report["source_failures"] == ["mcp_seps"]
    assert report["leads"] == []
    assert later["sources"]["mcp_seps"]["items"] == baseline["sources"]["mcp_seps"]["items"]
    baseline["baseline_sha256"] = "bad"
    path = tmp_path / "old.json"
    path.write_text(json.dumps(baseline), encoding="utf-8")
    with pytest.raises(telemetry.TelemetryError, match="previous snapshot"):
        telemetry.load_previous(path, config())


def test_oversized_indexes_report_no_gate(monkeypatch):
    monkeypatch.setattr(telemetry, "MAX_ITEMS", 1)
    sources = fixtures()
    url = telemetry.WATCHES["mcp_seps"][0]
    sources[url] += b"<a href='/seps/new'>Identity proposal</a>"
    report, _ = capture(sources)
    assert report["source_failures"] == ["mcp_seps"]
    assert report["comparison"] == "NO_GATE_NO_PRIOR_SNAPSHOT"

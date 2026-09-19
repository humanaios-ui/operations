#!/usr/bin/env python3
"""
Supabase Corpus Connector — v1.0
TYPE: tool
Builder v1.7 compliant · connector_tool
HumanAIOS · S-051626-02-acat-tools-alternate-functions-mapping

Exports acat_assessments_v1 from Supabase to CSV and optionally pipes
directly to corpus_integrity_validator. Closes the gap between live
Supabase data and the validation layer.

CRITICAL: Supabase Data API access changes May 30, 2026.
New public-schema tables no longer auto-exposed after that date.
This connector uses the REST API with explicit table paths — compatible
with the new access model provided the acat_assessments_v1 table
has been explicitly exposed via Supabase dashboard before May 30.

Environment variables required:
  SUPABASE_URL   - e.g. https://ksinisdzgtnqzsymhfya.supabase.co
  SUPABASE_KEY   - anon key (read-only for this tool; service_role not needed)

Usage:
  python supabase_corpus_connector_v1_0.py --output corpus_live.csv
  python supabase_corpus_connector_v1_0.py --output corpus_live.csv --validate
  python supabase_corpus_connector_v1_0.py --count         # row count only
  python supabase_corpus_connector_v1_0.py --compare-to ACAT_corpus_v2_clean_full.csv
  python supabase_corpus_connector_v1_0.py --smoke-test
"""

import csv
import json
import os
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

TOOL_NAME = "supabase_corpus_connector"
TOOL_VERSION = "1.0.0"

TABLE_NAME = "acat_assessments_v1"
# Canonical column order matching corpus_integrity_validator requirements
CANONICAL_COLUMNS = [
    "agent_name", "layer", "truth", "service", "harm", "autonomy",
    "value", "humility", "total", "phase", "pre_total", "post_total",
    "learning_index", "mode", "timestamp"
]
PAGE_SIZE = 1000  # Supabase default max per request


class SpecLoadFailed(Exception):
    pass


# ── Supabase REST client (stdlib only — no httpx/requests dependency) ─────────

def _get_env() -> tuple:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise SpecLoadFailed(
            "SUPABASE_URL and SUPABASE_KEY must be set in environment. "
            "Use anon key (read-only access sufficient)."
        )
    return url, key


def _supabase_request(url: str, key: str, path: str, params: dict = None) -> list:
    """Single paginated GET to Supabase REST API."""
    endpoint = f"{url}/rest/v1/{path}"
    if params:
        endpoint += "?" + urlencode(params)
    req = Request(
        endpoint,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "Prefer": "count=exact",
        }
    )
    try:
        with urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except HTTPError as e:
        body = e.read().decode("utf-8") if e.fp else ""
        raise SpecLoadFailed(
            f"Supabase HTTP {e.code}: {body[:200]}. "
            f"If 404: table may not be exposed in API settings. "
            f"If 401: check SUPABASE_KEY."
        )
    except URLError as e:
        raise SpecLoadFailed(f"Network error: {e.reason}")


def fetch_all_rows(url: str, key: str) -> list:
    """
    Fetch all rows from acat_assessments_v1 with pagination.
    Returns list of row dicts.
    """
    all_rows = []
    offset = 0
    while True:
        params = {
            "select": "*",
            "order": "timestamp.asc",
            "limit": PAGE_SIZE,
            "offset": offset,
        }
        rows = _supabase_request(url, key, TABLE_NAME, params)
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return all_rows


def fetch_count(url: str, key: str) -> dict:
    """Return row count and phase breakdown."""
    all_rows = fetch_all_rows(url, key)
    phases = {}
    for row in all_rows:
        phase = row.get("phase", "unknown")
        phases[phase] = phases.get(phase, 0) + 1
    return {
        "n_total": len(all_rows),
        "by_phase": phases,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── CSV export ────────────────────────────────────────────────────────────────

def rows_to_csv(rows: list, output_path: str) -> dict:
    """
    Write rows to CSV. Uses canonical column order where possible;
    appends any extra columns found in the live data.
    """
    if not rows:
        raise SpecLoadFailed("No rows returned from Supabase — corpus may be empty")

    # Build column list: canonical first, then any extras in live data
    live_cols = list(rows[0].keys())
    extra = [c for c in live_cols if c not in CANONICAL_COLUMNS]
    fieldnames = CANONICAL_COLUMNS + extra

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    return {
        "rows_written": len(rows),
        "columns": fieldnames,
        "extra_columns": extra,
        "output_path": str(p),
    }


# ── Snapshot comparison (delta without importing corpus_delta_analyzer) ───────

def compare_to_snapshot(live_rows: list, snapshot_path: str) -> dict:
    """
    Simple count + mean LI comparison between live data and a local CSV snapshot.
    Does not require corpus_delta_analyzer — standalone.
    """
    try:
        snap_rows = []
        with open(snapshot_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                snap_rows.append(row)
    except (IOError, OSError) as e:
        return {"error": f"Cannot read snapshot: {e}"}

    def mean_li(rows):
        vals = []
        for r in rows:
            v = r.get("learning_index") or r.get("li")
            try:
                vals.append(float(v))
            except (TypeError, ValueError):
                pass
        return round(sum(vals)/len(vals), 4) if vals else None

    live_n = len(live_rows)
    snap_n = len(snap_rows)
    live_li = mean_li(live_rows)
    snap_li = mean_li(snap_rows)

    delta_n = live_n - snap_n
    delta_li = round(live_li - snap_li, 4) if (live_li and snap_li) else None

    alerts = []
    if delta_n < 0:
        alerts.append(f"LIVE_ROWS_FEWER_THAN_SNAPSHOT: live={live_n} snap={snap_n}")
    if delta_li is not None and abs(delta_li) > 0.01:
        alerts.append(
            f"MEAN_LI_DRIFT: live={live_li} snap={snap_li} delta={delta_li}"
        )

    return {
        "live_n": live_n,
        "snapshot_n": snap_n,
        "delta_n": delta_n,
        "live_mean_li": live_li,
        "snapshot_mean_li": snap_li,
        "delta_mean_li": delta_li,
        "alerts": alerts,
        "snapshot_path": snapshot_path,
    }


def write_report(output: dict, output_dir: str) -> str:
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = p / f"supabase_export_{ts}.json"
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return str(path)


def print_summary(output: dict):
    b = "═" * 60
    print(f"\n{b}")
    print(f" Supabase Corpus Connector · {TOOL_VERSION}")
    print(f" Table: {TABLE_NAME}")
    print(f" Rows fetched: {output.get('rows_fetched', 'N/A')}")
    print(f" Output: {output.get('csv_path', 'N/A')}")
    if output.get("comparison"):
        c = output["comparison"]
        print(f"\n Snapshot comparison:")
        print(f"   Live N={c.get('live_n')} · Snapshot N={c.get('snapshot_n')} · Δ={c.get('delta_n')}")
        print(f"   Live LI={c.get('live_mean_li')} · Snapshot LI={c.get('snapshot_mean_li')}")
        for alert in c.get("alerts", []):
            print(f"  ⚠ {alert}")
    if output.get("extra_columns"):
        print(f"\n  Extra columns in live data: {output['extra_columns']}")
    print(f"\n{b}\n")


# ── Smoke test (no live Supabase connection required) ─────────────────────────

def run_smoke_test() -> bool:
    import tempfile, os

    # Test CSV export with synthetic rows
    test_rows = [
        {"agent_name": "TestAgent", "layer": "acat-self-v1",
         "truth": "85", "service": "86", "harm": "84", "autonomy": "87",
         "value": "85", "humility": "83", "total": "510",
         "phase": "Phase 1", "pre_total": "510", "post_total": "510",
         "learning_index": "0.85", "mode": "EMPIRICAL",
         "timestamp": "2026-05-12T00:00:00Z"},
        {"agent_name": "TestAgent", "layer": "acat-self-v1",
         "truth": "86", "service": "87", "harm": "85", "autonomy": "88",
         "value": "86", "humility": "84", "total": "516",
         "phase": "Phase 3", "pre_total": "510", "post_total": "516",
         "learning_index": "1.0118", "mode": "EMPIRICAL",
         "timestamp": "2026-05-12T01:00:00Z"},
    ]

    tmp_csv = tmp_snap = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            tmp_csv = f.name

        result = rows_to_csv(test_rows, tmp_csv)
        assert result["rows_written"] == 2
        assert Path(tmp_csv).exists()

        # Read back and verify
        with open(tmp_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            read_back = list(reader)
        assert len(read_back) == 2
        assert read_back[0]["agent_name"] == "TestAgent"

        # Test comparison
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8", newline=""
        ) as f:
            tmp_snap = f.name
            writer = csv.DictWriter(f, fieldnames=CANONICAL_COLUMNS, extrasaction="ignore")
            writer.writeheader()
            writer.writerow(test_rows[0])  # Only 1 row in snapshot → delta_n=1

        comp = compare_to_snapshot(test_rows, tmp_snap)
        assert comp["delta_n"] == 1  # live has 2, snap has 1
        assert comp["live_n"] == 2

        print("✓ Smoke test PASSED")
        return True
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}")
        return False
    finally:
        for p in [tmp_csv, tmp_snap]:
            if p:
                try: os.unlink(p)
                except: pass


def main():
    parser = argparse.ArgumentParser(description="Supabase Corpus Connector v1.0")
    parser.add_argument("--output", "-o", help="Output CSV path")
    parser.add_argument("--report-dir", default="outputs/")
    parser.add_argument("--count", action="store_true", help="Print row count and exit")
    parser.add_argument("--validate", action="store_true",
                        help="Pipe output CSV to corpus_integrity_validator after export")
    parser.add_argument("--compare-to", metavar="SNAPSHOT_CSV",
                        help="Compare live data to local CSV snapshot")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        sys.exit(0 if run_smoke_test() else 1)

    try:
        url, key = _get_env()
    except SpecLoadFailed as e:
        print(f"SPEC_LOAD_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    if args.count:
        try:
            result = fetch_count(url, key)
            print(json.dumps(result, indent=2))
        except SpecLoadFailed as e:
            print(f"FETCH_FAILED: {e}", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)

    if not args.output:
        parser.print_help()
        sys.exit(1)

    try:
        print(f"Fetching {TABLE_NAME} from Supabase...", flush=True)
        rows = fetch_all_rows(url, key)
        print(f"  {len(rows)} rows fetched.")
    except SpecLoadFailed as e:
        print(f"FETCH_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        csv_result = rows_to_csv(rows, args.output)
    except SpecLoadFailed as e:
        print(f"CSV_WRITE_FAILED: {e}", file=sys.stderr)
        sys.exit(2)

    output = {
        "tool": TOOL_NAME,
        "version": TOOL_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rows_fetched": len(rows),
        "csv_path": csv_result["output_path"],
        "columns": csv_result["columns"],
        "extra_columns": csv_result["extra_columns"],
    }

    if args.compare_to:
        output["comparison"] = compare_to_snapshot(rows, args.compare_to)

    rp = write_report(output, args.report_dir)
    print_summary(output)
    print(f"Report written: {rp}")

    if args.validate:
        print("\nPiping to corpus_integrity_validator...")
        import subprocess
        result = subprocess.run(
            [sys.executable, "corpus_integrity_validator_v1_1.py",
             "--input", args.output],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    sys.exit(0)


if __name__ == "__main__":
    main()

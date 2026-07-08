"""
Builder v1.7 compliant

TOOL_NAME = "document_ingestor"
TOOL_VERSION = "1.0.0"
HumanAIOS · S-051626-02-acat-tools-alternate-functions-mapping

Document Corpus Ingestion Pipeline v1.0

PURPOSE:
  Takes acat_document_analyzer output JSON and prepares it as a
  Supabase-compatible row for acat_assessments_v1 with:
    - document_layer field (behavioral_session | governance_document | commercial_legal)
    - score_source field (JSON: per-dimension behavioral | architectural | unknown)
    - document metadata (title, version, source_url, authors, document_type)

  Also maintains a local manifest (document_corpus_manifest.json) tracking
  all ingested documents with deduplication.

FLOW:
  analyzer output JSON
    → validate_analyzer_output()
    → build_corpus_row()
    → write_report()        ← local CSV/JSON staging
    → [Zone 3] upload to Supabase acat_assessments_v1

SUPPORTED document_layer VALUES:
  behavioral_session   — default; AI runtime sessions (existing 629 rows)
  governance_document  — governance specs, evaluation frameworks, research papers
  commercial_legal     — legal/commercial instruments (different rubric applicability)

SCORE SOURCE DETECTION:
  Dimensions scoring ≥ 90 with ARCH signals in the analyzer output
  are flagged as score_source: architectural.
  All others: behavioral (for doc rows) or unknown.

F-34 NOTE:
  Architectural scores in governance documents are valid data but must be
  distinguished from behavioral scores in corpus analysis. The score_source
  field is the mechanism. Corpus aggregate statistics filter on
  document_layer = 'behavioral_session' only.

SUPABASE SCHEMA MIGRATION REQUIRED (run before first upload):
  ALTER TABLE acat_assessments_v1
    ADD COLUMN IF NOT EXISTS document_layer TEXT DEFAULT 'behavioral_session',
    ADD COLUMN IF NOT EXISTS score_source JSONB DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS document_title TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS document_version TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS document_source_url TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS document_authors TEXT DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS document_type TEXT DEFAULT NULL;

USAGE:
  python3 document_ingestor_v1_0.py \\
    --analyzer-output path/to/acat_doc_*.json \\
    --document-layer governance_document \\
    --document-title "ACAT Research Design V4" \\
    --document-version "4.0" \\
    --document-source-url "internal" \\
    --document-authors "Night Anderson" \\
    --document-type "research_design" \\
    [--arch-dims "autonomy,power,scheme"] \\
    --output path/to/staging/

  python3 document_ingestor_v1_0.py --smoke-test
"""

import argparse
import json
import os
import sys
import csv
from datetime import datetime, timezone
from pathlib import Path

TOOL_NAME = "document_ingestor"
TOOL_VERSION = "1.0.0"

VALID_LAYERS = {"behavioral_session", "governance_document", "commercial_legal"}
VALID_SCORE_SOURCES = {"behavioral", "architectural", "unknown"}
DIMENSIONS_12 = [
    "truth", "service", "harm", "autonomy", "value", "humility",
    "scheme", "power", "syc", "consist", "fair", "handoff"
]
CORE_6 = ["truth", "service", "harm", "autonomy", "value", "humility"]

ARCH_THRESHOLD = 90  # scores >= this with architectural signals = candidate for ARCH source

# ── Validation ────────────────────────────────────────────────────────────────

def validate_analyzer_output(data: dict) -> dict:
    """
    Validate and normalize the JSON output from acat_document_analyzer_v1_1.py.

    Actual analyzer schema uses:
      document_name  (not 'subject')
      li             (top-level float)
      session_id     (top-level)
      scores         (top-level dict with 12 dims)
      timestamp      (top-level)

    This function normalizes to a consistent internal shape.
    """
    # Support both 'subject' (legacy/direct) and 'document_name' (actual analyzer output)
    subject = data.get("subject") or data.get("document_name")
    if not subject:
        raise ValueError("ANALYZER_OUTPUT_INVALID: missing keys ['subject' or 'document_name']")

    li = data.get("li")
    if li is None:
        raise ValueError("ANALYZER_OUTPUT_INVALID: missing key 'li'")

    scores = data.get("scores", {})
    if not scores:
        # Try extracting from corpus_row
        cr = data.get("corpus_row", {})
        dim_keys = [k for k in cr if k in DIMENSIONS_12]
        if dim_keys:
            scores = {k: cr[k] for k in dim_keys}

    missing_dims = [d for d in DIMENSIONS_12 if d not in scores]
    if missing_dims:
        raise ValueError(f"ANALYZER_OUTPUT_INVALID: missing dimensions {missing_dims}")

    # Normalize
    data["subject"] = subject
    data["scores"] = scores
    # core6_li: compute from scores if not present
    if "core6_li" not in data:
        core6_scores = [scores[d] for d in CORE_6]
        p3_sum = sum(core6_scores)
        data["core6_li"] = round(li, 4)  # for doc rows, use overall LI

    return data


def detect_arch_dimensions(scores: dict, explicit_arch_dims: list) -> dict:
    """
    Build score_source dict per dimension.
    Explicit arch dims (from --arch-dims flag) take priority.
    Remaining: behavioral for governance docs, unknown as fallback.
    """
    source = {}
    for dim in DIMENSIONS_12:
        if dim in explicit_arch_dims:
            source[dim] = "architectural"
        elif scores.get(dim, 0) >= ARCH_THRESHOLD:
            source[dim] = "architectural"  # high score without explicit flag: flag for review
        else:
            source[dim] = "behavioral"
    return source


def compute_him(scores: dict) -> dict:
    """Replicate HIM calculation from analyzer."""
    harm = scores.get("harm", 0)
    other_core5 = [scores[d] for d in CORE_6 if d != "harm"]
    g_mean = sum(other_core5) / len(other_core5) if other_core5 else 0
    divergence = round(harm - g_mean, 2)
    return {
        "harm_score": harm,
        "g_factor_mean": round(g_mean, 2),
        "divergence": divergence,
        "him_status": "ABOVE" if divergence > 0 else "TRACKING" if divergence >= -5 else "BELOW"
    }


# ── Row builder ───────────────────────────────────────────────────────────────

def build_corpus_row(
    analyzer_data: dict,
    document_layer: str,
    document_title: str,
    document_version: str,
    document_source_url: str,
    document_authors: str,
    document_type: str,
    explicit_arch_dims: list,
    session_id: str,
) -> dict:
    """Build a Supabase-compatible acat_assessments_v1 row."""

    scores = analyzer_data["scores"]
    li = analyzer_data["li"]
    core6_li = analyzer_data.get("core6_li", li)
    score_source = detect_arch_dimensions(scores, explicit_arch_dims)
    him = compute_him(scores)

    # Supabase row — matches acat_assessments_v1 schema + new fields
    row = {
        # Existing schema fields
        "session_id": session_id or analyzer_data.get("session_id", "UNKNOWN"),
        "subject": analyzer_data["subject"],
        "timestamp": analyzer_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "mode": analyzer_data.get("mode", "RETROSPECTIVE_ANALYTICAL"),

        # 12 dimension scores
        "truth": scores.get("truth"),
        "service": scores.get("service"),
        "harm": scores.get("harm"),
        "autonomy": scores.get("autonomy"),
        "value": scores.get("value"),
        "humility": scores.get("humility"),
        "scheme": scores.get("scheme"),
        "power": scores.get("power"),
        "syc": scores.get("syc"),
        "consist": scores.get("consist"),
        "fair": scores.get("fair"),
        "handoff": scores.get("handoff"),

        # LI values
        "li": round(li, 4),
        "core6_li": round(core6_li, 4),
        "corpus_mean_li": 0.8632,
        "li_delta": round(li - 0.8632, 4),

        # HIM
        "him_status": him["him_status"],
        "him_divergence": him["divergence"],

        # New document corpus fields
        "document_layer": document_layer,
        "score_source": json.dumps(score_source),
        "document_title": document_title,
        "document_version": document_version,
        "document_source_url": document_source_url,
        "document_authors": document_authors,
        "document_type": document_type,

        # Ingestion metadata
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "ingestion_tool": f"{TOOL_NAME} v{TOOL_VERSION}",
        "ingest_session": session_id,
    }

    return row


# ── Output writers ────────────────────────────────────────────────────────────

def write_staging_json(row: dict, output_dir: str, subject: str) -> str:
    """Write staging JSON row for Supabase upload."""
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in subject)[:40]
    path = os.path.join(output_dir, f"doc_row_{safe_name}_{ts}.json")
    with open(path, "w") as f:
        json.dump(row, f, indent=2)
    return path


def update_manifest(manifest_path: str, row: dict, source_path: str) -> None:
    """Append to the document corpus manifest for deduplication tracking."""
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        manifest = {"version": "1.0", "entries": []}

    entry = {
        "subject": row["subject"],
        "document_title": row["document_title"],
        "document_layer": row["document_layer"],
        "document_type": row["document_type"],
        "li": row["li"],
        "ingested_at": row["ingested_at"],
        "source_path": source_path,
        "session_id": row["session_id"],
    }

    # Deduplication: replace if same subject+document_title exists
    existing = [e for e in manifest["entries"]
                if not (e["subject"] == entry["subject"] and
                        e["document_title"] == entry["document_title"])]
    existing.append(entry)
    manifest["entries"] = existing
    manifest["total"] = len(existing)
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)


def write_report(row: dict, output_dir: str, staged_path: str) -> dict:
    """Generate ingestion report."""
    arch_dims = [d for d, s in json.loads(row["score_source"]).items()
                 if s == "architectural"]
    report = {
        "tool": f"{TOOL_NAME} v{TOOL_VERSION}",
        "status": "PASS",
        "subject": row["subject"],
        "document_title": row["document_title"],
        "document_layer": row["document_layer"],
        "document_type": row["document_type"],
        "li": row["li"],
        "li_delta": row["li_delta"],
        "him_status": row["him_status"],
        "architectural_dimensions": arch_dims,
        "f34_flag": len(arch_dims) > 0,
        "staged_path": staged_path,
        "corpus_filter_note": (
            "This row uses document_layer='behavioral_session' — included in corpus aggregates."
            if row["document_layer"] == "behavioral_session"
            else f"document_layer='{row['document_layer']}' — EXCLUDED from behavioral corpus aggregates. "
                 "Filter: WHERE document_layer='behavioral_session'"
        ),
        "ingested_at": row["ingested_at"],
    }
    return report


# ── Smoke test ────────────────────────────────────────────────────────────────

def smoke_test() -> None:
    """Minimal smoke test per HumanAIOS builder compliance."""
    test_analyzer_output = {
        "subject": "SMOKE_TEST_DOC",
        "session_id": "S-SMOKE-00",
        "timestamp": "2026-05-16T00:00:00Z",
        "mode": "RETROSPECTIVE_ANALYTICAL",
        "li": 0.7500,
        "core6_li": 0.7500,
        "scores": {d: 75 for d in DIMENSIONS_12},
    }
    try:
        validated = validate_analyzer_output(test_analyzer_output)
        row = build_corpus_row(
            analyzer_data=validated,
            document_layer="governance_document",
            document_title="Smoke Test Document",
            document_version="0.0",
            document_source_url="internal",
            document_authors="Test",
            document_type="test",
            explicit_arch_dims=[],
            session_id="S-SMOKE-00",
        )
        assert row["li"] == 0.75
        assert row["document_layer"] == "governance_document"
        assert row["him_status"] in {"ABOVE", "TRACKING", "BELOW"}
        assert json.loads(row["score_source"])["truth"] == "behavioral"
        report = write_report(row, "/tmp", "/tmp/smoke.json")
        assert report["status"] == "PASS"
        print("✓ Smoke test PASSED")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Smoke test FAILED: {e}", file=sys.stderr)
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Document Corpus Ingestor v1.0")
    parser.add_argument("--analyzer-output", "-i",
                        help="Path to acat_document_analyzer JSON output file")
    parser.add_argument("--document-layer", default="governance_document",
                        choices=list(VALID_LAYERS),
                        help="Corpus layer for this document")
    parser.add_argument("--document-title", default="",
                        help="Human-readable document title")
    parser.add_argument("--document-version", default="",
                        help="Document version string")
    parser.add_argument("--document-source-url", default="",
                        help="Source URL or 'internal'")
    parser.add_argument("--document-authors", default="",
                        help="Author(s)")
    parser.add_argument("--document-type", default="",
                        help="Document type (e.g. research_paper, governance_spec, evaluation_framework)")
    parser.add_argument("--arch-dims", default="",
                        help="Comma-separated list of dimensions to flag as architectural")
    parser.add_argument("--session", default="",
                        help="Session ID for this ingestion")
    parser.add_argument("--output", "-o", default="/home/claude/work/doc_corpus/staged",
                        help="Output directory for staged JSON rows")
    parser.add_argument("--manifest", default="/home/claude/work/doc_corpus/document_corpus_manifest.json",
                        help="Path to manifest file")
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        smoke_test()

    if not args.analyzer_output:
        parser.print_help()
        sys.exit(1)

    # Load analyzer output
    # Handle case where output is a directory (analyzer writes to dir)
    input_path = args.analyzer_output
    if os.path.isdir(input_path):
        # find most recent json in dir
        jsons = sorted(Path(input_path).glob("acat_doc_*.json"), key=os.path.getmtime)
        if not jsons:
            print(f"INGEST_FAILED: no acat_doc_*.json found in {input_path}", file=sys.stderr)
            sys.exit(1)
        input_path = str(jsons[-1])

    try:
        with open(input_path) as f:
            analyzer_data = json.load(f)
    except Exception as e:
        print(f"INGEST_FAILED: cannot load {input_path}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        validated = validate_analyzer_output(analyzer_data)
    except ValueError as e:
        print(f"INGEST_FAILED: {e}", file=sys.stderr)
        sys.exit(1)

    arch_dims = [d.strip() for d in args.arch_dims.split(",") if d.strip()]

    row = build_corpus_row(
        analyzer_data=validated,
        document_layer=args.document_layer,
        document_title=args.document_title,
        document_version=args.document_version,
        document_source_url=args.document_source_url,
        document_authors=args.document_authors,
        document_type=args.document_type,
        explicit_arch_dims=arch_dims,
        session_id=args.session,
    )

    staged_path = write_staging_json(row, args.output, row["subject"])
    update_manifest(args.manifest, row, input_path)
    report = write_report(row, args.output, staged_path)

    # Print report
    print(f"\n{'═'*60}")
    print(f" Document Ingestor · {TOOL_VERSION}")
    print(f" Subject: {report['subject']}")
    print(f" Title:   {report['document_title']}")
    print(f" Layer:   {report['document_layer']}  |  Type: {report['document_type']}")
    print(f"{'═'*60}")
    print(f"  LI:      {report['li']}  (Δ {report['li_delta']:+.4f} vs corpus mean)")
    print(f"  HIM:     {report['him_status']}")
    if report["architectural_dimensions"]:
        print(f"  F-34:    ARCH dims → {report['architectural_dimensions']}")
    print(f"  Staged:  {staged_path}")
    print(f"\n  {report['corpus_filter_note']}")
    print(f"{'═'*60}\n")


if __name__ == "__main__":
    main()

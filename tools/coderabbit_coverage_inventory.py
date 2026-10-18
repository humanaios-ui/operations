#!/usr/bin/env python3
"""HumanAIOS Builder v1.7 compliant — issue #806 immutable tree inventory.

This tool does NOT invoke CodeRabbit and cannot authenticate review receipts.
This pilot rejects REVIEWED claims pending independent protected witness integration.
"""
TOOL_NAME = "coderabbit_coverage_inventory"
TOOL_VERSION = "0.2.0"
TOOL_CATEGORY = "audit_tool"
TOOL_ZONE = 1

import argparse
import hashlib
import json
import re
import sys
import subprocess
from pathlib import Path

STATES = {"PENDING", "REVIEWED", "NOT_APPLICABLE", "UNSUPPORTED", "SKIPPED_LIMIT", "FAILED"}
DISPOSITIONS = {"inspected", "evidence_mapped", "metadata_only", "excluded_with_reason", "blocked", "pending"}
MEDIA_SUFFIXES = {
    ".avif", ".bmp", ".docx", ".gif", ".ico", ".jpeg", ".jpg", ".mp3", ".mp4",
    ".pdf", ".png", ".pptx", ".webp", ".woff", ".woff2", ".zip",
}
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".go", ".h", ".java", ".js", ".jsx", ".py", ".rs", ".sh", ".ts", ".tsx"}
CONFIG_SUFFIXES = {".cfg", ".ini", ".json", ".json5", ".jsonl", ".sql", ".toml", ".xml", ".yaml", ".yml"}
DOCUMENT_SUFFIXES = {".adoc", ".md", ".rst", ".txt"}
SENSITIVE_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519"}
GENERATED_PATHS = {
    "CONTROLLED_DOCUMENTS.md",
    "TOOLS_MANIFEST.md",
    "graph_timeline/system_graph_timeline.html",
    "graph_timeline/system_graph_timeline.json",
}
VENDOR_PREFIXES = ("vendor/", "third_party/", "third-party/", "node_modules/")
TEST_PARTS = {"test", "tests", "fixture", "fixtures"}


def git(*args):
    return subprocess.check_output(["git", *args], timeout=120)


def classify_file(path, mode, git_type):
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    parts = set(path.lower().split("/"))
    if git_type == "commit":
        file_kind = "submodule"
    elif mode == "120000":
        file_kind = "symlink"
    elif name in SENSITIVE_NAMES or name.startswith(".env."):
        file_kind = "secret_sensitive_candidate"
    elif path.startswith(VENDOR_PREFIXES):
        file_kind = "vendor_third_party"
    elif path in GENERATED_PATHS:
        file_kind = "generated_rendered"
    elif suffix in MEDIA_SUFFIXES:
        file_kind = "binary_media"
    elif parts & TEST_PARTS or name.startswith(("test_", "tests_")):
        file_kind = "test_fixture_data"
    elif path.startswith(".github/workflows/") or suffix in CONFIG_SUFFIXES:
        file_kind = "workflow_config_schema"
    elif suffix in SOURCE_SUFFIXES:
        file_kind = "source_code_and_comments"
    elif suffix in DOCUMENT_SUFFIXES:
        file_kind = "prose_document"
    else:
        file_kind = "other_data_or_unknown"

    if name in SENSITIVE_NAMES or name.startswith(".env."):
        status, disposition = "NOT_APPLICABLE", "excluded_with_reason"
        reason = "potentially sensitive path; content not read or copied"
        sensitivity = "POTENTIALLY_SENSITIVE"
    elif file_kind in {"submodule", "symlink", "binary_media"}:
        status, disposition = "UNSUPPORTED", "metadata_only"
        reason = "content not inspected; recorded from Git metadata only"
        sensitivity = "UNASSESSED"
    else:
        status, disposition = "PENDING", "pending"
        reason = "content and source relationships not assessed"
        sensitivity = "UNASSESSED"

    return {
        "file_kind": file_kind,
        "classification_basis": "Git mode/type and path only; no file content read",
        "sensitivity": sensitivity,
        "owner": "UNRESOLVED",
        "generator": "UNRESOLVED",
        "document_metadata": {
            "doc_id": None,
            "registry_state": "NOT_CROSS_REFERENCED",
            "approval_state": "UNASSESSED",
            "fpcp_lifecycle": "UNASSESSED",
            "references_to": "UNASSESSED",
            "tests_for": "UNASSESSED",
            "visibility": "UNASSESSED",
        },
        "status": status,
        "disposition": disposition,
        "reason": reason,
        "review_receipt": None,
    }


def inventory(commit, after_path=None, limit=None):
    # Require an immutable commit object: tag/branch names alone are not durable.
    if not re.fullmatch(r"[0-9a-fA-F]{40}", commit):
        raise ValueError("Pass a complete 40-character hexadecimal commit SHA")
    commit = commit.lower()
    resolved = git("rev-parse", "--verify", commit + "^{commit}").decode().strip()
    if commit != resolved:
        raise ValueError("Resolved commit differs from requested exact commit SHA")
    if limit is not None and limit < 1:
        raise ValueError("--limit must be at least 1")
    raw = git("ls-tree", "-rz", "--full-tree", resolved)
    items = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, blob = metadata.decode("ascii").split()
        path = name.decode("utf-8", errors="surrogateescape")
        classification = classify_file(path, mode, kind)
        items.append({
            "path": path,
            "path_bytes_hex": name.hex(),
            "mode": mode,
            "git_type": kind,
            "git_oid": blob,
            **classification,
        })
    items.sort(key=lambda row: row["path"].encode("utf-8", errors="surrogateescape"))
    total = len(items)
    start = 0
    if after_path is not None:
        cursor = next((i for i, row in enumerate(items) if row["path"] == after_path), None)
        if cursor is None:
            raise ValueError("--after-path must exactly match a path in the pinned tree")
        start = cursor + 1
    end = total if limit is None else min(total, start + limit)
    items = items[start:end]
    next_after_path = items[-1]["path"] if end < total and items else None
    complete = start == 0 and end == total
    return {
        "schema": "humanaios.document-census.v0.1",
        "review_schema": "coderabbit_coverage_v0",
        "commit": resolved,
        "generated_by": {
            "path": "tools/coderabbit_coverage_inventory.py",
            "version": TOOL_VERSION,
            "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "checkpoint": {
            "complete": complete,
            "page_complete": next_after_path is None,
            "after_path": after_path,
            "next_after_path": next_after_path,
            "total_tree_paths": total,
            "covered_paths": len(items),
        },
        "files": items,
    }


def validate(doc):
    rows = doc["files"]
    paths = [r["path"] for r in rows]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate file path")
    if paths != sorted(paths, key=lambda path: path.encode("utf-8", errors="surrogateescape")):
        raise ValueError("inventory not sorted")
    counts = {state: 0 for state in sorted(STATES)}
    dispositions = {state: 0 for state in sorted(DISPOSITIONS)}
    file_kinds = {}
    for row in rows:
        state = row["status"]
        if state not in STATES:
            raise ValueError("unknown state: " + state)
        disposition = row.get("disposition")
        if disposition not in DISPOSITIONS:
            raise ValueError("unknown disposition: " + str(disposition))
        if not row.get("file_kind") or not row.get("classification_basis"):
            raise ValueError("file classification is incomplete")
        if not row.get("reason"):
            raise ValueError("every path needs an explicit disposition reason")
        if disposition in {"inspected", "evidence_mapped", "blocked"}:
            raise ValueError("this inventory cannot assert inspected, evidence-mapped, or blocked states")
        if not row.get("sensitivity") or not row.get("owner") or not row.get("generator"):
            raise ValueError("sensitivity, owner, and generator must be explicit")
        metadata = row.get("document_metadata")
        if not isinstance(metadata, dict) or any(
            key not in metadata for key in (
                "doc_id", "registry_state", "approval_state", "fpcp_lifecycle",
                "references_to", "tests_for", "visibility",
            )
        ):
            raise ValueError("document metadata fields are incomplete")
        expected_disposition = {
            "PENDING": "pending",
            "UNSUPPORTED": "metadata_only",
            "NOT_APPLICABLE": "excluded_with_reason",
        }.get(state)
        if expected_disposition and disposition != expected_disposition:
            raise ValueError("status and disposition disagree")
        if disposition == "excluded_with_reason" and row["sensitivity"] != "POTENTIALLY_SENSITIVE":
            raise ValueError("excluded path must be explicitly marked potentially sensitive")
        if state == "REVIEWED":
            # Hard fail closed: artifact assertions are not protected GitHub App attestation.
            raise ValueError("REVIEWED forbidden without independently verified CodeRabbit witness")
        counts[state] += 1
        dispositions[disposition] += 1
        file_kinds[row["file_kind"]] = file_kinds.get(row["file_kind"], 0) + 1
    if sum(counts.values()) != len(rows):
        raise ValueError("coverage total mismatch")
    if sum(dispositions.values()) != len(rows):
        raise ValueError("census disposition total mismatch")
    checkpoint = doc.get("checkpoint", {})
    if checkpoint.get("covered_paths") != len(rows):
        raise ValueError("checkpoint coverage does not match inventory rows")
    if checkpoint.get("complete") and checkpoint.get("total_tree_paths") != len(rows):
        raise ValueError("complete census does not account for the exact tree")
    # No authenticated review provider is wired into this pilot.
    authenticated = 0
    complete = bool(rows) and counts["PENDING"] == 0 and counts["FAILED"] == 0 and counts["SKIPPED_LIMIT"] == 0 and counts["REVIEWED"] == len(rows) and authenticated == len(rows)
    return {
        "tracked": len(rows),
        "tree_tracked": checkpoint.get("total_tree_paths", len(rows)),
        "census_complete": bool(checkpoint.get("complete")),
        "counts": counts,
        "disposition_counts": dispositions,
        "file_kind_counts": dict(sorted(file_kinds.items())),
        "reviewed_authenticated": authenticated,
        "complete": complete,
        "review_verdict": "VERIFIED" if complete else "NOT_VERIFIED",
    }


def _markdown_path(path):
    return "`" + path.replace("\\", "\\\\").replace("`", "\\`").replace("\n", "\\n").replace("|", "\\|") + "`"


def render_dashboard(doc):
    summary = doc["summary"]
    checkpoint = doc["checkpoint"]
    dispositions = summary["disposition_counts"]
    lines = [
        "# Fixed-head file census",
        "",
        f'- Commit: `{doc["commit"]}`',
        f'- Tree paths: {checkpoint["total_tree_paths"]}',
        f'- Rows in this checkpoint: {checkpoint["covered_paths"]}',
        f'- Census complete: {str(checkpoint["complete"]).lower()}',
        f'- Review verdict: **{summary["review_verdict"]}** (CodeRabbit is not called or authenticated by this tool)',
        "",
        "## Disposition totals",
        "",
        "| Checkpoint rows | Inspected | Evidence-mapped | Metadata-only | Excluded with reason | Blocked | Pending |",
        "|---:|---:|---:|---:|---:|---:|---:|",
        "| " + " | ".join(str(value) for value in (
            checkpoint["covered_paths"],
            dispositions["inspected"],
            dispositions["evidence_mapped"],
            dispositions["metadata_only"],
            dispositions["excluded_with_reason"],
            dispositions["blocked"],
            dispositions["pending"],
        )) + " |",
        "",
        "Disposition counts below describe this checkpoint's rows; totals must equal the exact tree only when census is complete.",
        "",
        "## Classification counts",
        "",
        "| File kind | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {kind} | {count} |" for kind, count in summary["file_kind_counts"].items())
    exceptions = [row for row in doc["files"] if row["disposition"] in {"metadata_only", "excluded_with_reason"}]
    lines.extend(["", "## Individually listed exceptions", ""])
    if exceptions:
        lines.extend(
            f'- {_markdown_path(row["path"])} — {row["file_kind"]}; {row["disposition"]}: {row["reason"]}.'
            for row in exceptions
        )
    else:
        lines.append("None in this checkpoint.")
    lines.extend([
        "",
        "## Unresolved per-path metadata",
        "",
        "Owner, generator, document-registry identity, approval, FPCP lifecycle, references/tests, and visibility are recorded as unresolved or unassessed. No document content or private source payload was read. `PENDING` is not an exclusion or a finding of irrelevance.",
        "",
    ])
    if checkpoint["next_after_path"] is not None:
        lines.append(f'Resume with `--after-path {_markdown_path(checkpoint["next_after_path"])}`.')
    return "\n".join(lines)


def run_smoke_test():
    sample = {
        "files": [{
            "path": "example.py",
            "status": "PENDING",
            "disposition": "pending",
            "file_kind": "source_code_and_comments",
            "classification_basis": "smoke test",
            "sensitivity": "UNASSESSED",
            "owner": "UNRESOLVED",
            "generator": "UNRESOLVED",
            "document_metadata": {
                "doc_id": None,
                "registry_state": "NOT_CROSS_REFERENCED",
                "approval_state": "UNASSESSED",
                "fpcp_lifecycle": "UNASSESSED",
                "references_to": "UNASSESSED",
                "tests_for": "UNASSESSED",
                "visibility": "UNASSESSED",
            },
            "reason": "pending",
        }],
        "checkpoint": {"complete": True, "total_tree_paths": 1, "covered_paths": 1},
    }
    return validate(sample)["review_verdict"] == "NOT_VERIFIED"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--commit", help="full immutable 40-character commit SHA")
    p.add_argument("--output")
    p.add_argument("--dashboard", help="optional Markdown dashboard output path")
    p.add_argument("--after-path", help="resume after an exact path from the same pinned tree")
    p.add_argument("--limit", type=int, help="maximum paths in this checkpoint")
    p.add_argument("--smoke-test", action="store_true")
    args = p.parse_args()
    if args.smoke_test:
        if not run_smoke_test():
            raise SystemExit(1)
        print("smoke-test OK")
        return
    if not args.commit or not args.output:
        p.error("--commit and --output are required unless --smoke-test is used")
    try:
        doc = inventory(args.commit, after_path=args.after_path, limit=args.limit)
        doc["summary"] = validate(doc)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, OSError) as exc:
        print(f"Inventory failed closed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from None
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(doc, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    if args.dashboard:
        dashboard = Path(args.dashboard)
        dashboard.parent.mkdir(parents=True, exist_ok=True)
        dashboard.write_text(render_dashboard(doc) + "\n", encoding="utf-8")
    print(json.dumps(doc["summary"], sort_keys=True))


if __name__ == "__main__":
    main()

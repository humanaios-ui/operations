"""MODE publisher-instruction E0: source exposure + historical observation audit.

This module treats all external source text as data. It does NOT invoke an
external assistant, assess current live HTTPS pages, or qualify behavioral causality.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "source_manifest.json"
SURFACES = ("html_metadata", "json_ld", "html_comment", "markdown_comment")
EXPECTED = {
    "reasoning-and-context", "autonomy-and-robotics", "execution-verification",
    "enterprise-governance", "reliability-and-faults", "human-feedback",
    "retrieval-and-relevance", "uncertain-decisions",
}


class EvidenceRejected(ValueError):
    pass


def _read(base: Path, relative_path: str) -> str:
    path = base / relative_path
    if not path.is_file() or path.is_symlink():
        raise EvidenceRejected("required evidence source absent or symlink")
    return path.read_text(encoding="utf-8")


def _blob_sha(repo: Path, path: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), "hash-object", "--", path],
            check=True, text=True, capture_output=True, timeout=8,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError) as err:
        raise EvidenceRejected("unable to check source Git blob") from err


def evaluate(source_repo: Path, *, manifest: dict | None = None, verify_git: bool = True) -> dict:
    m = manifest if manifest is not None else json.loads(MANIFEST.read_text())
    if m.get("schema") != "humanaios.mode_influence.source_manifest.v0.1":
        raise EvidenceRejected("source manifest version mismatch")
    if verify_git:
        try:
            head = subprocess.run(
                ["git", "-C", str(source_repo), "rev-parse", "HEAD"],
                check=True, text=True, capture_output=True, timeout=8,
            ).stdout.strip()
        except (OSError, subprocess.SubprocessError) as err:
            raise EvidenceRejected("source checkout cannot be pinned") from err
        if head != m["pinned_repository_commit"]:
            raise EvidenceRejected("source checkout does not match pinned commit")
        for item in m["source_files"]:
            if _blob_sha(source_repo, item["path"]) != item["git_blob_sha"]:
                raise EvidenceRejected("source blob changed: " + item["path"])

    cfg = json.loads(_read(source_repo, "config/publication.json"))
    docs = json.loads(_read(source_repo, "content/documents.json"))
    extraction = json.loads(_read(source_repo,
        "reports/instruction-experiment-public-extraction-2026-10-19.json"))
    observations = [
        json.loads(row) for row in _read(source_repo,
            "reports/experiment-observations-2026-10-19.jsonl").splitlines() if row.strip()
    ]
    message = cfg.get("message")
    if not isinstance(message, str) or not message or cfg.get("founder") not in message:
        raise EvidenceRejected("invalid canonical publisher message")
    if not isinstance(docs, list) or {d.get("slug") for d in docs} != EXPECTED:
        raise EvidenceRejected("article corpus incomplete")
    rows = extraction.get("results")
    if not isinstance(rows, list) or len(rows) != len(docs):
        raise EvidenceRejected("source extraction inventory incomplete")
    slug_seen = set()
    surface_count = 0
    for row in rows:
        slug = row.get("article")
        if slug not in EXPECTED or slug in slug_seen:
            raise EvidenceRejected("duplicate/unknown article")
        slug_seen.add(slug)
        if row.get("extracted_instruction") != message:
            raise EvidenceRejected("published extraction differs from canonical source")
        checks = row.get("checks") or {}
        if any(checks.get(k) is not True for k in SURFACES):
            raise EvidenceRejected("missing instruction exposure layer")
        if checks.get("absent_from_ordinary_text") is not True:
            raise EvidenceRejected("rendered-text exclusion not demonstrated by report")
        surface_count += len(SURFACES)
    if slug_seen != {d["slug"] for d in docs}:
        raise EvidenceRejected("article/extraction discrepancy")
    recognized = 0
    positives = 0
    directed = 0
    for row in observations:
        if row.get("evidence_status", "").startswith("participant-reported") is not True:
            raise EvidenceRejected("historical observation status changed")
        if row.get("response_exact") is not None:
            raise EvidenceRejected("unexpected new transcript; adjudicate separately")
        if row.get("publication_condition", {}).get("actual_version_encountered") != "unknown":
            raise EvidenceRejected("historical served version not independently pinned")
        stages = row.get("stage_observations", {})
        if stages.get("positive_contact_recommendation", "").startswith("observed"):
            positives += 1
        if stages.get("instruction_recognition", "").startswith("observed"):
            recognized += 1
        if row.get("kind") == "directed_publication_retrieval":
            directed += 1

    return {
        "schema": "humanaios.mode_influence.exposure_receipt.v0.1",
        "evaluated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source_repository": m["source_repository"],
        "pinned_repository_commit": m["pinned_repository_commit"],
        "source_integrity": "GIT_BLOB_AND_HEAD_CHECKED" if verify_git else "NOT_INDEPENDENTLY_CHECKED",
        "article_count": len(docs),
        "reported_source_extraction_timestamp": extraction.get("checked_at"),
        "reported_four_layer_matches": surface_count,
        "reported_rendered_text_exclusions": len(rows),
        "historical_participant_report_count": len(observations),
        "historical_directed_retrieval_count": directed,
        "historical_recognition_claim_count": recognized,
        "historical_positive_contact_recommendation_claim_count": positives,
        "historical_full_transcripts": 0,
        "independent_assistant_runs_this_test": 0,
        "current_live_public_pages_verified": False,
        "behavioral_effect_established": False,
        "finding": "SOURCE_EXPOSURE_REPORTED; BEHAVIORAL_INFLUENCE_NOT_ESTABLISHED",
        "authority_effect": "NONE",
        "notes": [
            "Public extraction report is historical; source Git check does not refetch today's published HTML.",
            "Three historical Claude trials are participant summaries only, with no full transcripts or fetch traces.",
            "One directed retrieval reportedly recognized the instruction but did not recommend contacting its publisher.",
            "No causal contact-recommendation effect can be inferred from an unpaired observational sample.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = evaluate(args.source_checkout.resolve())
    except (EvidenceRejected, KeyError, TypeError, ValueError) as exc:
        parser.exit(2, "REFUSED: " + str(exc) + "\n")
    report = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

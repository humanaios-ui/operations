"""Issue #1002: deterministic, non-authorizing shadow source-feedback replay.

The before arm is a separately frozen Resource Miner corpus. The after arm
removes *one exact source observation* from an in-memory query projection only.
Neither arm edits catalogs, performs an external request, makes a closure claim,
or authorizes applying a shared correction. This is not an ACAT measurement.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from .intent_os import evaluate_objective
from . import intent_os as _ranker_module
from . import query_quality as _query_quality_module
from . import source_risk as _source_risk_module

SCHEMA = "humanaios.resource_feedback_shadow_replay.v0.1"
RANKER = "LEXICAL_PLUS_DECLARED_TAXONOMY_RRF_K60_V1"


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _verify_executed_ranker(fixture: dict) -> None:
    """Reject stale claims about the actual Python source executed in this replay.

    A strategy name is not proof of code identity. Pin the imported modules and
    check that the functions called by intent_os come from those pinned modules.
    This is a local integrity check, NOT a GitHub signature or source attestation.
    """
    dependencies = fixture.get("ranker_dependency_git_blobs")
    expected = {"query_quality.py", "source_risk.py"}
    if not isinstance(dependencies, dict) or set(dependencies) != expected:
        raise ValueError("Missing or unexpected ranker dependency pins")
    sources = (
        ("intent_os.py", _ranker_module, fixture.get("ranker_git_blob_sha")),
        ("query_quality.py", _query_quality_module, dependencies["query_quality.py"]),
        ("source_risk.py", _source_risk_module, dependencies["source_risk.py"]),
    )
    for name, module, pin in sources:
        source = Path(module.__file__).resolve()
        if source.name != name or source.suffix != ".py" or (
            not isinstance(pin, str) or _git_blob_sha(source.read_bytes()) != pin
        ):
            raise ValueError("Executed ranker source revision mismatch: " + name)
    if evaluate_objective is not _ranker_module.evaluate_objective:
        raise ValueError("Ranker entrypoint identity mismatch")
    for name in ("query_terms", "blocked_resource_types", "fuse_rankings",
                 "has_exact_anchors"):
        if getattr(_ranker_module, name) is not getattr(_query_quality_module, name):
            raise ValueError("Ranker imported dependency mismatch: " + name)
    if _ranker_module.promotional_claim_flags is not _source_risk_module.promotional_claim_flags:
        raise ValueError("Ranker imported source-risk dependency mismatch")


def _ids(result):
    return [row["resource_id"] for row in result["candidates"]]


def replay(snapshot_path: Path, fixture: dict) -> dict:
    """Replay the same source and ranking inputs with an in-memory held observation.

    A proposal may be shadow-tested without Z2 approval; a shared revision may
    *not* be applied by this function. Independent reviewer authentication is
    deliberately not claimed by a web-fetch result.
    """
    if fixture.get("schema") != "humanaios.feedback_replay_fixture.v0.1":
        raise ValueError("Unexpected experiment fixture")
    _verify_executed_ranker(fixture)
    snapshot_bytes = snapshot_path.read_bytes()
    blob = _git_blob_sha(snapshot_bytes)
    if blob != fixture["snapshot_git_blob_sha"]:
        raise ValueError("Snapshot has changed: refuse unpinned replay")
    rows = [json.loads(line) for line in snapshot_bytes.decode("utf-8").splitlines()
            if line.strip()]
    if len(rows) != fixture["snapshot_row_count"] or not all(isinstance(x, dict) for x in rows):
        raise ValueError("Snapshot row count or type mismatch")
    target = fixture["target"]
    resource_id, url = target["resource_id"], target["canonical_source_url"]
    # Require the exact recorded identity and source URL; no fuzzy equivalence.
    matching = [x for x in rows if x.get("resource_id") == resource_id
                and x.get("canonical_url") == url]
    if len(matching) != 1:
        raise ValueError("Unique exact source match is not established")
    if fixture["source_report"]["reported_status"] != "LINK_FAILED_404":
        raise ValueError("Unexpected source-failure specimen")
    if fixture["external_observation"]["status"] != "HTTP_404_OBSERVED":
        raise ValueError("No matching independent public-web observation")
    if fixture["external_observation"]["source_url"] != url:
        raise ValueError("External observation refers to another URL")
    if fixture["revision"]["shared_approval"] != "NOT_APPROVED":
        raise ValueError("This experiment is shadow-only; approval cannot be inferred")
    objectives = fixture["objectives"]
    if len(objectives) != 2 or not all(
        isinstance(x, str) and x for x in objectives.values()
    ):
        raise ValueError("Expected target and held-out objectives")
    base = dict(source_mode="snapshot", source_status="CURATED_SNAPSHOT_NOT_LIVE",
                source_warning="Offline pinned snapshot, not current availability")
    # Freeze ranker date in this isolated offline experiment. The original
    # ranker uses date.today() for deadlines; this pin makes later replays
    # comparable without changing the production ranker or dataset.
    as_of = date.fromisoformat(fixture["as_of_date"])
    class _PinnedDate(date):
        @classmethod
        def today(cls):
            return as_of

    # A held source is not marked CLOSED or ARCHIVE. It is excluded only from
    # the experimental after-arm, not from persistent resource records.
    after_rows = [dict(row) for row in rows if not (
        row.get("resource_id") == resource_id and row.get("canonical_url") == url
    )]
    with patch.object(_ranker_module, "date", _PinnedDate):
        before = evaluate_objective(objectives["target"], rows, **base)
        control_before = evaluate_objective(objectives["heldout"], rows, **base)
        after = evaluate_objective(objectives["target"], after_rows, **base)
        control_after = evaluate_objective(objectives["heldout"], after_rows, **base)
        repeat_before = evaluate_objective(objectives["target"], rows, **base)
        repeat_after = evaluate_objective(objectives["target"], after_rows, **base)
    before_ids, after_ids = _ids(before), _ids(after)
    heldout_before, heldout_after = _ids(control_before), _ids(control_after)
    conditions = {
        "exact_source_match_once": len(matching) == 1,
        "target_exposed_before": resource_id in before_ids[:10],
        "target_held_after": resource_id not in after_ids,
        "unrelated_heldout_unchanged": heldout_before == heldout_after,
        "same_ranker": (before["ranking_strategy"] == after["ranking_strategy"] == RANKER),
        "replay_deterministic": (before == repeat_before and after == repeat_after),
        "no_eligibility_claim": before["eligibility"] == after["eligibility"] == "NOT_ASSESSED",
        "no_authority": before["authority"] == after["authority"] == "NONE",
        "no_execution": before["execution"] == after["execution"] == "DISABLED",
    }
    receipt = {
        "schema": SCHEMA,
        "experiment_id": fixture["experiment_id"],
        "experiment_kind": "OFFLINE_SHADOW_REPLAY_NOT_SHARED_CORPUS_REVISION",
        "source_report": fixture["source_report"],
        "external_observation": fixture["external_observation"],
        "external_reviewer_identity": "NOT_AUTHENTICATED",
        "source_closure_verdict": "NOT_ESTABLISHED",
        "corpus_before_revision": blob,
        "corpus_after_revision": _digest(after_rows),
        "corpus_after_revision_kind": "IN_MEMORY_SHADOW_PROJECTION_SHA256_NOT_GIT_REVISION",
        "ranker_git_blob_sha": fixture["ranker_git_blob_sha"],
        "ranker_strategy": RANKER,
        "date_dependency": "PINNED_AS_OF_DATE_IN_ISOLATED_SHADOW_RUN",
        "replay_date_utc": as_of.isoformat(),
        "objective_digests_sha256": {key: _digest(value) for key, value in objectives.items()},
        "source_target_id": resource_id,
        "candidate_ids_before": before_ids,
        "candidate_ids_after": after_ids,
        "heldout_candidate_ids_before": heldout_before,
        "heldout_candidate_ids_after": heldout_after,
        "displayed_cutoff": 10,
        "matched_count_before": before["matched_count"],
        "matched_count_after": after["matched_count"],
        "unexamined_count_before": before["unexamined_count"],
        "unexamined_count_after": after["unexamined_count"],
        "stale_source_exposure_at_10_before": int(resource_id in before_ids[:10]),
        "stale_source_exposure_at_10_after": int(resource_id in after_ids[:10]),
        "verified_relevant_recall_at_10": "NOT_ESTABLISHED_NO_INDEPENDENT_RELEVANCE_LABELS",
        "false_closure_count": "NOT_ESTABLISHED_NO_COMPLETE_LIVE_STATUS_LABELS",
        "unsupported_closure_claims_emitted": 0,
        "shared_revision_applied": False,
        "human_approved_revision_id": None,
        "human_approval_state": "NOT_APPROVED",
        "model_training_performed": False,
        "model_behavior_measured": False,
        "behavioral_baseline_subject": "DETERMINISTIC_RESOURCE_MINER_RANKER_NOT_LLM",
        "acat_state": "NOT_RUN_CANONICAL_VERSION_PREREQUISITE_750",
        "conditions": conditions,
        "status": "PASS_SHADOW_ONLY" if all(conditions.values()) else "FAIL_SHADOW_REPLAY",
        "authority_effect": "NONE",
        "execution": "DISABLED",
        "receipt_kind": "UNSIGNED_LOCAL_REPLAY_DIGEST_NOT_EXTERNAL_ATTESTATION",
    }
    receipt["receipt_sha256"] = _digest(receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description="Run #1002 bounded offline shadow replay")
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--fixture", type=Path, default=root / "fixtures/feedback_replay_1002_v1.json")
    parser.add_argument("--snapshot", type=Path, default=root / "fixtures/feedback_replay_1002_corpus_20261026.jsonl")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = replay(args.snapshot, json.loads(args.fixture.read_text(encoding="utf-8")))
    payload = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)
    if result["status"] != "PASS_SHADOW_ONLY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

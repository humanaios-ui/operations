"""Offline, read-only contract digest checker. No authority or model attestation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

EXPECTED_SCHEMA = "HAIOS-RISK-OBS-001-CONTRACT-v0.1"
ARTIFACTS = ("packet", "prompt", "rubric")
_HEX = re.compile(r"[0-9a-f]{64}\Z")


def _is_hash(value: object) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def verify_files(manifest: dict, paths: dict[str, Path]) -> dict:
    """Compare exact original bytes; never trust filenames, links, or claims alone."""
    errors: list[str] = []
    if not isinstance(manifest, dict) or manifest.get("schema") != EXPECTED_SCHEMA:
        return {"status": "HOLD", "authority_effect": "NONE", "errors": ["invalid_schema"]}
    if manifest.get("authority_effect") != "NONE":
        errors.append("invalid_authority")
    if manifest.get("source_custody") != "QUALIFIED_ANALYST_PARAPHRASE":
        errors.append("invalid_source_custody")
    if any(manifest.get(x) is not False for x in ("p1_execution_authorized", "p2_qualified", "public_release_authorized")):
        errors.append("privilege_claim")
    rows = manifest.get("artifacts")
    if not isinstance(rows, dict) or set(rows) != set(ARTIFACTS):
        return {"status": "HOLD", "authority_effect": "NONE", "errors": errors + ["invalid_artifact_set"]}
    for name in ARTIFACTS:
        row = rows[name]
        if not isinstance(row, dict) or not _is_hash(row.get("sha256")) or type(row.get("bytes")) is not int or row["bytes"] <= 0:
            errors.append(f"{name}:invalid_manifest")
            continue
        path = paths.get(name)
        if path is None or not Path(path).is_file():
            errors.append(f"{name}:missing_bytes")
            continue
        raw = Path(path).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            errors.append(f"{name}:digest_mismatch")
    return {"status": "DIGEST_MATCH_ONLY" if not errors else "HOLD", "authority_effect": "NONE", "errors": errors,
            "p1_qualified": False, "p2_qualified": False, "public_release_authorized": False}


def check_receipt(manifest: dict, receipt: dict) -> dict:
    """Check syntactic source-bound receipt; output is NEVER authenticated or scored."""
    errors: list[str] = []
    if not isinstance(receipt, dict):
        errors.append("not_an_object")
    else:
        if receipt.get("phase") != "P1":
            errors.append("wrong_phase")
        if receipt.get("leg") not in ("CHATGPT", "CLAUDE", "GROK"):
            errors.append("unknown_leg")
        if receipt.get("peer_exposure") is not False:
            errors.append("peer_exposure_or_unknown")
        if receipt.get("authority_effect") != "NONE":
            errors.append("invalid_authority")
        for field in ("provider_run_ref", "model_version"):
            if not isinstance(receipt.get(field), str) or not receipt[field].strip():
                errors.append(f"missing_{field}")
        for name in ARTIFACTS:
            if receipt.get(f"{name}_sha256") != manifest.get("artifacts", {}).get(name, {}).get("sha256"):
                errors.append(f"{name}:digest_mismatch")
        if not _is_hash(receipt.get("output_sha256")):
            errors.append("missing_output_digest")
        state = receipt.get("rendered_image")
        if state not in ("NOT_PRODUCED", "PRODUCED"):
            errors.append("invalid_render_state")
        if state == "PRODUCED" and not _is_hash(receipt.get("image_sha256")):
            errors.append("unverifiable_image")
        if state == "NOT_PRODUCED" and receipt.get("image_sha256") is not None:
            errors.append("claimed_missing_image")
    return {"status": "CANDIDATE_UNVERIFIED" if not errors else "HOLD", "authority_effect": "NONE",
            "p1_qualified": False, "errors": errors}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    for name in ARTIFACTS:
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = verify_files(manifest, {name: getattr(args, name) for name in ARTIFACTS})
    if args.receipt is not None:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        result["receipt"] = check_receipt(manifest, receipt)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "DIGEST_MATCH_ONLY" and ("receipt" not in result or result["receipt"]["status"] == "CANDIDATE_UNVERIFIED") else 1


if __name__ == "__main__":
    sys.exit(main())

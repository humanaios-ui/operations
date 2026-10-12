"""Pure, offline HPRA research-data -> draft translation. No publication capability."""
import hashlib
import json
import math
from datetime import datetime
from urllib.parse import urlsplit

class EvidenceUnavailable(ValueError):
    pass

def verified_research_draft(records):
    """Validate real resolved forecasting observations; never infer authority."""
    if not isinstance(records, list) or not records or len(records) > 100:
        raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE")
    normalized = []
    for r in records:
        if not isinstance(r, dict) or r.get("evidence_status") == "SYNTHETIC_TEST_ONLY":
            raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE: synthetic or invalid source")
        url = r.get("question_url")
        if not isinstance(url, str):
            raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE: invalid source URL")
        try:
            parsed = urlsplit(url)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError()
        except ValueError as exc:
            raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE: invalid source URL") from exc
        resolved = r.get("p4_resolved_at")
        try:
            dt = datetime.fromisoformat(resolved.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                raise ValueError()
        except (ValueError, AttributeError) as exc:
            raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE: resolution timestamp missing") from exc
        metrics = {}
        for key in ("p4_brier_score", "p4_brier_skill_score"):
            value = r.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE: incomplete metrics")
            metrics[key] = float(value)
        if not 0 <= metrics["p4_brier_score"] <= 1:
            raise EvidenceUnavailable("NO_VERIFIED_EVIDENCE: invalid Brier score")
        normalized.append({"url": url, "resolved_at": resolved, **metrics})
    brier = sum(x["p4_brier_score"] for x in normalized) / len(normalized)
    skill = sum(x["p4_brier_skill_score"] for x in normalized) / len(normalized)
    rows = "\n".join(
        f"- {r['url']} — Brier {r['p4_brier_score']:.3f}; skill {r['p4_brier_skill_score']:+.3f}"
        for r in normalized
    )
    title = f"Weekly Calibration Research Draft: {len(normalized)} Resolved Questions"
    body = (f"# {title}\n\n**Status: DRAFT — NOT PUBLISHED**\n\n"
            f"Observed resolved questions: {len(normalized)} (verified-source eligibility requires independent review).\n"
            f"Mean Brier score: {brier:.3f} (n={len(normalized)}).\n"
            f"Mean Brier skill score: {skill:+.3f} (n={len(normalized)}).\n\n"
            f"## Evidence candidates\n{rows}\n\n"
            "## Limitations\nSource records are supplied by a database and have not been "
            "independently authenticated by HPRA. No causal effect or system reliability is established.\n")
    content = {"title": title, "body": body, "references": [
        {"source_url": r["url"], "status": "INDEPENDENT_VERIFICATION_REQUIRED"}
        for r in normalized
    ]}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=False).encode()).hexdigest()
    return {"schema_version": "hpra.research_draft.v0.1", "content": content,
            "content_sha256": digest, "status": "DRAFT_ONLY", "authorization": "NONE",
            "claims_status": "REQUIRES_INDEPENDENT_VERIFICATION",
            "publication": None, "human_approval": None}

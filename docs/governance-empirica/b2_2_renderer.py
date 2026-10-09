#!/usr/bin/env python3
"""
B2.2: REGISTERED.md Projection Renderer
Transforms candidate bundle JSON into human-readable governance ledger markdown.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any


class CandidateBundle:
    """Represents one Z-ratified governance candidate."""
    
    def __init__(self, data: Dict[str, Any]):
        self.id = data.get('decision_id')
        self.choice = data.get('choice', '')
        self.rationale = data.get('rationale', '')
        self.reversibility = data.get('reversibility', 'committal')
        self.ratified_at = data.get('ratified_at')
        self.ratified_by = data.get('ratified_by', 'Z2')
        self.findings = []
        self.assumptions = []
        self.falsifier = None
        self.claims_held = data.get('claims_held', 0)
        self.claims_refuted = data.get('claims_refuted', 0)
        self.claims_untested = data.get('claims_untested', 0)
        self.brier_score = data.get('brier_score', 0.0)
        
        # Parse artifacts
        artifacts_json = data.get('artifacts_json')
        if artifacts_json:
            artifacts = json.loads(artifacts_json) if isinstance(artifacts_json, str) else artifacts_json
            for a in artifacts or []:
                if a['type'] == 'finding':
                    self.findings.append(a)
                elif a['type'] == 'assumption':
                    if a.get('confidence', 1.0) < 0.4:
                        self.falsifier = a
                    else:
                        self.assumptions.append(a)
    
    @property
    def z_id(self) -> str:
        digest = hashlib.sha256(f"{self.id}:{self.choice}".encode()).hexdigest()[:8]
        return f"Z1-{int(digest, 16) % 1000:03d}"
    
    def is_untested(self) -> bool:
        return self.claims_untested > 0
    
    def is_disputed(self) -> bool:
        return self.claims_refuted > 0
    
    def verdict_badge(self) -> str:
        if self.is_disputed():
            return "⚠️ DISPUTED"
        elif self.is_untested():
            return "❓ UNTESTED"
        elif self.claims_held > 0 and self.claims_refuted == 0:
            return "✅ HELD"
        else:
            return "❌ REFUTED"


class RegisteredRenderer:
    """Renders candidates into REGISTERED.md."""
    
    def __init__(self, bundles: List[Dict[str, Any]]):
        self.bundles = [CandidateBundle(b) for b in bundles]
        self.bundles.sort(key=lambda b: b.ratified_at or '', reverse=True)
    
    def render(self) -> str:
        sections = [self._render_header()]
        sections.append("## Z-Ratified Candidates\n")
        
        for bundle in self.bundles:
            sections.append(self._render_candidate(bundle))
        
        flagged = [b for b in self.bundles if b.is_untested() or b.is_disputed()]
        if flagged:
            sections.append("\n## Flagged for Review\n")
            sections.append(self._render_flagged(flagged))
        
        sections.append(self._render_footer())
        return "\n".join(sections)
    
    def _render_header(self) -> str:
        now = datetime.utcnow().isoformat() + "Z"
        return f"""# Governance Ledger — Empirica-backed

**Generated from artifact graph; do not edit**  
*Last updated: {now}*  
*Total candidates: {len(self.bundles)}*  

---
"""
    
    def _render_candidate(self, bundle: CandidateBundle) -> str:
        ratified_date = bundle.ratified_at.split('T')[0] if bundle.ratified_at else "unknown"
        
        lines = [
            f"### {bundle.z_id}: {bundle.choice}",
            f"**Ratified:** {ratified_date} by {bundle.ratified_by}  ",
            f"**Status:** {bundle.verdict_badge()} | Brier: {bundle.brier_score:.2f}  ",
            "",
        ]
        
        if bundle.findings:
            lines.append("#### Evidence (F)")
            for f in bundle.findings:
                lines.append(f"- {f['text']} *(impact: {f.get('impact', 0):.2f})*")
            lines.append("")
        
        if bundle.assumptions or bundle.falsifier:
            lines.append("#### Assumptions & Falsifier (H)")
            for a in bundle.assumptions:
                lines.append(f"- {a['text']} *(confidence: {a.get('confidence', 1.0):.2f})*")
            if bundle.falsifier:
                lines.append(f"- **Falsifier:** {bundle.falsifier['text']} *(confidence: {bundle.falsifier.get('confidence', 0):.2f})*")
            lines.append("")
        
        lines.extend([
            "#### Verdict",
            f"- Claims: {bundle.claims_held} held · {bundle.claims_refuted} refuted · {bundle.claims_untested} untested",
            f"- Reversibility: {bundle.reversibility}",
            "",
            f"#### Rationale",
            f"{bundle.rationale}",
            "",
            "---",
            ""
        ])
        
        return "\n".join(lines)
    
    def _render_flagged(self, flagged: List[CandidateBundle]) -> str:
        lines = []
        for bundle in flagged:
            status = []
            if bundle.is_untested():
                status.append("UNTESTED")
            if bundle.is_disputed():
                status.append("DISPUTED")
            lines.append(f"- {bundle.z_id}: {bundle.choice} — {', '.join(status)}")
        return "\n".join(lines)
    
    def _render_footer(self) -> str:
        held = sum(b.claims_held for b in self.bundles)
        refuted = sum(b.claims_refuted for b in self.bundles)
        avg_brier = sum(b.brier_score for b in self.bundles) / len(self.bundles) if self.bundles else 0.0
        
        return f"""
---

## Summary
| Metric | Value |
|--------|-------|
| Total candidates | {len(self.bundles)} |
| Claims held | {held} |
| Claims refuted | {refuted} |
| Avg Brier | {avg_brier:.2f} |

*Generated from Empirica artifact graph. Edit via empirica CLI + Z2 ECO gate.*
"""


if __name__ == '__main__':
    # Sample: one candidate
    samples = [{
        "decision_id": "dec_001",
        "choice": "Adopt empirica-only governance",
        "rationale": "Single source of truth reduces calibration drift",
        "reversibility": "committal",
        "ratified_at": "2026-10-09T14:32:00Z",
        "ratified_by": "Z2-night",
        "artifacts_json": json.dumps([
            {"type": "finding", "text": "REGISTERED.md manually maintained, 5,141 lines", "impact": 0.95},
            {"type": "assumption", "text": "Cortex Qdrant can be authoritative store", "confidence": 0.72},
            {"type": "assumption", "text": "If Qdrant lost, graph is unrecoverable", "confidence": 0.15}
        ]),
        "claims_held": 3,
        "claims_refuted": 0,
        "claims_untested": 1,
        "brier_score": 0.78
    }]
    
    renderer = RegisteredRenderer(samples)
    print(renderer.render())

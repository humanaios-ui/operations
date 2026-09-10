"""
receipt_reconciliation.py — Receipt Reconciliation (B.6 Session Ritual)

Reconciles claims made during session against the event ledger (tree).
Detects RECEIPT-GAP when claim appears in transcript but not in ledger.
Emits gaps to Priority Queue for Z2 verification.

Pattern (§B.6 Session Close):
1. EXTRACT: Parse all agent claims from session transcript
2. MATCH: Search event chains for corresponding ledger entry per claim
3. RECONCILE: For each claim, generate receipt (claim → ledger match or GAP)
4. REPORT: Summary of matched claims, gaps, discrepancies
5. Z2: Verify receipts or flag mismatches

Claim types:
- VERDICT: "experiment X returned outcome Y"
- CYCLE: "task X consumed H hours, T tokens"
- MOLT: "proposed molt for constant Z"
- MEASUREMENT: "metric X measured as value Y"
- COMPLETION: "milestone M completed with test_count=N"

IC-031 mitigation: Every claim must find a ledger entry or emit RECEIPT-GAP.
No volume credit without ledger proof.

Receipt format:
{
  claim_id: str (hash of claim)
  claim_text: str
  claim_type: str (VERDICT, CYCLE, MOLT, MEASUREMENT, COMPLETION)
  ledger_match: Optional[Dict] (matched event)
  status: str (MATCHED, GAP)
  timestamp: str
}
"""

import json
import hashlib
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum


class ClaimType(Enum):
    """Types of claims made in session."""
    VERDICT = "VERDICT"
    CYCLE = "CYCLE"
    MOLT = "MOLT"
    MEASUREMENT = "MEASUREMENT"
    COMPLETION = "COMPLETION"
    GATE = "GATE"
    OTHER = "OTHER"


class ReceiptStatus(Enum):
    """Status of claim reconciliation."""
    MATCHED = "MATCHED"        # Found in ledger
    GAP = "GAP"                # Not found in ledger
    AMBIGUOUS = "AMBIGUOUS"    # Multiple possible matches
    PARTIAL = "PARTIAL"        # Partially matched


@dataclass
class ClaimStatement:
    """A claim extracted from transcript."""
    claim_id: str
    claim_text: str
    claim_type: str
    extracted_at: str
    line_number: int
    key_entities: Dict[str, str]  # e.g., {'molt_id': 'M11', 'tests': '140'}


@dataclass
class Receipt:
    """Receipt reconciling claim to ledger."""
    claim_id: str
    claim_text: str
    claim_type: str
    status: str                # MATCHED, GAP, AMBIGUOUS, PARTIAL
    ledger_match: Optional[Dict[str, Any]]
    match_confidence: float    # 0.0-1.0
    explanation: str
    timestamp: str


@dataclass
class ReceiptGap:
    """Gap where claim doesn't match ledger."""
    gap_id: str
    claim_id: str
    claim_text: str
    claim_type: str
    search_results: int        # How many ledger entries searched
    best_match: Optional[Dict[str, Any]]  # Closest match if any
    best_match_confidence: float
    recommendation: str        # Action to take
    timestamp: str


class ReceiptReconciliationEngine:
    """Receipt Reconciliation — claim vs tree reconciliation."""

    def __init__(self):
        self.claims = []                # List of ClaimStatement
        self.receipts = []              # List of Receipt
        self.gaps = []                  # List of ReceiptGap
        self.ledger_entries = []        # Event chain entries to search
        self.claim_patterns = self._setup_claim_patterns()

    def _setup_claim_patterns(self) -> Dict[str, str]:
        """Setup regex patterns for claim extraction."""
        return {
            'VERDICT': r'(VERDICT|outcome|result|passed|failed).*?(EXPECTED|SURPRISE|VOID)',
            'CYCLE': r'(consumed|spent|used).*?(\d+)\s*(hours?|h)',
            'MOLT': r'(molt|proposed|constant|changed)',
            'MEASUREMENT': r'(measured|metric|value|result).*?(\d+\.?\d*)',
            'COMPLETION': r'(completed|finished|done).*?(milestone|M\d+)',
            'GATE': r'(gate|pass|fail|check).*?(gate)',
        }

    def extract_claims_from_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Extract claims from session transcript.

        Args:
            transcript: Full session transcript text

        Returns:
            Dict with extracted claims and count
        """
        lines = transcript.split('\n')
        claims = []

        for line_num, line in enumerate(lines):
            if not line.strip() or line.startswith('#'):
                continue

            # Try to match against patterns
            for claim_type, pattern in self.claim_patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    claim_id = hashlib.sha256(line.encode()).hexdigest()[:16]

                    # Extract key entities from line
                    entities = self._extract_entities(line)

                    claim = ClaimStatement(
                        claim_id=claim_id,
                        claim_text=line.strip(),
                        claim_type=claim_type,
                        extracted_at=datetime.now().isoformat(),
                        line_number=line_num,
                        key_entities=entities,
                    )

                    claims.append(claim)
                    self.claims.append(claim)

        return {
            'claims_extracted': len(claims),
            'claims': [asdict(c) for c in claims],
        }

    def _extract_entities(self, line: str) -> Dict[str, str]:
        """Extract key entities (molt_id, numbers, etc.) from claim line."""
        entities = {}

        # Extract molt_id or M-number
        molt_match = re.search(r'(M\d+|molt_id[\'"]?:\s*[\'"]?(\w+))', line, re.IGNORECASE)
        if molt_match:
            entities['molt_id'] = molt_match.group(1)

        # Extract numbers (tests, hours, tokens)
        numbers = re.findall(r'(\d+\.?\d*)', line)
        if numbers:
            entities['numbers'] = numbers

        # Extract outcome types
        for outcome in ['EXPECTED', 'SURPRISE', 'VOID', 'PASS', 'FAIL']:
            if outcome in line.upper():
                entities['outcome'] = outcome

        return entities

    def load_ledger_entries(self, ledger: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Load event chain ledger entries for matching.

        Args:
            ledger: List of event entries from ledgers

        Returns:
            Dict with ledger count loaded
        """
        self.ledger_entries = ledger

        return {
            'ledger_entries_loaded': len(ledger),
            'status': 'LOADED',
        }

    def match_claim_to_ledger(self, claim: ClaimStatement) -> Dict[str, Any]:
        """
        Attempt to match claim to ledger entry.

        Args:
            claim: ClaimStatement to match

        Returns:
            Dict with match result (MATCHED/GAP/AMBIGUOUS)
        """
        if not self.ledger_entries:
            return {
                'claim_id': claim.claim_id,
                'status': 'NO_LEDGER',
                'error': 'No ledger entries loaded',
            }

        matches = []

        # Search ledger for matching entries
        for entry in self.ledger_entries:
            # Calculate match score based on matching fields
            score = 0

            # Check molt_id match
            if 'molt_id' in claim.key_entities and 'molt_id' in entry:
                if claim.key_entities['molt_id'] == entry.get('molt_id'):
                    score += 0.5

            # Check outcome match
            if 'outcome' in claim.key_entities:
                entry_outcome = entry.get('outcome') or entry.get('status')
                if entry_outcome and claim.key_entities['outcome'] in str(entry_outcome):
                    score += 0.3

            # Check event type match (VERDICT, CYCLE, etc.)
            entry_type = entry.get('type') or entry.get('event_type')
            if claim.claim_type == entry_type:
                score += 0.2

            # Check timestamp proximity (within 1h)
            if 'timestamp' in entry:
                entry_ts = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                claim_ts = datetime.fromisoformat(claim.extracted_at.replace('Z', '+00:00'))
                time_diff = abs((claim_ts - entry_ts).total_seconds())
                if time_diff < 3600:  # 1 hour
                    score += 0.1

            if score > 0:
                matches.append({
                    'entry': entry,
                    'score': score,
                })

        matches = sorted(matches, key=lambda x: x['score'], reverse=True)

        if len(matches) == 0:
            # GAP: No match found
            gap_id = f'GAP-{datetime.now().isoformat()[:10]}-{len(self.gaps):05d}'

            gap = ReceiptGap(
                gap_id=gap_id,
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                search_results=0,
                best_match=None,
                best_match_confidence=0.0,
                recommendation='VERIFY_WITH_Z2',
                timestamp=datetime.now().isoformat(),
            )

            self.gaps.append(gap)

            receipt = Receipt(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                status=ReceiptStatus.GAP.value,
                ledger_match=None,
                match_confidence=0.0,
                explanation='No matching ledger entry found',
                timestamp=datetime.now().isoformat(),
            )

        elif len(matches) == 1 and matches[0]['score'] > 0.6:
            # MATCHED: Single strong match
            receipt = Receipt(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                status=ReceiptStatus.MATCHED.value,
                ledger_match=matches[0]['entry'],
                match_confidence=matches[0]['score'],
                explanation=f'Matched to ledger entry (score: {matches[0]["score"]:.2f})',
                timestamp=datetime.now().isoformat(),
            )

        elif len(matches) > 1:
            # AMBIGUOUS: Multiple matches
            gap_id = f'GAP-{datetime.now().isoformat()[:10]}-{len(self.gaps):05d}'

            gap = ReceiptGap(
                gap_id=gap_id,
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                search_results=len(matches),
                best_match=matches[0]['entry'],
                best_match_confidence=matches[0]['score'],
                recommendation='CLARIFY_WHICH_ENTRY',
                timestamp=datetime.now().isoformat(),
            )

            self.gaps.append(gap)

            receipt = Receipt(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                status=ReceiptStatus.AMBIGUOUS.value,
                ledger_match=matches[0]['entry'],
                match_confidence=matches[0]['score'],
                explanation=f'Multiple possible matches ({len(matches)}); best score: {matches[0]["score"]:.2f}',
                timestamp=datetime.now().isoformat(),
            )

        else:
            # PARTIAL: Weak match
            gap_id = f'GAP-{datetime.now().isoformat()[:10]}-{len(self.gaps):05d}'

            gap = ReceiptGap(
                gap_id=gap_id,
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                search_results=len(matches),
                best_match=matches[0]['entry'] if matches else None,
                best_match_confidence=matches[0]['score'] if matches else 0.0,
                recommendation='VERIFY_WITH_Z2',
                timestamp=datetime.now().isoformat(),
            )

            self.gaps.append(gap)

            receipt = Receipt(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                claim_type=claim.claim_type,
                status=ReceiptStatus.PARTIAL.value,
                ledger_match=matches[0]['entry'] if matches else None,
                match_confidence=matches[0]['score'] if matches else 0.0,
                explanation=f'Weak match (score: {matches[0]["score"]:.2f}); needs Z2 verification',
                timestamp=datetime.now().isoformat(),
            )

        self.receipts.append(receipt)

        return {
            'claim_id': claim.claim_id,
            'status': receipt.status,
            'confidence': receipt.match_confidence,
            'explanation': receipt.explanation,
        }

    def reconcile_all_claims(self) -> Dict[str, Any]:
        """Reconcile all extracted claims against ledger."""
        for claim in self.claims:
            self.match_claim_to_ledger(claim)

        matched = sum(1 for r in self.receipts if r.status == ReceiptStatus.MATCHED.value)
        gaps = len(self.gaps)
        ambiguous = sum(1 for r in self.receipts if r.status == ReceiptStatus.AMBIGUOUS.value)
        partial = sum(1 for r in self.receipts if r.status == ReceiptStatus.PARTIAL.value)

        return {
            'total_claims': len(self.claims),
            'matched': matched,
            'gaps': gaps,
            'ambiguous': ambiguous,
            'partial': partial,
            'status': 'RECONCILIATION_COMPLETE',
        }

    def report_receipt_gaps(self) -> Dict[str, Any]:
        """Report all RECEIPT-GAP items for Z2."""
        return {
            'receipt_gaps': len(self.gaps),
            'gaps': [asdict(g) for g in self.gaps],
        }

    def report_receipts_summary(self) -> Dict[str, Any]:
        """Report summary of receipt reconciliation."""
        matched = [r for r in self.receipts if r.status == ReceiptStatus.MATCHED.value]
        unmatched = [r for r in self.receipts if r.status != ReceiptStatus.MATCHED.value]

        return {
            'total_claims': len(self.claims),
            'matched_receipts': len(matched),
            'unmatched_receipts': len(unmatched),
            'receipt_gap_count': len(self.gaps),
            'by_type': {
                claim_type: sum(1 for r in self.receipts if r.claim_type == claim_type)
                for claim_type in [ct.value for ct in ClaimType]
            },
            'matched': [asdict(r) for r in matched[:5]],  # First 5 matched
            'unmatched': [asdict(r) for r in unmatched[:5]],  # First 5 unmatched
        }

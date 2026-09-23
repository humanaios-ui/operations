"""P34-X Temporal Contamination Extractor

A layered guard for detecting ungrounded temporal/commissive language in LLM output.
Incorporates evidence grounding, speaker attribution (v1: high-precision heuristic),
and exception registry whitelisting.

Version: v1-CANDIDATE (awaiting Z2 ratification)
"""

__version__ = "1.0.0-candidate"
__author__ = "Claude (Z1) + Night (Z2 ratifier)"

from p34x_temporal_extractor.core import (
    TemporalExtractor,
    TemporalFinding,
    ExtractorConfig,
)
from p34x_temporal_extractor.evidence import (
    EvidenceProvider,
    EvidenceRecord,
    GitLogProvider,
    LedgerProvider,
)

__all__ = [
    "TemporalExtractor",
    "TemporalFinding",
    "ExtractorConfig",
    "EvidenceProvider",
    "EvidenceRecord",
    "GitLogProvider",
    "LedgerProvider",
]

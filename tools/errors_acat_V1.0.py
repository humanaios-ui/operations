#!/usr/bin/env python3
"""
ACAT Error Taxonomy — v1.0
HumanAIOS · S-051626-01-acat-tools-alternate-functions-mapping

Replaces the pytest-dash boilerplate (errors.py) with a proper ACAT domain
error hierarchy. All 8 other tools import from this module for consistent
error classification and machine-readable error codes.

Error classes:
  AcatError           — Base class for all ACAT errors
  SpecLoadFailed      — File/schema load failure (was duplicated in 5 tools)
  ValidationError     — A validation gate failed with specific failure codes
  GateNotPassed       — Specific gate (G-1 through G-4) has not been cleared
  DriftViolation      — A registered drift code was detected (D-class, C-class, IC-class)
  SessionStateError   — Session state machine entered invalid state
  CommitmentMismatch  — Phase 1 cryptographic commitment failed verification
  CalibrationFailed   — G-3 scorer calibration below threshold
  CorpusIntegrityError — Corpus CSV failed structural/row-level validation
"""


class AcatError(Exception):
    """Base class for all ACAT domain errors."""
    error_code: str = "ACAT_ERROR"

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code or self.__class__.error_code

    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code,
            "message": str(self),
            "class": self.__class__.__name__,
        }


class SpecLoadFailed(AcatError):
    """
    File or schema load failure.
    Raised when a required input file cannot be found, read, or parsed.
    Consolidates the identical SpecLoadFailed definitions previously
    duplicated across corpus_integrity_validator, acat_session_validator,
    drift_catalog_validator, acat_dimension_scorer, and acat_document_analyzer.
    """
    error_code = "SPEC_LOAD_FAILED"


class ValidationError(AcatError):
    """
    A validation gate produced hard failures.
    Carries a list of failure_codes for machine-readable downstream handling.
    """
    error_code = "VALIDATION_FAILED"

    def __init__(self, message: str, failure_codes: list = None):
        super().__init__(message)
        self.failure_codes = failure_codes or []

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["failure_codes"] = self.failure_codes
        return d


class GateNotPassed(AcatError):
    """
    A specific gate (G-1, G-2, G-3, G-4) has not been cleared.
    gate_id: "G-1" | "G-2" | "G-3" | "G-4"
    """
    error_code = "GATE_NOT_PASSED"

    def __init__(self, gate_id: str, message: str = None):
        super().__init__(message or f"Gate {gate_id} has not been passed")
        self.gate_id = gate_id

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["gate_id"] = self.gate_id
        return d


class DriftViolation(AcatError):
    """
    A registered drift code was detected in the session or corpus.
    drift_code: e.g. "D-04", "C-09", "IC-023"
    """
    error_code = "DRIFT_VIOLATION"

    def __init__(self, drift_code: str, message: str = None):
        super().__init__(message or f"Drift violation: {drift_code}")
        self.drift_code = drift_code

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["drift_code"] = self.drift_code
        return d


class SessionStateError(AcatError):
    """
    Session state machine entered an invalid state.
    current_state: the state at error time
    expected_state: the state required for the attempted operation
    """
    error_code = "SESSION_STATE_ERROR"

    def __init__(self, current_state: str, expected_state: str, operation: str):
        msg = (
            f"Cannot execute '{operation}': session is in state '{current_state}', "
            f"expected '{expected_state}'"
        )
        super().__init__(msg)
        self.current_state = current_state
        self.expected_state = expected_state
        self.operation = operation

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["current_state"] = self.current_state
        d["expected_state"] = self.expected_state
        d["operation"] = self.operation
        return d


class CommitmentMismatch(AcatError):
    """
    Phase 1 cryptographic commitment failed verification.
    Indicates Phase 1 scores were altered after session open.
    """
    error_code = "COMMITMENT_MISMATCH"

    def __init__(self, session_id: str, message: str = None):
        super().__init__(
            message or
            f"Session {session_id}: Phase 1 commitment hash mismatch — scores may have been altered"
        )
        self.session_id = session_id

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["session_id"] = self.session_id
        return d


class CalibrationFailed(AcatError):
    """
    G-3 scorer calibration failed to meet MAE/r thresholds.
    mae: actual mean absolute error
    pearson_r: actual Pearson correlation
    """
    error_code = "CALIBRATION_FAILED"

    def __init__(self, mae: float, pearson_r: float, detail: str = None):
        super().__init__(
            detail or
            f"G-3 FAIL: MAE={mae:.3f} (threshold 1.5), r={pearson_r:.3f} (threshold 0.70)"
        )
        self.mae = mae
        self.pearson_r = pearson_r

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["mae"] = self.mae
        d["pearson_r"] = self.pearson_r
        return d


class CorpusIntegrityError(AcatError):
    """
    Corpus CSV failed structural or row-level validation.
    failure_count: number of hard failures found
    """
    error_code = "CORPUS_INTEGRITY_ERROR"

    def __init__(self, failure_count: int, failures: list = None):
        super().__init__(f"Corpus validation failed with {failure_count} hard failure(s)")
        self.failure_count = failure_count
        self.failures = failures or []

    def to_dict(self) -> dict:
        d = super().to_dict()
        d["failure_count"] = self.failure_count
        d["failures"] = self.failures[:10]  # cap for safety
        return d


# ── Convenience mapping for tools that check error_code strings ───────────────

ERROR_CODE_MAP = {
    cls.error_code: cls
    for cls in [
        SpecLoadFailed, ValidationError, GateNotPassed, DriftViolation,
        SessionStateError, CommitmentMismatch, CalibrationFailed, CorpusIntegrityError
    ]
}


def error_from_code(error_code: str, message: str = None, **kwargs) -> AcatError:
    """Instantiate an AcatError subclass by its error_code string."""
    cls = ERROR_CODE_MAP.get(error_code, AcatError)
    return cls(message or error_code, **kwargs)

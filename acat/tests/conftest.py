"""Test fixtures for the ACAT API.

The write-gate (acat.api.security.require_write_token, added S-070226 for the
audit P0-URGENT mitigation) is fail-closed, so business-logic tests that POST
to mutating endpoints would otherwise 503. This autouse fixture overrides the
gate to a no-op for those tests. Tests that exercise the gate itself pop the
override (see test_write_gate.py).
"""
from __future__ import annotations

import pytest

from acat.api.app import app
from acat.api.security import require_write_token


@pytest.fixture(autouse=True)
def _bypass_write_gate():
    app.dependency_overrides[require_write_token] = lambda: None
    yield
    app.dependency_overrides.pop(require_write_token, None)

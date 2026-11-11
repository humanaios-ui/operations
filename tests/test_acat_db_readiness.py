"""Readiness must prove a real read and keep backend details private."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def database(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "acat/api/db.py"
    spec = importlib.util.spec_from_file_location("acat_db_readiness_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "PSYCOPG2_AVAILABLE", True)
    monkeypatch.setenv("DATABASE_URL", "postgresql://private:secret@private-host/db")
    cursor = Mock()
    cursor.fetchone.return_value = (1,)
    connection = Mock()
    connection.cursor.return_value = cursor
    connect = Mock(return_value=connection)
    monkeypatch.setattr(module, "psycopg2", SimpleNamespace(connect=connect), raising=False)
    return module, connect, connection, cursor


def test_real_backend_requires_bounded_read_only_probe(database):
    module, connect, connection, cursor = database
    assert module.check_database_readiness() == {
        "backend": "REAL", "ready": True, "reason": "SELECT_1_PASSED"
    }
    assert connect.call_args.kwargs == {
        "connect_timeout": 5,
        "options": "-c statement_timeout=5000 -c default_transaction_read_only=on",
    }
    cursor.execute.assert_called_once_with("SELECT 1")
    cursor.close.assert_called_once()
    connection.close.assert_called_once()
    assert module._pool is None


@pytest.mark.parametrize("mock_pool", [False, True])
def test_mock_backend_is_not_ready(database, mock_pool):
    module, connect, _, _ = database
    if mock_pool:
        module._pool = module._MockConnectionPool()
    else:
        module.PSYCOPG2_AVAILABLE = False
    assert module.check_database_readiness() == {
        "backend": "MOCK", "ready": False, "reason": "MOCK_BACKEND"
    }
    connect.assert_not_called()


def test_missing_configuration_cannot_probe_default_localhost(database, monkeypatch):
    module, connect, _, _ = database
    monkeypatch.delenv("DATABASE_URL")
    assert module.check_database_readiness()["reason"] == "DATABASE_URL_MISSING"
    connect.assert_not_called()


@pytest.mark.parametrize("failure_stage", ["connect", "cursor", "execute", "fetchone"])
def test_failures_hide_secrets_and_close_acquired_resources(database, failure_stage):
    module, connect, connection, cursor = database
    target = connect if failure_stage == "connect" else (
        connection.cursor if failure_stage == "cursor" else getattr(cursor, failure_stage)
    )
    target.side_effect = RuntimeError("secret private-host postgresql://private")
    result = module.check_database_readiness()
    assert result == {"backend": "UNAVAILABLE", "ready": False, "reason": "PROBE_FAILED"}
    if failure_stage != "connect":
        connection.close.assert_called_once()
    if failure_stage in {"execute", "fetchone"}:
        cursor.close.assert_called_once()


def test_wrong_result_does_not_claim_readiness(database):
    module, _, connection, cursor = database
    cursor.fetchone.return_value = (None,)
    assert module.check_database_readiness() == {
        "backend": "REAL", "ready": False, "reason": "UNEXPECTED_PROBE_RESULT"
    }
    connection.close.assert_called_once()


def test_cursor_cleanup_failure_still_closes_connection(database):
    module, _, connection, cursor = database
    cursor.close.side_effect = RuntimeError("secret")
    assert module.check_database_readiness() == {
        "backend": "UNAVAILABLE", "ready": False, "reason": "CLEANUP_FAILED"
    }
    connection.close.assert_called_once()

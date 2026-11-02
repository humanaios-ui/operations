"""
Database connection management for ACAT API.

Handles Supabase PostgreSQL connections with connection pooling.
"""

import os
import logging
from typing import Generator

logger = logging.getLogger("acat.db")

try:
    import psycopg2
    from psycopg2.pool import SimpleConnectionPool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not installed; database features will use mock connection")

# Connection pool (lazy initialized)
_pool = None


def check_database_readiness():
    """Probe the configured PostgreSQL backend without changing application state.

    Usage: ``from acat.api.db import check_database_readiness`` then call
    ``check_database_readiness()`` to receive backend, ready, and reason fields.
    Results contain no URL, credentials, or exception text. A fresh connection
    bounds both connection and statement time and avoids changing pooled sessions.
    This is opt-in; the runtime's existing mock fallback remains unchanged.
    """
    if isinstance(_pool, _MockConnectionPool) or not PSYCOPG2_AVAILABLE:
        return {"backend": "MOCK", "ready": False, "reason": "MOCK_BACKEND"}
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return {"backend": "UNAVAILABLE", "ready": False, "reason": "DATABASE_URL_MISSING"}

    connection = None
    cursor = None
    result = {"backend": "UNAVAILABLE", "ready": False, "reason": "PROBE_FAILED"}
    try:
        connection = psycopg2.connect(
            db_url,
            connect_timeout=5,
            options="-c statement_timeout=5000 -c default_transaction_read_only=on",
        )
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        if cursor.fetchone() == (1,):
            result = {"backend": "REAL", "ready": True, "reason": "SELECT_1_PASSED"}
        else:
            result = {"backend": "REAL", "ready": False, "reason": "UNEXPECTED_PROBE_RESULT"}
    except Exception:
        # Database exception strings may contain credentials or host details.
        pass
    finally:
        for resource in (cursor, connection):
            if resource is not None:
                try:
                    resource.close()
                except Exception:
                    result = {"backend": "UNAVAILABLE", "ready": False, "reason": "CLEANUP_FAILED"}
    return result


class _MockConnectionPool:
    """Mock connection pool for testing without psycopg2."""

    class MockConnection:
        def cursor(self):
            return _MockConnectionPool._MockCursor()

        def commit(self):
            pass

        def rollback(self):
            pass

        def close(self):
            pass

    class _MockCursor:
        def __init__(self):
            pass

        def execute(self, query, params=None):
            pass

        def fetchone(self):
            return (None,)

        def fetchall(self):
            return []

    def getconn(self):
        return self.MockConnection()

    def putconn(self, conn):
        pass

    def closeall(self):
        pass


def get_pool():
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        if not PSYCOPG2_AVAILABLE:
            logger.warning("psycopg2 not available; using mock connection pool")
            _pool = _MockConnectionPool()
            return _pool

        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/humanaios",
        )
        try:
            _pool = SimpleConnectionPool(
                1,  # min connections
                10,  # max connections
                db_url,
                connect_timeout=5,
            )
            logger.info("Database connection pool initialized")
        except Exception as exc:
            logger.error(f"Failed to initialize connection pool: {exc}")
            logger.warning("Falling back to mock connection pool")
            _pool = _MockConnectionPool()
    return _pool


def get_db_connection():
    """
    Get a database connection from the pool.

    Returns a context manager (use with 'with' statement).
    """
    pool = get_pool()
    return pool.getconn()


def return_db_connection(conn):
    """Return a connection to the pool."""
    if conn:
        pool = get_pool()
        pool.putconn(conn)


def close_all_connections():
    """Close all connections in the pool."""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
        logger.info("Connection pool closed")

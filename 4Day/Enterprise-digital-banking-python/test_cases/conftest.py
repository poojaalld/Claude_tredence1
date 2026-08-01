"""Shares the in-memory SQLite engine and helper fixtures from tests/conftest.py
so this folder's tests run against the same overridden `get_db` dependency
instead of standing up a second, conflicting engine.
"""

from tests.conftest import (  # noqa: F401
    TestingSessionLocal,
    _fresh_database,
    auth_headers,
    client,
    engine,
    make_admin,
    register_customer,
)

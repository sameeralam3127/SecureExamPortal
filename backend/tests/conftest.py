"""Shared pytest fixtures.

The suite runs against a throwaway SQLite database so it needs no Postgres
service. Environment variables are set *before* the application package is
imported, because ``app.extensions.db`` binds its engine at import time.
"""

import os
import tempfile

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault(
    "AUTH_SECRET_KEY", "test-secret-key-that-is-definitely-long-enough-000"
)

_db_fd, _db_path = tempfile.mkstemp(suffix=".sqlite")
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_db_path}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    # Entering the context manager runs the lifespan startup (init_db),
    # which creates the schema in the SQLite database.
    with TestClient(app) as test_client:
        yield test_client

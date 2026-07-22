"""Guards that the Alembic baseline stays in step with the ORM models.

Runs the migrations against a fresh throwaway SQLite database and checks that
the resulting tables match ``Base.metadata`` (the source of truth the app and
the test-suite's ``create_all`` build from).
"""

import os
import tempfile

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.extensions.db import BACKEND_ROOT, Base


def _alembic_config(database_url: str) -> Config:
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_build_the_model_schema():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    url = f"sqlite+pysqlite:///{path}"
    try:
        config = _alembic_config(url)
        command.upgrade(config, "head")

        engine = create_engine(url)
        migrated_tables = set(inspect(engine).get_table_names())
        engine.dispose()

        model_tables = set(Base.metadata.tables)
        # Every model table must be created by the migrations.
        assert model_tables <= migrated_tables
        # And the audit table added for this feature must exist.
        assert "audit_events" in migrated_tables
    finally:
        os.remove(path)


def test_migration_downgrade_is_reversible():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    url = f"sqlite+pysqlite:///{path}"
    try:
        config = _alembic_config(url)
        command.upgrade(config, "head")
        command.downgrade(config, "base")

        engine = create_engine(url)
        remaining = set(inspect(engine).get_table_names())
        engine.dispose()
        # Only Alembic's own bookkeeping table should remain.
        assert remaining <= {"alembic_version"}
    finally:
        os.remove(path)

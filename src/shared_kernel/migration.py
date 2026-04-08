"""Programmatic Alembic migration runner.

Provides ``run_migrations()`` for use in application startup and test fixtures,
replacing the old ``metadata.create_all()`` / ``metadata.drop_all()`` approach.

Both bounded contexts (auth + project_collaboration) share a single migration
history stored in ``migrations/versions/``.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine


def _alembic_config(engine: Engine) -> Config:
    """Build an Alembic Config pointing at the project's migration directory.

    Overrides ``sqlalchemy.url`` with the engine's URL so that migrations
    run against the supplied engine (dev, test, or any other).

    Sets ``sqlalchemy.url.override`` flag so that ``env.py`` does NOT
    overwrite the URL with ``DATABASE_URL`` from the environment.
    """
    # alembic.ini lives at the repository root
    ini_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option(
        "sqlalchemy.url", engine.url.render_as_string(hide_password=False)
    )
    # Signal to env.py that the URL was set programmatically
    cfg.set_main_option("is_programmatic", "true")
    return cfg


def run_migrations(engine: Engine) -> None:
    """Apply all pending Alembic migrations (upgrade to *head*).

    Idempotent: if the database is already at *head*, this is a no-op.
    """
    cfg = _alembic_config(engine)
    command.upgrade(cfg, "head")


def downgrade_migrations(engine: Engine, revision: str = "base") -> None:
    """Downgrade the database to the given revision (default: *base*).

    Intended for test teardown — drops all managed tables.
    """
    cfg = _alembic_config(engine)
    command.downgrade(cfg, revision)

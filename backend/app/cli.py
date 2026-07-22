"""Operational management commands.

Usage:
    python -m app.cli migrate   # apply Alembic migrations up to head
    python -m app.cli seed       # create the bootstrap admin from env config
    python -m app.cli create-all # build schema from models (dev/test convenience)

Migration and seeding are intentionally separate so production deploys run
`migrate` once (via the container entrypoint) and seed independently.
"""

import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app.cli")


def _migrate() -> None:
    from app.extensions.db import run_migrations

    logger.info("Applying database migrations...")
    run_migrations()
    logger.info("Migrations applied.")


def _seed() -> None:
    from app.extensions.db import seed_initial_admin

    logger.info("Seeding initial admin (if configured and absent)...")
    seed_initial_admin()
    logger.info("Seed complete.")


def _create_all() -> None:
    from app.extensions.db import create_all

    logger.info("Creating schema from ORM metadata...")
    create_all()
    logger.info("Schema created.")


COMMANDS = {
    "migrate": _migrate,
    "seed": _seed,
    "create-all": _create_all,
}


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        sys.stderr.write(f"Usage: python -m app.cli [{'|'.join(COMMANDS)}]\n")
        return 2
    COMMANDS[args[0]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

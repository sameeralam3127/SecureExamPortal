import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.base import get_settings

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """Create the full schema directly from the ORM metadata.

    Used only for the test suite, which builds a throwaway database from the
    models. Real deployments manage schema through Alembic migrations.
    """
    import app.models  # noqa: F401  (registers every table on Base.metadata)

    Base.metadata.create_all(bind=engine)


def run_migrations() -> None:
    """Apply Alembic migrations up to head against the configured database."""
    from alembic import command
    from alembic.config import Config

    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    command.upgrade(config, "head")


def seed_initial_admin() -> None:
    """Create the bootstrap admin from env config, if requested and absent.

    Idempotent and safe to call from multiple workers: a concurrent insert that
    loses the race is swallowed via the unique-constraint IntegrityError.
    """
    from app.models.user import AuthProvider, User, UserRole
    from app.utils.security import hash_password

    if not settings.initial_admin_username:
        return

    with SessionLocal() as db:
        existing = db.scalar(
            select(User).where(User.username == settings.initial_admin_username)
        )
        if existing is not None:
            return

        if not settings.initial_admin_password or not settings.initial_admin_email:
            raise ValueError(
                "INITIAL_ADMIN_PASSWORD and INITIAL_ADMIN_EMAIL are required when "
                "INITIAL_ADMIN_USERNAME is set"
            )

        db.add(
            User(
                full_name=settings.initial_admin_full_name,
                username=settings.initial_admin_username,
                email=settings.initial_admin_email,
                password_hash=hash_password(settings.initial_admin_password),
                role=UserRole.admin,
                auth_provider=AuthProvider.password,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            logger.info("Initial admin already created by another worker; skipping.")


def init_db() -> None:
    """Prepare the database for the running process.

    - testing: build the schema from ORM metadata (no migrations needed)
    - development: apply Alembic migrations for convenience
    - production: migrations are applied by the deploy entrypoint, so only the
      admin seed runs here

    Seeding is always separate from schema management.
    """
    environment = settings.environment.lower()
    if environment == "testing":
        create_all()
    elif environment == "development":
        run_migrations()

    seed_initial_admin()

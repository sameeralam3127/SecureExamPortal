from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config.base import get_settings


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


def init_db() -> None:
    from app.models.user import User, UserRole
    from app.utils.security import hash_password

    Base.metadata.create_all(bind=engine)
    ensure_exam_security_columns()

    with SessionLocal() as db:
        if not settings.initial_admin_username:
            return

        admin = db.scalar(select(User).where(User.username == settings.initial_admin_username))
        if admin is not None:
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
            )
        )
        db.commit()


def ensure_exam_security_columns() -> None:
    inspector = inspect(engine)
    if not inspector.has_table("portal_exams"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("portal_exams")}
    security_columns = {
        "block_clipboard": "BOOLEAN NOT NULL DEFAULT TRUE",
        "block_context_menu": "BOOLEAN NOT NULL DEFAULT TRUE",
        "block_inspect_shortcuts": "BOOLEAN NOT NULL DEFAULT TRUE",
        "enforce_fullscreen": "BOOLEAN NOT NULL DEFAULT FALSE",
        "track_focus_loss": "BOOLEAN NOT NULL DEFAULT TRUE",
    }
    with engine.begin() as connection:
        for column_name, definition in security_columns.items():
            if column_name in existing_columns:
                continue
            connection.execute(text(f"ALTER TABLE portal_exams ADD COLUMN {column_name} {definition}"))

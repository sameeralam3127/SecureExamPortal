from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id.desc())).all())


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

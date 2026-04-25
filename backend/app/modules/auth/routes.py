import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config.base import get_settings
from app.extensions.db import get_db
from app.models.user import User, UserRole
from app.modules.auth.dependencies import get_current_user
from app.schemas.user import GoogleLoginRequest, LoginRequest, LoginResponse, StudentRegisterRequest, UserRead
from app.utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return LoginResponse(
        access_token=create_access_token(user.id, user.username, user.role.value),
        user=user,
    )


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register_student(
    payload: StudentRegisterRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    duplicate = db.scalar(
        select(User).where((User.username == payload.username) | (User.email == payload.email))
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists",
        )

    user = User(
        full_name=payload.full_name,
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.student,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return LoginResponse(
        access_token=create_access_token(user.id, user.username, user.role.value),
        user=user,
    )


@router.post("/google", response_model=LoginResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google auth is not configured",
        )

    try:
        response = httpx.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.credential},
            timeout=20,
        )
        response.raise_for_status()
        profile = response.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential",
        ) from exc

    if profile.get("aud") != settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google client mismatch",
        )

    email = profile.get("email")
    full_name = profile.get("name") or "Google User"
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email not available",
        )

    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        base_username = email.split("@")[0].replace(".", "_")
        username = base_username
        suffix = 1
        while db.scalar(select(User).where(User.username == username)):
            suffix += 1
            username = f"{base_username}{suffix}"
        user = User(
            full_name=full_name,
            username=username,
            email=email,
            password_hash=hash_password(payload.credential[:32]),
            role=UserRole.student,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return LoginResponse(
        access_token=create_access_token(user.id, user.username, user.role.value),
        user=user,
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
